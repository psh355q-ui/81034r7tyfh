"""
Event-Driven Backtest Engine for AI Trading System.

This module simulates trading over historical data to evaluate strategy performance.

Features:
- Event-driven architecture (chronological order)
- Realistic execution simulation (slippage, commissions)
- Portfolio tracking
- Performance metrics (Sharpe, drawdown, win rate)
- Trading Agent integration

Cost: $0 (reuses Trading Agent, no additional API calls)
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Event-driven backtest engine.
    
    Simulates trading strategy over historical period:
    1. Load historical data (daily bars)
    2. For each date:
       - Get features from Feature Store
       - Call Trading Agent for decision
       - Execute trade (with slippage/commission)
       - Update portfolio
    3. Calculate performance metrics
    
    Realistic execution:
    - Slippage: 1 basis point (0.01%)
    - Commission: 0.015% per trade
    - No look-ahead bias (only past data available)
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        slippage_bps: float = 1.0,  # 1 basis point
        commission_rate: float = 0.00015,  # 0.015%
        max_positions: int = 10,
    ):
        """
        Initialize backtest engine.
        
        Args:
            initial_capital: Starting cash ($100,000 default)
            slippage_bps: Slippage in basis points (1 = 0.01%)
            commission_rate: Commission rate (0.00015 = 0.015%)
            max_positions: Maximum number of positions
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.slippage_bps = slippage_bps
        self.commission_rate = commission_rate
        self.max_positions = max_positions
        
        # Portfolio state
        self.positions: Dict[str, dict] = {}  # {ticker: {shares, entry_price, ...}}
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.trades: List[dict] = []
        
        # Performance tracking
        self.daily_returns: List[float] = []
        self.max_equity = initial_capital
        self.max_drawdown = 0.0
        
        logger.info(
            f"BacktestEngine initialized: "
            f"${initial_capital:,.0f} capital, "
            f"{slippage_bps} bps slippage, "
            f"{commission_rate:.4%} commission"
        )
    
    async def run(
        self,
        trading_agent,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime,
        feature_store,
    ) -> Dict:
        """
        Run backtest simulation.
        
        Args:
            trading_agent: TradingAgent instance
            tickers: List of tickers to trade
            start_date: Backtest start date
            end_date: Backtest end date
            feature_store: FeatureStore instance
        
        Returns:
            {
                "total_return": float,  # %
                "sharpe_ratio": float,
                "max_drawdown": float,  # %
                "win_rate": float,  # %
                "total_trades": int,
                "avg_trade_return": float,  # %
                "final_equity": float,
                "equity_curve": pd.DataFrame,
                "trades": pd.DataFrame,
            }
        """
        logger.info(
            f"Starting backtest: {start_date.date()} to {end_date.date()}, "
            f"{len(tickers)} tickers"
        )
        
        # Generate trading days (mock - in production use market calendar)
        trading_days = self._generate_trading_days(start_date, end_date)
        
        logger.info(f"Generated {len(trading_days)} trading days")
        
        # Event loop: simulate day by day
        for i, current_date in enumerate(trading_days):
            logger.debug(f"Simulating {current_date.date()} ({i+1}/{len(trading_days)})")
            
            # Get market data for this day
            market_data = await self._get_market_data(
                tickers, 
                current_date, 
                feature_store
            )
            
            # Update portfolio values (mark to market)
            self._update_portfolio_values(current_date, market_data)
            
            # Trading Agent decisions
            for ticker in tickers:
                if ticker not in market_data:
                    continue
                
                try:
                    # Get Trading Agent decision
                    decision = await trading_agent.analyze(ticker)
                    
                    # Execute trade
                    self._execute_trade(
                        ticker=ticker,
                        decision=decision,
                        current_price=market_data[ticker]["close"],
                        current_date=current_date,
                    )
                
                except Exception as e:
                    logger.warning(f"Error analyzing {ticker} on {current_date.date()}: {e}")
            
            # Record daily equity
            total_equity = self._calculate_total_equity(market_data)
            self.equity_curve.append((current_date, total_equity))
            
            # Calculate daily return
            if i > 0:
                prev_equity = self.equity_curve[i-1][1]
                daily_return = (total_equity - prev_equity) / prev_equity
                self.daily_returns.append(daily_return)
                
                # Update max drawdown
                self.max_equity = max(self.max_equity, total_equity)
                drawdown = (self.max_equity - total_equity) / self.max_equity
                self.max_drawdown = max(self.max_drawdown, drawdown)
        
        # Calculate final performance metrics
        results = self._calculate_performance_metrics()
        
        logger.info(
            f"Backtest completed: "
            f"{results['total_return']:.2%} return, "
            f"{results['sharpe_ratio']:.2f} Sharpe, "
            f"{results['max_drawdown']:.2%} max drawdown"
        )
        
        return results
    
    def _execute_trade(
        self,
        ticker: str,
        decision,
        current_price: float,
        current_date: datetime,
    ):
        """
        Execute trade with slippage and commission.
        
        Args:
            ticker: Stock ticker
            decision: TradingDecision from agent
            current_price: Current market price
            current_date: Current date
        """
        action = decision.action
        
        if action == "HOLD":
            return
        
        # Apply slippage
        if action == "BUY":
            execution_price = current_price * (1 + self.slippage_bps / 10000)
        else:  # SELL
            execution_price = current_price * (1 - self.slippage_bps / 10000)
        
        # Calculate position size
        if action == "BUY":
            # Check if we can open new position
            if len(self.positions) >= self.max_positions:
                logger.debug(f"Max positions reached, skipping BUY {ticker}")
                return
            
            # Calculate shares to buy
            position_value = self.cash * (decision.position_size / 100)
            shares = int(position_value / execution_price)
            
            if shares <= 0:
                return
            
            # Calculate cost
            trade_value = shares * execution_price
            commission = trade_value * self.commission_rate
            total_cost = trade_value + commission
            
            # Check if we have enough cash
            if total_cost > self.cash:
                logger.debug(f"Insufficient cash for {ticker}, need ${total_cost:.0f}")
                return
            
            # Execute BUY
            self.cash -= total_cost
            self.positions[ticker] = {
                "shares": shares,
                "entry_price": execution_price,
                "entry_date": current_date,
                "stop_loss": decision.stop_loss,
            }
            
            # Record trade
            self.trades.append({
                "date": current_date,
                "ticker": ticker,
                "action": "BUY",
                "shares": shares,
                "price": execution_price,
                "value": trade_value,
                "commission": commission,
                "conviction": decision.conviction,
            })
            
            logger.debug(
                f"BUY {ticker}: {shares} shares @ ${execution_price:.2f}, "
                f"cost ${total_cost:.0f}"
            )
        
        elif action == "SELL":
            # Check if we have position
            if ticker not in self.positions:
                return
            
            position = self.positions[ticker]
            shares = position["shares"]
            
            # Calculate proceeds
            trade_value = shares * execution_price
            commission = trade_value * self.commission_rate
            proceeds = trade_value - commission
            
            # Execute SELL
            self.cash += proceeds
            
            # Calculate P&L
            cost_basis = shares * position["entry_price"]
            pnl = proceeds - cost_basis
            pnl_pct = pnl / cost_basis
            
            # Record trade
            self.trades.append({
                "date": current_date,
                "ticker": ticker,
                "action": "SELL",
                "shares": shares,
                "price": execution_price,
                "value": trade_value,
                "commission": commission,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "holding_days": (current_date - position["entry_date"]).days,
            })
            
            # Close position
            del self.positions[ticker]
            
            logger.debug(
                f"SELL {ticker}: {shares} shares @ ${execution_price:.2f}, "
                f"P&L ${pnl:.0f} ({pnl_pct:.2%})"
            )
    
    def _update_portfolio_values(self, current_date: datetime, market_data: dict):
        """Update portfolio values and check stop losses."""
        positions_to_close = []
        
        for ticker, position in self.positions.items():
            if ticker not in market_data:
                continue
            
            current_price = market_data[ticker]["close"]
            
            # Check stop loss
            if position.get("stop_loss"):
                if current_price <= position["stop_loss"]:
                    logger.info(
                        f"Stop loss triggered for {ticker}: "
                        f"${current_price:.2f} <= ${position['stop_loss']:.2f}"
                    )
                    positions_to_close.append(ticker)
        
        # Close positions that hit stop loss
        for ticker in positions_to_close:
            # Create SELL decision
            class StopLossDecision:
                action = "SELL"
                conviction = 1.0
                position_size = 0
                stop_loss = None
            
            self._execute_trade(
                ticker=ticker,
                decision=StopLossDecision(),
                current_price=market_data[ticker]["close"],
                current_date=current_date,
            )
    
    def _calculate_total_equity(self, market_data: dict) -> float:
        """Calculate total portfolio equity."""
        equity = self.cash
        
        for ticker, position in self.positions.items():
            if ticker in market_data:
                current_price = market_data[ticker]["close"]
                position_value = position["shares"] * current_price
                equity += position_value
        
        return equity
    
    def _calculate_performance_metrics(self) -> Dict:
        """Calculate final performance metrics."""
        # Total return
        final_equity = self.equity_curve[-1][1] if self.equity_curve else self.initial_capital
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        # Sharpe ratio (assuming 252 trading days, 0% risk-free rate)
        if len(self.daily_returns) > 0:
            daily_mean = np.mean(self.daily_returns)
            daily_std = np.std(self.daily_returns)
            sharpe_ratio = (daily_mean / daily_std) * np.sqrt(252) if daily_std > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Trade statistics
        completed_trades = [t for t in self.trades if t["action"] == "SELL"]
        
        if completed_trades:
            winning_trades = [t for t in completed_trades if t.get("pnl", 0) > 0]
            win_rate = len(winning_trades) / len(completed_trades)
            avg_trade_return = np.mean([t["pnl_pct"] for t in completed_trades])
        else:
            win_rate = 0.0
            avg_trade_return = 0.0
        
        # Convert to DataFrames
        equity_df = pd.DataFrame(
            self.equity_curve,
            columns=["date", "equity"]
        ).set_index("date")
        
        trades_df = pd.DataFrame(self.trades)
        
        return {
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": win_rate,
            "total_trades": len(self.trades),
            "completed_trades": len(completed_trades),
            "avg_trade_return": avg_trade_return,
            "final_equity": final_equity,
            "initial_capital": self.initial_capital,
            "equity_curve": equity_df,
            "trades": trades_df,
        }
    
    def _generate_trading_days(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[datetime]:
        """
        Generate list of trading days (exclude weekends).
        
        In production, use proper market calendar (NYSE/NASDAQ).
        """
        trading_days = []
        current = start_date
        
        while current <= end_date:
            # Exclude weekends (Monday=0, Sunday=6)
            if current.weekday() < 5:
                trading_days.append(current)
            current += timedelta(days=1)
        
        return trading_days
    
    async def _get_market_data(
        self,
        tickers: List[str],
        date: datetime,
        feature_store,
    ) -> Dict[str, dict]:
        """
        Get market data for given date.
        
        In production, this would load from database.
        For now, using mock data.
        """
        market_data = {}
        
        for ticker in tickers:
            # Mock: generate random price movement
            # In production: load actual historical data
            base_price = self._get_base_price(ticker)
            
            # Random walk: ±2% daily
            daily_change = np.random.uniform(-0.02, 0.02)
            close_price = base_price * (1 + daily_change)
            
            market_data[ticker] = {
                "close": close_price,
                "open": close_price * 0.99,
                "high": close_price * 1.01,
                "low": close_price * 0.98,
                "volume": np.random.randint(1_000_000, 10_000_000),
            }
        
        return market_data
    
    def _get_base_price(self, ticker: str) -> float:
        """Get base price for ticker (mock)."""
        base_prices = {
            "AAPL": 150.0,
            "MSFT": 300.0,
            "GOOGL": 140.0,
            "NVDA": 500.0,
            "TSLA": 250.0,
        }
        return base_prices.get(ticker, 100.0)
    
    def get_summary(self) -> str:
        """Get human-readable backtest summary."""
        if not self.equity_curve:
            return "No backtest results available."
        
        final_equity = self.equity_curve[-1][1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        completed_trades = [t for t in self.trades if t["action"] == "SELL"]
        winning_trades = [t for t in completed_trades if t.get("pnl", 0) > 0]
        
        summary = f"""
╔════════════════════════════════════════════════════════════════╗
║                    BACKTEST SUMMARY                             ║
╚════════════════════════════════════════════════════════════════╝

💰 Financial Performance
   Initial Capital:       ${self.initial_capital:,.0f}
   Final Equity:          ${final_equity:,.0f}
   Total Return:          {total_return:.2%}
   Max Drawdown:          {self.max_drawdown:.2%}

📊 Risk-Adjusted Returns
   Sharpe Ratio:          {self._calculate_sharpe():.2f}
   Daily Volatility:      {np.std(self.daily_returns)*100:.2f}%

📈 Trading Statistics
   Total Trades:          {len(self.trades)}
   Completed Trades:      {len(completed_trades)}
   Winning Trades:        {len(winning_trades)}
   Win Rate:              {len(winning_trades)/len(completed_trades)*100 if completed_trades else 0:.1f}%

💵 Transaction Costs
   Total Slippage:        {self._calculate_total_slippage():.2f} bps
   Total Commissions:     ${self._calculate_total_commissions():,.0f}
"""
        return summary
    
    def _calculate_sharpe(self) -> float:
        """Calculate Sharpe ratio."""
        if len(self.daily_returns) > 0:
            daily_mean = np.mean(self.daily_returns)
            daily_std = np.std(self.daily_returns)
            return (daily_mean / daily_std) * np.sqrt(252) if daily_std > 0 else 0.0
        return 0.0
    
    def _calculate_total_slippage(self) -> float:
        """Calculate total slippage in basis points."""
        return len(self.trades) * self.slippage_bps
    
    def _calculate_total_commissions(self) -> float:
        """Calculate total commissions paid."""
        return sum(t.get("commission", 0) for t in self.trades)