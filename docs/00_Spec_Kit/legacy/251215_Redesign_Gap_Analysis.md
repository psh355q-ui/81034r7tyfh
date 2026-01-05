# 시스템 재설계 분석 및 실행 계획

**작성일**: 2025-12-15  
**목적**: 새로운 아이디어 vs 현재 시스템 비교 및 마이그레이션 전략

---

## 📊 1. Gap Analysis (현재 vs 제안)

### 철학 및 정체성

| 항목 | 현재 시스템 | 제안 시스템 | Gap |
|---|---|---|---|
| 정체성 | AI 자동매매 봇 | AI 투자 위원회 | ⚠️ 근본적 변경 |
| 사용자 역할 | 시스템 관리자 | Commander (승인권자) | ⚠️ UX 전면 변경 |
| AI 역할 | 분석 및 실행 | 토론 및 제안 | ⚠️ 로직 재작성 |
| 핵심 가치 | 수익 극대화 | 안전 보장 | ⚠️ KPI 변경 |

---

### 아키텍처

| 컴포넌트 | 현재 | 제안 | 난이도 |
|---|---|---|---|
| 구조 | 계층형 (AI → DB → API) | 3권 분립 | 🔴 High |
| AI | AIDebateEngine (5 agents) | Multi-Agent Debate | 🟡 Medium |
| 실행 | 직접 실행 | Proposal → 승인 → 실행 | 🔴 High |
| 거버넌스 | 없음 | Governance Ledger | 🔴 High |
| 헌법 | rules/ 폴더 | constitution/ (불변) | 🟡 Medium |

---

### 기능 비교

| 기능 | 현재 | 제안 | 구현 필요 |
|---|---|---|---|
| AI 토론 | ✅ AIDebateEngine | ✅ War Room (시각화) | 🟡 UI 개선 |
| 승인 매매 | ❌ 없음 | ✅ Commander Mode | 🔴 신규 |
| Shadow Trade | ❌ 없음 | ✅ 가상 추적 | 🔴 신규 |
| Trust Mileage | ❌ 없음 | ✅ 단계적 위임 | 🔴 신규 |
| Circuit Breaker | ⚠️ 부분 (MDD) | ✅ 자동 회수 | 🟡 확장 |
| Governance Log | ❌ 없음 | ✅ 위변조 불가 기록 | 🔴 신규 |
| PM 권한 제한 | ❌ 없음 | ✅ ID-Based Selector | 🔴 신규 |

---

## 🎯 2. 채택 vs 보류 전략

### 즉시 채택 가능 (기존 코드 활용)

#### ✅ 1. War Room UI 개선
**현재**: AIDebateEngine이 텍스트로 토론  
**변경**: 카카오톡 스타일 UI로 시각화

**파일**: `frontend/src/components/ai/AIDebateViewer.tsx`  
**작업**: 
- Trader/Risk/PM을 캐릭터로 표시
- 대화형 레이아웃
- 찬성 vs 반대 좌우 배치

**난이도**: 🟡 Medium (2-3시간)

---

#### ✅ 2. Shadow Trade 추적
**신규 기능**: 거부된 제안을 가상으로 추적

**파일**:
- `backend/backtest/shadow_trade_tracker.py` (신규)
- `backend/data/models/shadow_trade.py` (신규)

**DB 스키마**:
```sql
CREATE TABLE shadow_trades (
    id UUID PRIMARY KEY,
    proposal_id UUID,
    ticker VARCHAR(10),
    entry_price DECIMAL,
    exit_price DECIMAL,
    virtual_pnl DECIMAL,
    created_at TIMESTAMP
);
```

**난이도**: 🟢 Easy (1-2시간)

---

#### ✅ 3. KPI 재정의 (Shield Report)
**현재**: 수익률 중심  
**변경**: 방어 성과 중심

**파일**: `backend/reporting/shield_metrics.py` (신규)

**리포트 구조**:
```python
class ShieldMetrics:
    capital_preserved: float    # 자본 보존율
    avoided_loss: float         # 방어한 손실
    rejected_proposals: int     # 거부한 제안 수
    stress_index_diff: float    # 시장 vs 내 계좌 변동성
```

**난이도**: 🟡 Medium (2-3시간)

---

### 중기 채택 (구조 변경 필요)

#### 🟡 4. Proposal 기반 실행
**변경**: 모든 매매가 Proposal 객체를 거침

**현재 흐름**:
```
AIDebateEngine → InvestmentSignal → 즉시 실행
```

**제안 흐름**:
```
AIDebateEngine → Proposal (pending) → 
Commander 승인 → Execution
```

**파일 수정**:
- `backend/ai/core/investment_signal.py` → Proposal로 변경
- `backend/execution/order_executor.py` → 승인 체크 추가
- `backend/api/telegram_bot.py` → 승인/거부 버튼

**난이도**: 🔴 High (1-2일)

---

#### 🟡 5. PM Agent 권한 제한
**현재**: PM이 자유로운 텍스트 생성  
**변경**: ID-Based Selector Pattern

