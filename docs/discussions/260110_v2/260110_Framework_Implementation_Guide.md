# AI Trading System - 프레임워크 구현 가이드

**문서 버전**: 1.0  
**작성일**: 2026-01-10  
**목적**: State Machine + Event Bus + Recovery 로직 구현  
**대상**: Claude Code Agent  

---

## 📋 Executive Summary

### 배경
3개 AI (Gemini, Claude, ChatGPT)가 동일한 시스템을 분석한 결과, **공통된 핵심 문제점**과 **해결책**에 합의했습니다.

### 핵심 진단 (3-AI 합의)

| AI | 핵심 메시지 |
|----|-----------|
| **Gemini** | "분석 능력은 중상급, 실행 안정성(State)이 비어있다" |
| **Claude** | "구조는 있으나 강제성이 부족하다" |
| **ChatGPT** | "강제되지 않으면 **없다와 같다**. 안전벨트가 필요하다" |

### 한 문장 결론
> **"두뇌(AI 분석)는 상위 10% 수준이다. 이제 필요한 건 척수(State Machine)와 신경계(Event Bus)다."**

---

## 🎯 현재 시스템 진단

### ✅ 강점 (유지해야 할 것)

| 영역 | 상태 | 설명 |
|------|------|------|
| AI 앙상블 분석 | ✅ 우수 | LLM + RAG 기반, 상위 10% 설계 |
| 데이터 레이어 | ✅ 우수 | TimescaleDB / Redis / Vector Store 분리 |
| Hard Rules / Guardrail | ✅ 구현됨 | PM Agent + Constitution Validator (11개 규칙) |
| 중복 주문 방지 | ✅ 기본 구현 | 5분 윈도우 체크 (OrderValidator) |
| PIT Backtest | ✅ 구현됨 | Point-in-Time 개념 도입 |
| Shadow Trading | ✅ 진행중 | 90일 검증 (Day 4/90) |

### ❌ 치명적 약점 (반드시 수정)

| 영역 | 현재 상태 | 문제점 |
|------|----------|--------|
| **State Machine** | 문자열 필드만 존재 | 전이 규칙 강제 안됨, 직접 변경 가능 |
| **Recovery 로직** | 미구현 | 재시작 시 미완료 주문 복구 불가 |
| **Event-Driven** | 미구현 | 모듈 간 직접 호출, 결합도 높음 |
| **Single Writer** | 미적용 | 어디서든 order.status 변경 가능 |

### ⚠️ ChatGPT 핵심 경고

> **"`status = 'pending'` 같은 문자열 필드는 State Machine이 아니다."**
> 
> 상태 전이 규칙이 **강제되지 않으면** 그건 "로그"이지 "상태 관리"가 아니다.
> 
> 지금 구조에서 가능한 상황 (위험!):
> - `filled` → `pending` 되돌리기 가능
> - `cancelled` → `partial_filled` 전이 가능
> - 아무 모듈에서나 status 변경 가능
> 
> **이건 실전 자동매매에서 "언젠가 반드시 계좌를 터뜨린다"**

---

## 🔴 구현 우선순위 (3-AI 합의)

### Phase 1: State Machine (3-5일) - **최우선**

**목표**: Order 상태 전이를 코드로 강제

**구현 항목**:
1. `OrderState` Enum 정의
2. `OrderStateMachine` 클래스 (전이 규칙 강제)
3. `OrderManager` 클래스 (Single Writer)
4. 기존 직접 변경 코드 제거

### Phase 2: Recovery 로직 (2-3일)

**목표**: 프로그램 재시작 시 미완료 주문 복구

**구현 항목**:
1. `recover_on_startup()` 메서드
2. 브로커 상태 동기화
3. `needs_manual_review` 플래그

### Phase 3: Event Bus (1-2주)

**목표**: 모듈 간 결합도 제거, 추적성 확보

**구현 항목**:
1. `EventType` Enum 정의
2. `EventBus` 클래스 (In-process)
3. 핵심 모듈 이벤트 구독/발행 전환

---

## 📁 파일 구조

### 신규 생성 파일

