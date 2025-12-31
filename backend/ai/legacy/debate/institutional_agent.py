"""
InstitutionalAgent - 기관 투자자 전담 AI

스마트 머니 흐름을 분석하여 기관 투자자 관점의
매매 의견을 제공하는 AI Agent

핵심 역할:
1. Smart Money Signal 분석
2. 기관 매수 압력 평가
3. 내부자 거래 해석
4. 기관 전략 추론

작성일: 2025-12-15
Phase: E Week 4
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from backend.schemas.base_schema import (
    InvestmentSignal,
    SignalAction
)
from backend.data.collectors.smart_money_collector import (
    get_smart_money_collector,
    SignalStrength as SmartMoneyStrength
)

logger = logging.getLogger(__name__)


class InstitutionalAgent:
    """
    기관 투자자 전담 AI Agent
    
    Smart Money Collector의 데이터를 기반으로
    기관 투자자 관점의 투자 의견을 제공합니다.
    
    핵심 논리:
    - 기관 매수 압력 70% 이상 → STRONG_BUY
    - 주요 기관 대량 매수 → BUY 가중치 증가
    - CEO/CFO 매수 → 추가 신뢰도
    - 기관 이탈 감지 → SELL 경고
    
    Usage:
        agent = InstitutionalAgent()
        
        signal = await agent.analyze("AAPL", context)
        print(f"Action: {signal.action.value}")
        print(f"Confidence: {signal.confidence}")
    """
    
    def __init__(self, weight: float = 1.0):
        """
        Args:
            weight: Agent 가중치 (AIDebateEngine에서 사용)
        """
        self.weight = weight
        self.vote_weight = 0.10  # 10% voting weight (War Room)
        self.collector = get_smart_money_collector()
        logger.info(f"InstitutionalAgent initialized (weight={weight}, vote_weight={self.vote_weight})")
    
    async def analyze(
        self,
        ticker: str,
        context: Optional[Dict] = None
    ) -> InvestmentSignal:
        """
        기관 투자자 관점 분석
        
        Args:
            ticker: 종목 코드
            context: 추가 컨텍스트 (선택)
            
        Returns:
            InvestmentSignal
        """
        logger.info(f"InstitutionalAgent analyzing {ticker}")
        
        # 1. Smart Money Signal 가져오기
        smart_money = await self.collector.analyze_smart_money(ticker)
        
        # 2. 신호 강도 → 투자 액션 변환
        action = self._map_signal_to_action(smart_money.signal_strength)
        
        # 3. 신뢰도 계산
        confidence = self._calculate_confidence(smart_money)
        
        # 4. 이유 생성
        reasoning = self._generate_reasoning(smart_money)
        
        # 5. 목표가 추정 (기관 관점)
        target_price = self._estimate_target_price(
            smart_money.institution_buying_pressure
        )
        
        # 6. 리스크 평가
        risk_factors = self._assess_risks(smart_money)
        
        signal = InvestmentSignal(
            ticker=ticker,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            target_price=target_price,
            risk_factors=risk_factors,
            generated_at=datetime.now(),
            model="InstitutionalAgent"
        )
        
        logger.info(
            f"InstitutionalAgent signal: {action.value} "
            f"(confidence={confidence:.0%})"
        )
        
        # 🆕 War Room compatibility: Return dict instead of InvestmentSignal
        return {
            "agent": "institutional",
            "action": action.value,  # Convert enum to string
            "confidence": confidence,
            "reasoning": reasoning,
            "institutional_factors": {
                "buying_pressure": f"{smart_money.institution_buying_pressure*100:.0f}%",
                "insider_score": smart_money.insider_activity_score,
                "signal_strength": smart_money.signal_strength.value,
                "key_institutions": smart_money.key_institutions[:3] if smart_money.key_institutions else [],
                "key_insiders": smart_money.key_insiders[:2] if smart_money.key_insiders else []
            }
        }
    
    def _map_signal_to_action(
        self,
        signal_strength: SmartMoneyStrength
    ) -> SignalAction:
        """
        Smart Money Signal → Investment Action
        
        Args:
            signal_strength: 스마트 머니 신호 강도
            
        Returns:
            SignalAction
        """
        mapping = {
            SmartMoneyStrength.VERY_BULLISH: SignalAction.BUY,  # Use BUY instead of STRONG_BUY
            SmartMoneyStrength.BULLISH: SignalAction.BUY,
            SmartMoneyStrength.NEUTRAL: SignalAction.HOLD,
            SmartMoneyStrength.BEARISH: SignalAction.SELL,
            SmartMoneyStrength.VERY_BEARISH: SignalAction.SELL  # Use SELL instead of STRONG_SELL
        }
        
        return mapping.get(signal_strength, SignalAction.HOLD)
    
    def _calculate_confidence(self, smart_money) -> float:
        """
        신뢰도 계산
        
        기관 압력이 명확하고, 주요 기관이 참여할수록 높음
        
        Args:
            smart_money: SmartMoneySignal
            
        Returns:
            신뢰도 (0.0 ~ 1.0)
        """
        base_confidence = smart_money.confidence
        
        # 1. 기관 압력이 극단적일수록 신뢰도 증가
        pressure = smart_money.institution_buying_pressure
        if pressure > 0.8 or pressure < 0.2:
            base_confidence += 0.1
        
        # 2. 주요 기관(Berkshire, Vanguard 등) 참여 시 신뢰도 증가
        if len(smart_money.key_institutions) > 0:
            base_confidence += 0.05 * len(smart_money.key_institutions)
        
        # 3. CEO/CFO 거래 시 신뢰도 증가
        if len(smart_money.key_insiders) > 0:
            base_confidence += 0.05 * len(smart_money.key_insiders)
        
        return min(base_confidence, 1.0)
    
    def _generate_reasoning(self, smart_money) -> str:
        """
        판단 근거 생성
        
        Args:
            smart_money: SmartMoneySignal
            
        Returns:
            판단 근거 문자열
        """
        pressure = smart_money.institution_buying_pressure
        insider_score = smart_money.insider_activity_score
        
        reasons = []
        
        # 기관 압력
        if pressure > 0.7:
            reasons.append(f"🏦 기관 매수 압력 강함 ({pressure:.0%})")
        elif pressure < 0.3:
            reasons.append(f"📉 기관 이탈 감지 ({pressure:.0%})")
        
        # 주요 기관
        if smart_money.key_institutions:
            inst_list = ", ".join(smart_money.key_institutions[:2])
            reasons.append(f"🎯 주요 기관 참여: {inst_list}")
        
        # 내부자 거래
        if insider_score > 0.5:
            reasons.append(f"👔 내부자 대량 매수 감지")
        elif insider_score < -0.5:
            reasons.append(f"⚠️ 내부자 매도 증가")
        
        # CEO/CFO
        if smart_money.key_insiders:
            insider_list = ", ".join(smart_money.key_insiders[:2])
            reasons.append(f"💼 경영진 거래: {insider_list}")
        
        if not reasons:
            reasons.append("📊 스마트 머니 중립")
        
        return " | ".join(reasons)
    
    def _estimate_target_price(
        self,
        institution_pressure: float
    ) -> Optional[float]:
        """
        목표가 추정 (간단함)
        
        기관 압력이 높을수록 상향 목표가
        
        Args:
            institution_pressure: 기관 매수 압력 (0.0 ~ 1.0)
            
        Returns:
            목표가 (현재가 대비 %) 또는 None
        """
        # 압력에 따른 목표 수익률
        if institution_pressure > 0.8:
            return 15.0  # +15%
        elif institution_pressure > 0.6:
            return 8.0   # +8%
        elif institution_pressure < 0.2:
            return -10.0  # -10%
        elif institution_pressure < 0.4:
            return -5.0   # -5%
        else:
            return None  # 중립
    
    def _assess_risks(self, smart_money) -> list:
        """
        리스크 평가
        
        Args:
            smart_money: SmartMoneySignal
            
        Returns:
            리스크 요인 리스트
        """
        risks = []
        
        # 1. 신뢰도 낮음
        if smart_money.confidence < 0.5:
            risks.append("데이터 부족 - 신뢰도 낮음")
        
        # 2. 기관과 내부자 의견 불일치
        pressure = smart_money.institution_buying_pressure
        insider = smart_money.insider_activity_score
        
        if (pressure > 0.6 and insider < -0.3) or (pressure < 0.4 and insider > 0.3):
            risks.append("기관과 내부자 의견 불일치")
        
        # 3. 극단적 포지션
        if pressure > 0.9 or pressure < 0.1:
            risks.append("극단적 포지션 - 반전 위험")
        
        return risks


# 전역 인스턴스 (싱글톤)
_institutional_agent = None


def get_institutional_agent(weight: float = 1.0) -> InstitutionalAgent:
    """
    전역 InstitutionalAgent 인스턴스 반환
    
    Args:
        weight: Agent 가중치
        
    Returns:
        InstitutionalAgent
    """
    global _institutional_agent
    if _institutional_agent is None:
        _institutional_agent = InstitutionalAgent(weight=weight)
    return _institutional_agent


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== InstitutionalAgent Test ===\n")
        
        agent = InstitutionalAgent(weight=1.2)
        
        # 분석
        signal = await agent.analyze("AAPL")
        
        print(f"Ticker: {signal.ticker}")
        print(f"Action: {signal.action.value}")
        print(f"Confidence: {signal.confidence:.0%}")
        print(f"Target Price: {signal.target_price}%")
        print(f"\nReasoning:\n{signal.reasoning}")
        
        if signal.risk_factors:
            print(f"\nRisks:")
            for risk in signal.risk_factors:
                print(f"  - {risk}")
        
        print("\n✅ InstitutionalAgent test completed!")
    
    asyncio.run(test())
