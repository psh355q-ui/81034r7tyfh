# War Room MVP Enhancement - Implementation Plan

> **작성일:** 2026-01-09  
> **Source:** Claude + ChatGPT Ideas  
> **Goal:** Agent 분석 품질 향상 + PM 판단 로직 개선

---

## 📊 현재 문제 진단

### Claude 분석
| Agent | 현재 문제 | 누락된 핵심 데이터 |
|-------|----------|-------------------|
| Risk MVP | Position Sizing 없음 | VaR, 베타, 손절가 |
| Trader MVP | 진입/목표/손절 없음 | R/R Ratio, 지지/저항 |
| Analyst MVP | 구체성 부족 | P/E, 촉매제, 기관동향 |
| PM MVP | 5% 리스크 한도 고정 | Persona별 차등 없음 |

### ChatGPT 분석
| 구조적 문제 | 원인 | 해결 방향 |
|------------|------|----------|
| 의도 정의 실패 | 시간 프레임 미명시 | Agent별 타임프레임 강제 |
| 정보 신뢰도 없음 | 증거 레벨 미분류 | A/B/C 등급제 도입 |
| 기계적 거부 | 불일치 = 위험 고정 | 방향성 vs 강도 분리 |
| 이진 판단 | 승인/거부만 존재 | 조건부 승인 추가 |

---

## 🎯 구현 우선순위

| Phase | 내용 | 소요 시간 | 효과 |
|-------|------|----------|------|
| **1. Quick Wins** | Agent 프롬프트 필수 출력 항목 추가 | 1-2시간 | 🔴 높음 |
| **2. 구조 개선** | Persona별 Hard Rules, 방향성 불일치 로직, 조건부 승인 | 반나절 | 🔴 높음 |
| **3. 데이터 강화** | 멀티 타임프레임, 이벤트 근접도, 옵션 데이터 | 1일 | 🟡 중간 |
| **4. 고급 기능** | 종목 특화 분석기 (TSLA, NVDA) | 2-3일 | 🟢 장기 |

---

## Phase 1: Agent 프롬프트 강화 (1-2시간)

### 1.1 Risk MVP 필수 출력
**File:** `backend/ai/mvp/risk_agent_mvp.py`

```python
# 필수 출력 항목
{
    "position_sizing": {"recommended_pct": 3.5, "reason": "높은 베타 고려"},
    "var_95": -8.2,
    "beta": 2.0,
    "stop_loss": 400.00,
    "max_loss_scenario": {"event": "정책 변화", "loss_pct": -15},
    "risk_decomposition": {
        "structural": "추세 붕괴 위험",
        "event": "트럼프 취임",
        "sentiment": "과매도"
    }
}
```

### 1.2 Trader MVP 필수 출력
**File:** `backend/ai/mvp/trader_agent_mvp.py`

```python
# 필수 출력 항목
{
    "entry_price": 395.50,
    "target_price": 450.00,
    "stop_loss": 380.00,
    "risk_reward_ratio": 3.5,
    "support_levels": [390, 380, 350],
    "resistance_levels": [420, 445, 480],
    "volume_analysis": {"vs_average": 1.3, "interpretation": "매도 압력"},
    "timeframe": {"type": "스윙", "duration": "2-4주"}
}
```

### 1.3 Analyst MVP 필수 출력
**File:** `backend/ai/mvp/analyst_agent_mvp.py`

```python
# 필수 출력 항목
{
    "valuation": {"pe_ratio": 180, "ps_ratio": 12.3, "interpretation": "고평가"},
    "catalysts": {
        "positive": ["FSD v13", "에너지 고성장"],
        "negative": ["EV 보조금 폐지", "BYD 경쟁"],
        "dates": ["Q4 실적 1월말", "트럼프 취임 1/20"]
    },
    "evidence_grades": {
        "news_reliability": "C",
        "institutional_evidence": "B",
        "macro_impact": "A"
    }
}
```

---

## Phase 2: 구조 개선 (반나절)

### 2.1 Persona별 Hard Rules
**File:** `backend/ai/mvp/pm_agent_mvp.py`

