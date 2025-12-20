"""
Skeptic Agent (G2) - 악마의 변호인

다른 AI들이 "매수"를 외칠 때,
강제로 반대 논리를 찾아 "시장의 맹점"을 보고합니다.

핵심 원칙:
1. 어떤 상황에서도 긍정적 의견 금지
2. 숨겨진 약점, 과대평가된 요소 찾기
3. "이미 주가에 반영됨" 논리 활용
4. 구체적인 숫자와 데이터로 반박
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SkepticRecommendation(Enum):
    """회의론적 권고"""
    PROCEED = "진행 가능"  # 반박 논거가 약함
    CAUTION = "주의 필요"  # 일부 리스크 존재
    AVOID = "회피 권고"    # 심각한 리스크


@dataclass
class SkepticAnalysis:
    """회의론적 분석 결과"""
    ticker: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 다른 AI들의 견해
    consensus_view: str = ""  # BUY, SELL, HOLD
    consensus_confidence: float = 0.0
    consensus_reasoning: str = ""
    
    # 회의론적 반박
    counter_arguments: List[str] = field(default_factory=list)
    overlooked_risks: List[str] = field(default_factory=list)
    data_reliability_issues: List[str] = field(default_factory=list)
    
    # 역사적 유사 실패 사례
    historical_failures: List[str] = field(default_factory=list)
    
    # "모두가 아는 사실"의 허점
    blind_spots: List[str] = field(default_factory=list)
    
    # 최악의 시나리오
    worst_case_scenario: str = ""
    worst_case_probability: float = 0.0
    
    # 종합
    skeptic_score: float = 50.0  # 0-100 (높을수록 우려)
    recommendation: SkepticRecommendation = SkepticRecommendation.CAUTION


# 일반적인 시장 맹점 패턴
COMMON_BLIND_SPOTS = {
    "growth": [
        "성장률이 영구적으로 지속될 것이라는 가정",
        "경쟁사의 추격 가능성 과소평가",
        "시장 포화점 도달 시기 무시",
    ],
    "valuation": [
        "높은 PER이 정당화될 것이라는 믿음",
        "금리 상승 시 밸류에이션 압박 무시",
        "동종 업계 평균 대비 프리미엄 지속 가정",
    ],
    "moat": [
        "진입 장벽이 영구적이라는 착각",
        "기술 혁신으로 인한 disruption 가능성",
        "규제 변화 리스크 과소평가",
    ],
    "management": [
        "경영진의 과거 실수 패턴",
        "내부자 매도 신호 무시",
        "임원 보상 구조의 단기 편향",
    ],
}

# 역사적 실패 사례
HISTORICAL_FAILURES = [
    {
        "case": "2000년 시스코",
        "consensus": "인터넷 인프라의 절대 강자",
        "outcome": "80% 폭락, 20년간 고점 회복 못함",
        "lesson": "성장 신화가 영원하지 않다",
        "keywords": ["tech", "growth", "infrastructure"],
    },
    {
        "case": "2021년 줌비디오",
        "consensus": "재택근무 영구화로 수혜",
        "outcome": "고점 대비 70%+ 하락",
        "lesson": "팬데믹 특수가 정상화",
        "keywords": ["tech", "pandemic", "growth"],
    },
    {
        "case": "2022년 페이스북(메타)",
        "consensus": "메타버스로 재도약",
        "outcome": "70% 폭락 후 회복",
        "lesson": "전환 비용과 시간 과소평가",
        "keywords": ["tech", "pivot", "metaverse"],
    },
    {
        "case": "2008년 리먼 브라더스",
        "consensus": "Too Big To Fail",
        "outcome": "파산, 금융위기 촉발",
        "lesson": "시스템 리스크는 갑자기 현실화",
        "keywords": ["financial", "banking", "crisis"],
    },
    {
        "case": "2015년 발레안트",
        "consensus": "제약 롤업 전략의 승자",
        "outcome": "90% 폭락",
        "lesson": "공격적 회계와 부채의 위험",
        "keywords": ["pharma", "acquisition", "debt"],
    },
]


class SkepticAgent:
    """
    Skeptic Agent (악마의 변호인)
    
    시장 합의에 대해 강제로 반대 논리를 제시하여
    투자자가 인식하지 못하는 리스크를 발굴합니다.
    """
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
    
    async def analyze(
        self,
        ticker: str,
        consensus_analysis: Dict,
        market_data: Dict = None,
        news_data: List[str] = None,
    ) -> SkepticAnalysis:
        """
        회의론적 분석 수행
        
        Args:
            ticker: 종목 티커
            consensus_analysis: 다른 AI들의 합의 분석
            market_data: 시장 데이터
            news_data: 뉴스 데이터
            
        Returns:
            SkepticAnalysis: 회의론적 분석 결과
        """
        logger.info(f"Skeptic 분석 시작: {ticker}")
        
        consensus_view = consensus_analysis.get("action", "HOLD")
        consensus_confidence = consensus_analysis.get("confidence", 0.5)
        consensus_reasoning = consensus_analysis.get("reasoning", "")
        
        # 1. 반대 논거 생성
        counter_arguments = await self._generate_counter_arguments(
            ticker, consensus_analysis
        )
        
        # 2. 간과된 리스크 발굴
        overlooked_risks = await self._find_overlooked_risks(ticker, market_data)
        
        # 3. 데이터 신뢰성 검증
        data_issues = self._check_data_reliability(market_data)
        
        # 4. 시장의 맹점 찾기
        blind_spots = await self._identify_blind_spots(ticker, consensus_analysis)
        
        # 5. 역사적 실패 사례 검색
        historical_failures = self._search_historical_failures(ticker, consensus_analysis)
        
        # 6. 최악의 시나리오
        worst_case, worst_prob = await self._construct_worst_case(ticker, market_data)
        
        # 7. 종합 점수 계산
        skeptic_score = self._calculate_skeptic_score(
            counter_arguments,
            overlooked_risks,
            blind_spots,
            historical_failures,
            worst_prob,
        )
        
        # 8. 권고 결정
        recommendation = self._determine_recommendation(skeptic_score, consensus_confidence)
        
        return SkepticAnalysis(
            ticker=ticker,
            consensus_view=consensus_view,
            consensus_confidence=consensus_confidence,
            consensus_reasoning=consensus_reasoning,
            counter_arguments=counter_arguments,
            overlooked_risks=overlooked_risks,
            data_reliability_issues=data_issues,
            historical_failures=historical_failures,
            blind_spots=blind_spots,
            worst_case_scenario=worst_case,
            worst_case_probability=worst_prob,
            skeptic_score=skeptic_score,
            recommendation=recommendation,
        )
    
    async def _generate_counter_arguments(
        self,
        ticker: str,
        consensus: Dict,
    ) -> List[str]:
        """낙관론에 대한 반대 논거 생성"""
        arguments = []
        
        action = consensus.get("action", "HOLD")
        reasoning = consensus.get("reasoning", "")
        
        # 규칙 기반 반박
        if action == "BUY":
            arguments.append(f"'{ticker}'의 현재 주가는 이미 긍정적 기대를 반영하고 있을 가능성")
            arguments.append("상승 여력 대비 하락 위험이 비대칭적으로 큼")
            arguments.append("유사 종목 대비 밸류에이션 프리미엄이 과도할 수 있음")
        elif action == "SELL":
            arguments.append("악재가 이미 주가에 반영되어 반등 가능성")
            arguments.append("공매도 잔고 급증 시 숏커버 랠리 위험")
        
        # AI 기반 반박 (있을 경우)
        if self.ai_client:
            ai_arguments = await self._generate_ai_counter_arguments(ticker, consensus)
            arguments.extend(ai_arguments)
        
        return arguments[:5]  # 최대 5개
    
    async def _find_overlooked_risks(
        self,
        ticker: str,
        market_data: Dict = None,
    ) -> List[str]:
        """간과된 리스크 발굴"""
        risks = []
        
        # 일반적인 간과 리스크
        risks.append("매크로 환경 급변 시 상관관계 동시 상승 리스크")
        risks.append("유동성 축소 시 고밸류에이션 종목 우선 조정")
        
        if market_data:
            # 시장 데이터 기반 리스크
            pe = market_data.get("pe_ratio", 0)
            if pe and pe > 30:
                risks.append(f"P/E {pe:.1f}배: 실적 미스 시 급락 위험")
            
            short_interest = market_data.get("short_interest", 0)
            if short_interest and short_interest > 10:
                risks.append(f"공매도 비율 {short_interest:.1f}%: 부정적 시장 인식 존재")
        
        return risks
    
    def _check_data_reliability(self, market_data: Dict) -> List[str]:
        """데이터 신뢰성 검증"""
        issues = []
        
        if not market_data:
            issues.append("분석에 사용된 시장 데이터가 제한적임")
            return issues
        
        # 데이터 품질 체크
        if market_data.get("data_delay_days", 0) > 1:
            issues.append("사용된 데이터가 실시간이 아닐 수 있음")
        
        return issues
    
    async def _identify_blind_spots(
        self,
        ticker: str,
        consensus: Dict,
    ) -> List[str]:
        """시장의 맹점 찾기"""
        spots = []
        
        reasoning = consensus.get("reasoning", "").lower()
        
        # 키워드 기반 맹점 찾기
        if "growth" in reasoning or "성장" in reasoning:
            spots.extend(COMMON_BLIND_SPOTS["growth"][:2])
        
        if "value" in reasoning or "저평가" in reasoning:
            spots.extend(COMMON_BLIND_SPOTS["valuation"][:2])
        
        if "moat" in reasoning or "경쟁력" in reasoning:
            spots.extend(COMMON_BLIND_SPOTS["moat"][:2])
        
        # 기본 맹점
        if not spots:
            spots.append("'모두가 알고 있는' 정보는 이미 주가에 반영됨")
            spots.append("합의가 형성된 시점이 오히려 반전 시점일 수 있음")
        
        return spots[:5]
    
    def _search_historical_failures(
        self,
        ticker: str,
        consensus: Dict,
    ) -> List[str]:
        """유사한 합의가 틀렸던 역사적 사례"""
        failures = []
        
        reasoning = consensus.get("reasoning", "").lower()
        
        for case in HISTORICAL_FAILURES:
            # 키워드 매칭
            for keyword in case["keywords"]:
                if keyword in reasoning:
                    failures.append(
                        f"{case['case']}: '{case['consensus']}' → {case['outcome']} ({case['lesson']})"
                    )
                    break
        
        # 기본 사례
        if not failures:
            failures.append("2000년 시스코: 'IT 인프라 필수' 합의 → 80% 폭락")
            failures.append("2021년 줌비디오: '재택근무 영구화' 합의 → 70% 폭락")
        
        return failures[:3]
    
    async def _construct_worst_case(
        self,
        ticker: str,
        market_data: Dict = None,
    ) -> tuple:
        """최악의 시나리오 구성"""
        # 기본 시나리오
        worst_case = (
            f"{ticker}의 핵심 성장 동력이 예상보다 빠르게 약화되고, "
            "경쟁 심화와 매크로 악화가 동시에 발생하여 "
            "현재 주가 대비 30-50% 하락하는 시나리오"
        )
        
        # 확률 추정 (보수적)
        probability = 0.15  # 15%
        
        if market_data:
            pe = market_data.get("pe_ratio", 20)
            if pe and pe > 40:
                probability = 0.25  # 고PER이면 확률 상향
            
            beta = market_data.get("beta", 1.0)
            if beta and beta > 1.5:
                probability = min(0.35, probability + 0.1)
        
        return worst_case, probability
    
    def _calculate_skeptic_score(
        self,
        counter_arguments: List[str],
        overlooked_risks: List[str],
        blind_spots: List[str],
        historical_failures: List[str],
        worst_case_prob: float,
    ) -> float:
        """회의론적 점수 계산 (0-100)"""
        score = 30  # 기본 점수
        
        # 반박 논거 수
        score += min(20, len(counter_arguments) * 5)
        
        # 간과된 리스크 수
        score += min(15, len(overlooked_risks) * 5)
        
        # 맹점 수
        score += min(15, len(blind_spots) * 4)
        
        # 역사적 실패 사례
        score += min(10, len(historical_failures) * 4)
        
        # 최악 시나리오 확률
        score += worst_case_prob * 40
        
        return min(100, round(score, 1))
    
    def _determine_recommendation(
        self,
        skeptic_score: float,
        consensus_confidence: float,
    ) -> SkepticRecommendation:
        """권고 결정"""
        # 높은 회의론 점수 + 높은 합의 신뢰도 = 더 주의
        combined = skeptic_score + (consensus_confidence * 20)  # 과신 페널티
        
        if combined >= 80:
            return SkepticRecommendation.AVOID
        elif combined >= 50:
            return SkepticRecommendation.CAUTION
        else:
            return SkepticRecommendation.PROCEED
    
    async def _generate_ai_counter_arguments(
        self,
        ticker: str,
        consensus: Dict,
    ) -> List[str]:
        """AI를 사용한 반박 논거 생성"""
        if not self.ai_client:
            return []
        
        try:
            prompt = f"""당신은 "악마의 변호인" 역할입니다.
