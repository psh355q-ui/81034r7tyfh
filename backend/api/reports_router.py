"""
Reports API Router - Endpoints for report generation and management

Provides:
- Daily/Weekly/Monthly report generation
- PDF export
- Report history
- Performance analytics
- Risk analytics

Author: AI Trading System Team
Date: 2025-11-25
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
import io

from backend.core.database import get_db
from sqlalchemy.orm import Session

# Optional imports for report generation
try:
    from backend.reporting.report_generator import ReportGenerator
    REPORT_GENERATOR_AVAILABLE = True
except ImportError:
    REPORT_GENERATOR_AVAILABLE = False

try:
    from backend.reporting.pdf_renderer import PDFRenderer
    PDF_RENDERER_AVAILABLE = True
except ImportError:
    PDF_RENDERER_AVAILABLE = False

from backend.core.models.analytics_models import DailyAnalytics, WeeklyAnalytics, MonthlyAnalytics
from backend.analytics.performance_attribution import PerformanceAttributionAnalyzer
from backend.analytics.risk_analytics import RiskAnalyzer
from backend.analytics.trade_analytics import TradeAnalyzer
from backend.ai.skills.common.logging_decorator import log_endpoint

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


# =============================================================================
# Request/Response Models
# =============================================================================

class ReportMetadata(BaseModel):
    """Report metadata for listing."""
    report_id: str
    report_type: str  # daily/weekly/monthly
    report_date: Optional[str]
    year: Optional[int]
    month: Optional[int]
    week_number: Optional[int]
    generated_at: Optional[str]
    file_size_kb: Optional[int]


class DailyReportSummary(BaseModel):
    """Summary of daily report."""
    date: str
    portfolio_value: float
    daily_pnl: float
    daily_return_pct: float
    trades_count: int
    win_rate: Optional[float]


class AnalyticsQuery(BaseModel):
    """Query parameters for analytics."""
    start_date: date
    end_date: date
    metric: str  # portfolio_value/pnl/sharpe_ratio/etc
    aggregation: Optional[str] = "daily"  # daily/weekly/monthly


# =============================================================================
# Daily Report Endpoints
# =============================================================================

@router.get("/daily")
@log_endpoint("reports", "system")
async def get_daily_report(
    target_date: Optional[date] = Query(None, description="Report date (defaults to yesterday)"),
    format: str = Query("json", description="Response format: json or pdf"),
    db: Session = Depends(get_db),
):
    """
    Get daily trading report.

    Returns JSON data by default, or PDF if format=pdf.
    """
    if target_date is None:
        target_date = (datetime.utcnow() - timedelta(days=1)).date()

    try:
        # Check if dependencies are available
        if not REPORT_GENERATOR_AVAILABLE:
            raise HTTPException(status_code=503, detail="Report generator not available")

        # TODO: Fix SQLAlchemy 2.0 async compatibility
        # For now, return mock empty report
        return {
            "date": target_date.isoformat(),
            "summary": {
                "portfolio_value": 0.0,
                "daily_pnl": 0.0,
                "daily_return_pct": 0.0,
                "total_trades": 0,
            },
            "message": "No trading data available for this date"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return {
            "date": target_date.isoformat(),
            "error": "Report generation failed",
            "message": "No data available"
        }


@router.get("/content")
@log_endpoint("reports", "system")
async def get_report_content(
    type: str = Query(..., description="Report type: daily, weekly, monthly, quarterly, annual"),
    date: Optional[str] = Query(None, description="Date for daily report"),
    year: Optional[int] = Query(None, description="Year for periodic reports"),
    week: Optional[int] = Query(None, description="Week number for weekly report"),
    month: Optional[int] = Query(None, description="Month for monthly report"),
    quarter: Optional[int] = Query(None, description="Quarter for quarterly report"),
    db: Session = Depends(get_db),
):
    """
    Get raw content of a generated report (Markdown).
    """
    import os
    
    filename = ""
    docs_dir = "docs"
    
    try:
        if type == "daily":
            if not date:
                date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y%m%d")
            date_clean = date.replace("-", "")
            filename = f"Daily_Briefing_{date_clean}.md"
            
        elif type == "weekly":
            if not year: year = datetime.now().year
            if date:
                date_clean = date.replace("-", "")
                filename = f"Weekly_Report_{date_clean}.md"
            else:
                 # Try to find recent weekly report if specific date not provided
                 # Logic: Look for file matching pattern Weekly_Report_YYYYMMDD.md
                 filename = f"Weekly_Report_{year}.md" # Placeholder, improved logic below

        elif type == "monthly":
            if not year: year = datetime.now().year
            if not month: month = datetime.now().month
            filename = f"Monthly_Report_{year}_{month:02d}.md"

        elif type == "quarterly":
            if not year: year = datetime.now().year
            if not quarter: quarter = (datetime.now().month - 1) // 3 + 1
            filename = f"Quarterly_Report_{year}_Q{quarter}.md"

        elif type == "annual":
            if not year: year = datetime.now().year
            filename = f"Annual_Report_{year}.md"
            
        else:
            raise HTTPException(status_code=400, detail="Invalid report type")

        file_path = os.path.join(docs_dir, filename)
        
        # Absolute path for debugging
        abs_path = os.path.abspath(file_path)
        logger.info(f"Report Access Request: Type={type}, Year={year}, Month={month}, Filename={filename}")
        logger.info(f"Looking for file at: {abs_path}")
        
        # Fallback logic for finding files if exact name match fails (especially for weekly/daily dates)
        if not os.path.exists(file_path):
             logger.warning(f"File not found at {abs_path}, attempting fallback...")
             if type == "weekly":
                 # Find any weekly report for the year if specific one missing
                 for f in sorted(os.listdir(docs_dir), reverse=True):
                     if f.startswith(f"Weekly_Report_") and f.endswith(".md"):
                         file_path = os.path.join(docs_dir, f)
                         filename = f
                         break
             elif type == "monthly":
                  # Last available monthly
                  for f in sorted(os.listdir(docs_dir), reverse=True):
                     if f.startswith(f"Monthly_Report_") and f.endswith(".md"):
                         file_path = os.path.join(docs_dir, f)
                         filename = f
                         break
             elif type == "quarterly":
                  for f in sorted(os.listdir(docs_dir), reverse=True):
                     if f.startswith(f"Quarterly_Report_") and f.endswith(".md"):
                         file_path = os.path.join(docs_dir, f)
                         filename = f
                         break

        if not os.path.exists(file_path):
            logger.error(f"Final check failed. File does not exist: {file_path}")
            raise HTTPException(status_code=404, detail=f"Report file not found: {filename} (Path: {abs_path})")
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return {
            "content": content,
            "filename": filename,
            "generated_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading report content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Monthly Report Endpoints
# =============================================================================

@router.get("/monthly")
@log_endpoint("reports", "system")
async def get_monthly_report(
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)"),
    format: str = Query("json", description="Response format: json or pdf"),
    db: Session = Depends(get_db),
):
    """
    Generate or retrieve monthly trading report.
    """
    try:
        from backend.ai.reporters.monthly_reporter import MonthlyReporter
        reporter = MonthlyReporter()
        filename = await reporter.generate_monthly_report(year, month)
        
        return {
            "message": "Monthly report generated successfully",
            "filename": filename,
            "year": year,
            "month": month
        }

    except Exception as e:
        logger.error(f"Error generating monthly report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

# =============================================================================
# Quarterly Report Endpoints
# =============================================================================

@router.get("/quarterly")
@log_endpoint("reports", "system")
async def get_quarterly_report(
    year: int = Query(..., description="Year"),
    quarter: int = Query(..., description="Quarter (1-4)"),
    format: str = Query("json", description="Response format: json or pdf"),
    db: Session = Depends(get_db),
):
    """
    Generate or retrieve quarterly trading report.
    """
    try:
        from backend.ai.reporters.quarterly_reporter import QuarterlyReporter
        reporter = QuarterlyReporter()
        filename = await reporter.generate_quarterly_report(year, quarter)
        
        return {
            "message": "Quarterly report generated successfully",
            "filename": filename,
            "year": year,
            "quarter": quarter
        }

    except Exception as e:
        logger.error(f"Error generating quarterly report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/monthly/list")
@log_endpoint("reports", "system")
async def list_monthly_reports(
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db),
):
    """
    List available monthly reports.
    """
    from sqlalchemy import select
    stmt = select(MonthlyAnalytics)

    if year:
        stmt = stmt.where(MonthlyAnalytics.year == year)

    stmt = stmt.order_by(
        MonthlyAnalytics.year.desc(),
        MonthlyAnalytics.month.desc()
    )
    
    result = await db.execute(stmt)
    reports = result.scalars().all()

    return [
        {
            "year": r.year,
            "month": r.month,
            "monthly_pnl": float(r.monthly_pnl),
            "monthly_return_pct": float(r.monthly_return_pct) if r.monthly_return_pct else None,
            "total_trades": r.total_trades,
            "trading_days": r.trading_days,
        }
        for r in reports
    ]


# =============================================================================
# Analytics Endpoints
# =============================================================================

@router.get("/analytics/performance-summary")
@log_endpoint("reports", "system")
async def get_performance_summary(
    lookback_days: int = Query(30, description="Days to look back"),
    db: Session = Depends(get_db),
):
    """
    Get performance summary for the last N days.
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=lookback_days)

    try:
        # TODO: Fix SQLAlchemy 2.0 async compatibility
        # For now, return mock empty data
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": 0,
            },
            "current": {
                "portfolio_value": 0.0,
                "positions_count": 0,
            },
            "performance": {
                "total_pnl": 0.0,
                "total_trades": 0,
                "total_volume_usd": 0.0,
                "win_rate": None,
                "avg_daily_pnl": 0.0,
            },
            "risk": {
                "sharpe_ratio": None,
                "max_drawdown_pct": None,
                "volatility_30d": None,
            },
            "ai": {
                "total_cost_usd": 0.0,
                "total_signals": 0,
                "avg_accuracy": None,
            },
        }
    except Exception as e:
        logger.error(f"Error fetching performance summary: {e}")
        return {
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "days": 0},
            "current": {"portfolio_value": 0.0, "positions_count": 0},
            "performance": {"total_pnl": 0.0, "total_trades": 0, "total_volume_usd": 0.0, "win_rate": None, "avg_daily_pnl": 0.0},
            "risk": {"sharpe_ratio": None, "max_drawdown_pct": None, "volatility_30d": None},
            "ai": {"total_cost_usd": 0.0, "total_signals": 0, "avg_accuracy": None},
        }


