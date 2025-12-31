"""
Skeptic Agent - 악마의 변호인 (Devil's Advocate)

AI Council에서 강제 비관론자 역할을 수행하여 과최적화 방지

핵심 역할:
1. 다수 의견에 무조건 반대
2. 데이터의 신뢰성 의심
3. 시장이 간과한 악재 발굴
4. 최악의 시나리오 구성

작성일: 2025-12-14
Phase: B (Critical Intelligence)
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from backend.schemas.base_schema import InvestmentSignal, SignalAction

logger = logging.getLogger(__name__)


class SkepticMode(Enum):
    """회의 모드"""
    MILD = "mild"  # 온건한 비판
    MODERATE = "moderate"  # 중간 비판
    EXTREME = "extreme"  # 극단적 비판


@dataclass
class SkepticChallenge:
    """회의론자의 반박"""
    consensus_view: str
    challenges: List[str]
    worst_case_scenario: str
    hidden_risks: List[str]
    confidence: float  # 반박의 신뢰도


class SkepticAgent:
    """
    악마의 변호인 AI
    
    다른 AI들이 "매수"를 외칠 때, 강제로 반대 논리 제시
    
    Usage:
        skeptic = SkepticAgent()
        
        # 합의된 의견에 도전
        challenge = await skeptic.challenge(
            consensus_view="BUY NVDA",
            reasoning="AI boom will continue",
            confidence=0.85
        )
    """
    
    # 회의론자 페르소나
    PERSONA = """
    당신은 회의론자(Skeptic)이자 악마의 변호인(Devil's Advocate)입니다.
    
    당신의 유일한 임무는 다른 AI들의 의견에서 약점을 찾는 것입니다.
    
    다른 AI들이 "매수"를 외칠 때, 당신은 반드시:
    1. 데이터가 틀렸을 가능성을 지적
    2. 시장이 간과한 악재를 발굴
    3. 최악의 시나리오를 제시
    4. 과도한 낙관론을 경계
    
    당신은 결코 낙관적이어서는 안 됩니다.
    당신의 역할은 시스템의 과최적화를 방지하는 것입니다.
    """
    
    def __init__(
        self,
        mode: SkepticMode = SkepticMode.MODERATE,
        claude_client=None
    ):
        """
        Args:
            mode: 회의 강도
            claude_client: Claude API 클라이언트 (Extended Thinking 활용)
        """
        self.mode = mode
        
        # Claude Extended Thinking 활용
        if claude_client is None:
            from backend.ai.claude_client import get_claude_client
            self.claude = get_claude_client()
        else:
            self.claude = claude_client
        
        logger.info(f"SkepticAgent initialized: mode={mode.value}")
    
    async def challenge(
        self,
        consensus_view: str,
        reasoning: str,
        confidence: float,
        market_data: Optional[Dict] = None
    ) -> SkepticChallenge:
        """
        합의된 의견에 도전
        
        Args:
            consensus_view: 다수 의견 (예: "BUY NVDA")
            reasoning: 다수의 논거
            confidence: 다수의 신뢰도
            market_data: 시장 데이터 (선택)
            
        Returns:
            SkepticChallenge: 반박 내용
        """
        prompt = self._build_challenge_prompt(
            consensus_view, reasoning, confidence, market_data
        )
        
        try:
            # Claude Extended Thinking으로 심층 분석
            response = await self.claude.generate(
                prompt,
                model="claude-3-5-sonnet-20241022"  # Extended Thinking 지원
            )
            
            # 응답 파싱
            challenge = self._parse_response(response, consensus_view)
            
            logger.info(
                f"Skeptic challenged: {consensus_view} -> "
                f"{len(challenge.challenges)} issues found"
            )
            
            return challenge
            
        except Exception as e:
            logger.error(f"Skeptic challenge failed: {e}")
            return SkepticChallenge(
                consensus_view=consensus_view,
                challenges=["분석 실패"],
                worst_case_scenario="알 수 없음",
                hidden_risks=[],
                confidence=0.0
            )
    
    async def find_blind_spots(
        self,
        ticker: str,
        bull_thesis: str,
        market_sentiment: float  # -1 (극비관) ~ 1 (극낙관)
    ) -> Dict:
        """
        시장의 맹점(Blind Spot) 찾기
        
        Args:
            ticker: 종목 코드
            bull_thesis: 낙관론 논리
            market_sentiment: 시장 심리
            
        Returns:
            맹점 분석
        """
        prompt = f"""
        {self.PERSONA}
        
        모두가 낙관적일 때, 당신은 비관적이어야 합니다.
        
        종목: {ticker}
        낙관론: {bull_thesis}
        시장 심리: {market_sentiment:.2f} (1=극낙관)
        
        다음을 찾으세요:
        1. 시장이 간과한 리스크 3가지
        2. 데이터의 허점
        3. 과대평가 가능성
        4. 역사적 유사 사례 (거품 붕괴 등)
        
        냉정하고 객관적으로 분석하세요.
        """
        
        try:
            response = await self.claude.generate(prompt)
            
            return {
                "ticker": ticker,
                "blind_spots": response,
                "sentiment_bias": "과도한 낙관" if market_sentiment > 0.5 else "정상",
                "skeptic_score": 1.0 - market_sentiment  # 낙관적일수록 회의적
            }
            
        except Exception as e:
            logger.error(f"Blind spot analysis failed: {e}")
            return {"error": str(e)}
    
    async def stress_test(
        self,
        signal: InvestmentSignal,
        scenarios: List[str]
    ) -> Dict:
        """
        투자 신호 스트레스 테스트
        
        Args:
            signal: 투자 신호
            scenarios: 최악의 시나리오 목록
            
        Returns:
            스트레스 테스트 결과
        """
        prompt = f"""
        {self.PERSONA}
        
        투자 신호: {signal.action.value} {signal.ticker}
        신뢰도: {signal.confidence:.0%}
        근거: {signal.reasoning}
        
        다음 시나리오에서 이 신호가 실패할 가능성을 평가하세요:
        
        {chr(10).join(f"- {s}" for s in scenarios)}
        
        각 시나리오별로:
        1. $100,000 투자 시 예상 손실액
        2. 발생 확률 (0-100%)
        3. 대응 방안
        
        냉철하게 분석하세요.
        """
        
        try:
            response = await self.claude.generate(prompt)
            
            return {
                "signal": signal.dict(),
                "stress_test": response,
                "passed": False  # 회의론자는 항상 실패 가능성 강조
            }
            
        except Exception as e:
            logger.error(f"Stress test failed: {e}")
            return {"error": str(e)}
    
    def _build_challenge_prompt(
        self,
        consensus_view: str,
        reasoning: str,
        confidence: float,
        market_data: Optional[Dict]
    ) -> str:
        """도전 프롬프트 생성"""
        market_info = ""
        if market_data:
            market_info = f"""
            시장 데이터:
            - 가격: ${market_data.get('price', 'N/A')}
            - 변동성: {market_data.get('volatility', 'N/A')}
            - 거래량: {market_data.get('volume', 'N/A')}
            """
        
        prompt = f"""
        {self.PERSONA}
        
        다른 AI들의 합의 의견:
        - 결정: {consensus_view}
        - 근거: {reasoning}
        - 신뢰도: {confidence:.0%}
        
        {market_info}
        
        당신의 임무:
        1. 이 의견의 약점 3가지 찾기
        2. 데이터가 틀렸을 가능성 지적
        3. 시장이 간과한 악재 발굴
        4. 최악의 시나리오 제시
        
        결과 형식:
        - CHALLENGES: 약점 목록
        - WORST_CASE: 최악의 시나리오
        - HIDDEN_RISKS: 숨은 리스크
        
        비관적으로!
        """
        
        return prompt
    
    def _parse_response(
        self,
        response: str,
        consensus_view: str
    ) -> SkepticChallenge:
        """응답 파싱"""
        # 간단한 파싱 (실제로는 더 정교하게)
        challenges = []
        if "CHALLENGES:" in response:
            challenges_section = response.split("CHALLENGES:")[1].split("WORST_CASE:")[0]
            challenges = [
                line.strip().lstrip("-").strip()
                for line in challenges_section.split("\n")
                if line.strip() and not line.strip().startswith("WORST_CASE")
            ][:3]
        
        worst_case = ""
        if "WORST_CASE:" in response:
            worst_case = response.split("WORST_CASE:")[1].split("HIDDEN_RISKS:")[0].strip()
        
        hidden_risks = []
        if "HIDDEN_RISKS:" in response:
            risks_section = response.split("HIDDEN_RISKS:")[1]
            hidden_risks = [
                line.strip().lstrip("-").strip()
                for line in risks_section.split("\n")
                if line.strip()
            ][:3]
        
        return SkepticChallenge(
            consensus_view=consensus_view,
            challenges=challenges if challenges else ["분석 중 문제 발생"],
            worst_case_scenario=worst_case if worst_case else "파싱 실패",
            hidden_risks=hidden_risks,
            confidence=0.7  # 회의론자의 신뢰도
        )


# 전역 인스턴스
_skeptic_agent = None


def get_skeptic_agent(mode: SkepticMode = SkepticMode.MODERATE) -> SkepticAgent:
    """전역 SkepticAgent 인스턴스 반환"""
    global _skeptic_agent
    if _skeptic_agent is None:
        _skeptic_agent = SkepticAgent(mode=mode)
    return _skeptic_agent


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== Skeptic Agent Test ===\n")
        
        skeptic = SkepticAgent(mode=SkepticMode.EXTREME)
        
        # 1. 합의 의견 도전
        print("1. Challenging Consensus:")
        challenge = await skeptic.challenge(
            consensus_view="BUY NVDA",
            reasoning="AI boom will drive revenue growth",
            confidence=0.85,
            market_data={"price": 500, "volatility": 0.3}
        )
        print(f"  Consensus: {challenge.consensus_view}")
        print(f"  Challenges: {challenge.challenges}")
        print(f"  Worst Case: {challenge.worst_case_scenario[:50]}...\n")
        
        # 2. 맹점 찾기
        print("2. Finding Blind Spots:")
        blind_spots = await skeptic.find_blind_spots(
            ticker="TSLA",
            bull_thesis="EV adoption accelerating",
            market_sentiment=0.9  # 극낙관
        )
        print(f"  Sentiment Bias: {blind_spots.get('sentiment_bias')}")
        print(f"  Skeptic Score: {blind_spots.get('skeptic_score'):.2f}\n")
        
        print("✅ Skeptic Agent test completed!")
    
    asyncio.run(test())