```
backend/
├── execution/
│   ├── state_machine.py      # [NEW] OrderState, OrderStateMachine
│   ├── order_manager.py      # [NEW] OrderManager (Single Writer)
│   ├── recovery.py           # [NEW] Recovery 로직
│   └── order_validator.py    # [EXISTING] 수정 필요
│
├── events/
│   ├── __init__.py           # [NEW]
│   ├── event_types.py        # [NEW] EventType Enum
│   └── event_bus.py          # [NEW] EventBus 클래스
│
└── database/
    └── models.py             # [MODIFY] Order 모델 수정
```

---

## 🔩 Phase 1: State Machine 상세 설계

### 1.1 OrderState Enum

**파일**: `backend/execution/state_machine.py`

```python
"""
Order State Machine - 상태 전이 강제

3-AI 합의 사항:
- 상태 전이는 코드로 강제되어야 함
- 종료 상태는 전이 불가
- Single Writer 원칙 적용

작성일: 2026-01-10
"""

from enum import Enum
from typing import Dict, Set, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OrderState(Enum):
    """주문 상태 정의 (10개 상태)"""
    
    # 초기 상태
    IDLE = "idle"                        # 대기
    SIGNAL_RECEIVED = "signal_received"  # 시그널 수신
    
    # 검증 단계
    VALIDATING = "validating"            # 검증 중
    
    # 주문 단계
    ORDER_PENDING = "order_pending"      # 주문 전송 대기
    ORDER_SENT = "order_sent"            # 주문 전송 완료
    
    # 체결 단계
    PARTIAL_FILLED = "partial_filled"    # 부분 체결
    FULLY_FILLED = "fully_filled"        # 전체 체결 (종료)
    
    # 종료 상태
    CANCELLED = "cancelled"              # 취소 (종료)
    REJECTED = "rejected"                # 거부 (종료)
    FAILED = "failed"                    # 실패 (종료)


class InvalidStateTransitionError(Exception):
    """유효하지 않은 상태 전이 예외"""
    pass


class OrderStateMachine:
    """
    주문 상태 머신 - 전이 규칙 강제
    
    핵심 원칙:
    1. 유효한 전이만 허용 (나머지는 예외)
    2. 종료 상태는 전이 불가
    3. 모든 전이는 로깅됨
    """
    
    # ================================================================
    # 상태 전이 규칙 (이것만 허용, 나머지는 모두 거부)
    # ================================================================
    VALID_TRANSITIONS: Dict[OrderState, Set[OrderState]] = {
        OrderState.IDLE: {
            OrderState.SIGNAL_RECEIVED
        },
        OrderState.SIGNAL_RECEIVED: {
            OrderState.VALIDATING,
            OrderState.REJECTED      # 즉시 거부 가능
        },
        OrderState.VALIDATING: {
            OrderState.ORDER_PENDING,
            OrderState.REJECTED      # 검증 실패
        },
        OrderState.ORDER_PENDING: {
            OrderState.ORDER_SENT,
            OrderState.FAILED        # 전송 실패
        },
        OrderState.ORDER_SENT: {
            OrderState.PARTIAL_FILLED,
            OrderState.FULLY_FILLED,
            OrderState.CANCELLED     # 사용자/시스템 취소
        },
        OrderState.PARTIAL_FILLED: {
            OrderState.FULLY_FILLED,
            OrderState.CANCELLED     # 잔량 취소
        },
        # 종료 상태 - 전이 불가
        OrderState.FULLY_FILLED: set(),
        OrderState.CANCELLED: set(),
        OrderState.REJECTED: set(),
        OrderState.FAILED: set(),
    }
    
    # 종료 상태 목록
    TERMINAL_STATES: Set[OrderState] = {
        OrderState.FULLY_FILLED,
        OrderState.CANCELLED,
        OrderState.REJECTED,
        OrderState.FAILED,
    }
    
    # 미완료 상태 목록 (Recovery 대상)
    PENDING_STATES: Set[OrderState] = {
        OrderState.ORDER_SENT,
        OrderState.PARTIAL_FILLED,
        OrderState.ORDER_PENDING,
    }
    
    def can_transition(self, current: OrderState, target: OrderState) -> bool:
        """
        전이 가능 여부 확인
        
        Args:
            current: 현재 상태
            target: 목표 상태
            
        Returns:
            bool: 전이 가능 여부
        """
        valid_targets = self.VALID_TRANSITIONS.get(current, set())
        return target in valid_targets
    
    def get_valid_transitions(self, current: OrderState) -> Set[OrderState]:
        """현재 상태에서 가능한 전이 목록"""
        return self.VALID_TRANSITIONS.get(current, set())
    
    def is_terminal(self, state: OrderState) -> bool:
        """종료 상태인지 확인"""
        return state in self.TERMINAL_STATES
    
    def is_pending(self, state: OrderState) -> bool:
        """미완료 상태인지 확인 (Recovery 대상)"""
        return state in self.PENDING_STATES


# 싱글톤 인스턴스
state_machine = OrderStateMachine()
```