**구현**:
```python
# agents에 ID 부여
class TraderAgent:
    def analyze(self) -> Dict:
        return {
            "id": f"TRADER_{uuid4()}",
            "argument": "수급 증가",
            "confidence": 0.8
        }

# PM은 선택만
class PMAgent:
    def decide(self, arguments: List[Dict]) -> Dict:
        return {
            "verdict": "BUY",
            "selected_ids": ["TRADER_abc..."],
            # 새로운 텍스트 생성 금지!
        }
```

**난이도**: 🔴 High (1-2일)

---

### 장기 과제 (근본 재설계)

#### 🔴 6. 3권 분립 아키텍처
**변경**: 디렉토리 및 의존성 재구성

**마이그레이션 계획**:
```
Phase 1: backend/constitution/ 분리
Phase 2: backend/intelligence/ 통합
Phase 3: backend/execution/ 격리
Phase 4: 의존성 방향 검증
```

**예상 시간**: 3-5일

---

#### 🔴 7. 헌법 불변성 강제
**기능**: SHA256 해시 검증

**구현**:
```python
# backend/constitution/check_integrity.py
EXPECTED_HASHES = {
    "risk_limits.py": "abc123...",
    "allocation_rules.py": "def456..."
}

def verify_on_startup():
    for file, expected in EXPECTED_HASHES.items():
        current = hash_file(file)
        if current != expected:
            raise SystemFreeze(f"{file} 변조 감지!")
```

**난이도**: 🟡 Medium (1일)

---

#### 🔴 8. Governance Ledger
**기능**: 위변조 불가 의사결정 기록

**구현**: Hash Chain
```python
class GovernanceLog:
    id: UUID
    proposal_id: UUID
    action: str
    prev_hash: str  # 이전 로그 해시
    current_hash: str  # 이 로그 + prev_hash 해시
```

**난이도**: 🔴 High (2-3일)

---

## 🛣️ 3. 단계별 로드맵

### Phase 1: Quick Wins (1주일)
**목표**: 기존 시스템 유지하면서 새로운 가치 추가

1. ✅ Shadow Trade 추적 (1-2시간)
2. ✅ War Room UI 개선 (2-3시간)
3. ✅ Shield Report 추가 (2-3시간)
4. ✅ Circuit Breaker 강화 (1-2시간)

**결과**: 
- "방어 가치" 시각화
- 사용자 경험 개선
- 기존 코드 안전

---

### Phase 2: 승인 매매 (2주일)
**목표**: Commander Mode 도입

1. Proposal 객체 도입 (2-3일)
2. 텔레그램 승인/거부 버튼 (1-2일)
3. PM Agent 권한 제한 (1-2일)
4. 통합 테스트 (1일)

**결과**:
- 사용자가 최종 결정권
- "지휘관" 경험 제공

---

### Phase 3: 3권 분립 (1개월)
**목표**: 아키텍처 근본 재설계

1. constitution/ 분리 (1주)
2. intelligence/ 통합 (1주)
3. execution/ 격리 (1주)
4. Governance Ledger (1주)

**결과**:
- 깨끗한 아키텍처
- 확장 가능한 구조

---

### Phase 4: 운영 철학 (지속)
**목표**: 문화 및 원칙 정립

1. 온보딩 시나리오 (3일)
2. 헌법 문서화 (ongoing)
3. 운영자 리트머스 질문 (ongoing)

---

## ⚖️ 4. 의사결정 가이드

### 즉시 시작해야 할 것
1. ✅ Shadow Trade Tracker
2. ✅ Shield Report
3. ✅ War Room UI

**이유**: 
- 기존 코드 안전
- 즉각적인 가치
- 위험 낮음

---

### 신중히 검토할 것
1. ⚠️ 3권 분립
2. ⚠️ Governance Ledger
3. ⚠️ 헌법 불변성

**이유**:
- 대규모 리팩토링
- 높은 위험
- 시간 소모

**검토 질문**:
- Q1: 현재 시스템이 작동하는가?
   - A: ✅ Yes (Phase E 완료, 백테스트 완료)
   
- Q2: 근본 변경이 지금 필요한가?
   - A: ⚠️ 토론 필요

- Q3: 점진적 개선 vs 전면 재설계?
   - A: **점진적 개선 권장**

---

## 🎯 5. 추천 전략

### 추천: Hybrid Approach (하이브리드)

**Phase 1** (즉시 시작):
- Shadow Trade
- Shield Report
- War Room UI 개선

**Phase 2** (2주 후):
- Proposal 기반 실행
- Commander Mode

**Phase 3** (평가 후 결정):
- 3권 분립 (사용자 반응 보고 결정)
- Governance Ledger (스케일 필요 시)

**장점**:
- ✅ 즉각적인 가치 창출
- ✅ 리스크 분산
- ✅ 유연한 의사결정
- ✅ 기존 투자 보호

---

## 📝 6. 다음 단계 질문

**사용자 결정 필요**:

1. **철학 변경 동의 여부**
   - "자동매매 봇" → "AI 투자 위원회"로 전환?
   - KPI를 "수익" → "방어 성과"로 변경?

2. **타임라인**
   - 즉시 전면 재설계? (1-2개월)
   - 점진적 개선? (수주 단위)

3. **우선순위**
   - 빠른 가치 vs 깨끗한 아키텍처?

---

**작성일**: 2025-12-15 19:02 KST  
**다음 액션**: 사용자 의사결정 대기
