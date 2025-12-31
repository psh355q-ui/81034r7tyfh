"""
Accountability API Router

Phase 29: Accountability System
Date: 2025-12-30

API Endpoints:
- GET /api/accountability/status - Scheduler status
- GET /api/accountability/nia - News Interpretation Accuracy score
- GET /api/accountability/interpretations - List news interpretations with accuracy
- GET /api/accountability/failed - List failed interpretations for review
- POST /api/accountability/run - Manually trigger verification
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from backend.database.repository import get_sync_session
from sqlalchemy import text, func, and_
from backend.database.models import NewsInterpretation, NewsMarketReaction
from backend.ai.skills.common.logging_decorator import log_endpoint

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/accountability", tags=["accountability"])


# ============================================================================
# Response Models
# ============================================================================

class SchedulerStatus(BaseModel):
    """Accountability Scheduler status"""
    is_running: bool
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_interval_minutes: int
    total_verifications_today: int


class NIAScore(BaseModel):
    """News Interpretation Accuracy score"""
    overall_nia: float
    total_interpretations: int
    verified_interpretations: int
    pending_interpretations: int
    nia_by_time_horizon: dict  # {"1h": 0.75, "1d": 0.82, "3d": 0.68}
    nia_by_impact: dict  # {"HIGH": 0.80, "MEDIUM": 0.65, "LOW": 0.50}


class InterpretationItem(BaseModel):
    """News interpretation with accuracy"""
    id: int
    ticker: str
    headline_bias: str
    expected_impact: str
    time_horizon: str
    confidence: int
    reasoning: str
    interpreted_at: str
    accuracy_1h: Optional[float] = None
    accuracy_1d: Optional[float] = None
    accuracy_3d: Optional[float] = None
    is_verified: bool


class FailedInterpretation(BaseModel):
    """Failed interpretation for review"""
    interpretation_id: int
    ticker: str
    headline_bias: str
    expected_impact: str
    time_horizon: str
    confidence: int
    actual_direction: str
    price_change: float
    interpreted_at: str
    verified_at: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status", response_model=SchedulerStatus)
@log_endpoint("accountability", "system")
async def get_scheduler_status():
    """
    Get Accountability Scheduler status

    Returns:
        - is_running: Whether scheduler is active
        - last_run: Timestamp of last verification run
        - next_run: Timestamp of next scheduled run
        - total_verifications_today: Number of verifications today
    """
    try:
        with get_sync_session() as session:
            # Count verifications today
            today = datetime.utcnow().date()
            result = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM news_market_reactions
                    WHERE DATE(verified_at_1h) = :today
                       OR DATE(verified_at_1d) = :today
                       OR DATE(verified_at_3d) = :today
                """),
                {"today": today}
            )
            total_today = result.scalar() or 0

            # TODO: Get actual scheduler state from global instance
            # For now, return static values
            return SchedulerStatus(
                is_running=True,
                last_run=None,
                next_run=None,
                run_interval_minutes=60,
                total_verifications_today=total_today
            )

    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nia", response_model=NIAScore)
@log_endpoint("accountability", "system")
async def get_nia_score(
    lookback_days: int = Query(default=30, ge=1, le=365, description="Lookback period in days")
):
    """
    Get News Interpretation Accuracy (NIA) score

    Args:
        lookback_days: Lookback period (default: 30 days)

    Returns:
        - overall_nia: Overall accuracy score (0.0 ~ 1.0)
        - total_interpretations: Total news interpretations
        - verified_interpretations: Number of verified interpretations
        - nia_by_time_horizon: Accuracy breakdown by 1h/1d/3d
        - nia_by_impact: Accuracy breakdown by HIGH/MEDIUM/LOW
    """
    try:
        with get_sync_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

            # Total interpretations
            total = session.query(NewsInterpretation).filter(
                NewsInterpretation.interpreted_at >= cutoff_date
            ).count()

            # Verified interpretations (at least one time horizon verified)
            verified_query = session.query(NewsMarketReaction).filter(
                NewsMarketReaction.news_at >= cutoff_date,
                (NewsMarketReaction.verified_at_1h.isnot(None) |
                 NewsMarketReaction.verified_at_1d.isnot(None) |
                 NewsMarketReaction.verified_at_3d.isnot(None))
            )
            verified = verified_query.count()

            # Calculate overall NIA
            accuracy_scores = []
            for reaction in verified_query.all():
                if reaction.accuracy_1h is not None:
                    accuracy_scores.append(reaction.accuracy_1h)
                if reaction.accuracy_1d is not None:
                    accuracy_scores.append(reaction.accuracy_1d)
                if reaction.accuracy_3d is not None:
                    accuracy_scores.append(reaction.accuracy_3d)

            overall_nia = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0

            # NIA by time horizon
            nia_by_horizon = {}
            for horizon_col, horizon_name in [
                ("accuracy_1h", "1h"),
                ("accuracy_1d", "1d"),
                ("accuracy_3d", "3d")
            ]:
                result = session.execute(
                    text(f"SELECT AVG({horizon_col}) FROM news_market_reactions WHERE {horizon_col} IS NOT NULL AND news_at >= :cutoff"),
                    {"cutoff": cutoff_date}
                )
                avg = result.scalar()
                nia_by_horizon[horizon_name] = float(avg) if avg else 0.0

            # NIA by impact level (requires JOIN with news_interpretations)
            nia_by_impact = {}
            for impact_level in ["HIGH", "MEDIUM", "LOW"]:
                result = session.execute(
                    text("""
                        SELECT AVG(nmr.accuracy_1d)
                        FROM news_market_reactions nmr
                        JOIN news_interpretations ni ON nmr.interpretation_id = ni.id
                        WHERE ni.expected_impact = :impact
                          AND nmr.accuracy_1d IS NOT NULL
                          AND nmr.news_at >= :cutoff
                    """),
                    {"impact": impact_level, "cutoff": cutoff_date}
                )
                avg = result.scalar()
                nia_by_impact[impact_level] = float(avg) if avg else 0.0

            return NIAScore(
                overall_nia=overall_nia,
                total_interpretations=total,
                verified_interpretations=verified,
                pending_interpretations=total - verified,
                nia_by_time_horizon=nia_by_horizon,
                nia_by_impact=nia_by_impact
            )

    except Exception as e:
        logger.error(f"Error calculating NIA score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/interpretations", response_model=List[InterpretationItem])
