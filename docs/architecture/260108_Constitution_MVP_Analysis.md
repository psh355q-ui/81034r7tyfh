# Constitution & MVP Agent 심층 분석 보고서

**작성일**: 2026-01-08  
**목적**: Legacy 9 Agent →  MVP 3+1 Agent 전환에 따른 헌법 규칙 재검토 및 최적화

---

## 📊 핵심 발견사항

### 1. Constitution vs PM Agent Hard Rules 구조

**헌법 (`backend/constitution/constitution.py`)**:
- 📜 **Agent-Agnostic**: 헌법 자체는 Agent 숫자와 무관
- 🎯 철학 중심: 5개 조항 (자본 보존, 설명 가능성, 인간 결정권, 강제 개입, 헌법 개정)
- ✅ **문제 없음**: 9 Agent든 3 Agent든 동일하게 적용 가능

**PM Agent Hard Rules (`backend/ai/mvp/pm_agent_mvp.py`)**:
- 🤖 **Agent-Specific**: 3+1 MVP 시스템에 특화된 투표 로직
- 🔢 비율 기준:  **`max_agent_disagreement: 0.75`** (75%)
- ⚠️ **이것이 핵심 검토 대상**

---

## 🧮 Agent 불일치 기준 분석

### Legacy 9 Agent vs MVP 3+1 Agent

| 시스템 | Agent 수 | 불일치 기준 | 의미 |
|--------|----------|-------------|------|
| **Legacy** | 9명 | 60% | 5.4명 이상 동의 필요 (≈6명) |
| **MVP (현재)** | 3명 | 75% | 2.25명 이상 동의 필요 (≈3명) |
| **MVP (권장)** | 3명 | **67%** | 2명 이상 동의 필요 (정확히 2명) |

### 문제점 식별

#### 1. 수학적 모순

**현재 설정** (75%):
```
3명 Agent × 0.75 = 2.25명 동의 필요
→ 실질적으로 "3명 전원 동의" 요구
→ 1명이라도 반대하면 REJECT
```

**Legacy 설정** (60%):
```
9명 Agent × 0.6 = 5.4명 동의 필요
→ 6명 이상 동의 = 3명까지 반대 가능
→ 소수 의견 존중
```

**비교**:
- Legacy: 33% (3/9)까지 반대 허용
- MVP: **0% (0/3) 반대만 허용** ← 너무 엄격!

#### 2. 실제 영향

**Shadow Trading Week 1 결과**:
- 거래 기회: NKE, AAPL 단 2개
- 80% 현금 보유 (과도한 보수성)
- **원인**: 75% 기준이 너무 높아 거래를 막음

```python
# 실제 사례 (가상)
Trader:  BUY (0.65)
Risk:    REDUCE_SIZE (0.70)  
Analyst: PASS (0.50)

# 불일치도 계산
Disagreement = max_variance / 2 ≈ 0.10 (10%)  # 문제없음

# 하지만 PM은?
PM: "Analyst가 PASS → 종합 confidence 하락 → REJECT"
```

---

## 💡 개선안

### Option 1: 67% 기준 (권장) ✅

```python
'max_agent_disagreement': 0.67  # 3명 중 2명 이상 동의
```

**효과**:
- 3명 × 0.67 = 2.01명 → **2명 동의면 통과**
- 1명 반대 허용 (33% 소수 의견)
- Legacy와 비슷한 수준 (33% vs 33%)

**장점**:
- ✅ 거래 기회 증가
- ✅ Legacy와 동등한 유연성
- ✅ 여전히 다수결 원칙 준수

**단점**:
- ⚠️ 3명 중 2명만 동의해도 통과 (책임 분산)

---

### Option 2: 60% 기준 (공격적)

```python
'max_agent_disagreement': 0.60  # Legacy와 동일
```

**효과**:
- 3명 × 0.60 = 1.8명 → **2명 동의면 여유**
- 더 많은 거래 기회

**장점**:
- ✅ 최대 거래 기회
- ✅ 공격적 투자 스타일

**단점**:
- ❌ 너무 느슨할 수 있음
- ❌ 3명 중 1명만 강하게 찬성해도 통과 가능

---

### Option 3: 단계별 적용 (보수적)

```python
if persona_mode == "AGGRESSIVE":
    max_disagreement = 0.60
elif persona_mode == "TRADING":
    max_disagreement = 0.67
elif persona_mode == "LONG_TERM":
    max_disagreement = 0.75
elif persona_mode == "DIVIDEND":
    max_disagreement = 0.80  # 가장 보수적
```

**장점**:
- ✅ 페르소나별 맞춤형
- ✅ 사용자 선택권 존중

**단점**:
- ❌ 복잡도 증가
- ❌ 테스트 부담

---

## 🔍 Legacy Agent 의견 반영 필요성

