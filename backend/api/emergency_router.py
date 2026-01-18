"""
Emergency Status API Router

Provides real-time emergency detection based on Constitution rules
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.repository import get_sync_session
from backend.constitution.constitution import Constitution
from datetime import datetime, timedelta
import logging
from backend.ai.skills.common.logging_decorator import log_endpoint

router = APIRouter(prefix="/emergency", tags=["Emergency Detection"])
logger = logging.getLogger(__name__)


def get_db():
    """Database session dependency"""
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/status")
@log_endpoint("emergency", "system")
async def get_emergency_status(db: Session = Depends(get_db)):
    """
    Check if emergency conditions are active (Constitution-based + real data)
    
    Returns emergency status and Grounding search recommendation
    """
    try:
        from backend.services.market_data import get_vix_realtime
        constitution = Constitution()
        
        # Get real portfolio data from KIS
        daily_loss = 0.0
        total_drawdown = 0.0
        
        try:
            # Import from actual portfolio router
            from backend.api.portfolio_router import get_portfolio
            portfolio = await get_portfolio()
            
            # Daily loss from portfolio (PortfolioResponse object)
            daily_loss = (portfolio.daily_return_pct or 0) / 100.0
            
            # Calculate drawdown
            total_value = portfolio.total_value or 100000
            total_pnl = portfolio.total_pnl or 0
            initial_value = total_value - total_pnl
            
            if initial_value > 0:
                total_drawdown = -abs(min(0, total_pnl / initial_value))
            
        except Exception as e:
            logger.warning(f"Portfolio fetch failed, using defaults: {e}")
        
        # Get VIX real-time
        vix = await get_vix_realtime()
        
        # Constitution circuit breaker check
        should_trigger, reason = constitution.validate_circuit_breaker_trigger(
            daily_loss=daily_loss,
            total_drawdown=total_drawdown,
            vix=vix
        )
        
        # Get Grounding usage today
        today_count = await get_grounding_count_today(db)
        
        # Determine severity
        severity = "normal"
        if should_trigger:
            if abs(daily_loss) >= 0.05:  # 5%+ loss
                severity = "critical"
            elif vix >= 40:
                severity = "critical"
            elif vix >= 35:
                severity = "high"
            else:
                severity = "medium"
        
        return {
            "is_emergency": should_trigger,
            "severity": severity,
            "triggers": [reason] if should_trigger else [],
            "recommend_grounding": should_trigger and today_count < 1,
            "grounding_searches_today": today_count,
            "daily_limit": 10,
            "message": reason if should_trigger else "Market conditions normal",
            "portfolio_data": {
                "daily_loss_pct": daily_loss * 100,
                "total_drawdown_pct": total_drawdown * 100
            },
            "vix": vix,
            "last_checked": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking emergency status: {e}", exc_info=True)
        return {
            "is_emergency": False,
            "severity": "normal",
            "triggers": [],
            "recommend_grounding": False,
            "grounding_searches_today": 0,
            "daily_limit": 10,
            "error": str(e)
        }


async def get_grounding_count_today(db: Session) -> int:
    """Get number of Grounding searches made today"""
    try:
        from backend.database.models import GroundingSearchLog
        from sqlalchemy import func
        from datetime import date
        
        count = db.query(func.count(GroundingSearchLog.id)).filter(
            func.date(GroundingSearchLog.search_date) == date.today()
        ).scalar()
        
        return count or 0
    except Exception as e:
        logger.error(f"Error getting grounding count: {e}")
        return 0


@router.post("/grounding/track")
@log_endpoint("emergency", "system")
async def track_grounding_search(
    ticker: str,
    results_count: int = 0,
    emergency_trigger: str = None,
    db: Session = Depends(get_db)
):
    """
    Track a Grounding API search for cost monitoring
    
    Args:
        ticker: Stock ticker searched
        results_count: Number of results returned
        emergency_trigger: Emergency condition that triggered search (optional)
    """
    try:
        from backend.database.models import GroundingSearchLog
        
        cost = 0.035  # $0.035 per search
        
        log = GroundingSearchLog(
            ticker=ticker.upper(),
            query=f"latest news about {ticker.upper()} stock",
            result_count=results_count,
            estimated_cost=cost,
            emergency_trigger=emergency_trigger,
            was_emergency=emergency_trigger is not None
        )
        
        db.add(log)
        db.commit()
        
        logger.info(f"Grounding search tracked: {ticker}, cost=${cost}, trigger={emergency_trigger}")
        
        return {
            "success": True,
            "ticker": ticker,
            "cost_usd": cost,
            "results_count": results_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error tracking Grounding search: {e}", exc_info=True)
        db.rollback()
        return {"success": False, "error": str(e)}


@router.get("/grounding/usage")
@log_endpoint("emergency", "system")
async def get_grounding_usage(db: Session = Depends(get_db)):
    """
    Get Grounding API usage statistics
    
    Returns today and monthly usage
    """
    try:
        from backend.database.models import GroundingSearchLog
        from sqlalchemy import func, extract
        from datetime import date, datetime
        
        # Today's usage
        today = date.today()
        today_data = db.query(
            func.count(GroundingSearchLog.id).label('count'),
            func.sum(GroundingSearchLog.estimated_cost).label('cost'),
            func.count(func.distinct(GroundingSearchLog.ticker)).label('tickers')
        ).filter(
            func.date(GroundingSearchLog.search_date) == today
        ).first()
        
        # This month's usage
        now = datetime.now()
        month_data = db.query(
            func.count(GroundingSearchLog.id).label('count'),
            func.sum(GroundingSearchLog.estimated_cost).label('cost'),
            func.count(func.distinct(GroundingSearchLog.ticker)).label('tickers')
        ).filter(
            extract('year', GroundingSearchLog.search_date) == now.year,
            extract('month', GroundingSearchLog.search_date) == now.month
        ).first()
        
        return {
            "today": {
                "searches": today_data.count or 0,
                "cost": float(today_data.cost or 0),
                "unique_tickers": today_data.tickers or 0
            },
            "this_month": {
                "searches": month_data.count or 0,
                "cost": float(month_data.cost or 0),
                "unique_tickers": month_data.tickers or 0
            },
            "daily_limit": 10,
            "monthly_budget": 10.0,
            "remaining_daily": max(0, 10 - (today_data.count or 0)),
            "remaining_budget": max(0, 10.0 - float(month_data.cost or 0))
        }
        
    except Exception as e:
        logger.error(f"Error getting usage: {e}", exc_info=True)
        return {
            "today": {"searches": 0, "cost": 0.0, "unique_tickers": 0},
            "this_month": {"searches": 0, "cost": 0.0, "unique_tickers": 0},
            "error": str(e)
        }


@router.get("/grounding/report/monthly")
@log_endpoint("emergency", "system")
async def get_monthly_cost_report(
    year: int = None,
    month: int = None,
    db: Session = Depends(get_db)
):
    """
    Get monthly Grounding cost report
    
    Args:
        year: Year (default: current year)
        month: Month (default: current month)
    
    Returns:
        Monthly cost breakdown with ticker analysis
    """
    try:
        from backend.database.models import GroundingSearchLog
        from sqlalchemy import func, extract
        
        # Default to current month
        if not year or not month:
            now = datetime.now()
            year, month = now.year, now.month
        
        # Get all searches for the month
        searches = db.query(GroundingSearchLog).filter(
            extract('year', GroundingSearchLog.search_date) == year,
            extract('month', GroundingSearchLog.search_date) == month
        ).all()
        
        # Aggregate by ticker
        by_ticker = {}
        emergency_count = 0
        
        for s in searches:
            ticker = s.ticker
            by_ticker[ticker] = by_ticker.get(ticker, 0) + 1
            if s.was_emergency:
                emergency_count += 1

        total_cost = sum(s.estimated_cost for s in searches)
        
        # Top tickers
        top_tickers = sorted(by_ticker.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "year": year,
            "month": month,
            "total_searches": len(searches),
            "total_cost_usd": float(total_cost),
            "emergency_searches": emergency_count,
            "normal_searches": len(searches) - emergency_count,
            "unique_tickers": len(by_ticker),
            "by_ticker": dict(top_tickers),
            "all_tickers": by_ticker,
            "daily_average": len(searches) / 30 if len(searches) > 0 else 0,
            "budget_used_pct": (float(total_cost) / 10.0) * 100 if total_cost > 0 else 0,
            "budget_remaining": max(0, 10.0 - float(total_cost))
        }
        
    except Exception as e:
        logger.error(f"Error getting monthly report: {e}", exc_info=True)
        return {
            "error": str(e),
            "year": year,
            "month": month,
            "total_searches": 0,
            "total_cost_usd": 0.0
        }

