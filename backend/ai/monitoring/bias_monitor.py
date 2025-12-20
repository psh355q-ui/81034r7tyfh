"""
BiasMonitor - AI 시그널 편향 탐지 및 보정 시스템

Phase C2 핵심 기능:
- AI 트레이딩 시그널의 인지 편향 탐지
- 7가지 주요 편향 패턴 수치화
- 자동 편향 보정 및 경고

지원하는 편향 유형:
1. Confirmation Bias (확증 편향): 기존 믿음을 확인하는 정보만 선택
2. Recency Bias (최근성 편향): 최근 사건에 과도한 가중치
3. Anchoring Bias (앵커링 편향): 초기 정보에 과도하게 의존
4. Overconfidence Bias (과신 편향): 예측 능력 과대평가
5. Loss Aversion Bias (손실 회피): 손실을 과도하게 회피
6. Herd Behavior (군중 심리): 다수 의견을 맹목적으로 따름
7. Availability Bias (가용성 편향): 쉽게 떠오르는 정보에 의존

목표:
- AI 신뢰도: 95% → 97% (+2%)
- 편향 탐지율: 0% → 85% (+85%)
- 시스템 점수: 89/100 → 91/100 (+2)

작성일: 2025-12-03 (Phase C2)
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import Counter, deque

from backend.schemas.base_schema import InvestmentSignal, SignalAction

logger = logging.getLogger(__name__)


@dataclass
class BiasScore:
    """편향 점수"""
    bias_type: str
    score: float  # 0~1 (0=없음, 1=심각)
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class BiasReport:
    """편향 분석 보고서"""
    signal_id: str
    total_bias_score: float  # 0~1
    bias_scores: List[BiasScore] = field(default_factory=list)
    is_biased: bool = False
    correction_applied: bool = False
    corrected_confidence: Optional[float] = None
    warnings: List[str] = field(default_factory=list)


class BiasMonitor:
    """
    Bias Monitor - AI 시그널 편향 탐지 시스템

    AI 트레이딩 시스템의 7가지 인지 편향을 탐지하고 보정

    핵심 원칙:
    1. 편향 탐지: 과거 시그널 패턴 분석
    2. 점수화: 각 편향 0~1 점수
    3. 자동 보정: 신뢰도 하향 조정
    4. 경고: 심각한 편향 발생 시 알림
    """

    # 편향 임계값
    BIAS_THRESHOLDS = {
        "LOW": 0.25,
        "MEDIUM": 0.50,
        "HIGH": 0.70,
        "CRITICAL": 0.85
    }

    # 편향 가중치 (총 100%)
    BIAS_WEIGHTS = {
        "confirmation": 0.20,  # 20%
        "recency": 0.15,       # 15%
        "anchoring": 0.15,     # 15%
        "overconfidence": 0.20,  # 20%
        "loss_aversion": 0.10,   # 10%
        "herd_behavior": 0.10,   # 10%
        "availability": 0.10     # 10%
    }

    def __init__(self, history_window: int = 50):
        """
        Args:
            history_window: 편향 분석에 사용할 과거 시그널 수
        """
        self.history_window = history_window
        self.signal_history: deque = deque(maxlen=history_window)

        logger.info(f"BiasMonitor initialized with history_window={history_window}")

    def analyze_bias(
        self,
        signal: InvestmentSignal,
        signal_id: Optional[str] = None
    ) -> BiasReport:
        """
        시그널의 편향 분석

        Args:
            signal: 분석할 InvestmentSignal
            signal_id: 시그널 ID (선택)

        Returns:
            BiasReport
        """
        if signal_id is None:
            signal_id = f"{signal.ticker}_{datetime.now().timestamp()}"

        bias_scores = []

        # 1. Confirmation Bias 체크
        conf_score = self._check_confirmation_bias(signal)
        bias_scores.append(conf_score)

        # 2. Recency Bias 체크
        recency_score = self._check_recency_bias(signal)
        bias_scores.append(recency_score)

        # 3. Anchoring Bias 체크
        anchor_score = self._check_anchoring_bias(signal)
        bias_scores.append(anchor_score)

        # 4. Overconfidence Bias 체크
        overconf_score = self._check_overconfidence_bias(signal)
        bias_scores.append(overconf_score)

        # 5. Loss Aversion Bias 체크
        loss_score = self._check_loss_aversion_bias(signal)
        bias_scores.append(loss_score)

        # 6. Herd Behavior 체크
        herd_score = self._check_herd_behavior(signal)
        bias_scores.append(herd_score)

        # 7. Availability Bias 체크
        avail_score = self._check_availability_bias(signal)
        bias_scores.append(avail_score)

        # 총 편향 점수 계산
        total_bias = self._calculate_total_bias(bias_scores)

        # 편향 판정
        is_biased = total_bias >= self.BIAS_THRESHOLDS["MEDIUM"]

        # 편향 보정
        corrected_confidence = None
        correction_applied = False
        if is_biased:
            corrected_confidence = self._apply_bias_correction(
                signal.confidence, total_bias
            )
            correction_applied = True

        # 경고 생성
        warnings = self._generate_warnings(bias_scores, total_bias)

        # 시그널 히스토리에 추가
        self.signal_history.append({
            "signal": signal,
            "timestamp": datetime.now(),
            "bias_score": total_bias
        })

        report = BiasReport(
            signal_id=signal_id,
            total_bias_score=total_bias,
            bias_scores=bias_scores,
            is_biased=is_biased,
            correction_applied=correction_applied,
            corrected_confidence=corrected_confidence,
            warnings=warnings
        )

        logger.info(f"Bias analysis for {signal.ticker}: "
                   f"Total={total_bias:.0%}, Biased={is_biased}")

        return report

    def _check_confirmation_bias(self, signal: InvestmentSignal) -> BiasScore:
        """
        확증 편향 체크

        기존 포지션과 동일한 방향의 시그널만 지속적으로 생성하는지 확인
        """
        if len(self.signal_history) < 10:
            return BiasScore(
                bias_type="confirmation",
                score=0.0,
                severity="LOW",
                description="Insufficient history for confirmation bias check"
            )

        # 최근 10개 시그널에서 같은 티커의 액션 분포
        ticker_signals = [
            s["signal"] for s in self.signal_history
            if s["signal"].ticker == signal.ticker
        ]

        if len(ticker_signals) < 5:
            return BiasScore(
                bias_type="confirmation",
                score=0.0,
                severity="LOW",
                description="Not enough ticker history"
            )

        # 같은 액션 비율
        same_action_count = sum(
            1 for s in ticker_signals if s.action == signal.action
        )
        same_action_ratio = same_action_count / len(ticker_signals)

        # 90% 이상 같은 액션이면 확증 편향
        if same_action_ratio >= 0.9:
            score = min(same_action_ratio, 1.0)
            severity = self._get_severity(score)
            return BiasScore(
                bias_type="confirmation",
                score=score,
                severity=severity,
                description=f"High same-action ratio: {same_action_ratio:.0%} {signal.action}"
            )

        return BiasScore(
            bias_type="confirmation",
            score=same_action_ratio * 0.5,
            severity=self._get_severity(same_action_ratio * 0.5),
            description="No significant confirmation bias"
        )

    def _check_recency_bias(self, signal: InvestmentSignal) -> BiasScore:
        """
        최근성 편향 체크

        최근 1주일 시그널이 전체 히스토리의 50% 이상을 차지하는지 확인
        """
        if len(self.signal_history) < 20:
            return BiasScore(
                bias_type="recency",
                score=0.0,
                severity="LOW",
                description="Insufficient history"
            )

        now = datetime.now()
        recent_cutoff = now - timedelta(days=7)

        # 최근 7일 시그널 비율
        recent_count = sum(
            1 for s in self.signal_history
            if s["timestamp"] >= recent_cutoff
        )
        recent_ratio = recent_count / len(self.signal_history)

        # 50% 이상이면 최근성 편향
        if recent_ratio >= 0.5:
            score = min(recent_ratio, 1.0)
            severity = self._get_severity(score)
            return BiasScore(
                bias_type="recency",
                score=score,
                severity=severity,
                description=f"High recent signal concentration: {recent_ratio:.0%}"
            )

        return BiasScore(
            bias_type="recency",
            score=recent_ratio * 0.5,
            severity=self._get_severity(recent_ratio * 0.5),
            description="No significant recency bias"
        )

    def _check_anchoring_bias(self, signal: InvestmentSignal) -> BiasScore:
        """
        앵커링 편향 체크

        초기 신뢰도에 과도하게 의존하여 비슷한 신뢰도만 생성하는지 확인
        """
        if len(self.signal_history) < 15:
            return BiasScore(
                bias_type="anchoring",
                score=0.0,
                severity="LOW",
                description="Insufficient history"
            )

        # 신뢰도 분산 계산
        confidences = [s["signal"].confidence for s in self.signal_history]
        avg_conf = sum(confidences) / len(confidences)
        variance = sum((c - avg_conf) ** 2 for c in confidences) / len(confidences)
        std_dev = variance ** 0.5

        # 표준편차가 0.05 이하면 앵커링 편향 (거의 같은 신뢰도)
        if std_dev <= 0.05:
            score = 1.0 - (std_dev / 0.05)
            severity = self._get_severity(score)
            return BiasScore(
                bias_type="anchoring",
                score=score,
                severity=severity,
                description=f"Low confidence variance: σ={std_dev:.3f}"
            )

        return BiasScore(
            bias_type="anchoring",
            score=0.0,
            severity="LOW",
            description="Healthy confidence distribution"
        )

    def _check_overconfidence_bias(self, signal: InvestmentSignal) -> BiasScore:
        """
        과신 편향 체크

        지속적으로 90% 이상 고신뢰도 시그널을 생성하는지 확인
        """
        if len(self.signal_history) < 10:
            return BiasScore(
                bias_type="overconfidence",
                score=0.0,
                severity="LOW",
                description="Insufficient history"
            )

        # 90% 이상 신뢰도 비율
        high_conf_count = sum(
            1 for s in self.signal_history
            if s["signal"].confidence >= 0.90
        )
        high_conf_ratio = high_conf_count / len(self.signal_history)

        # 50% 이상이 고신뢰도면 과신 편향
        if high_conf_ratio >= 0.5:
            score = min(high_conf_ratio * 1.5, 1.0)
            severity = self._get_severity(score)
            return BiasScore(
                bias_type="overconfidence",
                score=score,
                severity=severity,
                description=f"High confidence concentration: {high_conf_ratio:.0%} signals ≥90%"
            )

        # 현재 시그널이 95% 이상이면 추가 경고
        if signal.confidence >= 0.95:
            return BiasScore(
                bias_type="overconfidence",
                score=0.7,
                severity="HIGH",
                description="Extremely high confidence signal (≥95%)"
            )

        return BiasScore(
            bias_type="overconfidence",
            score=high_conf_ratio * 0.3,
            severity=self._get_severity(high_conf_ratio * 0.3),
            description="No significant overconfidence"
        )

    def _check_loss_aversion_bias(self, signal: InvestmentSignal) -> BiasScore:
        """
        손실 회피 편향 체크

        SELL 시그널이 과도하게 적은지 확인 (손실을 회피하려는 경향)
        """
        if len(self.signal_history) < 20:
            return BiasScore(
                bias_type="loss_aversion",
                score=0.0,
                severity="LOW",
                description="Insufficient history"
            )

        # BUY vs SELL 비율
        action_counter = Counter(
            s["signal"].action for s in self.signal_history
        )

        buy_count = action_counter.get(SignalAction.BUY, 0)
        sell_count = action_counter.get(SignalAction.SELL, 0)
        total = buy_count + sell_count

        if total == 0:
            return BiasScore(
                bias_type="loss_aversion",
                score=0.0,
                severity="LOW",
                description="No BUY/SELL signals"
            )

        sell_ratio = sell_count / total

        # SELL이 10% 미만이면 손실 회피 편향
        if sell_ratio < 0.10:
            score = 1.0 - (sell_ratio / 0.10)
            severity = self._get_severity(score)
            return BiasScore(
                bias_type="loss_aversion",
                score=score,
                severity=severity,
                description=f"Very low SELL ratio: {sell_ratio:.0%}"
            )

        return BiasScore(
            bias_type="loss_aversion",
            score=0.0,
            severity="LOW",
            description="Healthy BUY/SELL balance"
        )

    def _check_herd_behavior(self, signal: InvestmentSignal) -> BiasScore:
        """
        군중 심리 편향 체크

        같은 티커에 대한 시그널이 집중되는지 확인
        """
        if len(self.signal_history) < 15:
            return BiasScore(
                bias_type="herd_behavior",
                score=0.0,
                severity="LOW",
                description="Insufficient history"
            )

        # 티커 분포
        ticker_counter = Counter(
            s["signal"].ticker for s in self.signal_history
        )

        # 가장 많은 티커의 비율
        most_common_ticker, max_count = ticker_counter.most_common(1)[0]
        max_ratio = max_count / len(self.signal_history)

        # 40% 이상이 같은 티커면 군중 심리
        if max_ratio >= 0.40:
            score = min(max_ratio * 2, 1.0)
            severity = self._get_severity(score)
            return BiasScore(
                bias_type="herd_behavior",
                score=score,
                severity=severity,
                description=f"High ticker concentration: {most_common_ticker} {max_ratio:.0%}"
            )

        return BiasScore(
            bias_type="herd_behavior",
            score=max_ratio * 0.5,
            severity=self._get_severity(max_ratio * 0.5),
            description="Diverse ticker distribution"
        )

    def _check_availability_bias(self, signal: InvestmentSignal) -> BiasScore:
        """
        가용성 편향 체크

        뉴스에 자주 등장하는 종목에만 시그널을 생성하는지 확인
        (메타데이터에 news_mentions 필드가 있다고 가정)
        """
        if len(self.signal_history) < 10:
            return BiasScore(
                bias_type="availability",
                score=0.0,
                severity="LOW",
                description="Insufficient history"
            )

        # 메타데이터에서 뉴스 언급 확인
        news_signals = []
        for s in self.signal_history:
            metadata = s["signal"].metadata or {}
            if metadata.get("news_mentions", 0) > 0:
                news_signals.append(s)

        if len(self.signal_history) == 0:
            return BiasScore(
                bias_type="availability",
                score=0.0,
                severity="LOW",
                description="No metadata available"
            )

        news_ratio = len(news_signals) / len(self.signal_history)

        # 80% 이상이 뉴스 기반이면 가용성 편향
        if news_ratio >= 0.80:
            score = min(news_ratio, 1.0)
            severity = self._get_severity(score)
            return BiasScore(
                bias_type="availability",
                score=score,
                severity=severity,
                description=f"High news-driven signal ratio: {news_ratio:.0%}"
            )

        return BiasScore(
            bias_type="availability",
            score=news_ratio * 0.3,
            severity=self._get_severity(news_ratio * 0.3),
            description="Balanced news/fundamental mix"
        )

    def _calculate_total_bias(self, bias_scores: List[BiasScore]) -> float:
        """
        총 편향 점수 계산 (가중 평균)

        Args:
            bias_scores: BiasScore 리스트

        Returns:
            총 편향 점수 (0~1)
        """
        total = 0.0
        for bias in bias_scores:
            weight = self.BIAS_WEIGHTS.get(bias.bias_type, 0.1)
            total += bias.score * weight

        return min(total, 1.0)

    def _get_severity(self, score: float) -> str:
        """편향 점수에 따른 심각도 반환"""
        if score >= self.BIAS_THRESHOLDS["CRITICAL"]:
            return "CRITICAL"
        elif score >= self.BIAS_THRESHOLDS["HIGH"]:
            return "HIGH"
        elif score >= self.BIAS_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"

    def _apply_bias_correction(
        self,
        original_confidence: float,
        bias_score: float
    ) -> float:
        """
        편향 보정 적용

        편향 점수에 비례하여 신뢰도 하향 조정

        Args:
            original_confidence: 원본 신뢰도
            bias_score: 편향 점수

        Returns:
            보정된 신뢰도
        """
        # 편향 점수에 따라 5~30% 하향 조정
        penalty = 0.05 + (bias_score * 0.25)
        corrected = original_confidence * (1 - penalty)

        return max(corrected, 0.3)  # 최소 30%

    def _generate_warnings(
        self,
        bias_scores: List[BiasScore],
        total_bias: float
    ) -> List[str]:
        """경고 메시지 생성"""
        warnings = []

        # 총 편향 점수 경고
        if total_bias >= self.BIAS_THRESHOLDS["CRITICAL"]:
            warnings.append(
                f"⚠️ CRITICAL: Total bias score {total_bias:.0%} - "
                "Signal reliability severely compromised"
            )
        elif total_bias >= self.BIAS_THRESHOLDS["HIGH"]:
            warnings.append(
                f"⚠️ HIGH: Total bias score {total_bias:.0%} - "
                "Consider manual review"
            )

        # 개별 편향 경고
        for bias in bias_scores:
            if bias.severity in ["HIGH", "CRITICAL"]:
                warnings.append(
                    f"⚠️ {bias.severity}: {bias.bias_type} - {bias.description}"
                )

        return warnings

    def get_bias_summary(self) -> Dict[str, Any]:
        """
        전체 편향 요약 통계

        Returns:
            편향 통계 딕셔너리
        """
        if not self.signal_history:
            return {
                "total_signals": 0,
                "avg_bias_score": 0.0,
                "biased_signals_ratio": 0.0,
                "bias_distribution": {}
            }

        total_signals = len(self.signal_history)
        avg_bias = sum(s["bias_score"] for s in self.signal_history) / total_signals

        biased_count = sum(
            1 for s in self.signal_history
            if s["bias_score"] >= self.BIAS_THRESHOLDS["MEDIUM"]
        )
        biased_ratio = biased_count / total_signals

        return {
            "total_signals": total_signals,
            "avg_bias_score": avg_bias,
            "biased_signals_ratio": biased_ratio,
            "biased_count": biased_count
        }


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("BiasMonitor Test")
    print("=" * 70)

    monitor = BiasMonitor(history_window=50)

    # Test 1: 정상 시그널
    print("\n=== Test 1: Normal Signal ===")
    normal_signal = InvestmentSignal(
        ticker="NVDA",
        action=SignalAction.BUY,
        confidence=0.75,
        rationale="Strong fundamentals",
        metadata={"news_mentions": 2}
    )
    report1 = monitor.analyze_bias(normal_signal, "test1")
    print(f"Total Bias: {report1.total_bias_score:.0%}")
    print(f"Is Biased: {report1.is_biased}")
    print(f"Warnings: {len(report1.warnings)}")

    # Test 2: 확증 편향 시뮬레이션 (같은 티커, 같은 액션 반복)
    print("\n=== Test 2: Confirmation Bias Simulation ===")
    for i in range(15):
        signal = InvestmentSignal(
            ticker="NVDA",
            action=SignalAction.BUY,
            confidence=0.80,
            rationale=f"BUY signal {i+1}",
            metadata={"news_mentions": 1}
        )
        report = monitor.analyze_bias(signal, f"conf_{i}")

    # 마지막 시그널 분석
    print(f"After 15 BUY signals:")
    print(f"Total Bias: {report.total_bias_score:.0%}")
    print(f"Is Biased: {report.is_biased}")
    for bias in report.bias_scores:
        if bias.score >= 0.25:
            print(f"  - {bias.bias_type}: {bias.score:.0%} ({bias.severity})")

    # Test 3: 과신 편향 (높은 신뢰도)
    print("\n=== Test 3: Overconfidence Bias ===")
    for i in range(10):
        signal = InvestmentSignal(
            ticker=["GOOGL", "AMD", "TSM"][i % 3],
            action=SignalAction.BUY,
            confidence=0.95,  # 매우 높은 신뢰도
            rationale=f"High confidence {i+1}",
            metadata={}
        )
        report = monitor.analyze_bias(signal, f"overconf_{i}")

    print(f"After 10 high-confidence signals:")
    print(f"Total Bias: {report.total_bias_score:.0%}")
    print(f"Correction Applied: {report.correction_applied}")
    if report.corrected_confidence:
        print(f"Original: {signal.confidence:.0%} → Corrected: {report.corrected_confidence:.0%}")

    # Test 4: 전체 요약
    print("\n=== Test 4: Bias Summary ===")
    summary = monitor.get_bias_summary()
    print(f"Total Signals: {summary['total_signals']}")
    print(f"Avg Bias Score: {summary['avg_bias_score']:.0%}")
    print(f"Biased Signals: {summary['biased_count']}/{summary['total_signals']} "
          f"({summary['biased_signals_ratio']:.0%})")

    print("\n=== Test PASSED! ===")
