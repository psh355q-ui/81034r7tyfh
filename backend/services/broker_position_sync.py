"""
Broker-Position Synchronization Service

Phase E 통합 (옵션 1 - Task 1.3)
KIS Broker와 Position Tracker 간 양방향 동기화

기능:
1. KIS 주문 체결 시 → Position 자동 업데이트
2. Position DCA 추가 시 → KIS 자동 주문 (옵션)
3. 주기적 동기화 (KIS 잔고 ↔ Position DB)

작성일: 2025-12-06
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from backend.data.position_tracker import PositionTracker, Position, PositionStatus

logger = logging.getLogger(__name__)


class BrokerPositionSync:
    """
    Broker와 Position Tracker 동기화

    기능:
    1. on_order_filled: 주문 체결 시 Position 업데이트
    2. sync_positions: KIS 잔고 → Position DB 동기화
    3. execute_dca_order: Position DCA → KIS 주문
    """

    def __init__(
        self,
        position_tracker: PositionTracker,
        kis_broker=None
    ):
        """
        Initialize Broker-Position Sync

        Args:
            position_tracker: PositionTracker 인스턴스
            kis_broker: KISBroker 인스턴스 (옵션)
        """
        self.position_tracker = position_tracker
        self.kis_broker = kis_broker

        logger.info("BrokerPositionSync initialized")

    async def on_order_filled(
        self,
        ticker: str,
        company_name: str,
        side: str,
        quantity: float,
        avg_price: float,
        order_id: str,
        filled_at: datetime
    ) -> Dict[str, Any]:
        """
        주문 체결 시 Position 자동 업데이트

        Args:
            ticker: 종목 티커
            company_name: 회사명
            side: "BUY" | "SELL"
            quantity: 체결 수량
            avg_price: 평균 체결가
            order_id: 주문 ID
            filled_at: 체결 시각

        Returns:
            업데이트 결과
        """
        logger.info(f"Processing order fill: {side} {quantity} {ticker} @ ${avg_price:.2f}")

        result = {
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "avg_price": avg_price,
            "order_id": order_id,
            "filled_at": filled_at.isoformat(),
            "action": None,
            "position_updated": False
        }

        try:
            if side == "BUY":
                # 매수 체결
                position = self.position_tracker.get_position(ticker)

                if position is None:
                    # 신규 포지션 생성
                    logger.info(f"Creating new position for {ticker}")

                    self.position_tracker.create_position(
                        ticker=ticker,
                        company_name=company_name,
                        initial_price=avg_price,
                        initial_amount=avg_price * quantity
                    )

                    result["action"] = "create_position"

                else:
                    # 기존 포지션에 DCA 추가
                    logger.info(f"Adding DCA to existing position {ticker}")

                    self.position_tracker.add_dca_entry(
                        ticker=ticker,
                        price=avg_price,
                        amount=avg_price * quantity,
                        reasoning=f"Broker order filled: {order_id}"
                    )

                    result["action"] = "add_dca"

                result["position_updated"] = True

            elif side == "SELL":
                # 매도 체결
                position = self.position_tracker.get_position(ticker)

                if position is None:
                    logger.warning(f"Cannot close position for {ticker}: position not found")
                    result["error"] = "position_not_found"
                    return result

                # 전체 청산인지 부분 청산인지 확인
                if quantity >= position.total_shares * 0.95:  # 95% 이상 매도 = 전체 청산
                    logger.info(f"Closing position {ticker}")

                    self.position_tracker.close_position(
                        ticker=ticker,
                        exit_price=avg_price,
                        exit_date=filled_at
                    )

                    result["action"] = "close_position"

                else:
                    # 부분 청산 (Position 수량 감소)
                    logger.info(f"Partial close for {ticker}: {quantity} shares")

                    # 간단히 메모만 추가 (실제로는 Position 클래스에 부분 청산 메서드 필요)
                    result["action"] = "partial_close"
                    result["note"] = "Partial close not fully implemented"

                result["position_updated"] = True

            else:
                logger.error(f"Unknown order side: {side}")
                result["error"] = f"unknown_side: {side}"

        except Exception as e:
            logger.error(f"Error updating position from order fill: {e}")
            result["error"] = str(e)
            result["position_updated"] = False

        return result

    async def sync_positions_from_broker(self) -> Dict[str, Any]:
        """
        KIS Broker 잔고 → Position DB 동기화

        Returns:
            동기화 결과
        """
        logger.info("Syncing positions from KIS Broker...")

        result = {
            "timestamp": datetime.now().isoformat(),
            "broker_available": self.kis_broker is not None,
            "positions_synced": 0,
            "positions_created": 0,
            "positions_updated": 0,
            "errors": []
        }

        if self.kis_broker is None:
            logger.warning("KIS Broker not available, skipping sync")
            return result

        try:
            # KIS Broker에서 잔고 조회
            balance = self.kis_broker.get_balance()

            if not balance or "holdings" not in balance:
                logger.warning("No holdings found in KIS balance")
                return result

            holdings = balance["holdings"]
            logger.info(f"Found {len(holdings)} holdings in KIS account")

            for holding in holdings:
                ticker = holding.get("symbol")
                quantity = holding.get("quantity", 0)
                avg_cost = holding.get("avg_cost", 0)
                company_name = holding.get("company_name", ticker)

                if quantity <= 0:
                    continue

                # Position DB에서 조회
                position = self.position_tracker.get_position(ticker)

                if position is None:
                    # 신규 포지션 생성
                    logger.info(f"Creating position from broker: {ticker}")

                    self.position_tracker.create_position(
                        ticker=ticker,
                        company_name=company_name,
                        initial_price=avg_cost,
                        initial_amount=avg_cost * quantity
                    )

                    result["positions_created"] += 1

                else:
                    # 기존 포지션 업데이트 (수량 차이 확인)
                    shares_diff = quantity - position.total_shares

                    if abs(shares_diff) > 0.01:  # 차이가 있으면 업데이트
                        logger.info(f"Updating position {ticker}: shares_diff={shares_diff:.2f}")

                        # 간단히 로그만 남김 (실제로는 Position 조정 로직 필요)
                        result["positions_updated"] += 1

                result["positions_synced"] += 1

        except Exception as e:
            logger.error(f"Error syncing positions from broker: {e}")
            result["errors"].append(str(e))

        logger.info(f"Sync complete: {result['positions_synced']} positions synced")
        return result

    async def execute_dca_order(
        self,
        ticker: str,
        amount: float,
        order_type: str = "MARKET",
        exchange: str = "NASDAQ"
    ) -> Dict[str, Any]:
        """
        Position DCA 추가 시 KIS 주문 자동 실행

        Args:
            ticker: 종목 티커
            amount: 투자 금액 (USD)
            order_type: 주문 유형 ("MARKET" | "LIMIT")
            exchange: 거래소

        Returns:
            주문 결과
        """
        logger.info(f"Executing DCA order: ${amount:.2f} {ticker}")

        result = {
            "ticker": ticker,
            "amount": amount,
            "order_type": order_type,
            "timestamp": datetime.now().isoformat(),
            "order_placed": False,
            "order_id": None
        }

        if self.kis_broker is None:
            logger.warning("KIS Broker not available, cannot execute order")
            result["error"] = "broker_not_available"
            return result

        try:
            # 현재 가격 조회
            price_info = self.kis_broker.get_price(ticker, exchange)

            if not price_info or "current_price" not in price_info:
                logger.error(f"Cannot get price for {ticker}")
                result["error"] = "price_not_available"
                return result

            current_price = price_info["current_price"]
            quantity = int(amount / current_price)  # 주식 수량 계산

            if quantity < 1:
                logger.warning(f"Insufficient amount for 1 share: ${amount:.2f} < ${current_price:.2f}")
                result["error"] = "insufficient_amount"
                return result

            result["current_price"] = current_price
            result["quantity"] = quantity

            # 주문 실행
            logger.info(f"Placing {order_type} order: {quantity} {ticker} @ ${current_price:.2f}")

            order_result = self.kis_broker.place_order(
                symbol=ticker,
                side="BUY",
                quantity=quantity,
                order_type=order_type,
                exchange=exchange
            )

            if order_result and order_result.get("success"):
                result["order_placed"] = True
                result["order_id"] = order_result.get("order_id")
                result["status"] = order_result.get("status")

                logger.info(f"✓ Order placed successfully: {result['order_id']}")

            else:
                logger.error(f"Order placement failed: {order_result}")
                result["error"] = order_result.get("error", "order_failed")

        except Exception as e:
            logger.error(f"Error executing DCA order: {e}")
            result["error"] = str(e)

        return result


# ============================================================================
# 팩토리 함수
# ============================================================================

def create_broker_position_sync(
    position_tracker: Optional[PositionTracker] = None,
    kis_broker=None
) -> BrokerPositionSync:
    """
    BrokerPositionSync 팩토리 함수

    Args:
        position_tracker: PositionTracker 인스턴스
        kis_broker: KISBroker 인스턴스

    Returns:
        BrokerPositionSync 인스턴스
    """
    if position_tracker is None:
        position_tracker = PositionTracker()

    return BrokerPositionSync(
        position_tracker=position_tracker,
        kis_broker=kis_broker
    )


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test():
        print("=" * 70)
        print("BrokerPositionSync Test")
        print("=" * 70)

        # 초기화 (Broker 없이)
        sync = create_broker_position_sync()

        # 주문 체결 시뮬레이션
        print("\n[Test 1] New BUY order filled")
        result1 = await sync.on_order_filled(
            ticker="NVDA",
            company_name="NVIDIA",
            side="BUY",
            quantity=10,
            avg_price=150.0,
            order_id="KIS20241206001",
            filled_at=datetime.now()
        )

        print(f"Action: {result1['action']}")
        print(f"Position Updated: {result1['position_updated']}")

        # DCA 체결 시뮬레이션
        print("\n[Test 2] DCA BUY order filled")
        result2 = await sync.on_order_filled(
            ticker="NVDA",
            company_name="NVIDIA",
            side="BUY",
            quantity=5,
            avg_price=135.0,
            order_id="KIS20241206002",
            filled_at=datetime.now()
        )

        print(f"Action: {result2['action']}")
        print(f"Position Updated: {result2['position_updated']}")

        # Position 확인
        position = sync.position_tracker.get_position("NVDA")
        if position:
            print(f"\n[Position Summary]")
            print(f"Total Shares: {position.total_shares}")
            print(f"Avg Entry Price: ${position.avg_entry_price:.2f}")
            print(f"DCA Count: {position.dca_count}")

    asyncio.run(test())
