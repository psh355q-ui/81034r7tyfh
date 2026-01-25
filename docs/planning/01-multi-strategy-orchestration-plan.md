# 멀티 전략 오케스트레이션 - 통합 기획서

**Version**: 1.0
**Date**: 2026-01-11
**Status**: Planning Complete

<!-- 
✅ 구현 완료 (2026-01-24)
- Conflict Detector: backend/ai/skills/system/conflict_detector.py
- Strategy Registry: backend/database/models.py (Strategy)
- Position Ownership: backend/database/models.py (PositionOwnership)
- Strategy Manager: backend/strategies/ensemble_strategy.py
- Adaptive Strategy Manager: backend/strategies/adaptive_strategy.py
-->

## MVP 캡슐

| # | 항목 | 내용 |
|---|------|------|
| 1 | 목표 | 시장 상황에 따라 최적 전략 조합을 선택하여 수익 극대화 |
| 2 | 페르소나 | 개인 투자자 (trading/long_term/dividend/aggressive 다중 페르소나 운영) |
| 3 | 핵심 기능 (MVP) | **FEAT-1: 전략 간 충돌 방지** - 장기 전략 보유 종목을 단기 전략이 손절하지 않도록 차단 |
| 4 | 성공 지표 (노스스타) | 전략 충돌 발생 0건 유지 |
| 5 | 입력 지표 | ① 전략별 성과 추적률 90% 이상<br>② 멀티 전략 운영 시 단일 대비 수익률 향상 |
| 6 | 비기능 요구 | AI 설명 가능성 - 모든 매매 결정에 대한 reasoning 제공 |
| 7 | Out-of-scope | 자본 분배 최적화는 v2, 단순 N분할 방식은 피함 |
| 8 | Top 리스크 | 전략 간 충돌 감지 로직이 누락되면 오히려 손실 증가 |
| 9 | 완화/실험 | Event Bus 활용한 실시간 충돌 감지, State Machine으로 주문 상태 추적 |
| 10 | 다음 단계 | DB 스키마 설계 → 충돌 감지 엔진 구현 → 테스트 |

---

## 1. 문제 정의

### 1.1 현재 상황 (As-Is)

**핵심 문제**: 장기 투자 전략과 단기 트레이딩 전략이 같은 종목에 대해 반대 신호를 내릴 때 충돌 발생

**실제 시나리오**:
```
Day 1: Long-Term Strategy가 NVDA를 매수 ($120, 보유 목표 3개월)
Day 5: Short-Term Strategy가 NVDA에 손절 신호 발생 ($118)
결과: 단기 손절로 장기 전략이 망가짐 → 불필요한 손실
```

**War Room MVP의 한계**:
- 단일 신호에 대한 합의만 가능
- 여러 전략이 동시에 다른 시간 프레임으로 운영될 때 조정 불가
- 포지션 소유권 개념 없음

### 1.2 목표 상황 (To-Be)

**전략 간 충돌 자동 감지 및 해결**:
1. 각 전략이 어떤 포지션을 소유하는지 명확히 추적
2. 새로운 주문이 기존 포지션과 충돌하는지 실시간 검사
3. 충돌 발생 시 우선순위 규칙에 따라 자동 해결 또는 차단
4. 모든 결정에 대한 설명 제공 (reasoning)

### 1.3 왜 지금인가?

**동기**:
- 2026-01-10 State Machine 및 Event Bus 구현 완료
- 멀티 전략 기반이 준비됨
- 불확실한 시장 환경에서 리스크 분산 필요성 증가

---

## 2. 사용자 페르소나

### 2.1 주요 페르소나: "전략가 김투자"

| 항목 | 내용 |
|------|------|
| 배경 | 개인 투자자, AI 트레이딩 시스템 운영 3개월차 |
| 투자 스타일 | 다중 페르소나 운영 (trading 30% / long_term 50% / dividend 20%) |
| 핵심 니즈 | 여러 전략을 동시에 안전하게 운영하고 싶음 |
| 불편 포인트 | 단기 전략이 장기 보유 종목을 손절해버리는 충돌 경험 |
| 사용 상황 | 매일 아침 전략별 포트폴리오 확인, 주말에 전략 성과 리뷰 |

### 2.2 페르소나의 하루

