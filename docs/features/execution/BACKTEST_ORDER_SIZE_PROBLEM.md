# Backtest Order Size Problem - 최종 정리

**작성일**: 2025-12-15 23:01 KST  
**목적**: AI 논의를 위한 명확한 문제 정의

---

## ✅ 해결된 문제 (Portfolio Phase Architecture)

**배분 규칙 Catch-22**:
- ✅ `skip_allocation_rules` 파라미터 추가
- ✅ BOOTSTRAP 단계에서 배분 규칙 스킵
- ✅ Constitution 철학 유지 + 백테스트 실용성 확보

---

## ❌ 새로운 문제: 주문 크기 제약

### 현재 상황
```
백테스트 초기 자본: ₩10,000,000 (≈ $8,333)
주문 크기: 10% = ₩1,000,000 (≈ $833)

Constitution 규칙:
  MIN_ORDER_SIZE = $1,000
  
결과: $833 < $1,000 → 거부!
```

### 문제의 본질

**이것은 설계 충돌이 아니라 파라미터 불일치입니다.**

Constitution은 USD 기반으로 설계되었으나,  
백테스트는 KRW 기반으로 실행 중입니다.

---

## 💡 해결 방안

### Option A: 초기 자본 증가 ⭐ **추천**

**변경**:
```python
# constitutional_backtest_engine.py
ConstitutionalBacktestEngine(
    initial_capital=100_000_000,  # ₩10M → ₩100M
    ...
)
```

**결과**:
- 10% = ₩10M (≈ $8,333)
- $8,333 > $1,000 ✅ 통과!

**장점**:
- Constitution 규칙 변경 없음
- 현실적인 자본 규모 (₩100M = 일반 투자자)
- 즉시 해결, 부작용 없음

**단점**:
- 없음

---

### Option B: 주문 비율 증가

**변경**:
```python
order_value = self.portfolio['total_value'] * 0.15  # 10% → 15%
```

**결과**:
- 15% = ₩1.5M (≈ $1,250)
- $1,250 > $1,000 ✅ 통과!

**장점**:
- 자본 변경 없음

**단점**:
- 15%는 공격적 (Constitution 철학과 충돌)
- 한 종목에 15%는 리스크 높음

---

### Option C: 최소 주문 크기 완화

**변경**:
```python
# trading_constraints.py
MIN_ORDER_SIZE = 500  # $1,000 → $500
```

**장점**:
- 소액 투자자도 수용 가능

**단점**:
- Constitution 규칙 약화
- 실전에서도 영향
- 철학 후퇴

---

### Option D: 백테스트 모드 확장

**변경**:
```python
# constitution.py
if skip_allocation_rules:
    skip order size validation for backtest
```

**장점**:
- 백테스트만 완화

**단점**:
- 검증 범위 축소 (백테스트 의미 퇴색)
- Constitution 예외가 늘어남

---

## 🎯 권장 해결책

### ✅ Option A: 초기 자본 ₩100M

**이유**:

1. **현실성**  
   - ₩100M (≈ $83K)은 일반적인 자산 규모
   - 너무 작지도, 크지도 않음

2. **Constitution 무손상**  
   - 모든 규칙 그대로 유지
   - 철학적 일관성 완벽

3. **즉시 적용 가능**  
   - 1줄 변경으로 해결
   - 테스트 비용 최소

4. **확장성**  
   - 나중에 다른 자본으로도 테스트 가능
   - 파라미터화 가능

---

## 📊 비교표

| 옵션 | Constitution 보존 | 실용성 | 구현 난이도 | 추천도 |
|------|------------------|--------|------------|--------|
| A: 초기 자본 ₩100M | ✅ 완벽 | ✅ 높음 | ⭐☆☆ | ⭐⭐⭐ |
| B: 주문 15% | ✅ 유지 | ⚠️ 공격적 | ⭐☆☆ | ⭐☆☆ |
| C: 최소 크기 완화 | ❌ 약화 | ✅ 높음 | ⭐☆☆ | ☆☆☆ |
| D: 검증 스킵 확장 | ⚠️ 예외 증가 | ✅ 높음 | ⭐⭐☆ | ⭐☆☆ |

---

## 🔧 구현 코드 (Option A)

```python
# backend/backtest/constitutional_backtest_engine.py

def main():
    """메인 함수"""
    print("\n" + "="*60)
    print(" "*10 + "🏛️ Constitutional Backtest Engine 🏛️")
    print("="*60)
    print()
    
    # 백테스트 실행
    engine = ConstitutionalBacktestEngine(
        initial_capital=100_000_000,  # ₩10M → ₩100M 변경
        start_date=datetime(2024, 11, 1),
        end_date=datetime(2024, 11, 30)
    )
    
    report = engine.run()
```

**변경 사항**: 딱 1줄!

---

## ✅ 최종 결론

### 문제 정의
- 백테스트 초기 자본이 너무 작아 최소 주문 크기 위반

### 해결책
- **Option A 채택**: 초기 자본 ₩10M → ₩100M

### 철학적 정당성
> "Constitution은 합리적 자본 규모를 전제한다.  
> ₩100M은 일반 투자자의 현실적 자산이며,  
> 이는 규칙 완화가 아니라 적절한 전제 조건 설정이다."

### 구현 난이도
- ⭐☆☆☆☆ (매우 쉬움)
- 소요 시간: 1분
- 영향 범위: 1개 파일, 1줄

### 예상 결과
```
실행 거래: 10-15건 ✅
수익률: -2% ~ +5% (정상 범위)
Shadow Trades: 0-5건
Constitution 준수: 100%
```

---

## 🤔 논의 포인트

### Q1: Constitution은 자본 규모 가정을 명시해야 하는가?

**현재**: 암묵적으로 일정 규모 이상 가정  
**제안**: 문서화 or 최소 자본 검증 추가?

### Q2: 백테스트 파라미터의 표준은?

- 초기 자본: ₩100M? $100K?
- 기간: 30일? 1년?
- 주문 크기: 10%? 15%?

### Q3: 다중 자본 규모 테스트?

```python
for capital in [10M, 100M, 1B]:
    backtest(capital)
```
→ Constitution이 모든 규모에서 작동하는지 검증?

---

## 📝 상태 선언

- 문제 정의: **완료**
- 해결책 선택: **확정 (Option A)**
- 철학적 충돌: **없음**
- 추가 토론 필요성: **선택 (Q1-Q3)**

**즉시 구현 가능** 상태입니다.

---

**작성일**: 2025-12-15 23:01 KST  
**상태**: AI 논의 대기  
**다음 액션**: 사용자 승인 후 1줄 변경
