# Claude Features Analysis for AI Trading System
**Date:** 2026-01-01
**Purpose:** Claude의 새로운 기능 검토 및 AI Trading System 적용 가능성 분석

## 📋 Overview
Claude API의 최신 기능들을 검토하고, AI Trading System에 적용 가능한 기능들을 우선순위별로 분석합니다.

---

## 🎯 High Priority - 즉시 적용 가능

### 1. ✅ **Agent Skills** (이미 구현 중)
**Status:** 이미 DB Schema Manager Skill 구현 완료

**현재 사용 중:**
- DB Schema Manager Skill
- 점진적 공개를 통한 컨텍스트 관리

**추가 적용 가능:**
- [ ] **Excel/CSV Analysis Skill**: 백테스트 결과 분석
- [ ] **PDF Report Generation Skill**: 일간/주간 트레이딩 리포트 자동 생성
- [ ] **Data Validation Skill**: 주가 데이터 품질 검증

**Implementation Plan:**
```python
# backend/ai/skills/excel_analysis/SKILL.md
"""
Excel/CSV 백테스트 결과 분석 Skill
- 백테스트 결과 CSV 파일 파싱
- 통계 분석 (Sharpe Ratio, Max Drawdown, Win Rate)
- 차트 생성 (matplotlib)
"""
```

### 2. ⭐ **Prompt Caching (1hr)** - 매우 중요!
**Current:** 5분 캐싱만 사용 중
**Benefit:** 1시간 캐싱으로 비용 절감 + 응답 속도 향상

**적용 대상:**
- **War Room System Prompts**: PM Agent, Macro Agent 등의 시스템 프롬프트
- **Knowledge Base**: 투자 원칙, 리스크 관리 규칙
- **Historical Context**: 과거 뉴스/분석 데이터

**예상 비용 절감:**
- War Room 1회 실행: 기존 $0.50 → 캐싱 후 $0.10 (80% 절감)
- 하루 10회 실행 기준: $5 → $1 절감

**Implementation:**
```python
# backend/ai/prompts/cached_prompts.py
SYSTEM_PROMPTS = {
    "pm_agent": {
        "content": "You are a Portfolio Manager...",
        "cache_control": {"type": "ephemeral", "duration": 3600}  # 1 hour
    },
    "macro_agent": {
        "content": "You are a Macro Economist...",
        "cache_control": {"type": "ephemeral", "duration": 3600}
    }
}
```

### 3. ⭐ **Citations** - 신뢰성 향상
**Benefit:** Deep Reasoning 분석 결과의 신뢰성 검증

**적용 시나리오:**
- Deep Reasoning 분석 시 뉴스 원문 인용
- War Room 결정 시 근거 문장 표시
- PM Agent 판단 근거 추적

**Example Output:**
```json
{
  "analysis": "NVIDIA will benefit from AI chip demand",
  "citations": [
    {
      "source": "news_article_123",
      "text": "Google announced TPU v6...",
      "start": 45,
      "end": 89
    }
  ]
}
```

**Implementation:**
```python
# backend/ai/reasoning/deep_reasoning.py
async def analyze_with_citations(self, news_text: str):
    response = await self.ai_client.generate(
        prompt=news_text,
        citations=True  # Enable citations
    )
    return {
        "result": response.content,
        "citations": response.citations
    }
```

### 4. ⭐ **Structured Outputs (JSON)** - 안정성 향상
**Current:** 수동 JSON 파싱 (에러 발생 가능)
**Benefit:** 스키마 보장, 파싱 에러 제거

**적용 대상:**
- War Room 결정 (포지션, 액션)
- Deep Reasoning 결과 (티커, 신뢰도)
- Backtest 설정 생성

**Schema Example:**
```python
from pydantic import BaseModel

class WarRoomDecision(BaseModel):
    action: Literal["BUY", "SELL", "HOLD", "TRIM"]
    ticker: str
    position_size: float
    confidence: float
    reasoning: str

# Claude API call
response = await client.generate(
    prompt="Analyze this news...",
    response_schema=WarRoomDecision.model_json_schema()
)
```

---

## 🚀 Medium Priority - 단기 적용 검토