### 1.2 OrderManager (Single Writer)

**파일**: `backend/execution/order_manager.py`

```python
"""
Order Manager - Single Writer 원칙

핵심 규칙:
- 상태 변경은 오직 이 클래스를 통해서만 가능
- order.status = "xxx" 직접 변경 절대 금지
- 모든 전이는 DB 영속화 + 로깅 포함

작성일: 2026-01-10
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from .state_machine import (
    OrderState, 
    OrderStateMachine, 
    InvalidStateTransitionError,
    state_machine
)

logger = logging.getLogger(__name__)


class OrderManager:
    """
    주문 관리자 - Single Writer
    
    모든 주문 상태 변경은 이 클래스를 통해서만 수행
    """
    
    def __init__(self, db_session, broker_client=None):
        """
        Args:
            db_session: SQLAlchemy 세션
            broker_client: 브로커 API 클라이언트 (Optional)
        """
        self.db = db_session
        self.broker = broker_client
        self.sm = state_machine
        
        # 상태 전이 이력 (메모리 캐시)
        self._transition_history: List[Dict] = []
    
    # ================================================================
    # 핵심 메서드: 상태 전이 (Single Writer)
    # ================================================================
    
    def transition(
        self, 
        order, 
        target: OrderState,
        reason: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        상태 전이 실행 (Single Writer)
        
        Args:
            order: Order 모델 인스턴스
            target: 목표 상태
            reason: 전이 사유
            metadata: 추가 메타데이터
            
        Returns:
            bool: 성공 여부
            
        Raises:
            InvalidStateTransitionError: 유효하지 않은 전이
        """
        current = OrderState(order.status)
        
        # 1. 전이 가능 여부 검증
        if not self.sm.can_transition(current, target):
            error_msg = f"Invalid transition: {current.value} → {target.value}"
            logger.error(f"[ORDER:{order.id}] {error_msg}")
            raise InvalidStateTransitionError(error_msg)
        
        # 2. 상태 변경 (원자적)
        old_status = order.status
        order.status = target.value
        order.updated_at = datetime.utcnow()
        
        # 3. 메타데이터 업데이트
        if metadata:
            if not order.metadata:
                order.metadata = {}
            order.metadata.update(metadata)
        
        # 4. DB 영속화
        try:
            self.db.add(order)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            order.status = old_status  # 롤백
            logger.error(f"[ORDER:{order.id}] DB commit failed: {e}")
            raise
        
        # 5. 로깅
        self._log_transition(order, current, target, reason)
        
        # 6. 이력 저장
        self._transition_history.append({
            'order_id': order.id,
            'symbol': order.ticker,
            'from': current.value,
            'to': target.value,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return True
    
    # ================================================================
    # 편의 메서드: 상태별 전이
    # ================================================================
    
    def receive_signal(self, order, signal_data: Dict) -> bool:
        """시그널 수신 → SIGNAL_RECEIVED"""
        return self.transition(
            order, 
            OrderState.SIGNAL_RECEIVED,
            reason="Signal received from AI ensemble",
            metadata={'signal': signal_data}
        )
    
    def start_validation(self, order) -> bool:
        """검증 시작 → VALIDATING"""
        return self.transition(
            order,
            OrderState.VALIDATING,
            reason="Starting order validation"
        )
    
    def validation_passed(self, order, validation_result: Dict) -> bool:
        """검증 통과 → ORDER_PENDING"""
        return self.transition(
            order,
            OrderState.ORDER_PENDING,
            reason="Validation passed",
            metadata={'validation': validation_result}
        )
    
    def validation_failed(self, order, violations: List[str]) -> bool:
        """검증 실패 → REJECTED"""
        return self.transition(
            order,
            OrderState.REJECTED,
            reason=f"Validation failed: {', '.join(violations)}",
            metadata={'violations': violations}
        )
    
    def order_sent(self, order, broker_order_id: str) -> bool:
        """주문 전송 완료 → ORDER_SENT"""
        order.order_id = broker_order_id
        return self.transition(
            order,
            OrderState.ORDER_SENT,
            reason=f"Order sent to broker: {broker_order_id}",
            metadata={'broker_order_id': broker_order_id}
        )
    
    def order_failed(self, order, error: str) -> bool:
        """주문 전송 실패 → FAILED"""
        order.error_message = error
        return self.transition(
            order,
            OrderState.FAILED,
            reason=f"Order failed: {error}"
        )
    
    def partial_fill(self, order, filled_qty: int, filled_price: float) -> bool:
        """부분 체결 → PARTIAL_FILLED"""
        order.filled_quantity = filled_qty
        order.filled_price = filled_price
        return self.transition(
            order,
            OrderState.PARTIAL_FILLED,
            reason=f"Partial fill: {filled_qty} @ ${filled_price}",
            metadata={'filled_qty': filled_qty, 'filled_price': filled_price}
        )
    
    def fully_filled(self, order, filled_price: float) -> bool:
        """전체 체결 → FULLY_FILLED"""
        order.filled_price = filled_price
        order.filled_at = datetime.utcnow()
        return self.transition(
            order,
            OrderState.FULLY_FILLED,
            reason=f"Fully filled @ ${filled_price}"
        )
    
    def cancel(self, order, reason: str = "User requested") -> bool:
        """취소 → CANCELLED"""
        return self.transition(
            order,
            OrderState.CANCELLED,
            reason=reason
        )
    
    # ================================================================
    # 조회 메서드
    # ================================================================
    
    def get_pending_orders(self) -> List:
        """미완료 주문 조회 (Recovery 대상)"""
        from backend.database.models import Order
        
        pending_values = [s.value for s in self.sm.PENDING_STATES]
        return self.db.query(Order).filter(
            Order.status.in_(pending_values)
        ).all()
    
    def get_transition_history(self, order_id: Optional[int] = None) -> List[Dict]:
        """전이 이력 조회"""
        if order_id:
            return [h for h in self._transition_history if h['order_id'] == order_id]
        return self._transition_history
    
    # ================================================================
    # Private 메서드
    # ================================================================
    
    def _log_transition(
        self, 
        order, 
        from_state: OrderState, 
        to_state: OrderState,
        reason: Optional[str]
    ):
        """상태 전이 로깅"""
        log_msg = (
            f"[ORDER:{order.id}] "
            f"{order.ticker} "
            f"{from_state.value} → {to_state.value}"
        )
        if reason:
            log_msg += f" | {reason}"
        
        # 종료 상태는 INFO, 나머지는 DEBUG
        if self.sm.is_terminal(to_state):
            logger.info(log_msg)
        else:
            logger.debug(log_msg)
```

