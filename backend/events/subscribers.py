"""
Event Subscribers - 시스템 이벤트 핸들러
Phase 4, T4.2

이벤트 기반 아키텍처(EDA)의 핵심 구독자들을 정의합니다.
각 핸들러는 특정 이벤트를 수신하여 비즈니스 로직(알림, 재계산 등)을 수행합니다.
"""

import logging
import asyncio
from typing import Dict, Any

from backend.events import event_bus, EventType
from backend.utils.retry import retry
# from backend.services.portfolio_optimizer import PortfolioOptimizer # Assuming usage

logger = logging.getLogger(__name__)

# Global reference to WebSocket manager (will be set during initialization)
_conflict_ws_manager = None

def set_conflict_ws_manager(manager):
    """Set the global WebSocket manager reference"""
    global _conflict_ws_manager
    _conflict_ws_manager = manager

class ConflictEventSubscriber:
    """충돌 관련 이벤트 구독자"""

    def __init__(self, db_session=None):
        self.db = db_session

    @retry(max_retries=3, delay=1)
    def handle_conflict_detected(self, data: Dict[str, Any]):
        """
        CONFLICT_DETECTED 처리
        - 목표: 로그 저장 및 중요 알림
        - WebSocket으로 실시간 브로드캐스트
        """
        ticker = data.get('ticker')
        strategy_id = data.get('strategy_id')
        detail = data.get('conflict_detail', {})

        logger.warning(f"⚠️ [CONFLICT_DETECTED] {ticker} by {strategy_id}. Detail: {detail}")

        # Broadcast to WebSocket clients
        if _conflict_ws_manager:
            message = {
                'type': 'CONFLICT_DETECTED',
                'data': data
            }
            try:
                # Run async broadcast in event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(_conflict_ws_manager.broadcast(message))
                else:
                    loop.run_until_complete(_conflict_ws_manager.broadcast(message))
            except Exception as e:
                logger.error(f"Failed to broadcast conflict: {e}")

        # Send push notification
        if _push_notification_service and _push_notification_service.is_enabled():
            try:
                # Get user tokens from database (placeholder - implement based on your DB schema)
                user_tokens = self._get_user_fcm_tokens()

                if user_tokens:
                    conflict_data = {
                        'ticker': ticker,
                        'conflicting_strategy': detail.get('conflicting_strategy', 'Unknown'),
                        'owning_strategy': detail.get('owning_strategy', 'Unknown'),
                        'message': detail.get('message', '전략 충돌 발생'),
                        'resolution': detail.get('resolution', '자동 해결')
                    }

                    # Run async push notification in event loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(
                            _push_notification_service.send_conflict_alert(user_tokens, conflict_data)
                        )
                    else:
                        loop.run_until_complete(
                            _push_notification_service.send_conflict_alert(user_tokens, conflict_data)
                        )
            except Exception as e:
                logger.error(f"Failed to send push notification for conflict: {e}")

    @retry(max_retries=3, delay=1)
    def handle_order_blocked(self, data: Dict[str, Any]):
        """
        ORDER_BLOCKED_BY_CONFLICT 처리
        - 목표: 사용자 대시보드 알림 (Pop-up)
        """
        ticker = data.get('ticker')
        reason = data.get('reason')

        logger.error(f"🚫 [ORDER_BLOCKED] {ticker}: {reason}")
        # TODO: Create UserFeedback entry or similar for UI display

        # Send push notification
        if _push_notification_service and _push_notification_service.is_enabled():
            try:
                user_tokens = self._get_user_fcm_tokens()

                if user_tokens:
                    # Send conflict alert for blocked order
                    conflict_data = {
                        'ticker': ticker,
                        'conflicting_strategy': 'Unknown',
                        'owning_strategy': 'Unknown',
                        'message': f"주문 차단됨: {reason}",
                        'resolution': '수동 확인 필요'
                    }

                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(
                            _push_notification_service.send_conflict_alert(user_tokens, conflict_data)
                        )
                    else:
                        loop.run_until_complete(
                            _push_notification_service.send_conflict_alert(user_tokens, conflict_data)
                        )
            except Exception as e:
                logger.error(f"Failed to send push notification for blocked order: {e}")

    @retry(max_retries=3, delay=1)
    def handle_priority_override(self, data: Dict[str, Any]):
        """
        PRIORITY_OVERRIDE 처리
        - 목표: 오버라이드 발생 사실 기록
        """
        ticker = data.get('ticker')
        strategy_id = data.get('strategy_id')
        
        logger.info(f"⚡ [PRIORITY_OVERRIDE] {ticker} taken by {strategy_id}")

    def _get_user_fcm_tokens(self) -> list:
        """
        사용자 FCM 토큰 목록 조회

        Returns:
            사용자 FCM 토큰 목록
        """
        try:
            if not self.db:
                from backend.database.repository import get_sync_session
                self.db = get_sync_session()
            
            from backend.database.models import UserFCMToken
            tokens = self.db.query(UserFCMToken).filter(
                UserFCMToken.is_active == True
            ).all()
            
            return [token.token for token in tokens]
        except Exception as e:
            logger.error(f"Failed to fetch FCM tokens: {e}")
            return []


