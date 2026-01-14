"""
Event Priority Gate

Dampens technical signals when strong news/fundamental events are present.
M3: The Brain
"""

from typing import List
from backend.fusion.normalizer import BaseSignal

class EventPriorityGate:
    """
    Prioritizes News/GNN signals over Technical signals during high impact events.
    """
    def __init__(self, news_impact_threshold: float = 0.8, dampening_factor: float = 0.5):
        self.news_impact_threshold = news_impact_threshold
        self.dampening_factor = dampening_factor

    def process_batch(self, signals: List[BaseSignal]) -> List[BaseSignal]:
        """
        Adjust signals based on event presence.
        """
        # 1. Check for strong news
        max_news_impact = 0.0
        for sig in signals:
            if sig.source in ["NEWS", "GNN"]:
                # Use absolute score or high confidence
                impact = abs(sig.score) * sig.confidence
                if impact > max_news_impact:
                    max_news_impact = impact
                    
        # 2. If strong news exists, dampen technical signals
        if max_news_impact >= self.news_impact_threshold:
            for sig in signals:
                if sig.source in ["CHART", "TECHNICAL"]:
                    sig.confidence *= self.dampening_factor
                    
        return signals
