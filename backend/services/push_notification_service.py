"""
Push Notification Service

Firebase Cloud Messaging (FCM)을 사용하여 모바일 푸시 알림을 전송하는 서비스

기능:
1. 충돌 알림 전송
2. 트레이딩 시그널 알림 전송
3. 일일 브리핑 알림 전송
4. 사용자 FCM 토큰 관리

참고: Phase 4 - Real-time Execution 완성
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Firebase Admin SDK (선택적 - 설치되지 않으면 비활성화)
try:
    from firebase_admin import messaging, credentials, initialize_app
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("firebase-admin not installed. Push notifications will be disabled.")


class PushNotificationService:
    """Firebase Cloud Messaging을 사용한 푸시 알림 서비스"""

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Push Notification Service 초기화

        Args:
            credentials_path: Firebase 서비스 계정 키 파일 경로
                           기본값: 환경변수 FIREBASE_CREDENTIALS_PATH
        """
        self.enabled = False
        self.app = None

        if not FIREBASE_AVAILABLE:
            logger.warning("PushNotificationService: Firebase Admin SDK not available")
            return

        try:
            # Firebase 자격 증명 파일 경로
            cred_path = credentials_path or os.getenv('FIREBASE_CREDENTIALS_PATH')

            if not cred_path:
                logger.warning("PushNotificationService: FIREBASE_CREDENTIALS_PATH not set")
                return

            if not os.path.exists(cred_path):
                logger.warning(f"PushNotificationService: Credentials file not found: {cred_path}")
                return

            # Firebase 초기화
            cred = credentials.Certificate(cred_path)
            self.app = initialize_app(cred)
            self.enabled = True

            logger.info("✅ PushNotificationService initialized successfully")

        except Exception as e:
            logger.error(f"❌ PushNotificationService initialization failed: {e}")

    async def send_conflict_alert(
        self,
        user_tokens: List[str],
        conflict: Dict
    ) -> Dict[str, int]:
        """
        충돌 알림 전송

        Args:
            user_tokens: 사용자 FCM 토큰 목록
            conflict: 충돌 정보
                {
                    'ticker': 'NVDA',
                    'conflicting_strategy': 'Momentum',
                    'owning_strategy': 'Value',
                    'message': '이미 보유 중인 종목입니다',
                    'resolution': '보유량 유지'
                }

        Returns:
            {
                'success_count': 성공한 알림 수,
                'failure_count': 실패한 알림 수
            }
        """
        if not self.enabled:
            logger.debug("Push notifications disabled")
            return {'success_count': 0, 'failure_count': len(user_tokens)}

        if not user_tokens:
            logger.warning("No user tokens provided")
            return {'success_count': 0, 'failure_count': 0}

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title='⚠️ 전략 충돌 감지',
                    body=f"{conflict['ticker']}: {conflict['message']}"
                ),
                data={
                    'type': 'conflict',
                    'ticker': conflict['ticker'],
                    'conflicting_strategy': conflict['conflicting_strategy'],
                    'owning_strategy': conflict['owning_strategy'],
                    'resolution': conflict['resolution'],
                    'timestamp': datetime.now().isoformat()
                },
                tokens=user_tokens
            )

            response = messaging.send_multicast(message)

            logger.info(
                f"Conflict alert sent: {response.success_count} success, "
                f"{response.failure_count} failure"
            )

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count
            }

        except Exception as e:
            logger.error(f"Failed to send conflict alert: {e}")
            return {'success_count': 0, 'failure_count': len(user_tokens)}

    async def send_signal_alert(
        self,
        user_tokens: List[str],
        signal: Dict
    ) -> Dict[str, int]:
        """
        트레이딩 시그널 알림 전송

        Args:
            user_tokens: 사용자 FCM 토큰 목록
            signal: 시그널 정보
                {
                    'ticker': 'NVDA',
                    'action': 'BUY',
                    'confidence': 0.85,
                    'reasoning': 'AI 칩 수요 증가',
                    'timestamp': '2026-01-25T06:00:00'
                }

        Returns:
            {
                'success_count': 성공한 알림 수,
                'failure_count': 실패한 알림 수
            }
        """
        if not self.enabled:
            logger.debug("Push notifications disabled")
            return {'success_count': 0, 'failure_count': len(user_tokens)}

        if not user_tokens:
            logger.warning("No user tokens provided")
            return {'success_count': 0, 'failure_count': 0}

        try:
            action_emoji = '🚀' if signal['action'] == 'BUY' else '📉'

            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=f"{action_emoji} {signal['action']} 시그널: {signal['ticker']}",
                    body=f"신뢰도: {signal['confidence']:.0%} | {signal['reasoning'][:50]}..."
                ),
                data={
                    'type': 'signal',
                    'ticker': signal['ticker'],
                    'action': signal['action'],
                    'confidence': str(signal['confidence']),
                    'reasoning': signal['reasoning'],
                    'timestamp': signal.get('timestamp', datetime.now().isoformat())
                },
                tokens=user_tokens
            )

            response = messaging.send_multicast(message)

            logger.info(
                f"Signal alert sent: {response.success_count} success, "
                f"{response.failure_count} failure"
            )

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count
            }

        except Exception as e:
            logger.error(f"Failed to send signal alert: {e}")
            return {'success_count': 0, 'failure_count': len(user_tokens)}

    async def send_daily_briefing(
        self,
        user_tokens: List[str],
        briefing_summary: str
    ) -> Dict[str, int]:
        """
        일일 브리핑 알림 전송

        Args:
            user_tokens: 사용자 FCM 토큰 목록
            briefing_summary: 브리핑 요약

        Returns:
            {
                'success_count': 성공한 알림 수,
                'failure_count': 실패한 알림 수
            }
        """
        if not self.enabled:
            logger.debug("Push notifications disabled")
            return {'success_count': 0, 'failure_count': len(user_tokens)}

        if not user_tokens:
            logger.warning("No user tokens provided")
            return {'success_count': 0, 'failure_count': 0}

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title='📊 일일 브리핑 도착',
                    body=briefing_summary
                ),
                data={
                    'type': 'briefing',
                    'summary': briefing_summary,
                    'timestamp': datetime.now().isoformat()
                },
                tokens=user_tokens
            )

            response = messaging.send_multicast(message)

            logger.info(
                f"Daily briefing sent: {response.success_count} success, "
                f"{response.failure_count} failure"
            )

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count
            }

        except Exception as e:
            logger.error(f"Failed to send daily briefing: {e}")
            return {'success_count': 0, 'failure_count': len(user_tokens)}

    async def send_order_alert(
        self,
        user_tokens: List[str],
        order: Dict
    ) -> Dict[str, int]:
        """
        주문 알림 전송

        Args:
            user_tokens: 사용자 FCM 토큰 목록
            order: 주문 정보
                {
                    'ticker': 'NVDA',
                    'action': 'BUY',
                    'quantity': 10,
                    'price': 500.0,
                    'status': 'FILLED'
                }

        Returns:
            {
                'success_count': 성공한 알림 수,
                'failure_count': 실패한 알림 수
            }
        """
        if not self.enabled:
            logger.debug("Push notifications disabled")
            return {'success_count': 0, 'failure_count': len(user_tokens)}

        if not user_tokens:
            logger.warning("No user tokens provided")
            return {'success_count': 0, 'failure_count': 0}

        try:
            status_emoji = '✅' if order['status'] == 'FILLED' else '⏳'

            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=f"{status_emoji} 주문 {order['status']}",
                    body=f"{order['action']} {order['quantity']} {order['ticker']} @ ${order['price']}"
                ),
                data={
                    'type': 'order',
                    'ticker': order['ticker'],
                    'action': order['action'],
                    'quantity': str(order['quantity']),
                    'price': str(order['price']),
                    'status': order['status'],
                    'timestamp': datetime.now().isoformat()
                },
                tokens=user_tokens
            )

            response = messaging.send_multicast(message)

            logger.info(
                f"Order alert sent: {response.success_count} success, "
                f"{response.failure_count} failure"
            )

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count
            }

        except Exception as e:
            logger.error(f"Failed to send order alert: {e}")
            return {'success_count': 0, 'failure_count': len(user_tokens)}

    def is_enabled(self) -> bool:
        """푸시 알림 활성화 여부 확인"""
        return self.enabled


# 전역 인스턴스
_push_notification_service: Optional[PushNotificationService] = None


def get_push_notification_service() -> PushNotificationService:
    """
    Push Notification Service 전역 인스턴스 반환

    Returns:
        PushNotificationService 인스턴스
    """
    global _push_notification_service

    if _push_notification_service is None:
        _push_notification_service = PushNotificationService()

    return _push_notification_service
