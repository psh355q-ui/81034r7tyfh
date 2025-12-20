"""
Auto Trader - 자동 거래 실행기

Phase E + Option 2 통합
Consensus 승인 시 자동으로 주문 실행

핵심 기능:
1. on_consensus_approved: Consensus 승인 → 자동 주문
2. execute_buy: BUY 시그널 → 주문 실행
3. execute_sell: SELL 시그널 → 청산
4. execute_dca: DCA 승인 → 추가 매수

작성일: 2025-12-06
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum

from backend.ai.consensus.consensus_models import ConsensusResult
from backend.data.position_tracker import PositionTracker
from backend.services.broker_position_sync import BrokerPositionSync

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    """주문 유형"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class AutoTrader:
    """
    자동 거래 실행기

    Consensus 승인된 시그널을 자동으로 주문 실행

    Usage:
        trader = AutoTrader(broker, position_tracker)
        result = await trader.on_consensus_approved(consensus_result, market_context)
    """

    def __init__(
        self,
        kis_broker=None,
        position_tracker: Optional[PositionTracker] = None,
        broker_sync: Optional[BrokerPositionSync] = None,
        auto_execute: bool = False,
        position_size_pct: float = 0.05,
        max_position_count: int = 10
    ):
        """
        Initialize Auto Trader

        Args:
            kis_broker: KIS Broker 인스턴스
            position_tracker: Position Tracker
            broker_sync: Broker-Position Sync
            auto_execute: 자동 실행 여부 (False면 dry-run)
            position_size_pct: 포트폴리오 대비 포지션 크기 (0.05 = 5%)
            max_position_count: 최대 포지션 개수
        """
        self.broker = kis_broker
        self.position_tracker = position_tracker or PositionTracker()
        self.broker_sync = broker_sync or BrokerPositionSync(self.position_tracker, kis_broker)
        self.auto_execute = auto_execute
        self.position_size_pct = position_size_pct
        self.max_position_count = max_position_count

        # 실행 로그
        self.execution_history = []

        logger.info(
            f"AutoTrader initialized: auto_execute={auto_execute}, "
            f"position_size={position_size_pct:.0%}, max_positions={max_position_count}"
        )

    async def on_consensus_approved(
        self,
        consensus_result: ConsensusResult,
        market_context=None,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Consensus 승인 시 자동 주문 실행

        Args:
            consensus_result: Consensus 투표 결과
            market_context: 시장 컨텍스트
            current_price: 현재 가격 (없으면 Broker에서 조회)

        Returns:
            실행 결과
        """
        if not consensus_result.approved:
            logger.warning("Consensus not approved, skipping execution")
            return {"error": "consensus_not_approved"}

        action = consensus_result.action
        ticker = consensus_result.ticker or market_context.ticker if market_context else None

        if not ticker:
            logger.error("Ticker not found in consensus result")
            return {"error": "ticker_missing"}

        logger.info(f"Consensus APPROVED: {action} {ticker}")

        result = {
            "action": action,
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "consensus_strength": consensus_result.consensus_strength.value,
            "executed": False
        }

        try:
            if action == "BUY":
                exec_result = await self.execute_buy(
                    ticker=ticker,
                    consensus_result=consensus_result,
                    current_price=current_price
                )
                result.update(exec_result)

            elif action == "SELL":
                exec_result = await self.execute_sell(
                    ticker=ticker,
                    consensus_result=consensus_result,
                    current_price=current_price
                )
                result.update(exec_result)

            elif action == "DCA":
                exec_result = await self.execute_dca(
                    ticker=ticker,
                    consensus_result=consensus_result,
                    current_price=current_price
                )
                result.update(exec_result)

            elif action == "STOP_LOSS":
                exec_result = await self.execute_stop_loss(
                    ticker=ticker,
                    consensus_result=consensus_result,
                    current_price=current_price
                )
                result.update(exec_result)

            else:
                logger.warning(f"Unknown action: {action}")
                result["error"] = f"unknown_action: {action}"

        except Exception as e:
            logger.error(f"Auto trading error: {e}")
            result["error"] = str(e)

        # 실행 로그 저장
        self.execution_history.append(result)

        return result

    async def execute_buy(
        self,
        ticker: str,
        consensus_result: ConsensusResult,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        BUY 주문 실행

        Args:
            ticker: 종목 티커
            consensus_result: Consensus 결과
            current_price: 현재 가격

        Returns:
            실행 결과
        """
        logger.info(f"Executing BUY order for {ticker}...")

        result = {
            "order_type": "BUY",
            "executed": False
        }

        # 1. 포지션 개수 체크
        open_positions = len(self.position_tracker.get_all_positions())
        if open_positions >= self.max_position_count:
            logger.warning(f"Max position count reached: {open_positions}/{self.max_position_count}")
            result["error"] = "max_positions_reached"
            return result

        # 2. 현재 가격 조회
        if current_price is None:
            if self.broker:
                price_info = self.broker.get_price(ticker)
                current_price = price_info.get("current_price") if price_info else None

            if current_price is None:
                logger.error(f"Cannot get price for {ticker}")
                result["error"] = "price_not_available"
                return result

        result["current_price"] = current_price

        # 3. 포지션 크기 계산
        # 간단히 고정 금액 사용 (실제로는 포트폴리오 총액 기반)
        position_size_usd = 10000.0 * self.position_size_pct
        quantity = int(position_size_usd / current_price)

        if quantity < 1:
            logger.warning(f"Insufficient amount for 1 share: ${position_size_usd:.2f} < ${current_price:.2f}")
            result["error"] = "insufficient_amount"
            return result

        result["position_size_usd"] = position_size_usd
        result["quantity"] = quantity

        # 4. 주문 실행 (실제 또는 dry-run)
        if self.auto_execute and self.broker:
            logger.info(f"[REAL] Placing BUY order: {quantity} {ticker} @ ${current_price:.2f}")

            try:
                order_result = self.broker.place_order(
                    symbol=ticker,
                    side="BUY",
                    quantity=quantity,
                    order_type=OrderType.MARKET.value
                )

                if order_result and order_result.get("success"):
                    result["executed"] = True
                    result["order_id"] = order_result.get("order_id")
                    result["status"] = order_result.get("status")

                    logger.info(f"Order placed successfully: {result['order_id']}")

                    # Position에 기록 (체결 후 콜백에서 처리하는 것이 더 정확하지만, 여기서는 즉시 기록)
                    await self.broker_sync.on_order_filled(
                        ticker=ticker,
                        company_name=ticker,
                        side="BUY",
                        quantity=quantity,
                        avg_price=current_price,
                        order_id=result["order_id"],
                        filled_at=datetime.now()
                    )

                else:
                    logger.error(f"Order placement failed: {order_result}")
                    result["error"] = order_result.get("error", "order_failed")

            except Exception as e:
                logger.error(f"Order execution error: {e}")
                result["error"] = str(e)

        else:
            # Dry-run mode
            logger.info(f"[DRY-RUN] Would place BUY order: {quantity} {ticker} @ ${current_price:.2f}")
            result["executed"] = False
            result["dry_run"] = True

        return result

    async def execute_sell(
        self,
        ticker: str,
        consensus_result: ConsensusResult,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        SELL 주문 실행 (포지션 청산)

        Args:
            ticker: 종목 티커
            consensus_result: Consensus 결과
            current_price: 현재 가격

        Returns:
            실행 결과
        """
        logger.info(f"Executing SELL order for {ticker}...")

        result = {
            "order_type": "SELL",
            "executed": False
        }

        # 1. 포지션 확인
        position = self.position_tracker.get_position(ticker)
        if position is None:
            logger.warning(f"No position found for {ticker}")
            result["error"] = "no_position"
            return result

        quantity = position.total_shares
        result["quantity"] = quantity

        # 2. 현재 가격 조회
        if current_price is None:
            if self.broker:
                price_info = self.broker.get_price(ticker)
                current_price = price_info.get("current_price") if price_info else None

            if current_price is None:
                current_price = position.avg_entry_price

        result["current_price"] = current_price

        # 3. 주문 실행
        if self.auto_execute and self.broker:
            logger.info(f"[REAL] Placing SELL order: {quantity} {ticker} @ ${current_price:.2f}")

            try:
                order_result = self.broker.place_order(
                    symbol=ticker,
                    side="SELL",
                    quantity=quantity,
                    order_type=OrderType.MARKET.value
                )

                if order_result and order_result.get("success"):
                    result["executed"] = True
                    result["order_id"] = order_result.get("order_id")

                    # Position 청산
                    await self.broker_sync.on_order_filled(
                        ticker=ticker,
                        company_name=position.company_name,
                        side="SELL",
                        quantity=quantity,
                        avg_price=current_price,
                        order_id=result["order_id"],
                        filled_at=datetime.now()
                    )

                    logger.info(f"Position closed: {ticker}")

                else:
                    result["error"] = order_result.get("error", "order_failed")

            except Exception as e:
                logger.error(f"Sell order error: {e}")
                result["error"] = str(e)

        else:
            logger.info(f"[DRY-RUN] Would place SELL order: {quantity} {ticker}")
            result["dry_run"] = True

        return result

    async def execute_dca(
        self,
        ticker: str,
        consensus_result: ConsensusResult,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        DCA 주문 실행 (추가 매수)

        Args:
            ticker: 종목 티커
            consensus_result: Consensus 결과
            current_price: 현재 가격

        Returns:
            실행 결과
        """
        logger.info(f"Executing DCA order for {ticker}...")

        result = {
            "order_type": "DCA",
            "executed": False
        }

        # 1. 포지션 확인
        position = self.position_tracker.get_position(ticker)
        if position is None:
            logger.warning(f"No position found for {ticker}, cannot DCA")
            result["error"] = "no_position"
            return result

        # 2. 현재 가격 조회
        if current_price is None:
            if self.broker:
                price_info = self.broker.get_price(ticker)
                current_price = price_info.get("current_price") if price_info else None

            if current_price is None:
                logger.error(f"Cannot get price for {ticker}")
                result["error"] = "price_not_available"
                return result

        result["current_price"] = current_price

        # 3. DCA 크기 계산 (점진적 감소)
        dca_sizes = [0.5, 0.33, 0.25]  # 1차, 2차, 3차
        dca_size = dca_sizes[position.dca_count] if position.dca_count < len(dca_sizes) else 0.25

        dca_amount = position.total_invested / (position.dca_count + 1) * dca_size
        quantity = int(dca_amount / current_price)

        if quantity < 1:
            logger.warning(f"DCA amount too small: ${dca_amount:.2f}")
            result["error"] = "insufficient_dca_amount"
            return result

        result["dca_amount"] = dca_amount
        result["quantity"] = quantity
        result["dca_number"] = position.dca_count + 1

        # 4. 주문 실행
        if self.auto_execute and self.broker:
            logger.info(f"[REAL] Placing DCA order: {quantity} {ticker} @ ${current_price:.2f}")

            try:
                order_result = self.broker.place_order(
                    symbol=ticker,
                    side="BUY",
                    quantity=quantity,
                    order_type=OrderType.MARKET.value
                )

                if order_result and order_result.get("success"):
                    result["executed"] = True
                    result["order_id"] = order_result.get("order_id")

                    # DCA 기록
                    await self.broker_sync.on_order_filled(
                        ticker=ticker,
                        company_name=position.company_name,
                        side="BUY",
                        quantity=quantity,
                        avg_price=current_price,
                        order_id=result["order_id"],
                        filled_at=datetime.now()
                    )

                    logger.info(f"DCA executed: {position.dca_count} -> {position.dca_count + 1}")

                else:
                    result["error"] = order_result.get("error", "order_failed")

            except Exception as e:
                logger.error(f"DCA order error: {e}")
                result["error"] = str(e)

        else:
            logger.info(f"[DRY-RUN] Would place DCA order: {quantity} {ticker}")
            result["dry_run"] = True

        return result

    async def execute_stop_loss(
        self,
        ticker: str,
        consensus_result: ConsensusResult,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        STOP_LOSS 실행 (긴급 청산)

        Args:
            ticker: 종목 티커
            consensus_result: Consensus 결과
            current_price: 현재 가격

        Returns:
            실행 결과
        """
        logger.warning(f"Executing STOP_LOSS for {ticker}...")

        # STOP_LOSS는 SELL과 동일하지만 우선순위가 높음
        result = await self.execute_sell(ticker, consensus_result, current_price)
        result["order_type"] = "STOP_LOSS"
        result["reason"] = "stop_loss_triggered"

        return result

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        실행 요약 통계

        Returns:
            실행 통계
        """
        total_executions = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e.get("executed"))

        by_action = {}
        for entry in self.execution_history:
            action = entry.get("action", "UNKNOWN")
            by_action[action] = by_action.get(action, 0) + 1

        return {
            "total_executions": total_executions,
            "successful": successful,
            "failed": total_executions - successful,
            "success_rate": successful / total_executions if total_executions > 0 else 0,
            "by_action": by_action,
            "last_execution": self.execution_history[-1] if self.execution_history else None
        }


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    import asyncio
    from backend.ai.consensus.consensus_models import ConsensusResult, ConsensusStrength, AIVote, VoteDecision

    async def test():
        print("=" * 80)
        print("AutoTrader Test")
        print("=" * 80)

        # 초기화 (dry-run mode)
        trader = AutoTrader(
            kis_broker=None,
            auto_execute=False  # Dry-run
        )

        # Mock Consensus 결과
        mock_consensus = ConsensusResult(
            approved=True,
            action="BUY",
            votes={
                "claude": AIVote(
                    ai_model="claude",
                    decision=VoteDecision.APPROVE,
                    confidence=0.85,
                    reasoning="Strong fundamentals"
                )
            },
            approve_count=2,
            reject_count=1,
            total_votes=3,
            consensus_strength=ConsensusStrength.STRONG,
            confidence_avg=0.8,
            ticker="AAPL",
            vote_requirement="2/3"
        )

        # BUY 실행
        print("\n[Test 1] Execute BUY")
        result1 = await trader.on_consensus_approved(
            consensus_result=mock_consensus,
            current_price=150.0
        )

        print(f"Action: {result1['action']}")
        print(f"Executed: {result1['executed']}")
        print(f"Dry-run: {result1.get('dry_run', False)}")
        if result1.get('quantity'):
            print(f"Quantity: {result1['quantity']} shares @ ${result1['current_price']:.2f}")

        # 실행 요약
        print("\n[Execution Summary]")
        summary = trader.get_execution_summary()
        print(f"Total: {summary['total_executions']}")
        print(f"Success Rate: {summary['success_rate']:.0%}")
        print(f"By Action: {summary['by_action']}")

    asyncio.run(test())
