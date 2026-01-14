# State Machine + Recovery + Event Bus 구현 완료 보고서
**Date**: 2026-01-10
**Status**: ✅ Phase 1-3 구현 완료

---

## 📋 구현 개요

3-AI 합의(Gemini, Claude, ChatGPT)를 기반으로 주문 관리 시스템의 핵심 인프라를 구현했습니다:
- **Phase 1**: State Machine (주문 상태 관리)
- **Phase 2**: Recovery Logic (시스템 재시작 복구)
- **Phase 3**: Event Bus (이벤트 기반 아키텍처)

---

## 🎯 구현 완료 항목

### Phase 1: State Machine

#### 1. `backend/execution/state_machine.py` (NEW)
- **OrderState Enum**: 10개 상태 정의
  ```python
  class OrderState(Enum):
      IDLE = "idle"                    # 초기 상태
      SIGNAL_RECEIVED = "signal_received"
      VALIDATING = "validating"
      ORDER_PENDING = "order_pending"
      ORDER_SENT = "order_sent"
      PARTIAL_FILLED = "partial_filled"
      FULLY_FILLED = "fully_filled"
      CANCELLED = "cancelled"
      REJECTED = "rejected"
      FAILED = "failed"
  ```

- **OrderStateMachine**: 상태 전이 규칙 정의
  - 유효한 전이만 허용 (예: IDLE → SIGNAL_RECEIVED)
  - 잘못된 전이 시 `InvalidStateTransitionError` 발생

#### 2. `backend/execution/order_manager.py` (NEW)
- **Single Writer 패턴** 구현
- 모든 주문 상태 변경은 반드시 OrderManager를 통해서만 가능
- 주요 메서드:
  - `receive_signal()`: 시그널 수신
  - `start_validation()`: 검증 시작
  - `validation_passed()`/`validation_failed()`: 검증 결과
  - `order_sent()`: 주문 전송
  - `fully_filled()`/`partially_filled()`: 체결
  - `cancel()`/`reject()`/`fail()`: 실패 처리

- **Event Bus 통합**: 상태 전이 시 이벤트 자동 발행
  ```python
  def _publish_event(self, order, to_state: OrderState, reason: Optional[str]):
      event_map = {
          OrderState.ORDER_SENT: EventType.ORDER_SENT,
          OrderState.FULLY_FILLED: EventType.ORDER_FILLED,
          OrderState.CANCELLED: EventType.ORDER_CANCELLED,
          OrderState.REJECTED: EventType.ORDER_REJECTED,
          OrderState.FAILED: EventType.ORDER_FAILED,
      }
      if event_type := event_map.get(to_state):
          event_bus.publish(event_type, event_data)
  ```

#### 3. Database Schema 업데이트

**Orders 테이블 컬럼 추가**:
```sql
-- backend/database/migrations/add_state_machine_columns.sql
ALTER TABLE orders ADD COLUMN IF NOT EXISTS filled_quantity INTEGER;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_metadata JSONB;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS needs_manual_review BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Trigger for auto-updating updated_at
CREATE OR REPLACE FUNCTION update_orders_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER orders_updated_at_trigger
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_orders_updated_at();
```

**⚠️ 중요: SQLAlchemy 예약어 충돌 해결**
- 초기에 `metadata` 컬럼명 사용 → SQLAlchemy 예약어 충돌
- `order_metadata`로 변경하여 해결

**Migration 실행 완료**:
```bash
✅ New columns verified:
  - filled_quantity: integer (nullable: YES)
  - order_metadata: jsonb (nullable: YES)
  - needs_manual_review: boolean (nullable: NO, default: false)
  - updated_at: timestamp (nullable: NO, default: CURRENT_TIMESTAMP)
```

#### 4. `backend/database/models.py` 수정
```python
class Order(Base):
    # ... existing fields ...
    filled_quantity = Column(Integer, nullable=True)
    order_metadata = Column(JSONB, nullable=True)  # Not 'metadata' (reserved)
    needs_manual_review = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
```

#### 5. 기존 코드 리팩토링 (OrderManager 사용)

**변경된 파일**:
1. `backend/ai/trading/shadow_trader.py:234-260`
2. `backend/ai/order_execution/shadow_order_executor.py:123-140`
3. `backend/api/war_room_router.py:215-225`

**Before (직접 status 변경)**:
```python
order.status = "FILLED"
db.commit()
```

**After (OrderManager 사용)**:
```python
order_manager = OrderManager(db)
order_manager.receive_signal(order, {"signal_id": signal.id})
order_manager.start_validation(order)
order_manager.validation_passed(order, {"shadow_mode": True})
order_manager.order_sent(order, order.order_id)
order_manager.fully_filled(order, price)
```

