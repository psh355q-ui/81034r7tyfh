"""
Knowledge Gate (Edge Filter)

Filters or adjusts edge weights based on static knowledge (Sector) and price correlations.
M2: The Eyes
"""

from typing import Dict, Tuple, Optional

class KnowledgeGate:
    """
    Gatekeeper for Graph Edges.
    """
    def __init__(
        self, 
        sector_map: Dict[str, str],
        corr_map: Dict[Tuple[str, str], float],
        min_correlation: float = 0.3
    ):
        self.sector_map = sector_map
        self.corr_map = corr_map
        self.min_correlation = min_correlation
        
    def apply_gate(self, u: str, v: str, initial_weight: float) -> float:
        """
        Adjust edge weight. Returns 0.0 if filtered out.
        """
        # 1. Ticker Validation
        if u not in self.sector_map or v not in self.sector_map:
            return 0.0
            
        # 2. Correlation Check
        # Check (u, v) or (v, u)
        corr = self.corr_map.get((u, v))
        if corr is None:
            corr = self.corr_map.get((v, u))
            
        if corr is not None:
            if corr < self.min_correlation:
                return 0.0 # Block weak correlation
        else:
            # Conservative: If no correlation data, default to block or low weight
            return 0.0 
            
        # 3. Sector Bonus (Optional)
        # If same sector, maybe boost weight?
        final_weight = initial_weight
        if self.sector_map[u] == self.sector_map[v]:
            final_weight *= 1.1
            
        return final_weight
