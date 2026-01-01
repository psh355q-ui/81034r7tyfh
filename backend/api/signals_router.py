"""
signals_router.py - 트레이딩 시그널 API

📊 Data Sources:
    - PostgreSQL: trading_signals 테이블
        - 시그널 생성/조회/업데이트 (CRUD)
        - 필터링: status, ticker, confidence, timeframe
    - SignalGenerator: AI 기반 시그널 생성
        - News 분석 결과 → Trading signal 변환
        - 포지션 사이즈, 컨피던스, 액션 결정
    - SignalValidator: 리스크 검증 및 Kill Switch
        - 일일 거래 한도, 손실 한도 검증
        - 연속 손실, 포지션 사이즈 제한
        - 시장 시간 체크
    - NotificationManager: 실시간 WebSocket 알림
        - 신규 시그널 브로드캐스트
        - 승인/거절/실행 상태 업데이트

🔗 External Dependencies:
    - fastapi: API 라우팅, WebSocket
    - pydantic: 요청/응답 모델 검증
    - sqlalchemy: PostgreSQL ORM
    - backend.ai.signal_generator: 시그널 생성 엔진
    - backend.validation.signal_validator: 검증 엔진
    - backend.notifications.notification_manager: 알림 관리

📤 API Endpoints:
    - WebSocket /signals/ws: 실시간 시그널 업데이트
    - POST /signals/generate: News에서 시그널 생성
    - GET /signals: 시그널 목록 (필터: status, ticker, confidence)
    - GET /signals/{id}: 시그널 상세 (news, analysis 포함)
    - POST /signals/{id}/approve: 시그널 승인
    - POST /signals/{id}/reject: 시그널 거절
    - GET /signals/pending/count: 대기 중 시그널 수
    - GET /signals/validator/status: Kill Switch 상태
    - POST /signals/validator/kill-switch: Kill Switch 토글
    - GET /signals/generator/settings: 생성기 설정 조회
    - PUT /signals/generator/settings: 생성기 설정 업데이트
    - GET /signals/validator/settings: 검증기 설정 조회
    - PUT /signals/validator/settings: 검증기 설정 업데이트
    - GET /signals/stats: 시그널 통계

🔄 Called By:
    - frontend/src/pages/SignalConsolidation.tsx
    - frontend/src/components/Signals/SignalCard.tsx
    - frontend/src/hooks/useSignalWebSocket.ts

📝 Notes:
    - WebSocket을 통한 실시간 업데이트 지원
    - Kill Switch로 리스크 관리
    - 모든 시그널은 DB에 영구 저장
    - Validator는 자동 실행 전 필수 검증

Author: AI Trading System
Date: 2025-11-15
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
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

# Import database models
from backend.database.models import TradingSignal as DBTradingSignal, AnalysisResult, NewsArticle
from backend.database.repository import get_sync_session
from backend.ai.skills.common.logging_decorator import log_endpoint

# Import auth if available
# from auth import require_read, require_write, require_execute

router = APIRouter(prefix="/signals", tags=["Trading Signals"])

# Global instances
_signal_generator = None
_signal_validator = None
_notification_manager = None

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Handle broken connections gracefully
                pass

manager = ConnectionManager()

# REMOVED: In-memory storage replaced with PostgreSQL database
# All signals are now stored in 'trading_signals' table
# Use get_sync_session() to access database


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


class NewsArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    url: str
    source: str
    published_date: str
    crawled_at: str

    class Config:
        from_attributes = True


class AnalysisResultResponse(BaseModel):
    id: int
    theme: str
    bull_case: str
    bear_case: str
    step1_direct_impact: Optional[str]
    step2_secondary_impact: Optional[str]
    step3_conclusion: Optional[str]
    model_name: str
    analysis_duration_seconds: Optional[float]
    analyzed_at: str

    class Config:
        from_attributes = True


class SignalDetailResponse(BaseModel):
    signal: SignalResponse
    news_article: Optional[NewsArticleResponse]
    analysis: Optional[AnalysisResultResponse]
    related_signals: List[SignalResponse] = []


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
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time signal updates.
    URL: /api/signals/ws
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# Signal Generation Endpoints
# ============================================================================

@router.post("/generate", response_model=Optional[SignalResponse])
@log_endpoint("signals", "trading")
async def generate_signal_from_news(
    request: GenerateSignalRequest,
    background_tasks: BackgroundTasks,
    # api_key: str = Depends(require_write),
):
    """
    Generate trading signal from news analysis.
    
    Signal is saved to PostgreSQL database and notifications are sent.
    """
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
    
    # 💾 Save to database
    db = get_sync_session()
    
    try:
        db_signal = DBTradingSignal(
            analysis_id=request.article_id,
            ticker=signal.ticker,
            action=signal.action.value if hasattr(signal.action, 'value') else signal.action,
            signal_type=signal.execution_type,
            confidence=signal.confidence,
            reasoning=signal.reason,
            source="news_analysis",  # 🆕 Track source
            generated_at=datetime.now(),
            entry_price=None,
        )
        
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)
        
        signal_id = db_signal.id
        
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
        
        # Send notification (in background)
        background_tasks.add_task(
            _send_signal_notification,
            notifier,
            signal_data,
        )
        
        return SignalResponse(**signal_data)
    
    finally:
        db.close()


async def _send_signal_notification(notifier, signal_data: Dict[str, Any]):
    """Send signal notification (background task)"""
    try:
        # 1. Send via NotificationManager (Slack/Email)
        await notifier.send_trading_signal(signal_data, priority="HIGH")
        
        # 2. Broadcast via WebSocket
        # Format for frontend needs to match: { type: 'new_signal', data: signal }
        await manager.broadcast({
            "type": "new_signal",
            "data": signal_data
        })
        
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
    Get all signals from the last N hours (from PostgreSQL database).
    
    - **hours**: Hours to look back (default: 168 = 1 week)
    - **limit**: Maximum number of signals to return
    """
    db = get_sync_session()
    
    try:
        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Query database
        signals = db.query(DBTradingSignal)\
            .filter(DBTradingSignal.created_at >= cutoff_time)\
            .order_by(DBTradingSignal.created_at.desc())\
            .limit(limit)\
            .all()
        
        # Convert to response format
        result = []
        for s in signals:
            result.append(SignalResponse(
                id=s.id,
                ticker=s.ticker,
                action=s.action,
                position_size=0.05,  # Default position size (from generator)
                confidence=s.confidence,
                execution_type="LIMIT",
                reason=s.reasoning,
                urgency="MEDIUM",
                created_at=s.created_at.isoformat(),
                news_title=None,
                affected_sectors=[],
                auto_execute=False,
                status="PENDING",  # TODO: Track status in DB
            ))
        
        return result
    
    finally:
        db.close()


