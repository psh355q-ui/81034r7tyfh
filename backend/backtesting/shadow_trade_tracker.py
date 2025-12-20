"""
Shadow Trade Tracker.

Tracks rejected trades to measure the "defensive value" of the Constitution.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from backend.data.models.shadow_trade import ShadowTrade

logger = logging.getLogger(__name__)

class ShadowTradeTracker:
    """
    Manages a collection of Shadow Trades during a backtest.
    """
    def __init__(self):
        self.active_shadow_trades: List[ShadowTrade] = []
        self.closed_shadow_trades: List[ShadowTrade] = []
        
    def add_trade(self, shadow_trade: ShadowTrade):
        """Add a new shadow trade to track."""
        self.active_shadow_trades.append(shadow_trade)
        logger.debug(f"Added Shadow Trade: {shadow_trade}")
        
    def update(self, current_date: datetime, current_prices: Dict[str, float]):
        """
        Update all active shadow trades with current prices.
        Check if tracking period has expired.
        """
        remaining_trades = []
        
        for trade in self.active_shadow_trades:
            if trade.ticker not in current_prices:
                remaining_trades.append(trade)
                continue
                
            current_price = current_prices[trade.ticker]
            
            # Update PnL
            trade.update_pnl(current_price)
            
            # Check expiration (e.g., 7 days)
            # Assuming created_at is set. If backtesting, created_at should be the rejection date.
            days_passed = (current_date - trade.created_at).days
            
            if days_passed >= trade.tracking_days:
                trade.close_tracking(current_price)
                self.closed_shadow_trades.append(trade)
                logger.debug(f"Closed Shadow Trade: {trade} (Avoided Loss: ${trade.get_avoided_loss():.2f})")
            else:
                remaining_trades.append(trade)
                
        self.active_shadow_trades = remaining_trades

    def get_metrics(self) -> Dict:
        """
        Calculate aggregate defensive metrics.
        """
        total_trades = len(self.active_shadow_trades) + len(self.closed_shadow_trades)
        if total_trades == 0:
            return {
                "total_shadow_trades": 0,
                "defensive_wins": 0,
                "defensive_win_rate": 0.0,
                "total_avoided_loss": 0.0,
                "missed_opportunities": 0
            }
            
        all_trades = self.active_shadow_trades + self.closed_shadow_trades
        
        defensive_wins = sum(1 for t in all_trades if t.is_defensive_win())
        defensive_win_rate = defensive_wins / total_trades
        
        total_avoided_loss = sum(t.get_avoided_loss() for t in all_trades)
        
        # Missed opportunities: Where we would have made money (Virtual PnL > 0 for BUY)
        # Assuming BUY rejection: Positive PnL means price went UP -> Missed Opportunity
        # Assuming SELL rejection: Negative PnL means price went DOWN (we held) -> Loss? Wait.
        # Shadow Trade Logic:
        # BUY Rejected: We confirm it was GOOD reject if price went DOWN (PnL < 0).
        #               If price went UP (PnL > 0), we missed profit.
        missed_opportunities = sum(1 for t in all_trades if not t.is_defensive_win())

        return {
            "total_shadow_trades": total_trades,
            "defensive_wins": defensive_wins,
            "defensive_win_rate": defensive_win_rate,
            "total_avoided_loss": total_avoided_loss,
            "missed_opportunities": missed_opportunities
        }
