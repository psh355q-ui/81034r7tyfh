"""
AI Quality API Router - Endpoints for AI analysis quality monitoring

Provides:
- Signal accuracy tracking
- Ensemble weight optimization
- Adaptive strategy management
- Performance attribution
- Validation reports

Author: AI Trading System Team
Date: 2025-11-24
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-quality", tags=["AI Quality"])


# =============================================================================
# Request/Response Models
# =============================================================================

class SignalRecordRequest(BaseModel):
    ticker: str
    signal: str  # BUY/SELL/HOLD
    confidence: float
    source: str  # claude/gemini/ensemble
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    time_horizon_days: int = 5
    rag_documents_used: int = 0
    rag_relevance_score: float = 0.0
    entry_price: Optional[float] = None
    metadata: Optional[Dict] = None


class AccuracyMetricsResponse(BaseModel):
    total_signals: int
    resolved_signals: int
    win_count: int
    loss_count: int
    neutral_count: int
    win_rate: float
    avg_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    avg_confidence: float
    confidence_correlation: float
    buy_accuracy: float
    sell_accuracy: float
    avg_days_to_resolution: float


class EnsembleWeightsResponse(BaseModel):
    claude_weight: float
    gemini_weight: float
    chatgpt_weight: float
    bull_multiplier: float
    bear_multiplier: float
    sideways_multiplier: float
    performance_score: float
    last_updated: Optional[str]


class StrategyConfigResponse(BaseModel):
    name: str
    max_position_size_pct: float
    max_portfolio_positions: int
    stop_loss_pct: float
    take_profit_pct: float
    min_confidence: float
    target_regime: str
    description: str


# =============================================================================
# Global Instances (initialized in main.py)
# =============================================================================

analysis_validator = None
ensemble_optimizer = None
adaptive_strategy_manager = None


def set_ai_quality_instances(validator, optimizer, strategy_mgr):
    """Set global instances (called from main.py)."""
    global analysis_validator, ensemble_optimizer, adaptive_strategy_manager
    analysis_validator = validator
    ensemble_optimizer = optimizer
    adaptive_strategy_manager = strategy_mgr


# =============================================================================
# Signal Validation Endpoints
# =============================================================================

@router.post("/signals/record")
async def record_signal(request: SignalRecordRequest):
    """
    Record an AI-generated signal for later validation.

    Returns:
        signal_id for tracking
    """
    if not analysis_validator:
        raise HTTPException(status_code=503, detail="Analysis validator not initialized")

    metadata = request.metadata or {}
    if request.entry_price:
        metadata["entry_price"] = request.entry_price

    signal_id = await analysis_validator.record_signal(
        ticker=request.ticker,
        signal=request.signal,
        confidence=request.confidence,
        source=request.source,
        target_price=request.target_price,
        stop_loss=request.stop_loss,
        time_horizon_days=request.time_horizon_days,
        rag_documents_used=request.rag_documents_used,
        rag_relevance_score=request.rag_relevance_score,
        metadata=metadata,
    )

    return {
        "success": True,
        "signal_id": signal_id,
        "message": "Signal recorded for validation",
    }


@router.post("/signals/update-outcomes")
async def update_signal_outcomes(current_prices: Optional[Dict[str, float]] = None):
    """
    Update outcomes for pending signals.

    Should be run daily after market close.
    """
    if not analysis_validator:
        raise HTTPException(status_code=503, detail="Analysis validator not initialized")

    await analysis_validator.update_outcomes(current_prices=current_prices)

    return {
        "success": True,
        "message": "Signal outcomes updated",
    }


@router.get("/signals/accuracy", response_model=AccuracyMetricsResponse)
async def get_signal_accuracy(
    source: Optional[str] = Query(None, description="Filter by AI source"),
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    lookback_days: int = Query(30, description="Days to analyze"),
    min_confidence: Optional[float] = Query(None, description="Min confidence threshold"),
):
    """
    Get signal accuracy metrics.
    """
    if not analysis_validator:
        raise HTTPException(status_code=503, detail="Analysis validator not initialized")

    metrics = await analysis_validator.get_accuracy_metrics(
        source=source,
        ticker=ticker,
        lookback_days=lookback_days,
        min_confidence=min_confidence,
    )

    return metrics


@router.get("/signals/confidence-calibration")
async def get_confidence_calibration(
    source: Optional[str] = Query(None),
    lookback_days: int = Query(90),
):
    """
    Get confidence calibration analysis.

    Shows whether AI confidence correlates with actual outcomes.
    """
    if not analysis_validator:
        raise HTTPException(status_code=503, detail="Analysis validator not initialized")

    calibration = analysis_validator.get_confidence_calibration(
        source=source,
        lookback_days=lookback_days,
    )

    return calibration


@router.get("/signals/rag-impact")
async def get_rag_impact_analysis(lookback_days: int = Query(90)):
    """
    Analyze impact of RAG on signal quality.

    Compares signals with vs without RAG context.
    """
    if not analysis_validator:
        raise HTTPException(status_code=503, detail="Analysis validator not initialized")

    impact = analysis_validator.get_rag_impact_analysis(lookback_days=lookback_days)

    return impact


@router.get("/signals/source-comparison")
async def get_source_comparison(lookback_days: int = Query(90)):
    """
    Compare performance across AI sources (Claude, Gemini, ChatGPT, Ensemble).
    """
    if not analysis_validator:
        raise HTTPException(status_code=503, detail="Analysis validator not initialized")

    comparison = analysis_validator.get_source_comparison(lookback_days=lookback_days)

    # Convert AccuracyMetrics to dict
    return {
        source: {
            "total_signals": metrics.total_signals,
            "resolved_signals": metrics.resolved_signals,
            "win_rate": metrics.win_rate,
            "avg_return_pct": metrics.avg_return_pct,
            "sharpe_ratio": metrics.sharpe_ratio,
            "avg_confidence": metrics.avg_confidence,
        }
        for source, metrics in comparison.items()
    }


@router.get("/signals/summary-report")
async def get_summary_report(lookback_days: int = Query(30)):
    """
    Get comprehensive signal validation summary report.
    """
    if not analysis_validator:
        raise HTTPException(status_code=503, detail="Analysis validator not initialized")

    report = analysis_validator.get_summary_report(lookback_days=lookback_days)

    return report


# =============================================================================
# Ensemble Optimization Endpoints
# =============================================================================

@router.get("/ensemble/weights", response_model=EnsembleWeightsResponse)
async def get_ensemble_weights():
    """
    Get current ensemble weights.
    """
    if not ensemble_optimizer:
        raise HTTPException(status_code=503, detail="Ensemble optimizer not initialized")

    weights = ensemble_optimizer.current_weights

    return EnsembleWeightsResponse(
        claude_weight=weights.claude_weight,
        gemini_weight=weights.gemini_weight,
        chatgpt_weight=weights.chatgpt_weight,
        bull_multiplier=weights.bull_multiplier,
        bear_multiplier=weights.bear_multiplier,
        sideways_multiplier=weights.sideways_multiplier,
        performance_score=weights.performance_score,
        last_updated=weights.last_updated.isoformat() if weights.last_updated else None,
    )


@router.post("/ensemble/optimize")
async def optimize_ensemble_weights(
    lookback_days: int = Query(90),
    objective: str = Query("sharpe", description="Optimization objective: sharpe/win_rate/total_return"),
    method: str = Query("bayesian", description="Optimization method: bayesian/grid/gradient"),
):
    """
    Optimize ensemble weights based on historical performance.

    This may take a few seconds.
    """
    if not ensemble_optimizer:
        raise HTTPException(status_code=503, detail="Ensemble optimizer not initialized")

    optimized_weights = await ensemble_optimizer.optimize_weights(
        lookback_days=lookback_days,
        objective=objective,
        method=method,
    )

    return {
        "success": True,
        "weights": {
            "claude": optimized_weights.claude_weight,
            "gemini": optimized_weights.gemini_weight,
            "chatgpt": optimized_weights.chatgpt_weight,
        },
        "performance_score": optimized_weights.performance_score,
        "method": method,
        "objective": objective,
    }


@router.get("/ensemble/optimization-report")
async def get_optimization_report():
    """
    Get ensemble optimization summary report.
    """
    if not ensemble_optimizer:
        raise HTTPException(status_code=503, detail="Ensemble optimizer not initialized")

    report = ensemble_optimizer.get_optimization_report()

    return report


# =============================================================================
# Adaptive Strategy Endpoints
# =============================================================================

@router.get("/strategy/current", response_model=StrategyConfigResponse)
async def get_current_strategy():
    """
    Get current active strategy configuration.
    """
    if not adaptive_strategy_manager:
        raise HTTPException(status_code=503, detail="Adaptive strategy manager not initialized")

    strategy = adaptive_strategy_manager.get_current_strategy()

    if not strategy:
        raise HTTPException(status_code=404, detail="No active strategy")

    return StrategyConfigResponse(
        name=strategy.name,
        max_position_size_pct=strategy.max_position_size_pct,
        max_portfolio_positions=strategy.max_portfolio_positions,
        stop_loss_pct=strategy.stop_loss_pct,
        take_profit_pct=strategy.take_profit_pct,
        min_confidence=strategy.min_confidence,
        target_regime=strategy.target_regime.value,
        description=strategy.description,
    )


@router.post("/strategy/update")
async def update_strategy(force: bool = Query(False)):
    """
    Update strategy based on current market regime.

    Args:
        force: Force update even within cooldown period
    """
    if not adaptive_strategy_manager:
        raise HTTPException(status_code=503, detail="Adaptive strategy manager not initialized")

    new_strategy = await adaptive_strategy_manager.update_strategy(force=force)

    if new_strategy:
        return {
            "success": True,
            "strategy_changed": True,
            "new_strategy": new_strategy.name,
            "regime": adaptive_strategy_manager.current_regime.value,
            "confidence": adaptive_strategy_manager.regime_confidence,
        }
    else:
        return {
            "success": True,
            "strategy_changed": False,
            "current_strategy": (
                adaptive_strategy_manager.current_strategy.name
                if adaptive_strategy_manager.current_strategy
                else None
            ),
            "current_regime": adaptive_strategy_manager.current_regime.value,
        }


@router.get("/strategy/position-size")
async def calculate_position_size(
    ticker: str,
    signal_confidence: float,
    portfolio_value: float,
):
    """
    Calculate position size based on current strategy.
    """
    if not adaptive_strategy_manager:
        raise HTTPException(status_code=503, detail="Adaptive strategy manager not initialized")

    position_size = adaptive_strategy_manager.get_position_size(
        ticker=ticker,
        signal_confidence=signal_confidence,
        portfolio_value=portfolio_value,
    )

    return {
        "ticker": ticker,
        "position_size_usd": position_size,
        "signal_confidence": signal_confidence,
        "portfolio_value": portfolio_value,
        "position_size_pct": (position_size / portfolio_value) * 100,
        "strategy": adaptive_strategy_manager.current_strategy.name if adaptive_strategy_manager.current_strategy else None,
    }


@router.post("/strategy/validate-signal")
async def validate_signal(
    signal: str,
    confidence: float,
    sharpe_ratio: Optional[float] = None,
):
    """
    Check if signal meets current strategy criteria.
    """
    if not adaptive_strategy_manager:
        raise HTTPException(status_code=503, detail="Adaptive strategy manager not initialized")

    should_take, reason = adaptive_strategy_manager.should_take_signal(
        signal=signal,
        confidence=confidence,
        sharpe_ratio=sharpe_ratio,
    )

    return {
        "should_take": should_take,
        "reason": reason,
        "signal": signal,
        "confidence": confidence,
        "current_strategy": (
            adaptive_strategy_manager.current_strategy.name
            if adaptive_strategy_manager.current_strategy
            else None
        ),
    }


@router.get("/strategy/status")
async def get_strategy_status():
    """
    Get adaptive strategy manager status.
    """
    if not adaptive_strategy_manager:
        raise HTTPException(status_code=503, detail="Adaptive strategy manager not initialized")

    status = adaptive_strategy_manager.get_status_report()

    return status


# =============================================================================
# Combined Analysis Endpoint
# =============================================================================

@router.get("/dashboard")
async def get_ai_quality_dashboard():
    """
    Get comprehensive AI quality dashboard data.

    Combines signal accuracy, ensemble weights, and strategy status.
    """
    dashboard = {
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Signal accuracy
    if analysis_validator:
        try:
            accuracy = await analysis_validator.get_accuracy_metrics(lookback_days=30)
            dashboard["signal_accuracy"] = {
                "win_rate": accuracy.win_rate,
                "avg_return_pct": accuracy.avg_return_pct,
                "sharpe_ratio": accuracy.sharpe_ratio,
                "resolved_signals": accuracy.resolved_signals,
            }

            rag_impact = analysis_validator.get_rag_impact_analysis(lookback_days=30)
            dashboard["rag_impact"] = rag_impact
        except Exception as e:
            logger.error(f"Error getting signal accuracy: {e}")
            dashboard["signal_accuracy"] = {"error": str(e)}

    # Ensemble weights
    if ensemble_optimizer:
        try:
            dashboard["ensemble"] = ensemble_optimizer.get_optimization_report()
        except Exception as e:
            logger.error(f"Error getting ensemble report: {e}")
            dashboard["ensemble"] = {"error": str(e)}

    # Strategy status
    if adaptive_strategy_manager:
        try:
            dashboard["strategy"] = adaptive_strategy_manager.get_status_report()
        except Exception as e:
            logger.error(f"Error getting strategy status: {e}")
            dashboard["strategy"] = {"error": str(e)}

    return dashboard
