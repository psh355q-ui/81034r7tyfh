
from typing import List, Dict, Any
from backend.ai.reasoning.models import MarketThesis

def calculate_heuristic_confidence(thesis: MarketThesis, technical_data: Dict[str, Any]) -> float:
    """
    Adjusts the AI's confidence score based on hard rules.
    """
    base_confidence = thesis.final_confidence_score
    penalty = 0.0
    
    # Rule 1: Risky check
    # If Bearish but RSI < 30 (Oversold), reduce confidence in Shorting
    if thesis.direction == "BEARISH":
        rsi = technical_data.get('rsi')
        if rsi and isinstance(rsi, (int, float)) and rsi < 30:
            penalty += 0.2  # Penalize "Shorting the bottom"
            
    # Rule 2: Bullish but Overbought
    if thesis.direction == "BULLISH":
        rsi = technical_data.get('rsi')
        if rsi and isinstance(rsi, (int, float)) and rsi > 70:
            penalty += 0.2  # Penalize "Buying the top"
            
    # Rule 3: Contradiction penalty
    if len(thesis.contradictions) > 0:
        penalty += 0.1 * len(thesis.contradictions)
        
    final_score = max(0.1, base_confidence - penalty)
    return round(final_score, 2)
