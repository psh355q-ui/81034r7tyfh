"""
Global Market Map - 글로벌 시장 상관관계 그래프

Phase F2: 글로벌 매크로 확장

자산/섹터/국가 간의 상관관계를 정의하고 이벤트 전파 경로를 추론

주요 기능:
- 자산 간 상관관계 정의 (correlations)
- 이벤트 영향 경로 탐색 (BFS/DFS)
- 글로벌 나비효과 시뮬레이션

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque
import logging
import networkx as nx  # Added for graph support

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 자산 유형 정의
# ═══════════════════════════════════════════════════════════════

class AssetType(str, Enum):
    """자산 유형"""
    CURRENCY = "currency"      # 통화
    BOND = "bond"              # 채권
    EQUITY = "equity"          # 주식
    COMMODITY = "commodity"    # 원자재
    INDEX = "index"            # 지수
    SECTOR = "sector"          # 섹터
    COUNTRY = "country"        # 국가
    INDICATOR = "indicator"    # 경제지표


@dataclass
class MarketNode:
    """시장 노드 (자산/섹터/지수)"""
    id: str
    name: str
    asset_type: AssetType
    country: Optional[str] = None  # US, JP, CN, EU, KR
    current_value: Optional[float] = None
    change_pct: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "asset_type": self.asset_type.value,
            "country": self.country,
            "current_value": self.current_value,
            "change_pct": self.change_pct,
            "metadata": self.metadata
        }


@dataclass
class Correlation:
    """자산 간 상관관계"""
    source: str
    target: str
    coefficient: float  # -1.0 ~ 1.0
    reason: str
    lag_days: int = 0  # 지연 효과 (일)
    confidence: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "coefficient": self.coefficient,
            "reason": self.reason,
            "lag_days": self.lag_days,
            "confidence": self.confidence
        }


@dataclass
class ImpactPath:
    """이벤트 영향 경로"""
    path: List[str]  # 노드 ID 경로
    total_impact: float  # 누적 영향도
    reasons: List[str]  # 각 단계 이유
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "total_impact": self.total_impact,
            "reasons": self.reasons,
            "confidence": self.confidence
        }


# ═══════════════════════════════════════════════════════════════
# Global Market Map 클래스
# ═══════════════════════════════════════════════════════════════

class GlobalMarketMap:
    """
    글로벌 시장 상관관계 그래프
    
    Usage:
        gmap = GlobalMarketMap()
        
        # 이벤트 영향 분석
        paths = gmap.trace_impact("JPY_STRENGTH", -0.5)
        for path in paths:
            print(f"{' -> '.join(path.path)}: {path.total_impact:.2%}")
        
        # 특정 자산에 영향주는 노드들 조회
        sources = gmap.get_impact_sources("KOSPI")
    """
    
    def __init__(self):
        """초기화 및 기본 상관관계 정의"""
        self.nodes: Dict[str, MarketNode] = {}
        self.correlations: Dict[str, List[Correlation]] = {}  # source -> [correlations]
        self.reverse_correlations: Dict[str, List[Correlation]] = {}  # target -> [correlations]
        self.graph = nx.DiGraph()  # ✅ Added: NetworkX graph for advanced analysis
        
        # 기본 노드 및 상관관계 정의
        self._setup_default_nodes()
        self._setup_default_correlations()
        
        logger.info(f"GlobalMarketMap initialized: {len(self.nodes)} nodes, {self._count_correlations()} correlations")
    
    def _setup_default_nodes(self):
        """기본 시장 노드 설정"""
        default_nodes = [
            # 통화
            MarketNode("USD_INDEX", "US Dollar Index", AssetType.CURRENCY, "US"),
            MarketNode("JPY_STRENGTH", "Japanese Yen Strength", AssetType.CURRENCY, "JP"),
            MarketNode("CNY_WEAKNESS", "Chinese Yuan Weakness", AssetType.CURRENCY, "CN"),
            MarketNode("EUR_INDEX", "Euro Index", AssetType.CURRENCY, "EU"),
            MarketNode("KRW_INDEX", "Korean Won Index", AssetType.CURRENCY, "KR"),
            
            # 금리/채권
            MarketNode("US_10Y", "US 10-Year Treasury", AssetType.BOND, "US"),
            MarketNode("US_2Y", "US 2-Year Treasury", AssetType.BOND, "US"),
            MarketNode("US_YIELD_CURVE", "US Yield Curve", AssetType.INDICATOR, "US"),
            MarketNode("BOJ_RATE", "BOJ Policy Rate", AssetType.INDICATOR, "JP"),
            MarketNode("ECB_RATE", "ECB Policy Rate", AssetType.INDICATOR, "EU"),
            MarketNode("FED_RATE", "Fed Funds Rate", AssetType.INDICATOR, "US"),
            
            # 주요 지수
            MarketNode("SPX", "S&P 500", AssetType.INDEX, "US"),
            MarketNode("NDX", "NASDAQ 100", AssetType.INDEX, "US"),
            MarketNode("VIX", "VIX Volatility", AssetType.INDEX, "US"),
            MarketNode("KOSPI", "KOSPI", AssetType.INDEX, "KR"),
            MarketNode("NIKKEI", "Nikkei 225", AssetType.INDEX, "JP"),
            MarketNode("CSI300", "CSI 300", AssetType.INDEX, "CN"),
            
            # 유동성
            MarketNode("US_TECH_LIQUIDITY", "US Tech Liquidity", AssetType.INDICATOR, "US"),
            MarketNode("GLOBAL_RISK_APPETITE", "Global Risk Appetite", AssetType.INDICATOR, None),
            
            # 원자재
            MarketNode("CRUDE_OIL", "Crude Oil (WTI)", AssetType.COMMODITY, None),
            MarketNode("GOLD", "Gold", AssetType.COMMODITY, None),
            MarketNode("COPPER", "Copper", AssetType.COMMODITY, None),
            MarketNode("NATURAL_GAS", "Natural Gas", AssetType.COMMODITY, None),
            
            # 반도체
            MarketNode("SEMICONDUCTOR", "Semiconductor Sector", AssetType.SECTOR, "US"),
            MarketNode("AI_CHIPS", "AI Chip Demand", AssetType.SECTOR, None),
            MarketNode("HBM_DEMAND", "HBM Memory Demand", AssetType.SECTOR, "KR"),
            
            # 기타 섹터
            MarketNode("ENERGY_SECTOR", "Energy Sector", AssetType.SECTOR, "US"),
            MarketNode("AIRLINE_SECTOR", "Airline Sector", AssetType.SECTOR, None),
            MarketNode("TECH_SECTOR", "Tech Sector", AssetType.SECTOR, "US"),
            MarketNode("FINANCE_SECTOR", "Financial Sector", AssetType.SECTOR, "US"),
        ]
        
        for node in default_nodes:
            self.nodes[node.id] = node
    
    def _setup_default_correlations(self):
        """기본 상관관계 설정"""
        default_correlations = [
            # 엔화 강세 영향
            Correlation("JPY_STRENGTH", "US_TECH_LIQUIDITY", -0.8, "Yen carry trade unwind"),
            Correlation("JPY_STRENGTH", "NIKKEI", -0.6, "Export competitiveness decline"),
            Correlation("JPY_STRENGTH", "GLOBAL_RISK_APPETITE", -0.5, "Risk-off signal"),
            
            # 유동성 영향
            Correlation("US_TECH_LIQUIDITY", "NDX", 0.85, "Tech funding dependency"),
            Correlation("US_TECH_LIQUIDITY", "SEMICONDUCTOR", 0.75, "VC funding for chips"),
            Correlation("US_TECH_LIQUIDITY", "AI_CHIPS", 0.7, "AI investment liquidity"),
            
            # 위험선호도 영향
            Correlation("GLOBAL_RISK_APPETITE", "SPX", 0.7, "Risk-on equity rally"),
            Correlation("GLOBAL_RISK_APPETITE", "KOSPI", 0.6, "EM risk sentiment"),
            Correlation("GLOBAL_RISK_APPETITE", "VIX", -0.85, "Fear gauge inverse"),
            Correlation("GLOBAL_RISK_APPETITE", "GOLD", -0.4, "Safe haven unwind"),
            
            # 달러 영향
            Correlation("USD_INDEX", "GOLD", -0.5, "Dollar-denominated assets"),
            Correlation("USD_INDEX", "CRUDE_OIL", -0.4, "Dollar-priced commodities"),
            Correlation("USD_INDEX", "KRW_INDEX", -0.6, "EM currency pressure"),
            
            # 금리 영향
            Correlation("FED_RATE", "US_10Y", 0.7, "Monetary policy transmission"),
            Correlation("FED_RATE", "USD_INDEX", 0.5, "Interest rate differential"),
            Correlation("FED_RATE", "US_TECH_LIQUIDITY", -0.6, "Higher cost of capital"),
            Correlation("US_10Y", "TECH_SECTOR", -0.5, "DCF valuation impact"),
            Correlation("US_10Y", "FINANCE_SECTOR", 0.6, "NIM expansion"),
            
            # 원유 영향
            Correlation("CRUDE_OIL", "ENERGY_SECTOR", 0.9, "Revenue increase"),
            Correlation("CRUDE_OIL", "AIRLINE_SECTOR", -0.8, "Fuel cost surge"),
            Correlation("CRUDE_OIL", "NATURAL_GAS", 0.6, "Energy complex correlation"),
            
            # 반도체 체인
            Correlation("AI_CHIPS", "SEMICONDUCTOR", 0.8, "AI driving chip demand"),
            Correlation("AI_CHIPS", "HBM_DEMAND", 0.85, "HBM for AI accelerators"),
            Correlation("SEMICONDUCTOR", "KOSPI", 0.5, "Samsung/SK weight"),
            
            # 중국 영향
            Correlation("CNY_WEAKNESS", "CSI300", -0.4, "Capital outflow fear"),
            Correlation("CNY_WEAKNESS", "COPPER", -0.5, "China demand proxy"),
            Correlation("CSI300", "KOSPI", 0.45, "Trade linkage"),
            
            # VIX 영향
            Correlation("VIX", "SPX", -0.75, "Fear vs equity"),
            Correlation("VIX", "GOLD", 0.3, "Flight to safety"),
        ]
        
        for corr in default_correlations:
            self.add_correlation(corr)
    
    def add_node(self, node: MarketNode):
        """노드 추가"""
        self.nodes[node.id] = node
        logger.debug(f"Added node: {node.id}")
    
    def add_correlation(self, correlation: Correlation):
        """상관관계 추가"""
        source = correlation.source
        target = correlation.target
        
        if source not in self.correlations:
            self.correlations[source] = []
        self.correlations[source].append(correlation)
        
        if target not in self.reverse_correlations:
            self.reverse_correlations[target] = []
        self.reverse_correlations[target].append(correlation)
    
    def get_node(self, node_id: str) -> Optional[MarketNode]:
        """노드 조회"""
        return self.nodes.get(node_id)
    
    def get_direct_impacts(self, source_id: str) -> List[Correlation]:
        """직접 영향받는 노드들 조회"""
        return self.correlations.get(source_id, [])
    
    def get_impact_sources(self, target_id: str) -> List[Correlation]:
        """해당 노드에 영향주는 소스들 조회"""
        return self.reverse_correlations.get(target_id, [])
    
    def trace_impact(
        self,
        source_id: str,
        initial_shock: float,
        max_depth: int = 4,
        min_impact: float = 0.05
    ) -> List[ImpactPath]:
        """
        이벤트 영향 경로 추적 (BFS)
        
        Args:
            source_id: 시작 노드 ID
            initial_shock: 초기 충격 (-1.0 ~ 1.0)
            max_depth: 최대 탐색 깊이
            min_impact: 최소 영향도 (이 이하는 무시)
            
        Returns:
            영향 경로 목록
        """
        if source_id not in self.nodes:
            logger.warning(f"Source node not found: {source_id}")
            return []
        
        impact_paths: List[ImpactPath] = []
        visited: Set[Tuple[str, ...]] = set()
        
        # BFS 큐: (path, cumulative_impact, reasons)
        queue = deque([(
            [source_id],
            initial_shock,
            ["Initial shock"],
            1.0  # confidence
        )])
        
        while queue:
            current_path, current_impact, reasons, confidence = queue.popleft()
            current_node = current_path[-1]
            
            if len(current_path) > max_depth:
                continue
            
            # 직접 연결된 노드들 탐색
            for corr in self.get_direct_impacts(current_node):
                next_impact = current_impact * corr.coefficient
                next_confidence = confidence * corr.confidence
                
                # 영향도가 너무 작으면 스킵
                if abs(next_impact) < min_impact:
                    continue
                
                # 순환 방지
                if corr.target in current_path:
                    continue
                
                new_path = current_path + [corr.target]
                path_tuple = tuple(new_path)
                
                if path_tuple in visited:
                    continue
                visited.add(path_tuple)
                
                new_reasons = reasons + [corr.reason]
                
                # 영향 경로 저장
                impact_paths.append(ImpactPath(
                    path=new_path,
                    total_impact=next_impact,
                    reasons=new_reasons,
                    confidence=next_confidence
                ))
                
                # 다음 탐색
                queue.append((new_path, next_impact, new_reasons, next_confidence))
        
        # 영향도 순 정렬
        impact_paths.sort(key=lambda x: abs(x.total_impact), reverse=True)
        
        return impact_paths
    
    def simulate_event(
        self,
        event_source: str,
        shock: float,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        이벤트 시뮬레이션
        
        Args:
            event_source: 이벤트 시작 노드
            shock: 충격 크기 (-1.0 ~ 1.0)
            description: 이벤트 설명
            
        Returns:
            시뮬레이션 결과
        """
        logger.info(f"Simulating event: {event_source} shock={shock:.2f}")
        
        paths = self.trace_impact(event_source, shock)
        
        # 최종 영향 집계
        final_impacts: Dict[str, float] = {}
        for path in paths:
            target = path.path[-1]
            if target not in final_impacts:
                final_impacts[target] = 0
            final_impacts[target] += path.total_impact * path.confidence
        
        # 결과 정리
        sorted_impacts = sorted(
            final_impacts.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        result = {
            "event": {
                "source": event_source,
                "shock": shock,
                "description": description,
                "timestamp": datetime.now().isoformat()
            },
            "paths_count": len(paths),
            "affected_nodes": len(final_impacts),
            "top_impacts": [
                {
                    "node": node_id,
                    "impact": impact,
                    "direction": "positive" if impact > 0 else "negative"
                }
                for node_id, impact in sorted_impacts[:10]
            ],
            "detailed_paths": [p.to_dict() for p in paths[:20]]
        }
        
        return result
    
    def get_sector_signals(
        self,
        event_source: str,
        shock: float,
        threshold: float = 0.1
    ) -> Dict[str, str]:
        """
        섹터별 매매 시그널 생성
        
        Args:
            event_source: 이벤트 소스
            shock: 충격 크기
            threshold: 시그널 임계값
            
        Returns:
            섹터별 시그널 (BUY, SELL, HOLD)
        """
        result = self.simulate_event(event_source, shock)
        signals = {}
        
        for item in result["top_impacts"]:
            node_id = item["node"]
            impact = item["impact"]
            node = self.get_node(node_id)
            
            if not node or node.asset_type not in [AssetType.SECTOR, AssetType.INDEX]:
                continue
            
            if impact > threshold:
                signals[node_id] = "BUY"
            elif impact < -threshold:
                signals[node_id] = "SELL"
            else:
                signals[node_id] = "HOLD"
        
        return signals
    
    def _count_correlations(self) -> int:
        """상관관계 수 카운트"""
        return sum(len(corrs) for corrs in self.correlations.values())
    
    async def update_market_data(self):
        """
        실제 시장 데이터 업데이트 (Yahoo Finance)
        """
        try:
            import yfinance as yf
            
            # Key Market Indicators Mapping
            # Node ID: YFinance Ticker
            ticker_map = {
                "SPX": "^GSPC",
                "NDX": "^NDX",
                "VIX": "^VIX",
                "KOSPI": "^KS11",
                "NIKKEI": "^N225",
                "CSI300": "000300.SS",
                "USD_INDEX": "DX-Y.NYB",
                "US_10Y": "^TNX",
                "CRUDE_OIL": "CL=F",
                "GOLD": "GC=F",
                "COPPER": "HG=F",
                "NATURAL_GAS": "NG=F",
                "EUR_INDEX": "EURUSD=X",
                "KRW_INDEX": "KRW=X",
                "JPY_STRENGTH": "JPY=X" # Higher means weaker JPY vs USD usually, need to inverse for strength logic if needed
            }
            
            tickers = list(ticker_map.values())
            data = yf.Tickers(" ".join(tickers))
            
            updated_count = 0
            
            for node_id, ticker in ticker_map.items():
                try:
                    info = data.tickers[ticker].fast_info
                    price = info.last_price
                    prev_close = info.previous_close
                    
                    if price and prev_close:
                        change_pct = ((price - prev_close) / prev_close) # decimal format
                        
                        # Special handling for VIX (absolute change might be more relevant, but sticking to pct for consistency)
                        
                        # Update Node
                        if node_id in self.nodes:
                            self.nodes[node_id].current_value = price
                            self.nodes[node_id].change_pct = change_pct
                            self.nodes[node_id].metadata["last_updated"] = datetime.now().isoformat()
                            updated_count += 1
                            
                except Exception as e:
                    logger.debug(f"Failed to fetch {node_id} ({ticker}): {e}")
            
            logger.info(f"Updated {updated_count} market nodes with real data")
            return updated_count
            
        except ImportError:
            logger.warning("yfinance not installed, skipping real data update")
            return 0
        except Exception as e:
            logger.error(f"Market data update error: {e}")
            return 0

    def get_summary(self) -> Dict[str, Any]:
        """맵 요약"""
        return {
            "nodes": len(self.nodes),
            "correlations": self._count_correlations(),
            "node_types": {
                asset_type.value: sum(1 for n in self.nodes.values() if n.asset_type == asset_type)
                for asset_type in AssetType
            },
            "countries": list(set(
                n.country for n in self.nodes.values() if n.country
            ))
        }


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_global_market_map: Optional[GlobalMarketMap] = None


def get_global_market_map() -> GlobalMarketMap:
    """GlobalMarketMap 싱글톤 인스턴스"""
    global _global_market_map
    if _global_market_map is None:
        _global_market_map = GlobalMarketMap()
    return _global_market_map


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    gmap = GlobalMarketMap()
    
    print("=== Global Market Map Test ===\n")
    print(f"Summary: {gmap.get_summary()}\n")
    
    # 시나리오 1: 일본 BOJ 금리 인상 (엔화 강세)
    print("="*60)
    print("Scenario: BOJ Rate Hike -> JPY Strength")
    print("="*60)
    
    result = gmap.simulate_event(
        event_source="JPY_STRENGTH",
        shock=-0.5,  # 50% 강세
        description="BOJ surprises with rate hike"
    )
    
    print(f"\nAffected nodes: {result['affected_nodes']}")
    print(f"Total paths: {result['paths_count']}")
    print("\nTop Impacts:")
    for item in result["top_impacts"][:8]:
        direction = "📈" if item["impact"] > 0 else "📉"
        print(f"  {direction} {item['node']}: {item['impact']:.1%}")
    
    # 시그널 생성
    print("\nSector Signals:")
    signals = gmap.get_sector_signals("JPY_STRENGTH", -0.5)
    for sector, signal in signals.items():
        print(f"  {sector}: {signal}")
    
    # 시나리오 2: 유가 급등
    print("\n" + "="*60)
    print("Scenario: Oil Price Surge")
    print("="*60)
    
    signals = gmap.get_sector_signals("CRUDE_OIL", 0.3)
    for sector, signal in signals.items():
        print(f"  {sector}: {signal}")
