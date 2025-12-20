"""
Global Event Graph - 글로벌 이벤트 영향 전파 분석

국가 간 경제 이벤트의 도미노 효과를 모델링하여 연쇄 반응 예측

핵심 기능:
1. 이벤트 전파 경로 추적 (A국 → B국 → C국)
2. 영향도 계산 (직접/간접)
3. 시간 지연 모델링
4. 리스크 증폭 감지

작성일: 2025-12-14
Phase: B Week 2
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import networkx as nx

logger = logging.getLogger(__name__)


class EventType(Enum):
    """이벤트 유형"""
    INTEREST_RATE = "interest_rate"
    GDP_CHANGE = "gdp_change"
    CURRENCY_CRISIS = "currency_crisis"
    TRADE_POLICY = "trade_policy"
    POLITICAL_CHANGE = "political_change"
    NATURAL_DISASTER = "natural_disaster"
    TECH_BREAKTHROUGH = "tech_breakthrough"


class ImpactLevel(Enum):
    """영향 수준"""
    NEGLIGIBLE = 0.1
    LOW = 0.3
    MODERATE = 0.5
    HIGH = 0.7
    CRITICAL = 0.9


@dataclass
class EconomicEvent:
    """경제 이벤트"""
    id: str
    country: str
    type: EventType
    description: str
    magnitude: float  # 0.0 ~ 1.0
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)


@dataclass
class PropagationPath:
    """전파 경로"""
    source_event: EconomicEvent
    path: List[Tuple[str, str, float]]  # (from_country, to_country, impact)
    total_impact: float
    time_delay_hours: int
    confidence: float


class GlobalEventGraph:
    """
    글로벌 이벤트 영향 전파 그래프
    
    경제 이벤트가 국가 간 어떻게 전파되는지 모델링
    
    예시 시나리오:
    1. 일본 금리 인상 (0.5%)
       → 엔캐리 트레이드 청산
       → 나스닥 유동성 축소 (-2%)
       → 코스피 하락 (-3%)
    
    2. 중국 GDP 하락
       → 원자재 수요 감소
       → 호주 수출 타격
       → 한국 반도체 수출 감소
    
    Usage:
        graph = GlobalEventGraph()
        
        # 이벤트 생성
        event = EconomicEvent(
            id="jp_rate_hike_2025",
            country="Japan",
            type=EventType.INTEREST_RATE,
            description="BOJ raises rate to 0.5%",
            magnitude=0.7
        )
        
        # 영향 전파 분석
        impacts = graph.analyze_propagation(event)
    """
    
    # 국가 간 연결 강도 (실제로는 DB나 설정 파일로)
    CONNECTIONS = {
        # 일본 → 다른 국가
        ("Japan", "USA"): {
            "channels": ["carry_trade", "treasury_holdings"],
            "strength": 0.8,
            "delay_hours": 24
        },
        ("Japan", "Korea"): {
            "channels": ["supply_chain", "tourism"],
            "strength": 0.6,
            "delay_hours": 12
        },
        
        # 미국 → 다른 국가
        ("USA", "Korea"): {
            "channels": ["tech_exports", "fx_reserves"],
            "strength": 0.9,
            "delay_hours": 12
        },
        ("USA", "China"): {
            "channels": ["trade", "tech"],
            "strength": 0.85,
            "delay_hours": 24
        },
        
        # 중국 → 다른 국가
        ("China", "Korea"): {
            "channels": ["trade", "supply_chain"],
            "strength": 0.75,
            "delay_hours": 18
        },
        ("China", "Australia"): {
            "channels": ["commodities", "iron_ore"],
            "strength": 0.7,
            "delay_hours": 12
        },
    }
    
    def __init__(self):
        """글로벌 이벤트 그래프 초기화"""
        # NetworkX 그래프 생성
        self.graph = nx.DiGraph()
        
        # 연결 추가
        for (source, target), props in self.CONNECTIONS.items():
            self.graph.add_edge(
                source, target,
                **props
            )
        
        logger.info(
            f"GlobalEventGraph initialized: "
            f"{self.graph.number_of_nodes()} countries, "
            f"{self.graph.number_of_edges()} connections"
        )
    
    def analyze_propagation(
        self,
        event: EconomicEvent,
        target_country: Optional[str] = None,
        max_hops: int = 3
    ) -> List[PropagationPath]:
        """
        이벤트 전파 분석
        
        Args:
            event: 분석할 이벤트
            target_country: 특정 타겟 국가 (None이면 모든 국가)
            max_hops: 최대 전파 단계
            
        Returns:
            전파 경로 리스트
        """
        paths = []
        
        if target_country:
            # 특정 국가로의 경로만
            country_paths = self._find_paths(
                event.country, target_country, max_hops
            )
            for path in country_paths:
                prop_path = self._calculate_impact(event, path)
                if prop_path:
                    paths.append(prop_path)
        else:
            # 모든 국가로의 경로
            for target in self.graph.nodes():
                if target == event.country:
                    continue
                
                country_paths = self._find_paths(
                    event.country, target, max_hops
                )
                for path in country_paths:
                    prop_path = self._calculate_impact(event, path)
                    if prop_path:
                        paths.append(prop_path)
        
        # 영향도 순으로 정렬
        paths.sort(key=lambda x: x.total_impact, reverse=True)
        
        logger.info(
            f"Propagation analysis: {event.country} event → "
            f"{len(paths)} impact paths found"
        )
        
        return paths
    
    def _find_paths(
        self,
        source: str,
        target: str,
        max_hops: int
    ) -> List[List[str]]:
        """두 국가 간 모든 경로 찾기"""
        try:
            # NetworkX로 모든 단순 경로 찾기
            paths = list(nx.all_simple_paths(
                self.graph,
                source=source,
                target=target,
                cutoff=max_hops
            ))
            return paths
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            logger.warning(f"Country not in graph: {source} or {target}")
            return []
    
    def _calculate_impact(
        self,
        event: EconomicEvent,
        path: List[str]
    ) -> Optional[PropagationPath]:
        """경로별 영향도 계산"""
        if len(path) < 2:
            return None
        
        # 초기 영향도 = 이벤트 magnitude
        current_impact = event.magnitude
        total_delay = 0
        impact_chain = []
        
        # 경로를 따라 영향 전파
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]
            
            # 연결 정보 가져오기
            edge_data = self.graph.get_edge_data(source, target)
            if not edge_data:
                return None
            
            # 영향 감쇠 계산
            strength = edge_data.get("strength", 0.5)
            current_impact *= strength
            
            # 시간 지연 누적
            delay = edge_data.get("delay_hours", 24)
            total_delay += delay
            
            # 경로 기록
            impact_chain.append((source, target, current_impact))
        
        # 최종 영향도가 너무 작으면 무시
        if current_impact < 0.1:
            return None
        
        # 신뢰도 계산 (경로가 길수록 신뢰도 감소)
        confidence = 0.9 ** (len(path) - 1)
        
        return PropagationPath(
            source_event=event,
            path=impact_chain,
            total_impact=current_impact,
            time_delay_hours=total_delay,
            confidence=confidence
        )
    
    def get_direct_impact_countries(
        self,
        country: str,
        min_strength: float = 0.5
    ) -> List[Tuple[str, float]]:
        """특정 국가와 직접 연결된 국가 목록"""
        direct_impacts = []
        
        for neighbor in self.graph.successors(country):
            edge_data = self.graph.get_edge_data(country, neighbor)
            strength = edge_data.get("strength", 0.0)
            
            if strength >= min_strength:
                direct_impacts.append((neighbor, strength))
        
        # 강도 순 정렬
        direct_impacts.sort(key=lambda x: x[1], reverse=True)
        return direct_impacts
    
    def find_amplification_loops(
        self,
        event: EconomicEvent,
        max_loop_size: int = 4
    ) -> List[List[str]]:
        """
        증폭 루프 찾기
        
        예: 일본 → 미국 → 유럽 → 일본 (feedback loop)
        """
        loops = []
        
        try:
            # 사이클 찾기
            cycles = nx.simple_cycles(self.graph)
            
            for cycle in cycles:
                if event.country in cycle and len(cycle) <= max_loop_size:
                    loops.append(cycle)
                    
        except Exception as e:
            logger.error(f"Failed to find loops: {e}")
        
        return loops
    
    def visualize_impact(
        self,
        event: EconomicEvent,
        paths: List[PropagationPath]
    ) -> str:
        """
        영향 전파 시각화 (텍스트)
        
        Returns:
            시각화 문자열
        """
        viz = f"\n{'='*60}\n"
        viz += f"Event: {event.description}\n"
        viz += f"Source: {event.country}\n"
        viz += f"Magnitude: {event.magnitude:.1%}\n"
        viz += f"{'='*60}\n\n"
        
        viz += "Impact Propagation Paths:\n\n"
        
        for i, path in enumerate(paths[:5], 1):  # Top 5
            viz += f"{i}. "
            
            # 경로 표시
            for j, (source, target, impact) in enumerate(path.path):
                if j > 0:
                    viz += " → "
                viz += f"{target} ({impact:.1%})"
            
            viz += f"\n   Total Impact: {path.total_impact:.1%}"
            viz += f" | Delay: {path.time_delay_hours}h"
            viz += f" | Confidence: {path.confidence:.0%}\n\n"
        
        return viz


# 전역 인스턴스
_event_graph = None


def get_event_graph() -> GlobalEventGraph:
    """전역 GlobalEventGraph 인스턴스 반환"""
    global _event_graph
    if _event_graph is None:
        _event_graph = GlobalEventGraph()
    return _event_graph


# 테스트
if __name__ == "__main__":
    print("=== Global Event Graph Test ===\n")
    
    graph = GlobalEventGraph()
    
    # 시나리오 1: 일본 금리 인상
    print("Scenario 1: Japan Interest Rate Hike\n")
    event = EconomicEvent(
        id="jp_rate_hike_2025",
        country="Japan",
        type=EventType.INTEREST_RATE,
        description="BOJ raises rate from 0% to 0.5%",
        magnitude=0.7,
        timestamp=datetime.now()
    )
    
    # 한국으로의 영향 분석
    paths = graph.analyze_propagation(event, target_country="Korea")
    
    # 시각화
    print(graph.visualize_impact(event, paths))
    
    # 직접 영향 국가
    print("Direct Impact Countries:")
    direct = graph.get_direct_impact_countries("Japan")
    for country, strength in direct:
        print(f"  - {country}: {strength:.0%}")
    
    print("\n✅ Global Event Graph test completed!")