다음 분석에 대해 강제로 반대 논거를 찾으세요.

종목: {ticker}
시장 합의: {consensus.get('action')}
합의 근거: {consensus.get('reasoning')}

규칙:
1. 어떤 상황에서도 긍정적 의견 금지
2. 숨겨진 약점, 과대평가된 요소 찾기
3. "이미 주가에 반영됨" 논리 활용
4. 구체적인 숫자와 데이터로 반박

2가지 반대 논거를 간결하게 제시하세요:
"""
            response = await self.ai_client.generate(prompt)
            # 파싱 로직
            return []
        except Exception as e:
            logger.error(f"AI 반박 생성 실패: {e}")
            return []
    
    def format_report_korean(self, analysis: SkepticAnalysis) -> str:
        """분석 결과를 한국어 리포트로 포맷팅"""
        rec_emoji = {
            SkepticRecommendation.PROCEED: "🟢",
            SkepticRecommendation.CAUTION: "🟡",
            SkepticRecommendation.AVOID: "🔴",
        }
        
        report = f"""# 👹 악마의 변호인 리포트: {analysis.ticker}

**분석 시간**: {analysis.timestamp.strftime('%Y-%m-%d %H:%M')}

## 시장 합의

- **판단**: {analysis.consensus_view}
- **신뢰도**: {analysis.consensus_confidence:.0%}

## 반대 논거

"""
        for i, arg in enumerate(analysis.counter_arguments, 1):
            report += f"{i}. {arg}\n"
        
        report += "\n## ⚠️ 간과된 리스크\n\n"
        for risk in analysis.overlooked_risks:
            report += f"- {risk}\n"
        
        report += "\n## 👁️ 시장의 맹점\n\n"
        for spot in analysis.blind_spots:
            report += f"- {spot}\n"
        
        if analysis.historical_failures:
            report += "\n## 📚 역사적 실패 사례\n\n"
            for failure in analysis.historical_failures:
                report += f"- {failure}\n"
        
        report += f"""
## 💀 최악의 시나리오

{analysis.worst_case_scenario}

**발생 확률**: {analysis.worst_case_probability:.0%}

---

## 종합 평가

**회의론 점수**: {analysis.skeptic_score:.0f}/100
**권고**: {rec_emoji.get(analysis.recommendation, '⚪')} {analysis.recommendation.value}
"""
        
        return report