### 1.3 기존 코드 수정 사항

**금지 패턴 (반드시 제거)**:

```python
# ❌ 절대 금지 - 직접 상태 변경
order.status = "filled"
order.status = OrderState.FULLY_FILLED.value

# ❌ 절대 금지 - 문자열로 상태 비교
if order.status == "pending":
    ...

# ❌ 절대 금지 - 상태 롤백
order.status = "idle"  # 되돌리기
```

**허용 패턴 (반드시 사용)**:

```python
# ✅ 올바른 방법 - OrderManager를 통한 전이
order_manager.fully_filled(order, filled_price=150.0)
order_manager.cancel(order, reason="Stop loss hit")

# ✅ 올바른 방법 - Enum으로 상태 비교
if OrderState(order.status) == OrderState.ORDER_PENDING:
    ...

# ✅ 올바른 방법 - 상태 머신으로 전이 가능 여부 확인
if state_machine.can_transition(current_state, target_state):
    order_manager.transition(order, target_state)
```

---

## 🔄 Phase 2: Recovery 로직 상세 설계

**파일**: `backend/execution/recovery.py`

```python
"""
Order Recovery - 재시작 시 미완료 주문 복구

핵심 원칙:
- 브로커 상태가 진실(Source of Truth)
- 실패한 주문은 수동 검토 플래그
- 자동화의 한계를 시스템이 인지

작성일: 2026-01-10
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging

from .state_machine import OrderState, state_machine
from .order_manager import OrderManager

logger = logging.getLogger(__name__)


class OrderRecovery:
    """주문 복구 시스템"""
    
    def __init__(self, order_manager: OrderManager):
        self.om = order_manager
        self.recovery_results: List[Dict] = []
    
    async def recover_on_startup(self) -> Dict:
        """
        프로그램 시작 시 미완료 주문 복구
        
        Returns:
            Dict: 복구 결과 요약
        """
        logger.info("=" * 50)
        logger.info("🔄 Starting Order Recovery...")
        logger.info("=" * 50)
        
        # 1. 미완료 주문 조회
        pending_orders = self.om.get_pending_orders()
        
        if not pending_orders:
            logger.info("✅ No pending orders to recover")
            return {'recovered': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"Found {len(pending_orders)} pending orders")
        
        recovered = 0
        failed = 0
        
        # 2. 각 주문 복구 시도
        for order in pending_orders:
            try:
                result = await self._recover_order(order)
                if result['success']:
                    recovered += 1
                else:
                    failed += 1
                self.recovery_results.append(result)
                
            except Exception as e:
                logger.error(f"[ORDER:{order.id}] Recovery exception: {e}")
                await self._mark_for_review(order, str(e))
                failed += 1
        
        # 3. 결과 요약
        summary = {
            'recovered': recovered,
            'failed': failed,
            'total': len(pending_orders),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("=" * 50)
        logger.info(f"✅ Recovery Complete: {recovered}/{len(pending_orders)} recovered")
        if failed > 0:
            logger.warning(f"⚠️ {failed} orders need manual review")
        logger.info("=" * 50)
        
        return summary
    
    async def _recover_order(self, order) -> Dict:
        """
        개별 주문 복구
        
        Args:
            order: Order 모델 인스턴스
            
        Returns:
            Dict: 복구 결과
        """
        current_state = OrderState(order.status)
        logger.info(f"[ORDER:{order.id}] {order.ticker} - Recovering from {current_state.value}")
        
        # 브로커에서 실제 상태 확인
        if not self.om.broker:
            logger.warning(f"[ORDER:{order.id}] No broker client - marking for review")
            await self._mark_for_review(order, "No broker client available")
            return {'success': False, 'order_id': order.id, 'reason': 'No broker'}
        
        try:
            broker_status = await self.om.broker.get_order_status(order.order_id)
        except Exception as e:
            logger.error(f"[ORDER:{order.id}] Broker API error: {e}")
            await self._mark_for_review(order, f"Broker API error: {e}")
            return {'success': False, 'order_id': order.id, 'reason': str(e)}
        
        # 브로커 상태에 따라 동기화
        broker_state = broker_status.get('status', '').lower()
        
        if broker_state == 'filled':
            # 전체 체결
            self.om.fully_filled(order, broker_status.get('filled_price', 0))
            logger.info(f"  ✅ {order.ticker}: Recovered as FULLY_FILLED")
            return {'success': True, 'order_id': order.id, 'new_state': 'fully_filled'}
        
        elif broker_state == 'cancelled':
            # 취소됨
            self.om.cancel(order, reason="Recovered as cancelled from broker")
            logger.info(f"  ⚠️ {order.ticker}: Recovered as CANCELLED")
            return {'success': True, 'order_id': order.id, 'new_state': 'cancelled'}
        
        elif broker_state == 'partial':
            # 부분 체결 → 모니터링 재개
            filled_qty = broker_status.get('filled_quantity', 0)
            filled_price = broker_status.get('filled_price', 0)
            
            if current_state != OrderState.PARTIAL_FILLED:
                self.om.partial_fill(order, filled_qty, filled_price)
            
            logger.info(f"  🔶 {order.ticker}: Partial filled ({filled_qty}), resuming monitor")
            return {'success': True, 'order_id': order.id, 'new_state': 'partial_filled', 'monitor': True}
        
        elif broker_state in ['pending', 'open', 'new']:
            # 여전히 진행 중 → 모니터링 재개
            logger.info(f"  🔵 {order.ticker}: Still pending, resuming monitor")
            return {'success': True, 'order_id': order.id, 'new_state': order.status, 'monitor': True}
        
        else:
            # 알 수 없는 상태
            logger.warning(f"  ❓ {order.ticker}: Unknown broker state '{broker_state}'")
            await self._mark_for_review(order, f"Unknown broker state: {broker_state}")
            return {'success': False, 'order_id': order.id, 'reason': f'Unknown state: {broker_state}'}
    
    async def _mark_for_review(self, order, error_message: str):
        """수동 검토 필요 플래그 설정"""
        order.needs_manual_review = True
        order.error_message = error_message
        order.updated_at = datetime.utcnow()
        
        self.om.db.add(order)
        self.om.db.commit()
        
        logger.warning(f"[ORDER:{order.id}] Marked for manual review: {error_message}")
    
    def get_recovery_results(self) -> List[Dict]:
        """복구 결과 조회"""
        return self.recovery_results
```