```
07:00 - 시스템 접속, 전략별 포지션 현황 확인
08:00 - 전략 충돌 경고 확인 (있다면)
09:30 - 장 시작, 전략별 신호 실시간 모니터링
12:00 - 점심, 오전 거래 요약 확인
16:00 - 장 마감, 전략별 P&L 확인
21:00 - 다음날 전략 조정 (필요 시)
```

---

## 3. 사용자 스토리

### FEAT-0: 기존 시스템 (구현 완료)

- [x] War Room MVP - 3+1 에이전트 의사결정
- [x] State Machine - 주문 상태 관리
- [x] Event Bus - 이벤트 기반 아키텍처
- [x] Recovery Logic - 시스템 재시작 복구

### FEAT-1: 전략 간 충돌 방지 (MVP - 이번 구현)

- [ ] **투자자로서**, 각 전략이 어떤 포지션을 소유하는지 확인할 수 있어야 한다.
  **왜냐하면** 포지션 소유권이 명확해야 충돌을 판단할 수 있기 때문이다.

- [ ] **시스템으로서**, 새로운 주문 실행 전에 기존 포지션과의 충돌 여부를 자동 검사해야 한다.
  **왜냐하면** 사전에 충돌을 감지해야 손실을 방지할 수 있기 때문이다.

- [ ] **투자자로서**, 충돌이 감지되면 어떤 전략들이 왜 충돌하는지 설명을 볼 수 있어야 한다.
  **왜냐하면** AI의 결정을 이해하고 신뢰할 수 있어야 하기 때문이다.

- [ ] **시스템으로서**, 충돌 발생 시 우선순위 규칙에 따라 자동으로 해결하거나 주문을 차단해야 한다.
  **왜냐하면** 수동 개입 없이 안전하게 운영되어야 하기 때문이다.

### FEAT-2: 시장 상황 평가 및 전략 선택 (v2)

- [ ] 현재 시장 regime 자동 분류 (상승/하락/보합)
- [ ] 각 전략의 적합도 점수 계산
- [ ] 시장 상황에 따라 전략 자동 활성화/비활성화

### FEAT-3: 전략 성과 모니터링 (v2)

- [ ] 전략별 실시간 P&L 추적
- [ ] 전략 간 성과 비교 대시보드
- [ ] 주간/월간 성과 리포트 자동 생성

---

## 4. 성공 지표

### 4.1 노스스타 지표 (결과 지표)

| 지표명 | 정의 | 목표치 | 측정 주기 |
|--------|------|--------|----------|
| 전략 충돌 발생 건수 | 충돌 감지 → 차단된 주문 수 | 0건 (감지는 OK, 실행은 차단) | 일간 |

### 4.2 입력 지표 (행동 지표)

| 지표명 | 정의 | 목표치 |
|--------|------|--------|
| 전략별 성과 추적률 | 모든 거래에 전략 태그 부여 비율 | 90% 이상 |
| 멀티 전략 수익률 | 멀티 전략 운영 시 수익률 | 단일 전략 대비 향상 |
| AI 설명 제공률 | reasoning 필드 채워진 비율 | 100% |

---

## 5. 시스템 아키텍처

### 5.1 고수준 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│              Multi-Strategy Orchestration Layer              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐      ┌──────────────────┐           │
│  │ Strategy Registry│      │ Conflict Detector│           │
│  │  - Metadata      │─────▶│  - Rules Engine  │           │
│  │  - Ownership     │      │  - Priority      │           │
│  └──────────────────┘      └──────────────────┘           │
│           │                         │                      │
│           │                         ▼                      │
│           │              ┌──────────────────┐            │
│           └─────────────▶│  Order Manager   │            │
│                          │  (State Machine) │            │
│                          └──────────────────┘            │
│                                   │                        │
└───────────────────────────────────┼────────────────────────┘
                                    │
                            ┌───────▼────────┐
                            │   Event Bus    │
                            │  - Publish     │
                            │  - Subscribe   │
                            └────────────────┘