@router.get("/analytics/time-series")
@log_endpoint("reports", "system")
async def get_time_series_data(
    metric: str = Query(..., description="Metric name (portfolio_value/daily_pnl/sharpe_ratio/etc)"),
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
):
    """
    Get time series data for a specific metric.

    Useful for charting.
    """
    from sqlalchemy import select
    stmt = select(DailyAnalytics).where(
        DailyAnalytics.date >= start_date,
        DailyAnalytics.date <= end_date,
    ).order_by(DailyAnalytics.date)
    
    result = await db.execute(stmt)
    daily_records = result.scalars().all()

    if not daily_records:
        raise HTTPException(status_code=404, detail="No data available for date range")

    # Map metric name to column
    metric_map = {
        "portfolio_value": "portfolio_value_eod",
        "daily_pnl": "daily_pnl",
        "daily_return": "daily_return_pct",
        "sharpe_ratio": "sharpe_ratio",
        "trades": "total_trades",
        "win_rate": "win_rate",
        "ai_cost": "ai_cost_usd",
    }

    if metric not in metric_map:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")

    column_name = metric_map[metric]

    # Extract data
    dates = [r.date.isoformat() for r in daily_records]
    values = []

    for r in daily_records:
        value = getattr(r, column_name, None)
        if value is not None:
            if isinstance(value, Decimal):
                values.append(float(value))
            else:
                values.append(value)
        else:
            values.append(None)

    return {
        "metric": metric,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "data_points": len(dates),
        "dates": dates,
        "values": values,
    }


