"""
DCA Strategy - Dollar Cost Averaging (물타기 전략)

Phase E2: DCA Strategy Implementation

펀더멘털이 유지되는 상황에서 단기 하락 시 점진적 매수를 통해
평균 단가를 낮추는 전략

작성일: 2025-12-06
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from backend.schemas.base_schema import MarketContext, MarketRegime

logger = logging.getLogger(__name__)


@dataclass
class DCADecision:
    """DCA 실행 결정"""
    should_dca: bool                          # DCA 실행 여부
    reasoning: str                            # 판단 근거
    position_size: Optional[float] = None     # 추천 포지션 크기 (0~1)
    confidence: Optional[float] = None        # 신뢰도 (0~1)
    risk_factors: List[str] = None           # 리스크 요인

    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []


@dataclass
class DCAMetrics:
    """DCA 메트릭"""
    ticker: str
    avg_entry_price: float                    # 평균 매수가
    current_price: float                      # 현재 가격
    price_drop_pct: float                     # 하락폭 (%)
    dca_count: int                            # 현재 DCA 횟수
    total_invested: float                     # 총 투자액
    unrealized_pnl: float                     # 미실현 손익
    unrealized_pnl_pct: float                 # 미실현 손익률 (%)


class DCAStrategy:
    """
    Dollar Cost Averaging Strategy

    펀더멘털 유지 시 단기 하락에 점진적 매수

    핵심 원칙:
    1. 펀더멘털 체크: 기업 가치 유지 확인
    2. 최대 횟수 제한: 3회까지만 DCA 허용
    3. 점진적 감소: 각 DCA는 초기 투자액의 50%, 33%, 25%
    4. Consensus 필수: 3-AI 전원 동의 필요
    """

    def __init__(
        self,
        max_dca_count: int = 3,
        initial_dca_size: float = 0.5,        # 초기 투자액 대비 비율
        min_price_drop_pct: float = 10.0,     # 최소 하락폭 (%)
        max_total_loss_pct: float = 30.0      # 최대 총 손실률 (%)
    ):
        """
        Initialize DCA Strategy

        Args:
            max_dca_count: 최대 DCA 횟수
            initial_dca_size: 초기 투자액 대비 DCA 비율
            min_price_drop_pct: DCA 실행 최소 하락폭
            max_total_loss_pct: DCA 중단 최대 손실률
        """
        self.max_dca_count = max_dca_count
        self.initial_dca_size = initial_dca_size
        self.min_price_drop_pct = min_price_drop_pct
        self.max_total_loss_pct = max_total_loss_pct

        logger.info(
            f"DCAStrategy initialized: max_count={max_dca_count}, "
            f"min_drop={min_price_drop_pct}%, max_loss={max_total_loss_pct}%"
        )

    async def should_dca(
        self,
        ticker: str,
        current_price: float,
        avg_entry_price: float,
        dca_count: int,
        total_invested: float,
        context: MarketContext
    ) -> DCADecision:
        """
        DCA 실행 여부 판단

        Args:
            ticker: 종목 티커
            current_price: 현재 가격
            avg_entry_price: 평균 매수가
            dca_count: 현재까지 DCA 횟수
            total_invested: 총 투자액
            context: 시장 컨텍스트

        Returns:
            DCADecision: DCA 실행 여부 및 근거
        """
        logger.info(f"Evaluating DCA for {ticker}: price ${current_price} vs avg ${avg_entry_price}")

        risk_factors = []

        # 1. 최대 횟수 체크
        if dca_count >= self.max_dca_count:
            return DCADecision(
                should_dca=False,
                reasoning=f"DCA limit reached ({dca_count}/{self.max_dca_count})",
                risk_factors=["max_dca_count_reached"]
            )

        # 2. 하락폭 체크
        price_drop_pct = ((current_price - avg_entry_price) / avg_entry_price) * 100

        if price_drop_pct > -self.min_price_drop_pct:
            return DCADecision(
                should_dca=False,
                reasoning=f"Price drop insufficient ({price_drop_pct:.1f}% < {self.min_price_drop_pct}%)",
                risk_factors=["insufficient_price_drop"]
            )

        # 3. 최대 손실률 체크
        unrealized_pnl_pct = price_drop_pct  # 동일한 값
        if abs(unrealized_pnl_pct) > self.max_total_loss_pct:
            return DCADecision(
                should_dca=False,
                reasoning=f"Total loss too high ({unrealized_pnl_pct:.1f}% > {self.max_total_loss_pct}%)",
                risk_factors=["excessive_total_loss"]
            )

        # 4. 펀더멘털 체크
        fundamentals_ok, fundamental_reasoning = await self._check_fundamentals(ticker, context)

        if not fundamentals_ok:
            return DCADecision(
                should_dca=False,
                reasoning=f"Fundamentals deteriorated: {fundamental_reasoning}",
                risk_factors=["fundamental_deterioration"]
            )

        # 5. 시장 국면 체크
        regime_ok, regime_reasoning = self._check_market_regime(context)
        if not regime_ok:
            risk_factors.append("unfavorable_market_regime")

        # 6. 포지션 크기 계산
        position_size = self._calculate_dca_position_size(dca_count, total_invested)

        # 7. 신뢰도 계산
        confidence = self._calculate_confidence(
            price_drop_pct,
            fundamentals_ok,
            regime_ok,
            context
        )

        # 모든 조건 통과
        reasoning_parts = [
            f"Fundamentals intact: {fundamental_reasoning}",
            f"Price drop: {price_drop_pct:.1f}%",
            f"DCA count: {dca_count}/{self.max_dca_count}",
            f"Recommended position: {position_size:.1%}"
        ]

        return DCADecision(
            should_dca=True,
            reasoning="; ".join(reasoning_parts),
            position_size=position_size,
            confidence=confidence,
            risk_factors=risk_factors
        )

    async def _check_fundamentals(
        self,
        ticker: str,
        context: MarketContext
    ) -> tuple[bool, str]:
        """
        펀더멘털 유지 여부 확인

        Args:
            ticker: 종목 티커
            context: 시장 컨텍스트

        Returns:
            (펀더멘털 OK 여부, 판단 근거)
        """
        reasons = []

        # 1. 뉴스 감성 분석
        if context.news:
            sentiment = context.news.sentiment or 0.0

            if sentiment < -0.5:
                return (False, f"Negative news sentiment ({sentiment:.2f})")

            if sentiment >= -0.2:
                reasons.append(f"News sentiment neutral/positive ({sentiment:.2f})")
            else:
                reasons.append(f"News sentiment mildly negative ({sentiment:.2f})")

        # 2. 공급망 리스크
        if context.risk_factors:
            supply_chain_risk = context.risk_factors.get("supply_chain", 0)

            if supply_chain_risk > 0.7:
                return (False, f"High supply chain risk ({supply_chain_risk:.2f})")

            if supply_chain_risk > 0.4:
                reasons.append(f"Moderate supply chain risk ({supply_chain_risk:.2f})")

        # 3. 정책 리스크 (PERI)
        if context.policy_risk:
            peri = context.policy_risk.peri

            if peri > 60:
                return (False, f"High policy risk (PERI: {peri:.0f})")

            if peri > 40:
                reasons.append(f"Moderate policy risk (PERI: {peri:.0f})")

        # 4. 단위 경제학 (칩 경제성)
        if context.unit_economics:
            token_cost = context.unit_economics.token_cost

            if token_cost and token_cost > 2e-8:  # 임계값 예시
                reasons.append("Token cost increasing")

        # 5. 세그먼트 건전성
        if context.news and context.news.segment:
            segment = context.news.segment.value
            reasons.append(f"Segment: {segment}")

        # 기본값: 펀더멘털 유지
        if not reasons:
            reasons.append("No significant fundamental changes detected")

        return (True, "; ".join(reasons))

    def _check_market_regime(self, context: MarketContext) -> tuple[bool, str]:
        """
        시장 국면 체크

        Args:
            context: 시장 컨텍스트

        Returns:
            (시장 국면 OK 여부, 판단 근거)
        """
        if not context.market_regime:
            return (True, "Market regime unknown")

        regime = context.market_regime

        # DCA 불리한 국면
        unfavorable_regimes = [MarketRegime.CRASH, MarketRegime.BEAR]

        if regime in unfavorable_regimes:
            return (False, f"Unfavorable market regime: {regime.value}")

        # DCA 유리한 국면
        favorable_regimes = [MarketRegime.RECOVERY, MarketRegime.SIDEWAYS]

        if regime in favorable_regimes:
            return (True, f"Favorable regime for DCA: {regime.value}")

        # 중립 국면
        return (True, f"Neutral market regime: {regime.value}")

    def _calculate_dca_position_size(
        self,
        dca_count: int,
        total_invested: float
    ) -> float:
        """
        DCA 포지션 크기 계산

        점진적 감소 전략:
        - 1차 DCA: 초기 투자액의 50%
        - 2차 DCA: 초기 투자액의 33%
        - 3차 DCA: 초기 투자액의 25%

        Args:
            dca_count: 현재 DCA 횟수
            total_invested: 총 투자액

        Returns:
            추천 포지션 크기 (초기 투자액 대비 비율)
        """
        # 초기 투자액 추정 (간단히 total_invested 사용)
        initial_investment = total_invested

        # DCA 횟수에 따른 비율
        size_schedule = {
            0: 0.50,  # 1차 DCA
            1: 0.33,  # 2차 DCA
            2: 0.25,  # 3차 DCA
        }

        return size_schedule.get(dca_count, 0.20)

    def _calculate_confidence(
        self,
        price_drop_pct: float,
        fundamentals_ok: bool,
        regime_ok: bool,
        context: MarketContext
    ) -> float:
        """
        DCA 신뢰도 계산

        Args:
            price_drop_pct: 가격 하락폭 (%)
            fundamentals_ok: 펀더멘털 OK 여부
            regime_ok: 시장 국면 OK 여부
            context: 시장 컨텍스트

        Returns:
            신뢰도 (0~1)
        """
        confidence = 0.5  # 기본값

        # 1. 펀더멘털 가중치 (40%)
        if fundamentals_ok:
            confidence += 0.2
        else:
            confidence -= 0.2

        # 2. 시장 국면 가중치 (20%)
        if regime_ok:
            confidence += 0.1
        else:
            confidence -= 0.1

        # 3. 하락폭 가중치 (20%)
        # 적당한 하락폭 (10~20%)이 가장 좋음
        abs_drop = abs(price_drop_pct)
        if 10 <= abs_drop <= 20:
            confidence += 0.15
        elif 20 < abs_drop <= 30:
            confidence += 0.05
        else:
            confidence -= 0.1

        # 4. 뉴스 감성 가중치 (20%)
        if context.news and context.news.sentiment:
            sentiment = context.news.sentiment
            if sentiment >= 0:
                confidence += 0.1
            elif sentiment >= -0.3:
                confidence += 0.05
            else:
                confidence -= 0.05

        # 0~1 범위로 클램핑
        return max(0.0, min(1.0, confidence))

    def calculate_metrics(
        self,
        ticker: str,
        current_price: float,
        avg_entry_price: float,
        dca_count: int,
        total_invested: float
    ) -> DCAMetrics:
        """
        DCA 메트릭 계산

        Args:
            ticker: 종목 티커
            current_price: 현재 가격
            avg_entry_price: 평균 매수가
            dca_count: DCA 횟수
            total_invested: 총 투자액

        Returns:
            DCAMetrics
        """
        price_drop_pct = ((current_price - avg_entry_price) / avg_entry_price) * 100

        # 현재 보유 주식 수 추정
        shares = total_invested / avg_entry_price

        # 현재 가치
        current_value = shares * current_price

        # 미실현 손익
        unrealized_pnl = current_value - total_invested
        unrealized_pnl_pct = (unrealized_pnl / total_invested) * 100

        return DCAMetrics(
            ticker=ticker,
            avg_entry_price=avg_entry_price,
            current_price=current_price,
            price_drop_pct=price_drop_pct,
            dca_count=dca_count,
            total_invested=total_invested,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct
        )


# ============================================================================
# Singleton
# ============================================================================

_dca_strategy: Optional[DCAStrategy] = None


def get_dca_strategy() -> DCAStrategy:
    """DCA Strategy 싱글톤 인스턴스"""
    global _dca_strategy
    if _dca_strategy is None:
        _dca_strategy = DCAStrategy()
    return _dca_strategy


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    import asyncio
    from backend.schemas.base_schema import NewsFeatures, MarketSegment, MarketRegime

    async def test_dca():
        print("=" * 70)
        print("DCA Strategy Test")
        print("=" * 70)

        strategy = DCAStrategy()

        # 테스트 시나리오
        scenarios = [
            {
                "name": "Scenario 1: Good DCA opportunity",
                "ticker": "NVDA",
                "current_price": 130.0,
                "avg_entry_price": 150.0,
                "dca_count": 0,
                "total_invested": 10000.0,
                "context": MarketContext(
                    ticker="NVDA",
                    news=NewsFeatures(
                        headline="NVIDIA maintains strong fundamentals",
                        segment=MarketSegment.TRAINING,
                        sentiment=0.3
                    ),
                    market_regime=MarketRegime.SIDEWAYS
                )
            },
            {
                "name": "Scenario 2: DCA limit reached",
                "ticker": "NVDA",
                "current_price": 120.0,
                "avg_entry_price": 150.0,
                "dca_count": 3,
                "total_invested": 15000.0,
                "context": MarketContext(
                    ticker="NVDA",
                    news=NewsFeatures(
                        headline="NVIDIA continues to perform",
                        segment=MarketSegment.TRAINING,
                        sentiment=0.5
                    ),
                    market_regime=MarketRegime.RECOVERY
                )
            },
            {
                "name": "Scenario 3: Fundamental deterioration",
                "ticker": "NVDA",
                "current_price": 130.0,
                "avg_entry_price": 150.0,
                "dca_count": 1,
                "total_invested": 12000.0,
                "context": MarketContext(
                    ticker="NVDA",
                    news=NewsFeatures(
                        headline="NVIDIA faces regulatory challenges",
                        segment=MarketSegment.TRAINING,
                        sentiment=-0.6
                    ),
                    market_regime=MarketRegime.BEAR
                )
            }
        ]

        for scenario in scenarios:
            print(f"\n{'-' * 70}")
            print(f"{scenario['name']}")
            print(f"{'-' * 70}")

            decision = await strategy.should_dca(
                ticker=scenario["ticker"],
                current_price=scenario["current_price"],
                avg_entry_price=scenario["avg_entry_price"],
                dca_count=scenario["dca_count"],
                total_invested=scenario["total_invested"],
                context=scenario["context"]
            )

            print(f"Decision: {'DCA RECOMMENDED' if decision.should_dca else 'DCA NOT RECOMMENDED'}")
            print(f"Reasoning: {decision.reasoning}")

            if decision.should_dca:
                print(f"Position Size: {decision.position_size:.1%}")
                print(f"Confidence: {decision.confidence:.2f}")

            if decision.risk_factors:
                print(f"Risk Factors: {', '.join(decision.risk_factors)}")

            # Metrics
            metrics = strategy.calculate_metrics(
                ticker=scenario["ticker"],
                current_price=scenario["current_price"],
                avg_entry_price=scenario["avg_entry_price"],
                dca_count=scenario["dca_count"],
                total_invested=scenario["total_invested"]
            )

            print(f"\nMetrics:")
            print(f"  Price Drop: {metrics.price_drop_pct:.1f}%")
            print(f"  Unrealized P&L: ${metrics.unrealized_pnl:,.2f} ({metrics.unrealized_pnl_pct:.1f}%)")

    asyncio.run(test_dca())
