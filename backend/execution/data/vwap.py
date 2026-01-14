"""
Arrival VWAP Calculator

Calculates Volume Weighted Average Price (VWAP) starting from the 'Arrival' time of the order.
Used as the primary benchmark for the Execution RL agent's reward function.
"""

from typing import Optional

class ArrivalVWAP:
    """
    Tracks accumulated volume and turnover to calculate VWAP in real-time.
    Resets when a new parent order arrives.
    """
    def __init__(self):
        self.total_volume: int = 0
        self.total_turnover: float = 0.0 # Price * Volume
        
    def reset(self):
        """Reset counters for a new order."""
        self.total_volume = 0
        self.total_turnover = 0.0
        
    def update(self, price: float, volume: int):
        """Update with a new trade tick."""
        if volume <= 0:
            return
            
        self.total_turnover += price * volume
        self.total_volume += volume
        
    def get_vwap(self) -> Optional[float]:
        """
        Get current VWAP.
        Returns None if no volume yet.
        """
        if self.total_volume == 0:
            return None
            
        return self.total_turnover / self.total_volume
