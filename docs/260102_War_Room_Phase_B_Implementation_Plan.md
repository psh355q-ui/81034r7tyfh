# War Room MVP - Phase B Implementation Plan

**Date**: 2026-01-02  
**Phase**: Post-Migration Enhancements  
**Priority**: Medium (1개월 내)

---

## 개요

Skills Migration (Phase A) 완료 후, Claude API의 고급 기능을 활용하여 War Room MVP의 성능과 안정성을 개선합니다.

---

## Phase B Features

### 1. Structured Outputs (JSON Schema) ⭐

**목표**: JSON 파싱 에러 제로화, 응답 구조 표준화

**현재 상태:**
- Agent 응답이 자유 형식 JSON
- 파싱 실패 시 fallback 로직 필요
- 응답 형식이 agent마다 약간씩 다름

**개선 방안:**
```python
# Pydantic 스키마 정의
from pydantic import BaseModel, Field

class TraderAgentResponse(BaseModel):
    action: Literal['buy', 'sell', 'hold', 'pass']
    confidence: float = Field(ge=0.0, le=1.0)
    opportunity_score: float = Field(ge=0.0, le=100.0)
    reasoning: str
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
```

**구현 위치:**
- `backend/ai/schemas/war_room_schemas.py` (신규)
- 각 agent의 `analyze()` 또는 handler `execute()` 수정

**예상 효과:**
- 파싱 에러 100% → 0%
- 타입 안전성 보장
- API 문서 자동 생성

**작업 시간:** 2-3시간

---

### 2. Prompt Caching ⭐⭐

**목표**: API 비용 80% 절감, 응답 속도 개선

**현재 상태:**
- 매 요청마다 전체 프롬프트 전송
- 시스템 프롬프트 (investment principles, agent roles) 반복 전송

**개선 방안:**
```python
from anthropic import Anthropic

client = Anthropic()

# Cache 가능한 시스템 프롬프트
system_prompt_cached = [
    {
        "type": "text",
        "text": "You are a professional trader...",  # 길이 > 1024 tokens
        "cache_control": {"type": "ephemeral"}
    }
]

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    system=system_prompt_cached,
    messages=[...],
    max_tokens=1024
)
```

**Cache 대상:**
1. **Investment Principles** (~2000 tokens)
   - 위치: 각 agent의 시스템 프롬프트
   
2. **Agent Role Definitions** (~500-1000 tokens)
   - PM Agent: Hard Rules
   - Trader Agent: Technical analysis guidelines
   - Risk Agent: Kelly Criterion formula
   - Analyst Agent: 4-in-1 analysis framework

3. **Recent Market Context** (선택적)
   - 최근 24시간 뉴스 요약
   - 매크로 경제 지표

**구현 파일:**
- `backend/ai/config/cached_prompts.py` (신규)
- 각 MVP agent 파일 수정 (trader_agent_mvp.py, risk_agent_mvp.py 등)

**예상 효과:**
- API 비용: $250/월 → $50/월 (80% 절감)
- Cache hit 시 응답 속도 2-5배 향상
- 연간 절감: $2,400

**작업 시간:** 1-2시간

---

### 3. invoke_legacy_war_room() 실제 구현

**목표**: MVP에서 Legacy 8-Agent 호출 가능

**현재 상태:**
- Placeholder 함수만 존재
- TODO 상태

**구현 방안:**
```python
# backend/ai/skills/war_room_mvp/orchestrator_mvp/handler.py

def invoke_legacy_war_room(symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """MVP가 Legacy 8-Agent War Room을 호출"""
    from backend.ai.debate.debate_engine import DebateEngine
    
    # Legacy Engine 초기화
    engine = DebateEngine()
    
    # 8개 agent 투표 실행
    debate_result = engine.run_debate(
        symbol=symbol,
        action=context.get('action', 'analyze'),
        additional_context=context
    )
    
    return {
        'source': 'legacy_8_agent_war_room',
        'symbol': symbol,
        'votes': debate_result.get('votes', []),
        'consensus': debate_result.get('consensus'),
        'final_decision': debate_result.get('final_decision'),
        'processing_time': debate_result.get('processing_time')
    }
```

**사용 시나리오:**
1. **A/B Testing**: MVP vs Legacy 결과 비교
2. **Validation**: 중요한 결정의 2차 검증
3. **Fallback**: MVP에 문제 발생 시 자동 전환

**작업 시간:** 1시간

---

## 구현 우선순위

### Priority 1: Prompt Caching
- **이유**: 가장 큰 비용 절감 효과
- **난이도**: 낮음
- **영향도**: 높음 (전체 시스템)

### Priority 2: Structured Outputs
- **이유**: 안정성 크게 향상
- **난이도**: 중간
- **영향도**: 높음 (파싱 에러 제거)

### Priority 3: Legacy Integration
- **이유**: 검증 및 fallback 용도
- **난이도**: 낮음
- **영향도**: 중간 (선택적 사용)

---

## 상세 구현 가이드

### Prompt Caching Implementation

