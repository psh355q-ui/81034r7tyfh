"""
Market Moving Score Calculator - v2.3

ChatGPT/Gemini 합의 기반 뉴스 필터링
공식: Score = Impact×0.5 + Specificity×0.3 + Reliability×0.2

동적 임계값: VIX에 따라 조정
- VIX 높음 (패닉) → 임계값 높여서 '진짜 큰 뉴스'만 통과
- VIX 낮음 (안정) → 임계값 낮춰서 민감하게 반응

작성일: 2026-01-24
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketMovingScore:
    """뉴스의 시장 영향도 점수"""
    total_score: float  # 0-100
    impact_score: float  # 0-100
    specificity_score: float  # 0-100
    reliability_score: float  # 0-100
    should_include: bool  # 임계값 초과 여부
    reasoning: str
    threshold: float  # 현재 임계값


class MarketMovingScoreCalculator:
    """
    Market Moving Score 계산기
    
    동적 임계값: VIX에 따라 조정
    - VIX 높음 (패닉) → 임계값 높여서 '진짜 큰 뉴스'만 통과
    - VIX 낮음 (안정) → 임계값 낮춰서 민감하게 반응
    """
    
    # 출처별 신뢰도 점수 (0-100)
    SOURCE_RELIABILITY = {
        # 100점: 공식 소스
        'Bloomberg': 100,
        'Bloomberg Terminal': 100,
        'Reuters': 100,
        'SEC Filing': 100,
        'EDGAR': 100,
        'Federal Reserve': 100,
        'Fed': 100,
        'White House': 100,
        'U.S. Treasury': 100,
        
        # 80점: 주요 언론
        'CNBC': 80,
        'Wall Street Journal': 80,
        'WSJ': 80,
        'Financial Times': 80,
        'FT': 80,
        'AP News': 80,
        'Associated Press': 80,
        'New York Times': 80,
        'NYT': 80,
        
        # 60점: 경제지
        'MarketWatch': 60,
        'Seeking Alpha': 60,
        'Yahoo Finance': 60,
        'Barron\'s': 60,
        'Investor\'s Business Daily': 60,
        'Forbes': 60,
        
        # 40점: 커뮤니티/블로그
        'Twitter': 40,
        'X': 40,
        'Reddit': 40,
        'Medium': 40,
        'Blog': 30,
        
        # 기본값
        'default': 50
    }
    
    # 영향도 높은 키워드 (100점)
    HIGH_IMPACT_KEYWORDS = [
        # 실적/가이던스
        r'earnings (beat|miss|surprise)',
        r'guidance (raised|lowered|cut|increased)',
        r'revenue (miss|beat|surpass|exceed)',
        r'profit (warning|alert)',
        r'(eps|earnings per share) (beat|miss)',
        
        # 금리/정책
        r'fed (hike|cut|pause|hold|raise)',
        r'fomc (decision|meeting|minutes)',
        r'(rate|interest rate) (hike|cut|decision|increase|decrease)',
        r'(hawkish|dovish) (stance|pivot|shift)',
        r'(inflation|cpi|pce) (surge|spike|soar|plunge)',
        
        # M&A/규제
        r'(acquire|acquisition|merger|takeover|buyout)',
        r'(antitrust|regulation|lawsuit|investigation)',
        r'(sec|doj|ftc) (probe|investigation)',
        r'(bankruptcy|chapter 11|liquidation)',
        
        # 지정학적
        r'(war|invasion|attack|conflict)',
        r'(sanction|embargo|ban)',
        r'(tariff|trade war)',
        r'(geopolitical|security) (risk|crisis)',
        
        # 시장 구조적
        r'(market|trading) (halt|suspension)',
        r'circuit breaker',
        r'short squeeze',
        r'margin call',
        r'(flash|market) crash',
    ]
    
    # 영향도 중간 키워드 (50점)
    MEDIUM_IMPACT_KEYWORDS = [
        r'analyst (upgrade|downgrade)',
        r'price target (raised|cut|increased|lowered)',
        r'(market|stock) (rally|selloff|surge|plunge)',
        r'sector (rotation|shift)',
        r'(buy|sell) rating',
        r'(bullish|bearish) (outlook|sentiment)',
        r'(insider|institutional) (buying|selling)',
        r'share (buyback|repurchase)',
        r'dividend (increase|cut|raised)',
        r'(new|record) (high|low)',
    ]
    
    # 영향도 낮은 키워드 (20점)
    LOW_IMPACT_KEYWORDS = [
        r'(ceo|executive|insider) (sold|bought) shares',
        r'(product|service) (launch|announcement)',
        r'partnership (announced|formed)',
        r'(hiring|layoff) (announced|planned)',
        r'(conference|event) (scheduled|upcoming)',
    ]
    
    # 구체성 높은 패턴 (100점)
    HIGH_SPECIFICITY_PATTERNS = [
        r'\b[A-Z]{1,5}\b',  # 티커 심볼 (NVDA, MSFT, SPY)
        r'\$\d+(\.\d+)?[BMK]?',   # 금액 ($150.25, $5B, $10M)
        r'-?\d+(\.\d+)?%',    # 퍼센트 (5.5%, -3.2%)
        r'\d{1,3}(,\d{3})*(\.\d+)?',  # 숫자 (1,000, 5,000,000)
        r'\b(CPI|PPI|GDP|PCE|NFP|PMI|ISM|VIX|DXY|US10Y)\b',  # 경제지표
        r'\b(Fed|FOMC|ECB|BOJ|PBOC)\b',  # 중앙은행
        r'\b(Q[1-4]|FY\d{2,4})\b',  # 분기/회계연도 (Q1, Q2, FY2024)
        r'\b\d{1,2}:\d{2}\s?(AM|PM|EST|PST|UTC|KST)\b',  # 시간
    ]
    
    # 노이즈 키워드 (점수 큰 폭 감소)
    NOISE_PENALTIES = [
        (r'(may|might|could|possibly|potentially)', -20),  # 추측성
        (r'(rumor|speculation|unconfirmed)', -30),  # 루머
        (r'(opinion|commentary|thinks|believes)', -15),  # 의견
        (r'(social media|twitter|reddit) (buzz|trend)', -25),  # SNS 버즈
    ]
    
    def __init__(self, current_vix: float = 20.0):
        """
        Args:
            current_vix: 현재 VIX 값 (기본값 20.0)
        """
        self.current_vix = current_vix
        self.base_threshold = 60.0  # 기준 임계값
    
    def calculate(
        self,
        title: str,
        summary: str,
        source: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> MarketMovingScore:
        """
        뉴스의 Market Moving Score 계산
        
        Args:
            title: 뉴스 제목
            summary: 뉴스 요약
            source: 출처
            content: 본문 (선택)
            tags: 태그 (선택)
        
        Returns:
            MarketMovingScore 객체
        """
        # 텍스트 합치기
        text = f"{title} {summary}"
        if content:
            text += f" {content}"
        if tags:
            text += f" {' '.join(tags)}"
        
        text_lower = text.lower()
        
        # 1. Impact Score (50% 가중치)
        impact = self._calculate_impact(text_lower)
        
        # 2. Specificity Score (30% 가중치)
        specificity = self._calculate_specificity(text)
        
        # 3. Reliability Score (20% 가중치)
        reliability = self._get_source_reliability(source)
        
        # 노이즈 페널티 적용
        penalty = self._calculate_noise_penalty(text_lower)
        
        # 가중 평균 + 페널티
        total = max(0, (impact * 0.5 + specificity * 0.3 + reliability * 0.2) + penalty)
        
        # 동적 임계값 계산
        threshold = self._get_dynamic_threshold()
        
        # 판정
        should_include = total >= threshold
        
        return MarketMovingScore(
            total_score=round(total, 1),
            impact_score=round(impact, 1),
            specificity_score=round(specificity, 1),
            reliability_score=round(reliability, 1),
            should_include=should_include,
            threshold=round(threshold, 1),
            reasoning=self._generate_reasoning(
                impact, specificity, reliability, penalty, threshold, should_include
            )
        )
    
    def _calculate_impact(self, text: str) -> float:
        """
        영향도 점수 계산 (0-100)
        
        HIGH 키워드 매칭: 100점
        MEDIUM 키워드 매칭: 50점
        LOW 키워드 매칭: 20점
        기본값: 10점
        """
        # HIGH 키워드 매칭
        for pattern in self.HIGH_IMPACT_KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.debug(f"HIGH impact pattern matched: {pattern}")
                return 100.0
        
        # MEDIUM 키워드 매칭
        for pattern in self.MEDIUM_IMPACT_KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.debug(f"MEDIUM impact pattern matched: {pattern}")
                return 50.0
        
        # LOW 키워드 매칭
        for pattern in self.LOW_IMPACT_KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.debug(f"LOW impact pattern matched: {pattern}")
                return 20.0
        
        return 10.0
    
    def _calculate_specificity(self, text: str) -> float:
        """
        구체성 점수 계산 (0-100)
        
        매칭 수에 따라 점수:
        - 5개 이상: 100점
        - 3-4개: 80점
        - 2개: 60점
        - 1개: 40점
        - 0개: 10점
        """
        matches = 0
        matched_patterns = []
        
        for pattern in self.HIGH_SPECIFICITY_PATTERNS:
            if re.search(pattern, text):
                matches += 1
                matched_patterns.append(pattern)
        
        if matches >= 5:
            score = 100.0
        elif matches >= 3:
            score = 80.0
        elif matches >= 2:
            score = 60.0
        elif matches >= 1:
            score = 40.0
        else:
            score = 10.0
        
        logger.debug(f"Specificity: {matches} patterns matched → {score} points")
        return score
    
    def _get_source_reliability(self, source: str) -> float:
        """
        출처 신뢰도 점수 (0-100)
        """
        # 정확히 일치하는 출처 찾기
        for key, value in self.SOURCE_RELIABILITY.items():
            if key.lower() in source.lower():
                logger.debug(f"Source '{source}' matched to '{key}' → {value} points")
                return value
        
        # 기본값
        default = self.SOURCE_RELIABILITY['default']
        logger.debug(f"Source '{source}' not matched → default {default} points")
        return default
    
    def _calculate_noise_penalty(self, text: str) -> float:
        """
        노이즈 페널티 계산
        
        추측성, 루머, 의견 등의 표현이 있으면 감점
        """
        total_penalty = 0.0
        
        for pattern, penalty in self.NOISE_PENALTIES:
            if re.search(pattern, text, re.IGNORECASE):
                total_penalty += penalty
                logger.debug(f"Noise pattern '{pattern}' → {penalty} penalty")
        
        return total_penalty
    
    def _get_dynamic_threshold(self) -> float:
        """
        VIX 기반 동적 임계값
        
        - VIX 20 (기준) → threshold = 60
        - VIX 30 (패닉) → threshold = 75 (중요한 뉴스만)
        - VIX 12 (안정) → threshold = 48 (민감하게)
        
        공식: threshold = base_threshold + (VIX - 20) × 1.5
        범위: 30 ~ 90
        """
        adjustment = (self.current_vix - 20) * 1.5
        threshold = self.base_threshold + adjustment
        
        # 범위 제한
        threshold = max(30, min(90, threshold))
        
        logger.debug(
            f"Dynamic threshold: VIX={self.current_vix:.1f} → "
            f"adjustment={adjustment:+.1f} → threshold={threshold:.1f}"
        )
        
        return threshold
    
    def _generate_reasoning(
        self,
        impact: float,
        specificity: float,
        reliability: float,
        penalty: float,
        threshold: float,
        should_include: bool
    ) -> str:
        """점수 근거 생성"""
        
        # 가중 평균 계산 과정
        weighted_sum = impact * 0.5 + specificity * 0.3 + reliability * 0.2
        total = max(0, weighted_sum + penalty)
        
        parts = [
            f"Impact={impact:.0f}×0.5",
            f"Specificity={specificity:.0f}×0.3",
            f"Reliability={reliability:.0f}×0.2",
        ]
        
        if penalty != 0:
            parts.append(f"Penalty={penalty:+.0f}")
        
        calculation = " + ".join(parts)
        
        decision = "✅ INCLUDE" if should_include else "❌ EXCLUDE"
        
        return (
            f"{calculation} = {total:.1f} | "
            f"Threshold={threshold:.1f} (VIX={self.current_vix:.1f}) | "
            f"{decision}"
        )
    
    def bulk_score(
        self,
        news_list: List[Dict[str, Any]],
        vix: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        뉴스 목록 일괄 점수 계산
        
        Args:
            news_list: 뉴스 딕셔너리 리스트
                [{"title": "...", "summary": "...", "source": "...", ...}, ...]
            vix: VIX 값 (None이면 self.current_vix 사용)
        
        Returns:
            점수 정보가 추가된 뉴스 리스트
        """
        if vix is not None:
            self.current_vix = vix
        
        scored_news = []
        for news in news_list:
            score = self.calculate(
                title=news.get('title', ''),
                summary=news.get('summary', ''),
                source=news.get('source', ''),
                content=news.get('content'),
                tags=news.get('tags')
            )
            
            # 원본 뉴스에 점수 정보 추가
            news_with_score = news.copy()
            news_with_score['market_moving_score'] = score.total_score
            news_with_score['impact_score'] = score.impact_score
            news_with_score['specificity_score'] = score.specificity_score
            news_with_score['reliability_score'] = score.reliability_score
            news_with_score['should_include'] = score.should_include
            news_with_score['score_reasoning'] = score.reasoning
            
            scored_news.append(news_with_score)
        
        # 점수 순으로 정렬
        scored_news.sort(key=lambda x: x['market_moving_score'], reverse=True)
        
        logger.info(
            f"Bulk scored {len(news_list)} news items. "
            f"Included: {sum(1 for n in scored_news if n['should_include'])}"
        )
        
        return scored_news


