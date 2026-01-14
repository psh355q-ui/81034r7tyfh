"""
Signal Normalizer

Standardizes signals from various sources (News, Chart, GNN) into a common scale.
Part of Multi-Modal Fusion (M3).
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class BaseSignal:
    source: str         # "NEWS", "CHART", "GNN"
    score: float        # Normalized: -1.0 (Strong Sell) to 1.0 (Strong Buy)
    confidence: float   # 0.0 to 1.0
    metadata: Optional[Dict[str, Any]] = None

class SignalNormalizer:
    """
    Utilities to create standardized signals.
    """
    
    def normalize_score(self, raw_score: float) -> float:
        """Clip score to [-1.0, 1.0]."""
        return max(-1.0, min(1.0, raw_score))
        
    def normalize_confidence(self, raw_conf: float) -> float:
        """Clip confidence to [0.0, 1.0]."""
        return max(0.0, min(1.0, raw_conf))
        
    def create_signal(
        self, 
        source: str, 
        score: float, 
        confidence: float, 
        metadata: Optional[Dict] = None
    ) -> BaseSignal:
        """Create a validated and normalized BaseSignal."""
        norm_score = self.normalize_score(score)
        norm_conf = self.normalize_confidence(confidence)
        
        return BaseSignal(
            source=source,
            score=norm_score,
            confidence=norm_conf,
            metadata=metadata
        )