---

### Phase 2: Recovery Logic

#### 1. `backend/execution/recovery.py` (NEW)
```python
class OrderRecovery:
    """시스템 재시작 시 미처리 주문 복구"""

    async def recover_on_startup(self) -> Dict:
        pending_orders = self.om.get_pending_orders()

        for order in pending_orders:
            # Broker 상태 확인 (Source of Truth)
            broker_status = await self.om.broker.get_order_status(order.order_id)

            # 상태 동기화
            if broker_state == 'filled':
                self.om.fully_filled(order, broker_status.get('filled_price'))
            elif broker_state == 'cancelled':
                self.om.cancel(order, "Recovered as cancelled from broker")
            # ... more cases
```

**복구 전략**:
- Broker를 "진실의 원천(Source of Truth)"으로 사용
- 시스템 재시작 시 pending 상태 주문 자동 복구
- 복구 실패 시 `needs_manual_review = True` 플래그 설정

#### 2. `backend/main.py` 통합
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup code ...

    # 🔄 Order Recovery on Startup (State Machine Phase 2)
    try:
        logger.info("🔄 Starting Order Recovery...")
        db = get_sync_session()
        order_manager = OrderManager(db, broker_client=None)
        recovery = OrderRecovery(order_manager)
        recovery_result = await recovery.recover_on_startup()

        if recovery_result['total'] > 0:
            logger.info(f"✅ Order Recovery Complete: {recovery_result['recovered']}/{recovery_result['total']}")
        else:
            logger.info("✅ No pending orders to recover")
    except Exception as e:
        logger.error(f"❌ Order Recovery failed: {e}")
```

---

### Phase 3: Event Bus

#### 1. `backend/events/event_types.py` (NEW)
23개 이벤트 타입 정의:
```python
class EventType(Enum):
    # Order Events (5)
    ORDER_SENT = "order_sent"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    ORDER_FAILED = "order_failed"

    # Signal Events (3)
    SIGNAL_RECEIVED = "signal_received"
    SIGNAL_VALIDATED = "signal_validated"
    SIGNAL_REJECTED = "signal_rejected"

    # Position Events (4)
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"
    POSITION_STOP_LOSS_TRIGGERED = "position_stop_loss_triggered"

    # Risk Events (3)
    RISK_LIMIT_EXCEEDED = "risk_limit_exceeded"
    KILL_SWITCH_ACTIVATED = "kill_switch_activated"
    RISK_ALERT = "risk_alert"

    # War Room Events (3)
    DEBATE_STARTED = "debate_started"
    DEBATE_ENDED = "debate_ended"
    CONSENSUS_REACHED = "consensus_reached"

    # System Events (5)
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    ERROR_OCCURRED = "error_occurred"
```

#### 2. `backend/events/event_bus.py` (NEW)
```python
class EventBus:
    """In-process Event Bus (Phase 3)"""

    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._history: List[Dict] = []

    def subscribe(self, event_type: EventType, handler: Callable):
        """이벤트 핸들러 등록"""

    def publish(self, event_type: EventType, data: Dict[str, Any]):
        """이벤트 발행"""
        event = self._create_event(event_type, data)
        self._log_event(event)
        self._save_history(event)

        for handler in self._handlers.get(event_type, []):
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Event handler failed: {e}")
```

**특징**:
- In-process 이벤트 버스 (멀티프로세스는 추후 고려)
- 이벤트 히스토리 저장 (메모리)
- 핸들러 실패 시에도 다른 핸들러 계속 실행

#### 3. OrderManager 통합
- 주요 상태 전이 시 자동으로 이벤트 발행
- `_publish_event()` 메서드에서 처리

---

## 🔧 기술적 결정사항

### 1. Single Writer 패턴
- **문제**: 여러 곳에서 직접 `order.status` 수정 → 일관성 문제
- **해결**: OrderManager만 상태 변경 가능하도록 강제
- **효과**: 상태 전이 검증, 이벤트 발행, 메타데이터 업데이트 일관성 보장

### 2. Broker as Source of Truth
- **문제**: 시스템 재시작 시 주문 상태 불일치
- **해결**: 복구 시 Broker 상태를 기준으로 동기화
- **효과**: 데이터 정합성 보장

### 3. JSONB 메타데이터
- **선택**: `order_metadata JSONB`
- **이유**: 유연한 메타데이터 저장 (signal_data, validation_result, broker_info 등)
- **장점**: 스키마 변경 없이 확장 가능

### 4. 예약어 충돌 해결
- **문제**: SQLAlchemy에서 `metadata` 예약어 사용
- **해결**: `order_metadata`로 변경
- **영향 범위**:
  - `backend/database/models.py`
  - `backend/execution/order_manager.py`
  - `backend/database/migrations/add_state_machine_columns.sql`
  - `backend/ai/skills/system/db-schema-manager/schemas/orders.json`

---

## 📊 상태 전이 다이어그램

```
IDLE
 ├─→ SIGNAL_RECEIVED
      ├─→ VALIDATING
      │    ├─→ ORDER_PENDING
      │    │    ├─→ ORDER_SENT
      │    │    │    ├─→ PARTIAL_FILLED → FULLY_FILLED
      │    │    │    ├─→ FULLY_FILLED
      │    │    │    ├─→ CANCELLED
      │    │    │    └─→ FAILED
      │    │    └─→ REJECTED
      │    └─→ REJECTED
      └─→ REJECTED