```

### 5.2 핵심 컴포넌트

| 컴포넌트 | 역할 | 기존 시스템 활용 |
|----------|------|-----------------|
| **Strategy Registry** | 전략 메타데이터 관리 | 신규 |
| **Conflict Detector** | 충돌 감지 및 해결 | 신규 |
| **Position Tracker** | 포지션 소유권 추적 | 기존 DB 확장 |
| **Order Manager** | 주문 상태 관리 | ✅ 기존 (State Machine) |
| **Event Bus** | 이벤트 발행/구독 | ✅ 기존 |

---

## 6. 데이터베이스 설계

### 6.1 새로운 테이블

#### strategies (전략 레지스트리)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK | 전략 고유 ID |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 전략명 (trading, long_term, etc.) |
| display_name | VARCHAR(100) | NOT NULL | 표시 이름 |
| persona_type | VARCHAR(50) | NOT NULL | PersonaRouter 타입 |
| priority | INTEGER | NOT NULL | 충돌 시 우선순위 (높을수록 우선) |
| time_horizon | VARCHAR(20) | NOT NULL | short/medium/long |
| is_active | BOOLEAN | DEFAULT true | 활성화 여부 |
| config_metadata | JSONB | NULL | 전략별 설정 |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 수정일 |

**인덱스:**
- `idx_strategies_name` ON name
- `idx_strategies_priority` ON priority DESC

#### position_ownership (포지션 소유권)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK | 고유 ID |
| position_id | UUID | FK → positions.id | 포지션 ID |
| strategy_id | UUID | FK → strategies.id | 소유 전략 |
| ticker | VARCHAR(10) | NOT NULL | 종목 코드 |
| ownership_type | VARCHAR(20) | NOT NULL | primary/shared |
| locked_until | TIMESTAMP | NULL | 잠금 해제 시간 |
| reasoning | TEXT | NULL | 소유 이유 |
| created_at | TIMESTAMP | DEFAULT NOW() | 생성일 |

**인덱스:**
- `idx_ownership_position` ON position_id
- `idx_ownership_strategy` ON strategy_id
- `idx_ownership_ticker` ON ticker

#### conflict_logs (충돌 로그)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK | 고유 ID |
| ticker | VARCHAR(10) | NOT NULL | 종목 코드 |
| conflicting_strategy_id | UUID | FK → strategies.id | 충돌 전략 |
| owning_strategy_id | UUID | FK → strategies.id | 소유 전략 |
| action_attempted | VARCHAR(10) | NOT NULL | buy/sell |
| action_blocked | BOOLEAN | NOT NULL | 차단 여부 |
| resolution | VARCHAR(50) | NOT NULL | allowed/blocked/priority_override |
| reasoning | TEXT | NOT NULL | 충돌 이유 및 해결 방법 |
| created_at | TIMESTAMP | DEFAULT NOW() | 발생 시간 |

**인덱스:**
- `idx_conflict_ticker` ON ticker
- `idx_conflict_created_at` ON created_at DESC

### 6.2 기존 테이블 확장

#### orders 테이블에 컬럼 추가

```sql
ALTER TABLE orders ADD COLUMN strategy_id UUID REFERENCES strategies(id);
ALTER TABLE orders ADD COLUMN conflict_check_passed BOOLEAN DEFAULT false;
ALTER TABLE orders ADD COLUMN conflict_reasoning TEXT;

CREATE INDEX idx_orders_strategy_id ON orders(strategy_id);
```

#### positions 테이블에 컬럼 추가

```sql
ALTER TABLE positions ADD COLUMN primary_strategy_id UUID REFERENCES strategies(id);
ALTER TABLE positions ADD COLUMN is_locked BOOLEAN DEFAULT false;
ALTER TABLE positions ADD COLUMN locked_reason TEXT;

CREATE INDEX idx_positions_strategy_id ON positions(primary_strategy_id);
```

---

## 7. API 설계

### 7.1 전략 관리 API

#### GET /api/v1/strategies
전략 목록 조회

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "long_term",
      "display_name": "장기 투자",
      "priority": 100,
      "time_horizon": "long",
      "is_active": true
    }
  ]
}
```

#### POST /api/v1/strategies/{strategy_id}/activate
전략 활성화/비활성화

### 7.2 충돌 검사 API

#### POST /api/v1/orders/check-conflict
주문 실행 전 충돌 검사

**Request:**
```json
{
  "strategy_id": "uuid",
  "ticker": "NVDA",
  "action": "sell",
  "quantity": 10
}
```

**Response:**
```json
{
  "has_conflict": true,
  "conflict_details": {
    "owning_strategy": "long_term",
    "ownership_type": "primary",
    "locked_until": "2026-04-11T00:00:00Z",
    "reasoning": "장기 투자 전략이 해당 포지션을 3개월 보유 목표로 소유 중입니다."
  },
  "resolution": "blocked",
  "can_override": false
}
```

### 7.3 포지션 소유권 API

#### GET /api/v1/positions/ownership
포지션별 소유권 조회

