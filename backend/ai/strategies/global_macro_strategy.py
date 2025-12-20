"""
Global Macro Strategy - 글로벌 매크로 전략 엔진

Phase F2: 글로벌 매크로 확장

글로벌 이벤트를 감지하고 나비효과를 추론하여 매매 시그널 생성

주요 기능:
- 매크로 이벤트 감지
- GlobalMarketMap 기반 영향 전파 분석
- 섹터/종목별 시그널 생성
- 리스크 조정된 포지션 사이징

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from backend.ai.macro.global_market_map import (
    GlobalMarketMap, get_global_market_map,
    MarketNode, AssetType, ImpactPath
)
from backend.ai.macro.country_risk_engine import (
    CountryRiskEngine, get_country_risk_engine,
    Country, RiskLevel
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 이벤트 및 시그널 스키마
# ═══════════════════════════════════════════════════════════════

class EventType(str, Enum):
    """매크로 이벤트 유형"""
    RATE_DECISION = "rate_decision"
    INFLATION_DATA = "inflation_data"
    GDP_RELEASE = "gdp_release"
    CURRENCY_MOVE = "currency_move"
    GEOPOLITICAL = "geopolitical"
    COMMODITY_SHOCK = "commodity_shock"
    CENTRAL_BANK = "central_bank"
    TRADE_POLICY = "trade_policy"


class SignalType(str, Enum):
    """시그널 유형"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    INCREASE = "INCREASE"


@dataclass
class MacroEvent:
    """매크로 이벤트"""
    id: str
    event_type: EventType
    source_node: str  # GlobalMarketMap 노드 ID
    shock_magnitude: float  # -1.0 ~ 1.0
    description: str
    country: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "source_node": self.source_node,
            "shock_magnitude": self.shock_magnitude,
            "description": self.description,
            "country": self.country,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class MacroSignal:
    """매크로 기반 시그널"""
    target: str  # 섹터, 지수, 또는 티커
    signal_type: SignalType
    strength: float  # 0.0 ~ 1.0
    reason: str
    impact_path: List[str]  # 영향 경로
    confidence: float
    country_risk_adjusted: bool = False
    position_size_pct: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "signal_type": self.signal_type.value,
            "strength": self.strength,
            "reason": self.reason,
            "impact_path": self.impact_path,
            "confidence": self.confidence,
            "country_risk_adjusted": self.country_risk_adjusted,
            "position_size_pct": self.position_size_pct
        }


@dataclass
class MacroAnalysisResult:
    """매크로 분석 결과"""
    event: MacroEvent
    signals: List[MacroSignal]
    affected_countries: List[str]
    risk_summary: Dict[str, Any]
    execution_priority: int  # 1 (highest) ~ 5 (lowest)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event.to_dict(),
            "signals": [s.to_dict() for s in self.signals],
            "affected_countries": self.affected_countries,
            "risk_summary": self.risk_summary,
            "execution_priority": self.execution_priority,
            "timestamp": self.timestamp.isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# Global Macro Strategy 클래스
# ═══════════════════════════════════════════════════════════════

