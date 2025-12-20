# Constitutional Backtest 문제 정리

**작성일**: 2025-12-15 22:50 KST  
**목적**: AI 간 논의를 위한 문제 정리

---

## 🎯 문제 요약

**백테스트가 모든 거래를 거부합니다 (15/15건 거부)**

---

## 📊 현재 상황

### 백테스트 결과
```
기간: 2024-11-01 ~ 2024-11-30 (21일)
초기 자본: ₩10,000,000
최종 자본: ₩10,000,000
수익률: +0.00%

실행 거래: 0건
거부 거래: 15건
Shadow Trades: 15건
```

### 거부 이유
```
위반 사항: risk_on 체제: 주식 비중 미달 (0.0% < 70.0%)
위반 사항: neutral 체제: 주식 비중 미달 (0.0% < 40.0%)
```

---

## 🔍 근본 원인

### Catch-22 문제 (닭이 먼저냐 달걀이 먼저냐)

**Constitution 규칙**:
```python
# allocation_rules.py
RISK_ON_STOCK_MIN = 0.70  # risk_on에서는 주식 70% 이상
NEUTRAL_STOCK_MIN = 0.40  # neutral에서는 주식 40% 이상
```

**백테스트 초기 상태**:
```python
portfolio = {
    'cash': 10,000,000,  # 100%
    'positions': {},      # 0%
}
```

**문제**:
1. 백테스트 시작 → 100% 현금 (주식 0%)
2. AI가 "BUY SPY" 제안
3. Constitution 검증:
   - 현재 주식: 0%
   - 필요 주식: 70% (risk_on) or 40% (neutral)
   - 결과: ❌ 위반!
4. 거래 거부 → Shadow Trade 생성
5. 여전히 100% 현금...
6. 무한 반복

**핵심**: 첫 거래를 하려면 이미 주식이 70%여야 하는데, 주식을 사려면 거래를 해야 함!

---

## 💡 해결 방안

### Option 1: 백테스트 모드 플래그 (추천 ⭐)

**장점**:
- Constitution 철학 유지
- 실전에서는 엄격한 규칙 적용
- 백테스트에서는 성과 측정 가능
- 깔끔한 구현

**구현**:
```python
# Constitution.validate_proposal()에 추가
def validate_proposal(
    self, 
    proposal: dict, 
    context: dict,
    backtest_mode: bool = False  # 추가
):
    # ...
    
    # 배분 규칙 (백테스트에서는 스킵)
    if not backtest_mode:
        is_valid, violations = AllocationRules.validate_allocation(...)
```

**수정 필요 파일**:
1. `backend/constitution/constitution.py` - `backtest_mode` 파라미터 추가
2. `backend/backtest/constitutional_backtest_engine.py` - `backtest_mode=True` 전달

**예상 결과**:
```
✅ 거래 실행: 10-15건
✅ 수익률: -2% ~ +5%
✅ Shadow Trades: 0-5건
✅ 실제 전략 성과 측정 가능
```

---

### Option 2: 헌법 수정

**변경안**:
```python
# allocation_rules.py
RISK_ON_STOCK_MIN = 0.30  # 70% → 30%로 완화
NEUTRAL_STOCK_MIN = 0.10  # 40% → 10%로 완화
```

**장점**:
- 간단한 수정
- 점진적 투자 가능

**단점**:
- Constitution 철학 훼손
- 실전에서도 완화된 규칙 적용
- "자본 보존 우선" 원칙 약화

---

### Option 3: 현상 유지

**의미**:
- 백테스트 = 100% 자본 보존 (거래 안함)
- 실전 = 사람이 직접 초기 배분

**장점**:
- Constitution 철학 완벽 유지
- 극도로 보수적 (안전 최우선)

**단점**:
- 백테스트로 성과 측정 불가
- 전략 검증 어려움

---

## 🎯 권장 사항

### 추천: Option 1 (백테스트 모드)

**이유**:
1. **Constitution 철학 유지**
   - 실전: 엄격한 규칙 적용
   - 백테스트: 성과 측정 목적

2. **실용성**
   - 전략 성과 측정 가능
   - 백테스트 본연의 목적 달성

3. **구현 용이성**
   - 파라미터 하나 추가
   - 기존 코드 영향 최소

**철학적 정당성**:
> "백테스트는 시뮬레이션이다. 실전에서는 사람이 초기 배분을 하지만,  
> 백테스트에서는 시스템이 전체 과정을 자동화해야 한다."

---

## 📝 구현 계획 (Option 1)

### Step 1: Constitution 수정
```python
# backend/constitution/constitution.py

def validate_proposal(
    self,
    proposal: dict,
    context: dict,
    backtest_mode: bool = False  # 추가
) -> tuple:
    # ...
    
    # 2. Allocation Rules (백테스트에서는 스킵)
    if not backtest_mode:
        allocation_valid, allocation_violations = (
            AllocationRules.validate_allocation(...)
        )
        if not allocation_valid:
            is_valid = False
            violations.extend(allocation_violations)
            violated_articles.append("제1조: 자산 배분")
```

### Step 2: Backtest Engine 수정
```python
# backend/backtest/constitutional_backtest_engine.py

is_valid, violations, violated_articles = self.constitution.validate_proposal(
    full_proposal, 
    context,
    backtest_mode=True  # 추가
)
```

### Step 3: 테스트
```bash
python backend/backtest/constitutional_backtest_engine.py
```

**예상 출력**:
```
[2024-11-01] BUY SPY: 22주 @ ₩450
[2024-11-02] BUY SPY: 23주 @ ₩451
...
📊 Backtest Results
  실행: 12건
  거부: 3건
  수익률: +3.2%
```

---

## 🤔 논의 포인트

### 질문 1: Constitution의 역할
- Constitution은 "절대 불변"인가?
- 아니면 "맥락에 따라 적용"인가?

### 질문 2: 백테스트의 목적
- 100% 안전(거래 안함)을 보여주는 것?
- 전략의 성과를 측정하는 것?

### 질문 3: 실전 vs 시뮬레이션
- 실전: 사람이 초기 투자 → 시스템이 관리
- 백테스트: 사람 없음 → 시스템이 전부

---

## 💭 철학적 고민

### Constitutional AI의 정체성
```
"우리는 안전을 판다"
→ 백테스트에서 0% 거래 = 100% 안전은 맞음
→ 하지만 성과 측정이 불가능

vs.

"우리는 안전한 투자를 돕는다"
→ 백테스트 = 시스템 검증 도구
→ 배분 규칙은 포트폴리오 관리용, 진입 규칙 아님
```

### 현실적 타협점
```
실전: Commander가 초기 배분 승인
      → Constitution이 전체 관리

백테스트: 자동 초기 배분
          → Constitution이 거래만 관리
```

---

## 🎯 최종 요약

**현재 문제**:
- 백테스트가 Catch-22로 모든 거래 거부

**권장 해결책**:
- Option 1: `backtest_mode=True` 플래그 추가
- 배분 규칙만 백테스트에서 스킵
- 나머지 규칙은 모두 적용

**구현 난이도**: ⭐☆☆☆☆ (매우 쉬움)  
**예상 소요**: 10분  
**영향 범위**: Constitution + Backtest Engine (2개 파일)

---

**작성일**: 2025-12-15 22:50 KST  
**상태**: AI 논의 대기  
**다음**: 사용자 결정 후 구현
