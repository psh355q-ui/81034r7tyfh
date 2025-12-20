"""
Macro Consistency Checker - 매크로 정합성 검증기

경제 지표 간 논리적 모순을 탐지하여 숨겨진 리스크 발견

핵심 기능:
1. GDP vs Interest Rate 모순 탐지
2. Unemployment vs Inflation 모순 탐지
3. 정치적 압력 추론
4. 다중 시나리오 생성

작성일: 2025-12-14
Phase: B (Critical Intelligence)
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ContradictionType(Enum):
    """모순 유형"""
    GDP_RATE_MISMATCH = "gdp_rate_mismatch"  # GDP↑ + 금리↓
    UNEMPLOYMENT_INFLATION = "unemployment_inflation"  # 실업↓ + 인플레↑
    GROWTH_SPENDING = "growth_spending"  # 성장↑ + 지출↓
    OTHER = "other"


class SeverityLevel(Enum):
    """심각도"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EconomicIndicator:
    """경제 지표"""
    name: str
    value: float
    trend: str  # "UP", "DOWN", "FLAT"
    period: str
    source: str


@dataclass
class Contradiction:
    """발견된 모순"""
    type: ContradictionType
    severity: SeverityLevel
    description: str
    indicators: List[EconomicIndicator]
    possible_reasons: List[str]
    scenarios: List[Dict]
    confidence: float