class GlobalMacroStrategy:
    """
    글로벌 매크로 전략 엔진
    
    Usage:
        strategy = GlobalMacroStrategy()
        
        # 이벤트 분석
        event = MacroEvent(
            id="evt_001",
            event_type=EventType.RATE_DECISION,
            source_node="BOJ_RATE",
            shock_magnitude=0.3,
            description="BOJ raises rates by 25bps"
        )
        
        result = strategy.analyze_event(event)
        
        for signal in result.signals:
            print(f"{signal.target}: {signal.signal_type.value}")
    """
    
    # 시그널 임계값
    BUY_THRESHOLD = 0.15
    SELL_THRESHOLD = -0.15
    STRONG_THRESHOLD = 0.25
    
    # 섹터 -> 대표 ETF/종목 매핑
    SECTOR_TICKERS = {
        "SEMICONDUCTOR": ["NVDA", "AMD", "INTC", "TSM", "SMH"],
        "AI_CHIPS": ["NVDA", "AMD", "GOOGL", "MSFT"],
        "HBM_DEMAND": ["SK", "TSM", "MU"],
        "ENERGY_SECTOR": ["XOM", "CVX", "XLE"],
        "AIRLINE_SECTOR": ["DAL", "UAL", "AAL", "JETS"],
        "TECH_SECTOR": ["AAPL", "MSFT", "GOOGL", "QQQ"],
        "FINANCE_SECTOR": ["JPM", "BAC", "XLF"],
        "KOSPI": ["EWY", "KOSPI"],
        "NIKKEI": ["EWJ", "NKY"],
        "CSI300": ["FXI", "MCHI"],
        "NDX": ["QQQ", "TQQQ"],
        "SPX": ["SPY", "VOO"]
    }
    
    def __init__(
        self,
        market_map: Optional[GlobalMarketMap] = None,
        risk_engine: Optional[CountryRiskEngine] = None
    ):
        """초기화"""
        self.market_map = market_map or get_global_market_map()
        self.risk_engine = risk_engine or get_country_risk_engine()
        
        self._event_history: List[MacroEvent] = []
        self._signal_history: List[MacroSignal] = []
        
        logger.info("GlobalMacroStrategy initialized")
    
    def analyze_event(
        self,
        event: MacroEvent,
        apply_country_risk: bool = True
    ) -> MacroAnalysisResult:
        """
        매크로 이벤트 분석 및 시그널 생성
        
        Args:
            event: 매크로 이벤트
            apply_country_risk: 국가 리스크 조정 적용 여부
            
        Returns:
            MacroAnalysisResult
        """
        logger.info(f"Analyzing event: {event.description}")
        
        # 1. 이벤트 영향 전파 시뮬레이션
        simulation = self.market_map.simulate_event(
            event_source=event.source_node,
            shock=event.shock_magnitude,
            description=event.description
        )
        
        # 2. 시그널 생성
        signals = self._generate_signals(
            simulation["detailed_paths"],
            event.confidence
        )
        
        # 3. 영향받는 국가 파악
        affected_countries = self._identify_affected_countries(
            simulation["top_impacts"]
        )
        
        # 4. 국가 리스크 조정
        if apply_country_risk:
            signals = self._adjust_for_country_risk(signals, affected_countries)
        
        # 5. 포지션 사이징
        signals = self._calculate_position_sizes(signals, event)
        
        # 6. 리스크 요약
        risk_summary = self._generate_risk_summary(affected_countries)
        
        # 7. 실행 우선순위 결정
        priority = self._determine_priority(event, signals)
        
        # 히스토리 저장
        self._event_history.append(event)
        self._signal_history.extend(signals)
        
        return MacroAnalysisResult(
            event=event,
            signals=signals,
            affected_countries=affected_countries,
            risk_summary=risk_summary,
            execution_priority=priority
        )
    
    def _generate_signals(
        self,
        impact_paths: List[Dict],
        event_confidence: float
    ) -> List[MacroSignal]:
        """영향 경로에서 시그널 생성"""
        signals = []
        seen_targets = set()
        
        for path_data in impact_paths:
            path = path_data.get("path", [])
            impact = path_data.get("total_impact", 0)
            reasons = path_data.get("reasons", [])
            confidence = path_data.get("confidence", 0.8) * event_confidence
            
            if len(path) < 2:
                continue
            
            target = path[-1]
            if target in seen_targets:
                continue
            seen_targets.add(target)
            
            # 시그널 유형 결정
            if impact > self.STRONG_THRESHOLD:
                signal_type = SignalType.BUY
                strength = min(1.0, impact / 0.5)
            elif impact > self.BUY_THRESHOLD:
                signal_type = SignalType.INCREASE
                strength = impact / self.STRONG_THRESHOLD
            elif impact < -self.STRONG_THRESHOLD:
                signal_type = SignalType.SELL
                strength = min(1.0, abs(impact) / 0.5)
            elif impact < self.SELL_THRESHOLD:
                signal_type = SignalType.REDUCE
                strength = abs(impact) / abs(self.STRONG_THRESHOLD)
            else:
                signal_type = SignalType.HOLD
                strength = 0.0
            
            if signal_type == SignalType.HOLD:
                continue  # HOLD 시그널은 스킵
            
            signals.append(MacroSignal(
                target=target,
                signal_type=signal_type,
                strength=strength,
                reason=" -> ".join(reasons[-3:]),  # 마지막 3개 이유
                impact_path=path,
                confidence=confidence
            ))
        
        # 강도순 정렬
        signals.sort(key=lambda x: x.strength, reverse=True)
        
        return signals[:10]  # 상위 10개
    
    def _identify_affected_countries(
        self,
        top_impacts: List[Dict]
    ) -> List[str]:
        """영향받는 국가 파악"""
        countries = set()
        
        for item in top_impacts:
            node_id = item.get("node", "")
            node = self.market_map.get_node(node_id)
            if node and node.country:
                countries.add(node.country)
        
        return list(countries)
    
    def _adjust_for_country_risk(
        self,
        signals: List[MacroSignal],
        affected_countries: List[str]
    ) -> List[MacroSignal]:
        """국가 리스크에 따른 시그널 조정"""
        adjusted_signals = []
        
        for signal in signals:
            node = self.market_map.get_node(signal.target)
            if not node or not node.country:
                adjusted_signals.append(signal)
                continue
            
            try:
                country = Country(node.country)
                risk_score = self.risk_engine.calculate_risk_score(country)
                
                # 고위험 국가 BUY 시그널 약화
                if risk_score.risk_level in [RiskLevel.ELEVATED, RiskLevel.HIGH]:
                    if signal.signal_type in [SignalType.BUY, SignalType.INCREASE]:
                        signal.strength *= 0.7
                        signal.reason += f" (risk-adjusted: {node.country})"
                
                # 저위험 국가 시그널 강화
                elif risk_score.risk_level == RiskLevel.LOW:
                    if signal.signal_type in [SignalType.BUY, SignalType.INCREASE]:
                        signal.strength = min(1.0, signal.strength * 1.1)
                
                signal.country_risk_adjusted = True
                
            except ValueError:
                pass
            
            adjusted_signals.append(signal)
        
        return adjusted_signals
    
    def _calculate_position_sizes(
        self,
        signals: List[MacroSignal],
        event: MacroEvent
    ) -> List[MacroSignal]:
        """포지션 사이즈 계산"""
        # 기본 포지션 사이즈 (포트폴리오의 %)
        BASE_POSITION = 5.0  # 5%
        MAX_POSITION = 15.0  # 최대 15%
        
        for signal in signals:
            # 강도와 신뢰도 기반 사이즈
            size = BASE_POSITION * signal.strength * signal.confidence
            
            # 이벤트 충격 크기 반영
            size *= (1 + abs(event.shock_magnitude))
            
            # 리스크 조정된 경우 보수적
            if signal.country_risk_adjusted:
                size *= 0.8
            
            signal.position_size_pct = min(MAX_POSITION, max(1.0, size))
        
        return signals
    
    def _generate_risk_summary(
        self,
        affected_countries: List[str]
    ) -> Dict[str, Any]:
        """리스크 요약 생성"""
        country_scores = {}
        
        for country_code in affected_countries:
            try:
                country = Country(country_code)
                score = self.risk_engine.get_risk_score(country)
                if score:
                    country_scores[country_code] = {
                        "score": score.composite_score,
                        "level": score.risk_level.value,
                        "factors": score.factors[:2]
                    }
            except ValueError:
                pass
        
        avg_risk = (
            sum(c["score"] for c in country_scores.values()) / len(country_scores)
            if country_scores else 50.0
        )
        
        return {
            "country_risks": country_scores,
            "average_risk": avg_risk,
            "high_risk_countries": [
                c for c, data in country_scores.items()
                if data["level"] in ["elevated", "high"]
            ]
        }
    
    def _determine_priority(
        self,
        event: MacroEvent,
        signals: List[MacroSignal]
    ) -> int:
        """실행 우선순위 결정 (1=최고, 5=최저)"""
        # 충격 크기
        shock_factor = abs(event.shock_magnitude)
        
        # 시그널 강도
        avg_strength = (
            sum(s.strength for s in signals) / len(signals)
            if signals else 0
        )
        
        # 신뢰도
        confidence = event.confidence
        
        # 종합 점수
        score = shock_factor * 0.4 + avg_strength * 0.4 + confidence * 0.2
        
        if score > 0.7:
            return 1
        elif score > 0.5:
            return 2
        elif score > 0.3:
            return 3
        elif score > 0.15:
            return 4
        else:
            return 5
    
    def get_tradeable_tickers(
        self,
        signals: List[MacroSignal]
    ) -> List[Dict[str, Any]]:
        """시그널을 구체적인 티커로 변환"""
        result = []
        
        for signal in signals:
            tickers = self.SECTOR_TICKERS.get(signal.target, [signal.target])
            
            for ticker in tickers[:3]:  # 섹터당 상위 3개
                result.append({
                    "ticker": ticker,
                    "signal": signal.signal_type.value,
                    "strength": signal.strength,
                    "reason": signal.reason,
                    "position_size_pct": signal.position_size_pct,
                    "from_sector": signal.target
                })
        
        return result
    
    def get_event_history(self, limit: int = 10) -> List[MacroEvent]:
        """이벤트 히스토리 조회"""
        return self._event_history[-limit:]
    
    def get_signal_history(self, limit: int = 20) -> List[MacroSignal]:
        """시그널 히스토리 조회"""
        return self._signal_history[-limit:]


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_global_macro_strategy: Optional[GlobalMacroStrategy] = None