### 5. **Extended Thinking** - 복잡한 분석 개선
**Benefit:** War Room MVP의 의사결정 품질 향상

**적용 시나리오:**
- 복잡한 포트폴리오 리밸런싱 결정
- 다중 에이전트 간 의견 충돌 해결
- 극단적 시장 상황 분석

**Implementation:**
```python
# backend/ai/war_room/pm_agent_mvp.py
async def make_complex_decision(self, context):
    response = await self.ai_client.generate(
        prompt=context,
        extended_thinking=True,  # Enable extended thinking
        max_thinking_tokens=10000
    )
    return {
        "thinking_process": response.thinking,  # 내부 추론 과정
        "final_decision": response.content       # 최종 결정
    }
```

**Use Case:**
```
[사고 과정]
1. 현재 포트폴리오: NVDA 30%, AAPL 20%...
2. 뉴스 분석: AI 칩 수요 급증...
3. 리스크 고려: 집중도 초과 위험...
4. 결론: NVDA TRIM 5% → 현금 보유

[최종 결정]
Action: TRIM NVDA 5%
```

### 6. **Memory** - 학습 능력 추가
**Benefit:** 과거 실패/성공 학습

**적용 시나리오:**
- 과거 백테스트 결과 기억
- 실패한 트레이드 패턴 학습
- 사용자 선호도 저장

**Implementation:**
```python
# backend/ai/memory/trading_memory.py
class TradingMemory:
    async def save_trade_outcome(self, trade_id, outcome):
        """성공/실패 트레이드 저장"""
        await self.memory_api.save({
            "type": "trade_outcome",
            "trade_id": trade_id,
            "success": outcome.profit > 0,
            "lesson": "NVDA 급등 시 익절 타이밍 중요"
        })

    async def get_relevant_memories(self, context):
        """현재 상황과 유사한 과거 경험 조회"""
        return await self.memory_api.search(
            query=context,
            limit=5
        )
```

### 7. **Web Search** - 실시간 정보 통합
**Current:** 수동으로 뉴스 크롤링
**Benefit:** 최신 시장 뉴스 자동 검색

**적용 시나리오:**
- War Room 실행 전 최신 뉴스 수집
- 티커 언급 뉴스 자동 검색
- 경쟁사 동향 파악

**Implementation:**
```python
# backend/ai/tools/web_search.py
async def search_latest_news(ticker: str):
    results = await claude.web_search(
        query=f"{ticker} stock news today",
        max_results=10
    )
    return [
        {"title": r.title, "snippet": r.snippet, "url": r.url}
        for r in results
    ]
```

### 8. **Batch Processing** - 비용 절감
**Benefit:** 비용 50% 절감

**적용 시나리오:**
- 일일 백테스트 대량 실행
- 전체 포트폴리오 티커 분석 (한 번에 20개)
- 과거 뉴스 재분석 (데이터 보강)

**Example:**
```python
# backend/ai/batch/batch_analysis.py
async def batch_analyze_tickers(tickers: List[str]):
    # 20개 티커를 배치로 분석
    batch_requests = [
        {"ticker": t, "prompt": f"Analyze {t}"}
        for t in tickers
    ]

    # 50% 비용 절감
    batch_result = await claude.batch_process(batch_requests)

    # 24시간 내 결과 수신
    return await batch_result.wait_for_completion()
```

---

## 📊 Low Priority - 장기 검토

### 9. **Computer Use** - 브라우저 자동화
**Use Case:** 한국투자증권 웹사이트 자동 주문

**Risk:** 보안 문제, 안정성 낮음
**Decision:** 현재는 KIS API 사용, 추후 검토

### 10. **Code Execution** - 데이터 분석
**Current:** 자체 Python 코드 실행
**Benefit:** Claude가 직접 분석 코드 작성/실행

**Use Case:**
```python
# Claude가 직접 코드 작성/실행
result = await claude.execute_code(
    prompt="Calculate Sharpe Ratio from this CSV",
    data=backtest_results_csv
)
# result.output: "Sharpe Ratio: 1.85"
```

### 11. **Files API** - 파일 관리
**Use Case:** 반복 업로드 방지

