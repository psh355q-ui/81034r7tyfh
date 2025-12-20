"""
Backtest Simulator - Historical Trading Simulation

Simulates trading strategy performance using historical data.

Features:
- Historical data simulation
- Multi-ticker portfolio backtesting
- Performance metrics calculation
- Trade execution simulation
- Portfolio tracking over time

Author: AI Trading System Team
Date: 2025-11-14
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import random

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Backtest configuration."""
    start_date: str  # "2024-01-01"
    end_date: str    # "2024-12-31"
    initial_capital: float = 100000.0
    tickers: List[str] = field(default_factory=list)
    commission_rate: float = 0.001  # 0.1%
    slippage_bps: float = 2.0  # 2 basis points
    max_positions: int = 20
    rebalance_frequency: str = "daily"  # daily, weekly, monthly


@dataclass
class Trade:
    """Individual trade record."""
    timestamp: datetime
    ticker: str
    action: str  # BUY, SELL
    shares: int
    price: float
    commission: float
    total_cost: float
    portfolio_value: float


@dataclass
class PortfolioSnapshot:
    """Portfolio state at a point in time."""
    timestamp: datetime
    cash: float
    positions: Dict[str, Dict]  # ticker -> {shares, avg_price, value}
    total_value: float
    daily_return: float = 0.0
    cumulative_return: float = 0.0


@dataclass
class BacktestResult:
    """Complete backtest results."""
    config: BacktestConfig
    trades: List[Trade]
    portfolio_history: List[PortfolioSnapshot]
    metrics: Dict

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "config": {
                "start_date": self.config.start_date,
                "end_date": self.config.end_date,
                "initial_capital": self.config.initial_capital,
                "tickers": self.config.tickers,
            },
            "total_trades": len(self.trades),
            "final_value": self.portfolio_history[-1].total_value if self.portfolio_history else 0,
            "metrics": self.metrics,
        }