---

## 📡 Phase 3: Event Bus 상세 설계

**파일**: `backend/events/event_types.py`

```python
"""
Event Types - 이벤트 타입 정의

작성일: 2026-01-10
"""

from enum import Enum


class EventType(Enum):
    """시스템 이벤트 타입"""
    
    # ================================================================
    # 데이터 이벤트
    # ================================================================
    MARKET_DATA_RECEIVED = "market_data_received"    # 시장 데이터 수신
    NEWS_RECEIVED = "news_received"                  # 뉴스 수신
    
    # ================================================================
    # AI 분석 이벤트
    # ================================================================
    AI_ANALYSIS_STARTED = "ai_analysis_started"      # AI 분석 시작
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"    # AI 분석 완료
    SIGNAL_GENERATED = "signal_generated"            # 시그널 생성
    
    # ================================================================
    # 주문 이벤트
    # ================================================================
    ORDER_REQUESTED = "order_requested"              # 주문 요청
    ORDER_VALIDATED = "order_validated"              # 주문 검증 완료
    ORDER_REJECTED = "order_rejected"                # 주문 거부
    ORDER_SENT = "order_sent"                        # 주문 전송
    ORDER_FILLED = "order_filled"                    # 주문 체결
    ORDER_CANCELLED = "order_cancelled"              # 주문 취소
    ORDER_FAILED = "order_failed"                    # 주문 실패
    
    # ================================================================
    # 포지션 이벤트
    # ================================================================
    POSITION_OPENED = "position_opened"              # 포지션 오픈
    POSITION_UPDATED = "position_updated"            # 포지션 업데이트
    POSITION_CLOSED = "position_closed"              # 포지션 종료
    
    # ================================================================
    # 리스크 이벤트
    # ================================================================
    RISK_ALERT = "risk_alert"                        # 리스크 경고
    STOP_LOSS_HIT = "stop_loss_hit"                  # 스탑로스 도달
    CIRCUIT_BREAKER = "circuit_breaker"              # 서킷브레이커 발동
    
    # ================================================================
    # 시스템 이벤트
    # ================================================================
    SYSTEM_STARTED = "system_started"                # 시스템 시작
    SYSTEM_SHUTDOWN = "system_shutdown"              # 시스템 종료
    RECOVERY_COMPLETE = "recovery_complete"          # 복구 완료
```

