"""
Signal Executor Service

신호 승인 시 KIS 브로커를 통해 실제 주문 실행

Features:
- 신호 → KIS 주문 변환
- 자동 주문 실행
- 주문 상태 추적
- 에러 처리 및 재시도
- 실행 히스토리 저장

Author: AI Trading System
Date: 2025-12-03
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """주문 상태"""
    PENDING = "PENDING"      # 대기 중
    SUBMITTED = "SUBMITTED"  # 제출됨
    FILLED = "FILLED"        # 체결됨
    PARTIAL = "PARTIAL"      # 부분 체결
    CANCELLED = "CANCELLED"  # 취소됨
    REJECTED = "REJECTED"    # 거부됨
    FAILED = "FAILED"        # 실패


class ExecutionResult:
    """주문 실행 결과"""

    def __init__(
        self,
        success: bool,
        order_id: Optional[str] = None,
        status: OrderStatus = OrderStatus.PENDING,
        message: str = "",
        kis_response: Optional[Dict] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.order_id = order_id
        self.status = status
        self.message = message
        self.kis_response = kis_response
        self.error = error
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "success": self.success,
            "order_id": self.order_id,
            "status": self.status.value,
            "message": self.message,
            "kis_response": self.kis_response,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class SignalExecutor:
    """
    신호 실행기

    신호를 KIS 브로커 주문으로 변환하고 실행합니다.

    Usage:
        executor = SignalExecutor(use_paper_trading=True)
        result = await executor.execute_signal(signal)
    """

    def __init__(
        self,
        use_paper_trading: bool = True,
        max_retries: int = 3,
        enable_auto_execute: bool = False,
    ):
        """
        Args:
            use_paper_trading: 모의투자 사용 여부 (기본: True, 안전)
            max_retries: 실패 시 재시도 횟수
            enable_auto_execute: 자동 실행 활성화 (신호의 auto_execute=True 일 때만)
        """
        self.use_paper_trading = use_paper_trading
        self.max_retries = max_retries
        self.enable_auto_execute = enable_auto_execute

        # KIS Client (lazy loading)
        self._kis_client = None

        # 실행 히스토리
        self.execution_history: List[Dict] = []

        # 통계
        self.stats = {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "rejected": 0,
            "total_volume": 0.0,  # 총 거래 금액
        }

        logger.info(
            f"SignalExecutor initialized: "
            f"paper_trading={use_paper_trading}, "
            f"auto_execute={enable_auto_execute}"
        )

    def _get_kis_client(self):
        """KIS 클라이언트 가져오기 (lazy loading)"""
        if self._kis_client is None:
            try:
                from backend.trading.kis_client import KISClient

                self._kis_client = KISClient(
                    use_paper=self.use_paper_trading
                )

                # 인증 토큰 확보
                if not self._kis_client.get_access_token():
                    logger.error("Failed to get KIS access token")
                    return None

                logger.info("KIS client initialized successfully")

            except ImportError:
                logger.error("KIS client not available")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize KIS client: {e}")
                return None

        return self._kis_client

    async def execute_signal(
        self,
        signal: Dict[str, Any],
        force_execute: bool = False,
    ) -> ExecutionResult:
        """
        신호 실행

        Args:
            signal: 트레이딩 신호 (dict)
            force_execute: 강제 실행 (auto_execute 무시)

        Returns:
            ExecutionResult
        """
        self.stats["total_executions"] += 1

        # 1. 자동 실행 권한 체크
        if not force_execute and not self.enable_auto_execute:
            logger.warning("Auto execution is disabled")
            return ExecutionResult(
                success=False,
                status=OrderStatus.REJECTED,
                message="Auto execution is disabled. Use force_execute=True or enable auto_execute.",
                error="AUTO_EXECUTE_DISABLED"
            )

        if not force_execute and not signal.get("auto_execute", False):
            logger.info(f"Signal {signal.get('ticker')} auto_execute=False, skipping")
            return ExecutionResult(
                success=False,
                status=OrderStatus.REJECTED,
                message="Signal auto_execute flag is False",
                error="SIGNAL_NOT_AUTO_EXECUTABLE"
            )

        # 2. 신호 검증
        if not self._validate_signal(signal):
            self.stats["rejected"] += 1
            return ExecutionResult(
                success=False,
                status=OrderStatus.REJECTED,
                message="Signal validation failed",
                error="INVALID_SIGNAL"
            )

        # 3. KIS 클라이언트 확보
        kis = self._get_kis_client()
        if not kis:
            self.stats["failed"] += 1
            return ExecutionResult(
                success=False,
                status=OrderStatus.FAILED,
                message="KIS client not available",
                error="KIS_CLIENT_UNAVAILABLE"
            )

        # 4. 주문 실행 (재시도 포함)
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Executing signal: {signal['action']} {signal['ticker']} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

                result = await self._execute_order(kis, signal)

                if result.success:
                    self.stats["successful"] += 1

                    # 히스토리 저장
                    self.execution_history.append({
                        "signal": signal,
                        "result": result.to_dict(),
                        "timestamp": datetime.now().isoformat()
                    })

                    # 히스토리 제한 (최근 100개)
                    if len(self.execution_history) > 100:
                        self.execution_history = self.execution_history[-100:]

                    return result

                # 실패 시 재시도
                if attempt < self.max_retries - 1:
                    logger.warning(f"Execution failed, retrying in 2 seconds...")
                    await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Execution error: {e}", exc_info=True)

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    # 최종 실패
                    self.stats["failed"] += 1
                    return ExecutionResult(
                        success=False,
                        status=OrderStatus.FAILED,
                        message=f"Execution failed after {self.max_retries} attempts",
                        error=str(e)
                    )

        # 모든 재시도 실패
        self.stats["failed"] += 1
        return ExecutionResult(
            success=False,
            status=OrderStatus.FAILED,
            message=f"Execution failed after {self.max_retries} attempts",
            error="MAX_RETRIES_EXCEEDED"
        )

    def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """신호 유효성 검증"""

        # 필수 필드 체크
        required_fields = ["ticker", "action", "position_size", "confidence"]
        for field in required_fields:
            if field not in signal:
                logger.error(f"Missing required field: {field}")
                return False

        # Action 체크
        if signal["action"] not in ["BUY", "SELL"]:
            logger.error(f"Invalid action: {signal['action']}")
            return False

        # Position size 체크
        if signal["position_size"] <= 0 or signal["position_size"] > 1.0:
            logger.error(f"Invalid position_size: {signal['position_size']}")
            return False

        # Confidence 체크
        if signal["confidence"] < 0.6:
            logger.warning(f"Low confidence: {signal['confidence']}")
            return False

        return True

    async def _execute_order(
        self,
        kis,
        signal: Dict[str, Any]
    ) -> ExecutionResult:
        """
        실제 주문 실행

        Args:
            kis: KIS 클라이언트
            signal: 신호

        Returns:
            ExecutionResult
        """
        ticker = signal["ticker"]
        action = signal["action"]
        position_size = signal["position_size"]

        try:
            # 1. 현재 가격 조회
            current_price = await self._get_current_price(kis, ticker)
            if not current_price:
                return ExecutionResult(
                    success=False,
                    status=OrderStatus.FAILED,
                    message=f"Failed to get current price for {ticker}",
                    error="PRICE_FETCH_FAILED"
                )

            # 2. 계좌 잔고 조회
            balance = await self._get_account_balance(kis)
            if not balance:
                return ExecutionResult(
                    success=False,
                    status=OrderStatus.FAILED,
                    message="Failed to get account balance",
                    error="BALANCE_FETCH_FAILED"
                )

            # 3. 주문 수량 계산
            quantity = self._calculate_quantity(
                balance,
                current_price,
                position_size
            )

            if quantity <= 0:
                return ExecutionResult(
                    success=False,
                    status=OrderStatus.REJECTED,
                    message=f"Insufficient balance or invalid quantity: {quantity}",
                    error="INSUFFICIENT_BALANCE"
                )

            # 4. 주문 실행
            execution_type = signal.get("execution_type", "LIMIT")

            if execution_type == "MARKET":
                # 시장가 주문
                order_result = await self._market_order(
                    kis, ticker, action, quantity
                )
            else:
                # 지정가 주문 (기본)
                order_result = await self._limit_order(
                    kis, ticker, action, quantity, current_price
                )

            if order_result["success"]:
                logger.info(
                    f"Order executed: {action} {quantity} shares of {ticker} "
                    f"@ ${current_price:.2f}"
                )

                # 통계 업데이트
                self.stats["total_volume"] += quantity * current_price

                return ExecutionResult(
                    success=True,
                    order_id=order_result.get("order_id"),
                    status=OrderStatus.SUBMITTED,
                    message=f"Order submitted: {action} {quantity} shares @ ${current_price:.2f}",
                    kis_response=order_result
                )
            else:
                return ExecutionResult(
                    success=False,
                    status=OrderStatus.FAILED,
                    message=order_result.get("message", "Order execution failed"),
                    kis_response=order_result,
                    error=order_result.get("error")
                )

        except Exception as e:
            logger.error(f"Order execution error: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                status=OrderStatus.FAILED,
                message=str(e),
                error="EXECUTION_EXCEPTION"
            )

    async def _get_current_price(self, kis, ticker: str) -> Optional[float]:
        """현재가 조회"""
        try:
            # KIS API 호출 (동기 함수를 비동기로 래핑)
            response = await asyncio.to_thread(
                kis.get_current_price,
                ticker
            )

            if response and response.isOK():
                body = response.getBody()
                price = float(body.output.stck_prpr)  # 현재가
                return price

            return None

        except Exception as e:
            logger.error(f"Failed to get current price: {e}")
            return None

    async def _get_account_balance(self, kis) -> Optional[float]:
        """계좌 잔고 조회"""
        try:
            # KIS API 호출
            response = await asyncio.to_thread(
                kis.get_balance
            )

            if response and response.isOK():
                body = response.getBody()
                # 예수금 (주문 가능 금액)
                balance = float(body.output2[0].dnca_tot_amt)
                return balance

            return None

        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            return None

    def _calculate_quantity(
        self,
        balance: float,
        price: float,
        position_size: float
    ) -> int:
        """주문 수량 계산"""

        # 투자 금액 = 잔고 × position_size
        investment_amount = balance * position_size

        # 수량 = 투자 금액 / 주가 (정수로 내림)
        quantity = int(investment_amount / price)

        logger.info(
            f"Calculated quantity: {quantity} "
            f"(balance=${balance:.2f}, price=${price:.2f}, size={position_size:.1%})"
        )

        return quantity

    async def _market_order(
        self,
        kis,
        ticker: str,
        action: str,
        quantity: int
    ) -> Dict[str, Any]:
        """시장가 주문"""
        try:
            if action == "BUY":
                response = await asyncio.to_thread(
                    kis.buy_market_order,
                    ticker,
                    quantity
                )
            else:  # SELL
                response = await asyncio.to_thread(
                    kis.sell_market_order,
                    ticker,
                    quantity
                )

            if response and response.isOK():
                body = response.getBody()
                return {
                    "success": True,
                    "order_id": body.output.ODNO,  # 주문번호
                    "message": response.getMessage()
                }
            else:
                return {
                    "success": False,
                    "message": response.getMessage() if response else "Unknown error",
                    "error": response.getReturnCode() if response else "NO_RESPONSE"
                }

        except Exception as e:
            logger.error(f"Market order error: {e}")
            return {
                "success": False,
                "message": str(e),
                "error": "MARKET_ORDER_EXCEPTION"
            }

    async def _limit_order(
        self,
        kis,
        ticker: str,
        action: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """지정가 주문"""
        try:
            if action == "BUY":
                response = await asyncio.to_thread(
                    kis.buy_limit_order,
                    ticker,
                    quantity,
                    int(price)  # 원화는 정수
                )
            else:  # SELL
                response = await asyncio.to_thread(
                    kis.sell_limit_order,
                    ticker,
                    quantity,
                    int(price)
                )

            if response and response.isOK():
                body = response.getBody()
                return {
                    "success": True,
                    "order_id": body.output.ODNO,
                    "message": response.getMessage()
                }
            else:
                return {
                    "success": False,
                    "message": response.getMessage() if response else "Unknown error",
                    "error": response.getReturnCode() if response else "NO_RESPONSE"
                }

        except Exception as e:
            logger.error(f"Limit order error: {e}")
            return {
                "success": False,
                "message": str(e),
                "error": "LIMIT_ORDER_EXCEPTION"
            }

    def get_statistics(self) -> Dict[str, Any]:
        """통계 조회"""
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful"] / self.stats["total_executions"]
                if self.stats["total_executions"] > 0 else 0
            ),
            "history_count": len(self.execution_history)
        }

    def get_execution_history(self, limit: int = 10) -> List[Dict]:
        """실행 히스토리 조회"""
        return self.execution_history[-limit:]


# ============================================================================
# Global Executor Instance
# ============================================================================

_global_executor: Optional[SignalExecutor] = None


def get_signal_executor(
    use_paper_trading: bool = True,
    enable_auto_execute: bool = False
) -> SignalExecutor:
    """전역 실행기 인스턴스 가져오기"""
    global _global_executor

    if _global_executor is None:
        _global_executor = SignalExecutor(
            use_paper_trading=use_paper_trading,
            enable_auto_execute=enable_auto_execute
        )
        logger.info("Global SignalExecutor created")

    return _global_executor