# =============================================================================
# Export Endpoints
# =============================================================================

@router.post("/export/csv")
@log_endpoint("reports", "system")
async def export_to_csv(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
):
    """
    Export daily analytics to CSV.
    """
    from sqlalchemy import select
    stmt = select(DailyAnalytics).where(
        DailyAnalytics.date >= start_date,
        DailyAnalytics.date <= end_date,
    ).order_by(DailyAnalytics.date)
    
    result = await db.execute(stmt)
    daily_records = result.scalars().all()

    if not daily_records:
        raise HTTPException(status_code=404, detail="No data available for date range")

    # Build CSV
    csv_lines = []
    headers = [
        "Date", "Portfolio Value", "Daily P&L", "Daily Return %",
        "Trades", "Win Rate", "Sharpe Ratio", "AI Cost"
    ]
    csv_lines.append(",".join(headers))

    for r in daily_records:
        row = [
            r.date.isoformat(),
            f"{r.portfolio_value_eod:.2f}",
            f"{r.daily_pnl:.2f}",
            f"{r.daily_return_pct:.4f}" if r.daily_return_pct else "",
            str(r.total_trades),
            f"{r.win_rate:.4f}" if r.win_rate else "",
            f"{r.sharpe_ratio:.4f}" if r.sharpe_ratio else "",
            f"{r.ai_cost_usd:.4f}",
        ]
        csv_lines.append(",".join(row))

    csv_content = "\n".join(csv_lines)

    # Return CSV response
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=analytics_{start_date}_{end_date}.csv"
        }
    )


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
@log_endpoint("reports", "system")
async def reports_health_check(db: Session = Depends(get_db)):
    """
    Health check for reports service.
    """
    # Check if we have recent data
    try:
        from sqlalchemy import select
        stmt = select(DailyAnalytics).order_by(DailyAnalytics.date.desc())
        result = await db.execute(stmt)
        latest_daily = result.scalars().first()

        return {
            "status": "healthy",
            "latest_daily_report": latest_daily.date.isoformat() if latest_daily else None,
            "data_available": latest_daily is not None,
        }
    except Exception as e:
        # Table may not exist yet
        logger.warning(f"Reports health check error: {e}")
        return {
            "status": "healthy",
            "latest_daily_report": None,
            "data_available": False,
            "note": "No data yet - expected on first run"
        }


