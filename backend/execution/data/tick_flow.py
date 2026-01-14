"""
TickFlow Calculator

Calculates the net order flow (Buy Volume - Sell Volume) over a sliding time window.
Used as a state feature for Execution RL agent.
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Tick:
    timestamp: datetime
    price: float
    volume: int
    is_buy_initiated: bool  # True if Buyer Initiated (Ask hit), False if Seller Initiated (Bid hit)

class TickFlow:
    """
    Manages a stream of ticks and calculates flow metrics.
    """
    def __init__(self):
        self.ticks: List[Tick] = []
        
    def add_tick(self, timestamp: datetime, price: float, volume: int, is_buy_initiated: bool):
        """Add a new trade tick."""
        tick = Tick(timestamp, price, volume, is_buy_initiated)
        self.ticks.append(tick)
        
    def get_flow(self, window_seconds: int, current_time: Optional[datetime] = None) -> float:
        """
        Calculate Net Flow for the last `window_seconds`.
        
        Flow = Sum(Price * Volume * Direction)
        Direction = +1 (Buy) / -1 (Sell)
        
        Returns:
            Net Flow (Money Amount)
        """
        if current_time is None:
            current_time = datetime.now()
            
        cutoff_time = current_time - timedelta(seconds=window_seconds)
        
        net_flow = 0.0
        
        # Iterate backwards for efficiency (though list is small for short windows)
        for tick in reversed(self.ticks):
            if tick.timestamp < cutoff_time:
                break
                
            if tick.timestamp > current_time:
                continue
                
            amount = tick.price * tick.volume
            direction = 1.0 if tick.is_buy_initiated else -1.0
            
            net_flow += amount * direction
            
        return net_flow
        
    def cleanup(self, current_time: datetime, max_age_seconds: int = 60):
        """Remove ticks older than max_age_seconds."""
        cutoff_time = current_time - timedelta(seconds=max_age_seconds)
        
        # Since ticks are appended in chronological order, we can find the split point
        # But for simple implementation with small list, list comprehension is fine.
        # Optimization: use deque or bisect if performance becomes an issue.
        self.ticks = [t for t in self.ticks if t.timestamp >= cutoff_time]
