# Claude 신기능 구현 계획 (간단 버전)
**Date:** 2026-01-01
**Priority:** P0 (최우선)

---

## 🎯 Phase 1: 즉시 적용 (이번 주)

### 1. Prompt Caching (1hr) ⭐⭐⭐
**목표:** API 비용 80% 절감 ($150/월 → $30/월)

**구현:**
```python
# backend/ai/config/cached_prompts.py
CACHED_PROMPTS = {
    "pm_agent": {
        "content": "You are Portfolio Manager...",
        "cache_control": {"type": "ephemeral", "duration": 3600}
    },
    "macro_agent": {
        "content": "You are Macro Economist...",
        "cache_control": {"type": "ephemeral", "duration": 3600}
    },
    "investment_rules": {
        "content": "투자 원칙:\n1. 리스크 관리...",
        "cache_control": {"type": "ephemeral", "duration": 3600}
    }
}
```

**적용 대상:**
- War Room MVP (PM Agent, Macro Agent, Risk Agent)
- Deep Reasoning 시스템 프롬프트
- 투자 원칙 / 리스크 관리 규칙

**작업 시간:** 1일

---

### 2. Structured Outputs (JSON Schema) ⭐⭐⭐
**목표:** JSON 파싱 에러 제로화

**구현:**
```python
# backend/ai/schemas/war_room_schemas.py
from pydantic import BaseModel, Field
from typing import Literal

class WarRoomDecision(BaseModel):
    action: Literal["BUY", "SELL", "HOLD", "TRIM", "PASS"]
    ticker: str = Field(pattern=r"^[A-Z]{1,5}$")
    position_size: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    reasoning: str = Field(min_length=10)

class DeepReasoningResult(BaseModel):
    theme: str
    primary_beneficiary: Optional[BeneficiarySchema]
    hidden_beneficiary: Optional[BeneficiarySchema]
    loser: Optional[BeneficiarySchema]
    bull_case: str
    bear_case: str

# Usage
response = await agent.make_decision(
    context=context,
    response_schema=WarRoomDecision.model_json_schema()
)
```

**적용 대상:**
- War Room MVP 모든 에이전트 응답
- Deep Reasoning 분석 결과
- Backtest 설정 생성

**작업 시간:** 2일

---

### 3. Citations (인용) ⭐⭐
**목표:** 분석 신뢰성 향상

**구현:**
```python
# backend/ai/reasoning/deep_reasoning_with_citations.py
async def analyze_with_citations(news_text: str):
    response = await client.generate(
        prompt=f"Analyze with citations:\n{news_text}",
        citations=True
    )

    return {
        "analysis": response.content,
        "citations": [
            {
                "text": cite.text,
                "start": cite.start,
                "end": cite.end
            }
            for cite in response.citations
        ]
    }
```

**Frontend:**
```typescript
// 인용 표시
<div className="citations">
  {result.citations.map((cite, i) => (
    <span key={i} className="citation">
      <sup>[{i+1}]</sup> "{cite.text}"
    </span>
  ))}
</div>
```

**적용 대상:**
- Deep Reasoning 뉴스 분석
- War Room 의사결정 근거

**작업 시간:** 2일

---

## 🚀 Phase 2: 단기 적용 (다음 주)

### 4. Extended Thinking ⭐⭐
**목표:** 복잡한 의사결정 품질 향상

**구현:**
```python
# backend/ai/war_room/pm_agent_enhanced.py
async def make_complex_decision(context):
    response = await client.generate(
        prompt=context,
        extended_thinking=True,
        max_thinking_tokens=10000
    )

    return {
        "thinking": response.thinking,  # 사고 과정
        "decision": response.content     # 최종 결정
    }
```

**적용 시나리오:**
- 복잡한 포트폴리오 리밸런싱
- 다중 에이전트 의견 충돌 해결
- 극단적 시장 상황 분석

**작업 시간:** 3일

---

### 5. Web Search ⭐⭐
**목표:** 최신 뉴스 자동 수집

**구현:**
```python
# backend/ai/tools/web_search.py
async def search_latest_news(ticker: str):
    results = await claude.web_search(
        query=f"{ticker} stock news today",
        max_results=10
    )
    return results
```

**적용 시나리오:**
- War Room 실행 전 최신 뉴스 수집
- 티커별 뉴스 자동 검색
- 경쟁사 동향 파악

**작업 시간:** 3일

---

### 6. Memory (기억) ⭐
**목표:** 과거 학습 능력 추가

**구현:**
```python
# backend/ai/memory/trading_memory.py
class TradingMemory:
    async def save_outcome(trade_id, outcome):
        await memory.save({
            "type": "trade_outcome",
            "success": outcome.profit > 0,
            "lesson": "NVDA 급등 시 익절 타이밍 중요"
        })

    async def get_similar_cases(context):
        return await memory.search(query=context, limit=5)
```