class BacktestSimulator:
    """
    Historical trading simulation engine.

    Simulates trading strategy execution on historical data
    to evaluate performance before live trading.
    """

    def __init__(self, config: BacktestConfig):
        self.config = config

        # Portfolio state
        self.cash = config.initial_capital
        self.positions: Dict[str, Dict] = {}  # ticker -> {shares, avg_price}

        # History tracking
        self.trades: List[Trade] = []
        self.portfolio_history: List[PortfolioSnapshot] = []

        logger.info(f"Backtest initialized: {config.start_date} to {config.end_date}")

    async def run(self, strategy_function) -> BacktestResult:
        """
        Run backtest simulation.

        Args:
            strategy_function: async function(date, portfolio) -> List[Decision]

        Returns:
            BacktestResult with complete performance data
        """
        logger.info("Starting backtest simulation...")

        # Generate date range
        dates = self._generate_date_range(
            self.config.start_date,
            self.config.end_date
        )

        logger.info(f"Simulating {len(dates)} trading days...")

        # Simulate each trading day
        for i, date in enumerate(dates):
            if i % 20 == 0:  # Progress update every 20 days
                logger.info(f"Progress: {i}/{len(dates)} days ({i/len(dates)*100:.1f}%)")

            # Get market data for this date
            market_data = await self._get_market_data(date)

            # Get strategy decisions
            decisions = await strategy_function(date, self._get_portfolio_context())

            # Execute decisions
            for decision in decisions:
                await self._execute_decision(decision, market_data, date)

            # Record portfolio snapshot
            self._record_portfolio_snapshot(date, market_data)

        # Calculate final metrics
        metrics = self._calculate_metrics()

        logger.info("Backtest completed!")
        logger.info(f"Final portfolio value: ${self.portfolio_history[-1].total_value:,.2f}")
        logger.info(f"Total return: {metrics['total_return_pct']:.2f}%")

        return BacktestResult(
            config=self.config,
            trades=self.trades,
            portfolio_history=self.portfolio_history,
            metrics=metrics,
        )

    async def _get_market_data(self, date: datetime) -> Dict[str, float]:
        """
        Get historical market prices for date.

        In production, this would fetch from database or API.
        For now, we simulate with random walk.
        """
        market_data = {}

        for ticker in self.config.tickers:
            # Simulate price with random walk
            # In production: fetch from Yahoo Finance or database
            base_price = 100.0
            days_elapsed = (date - datetime.strptime(self.config.start_date, "%Y-%m-%d")).days

            # Random walk with slight upward drift
            drift = 0.0002  # 0.02% per day
            volatility = 0.015  # 1.5% daily volatility

            random_return = random.gauss(drift, volatility)
            price = base_price * (1 + random_return) ** days_elapsed

            # Add some noise
            price *= (1 + random.gauss(0, 0.005))

            market_data[ticker] = round(price, 2)

        return market_data

    async def _execute_decision(
        self,
        decision: Dict,
        market_data: Dict[str, float],
        date: datetime
    ):
        """Execute a trading decision."""
        ticker = decision.get("ticker")
        action = decision.get("action")

        if not ticker or not action or action == "HOLD":
            return

        if ticker not in market_data:
            logger.warning(f"No market data for {ticker} on {date}")
            return

        price = market_data[ticker]

        # Apply slippage
        if action == "BUY":
            execution_price = price * (1 + self.config.slippage_bps / 10000)
        else:
            execution_price = price * (1 - self.config.slippage_bps / 10000)

        # Calculate shares based on position size
        position_size_pct = decision.get("position_size", 3.0)
        portfolio_value = self._get_portfolio_value(market_data)
        dollar_amount = portfolio_value * (position_size_pct / 100.0)
        shares = int(dollar_amount / execution_price)

        if shares == 0:
            return

        # Execute trade
        if action == "BUY":
            await self._execute_buy(ticker, shares, execution_price, date, portfolio_value)
        elif action == "SELL":
            await self._execute_sell(ticker, shares, execution_price, date, portfolio_value)

    async def _execute_buy(
        self,
        ticker: str,
        shares: int,
        price: float,
        date: datetime,
        portfolio_value: float
    ):
        """Execute buy order."""
        cost = shares * price
        commission = cost * self.config.commission_rate
        total_cost = cost + commission

        # Check if we have enough cash
        if total_cost > self.cash:
            logger.debug(f"Insufficient cash for {ticker}: need ${total_cost:.2f}, have ${self.cash:.2f}")
            return

        # Check position limits
        if ticker not in self.positions and len(self.positions) >= self.config.max_positions:
            logger.debug(f"Max positions reached ({self.config.max_positions})")
            return

        # Update cash
        self.cash -= total_cost

        # Update position
        if ticker in self.positions:
            pos = self.positions[ticker]
            total_shares = pos["shares"] + shares
            total_cost_basis = pos["shares"] * pos["avg_price"] + shares * price
            pos["shares"] = total_shares
            pos["avg_price"] = total_cost_basis / total_shares
        else:
            self.positions[ticker] = {
                "shares": shares,
                "avg_price": price,
            }

        # Record trade
        trade = Trade(
            timestamp=date,
            ticker=ticker,
            action="BUY",
            shares=shares,
            price=price,
            commission=commission,
            total_cost=total_cost,
            portfolio_value=portfolio_value,
        )
        self.trades.append(trade)

        logger.debug(f"BUY {shares} {ticker} @ ${price:.2f}")

    async def _execute_sell(
        self,
        ticker: str,
        shares: int,
        price: float,
        date: datetime,
        portfolio_value: float
    ):
        """Execute sell order."""
        # Check if we have the position
        if ticker not in self.positions:
            return

        pos = self.positions[ticker]
        shares = min(shares, pos["shares"])  # Can't sell more than we have

        if shares == 0:
            return

        proceeds = shares * price
        commission = proceeds * self.config.commission_rate
        net_proceeds = proceeds - commission

        # Update cash
        self.cash += net_proceeds

        # Update position
        pos["shares"] -= shares
        if pos["shares"] == 0:
            del self.positions[ticker]

        # Record trade
        trade = Trade(
            timestamp=date,
            ticker=ticker,
            action="SELL",
            shares=shares,
            price=price,
            commission=commission,
            total_cost=-net_proceeds,  # Negative for proceeds
            portfolio_value=portfolio_value,
        )
        self.trades.append(trade)

        logger.debug(f"SELL {shares} {ticker} @ ${price:.2f}")

    def _record_portfolio_snapshot(self, date: datetime, market_data: Dict[str, float]):
        """Record current portfolio state."""
        # Calculate position values
        positions_dict = {}
        positions_value = 0.0

        for ticker, pos in self.positions.items():
            if ticker in market_data:
                current_price = market_data[ticker]
                value = pos["shares"] * current_price
                positions_value += value

                positions_dict[ticker] = {
                    "shares": pos["shares"],
                    "avg_price": pos["avg_price"],
                    "current_price": current_price,
                    "value": value,
                    "unrealized_pnl": value - (pos["shares"] * pos["avg_price"]),
                }

        total_value = self.cash + positions_value

        # Calculate returns
        if self.portfolio_history:
            prev_value = self.portfolio_history[-1].total_value
            daily_return = (total_value - prev_value) / prev_value
        else:
            daily_return = 0.0

        cumulative_return = (total_value - self.config.initial_capital) / self.config.initial_capital

        snapshot = PortfolioSnapshot(
            timestamp=date,
            cash=self.cash,
            positions=positions_dict,
            total_value=total_value,
            daily_return=daily_return,
            cumulative_return=cumulative_return,
        )

        self.portfolio_history.append(snapshot)

    def _get_portfolio_context(self) -> Dict:
        """Get current portfolio context for strategy."""
        positions_value = sum(
            pos["shares"] * pos["avg_price"]
            for pos in self.positions.values()
        )

        return {
            "cash": self.cash,
            "positions": self.positions.copy(),
            "num_positions": len(self.positions),
            "total_value": self.cash + positions_value,
        }

    def _get_portfolio_value(self, market_data: Dict[str, float]) -> float:
        """Calculate current portfolio value."""
        positions_value = sum(
            pos["shares"] * market_data.get(pos_ticker, pos["avg_price"])
            for pos_ticker, pos in self.positions.items()
        )
        return self.cash + positions_value

    def _generate_date_range(self, start_date: str, end_date: str) -> List[datetime]:
        """Generate list of trading days."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        dates = []
        current = start

        while current <= end:
            # Skip weekends (Saturday=5, Sunday=6)
            if current.weekday() < 5:
                dates.append(current)
            current += timedelta(days=1)

        return dates

    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics."""
        if not self.portfolio_history:
            return {}

        initial_value = self.config.initial_capital
        final_value = self.portfolio_history[-1].total_value

        # Total return
        total_return = final_value - initial_value
        total_return_pct = (total_return / initial_value) * 100

        # Daily returns
        daily_returns = [snap.daily_return for snap in self.portfolio_history[1:]]

        # Sharpe ratio (simplified, assuming 0% risk-free rate)
        if daily_returns:
            avg_daily_return = sum(daily_returns) / len(daily_returns)
            std_daily_return = (
                sum((r - avg_daily_return) ** 2 for r in daily_returns) / len(daily_returns)
            ) ** 0.5
            sharpe_ratio = (avg_daily_return / std_daily_return) * (252 ** 0.5) if std_daily_return > 0 else 0
        else:
            sharpe_ratio = 0

        # Max drawdown
        peak = initial_value
        max_drawdown = 0

        for snap in self.portfolio_history:
            if snap.total_value > peak:
                peak = snap.total_value
            drawdown = (peak - snap.total_value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        # Win rate
        winning_trades = sum(1 for t in self.trades if t.action == "SELL" and t.total_cost < 0)  # Proceeds > 0
        total_trades = len([t for t in self.trades if t.action == "SELL"])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Total commission
        total_commission = sum(t.commission for t in self.trades)

        return {
            "initial_value": initial_value,
            "final_value": final_value,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_pct": max_drawdown * 100,
            "total_trades": len(self.trades),
            "win_rate": win_rate,
            "total_commission": total_commission,
            "num_trading_days": len(self.portfolio_history),
        }


# Demo strategy function
async def demo_strategy(date: datetime, portfolio: Dict) -> List[Dict]:
    """
    Demo strategy: Random buy/sell decisions.

    In production, this would be replaced with actual AI strategy.
    """
    decisions = []

    # Simple momentum strategy (mock)
    if random.random() < 0.1:  # 10% chance to trade each day
        action = random.choice(["BUY", "HOLD"])
        ticker = random.choice(["AAPL", "NVDA", "MSFT", "GOOGL"])

        decisions.append({
            "ticker": ticker,
            "action": action,
            "position_size": random.uniform(2.0, 5.0),
            "conviction": random.uniform(0.6, 0.9),
        })

    return decisions


# Demo
async def demo():
    """Run backtest demo."""
    print("=" * 60)
    print("Backtest Simulator Demo")
    print("=" * 60)

    # Configuration
    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-03-31",  # 3 months
        initial_capital=100000.0,
        tickers=["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN"],
        commission_rate=0.001,
        slippage_bps=2.0,
    )

    print(f"\nBacktest Configuration:")
    print(f"  Period: {config.start_date} to {config.end_date}")
    print(f"  Initial Capital: ${config.initial_capital:,.0f}")
    print(f"  Tickers: {', '.join(config.tickers)}")

    # Run backtest
    simulator = BacktestSimulator(config)
    result = await simulator.run(demo_strategy)

    # Display results
    print(f"\n" + "=" * 60)
    print("Backtest Results")
    print("=" * 60)

    metrics = result.metrics
    print(f"\nPerformance:")
    print(f"  Initial Value: ${metrics['initial_value']:,.2f}")
    print(f"  Final Value: ${metrics['final_value']:,.2f}")
    print(f"  Total Return: ${metrics['total_return']:,.2f} ({metrics['total_return_pct']:+.2f}%)")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")

    print(f"\nTrading:")
    print(f"  Total Trades: {metrics['total_trades']}")
    print(f"  Win Rate: {metrics['win_rate']:.1%}")
    print(f"  Total Commission: ${metrics['total_commission']:.2f}")
    print(f"  Trading Days: {metrics['num_trading_days']}")

    print("\n" + "=" * 60)
    print("Demo completed!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo())