**Current:** 매번 뉴스 텍스트 전송
**Improvement:** 파일 업로드 후 ID만 전송

---

## 🎯 Recommended Implementation Plan

### Phase 1: 즉시 적용 (1주 내)
1. ✅ **Prompt Caching (1hr)** - War Room 프롬프트
   - Priority: P0 (최우선)
   - Effort: 1일
   - Impact: 비용 80% 절감

2. ✅ **Structured Outputs** - JSON 스키마 강제
   - Priority: P0
   - Effort: 2일
   - Impact: 파싱 에러 제로화

3. ✅ **Citations** - Deep Reasoning 신뢰성
   - Priority: P1
   - Effort: 2일
   - Impact: 사용자 신뢰도 향상

### Phase 2: 단기 적용 (2주 내)
4. **Extended Thinking** - PM Agent 개선
   - Priority: P1
   - Effort: 3일
   - Impact: 의사결정 품질 20% 향상

5. **Web Search** - 실시간 뉴스 통합
   - Priority: P1
   - Effort: 3일
   - Impact: 최신 정보 자동 수집

6. **Memory** - 학습 능력 추가
   - Priority: P2
   - Effort: 5일
   - Impact: 장기 성과 개선

### Phase 3: 장기 검토 (1개월 내)
7. **Batch Processing** - 비용 최적화
   - Priority: P2
   - Effort: 2일
   - Impact: 추가 50% 비용 절감

8. **Code Execution** - 자동 분석
   - Priority: P3
   - Effort: 4일
   - Impact: 분석 자동화

---

## 💰 Cost-Benefit Analysis

### Current Costs (월간 추정)
- War Room 실행: $150/month (하루 10회 × 30일 × $0.50)
- Deep Reasoning: $100/month
- **Total: $250/month**

### After Implementation (Phase 1)
- War Room (with 1hr cache): $30/month (80% 절감)
- Deep Reasoning (with citations): $100/month
- **Total: $130/month (-48% 절감)**

### After Implementation (Phase 2)
- Batch Processing 추가: $65/month (50% 추가 절감)
- **Total: $65/month (-74% 절감)**

### Annual Savings
- 현재: $3,000/year
- 최적화 후: $780/year
- **절감액: $2,220/year (74%)**

---

## 🔧 Technical Implementation Details

### 1. Prompt Caching Implementation

**File:** `backend/ai/config/cached_prompts.py`
```python
from typing import Dict, Any

CACHED_PROMPTS = {
    "pm_agent_system": {
        "type": "system",
        "content": """You are a Portfolio Manager Agent...""",
        "cache_control": {"type": "ephemeral", "duration": 3600}
    },
    "macro_agent_system": {
        "type": "system",
        "content": """You are a Macro Economist Agent...""",
        "cache_control": {"type": "ephemeral", "duration": 3600}
    },
    "investment_principles": {
        "type": "context",
        "content": """투자 원칙:\n1. 리스크 관리...""",
        "cache_control": {"type": "ephemeral", "duration": 3600}
    }
}

def get_cached_prompt(prompt_key: str) -> Dict[str, Any]:
    """캐시된 프롬프트 반환"""
    return CACHED_PROMPTS.get(prompt_key)
```

**Usage in War Room:**
```python
# backend/ai/war_room/pm_agent_mvp.py
from backend.ai.config.cached_prompts import get_cached_prompt

async def make_decision(self, context):
    messages = [
        get_cached_prompt("pm_agent_system"),  # 1시간 캐싱
        get_cached_prompt("investment_principles"),  # 1시간 캐싱
        {"role": "user", "content": context}  # 현재 요청만 매번 전송
    ]

    response = await self.ai_client.generate(messages=messages)
    return response
```

### 2. Structured Outputs Implementation

**File:** `backend/ai/schemas/war_room_schemas.py`
```python
from pydantic import BaseModel, Field
from typing import Literal

class WarRoomDecision(BaseModel):
    """War Room 의사결정 스키마"""
    action: Literal["BUY", "SELL", "HOLD", "TRIM", "PASS"]
    ticker: str = Field(..., pattern=r"^[A-Z]{1,5}$")
    position_size: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str = Field(..., min_length=10)
    risk_score: float = Field(..., ge=0, le=10)

class DeepReasoningResult(BaseModel):
    """Deep Reasoning 결과 스키마"""
    theme: str
    primary_beneficiary: Optional[BeneficiarySchema]
    hidden_beneficiary: Optional[BeneficiarySchema]
    loser: Optional[BeneficiarySchema]
    bull_case: str
    bear_case: str
```

