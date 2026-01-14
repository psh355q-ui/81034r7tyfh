"""
Liquidity Gate

Filters out Technical/Chart signals when market volume is too low to reliability trade.
M3: The Brain
"""

from typing import Dict, Optional, Any
from backend.fusion.normalizer import BaseSignal

class LiquidityGate:
    """
    Blocks technical signals if volume is low.
    """
    def __init__(self, min_volume: float = 10000.0):
        self.min_volume = min_volume

    def process(self, signal: BaseSignal, market_state: Dict[str, Any]) -> Optional[BaseSignal]:
        """
        Check volume and dampen/block signal if needed.
        """
        # Only apply to CHART/TECHNICAL signals
        if signal.source not in ["CHART", "TECHNICAL"]:
            return signal
            
        current_volume = market_state.get("volume", 0.0)
        
        if current_volume < self.min_volume:
            # Low liquidity -> Block signal (Confidence 0)
            signal.confidence = 0.0
            return signal
            
        return signal
