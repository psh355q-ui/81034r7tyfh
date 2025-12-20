"""
Stop-Loss Monitor - 실시간 손절 모니터링 서비스

Phase E + Option 2 통합
실시간으로 포지션을 모니터링하고 손절 조건 체크

핵심 기능:
1. 주기적으로 모든 포지션 체크 (1분 간격)
2. 손절 조건 체크 (손실률, 변동성, 시간 등)
3. Consensus 투표 (1/3 승인으로 즉시 실행)
4. Auto Trader로 Stop-loss 주문 전달

작성일: 2025-12-06
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from backend.data.position_tracker import PositionTracker, Position
from backend.ai.consensus.consensus_engine import ConsensusEngine
from backend.automation.auto_trader import AutoTrader
from backend.schemas.base_schema import MarketContext, NewsFeatures, MarketSegment

logger = logging.getLogger(__name__)


@dataclass
class StopLossCondition:
    """손절 조건"""
    ticker: str
    triggered: bool
    reason: str
    current_price: float
    avg_entry_price: float
    loss_pct: float
    threshold_pct: float


class StopLossMonitor:
    """
    Stop-Loss 실시간 모니터링 서비스

    Background task로 실행되며, 주기적으로 포지션 체크

    Usage:
        monitor = StopLossMonitor(position_tracker, consensus_engine, auto_trader)
        asyncio.create_task(monitor.start_monitoring())
    """

    def __init__(
        self,
        position_tracker: PositionTracker,
        consensus_engine: Optional[ConsensusEngine] = None,
        auto_trader: Optional[AutoTrader] = None,
        kis_broker=None,
        stop_loss_threshold_pct: float = -10.0,
        check_interval_seconds: int = 60,
        enable_auto_execute: bool = False
    ):
        """
        Initialize Stop-Loss Monitor

        Args:
            position_tracker: Position Tracker
            consensus_engine: Consensus Engine (옵션)
            auto_trader: Auto Trader (옵션)
            kis_broker: KIS Broker for price updates
            stop_loss_threshold_pct: 손절 기준 (-10.0 = -10%)
            check_interval_seconds: 체크 간격 (초)
            enable_auto_execute: 자동 실행 여부
        """
        self.position_tracker = position_tracker
        self.consensus_engine = consensus_engine
        self.auto_trader = auto_trader
        self.broker = kis_broker
        self.stop_loss_threshold_pct = stop_loss_threshold_pct
        self.check_interval_seconds = check_interval_seconds
        self.enable_auto_execute = enable_auto_execute

        # 모니터링 상태
        self.is_running = False
        self.check_count = 0
        self.stop_loss_triggered_count = 0

        # 트리거 이력
        self.trigger_history: List[StopLossCondition] = []

        logger.info(
            f"StopLossMonitor initialized: threshold={stop_loss_threshold_pct}%, "
            f"interval={check_interval_seconds}s, auto_execute={enable_auto_execute}"
        )

    async def start_monitoring(self):
        """
        모니터링 시작 (무한 루프)

        Background task로 실행
        """
        logger.info("Stop-Loss monitoring started")
        self.is_running = True

        try:
            while self.is_running:
                await self._check_all_positions()
                await asyncio.sleep(self.check_interval_seconds)

        except asyncio.CancelledError:
            logger.info("Stop-Loss monitoring cancelled")
            self.is_running = False

        except Exception as e:
            logger.error(f"Stop-Loss monitoring error: {e}")
            self.is_running = False

    def stop_monitoring(self):
        """모니터링 중지"""
        logger.info("Stopping Stop-Loss monitoring...")
        self.is_running = False

    async def _check_all_positions(self):
        """
        모든 포지션 체크

        Internal method - 주기적으로 호출됨
        """
        self.check_count += 1
        positions = self.position_tracker.get_all_positions()

        if not positions:
            logger.debug("No positions to monitor")
            return

        logger.info(f"[Check #{self.check_count}] Monitoring {len(positions)} positions...")

        for position in positions:
            try:
                await self._check_position(position)
            except Exception as e:
                logger.error(f"Error checking position {position.ticker}: {e}")

    async def _check_position(self, position: Position):
        """
        개별 포지션 체크

        Args:
            position: Position 객체
        """
        ticker = position.ticker

        # 1. 현재 가격 조회
        current_price = await self._get_current_price(ticker)

        if current_price is None:
            logger.warning(f"Cannot get price for {ticker}, skipping")
            return

        # 2. 손실률 계산
        loss_pct = ((current_price - position.avg_entry_price) / position.avg_entry_price) * 100

        # 3. 손절 조건 체크
        condition = StopLossCondition(
            ticker=ticker,
            triggered=False,
            reason="",
            current_price=current_price,
            avg_entry_price=position.avg_entry_price,
            loss_pct=loss_pct,
            threshold_pct=self.stop_loss_threshold_pct
        )

        if loss_pct < self.stop_loss_threshold_pct:
            condition.triggered = True
            condition.reason = f"Loss {loss_pct:.2f}% exceeds threshold {self.stop_loss_threshold_pct}%"

            logger.warning(f"STOP-LOSS TRIGGERED: {ticker} ({condition.reason})")

            self.trigger_history.append(condition)
            self.stop_loss_triggered_count += 1

            # 4. Consensus 투표 + 자동 실행
            await self._execute_stop_loss(position, condition)

        else:
            logger.debug(f"{ticker}: P&L {loss_pct:+.2f}% (OK)")

    async def _get_current_price(self, ticker: str) -> Optional[float]:
        """
        현재 가격 조회

        Args:
            ticker: 종목 티커

        Returns:
            현재 가격 (실패 시 None)
        """
        if self.broker is None:
            # Broker 없으면 Mock 가격 (테스트용)
            return None

        try:
            price_info = self.broker.get_price(ticker)
            return price_info.get("current_price") if price_info else None

        except Exception as e:
            logger.error(f"Error getting price for {ticker}: {e}")
            return None

    async def _execute_stop_loss(self, position: Position, condition: StopLossCondition):
        """
        Stop-Loss 실행

        Args:
            position: Position 객체
            condition: 손절 조건
        """
        ticker = position.ticker

        logger.warning(f"Executing STOP-LOSS for {ticker}...")

        # 1. Consensus 투표 (STOP_LOSS는 1/3만 승인해도 실행)
        if self.consensus_engine:
            logger.info(f"Running Consensus vote for STOP_LOSS on {ticker}...")

            # Mock MarketContext (실제로는 뉴스/시장 데이터 필요)
            market_context = MarketContext(
                ticker=ticker,
                company_name=position.company_name,
                chip_info=[],
                supply_chain=[],
                unit_economics=None,
                news=NewsFeatures(
                    headline=f"Stop-loss triggered for {ticker}",
                    segment=MarketSegment.TRAINING,
                    tickers_mentioned=[ticker],
                    sentiment=-0.5,  # 부정적
                    urgency="high",
                    tone="negative"
                ),
                risk_factors={"stop_loss": True},
                market_regime=None
            )

            try:
                consensus_result = await self.consensus_engine.vote_on_signal(
                    context=market_context,
                    action="STOP_LOSS",
                    additional_info={
                        "current_price": condition.current_price,
                        "avg_entry_price": condition.avg_entry_price,
                        "loss_pct": condition.loss_pct,
                        "reason": condition.reason
                    }
                )

                logger.info(
                    f"Consensus result: {consensus_result.approved} "
                    f"({consensus_result.approve_count}/{consensus_result.total_votes})"
                )

                if not consensus_result.approved:
                    logger.info(f"Consensus REJECTED stop-loss for {ticker}")
                    return

                logger.warning(f"Consensus APPROVED stop-loss for {ticker}")

            except Exception as e:
                logger.error(f"Consensus voting error: {e}")
                return

        else:
            logger.warning("No Consensus Engine, skipping vote (risky!)")
            # Consensus 없으면 자동 승인 안 함 (안전)
            return

        # 2. Auto Trader로 실행
        if self.auto_trader and self.enable_auto_execute:
            logger.warning(f"Auto-executing STOP-LOSS for {ticker}...")

            try:
                exec_result = await self.auto_trader.execute_stop_loss(
                    ticker=ticker,
                    consensus_result=consensus_result,
                    current_price=condition.current_price
                )

                if exec_result.get("executed"):
                    logger.warning(f"STOP-LOSS EXECUTED: {ticker}")
                else:
                    logger.error(f"STOP-LOSS FAILED: {ticker} - {exec_result.get('error')}")

            except Exception as e:
                logger.error(f"Stop-loss execution error: {e}")

        else:
            logger.info(f"[DRY-RUN] Would execute STOP-LOSS for {ticker}")

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """
        모니터링 요약 통계

        Returns:
            모니터링 통계
        """
        return {
            "is_running": self.is_running,
            "check_count": self.check_count,
            "stop_loss_triggered_count": self.stop_loss_triggered_count,
            "current_positions": len(self.position_tracker.get_all_positions()),
            "stop_loss_threshold_pct": self.stop_loss_threshold_pct,
            "check_interval_seconds": self.check_interval_seconds,
            "recent_triggers": [
                {
                    "ticker": t.ticker,
                    "loss_pct": t.loss_pct,
                    "reason": t.reason
                }
                for t in self.trigger_history[-5:]  # 최근 5개
            ]
        }


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 80)
        print("Stop-Loss Monitor Test")
        print("=" * 80)

        # 초기화
        position_tracker = PositionTracker()

        # 테스트 포지션 생성
        position_tracker.create_position(
            ticker="NVDA",
            company_name="NVIDIA",
            initial_price=150.0,
            initial_amount=10000.0
        )

        monitor = StopLossMonitor(
            position_tracker=position_tracker,
            consensus_engine=None,
            auto_trader=None,
            stop_loss_threshold_pct=-10.0,
            check_interval_seconds=2,  # 2초 간격 (테스트용)
            enable_auto_execute=False
        )

        print("\n[Starting monitoring for 10 seconds...]")

        # 모니터링 시작 (background task)
        monitor_task = asyncio.create_task(monitor.start_monitoring())

        # 10초 후 중지
        await asyncio.sleep(10)
        monitor.stop_monitoring()

        # Task 종료 대기
        try:
            await asyncio.wait_for(monitor_task, timeout=2.0)
        except asyncio.TimeoutError:
            monitor_task.cancel()

        # 요약
        summary = monitor.get_monitoring_summary()
        print(f"\n[Monitoring Summary]")
        print(f"Check Count: {summary['check_count']}")
        print(f"Stop-Loss Triggered: {summary['stop_loss_triggered_count']}")
        print(f"Positions Monitored: {summary['current_positions']}")

    asyncio.run(test())
