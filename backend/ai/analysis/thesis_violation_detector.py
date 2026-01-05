"""
Thesis Violation Detector - Investment Thesis Monitoring for Long-Term Investors

Phase: Phase 4.2 - Grand Unified Strategy (Core Features)
Date: 2026-01-05

Purpose:
    장기 투자자를 위한 '투자 아이디어(Thesis) 훼손' 감지 시스템.
    가격이 떨어져서 파는 게 아니라, **투자의 근거가 무너졌을 때** 알림.

Key Violations Detected:
    1. 경쟁 우위 훼손: 시장 점유율 2분기 연속 하락
    2. BM 훼손: 영업이익률(OPM) 구조적 하락
    3. 경영진 리스크: CEO/Insider 대량 매도
    4. 배당 정책 변경: 배당 삭감 또는 중단
    5. 부채 급증: 부채비율 급격한 상승

Usage:
    detector = ThesisViolationDetector()
    result = detector.check_thesis(ticker="AAPL", thesis_type="moat", fundamental_data={...})
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ThesisType(str, Enum):
    """투자 아이디어 유형"""
    MOAT = "moat"                   # 경쟁 우위 기반
    GROWTH = "growth"               # 성장성 기반
    DIVIDEND = "dividend"           # 배당 성장 기반
    VALUE = "value"                 # 저평가 기반
    TURNAROUND = "turnaround"       # 턴어라운드 기반


class ViolationType(str, Enum):
    """위반 유형"""
    MARKET_SHARE_DECLINE = "market_share_decline"
    MARGIN_DETERIORATION = "margin_deterioration"
    INSIDER_SELLING = "insider_selling"
    DIVIDEND_CUT = "dividend_cut"
    DEBT_SURGE = "debt_surge"
    MANAGEMENT_CHANGE = "management_change"
    COMPETITIVE_THREAT = "competitive_threat"
    REGULATORY_RISK = "regulatory_risk"


class ViolationSeverity(str, Enum):
    """위반 심각도"""
    WATCH = "watch"         # 관찰 필요
    WARNING = "warning"     # 경고 (검토 권장)
    CRITICAL = "critical"   # 심각 (즉시 검토 필요)


@dataclass
class ThesisViolation:
    """투자 아이디어 위반 상세"""
    violation_type: ViolationType
    severity: ViolationSeverity
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class ThesisCheckResult:
    """투자 아이디어 검증 결과"""
    ticker: str
    thesis_type: ThesisType
    thesis_intact: bool                          # 투자 아이디어 유효 여부
    violations: List[ThesisViolation]            # 감지된 위반 목록
    recommendation: str                          # 권장 행동
    confidence: float                            # 판단 신뢰도 (0-1)
    checked_at: datetime = field(default_factory=datetime.now)


class ThesisViolationDetector:
    """
    Thesis Violation Detector - 투자 아이디어 훼손 감지기
    
    장기 투자자에게 "가격 하락"이 아닌 "투자 근거 붕괴"를 알립니다.
    """
    
    # 위반 감지 임계값
    THRESHOLDS = {
        "market_share_decline_pct": -5.0,     # 점유율 5% 이상 하락
        "margin_decline_quarters": 2,          # 2분기 연속 마진 하락
        "margin_decline_threshold": -3.0,      # 마진 3%p 이상 하락
        "insider_selling_pct": 10.0,          # 10% 이상 내부자 매도
        "dividend_cut_pct": -20.0,            # 배당 20% 이상 삭감
        "debt_ratio_increase_pct": 50.0,      # 부채비율 50% 이상 상승
        "minimum_data_quarters": 4,            # 최소 4분기 데이터 필요
    }
    
    def __init__(self, custom_thresholds: Optional[Dict[str, float]] = None):
        """
        Args:
            custom_thresholds: 커스텀 임계값 (기본값 오버라이드)
        """
        self.thresholds = {**self.THRESHOLDS, **(custom_thresholds or {})}
    
    def check_thesis(
        self,
        ticker: str,
        thesis_type: str,
        fundamental_data: Dict[str, Any],
        news_events: Optional[List[Dict[str, Any]]] = None
    ) -> ThesisCheckResult:
        """
        투자 아이디어 위반 검사 (Master Method)
        
        Args:
            ticker: 종목 티커
            thesis_type: 투자 아이디어 유형 (moat, growth, dividend, value, turnaround)
            fundamental_data: 재무제표 데이터
                {
                    "market_share_history": [{"quarter": "Q1", "share": 25.0}, ...],
                    "operating_margin_history": [{"quarter": "Q1", "margin": 20.0}, ...],
                    "dividend_history": [{"year": 2025, "dividend": 3.5}, ...],
                    "debt_to_equity_history": [{"quarter": "Q1", "ratio": 0.5}, ...],
                    "insider_transactions": [{"type": "sell", "shares": 50000, "pct": 5.0}, ...]
                }
            news_events: 관련 뉴스 이벤트 (경영진 변경, 규제 등)
        
        Returns:
            ThesisCheckResult: 검증 결과
        """
        thesis_enum = ThesisType(thesis_type.lower())
        violations: List[ThesisViolation] = []
        
        # 1. 시장 점유율 체크 (Moat, Growth)
        if thesis_enum in [ThesisType.MOAT, ThesisType.GROWTH]:
            ms_violation = self._check_market_share(fundamental_data.get("market_share_history", []))
            if ms_violation:
                violations.append(ms_violation)
        
        # 2. 마진 체크 (Moat, Value)
        if thesis_enum in [ThesisType.MOAT, ThesisType.VALUE]:
            margin_violation = self._check_margin_trend(fundamental_data.get("operating_margin_history", []))
            if margin_violation:
                violations.append(margin_violation)
        
        # 3. 배당 체크 (Dividend)
        if thesis_enum == ThesisType.DIVIDEND:
            dividend_violation = self._check_dividend(fundamental_data.get("dividend_history", []))
            if dividend_violation:
                violations.append(dividend_violation)
        
        # 4. 내부자 매도 체크 (All)
        insider_violation = self._check_insider_selling(fundamental_data.get("insider_transactions", []))
        if insider_violation:
            violations.append(insider_violation)
        
        # 5. 부채 비율 체크 (All)
        debt_violation = self._check_debt_surge(fundamental_data.get("debt_to_equity_history", []))
        if debt_violation:
            violations.append(debt_violation)
        
        # 6. 뉴스 기반 경영진/규제 리스크 체크
        if news_events:
            news_violations = self._check_news_events(news_events)
            violations.extend(news_violations)
        
        # 결과 판정
        critical_count = sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL)
        warning_count = sum(1 for v in violations if v.severity == ViolationSeverity.WARNING)
        
        thesis_intact = critical_count == 0 and warning_count <= 1
        
        # 권장 행동 결정
        if critical_count >= 2:
            recommendation = "즉시 청산 검토: 투자 아이디어가 심각하게 훼손되었습니다."
            confidence = 0.9
        elif critical_count == 1:
            recommendation = "포지션 축소 검토: 핵심 투자 근거에 균열이 발생했습니다."
            confidence = 0.75
        elif warning_count >= 2:
            recommendation = "면밀한 모니터링 필요: 여러 경고 신호가 감지되었습니다."
            confidence = 0.6
        elif warning_count == 1:
            recommendation = "관찰 유지: 경미한 경고 신호가 있으나 투자 아이디어는 유효합니다."
            confidence = 0.5
        else:
            recommendation = "투자 아이디어 유효: 특이 사항 없음."
            confidence = 0.85
        
        return ThesisCheckResult(
            ticker=ticker,
            thesis_type=thesis_enum,
            thesis_intact=thesis_intact,
            violations=violations,
            recommendation=recommendation,
            confidence=confidence
        )
    
    def _check_market_share(self, history: List[Dict[str, Any]]) -> Optional[ThesisViolation]:
        """시장 점유율 하락 체크"""
        if len(history) < 2:
            return None
        
        # 최근 2분기 비교
        recent = history[-1].get("share", 0)
        previous = history[-2].get("share", 0)
        
        if previous > 0:
            change_pct = ((recent - previous) / previous) * 100
            if change_pct <= self.thresholds["market_share_decline_pct"]:
                return ThesisViolation(
                    violation_type=ViolationType.MARKET_SHARE_DECLINE,
                    severity=ViolationSeverity.WARNING if change_pct > -10 else ViolationSeverity.CRITICAL,
                    message=f"시장 점유율 {change_pct:.1f}% 하락 ({previous:.1f}% → {recent:.1f}%)",
                    data={"previous": previous, "current": recent, "change_pct": change_pct}
                )
        return None
    
    def _check_margin_trend(self, history: List[Dict[str, Any]]) -> Optional[ThesisViolation]:
        """영업이익률 추세 체크"""
        if len(history) < self.thresholds["margin_decline_quarters"]:
            return None
        
        # 연속 하락 횟수 카운트
        decline_count = 0
        for i in range(1, len(history)):
            if history[i].get("margin", 0) < history[i-1].get("margin", 0):
                decline_count += 1
            else:
                decline_count = 0  # 연속 끊김
        
        # 최근 vs 최고점 비교
        recent = history[-1].get("margin", 0)
        peak = max(h.get("margin", 0) for h in history)
        drop = recent - peak
        
        if decline_count >= self.thresholds["margin_decline_quarters"] or drop <= self.thresholds["margin_decline_threshold"]:
            severity = ViolationSeverity.CRITICAL if drop <= -5 else ViolationSeverity.WARNING
            return ThesisViolation(
                violation_type=ViolationType.MARGIN_DETERIORATION,
                severity=severity,
                message=f"영업이익률 {decline_count}분기 연속 하락, 고점 대비 {drop:.1f}%p 감소",
                data={"consecutive_declines": decline_count, "peak": peak, "current": recent, "drop": drop}
            )
        return None
    
    def _check_dividend(self, history: List[Dict[str, Any]]) -> Optional[ThesisViolation]:
        """배당 삭감 체크"""
        if len(history) < 2:
            return None
        
        recent = history[-1].get("dividend", 0)
        previous = history[-2].get("dividend", 0)
        
        if previous > 0:
            change_pct = ((recent - previous) / previous) * 100
            if change_pct <= self.thresholds["dividend_cut_pct"]:
                severity = ViolationSeverity.CRITICAL if change_pct <= -50 else ViolationSeverity.WARNING
                return ThesisViolation(
                    violation_type=ViolationType.DIVIDEND_CUT,
                    severity=severity,
                    message=f"배당 {abs(change_pct):.0f}% 삭감 (${previous:.2f} → ${recent:.2f})",
                    data={"previous": previous, "current": recent, "change_pct": change_pct}
                )
        elif previous == 0 and recent == 0:
            pass  # 원래 무배당
        elif previous > 0 and recent == 0:
            return ThesisViolation(
                violation_type=ViolationType.DIVIDEND_CUT,
                severity=ViolationSeverity.CRITICAL,
                message="배당 중단 (100% 삭감)",
                data={"previous": previous, "current": 0, "change_pct": -100}
            )
        return None
    
    def _check_insider_selling(self, transactions: List[Dict[str, Any]]) -> Optional[ThesisViolation]:
        """내부자 매도 체크"""
        if not transactions:
            return None
        
        # 최근 90일 내 매도 합산
        total_sell_pct = sum(
            t.get("pct", 0) for t in transactions 
            if t.get("type") == "sell"
        )
        
        if total_sell_pct >= self.thresholds["insider_selling_pct"]:
            severity = ViolationSeverity.CRITICAL if total_sell_pct >= 20 else ViolationSeverity.WARNING
            return ThesisViolation(
                violation_type=ViolationType.INSIDER_SELLING,
                severity=severity,
                message=f"내부자 지분 {total_sell_pct:.1f}% 매도 (최근 거래 기준)",
                data={"total_sell_pct": total_sell_pct, "transactions": len(transactions)}
            )
        return None
    
    def _check_debt_surge(self, history: List[Dict[str, Any]]) -> Optional[ThesisViolation]:
        """부채비율 급증 체크"""
        if len(history) < 2:
            return None
        
        recent = history[-1].get("ratio", 0)
        year_ago = history[0].get("ratio", 0) if len(history) >= 4 else history[-2].get("ratio", 0)
        
        if year_ago > 0:
            change_pct = ((recent - year_ago) / year_ago) * 100
            if change_pct >= self.thresholds["debt_ratio_increase_pct"]:
                severity = ViolationSeverity.CRITICAL if change_pct >= 100 else ViolationSeverity.WARNING
                return ThesisViolation(
                    violation_type=ViolationType.DEBT_SURGE,
                    severity=severity,
                    message=f"부채비율 {change_pct:.0f}% 상승 ({year_ago:.1f}x → {recent:.1f}x)",
                    data={"previous": year_ago, "current": recent, "change_pct": change_pct}
                )
        return None
    
    def _check_news_events(self, events: List[Dict[str, Any]]) -> List[ThesisViolation]:
        """뉴스 기반 리스크 체크"""
        violations = []
        
        for event in events:
            event_type = event.get("type", "").lower()
            
            if "ceo" in event_type or "management" in event_type:
                violations.append(ThesisViolation(
                    violation_type=ViolationType.MANAGEMENT_CHANGE,
                    severity=ViolationSeverity.WARNING,
                    message=f"경영진 변동: {event.get('description', 'N/A')}",
                    data=event
                ))
            
            if "regulatory" in event_type or "antitrust" in event_type or "fine" in event_type:
                violations.append(ThesisViolation(
                    violation_type=ViolationType.REGULATORY_RISK,
                    severity=ViolationSeverity.WARNING,
                    message=f"규제 리스크: {event.get('description', 'N/A')}",
                    data=event
                ))
            
            if "competitor" in event_type or "disruption" in event_type:
                violations.append(ThesisViolation(
                    violation_type=ViolationType.COMPETITIVE_THREAT,
                    severity=ViolationSeverity.WATCH,
                    message=f"경쟁 위협: {event.get('description', 'N/A')}",
                    data=event
                ))
        
        return violations


# 싱글톤 인스턴스
_default_detector: Optional[ThesisViolationDetector] = None


def get_thesis_detector() -> ThesisViolationDetector:
    """전역 ThesisViolationDetector 인스턴스 반환"""
    global _default_detector
    if _default_detector is None:
        _default_detector = ThesisViolationDetector()
    return _default_detector


# 테스트용
if __name__ == "__main__":
    detector = ThesisViolationDetector()
    
    print("=== Thesis Violation Detector Test ===\n")
    
    # Test: Moat thesis with market share decline
    result = detector.check_thesis(
        ticker="INTC",
        thesis_type="moat",
        fundamental_data={
            "market_share_history": [
                {"quarter": "Q1", "share": 80.0},
                {"quarter": "Q2", "share": 75.0},
                {"quarter": "Q3", "share": 70.0},
                {"quarter": "Q4", "share": 62.0},
            ],
            "operating_margin_history": [
                {"quarter": "Q1", "margin": 30.0},
                {"quarter": "Q2", "margin": 28.0},
                {"quarter": "Q3", "margin": 25.0},
                {"quarter": "Q4", "margin": 22.0},
            ],
            "insider_transactions": [
                {"type": "sell", "shares": 100000, "pct": 15.0}
            ]
        }
    )
    
    print(f"Ticker: {result.ticker}")
    print(f"Thesis Intact: {result.thesis_intact}")
    print(f"Recommendation: {result.recommendation}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Violations ({len(result.violations)}):")
    for v in result.violations:
        print(f"  - [{v.severity.value.upper()}] {v.violation_type.value}: {v.message}")