@log_endpoint("accountability", "system")
async def get_interpretations(
    ticker: Optional[str] = Query(default=None, description="Filter by ticker"),
    impact: Optional[str] = Query(default=None, description="Filter by impact (HIGH/MEDIUM/LOW)"),
    limit: int = Query(default=50, ge=1, le=500, description="Max results")
):
    """
    Get news interpretations with accuracy scores

    Args:
        ticker: Filter by ticker (optional)
        impact: Filter by impact level (optional)
        limit: Max results (default: 50)

    Returns:
        List of news interpretations with accuracy scores
    """
    try:
        with get_sync_session() as session:
            query = session.query(NewsInterpretation).order_by(
                NewsInterpretation.interpreted_at.desc()
            )

            if ticker:
                query = query.filter(NewsInterpretation.ticker == ticker)
            if impact:
                query = query.filter(NewsInterpretation.expected_impact == impact)

            interpretations = query.limit(limit).all()

            results = []
            for interp in interpretations:
                # Get associated market reaction
                reaction = session.query(NewsMarketReaction).filter(
                    NewsMarketReaction.interpretation_id == interp.id
                ).first()

                results.append(InterpretationItem(
                    id=interp.id,
                    ticker=interp.ticker,
                    headline_bias=interp.headline_bias,
                    expected_impact=interp.expected_impact,
                    time_horizon=interp.time_horizon,
                    confidence=interp.confidence,
                    reasoning=interp.reasoning,
                    interpreted_at=interp.interpreted_at.isoformat(),
                    accuracy_1h=float(reaction.accuracy_1h) if reaction and reaction.accuracy_1h else None,
                    accuracy_1d=float(reaction.accuracy_1d) if reaction and reaction.accuracy_1d else None,
                    accuracy_3d=float(reaction.accuracy_3d) if reaction and reaction.accuracy_3d else None,
                    is_verified=reaction is not None and reaction.verified_at_1d is not None
                ))

            return results

    except Exception as e:
        logger.error(f"Error getting interpretations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failed", response_model=List[FailedInterpretation])
@log_endpoint("accountability", "system")
async def get_failed_interpretations(
    lookback_days: int = Query(default=7, ge=1, le=90, description="Lookback period in days")
):
    """
    Get failed interpretations for review

    Failed = accuracy < 0.5 (wrong direction)

    Args:
        lookback_days: Lookback period (default: 7 days)

    Returns:
        List of failed interpretations
    """
    try:
        with get_sync_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

            failed = session.execute(
                text("""
                    SELECT
                        ni.id AS interpretation_id,
                        ni.ticker,
                        ni.headline_bias,
                        ni.expected_impact,
                        ni.time_horizon,
                        ni.confidence,
                        nmr.price_change_1d,
                        ni.interpreted_at,
                        nmr.verified_at_1d
                    FROM news_interpretations ni
                    JOIN news_market_reactions nmr ON ni.id = nmr.interpretation_id
                    WHERE nmr.accuracy_1d < 0.5
                      AND nmr.verified_at_1d >= :cutoff
                    ORDER BY nmr.verified_at_1d DESC
                """),
                {"cutoff": cutoff_date}
            )

            results = []
            for row in failed:
                # Determine actual direction
                actual_direction = "UP" if row.price_change_1d > 0 else "DOWN" if row.price_change_1d < 0 else "FLAT"

                results.append(FailedInterpretation(
                    interpretation_id=row.interpretation_id,
                    ticker=row.ticker,
                    headline_bias=row.headline_bias,
                    expected_impact=row.expected_impact,
                    time_horizon=row.time_horizon,
                    confidence=row.confidence,
                    actual_direction=actual_direction,
                    price_change=float(row.price_change_1d),
                    interpreted_at=row.interpreted_at.isoformat(),
                    verified_at=row.verified_at_1d.isoformat()
                ))

            return results

    except Exception as e:
        logger.error(f"Error getting failed interpretations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
@log_endpoint("accountability", "system")
async def trigger_manual_verification():
    """
    Manually trigger accountability verification

    This will immediately run the verification process
    instead of waiting for the hourly schedule.

    Returns:
        Status message
    """
    try:
        from backend.automation.price_tracking_verifier import PriceTrackingVerifier

        verifier = PriceTrackingVerifier()
        result = await verifier.verify_all()

        return {
            "status": "success",
            "message": "Manual verification completed",
            "verified_1h": result.get("verified_1h", 0),
            "verified_1d": result.get("verified_1d", 0),
            "verified_3d": result.get("verified_3d", 0)
        }

    except Exception as e:
        logger.error(f"Error triggering manual verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))
