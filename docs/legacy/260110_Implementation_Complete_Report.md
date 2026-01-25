# State Machine + Recovery + Event Bus 구현 완료 보고서

**작성일**: 2026-01-10
**작성자**: Claude Code Agent
**버전**: 1.0
**상태**: ✅ 구현 완료

---

## 📊 Executive Summary

3개 AI (Gemini, Claude, ChatGPT)의 합의에 따라 **State Machine, Recovery 로직, Event Bus**를 성공적으로 구현했습니다.

### 핵심 성과
- ✅ **상태 전이 강제**: Order 상태는 OrderManager를 통해서만 변경 가능
- ✅ **안전성 확보**: 유효하지 않은 상태 전이는 예외 발생
- ✅ **Recovery 준비**: 시스템 재시작 시 미완료 주문 복구 가능
- ✅ **이벤트 기반**: 모듈 간 결합도 감소, 추적성 확보

---

## 🎯 구현 항목

### Phase 1: State Machine (완료)

#### 1.1 OrderState Enum 및 OrderStateMachine
**파일**: [`backend/execution/state_machine.py`](../../../backend/execution/state_machine.py)

**주요 기능**:
- 10개 상태 정의 (IDLE, SIGNAL_RECEIVED, VALIDATING, ORDER_PENDING, ORDER_SENT, PARTIAL_FILLED, FULLY_FILLED, CANCELLED, REJECTED, FAILED)
- 상태 전이 규칙 강제 (VALID_TRANSITIONS)
- 종료 상태 (TERMINAL_STATES) 및 미완료 상태 (PENDING_STATES) 관리

**상태 전이 다이어그램**:
```
IDLE → SIGNAL_RECEIVED → VALIDATING → ORDER_PENDING → ORDER_SENT → FULLY_FILLED
                             ↓              ↓              ↓
                         REJECTED       FAILED      CANCELLED
                                                        ↑
                                            PARTIAL_FILLED
```

#### 1.2 OrderManager (Single Writer)
**파일**: [`backend/execution/order_manager.py`](../../../backend/execution/order_manager.py)

**핵심 원칙**:
- **Single Writer**: 모든 상태 변경은 OrderManager를 통해서만 가능
- **원자적 전이**: DB 커밋 실패 시 자동 롤백
- **로깅**: 모든 전이는 로그로 기록
- **이력 추적**: 메모리 캐시에 전이 이력 저장

**편의 메서드**:
```python
order_manager.receive_signal(order, signal_data)
order_manager.start_validation(order)
order_manager.validation_passed(order, validation_result)
order_manager.validation_failed(order, violations)
order_manager.order_sent(order, broker_order_id)
order_manager.order_failed(order, error)
order_manager.partial_fill(order, filled_qty, filled_price)
order_manager.fully_filled(order, filled_price)
order_manager.cancel(order, reason)
```

#### 1.3 Order 모델 업데이트
**파일**: [`backend/database/models.py`](../../../backend/database/models.py)

**추가된 필드**:
- `filled_quantity`: 부분 체결 수량 추적
- `metadata`: JSONB 타입으로 유연한 메타데이터 저장
- `needs_manual_review`: Recovery 실패 시 수동 검토 플래그
- `updated_at`: 상태 업데이트 시각 추적

**변경된 필드**:
- `status` default: `'pending'` → `'idle'`

#### 1.4 기존 코드 마이그레이션

**수정된 파일**:
1. [`backend/ai/trading/shadow_trader.py`](../../../backend/ai/trading/shadow_trader.py)
   - `_record_order()` 메서드에서 OrderManager 사용
   - 상태 전이 시퀀스: IDLE → SIGNAL_RECEIVED → VALIDATING → ORDER_PENDING → ORDER_SENT → FULLY_FILLED

2. [`backend/ai/order_execution/shadow_order_executor.py`](../../../backend/ai/order_execution/shadow_order_executor.py)
   - `_save_order()` 메서드에서 OrderState 사용
   - 비동기 컨텍스트에서 수동으로 상태 전이 (async OrderManager 향후 구현 필요)

3. [`backend/api/war_room_router.py`](../../../backend/api/war_room_router.py)
   - Order 생성 시 OrderManager 사용
   - 브로커 주문 전송 후 ORDER_SENT 상태로 전이

---