**Response:**
```json
{
  "data": [
    {
      "ticker": "NVDA",
      "quantity": 100,
      "primary_strategy": "long_term",
      "is_locked": true,
      "locked_until": "2026-04-11T00:00:00Z"
    }
  ]
}
```

---

## 8. 충돌 해결 규칙

### 8.1 우선순위 규칙

| 전략 | Priority | Time Horizon | 설명 |
|------|----------|--------------|------|
| long_term | 100 | long (3개월+) | 최우선 |
| dividend | 90 | long (1년+) | 배당주 장기 보유 |
| trading | 50 | short (1일~1주) | 일반 단기 |
| aggressive | 30 | short (1일) | 공격적 단기 |

### 8.2 충돌 시나리오 및 해결

#### 시나리오 1: 장기 전략 보유 중 → 단기 전략 매도 시도

```
Current: Long-Term Strategy owns NVDA (100 shares, locked until 2026-04-11)
New Signal: Trading Strategy wants to sell NVDA (10 shares)

Resolution: BLOCKED
Reasoning: "장기 투자 전략이 우선순위(100)로 포지션을 소유 중입니다.
           단기 트레이딩 전략(50)은 매도할 수 없습니다."
```

#### 시나리오 2: 단기 전략 보유 중 → 장기 전략 매수 시도

```
Current: Trading Strategy owns TSLA (50 shares, no lock)
New Signal: Long-Term Strategy wants to buy TSLA (100 shares)

Resolution: ALLOWED (Transfer ownership)
Reasoning: "장기 투자 전략이 더 높은 우선순위(100)를 가지고 있습니다.
           기존 포지션의 소유권을 장기 전략으로 이전하고 추가 매수를 허용합니다."
```

#### 시나리오 3: 같은 전략 내 신호

```
Current: Long-Term Strategy owns AAPL (100 shares)
New Signal: Long-Term Strategy wants to sell AAPL (50 shares)

Resolution: ALLOWED (Partial exit)
Reasoning: "동일 전략 내 포지션 조정은 허용됩니다."
```

### 8.3 잠금 해제 조건

1. **시간 기반**: `locked_until` 시간 경과
2. **Stop Loss 트리거**: 극단적 손실 시 강제 해제
3. **수동 해제**: 사용자 명시적 해제 (UI)
4. **전략 비활성화**: 전략 자체가 비활성화되면 자동 해제

---

## 9. Event Bus 이벤트 추가

### 9.1 신규 이벤트 타입

```python
# backend/events/event_types.py에 추가

class EventType(Enum):
    # ... 기존 이벤트들 ...

    # Strategy Events
    STRATEGY_ACTIVATED = "strategy_activated"
    STRATEGY_DEACTIVATED = "strategy_deactivated"

    # Conflict Events
    CONFLICT_DETECTED = "conflict_detected"
    CONFLICT_RESOLVED = "conflict_resolved"
    ORDER_BLOCKED_BY_CONFLICT = "order_blocked_by_conflict"

    # Ownership Events
    OWNERSHIP_ACQUIRED = "ownership_acquired"
    OWNERSHIP_TRANSFERRED = "ownership_transferred"
    OWNERSHIP_RELEASED = "ownership_released"
```

### 9.2 이벤트 발행 시점

| 이벤트 | 발행 시점 | 데이터 |
|--------|----------|--------|
| CONFLICT_DETECTED | 충돌 감지 시 | ticker, strategies, reasoning |
| ORDER_BLOCKED_BY_CONFLICT | 주문 차단 시 | order_id, conflict_id, reasoning |
| OWNERSHIP_TRANSFERRED | 소유권 이전 시 | ticker, from_strategy, to_strategy |

---

## 10. 프론트엔드 UI 설계

### 10.1 새로운 페이지/섹션

#### 멀티 전략 대시보드 (`/strategies`)

**구성 요소:**
1. **전략 카드 그리드**
   - 각 전략별 독립 카드
   - 활성화 상태 토글
   - 실시간 P&L 표시
   - 보유 포지션 개수

2. **포지션 소유권 테이블**
   - 종목별 소유 전략 표시
   - 잠금 상태 및 해제 시간
   - 우선순위 표시

3. **충돌 경고 영역**
   - 최근 충돌 로그 (상단 고정)
   - 차단된 주문 내역
   - 충돌 reasoning 표시

#### 전략별 상세 페이지 (`/strategies/{id}`)

