"""
Cost Monitoring API Endpoints.

Provides REST API for cost analytics and monitoring.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.monitoring.cost_analytics import CostAnalytics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cost", tags=["Cost Monitoring"])


@router.get("/summary/daily")
async def get_daily_summary(
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get cost summary for a specific day.

    Args:
        target_date: Target date (default: today)
        db: Database session

    Returns:
        Daily cost summary
    """
    analytics = CostAnalytics(db)

    if target_date:
        try:
            parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        parsed_date = date.today()

    summary = await analytics.get_daily_summary(parsed_date)

    return summary.to_dict()


@router.get("/summary/monthly")
async def get_monthly_summary(
    year: int = Query(..., description="Year"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get cost summaries for entire month.

    Args:
        year: Year
        month: Month (1-12)
        db: Database session

    Returns:
        List of daily summaries for the month
    """
    analytics = CostAnalytics(db)

    summaries = await analytics.get_monthly_costs(year, month)

    return {
        "year": year,
        "month": month,
        "days": len(summaries),
        "total_cost": sum(s.total_cost_usd for s in summaries),
        "daily_summaries": [s.to_dict() for s in summaries],
    }


@router.get("/summary/monthly/total")
async def get_monthly_total(
    year: Optional[int] = Query(None, description="Year (default: current)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month (default: current)"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get total monthly cost.

    Args:
        year: Year (default: current year)
        month: Month (default: current month)
        db: Database session

    Returns:
        Monthly total cost
    """
    analytics = CostAnalytics(db)

    today = date.today()
    year = year or today.year
    month = month or today.month

    total = await analytics.get_monthly_total(year, month)

    return {
        "year": year,
        "month": month,
        "total_cost_usd": total,
        "daily_average": total / today.day if year == today.year and month == today.month else total / 30,
    }


@router.get("/breakdown")
async def get_cost_breakdown(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get detailed cost breakdown for a period.

    Args:
        start_date: Start date
        end_date: End date
        db: Database session

    Returns:
        Detailed cost breakdown
    """
    analytics = CostAnalytics(db)

    try:
        parsed_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        parsed_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    if parsed_start > parsed_end:
        raise HTTPException(
            status_code=400, detail="Start date must be before end date"
        )

    breakdown = await analytics.get_cost_breakdown(parsed_start, parsed_end)

    return breakdown


@router.get("/budget/check")
async def check_budget(
    daily_limit: Optional[float] = Query(None, description="Daily limit in USD"),
    monthly_limit: Optional[float] = Query(None, description="Monthly limit in USD"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Check current costs against budget limits.

    Args:
        daily_limit: Daily budget limit (default: 1.0)
        monthly_limit: Monthly budget limit (default: 10.0)
        db: Database session

    Returns:
        Budget alert status
    """
    analytics = CostAnalytics(db)

    alert = await analytics.check_budget_alert(
        daily_limit=daily_limit, monthly_limit=monthly_limit
    )

    return alert


@router.get("/trends")
async def get_cost_trends(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get cost trends over the last N days.

    Args:
        days: Number of days (1-90)
        db: Database session

    Returns:
        Cost trend analysis
    """
    analytics = CostAnalytics(db)

    trends = await analytics.get_cost_trends(days=days)

    return trends


@router.get("/pricing")
async def get_pricing_info() -> Dict[str, Any]:
    """
    Get current API pricing information.

    Returns:
        Pricing details for all services
    """
    return {
        "last_updated": "2025-11-23",
        "pricing": CostAnalytics.PRICING,
        "limits": {
            "daily_usd": CostAnalytics.DAILY_LIMIT_USD,
            "monthly_usd": CostAnalytics.MONTHLY_LIMIT_USD,
        },
    }


@router.get("/dashboard")
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard data.

    Returns:
        All cost metrics for dashboard display
    """
    analytics = CostAnalytics(db)

    today = date.today()

    # Get today's summary
    daily_summary = await analytics.get_daily_summary(today)

    # Get monthly total
    monthly_total = await analytics.get_monthly_total(today.year, today.month)

    # Get budget status
    budget = await analytics.check_budget_alert()

    # Get 7-day trends
    trends_7d = await analytics.get_cost_trends(days=7)

    # Get 30-day trends
    trends_30d = await analytics.get_cost_trends(days=30)

    # Get breakdown for last 7 days
    breakdown = await analytics.get_cost_breakdown(
        today - timedelta(days=6), today
    )

    return {
        "today": daily_summary.to_dict(),
        "monthly_total": monthly_total,
        "budget": budget,
        "trends_7d": trends_7d,
        "trends_30d": trends_30d,
        "breakdown_7d": breakdown,
        "generated_at": datetime.now().isoformat(),
    }


# Example usage documentation
@router.get("/docs/examples")
async def get_api_examples() -> Dict[str, Any]:
    """
    Get API usage examples.

    Returns:
        Example API calls and responses
    """
    return {
        "examples": {
            "get_today_summary": {
                "method": "GET",
                "endpoint": "/api/cost/summary/daily",
                "description": "Get today's cost summary",
            },
            "get_monthly_total": {
                "method": "GET",
                "endpoint": "/api/cost/summary/monthly/total?year=2025&month=11",
                "description": "Get November 2025 total cost",
            },
            "check_budget": {
                "method": "GET",
                "endpoint": "/api/cost/budget/check",
                "description": "Check if costs exceed budget limits",
            },
            "get_7day_trends": {
                "method": "GET",
                "endpoint": "/api/cost/trends?days=7",
                "description": "Get cost trends for last 7 days",
            },
            "get_breakdown": {
                "method": "GET",
                "endpoint": "/api/cost/breakdown?start_date=2025-11-01&end_date=2025-11-23",
                "description": "Get detailed cost breakdown",
            },
            "get_dashboard": {
                "method": "GET",
                "endpoint": "/api/cost/dashboard",
                "description": "Get all dashboard data in one call",
            },
        }
    }