**적용 시나리오:**
- 과거 백테스트 결과 기억
- 실패한 트레이드 패턴 학습
- 사용자 선호도 저장

**작업 시간:** 5일

---

## 📊 Phase 3: 장기 검토 (1개월)

### 7. Batch Processing
**목표:** 추가 50% 비용 절감

```python
# 20개 티커를 배치로 분석 (비용 50% 절감)
batch_result = await claude.batch_process([
    {"ticker": t, "prompt": f"Analyze {t}"}
    for t in tickers
])
```

**작업 시간:** 2일

---

### 8. Code Execution
**목표:** 분석 자동화

```python
# Claude가 직접 코드 작성/실행
result = await claude.execute_code(
    prompt="Calculate Sharpe Ratio from this CSV",
    data=backtest_results_csv
)
```

**작업 시간:** 4일

---

## 💰 예상 비용 절감

| Phase | 월 비용 | 절감률 |
|-------|---------|--------|
| 현재 | $250 | - |
| Phase 1 | $130 | -48% |
| Phase 2 | $100 | -60% |
| Phase 3 | $65 | -74% |

**연간 절감:** $2,220/year

---

## 📋 구현 체크리스트

### Week 1 (이번 주)
- [ ] Prompt Caching 적용
  - [ ] cached_prompts.py 생성
  - [ ] PM Agent 통합
  - [ ] Macro Agent 통합
  - [ ] 비용 절감 측정

- [ ] Structured Outputs 적용
  - [ ] war_room_schemas.py 생성
  - [ ] WarRoomDecision 스키마
  - [ ] DeepReasoningResult 스키마
  - [ ] API 통합

- [ ] Citations 적용
  - [ ] deep_reasoning_with_citations.py
  - [ ] Frontend 인용 UI
  - [ ] API 통합

### Week 2 (다음 주)
- [ ] Extended Thinking
  - [ ] PM Agent 복잡한 의사결정
  - [ ] Frontend 사고 과정 표시

- [ ] Web Search
  - [ ] 티커 뉴스 검색 API
  - [ ] War Room 통합

- [ ] Memory
  - [ ] TradingMemory 클래스
  - [ ] 트레이드 결과 저장
  - [ ] 유사 케이스 검색

### Month 1
- [ ] Batch Processing
- [ ] Code Execution

---

## 🔧 테스트 계획

### Prompt Caching 테스트
```bash
# Before
curl -X POST /api/war-room/run
# Response time: 5s, Cost: $0.50

# After (with cache hit)
curl -X POST /api/war-room/run
# Response time: 1s, Cost: $0.10
```

### Structured Outputs 테스트
```python
# 100번 호출 → JSON 파싱 에러 0개 확인
for i in range(100):
    result = await war_room.run()
    assert isinstance(result, WarRoomDecision)
```

### Citations 테스트
```python
result = await deep_reasoning.analyze_with_citations(news)
assert len(result.citations) > 0
assert all(cite.text in news for cite in result.citations)
```

---

## 📊 성공 지표

### Phase 1 (1주 후)
- ✅ API 비용 70% 이상 절감
- ✅ JSON 파싱 에러 0개
- ✅ 인용 표시 100% 적용

### Phase 2 (2주 후)
- ✅ Extended Thinking 적용 완료
- ✅ 최신 뉴스 자동 수집
- ✅ 과거 트레이드 학습 시작

### Phase 3 (1개월 후)
- ✅ 총 비용 74% 절감 달성
- ✅ 자동 분석 파이프라인 구축

---

## 🚨 리스크 & 대응

### Risk 1: API 비용 증가
**대응:** Caching 먼저 적용 → 비용 확인 → 다른 기능 추가

### Risk 2: Beta 기능 불안정
**대응:** Feature Flag로 점진적 롤아웃

### Risk 3: 학습 곡선
**대응:** 한 번에 하나씩 적용, 충분한 테스트

---

## 📁 파일 구조

```
backend/ai/
├── config/
│   └── cached_prompts.py          # Prompt Caching
├── schemas/
│   └── war_room_schemas.py        # Structured Outputs
├── reasoning/
│   └── deep_reasoning_with_citations.py  # Citations
├── tools/
│   └── web_search.py              # Web Search
└── memory/
    └── trading_memory.py          # Memory

docs/
└── 260101_Claude_Features_Implementation_Plan.md
```

---

## ✅ Next Actions

**이번 주 (최우선):**
1. Prompt Caching 1hr 적용 (PM Agent, Macro Agent)
2. 비용 절감 확인
3. Structured Outputs 스키마 정의

**다음 주:**
4. Citations 통합
5. Extended Thinking 테스트
6. Web Search 통합

**1개월 내:**
7. Memory 시스템
8. Batch Processing
9. Code Execution 검토

---

**Status:** Ready to Implement
**Owner:** AI Trading System Team
**Estimated Total Time:** 3 weeks
**Expected Cost Savings:** $2,220/year (74% reduction)
