"""
Theme Risk Detector - 테마주/찌라시 리스크 탐지

Phase F3: 한국 시장 특수 리스크

정치테마주, 찌라시, 선반영 구조를 정량적으로 감지

ThemeRiskScore 구성:
- PriceSpikeScore: 1일 +20% → +30점
- VolumeSpikeScore: 5일 평균 400% → +25점
- No-DART-News Penalty: 공시 미존재 → +30점
- CommunitySource Weight: 커뮤니티 출처 → +20점
- PoliticalKeyword: 정치 키워드 → +15점

70점 이상: 자동 경고
85점 이상: 매수 금지 / 포지션 축소

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 리스크 레벨 및 스키마
# ═══════════════════════════════════════════════════════════════

class ThemeRiskLevel(str, Enum):
    """테마주 리스크 레벨"""
    SAFE = "safe"           # 0-40
    CAUTION = "caution"     # 40-70
    WARNING = "warning"     # 70-85
    DANGER = "danger"       # 85-100


class RiskAction(str, Enum):
    """권장 조치"""
    NORMAL = "normal"           # 정상 거래
    MONITOR = "monitor"         # 모니터링 강화
    REDUCE = "reduce"           # 포지션 축소
    AVOID = "avoid"             # 매수 금지
    SELL_IMMEDIATELY = "sell_immediately"  # 즉시 매도


@dataclass
class PriceVolumeData:
    """가격/거래량 데이터"""
    ticker: str
    current_price: float
    prev_close: float
    avg_volume_5d: float
    current_volume: float
    price_change_1d: float  # %
    price_change_5d: float  # %
    volume_ratio: float  # 현재/5일평균
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "current_price": self.current_price,
            "prev_close": self.prev_close,
            "price_change_1d": self.price_change_1d,
            "price_change_5d": self.price_change_5d,
            "volume_ratio": self.volume_ratio
        }


@dataclass
class NewsAnalysis:
    """뉴스 분석 결과"""
    has_official_news: bool  # DART 공시 존재
    has_ir_announcement: bool  # IR 발표 존재
    community_mentions: int  # 커뮤니티 언급 수
    political_keywords_found: List[str]
    rumor_indicators: List[str]
    news_sources: List[str]  # 뉴스 출처 목록
    credibility_score: float  # 0-1


@dataclass
class ThemeRiskScore:
    """테마주 리스크 점수"""
    ticker: str
    total_score: float  # 0-100
    risk_level: ThemeRiskLevel
    recommended_action: RiskAction
    
    # 개별 점수
    price_spike_score: float
    volume_spike_score: float
    no_dart_penalty: float
    community_source_score: float
    political_keyword_score: float
    
    # 상세 정보
    factors: List[str]
    warnings: List[str]
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "total_score": self.total_score,
            "risk_level": self.risk_level.value,
            "recommended_action": self.recommended_action.value,
            "scores": {
                "price_spike": self.price_spike_score,
                "volume_spike": self.volume_spike_score,
                "no_dart_penalty": self.no_dart_penalty,
                "community_source": self.community_source_score,
                "political_keyword": self.political_keyword_score
            },
            "factors": self.factors,
            "warnings": self.warnings,
            "calculated_at": self.calculated_at.isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# Theme Risk Detector 클래스
# ═══════════════════════════════════════════════════════════════

class ThemeRiskDetector:
    """
    테마주 리스크 탐지기
    
    Usage:
        detector = ThemeRiskDetector()
        
        # 가격/거래량 데이터로 분석
        price_data = PriceVolumeData(
            ticker="005930",
            current_price=75000,
            prev_close=62500,  # 20% 급등
            avg_volume_5d=1000000,
            current_volume=5000000,  # 500% 거래량
            price_change_1d=20.0,
            price_change_5d=35.0,
            volume_ratio=5.0
        )
        
        news = NewsAnalysis(
            has_official_news=False,
            has_ir_announcement=False,
            community_mentions=150,
            political_keywords_found=["대선", "관련주"],
            ...
        )
        
        score = detector.analyze(price_data, news)
        if score.risk_level == ThemeRiskLevel.DANGER:
            # 매수 금지
    """
    
    # 점수 임계값
    PRICE_SPIKE_THRESHOLD = 20.0   # 1일 +20%
    VOLUME_SPIKE_THRESHOLD = 4.0   # 5일 평균 400%
    
    # 점수 배점
    PRICE_SPIKE_MAX = 30
    VOLUME_SPIKE_MAX = 25
    NO_DART_MAX = 30
    COMMUNITY_SOURCE_MAX = 20
    POLITICAL_KEYWORD_MAX = 15
    
    # 리스크 레벨 기준
    CAUTION_THRESHOLD = 40
    WARNING_THRESHOLD = 70
    DANGER_THRESHOLD = 85
    
    # 정치 키워드
    POLITICAL_KEYWORDS_KR = [
        "대선", "총선", "대통령", "국회", "정치",
        "윤석열", "이재명", "한동훈", "조국",
        "더불어민주당", "국민의힘", "민주당", "여당", "야당",
        "관련주", "테마주", "수혜주", "대장주",
        "탄핵", "특검", "검찰", "청와대", "대선후보"
    ]
    
    # 루머 지표 키워드
    RUMOR_KEYWORDS = [
        "찌라시", "루머", "소문", "카더라", "떡밥",
        "급등예고", "상한가", "작전주", "세력",
        "텔레그램", "리딩방", "비밀", "극비", "내부정보"
    ]
    
    # 신뢰도 낮은 출처
    LOW_CREDIBILITY_SOURCES = [
        "디시인사이드", "클리앙", "FM코리아", "인스티즈",
        "네이트판", "더쿠", "mlbpark", "에펨코리아",
        "개인블로그", "유튜브", "텔레그램"
    ]
    
    def __init__(self):
        """초기화"""
        self._cache: Dict[str, ThemeRiskScore] = {}
        self._history: List[ThemeRiskScore] = []
        
        logger.info("ThemeRiskDetector initialized")
    
    def analyze(
        self,
        price_data: PriceVolumeData,
        news_analysis: Optional[NewsAnalysis] = None
    ) -> ThemeRiskScore:
        """
        테마주 리스크 분석
        
        Args:
            price_data: 가격/거래량 데이터
            news_analysis: 뉴스 분석 결과 (선택)
            
        Returns:
            ThemeRiskScore
        """
        ticker = price_data.ticker
        factors = []
        warnings = []
        
        # 1. 가격 급등 점수
        price_spike_score = self._calculate_price_spike_score(
            price_data.price_change_1d,
            price_data.price_change_5d
        )
        if price_spike_score > 0:
            factors.append(f"1일 {price_data.price_change_1d:.1f}% 급등")
            if price_spike_score >= self.PRICE_SPIKE_MAX * 0.8:
                warnings.append("급격한 가격 상승")
        
        # 2. 거래량 급증 점수
        volume_spike_score = self._calculate_volume_spike_score(
            price_data.volume_ratio
        )
        if volume_spike_score > 0:
            factors.append(f"거래량 {price_data.volume_ratio:.1f}배")
            if volume_spike_score >= self.VOLUME_SPIKE_MAX * 0.8:
                warnings.append("비정상적 거래량")
        
        # 3-5. 뉴스 기반 점수
        no_dart_penalty = 0.0
        community_source_score = 0.0
        political_keyword_score = 0.0
        
        if news_analysis:
            # 3. DART 공시 없음
            no_dart_penalty = self._calculate_no_dart_penalty(news_analysis)
            if no_dart_penalty > 0:
                factors.append("공식 공시 미확인")
                warnings.append("DART 공시 없이 급등")
            
            # 4. 커뮤니티 출처
            community_source_score = self._calculate_community_score(news_analysis)
            if community_source_score > 0:
                factors.append(f"커뮤니티 언급 {news_analysis.community_mentions}건")
            
            # 5. 정치 키워드
            political_keyword_score = self._calculate_political_score(news_analysis)
            if political_keyword_score > 0:
                factors.append(f"정치 키워드: {', '.join(news_analysis.political_keywords_found[:3])}")
                warnings.append("정치테마주 의심")
        else:
            # 뉴스 분석 없으면 가격/거래량 기반으로만 의심 점수 부여
            if price_spike_score > 20 and volume_spike_score > 15:
                no_dart_penalty = 15  # 뉴스 확인 안됨 패널티
                factors.append("뉴스 분석 필요")
        
        # 총점 계산
        total_score = (
            price_spike_score +
            volume_spike_score +
            no_dart_penalty +
            community_source_score +
            political_keyword_score
        )
        total_score = min(100, total_score)  # 최대 100점
        
        # 리스크 레벨 결정
        risk_level = self._determine_risk_level(total_score)
        
        # 권장 조치 결정
        recommended_action = self._determine_action(total_score, risk_level, warnings)
        
        score = ThemeRiskScore(
            ticker=ticker,
            total_score=total_score,
            risk_level=risk_level,
            recommended_action=recommended_action,
            price_spike_score=price_spike_score,
            volume_spike_score=volume_spike_score,
            no_dart_penalty=no_dart_penalty,
            community_source_score=community_source_score,
            political_keyword_score=political_keyword_score,
            factors=factors,
            warnings=warnings
        )
        
        # 캐시 및 히스토리 저장
        self._cache[ticker] = score
        self._history.append(score)
        
        logger.info(
            f"Theme risk for {ticker}: {total_score:.1f} ({risk_level.value}) "
            f"-> {recommended_action.value}"
        )
        
        return score
    
    def _calculate_price_spike_score(
        self,
        change_1d: float,
        change_5d: float
    ) -> float:
        """가격 급등 점수 계산"""
        score = 0.0
        
        # 1일 급등
        if change_1d >= self.PRICE_SPIKE_THRESHOLD:
            # 20% → 30점, 30% → 45점 (비선형)
            ratio = change_1d / self.PRICE_SPIKE_THRESHOLD
            score = min(self.PRICE_SPIKE_MAX * 1.5, self.PRICE_SPIKE_MAX * ratio)
        elif change_1d >= 10:
            # 10-20% → 비례 점수
            score = (change_1d / self.PRICE_SPIKE_THRESHOLD) * self.PRICE_SPIKE_MAX
        
        # 5일 급등 보너스
        if change_5d >= 50:
            score += 10
        elif change_5d >= 30:
            score += 5
        
        return min(self.PRICE_SPIKE_MAX * 1.5, score)  # 최대 45점
    
    def _calculate_volume_spike_score(self, volume_ratio: float) -> float:
        """거래량 급증 점수 계산"""
        score = 0.0
        
        if volume_ratio >= self.VOLUME_SPIKE_THRESHOLD:
            # 400% → 25점, 800% → 37.5점
            ratio = volume_ratio / self.VOLUME_SPIKE_THRESHOLD
            score = min(self.VOLUME_SPIKE_MAX * 1.5, self.VOLUME_SPIKE_MAX * ratio)
        elif volume_ratio >= 2.0:
            # 200-400% → 비례 점수
            score = ((volume_ratio - 2.0) / 2.0) * self.VOLUME_SPIKE_MAX
        
        return min(self.VOLUME_SPIKE_MAX * 1.5, score)  # 최대 37.5점
    
    def _calculate_no_dart_penalty(self, news: NewsAnalysis) -> float:
        """DART 공시 없음 패널티"""
        if news.has_official_news or news.has_ir_announcement:
            return 0.0
        
        # 공식 뉴스 없으면 패널티
        penalty = self.NO_DART_MAX
        
        # 공신력 있는 출처가 있으면 감소
        if news.credibility_score > 0.7:
            penalty *= 0.5
        elif news.credibility_score > 0.5:
            penalty *= 0.7
        
        return penalty
    
    def _calculate_community_score(self, news: NewsAnalysis) -> float:
        """커뮤니티 출처 점수"""
        score = 0.0
        
        # 커뮤니티 언급 수
        if news.community_mentions >= 100:
            score += self.COMMUNITY_SOURCE_MAX
        elif news.community_mentions >= 50:
            score += self.COMMUNITY_SOURCE_MAX * 0.7
        elif news.community_mentions >= 20:
            score += self.COMMUNITY_SOURCE_MAX * 0.4
        
        # 루머 지표 발견
        if news.rumor_indicators:
            score += len(news.rumor_indicators) * 3
        
        # 저신뢰 출처 비율
        low_cred_count = sum(
            1 for src in news.news_sources
            if any(lc in src.lower() for lc in self.LOW_CREDIBILITY_SOURCES)
        )
        if low_cred_count > 0 and news.news_sources:
            ratio = low_cred_count / len(news.news_sources)
            score += ratio * 10
        
        return min(self.COMMUNITY_SOURCE_MAX * 1.5, score)
    
    def _calculate_political_score(self, news: NewsAnalysis) -> float:
        """정치 키워드 점수"""
        if not news.political_keywords_found:
            return 0.0
        
        # 키워드 수에 따른 점수
        keyword_count = len(news.political_keywords_found)
        
        if keyword_count >= 5:
            score = self.POLITICAL_KEYWORD_MAX
        elif keyword_count >= 3:
            score = self.POLITICAL_KEYWORD_MAX * 0.8
        elif keyword_count >= 1:
            score = self.POLITICAL_KEYWORD_MAX * 0.5
        else:
            score = 0.0
        
        return score
    
    def _determine_risk_level(self, total_score: float) -> ThemeRiskLevel:
        """리스크 레벨 결정"""
        if total_score >= self.DANGER_THRESHOLD:
            return ThemeRiskLevel.DANGER
        elif total_score >= self.WARNING_THRESHOLD:
            return ThemeRiskLevel.WARNING
        elif total_score >= self.CAUTION_THRESHOLD:
            return ThemeRiskLevel.CAUTION
        else:
            return ThemeRiskLevel.SAFE
    
    def _determine_action(
        self,
        total_score: float,
        risk_level: ThemeRiskLevel,
        warnings: List[str]
    ) -> RiskAction:
        """권장 조치 결정"""
        if risk_level == ThemeRiskLevel.DANGER:
            if total_score >= 95:
                return RiskAction.SELL_IMMEDIATELY
            return RiskAction.AVOID
        elif risk_level == ThemeRiskLevel.WARNING:
            return RiskAction.REDUCE
        elif risk_level == ThemeRiskLevel.CAUTION:
            return RiskAction.MONITOR
        else:
            return RiskAction.NORMAL
    
    def quick_check(
        self,
        ticker: str,
        price_change_1d: float,
        volume_ratio: float
    ) -> Tuple[bool, str]:
        """
        빠른 위험 체크 (가격/거래량만)
        
        Returns:
            (is_risky, reason)
        """
        if price_change_1d >= 25 and volume_ratio >= 5:
            return True, "급등+폭증 (확인 필요)"
        elif price_change_1d >= 30:
            return True, "극심한 급등"
        elif volume_ratio >= 10:
            return True, "극심한 거래량"
        elif price_change_1d >= 20 and volume_ratio >= 3:
            return True, "테마주 의심"
        
        return False, "정상"
    
    def get_cached_score(self, ticker: str) -> Optional[ThemeRiskScore]:
        """캐시된 점수 조회"""
        return self._cache.get(ticker)
    
    def get_high_risk_tickers(
        self,
        min_level: ThemeRiskLevel = ThemeRiskLevel.WARNING
    ) -> List[ThemeRiskScore]:
        """고위험 종목 목록"""
        threshold = {
            ThemeRiskLevel.CAUTION: self.CAUTION_THRESHOLD,
            ThemeRiskLevel.WARNING: self.WARNING_THRESHOLD,
            ThemeRiskLevel.DANGER: self.DANGER_THRESHOLD
        }[min_level]
        
        return [
            score for score in self._cache.values()
            if score.total_score >= threshold
        ]
    
    def scan_text_for_risk(self, text: str) -> Dict[str, Any]:
        """
        텍스트에서 리스크 신호 스캔
        
        Args:
            text: 뉴스/게시글 텍스트
            
        Returns:
            리스크 신호 분석 결과
        """
        text_lower = text.lower()
        
        # 정치 키워드 검색
        political_found = [
            kw for kw in self.POLITICAL_KEYWORDS_KR
            if kw in text
        ]
        
        # 루머 키워드 검색
        rumor_found = [
            kw for kw in self.RUMOR_KEYWORDS
            if kw in text
        ]
        
        # 위험 점수 계산
        risk_score = (
            len(political_found) * 3 +
            len(rumor_found) * 5
        )
        
        return {
            "political_keywords": political_found,
            "rumor_keywords": rumor_found,
            "risk_score": risk_score,
            "is_risky": risk_score >= 10
        }


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_theme_risk_detector: Optional[ThemeRiskDetector] = None


def get_theme_risk_detector() -> ThemeRiskDetector:
    """ThemeRiskDetector 싱글톤 인스턴스"""
    global _theme_risk_detector
    if _theme_risk_detector is None:
        _theme_risk_detector = ThemeRiskDetector()
    return _theme_risk_detector


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    detector = ThemeRiskDetector()
    
    print("=== Theme Risk Detector Test ===\n")
    
    # 테스트 케이스 1: 정상 종목
    print("Case 1: Normal Stock")
    price1 = PriceVolumeData(
        ticker="005930",
        current_price=75000,
        prev_close=74000,
        avg_volume_5d=1000000,
        current_volume=1200000,
        price_change_1d=1.35,
        price_change_5d=3.5,
        volume_ratio=1.2
    )
    score1 = detector.analyze(price1)
    print(f"  Score: {score1.total_score:.1f}")
    print(f"  Level: {score1.risk_level.value}")
    print(f"  Action: {score1.recommended_action.value}")
    
    # 테스트 케이스 2: 급등 + 거래량 폭증
    print("\nCase 2: Suspicious Stock (급등+폭증)")
    price2 = PriceVolumeData(
        ticker="123456",
        current_price=15000,
        prev_close=12500,
        avg_volume_5d=500000,
        current_volume=3000000,
        price_change_1d=20.0,
        price_change_5d=45.0,
        volume_ratio=6.0
    )
    news2 = NewsAnalysis(
        has_official_news=False,
        has_ir_announcement=False,
        community_mentions=80,
        political_keywords_found=["대선", "관련주"],
        rumor_indicators=["찌라시", "급등예고"],
        news_sources=["디시인사이드", "개인블로그"],
        credibility_score=0.2
    )
    score2 = detector.analyze(price2, news2)
    print(f"  Score: {score2.total_score:.1f}")
    print(f"  Level: {score2.risk_level.value}")
    print(f"  Action: {score2.recommended_action.value}")
    print(f"  Factors: {score2.factors}")
    print(f"  Warnings: {score2.warnings}")
    
    # 테스트 케이스 3: 정치테마주
    print("\nCase 3: Political Theme Stock")
    price3 = PriceVolumeData(
        ticker="999999",
        current_price=8000,
        prev_close=5000,
        avg_volume_5d=100000,
        current_volume=2000000,
        price_change_1d=60.0,
        price_change_5d=120.0,
        volume_ratio=20.0
    )
    news3 = NewsAnalysis(
        has_official_news=False,
        has_ir_announcement=False,
        community_mentions=500,
        political_keywords_found=["대선", "윤석열", "이재명", "대장주", "수혜주"],
        rumor_indicators=["작전주", "세력", "텔레그램"],
        news_sources=["디시인사이드", "FM코리아", "텔레그램"],
        credibility_score=0.1
    )
    score3 = detector.analyze(price3, news3)
    print(f"  Score: {score3.total_score:.1f}")
    print(f"  Level: {score3.risk_level.value}")
    print(f"  Action: {score3.recommended_action.value}")
    print(f"  Factors: {score3.factors}")