**파일**: `backend/events/event_bus.py`

```python
"""
Event Bus - In-process 이벤트 버스

핵심 원칙:
- 가벼운 In-process 구현 (Kafka/Redis 아님)
- 모든 이벤트 로깅 (추적성)
- 동기/비동기 핸들러 구분

작성일: 2026-01-10
"""

from typing import Callable, Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging
import asyncio
from functools import wraps

from .event_types import EventType

logger = logging.getLogger(__name__)


class EventBus:
    """
    In-process Event Bus
    
    사용법:
        event_bus = EventBus()
        event_bus.subscribe(EventType.ORDER_FILLED, handle_fill)
        event_bus.publish(EventType.ORDER_FILLED, {'order_id': 123})
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._async_handlers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Dict] = []
        self._max_history = 1000  # 최대 이력 보관
    
    # ================================================================
    # 구독
    # ================================================================
    
    def subscribe(
        self, 
        event_type: EventType, 
        handler: Callable,
        is_async: bool = False
    ):
        """
        이벤트 구독
        
        Args:
            event_type: 구독할 이벤트 타입
            handler: 핸들러 함수
            is_async: 비동기 핸들러 여부
        """
        if is_async:
            if event_type not in self._async_handlers:
                self._async_handlers[event_type] = []
            self._async_handlers[event_type].append(handler)
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
        
        logger.debug(f"Subscribed {handler.__name__} to {event_type.value} (async={is_async})")
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """이벤트 구독 해제"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]
        if event_type in self._async_handlers:
            self._async_handlers[event_type] = [
                h for h in self._async_handlers[event_type] if h != handler
            ]
    
    # ================================================================
    # 발행
    # ================================================================
    
    def publish(self, event_type: EventType, data: Dict[str, Any]):
        """
        이벤트 발행 (동기)
        
        Args:
            event_type: 이벤트 타입
            data: 이벤트 데이터
        """
        event = self._create_event(event_type, data)
        
        # 로깅 (추적성)
        self._log_event(event)
        
        # 이력 저장
        self._save_history(event)
        
        # 동기 핸들러 실행
        for handler in self._handlers.get(event_type, []):
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Handler {handler.__name__} failed: {e}")
                # 핸들러 실패가 전체 흐름을 막지 않음
    
    async def publish_async(self, event_type: EventType, data: Dict[str, Any]):
        """
        이벤트 발행 (비동기 핸들러 포함)
        
        Args:
            event_type: 이벤트 타입
            data: 이벤트 데이터
        """
        event = self._create_event(event_type, data)
        
        # 로깅
        self._log_event(event)
        
        # 이력 저장
        self._save_history(event)
        
        # 동기 핸들러 먼저
        for handler in self._handlers.get(event_type, []):
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Sync handler {handler.__name__} failed: {e}")
        
        # 비동기 핸들러
        async_handlers = self._async_handlers.get(event_type, [])
        if async_handlers:
            tasks = [handler(data) for handler in async_handlers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for handler, result in zip(async_handlers, results):
                if isinstance(result, Exception):
                    logger.error(f"Async handler {handler.__name__} failed: {result}")
    
    # ================================================================
    # 이력 조회
    # ================================================================
    
    def get_history(
        self, 
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        이벤트 이력 조회
        
        Args:
            event_type: 필터링할 이벤트 타입 (None=전체)
            limit: 최대 조회 개수
            
        Returns:
            List[Dict]: 이벤트 이력
        """
        history = self._event_history
        
        if event_type:
            history = [e for e in history if e['type'] == event_type.value]
        
        return history[-limit:]
    
    def reconstruct_day(self, date: str) -> List[Dict]:
        """
        특정 날짜의 이벤트 흐름 재구성
        
        Args:
            date: 날짜 (YYYY-MM-DD)
            
        Returns:
            List[Dict]: 해당 날짜의 이벤트 목록
        """
        return [
            e for e in self._event_history 
            if e['timestamp'].startswith(date)
        ]
    
    # ================================================================
    # Private 메서드
    # ================================================================
    
    def _create_event(self, event_type: EventType, data: Dict) -> Dict:
        """이벤트 객체 생성"""
        return {
            'type': event_type.value,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': data.get('symbol', data.get('ticker', 'N/A')),
            'order_id': data.get('order_id', data.get('id', None)),
        }
    
    def _log_event(self, event: Dict):
        """이벤트 로깅"""
        log_msg = f"EVENT: {event['type']} | {event['symbol']}"
        
        if event['order_id']:
            log_msg += f" | order:{event['order_id']}"
        
        # 중요 이벤트는 INFO, 나머지는 DEBUG
        important_events = {
            'order_filled', 'order_rejected', 'stop_loss_hit',
            'circuit_breaker', 'risk_alert', 'position_opened', 'position_closed'
        }
        
        if event['type'] in important_events:
            logger.info(log_msg)
        else:
            logger.debug(log_msg)
    
    def _save_history(self, event: Dict):
        """이벤트 이력 저장"""
        self._event_history.append(event)
        
        # 최대 개수 초과 시 오래된 것 제거
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]


# 싱글톤 인스턴스
event_bus = EventBus()
```

