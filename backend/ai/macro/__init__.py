"""
AI Macro Module - 글로벌 매크로 분석

Phase F2: 글로벌 매크로 확장

글로벌 시장 상관관계, 국가별 리스크, 나비효과 분석

Components:
- global_market_map: 글로벌 시장 상관관계 그래프
- country_risk_engine: 국가별 리스크 점수
- global_event_graph: 이벤트 전파 그래프 (예정)
"""

from backend.ai.macro.global_market_map import (
    AssetType,
    MarketNode,
    Correlation,
    ImpactPath,
    GlobalMarketMap,
    get_global_market_map
)

from backend.ai.macro.country_risk_engine import (
    Country,
    RiskLevel,
    CountryMacroData,
    CountryRiskScore,
    CountryRiskEngine,
    get_country_risk_engine
)

__all__ = [
    # Market Map
    "AssetType",
    "MarketNode",
    "Correlation",
    "ImpactPath",
    "GlobalMarketMap",
    "get_global_market_map",
    
    # Country Risk
    "Country",
    "RiskLevel",
    "CountryMacroData",
    "CountryRiskScore",
    "CountryRiskEngine",
    "get_country_risk_engine"
]