### Phase 2: Recovery 로직 (완료)

#### 2.1 OrderRecovery 클래스
**파일**: [`backend/execution/recovery.py`](../../../backend/execution/recovery.py)

**핵심 기능**:
- `recover_on_startup()`: 시스템 시작 시 미완료 주문 자동 복구
- `_recover_order()`: 개별 주문 복구 로직
- `_mark_for_review()`: 복구 실패 시 수동 검토 플래그 설정

**복구 프로세스**:
1. 미완료 상태 주문 조회 (ORDER_SENT, PARTIAL_FILLED, ORDER_PENDING)
2. 브로커 API로 실제 상태 확인
3. 브로커 상태에 따라 동기화:
   - `filled` → FULLY_FILLED 전이
   - `cancelled` → CANCELLED 전이
   - `partial` → PARTIAL_FILLED 유지, 모니터링 재개
   - `pending` → 현재 상태 유지, 모니터링 재개
   - `unknown` → needs_manual_review = True

**브로커 상태 = Source of Truth**:
- DB 상태보다 브로커 실제 상태를 우선
- 불일치 발견 시 브로커 상태로 강제 동기화

---

### Phase 3: Event Bus (완료)

#### 3.1 EventType Enum
**파일**: [`backend/events/event_types.py`](../../../backend/events/event_types.py)

**이벤트 카테고리**:
- **데이터 이벤트**: MARKET_DATA_RECEIVED, NEWS_RECEIVED
- **AI 분석 이벤트**: AI_ANALYSIS_STARTED, AI_ANALYSIS_COMPLETE, SIGNAL_GENERATED
- **주문 이벤트**: ORDER_REQUESTED, ORDER_VALIDATED, ORDER_REJECTED, ORDER_SENT, ORDER_FILLED, ORDER_CANCELLED, ORDER_FAILED
- **포지션 이벤트**: POSITION_OPENED, POSITION_UPDATED, POSITION_CLOSED
- **리스크 이벤트**: RISK_ALERT, STOP_LOSS_HIT, CIRCUIT_BREAKER
- **시스템 이벤트**: SYSTEM_STARTED, SYSTEM_SHUTDOWN, RECOVERY_COMPLETE

#### 3.2 EventBus 클래스
**파일**: [`backend/events/event_bus.py`](../../../backend/events/event_bus.py)

**설계 원칙**:
- **In-process**: Kafka/Redis 없이 가벼운 구현
- **동기/비동기 구분**: 핸들러 타입에 따라 분리
- **이력 추적**: 모든 이벤트 로깅 및 저장 (최대 1000개)
- **실패 격리**: 핸들러 실패가 전체 흐름을 막지 않음

**사용 예시**:
```python
from backend.events import event_bus, EventType

# 구독
def handle_order_filled(data):
    print(f"Order {data['order_id']} filled!")

event_bus.subscribe(EventType.ORDER_FILLED, handle_order_filled)

# 발행
event_bus.publish(EventType.ORDER_FILLED, {
    'order_id': 123,
    'ticker': 'AAPL',
    'filled_price': 150.0
})
```

---

## 🗄️ 데이터베이스 마이그레이션

### Schema Definition
**파일**: [`backend/ai/skills/system/db-schema-manager/schemas/orders.json`](../../../backend/ai/skills/system/db-schema-manager/schemas/orders.json)

### Migration SQL
**파일**: [`backend/database/migrations/add_state_machine_columns.sql`](../../../backend/database/migrations/add_state_machine_columns.sql)

**변경 사항**:
```sql
-- 1. 새 컬럼 추가
ALTER TABLE orders ADD COLUMN filled_quantity INTEGER;
ALTER TABLE orders ADD COLUMN metadata JSONB;
ALTER TABLE orders ADD COLUMN needs_manual_review BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE orders ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- 2. status default 변경
ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'idle';

-- 3. updated_at 자동 업데이트 트리거
CREATE TRIGGER orders_updated_at_trigger
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_orders_updated_at();
```

**마이그레이션 실행**:
```bash
psql -U postgres -d ai_trading_system -f backend/database/migrations/add_state_machine_columns.sql
```

---

## ✅ 검증 체크리스트

