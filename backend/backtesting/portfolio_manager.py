"""
Portfolio Manager Module.

Manages portfolio state (cash, positions, equity) and handles trade execution logic
including slippage and commission calculations.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from .performance_metrics import calculate_comprehensive_metrics

logger = logging.getLogger(__name__)

class PortfolioManager:
    """
    Manages portfolio state, trade execution, and performance tracking.
    """
    def __init__(
        self,
        initial_capital: float = 100000.0,
        slippage_bps: float = 1.0,  # 0.01%
        commission_rate: float = 0.00015,  # 0.015%
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.slippage_bps = slippage_bps
        self.commission_rate = commission_rate
        
        # State
        self.positions: Dict[str, Dict] = {}  # ticker -> {shares, entry_price, ...}
        self.trades: List[Dict] = []  # List of executed trades
        self.equity_curve: List[Tuple[datetime, float]] = []  # (date, equity)
        self.daily_returns: List[float] = []

    def get_current_equity(self, current_prices: Dict[str, float]) -> float:
        """Calculate total equity (cash + market value of positions)."""
        position_value = 0.0
        for ticker, position in self.positions.items():
            if ticker in current_prices:
                position_value += position['shares'] * current_prices[ticker]
            else:
                # Fallback to entry price or last known price if current not available
                # (Ideally current_prices should contain all tickers)
                logger.warning(f"No current price for {ticker}, using last known")
                position_value += position['shares'] * position.get('last_price', position['entry_price'])
                
        return self.cash + position_value

    def update_mark_to_market(self, current_date: datetime, current_prices: Dict[str, float]):
        """Update portfolio value for the day."""
        equity = self.get_current_equity(current_prices)
        
        # Record equity
        self.equity_curve.append((current_date, equity))
        
        # Calculate daily return
        if len(self.equity_curve) > 1:
            prev_equity = self.equity_curve[-2][1]
            if prev_equity > 0:
                daily_return = (equity - prev_equity) / prev_equity
                self.daily_returns.append(daily_return)
        
        # Update last known prices in positions
        for ticker, price in current_prices.items():
            if ticker in self.positions:
                self.positions[ticker]['last_price'] = price

    def execute_trade(
        self,
        ticker: str,
        action: str,  # "BUY" or "SELL"
        amount: float, # Shares for BUY? Or Value? Assuming Shares based on internal logic or logic below
        price: float,
        date: datetime,
        reason: str = ""
    ) -> bool:
        """
        Execute a trade. 
        Note: The caller determines 'amount' (shares).
        """
        if action not in ["BUY", "SELL"]:
            return False

        # Apply Slippage
        execution_price = price * (1 + self.slippage_bps/10000) if action == "BUY" else price * (1 - self.slippage_bps/10000)
        
        # Calculate Costs
        trade_value = amount * execution_price
        commission = trade_value * self.commission_rate
        
        if action == "BUY":
            total_cost = trade_value + commission
            if total_cost > self.cash:
                logger.warning(f"Insufficient cash to BUY {ticker}: Need {total_cost}, Have {self.cash}")
                return False
                
            self.cash -= total_cost
            
            # Update Position
            if ticker in self.positions:
                # Average Down/Up
                current_shares = self.positions[ticker]['shares']
                total_shares = current_shares + amount
                # Weighted average price
                avg_price = ((current_shares * self.positions[ticker]['entry_price']) + (amount * execution_price)) / total_shares
                
                self.positions[ticker]['shares'] = total_shares
                self.positions[ticker]['entry_price'] = avg_price
                self.positions[ticker]['last_price'] = execution_price
            else:
                self.positions[ticker] = {
                    'shares': amount,
                    'entry_price': execution_price,
                    'entry_date': date,
                    'last_price': execution_price
                }
                
        elif action == "SELL":
            if ticker not in self.positions:
                logger.warning(f"Cannot SELL {ticker}: No position")
                return False
                
            current_shares = self.positions[ticker]['shares']
            if amount > current_shares:
                logger.warning(f"Cannot SELL {amount} {ticker}: Only have {current_shares}")
                return False
                
            proceeds = trade_value - commission
            self.cash += proceeds
            
            # Record P&L
            entry_price = self.positions[ticker]['entry_price']
            cost_basis = amount * entry_price
            pnl = proceeds - cost_basis # Net P&L after commission? Approx. Pnl = (ExPrice - EnPrice)*Shares - Comm
            pnl_pct = pnl / cost_basis if cost_basis > 0 else 0
            
            # Update Position
            self.positions[ticker]['shares'] -= amount
            if self.positions[ticker]['shares'] <= 0:
                del self.positions[ticker]
            
            # Log Trade with P&L
            self.trades.append({
                "date": date,
                "ticker": ticker,
                "action": "SELL",
                "shares": amount,
                "price": execution_price,
                "commission": commission,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "reason": reason
            })
            return True

        # Log BUY trade (no P&L yet)
        self.trades.append({
            "date": date,
            "ticker": ticker,
            "action": "BUY",
            "shares": amount,
            "price": execution_price,
            "commission": commission,
            "reason": reason
        })
        return True

    def get_metrics(self) -> Dict:
        """Get current performance metrics."""
        equity_values = [e[1] for e in self.equity_curve]
        return calculate_comprehensive_metrics(
            self.initial_capital,
            equity_values,
            self.trades,
            self.daily_returns
        )
