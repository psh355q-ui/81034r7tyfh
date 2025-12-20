"""
Risk Analytics - Advanced risk analysis and monitoring

Features:
- Real-time risk metrics
- Correlation analysis
- Stress testing
- Scenario analysis
- Risk decomposition
- Concentration risk

Author: AI Trading System Team
Date: 2025-11-25
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
import numpy as np

from backend.core.models.analytics_models import (
    DailyAnalytics,
    TradeExecution,
    PortfolioSnapshot,
)

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """
    Advanced risk analytics for portfolio monitoring.

    Provides:
    - VaR (Value at Risk) calculations
    - Stress testing
    - Correlation analysis
    - Concentration risk
    - Drawdown analysis
    """

    def __init__(self, db_session: Session):
        """
        Initialize risk analyzer.

        Args:
            db_session: Database session
        """
        self.db = db_session
        logger.info("RiskAnalyzer initialized")

    async def calculate_var_metrics(
        self,
        lookback_days: int = 90,
        confidence_levels: List[float] = [0.95, 0.99],
    ) -> Dict:
        """
        Calculate Value at Risk (VaR) metrics.

        Args:
            lookback_days: Days of historical data
            confidence_levels: List of confidence levels

        Returns:
            VaR metrics dictionary
        """
        logger.info(f"Calculating VaR metrics ({lookback_days} days)")

        # Get daily returns
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=lookback_days)

        stmt = select(DailyAnalytics).where(


            
            DailyAnalytics.date >= start_date,
            DailyAnalytics.date <= end_date,
        ).order_by(DailyAnalytics.date


        )


        result = await self.db.execute(stmt)


        daily_records = result.scalars().all()

        if len(daily_records) < 20:
            raise ValueError("Insufficient data for VaR calculation")

        returns = [float(r.daily_return_pct or 0) for r in daily_records]
        returns_array = np.array(returns)

        # Get current portfolio value
        latest = daily_records[-1]
        portfolio_value = float(latest.portfolio_value_eod)

        # Calculate VaR for each confidence level
        var_results = {}

        for confidence in confidence_levels:
            percentile = (1 - confidence) * 100
            var_pct = np.percentile(returns_array, percentile)
            var_usd = portfolio_value * (var_pct / 100)

            var_results[f"var_{int(confidence*100)}"] = {
                'confidence_level': confidence,
                'var_pct': float(var_pct),
                'var_usd': float(var_usd),
                'interpretation': f"${abs(var_usd):,.2f} max loss at {confidence*100}% confidence"
            }

        # Calculate Conditional VaR (CVaR / Expected Shortfall)
        for confidence in confidence_levels:
            percentile = (1 - confidence) * 100
            threshold = np.percentile(returns_array, percentile)
            tail_losses = returns_array[returns_array <= threshold]

            if len(tail_losses) > 0:
                cvar_pct = np.mean(tail_losses)
                cvar_usd = portfolio_value * (cvar_pct / 100)

                var_results[f"cvar_{int(confidence*100)}"] = {
                    'confidence_level': confidence,
                    'cvar_pct': float(cvar_pct),
                    'cvar_usd': float(cvar_usd),
                    'interpretation': f"${abs(cvar_usd):,.2f} expected loss if VaR is breached"
                }

        result = {
            'lookback_days': lookback_days,
            'data_points': len(returns),
            'portfolio_value': portfolio_value,
            'var_metrics': var_results,
            'calculated_at': datetime.utcnow().isoformat(),
        }

        logger.info(f"VaR metrics calculated for {len(confidence_levels)} confidence levels")

        return result

    async def analyze_drawdown_metrics(
        self,
        lookback_days: int = 180,
    ) -> Dict:
        """
        Analyze drawdown metrics.

        Args:
            lookback_days: Days of historical data

        Returns:
            Drawdown analysis
        """
        logger.info(f"Analyzing drawdown metrics ({lookback_days} days)")

        # Get daily portfolio values
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=lookback_days)

        stmt = select(DailyAnalytics).where(


            
            DailyAnalytics.date >= start_date,
            DailyAnalytics.date <= end_date,
        ).order_by(DailyAnalytics.date


        )


        result = await self.db.execute(stmt)


        daily_records = result.scalars().all()

        if len(daily_records) < 10:
            raise ValueError("Insufficient data for drawdown analysis")

        # Calculate drawdowns
        values = [float(r.portfolio_value_eod) for r in daily_records]
        dates = [r.date for r in daily_records]

        running_max = np.maximum.accumulate(values)
        drawdowns = [(v - m) / m * 100 for v, m in zip(values, running_max)]

        # Find maximum drawdown
        max_dd_idx = np.argmin(drawdowns)
        max_drawdown_pct = drawdowns[max_dd_idx]

        # Find peak before max drawdown
        peak_idx = np.argmax(values[:max_dd_idx+1])

        # Calculate recovery time if recovered
        recovery_days = None
        if max_dd_idx < len(values) - 1:
            peak_value = values[peak_idx]
            for i in range(max_dd_idx + 1, len(values)):
                if values[i] >= peak_value:
                    recovery_days = i - max_dd_idx
                    break

        # Current drawdown
        current_max = max(values)
        current_value = values[-1]
        current_drawdown = ((current_value - current_max) / current_max) * 100

        # Drawdown duration
        drawdown_durations = []
        current_duration = 0
        in_drawdown = False

        for i in range(len(values)):
            if values[i] < running_max[i]:
                if not in_drawdown:
                    in_drawdown = True
                    current_duration = 1
                else:
                    current_duration += 1
            else:
                if in_drawdown and current_duration > 0:
                    drawdown_durations.append(current_duration)
                in_drawdown = False
                current_duration = 0

        avg_drawdown_duration = np.mean(drawdown_durations) if drawdown_durations else 0

        result = {
            'lookback_days': lookback_days,
            'max_drawdown': {
                'pct': float(max_drawdown_pct),
                'peak_date': dates[peak_idx].isoformat(),
                'trough_date': dates[max_dd_idx].isoformat(),
                'peak_value': values[peak_idx],
                'trough_value': values[max_dd_idx],
                'recovery_days': recovery_days,
            },
            'current_drawdown': {
                'pct': float(current_drawdown),
                'peak_value': current_max,
                'current_value': current_value,
            },
            'statistics': {
                'avg_drawdown_duration_days': float(avg_drawdown_duration),
                'total_drawdown_periods': len(drawdown_durations),
                'max_drawdown_duration_days': max(drawdown_durations) if drawdown_durations else 0,
            },
            'calculated_at': datetime.utcnow().isoformat(),
        }

        logger.info(f"Drawdown analysis complete: max DD = {max_drawdown_pct:.2f}%")

        return result

    async def analyze_concentration_risk(
        self,
        target_date: Optional[date] = None,
    ) -> Dict:
        """
        Analyze portfolio concentration risk.

        Args:
            target_date: Date to analyze (defaults to today)

        Returns:
            Concentration risk metrics
        """
        if target_date is None:
            target_date = datetime.utcnow().date()

        logger.info(f"Analyzing concentration risk for {target_date}")

        # Get portfolio snapshot
        stmt = select(PortfolioSnapshot).where(

            
            PortfolioSnapshot.snapshot_date == target_date
        ).first()

        if not snapshot or not snapshot.positions:
            raise ValueError(f"No portfolio data for {target_date}")

        positions = snapshot.positions
        total_value = float(snapshot.total_value)

        # Calculate position concentrations
        position_weights = []
        for pos in positions:
            weight = pos.get('value', 0) / total_value * 100 if total_value > 0 else 0
            position_weights.append({
                'ticker': pos.get('ticker'),
                'weight_pct': weight,
                'value': pos.get('value', 0),
                'sector': pos.get('sector'),
            })

        # Sort by weight
        position_weights.sort(key=lambda x: x['weight_pct'], reverse=True)

        # Top 5 concentration
        top5_weight = sum(p['weight_pct'] for p in position_weights[:5])
        top10_weight = sum(p['weight_pct'] for p in position_weights[:10])

        # Sector concentration
        sector_weights = {}
        for pos in positions:
            sector = pos.get('sector', 'Unknown')
            value = pos.get('value', 0)
            sector_weights[sector] = sector_weights.get(sector, 0) + value

        sector_pcts = {
            sector: (value / total_value * 100) if total_value > 0 else 0
            for sector, value in sector_weights.items()
        }

        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        hhi = sum(w['weight_pct'] ** 2 for w in position_weights)

        # Concentration risk level
        if hhi < 1000:
            risk_level = 'LOW'
        elif hhi < 1800:
            risk_level = 'MODERATE'
        else:
            risk_level = 'HIGH'

        result = {
            'date': target_date.isoformat(),
            'total_positions': len(positions),
            'largest_position': position_weights[0] if position_weights else None,
            'top_5_concentration_pct': float(top5_weight),
            'top_10_concentration_pct': float(top10_weight),
            'herfindahl_index': float(hhi),
            'concentration_risk_level': risk_level,
            'position_weights': position_weights[:20],  # Top 20
            'sector_concentration': sector_pcts,
            'calculated_at': datetime.utcnow().isoformat(),
        }

        logger.info(f"Concentration analysis complete: HHI = {hhi:.2f} ({risk_level})")

        return result

    async def analyze_correlation_risk(
        self,
        lookback_days: int = 60,
    ) -> Dict:
        """
        Analyze correlation between positions.

        Args:
            lookback_days: Days of historical data

        Returns:
            Correlation analysis
        """
        logger.info(f"Analyzing correlation risk ({lookback_days} days)")

        # Get recent trades
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=lookback_days)

        stmt = select(TradeExecution).where(


            
            func.date(TradeExecution.execution_timestamp) >= start_date,
            func.date(TradeExecution.execution_timestamp) <= end_date,
        

        )

        result = await self.db.execute(stmt)

        snapshot = result.scalars().all()

        # Group trades by ticker
        ticker_returns = {}
        for trade in trades:
            if trade.pnl_pct is not None:
                if trade.ticker not in ticker_returns:
                    ticker_returns[trade.ticker] = []
                ticker_returns[trade.ticker].append(float(trade.pnl_pct))

        # Calculate average correlation
        if len(ticker_returns) < 2:
            return {
                'message': 'Insufficient data for correlation analysis',
                'tickers_analyzed': len(ticker_returns),
            }

        # Find highly correlated pairs
        correlations = []
        tickers = list(ticker_returns.keys())

        for i in range(len(tickers)):
            for j in range(i + 1, len(tickers)):
                ticker1 = tickers[i]
                ticker2 = tickers[j]

                returns1 = ticker_returns[ticker1]
                returns2 = ticker_returns[ticker2]

                # Need at least 5 data points
                if len(returns1) >= 5 and len(returns2) >= 5:
                    # Align lengths
                    min_len = min(len(returns1), len(returns2))
                    r1 = np.array(returns1[:min_len])
                    r2 = np.array(returns2[:min_len])

                    # Calculate correlation
                    if len(r1) > 1:
                        corr = np.corrcoef(r1, r2)[0, 1]
                        if not np.isnan(corr):
                            correlations.append({
                                'ticker1': ticker1,
                                'ticker2': ticker2,
                                'correlation': float(corr),
                            })

        # Sort by absolute correlation
        correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)

        # Average absolute correlation
        avg_correlation = np.mean([abs(c['correlation']) for c in correlations]) if correlations else 0

        result = {
            'lookback_days': lookback_days,
            'tickers_analyzed': len(ticker_returns),
            'correlation_pairs': len(correlations),
            'avg_absolute_correlation': float(avg_correlation),
            'highly_correlated': [c for c in correlations if abs(c['correlation']) > 0.7][:10],
            'negatively_correlated': [c for c in correlations if c['correlation'] < -0.5][:10],
            'calculated_at': datetime.utcnow().isoformat(),
        }

        logger.info(f"Correlation analysis complete: {len(correlations)} pairs analyzed")

        return result

    async def stress_test_portfolio(
        self,
        scenarios: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Perform stress testing on portfolio.

        Args:
            scenarios: List of stress scenarios

        Returns:
            Stress test results
        """
        logger.info("Performing portfolio stress test")

        # Default scenarios
        if scenarios is None:
            scenarios = [
                {'name': 'Market Crash (-20%)', 'market_shock': -0.20},
                {'name': 'Correction (-10%)', 'market_shock': -0.10},
                {'name': 'Volatility Spike (+50%)', 'volatility_shock': 0.50},
                {'name': 'Sector Rotation', 'sector_shock': {'Technology': -0.15, 'Finance': 0.10}},
            ]

        # Get current portfolio
        stmt = select(PortfolioSnapshot).order_by(
            PortfolioSnapshot.snapshot_date.desc()
        )
        result = await self.db.execute(stmt)
        latest_snapshot = result.scalars().first()

        if not latest_snapshot:
            raise ValueError("No portfolio data available")

        current_value = float(latest_snapshot.total_value)
        positions = latest_snapshot.positions or []

        # Calculate average portfolio beta (simplified - assume 1.0 for now)
        portfolio_beta = 1.0

        # Perform stress tests
        stress_results = []

        for scenario in scenarios:
            scenario_impact = 0

            if 'market_shock' in scenario:
                # Market-wide shock
                shock = scenario['market_shock']
                impact = current_value * shock * portfolio_beta
                scenario_impact = impact

            elif 'volatility_shock' in scenario:
                # Estimate impact based on VaR
                volatility_increase = scenario['volatility_shock']
                # Simplified: assume VaR increases proportionally
                var_impact = current_value * -0.05 * volatility_increase
                scenario_impact = var_impact

            elif 'sector_shock' in scenario:
                # Sector-specific shock
                sector_shocks = scenario['sector_shock']
                for pos in positions:
                    sector = pos.get('sector', 'Unknown')
                    if sector in sector_shocks:
                        pos_value = pos.get('value', 0)
                        scenario_impact += pos_value * sector_shocks[sector]

            stress_results.append({
                'scenario': scenario['name'],
                'impact_usd': float(scenario_impact),
                'impact_pct': (scenario_impact / current_value * 100) if current_value > 0 else 0,
                'portfolio_value_after': current_value + scenario_impact,
            })

        result = {
            'current_portfolio_value': current_value,
            'stress_scenarios': stress_results,
            'worst_case': min(stress_results, key=lambda x: x['impact_usd']),
            'calculated_at': datetime.utcnow().isoformat(),
        }

        logger.info(f"Stress test complete: {len(scenarios)} scenarios analyzed")

        return result

    async def get_risk_dashboard(self) -> Dict:
        """
        Get comprehensive risk dashboard.

        Returns:
            Risk dashboard metrics
        """
        logger.info("Generating risk dashboard")

        try:
            # Get all risk metrics
            var_metrics = await self.calculate_var_metrics(lookback_days=90)
            drawdown = await self.analyze_drawdown_metrics(lookback_days=180)
            concentration = await self.analyze_concentration_risk()
            correlation = await self.analyze_correlation_risk(lookback_days=60)
            stress_test = await self.stress_test_portfolio()

            result = {
                'var_metrics': var_metrics,
                'drawdown_analysis': drawdown,
                'concentration_risk': concentration,
                'correlation_analysis': correlation,
                'stress_test': stress_test,
                'generated_at': datetime.utcnow().isoformat(),
            }

            logger.info("Risk dashboard generated successfully")

            return result

        except Exception as e:
            logger.error(f"Error generating risk dashboard: {e}", exc_info=True)
            raise