```

---

## 🧪 테스트 필요 항목

### Phase 1: State Machine
- [ ] 유효한 상태 전이 테스트
- [ ] 잘못된 상태 전이 시 예외 발생 테스트
- [ ] OrderManager를 통한 메타데이터 업데이트 테스트

### Phase 2: Recovery
- [ ] 시스템 재시작 시 pending 주문 복구 테스트
- [ ] Broker 상태 동기화 테스트
- [ ] 복구 실패 시 manual_review 플래그 테스트

### Phase 3: Event Bus
- [ ] 이벤트 발행/구독 테스트
- [ ] 여러 핸들러 등록 테스트
- [ ] 핸들러 실패 시에도 다른 핸들러 실행 테스트

---

## 📝 다음 단계

### 1. 백엔드 재시작 및 검증
```bash
# 백엔드 재시작
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# 로그 확인
# ✅ Order Recovery Complete: X/Y
# ✅ No pending orders to recover
```

### 2. 통합 테스트
- Shadow Trading 실행하여 전체 플로우 테스트
- 상태 전이가 올바르게 동작하는지 확인
- Event Bus 이벤트 발행 확인

### 3. 단위 테스트 작성
- `tests/test_state_machine.py`
- `tests/test_order_manager.py`
- `tests/test_recovery.py`
- `tests/test_event_bus.py`

### 4. 문서화
- [x] 구현 완료 보고서 작성
- [ ] API 문서 업데이트
- [ ] 아키텍처 다이어그램 업데이트

---

## 🎉 결론

✅ **Phase 1-3 구현 완료**
- State Machine: 10개 상태, 유효 전이 검증
- Recovery Logic: Broker 기반 자동 복구
- Event Bus: 23개 이벤트 타입, 핸들러 시스템

✅ **DB Migration 완료**
- 4개 컬럼 추가 (filled_quantity, order_metadata, needs_manual_review, updated_at)
- Trigger 생성 (auto-update updated_at)

✅ **기존 코드 리팩토링 완료**
- 3개 파일에서 OrderManager 사용으로 변경
- Single Writer 패턴 적용

🔜 **다음 작업**
- 백엔드 재시작 후 Recovery 동작 확인
- 통합 테스트 및 단위 테스트 작성
- Event Bus 핸들러 추가 구현 (알림, 로깅 등)

---

## 📂 변경된 파일 목록

### New Files (8)
1. `backend/execution/state_machine.py` - State Machine 구현
2. `backend/execution/order_manager.py` - Single Writer 패턴
3. `backend/execution/recovery.py` - Recovery Logic
4. `backend/events/__init__.py` - Event Bus 모듈
5. `backend/events/event_types.py` - 23개 이벤트 타입
6. `backend/events/event_bus.py` - Event Bus 구현
7. `backend/database/migrations/add_state_machine_columns.sql` - DB Migration
8. `backend/ai/skills/system/db-schema-manager/schemas/orders.json` - Schema 정의

### Modified Files (5)
1. `backend/database/models.py` - Order 모델에 4개 컬럼 추가
2. `backend/main.py` - Recovery 통합
3. `backend/ai/trading/shadow_trader.py` - OrderManager 사용
4. `backend/ai/order_execution/shadow_order_executor.py` - OrderManager 사용
5. `backend/api/war_room_router.py` - OrderManager 사용

### Helper Files (2)
1. `run_migration.py` - DB Migration 실행 스크립트
2. `MIGRATION_MANUAL.sql` - 수동 마이그레이션 가이드

---

**Generated by**: Claude Code
**Implementation Period**: 2026-01-10
**Status**: ✅ Ready for Testing