class PortfolioEventSubscriber:
    """포트폴리오 관련 이벤트 구독자"""

    @retry(max_retries=3, delay=2)
    def handle_ownership_transferred(self, data: Dict[str, Any]):
        """
        OWNERSHIP_TRANSFERRED 처리
        - 목표: 포트폴리오 재계산
        """
        ticker = data.get('ticker')
        new_owner = data.get('to_strategy_name')
        
        logger.info(f"🔄 [PORTFOLIO_RECALC] Triggered by ownership transfer of {ticker} to {new_owner}")
        
        # 실제 재계산 로직 호출 (Phase 5+)
        # optimizer = PortfolioOptimizer(...)
        # optimizer.rebalance_strategy(new_owner)


class TradingSignalEventSubscriber:
    """트레이딩 시그널 관련 이벤트 구독자"""

    @retry(max_retries=3, delay=1)
    def handle_signal_generated(self, data: Dict[str, Any]):
        """
        TRADING_SIGNAL_GENERATED 처리
        - 목표: 푸시 알림 전송
        """
        ticker = data.get('ticker')
        action = data.get('action')
        confidence = data.get('confidence')
        reasoning = data.get('reasoning')

        logger.info(f"🚀 [SIGNAL_GENERATED] {action} {ticker} (confidence: {confidence:.2%})")

        # Send push notification
        if _push_notification_service and _push_notification_service.is_enabled():
            try:
                user_tokens = self._get_user_fcm_tokens()

                if user_tokens:
                    signal_data = {
                        'ticker': ticker,
                        'action': action,
                        'confidence': confidence,
                        'reasoning': reasoning,
                        'timestamp': data.get('timestamp')
                    }

                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(
                            _push_notification_service.send_signal_alert(user_tokens, signal_data)
                        )
                    else:
                        loop.run_until_complete(
                            _push_notification_service.send_signal_alert(user_tokens, signal_data)
                        )
            except Exception as e:
                logger.error(f"Failed to send push notification for signal: {e}")

    def _get_user_fcm_tokens(self) -> list:
        """
        사용자 FCM 토큰 목록 조회

        Returns:
            사용자 FCM 토큰 목록
        """
        try:
            from backend.database.repository import get_sync_session
            from backend.database.models import UserFCMToken
            
            db = get_sync_session()
            tokens = db.query(UserFCMToken).filter(
                UserFCMToken.is_active == True
            ).all()
            
            return [token.token for token in tokens]
        except Exception as e:
            logger.error(f"Failed to fetch FCM tokens: {e}")
            return []


def register_subscribers():
    """모든 구독자 등록 (App Startup 시 호출)"""
    conflict_sub = ConflictEventSubscriber()
    portfolio_sub = PortfolioEventSubscriber()
    signal_sub = TradingSignalEventSubscriber()

    event_bus.subscribe(EventType.CONFLICT_DETECTED, conflict_sub.handle_conflict_detected)
    event_bus.subscribe(EventType.ORDER_BLOCKED_BY_CONFLICT, conflict_sub.handle_order_blocked)
    event_bus.subscribe(EventType.PRIORITY_OVERRIDE, conflict_sub.handle_priority_override)
    event_bus.subscribe(EventType.OWNERSHIP_TRANSFERRED, portfolio_sub.handle_ownership_transferred)

    # 트레이딩 시그널 이벤트 등록 (이벤트 타입이 있는 경우)
    if hasattr(EventType, 'TRADING_SIGNAL_GENERATED'):
        event_bus.subscribe(EventType.TRADING_SIGNAL_GENERATED, signal_sub.handle_signal_generated)

    logger.info("✅ Event Subscribers Registered")
