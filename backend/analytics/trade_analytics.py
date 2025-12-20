"""
Trade Analytics - Analyze trading patterns and execution quality

Features:
- Trade pattern analysis
- Execution quality metrics
- Slippage analysis
- Win/loss analysis
- Optimal entry/exit timing
- Trade duration analysis

Author: AI Trading System Team
Date: 2025-11-25
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from collections import defaultdict
import numpy as np

from backend.core.models.analytics_models import (
    DailyAnalytics,
    TradeExecution,
)

logger = logging.getLogger(__name__)


class TradeAnalyzer:
    """
    Analyzes trading patterns and execution quality.

    Provides insights into:
    - Win/loss patterns
    - Execution quality
    - Optimal timing
    - Trade characteristics
    """

    def __init__(self, db_session: Session):
        """
        Initialize trade analyzer.

        Args:
            db_session: Database session
        """
        self.db = db_session
        logger.info("TradeAnalyzer initialized")

    async def analyze_win_loss_patterns(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """
        Analyze win/loss patterns.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Win/loss analysis
        """
        logger.info(f"Analyzing win/loss patterns from {start_date} to {end_date}")

        # Get closed trades
        stmt = select(TradeExecution).where(

            
            TradeExecution.exit_timestamp.isnot(None),
            func.date(TradeExecution.exit_timestamp) >= start_date,
            func.date(TradeExecution.exit_timestamp) <= end_date,
            TradeExecution.status == 'CLOSED',
        

        )

        result = await self.db.execute(stmt)

        trades = result.scalars().all()

        if not trades:
            return {'message': 'No closed trades in period'}

        # Separate wins and losses
        wins = [t for t in trades if t.is_win]
        losses = [t for t in trades if not t.is_win]

        # Calculate statistics
        win_pnls = [float(t.pnl_usd) for t in wins if t.pnl_usd]
        loss_pnls = [float(t.pnl_usd) for t in losses if t.pnl_usd]

        win_returns = [float(t.pnl_pct) for t in wins if t.pnl_pct]
        loss_returns = [float(t.pnl_pct) for t in losses if t.pnl_pct]

        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_trades': len(trades),
            'wins': {
                'count': len(wins),
                'win_rate': len(wins) / len(trades) if trades else 0,
                'avg_pnl': np.mean(win_pnls) if win_pnls else 0,
                'median_pnl': np.median(win_pnls) if win_pnls else 0,
                'max_pnl': max(win_pnls) if win_pnls else 0,
                'avg_return_pct': np.mean(win_returns) if win_returns else 0,
                'total_pnl': sum(win_pnls) if win_pnls else 0,
            },
            'losses': {
                'count': len(losses),
                'loss_rate': len(losses) / len(trades) if trades else 0,
                'avg_pnl': np.mean(loss_pnls) if loss_pnls else 0,
                'median_pnl': np.median(loss_pnls) if loss_pnls else 0,
                'max_loss': min(loss_pnls) if loss_pnls else 0,
                'avg_return_pct': np.mean(loss_returns) if loss_returns else 0,
                'total_pnl': sum(loss_pnls) if loss_pnls else 0,
            },
            'metrics': {
                'profit_factor': abs(sum(win_pnls) / sum(loss_pnls)) if loss_pnls and sum(loss_pnls) != 0 else 0,
                'avg_win_to_loss_ratio': (np.mean(win_pnls) / abs(np.mean(loss_pnls))) if loss_pnls and np.mean(loss_pnls) != 0 else 0,
                'expectancy': (len(wins) * np.mean(win_pnls) + len(losses) * np.mean(loss_pnls)) / len(trades) if trades and win_pnls and loss_pnls else 0,
            }
        }

        logger.info(f"Win/loss analysis complete: {len(wins)} wins, {len(losses)} losses")

        return result

    async def analyze_execution_quality(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """
        Analyze execution quality metrics.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Execution quality analysis
        """
        logger.info(f"Analyzing execution quality from {start_date} to {end_date}")

        # Get all trades
        stmt = select(TradeExecution).where(

            
            func.date(TradeExecution.execution_timestamp) >= start_date,
            func.date(TradeExecution.execution_timestamp) <= end_date,
        

        )

        result = await self.db.execute(stmt)

        trades = result.scalars().all()

        if not trades:
            return {'message': 'No trades in period'}

        # Slippage analysis
        slippages = [float(t.slippage_bps) for t in trades if t.slippage_bps is not None]
        execution_times = [float(t.execution_time_ms) for t in trades if t.execution_time_ms is not None]

        # Group by action
        buy_trades = [t for t in trades if t.action == 'BUY']
        sell_trades = [t for t in trades if t.action == 'SELL']

        buy_slippages = [float(t.slippage_bps) for t in buy_trades if t.slippage_bps is not None]
        sell_slippages = [float(t.slippage_bps) for t in sell_trades if t.slippage_bps is not None]

        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_trades': len(trades),
            'slippage': {
                'avg_slippage_bps': np.mean(slippages) if slippages else 0,
                'median_slippage_bps': np.median(slippages) if slippages else 0,
                'max_slippage_bps': max(slippages) if slippages else 0,
                'min_slippage_bps': min(slippages) if slippages else 0,
                'std_slippage_bps': np.std(slippages) if slippages else 0,
                'buy_avg_slippage': np.mean(buy_slippages) if buy_slippages else 0,
                'sell_avg_slippage': np.mean(sell_slippages) if sell_slippages else 0,
            },
            'execution_time': {
                'avg_time_ms': np.mean(execution_times) if execution_times else 0,
                'median_time_ms': np.median(execution_times) if execution_times else 0,
                'max_time_ms': max(execution_times) if execution_times else 0,
                'min_time_ms': min(execution_times) if execution_times else 0,
            },
            'position_sizing': {
                'avg_position_size': np.mean([float(t.position_size_usd) for t in trades]),
                'median_position_size': np.median([float(t.position_size_usd) for t in trades]),
                'max_position_size': max([float(t.position_size_usd) for t in trades]),
            }
        }

        logger.info(f"Execution quality analysis complete: avg slippage = {result['slippage']['avg_slippage_bps']:.2f} bps")

        return result

    async def analyze_hold_duration_patterns(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """
        Analyze trade hold duration patterns.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Hold duration analysis
        """
        logger.info(f"Analyzing hold duration patterns from {start_date} to {end_date}")

        # Get closed trades
        stmt = select(TradeExecution).where(

            
            TradeExecution.exit_timestamp.isnot(None),
            func.date(TradeExecution.exit_timestamp) >= start_date,
            func.date(TradeExecution.exit_timestamp) <= end_date,
            TradeExecution.status == 'CLOSED',
        

        )

        result = await self.db.execute(stmt)

        trades = result.scalars().all()

        if not trades:
            return {'message': 'No closed trades in period'}

        # Separate by outcome
        wins = [t for t in trades if t.is_win and t.hold_duration_hours]
        losses = [t for t in trades if not t.is_win and t.hold_duration_hours]

        win_durations = [float(t.hold_duration_hours) for t in wins]
        loss_durations = [float(t.hold_duration_hours) for t in losses]
        all_durations = [float(t.hold_duration_hours) for t in trades if t.hold_duration_hours]

        # Duration buckets
        duration_buckets = {
            'less_than_1h': 0,
            '1h_to_4h': 0,
            '4h_to_1day': 0,
            '1day_to_3days': 0,
            '3days_to_7days': 0,
            'more_than_7days': 0,
        }

        for duration in all_durations:
            if duration < 1:
                duration_buckets['less_than_1h'] += 1
            elif duration < 4:
                duration_buckets['1h_to_4h'] += 1
            elif duration < 24:
                duration_buckets['4h_to_1day'] += 1
            elif duration < 72:
                duration_buckets['1day_to_3days'] += 1
            elif duration < 168:
                duration_buckets['3days_to_7days'] += 1
            else:
                duration_buckets['more_than_7days'] += 1

        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_trades': len(trades),
            'overall': {
                'avg_hold_hours': np.mean(all_durations) if all_durations else 0,
                'median_hold_hours': np.median(all_durations) if all_durations else 0,
                'max_hold_hours': max(all_durations) if all_durations else 0,
                'min_hold_hours': min(all_durations) if all_durations else 0,
            },
            'winning_trades': {
                'avg_hold_hours': np.mean(win_durations) if win_durations else 0,
                'median_hold_hours': np.median(win_durations) if win_durations else 0,
            },
            'losing_trades': {
                'avg_hold_hours': np.mean(loss_durations) if loss_durations else 0,
                'median_hold_hours': np.median(loss_durations) if loss_durations else 0,
            },
            'duration_distribution': duration_buckets,
        }

        logger.info(f"Hold duration analysis complete: avg = {result['overall']['avg_hold_hours']:.2f}h")

        return result

    async def analyze_confidence_impact(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """
        Analyze impact of AI confidence on outcomes.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Confidence impact analysis
        """
        logger.info(f"Analyzing confidence impact from {start_date} to {end_date}")

        # Get closed trades with confidence scores
        stmt = select(TradeExecution).where(

            
            TradeExecution.exit_timestamp.isnot(None),
            func.date(TradeExecution.exit_timestamp) >= start_date,
            func.date(TradeExecution.exit_timestamp) <= end_date,
            TradeExecution.status == 'CLOSED',
            TradeExecution.signal_confidence.isnot(None),
        

        )

        result = await self.db.execute(stmt)

        trades = result.scalars().all()

        if not trades:
            return {'message': 'No trades with confidence scores in period'}

        # Confidence buckets
        confidence_buckets = {
            '0.5-0.6': {'trades': [], 'wins': 0},
            '0.6-0.7': {'trades': [], 'wins': 0},
            '0.7-0.8': {'trades': [], 'wins': 0},
            '0.8-0.9': {'trades': [], 'wins': 0},
            '0.9-1.0': {'trades': [], 'wins': 0},
        }

        for trade in trades:
            confidence = float(trade.signal_confidence)

            # Determine bucket
            if confidence < 0.6:
                bucket = '0.5-0.6'
            elif confidence < 0.7:
                bucket = '0.6-0.7'
            elif confidence < 0.8:
                bucket = '0.7-0.8'
            elif confidence < 0.9:
                bucket = '0.8-0.9'
            else:
                bucket = '0.9-1.0'

            confidence_buckets[bucket]['trades'].append(trade)
            if trade.is_win:
                confidence_buckets[bucket]['wins'] += 1

        # Calculate metrics per bucket
        bucket_stats = {}
        for bucket, data in confidence_buckets.items():
            trades_list = data['trades']
            if trades_list:
                pnls = [float(t.pnl_usd) for t in trades_list if t.pnl_usd]
                returns = [float(t.pnl_pct) for t in trades_list if t.pnl_pct]

                bucket_stats[bucket] = {
                    'count': len(trades_list),
                    'win_count': data['wins'],
                    'win_rate': data['wins'] / len(trades_list),
                    'avg_pnl': np.mean(pnls) if pnls else 0,
                    'avg_return_pct': np.mean(returns) if returns else 0,
                }

        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_trades': len(trades),
            'confidence_buckets': bucket_stats,
            'correlation': {
                'confidence_vs_winrate': 'Positive' if bucket_stats.get('0.9-1.0', {}).get('win_rate', 0) > bucket_stats.get('0.5-0.6', {}).get('win_rate', 0) else 'Negative',
            }
        }

        logger.info(f"Confidence impact analysis complete: {len(trades)} trades analyzed")

        return result

    async def analyze_entry_exit_timing(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """
        Analyze optimal entry/exit timing.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Timing analysis
        """
        logger.info(f"Analyzing entry/exit timing from {start_date} to {end_date}")

        # Get all trades
        stmt = select(TradeExecution).where(

            
            func.date(TradeExecution.execution_timestamp) >= start_date,
            func.date(TradeExecution.execution_timestamp) <= end_date,
        

        )

        result = await self.db.execute(stmt)

        trades = result.scalars().all()

        if not trades:
            return {'message': 'No trades in period'}

        # Hour of day analysis
        entry_hours = defaultdict(lambda: {'count': 0, 'total_pnl': 0, 'wins': 0})

        for trade in trades:
            hour = trade.execution_timestamp.hour

            entry_hours[hour]['count'] += 1
            if trade.pnl_usd:
                entry_hours[hour]['total_pnl'] += float(trade.pnl_usd)
            if trade.is_win:
                entry_hours[hour]['wins'] += 1

        # Calculate metrics per hour
        hour_stats = {}
        for hour, data in entry_hours.items():
            if data['count'] > 0:
                hour_stats[hour] = {
                    'trades': data['count'],
                    'avg_pnl': data['total_pnl'] / data['count'],
                    'win_rate': data['wins'] / data['count'],
                }

        # Find best/worst hours
        if hour_stats:
            best_hour = max(hour_stats.items(), key=lambda x: x[1]['avg_pnl'])
            worst_hour = min(hour_stats.items(), key=lambda x: x[1]['avg_pnl'])
        else:
            best_hour = worst_hour = None

        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_trades': len(trades),
            'by_hour': hour_stats,
            'best_hour': {
                'hour': best_hour[0] if best_hour else None,
                'avg_pnl': best_hour[1]['avg_pnl'] if best_hour else 0,
                'win_rate': best_hour[1]['win_rate'] if best_hour else 0,
            } if best_hour else None,
            'worst_hour': {
                'hour': worst_hour[0] if worst_hour else None,
                'avg_pnl': worst_hour[1]['avg_pnl'] if worst_hour else 0,
                'win_rate': worst_hour[1]['win_rate'] if worst_hour else 0,
            } if worst_hour else None,
        }

        logger.info(f"Entry/exit timing analysis complete")

        return result

    async def get_trade_insights(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """
        Get comprehensive trade insights.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Complete trade analytics
        """
        logger.info(f"Generating comprehensive trade insights from {start_date} to {end_date}")

        try:
            # Get all analyses
            win_loss = await self.analyze_win_loss_patterns(start_date, end_date)
            execution = await self.analyze_execution_quality(start_date, end_date)
            duration = await self.analyze_hold_duration_patterns(start_date, end_date)
            confidence = await self.analyze_confidence_impact(start_date, end_date)
            timing = await self.analyze_entry_exit_timing(start_date, end_date)

            result = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                },
                'win_loss_analysis': win_loss,
                'execution_quality': execution,
                'hold_duration': duration,
                'confidence_impact': confidence,
                'timing_analysis': timing,
                'generated_at': datetime.utcnow().isoformat(),
            }

            logger.info("Comprehensive trade insights generated")

            return result

        except Exception as e:
            logger.error(f"Error generating trade insights: {e}", exc_info=True)
            raise
