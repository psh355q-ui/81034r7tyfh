"""
News Co-occurrence Builder

Parses news text to detect ticker mentions and builds co-occurrence edges.
Part of the GNN Impact Analysis module (M2).
"""

import re
from itertools import combinations
from typing import List, Tuple, Set

class NewsCooccurrenceBuilder:
    """
    Detects multiple tickers in text and creates edges between them.
    """
    def __init__(self, known_tickers: List[str]):
        """
        Args:
            known_tickers: List of ticker symbols to look for (e.g., ["AAPL", "NVDA"])
        """
        self.known_tickers = set(known_tickers)
        # Create regex pattern for exact word match
        # \b(AAPL|NVDA|...)\b
        escaped_tickers = [re.escape(t) for t in known_tickers]
        self.pattern = re.compile(r'\b(' + '|'.join(escaped_tickers) + r')\b')

    def extract_edges(self, text: str) -> List[Tuple[str, str, float]]:
        """
        Extract co-occurrence edges from text.
        
        Returns:
            List of (TickerA, TickerB, Weight)
        """
        found_tickers = self._find_tickers(text)
        
        if len(found_tickers) < 2:
            return []
            
        edges = []
        # Create complete graph between found tickers (Clique)
        for u, v in combinations(found_tickers, 2):
            # Sort to ensure canonical edge (A-B instead of B-A)
            if u > v:
                u, v = v, u
            edges.append((u, v, 1.0))
            
        return edges

    def _find_tickers(self, text: str) -> Set[str]:
        """Find unique tickers mentioned in text."""
        matches = self.pattern.findall(text)
        return set(matches)