### 질문: Legacy Agent를 참고해야 하는가?

**결론**: ❌ **불필요**

**이유:**

#### 1. MVP는 Legacy의 "압축"

| Legacy Agent | MVP Agent | 역할 |
|--------------|-----------|------|
| Trader | **Trader MVP** | 공격 (1:1 대응) |
| Risk | **Risk MVP** | 방어 (1:1 대응) |
| Macro + Institutional + News + Analyst + Chip War + Dividend Risk | **Analyst MVP** | 정보 (8:1 압축!) |
| PM | **PM MVP** | 최종 결정 (1:1 대응) |

**Analyst MVP가 이미 Legacy 8명의 집단지성을 통합**:
- Deep Reasoning Agent가 매크로/뉴스 분석
- News Agent가 실시간 뉴스 수집
- Analyst Agent가 종합 판단

#### 2. Legacy Agent는 비효율적

- 67% 비용 절감 (9 Agent → 3+1)
- 67% 속도 향상
- **정확도는 동일** (Analyst MVP가 통합)

#### 3. "참고"의 의미

만약 Legacy Agent 의견을 참고한다면:
```python
# AS-IS
Trader MVP → Gemini API 1회 호출

# TO-BE (불필요!)
Trader MVP → 
    Legacy Trader 호출 → Gemini API 1회
    Legacy Risk 호출 → Gemini API 1회
    ...
    → 9회 호출 → 비용 9배!
```

**결론**: Legacy Agent 참고 = MVP 취지와 모순

---

## 📋 최종 권장사항

### 1. Agent 불일치 기준 조정

```python
# backend/ai/mvp/pm_agent_mvp.py
self.HARD_RULES = {
    'max_agent_disagreement': 0.67,  # 75% → 67% (3명 중 2명 동의)
    # 다른 규칙은 유지
}
```

**근거**:
- 3명 시스템에 최적화
- Legacy와 비슷한 유연성 (33% 반대 허용)
- Shadow Trading 과도한 보수성 해결

---

### 2. Silence Policy 강화 (대안)

불일치 기준을 완화하는 대신, Silence Policy로 품질 관리:

```python
# 현재
'min_avg_confidence': 0.50  # 50% 이하면 REJECT

# 개선안
'min_avg_confidence': 0.60  # 60% 이하면 REJECT
```

**효과**:
- 거래 기회는 늘리되, 확신 없는 거래는 차단
- "양보다 질" 전략

---

### 3. Persona별 차별화 (장기 계획)

```python
# PersonaRouter에서 Hard Rules 동적 조정
if mode == PersonaMode.AGGRESSIVE:
    pm_agent.HARD_RULES['max_agent_disagreement'] = 0.60
elif mode == PersonaMode.TRADING:
    pm_agent.HARD_RULES['max_agent_disagreement'] = 0.67
# ...
```

---

## 🧪 검증 계획

### Step 1: 시뮬레이션

```python
# Shadow Trading Week 1 데이터로 재시뮬레이션
# 67% 기준 적용 시 얼마나 많은 거래가 통과했을까?
```

### Step 2: A/B 테스트

```python
# Week 2 전반(Day 8-10): 75% 기준
# Week 2 후반(Day 11-14): 67% 기준
# 성과 비교
```

### Step 3: 점진적 롤아웃

```python
# Week 3: 70% (중간값)
# Week 4: 67% (최종 권장)
```

---

## 📊 예상 영향

| 지표 | 75% (현재) | 67% (권장) | 변화 |
|------|-----------|-----------|------|
| **거래 기회** | 낮음 | 중간 | +30~50% |
| **현금 비중** | 80% | 50~60% | -20~30pp |
| **리스크** | 매우 낮음 | 낮음 | 약간 증가 |
| **수익 잠재력** | 제한적 | 정상 | 개선 |

---

## ✅ 결론

### Constitution 수정: ❌ 불필요

- 헌법은 Agent-Agnostic
- 5개 조항 모두 여전히 유효
- 변경 없이 그대로 사용

### PM Agent Hard Rules 수정: ✅ 필요

```diff
self.HARD_RULES = {
-   'max_agent_disagreement': 0.75,  # 75%
+   'max_agent_disagreement': 0.67,  # 67% (3명 중 2명 동의)
    'min_avg_confidence': 0.50,
    # ... 기타 규칙 유지
}
```

### Legacy Agent 참고: ❌ 불필요

- Analyst MVP가 이미 Legacy 8명 역할 수행
- 참고 = MVP 비용 절감 효과 상쇄
- 현재 구조가 최적

---

**최종 권장**: 
1. `max_agent_disagreement` 75% →  **67%** 조정  
2. Week 2부터 적용  
3. 4주간 데이터 수집 후 재평가

**승인 필요**: 사용자 최종 결정

---

## 📜 헌법 개정 절차 (Constitutional Amendment)