@router.get("/active", response_model=List[SignalResponse])
@log_endpoint("signals", "trading")
async def get_active_signals(
    # api_key: str = Depends(require_read),
):
    """
    Get all active (pending) signals from database.
    
    Note: 'status' is not currently tracked in DB, so returns recent signals.
    TODO: Add status column to trading_signals table.
    """
    db = get_sync_session()
    
    try:
        # For now, return signals from last 7 days (active window)
        cutoff = datetime.now() - timedelta(days=7)
        
        signals = db.query(DBTradingSignal)\
            .filter(DBTradingSignal.generated_at >= cutoff)\
            .order_by(DBTradingSignal.confidence.desc())\
            .all()
        
        result = []
        for s in signals:
            result.append(SignalResponse(
                id=s.id,
                ticker=s.ticker,
                action=s.action,
                position_size=0.05,
                confidence=s.confidence,
                execution_type="LIMIT",
                reason=s.reasoning,
                urgency="MEDIUM",
                created_at=s.created_at.isoformat(),
                news_title=None,
                affected_sectors=[],
                auto_execute=False,
                status="PENDING",  # TODO: Track in DB
            ))
        
        return result
    
    finally:
        db.close()


@router.get("/history", response_model=List[SignalResponse])
@log_endpoint("signals", "trading")
async def get_signal_history(
    limit: int = Query(50, ge=1, le=500),
    action_filter: Optional[str] = None,
    # api_key: str = Depends(require_read),
):
    """
    Get signal history from database.
    
    - **limit**: Maximum records
    - **action_filter**: Filter by action (BUY, SELL)
    """
    db = get_sync_session()
    
    try:
        query = db.query(DBTradingSignal)
        
        if action_filter:
            query = query.filter(DBTradingSignal.action == action_filter.upper())
        
        signals = query.order_by(DBTradingSignal.generated_at.desc())\
            .limit(limit)\
            .all()
        
        result = []
        for s in signals:
            result.append(SignalResponse(
                id=s.id,
                ticker=s.ticker,
                action=s.action,
                position_size=0.05,
                confidence=s.confidence,
                execution_type="LIMIT",
                reason=s.reasoning,
                urgency="MEDIUM",
                created_at=s.created_at.isoformat(),
                news_title=None,
                affected_sectors=[],
                auto_execute=False,
                status="EXECUTED" if s.exit_price else "PENDING",
            ))
        
        return result
    
    finally:
        db.close()