- 전략 설정
- 거래 내역
- 성과 차트
- 포지션 목록

### 10.2 기존 War Room 대시보드 확장

**추가 정보:**
- 현재 신호의 전략 태그 표시
- 충돌 검사 결과 표시
- 소유권 정보 표시

---

## 11. 구현 계획 (Phase별)

### Phase 0: DB 스키마 & 테스트 설계 (TDD RED)

**산출물:**
- [ ] DB 마이그레이션 스크립트
- [ ] Pydantic 스키마 정의
- [ ] API 계약 정의 (contracts/)
- [ ] 단위 테스트 작성 (모두 실패 상태 - RED)

**예상 기간**: 1~2일

### Phase 1: 전략 레지스트리 구현 (RED → GREEN)

**산출물:**
- [ ] strategies 테이블 CRUD
- [ ] 기본 전략 시드 데이터 (long_term, trading, etc.)
- [ ] Strategy 모델 및 서비스
- [ ] 테스트 통과 (GREEN)

**예상 기간**: 2~3일

### Phase 2: 포지션 소유권 추적 (RED → GREEN)

**산출물:**
- [ ] position_ownership 테이블 CRUD
- [ ] 포지션 생성 시 자동 소유권 할당
- [ ] 소유권 이전 로직
- [ ] 테스트 통과 (GREEN)

**예상 기간**: 2~3일

### Phase 3: 충돌 감지 엔진 (RED → GREEN)

**산출물:**
- [ ] ConflictDetector 클래스
- [ ] 충돌 규칙 엔진
- [ ] 우선순위 비교 로직
- [ ] conflict_logs 테이블 연동
- [ ] 테스트 통과 (GREEN)

**예상 기간**: 3~4일

### Phase 4: Order Manager 통합 (RED → GREEN)

**산출물:**
- [ ] OrderManager에 충돌 검사 추가
- [ ] 주문 실행 전 check_conflict() 호출
- [ ] 충돌 시 차단 로직
- [ ] Event Bus 이벤트 발행
- [ ] 테스트 통과 (GREEN)

**예상 기간**: 2~3일

### Phase 5: API & 프론트엔드 (RED → GREEN)

**산출물:**
- [ ] 전략 관리 API
- [ ] 충돌 검사 API
- [ ] 포지션 소유권 API
- [ ] React 컴포넌트 (전략 대시보드)
- [ ] E2E 테스트 통과 (GREEN)

**예상 기간**: 4~5일

---

## 12. 테스트 전략

### 12.1 단위 테스트

**ConflictDetector 테스트:**
```python
def test_detect_conflict_long_term_vs_trading():
    # Given: Long-Term owns NVDA
    long_term = Strategy(name="long_term", priority=100)
    ownership = PositionOwnership(
        ticker="NVDA",
        strategy=long_term,
        locked_until=datetime.now() + timedelta(days=90)
    )

    # When: Trading tries to sell NVDA
    trading = Strategy(name="trading", priority=50)
    signal = TradingSignal(strategy=trading, action="sell", ticker="NVDA")

    result = conflict_detector.check_conflict(signal)

    # Then: Conflict detected, blocked
    assert result.has_conflict == True
    assert result.resolution == "blocked"
    assert "우선순위" in result.reasoning
```

### 12.2 통합 테스트

**Order Manager + Conflict Detector 통합:**
```python
async def test_order_blocked_by_conflict():
    # Given: Long-Term owns position
    # When: Trading submits sell order
    # Then: Order transitions to REJECTED, event published
```

### 12.3 E2E 테스트

**Playwright 시나리오:**
```typescript
test('충돌 감지 및 차단 플로우', async ({ page }) => {
  // 1. 장기 전략으로 NVDA 매수
  // 2. 단기 전략으로 NVDA 매도 시도
  // 3. 충돌 경고 표시 확인
  // 4. 주문 차단 확인
});
```

---

## 13. 리스크 및 완화 전략

### 13.1 Top 5 리스크 보드