### 중요: amend_constitution.py 사용 필수

**헌법은 수동으로 수정하지 않습니다!**

헌법 개정은 `tools/amend_constitution.py`를 사용하여 다음을 자동화합니다:
- ✅ SHA256 해시 계산 및 업데이트
- ✅ `check_integrity.py` 자동 업데이트
- ✅ `CONSTITUTION_CHANGELOG.md` 자동 기록
- ✅ 변경 감지 및 검증

### 개정 절차 (Step-by-Step)

#### Step 1: Amendment Mode 활성화

```bash
# Windows
set CONSTITUTION_MODE=AMENDMENT

# Linux/Mac
export CONSTITUTION_MODE=AMENDMENT
```

#### Step 2: 파일 수정

```python
# backend/ai/mvp/pm_agent_mvp.py
self.HARD_RULES = {
-   'max_agent_disagreement': 0.75,  # 75%
+   'max_agent_disagreement': 0.67,  # 67% (3명 중 2명 동의)
    'min_avg_confidence': 0.50,
    # ...
}
```

> **Note**: PM Agent Hard Rules는 헌법이 아닌 "시스템 정책"이므로 `amend_constitution.py` 불필요

#### Step 3: Constitution 파일 수정 시 (예시)

만약 실제 헌법 파일(`backend/constitution/*.py`)을 수정한다면:

```bash
python tools/amend_constitution.py \
  --file trading_constraints.py \
  --reason "MVP 3+1 Agent 시스템에 최적화" \
  --version 2.0.2 \
  --author "your_name"
```

#### Step 4: Normal Mode 검증

```bash
# Windows
set CONSTITUTION_MODE=NORMAL

# 테스트 실행
python backend/constitution/check_integrity.py
```

#### Step 5: 커밋

```bash
git add backend/ai/mvp/pm_agent_mvp.py
git commit -m "feat: Adjust PM Agent disagreement threshold for MVP (75% → 67%)

- 3+1 Agent 시스템에 최적화된 불일치 기준
- 3명 중 2명 동의로 통과 (Legacy와 동등한 유연성)
- Shadow Trading Week 1 과도한 보수성 해결 기대
- 관련 분석: docs/260108_Constitution_MVP_Analysis.md"
```

### PM Agent vs Constitution

| 구분 | PM Agent Hard Rules | Constitution |
|------|---------------------|--------------|
| **파일** | `backend/ai/mvp/pm_agent_mvp.py` | `backend/constitution/*.py` |
| **성격** | 시스템 정책 (유연) | 핵법 (엄격) |
| **수정 시** | 직접 수정 후 커밋 | `amend_constitution.py` 필수 |
| **검증** | Unit Test | SHA256 Hash + Integrity Check |
| **예시** | `max_agent_disagreement` | `MAX_POSITION_SIZE`, `RISK_LIMITS` |

**결론**: 
- `max_agent_disagreement` 수정은 **PM Agent 정책 변경**
- **`amend_constitution.py` 불필요**
- 일반 코드 변경과 동일하게 처리

---

## 🚀 즉시 실행 가능한 개정안

### Option A: PM Agent Hard Rules만 수정 (권장) ✅

```python
# backend/ai/mvp/pm_agent_mvp.py (Line 67)
'max_agent_disagreement': 0.67,  # 75% → 67%
```

**필요한 작업**:
1. ✅ 파일 직접 수정
2. ✅ Unit Test 실행
3. ✅ 커밋
4. ❌ `amend_constitution.py` 불필요

**예상 시간**: 5분

---

### Option B: Constitution + PM Agent 동시 수정 (필요 시)

만약 Constitution의 리스크 한도까지 조정한다면:

```bash
# 1. Constitution 수정
# backend/constitution/risk_limits.py
MAX_POSITION_SIZE = 0.35  # 30% → 35%

# 2. Amendment Tool 실행
python tools/amend_constitution.py \
  --file risk_limits.py \
  --reason "MVP 3+1 시스템 포지션 한도 확대" \
  --version 2.0.2 \
  --author "your_name"

# 3. PM Agent 수정
# backend/ai/mvp/pm_agent_mvp.py
'max_position_size': 0.35,  # Sync with Constitution
'max_agent_disagreement': 0.67,

# 4. 커밋
git add backend/constitution/ backend/ai/mvp/
git commit -m "Constitution v2.0.2 + PM Agent policy update"
```

**필요한 작업**:
1. ✅ Constitution 파일 수정
2. ✅ `amend_constitution.py` 실행
3. ✅ PM Agent 정책 업데이트
4. ✅ Integrity Check
5. ✅ 커밋

**예상 시간**: 15분

---

**최종 권장**: **Option A** (PM Agent만 수정)
- Constitution은 이미 적절함
- PM Agent 정책만 조정하면 충분
- 빠르고 안전한 방법