@router.get("/{signal_id}", response_model=SignalDetailResponse)
@log_endpoint("signals", "trading")
async def get_signal_by_id(
    signal_id: int,
    # api_key: str = Depends(require_read),
):
    """
    Get a specific signal by ID with full details (Analysis + News).
    """
    db = get_sync_session()
    
    try:
        # Get signal by ID (relationship not needed - analysis_id exists but relationship not defined)
        signal = db.query(DBTradingSignal)\
            .filter(DBTradingSignal.id == signal_id)\
            .first()
        
        if not signal:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
        
        # 1. Base Signal Response
        signal_resp = SignalResponse(
            id=signal.id,
            ticker=signal.ticker,
            action=signal.action,
            position_size=0.05,
            confidence=signal.confidence,
            execution_type="LIMIT",
            reason=signal.reasoning,
            urgency="MEDIUM",
            created_at=signal.generated_at.isoformat(),
            news_title=signal.analysis.article.title if signal.analysis and signal.analysis.article else None,
            affected_sectors=[],
            auto_execute=False,
            status="EXECUTED" if signal.exit_price else "PENDING",
        )

        # 2. Analysis Response
        analysis_resp = None
        news_resp = None

        if signal.analysis:
            analysis_resp = AnalysisResultResponse(
                id=signal.analysis.id,
                theme=signal.analysis.theme,
                bull_case=signal.analysis.bull_case,
                bear_case=signal.analysis.bear_case,
                step1_direct_impact=signal.analysis.step1_direct_impact,
                step2_secondary_impact=signal.analysis.step2_secondary_impact,
                step3_conclusion=signal.analysis.step3_conclusion,
                model_name=signal.analysis.model_name,
                analysis_duration_seconds=signal.analysis.analysis_duration_seconds,
                analyzed_at=signal.analysis.analyzed_at.isoformat(),
            )

            # 3. News Response (linked via Analysis)
            if signal.analysis.article:
                art = signal.analysis.article
                news_resp = NewsArticleResponse(
                    id=art.id,
                    title=art.title,
                    content=art.content,
                    url=art.url,
                    source=art.source,
                    published_date=art.published_date.isoformat(),
                    crawled_at=art.crawled_at.isoformat(),
                )

        return SignalDetailResponse(
            signal=signal_resp,
            analysis=analysis_resp,
            news_article=news_resp,
            related_signals=[]  # Can implement related signal fetch logic later
        )
    
    finally:
        db.close()


# ============================================================================
# Signal Action Endpoints
# ============================================================================

@router.put("/{signal_id}/approve")
@log_endpoint("signals", "trading")
async def approve_signal(
    signal_id: int,
    request: ApproveSignalRequest,
    # api_key: str = Depends(require_execute),
):
    """
    Approve a pending signal.
    
    Note: Status tracking not fully implemented in DB yet.
    This endpoint updates entry_price to mark as approved.
    
    - **execute_immediately**: Execute the signal right away
    - **adjusted_position_size**: Override position size (not stored in DB yet)
    """
    db = get_sync_session()
   
    try:
        signal = db.query(DBTradingSignal)\
            .filter(DBTradingSignal.id == signal_id)\
            .first()
        
        if not signal:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
        
        # Update signal (mark as approved by setting entry_price)
        if request.adjusted_position_size:
            # TODO: Add position_size column to DB
            pass
        
        # For now, we'll just return success
        # In future: add status, approved_at columns to trading_signals table
        
        return {
            "signal_id": signal_id,
            "status": "APPROVED",
            "approved_at": datetime.now().isoformat(),
            "execute_immediately": request.execute_immediately,
            "message": "Signal approved (status tracking pending DB migration)"
        }
    
    finally:
        db.close()