| # | 가정 | 리스크 | 완화 | 트리거 | 대응 |
|---|------|--------|------|--------|------|
| 1 | 충돌 감지 로직이 완벽 | 미감지 충돌 발생 | 포괄적 테스트, 로그 모니터링 | 충돌 후 손실 발생 | 수동 복구, 로직 개선 |
| 2 | DB 트랜잭션 정합성 | 동시성 문제 | PostgreSQL 트랜잭션, 락 사용 | 포지션 중복 | 롤백, 데이터 정합성 체크 |
| 3 | 우선순위 규칙이 명확 | 애매한 케이스 | 사용자 수동 override 옵션 | 사용자 불만 | 규칙 개선 |
| 4 | Event Bus 안정성 | 이벤트 손실 | 이벤트 히스토리 저장, 재처리 | 이벤트 미발행 | 수동 재발행 |
| 5 | 성능 저하 없음 | 충돌 검사 오버헤드 | 캐싱, 인덱스 최적화 | 응답 시간 증가 | 쿼리 최적화 |

---

## 14. 수익 모델 (장기)

### 14.1 SaaS 구독 모델

**계층:**
- **Free**: 단일 전략만 (현재 War Room)
- **Pro** ($29/월): 멀티 전략 (최대 3개)
- **Premium** ($99/월): 무제한 전략 + 고급 분석

### 14.2 전환 로드맵

1. **Phase 1**: 개인 사용 (현재)
2. **Phase 2**: 베타 테스터 모집 (친구/커뮤니티)
3. **Phase 3**: SaaS 플랫폼 전환 (클라우드 배포)
4. **Phase 4**: 마케팅 및 유료 전환

---

## 15. Decision Log

### D-01: MVP 핵심 기능 선택

| 항목 | 내용 |
|------|------|
| 결정 | FEAT-1: 전략 간 충돌 방지를 MVP로 선택 |
| 근거 | 이게 없으면 멀티 전략이 오히려 독이 됨 |
| 영향 | 자본 분배 최적화는 v2로 연기 |
| 보류안 | 시장 상황 평가는 FEAT-2로 이동 |

### D-02: 우선순위 규칙

| 항목 | 내용 |
|------|------|
| 결정 | 장기 전략 > 단기 전략 우선순위 |
| 근거 | 장기 투자는 시간이 핵심이므로 보호 필요 |
| 영향 | 단기 전략의 일부 신호는 차단될 수 있음 |
| 보류안 | 사용자 수동 override 기능은 v1.1 |

### D-03: 기술 스택 유지

| 항목 | 내용 |
|------|------|
| 결정 | FastAPI + React + PostgreSQL 유지 |
| 근거 | 기존 War Room MVP와 호환성, 학습 곡선 최소화 |
| 영향 | 새로운 기술 학습 불필요, 빠른 구현 가능 |
| 보류안 | Gemini → GLM 전환은 비용 절감 시 고려 |

### D-04: AI 설명 가능성

| 항목 | 내용 |
|------|------|
| 결정 | 모든 충돌 결정에 reasoning 필드 필수 |
| 근거 | AI 토론에서 도출된 중요 요구사항 |
| 영향 | 사용자 신뢰도 향상, 디버깅 용이 |
| 보류안 | 설명 품질 향상은 지속적 개선 |

---

## 16. 다음 단계

### 즉시 실행 (이번 주)

1. [ ] **tasks-generator 실행**: TASKS.md 생성
2. [ ] **DB 마이그레이션 스크립트 작성**: Phase 0
3. [ ] **단위 테스트 템플릿 작성**: TDD RED 상태
4. [ ] **API 계약 정의**: contracts/ 디렉토리

### 단기 목표 (1~2주)

1. [ ] Phase 1~3 완료: 전략 레지스트리 + 소유권 추적 + 충돌 감지
2. [ ] 단위 테스트 통과: GREEN 상태
3. [ ] Order Manager 통합: Phase 4

### 중기 목표 (3~4주)

1. [ ] API & 프론트엔드: Phase 5
2. [ ] E2E 테스트 통과
3. [ ] 실제 Shadow Trading 환경에서 검증

### 장기 목표 (2~3개월)

1. [ ] FEAT-2, FEAT-3 구현 (v2)
2. [ ] SaaS 플랫폼 전환 준비
3. [ ] 베타 테스터 모집 및 피드백 수집

---

## 17. 참고 문서

- 현재 시스템 상태: `docs/00_Spec_Kit/260104_Current_System_State.md`
- MVP 아키텍처: `docs/00_Spec_Kit/260104_MVP_Architecture.md`
- State Machine 구현: `docs/Implementation_Report_260110.md`
- War Room MVP: `backend/ai/mvp/war_room_mvp.py`

---

**Generated by**: Socrates Skill (Claude Code)
**Planning Session**: 2026-01-11
**Status**: ✅ Planning Complete - Ready for TASKS.md Generation
