"""
Macro Analyzer Agent - 거시경제 전담 AI

개별 종목이 아닌 시장 전체의 "날씨"를 판단하는 AI

핵심 역할:
1. 거시경제 지표 종합 분석 (금리, VIX, 달러)
2. Market Regime 판단 (Risk On/Off)
3. 주식 비중 동적 조정 (0% ~ 100%)
4. 다른 Agent들에게 지시

작성일: 2025-12-15
Phase: E Week 5-6
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """시장 체제"""
    RISK_ON = "risk_on"          # 주식 강세 국면
    RISK_OFF = "risk_off"        # 방어 국면
    TRANSITION = "transition"     # 전환기
    NEUTRAL = "neutral"          # 중립


class RegimeStrength(Enum):
    """체제 강도"""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


@dataclass
class MacroIndicators:
    """거시경제 지표"""
    treasury_10y: float  # 10년물 국채 금리
    treasury_2y: float   # 2년물 국채 금리
    yield_curve: float   # 수익률 곡선 (10Y - 2Y)
    vix: float           # 변동성 지수
    dxy: float           # 달러 지수
    sp500: float         # S&P 500
    gold: float          # 금 가격
    oil: float           # 원유 가격
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RegimeAnalysis:
    """시장 체제 분석"""
    regime: MarketRegime
    strength: RegimeStrength
    stock_allocation: float  # 주식 권장 비중 (0.0 ~ 1.0)
    confidence: float
    key_signals: List[str]
    warnings: List[str]
    analysis: str
    timestamp: datetime = field(default_factory=datetime.now)


class MacroAnalyzerAgent:
    """
    거시경제 전담 AI Agent
    
    시장 전체의 거시경제 상황을 분석하여
    Risk On/Off를 판단하고 포지션 조정을 권고합니다.
    
    핵심 논리:
    - VIX < 15 + 금리 안정 → Risk On (주식 100%)
    - VIX > 30 + 수익률 역전 → Risk Off (현금 50%+)
    - 변동성 급증 → 포지션 축소
    
    Usage:
        agent = MacroAnalyzerAgent()
        
        analysis = await agent.analyze_market_regime()
        print(f"Regime: {analysis.regime.value}")
        print(f"Stock Allocation: {analysis.stock_allocation:.0%}")
    """
    
    # Risk 임계값
    RISK_ON_THRESHOLDS = {
        "vix_max": 20.0,
        "yield_curve_min": 0.0,  # 정상 (양의 기울기)
    }
    
    RISK_OFF_THRESHOLDS = {
        "vix_min": 25.0,
        "yield_curve_max": -0.5,  # 역전
    }
    
    def __init__(self, weight: float = 1.5):
        """
        Args:
            weight: Agent 가중치 (거시경제는 매우 중요 → 1.5)
        """
        self.weight = weight
        logger.info(f"MacroAnalyzerAgent initialized (weight={weight})")
    
    async def get_macro_indicators(self) -> MacroIndicators:
        """
        거시경제 지표 수집 (FRED API 연동)
        
        Returns:
            MacroIndicators
        """
        from backend.data.collectors.api_clients.fred_client import get_fred_client
        
        logger.info("Fetching macro indicators (real data)")
        
        try:
            # FRED Client 사용
            client = get_fred_client()
            
            # 전체 지표 가져오기
            data = client.get_all_macro_indicators()
            
            indicators = MacroIndicators(
                treasury_10y=data['treasury_10y'],
                treasury_2y=data['treasury_2y'],
                yield_curve=data['yield_curve'],
                vix=data['vix'],
                dxy=data['dxy'],
                sp500=data['sp500'],
                gold=data['gold'],
                oil=data['oil']
            )
            
            logger.info(
                f"Real indicators: VIX={indicators.vix}, "
                f"Yield Curve={indicators.yield_curve:+.2f}%"
            )
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to fetch real data, using fallback: {e}")
            return self._get_fallback_indicators()
    
    def _get_fallback_indicators(self) -> MacroIndicators:
        """폴백 샘플 데이터"""
        logger.warning("Using fallback sample indicators")
        
        return MacroIndicators(
            treasury_10y=4.25,
            treasury_2y=4.50,
            yield_curve=-0.25,
            vix=18.5,
            dxy=104.2,
            sp500=4500.0,
            gold=2050.0,
            oil=75.0
        )
    
    def analyze_yield_curve(self, indicators: MacroIndicators) -> tuple[str, float]:
        """
        수익률 곡선 분석
        
        Args:
            indicators: 거시경제 지표
            
        Returns:
            (신호, 가중치)
        """
        curve = indicators.yield_curve
        
        if curve < -0.5:
            # 깊은 역전 → 경기침체 신호
            return "🚨 수익률 곡선 깊은 역전 (경기침체 우려)", -0.8
        elif curve < 0:
            # 역전 → 경고
            return "⚠️ 수익률 곡선 역전", -0.4
        elif curve > 1.0:
            # 가파른 정상 곡선 → 경기 확장
            return "✅ 가파른 정상 곡선 (경기 확장)", 0.6
        else:
            # 정상 범위
            return "📊 정상 수익률 곡선", 0.2
    
    def analyze_vix(self, indicators: MacroIndicators) -> tuple[str, float]:
        """
        VIX 분석
        
        Args:
            indicators: 거시경제 지표
            
        Returns:
            (신호, 가중치)
        """
        vix = indicators.vix
        
        if vix < 12:
            # 극단적 안정 → 역설적으로 위험 (complacency)
            return "⚠️ VIX 극단적 저점 (안일함 경고)", 0.0
        elif vix < 15:
            # 매우 안정 → Risk On
            return "✅ VIX 저점 (안정)", 0.8
        elif vix < 20:
            # 정상 범위
            return "📊 VIX 정상 범위", 0.4
        elif vix < 30:
            # 변동성 증가 → 주의
            return "⚠️ VIX 상승 (변동성 증가)", -0.3
        else:
            # 공포 → Risk Off
            return "🚨 VIX 고점 (시장 공포)", -0.8
    
    def analyze_dollar(self, indicators: MacroIndicators) -> tuple[str, float]:
        """
        달러 지수 분석
        
        Args:
            indicators: 거시경제 지표
            
        Returns:
            (신호, 가중치)
        """
        dxy = indicators.dxy
        
        if dxy > 110:
            # 극단적 달러 강세 → 위험 자산 부담
            return "🚨 달러 극단 강세 (위험 자산 압박)", -0.5
        elif dxy > 105:
            # 달러 강세
            return "⚠️ 달러 강세", -0.2
        elif dxy < 95:
            # 달러 약세 → 위험 자산 유리
            return "✅ 달러 약세 (위험 자산 우호)", 0.4
        else:
            # 정상
            return "📊 달러 정상 범위", 0.0
    
    async def analyze_market_regime(self) -> RegimeAnalysis:
        """
        시장 체제 종합 분석
        
        Returns:
            RegimeAnalysis
        """
        logger.info("Analyzing market regime")
        
        # 1. 지표 수집
        indicators = await self.get_macro_indicators()
        
        # 2. 개별 분석
        yield_signal, yield_weight = self.analyze_yield_curve(indicators)
        vix_signal, vix_weight = self.analyze_vix(indicators)
        dollar_signal, dollar_weight = self.analyze_dollar(indicators)
        
        key_signals = [yield_signal, vix_signal, dollar_signal]
        
        # 3. 종합 점수 계산 (-1.0 ~ 1.0)
        total_score = (
            yield_weight * 0.4 +  # 수익률 곡선 40% 가중
            vix_weight * 0.4 +    # VIX 40% 가중
            dollar_weight * 0.2   # 달러 20% 가중
        )
        
        # 4. Regime 판정
        if total_score > 0.5:
            regime = MarketRegime.RISK_ON
            strength = RegimeStrength.STRONG
        elif total_score > 0.2:
            regime = MarketRegime.RISK_ON
            strength = RegimeStrength.MODERATE
        elif total_score < -0.5:
            regime = MarketRegime.RISK_OFF
            strength = RegimeStrength.STRONG
        elif total_score < -0.2:
            regime = MarketRegime.RISK_OFF
            strength = RegimeStrength.MODERATE
        else:
            regime = MarketRegime.NEUTRAL
            strength = RegimeStrength.MODERATE
        
        # 5. 주식 비중 계산
        if regime == MarketRegime.RISK_ON:
            base_allocation = 0.9  # 90%
            if strength == RegimeStrength.STRONG:
                stock_allocation = 1.0  # 100%
            else:
                stock_allocation = base_allocation
        elif regime == MarketRegime.RISK_OFF:
            base_allocation = 0.3  # 30%
            if strength == RegimeStrength.STRONG:
                stock_allocation = 0.2  # 20% (방어)
            else:
                stock_allocation = base_allocation
        else:
            stock_allocation = 0.6  # 60% (중립)
        
        # 6. 경고 생성
        warnings = []
        
        if indicators.yield_curve < 0:
            warnings.append("수익률 곡선 역전 - 경기침체 가능성")
        
        if indicators.vix > 25:
            warnings.append("VIX 고점 - 시장 변동성 극심")
        
        if indicators.vix < 12:
            warnings.append("VIX 극저점 - 과도한 낙관 경계")
        
        # 7. AI 분석 (Claude에게 요청 가능)
        analysis = self._generate_analysis(
            regime, strength, indicators, total_score
        )
        
        # 8. 신뢰도
        confidence = 0.85  # 거시 지표는 신뢰도 높음
        
        result = RegimeAnalysis(
            regime=regime,
            strength=strength,
            stock_allocation=stock_allocation,
            confidence=confidence,
            key_signals=key_signals,
            warnings=warnings,
            analysis=analysis
        )
        
        logger.info(
            f"Regime: {regime.value} ({strength.value}), "
            f"Stock: {stock_allocation:.0%}"
        )
        
        return result
    
    def _generate_analysis(
        self,
        regime: MarketRegime,
        strength: RegimeStrength,
        indicators: MacroIndicators,
        score: float
    ) -> str:
        """
        종합 분석 텍스트 생성
        
        Args:
            regime: 시장 체제
            strength: 강도
            indicators: 지표
            score: 종합 점수
            
        Returns:
            분석 텍스트
        """
        lines = [
            f"📈 Market Regime: {regime.value.upper()} ({strength.value})",
            f"📊 Composite Score: {score:+.2f}",
            "",
            "주요 지표:",
            f"  - 10년물 금리: {indicators.treasury_10y}%",
            f"  - 수익률 곡선: {indicators.yield_curve:+.2f}%",
            f"  - VIX: {indicators.vix}",
            f"  - 달러 지수: {indicators.dxy}",
        ]
        
        return "\n".join(lines)
    
    def get_trading_directive(
        self,
        analysis: RegimeAnalysis
    ) -> Dict[str, any]:
        """
        거래 지시 생성
        
        Args:
            analysis: Regime 분석
            
        Returns:
            거래 지시 딕셔너리
        """
        directive = {
            "action": "ADJUST_ALLOCATION",
            "target_stock_allocation": analysis.stock_allocation,
            "regime": analysis.regime.value,
            "urgency": "HIGH" if analysis.strength == RegimeStrength.STRONG else "MEDIUM",
            "reason": f"{analysis.regime.value} regime detected"
        }
        
        # Risk Off 시 즉시 포지션 축소 권고
        if analysis.regime == MarketRegime.RISK_OFF:
            directive["immediate_action"] = "REDUCE_POSITION"
        
        return directive


# 전역 인스턴스
_macro_analyzer_agent = None


def get_macro_analyzer_agent(weight: float = 1.5) -> MacroAnalyzerAgent:
    """
    전역 MacroAnalyzerAgent 인스턴스 반환
    
    Args:
        weight: Agent 가중치
        
    Returns:
        MacroAnalyzerAgent
    """
    global _macro_analyzer_agent
    if _macro_analyzer_agent is None:
        _macro_analyzer_agent = MacroAnalyzerAgent(weight=weight)
    return _macro_analyzer_agent


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== Macro Analyzer Agent Test ===\n")
        
        agent = MacroAnalyzerAgent(weight=1.5)
        
        # 시장 체제 분석
        analysis = await agent.analyze_market_regime()
        
        print(f"Market Regime: {analysis.regime.value.upper()}")
        print(f"Strength: {analysis.strength.value}")
        print(f"Stock Allocation: {analysis.stock_allocation:.0%}")
        print(f"Confidence: {analysis.confidence:.0%}")
        print()
        
        print("Key Signals:")
        for signal in analysis.key_signals:
            print(f"  {signal}")
        print()
        
        if analysis.warnings:
            print("⚠️  Warnings:")
            for warning in analysis.warnings:
                print(f"  - {warning}")
            print()
        
        print("Analysis:")
        print(analysis.analysis)
        print()
        
        # 거래 지시
        directive = agent.get_trading_directive(analysis)
        print("Trading Directive:")
        for key, value in directive.items():
            print(f"  {key}: {value}")
        
        print("\n✅ Macro Analyzer Agent test completed!")
    
    asyncio.run(test())