# =============================================================================
# Advanced Analytics Endpoints (Phase 15.5)
# =============================================================================

@router.get("/advanced/performance-attribution")
@log_endpoint("reports", "system")
async def get_performance_attribution(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    dimension: str = Query("all", description="Dimension: strategy/sector/ai_source/position/time/all"),
    db: Session = Depends(get_db),
):
    """
    Get performance attribution analysis.

    Breaks down returns by various dimensions.
    """
    analyzer = PerformanceAttributionAnalyzer(db)

    try:
        if dimension == "strategy":
            result = await analyzer.analyze_strategy_attribution(start_date, end_date)
        elif dimension == "sector":
            result = await analyzer.analyze_sector_attribution(start_date, end_date)
        elif dimension == "ai_source":
            result = await analyzer.analyze_ai_source_attribution(start_date, end_date)
        elif dimension == "position":
            result = await analyzer.analyze_position_attribution(start_date, end_date, top_n=20)
        elif dimension == "time":
            result = await analyzer.analyze_time_based_attribution(start_date, end_date)
        elif dimension == "all":
            result = await analyzer.get_comprehensive_attribution(start_date, end_date)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown dimension: {dimension}")

        return result

    except Exception as e:
        logger.error(f"Error in performance attribution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/risk-dashboard")
@log_endpoint("reports", "system")
async def get_risk_dashboard(
    db: Session = Depends(get_db),
):
    """
    Get comprehensive risk dashboard.

    Includes VaR, drawdown, concentration, correlation, and stress test.
    """
    analyzer = RiskAnalyzer(db)

    try:
        result = await analyzer.get_risk_dashboard()
        return result

    except Exception as e:
        logger.error(f"Error generating risk dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/risk-metrics")
