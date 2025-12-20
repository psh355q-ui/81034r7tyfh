"""
Performance Attribution - Analyze what drove portfolio returns

Features:
- Strategy-based attribution
- Sector-based attribution
- AI source attribution
- Time period analysis
- Factor decomposition

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

from backend.core.models.analytics_models import (
    DailyAnalytics,
    TradeExecution,
    PortfolioSnapshot,
)

logger = logging.getLogger(__name__)


class PerformanceAttributionAnalyzer:
    """
    Analyzes portfolio performance attribution.

    Breaks down returns by various dimensions:
    - Strategy
    - Sector
    - AI Source
    - Individual positions
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize analyzer.

        Args:
            db_session: Database session
        """
        self.db = db_session
        logger.info("PerformanceAttributionAnalyzer initialized")

    async def analyze_strategy_attribution(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Dict]:
        """
        Analyze returns by strategy.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary of strategy attribution
        """
        logger.info(f"Analyzing strategy attribution from {start_date} to {end_date}")

        # Get all closed trades in period
        stmt = select(TradeExecution).where(

            
            TradeExecution.exit_timestamp.isnot(None),
            func.date(TradeExecution.exit_timestamp) >= start_date,
            func.date(TradeExecution.exit_timestamp) <= end_date,
            TradeExecution.status == 'CLOSED',
        

        )

        result = await self.db.execute(stmt)

        trades = result.scalars().all()

        # Group by strategy
        strategy_stats = defaultdict(lambda: {
            'total_pnl': Decimal('0'),
            'total_trades': 0,
            'win_count': 0,
            'loss_count': 0,
            'avg_return_pct': Decimal('0'),
            'total_volume': Decimal('0'),
            'contribution_pct': Decimal('0'),
        })

        total_pnl = Decimal('0')

        for trade in trades:
            strategy = trade.strategy_name or 'Unknown'
            pnl = trade.pnl_usd or Decimal('0')

            strategy_stats[strategy]['total_pnl'] += pnl
            strategy_stats[strategy]['total_trades'] += 1
            strategy_stats[strategy]['total_volume'] += trade.position_size_usd or Decimal('0')

            if trade.is_win:
                strategy_stats[strategy]['win_count'] += 1
            else:
                strategy_stats[strategy]['loss_count'] += 1

            total_pnl += pnl

        # Calculate percentages and averages
        for strategy, stats in strategy_stats.items():
            if stats['total_trades'] > 0:
                stats['win_rate'] = stats['win_count'] / stats['total_trades']

            if total_pnl != 0:
                stats['contribution_pct'] = (stats['total_pnl'] / total_pnl) * 100

        # Convert to regular dict and format
        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_pnl': float(total_pnl),
            'strategies': {
                strategy: {
                    'total_pnl': float(stats['total_pnl']),
                    'total_trades': stats['total_trades'],
                    'win_count': stats['win_count'],
                    'loss_count': stats['loss_count'],
                    'win_rate': float(stats.get('win_rate', 0)),
                    'total_volume': float(stats['total_volume']),
                    'contribution_pct': float(stats['contribution_pct']),
                }
                for strategy, stats in strategy_stats.items()
            }
        }

        logger.info(f"Strategy attribution analysis complete: {len(strategy_stats)} strategies")

        return result

    async def analyze_sector_attribution(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Dict]:
        """
        Analyze returns by sector.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary of sector attribution
        """
        logger.info(f"Analyzing sector attribution from {start_date} to {end_date}")

        # Get all closed trades in period
        stmt = select(TradeExecution).where(

            
            TradeExecution.exit_timestamp.isnot(None),
            func.date(TradeExecution.exit_timestamp) >= start_date,
            func.date(TradeExecution.exit_timestamp) <= end_date,
            TradeExecution.status == 'CLOSED',
        

        )

        result = await self.db.execute(stmt)

        trades = result.scalars().all()

        # Group by sector
        sector_stats = defaultdict(lambda: {
            'total_pnl': Decimal('0'),
            'total_trades': 0,
            'win_count': 0,
            'loss_count': 0,
            'total_volume': Decimal('0'),
            'contribution_pct': Decimal('0'),
            'tickers': set(),
        })

        total_pnl = Decimal('0')

        for trade in trades:
            sector = trade.sector or 'Unknown'
            pnl = trade.pnl_usd or Decimal('0')

            sector_stats[sector]['total_pnl'] += pnl
            sector_stats[sector]['total_trades'] += 1
            sector_stats[sector]['total_volume'] += trade.position_size_usd or Decimal('0')
            sector_stats[sector]['tickers'].add(trade.ticker)

            if trade.is_win:
                sector_stats[sector]['win_count'] += 1
            else:
                sector_stats[sector]['loss_count'] += 1

            total_pnl += pnl

        # Calculate percentages
        for sector, stats in sector_stats.items():
            if stats['total_trades'] > 0:
                stats['win_rate'] = stats['win_count'] / stats['total_trades']

            if total_pnl != 0:
                stats['contribution_pct'] = (stats['total_pnl'] / total_pnl) * 100

        # Format result
        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_pnl': float(total_pnl),
            'sectors': {
                sector: {
                    'total_pnl': float(stats['total_pnl']),
                    'total_trades': stats['total_trades'],
                    'win_count': stats['win_count'],
                    'loss_count': stats['loss_count'],
                    'win_rate': float(stats.get('win_rate', 0)),
                    'total_volume': float(stats['total_volume']),
                    'contribution_pct': float(stats['contribution_pct']),
                    'unique_tickers': len(stats['tickers']),
                }
                for sector, stats in sector_stats.items()
            }
        }

        logger.info(f"Sector attribution analysis complete: {len(sector_stats)} sectors")

        return result

    async def analyze_ai_source_attribution(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Dict]:
        """
        Analyze returns by AI source.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary of AI source attribution
        """
        logger.info(f"Analyzing AI source attribution from {start_date} to {end_date}")

        # Get all closed trades in period
        stmt = select(TradeExecution).where(

            
            TradeExecution.exit_timestamp.isnot(None),
            func.date(TradeExecution.exit_timestamp) >= start_date,
            func.date(TradeExecution.exit_timestamp) <= end_date,
            TradeExecution.status == 'CLOSED',
        

        )

        result = await self.db.execute(stmt)

        trades = result.scalars().all()

        # Group by AI source
        source_stats = defaultdict(lambda: {
            'total_pnl': Decimal('0'),
            'total_trades': 0,
            'win_count': 0,
            'loss_count': 0,
            'avg_confidence': Decimal('0'),
            'total_volume': Decimal('0'),
            'contribution_pct': Decimal('0'),
            'avg_hold_hours': Decimal('0'),
        })

        total_pnl = Decimal('0')

        for trade in trades:
            source = trade.ai_source or 'Unknown'
            pnl = trade.pnl_usd or Decimal('0')

            source_stats[source]['total_pnl'] += pnl
            source_stats[source]['total_trades'] += 1
            source_stats[source]['total_volume'] += trade.position_size_usd or Decimal('0')

            if trade.signal_confidence:
                source_stats[source]['avg_confidence'] += Decimal(str(trade.signal_confidence))

            if trade.hold_duration_hours:
                source_stats[source]['avg_hold_hours'] += trade.hold_duration_hours

            if trade.is_win:
                source_stats[source]['win_count'] += 1
            else:
                source_stats[source]['loss_count'] += 1

            total_pnl += pnl

        # Calculate averages and percentages
        for source, stats in source_stats.items():
            if stats['total_trades'] > 0:
                stats['win_rate'] = stats['win_count'] / stats['total_trades']
                stats['avg_confidence'] = stats['avg_confidence'] / stats['total_trades']
                stats['avg_hold_hours'] = stats['avg_hold_hours'] / stats['total_trades']

            if total_pnl != 0:
                stats['contribution_pct'] = (stats['total_pnl'] / total_pnl) * 100

        # Format result
        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_pnl': float(total_pnl),
            'ai_sources': {
                source: {
                    'total_pnl': float(stats['total_pnl']),
                    'total_trades': stats['total_trades'],
                    'win_count': stats['win_count'],
                    'loss_count': stats['loss_count'],
                    'win_rate': float(stats.get('win_rate', 0)),
                    'avg_confidence': float(stats['avg_confidence']),
                    'total_volume': float(stats['total_volume']),
                    'contribution_pct': float(stats['contribution_pct']),
                    'avg_hold_hours': float(stats['avg_hold_hours']),
                }
                for source, stats in source_stats.items()
            }
        }

        logger.info(f"AI source attribution analysis complete: {len(source_stats)} sources")

        return result

    async def analyze_position_attribution(
        self,
        start_date: date,
        end_date: date,
        top_n: int = 20,
    ) -> Dict[str, Dict]:
        """
        Analyze top contributing positions.

        Args:
            start_date: Start date
            end_date: End date
            top_n: Number of top positions to return

        Returns:
            Dictionary of position attribution
        """
        logger.info(f"Analyzing position attribution from {start_date} to {end_date}")

        # Get all closed trades in period
        stmt = select(TradeExecution).where(

            
            TradeExecution.exit_timestamp.isnot(None),
            func.date(TradeExecution.exit_timestamp) >= start_date,
            func.date(TradeExecution.exit_timestamp) <= end_date,
            TradeExecution.status == 'CLOSED',
        

        )

        result = await self.db.execute(stmt)

        trades = result.scalars().all()

        # Group by ticker
        ticker_stats = defaultdict(lambda: {
            'total_pnl': Decimal('0'),
            'total_trades': 0,
            'win_count': 0,
            'loss_count': 0,
            'total_volume': Decimal('0'),
            'sector': None,
            'avg_return_pct': Decimal('0'),
        })

        total_pnl = Decimal('0')

        for trade in trades:
            ticker = trade.ticker
            pnl = trade.pnl_usd or Decimal('0')

            ticker_stats[ticker]['total_pnl'] += pnl
            ticker_stats[ticker]['total_trades'] += 1
            ticker_stats[ticker]['total_volume'] += trade.position_size_usd or Decimal('0')
            ticker_stats[ticker]['sector'] = trade.sector

            if trade.pnl_pct:
                ticker_stats[ticker]['avg_return_pct'] += trade.pnl_pct

            if trade.is_win:
                ticker_stats[ticker]['win_count'] += 1
            else:
                ticker_stats[ticker]['loss_count'] += 1

            total_pnl += pnl

        # Calculate averages
        for ticker, stats in ticker_stats.items():
            if stats['total_trades'] > 0:
                stats['win_rate'] = stats['win_count'] / stats['total_trades']
                stats['avg_return_pct'] = stats['avg_return_pct'] / stats['total_trades']

            if total_pnl != 0:
                stats['contribution_pct'] = (stats['total_pnl'] / total_pnl) * 100

        # Sort by total PnL and get top N
        sorted_tickers = sorted(
            ticker_stats.items(),
            key=lambda x: float(x[1]['total_pnl']),
            reverse=True
        )[:top_n]

        # Format result
        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_pnl': float(total_pnl),
            'top_positions': [
                {
                    'ticker': ticker,
                    'total_pnl': float(stats['total_pnl']),
                    'total_trades': stats['total_trades'],
                    'win_count': stats['win_count'],
                    'loss_count': stats['loss_count'],
                    'win_rate': float(stats.get('win_rate', 0)),
                    'avg_return_pct': float(stats['avg_return_pct']),
                    'total_volume': float(stats['total_volume']),
                    'contribution_pct': float(stats['contribution_pct']),
                    'sector': stats['sector'],
                }
                for ticker, stats in sorted_tickers
            ]
        }

        logger.info(f"Position attribution analysis complete: top {len(sorted_tickers)} positions")

        return result

    async def analyze_time_based_attribution(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Dict]:
        """
        Analyze returns by time period (day of week, hour).

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary of time-based attribution
        """
        logger.info(f"Analyzing time-based attribution from {start_date} to {end_date}")

        # Get all closed trades in period
        stmt = select(TradeExecution).where(

            
            TradeExecution.exit_timestamp.isnot(None),
            func.date(TradeExecution.exit_timestamp) >= start_date,
            func.date(TradeExecution.exit_timestamp) <= end_date,
            TradeExecution.status == 'CLOSED',
        

        )

        result = await self.db.execute(stmt)

        trades = result.scalars().all()

        # Day of week stats
        day_stats = defaultdict(lambda: {
            'total_pnl': Decimal('0'),
            'total_trades': 0,
            'win_count': 0,
        })

        # Hour of day stats
        hour_stats = defaultdict(lambda: {
            'total_pnl': Decimal('0'),
            'total_trades': 0,
            'win_count': 0,
        })

        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for trade in trades:
            pnl = trade.pnl_usd or Decimal('0')

            # Day of week (0 = Monday)
            day_of_week = trade.exit_timestamp.weekday()
            day_name = day_names[day_of_week]

            day_stats[day_name]['total_pnl'] += pnl
            day_stats[day_name]['total_trades'] += 1
            if trade.is_win:
                day_stats[day_name]['win_count'] += 1

            # Hour of day
            hour = trade.exit_timestamp.hour
            hour_stats[hour]['total_pnl'] += pnl
            hour_stats[hour]['total_trades'] += 1
            if trade.is_win:
                hour_stats[hour]['win_count'] += 1

        # Calculate win rates
        for stats in day_stats.values():
            if stats['total_trades'] > 0:
                stats['win_rate'] = stats['win_count'] / stats['total_trades']

        for stats in hour_stats.values():
            if stats['total_trades'] > 0:
                stats['win_rate'] = stats['win_count'] / stats['total_trades']

        # Format result
        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'by_day_of_week': {
                day: {
                    'total_pnl': float(stats['total_pnl']),
                    'total_trades': stats['total_trades'],
                    'win_count': stats['win_count'],
                    'win_rate': float(stats.get('win_rate', 0)),
                }
                for day, stats in day_stats.items()
            },
            'by_hour': {
                hour: {
                    'total_pnl': float(stats['total_pnl']),
                    'total_trades': stats['total_trades'],
                    'win_count': stats['win_count'],
                    'win_rate': float(stats.get('win_rate', 0)),
                }
                for hour, stats in hour_stats.items()
            }
        }

        logger.info("Time-based attribution analysis complete")

        return result

    async def get_comprehensive_attribution(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict:
        """
        Get comprehensive attribution analysis.

        Combines all attribution dimensions.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Complete attribution report
        """
        logger.info(f"Generating comprehensive attribution report from {start_date} to {end_date}")

        # Get all attribution analyses
        strategy_attr = await self.analyze_strategy_attribution(start_date, end_date)
        sector_attr = await self.analyze_sector_attribution(start_date, end_date)
        ai_source_attr = await self.analyze_ai_source_attribution(start_date, end_date)
        position_attr = await self.analyze_position_attribution(start_date, end_date, top_n=10)
        time_attr = await self.analyze_time_based_attribution(start_date, end_date)

        # Combine results
        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'total_pnl': strategy_attr['total_pnl'],
            'attribution': {
                'by_strategy': strategy_attr['strategies'],
                'by_sector': sector_attr['sectors'],
                'by_ai_source': ai_source_attr['ai_sources'],
                'top_positions': position_attr['top_positions'],
                'by_time': {
                    'day_of_week': time_attr['by_day_of_week'],
                    'hour_of_day': time_attr['by_hour'],
                }
            }
        }

        logger.info("Comprehensive attribution report generated")

        return result