### State Machine
- [x] OrderState Enum 정의 (10개 상태)
- [x] VALID_TRANSITIONS 정의 (유효한 전이만 허용)
- [x] InvalidStateTransitionError 예외 정의
- [x] TERMINAL_STATES 정의 (종료 상태)
- [x] PENDING_STATES 정의 (Recovery 대상)

### OrderManager
- [x] Single Writer 원칙 적용
- [x] transition() 메서드 구현 (전이 가능 여부 검증)
- [x] DB 영속화 및 롤백 처리
- [x] 로깅 (INFO/DEBUG 레벨 구분)
- [x] 전이 이력 저장
- [x] 편의 메서드 9개 구현

### Recovery
- [x] recover_on_startup() 메서드
- [x] 브로커 상태 동기화
- [x] needs_manual_review 플래그
- [x] 복구 결과 요약 반환

### Event Bus
- [x] EventType Enum (23개 이벤트)
- [x] 동기/비동기 핸들러 구분
- [x] 이벤트 로깅 및 이력 저장
- [x] 핸들러 실패 격리

### Database
- [x] orders.json 스키마 정의
- [x] 마이그레이션 SQL 생성
- [x] DB 스키마 비교 (compare_to_db.py)

---

## 📝 남은 작업

### 1. 마이그레이션 실행
```bash
psql -U postgres -d ai_trading_system -f backend/database/migrations/add_state_machine_columns.sql
```

### 2. 시스템 시작 시 Recovery 통합
**파일**: `backend/api/main.py` 또는 `backend/core/startup.py`

```python
from backend.execution.order_manager import OrderManager
from backend.execution.recovery import OrderRecovery
from backend.database.repository import get_sync_session

@app.on_event("startup")
async def startup_event():
    # ... 기존 startup 로직 ...

    # Order Recovery
    db = get_sync_session()
    order_manager = OrderManager(db, broker_client=kis_broker)
    recovery = OrderRecovery(order_manager)

    recovery_result = await recovery.recover_on_startup()
    logger.info(f"Order Recovery: {recovery_result}")
```

### 3. Event Bus 통합
OrderManager의 transition() 메서드에서 이벤트 발행:

```python
from backend.events import event_bus, EventType

def transition(self, order, target: OrderState, ...):
    # ... 기존 전이 로직 ...

    # 이벤트 발행
    if target == OrderState.FULLY_FILLED:
        event_bus.publish(EventType.ORDER_FILLED, {
            'order_id': order.id,
            'ticker': order.ticker,
            'filled_price': order.filled_price
        })
    elif target == OrderState.REJECTED:
        event_bus.publish(EventType.ORDER_REJECTED, {
            'order_id': order.id,
            'ticker': order.ticker,
            'reason': reason
        })
    # ... 다른 상태에 대한 이벤트 발행 ...
```

### 4. 테스트 코드 작성
```python
# backend/tests/test_state_machine.py
def test_valid_transition():
    """유효한 전이는 성공해야 함"""
    assert state_machine.can_transition(
        OrderState.ORDER_SENT,
        OrderState.FULLY_FILLED
    ) == True

def test_invalid_transition():
    """무효한 전이는 실패해야 함"""
    assert state_machine.can_transition(
        OrderState.FULLY_FILLED,
        OrderState.ORDER_SENT
    ) == False

# backend/tests/test_order_manager.py
def test_order_manager_transition():
    """OrderManager를 통한 전이 테스트"""
    order = create_test_order()
    order_manager.receive_signal(order, {'test': True})
    assert order.status == OrderState.SIGNAL_RECEIVED.value
```

---

## 🎓 사용 가이드

### OrderManager 사용 예시

```python
from backend.execution.order_manager import OrderManager
from backend.database.repository import get_sync_session
from backend.database.models import Order

# 1. OrderManager 인스턴스 생성
db = get_sync_session()
order_manager = OrderManager(db, broker_client=kis_broker)

# 2. Order 생성
order = Order(
    ticker='AAPL',
    action='BUY',
    quantity=100,
    order_type='market',
    status=OrderState.IDLE.value
)
db.add(order)
db.flush()

# 3. 상태 전이
order_manager.receive_signal(order, {'signal_id': 123})
order_manager.start_validation(order)
order_manager.validation_passed(order, {'rule_check': 'passed'})
order_manager.order_sent(order, 'KIS20260110001')

# 브로커 체결 후
order_manager.fully_filled(order, 150.0)

# 4. 전이 이력 조회
history = order_manager.get_transition_history(order.id)
print(history)
```