class MacroConsistencyChecker:
    """
    매크로 경제 지표 정합성 검증기
    
    경제 지표 간 논리적 충돌을 감지하고 숨겨진 이유 추론
    
    주요 모순 탐지:
    1. GDP 상승 + 금리 인하 = Over-Stimulus Warning
    2. 실업률 하락 + 인플레이션 지속 = Sticky Inflation
    3. 경기 호황 + 정부 긴축 = 정치적 압력
    
    Usage:
        checker = MacroConsistencyChecker()
        
        # 지표 입력
        gdp = EconomicIndicator("GDP Growth", 2.3, "UP", "2025Q1", "BEA")
        rate = EconomicIndicator("Fed Funds Rate", 4.75, "DOWN", "2025-01", "Fed")
        
        # 모순 탐지
        contradictions = checker.check_consistency([gdp, rate])
    """
    
    def __init__(self, claude_client=None, search_tool=None):
        """
        Args:
            claude_client: Claude API (Extended Thinking용)
            search_tool: Gemini Search Tool (사실 검증용)
        """
        if claude_client is None:
            from backend.ai.claude_client import get_claude_client
            self.claude = get_claude_client()
        else:
            self.claude = claude_client
        
        if search_tool is None:
            from backend.ai.tools.search_grounding import get_search_tool
            self.search = get_search_tool()
        else:
            self.search = search_tool
        
        logger.info("MacroConsistencyChecker initialized")
    
    async def check_consistency(
        self,
        indicators: List[EconomicIndicator]
    ) -> List[Contradiction]:
        """
        경제 지표 정합성 검증
        
        Args:
            indicators: 검증할 지표 목록
            
        Returns:
            발견된 모순 리스트
        """
        contradictions = []
        
        # 지표 쌍별로 모순 확인
        for i, ind1 in enumerate(indicators):
            for ind2 in indicators[i+1:]:
                contradiction = await self._check_pair(ind1, ind2)
                if contradiction:
                    contradictions.append(contradiction)
        
        logger.info(f"Found {len(contradictions)} contradictions in {len(indicators)} indicators")
        return contradictions
    
    async def _check_pair(
        self,
        indicator1: EconomicIndicator,
        indicator2: EconomicIndicator
    ) -> Optional[Contradiction]:
        """두 지표 간 모순 확인"""
        
        # GDP vs Interest Rate
        if self._is_gdp_rate_pair(indicator1, indicator2):
            return await self._check_gdp_rate_contradiction(indicator1, indicator2)
        
        # Unemployment vs Inflation
        elif self._is_unemployment_inflation_pair(indicator1, indicator2):
            return await self._check_unemployment_inflation(indicator1, indicator2)
        
        # Growth vs Spending
        elif self._is_growth_spending_pair(indicator1, indicator2):
            return await self._check_growth_spending(indicator1, indicator2)
        
        return None
    
    async def _check_gdp_rate_contradiction(
        self,
        gdp: EconomicIndicator,
        rate: EconomicIndicator
    ) -> Optional[Contradiction]:
        """
        GDP vs Interest Rate 모순 탐지
        
        경제학 원칙:
        - GDP 상승 → 경기 호황 → 금리 인상 (과열 방지)
        - GDP 하락 → 경기 침체 → 금리 인하 (부양)
        
        모순 케이스:
        - GDP 상승 + 금리 인하 = Over-Stimulus (정치적 압력?)
        - GDP 하락 + 금리 인상 = 인플레 우선 (숨은 위기?)
        """
        # GDP 상승 + 금리 인하?
        if gdp.trend == "UP" and rate.trend == "DOWN":
            # 모순 발견! 심층 분석
            prompt = f"""
            경제 지표 간 모순이 발견되었습니다:
            
            - GDP 성장률: {gdp.value}% (상승 중)
            - 기준 금리: {rate.value}% (하락 중)
            
            경제학적으로 GDP가 상승하면 금리를 인상해야 하는데,
            오히려 금리를 내리고 있습니다.
            
            이 모순이 발생한 숨겨진 이유를 3가지 시나리오로 추론하세요:
            
            1. 정치적 압력 (선거, 정부)
            2. 숨은 유동성 위기
            3. 데이터 조작 가능성
            
            각 시나리오의 발생 확률과 증거를 제시하세요.
            """
            
            try:
                analysis = await self.claude.generate(prompt)
                
                return Contradiction(
                    type=ContradictionType.GDP_RATE_MISMATCH,
                    severity=SeverityLevel.HIGH,
                    description=f"GDP 상승({gdp.value}%) + 금리 인하({rate.value}%) = 과잉 부양 경고",
                    indicators=[gdp, rate],
                    possible_reasons=self._extract_reasons(analysis),
                    scenarios=self._extract_scenarios(analysis),
                    confidence=0.85
                )
            except Exception as e:
                logger.error(f"Failed to analyze GDP-Rate contradiction: {e}")
                return None
        
        # GDP 하락 + 금리 인상?
        elif gdp.trend == "DOWN" and rate.trend == "UP":
            prompt = f"""
            비정상적 정책 조합 발견:
            
            - GDP 성장률: {gdp.value}% (하락 중)
            - 기준 금리: {rate.value}% (상승 중)
            
            경기가 나빠지는데 금리를 올리는 것은 인플레이션이
            심각하거나 다른 숨은 위기가 있다는 신호입니다.
            
            가능한 이유를 분석하세요.
            """
            
            try:
                analysis = await self.claude.generate(prompt)
                
                return Contradiction(
                    type=ContradictionType.GDP_RATE_MISMATCH,
                    severity=SeverityLevel.CRITICAL,
                    description=f"GDP 하락({gdp.value}%) + 금리 인상({rate.value}%) = 숨은 위기 의심",
                    indicators=[gdp, rate],
                    possible_reasons=self._extract_reasons(analysis),
                    scenarios=self._extract_scenarios(analysis),
                    confidence=0.9
                )
            except Exception as e:
                logger.error(f"Failed to analyze GDP-Rate contradiction: {e}")
                return None
        
        return None
    
    async def _check_unemployment_inflation(
        self,
        unemployment: EconomicIndicator,
        inflation: EconomicIndicator
    ) -> Optional[Contradiction]:
        """
        Unemployment vs Inflation 모순 탐지
        
        Phillips Curve:
        - 실업률↓ + 인플레↑ = 정상 (경기 과열)
        - 실업률↑ + 인플레↓ = 정상 (경기 침체)
        
        모순 (Stagflation):
        - 실업률↑ + 인플레↑ = 최악 (스태그플레이션)
        """
        # Stagflation 감지
        if unemployment.trend == "UP" and inflation.trend == "UP":
            prompt = f"""
            Stagflation(스태그플레이션) 신호 감지:
            
            - 실업률: {unemployment.value}% (상승 중)
            - 인플레이션: {inflation.value}% (상승 중)
            
            이는 1970년대 오일쇼크 이후 가장 위험한 경제 상황입니다.
            
            현재 상황의 원인과 투자 전략을 제시하세요.
            """
            
            try:
                analysis = await self.claude.generate(prompt)
                
                return Contradiction(
                    type=ContradictionType.UNEMPLOYMENT_INFLATION,
                    severity=SeverityLevel.CRITICAL,
                    description=f"Stagflation 경고: 실업↑({unemployment.value}%) + 인플레↑({inflation.value}%)",
                    indicators=[unemployment, inflation],
                    possible_reasons=["공급망 붕괴", "에너지 위기", "통화 정책 실패"],
                    scenarios=self._extract_scenarios(analysis),
                    confidence=0.95
                )
            except Exception as e:
                logger.error(f"Failed to analyze Stagflation: {e}")
                return None
        
        return None
    
    async def _check_growth_spending(
        self,
        growth: EconomicIndicator,
        spending: EconomicIndicator
    ) -> Optional[Contradiction]:
        """성장 vs 지출 모순 탐지"""
        # 성장 호조 + 정부 긴축?
        if growth.trend == "UP" and spending.trend == "DOWN":
            return Contradiction(
                type=ContradictionType.GROWTH_SPENDING,
                severity=SeverityLevel.MODERATE,
                description="경기 호황기 정부 긴축 = 재정 건전화 우선",
                indicators=[growth, spending],
                possible_reasons=["부채 축소", "인플레 억제", "정치적 보수주의"],
                scenarios=[],
                confidence=0.7
            )
        
        return None
    
    def _is_gdp_rate_pair(self, ind1: EconomicIndicator, ind2: EconomicIndicator) -> bool:
        """GDP와 금리 쌍인지 확인"""
        names = {ind1.name.lower(), ind2.name.lower()}
        return (
            any("gdp" in name or "growth" in name for name in names) and
            any("rate" in name or "interest" in name or "funds" in name for name in names)
        )
    
    def _is_unemployment_inflation_pair(self, ind1: EconomicIndicator, ind2: EconomicIndicator) -> bool:
        """실업률과 인플레이션 쌍인지 확인"""
        names = {ind1.name.lower(), ind2.name.lower()}
        return (
            any("unemployment" in name or "jobless" in name for name in names) and
            any("inflation" in name or "cpi" in name or "pce" in name for name in names)
        )
    
    def _is_growth_spending_pair(self, ind1: EconomicIndicator, ind2: EconomicIndicator) -> bool:
        """성장과 지출 쌍인지 확인"""
        names = {ind1.name.lower(), ind2.name.lower()}
        return (
            any("gdp" in name or "growth" in name for name in names) and
            any("spending" in name or "budget" in name or "fiscal" in name for name in names)
        )
    
    def _extract_reasons(self, analysis: str) -> List[str]:
        """분석에서 이유 추출"""
        # 간단한 파싱 (실제로는 더 정교하게)
        reasons = []
        if "정치" in analysis or "압력" in analysis:
            reasons.append("정치적 압력")
        if "유동성" in analysis or "위기" in analysis:
            reasons.append("숨은 유동성 위기")
        if "데이터" in analysis or "조작" in analysis:
            reasons.append("데이터 신뢰성 문제")
        
        return reasons if reasons else ["추가 분석 필요"]
    
    def _extract_scenarios(self, analysis: str) -> List[Dict]:
        """분석에서 시나리오 추출"""
        # 간단한 구조 반환 (실제로는 LLM 응답 파싱)
        return [
            {"name": "Base Case", "probability": 0.6, "description": analysis[:100]},
            {"name": "Worst Case", "probability": 0.3, "description": "시장 급락"},
            {"name": "Best Case", "probability": 0.1, "description": "일시적 현상"}
        ]