---

## ⚠️ 추가 고려사항 (ChatGPT 지적)

### 1. Order State ≠ Position State

현재 설계는 **Order State**에 집중되어 있습니다. 향후 **Position State**도 분리 필요:

```
Order: FULLY_FILLED
  ↓
Position: OPENING → OPEN → CLOSING → CLOSED
```

**지금은 구현하지 않되, 설계 시 인지해야 함.**

### 2. Event Bus 동기/비동기 경계

권장 원칙:
- **State 변경 이벤트** → 동기 (ORDER_FILLED 등)
- **로깅 / 알림 / 분석** → 비동기 (실패해도 주문 흐름 막지 않음)

---

## ✅ 실행 전 체크리스트

코드 작성 전 반드시 확인:

### 필수 조건 (모두 Yes여야 함)

- [ ] `order.status = "xxx"` 직접 변경 코드가 **0개**인가?
- [ ] 상태 전이 실패 시 **예외가 발생**하는가?
- [ ] 재시작 시 `recover_on_startup()`이 자동 실행되는가?
- [ ] 모든 상태 전이가 **로깅**되는가?
- [ ] Event 로그만 보고 하루 흐름을 재구성할 수 있는가?

### 테스트 시나리오

```python
# 테스트 1: 유효한 전이
order = create_test_order()
order_manager.receive_signal(order, signal_data)
assert order.status == "signal_received"

# 테스트 2: 무효한 전이 (예외 발생해야 함)
order.status = "fully_filled"
with pytest.raises(InvalidStateTransitionError):
    order_manager.receive_signal(order, signal_data)  # filled → signal_received 불가

# 테스트 3: Recovery
order = create_order_with_status("order_sent")
await recovery.recover_on_startup()
# 브로커 상태에 따라 동기화 확인
```