#### Step 1: 캐시 가능한 프롬프트 추출
```python
# backend/ai/config/cached_prompts.py

INVESTMENT_PRINCIPLES = """
You are an AI trading agent following these core principles:

1. **Risk Management First**
   - Never risk more than 2% of portfolio on single trade
   - Always use stop-loss orders
   - Diversify across sectors
   ...
"""

TRADER_AGENT_ROLE = """
You are a professional trader specializing in:
- Technical analysis (RSI, MACD, Bollinger Bands)
- Momentum trading
- Short-term opportunities (1-2 weeks)
...
"""

# 2000+ tokens (cache 최소 크기)
```

#### Step 2: Agent 수정
```python
# backend/ai/mvp/trader_agent_mvp.py

from ai.config.cached_prompts import INVESTMENT_PRINCIPLES, TRADER_AGENT_ROLE

class TraderAgentMVP:
    def _build_prompt_with_cache(self, ...):
        # System prompt with caching
        system_prompt = [
            {
                "type": "text",
                "text": INVESTMENT_PRINCIPLES,
                "cache_control": {"type": "ephemeral"}
            },
            {
                "type": "text", 
                "text": TRADER_AGENT_ROLE,
                "cache_control": {"type": "ephemeral"}
            }
        ]
        
        return system_prompt
```

#### Step 3: Gemini API 호출 수정
```python
# Gemini에는 native caching이 없으므로 대안 방식
# 1. Context Caching API 사용 (있다면)
# 2. 프롬프트 재구성으로 토큰 절약
```

---

### Structured Outputs Implementation

#### Step 1: Schema 정의
```python
# backend/ai/schemas/war_room_schemas.py

from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class TraderOpinion(BaseModel):
    agent: Literal['trader_mvp'] = 'trader_mvp'
    action: Literal['buy', 'sell', 'hold', 'pass']
    confidence: float = Field(ge=0.0, le=1.0)
    opportunity_score: float = Field(ge=0.0, le=100.0)
    reasoning: str
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    technical_indicators: Optional[dict] = None
    catalysts: List[str] = []

class RiskOpinion(BaseModel):
    agent: Literal['risk_mvp'] = 'risk_mvp'
    action: Literal['approve', 'reject', 'reduce_size']
    confidence: float = Field(ge=0.0, le=1.0)
    position_size: float = Field(ge=0.0, le=100.0)
    risk_level: Literal['low', 'moderate', 'high', 'extreme']
    stop_loss: float
    reasoning: str
    kelly_calculation: Optional[dict] = None
    warnings: List[str] = []

class PMDecision(BaseModel):
    agent: Literal['pm_mvp'] = 'pm_mvp'
    final_decision: Literal['approve', 'reject', 'reduce_size', 'silence']
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    hard_rules_passed: bool
    recommended_action: str
    approved_params: Optional[dict] = None
```

#### Step 2: Agent 수정
```python
# backend/ai/mvp/trader_agent_mvp.py

from ai.schemas.war_room_schemas import TraderOpinion

class TraderAgentMVP:
    def analyze(self, ...) -> TraderOpinion:
        # Gemini API 호출
        response = self.model.generate_content(...)
        
        # JSON schema 지정 (Gemini 2.0+)
        result_json = self._parse_with_schema(response, TraderOpinion)
        
        # Pydantic validation
        return TraderOpinion(**result_json)
```

---

## 테스트 계획

### Prompt Caching Test
```python
# 1. Cache miss (첫 요청)
result1 = trader.analyze(...)
print(f"First call: {result1['usage']['cache_creation_input_tokens']}")

# 2. Cache hit (두번째 요청, 5분 이내)
result2 = trader.analyze(...)  
print(f"Second call: {result2['usage']['cache_read_input_tokens']}")

# 예상:
# - First call: 2000 tokens cached
# - Second call: 2000 tokens from cache (90% 비용 절감)
```

### Structured Outputs Test
```python
# Schema validation 테스트
try:
    result = trader.analyze(...)
    assert isinstance(result, TraderOpinion)
    assert result.confidence >= 0.0 and result.confidence <= 1.0
    print("✅ Schema validation passed")
except ValidationError as e:
    print(f"❌ Schema validation failed: {e}")
```

---

## Roll-out Plan

### Week 1: Prompt Caching
- Day 1-2: 캐시 가능한 프롬프트 추출 및 정리
- Day 3-4: Agent 코드 수정
- Day 5: 테스트 및 비용 측정

### Week 2: Structured Outputs  
- Day 1-2: Pydantic 스키마 정의
- Day 3-4: Agent 응답 파싱 수정
- Day 5: 통합 테스트

### Week 3: Legacy Integration
- Day 1-2: invoke_legacy_war_room() 구현
- Day 3: A/B 테스트
- Day 4-5: 문서화

### Week 4: 검증 및 Production
- 성능 측정
- 비용 절감 확인
- Production 배포

---

## 성공 지표

### Prompt Caching
- ✅ API 비용 80% 이상 절감
- ✅ Cache hit rate > 70%
- ✅ 응답 속도 2배 이상 개선

### Structured Outputs
- ✅ JSON 파싱 에러 0건/일
- ✅ 모든 응답이 schema 통과
- ✅ Type 관련 버그 0건

### Legacy Integration
- ✅ MVP ↔ Legacy 결과 비교 성공
- ✅ Fallback 메커니즘 동작 검증
- ✅ A/B 테스트 데이터 수집

---

**작성자:** AI Trading System Team  
**최종 업데이트:** 2026-01-02  
**Status:** Ready to Implement