# 전역 인스턴스
_consistency_checker = None


def get_consistency_checker() -> MacroConsistencyChecker:
    """전역 MacroConsistencyChecker 인스턴스 반환"""
    global _consistency_checker
    if _consistency_checker is None:
        _consistency_checker = MacroConsistencyChecker()
    return _consistency_checker


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== Macro Consistency Checker Test ===\n")
        
        checker = MacroConsistencyChecker()
        
        # 테스트 시나리오 1: GDP 상승 + 금리 인하 (모순!)
        print("Scenario 1: GDP UP + Rate DOWN (Contradiction!)")
        gdp = EconomicIndicator("GDP Growth", 2.3, "UP", "2025Q1", "BEA")
        rate = EconomicIndicator("Fed Funds Rate", 4.75, "DOWN", "2025-01", "Fed")
        
        contradictions = await checker.check_consistency([gdp, rate])
        
        if contradictions:
            c = contradictions[0]
            print(f"  Type: {c.type.value}")
            print(f"  Severity: {c.severity.value}")
            print(f"  Description: {c.description}")
            print(f"  Possible Reasons: {c.possible_reasons}")
            print(f"  Confidence: {c.confidence:.0%}\n")
        else:
            print("  No contradiction found\n")
        
        # 테스트 시나리오 2: Stagflation
        print("Scenario 2: Unemployment UP + Inflation UP (Stagflation!)")
        unemployment = EconomicIndicator("Unemployment Rate", 5.2, "UP", "2025-01", "BLS")
        inflation = EconomicIndicator("CPI", 4.5, "UP", "2025-01", "BLS")
        
        contradictions2 = await checker.check_consistency([unemployment, inflation])
        
        if contradictions2:
            c = contradictions2[0]
            print(f"  Type: {c.type.value}")
            print(f"  Severity: {c.severity.value}")
            print(f"  Description: {c.description}\n")
        
        print("✅ Macro Consistency Checker test completed!")
    
    asyncio.run(test())