def get_global_macro_strategy() -> GlobalMacroStrategy:
    """GlobalMacroStrategy 싱글톤 인스턴스"""
    global _global_macro_strategy
    if _global_macro_strategy is None:
        _global_macro_strategy = GlobalMacroStrategy()
    return _global_macro_strategy


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    strategy = GlobalMacroStrategy()
    
    print("=== Global Macro Strategy Test ===\n")
    
    # 시나리오: BOJ 금리 인상 -> 엔화 강세
    event = MacroEvent(
        id="evt_boj_001",
        event_type=EventType.RATE_DECISION,
        source_node="JPY_STRENGTH",
        shock_magnitude=-0.4,  # 엔화 40% 강세 충격
        description="BOJ unexpectedly raises rates by 25bps",
        country="JP",
        confidence=0.85
    )
    
    result = strategy.analyze_event(event)
    
    print(f"Event: {event.description}")
    print(f"Shock: {event.shock_magnitude:.1%}")
    print(f"Execution Priority: {result.execution_priority}/5")
    print(f"\nAffected Countries: {result.affected_countries}")
    
    print("\n" + "="*60)
    print("Generated Signals:")
    print("="*60)
    
    for signal in result.signals:
        emoji = "📈" if signal.signal_type in [SignalType.BUY, SignalType.INCREASE] else "📉"
        print(f"{emoji} {signal.target}: {signal.signal_type.value}")
        print(f"   Strength: {signal.strength:.1%}, Size: {signal.position_size_pct:.1f}%")
        print(f"   Path: {' -> '.join(signal.impact_path)}")
        print(f"   Reason: {signal.reason}")
    
    print("\n" + "="*60)
    print("Tradeable Tickers:")
    print("="*60)
    
    tickers = strategy.get_tradeable_tickers(result.signals[:5])
    for t in tickers[:10]:
        signal_emoji = "🟢" if t["signal"] in ["BUY", "INCREASE"] else "🔴"
        print(f"{signal_emoji} {t['ticker']}: {t['signal']} ({t['position_size_pct']:.1f}%)")
