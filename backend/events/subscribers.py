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

    @retry(max_retries=3, delay=1)
    def handle_priority_override(self, data: Dict[str, Any]):
        """
        PRIORITY_OVERRIDE 처리
        - 목표: 오버라이드 발생 사실 기록
        """
        ticker = data.get('ticker')
        strategy_id = data.get('strategy_id')
        
        logger.info(f"⚡ [PRIORITY_OVERRIDE] {ticker} taken by {strategy_id}")


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


def register_subscribers():
    """모든 구독자 등록 (App Startup 시 호출)"""
    conflict_sub = ConflictEventSubscriber()
    portfolio_sub = PortfolioEventSubscriber()

    event_bus.subscribe(EventType.CONFLICT_DETECTED, conflict_sub.handle_conflict_detected)
    event_bus.subscribe(EventType.ORDER_BLOCKED_BY_CONFLICT, conflict_sub.handle_order_blocked)
    event_bus.subscribe(EventType.PRIORITY_OVERRIDE, conflict_sub.handle_priority_override)
    event_bus.subscribe(EventType.OWNERSHIP_TRANSFERRED, portfolio_sub.handle_ownership_transferred)

    logger.info("✅ Event Subscribers Registered")
