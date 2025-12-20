"""
SEC 분석 결과 데이터 모델

Author: AI Trading System
Date: 2025-11-22
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class RiskLevel(str, Enum):
    """리스크 레벨"""
    CRITICAL = "CRITICAL"  # 0.8~1.0: 즉시 매도 고려
    HIGH = "HIGH"          # 0.6~0.8: 신중한 모니터링
    MEDIUM = "MEDIUM"      # 0.4~0.6: 일반적 수준
    LOW = "LOW"            # 0.2~0.4: 낮은 수준
    MINIMAL = "MINIMAL"    # 0.0~0.2: 최소 수준


class SentimentTone(str, Enum):
    """경영진 어조"""
    VERY_POSITIVE = "VERY_POSITIVE"      # 0.6~1.0
    POSITIVE = "POSITIVE"                # 0.2~0.6
    NEUTRAL = "NEUTRAL"                  # -0.2~0.2
    NEGATIVE = "NEGATIVE"                # -0.6~-0.2
    VERY_NEGATIVE = "VERY_NEGATIVE"      # -1.0~-0.6


class RedFlagType(str, Enum):
    """위험 신호 유형"""
    ACCOUNTING_CHANGE = "ACCOUNTING_CHANGE"      # 회계 방식 변경
    AUDITOR_CHANGE = "AUDITOR_CHANGE"            # 감사인 변경
    GOING_CONCERN = "GOING_CONCERN"              # 계속기업 의문
    RESTATEMENT = "RESTATEMENT"                  # 재무제표 재작성
    LAWSUIT = "LAWSUIT"                          # 중대 소송
    REGULATORY_ACTION = "REGULATORY_ACTION"      # 규제 조치
    INSIDER_TRADING_SPIKE = "INSIDER_TRADING"    # 내부자 거래 급증
    DEBT_COVENANT_BREACH = "DEBT_COVENANT"       # 부채 약정 위반
    MATERIAL_WEAKNESS = "MATERIAL_WEAKNESS"      # 내부통제 중대 취약점
    REVENUE_RECOGNITION = "REVENUE_RECOGNITION"  # 매출 인식 이슈


@dataclass
class RiskFactor:
    """개별 리스크 요인"""
    category: str  # 카테고리 (Market, Operational, Financial 등)
    title: str     # 리스크 제목
    description: str  # 리스크 설명 (요약)
    severity: RiskLevel
    impact_score: float  # 0.0~1.0
    likelihood_score: float  # 0.0~1.0
    is_new: bool = False  # 신규 리스크 여부 (전년 대비)
    
    @property
    def risk_score(self) -> float:
        """종합 리스크 스코어"""
        return (self.impact_score + self.likelihood_score) / 2


@dataclass
class RedFlag:
    """위험 신호"""
    flag_type: RedFlagType
    severity: RiskLevel
    description: str
    detected_in_section: str  # 어느 섹션에서 발견되었는지
    quotes: List[str] = field(default_factory=list)  # 관련 인용구
    action_required: bool = False  # 즉각 조치 필요 여부


@dataclass
class FinancialTrend:
    """재무 트렌드 분석"""
    metric: str  # revenue, net_income, eps, debt 등
    current_value: Optional[str] = None
    prior_value: Optional[str] = None
    change_percent: Optional[float] = None
    trend: str = "STABLE"  # IMPROVING, STABLE, DECLINING
    interpretation: str = ""


@dataclass
class ManagementTone:
    """경영진 어조 분석"""
    overall_sentiment: SentimentTone
    sentiment_score: float  # -1.0 (매우 부정) ~ +1.0 (매우 긍정)
    confidence_level: str  # HIGH, MEDIUM, LOW
    key_phrases: List[str] = field(default_factory=list)
    tone_change_vs_prior: Optional[str] = None  # "더 긍정적", "더 부정적", "유사"
    concerns_mentioned: List[str] = field(default_factory=list)
    opportunities_mentioned: List[str] = field(default_factory=list)


@dataclass
class SECAnalysisResult:
    """SEC 공시 분석 결과"""
    
    # 메타 정보
    ticker: str
    filing_type: str  # "10-K", "10-Q"
    fiscal_period: str
    
    # 종합 평가
    overall_risk_level: RiskLevel
    overall_risk_score: float  # 0.0~1.0
    investment_signal: str  # "BUY", "HOLD", "SELL", "AVOID"
    
    # 상세 분석
    risk_factors: List[RiskFactor] = field(default_factory=list)
    red_flags: List[RedFlag] = field(default_factory=list)
    financial_trends: List[FinancialTrend] = field(default_factory=list)
    management_tone: Optional[ManagementTone] = None
    
    # 요약
    executive_summary: str = ""  # 3-5문장 요약
    key_takeaways: List[str] = field(default_factory=list)  # 5개 핵심 포인트
    
    # AI 메타 정보
    model_used: str = "claude-sonnet-4.5"
    tokens_used: int = 0
    analysis_cost: float = 0.0  # USD
    confidence_score: float = 0.0  # 분석 신뢰도 (0.0~1.0)
    analysis_date: datetime = field(default_factory=datetime.now)
    
    def get_critical_red_flags(self) -> List[RedFlag]:
        """CRITICAL 레벨 위험 신호만 추출"""
        return [rf for rf in self.red_flags if rf.severity == RiskLevel.CRITICAL]
    
    def get_high_risks(self) -> List[RiskFactor]:
        """HIGH 이상 리스크 추출"""
        return [
            rf for rf in self.risk_factors 
            if rf.severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]
    
    def should_avoid_investment(self) -> bool:
        """투자 회피 권장 여부"""
        # CRITICAL red flags 있으면 회피
        if self.get_critical_red_flags():
            return True
        
        # Overall risk가 HIGH 이상이고 어조가 부정적
        if self.overall_risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            if self.management_tone and self.management_tone.sentiment_score < -0.3:
                return True
        
        return False
    
    def get_risk_breakdown(self) -> Dict[str, int]:
        """리스크 레벨별 개수"""
        breakdown = {level.value: 0 for level in RiskLevel}
        for risk in self.risk_factors:
            breakdown[risk.severity.value] += 1
        return breakdown
    
    def to_summary_dict(self) -> Dict:
        """요약 딕셔너리 (Trading Agent용)"""
        return {
            "ticker": self.ticker,
            "filing": f"{self.filing_type} {self.fiscal_period}",
            "overall_risk": self.overall_risk_level.value,
            "risk_score": round(self.overall_risk_score, 3),
            "signal": self.investment_signal,
            "red_flags_count": len(self.red_flags),
            "critical_red_flags": len(self.get_critical_red_flags()),
            "sentiment": self.management_tone.overall_sentiment.value if self.management_tone else "UNKNOWN",
            "should_avoid": self.should_avoid_investment(),
            "summary": self.executive_summary,
            "key_takeaways": self.key_takeaways[:3]  # 상위 3개만
        }


@dataclass
class SECAnalysisCache:
    """분석 결과 캐시 메타데이터"""
    ticker: str
    filing_type: str
    fiscal_period: str
    cached_at: datetime
    cache_key: str
    ttl_days: int = 90  # 10-K/10-Q는 분기마다만 업데이트
    
    @property
    def is_expired(self) -> bool:
        """캐시 만료 여부"""
        from datetime import timedelta
        expiry = self.cached_at + timedelta(days=self.ttl_days)
        return datetime.now() > expiry


@dataclass
class SECAnalysisRequest:
    """분석 요청"""
    ticker: str
    filing_type: str  # "10-K", "10-Q"
    force_refresh: bool = False
    max_tokens: int = 50000  # Claude 입력 토큰 제한
    include_financial_metrics: bool = True
    include_management_tone: bool = True
    include_risk_comparison: bool = False  # 전년 대비 비교 (추후 구현)


# ============================================
# 분석 컨텍스트 (Trading Agent 통합용)
# ============================================

@dataclass
class SECTradingContext:
    """Trading Agent용 SEC 컨텍스트"""
    latest_10k: Optional[SECAnalysisResult] = None
    latest_10q: Optional[SECAnalysisResult] = None
    recent_8k_flags: List[RedFlag] = field(default_factory=list)
    
    def get_current_risk_level(self) -> RiskLevel:
        """현재 리스크 레벨 (최신 공시 기준)"""
        if self.latest_10q:
            return self.latest_10q.overall_risk_level
        elif self.latest_10k:
            return self.latest_10k.overall_risk_level
        return RiskLevel.MEDIUM
    
    def has_critical_issues(self) -> bool:
        """심각한 이슈 존재 여부"""
        for analysis in [self.latest_10k, self.latest_10q]:
            if analysis and analysis.get_critical_red_flags():
                return True
        return bool(self.recent_8k_flags)
    
    def get_investment_recommendation(self) -> str:
        """투자 권장 사항"""
        if self.has_critical_issues():
            return "AVOID"
        
        current_risk = self.get_current_risk_level()
        
        if current_risk == RiskLevel.CRITICAL:
            return "SELL"
        elif current_risk == RiskLevel.HIGH:
            return "HOLD"
        elif current_risk == RiskLevel.MEDIUM:
            return "HOLD"
        else:
            return "BUY"


# ============================================
# Phase 15: CEO Speech Analysis Models
# ============================================

@dataclass
class Quote:
    """CEO 발언 Quote"""
    text: str
    quote_type: str  # "forward_looking", "risk_mention", "opportunity", "strategy"
    position: int = 0
    section: str = "MD&A"
    sentiment: Optional[float] = None  # -1.0 to 1.0


class ToneShiftDirection(str, Enum):
    """어조 변화 방향"""
    MORE_OPTIMISTIC = "MORE_OPTIMISTIC"
    SIMILAR = "SIMILAR"
    MORE_PESSIMISTIC = "MORE_PESSIMISTIC"


@dataclass
class ToneShift:
    """어조 변화 분석"""
    direction: ToneShiftDirection
    magnitude: float  # 0.0-1.0
    key_changes: List[str] = field(default_factory=list)
    signal: str = "NEUTRAL"  # "POSITIVE" | "NEUTRAL" | "NEGATIVE"
    
    @property
    def is_significant(self) -> bool:
        """유의미한 변화인지 (magnitude > 0.3)"""
        return self.magnitude > 0.3


@dataclass
class ManagementAnalysis:
    """MD&A 집중 분석 결과"""
    ticker: str
    fiscal_period: str
    ceo_quotes: List[Quote] = field(default_factory=list)
    forward_looking_count: int = 0
    tone: Optional[ManagementTone] = None
    tone_shift: Optional[ToneShift] = None
    risk_mentions: Dict[str, int] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=datetime.now)
    
    def get_optimistic_quotes(self) -> List[Quote]:
        """긍정적 발언만 추출"""
        return [q for q in self.ceo_quotes if q.sentiment and q.sentiment > 0.3]
    
    def get_pessimistic_quotes(self) -> List[Quote]:
        """부정적 발언만 추출"""
        return [q for q in self.ceo_quotes if q.sentiment and q.sentiment < -0.3]


# ============================================
# 유틸리티 함수
# ============================================

def risk_level_from_score(score: float) -> RiskLevel:
    """스코어로부터 리스크 레벨 결정"""
    if score >= 0.8:
        return RiskLevel.CRITICAL
    elif score >= 0.6:
        return RiskLevel.HIGH
    elif score >= 0.4:
        return RiskLevel.MEDIUM
    elif score >= 0.2:
        return RiskLevel.LOW
    else:
        return RiskLevel.MINIMAL


def sentiment_from_score(score: float) -> SentimentTone:
    """스코어로부터 어조 결정"""
    if score >= 0.6:
        return SentimentTone.VERY_POSITIVE
    elif score >= 0.2:
        return SentimentTone.POSITIVE
    elif score >= -0.2:
        return SentimentTone.NEUTRAL
    elif score >= -0.6:
        return SentimentTone.NEGATIVE
    else:
        return SentimentTone.VERY_NEGATIVE


def signal_from_risk(
    risk_level: RiskLevel,
    sentiment: Optional[SentimentTone],
    has_red_flags: bool
) -> str:
    """리스크/어조/레드플래그로부터 투자 신호 생성"""
    
    # Red flags 있으면 보수적
    if has_red_flags:
        return "AVOID"
    
    # 리스크 레벨 기반
    if risk_level == RiskLevel.CRITICAL:
        return "SELL"
    elif risk_level == RiskLevel.HIGH:
        return "HOLD"
    elif risk_level == RiskLevel.MEDIUM:
        # 어조 고려
        if sentiment in [SentimentTone.VERY_POSITIVE, SentimentTone.POSITIVE]:
            return "HOLD"
        elif sentiment == SentimentTone.NEUTRAL:
            return "HOLD"
        else:
            return "SELL"
    else:  # LOW, MINIMAL
        # 어조 고려
        if sentiment in [SentimentTone.VERY_POSITIVE, SentimentTone.POSITIVE]:
            return "BUY"
        elif sentiment == SentimentTone.NEUTRAL:
            return "HOLD"
        else:
            return "HOLD"
