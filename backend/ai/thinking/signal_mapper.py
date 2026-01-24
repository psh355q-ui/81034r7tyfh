"""
Signal Mapper - 인텔리전스 신호 매핑

추출된 인텔리전스(Entity/Fact)를 실제 거래 가능한 종목(Ticker)으로 매핑합니다.
Thinking Layer의 핵심 컴포넌트입니다.
"""

from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

class SignalMapper:
    """
    Maps market intelligence to tradable assets.
    """
    
    # Static Mapping Database (Extendable)
    # Keyword (Lower) -> Tickers List
    MAPPING_DB = {
        # --- Economy ---
        "inflation": ["TIP", "GLD", "TBT"],
        "cpi": ["TIP", "GLD"],
        "rate": ["TLT", "IEF", "SHY"],
        "labor": ["JOLT? (No Ticker)", "SPY"], # Labor usually affects broad market
        "jobs": ["SPY", "QQQ"],
        "recession": ["GLD", "TLT", "XLP"],
        
        # --- Sectors ---
        "tech": ["XLK", "QQQ", "VGT"],
        "semiconductor": ["SMH", "SOXX", "NVDA"],
        "chips": ["SMH", "SOXX"],
        "oil": ["XLE", "USO", "CVX", "XOM"],
        "energy": ["XLE", "ICLN"],
        "defense": ["XAR", "ITA", "LMT", "RTX"],
        "war": ["XAR", "ITA", "GLD", "LMT"],
        "bank": ["KBE", "XLF"],
        "finance": ["XLF"],
        "retail": ["XRT"],
        "housing": ["XHB", "ITB"],
        "construction": ["XHB", "CAT"],
        
        # --- Geopolitics / Countries ---
        "china": ["FXI", "MCHI", "KWEB"],
        "taiwan": ["EWT", "TSM"],
        "korea": ["EWY"],
        "japan": ["EWJ"],
        "europe": ["VGK", "EZU"],
        "bitcoin": ["IBIT", "BITO"],
        "crypto": ["IBIT", "COIN"],
        "greenland": ["N/A"] # Specific cases
    }

    def __init__(self):
        logger.info("SignalMapper initialized")

    def map_signals(self, intelligence_data: List[Dict]) -> List[Dict]:
        """
        Enrich intelligence data with related tickers.
        
        Args:
            intelligence_data: List of dicts from VideoAnalyzer._extract_intelligence
            
        Returns:
            Enriched list with 'related_tickers' field.
        """
        enriched_data = []
        
        for item in intelligence_data:
            # Create a copy to modify
            mapped_item = item.copy()
            found_tickers: Set[str] = set()
            
            # 1. Search in Entity
            entities = item.get('entity', [])
            if isinstance(entities, str): entities = [entities] # Handle if string
            
            for entity in entities:
                tickers = self._lookup_tickers(entity)
                found_tickers.update(tickers)
                
            # 2. Search in Fact (Keywords)
            fact = item.get('fact', "").lower()
            for keyword, tickers in self.MAPPING_DB.items():
                if keyword in fact:
                     found_tickers.update(tickers)
            
            # 3. Search in Related Sectors
            sectors = item.get('related_sectors', [])
            for sector in sectors:
                tickers = self._lookup_tickers(sector)
                found_tickers.update(tickers)

            mapped_item['related_tickers'] = list(found_tickers)
            enriched_data.append(mapped_item)
            
            if found_tickers:
                logger.info(f"Mapped signals: {entities} -> {found_tickers}")
                
        return enriched_data

    def _lookup_tickers(self, term: str) -> List[str]:
        """
        Simple fuzzy/exact lookup for a term.
        """
        term = term.lower().strip()
        
        # Exact Match
        if term in self.MAPPING_DB:
            return self.MAPPING_DB[term]
        
        # Partial Match (e.g. "semiconductor industry" -> "semiconductor")
        matches = []
        for key, tickers in self.MAPPING_DB.items():
            if key in term or term in key: # Bidirectional containment
                matches.extend(tickers)
                
        return list(set(matches)) # Unique list

# Global instance
_signal_mapper = None

def get_signal_mapper() -> SignalMapper:
    global _signal_mapper
    if _signal_mapper is None:
        _signal_mapper = SignalMapper()
    return _signal_mapper