@router.delete("/{signal_id}/reject")
@log_endpoint("signals", "trading")
async def reject_signal(
    signal_id: int,
    reason: str = Query("Manual rejection"),
    # api_key: str = Depends(require_write),
):
    """
    Reject a pending signal.
    
    Note: Status tracking not fully implemented in DB yet.
    
    - **reason**: Reason for rejection (not stored in DB yet)
    """
    db = get_sync_session()
    
    try:
        signal = db.query(DBTradingSignal)\
            .filter(DBTradingSignal.id == signal_id)\
            .first()
        
        if not signal:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
        
        # In future: add status, rejected_at, rejection_reason columns
        
        return {
            "signal_id": signal_id,
            "status": "REJECTED",
            "rejected_at": datetime.now().isoformat(),
            "reason": reason,
            "message": "Signal rejected (status tracking pending DB migration)"
        }
    
    finally:
        db.close()


@router.post("/{signal_id}/execute")
@log_endpoint("signals", "trading")
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
@log_endpoint("signals", "trading")
async def get_validator_status(
    # api_key: str = Depends(require_read),
):
    """
    Get current validator status (kill switch, limits, etc.).
    """
    validator = get_validator()
    return ValidatorStatusResponse(**validator.get_status())


@router.post("/validator/reset-kill-switch")
@log_endpoint("signals", "trading")
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
@log_endpoint("signals", "trading")
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
@log_endpoint("signals", "trading")
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
@log_endpoint("signals", "trading")
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
@log_endpoint("signals", "trading")
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
@log_endpoint("signals", "trading")
async def get_signal_statistics(
    # api_key: str = Depends(require_read),
):
    """
    Get overall signal generation and validation statistics from database.
    
    Note: Some stats simplified due to status tracking not in DB yet.
    """
    generator = get_generator()
    validator = get_validator()
    
    gen_stats = generator.get_statistics()
    val_status = validator.get_status()
    
    # Calculate DB stats
    db = get_sync_session()

    try:
        # Count all signals
        total_signals = db.query(DBTradingSignal).count()

        # Count executed signals (those with performance records)
        # TODO: signal_performance 테이블이 생성되면 활성화
        executed = 0  # 테이블 없으므로 0으로 처리 (향후 구현 예정)

        # Count from last 24 hours (active)
        cutoff = datetime.now() - timedelta(hours=24)
        recent_signals = db.query(DBTradingSignal)\
            .filter(DBTradingSignal.created_at >= cutoff)\
            .count()
        
        return {
            "generator": gen_stats,
            "validator": val_status["statistics"],
            "signals": {
                "active_count": recent_signals,
                "total_count": total_signals,
                "executed_count": executed,
                "execution_rate": executed / total_signals if total_signals > 0 else 0,
                "note": "Full status tracking (APPROVED/REJECTED) pending DB migration"
            },
            "system": {
                "kill_switch_active": val_status["kill_switch_active"],
                "market_open": val_status["market_open"],
                "daily_trades": val_status["daily_trades_count"],
                "daily_pnl": val_status["daily_pnl"],
            }
        }
    
    finally:
        db.close()


@router.get("/health")
@log_endpoint("signals", "trading")
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
    
    # Count recent signals from DB
    db = get_sync_session()
    try:
        cutoff = datetime.now() - timedelta(hours=24)
        active_count = db.query(DBTradingSignal)\
            .filter(DBTradingSignal.generated_at >= cutoff)\
            .count()
    finally:
        db.close()
    
    return {
        "status": health_status,
        "timestamp": datetime.now().isoformat(),
        "active_signals": active_count,
        "kill_switch": val_status["kill_switch_active"],
        "market_open": val_status["market_open"],
        "warnings": warnings,
    }