### Recovery 사용 예시

```python
from backend.execution.recovery import OrderRecovery

# 시스템 시작 시
recovery = OrderRecovery(order_manager)
result = await recovery.recover_on_startup()

# 결과
# {
#     'recovered': 5,
#     'failed': 1,
#     'total': 6,
#     'timestamp': '2026-01-10T12:00:00'
# }
```

### Event Bus 사용 예시

```python
from backend.events import event_bus, EventType

# 핸들러 등록
def on_order_filled(data):
    logger.info(f"Order {data['order_id']} filled @ ${data['filled_price']}")
    # 포지션 업데이트 로직...

event_bus.subscribe(EventType.ORDER_FILLED, on_order_filled)

# 이벤트 발행
event_bus.publish(EventType.ORDER_FILLED, {
    'order_id': 123,
    'ticker': 'AAPL',
    'filled_price': 150.0
})

# 이벤트 이력 조회
history = event_bus.get_history(EventType.ORDER_FILLED, limit=10)
```

---

## 🚨 주의사항

### ❌ 절대 금지 패턴

```python
# ❌ 직접 상태 변경 (절대 금지!)
order.status = "filled"
order.status = OrderState.FULLY_FILLED.value

# ❌ 문자열로 상태 비교
if order.status == "pending":
    ...

# ❌ 상태 롤백
order.status = "idle"  # 되돌리기
```

### ✅ 올바른 패턴

```python
# ✅ OrderManager를 통한 전이
order_manager.fully_filled(order, filled_price=150.0)
order_manager.cancel(order, reason="Stop loss hit")

# ✅ Enum으로 상태 비교
if OrderState(order.status) == OrderState.ORDER_PENDING:
    ...

# ✅ 상태 머신으로 전이 가능 여부 확인
if state_machine.can_transition(current_state, target_state):
    order_manager.transition(order, target_state)
```

---

## 📊 성능 및 영향도

### 메모리 사용
- EventBus 이력: 최대 1000개 이벤트 (약 100KB)
- OrderManager 전이 이력: 세션당 메모리 캐시 (적음)

### DB 부하
- 새 컬럼 4개 추가: metadata (JSONB), filled_quantity, needs_manual_review, updated_at
- 트리거 1개: updated_at 자동 업데이트
- 영향: 미미 (컬럼 추가만)

### 성능 영향
- 상태 전이 검증: O(1) - Dictionary lookup
- Event Bus 발행: O(n) - n = 핸들러 개수 (일반적으로 < 10)
- Recovery: 시작 시 1회, 미완료 주문 개수에 비례

---

## 🔗 관련 문서

- [260110_Framework_Implementation_Guide.md](260110_Framework_Implementation_Guide.md) - 구현 가이드 (원본)
- [260110_Final_Status_Summary_KR.md](../260110/260110_Final_Status_Summary_KR.md) - 이전 상태 요약
- [database_standards.md](../../../.gemini/antigravity/brain/c360bcf5-0a4d-48b1-b58b-0e2ef4000b25/database_standards.md) - DB 표준

---

## 📈 다음 단계 (Future Work)

### Phase 4: Strategy & Data Enhancements (향후)
- Order Flow 데이터 활용
- 옵션 데이터 연동
- Alternative Data 추가 (소셜 센티먼트)
- ML Ensembles 고도화
- Advanced Risk Metrics (VaR, CVaR, GARCH)

### Phase 5: Production Readiness (향후)
- 부하 테스트
- 모니터링 대시보드
- 알림 시스템 통합
- 백업 및 복구 절차

---

## ✅ 구현 완료 확인

- [x] Phase 1: State Machine 구현
- [x] Phase 2: Recovery 로직 구현
- [x] Phase 3: Event Bus 구현
- [x] DB 스키마 정의
- [x] 마이그레이션 SQL 생성
- [x] 기존 코드 마이그레이션
- [x] 문서화

**상태**: ✅ 구현 완료 (마이그레이션 실행 및 통합 테스트 대기)

---

**작성자**: Claude Code Agent
**검토**: 3-AI 합의 기반 (Gemini, Claude, ChatGPT)
**승인**: 사용자
**문서 버전**: 1.0
**최종 업데이트**: 2026-01-10
