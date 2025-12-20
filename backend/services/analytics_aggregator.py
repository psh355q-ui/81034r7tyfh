"""
Analytics Aggregator - Aggregate Prometheus metrics into database

Features:
- Daily metric aggregation from Prometheus
- Trade execution tracking
- Portfolio snapshots
- Signal performance validation
- Weekly/monthly rollups
- Automatic scheduling

Author: AI Trading System Team
Date: 2025-11-25
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
import asyncio

from backend.core.models.analytics_models import (
    DailyAnalytics,
    TradeExecution,
    PortfolioSnapshot,
    SignalPerformance,
    WeeklyAnalytics,
    MonthlyAnalytics,
)
from backend.core.database import get_db
from backend.monitoring import trading_metrics

logger = logging.getLogger(__name__)


class AnalyticsAggregator:
    """
    Aggregates metrics from Prometheus and other sources into analytics tables.

    Runs daily to create historical records for reporting.
    """

    def __init__(
        self,
        db_session: Session,
        portfolio_manager=None,
        signal_validator=None,
    ):
        """
        Initialize aggregator.

        Args:
            db_session: Database session
            portfolio_manager: Portfolio manager instance for current state
            signal_validator: Signal validator for signal performance
        """
        self.db = db_session
        self.portfolio_manager = portfolio_manager
        self.signal_validator = signal_validator

        logger.info("AnalyticsAggregator initialized")

    async def aggregate_daily_metrics(self, target_date: Optional[date] = None) -> DailyAnalytics:
        """
        Aggregate daily metrics from Prometheus.

        Args:
            target_date: Date to aggregate (defaults to yesterday)

        Returns:
            DailyAnalytics record
        """
        if target_date is None:
            target_date = (datetime.utcnow() - timedelta(days=1)).date()

        logger.info(f"Aggregating daily metrics for {target_date}")

        # Check if already exists
        existing = self.db.query(DailyAnalytics).filter(
            DailyAnalytics.date == target_date
        ).first()

        if existing:
            logger.info(f"Daily analytics for {target_date} already exists, updating...")
            daily_record = existing
        else:
            daily_record = DailyAnalytics(date=target_date)

        # Portfolio metrics
        daily_record.portfolio_value_eod = await self._get_portfolio_value_eod(target_date)
        daily_record.daily_pnl = await self._get_daily_pnl(target_date)
        daily_record.daily_return_pct = self._calculate_daily_return(
            daily_record.daily_pnl,
            daily_record.portfolio_value_eod,
        )

        # Calculate cumulative PnL
        daily_record.cumulative_pnl = await self._get_cumulative_pnl(target_date)

        # Trading activity
        trade_stats = await self._get_trade_stats(target_date)
        daily_record.total_trades = trade_stats['total']
        daily_record.buy_trades = trade_stats['buys']
        daily_record.sell_trades = trade_stats['sells']
        daily_record.total_volume_usd = trade_stats['volume_usd']

        # Performance metrics
        perf_metrics = await self._get_performance_metrics(target_date)
        daily_record.win_count = perf_metrics['win_count']
        daily_record.loss_count = perf_metrics['loss_count']
        daily_record.win_rate = perf_metrics['win_rate']
        daily_record.avg_win_pct = perf_metrics['avg_win_pct']
        daily_record.avg_loss_pct = perf_metrics['avg_loss_pct']

        # Risk metrics
        risk_metrics = await self._calculate_risk_metrics(target_date)
        daily_record.sharpe_ratio = risk_metrics.get('sharpe_ratio')
        daily_record.sortino_ratio = risk_metrics.get('sortino_ratio')
        daily_record.max_drawdown_pct = risk_metrics.get('max_drawdown_pct')
        daily_record.volatility_30d = risk_metrics.get('volatility_30d')
        daily_record.var_95 = risk_metrics.get('var_95')

        # AI metrics
        ai_metrics = await self._get_ai_metrics(target_date)
        daily_record.ai_cost_usd = ai_metrics['cost_usd']
        daily_record.ai_tokens_used = ai_metrics['tokens_used']
        daily_record.signals_generated = ai_metrics['signals_generated']
        daily_record.signal_avg_confidence = ai_metrics.get('avg_confidence')
        daily_record.signal_accuracy = ai_metrics.get('accuracy')

        # Execution quality
        exec_quality = await self._get_execution_quality(target_date)
        daily_record.avg_slippage_bps = exec_quality.get('avg_slippage_bps')
        daily_record.avg_execution_time_ms = exec_quality.get('avg_exec_time_ms')

        # Position metrics
        position_metrics = await self._get_position_metrics(target_date)
        daily_record.positions_count = position_metrics['count']
        daily_record.avg_position_size_usd = position_metrics.get('avg_size')
        daily_record.max_position_size_usd = position_metrics.get('max_size')

        # Risk management
        risk_mgmt = await self._get_risk_management_metrics(target_date)
        daily_record.circuit_breaker_triggers = risk_mgmt['circuit_breaker_triggers']
        daily_record.kill_switch_active = risk_mgmt['kill_switch_active']
        daily_record.alerts_triggered = risk_mgmt['alerts_triggered']

        # Save to database
        if not existing:
            self.db.add(daily_record)
        self.db.commit()
        self.db.refresh(daily_record)

        logger.info(
            f"Daily analytics saved for {target_date}: "
            f"Portfolio=${daily_record.portfolio_value_eod:,.2f}, "
            f"PnL=${daily_record.daily_pnl:,.2f}, "
            f"Trades={daily_record.total_trades}"
        )

        return daily_record

    async def _get_portfolio_value_eod(self, target_date: date) -> Decimal:
        """Get end-of-day portfolio value from Prometheus."""
        # In production, query Prometheus for portfolio_value_usd at EOD
        # For now, get current value from portfolio manager
        if self.portfolio_manager:
            value = await self.portfolio_manager.get_total_value()
            return Decimal(str(value))
        return Decimal('100000.00')  # Default initial value

    async def _get_daily_pnl(self, target_date: date) -> Decimal:
        """Get daily P&L from Prometheus."""
        # Query Prometheus for portfolio_daily_pnl_usd
        # For now, calculate from previous day
        previous_day = self.db.query(DailyAnalytics).filter(
            DailyAnalytics.date == target_date - timedelta(days=1)
        ).first()

        current_value = await self._get_portfolio_value_eod(target_date)

        if previous_day:
            return current_value - previous_day.portfolio_value_eod
        return Decimal('0.00')

    def _calculate_daily_return(self, pnl: Decimal, portfolio_value: Decimal) -> Optional[Decimal]:
        """Calculate daily return percentage."""
        if portfolio_value and portfolio_value > 0:
            return (pnl / portfolio_value) * 100
        return None

    async def _get_cumulative_pnl(self, target_date: date) -> Decimal:
        """Calculate cumulative PnL since inception."""
        # Sum all daily PnL up to target date
        result = self.db.query(func.sum(DailyAnalytics.daily_pnl)).filter(
            DailyAnalytics.date <= target_date
        ).scalar()

        return Decimal(str(result)) if result else Decimal('0.00')

    async def _get_trade_stats(self, target_date: date) -> Dict:
        """Get trading activity statistics."""
        # Query trade_executions table
        trades = self.db.query(TradeExecution).filter(
            func.date(TradeExecution.execution_timestamp) == target_date
        ).all()

        total = len(trades)
        buys = sum(1 for t in trades if t.action == 'BUY')
        sells = sum(1 for t in trades if t.action == 'SELL')
        volume_usd = sum(float(t.position_size_usd or 0) for t in trades)

        return {
            'total': total,
            'buys': buys,
            'sells': sells,
            'volume_usd': Decimal(str(volume_usd)),
        }

    async def _get_performance_metrics(self, target_date: date) -> Dict:
        """Get performance metrics from closed trades."""
        # Query closed trades for the day
        closed_trades = self.db.query(TradeExecution).filter(
            func.date(TradeExecution.exit_timestamp) == target_date,
            TradeExecution.status == 'CLOSED',
        ).all()

        if not closed_trades:
            return {
                'win_count': 0,
                'loss_count': 0,
                'win_rate': None,
                'avg_win_pct': None,
                'avg_loss_pct': None,
            }

        wins = [t for t in closed_trades if t.is_win]
        losses = [t for t in closed_trades if not t.is_win]

        win_count = len(wins)
        loss_count = len(losses)
        win_rate = Decimal(str(win_count / len(closed_trades))) if closed_trades else None

        avg_win_pct = None
        if wins:
            avg_win_pct = Decimal(str(sum(float(t.pnl_pct or 0) for t in wins) / len(wins)))

        avg_loss_pct = None
        if losses:
            avg_loss_pct = Decimal(str(sum(float(t.pnl_pct or 0) for t in losses) / len(losses)))

        return {
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate,
            'avg_win_pct': avg_win_pct,
            'avg_loss_pct': avg_loss_pct,
        }

    async def _calculate_risk_metrics(self, target_date: date) -> Dict:
        """Calculate risk metrics."""
        # Get last 30 days of returns
        thirty_days_ago = target_date - timedelta(days=30)
        daily_records = self.db.query(DailyAnalytics).filter(
            DailyAnalytics.date >= thirty_days_ago,
            DailyAnalytics.date <= target_date,
        ).order_by(DailyAnalytics.date).all()

        if len(daily_records) < 5:
            return {}

        returns = [float(r.daily_return_pct or 0) for r in daily_records if r.daily_return_pct]

        if not returns:
            return {}

        # Calculate Sharpe Ratio
        import numpy as np
        returns_array = np.array(returns)
        avg_return = np.mean(returns_array)
        std_return = np.std(returns_array)

        # Annualized Sharpe (assuming 252 trading days)
        sharpe_ratio = None
        if std_return > 0:
            sharpe_ratio = Decimal(str((avg_return / std_return) * np.sqrt(252)))

        # Calculate Sortino Ratio (downside deviation)
        downside_returns = [r for r in returns if r < 0]
        sortino_ratio = None
        if downside_returns:
            downside_std = np.std(downside_returns)
            if downside_std > 0:
                sortino_ratio = Decimal(str((avg_return / downside_std) * np.sqrt(252)))

        # Calculate Maximum Drawdown
        cumulative_returns = np.cumprod(1 + returns_array / 100)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max * 100
        max_drawdown = Decimal(str(np.min(drawdowns)))

        # Calculate 30-day volatility (annualized)
        volatility_30d = Decimal(str(std_return * np.sqrt(252)))

        # Calculate VaR (95% confidence)
        var_95_pct = np.percentile(returns_array, 5)
        portfolio_value = await self._get_portfolio_value_eod(target_date)
        var_95 = portfolio_value * Decimal(str(var_95_pct / 100))

        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown_pct': max_drawdown,
            'volatility_30d': volatility_30d,
            'var_95': var_95,
        }

    async def _get_ai_metrics(self, target_date: date) -> Dict:
        """Get AI cost and performance metrics."""
        # In production, query Prometheus for ai_cost_usd_total, ai_tokens_used_total
        # For now, query signal_performance table
        signals = self.db.query(SignalPerformance).filter(
            func.date(SignalPerformance.generated_at) == target_date
        ).all()

        signals_generated = len(signals)

        avg_confidence = None
        if signals:
            avg_confidence = Decimal(str(sum(float(s.confidence or 0) for s in signals) / len(signals)))

        # Calculate accuracy for resolved signals
        resolved_signals = [s for s in signals if s.status == 'RESOLVED']
        accuracy = None
        if resolved_signals:
            wins = sum(1 for s in resolved_signals if s.outcome == 'WIN')
            accuracy = Decimal(str(wins / len(resolved_signals)))

        return {
            'cost_usd': Decimal('0.00'),  # TODO: Query from cost tracking
            'tokens_used': 0,  # TODO: Query from cost tracking
            'signals_generated': signals_generated,
            'avg_confidence': avg_confidence,
            'accuracy': accuracy,
        }

    async def _get_execution_quality(self, target_date: date) -> Dict:
        """Get execution quality metrics."""
        trades = self.db.query(TradeExecution).filter(
            func.date(TradeExecution.execution_timestamp) == target_date
        ).all()

        if not trades:
            return {}

        avg_slippage = sum(float(t.slippage_bps or 0) for t in trades) / len(trades)
        avg_exec_time = sum(float(t.execution_time_ms or 0) for t in trades) / len(trades)

        return {
            'avg_slippage_bps': Decimal(str(avg_slippage)),
            'avg_exec_time_ms': Decimal(str(avg_exec_time)),
        }

    async def _get_position_metrics(self, target_date: date) -> Dict:
        """Get position sizing metrics."""
        # Get snapshot for target date
        snapshot = self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.snapshot_date == target_date
        ).first()

        if not snapshot:
            return {'count': 0}

        positions = snapshot.positions or []

        avg_size = None
        max_size = None
        if positions:
            sizes = [float(p.get('value', 0)) for p in positions]
            avg_size = Decimal(str(sum(sizes) / len(sizes)))
            max_size = Decimal(str(max(sizes)))

        return {
            'count': len(positions),
            'avg_size': avg_size,
            'max_size': max_size,
        }

    async def _get_risk_management_metrics(self, target_date: date) -> Dict:
        """Get risk management trigger metrics."""
        # TODO: Query from monitoring system
        return {
            'circuit_breaker_triggers': 0,
            'kill_switch_active': False,
            'alerts_triggered': 0,
        }

    async def create_portfolio_snapshot(self, target_date: Optional[date] = None) -> PortfolioSnapshot:
        """
        Create daily portfolio snapshot.

        Args:
            target_date: Date for snapshot (defaults to today)

        Returns:
            PortfolioSnapshot record
        """
        if target_date is None:
            target_date = datetime.utcnow().date()

        logger.info(f"Creating portfolio snapshot for {target_date}")

        # Check if already exists
        existing = self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.snapshot_date == target_date
        ).first()

        if existing:
            logger.info(f"Snapshot for {target_date} already exists")
            return existing

        snapshot = PortfolioSnapshot(
            snapshot_date=target_date,
            snapshot_timestamp=datetime.utcnow(),
        )

        # Get portfolio state from portfolio manager
        if self.portfolio_manager:
            portfolio_state = await self.portfolio_manager.get_portfolio_state()

            snapshot.total_value = Decimal(str(portfolio_state['total_value']))
            snapshot.cash = Decimal(str(portfolio_state['cash']))
            snapshot.invested_value = Decimal(str(portfolio_state['invested_value']))
            snapshot.positions = portfolio_state['positions']
            snapshot.positions_count = len(portfolio_state['positions'])

            # Calculate allocations
            snapshot.sector_allocation = self._calculate_sector_allocation(portfolio_state['positions'])
            snapshot.strategy_allocation = self._calculate_strategy_allocation(portfolio_state['positions'])

            # Risk metrics
            if snapshot.total_value > 0:
                snapshot.cash_pct = (snapshot.cash / snapshot.total_value)
                if portfolio_state['positions']:
                    largest_position = max(
                        float(p.get('value', 0)) for p in portfolio_state['positions']
                    )
                    snapshot.largest_position_pct = Decimal(str((largest_position / float(snapshot.total_value))))

            # Performance metrics
            snapshot.total_pnl = await self._get_cumulative_pnl(target_date)
            if snapshot.total_value > 0:
                initial_value = Decimal('100000.00')  # TODO: Get from config
                snapshot.total_return_pct = ((snapshot.total_value - initial_value) / initial_value) * 100

        # Save
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)

        logger.info(f"Portfolio snapshot created: ${snapshot.total_value:,.2f}, {snapshot.positions_count} positions")

        return snapshot

    def _calculate_sector_allocation(self, positions: List[Dict]) -> Dict:
        """Calculate allocation by sector."""
        sector_totals = {}
        total_value = sum(float(p.get('value', 0)) for p in positions)

        for position in positions:
            sector = position.get('sector', 'Unknown')
            value = float(position.get('value', 0))
            sector_totals[sector] = sector_totals.get(sector, 0) + value

        # Convert to percentages
        if total_value > 0:
            return {
                sector: round((value / total_value) * 100, 2)
                for sector, value in sector_totals.items()
            }
        return {}

    def _calculate_strategy_allocation(self, positions: List[Dict]) -> Dict:
        """Calculate allocation by strategy."""
        strategy_totals = {}
        total_value = sum(float(p.get('value', 0)) for p in positions)

        for position in positions:
            strategy = position.get('strategy', 'Unknown')
            value = float(position.get('value', 0))
            strategy_totals[strategy] = strategy_totals.get(strategy, 0) + value

        # Convert to percentages
        if total_value > 0:
            return {
                strategy: round((value / total_value) * 100, 2)
                for strategy, value in strategy_totals.items()
            }
        return {}

    async def aggregate_weekly_metrics(self, year: int, week_number: int) -> WeeklyAnalytics:
        """
        Aggregate weekly metrics from daily analytics.

        Args:
            year: Year
            week_number: ISO week number (1-53)

        Returns:
            WeeklyAnalytics record
        """
        logger.info(f"Aggregating weekly metrics for {year}-W{week_number}")

        # Calculate week start/end dates
        from datetime import datetime, timedelta
        first_day = datetime.strptime(f'{year}-W{week_number}-1', '%Y-W%W-%w').date()
        last_day = first_day + timedelta(days=6)

        # Get daily records for the week
        daily_records = self.db.query(DailyAnalytics).filter(
            DailyAnalytics.date >= first_day,
            DailyAnalytics.date <= last_day,
        ).order_by(DailyAnalytics.date).all()

        if not daily_records:
            logger.warning(f"No daily records for week {year}-W{week_number}")
            return None

        # Check if already exists
        existing = self.db.query(WeeklyAnalytics).filter(
            WeeklyAnalytics.year == year,
            WeeklyAnalytics.week_number == week_number,
        ).first()

        if existing:
            weekly = existing
        else:
            weekly = WeeklyAnalytics(
                year=year,
                week_number=week_number,
                week_start_date=first_day,
                week_end_date=last_day,
            )

        # Aggregate metrics
        weekly.portfolio_value_start = daily_records[0].portfolio_value_eod
        weekly.portfolio_value_end = daily_records[-1].portfolio_value_eod
        weekly.weekly_pnl = sum(float(r.daily_pnl or 0) for r in daily_records)
        weekly.weekly_pnl = Decimal(str(weekly.weekly_pnl))

        if weekly.portfolio_value_start > 0:
            weekly.weekly_return_pct = (
                (weekly.portfolio_value_end - weekly.portfolio_value_start) /
                weekly.portfolio_value_start * 100
            )

        # Trading activity
        weekly.total_trades = sum(r.total_trades for r in daily_records)
        weekly.total_volume_usd = Decimal(str(sum(float(r.total_volume_usd or 0) for r in daily_records)))
        weekly.avg_daily_trades = Decimal(str(weekly.total_trades / len(daily_records)))

        # Performance
        weekly.win_count = sum(r.win_count for r in daily_records)
        weekly.loss_count = sum(r.loss_count for r in daily_records)
        total_closed = weekly.win_count + weekly.loss_count
        weekly.win_rate = Decimal(str(weekly.win_count / total_closed)) if total_closed > 0 else None

        # Risk metrics
        sharpe_ratios = [float(r.sharpe_ratio) for r in daily_records if r.sharpe_ratio]
        weekly.sharpe_ratio = Decimal(str(sum(sharpe_ratios) / len(sharpe_ratios))) if sharpe_ratios else None

        drawdowns = [float(r.max_drawdown_pct) for r in daily_records if r.max_drawdown_pct]
        weekly.max_drawdown_pct = Decimal(str(min(drawdowns))) if drawdowns else None

        # AI costs
        weekly.total_ai_cost_usd = Decimal(str(sum(float(r.ai_cost_usd or 0) for r in daily_records)))
        weekly.avg_daily_ai_cost = weekly.total_ai_cost_usd / len(daily_records)

        # Best/worst days
        best_day = max(daily_records, key=lambda r: float(r.daily_return_pct or 0))
        worst_day = min(daily_records, key=lambda r: float(r.daily_return_pct or 0))
        weekly.best_day_date = best_day.date
        weekly.best_day_return_pct = best_day.daily_return_pct
        weekly.worst_day_date = worst_day.date
        weekly.worst_day_return_pct = worst_day.daily_return_pct

        # Save
        if not existing:
            self.db.add(weekly)
        self.db.commit()
        self.db.refresh(weekly)

        logger.info(f"Weekly analytics saved for {year}-W{week_number}: PnL=${weekly.weekly_pnl:,.2f}")

        return weekly

    async def aggregate_monthly_metrics(self, year: int, month: int) -> MonthlyAnalytics:
        """
        Aggregate monthly metrics from daily/weekly analytics.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            MonthlyAnalytics record
        """
        logger.info(f"Aggregating monthly metrics for {year}-{month:02d}")

        # Get daily records for the month
        from calendar import monthrange
        _, last_day = monthrange(year, month)

        first_date = date(year, month, 1)
        last_date = date(year, month, last_day)

        daily_records = self.db.query(DailyAnalytics).filter(
            DailyAnalytics.date >= first_date,
            DailyAnalytics.date <= last_date,
        ).order_by(DailyAnalytics.date).all()

        if not daily_records:
            logger.warning(f"No daily records for {year}-{month:02d}")
            return None

        # Check if already exists
        existing = self.db.query(MonthlyAnalytics).filter(
            MonthlyAnalytics.year == year,
            MonthlyAnalytics.month == month,
        ).first()

        if existing:
            monthly = existing
        else:
            monthly = MonthlyAnalytics(year=year, month=month)

        # Aggregate metrics
        monthly.portfolio_value_start = daily_records[0].portfolio_value_eod
        monthly.portfolio_value_end = daily_records[-1].portfolio_value_eod
        monthly.monthly_pnl = Decimal(str(sum(float(r.daily_pnl or 0) for r in daily_records)))

        if monthly.portfolio_value_start > 0:
            monthly.monthly_return_pct = (
                (monthly.portfolio_value_end - monthly.portfolio_value_start) /
                monthly.portfolio_value_start * 100
            )

        # Trading activity
        monthly.total_trades = sum(r.total_trades for r in daily_records)
        monthly.total_volume_usd = Decimal(str(sum(float(r.total_volume_usd or 0) for r in daily_records)))
        monthly.trading_days = len(daily_records)

        # Performance
        monthly.win_count = sum(r.win_count for r in daily_records)
        monthly.loss_count = sum(r.loss_count for r in daily_records)
        total_closed = monthly.win_count + monthly.loss_count
        monthly.win_rate = Decimal(str(monthly.win_count / total_closed)) if total_closed > 0 else None

        # Risk metrics
        sharpe_ratios = [float(r.sharpe_ratio) for r in daily_records if r.sharpe_ratio]
        monthly.sharpe_ratio = Decimal(str(sum(sharpe_ratios) / len(sharpe_ratios))) if sharpe_ratios else None

        sortino_ratios = [float(r.sortino_ratio) for r in daily_records if r.sortino_ratio]
        monthly.sortino_ratio = Decimal(str(sum(sortino_ratios) / len(sortino_ratios))) if sortino_ratios else None

        drawdowns = [float(r.max_drawdown_pct) for r in daily_records if r.max_drawdown_pct]
        monthly.max_drawdown_pct = Decimal(str(min(drawdowns))) if drawdowns else None

        # AI costs
        monthly.total_ai_cost_usd = Decimal(str(sum(float(r.ai_cost_usd or 0) for r in daily_records)))
        monthly.avg_daily_ai_cost = monthly.total_ai_cost_usd / monthly.trading_days
        monthly.total_tokens_used = sum(r.ai_tokens_used for r in daily_records)

        # Save
        if not existing:
            self.db.add(monthly)
        self.db.commit()
        self.db.refresh(monthly)

        logger.info(f"Monthly analytics saved for {year}-{month:02d}: PnL=${monthly.monthly_pnl:,.2f}")

        return monthly

    async def run_daily_aggregation(self):
        """
        Run complete daily aggregation workflow.

        Should be scheduled to run daily after market close.
        """
        target_date = (datetime.utcnow() - timedelta(days=1)).date()

        logger.info(f"Starting daily aggregation workflow for {target_date}")

        try:
            # 1. Aggregate daily metrics
            await self.aggregate_daily_metrics(target_date)

            # 2. Create portfolio snapshot
            await self.create_portfolio_snapshot(target_date)

            # 3. Check if we need weekly aggregation (Sunday)
            if target_date.weekday() == 6:  # Sunday
                iso_year, iso_week, _ = target_date.isocalendar()
                await self.aggregate_weekly_metrics(iso_year, iso_week)

            # 4. Check if we need monthly aggregation (last day of month)
            from calendar import monthrange
            _, last_day = monthrange(target_date.year, target_date.month)
            if target_date.day == last_day:
                await self.aggregate_monthly_metrics(target_date.year, target_date.month)

            # 5. Refresh materialized view
            self.db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY analytics_summary;")
            self.db.commit()

            logger.info(f"Daily aggregation workflow completed successfully for {target_date}")

        except Exception as e:
            logger.error(f"Error in daily aggregation workflow: {e}", exc_info=True)
            self.db.rollback()
            raise
