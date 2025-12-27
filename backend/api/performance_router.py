"""
Performance API Router

Phase 25.2: Agent Performance Tracking
Date: 2025-12-23

API Endpoints:
- GET /api/performance/summary - Overall performance summary
- GET /api/performance/by-action - Performance by action (BUY/SELL/HOLD)
- GET /api/performance/history - Daily performance trend
- GET /api/performance/top-sessions - Best/worst performing sessions
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from backend.database.repository import get_sync_session
from sqlalchemy import text
from backend.ai.learning.agent_weight_manager import AgentWeightManager
from backend.ai.learning.alert_system import AgentAlertSystem
from backend.ai.skills.common.logging_decorator import log_endpoint

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/performance", tags=["performance"])


# ============================================================================
# Response Models
# ============================================================================

class PerformanceSummary(BaseModel):
    """Overall performance summary"""
    total_predictions: int
    correct_predictions: int
    accuracy: float
    avg_return: float
    avg_performance_score: float
    best_action: Optional[str] = None


class ActionPerformance(BaseModel):
    """Performance by action type"""
    action: str
    total: int
    correct: int
    accuracy: float
    avg_return: float
    avg_performance_score: float


class DailyPerformance(BaseModel):
    """Daily performance metrics"""
    date: str
    total: int
    correct: int
    accuracy: float
    avg_return: float


class SessionPerformance(BaseModel):
    """Individual session performance"""
    session_id: int
    ticker: str
    consensus_action: str
    consensus_confidence: float
    return_pct: float
    is_correct: bool
    performance_score: float
    initial_timestamp: str


class AgentPerformance(BaseModel):
    """Agent-specific performance metrics"""
    agent_name: str
    total_votes: int
    correct_votes: int
    accuracy: float
    avg_return: float
    avg_performance_score: float


class AgentActionPerformance(BaseModel):
    """Agent performance by action type"""
    agent_name: str
    action: str
    total: int
    correct: int
    accuracy: float
    avg_return: float
    avg_performance_score: float


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/summary", response_model=PerformanceSummary)
@log_endpoint("performance", "system")
async def get_performance_summary():
    """
    Get overall performance summary

    Returns:
        Overall accuracy, average return, and best performing action
    """
    db = get_sync_session()

    try:
        # Query overall performance metrics
        query = text("""
            SELECT
                COUNT(*) as total_predictions,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_predictions,
                ROUND(
                    CAST(SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS NUMERIC) /
                    NULLIF(COUNT(*), 0) * 100,
                    2
                ) as accuracy,
                ROUND(AVG(return_pct), 4) as avg_return,
                ROUND(AVG(performance_score), 4) as avg_performance_score
            FROM price_tracking
            WHERE status = 'COMPLETED'
        """)

        result = db.execute(query).fetchone()

        if not result or result.total_predictions == 0:
            # No data yet - return zeros
            return PerformanceSummary(
                total_predictions=0,
                correct_predictions=0,
                accuracy=0.0,
                avg_return=0.0,
                avg_performance_score=0.0,
                best_action=None
            )

        # Find best performing action
        action_query = text("""
            SELECT
                consensus_action,
                ROUND(
                    CAST(SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS NUMERIC) /
                    NULLIF(COUNT(*), 0) * 100,
                    2
                ) as accuracy
            FROM price_tracking
            WHERE status = 'COMPLETED'
            GROUP BY consensus_action
            ORDER BY accuracy DESC
            LIMIT 1
        """)

        best_action_result = db.execute(action_query).fetchone()
        best_action = best_action_result.consensus_action if best_action_result else None

        logger.info(f"📊 Performance summary fetched: {result.total_predictions} predictions, {result.accuracy}% accuracy")

        return PerformanceSummary(
            total_predictions=result.total_predictions,
            correct_predictions=result.correct_predictions,
            accuracy=float(result.accuracy) if result.accuracy else 0.0,
            avg_return=float(result.avg_return) if result.avg_return else 0.0,
            avg_performance_score=float(result.avg_performance_score) if result.avg_performance_score else 0.0,
            best_action=best_action
        )

    except Exception as e:
        logger.error(f"❌ Failed to fetch performance summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance summary: {str(e)}")

    finally:
        db.close()


@router.get("/by-action", response_model=List[ActionPerformance])
@log_endpoint("performance", "system")
async def get_performance_by_action():
    """
    Get performance metrics grouped by action (BUY/SELL/HOLD)

    Returns:
        Performance breakdown by action type
    """
    db = get_sync_session()

    try:
        query = text("""
            SELECT
                consensus_action as action,
                COUNT(*) as total,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
                ROUND(
                    CAST(SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS NUMERIC) /
                    NULLIF(COUNT(*), 0) * 100,
                    2
                ) as accuracy,
                ROUND(AVG(return_pct), 4) as avg_return,
                ROUND(AVG(performance_score), 4) as avg_performance_score
            FROM price_tracking
            WHERE status = 'COMPLETED'
            GROUP BY consensus_action
            ORDER BY accuracy DESC
        """)

        results = db.execute(query).fetchall()

        if not results:
            # No data yet - return empty list
            return []

        performance_list = []
        for row in results:
            performance_list.append(ActionPerformance(
                action=row.action,
                total=row.total,
                correct=row.correct,
                accuracy=float(row.accuracy) if row.accuracy else 0.0,
                avg_return=float(row.avg_return) if row.avg_return else 0.0,
                avg_performance_score=float(row.avg_performance_score) if row.avg_performance_score else 0.0
            ))

        logger.info(f"📊 Fetched performance for {len(performance_list)} action types")

        return performance_list

    except Exception as e:
        logger.error(f"❌ Failed to fetch performance by action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance by action: {str(e)}")

    finally:
        db.close()


@router.get("/history", response_model=List[DailyPerformance])
@log_endpoint("performance", "system")
async def get_performance_history(
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch")
):
    """
    Get daily performance trend

    Args:
        days: Number of days to fetch (default 30)

    Returns:
        Daily performance metrics
    """
    db = get_sync_session()

    try:
        query = text("""
            SELECT
                DATE(evaluated_at) as date,
                COUNT(*) as total,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
                ROUND(
                    CAST(SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS NUMERIC) /
                    NULLIF(COUNT(*), 0) * 100,
                    2
                ) as accuracy,
                ROUND(AVG(return_pct), 4) as avg_return
            FROM price_tracking
            WHERE status = 'COMPLETED'
                AND evaluated_at >= CURRENT_DATE - INTERVAL ':days days'
            GROUP BY DATE(evaluated_at)
            ORDER BY date DESC
        """)

        results = db.execute(query, {"days": days}).fetchall()

        if not results:
            # No data yet - return empty list
            return []

        history = []
        for row in results:
            history.append(DailyPerformance(
                date=row.date.isoformat(),
                total=row.total,
                correct=row.correct,
                accuracy=float(row.accuracy) if row.accuracy else 0.0,
                avg_return=float(row.avg_return) if row.avg_return else 0.0
            ))

        logger.info(f"📊 Fetched {len(history)} days of performance history")

        return history

    except Exception as e:
        logger.error(f"❌ Failed to fetch performance history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance history: {str(e)}")

    finally:
        db.close()


@router.get("/top-sessions", response_model=List[SessionPerformance])
@log_endpoint("performance", "system")
async def get_top_sessions(
    order: str = Query("best", pattern="^(best|worst)$", description="Sort order (best or worst)"),
    limit: int = Query(10, ge=1, le=50, description="Number of sessions to return")
):
    """
    Get best/worst performing sessions

    Args:
        order: Sort order - "best" for highest scores, "worst" for lowest
        limit: Number of sessions to return

    Returns:
        List of top/bottom performing sessions
    """
    db = get_sync_session()

    try:
        order_clause = "DESC" if order == "best" else "ASC"

        query = text(f"""
            SELECT
                session_id,
                ticker,
                consensus_action,
                consensus_confidence,
                return_pct,
                is_correct,
                performance_score,
                initial_timestamp
            FROM price_tracking
            WHERE status = 'COMPLETED'
            ORDER BY performance_score {order_clause}
            LIMIT :limit
        """)

        results = db.execute(query, {"limit": limit}).fetchall()

        if not results:
            # No data yet - return empty list
            return []

        sessions = []
        for row in results:
            sessions.append(SessionPerformance(
                session_id=row.session_id,
                ticker=row.ticker,
                consensus_action=row.consensus_action,
                consensus_confidence=float(row.consensus_confidence),
                return_pct=float(row.return_pct) if row.return_pct else 0.0,
                is_correct=row.is_correct,
                performance_score=float(row.performance_score) if row.performance_score else 0.0,
                initial_timestamp=row.initial_timestamp.isoformat() if row.initial_timestamp else ""
            ))

        logger.info(f"📊 Fetched top {len(sessions)} {order} performing sessions")

        return sessions

    except Exception as e:
        logger.error(f"❌ Failed to fetch top sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch top sessions: {str(e)}")

    finally:
        db.close()


@router.get("/by-agent", response_model=List[AgentPerformance])
@log_endpoint("performance", "system")
async def get_performance_by_agent():
    """
    Get performance metrics grouped by agent

    Phase 25.3: Agent-specific performance tracking

    Returns:
        Performance breakdown by agent (trader, analyst, risk, etc.)
    """
    db = get_sync_session()

    try:
        query = text("""
            SELECT
                agent_name,
                COUNT(*) as total_votes,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_votes,
                ROUND(
                    CAST(SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS NUMERIC) /
                    NULLIF(COUNT(*), 0) * 100,
                    2
                ) as accuracy,
                ROUND(AVG(return_pct), 4) as avg_return,
                ROUND(AVG(performance_score), 4) as avg_performance_score
            FROM agent_vote_tracking
            WHERE status = 'COMPLETED'
            GROUP BY agent_name
            ORDER BY accuracy DESC
        """)

        results = db.execute(query).fetchall()

        if not results:
            # No data yet - return empty list
            return []

        agent_performance = []
        for row in results:
            agent_performance.append(AgentPerformance(
                agent_name=row.agent_name,
                total_votes=row.total_votes,
                correct_votes=row.correct_votes,
                accuracy=float(row.accuracy) if row.accuracy else 0.0,
                avg_return=float(row.avg_return) if row.avg_return else 0.0,
                avg_performance_score=float(row.avg_performance_score) if row.avg_performance_score else 0.0
            ))

        logger.info(f"📊 Fetched performance for {len(agent_performance)} agents")

        return agent_performance

    except Exception as e:
        logger.error(f"❌ Failed to fetch agent performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch agent performance: {str(e)}")

    finally:
        db.close()


@router.get("/by-agent-action", response_model=List[AgentActionPerformance])
@log_endpoint("performance", "system")
async def get_performance_by_agent_action(
    agent: Optional[str] = Query(None, description="Filter by specific agent")
):
    """
    Get performance metrics grouped by agent and action

    Phase 25.3: Agent-specific performance by action type

    Args:
        agent: Optional agent name filter

    Returns:
        Performance breakdown by agent and action (BUY/SELL/HOLD)
    """
    db = get_sync_session()

    try:
        # Build query with optional agent filter
        where_clause = "WHERE status = 'COMPLETED'"
        if agent:
            where_clause += f" AND agent_name = :agent"

        query = text(f"""
            SELECT
                agent_name,
                vote_action as action,
                COUNT(*) as total,
                SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
                ROUND(
                    CAST(SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS NUMERIC) /
                    NULLIF(COUNT(*), 0) * 100,
                    2
                ) as accuracy,
                ROUND(AVG(return_pct), 4) as avg_return,
                ROUND(AVG(performance_score), 4) as avg_performance_score
            FROM agent_vote_tracking
            {where_clause}
            GROUP BY agent_name, vote_action
            ORDER BY agent_name, accuracy DESC
        """)

        params = {"agent": agent} if agent else {}
        results = db.execute(query, params).fetchall()

        if not results:
            # No data yet - return empty list
            return []

        agent_action_performance = []
        for row in results:
            agent_action_performance.append(AgentActionPerformance(
                agent_name=row.agent_name,
                action=row.action,
                total=row.total,
                correct=row.correct,
                accuracy=float(row.accuracy) if row.accuracy else 0.0,
                avg_return=float(row.avg_return) if row.avg_return else 0.0,
                avg_performance_score=float(row.avg_performance_score) if row.avg_performance_score else 0.0
            ))

        logger.info(f"📊 Fetched {len(agent_action_performance)} agent-action performance records")

        return agent_action_performance

    except Exception as e:
        logger.error(f"❌ Failed to fetch agent-action performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch agent-action performance: {str(e)}")

    finally:
        db.close()


@router.post("/calculate-weights")
@log_endpoint("performance", "system")
async def calculate_agent_weights(lookback_days: int = Query(30, ge=1, le=365)):
    """
    Calculate new agent weights based on performance

    Phase 25.4: Self-Learning Feedback Loop

    Args:
        lookback_days: Days to look back for performance data (default 30)

    Returns:
        Weight calculation results and alerts
    """
    db = get_sync_session()

    try:
        logger.info(f"🔄 Starting agent weight calculation (lookback={lookback_days} days)")

        # Calculate weights
        manager = AgentWeightManager(db)
        weights_info = manager.calculate_agent_weights(lookback_days)

        # Detect issues
        low_performers = manager.detect_low_performers(threshold=0.50, lookback_days=lookback_days)
        overconfident = manager.detect_overconfident_agents(gap_threshold=0.20, lookback_days=lookback_days)

        # Send alerts
        alert_system = AgentAlertSystem()
        alerts = alert_system.check_and_send_alerts(low_performers, overconfident)

        logger.info(f"✅ Weight calculation complete: {len(weights_info)} agents, {len(alerts)} alerts")

        return {
            "status": "success",
            "lookback_days": lookback_days,
            "weights": weights_info,
            "low_performers": low_performers,
            "overconfident_agents": overconfident,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Failed to calculate weights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate weights: {str(e)}")

    finally:
        db.close()


@router.get("/agent-weights")
@log_endpoint("performance", "system")
async def get_agent_weights():
    """
    Get current agent weights

    Phase 25.4: Self-Learning Feedback Loop

    Returns:
        Current agent weights
    """
    db = get_sync_session()

    try:
        manager = AgentWeightManager(db)
        weights = manager.get_current_weights()

        logger.info(f"📊 Retrieved current agent weights")

        return {
            "status": "success",
            "weights": weights,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Failed to get agent weights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get agent weights: {str(e)}")

    finally:
        db.close()


@router.get("/low-performers")
@log_endpoint("performance", "system")
async def get_low_performers(
    threshold: float = Query(0.50, ge=0.0, le=1.0),
    lookback_days: int = Query(30, ge=1, le=365)
):
    """
    Get list of low-performing agents

    Phase 25.4: Self-Learning Feedback Loop

    Args:
        threshold: Accuracy threshold (default 0.50 = 50%)
        lookback_days: Days to look back (default 30)

    Returns:
        List of low-performing agents
    """
    db = get_sync_session()

    try:
        manager = AgentWeightManager(db)
        low_performers = manager.detect_low_performers(threshold, lookback_days)

        logger.info(f"📊 Found {len(low_performers)} low performers")

        return {
            "status": "success",
            "threshold": threshold,
            "lookback_days": lookback_days,
            "low_performers": low_performers,
            "count": len(low_performers),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Failed to get low performers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get low performers: {str(e)}")

    finally:
        db.close()


@router.get("/overconfident-agents")
@log_endpoint("performance", "system")
async def get_overconfident_agents(
    gap_threshold: float = Query(0.20, ge=0.0, le=1.0),
    lookback_days: int = Query(30, ge=1, le=365)
):
    """
    Get list of overconfident agents

    Phase 25.4: Self-Learning Feedback Loop

    Args:
        gap_threshold: Confidence gap threshold (default 0.20 = 20%)
        lookback_days: Days to look back (default 30)

    Returns:
        List of overconfident agents
    """
    db = get_sync_session()

    try:
        manager = AgentWeightManager(db)
        overconfident = manager.detect_overconfident_agents(gap_threshold, lookback_days)

        logger.info(f"📊 Found {len(overconfident)} overconfident agents")

        return {
            "status": "success",
            "gap_threshold": gap_threshold,
            "lookback_days": lookback_days,
            "overconfident_agents": overconfident,
            "count": len(overconfident),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Failed to get overconfident agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get overconfident agents: {str(e)}")

    finally:
        db.close()