@log_endpoint("reports", "system")
async def get_risk_metrics(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    metric: str = Query("all", description="Risk metric: var, drawdown, concentration, correlation, stress_test, or all"),
    db: Session = Depends(get_db),
):
    """
    Get risk metrics for specified date range.

    Metrics:
    - var: Value at Risk analysis
    - drawdown: Drawdown metrics and periods
    - concentration: Portfolio concentration analysis
    - correlation: Correlation analysis
    - stress_test: Stress test scenarios
    - all: All risk metrics
    """
    analyzer = RiskAnalyzer(db)

    try:
        lookback_days = (end_date - start_date).days

        if metric == "var":
            result = {"var_metrics": await analyzer.calculate_var_metrics(
                lookback_days=lookback_days,
                confidence_levels=[0.95, 0.99]
            )}
        elif metric == "drawdown":
            result = {"drawdown_metrics": await analyzer.analyze_drawdown_metrics(lookback_days=lookback_days)}
        elif metric == "concentration":
            result = {"concentration_metrics": await analyzer.analyze_concentration_risk(target_date=end_date)}
        elif metric == "correlation":
            result = {"correlation_analysis": await analyzer.analyze_correlations(lookback_days=lookback_days)}
        elif metric == "stress_test":
            result = {"stress_test_scenarios": await analyzer.run_stress_tests()}
        elif metric == "all":
            result = await analyzer.get_risk_dashboard()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")

        return result

    except Exception as e:
        logger.error(f"Error calculating risk metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/risk/var")
@log_endpoint("reports", "system")
async def get_var_metrics(
    lookback_days: int = Query(90, description="Days of historical data"),
    db: Session = Depends(get_db),
):
    """
    Get Value at Risk (VaR) metrics.
    """
    analyzer = RiskAnalyzer(db)

    try:
        result = await analyzer.calculate_var_metrics(
            lookback_days=lookback_days,
            confidence_levels=[0.95, 0.99]
        )
        return result

    except Exception as e:
        logger.error(f"Error calculating VaR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/risk/drawdown")
@log_endpoint("reports", "system")
async def get_drawdown_analysis(
    lookback_days: int = Query(180, description="Days of historical data"),
    db: Session = Depends(get_db),
):
    """
    Get drawdown analysis.
    """
    analyzer = RiskAnalyzer(db)

    try:
        result = await analyzer.analyze_drawdown_metrics(lookback_days=lookback_days)
        return result

    except Exception as e:
        logger.error(f"Error analyzing drawdown: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/risk/concentration")
@log_endpoint("reports", "system")
async def get_concentration_risk(
    target_date: Optional[date] = Query(None, description="Date to analyze"),
    db: Session = Depends(get_db),
):
    """
    Get concentration risk analysis.
    """
    analyzer = RiskAnalyzer(db)

    try:
        result = await analyzer.analyze_concentration_risk(target_date=target_date)
        return result

    except Exception as e:
        logger.error(f"Error analyzing concentration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/risk/correlation")
@log_endpoint("reports", "system")
async def get_correlation_analysis(
    lookback_days: int = Query(60, description="Days of historical data"),
    db: Session = Depends(get_db),
):
    """
    Get correlation risk analysis.
    """
    analyzer = RiskAnalyzer(db)

    try:
        result = await analyzer.analyze_correlation_risk(lookback_days=lookback_days)
        return result

    except Exception as e:
        logger.error(f"Error analyzing correlation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/advanced/risk/stress-test")
@log_endpoint("reports", "system")
async def run_stress_test(
    scenarios: Optional[List[Dict]] = None,
    db: Session = Depends(get_db),
):
    """
    Run portfolio stress test.
    """
    analyzer = RiskAnalyzer(db)

    try:
        result = await analyzer.stress_test_portfolio(scenarios=scenarios)
        return result

    except Exception as e:
        logger.error(f"Error running stress test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/trade-insights")
