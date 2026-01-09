# Agent 불일치 계산 로직 심층 분석

**작성일**: 2026-01-08  
**발견**: 사용자 지적 - "PM도 포함되어야 75%가 맞지 않나?"

---

## 🔍 실제 구현 확인

### 코드 분석 (pm_agent_mvp.py Line 326-341)

```python
# Rule 3: Agent Disagreement > 75%
actions = [
    trader_opinion.get('action', 'pass'),        # Agent 1
    risk_opinion.get('recommendation', 'reject'), # Agent 2
    analyst_opinion.get('action', 'pass')         # Agent 3
]

# Count unique actions (excluding 'pass')
non_pass_actions = [a for a in actions if a != 'pass']

if len(non_pass_actions) > 0:
    disagreement = 1.0 - (non_pass_actions.count(non_pass_actions[0]) / len(non_pass_actions))
    
    if disagreement > self.HARD_RULES['max_agent_disagreement']:
        violations.append(...)
```

### 핵심 발견

**PM Agent는 불일치 계산에 포함되지 않음!** ✅

- 계산 대상: **3명만** (Trader, Risk, Analyst)
- PM은 Hard Rules 검증 후 최종 결정만 수행
- **사용자 추측이 틀렸음**

---

## 📊 불일치도 계산 로직 상세

### 공식

```python
disagreement = 1.0 - (most_common_count / total_non_pass_count)
```

### 예시 시나리오

#### 시나리오 1: 전원 동의
```python
actions = ['buy', 'buy', 'buy']
non_pass_actions = ['buy', 'buy', 'buy']

disagreement = 1.0 - (3 / 3) = 0.0  # 0% 불일치 ✅
```

#### 시나리오 2: 2명 동의, 1명 반대
```python
actions = ['buy', 'buy', 'sell'] 
non_pass_actions = ['buy', 'buy', 'sell']

disagreement = 1.0 - (2 / 3) = 0.33  # 33% 불일치 ✅
```

#### 시나리오 3: 의견 3갈래
```python
actions = ['buy', 'sell', 'hold']
non_pass_actions = ['buy', 'sell', 'hold']

disagreement = 1.0 - (1 / 3) = 0.67  # 67% 불일치 ⚠️
```

#### 시나리오 4: 전원 다른 의견
불가능! (3명이 3가지 의견 = 시나리오 3과 동일)

---

## 🧮 수학적 분석

### 3명 시스템에서 가능한 불일치도

| 의견 분포 | 불일치도 | 75% 기준 | 67% 기준 | 60% 기준 |
|-----------|----------|----------|----------|----------|
| **3-0-0** (전원 동의) | 0% | ✅ 통과 | ✅ 통과 | ✅ 통과 |
| **2-1-0** (2명 동의) | 33% | ✅ 통과 | ✅ 통과 | ✅ 통과 |
| **1-1-1** (3갈래) | 67% | ✅ 통과 | ❌ 거부 | ❌ 거부 |

### 문제점 재정의

**75% 기준의 실제 의미**:
- 3명 전원 동의 (0%) ✅
- 2명 동의 (33%) ✅
- 3갈래 의견 (67%) ✅ ← **이것도 통과!**

**즉, 75%는 사실상 "모든 경우" 통과** 🤯

---

## 💡 사용자 지적 재검토

### 사용자 추측

> "PM도 퍼센트에 들어가야 75%가 가능할 것 같다"

**결론**: ❌ 틀림

- PM은 계산에 포함되지 않음
- 하지만 **본질적 지적은 맞음!**

### 본질적 문제

**사용자가 직감한 문제**:
- 75%는 너무 관대함
- 3명 시스템에서 **67% 불일치까지 허용**
- = 3갈래 의견도 OK

**실제로 필요한 것**:
- **67% 기준**: 2명 동의 필요 (33% 불일치까지만 허용)
- **60% 기준**: 더 관대 (67% 불일치도 허용)

---

## 🎯 올바른 해석

### 기준별 의미

| 기준 | 허용 불일치 | 실제 의미 |
|------|-------------|----------|
| **75%** | 67%까지 | 3갈래 의견도 OK (너무 관대) |
| **67%** | 33%까지 | 2명 동의 필요 (적절) ✅ |
| **60%** | 33%까지 | 2명 동의 필요 (67%도 67% 미만이므로 통과!) |
| **50%** | 0%까지 | 전원 동의만 허용 (너무 엄격) |

### 수정된 권장안

**기존 분석 오류 수정**:

#### LONG_TERM
```python
'max_agent_disagreement': 0.50  # 전원 동의만 허용
```
- 보수적 투자 = 확실한 경우만
- 3명 전원이 동의해야 진행

#### TRADING (현재 기본)
```python
'max_agent_disagreement': 0.67  # 2명 동의 필요
```
- 균형잡힌 접근
- 1명 반대 허용

#### AGGRESSIVE
```python
'max_agent_disagreement': 0.75  # 3갈래도 OK
```
- 공격적 투자
- 의견 분열되어도 진행

---

## 📋 최종 권장사항 (수정)

### Persona별 기준

```python
# backend/ai/mvp/pm_agent_mvp.py 또는 PersonaRouter

DISAGREEMENT_BY_PERSONA = {
    'DIVIDEND': 0.40,      # 거의 전원 동의 필요
    'LONG_TERM': 0.50,     # 전원 동의 필요
    'TRADING': 0.67,       # 2명 동의 필요 (권장)
    'AGGRESSIVE': 0.80     # 3갈래도 허용
}
```

### 구현 방식

#### Option 1: PersonaRouter에서 동적 조정

```python
# backend/ai/router/persona_router.py

def get_hard_rules_config(self, mode: PersonaMode) -> Dict:
    """페르소나별 Hard Rules 설정 반환"""
    
    disagreement_thresholds = {
        PersonaMode.DIVIDEND: 0.40,
        PersonaMode.LONG_TERM: 0.50,
        PersonaMode.TRADING: 0.67,
        PersonaMode.AGGRESSIVE: 0.80
    }
    
    return {
        'max_agent_disagreement': disagreement_thresholds[mode]
    }
```

#### Option 2: PM Agent에서 Persona 인식

```python
# backend/ai/mvp/pm_agent_mvp.py

def __init__(self, persona_mode: str = 'TRADING'):
    self.persona_mode = persona_mode
    
    # Persona별 기준 설정
    disagreement_config = {
        'DIVIDEND': 0.40,
        'LONG_TERM': 0.50,
        'TRADING': 0.67,
        'AGGRESSIVE': 0.80
    }
    
    self.HARD_RULES = {
        'max_agent_disagreement': disagreement_config.get(persona_mode, 0.67),
        # ...
    }
```

---

## ✅ 결론

### 사용자 지적 평가

1. **PM 포함 추측**: ❌ 틀림 (PM은 계산 안 됨)
2. **75%가 높다**: ✅ **완전히 맞음!**
3. **LONG_TERM 75%**: ✅ **절대 안 됨!**

### 올바른 설정

| Persona | 권장 기준 | 의미 |
|---------|----------|------|
| DIVIDEND | 40% | 거의 전원 동의 |
| LONG_TERM | **50%** | 전원 동의 필수 |
| TRADING | **67%** | 2명 동의 |
| AGGRESSIVE | 80% | 3갈래도 OK |

---

**다음 단계**: 페르소나별 불일치 기준 구현
