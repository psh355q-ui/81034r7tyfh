"""
Scenario Simulator - 시나리오 분석 엔진

"만약 ~한다면?" 조건부 시뮬레이션을 통한 다중 시나리오 생성

핵심 기능:
1. Bull/Neutral/Bear 시나리오 자동 생성
2. 조건별 영향도 계산
3. 확률 가중 평균
4. 스트레스 테스트

작성일: 2025-12-14
Phase: B Week 2
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """시나리오 유형"""
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"


class ConditionType(Enum):
    """조건 유형"""
    INTEREST_RATE = "interest_rate"
    GDP_GROWTH = "gdp_growth"
    INFLATION = "inflation"
    EARNINGS = "earnings"
    VALUATION = "valuation"
    SENTIMENT = "sentiment"


@dataclass
class Condition:
    """시나리오 조건"""
    type: ConditionType
    current_value: float
    scenario_value: float
    description: str


@dataclass
class MarketImpact:
    """시장 영향"""
    asset_class: str  # "stocks", "bonds", "fx", "commodities"
    expected_return: float  # %
    volatility: float  # %
    confidence: float


@dataclass
class Scenario:
    """시나리오"""
    id: str
    name: str
    type: ScenarioType
    probability: float  # 0.0 ~ 1.0
    conditions: List[Condition]
    impacts: List[MarketImpact]
    narrative: str  # AI 생성 서술
    created_at: datetime = field(default_factory=datetime.now)


class ScenarioSimulator:
    """
    시나리오 시뮬레이터
    
    조건부 "만약 ~한다면?" 분석을 통해 다양한 시나리오 생성
    
    예시:
    1. "만약 Fed가 금리를 0.5% 올린다면?"
       → Bull/Neutral/Bear 시나리오 3개 생성
       → 각 시나리오의 확률과 영향 계산
    
    2. "만약 엔비디아 실적이 20% 증가한다면?"
       → 반도체 섹터 영향
       → 연관 종목 영향
    
    Usage:
        simulator = ScenarioSimulator()
        
        # 조건 설정
        condition = Condition(
            type=ConditionType.INTEREST_RATE,
            current_value=4.75,
            scenario_value=5.25,
            description="Fed raises rate by 0.5%"
        )
        
        # 시나리오 생성
        scenarios = simulator.generate_scenarios([condition])
    """
    
    def __init__(self, claude_client=None):
        """
        Args:
            claude_client: Claude API (시나리오 서술 생성용)
        """
        if claude_client is None:
            from backend.ai.claude_client import get_claude_client
            self.claude = get_claude_client()
        else:
            self.claude = claude_client
        
        logger.info("ScenarioSimulator initialized")
    
    async def generate_scenarios(
        self,
        conditions: List[Condition],
        ticker: Optional[str] = None
    ) -> List[Scenario]:
        """
        조건 기반 시나리오 생성
        
        Args:
            conditions: 시나리오 조건 목록
            ticker: 특정 종목 (선택)
            
        Returns:
            Bull/Neutral/Bear 시나리오 리스트
        """
        scenarios = []
        
        # Bull 시나리오
        bull = await self._generate_bull_scenario(conditions, ticker)
        scenarios.append(bull)
        
        # Neutral 시나리오
        neutral = await self._generate_neutral_scenario(conditions, ticker)
        scenarios.append(neutral)
        
        # Bear 시나리오
        bear = await self._generate_bear_scenario(conditions, ticker)
        scenarios.append(bear)
        
        # 확률 정규화 (합계 1.0)
        self._normalize_probabilities(scenarios)
        
        logger.info(
            f"Generated {len(scenarios)} scenarios: "
            f"Bull={bull.probability:.0%}, "
            f"Neutral={neutral.probability:.0%}, "
            f"Bear={bear.probability:.0%}"
        )
        
        return scenarios
    
    async def _generate_bull_scenario(
        self,
        conditions: List[Condition],
        ticker: Optional[str]
    ) -> Scenario:
        """낙관 시나리오 생성"""
        
        # AI로 낙관적 서술 생성
        prompt = self._build_scenario_prompt(
            conditions, ticker, "bullish"
        )
        narrative = await self.claude.generate(prompt)
        
        # 영향 계산 (낙관적)
        impacts = [
            MarketImpact(
                asset_class="stocks",
                expected_return=15.0,  # +15%
                volatility=12.0,
                confidence=0.7
            ),
            MarketImpact(
                asset_class="bonds",
                expected_return=-5.0,  # -5% (금리 상승 시)
                volatility=8.0,
                confidence=0.6
            )
        ]
        
        return Scenario(
            id=f"bull_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Bullish Case",
            type=ScenarioType.BULLISH,
            probability=0.3,  # 초기값, 나중에 정규화
            conditions=conditions,
            impacts=impacts,
            narrative=narrative[:500]  # 500자 제한
        )
    
    async def _generate_neutral_scenario(
        self,
        conditions: List[Condition],
        ticker: Optional[str]
    ) -> Scenario:
        """중립 시나리오 생성"""
        
        prompt = self._build_scenario_prompt(
            conditions, ticker, "neutral"
        )
        narrative = await self.claude.generate(prompt)
        
        impacts = [
            MarketImpact(
                asset_class="stocks",
                expected_return=5.0,  # +5%
                volatility=10.0,
                confidence=0.8
            ),
            MarketImpact(
                asset_class="bonds",
                expected_return=2.0,
                volatility=5.0,
                confidence=0.8
            )
        ]
        
        return Scenario(
            id=f"neutral_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Base Case",
            type=ScenarioType.NEUTRAL,
            probability=0.5,  # 초기값
            conditions=conditions,
            impacts=impacts,
            narrative=narrative[:500]
        )
    
    async def _generate_bear_scenario(
        self,
        conditions: List[Condition],
        ticker: Optional[str]
    ) -> Scenario:
        """비관 시나리오 생성"""
        
        prompt = self._build_scenario_prompt(
            conditions, ticker, "bearish"
        )
        narrative = await self.claude.generate(prompt)
        
        impacts = [
            MarketImpact(
                asset_class="stocks",
                expected_return=-10.0,  # -10%
                volatility=18.0,
                confidence=0.6
            ),
            MarketImpact(
                asset_class="bonds",
                expected_return=8.0,  # 안전자산 선호
                volatility=6.0,
                confidence=0.7
            )
        ]
        
        return Scenario(
            id=f"bear_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Bearish Case",
            type=ScenarioType.BEARISH,
            probability=0.2,  # 초기값
            conditions=conditions,
            impacts=impacts,
            narrative=narrative[:500]
        )
    
    def _build_scenario_prompt(
        self,
        conditions: List[Condition],
        ticker: Optional[str],
        scenario_type: str
    ) -> str:
        """시나리오 생성 프롬프트"""
        
        conditions_text = "\n".join([
            f"- {c.description}: {c.current_value} → {c.scenario_value}"
            for c in conditions
        ])
        
        ticker_text = f" for {ticker}" if ticker else ""
        
        prompt = f"""
        다음 조건 하에서 {scenario_type} 시나리오를 작성하세요{ticker_text}:
        
        조건:
        {conditions_text}
        
        {scenario_type.upper()} 관점에서:
        1. 시장 반응 (2-3문장)
        2. 주요 리스크 또는 기회
        3. 투자 시사점
        
        간결하게 5문장 이내로 작성하세요.
        """
        
        return prompt
    
    def _normalize_probabilities(self, scenarios: List[Scenario]):
        """확률 정규화 (합계 1.0)"""
        total = sum(s.probability for s in scenarios)
        
        if total > 0:
            for scenario in scenarios:
                scenario.probability /= total
    
    def calculate_expected_value(
        self,
        scenarios: List[Scenario],
        asset_class: str = "stocks"
    ) -> Dict:
        """
        기대값 계산 (확률 가중 평균)
        
        Args:
            scenarios: 시나리오 리스트
            asset_class: 자산 클래스
            
        Returns:
            기대 수익률 및 리스크
        """
        expected_return = 0.0
        expected_volatility = 0.0
        
        for scenario in scenarios:
            # 해당 자산 클래스 영향 찾기
            for impact in scenario.impacts:
                if impact.asset_class == asset_class:
                    expected_return += scenario.probability * impact.expected_return
                    expected_volatility += scenario.probability * impact.volatility
                    break
        
        return {
            "expected_return": expected_return,
            "expected_volatility": expected_volatility,
            "sharpe_ratio": expected_return / expected_volatility if expected_volatility > 0 else 0
        }
    
    def stress_test(
        self,
        scenarios: List[Scenario],
        portfolio_value: float,
        asset_allocation: Dict[str, float]  # {"stocks": 0.6, "bonds": 0.4}
    ) -> Dict:
        """
        포트폴리오 스트레스 테스트
        
        Args:
            scenarios: 시나리오 리스트
            portfolio_value: 포트폴리오 가치
            asset_allocation: 자산 배분
            
        Returns:
            시나리오별 손익
        """
        results = {}
        
        for scenario in scenarios:
            total_return = 0.0
            
            for asset_class, weight in asset_allocation.items():
                # 해당 자산의 영향 찾기
                for impact in scenario.impacts:
                    if impact.asset_class == asset_class:
                        total_return += weight * impact.expected_return / 100
                        break
            
            # 손익 계산
            pnl = portfolio_value * total_return
            
            results[scenario.name] = {
                "return_pct": total_return * 100,
                "pnl": pnl,
                "final_value": portfolio_value + pnl,
                "probability": scenario.probability
            }
        
        # 기대값 계산
        expected_pnl = sum(
            r["pnl"] * r["probability"] 
            for r in results.values()
        )
        
        results["Expected"] = {
            "pnl": expected_pnl,
            "final_value": portfolio_value + expected_pnl
        }
        
        return results
    
    def get_worst_case(
        self,
        scenarios: List[Scenario],
        asset_class: str = "stocks"
    ) -> Tuple[Scenario, MarketImpact]:
        """최악의 시나리오 찾기"""
        worst_scenario = None
        worst_impact = None
        min_return = float('inf')
        
        for scenario in scenarios:
            for impact in scenario.impacts:
                if impact.asset_class == asset_class:
                    if impact.expected_return < min_return:
                        min_return = impact.expected_return
                        worst_scenario = scenario
                        worst_impact = impact
        
        return worst_scenario, worst_impact


# 전역 인스턴스
_scenario_simulator = None


def get_scenario_simulator() -> ScenarioSimulator:
    """전역 ScenarioSimulator 인스턴스 반환"""
    global _scenario_simulator
    if _scenario_simulator is None:
        _scenario_simulator = ScenarioSimulator()
    return _scenario_simulator


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== Scenario Simulator Test ===\n")
        
        simulator = ScenarioSimulator()
        
        # 시나리오: Fed 금리 인상
        print("Scenario: Fed raises rate by 0.5%\n")
        condition = Condition(
            type=ConditionType.INTEREST_RATE,
            current_value=4.75,
            scenario_value=5.25,
            description="Fed raises rate by 0.5%"
        )
        
        scenarios = await simulator.generate_scenarios([condition])
        
        # 시나리오 출력
        for scenario in scenarios:
            print(f"{scenario.name}:")
            print(f"  Type: {scenario.type.value}")
            print(f"  Probability: {scenario.probability:.0%}")
            print(f"  Narrative: {scenario.narrative[:100]}...")
            
            # 주식 영향
            for impact in scenario.impacts:
                if impact.asset_class == "stocks":
                    print(f"  Stocks: {impact.expected_return:+.1f}% (±{impact.volatility:.1f}%)")
            print()
        
        # 기대값 계산
        print("Expected Value (Stocks):")
        ev = simulator.calculate_expected_value(scenarios, "stocks")
        print(f"  Return: {ev['expected_return']:+.1f}%")
        print(f"  Volatility: {ev['expected_volatility']:.1f}%")
        print(f"  Sharpe: {ev['sharpe_ratio']:.2f}\n")
        
        # 포트폴리오 스트레스 테스트
        print("Portfolio Stress Test ($100,000):")
        test_results = simulator.stress_test(
            scenarios,
            portfolio_value=100000,
            asset_allocation={"stocks": 0.6, "bonds": 0.4}
        )
        
        for scenario_name, result in test_results.items():
            if "pnl" in result:
                print(f"  {scenario_name}: ${result['pnl']:+,.0f} ({result.get('probability', 0):.0%})")
        
        print("\n✅ Scenario Simulator test completed!")
    
    asyncio.run(test())
