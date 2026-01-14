"""
Fusion Engine

Core of The Brain.
Synthesizes normalized signals into a final Trading Intent using Gated Fusion.
M3: The Brain
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from backend.fusion.normalizer import BaseSignal
from backend.fusion.gates.liquidity import LiquidityGate
from backend.fusion.gates.event_priority import EventPriorityGate

@dataclass
class TradingIntent:
    ticker: str
    direction: str      # BUY, SELL, HOLD
    score: float        # -1.0 to 1.0 (Weighted Sum)
    confidence: float   # 0.0 to 1.0 (Avg Confidence or min)
    rationale: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class FusionEngine:
    """
    Combines signals and applies logic gates.
    """
    def __init__(self):
        # Default Gates
        self.liquidity_gate = LiquidityGate()
        self.event_gate = EventPriorityGate()
        
        # Default Weights per Source
        self.default_weights = {
            "NEWS": 0.4,
            "CHART": 0.4,
            "GNN": 0.2,
            "TECHNICAL": 0.4 # Alias for CHART
        }

    def fuse(
        self, 
        signals: List[BaseSignal], 
        weights: Optional[Dict[str, float]] = None,
        market_state: Optional[Dict[str, Any]] = None
    ) -> TradingIntent:
        """
        Process signals -> Apply Gates -> Weighted Sum -> Intent
        """
        if not signals:
            return TradingIntent("UNKNOWN", "HOLD", 0.0, 0.0, ["No signals"])

        # 0. Identify Ticker
        ticker = "UNKNOWN"
        for sig in signals:
            if sig.metadata and "ticker" in sig.metadata:
                ticker = sig.metadata["ticker"]
                break
                
        # 1. Apply Logic Gates (Pre-fusion filtering)
        current_state = market_state or {}
        
        # 1.1 Liquidity Gate (Filter individual signals)
        gated_signals = []
        for sig in signals:
            processed = self.liquidity_gate.process(sig, current_state)
            if processed:
                gated_signals.append(processed)
        
        # 1.2 Event Priority Gate (Batch adjustment)
        gated_signals = self.event_gate.process_batch(gated_signals)
        
        # 2. Weighted Sum
        active_weights = weights or self.default_weights
        total_score = 0.0
        total_weight = 0.0
        avg_confidence = 0.0
        
        rationale = []
        
        for sig in gated_signals:
            w = active_weights.get(sig.source, 0.0)
            
            # Weighted Contribution = Score * Confidence * Weight
            contribution = sig.score * sig.confidence * w
            
            total_score += contribution
            total_weight += w
            avg_confidence += sig.confidence
            
            rationale.append(f"{sig.source}: Score={sig.score:.2f}, Conf={sig.confidence:.2f}, W={w}")
            
        # Normalize final score
        final_score = 0.0
        if total_weight > 0:
            # We normalize by sum of weights used
            # But usually we want -1 to 1 scale. 
            # If total_weight is ~1.0, then sum is fine.
            final_score = total_score / total_weight if total_weight > 0 else 0.0
            avg_confidence /= len(gated_signals)
            
        # 3. Determine Direction
        direction = "HOLD"
        threshold = 0.2 # Decision threshold
        
        if final_score > threshold:
            direction = "BUY"
        elif final_score < -threshold:
            direction = "SELL"
            
        return TradingIntent(
            ticker=ticker,
            direction=direction,
            score=final_score,
            confidence=avg_confidence,
            rationale=rationale
        )
