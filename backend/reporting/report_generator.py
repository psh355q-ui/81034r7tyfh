"""
Report Generator - Generate reports from analytics data

Features:
- Daily/Weekly/Monthly report generation
- Data aggregation from analytics tables
- Chart data preparation
- Performance attribution
- Risk analysis

Author: AI Trading System Team
Date: 2025-11-25
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.core.models.analytics_models import (
    DailyAnalytics,
    TradeExecution,
    PortfolioSnapshot,
    SignalPerformance,
    WeeklyAnalytics,
    MonthlyAnalytics,
)
from backend.reporting.report_templates import (
    DailyReport,
    WeeklyReport,
    MonthlyReport,
    ExecutiveSummary,
    TradingActivity,
    PortfolioOverview,
    AIPerformance,
    RiskMetrics,
    PerformanceAttribution,
    ChartData,
    TableData,
    generate_report_id,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates trading reports from analytics data.

    Pulls data from analytics tables and structures it into report objects.
    """

    def __init__(self, db_session: Session):
        """
        Initialize report generator.

        Args:
            db_session: Database session
        """
        self.db = db_session
        logger.info("ReportGenerator initialized")

    async def generate_daily_report(self, target_date: Optional[date] = None) -> DailyReport:
        """
        Generate daily report.

        Args:
            target_date: Date for report (defaults to yesterday)

        Returns:
            DailyReport object
        """
        if target_date is None:
            target_date = (datetime.utcnow() - timedelta(days=1)).date()

        logger.info(f"Generating daily report for {target_date}")

        # Get daily analytics
        daily_analytics = self.db.query(DailyAnalytics).filter(
            DailyAnalytics.date == target_date
        ).first()

        if not daily_analytics:
            raise ValueError(f"No daily analytics found for {target_date}")

        # Get portfolio snapshot
        portfolio_snapshot = self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.snapshot_date == target_date
        ).first()

        # Create report
        report = DailyReport(
            report_id=generate_report_id("daily", target_date),
            report_date=target_date,
            generated_at=datetime.utcnow(),
        )

        # Build sections
        report.executive_summary = self._build_executive_summary(daily_analytics, portfolio_snapshot)
        report.trading_activity = self._build_trading_activity(daily_analytics, target_date)
        report.portfolio_overview = self._build_portfolio_overview(portfolio_snapshot, daily_analytics)
        report.ai_performance = self._build_ai_performance(daily_analytics, target_date)
        report.risk_metrics = self._build_risk_metrics(daily_analytics)

        # Build charts
        report.performance_chart = await self._build_performance_chart(target_date, lookback_days=30)
        report.pnl_chart = await self._build_pnl_chart(target_date, lookback_days=30)

        logger.info(f"Daily report generated for {target_date}")

        return report

    def _build_executive_summary(
        self,
        daily_analytics: DailyAnalytics,
        portfolio_snapshot: Optional[PortfolioSnapshot],
    ) -> ExecutiveSummary:
        """Build executive summary section."""
        summary = ExecutiveSummary(
            portfolio_value=daily_analytics.portfolio_value_eod,
            daily_pnl=daily_analytics.daily_pnl,
            daily_return_pct=daily_analytics.daily_return_pct or Decimal('0'),
            total_return_pct=self._calculate_total_return(daily_analytics),
            win_rate=daily_analytics.win_rate,
            sharpe_ratio=daily_analytics.sharpe_ratio,
            positions_count=daily_analytics.positions_count,
            trades_count=daily_analytics.total_trades,
            ai_cost_usd=daily_analytics.ai_cost_usd,
        )

        # Generate highlights
        highlights = []

        # Performance highlights
        if daily_analytics.daily_pnl > 0:
            highlights.append(f"Profitable day with ${daily_analytics.daily_pnl:,.2f} gain ({daily_analytics.daily_return_pct:.2f}%)")
        elif daily_analytics.daily_pnl < 0:
            highlights.append(f"Loss of ${abs(daily_analytics.daily_pnl):,.2f} ({daily_analytics.daily_return_pct:.2f}%)")

        # Trading activity
        if daily_analytics.total_trades > 0:
            highlights.append(f"Executed {daily_analytics.total_trades} trades")
            if daily_analytics.win_rate:
                highlights.append(f"Win rate: {daily_analytics.win_rate*100:.1f}%")

        # AI performance
        if daily_analytics.signals_generated > 0:
            highlights.append(f"Generated {daily_analytics.signals_generated} AI signals")

        summary.highlights = highlights

        # Risk alerts
        risk_alerts = []

        if daily_analytics.circuit_breaker_triggers > 0:
            risk_alerts.append(f"⚠️ Circuit breaker triggered {daily_analytics.circuit_breaker_triggers} times")

        if daily_analytics.kill_switch_active:
            risk_alerts.append("🛑 Kill switch is ACTIVE")

        if daily_analytics.max_drawdown_pct and daily_analytics.max_drawdown_pct < -10:
            risk_alerts.append(f"⚠️ Significant drawdown: {daily_analytics.max_drawdown_pct:.2f}%")

        summary.risk_alerts = risk_alerts

        return summary

    def _calculate_total_return(self, daily_analytics: DailyAnalytics) -> Decimal:
        """Calculate total return since inception."""
        initial_value = Decimal('100000.00')  # TODO: Get from config
        if daily_analytics.portfolio_value_eod > 0:
            return ((daily_analytics.portfolio_value_eod - initial_value) / initial_value) * 100
        return Decimal('0')

    def _build_trading_activity(
        self,
        daily_analytics: DailyAnalytics,
        target_date: date,
    ) -> TradingActivity:
        """Build trading activity section."""
        activity = TradingActivity(
            total_trades=daily_analytics.total_trades,
            buy_trades=daily_analytics.buy_trades,
            sell_trades=daily_analytics.sell_trades,
            total_volume_usd=daily_analytics.total_volume_usd or Decimal('0'),
            avg_position_size_usd=daily_analytics.avg_position_size_usd,
            win_count=daily_analytics.win_count,
            loss_count=daily_analytics.loss_count,
            win_rate=daily_analytics.win_rate,
            avg_win_pct=daily_analytics.avg_win_pct,
            avg_loss_pct=daily_analytics.avg_loss_pct,
            avg_slippage_bps=daily_analytics.avg_slippage_bps,
            avg_execution_time_ms=daily_analytics.avg_execution_time_ms,
        )

        # Get top trades
        top_trades_data = self.db.query(TradeExecution).filter(
            func.date(TradeExecution.exit_timestamp) == target_date,
            TradeExecution.status == 'CLOSED',
        ).order_by(
            TradeExecution.pnl_usd.desc()
        ).limit(10).all()

        if top_trades_data:
            headers = ["Ticker", "Action", "PnL", "Return %", "Confidence", "AI Source"]
            rows = [
                [
                    t.ticker,
                    t.action,
                    f"${t.pnl_usd:,.2f}",
                    f"{t.pnl_pct:.2f}%",
                    f"{t.signal_confidence*100:.0f}%" if t.signal_confidence else "N/A",
                    t.ai_source or "N/A",
                ]
                for t in top_trades_data
            ]
            activity.top_trades = TableData(
                title="Top Trades",
                headers=headers,
                rows=rows,
            )

        return activity

    def _build_portfolio_overview(
        self,
        portfolio_snapshot: Optional[PortfolioSnapshot],
        daily_analytics: DailyAnalytics,
    ) -> PortfolioOverview:
        """Build portfolio overview section."""
        if not portfolio_snapshot:
            # Fallback to daily analytics
            return PortfolioOverview(
                total_value=daily_analytics.portfolio_value_eod,
                cash=Decimal('0'),
                invested_value=daily_analytics.portfolio_value_eod,
                positions_count=daily_analytics.positions_count,
                sector_allocation={},
                strategy_allocation={},
            )

        overview = PortfolioOverview(
            total_value=portfolio_snapshot.total_value,
            cash=portfolio_snapshot.cash,
            invested_value=portfolio_snapshot.invested_value,
            positions_count=portfolio_snapshot.positions_count,
            sector_allocation=portfolio_snapshot.sector_allocation or {},
            strategy_allocation=portfolio_snapshot.strategy_allocation or {},
            largest_position_pct=portfolio_snapshot.largest_position_pct,
            cash_pct=portfolio_snapshot.cash_pct,
        )

        # Build top positions table
        if portfolio_snapshot.positions:
            # Sort by value
            sorted_positions = sorted(
                portfolio_snapshot.positions,
                key=lambda p: float(p.get('value', 0)),
                reverse=True
            )[:10]

            headers = ["Ticker", "Shares", "Value", "P&L", "% Portfolio"]
            rows = [
                [
                    p.get('ticker', 'N/A'),
                    str(p.get('shares', 0)),
                    f"${p.get('value', 0):,.2f}",
                    f"${p.get('pnl', 0):,.2f}",
                    f"{p.get('portfolio_pct', 0):.2f}%",
                ]
                for p in sorted_positions
            ]

            overview.top_positions = TableData(
                title="Top Positions",
                headers=headers,
                rows=rows,
            )

        return overview

    def _build_ai_performance(
        self,
        daily_analytics: DailyAnalytics,
        target_date: date,
    ) -> AIPerformance:
        """Build AI performance section."""
        performance = AIPerformance(
            signals_generated=daily_analytics.signals_generated,
            signal_avg_confidence=daily_analytics.signal_avg_confidence,
            signal_accuracy=daily_analytics.signal_accuracy,
            ai_cost_usd=daily_analytics.ai_cost_usd,
            ai_tokens_used=daily_analytics.ai_tokens_used,
        )

        # Calculate cost per signal
        if daily_analytics.signals_generated > 0:
            performance.cost_per_signal = daily_analytics.ai_cost_usd / daily_analytics.signals_generated

        # Build source comparison chart
        signal_sources = self.db.query(
            SignalPerformance.source,
            func.count(SignalPerformance.id).label('count'),
            func.avg(SignalPerformance.confidence).label('avg_confidence'),
        ).filter(
            func.date(SignalPerformance.generated_at) == target_date
        ).group_by(
            SignalPerformance.source
        ).all()

        if signal_sources:
            labels = [s.source for s in signal_sources]
            counts = [s.count for s in signal_sources]
            confidences = [float(s.avg_confidence) * 100 if s.avg_confidence else 0 for s in signal_sources]

            performance.source_comparison = ChartData(
                chart_type="bar",
                title="Signals by AI Source",
                x_labels=labels,
                datasets=[
                    {
                        "label": "Signal Count",
                        "data": counts,
                        "color": "#3b82f6",
                    },
                ],
                y_axis_label="Count",
            )

        return performance

    def _build_risk_metrics(self, daily_analytics: DailyAnalytics) -> RiskMetrics:
        """Build risk metrics section."""
        return RiskMetrics(
            sharpe_ratio=daily_analytics.sharpe_ratio,
            sortino_ratio=daily_analytics.sortino_ratio,
            max_drawdown_pct=daily_analytics.max_drawdown_pct,
            volatility_30d=daily_analytics.volatility_30d,
            var_95=daily_analytics.var_95,
            circuit_breaker_triggers=daily_analytics.circuit_breaker_triggers,
            kill_switch_active=daily_analytics.kill_switch_active,
            alerts_triggered=daily_analytics.alerts_triggered,
        )

    async def _build_performance_chart(
        self,
        target_date: date,
        lookback_days: int = 30,
    ) -> ChartData:
        """Build portfolio performance chart."""
        start_date = target_date - timedelta(days=lookback_days)

        daily_records = self.db.query(DailyAnalytics).filter(
            DailyAnalytics.date >= start_date,
            DailyAnalytics.date <= target_date,
        ).order_by(DailyAnalytics.date).all()

        if not daily_records:
            return None

        labels = [r.date.strftime("%m/%d") for r in daily_records]
        portfolio_values = [float(r.portfolio_value_eod) for r in daily_records]

        return ChartData(
            chart_type="line",
            title=f"Portfolio Value ({lookback_days} days)",
            x_labels=labels,
            datasets=[
                {
                    "label": "Portfolio Value",
                    "data": portfolio_values,
                    "color": "#10b981",
                    "fill": True,
                }
            ],
            y_axis_label="Value (USD)",
            x_axis_label="Date",
        )

    async def _build_pnl_chart(
        self,
        target_date: date,
        lookback_days: int = 30,
    ) -> ChartData:
        """Build daily P&L chart."""
        start_date = target_date - timedelta(days=lookback_days)

        daily_records = self.db.query(DailyAnalytics).filter(
            DailyAnalytics.date >= start_date,
            DailyAnalytics.date <= target_date,
        ).order_by(DailyAnalytics.date).all()

        if not daily_records:
            return None

        labels = [r.date.strftime("%m/%d") for r in daily_records]
        pnl_values = [float(r.daily_pnl) for r in daily_records]

        # Color bars based on positive/negative
        colors = ["#10b981" if pnl >= 0 else "#ef4444" for pnl in pnl_values]

        return ChartData(
            chart_type="bar",
            title=f"Daily P&L ({lookback_days} days)",
            x_labels=labels,
            datasets=[
                {
                    "label": "P&L",
                    "data": pnl_values,
                    "backgroundColor": colors,
                }
            ],
            y_axis_label="P&L (USD)",
            x_axis_label="Date",
        )

    async def generate_weekly_report(
        self,
        year: int,
        week_number: int,
    ) -> WeeklyReport:
        """
        Generate weekly report.

        Args:
            year: Year
            week_number: ISO week number (1-53)

        Returns:
            WeeklyReport object
        """
        logger.info(f"Generating weekly report for {year}-W{week_number}")

        # Get weekly analytics
        weekly_analytics = self.db.query(WeeklyAnalytics).filter(
            WeeklyAnalytics.year == year,
            WeeklyAnalytics.week_number == week_number,
        ).first()

        if not weekly_analytics:
            raise ValueError(f"No weekly analytics found for {year}-W{week_number}")

        report = WeeklyReport(
            report_id=generate_report_id("weekly", weekly_analytics.week_start_date),
            year=year,
            week_number=week_number,
            week_start_date=weekly_analytics.week_start_date,
            week_end_date=weekly_analytics.week_end_date,
            generated_at=datetime.utcnow(),
            portfolio_value_start=weekly_analytics.portfolio_value_start,
            portfolio_value_end=weekly_analytics.portfolio_value_end,
            weekly_pnl=weekly_analytics.weekly_pnl,
            weekly_return_pct=weekly_analytics.weekly_return_pct,
            total_trades=weekly_analytics.total_trades,
            win_rate=weekly_analytics.win_rate,
            best_day_date=weekly_analytics.best_day_date,
            best_day_return_pct=weekly_analytics.best_day_return_pct,
            worst_day_date=weekly_analytics.worst_day_date,
            worst_day_return_pct=weekly_analytics.worst_day_return_pct,
        )

        # Build daily P&L chart
        daily_records = self.db.query(DailyAnalytics).filter(
            DailyAnalytics.date >= weekly_analytics.week_start_date,
            DailyAnalytics.date <= weekly_analytics.week_end_date,
        ).order_by(DailyAnalytics.date).all()

        if daily_records:
            labels = [r.date.strftime("%m/%d") for r in daily_records]
            pnl_values = [float(r.daily_pnl) for r in daily_records]

            report.daily_pnl_chart = ChartData(
                chart_type="bar",
                title="Daily P&L (This Week)",
                x_labels=labels,
                datasets=[
                    {
                        "label": "P&L",
                        "data": pnl_values,
                        "backgroundColor": ["#10b981" if p >= 0 else "#ef4444" for p in pnl_values],
                    }
                ],
                y_axis_label="P&L (USD)",
            )

        logger.info(f"Weekly report generated for {year}-W{week_number}")

        return report

    async def generate_monthly_report(
        self,
        year: int,
        month: int,
    ) -> MonthlyReport:
        """
        Generate monthly report.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            MonthlyReport object
        """
        logger.info(f"Generating monthly report for {year}-{month:02d}")

        # Get monthly analytics
        monthly_analytics = self.db.query(MonthlyAnalytics).filter(
            MonthlyAnalytics.year == year,
            MonthlyAnalytics.month == month,
        ).first()

        if not monthly_analytics:
            raise ValueError(f"No monthly analytics found for {year}-{month:02d}")

        report = MonthlyReport(
            report_id=generate_report_id("monthly", date(year, month, 1)),
            year=year,
            month=month,
            generated_at=datetime.utcnow(),
            portfolio_value_start=monthly_analytics.portfolio_value_start,
            portfolio_value_end=monthly_analytics.portfolio_value_end,
            monthly_pnl=monthly_analytics.monthly_pnl,
            monthly_return_pct=monthly_analytics.monthly_return_pct,
            total_trades=monthly_analytics.total_trades,
            trading_days=monthly_analytics.trading_days,
            win_rate=monthly_analytics.win_rate,
            sharpe_ratio=monthly_analytics.sharpe_ratio,
            total_ai_cost_usd=monthly_analytics.total_ai_cost_usd,
            total_tokens_used=monthly_analytics.total_tokens_used,
        )

        # Build performance attribution
        # TODO: Implement full attribution analysis
        report.attribution = PerformanceAttribution(
            strategy_returns={},
            sector_returns={},
            ai_source_returns={},
        )

        logger.info(f"Monthly report generated for {year}-{month:02d}")

        return report
