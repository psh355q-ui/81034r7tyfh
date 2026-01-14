# Phase 3: 충돌 감지 및 소유권 이전 통합 완료 보고서
날짜: 2026-01-12

## 1. 진행 내용 요약

오늘 작업은 **Phase 3: 충돌 감지 엔진 (Conflict Detection Engine)**의 핵심 기능을 구현하고 통합하는 데 집중했습니다.

### 주요 구현 사항
1.  **충돌 감지 로직 통합 (T3.2)**
    *   `OrderManager`가 주문 생성 시 `ConflictDetector`를 호출하도록 수정했습니다.
    *   **Blocking Logic**: 더 높은 우선순위의 전략이 소유한 종목을 낮은 우선순위 전략이 건드리지 못하도록 차단합니다.
2.  **소유권 이전 및 우선순위 오버라이드 (T3.3)**
    *   **Priority Override**: 높은 우선순위 전략(예: Long Term)이 낮은 우선순위 전략(예: Aggressive)의 포지션을 가져올 수 있도록 구현했습니다.
    *   `ConflictDetector`가 `PRIORITY_OVERRIDE` 판단을 내리면, `OwnershipService`를 통해 소유권을 즉시 이전합니다.
3.  **DB 스키마 검증 (Schema Manager)**
    *   `VARCHAR(10)` 길이 제한으로 인한 테스트 실패 문제를 해결하기 위해 `VARCHAR(50)`으로 확장했습니다.
    *   `backend/scripts/check_schema.py` 스크립트를 통해 실제 DB(`position_ownership`, `conflict_logs`)의 컬럼 타입이 변경되었음을 검증했습니다.

---

## 2. 트러블슈팅 (Troubleshooting Log)

작업 도중 발생한 주요 오류와 해결 과정입니다.

### 오류 1: `DetachedInstanceError` (ORM Session Issue)
*   **증상**: `OwnershipService`에서 소유권 이전 후 `target_strategy.name` 등에 접근할 때, 객체가 세션에서 분리(Detached)되었다는 에러 발생.
*   **원인**: `session.flush()` 또는 `commit()` 이후 SQLAlchemy가 객체를 만료(Expire/Invalidate)시키는데, 이후 지연 로딩(Lazy Loading)으로 연관 객체(`strategy`)에 접근하려다 세션이 닫혀있거나 연결이 끊겨 발생.
*   **해결 시도**:
    1.  `session.refresh()` / `session.merge()` 사용 -> 효과 미미.
    2.  Raw SQL 사용 -> 파라미터 바인딩 오류 발생.
*   **최종 해결**: **"Early Capture & Query Update Pattern"** 적용
    *   객체의 속성(이름, ID 등)을 DB 수정 **전에** 미리 변수에 저장(Copy).
    *   DB 업데이트는 ORM 객체 수정 대신 `session.query(...).update(...)`를 사용하여 인스턴스 상태와 무관하게 처리.
    *   리턴 값은 미리 저장해둔 변수를 사용하여 안전하게 반환.

### 오류 2: SQL Binding Error (`ProgrammingError: %(param)s`)
*   **증상**: Raw SQL 사용 시 파라미터 바인딩이 실패하거나, 엉뚱한 값(ex: `ownership_type_1`)을 찾음.
*   **원인**: SQLAlchemy ORM의 자동 플러시(Autoflush)가 Raw SQL 실행 시점과 겹치면서, 더티 체킹(Dirty Checking) 중인 객체와 충돌하거나 파라미터 해석 방식(dict vs tuples)이 드라이버와 맞지 않음.
*   **최종 해결**: Raw SQL 대신 SQLAlchemy Core의 `update()` 메서드(`session.query(...).update(...)`)를 사용하여 안전하고 표준적인 방식으로 처리.

---

## 3. 결과 확인
*   **Integration Test**: `backend/tests/test_order_conflict_integration.py`
    *   Scenario 1 (Block): 정상 차단 확인.
    *   Scenario 2 (Override): 정상 이전 및 로그 기록 확인.
*   **Schema Check**: `ticker` 컬럼 `VARCHAR(50)` 적용 확인.

## 4. 향후 계획 (Next Steps)
*   **Phase 4: Order Execution Lifecycle** 진입
*   실제 주문 집행(`OrderExecutor`) 및 상태 천이(`FILLED`, `REJECTED`) 로직 구현.