# ============================================================================
# Helper Functions
# ============================================================================

def filter_market_moving_news(
    news_list: List[Dict[str, Any]],
    vix: float = 20.0
) -> List[Dict[str, Any]]:
    """
    시장 영향 뉴스만 필터링 (편의 함수)
    
    Args:
        news_list: 뉴스 리스트
        vix: VIX 값
    
    Returns:
        should_include=True인 뉴스만 반환
    """
    calculator = MarketMovingScoreCalculator(current_vix=vix)
    scored = calculator.bulk_score(news_list, vix=vix)
    return [n for n in scored if n['should_include']]


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Market Moving Score Calculator Test")
    print("=" * 60)
    
    # 테스트 뉴스
    test_news = [
        {
            "title": "NVDA Earnings Beat Expectations at $5.5B Revenue",
            "summary": "NVIDIA reported Q4 earnings of $5.53 per share, beating analyst expectations of $4.92. Revenue surged 265% YoY.",
            "source": "Bloomberg",
        },
        {
            "title": "CEO of Small Tech Company Sold 100 Shares",
            "summary": "The CEO sold a small amount of shares for personal reasons.",
            "source": "Blog",
        },
        {
            "title": "Fed May Consider Rate Cut in Future Meetings",
            "summary": "Analysts speculate that the Fed might potentially cut rates later this year.",
            "source": "Twitter",
        },
        {
            "title": "Market Rally Continues as SPY Hits New Record",
            "summary": "S&P 500 ETF (SPY) closed at $520.50, up 1.2% amid strong earnings season.",
            "source": "CNBC",
        }
    ]
    
    # VIX 20 (정상)
    print("\n[VIX = 20.0 (Normal Market)]")
    print("-" * 60)
    calculator = MarketMovingScoreCalculator(current_vix=20.0)
    
    for i, news in enumerate(test_news, 1):
        score = calculator.calculate(
            title=news['title'],
            summary=news['summary'],
            source=news['source']
        )
        
        print(f"\n{i}. {news['title'][:50]}...")
        print(f"   Source: {news['source']}")
        print(f"   Total Score: {score.total_score} (Threshold: {score.threshold})")
        print(f"   Impact: {score.impact_score}, Specificity: {score.specificity_score}, Reliability: {score.reliability_score}")
        print(f"   Decision: {'✅ INCLUDE' if score.should_include else '❌ EXCLUDE'}")
        print(f"   Reasoning: {score.reasoning}")
    
    # VIX 30 (패닉)
    print("\n\n[VIX = 30.0 (Panic Mode)]")
    print("-" * 60)
    calculator_panic = MarketMovingScoreCalculator(current_vix=30.0)
    
    score = calculator_panic.calculate(
        title=test_news[0]['title'],
        summary=test_news[0]['summary'],
        source=test_news[0]['source']
    )
    
    print(f"뉴스: {test_news[0]['title'][:50]}...")
    print(f"Total Score: {score.total_score} (Threshold: {score.threshold})")
    print(f"Decision: {'✅ INCLUDE' if score.should_include else '❌ EXCLUDE'}")
    
    # Bulk scoring
    print("\n\n[Bulk Scoring Test]")
    print("-" * 60)
    scored = calculator.bulk_score(test_news)
    
    included = [n for n in scored if n['should_include']]
    print(f"Total: {len(scored)}, Included: {len(included)}")
    print("\nIncluded news:")
    for n in included:
        print(f"  - {n['title'][:60]}... (Score: {n['market_moving_score']:.1f})")
