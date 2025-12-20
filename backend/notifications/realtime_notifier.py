"""
Realtime Notifier - 실시간 알림 시스템

Phase E + Option 2 통합
WebSocket + Telegram/Slack 실시간 알림

핵심 기능:
1. WebSocket 브로드캐스트 (프론트엔드)
2. Telegram 알림
3. Slack 알림 (옵션)
4. 이벤트 타입별 템플릿

알림 이벤트:
- consensus_decision: Consensus 투표 결과
- order_filled: 주문 체결
- stop_loss_triggered: 손절 트리거
- dca_executed: DCA 실행
- position_update: 포지션 업데이트

작성일: 2025-12-06
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import json

logger = logging.getLogger(__name__)


class NotificationLevel(str, Enum):
    """알림 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """알림 채널"""
    WEBSOCKET = "websocket"
    TELEGRAM = "telegram"
    SLACK = "slack"
    EMAIL = "email"


class RealtimeNotifier:
    """
    실시간 알림 시스템

    Usage:
        notifier = RealtimeNotifier()
        await notifier.notify_consensus_decision(consensus_result)
        await notifier.notify_order_filled(order_info)
    """

    def __init__(
        self,
        enable_websocket: bool = True,
        enable_telegram: bool = False,
        enable_slack: bool = False,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        slack_webhook_url: Optional[str] = None
    ):
        """
        Initialize Realtime Notifier

        Args:
            enable_websocket: WebSocket 활성화
            enable_telegram: Telegram 활성화
            enable_slack: Slack 활성화
            telegram_bot_token: Telegram Bot Token
            telegram_chat_id: Telegram Chat ID
            slack_webhook_url: Slack Webhook URL
        """
        self.enable_websocket = enable_websocket
        self.enable_telegram = enable_telegram
        self.enable_slack = enable_slack

        # WebSocket connections (프론트엔드 클라이언트)
        self.websocket_connections: Set[Any] = set()

        # Telegram
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

        # Slack
        self.slack_webhook_url = slack_webhook_url

        # 알림 이력
        self.notification_history: List[Dict[str, Any]] = []

        logger.info(
            f"RealtimeNotifier initialized: "
            f"websocket={enable_websocket}, telegram={enable_telegram}, slack={enable_slack}"
        )

    # ========================================================================
    # WebSocket 관리
    # ========================================================================

    def add_websocket_connection(self, websocket):
        """
        WebSocket 연결 추가

        Args:
            websocket: WebSocket 객체
        """
        self.websocket_connections.add(websocket)
        logger.info(f"WebSocket client connected (total: {len(self.websocket_connections)})")

    def remove_websocket_connection(self, websocket):
        """
        WebSocket 연결 제거

        Args:
            websocket: WebSocket 객체
        """
        self.websocket_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected (total: {len(self.websocket_connections)})")

    async def broadcast_websocket(self, message: Dict[str, Any]):
        """
        모든 WebSocket 클라이언트에 브로드캐스트

        Args:
            message: 메시지 딕셔너리
        """
        if not self.enable_websocket:
            return

        if not self.websocket_connections:
            logger.debug("No WebSocket clients to broadcast")
            return

        message_json = json.dumps(message)
        disconnected = set()

        for ws in self.websocket_connections:
            try:
                await ws.send(message_json)
                logger.debug(f"Sent WebSocket message: {message['type']}")

            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                disconnected.add(ws)

        # 연결 끊긴 클라이언트 제거
        for ws in disconnected:
            self.remove_websocket_connection(ws)

    # ========================================================================
    # 이벤트별 알림
    # ========================================================================

    async def notify_consensus_decision(
        self,
        consensus_result,
        channels: Optional[List[NotificationChannel]] = None
    ):
        """
        Consensus 투표 결과 알림

        Args:
            consensus_result: ConsensusResult 객체
            channels: 알림 채널 리스트 (None이면 전체)
        """
        message = {
            "type": "consensus_decision",
            "action": consensus_result.action,
            "ticker": consensus_result.ticker,
            "approved": consensus_result.approved,
            "votes": f"{consensus_result.approve_count}/{consensus_result.total_votes}",
            "consensus_strength": consensus_result.consensus_strength.value,
            "timestamp": datetime.now().isoformat()
        }

        # 레벨 결정
        if consensus_result.action == "STOP_LOSS":
            level = NotificationLevel.CRITICAL
        elif consensus_result.approved:
            level = NotificationLevel.WARNING
        else:
            level = NotificationLevel.INFO

        # 텍스트 메시지 생성
        status_emoji = "✅" if consensus_result.approved else "❌"
        text = (
            f"{status_emoji} *Consensus Decision*\n"
            f"Action: {consensus_result.action} {consensus_result.ticker}\n"
            f"Approved: {consensus_result.approved}\n"
            f"Votes: {consensus_result.approve_count}/{consensus_result.total_votes}\n"
            f"Strength: {consensus_result.consensus_strength.value}"
        )

        await self._send_notification(message, text, level, channels)

    async def notify_order_filled(
        self,
        order_info: Dict[str, Any],
        channels: Optional[List[NotificationChannel]] = None
    ):
        """
        주문 체결 알림

        Args:
            order_info: 주문 정보
            channels: 알림 채널
        """
        message = {
            "type": "order_filled",
            "ticker": order_info.get("ticker"),
            "side": order_info.get("side"),
            "quantity": order_info.get("quantity"),
            "avg_price": order_info.get("avg_price"),
            "order_id": order_info.get("order_id"),
            "timestamp": datetime.now().isoformat()
        }

        side = order_info.get("side", "")
        ticker = order_info.get("ticker", "")
        quantity = order_info.get("quantity", 0)
        avg_price = order_info.get("avg_price", 0)

        text = (
            f"📊 *Order Filled*\n"
            f"{side} {quantity} {ticker} @ ${avg_price:.2f}\n"
            f"Order ID: {order_info.get('order_id')}"
        )

        await self._send_notification(message, text, NotificationLevel.WARNING, channels)

    async def notify_stop_loss_triggered(
        self,
        ticker: str,
        loss_pct: float,
        current_price: float,
        avg_entry_price: float,
        channels: Optional[List[NotificationChannel]] = None
    ):
        """
        Stop-loss 트리거 알림

        Args:
            ticker: 종목 티커
            loss_pct: 손실률
            current_price: 현재 가격
            avg_entry_price: 평균 진입가
            channels: 알림 채널
        """
        message = {
            "type": "stop_loss_triggered",
            "ticker": ticker,
            "loss_pct": loss_pct,
            "current_price": current_price,
            "avg_entry_price": avg_entry_price,
            "timestamp": datetime.now().isoformat()
        }

        text = (
            f"🚨 *STOP-LOSS TRIGGERED*\n"
            f"Ticker: {ticker}\n"
            f"Loss: {loss_pct:.2f}%\n"
            f"Current: ${current_price:.2f}\n"
            f"Entry: ${avg_entry_price:.2f}"
        )

        await self._send_notification(message, text, NotificationLevel.CRITICAL, channels)

    async def notify_dca_executed(
        self,
        ticker: str,
        dca_number: int,
        price: float,
        amount: float,
        channels: Optional[List[NotificationChannel]] = None
    ):
        """
        DCA 실행 알림

        Args:
            ticker: 종목 티커
            dca_number: DCA 횟수
            price: 매수 가격
            amount: 매수 금액
            channels: 알림 채널
        """
        message = {
            "type": "dca_executed",
            "ticker": ticker,
            "dca_number": dca_number,
            "price": price,
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        }

        text = (
            f"🔄 *DCA Executed*\n"
            f"Ticker: {ticker}\n"
            f"DCA #{dca_number}\n"
            f"Price: ${price:.2f}\n"
            f"Amount: ${amount:.2f}"
        )

        await self._send_notification(message, text, NotificationLevel.INFO, channels)

    async def notify_position_update(
        self,
        ticker: str,
        total_shares: float,
        avg_entry_price: float,
        unrealized_pnl: float,
        unrealized_pnl_pct: float,
        channels: Optional[List[NotificationChannel]] = None
    ):
        """
        포지션 업데이트 알림

        Args:
            ticker: 종목 티커
            total_shares: 총 보유 주식
            avg_entry_price: 평균 진입가
            unrealized_pnl: 미실현 손익
            unrealized_pnl_pct: 미실현 손익률
            channels: 알림 채널
        """
        message = {
            "type": "position_update",
            "ticker": ticker,
            "total_shares": total_shares,
            "avg_entry_price": avg_entry_price,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "timestamp": datetime.now().isoformat()
        }

        pnl_emoji = "📈" if unrealized_pnl >= 0 else "📉"
        text = (
            f"{pnl_emoji} *Position Update*\n"
            f"Ticker: {ticker}\n"
            f"Shares: {total_shares:.2f}\n"
            f"Avg Entry: ${avg_entry_price:.2f}\n"
            f"P&L: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.2f}%)"
        )

        await self._send_notification(message, text, NotificationLevel.INFO, channels)

    # ========================================================================
    # 내부 전송 로직
    # ========================================================================

    async def _send_notification(
        self,
        message: Dict[str, Any],
        text: str,
        level: NotificationLevel,
        channels: Optional[List[NotificationChannel]] = None
    ):
        """
        모든 채널로 알림 전송

        Args:
            message: WebSocket 메시지 (JSON)
            text: 텍스트 메시지 (Telegram/Slack)
            level: 알림 레벨
            channels: 알림 채널 (None이면 전체)
        """
        message["level"] = level.value

        # 이력 저장
        self.notification_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": message.get("type"),
            "level": level.value,
            "message": message
        })

        # 채널별 전송
        if channels is None:
            channels = [
                NotificationChannel.WEBSOCKET,
                NotificationChannel.TELEGRAM,
                NotificationChannel.SLACK
            ]

        tasks = []

        if NotificationChannel.WEBSOCKET in channels and self.enable_websocket:
            tasks.append(self.broadcast_websocket(message))

        if NotificationChannel.TELEGRAM in channels and self.enable_telegram:
            tasks.append(self._send_telegram(text))

        if NotificationChannel.SLACK in channels and self.enable_slack:
            tasks.append(self._send_slack(text))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_telegram(self, text: str):
        """
        Telegram 메시지 전송

        Args:
            text: 메시지 텍스트
        """
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("Telegram credentials missing, skipping")
            return

        try:
            import aiohttp

            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Telegram notification sent")
                    else:
                        logger.error(f"Telegram send failed: {response.status}")

        except Exception as e:
            logger.error(f"Telegram send error: {e}")

    async def _send_slack(self, text: str):
        """
        Slack 메시지 전송

        Args:
            text: 메시지 텍스트
        """
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL missing, skipping")
            return

        try:
            import aiohttp

            payload = {"text": text}

            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Slack notification sent")
                    else:
                        logger.error(f"Slack send failed: {response.status}")

        except Exception as e:
            logger.error(f"Slack send error: {e}")

    def get_notification_summary(self) -> Dict[str, Any]:
        """
        알림 통계

        Returns:
            알림 통계
        """
        total = len(self.notification_history)
        by_type = {}
        by_level = {}

        for entry in self.notification_history:
            ntype = entry.get("type", "unknown")
            level = entry.get("level", "unknown")

            by_type[ntype] = by_type.get(ntype, 0) + 1
            by_level[level] = by_level.get(level, 0) + 1

        return {
            "total_notifications": total,
            "websocket_clients": len(self.websocket_connections),
            "by_type": by_type,
            "by_level": by_level,
            "recent_notifications": self.notification_history[-5:]  # 최근 5개
        }


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 80)
        print("Realtime Notifier Test")
        print("=" * 80)

        # 초기화 (WebSocket만)
        notifier = RealtimeNotifier(
            enable_websocket=True,
            enable_telegram=False,
            enable_slack=False
        )

        # Mock Consensus 결과
        from backend.ai.consensus.consensus_models import ConsensusResult, ConsensusStrength, AIVote, VoteDecision

        mock_consensus = ConsensusResult(
            approved=True,
            action="BUY",
            votes={
                "claude": AIVote(
                    ai_model="claude",
                    decision=VoteDecision.APPROVE,
                    confidence=0.85,
                    reasoning="Test"
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

        # 알림 전송
        print("\n[Test 1] Consensus Decision")
        await notifier.notify_consensus_decision(mock_consensus)

        print("\n[Test 2] Order Filled")
        await notifier.notify_order_filled({
            "ticker": "AAPL",
            "side": "BUY",
            "quantity": 10,
            "avg_price": 150.0,
            "order_id": "TEST001"
        })

        print("\n[Test 3] Stop-loss Triggered")
        await notifier.notify_stop_loss_triggered(
            ticker="NVDA",
            loss_pct=-12.5,
            current_price=130.0,
            avg_entry_price=148.57
        )

        # 통계
        summary = notifier.get_notification_summary()
        print(f"\n[Notification Summary]")
        print(f"Total: {summary['total_notifications']}")
        print(f"By Type: {summary['by_type']}")
        print(f"By Level: {summary['by_level']}")

    asyncio.run(test())
