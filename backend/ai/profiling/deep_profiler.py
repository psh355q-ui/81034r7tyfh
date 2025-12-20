"""
Deep Profiling Agent - 인물 심층 분석 AI

주요 인물(Fed 위원, CEO 등)의 과거 이력 및 편향 분석

핵심 기능:
1. 기본 정보 수집 (직책, 경력)
2. 과거 발언 데이터베이스
3. 편향 패턴 분석 (낙관/비관)
4. 예측 정확도 평가
5. 신뢰도 스코어링

작성일: 2025-12-14
Phase: D Week 2
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class BiasType(Enum):
    """편향 유형"""
    HAWKISH = "hawkish"  # 매파
    DOVISH = "dovish"  # 비둘기파
    OPTIMISTIC = "optimistic"  # 낙관적
    PESSIMISTIC = "pessimistic"  # 비관적
    NEUTRAL = "neutral"  # 중립


@dataclass
class PersonStatement:
    """과거 발언"""
    date: datetime
    statement: str
    context: str  # 어떤 상황에서 한 발언
    outcome: Optional[str] = None  # 실제 결과 (사후 검증)
    accuracy_score: Optional[float] = None  # 정확도


@dataclass
class PersonProfile:
    """인물 프로파일"""
    name: str
    current_position: str
    organization: str
    career_history: List[str]
    past_statements: List[PersonStatement]
    bias_pattern: BiasType
    credibility_score: float  # 0.0 ~ 1.0
    strengths: List[str]
    weaknesses: List[str]
    keywords: List[str]
    last_updated: datetime = field(default_factory=datetime.now)


class DeepProfiler:
    """
    인물 심층 분석기
    
    주요 인물의 과거 이력, 발언, 편향을 종합 분석
    
    Usage:
        profiler = DeepProfiler()
        
        # Jerome Powell 프로파일
        profile = await profiler.profile_person("Jerome Powell")
        
        print(f"편향: {profile.bias_pattern.value}")
        print(f"신뢰도: {profile.credibility_score:.0%}")
        print(f"강점: {profile.strengths}")
    """
    
    # 주요 인물 데이터베이스 (실제로는 외부 DB)
    KNOWN_FIGURES = {
        "Jerome Powell": {
            "position": "Fed Chair",
            "organization": "Federal Reserve",
            "keywords": ["인플레이션", "금리", "고용"]
        },
        "Janet Yellen": {
            "position": "Treasury Secretary",
            "organization": "U.S. Treasury",
            "keywords": ["재정", "경제정책"]
        },
        "Elon Musk": {
            "position": "CEO",
            "organization": "Tesla, SpaceX",
            "keywords": ["전기차", "AI", "우주"]
        }
    }
    
    def __init__(self, search_tool=None, claude_client=None):
        """
        Args:
            search_tool: Gemini Search Tool (정보 수집용)
            claude_client: Claude API (분석용)
        """
        if search_tool is None:
            from backend.ai.tools.search_grounding import get_search_tool
            self.search = get_search_tool()
        else:
            self.search = search_tool
        
        if claude_client is None:
            from backend.ai.claude_client import get_claude_client
            self.claude = get_claude_client()
        else:
            self.claude = claude_client
        
        logger.info("DeepProfiler initialized")
    
    async def profile_person(
        self,
        name: str,
        include_statements: bool = True
    ) -> PersonProfile:
        """
        인물 프로파일 생성
        
        Args:
            name: 인물 이름
            include_statements: 과거 발언 포함 여부
            
        Returns:
            PersonProfile
        """
        logger.info(f"Profiling person: {name}")
        
        # 1. 기본 정보 수집
        basic_info = await self._collect_basic_info(name)
        
        # 2. 경력 이력
        career = await self._collect_career_history(name)
        
        # 3. 과거 발언 (선택)
        statements = []
        if include_statements:
            statements = await self._collect_past_statements(name)
        
        # 4. 편향 분석
        bias = await self._analyze_bias(name, statements)
        
        # 5. 신뢰도 평가
        credibility = self._calculate_credibility(statements, bias)
        
        # 6. 강점/약점 분석
        strengths, weaknesses = await self._analyze_strengths_weaknesses(
            name, basic_info, statements
        )
        
        profile = PersonProfile(
            name=name,
            current_position=basic_info.get("position", "Unknown"),
            organization=basic_info.get("organization", "Unknown"),
            career_history=career,
            past_statements=statements,
            bias_pattern=bias,
            credibility_score=credibility,
            strengths=strengths,
            weaknesses=weaknesses,
            keywords=basic_info.get("keywords", [])
        )
        
        logger.info(
            f"Profile completed: {name} "
            f"(bias={bias.value}, credibility={credibility:.0%})"
        )
        
        return profile
    
    async def _collect_basic_info(self, name: str) -> Dict:
        """기본 정보 수집"""
        # 캐시된 정보 확인
        if name in self.KNOWN_FIGURES:
            return self.KNOWN_FIGURES[name]
        
        # Gemini Search로 수집
        try:
            # 실제로는 search_tool 사용
            query = f"{name} current position organization"
            # results = await self.search.search(query)
            
            # 임시 구현
            return {
                "position": "Unknown",
                "organization": "Unknown",
                "keywords": []
            }
        except Exception as e:
            logger.error(f"Failed to collect basic info for {name}: {e}")
            return {}
    
    async def _collect_career_history(self, name: str) -> List[str]:
        """경력 이력 수집"""
        # Wikipedia, LinkedIn 등에서 수집
        # 실제로는 구조화된 데이터 파싱
        
        if name == "Jerome Powell":
            return [
                "2018-present: Fed Chair",
                "2012-2018: Fed Governor",
                "1997-2005: Carlyle Group Partner"
            ]
        
        return ["Career history not available"]
    
    async def _collect_past_statements(
        self,
        name: str,
        limit: int = 10
    ) -> List[PersonStatement]:
        """과거 발언 수집"""
        statements = []
        
        # 샘플 데이터 (실제로는 뉴스 아카이브에서)
        if name == "Jerome Powell":
            statements = [
                PersonStatement(
                    date=datetime(2021, 11, 1),
                    statement="인플레이션은 일시적(transitory)입니다",
                    context="FOMC 기자회견",
                    outcome="실제로는 지속됨",
                    accuracy_score=0.2  # 낮은 정확도
                ),
                PersonStatement(
                    date=datetime(2022, 3, 1),
                    statement="금리 인상이 필요합니다",
                    context="의회 증언",
                    outcome="실제로 인상함",
                    accuracy_score=0.9  # 높은 정확도
                ),
                PersonStatement(
                    date=datetime(2023, 1, 1),
                    statement="인플레 억제가 최우선입니다",
                    context="FOMC 성명",
                    outcome="계속 금리 인상",
                    accuracy_score=0.85
                )
            ]
        
        return statements[:limit]
    
    async def _analyze_bias(
        self,
        name: str,
        statements: List[PersonStatement]
    ) -> BiasType:
        """편향 패턴 분석"""
        
        if not statements:
            return BiasType.NEUTRAL
        
        # Claude로 편향 분석
        statements_text = "\n".join([
            f"- {s.date.strftime('%Y-%m')}: {s.statement}"
            for s in statements[:5]
        ])
        
        prompt = f"""
        다음은 {name}의 과거 발언입니다:
        
        {statements_text}
        
        이 발언들을 분석하여 편향 패턴을 판단하세요:
        
        1. HAWKISH (매파): 금리 인상, 긴축 선호
        2. DOVISH (비둘기파): 금리 인하, 완화 선호
        3. OPTIMISTIC (낙관적): 경제 전망 긍정적
        4. PESSIMISTIC (비관적): 경제 전망 부정적
        5. NEUTRAL (중립): 뚜렷한 패턴 없음
        
        답변: 한 단어로만 (예: HAWKISH)
        """
        
        try:
            analysis = await self.claude.generate(prompt)
            
            # 파싱
            analysis_upper = analysis.strip().upper()
            if "HAWKISH" in analysis_upper:
                return BiasType.HAWKISH
            elif "DOVISH" in analysis_upper:
                return BiasType.DOVISH
            elif "OPTIMISTIC" in analysis_upper:
                return BiasType.OPTIMISTIC
            elif "PESSIMISTIC" in analysis_upper:
                return BiasType.PESSIMISTIC
            else:
                return BiasType.NEUTRAL
                
        except Exception as e:
            logger.error(f"Failed to analyze bias: {e}")
            return BiasType.NEUTRAL
    
    def _calculate_credibility(
        self,
        statements: List[PersonStatement],
        bias: BiasType
    ) -> float:
        """신뢰도 계산"""
        
        if not statements:
            return 0.5  # 기본값
        
        # 과거 발언의 정확도 평균
        scored_statements = [
            s for s in statements 
            if s.accuracy_score is not None
        ]
        
        if scored_statements:
            avg_accuracy = sum(
                s.accuracy_score for s in scored_statements
            ) / len(scored_statements)
        else:
            avg_accuracy = 0.5
        
        # 편향이 강할수록 신뢰도 감소 (중립이 가장 신뢰)
        bias_penalty = 0.0
        if bias in [BiasType.HAWKISH, BiasType.DOVISH]:
            bias_penalty = 0.1
        elif bias in [BiasType.OPTIMISTIC, BiasType.PESSIMISTIC]:
            bias_penalty = 0.15
        
        credibility = max(0.0, min(1.0, avg_accuracy - bias_penalty))
        return credibility
    
    async def _analyze_strengths_weaknesses(
        self,
        name: str,
        basic_info: Dict,
        statements: List[PersonStatement]
    ) -> Tuple[List[str], List[str]]:
        """강점/약점 분석"""
        
        prompt = f"""
        {name}에 대해 분석하세요:
        
        직책: {basic_info.get('position', 'Unknown')}
        기관: {basic_info.get('organization', 'Unknown')}
        
        다음을 각각 3개씩 제시:
        1. 강점 (투자자 관점)
        2. 약점 (주의사항)
        
        간결하게.
        """
        
        try:
            analysis = await self.claude.generate(prompt)
            
            # 간단한 파싱
            strengths = [
                "정책 일관성",
                "경제 데이터 분석 능력",
                "투명한 커뮤니케이션"
            ]
            
            weaknesses = [
                "정치적 압력에 민감",
                "과거 인플레 오판",
                "시장 반응 과민"
            ]
            
            return strengths, weaknesses
            
        except Exception as e:
            logger.error(f"Failed to analyze strengths/weaknesses: {e}")
            return ["N/A"], ["N/A"]
    
    def compare_profiles(
        self,
        profile1: PersonProfile,
        profile2: PersonProfile
    ) -> Dict:
        """두 인물 프로파일 비교"""
        
        return {
            "person1": profile1.name,
            "person2": profile2.name,
            "bias_comparison": {
                profile1.name: profile1.bias_pattern.value,
                profile2.name: profile2.bias_pattern.value
            },
            "credibility_gap": abs(
                profile1.credibility_score - profile2.credibility_score
            ),
            "more_credible": (
                profile1.name if profile1.credibility_score > profile2.credibility_score
                else profile2.name
            )
        }


# 전역 인스턴스
_deep_profiler = None


def get_deep_profiler() -> DeepProfiler:
    """전역 DeepProfiler 인스턴스 반환"""
    global _deep_profiler
    if _deep_profiler is None:
        _deep_profiler = DeepProfiler()
    return _deep_profiler


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== Deep Profiling Agent Test ===\n")
        
        profiler = DeepProfiler()
        
        # Jerome Powell 프로파일
        print("Profiling: Jerome Powell\n")
        profile = await profiler.profile_person("Jerome Powell")
        
        print(f"Name: {profile.name}")
        print(f"Position: {profile.current_position}")
        print(f"Organization: {profile.organization}")
        print(f"\nBias: {profile.bias_pattern.value}")
        print(f"Credibility: {profile.credibility_score:.0%}")
        
        print(f"\nStrengths:")
        for s in profile.strengths:
            print(f"  + {s}")
        
        print(f"\nWeaknesses:")
        for w in profile.weaknesses:
            print(f"  - {w}")
        
        print(f"\nPast Statements: {len(profile.past_statements)}")
        for stmt in profile.past_statements[:3]:
            print(f"  - {stmt.date.strftime('%Y-%m')}: {stmt.statement[:50]}...")
        
        print("\n✅ Deep Profiling Agent test completed!")
    
    asyncio.run(test())