**Usage:**
```python
# backend/api/war_room_mvp_router.py
response = await pm_agent.make_decision(
    context=context,
    response_schema=WarRoomDecision.model_json_schema()
)

# response는 항상 WarRoomDecision 형식 보장
decision = WarRoomDecision(**response)
```

### 3. Citations Implementation

**File:** `backend/ai/reasoning/deep_reasoning_with_citations.py`
```python
from typing import List, Dict

class CitedAnalysis:
    """인용 포함 분석"""

    async def analyze_with_citations(
        self,
        news_text: str
    ) -> Dict:
        response = await self.ai_client.generate(
            prompt=f"Analyze this news with citations:\n{news_text}",
            citations=True
        )

        return {
            "analysis": response.content,
            "citations": [
                {
                    "source": "input_news",
                    "text": citation.text,
                    "start": citation.start,
                    "end": citation.end
                }
                for citation in response.citations
            ]
        }
```

**Frontend Display:**
```typescript
// frontend/src/components/AnalysisWithCitations.tsx
interface Citation {
  source: string;
  text: string;
  start: number;
  end: number;
}

const AnalysisWithCitations: React.FC<{result: Analysis}> = ({result}) => {
  return (
    <div>
      <p>{result.analysis}</p>
      <div className="citations">
        <h4>Sources:</h4>
        {result.citations.map((cite, i) => (
          <div key={i} className="citation">
            <sup>[{i+1}]</sup>
            <span>"{cite.text}"</span>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 📈 Success Metrics

### Phase 1 Success Criteria (1주)
- [ ] Prompt Caching 적용 완료
- [ ] API 비용 70% 이상 절감 확인
- [ ] Structured Outputs 적용 완료
- [ ] JSON 파싱 에러 제로 달성
- [ ] Citations 적용 완료
- [ ] 사용자 피드백 긍정적

### Phase 2 Success Criteria (2주)
- [ ] Extended Thinking 적용
- [ ] War Room 의사결정 품질 측정 개선
- [ ] Web Search 통합
- [ ] 최신 뉴스 자동 수집 확인
- [ ] Memory 시스템 구축
- [ ] 과거 트레이드 학습 확인

---

## 🚨 Risks & Mitigation

### Risk 1: API 비용 증가
**Mitigation:**
- Caching 먼저 적용 → 비용 절감 확인 후 다른 기능 추가
- Batch Processing으로 추가 절감

### Risk 2: 새 기능 불안정
**Mitigation:**
- Beta 기능은 별도 브랜치에서 테스트
- Feature Flag로 점진적 롤아웃

### Risk 3: 학습 곡선
**Mitigation:**
- 한 번에 하나씩 적용
- 충분한 테스트 및 문서화

---

## 📚 References
- [Claude API Documentation](https://platform.claude.com/docs/ko/build-with-claude/overview)
- [Prompt Caching Guide](https://platform.claude.com/docs/ko/build-with-claude/prompt-caching)
- [Structured Outputs Guide](https://platform.claude.com/docs/ko/build-with-claude/structured-outputs)

---

## ✅ Action Items

### Immediate (이번 주)
1. [ ] Prompt Caching 1hr 적용 (PM Agent, Macro Agent)
2. [ ] 비용 절감 측정 대시보드 추가
3. [ ] Structured Outputs 스키마 정의

### Short-term (다음 주)
4. [ ] Citations 통합 (Deep Reasoning)
5. [ ] Extended Thinking 테스트 (복잡한 의사결정)
6. [ ] Web Search 통합 계획

### Long-term (1개월)
7. [ ] Memory 시스템 설계
8. [ ] Batch Processing 파이프라인 구축
9. [ ] Code Execution 검토

---

**Status:** Ready for Implementation
**Owner:** AI Trading System Team
**Priority:** P0 (Highest)
