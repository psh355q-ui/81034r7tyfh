"""
Trading Signals API Router

Features:
- Generate signals from news
- Get active/historical signals
- Approve/Reject signals
- Signal validation status
- Backtest integration

Author: AI Trading System
Date: 2025-11-15
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
import asyncio

# Import modules
from backend.signals.news_signal_generator import (
    NewsSignalGenerator,
    TradingSignal,
    SignalAction,
    create_signal_generator,
)
from backend.signals.signal_validator import (
    SignalValidator,
    create_signal_validator,
)

# Import notification manager for alerts
from backend.notifications.notification_manager import (
    create_notification_manager,
)

# Import database models (adjust import as needed)
# from data.news_models import NewsArticle, NewsAnalysis, get_db

# Import auth if available
# from auth import require_read, require_write, require_execute

router = APIRouter(prefix="/signals", tags=["Trading Signals"])

# Global instances
_signal_generator = None
_signal_validator = None
_notification_manager = None

# In-memory signal storage (in production, use database)
_active_signals: Dict[int, Dict[str, Any]] = {}
_signal_history: List[Dict[str, Any]] = []
_signal_counter = 0


def get_generator():
    global _signal_generator
    if _signal_generator is None:
        _signal_generator = create_signal_generator()
    return _signal_generator


def get_validator():
    global _signal_validator
    if _signal_validator is None:
        _signal_validator = create_signal_validator()
    return _signal_validator


def get_notifier():
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = create_notification_manager()
    return _notification_manager


# ============================================================================
# Request/Response Models
# ============================================================================

class GenerateSignalRequest(BaseModel):
    """Request to generate signal from news analysis"""
    title: str
    url: Optional[str] = ""
    sentiment_overall: str  # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score: float  # -1.0 to 1.0
    sentiment_confidence: float = 0.7
    impact_magnitude: float  # 0.0 to 1.0
    urgency: str = "MEDIUM"  # IMMEDIATE, HIGH, MEDIUM, LOW
    risk_category: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    trading_actionable: bool = True
    related_tickers: List[Dict[str, Any]] = []
    affected_sectors: List[str] = []
    key_facts: List[str] = []
    key_warnings: List[str] = []
    article_id: Optional[int] = None


class SignalResponse(BaseModel):
    """Trading signal response"""
    id: int
    ticker: str
    action: str
    position_size: float
    confidence: float
    execution_type: str
    reason: str
    urgency: str
    created_at: str
    news_title: Optional[str]
    affected_sectors: List[str]
    auto_execute: bool
    status: str  # PENDING, APPROVED, REJECTED, EXECUTED
    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    executed_at: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApproveSignalRequest(BaseModel):
    """Request to approve a signal"""
    execute_immediately: bool = False
    adjusted_position_size: Optional[float] = None


class ValidatorStatusResponse(BaseModel):
    """Validator status response"""
    kill_switch_active: bool
    kill_switch_reason: str
    daily_trades_count: int
    daily_trade_limit: int
    daily_pnl: float
    daily_loss_limit: float
    consecutive_losses: int
    max_consecutive_losses: int
    market_open: bool
    statistics: Dict[str, int]


class GeneratorSettingsRequest(BaseModel):
    """Update generator settings"""
    base_position_size: Optional[float] = None
    max_position_size: Optional[float] = None
    min_confidence_threshold: Optional[float] = None
    sentiment_threshold: Optional[float] = None
    impact_threshold: Optional[float] = None
    enable_auto_execute: Optional[bool] = None


class ValidatorSettingsRequest(BaseModel):
    """Update validator settings"""
    min_confidence: Optional[float] = None
    max_position_size: Optional[float] = None
    daily_trade_limit: Optional[int] = None
    daily_loss_limit_pct: Optional[float] = None
    max_consecutive_losses: Optional[int] = None
    market_hours_only: Optional[bool] = None


# ============================================================================
# Signal Generation Endpoints
# ============================================================================

@router.post("/generate", response_model=Optional[SignalResponse])
async def generate_signal_from_news(
    request: GenerateSignalRequest,
    background_tasks: BackgroundTasks,
    # api_key: str = Depends(require_write),
):
    """
    Generate trading signal from news analysis.
    
    If signal is generated, it's added to active signals and notifications are sent.
    """
    global _signal_counter, _active_signals
    
    generator = get_generator()
    validator = get_validator()
    notifier = get_notifier()
    
    # Convert request to analysis dict
    analysis = {
        "title": request.title,
        "url": request.url,
        "sentiment_overall": request.sentiment_overall,
        "sentiment_score": request.sentiment_score,
        "sentiment_confidence": request.sentiment_confidence,
        "impact_magnitude": request.impact_magnitude,
        "urgency": request.urgency,
        "risk_category": request.risk_category,
        "trading_actionable": request.trading_actionable,
        "related_tickers": request.related_tickers,
        "affected_sectors": request.affected_sectors,
        "key_facts": request.key_facts,
        "key_warnings": request.key_warnings,
        "article_id": request.article_id,
    }
    
    # Generate signal
    signal = generator.generate_signal(analysis)
    
    if not signal:
        return None
    
    # Validate signal
    approved, reason, recommendation = validator.validate_signal(signal)
    
    # Store signal
    _signal_counter += 1
    signal_id = _signal_counter
    
    signal_data = {
        "id": signal_id,
        **signal.to_dict(),
        "status": "PENDING",
        "validation_result": {
            "approved": approved,
            "reason": reason,
            "recommendation": recommendation,
        },
        "approved_at": None,
        "rejected_at": None,
        "executed_at": None,
        "rejection_reason": None,
    }
    
    _active_signals[signal_id] = signal_data
    
    # Send notification (in background)
    background_tasks.add_task(
        _send_signal_notification,
        notifier,
        signal_data,
    )
    
    return SignalResponse(**signal_data)


async def _send_signal_notification(notifier, signal_data: Dict[str, Any]):
    """Send signal notification (background task)"""
    try:
        await notifier.send_trading_signal(signal_data, priority="HIGH")
    except Exception as e:
        import logging
        logging.error(f"Failed to send signal notification: {e}")


@router.get("", response_model=List[SignalResponse])
async def get_signals(
    hours: int = Query(168, description="Hours to look back"),
    limit: int = Query(100, ge=1, le=500),
    # api_key: str = Depends(require_read),
):
    """
    Get all signals from the last N hours.
    
    - **hours**: Hours to look back (default: 168 = 1 week)
    - **limit**: Maximum number of signals to return
    """
    # Calculate cutoff time
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    # Combine active and recent history
    all_signals = []
    
    # Add active signals
    all_signals.extend(list(_active_signals.values()))
    
    # Add history within time window
    for s in _signal_history:
        created_at = datetime.fromisoformat(s.get("created_at", ""))
        if created_at >= cutoff_time:
            all_signals.append(s)
    
    # Sort by created_at (newest first)
    all_signals.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return [SignalResponse(**s) for s in all_signals[:limit]]


@router.get("/active", response_model=List[SignalResponse])
async def get_active_signals(
    # api_key: str = Depends(require_read),
):
    """
    Get all active (pending) signals.
    """
    active = [
        SignalResponse(**s)
        for s in _active_signals.values()
        if s.get("status") == "PENDING"
    ]
    
    # Sort by confidence (highest first)
    active.sort(key=lambda x: x.confidence, reverse=True)
    
    return active


@router.get("/history", response_model=List[SignalResponse])
async def get_signal_history(
    limit: int = Query(50, ge=1, le=500),
    action_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    # api_key: str = Depends(require_read),
):
    """
    Get signal history.
    
    - **limit**: Maximum records
    - **action_filter**: Filter by action (BUY, SELL)
    - **status_filter**: Filter by status (APPROVED, REJECTED, EXECUTED)
    """
    history = list(_signal_history)
    
    if action_filter:
        history = [h for h in history if h.get("action") == action_filter]
    
    if status_filter:
        history = [h for h in history if h.get("status") == status_filter]
    
    # Sort by created_at (newest first)
    history.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return [SignalResponse(**h) for h in history[:limit]]


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal_by_id(
    signal_id: int,
    # api_key: str = Depends(require_read),
):
    """
    Get a specific signal by ID.
    """
    # Check active signals
    if signal_id in _active_signals:
        return SignalResponse(**_active_signals[signal_id])
    
    # Check history
    for s in _signal_history:
        if s.get("id") == signal_id:
            return SignalResponse(**s)
    
    raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")


# ============================================================================
# Signal Action Endpoints
# ============================================================================

@router.put("/{signal_id}/approve")
async def approve_signal(
    signal_id: int,
    request: ApproveSignalRequest,
    # api_key: str = Depends(require_execute),
):
    """
    Approve a pending signal.
    
    - **execute_immediately**: Execute the signal right away
    - **adjusted_position_size**: Override position size
    """
    if signal_id not in _active_signals:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    
    signal_data = _active_signals[signal_id]
    
    if signal_data["status"] != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Signal is not pending (status: {signal_data['status']})"
        )
    
    # Update signal
    signal_data["status"] = "APPROVED"
    signal_data["approved_at"] = datetime.now().isoformat()
    
    if request.adjusted_position_size is not None:
        signal_data["position_size"] = request.adjusted_position_size
    
    result = {
        "signal_id": signal_id,
        "status": "APPROVED",
        "approved_at": signal_data["approved_at"],
        "execute_immediately": request.execute_immediately,
    }
    
    # Execute if requested
    if request.execute_immediately:
        # In production, integrate with Phase 6 Smart Execution
        signal_data["status"] = "EXECUTED"
        signal_data["executed_at"] = datetime.now().isoformat()
        result["status"] = "EXECUTED"
        result["executed_at"] = signal_data["executed_at"]
        result["message"] = "Signal executed (simulated)"
    
    # Move to history
    _signal_history.append(signal_data)
    del _active_signals[signal_id]
    
    return result


@router.delete("/{signal_id}/reject")
async def reject_signal(
    signal_id: int,
    reason: str = Query("Manual rejection"),
    # api_key: str = Depends(require_write),
):
    """
    Reject a pending signal.
    
    - **reason**: Reason for rejection
    """
    if signal_id not in _active_signals:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    
    signal_data = _active_signals[signal_id]
    
    if signal_data["status"] != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Signal is not pending (status: {signal_data['status']})"
        )
    
    # Update signal
    signal_data["status"] = "REJECTED"
    signal_data["rejected_at"] = datetime.now().isoformat()
    signal_data["rejection_reason"] = reason
    
    # Move to history
    _signal_history.append(signal_data)
    del _active_signals[signal_id]
    
    return {
        "signal_id": signal_id,
        "status": "REJECTED",
        "rejected_at": signal_data["rejected_at"],
        "reason": reason,
    }


@router.post("/{signal_id}/execute")
async def execute_signal(
    signal_id: int,
    # api_key: str = Depends(require_execute),
):
    """
    Execute an approved signal.
    
    ⚠️ This requires EXECUTE permission.
    """
    # Find signal (active or in history)
    signal_data = None
    
    if signal_id in _active_signals:
        signal_data = _active_signals[signal_id]
    else:
        for s in _signal_history:
            if s.get("id") == signal_id:
                signal_data = s
                break
    
    if not signal_data:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    
    if signal_data["status"] not in ["PENDING", "APPROVED"]:
        raise HTTPException(
            status_code=400,
            detail=f"Signal cannot be executed (status: {signal_data['status']})"
        )
    
    # Execute (integrate with Phase 6 in production)
    signal_data["status"] = "EXECUTED"
    signal_data["executed_at"] = datetime.now().isoformat()
    
    # Record execution in validator
    validator = get_validator()
    # In production, record actual P&L
    # validator.record_trade_result(profit_pct)
    
    # Move to history if still active
    if signal_id in _active_signals:
        _signal_history.append(signal_data)
        del _active_signals[signal_id]
    
    return {
        "signal_id": signal_id,
        "status": "EXECUTED",
        "executed_at": signal_data["executed_at"],
        "message": "Signal executed successfully (simulated)",
        "ticker": signal_data["ticker"],
        "action": signal_data["action"],
        "position_size": signal_data["position_size"],
    }


# ============================================================================
# Validator & Generator Management
# ============================================================================

@router.get("/validator/status", response_model=ValidatorStatusResponse)
async def get_validator_status(
    # api_key: str = Depends(require_read),
):
    """
    Get current validator status (kill switch, limits, etc.).
    """
    validator = get_validator()
    return ValidatorStatusResponse(**validator.get_status())


@router.post("/validator/reset-kill-switch")
async def reset_kill_switch(
    # api_key: str = Depends(require_execute),
):
    """
    Reset the kill switch (admin action).
    
    ⚠️ Only do this after reviewing the situation.
    """
    validator = get_validator()
    validator.reset_kill_switch()
    
    return {
        "status": "reset",
        "message": "Kill switch has been reset",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/validator/reset-daily")
async def reset_daily_stats(
    # api_key: str = Depends(require_write),
):
    """
    Reset daily statistics (call at market close).
    """
    validator = get_validator()
    validator.reset_daily_stats()
    
    return {
        "status": "reset",
        "message": "Daily statistics reset",
        "timestamp": datetime.now().isoformat(),
    }


@router.put("/generator/settings")
async def update_generator_settings(
    settings: GeneratorSettingsRequest,
    # api_key: str = Depends(require_write),
):
    """
    Update signal generator settings.
    """
    generator = get_generator()
    generator.update_settings(**settings.dict(exclude_none=True))
    
    return {
        "status": "updated",
        "message": "Generator settings updated",
        "new_settings": {
            "base_position_size": generator.base_position_size,
            "max_position_size": generator.max_position_size,
            "min_confidence_threshold": generator.min_confidence_threshold,
            "sentiment_threshold": generator.sentiment_threshold,
            "impact_threshold": generator.impact_threshold,
            "enable_auto_execute": generator.enable_auto_execute,
        }
    }


@router.put("/validator/settings")
async def update_validator_settings(
    settings: ValidatorSettingsRequest,
    # api_key: str = Depends(require_write),
):
    """
    Update signal validator settings.
    """
    validator = get_validator()
    validator.update_settings(**settings.dict(exclude_none=True))
    
    status = validator.get_status()
    return {
        "status": "updated",
        "message": "Validator settings updated",
        "current_status": status,
    }


@router.get("/stats/summary")
async def get_stats_summary(
    # api_key: str = Depends(require_read),
):
    """
    Get signal statistics summary (alias for /statistics).
    """
    # This is an alias for the /statistics endpoint
    # to match frontend expectations
    return await get_signal_statistics()


@router.get("/statistics")
async def get_signal_statistics(
    # api_key: str = Depends(require_read),
):
    """
    Get overall signal generation and validation statistics.
    """
    generator = get_generator()
    validator = get_validator()
    
    gen_stats = generator.get_statistics()
    val_status = validator.get_status()
    
    # Calculate history stats
    total_history = len(_signal_history)
    approved = sum(1 for s in _signal_history if s.get("status") == "APPROVED")
    rejected = sum(1 for s in _signal_history if s.get("status") == "REJECTED")
    executed = sum(1 for s in _signal_history if s.get("status") == "EXECUTED")
    
    return {
        "generator": gen_stats,
        "validator": val_status["statistics"],
        "signals": {
            "active_count": len(_active_signals),
            "history_count": total_history,
            "approved_count": approved,
            "rejected_count": rejected,
            "executed_count": executed,
            "approval_rate": approved / total_history if total_history > 0 else 0,
            "execution_rate": executed / total_history if total_history > 0 else 0,
        },
        "system": {
            "kill_switch_active": val_status["kill_switch_active"],
            "market_open": val_status["market_open"],
            "daily_trades": val_status["daily_trades_count"],
            "daily_pnl": val_status["daily_pnl"],
        }
    }


@router.get("/health")
async def signals_health():
    """
    Check signals system health.
    """
    generator = get_generator()
    validator = get_validator()
    
    val_status = validator.get_status()
    
    health_status = "healthy"
    warnings = []
    
    if val_status["kill_switch_active"]:
        health_status = "critical"
        warnings.append("Kill switch is active")
    
    if val_status["consecutive_losses"] >= val_status["max_consecutive_losses"] - 1:
        health_status = "warning"
        warnings.append("Near consecutive loss limit")
    
    if val_status["daily_pnl"] <= -(val_status["daily_loss_limit"] * 0.8):
        health_status = "warning"
        warnings.append("Approaching daily loss limit")
    
    return {
        "status": health_status,
        "timestamp": datetime.now().isoformat(),
        "active_signals": len(_active_signals),
        "kill_switch": val_status["kill_switch_active"],
        "market_open": val_status["market_open"],
        "warnings": warnings,
    }