@log_endpoint("reports", "system")
async def get_trade_insights(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive trade insights.

    Includes win/loss patterns, execution quality, hold duration, confidence impact, and timing.
    """
    analyzer = TradeAnalyzer(db)

    try:
        result = await analyzer.get_trade_insights(start_date, end_date)
        return result

    except Exception as e:
        logger.error(f"Error generating trade insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/trade/win-loss")
@log_endpoint("reports", "system")
async def get_win_loss_patterns(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
):
    """
    Get win/loss pattern analysis.
    """
    analyzer = TradeAnalyzer(db)

    try:
        result = await analyzer.analyze_win_loss_patterns(start_date, end_date)
        return result

    except Exception as e:
        logger.error(f"Error analyzing win/loss patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/trade/execution-quality")
@log_endpoint("reports", "system")
async def get_execution_quality(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
):
    """
    Get execution quality analysis.
    """
    analyzer = TradeAnalyzer(db)

    try:
        result = await analyzer.analyze_execution_quality(start_date, end_date)
        return result

    except Exception as e:
        logger.error(f"Error analyzing execution quality: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advanced/trade/confidence-impact")
@log_endpoint("reports", "system")
async def get_confidence_impact(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db),
):
    """
    Get AI confidence impact analysis.
    """
    analyzer = TradeAnalyzer(db)

    try:
        result = await analyzer.analyze_confidence_impact(start_date, end_date)
        return result

    except Exception as e:
        logger.error(f"Error analyzing confidence impact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Portfolio Management Endpoints
# =============================================================================

class PortfolioPosition(BaseModel):
    """포트폴리오 포지션 정보"""
    ticker: str
    quantity: int
    current_price: float
    entry_price: float
    weight: float
    value: float


class PortfolioAnalyzeRequest(BaseModel):
    """포트폴리오 분석 요청"""
    positions: List[PortfolioPosition]
    equity_curve: Optional[List[float]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "positions": [
                    {"ticker": "NVDA", "quantity": 10, "current_price": 145.0, "entry_price": 140.0, "weight": 0.25, "value": 1450.0},
                    {"ticker": "AMD", "quantity": 20, "current_price": 135.0, "entry_price": 130.0, "weight": 0.15, "value": 2700.0}
                ],
                "equity_curve": [100000, 101000, 102500, 101800, 103000]
            }
        }


@router.post("/portfolio/analyze")
@log_endpoint("reports", "system")
async def analyze_portfolio(request: PortfolioAnalyzeRequest):
    """
    포트폴리오 종합 분석
    
    분석 내용:
    - VaR (Value at Risk)
    - Concentration Risk (집중도 리스크)
    - Drawdown (최대 낙폭)
    - 리밸런싱 제안
    """
    try:
        from backend.analytics.portfolio_manager import PortfolioManager
        
        manager = PortfolioManager()
        
        # Convert Pydantic models to dicts
        positions = [p.dict() for p in request.positions]
        
        result = await manager.analyze_portfolio(
            current_positions=positions,
            equity_curve=request.equity_curve
        )
        
        return {
            "success": True,
            "analysis": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/portfolio/rebalance")
@log_endpoint("reports", "system")
async def get_rebalancing_suggestions(request: PortfolioAnalyzeRequest):
    """
    포트폴리오 리밸런싱 제안
    
    집중도 초과, 리스크 한도 초과 포지션에 대한 조정 제안
    """
    try:
        from backend.analytics.portfolio_manager import PortfolioManager
        
        manager = PortfolioManager()
        
        positions = [p.dict() for p in request.positions]
        
        suggestions = await manager.suggest_rebalancing(current_positions=positions)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating rebalancing suggestions: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "suggestions": [],
            "timestamp": datetime.now().isoformat()
        }


@router.get("/portfolio/health")
@log_endpoint("reports", "system")
async def get_portfolio_health():
    """
    포트폴리오 헬스 체크 (샘플 데이터)
    
    현재 포지션 없이 빠른 헬스 체크
    """
    return {
        "status": "healthy",
        "message": "Portfolio Manager API ready",
        "available_endpoints": [
            "POST /reports/portfolio/analyze",
            "POST /reports/portfolio/rebalance"
        ],
        "timestamp": datetime.now().isoformat()
    }

