"""
Portfolio Optimizer

Phase 31: Portfolio Optimization (MPT)
Date: 2025-12-30

Modern Portfolio Theory implementation:
- Efficient Frontier calculation
- Sharpe Ratio maximization
- Minimum Variance Portfolio
- Monte Carlo simulation
- Risk Parity allocation
"""

import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import yfinance as yf
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """
    Modern Portfolio Theory Optimizer

    Implements various portfolio optimization strategies
    """

    def __init__(self, risk_free_rate: float = 0.04):
        """
        Initialize Portfolio Optimizer

        Args:
            risk_free_rate: Annual risk-free rate (default: 4%)
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logger

    def fetch_price_data(
        self,
        symbols: List[str],
        period: str = "1y"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical price data for symbols

        Args:
            symbols: List of asset symbols
            period: Lookback period (1y, 2y, 5y, max)

        Returns:
            DataFrame with adjusted close prices or None
        """
        try:
            raw_data = yf.download(symbols, period=period, progress=False)

            if raw_data.empty:
                self.logger.error(f"No price data fetched for {symbols}")
                return None

            # Extract Close prices (MultiIndex structure)
            if len(symbols) == 1:
                data = raw_data['Close'].to_frame(name=symbols[0])
            else:
                # Close is at level 0 of MultiIndex
                data = raw_data['Close']

            self.logger.info(f"✅ Fetched {len(data)} days of price data for {len(symbols)} assets")
            return data

        except Exception as e:
            self.logger.error(f"Error fetching price data: {e}")
            return None

    def calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate daily returns from prices

        Args:
            prices: DataFrame of prices

        Returns:
            DataFrame of daily returns
        """
        returns = prices.pct_change().dropna()
        self.logger.info(f"Calculated returns: {len(returns)} days")
        return returns

    def calculate_portfolio_metrics(
        self,
        weights: np.ndarray,
        mean_returns: pd.Series,
        cov_matrix: pd.DataFrame
    ) -> Tuple[float, float]:
        """
        Calculate portfolio return and volatility

        Args:
            weights: Portfolio weights (sum to 1.0)
            mean_returns: Mean returns for each asset
            cov_matrix: Covariance matrix

        Returns:
            (annual_return, annual_volatility)
        """
        # Annual return (assuming 252 trading days)
        portfolio_return = np.sum(weights * mean_returns) * 252

        # Annual volatility
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix * 252, weights))
        portfolio_std = np.sqrt(portfolio_variance)

        return portfolio_return, portfolio_std

    def sharpe_ratio(
        self,
        weights: np.ndarray,
        mean_returns: pd.Series,
        cov_matrix: pd.DataFrame
    ) -> float:
        """
        Calculate Sharpe Ratio

        Args:
            weights: Portfolio weights
            mean_returns: Mean returns
            cov_matrix: Covariance matrix

        Returns:
            Sharpe Ratio
        """
        ret, vol = self.calculate_portfolio_metrics(weights, mean_returns, cov_matrix)

        if vol == 0:
            return 0.0

        sharpe = (ret - self.risk_free_rate) / vol
        return sharpe

    def optimize_sharpe_ratio(
        self,
        returns: pd.DataFrame
    ) -> Dict:
        """
        Find portfolio weights that maximize Sharpe Ratio

        Args:
            returns: DataFrame of asset returns

        Returns:
            Dict with optimal weights, return, volatility, sharpe
        """
        num_assets = len(returns.columns)
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        # Objective: Negative Sharpe (for minimization)
        def neg_sharpe(weights):
            return -self.sharpe_ratio(weights, mean_returns, cov_matrix)

        # Constraints: weights sum to 1
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})

        # Bounds: 0 <= weight <= 1 (no short selling)
        bounds = tuple((0, 1) for _ in range(num_assets))

        # Initial guess: equal weights
        init_guess = np.array([1/num_assets] * num_assets)

        # Optimize
        result = minimize(
            neg_sharpe,
            init_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if not result.success:
            self.logger.warning(f"Optimization did not converge: {result.message}")

        optimal_weights = result.x
        ret, vol = self.calculate_portfolio_metrics(optimal_weights, mean_returns, cov_matrix)
        sharpe = self.sharpe_ratio(optimal_weights, mean_returns, cov_matrix)

        self.logger.info(f"✅ Max Sharpe: {sharpe:.2f} (Return: {ret*100:.1f}%, Vol: {vol*100:.1f}%)")

        return {
            "weights": {symbol: float(w) for symbol, w in zip(returns.columns, optimal_weights)},
            "annual_return": float(ret),
            "annual_volatility": float(vol),
            "sharpe_ratio": float(sharpe)
        }

    def optimize_min_variance(
        self,
        returns: pd.DataFrame
    ) -> Dict:
        """
        Find minimum variance portfolio

        Args:
            returns: DataFrame of asset returns

        Returns:
            Dict with optimal weights, return, volatility
        """
        num_assets = len(returns.columns)
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        # Objective: Portfolio variance
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        bounds = tuple((0, 1) for _ in range(num_assets))
        init_guess = np.array([1/num_assets] * num_assets)

        result = minimize(
            portfolio_variance,
            init_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        optimal_weights = result.x
        ret, vol = self.calculate_portfolio_metrics(optimal_weights, mean_returns, cov_matrix)
        sharpe = self.sharpe_ratio(optimal_weights, mean_returns, cov_matrix)

        self.logger.info(f"✅ Min Variance: Vol: {vol*100:.1f}% (Return: {ret*100:.1f}%, Sharpe: {sharpe:.2f})")

        return {
            "weights": {symbol: float(w) for symbol, w in zip(returns.columns, optimal_weights)},
            "annual_return": float(ret),
            "annual_volatility": float(vol),
            "sharpe_ratio": float(sharpe)
        }

    def efficient_frontier(
        self,
        returns: pd.DataFrame,
        num_points: int = 50
    ) -> pd.DataFrame:
        """
        Calculate Efficient Frontier

        Args:
            returns: DataFrame of asset returns
            num_points: Number of points on frontier

        Returns:
            DataFrame with columns [return, volatility, sharpe, weights]
        """
        num_assets = len(returns.columns)
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        # Get min and max returns
        min_var_portfolio = self.optimize_min_variance(returns)
        max_sharpe_portfolio = self.optimize_sharpe_ratio(returns)

        min_return = min_var_portfolio['annual_return']
        max_return = max_sharpe_portfolio['annual_return']

        # Target returns across the frontier
        target_returns = np.linspace(min_return, max_return, num_points)

        frontier_points = []

        for target_ret in target_returns:
            # Objective: minimize variance
            def portfolio_variance(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))

            # Constraints: weights sum to 1, target return met
            constraints = (
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
                {'type': 'eq', 'fun': lambda w: np.sum(w * mean_returns) * 252 - target_ret}
            )

            bounds = tuple((0, 1) for _ in range(num_assets))
            init_guess = np.array([1/num_assets] * num_assets)

            result = minimize(
                portfolio_variance,
                init_guess,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'disp': False}
            )

            if result.success:
                weights = result.x
                ret, vol = self.calculate_portfolio_metrics(weights, mean_returns, cov_matrix)
                sharpe = self.sharpe_ratio(weights, mean_returns, cov_matrix)

                frontier_points.append({
                    'return': ret,
                    'volatility': vol,
                    'sharpe': sharpe,
                    'weights': weights.tolist()
                })

        frontier_df = pd.DataFrame(frontier_points)
        self.logger.info(f"✅ Calculated Efficient Frontier ({len(frontier_df)} points)")

        return frontier_df

    def monte_carlo_simulation(
        self,
        returns: pd.DataFrame,
        num_simulations: int = 10000
    ) -> pd.DataFrame:
        """
        Monte Carlo simulation for random portfolios

        Args:
            returns: DataFrame of asset returns
            num_simulations: Number of random portfolios

        Returns:
            DataFrame with columns [return, volatility, sharpe, weights]
        """
        num_assets = len(returns.columns)
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        results = []

        for _ in range(num_simulations):
            # Random weights
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)  # Normalize to sum=1

            ret, vol = self.calculate_portfolio_metrics(weights, mean_returns, cov_matrix)
            sharpe = self.sharpe_ratio(weights, mean_returns, cov_matrix)

            results.append({
                'return': ret,
                'volatility': vol,
                'sharpe': sharpe,
                'weights': weights.tolist()
            })

        results_df = pd.DataFrame(results)
        self.logger.info(f"✅ Monte Carlo: {num_simulations} random portfolios")

        return results_df

    def risk_parity_allocation(
        self,
        returns: pd.DataFrame
    ) -> Dict:
        """
        Risk Parity allocation (equal risk contribution)

        Args:
            returns: DataFrame of asset returns

        Returns:
            Dict with weights, return, volatility
        """
        num_assets = len(returns.columns)
        mean_returns = returns.mean()
        cov_matrix = returns.cov()

        # Objective: minimize difference between risk contributions
        def risk_parity_objective(weights):
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_vol = np.sqrt(portfolio_variance)

            # Marginal contribution to risk
            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol

            # Risk contribution of each asset
            risk_contrib = weights * marginal_contrib

            # Target: equal risk contribution
            target_risk = portfolio_vol / num_assets

            # Minimize sum of squared differences
            return np.sum((risk_contrib - target_risk) ** 2)

        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        bounds = tuple((0, 1) for _ in range(num_assets))
        init_guess = np.array([1/num_assets] * num_assets)

        result = minimize(
            risk_parity_objective,
            init_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        optimal_weights = result.x
        ret, vol = self.calculate_portfolio_metrics(optimal_weights, mean_returns, cov_matrix)
        sharpe = self.sharpe_ratio(optimal_weights, mean_returns, cov_matrix)

        self.logger.info(f"✅ Risk Parity: Vol: {vol*100:.1f}% (Return: {ret*100:.1f}%, Sharpe: {sharpe:.2f})")

        return {
            "weights": {symbol: float(w) for symbol, w in zip(returns.columns, optimal_weights)},
            "annual_return": float(ret),
            "annual_volatility": float(vol),
            "sharpe_ratio": float(sharpe)
        }


def main():
    """CLI entry point for testing"""
    logging.basicConfig(level=logging.INFO)

    optimizer = PortfolioOptimizer(risk_free_rate=0.04)

    # Test portfolio
    symbols = ["AAPL", "MSFT", "GOOGL", "TLT", "GLD"]

    print("\n" + "="*80)
    print("Portfolio Optimizer - Test Run")
    print("="*80)
    print(f"\nSymbols: {', '.join(symbols)}")
    print(f"Risk-free rate: {optimizer.risk_free_rate*100:.1f}%")
    print()

    # Fetch data
    print("Fetching price data...")
    prices = optimizer.fetch_price_data(symbols, period="2y")

    if prices is None:
        print("❌ Failed to fetch price data")
        return

    returns = optimizer.calculate_returns(prices)

    # Max Sharpe
    print("\n1️⃣ Maximum Sharpe Ratio Portfolio")
    print("-" * 80)
    max_sharpe = optimizer.optimize_sharpe_ratio(returns)
    for symbol, weight in max_sharpe['weights'].items():
        print(f"  {symbol:6s}: {weight*100:5.1f}%")
    print(f"\n  Return:     {max_sharpe['annual_return']*100:5.1f}%")
    print(f"  Volatility: {max_sharpe['annual_volatility']*100:5.1f}%")
    print(f"  Sharpe:     {max_sharpe['sharpe_ratio']:5.2f}")

    # Min Variance
    print("\n2️⃣ Minimum Variance Portfolio")
    print("-" * 80)
    min_var = optimizer.optimize_min_variance(returns)
    for symbol, weight in min_var['weights'].items():
        print(f"  {symbol:6s}: {weight*100:5.1f}%")
    print(f"\n  Return:     {min_var['annual_return']*100:5.1f}%")
    print(f"  Volatility: {min_var['annual_volatility']*100:5.1f}%")
    print(f"  Sharpe:     {min_var['sharpe_ratio']:5.2f}")

    # Risk Parity
    print("\n3️⃣ Risk Parity Portfolio")
    print("-" * 80)
    risk_parity = optimizer.risk_parity_allocation(returns)
    for symbol, weight in risk_parity['weights'].items():
        print(f"  {symbol:6s}: {weight*100:5.1f}%")
    print(f"\n  Return:     {risk_parity['annual_return']*100:5.1f}%")
    print(f"  Volatility: {risk_parity['annual_volatility']*100:5.1f}%")
    print(f"  Sharpe:     {risk_parity['sharpe_ratio']:5.2f}")

    # Efficient Frontier
    print("\n4️⃣ Efficient Frontier")
    print("-" * 80)
    frontier = optimizer.efficient_frontier(returns, num_points=20)
    print(f"Calculated {len(frontier)} points on efficient frontier")
    print(f"Return range: {frontier['return'].min()*100:.1f}% ~ {frontier['return'].max()*100:.1f}%")
    print(f"Vol range:    {frontier['volatility'].min()*100:.1f}% ~ {frontier['volatility'].max()*100:.1f}%")

    # Monte Carlo
    print("\n5️⃣ Monte Carlo Simulation")
    print("-" * 80)
    mc_results = optimizer.monte_carlo_simulation(returns, num_simulations=5000)
    print(f"Simulated 5,000 random portfolios")
    print(f"Sharpe range: {mc_results['sharpe'].min():.2f} ~ {mc_results['sharpe'].max():.2f}")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