---

## 📚 참고 자료

- Ernest P. Chan – *Algorithmic Trading*
- QuantConnect Lean Architecture Docs
- Martin Fowler – *Event-Driven Architecture*
- Anthropic / OpenAI – AI Safety & Guardrails 문서

---

## 🚀 실행 명령

### 1단계: 파일 생성

```bash
# 디렉토리 생성
mkdir -p backend/execution
mkdir -p backend/events

# 파일 생성 (이 문서의 코드 복사)
touch backend/execution/state_machine.py
touch backend/execution/order_manager.py
touch backend/execution/recovery.py
touch backend/events/__init__.py
touch backend/events/event_types.py
touch backend/events/event_bus.py
```

### 2단계: 기존 코드 수정

```bash
# 직접 상태 변경 코드 검색
grep -rn "order.status =" backend/
grep -rn "\.status = " backend/

# 해당 코드를 OrderManager 호출로 변경
```

### 3단계: 테스트

```bash
# 단위 테스트
python -m pytest backend/tests/test_state_machine.py -v

# 통합 테스트
python -m pytest backend/tests/integration/test_order_flow.py -v
```

---


---

## 📈 Phase 4: Strategy & Data Enhancements (ChatGPT Analysis)

**목표**: 프레임워크 안정화 후, 데이터 다양성 및 분석 고도화

### 4.1 Data Diversity (데이터 확장)
*   **Order Flow**: 시장 주문 흐름(Orderbook) 데이터 활용
*   **Derivatives**: 옵션(Options) 데이터, 선물 지표 연동
*   **Alternative Data**: 소셜 센티먼트(Google Trends, Twitter) 등 비정형 데이터 추가

### 4.2 ML Ensembles (모델 고도화)
*   **Hybrid Approach**: LLM(이해/판단) + XGBoost/Transformer(수치 예측) 결합
*   **Ensemble**: 단순 평균이 아닌, 모델별 신뢰도 기반 가중치 적용

### 4.3 Advanced Risk Metrics (리스크 관리 강화)
*   **VaR (Value at Risk)**: 정상 시장에서의 잠재 손실 예측
*   **CVaR (Conditional VaR)**: 꼬리 위험(Tail Risk) 관리
*   **Volatility Estimation/GARCH**: 변동성 예측 모델 도입

### 4.4 Reinforcement Learning (장기 로드맵)
*   **Policy-based RL**: 시장 상황에 따른 최적 전략 자동 선택 (Meta-Labeling)

---

**문서 끝**

**작성**: Claude (Anthropic)  
**검토**: Gemini, ChatGPT  
**승인**: 사용자  
**상태**: ✅ 구현 준비 완료
