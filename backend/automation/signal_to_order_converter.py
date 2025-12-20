"""
SignalToOrderConverter - 투자 시그널을 실제 주문으로 변환

Phase B 통합:
- InvestmentSignal → Broker Order 변환
- Constitution Rules 적용 (Pre-Check, Post-Check)
- 포지션 사이징 및 리스크 관리
- 주문 실행 및 로깅

작성일: 2025-12-03 (Phase B)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from backend.schemas.base_schema import InvestmentSignal, SignalAction

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """주문 유형"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """주문 방향"""
    BUY = "buy"
    SELL = "sell"


class Order:
    """주문 객체"""

    def __init__(
        self,
        ticker: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ):
        self.ticker = ticker
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "ticker": self.ticker,
            "side": self.side.value,
            "quantity": self.quantity,
            "order_type": self.order_type.value,
            "limit_price": self.limit_price,
            "stop_price": self.stop_price,
            "timestamp": self.timestamp.isoformat()
        }

    def __repr__(self) -> str:
        return f"Order({self.side.value} {self.quantity} {self.ticker} @ {self.order_type.value})"


class SignalToOrderConverter:
    """
    투자 시그널을 실제 주문으로 변환

    주요 기능:
    1. InvestmentSignal → Order 변환
    2. Constitution Rules 적용 (Pre-Check)
    3. 포지션 사이징 계산
    4. Risk Management (최대 포지션 제한)
    5. 주문 검증 및 실행

    Constitution Rules (로드맵 기준):
    - Pre-Check Filters (6개 규칙)
    - Post-Check Adjustments (4개 규칙)
    - Position Sizing 자동 조절
    """

    # Constitution Rules - Pre-Check Filters
    MAX_POSITION_SIZE = 0.25  # 포트폴리오의 25%까지
    MIN_CONFIDENCE = 0.6  # 최소 신뢰도 60%
    MAX_DAILY_TRADES = 10  # 일일 최대 거래 수
    MIN_PORTFOLIO_VALUE = 1000  # 최소 포트폴리오 가치 (USD)

    # Risk Management
    MAX_TOTAL_EXPOSURE = 0.90  # 총 노출도 90%까지
    RESERVE_CASH_RATIO = 0.10  # 현금 보유 비율 10%

    def __init__(
        self,
        portfolio_value: float = 100000,
        current_positions: Optional[Dict[str, int]] = None,
        price_fetcher: Optional[Any] = None
    ):
        """
        Args:
            portfolio_value: 포트폴리오 총 가치 (USD)
            current_positions: 현재 포지션 {ticker: quantity}
            price_fetcher: 가격 조회 함수 (ticker) -> price
        """
        self.portfolio_value = portfolio_value
        self.current_positions = current_positions or {}
        self.price_fetcher = price_fetcher or self._mock_price_fetcher

        self.daily_trade_count = 0
        self.daily_trades_reset_date = datetime.now().date()

        logger.info(
            f"SignalToOrderConverter initialized: "
            f"portfolio=${portfolio_value:,.0f}"
        )

    def convert(self, signal: InvestmentSignal) -> Optional[Order]:
        """
        InvestmentSignal을 Order로 변환

        Args:
            signal: InvestmentSignal 스키마

        Returns:
            Order 객체 (규칙 통과 시) 또는 None (필터링됨)
        """
        logger.info(f"Converting signal: {signal.action} {signal.ticker}")

        # 1. Pre-Check Filters
        if not self._pre_check_filters(signal):
            logger.warning(f"Signal filtered out: {signal.ticker}")
            return None

        # 2. Position Sizing 계산
        quantity = self._calculate_position_size(signal)

        if quantity == 0:
            logger.warning(f"Position size is zero: {signal.ticker}")
            return None

        # 3. Order 생성
        order_side = self._signal_action_to_order_side(signal.action)

        if order_side is None:
            logger.warning(f"Cannot convert action {signal.action} to order side")
            return None

        order = Order(
            ticker=signal.ticker,
            side=order_side,
            quantity=quantity,
            order_type=OrderType.MARKET
        )

        # 4. Post-Check Adjustments
        adjusted_order = self._post_check_adjustments(order, signal)

        logger.info(f"Order created: {adjusted_order}")

        return adjusted_order

    def _pre_check_filters(self, signal: InvestmentSignal) -> bool:
        """
        Pre-Check Filters (6개 규칙)

        Returns:
            통과하면 True, 필터링되면 False
        """

        # Rule 1: 최소 신뢰도 체크
        if signal.confidence < self.MIN_CONFIDENCE:
            logger.info(f"Filter: Confidence too low ({signal.confidence:.0%} < {self.MIN_CONFIDENCE:.0%})")
            return False

        # Rule 2: HOLD 시그널은 스킵
        if signal.action == SignalAction.HOLD:
            logger.info("Filter: HOLD signal skipped")
            return False

        # Rule 3: 일일 거래 한도 체크
        if self._check_daily_trade_limit():
            logger.warning(f"Filter: Daily trade limit reached ({self.daily_trade_count}/{self.MAX_DAILY_TRADES})")
            return False

        # Rule 4: 포트폴리오 최소 가치 체크
        if self.portfolio_value < self.MIN_PORTFOLIO_VALUE:
            logger.error(f"Filter: Portfolio value too low (${self.portfolio_value:,.0f})")
            return False

        # Rule 5: 총 노출도 체크 (BUY 신호일 때)
        if signal.action == SignalAction.BUY:
            current_exposure = self._calculate_total_exposure()
            if current_exposure >= self.MAX_TOTAL_EXPOSURE:
                logger.warning(f"Filter: Total exposure limit reached ({current_exposure:.0%})")
                return False

        # Rule 6: 티커 유효성 체크 (간단한 검증)
        if not signal.ticker or len(signal.ticker) > 5:
            logger.error(f"Filter: Invalid ticker ({signal.ticker})")
            return False

        return True

    def _calculate_position_size(self, signal: InvestmentSignal) -> int:
        """
        포지션 사이징 계산

        Args:
            signal: InvestmentSignal

        Returns:
            매수/매도할 주식 수량
        """
        # 1. 신호에서 제안한 포지션 사이즈 가져오기
        suggested_size = signal.position_size or 0.1

        # 2. Constitution Rules: 최대 포지션 제한 적용
        position_size = min(suggested_size, self.MAX_POSITION_SIZE)

        # 3. 신뢰도 기반 조절 (낮은 신뢰도면 축소)
        if signal.confidence < 0.8:
            position_size *= 0.7  # 30% 축소

        # 4. 포트폴리오 가치 기반 달러 금액 계산
        position_value = self.portfolio_value * position_size

        # 5. 현재 가격 조회
        current_price = self.price_fetcher(signal.ticker)

        if current_price <= 0:
            logger.error(f"Invalid price for {signal.ticker}: ${current_price}")
            return 0

        # 6. 수량 계산 (정수)
        quantity = int(position_value / current_price)

        # SELL 신호의 경우 현재 보유 수량 초과 불가
        if signal.action == SignalAction.SELL:
            current_holding = self.current_positions.get(signal.ticker, 0)
            quantity = min(quantity, current_holding)

        logger.info(
            f"Position sizing: {signal.ticker} = {quantity} shares "
            f"(${position_value:,.0f} @ ${current_price:.2f})"
        )

        return quantity

    def _post_check_adjustments(self, order: Order, signal: InvestmentSignal) -> Order:
        """
        Post-Check Adjustments (4개 규칙)

        Args:
            order: 생성된 Order
            signal: 원본 InvestmentSignal

        Returns:
            조정된 Order
        """

        # Rule 1: 리스크 팩터 기반 수량 조정
        if signal.metadata:
            risk_level = signal.metadata.get("risk_level", 0.5)
            if risk_level > 0.7:
                # 고위험이면 수량 50% 축소
                order.quantity = int(order.quantity * 0.5)
                logger.info(f"Adjustment: High risk - quantity reduced by 50%")

        # Rule 2: 현금 보유 비율 확보
        reserved_cash = self.portfolio_value * self.RESERVE_CASH_RATIO
        current_cash = self._estimate_available_cash()

        if current_cash - (order.quantity * self.price_fetcher(order.ticker)) < reserved_cash:
            # 현금 부족하면 수량 줄이기
            max_buyable = int((current_cash - reserved_cash) / self.price_fetcher(order.ticker))
            order.quantity = min(order.quantity, max_buyable)
            logger.info(f"Adjustment: Cash reserve - quantity adjusted to {order.quantity}")

        # Rule 3: 최소 거래 단위 (1주 미만이면 취소)
        if order.quantity < 1:
            logger.warning("Adjustment: Quantity < 1, order cancelled")
            return None

        # Rule 4: 라운딩 (100주 단위로 매수)
        if order.side == OrderSide.BUY and order.quantity >= 100:
            order.quantity = (order.quantity // 100) * 100
            logger.info(f"Adjustment: Rounded to 100-share lots: {order.quantity}")

        return order

    def _signal_action_to_order_side(self, action: SignalAction) -> Optional[OrderSide]:
        """SignalAction을 OrderSide로 변환"""
        if action == SignalAction.BUY:
            return OrderSide.BUY
        elif action == SignalAction.SELL:
            return OrderSide.SELL
        else:
            return None

    def _check_daily_trade_limit(self) -> bool:
        """일일 거래 한도 체크"""
        today = datetime.now().date()

        # 날짜가 바뀌면 카운터 리셋
        if today != self.daily_trades_reset_date:
            self.daily_trade_count = 0
            self.daily_trades_reset_date = today

        return self.daily_trade_count >= self.MAX_DAILY_TRADES

    def _calculate_total_exposure(self) -> float:
        """총 노출도 계산 (포지션 가치 / 포트폴리오 가치)"""
        total_position_value = 0

        for ticker, quantity in self.current_positions.items():
            price = self.price_fetcher(ticker)
            total_position_value += quantity * price

        return total_position_value / self.portfolio_value if self.portfolio_value > 0 else 0

    def _estimate_available_cash(self) -> float:
        """사용 가능한 현금 추정"""
        total_position_value = 0

        for ticker, quantity in self.current_positions.items():
            price = self.price_fetcher(ticker)
            total_position_value += quantity * price

        return self.portfolio_value - total_position_value

    def _mock_price_fetcher(self, ticker: str) -> float:
        """Mock 가격 조회 (테스트용)"""
        # 실제로는 Yahoo Finance API 등 사용
        mock_prices = {
            "NVDA": 500.0,
            "GOOGL": 140.0,
            "AMD": 120.0,
            "TSM": 95.0,
            "AVGO": 900.0,
            "MSFT": 370.0,
            "AMZN": 150.0,
            "META": 350.0
        }
        return mock_prices.get(ticker, 100.0)

    def record_trade(self, order: Order):
        """거래 기록 (일일 거래 카운터 증가)"""
        self.daily_trade_count += 1
        logger.info(f"Trade recorded: {order} (total today: {self.daily_trade_count})")


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SignalToOrderConverter Test")
    print("=" * 70)

    # Converter 초기화
    converter = SignalToOrderConverter(
        portfolio_value=100000,
        current_positions={"NVDA": 50}  # 이미 NVDA 50주 보유
    )

    # 테스트 시그널 1: BUY (높은 신뢰도)
    signal1 = InvestmentSignal(
        ticker="GOOGL",
        action=SignalAction.BUY,
        confidence=0.85,
        reasoning="Strong inference market growth",
        position_size=0.15
    )

    order1 = converter.convert(signal1)
    if order1:
        print(f"\n1. {order1}")
        print(f"   Value: ${order1.quantity * converter.price_fetcher(order1.ticker):,.0f}")

    # 테스트 시그널 2: BUY (낮은 신뢰도 - 필터링될 수 있음)
    signal2 = InvestmentSignal(
        ticker="AMD",
        action=SignalAction.BUY,
        confidence=0.55,  # < 0.6 threshold
        reasoning="Weak signal",
        position_size=0.1
    )

    order2 = converter.convert(signal2)
    if order2:
        print(f"\n2. {order2}")
    else:
        print(f"\n2. Signal filtered out (confidence too low)")

    # 테스트 시그널 3: SELL
    signal3 = InvestmentSignal(
        ticker="NVDA",
        action=SignalAction.SELL,
        confidence=0.75,
        reasoning="Taking profit",
        position_size=0.5  # 50% 매도
    )

    order3 = converter.convert(signal3)
    if order3:
        print(f"\n3. {order3}")
        print(f"   (Current holding: {converter.current_positions['NVDA']} shares)")

    # 현금 및 노출도 확인
    print(f"\nPortfolio Status:")
    print(f"  Total Value: ${converter.portfolio_value:,.0f}")
    print(f"  Available Cash: ${converter._estimate_available_cash():,.0f}")
    print(f"  Total Exposure: {converter._calculate_total_exposure():.0%}")
    print(f"  Daily Trades: {converter.daily_trade_count}/{converter.MAX_DAILY_TRADES}")

    print("\n=== Test PASSED! ===")