```python
PERSONA_HARD_RULES = {
    "trading": {
        "max_portfolio_risk_pct": 15.0,
        "max_agent_disagreement": 0.60,
        "max_position_pct": 10.0
    },
    "long_term": {
        "max_portfolio_risk_pct": 20.0,  # 18.1% 통과!
        "max_agent_disagreement": 0.70,
        "max_position_pct": 15.0
    },
    "dividend": {
        "max_portfolio_risk_pct": 10.0,
        "max_agent_disagreement": 0.40,
        "max_position_pct": 8.0
    },
    "aggressive": {
        "max_portfolio_risk_pct": 25.0,
        "max_agent_disagreement": 0.80,
        "max_position_pct": 20.0
    }
}
```

### 2.2 방향성 기반 불일치 계산 (핵심!)

```python
def calculate_directional_disagreement(votes: List[Dict]) -> float:
    """중립은 불일치 계산에서 제외"""
    directions = {
        "attack": ["buy", "매수"],
        "defense": ["sell", "reduce_size", "축소"],
        "neutral": ["hold", "보류"]  # 제외
    }
    
    attack_weight = sum(v["weight"] for v in votes if v["action"] in directions["attack"])
    defense_weight = sum(v["weight"] for v in votes if v["action"] in directions["defense"])
    
    total = attack_weight + defense_weight
    if total == 0:
        return 0.0
    
    minority = min(attack_weight, defense_weight)
    return minority / total  # 67% → 50%로 개선!
```

### 2.3 조건부 승인 기능

```python
class DecisionType(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    CONDITIONAL = "conditional"  # 새로 추가!

# PM MVP에서 조건부 승인 반환
{
    "decision": "conditional",
    "conditions": ["200DMA 유지 시 진입", "3% 포지션 분할"],
    "human_question": "위 조건 하에서 진입을 승인하시겠습니까?"
}
```

---

## Phase 3: 데이터 강화 (1일)

### 3.1 멀티 타임프레임
| Agent | 필수 타임프레임 |
|-------|----------------|
| Trader | 1D, 4H |
| Risk | 1W, 1D |
| Analyst | 1W, 1M |

### 3.2 이벤트 근접도
- 실적 발표까지 D-몇?
- FOMC, CPI, 옵션 만기?
- 머스크 발언, 규제 일정?

### 3.3 옵션 데이터
- Put/Call Ratio
- Max Pain 가격
- IV 스파이크 감지

---

## Phase 4: 고급 기능 (2-3일)

### 4.1 종목 특화 분석기
```
backend/ai/mvp/stock_specific/
├── __init__.py
├── tsla_analyzer.py  # Tesla 특화
├── nvda_analyzer.py  # NVIDIA 특화 (칩워 연동)
└── generic_analyzer.py
```

**TSLA 특화:**
- CEO 리스크 (머스크 활동)
- 정치적 환경 (DOGE, EV 보조금)
- 경쟁 (BYD)
- 촉매제 (FSD, 로보택시)

---

## 📋 내일 작업 체크리스트

### Phase 1: Quick Wins ⭐ 먼저 시작
- [ ] `risk_agent_mvp.py` 프롬프트에 필수 출력 항목 추가
- [ ] `trader_agent_mvp.py` 프롬프트에 진입/목표/손절가 필수화
- [ ] `analyst_agent_mvp.py` 프롬프트에 밸류에이션/촉매제/증거등급 추가
- [ ] 칩워 언급 조건 추가 (반도체 기업만)

### Phase 2: 구조 개선
- [ ] PERSONA_HARD_RULES 딕셔너리 구현
- [ ] calculate_directional_disagreement() 함수 구현
- [ ] PM MVP에 조건부 승인 (CONDITIONAL) 로직 추가

### Phase 3+4: 데이터/고급
- [ ] 멀티 타임프레임 데이터 fetching
- [ ] EventProximityLayer 클래스
- [ ] 종목 특화 분석기 (TSLA, NVDA)

---

## 🎯 예상 결과

**개선 전:**
```
PM MVP: 거부 (리스크 18.1% > 5.0%, 불일치 67% > 50%)
```

**개선 후:**
```
PM MVP (long_term): 조건부 승인
├── Persona 기준: 리스크 18.1% < 20% ✅
├── 방향성 불일치: 50% < 70% ✅  
├── 조건: "200DMA 유지 시 3% 포지션으로 분할 진입"
└── 인간 질문: "위 조건 하에서 승인하시겠습니까?"
```
