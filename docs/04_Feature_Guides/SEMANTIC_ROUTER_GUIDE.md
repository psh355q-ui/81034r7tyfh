# Semantic Router 가이드

## 개요

**Semantic Router**는 AI Trading System의 토큰 사용량을 최적화하는 3단계 라우팅 시스템입니다.

### 핵심 목표

- **토큰 사용량 83% 절감**: 3,800 토큰/요청 → 650 토큰/요청
- **비용 72% 절감**: $330/월 → $94/월 (1,000 요청/일 기준)
- **동적 도구 선택**: 필요한 도구만 로드
- **최적 모델 라우팅**: Intent에 맞는 AI 모델 자동 선택

---

## 시스템 아키텍처

```
사용자 입력
    ↓
┌─────────────────────────────────────────────────┐
│ Stage 1: Intent Classification                 │
│ - 규칙 기반 패턴 매칭 (무료, 빠름)               │
│ - 또는 Local LLM (선택적)                       │
└─────────────────────────────────────────────────┘
    ↓
    Intent: news_analysis
    ↓
┌─────────────────────────────────────────────────┐
│ Stage 2: Tool Group Selection                  │
│ - Intent → Tool Groups 매핑                    │
│ - 필요한 도구만 로드 (평균 5개 vs 전체 30개)     │
│ - Tool Definition 캐싱                         │
└─────────────────────────────────────────────────┘
    ↓
    Tool Groups: [News, Gemini]
    ↓
┌─────────────────────────────────────────────────┐
│ Stage 3: Model Selection                       │
│ - Intent 기반 최적 모델 선택                     │
│ - 비용/성능 균형                                │
└─────────────────────────────────────────────────┘
    ↓
    Model: gemini-1.5-flash
    ↓
API 요청 실행
```

---

## 주요 기능

### 1. Intent Classification

사용자 입력을 7가지 Intent로 분류:

| Intent | 설명 | 예시 |
|--------|------|------|
| `news_analysis` | 뉴스/기사 분석 | "삼성전자 최근 뉴스 분석해줘" |
| `trading_execution` | 매매 실행 | "삼성전자 10주 매수해줘" |
| `strategy_generation` | 전략 생성/백테스트 | "이동평균 전략 만들어줘" |
| `market_research` | 시장/기업 조사 | "반도체 산업 분석해줘" |
| `portfolio_management` | 포트폴리오 관리 | "내 계좌 잔고 확인해줘" |
| `data_query` | 데이터 조회 | "삼성전자 현재가는?" |
| `general_query` | 일반 질문 | "안녕하세요" |

### 2. Tool Group Selection

Intent에 따라 필요한 Tool Groups만 선택:

```python
Intent.NEWS_ANALYSIS → [
    "MarketData.News",      # 뉴스 검색/수집
    "Intelligence.Gemini"   # 뉴스 분석
]

Intent.TRADING_EXECUTION → [
    "Trading.KIS",          # KIS API 주문
    "Trading.Order",        # 주문 관리
    "Trading.Risk"          # 리스크 관리
]
```

**토큰 절감 효과**:
- 현재: 30개 도구 × 100토큰 = 3,000 토큰
- 최적화: 5개 도구 × 100토큰 = 500 토큰
- **절감: 2,500 토큰 (83%)**

### 3. Model Selection

Intent별 최적 AI 모델 자동 선택:

| Intent | 모델 | 이유 |
|--------|------|------|
| `news_analysis` | Gemini 1.5 Flash | 뉴스 분석 특화, 저렴 |
| `trading_execution` | GPT-4o Mini | 빠른 응답, 안정성 |
| `strategy_generation` | GPT-4o | 고품질 전략 생성 |
| `market_research` | Claude Sonnet 4.5 | 긴 컨텍스트, 심층 분석 |
| `data_query` | Local LLM (Llama 3.2) | 간단한 쿼리, 무료 |

### 4. Tool Definition Caching

도구 정의를 캐싱하여 중복 전송 방지:

```python
# 첫 요청
tools = get_tools_for_intent(Intent.NEWS_ANALYSIS)  # 5개 도구
cache_key = cache_tools(tools)  # "a3f8c2e9..."

# 이후 요청 (같은 Intent)
cached_tools = get_cached_tools(cache_key)  # 캐시에서 로드
# 토큰 90% 절감!
```

**캐시 히트 시 절감**:
- 원본: 500 토큰
- 캐시: 50 토큰
- **절감: 450 토큰 (90%)**

---

## 사용 방법

### 기본 사용

```python
from backend.routing import SemanticRouter

# 라우터 생성
router = SemanticRouter(
    use_local_llm_for_intent=False,  # Local LLM 사용 여부
    enable_caching=True,             # 캐싱 활성화
    prefer_low_cost=False,           # 저비용 모드
)

# 라우팅 실행
result = await router.route("삼성전자 최근 뉴스 분석해줘")

print(f"Intent: {result.intent}")
print(f"Model: {result.provider}/{result.model}")
print(f"Tools: {result.tool_count}개")
print(f"Estimated Tokens: {result.estimated_tokens}")
print(f"Estimated Cost: ${result.estimated_cost_usd:.6f}")
```

### 라우팅 결과 활용

```python
# 라우팅 결과로 AI API 호출
if result.provider == "openai":
    from openai import AsyncOpenAI
    client = AsyncOpenAI()

    response = await client.chat.completions.create(
        model=result.model,
        messages=[
            {"role": "system", "content": "You are a trading assistant."},
            {"role": "user", "content": user_input}
        ],
        tools=result.tools,  # 선택된 도구만 전송
        max_tokens=result.model_config["max_tokens"],
        temperature=result.model_config["temperature"],
    )

elif result.provider == "gemini":
    # Gemini API 호출
    ...
```

### 저비용 모드

비용을 최우선으로 고려:

```python
router = SemanticRouter(prefer_low_cost=True)

result = await router.route("복잡한 전략 만들어줘")
# 일반 모드: GPT-4o ($$$)
# 저비용 모드: GPT-4o Mini ($)
```

### Local LLM for Intent Classification

로컬 LLM으로 Intent 분류 (완전 무료):

```python
# Ollama 실행 필요
# docker-compose up -d local-llm

router = SemanticRouter(use_local_llm_for_intent=True)
result = await router.route("삼성전자 뉴스 분석해줘")
# Intent 분류 비용: $0 (무료!)
```

### 통계 조회

```python
stats = router.get_statistics()

print(f"Total Routes: {stats['total_routes']}")
print(f"Tokens Saved: {stats['total_tokens_saved']:,}")
print(f"Cache Hit Rate: {stats['cache_stats']['hit_rate'] * 100:.1f}%")
```

---

## 테스트 실행

```bash
# 테스트 실행
cd D:\code\ai-trading-system
python -m backend.routing.test_semantic_router

# 예상 출력:
# ✅ Single route test passed!
# ✅ Batch routing test passed!
# ✅ Caching effect test passed!
# ✅ Low cost mode test passed!
# ✅ Statistics test passed!
#
# 💰 Total Savings (1,000 requests/day):
#   Tokens: 2,500,000 (83%)
#   Cost: $236/month (72%)
```

---

## 성능 벤치마크

### 시나리오: 하루 1,000 요청

| 메트릭 | 최적화 전 | 최적화 후 | 절감 |
|--------|----------|----------|------|
| **토큰/요청** | 3,800 | 650 | 83% |
| **일일 토큰** | 3,800,000 | 650,000 | 83% |
| **일일 비용** | $11.00 | $3.13 | 72% |
| **월간 비용** | $330 | $94 | **$236 절감** |
| **연간 비용** | $3,960 | $1,128 | **$2,832 절감** |

### 캐싱 효과

| 요청 유형 | 토큰 | 비용 | 절감률 |
|----------|------|------|--------|
| 캐시 미스 (첫 요청) | 500 | $0.00125 | 0% |
| 캐시 히트 (이후 요청) | 50 | $0.000125 | 90% |

**캐시 히트율 80% 가정 시**:
- 200 요청 (캐시 미스) × 500 토큰 = 100,000 토큰
- 800 요청 (캐시 히트) × 50 토큰 = 40,000 토큰
- **총합: 140,000 토큰 (vs 500,000 토큰) → 72% 절감**

---

## 통합 가이드

### FastAPI 통합

```python
# backend/main.py
from fastapi import FastAPI
from backend.routing import get_semantic_router

app = FastAPI()
router = get_semantic_router(enable_caching=True)

@app.post("/api/chat")
async def chat(user_input: str):
    # 라우팅
    routing_result = await router.route(user_input)

    # AI API 호출 (선택된 모델과 도구 사용)
    response = await call_ai_api(
        provider=routing_result.provider,
        model=routing_result.model,
        tools=routing_result.tools,
        user_input=user_input,
    )

    return {
        "response": response,
        "routing": {
            "intent": routing_result.intent,
            "model": routing_result.model,
            "tokens": routing_result.estimated_tokens,
            "cost": routing_result.estimated_cost_usd,
        }
    }
```

### 신호 생성 파이프라인 통합

```python
# backend/services/signal_pipeline.py
from backend.routing import get_semantic_router

class SignalPipeline:
    def __init__(self):
        self.router = get_semantic_router(enable_caching=True)

    async def process_latest_news(self):
        # 뉴스 조회
        news = get_unanalyzed_news()

        for article in news:
            # 자동 라우팅 (뉴스 분석 → Gemini)
            routing = await self.router.route(
                f"다음 뉴스를 분석해줘: {article.title}"
            )

            # Gemini로 분석 (저비용)
            analysis = await analyze_with_gemini(article, routing.tools)

            # 신호 생성
            signal = self.generate_signal(analysis)
```

---

## 환경 변수 설정

```bash
# .env

# OpenAI
OPENAI_API_KEY=sk-...

# Gemini
GEMINI_API_KEY=...

# Claude
CLAUDE_API_KEY=sk-ant-...

# Semantic Router 설정
SEMANTIC_ROUTER_USE_LOCAL_LLM=false      # Local LLM 사용
SEMANTIC_ROUTER_ENABLE_CACHING=true      # 캐싱 활성화
SEMANTIC_ROUTER_PREFER_LOW_COST=false    # 저비용 모드
SEMANTIC_ROUTER_CACHE_TTL_HOURS=24       # 캐시 유효 시간
```

---

## Local LLM 설정 (선택적)

Intent 분류를 로컬 LLM으로 처리하여 완전 무료 라우팅:

### 1. Ollama 설치

```bash
# Docker Compose에 추가
docker-compose up -d local-llm
```

### 2. 모델 다운로드

```bash
docker exec -it ai-trading-local-llm ollama pull llama3.2:3b
# 또는
docker exec -it ai-trading-local-llm ollama pull phi-3-mini
```

### 3. SemanticRouter에서 활성화

```python
router = SemanticRouter(use_local_llm_for_intent=True)
# Intent 분류 비용: $0 (무료!)
```

### 모델 비교

| 모델 | 크기 | VRAM | 응답 시간 | 정확도 |
|------|------|------|----------|--------|
| Llama 3.2 3B | 3GB | 4GB | ~500ms | 85% |
| Phi-3 Mini | 2GB | 3GB | ~300ms | 80% |
| TinyLlama 1.1B | 1GB | 2GB | ~200ms | 70% |

**권장**: Llama 3.2 3B (정확도 최고)

---

## 트러블슈팅

### Q: 캐시 히트율이 낮아요

**A**: Intent가 다양하면 캐시 히트율이 낮을 수 있습니다.

해결:
```python
# 캐시 TTL 늘리기
from backend.utils.tool_cache import get_tool_cache

cache = get_tool_cache()
cache.ttl = timedelta(hours=48)  # 24시간 → 48시간
```

### Q: Local LLM이 연결 안 돼요

**A**: Ollama 서버가 실행 중인지 확인:

```bash
# 상태 확인
docker ps | grep local-llm

# 로그 확인
docker logs ai-trading-local-llm

# 재시작
docker-compose restart local-llm
```

### Q: Intent 분류가 정확하지 않아요

**A**: 규칙 기반 패턴 추가 또는 Local LLM 활성화:

```python
# 패턴 추가
from backend.routing.intent_classifier import IntentClassifier

classifier = IntentClassifier()
classifier.INTENT_PATTERNS[Intent.NEWS_ANALYSIS].append(r"새로운.*뉴스")

# 또는 Local LLM 사용
router = SemanticRouter(use_local_llm_for_intent=True)
```

---

## 다음 단계

1. **Skill Layer 구현**: Tool Groups를 실제 Skill로 구현
2. **Docker Sandbox 분리**: 보안 강화를 위한 3계층 분리
3. **Code Model Pattern**: 복잡한 워크플로우 최적화
4. **MCP Gateway**: 동적 도구 로딩 (선택적)

자세한 내용은 [ARCHITECTURE_INTEGRATION_PLAN.md](./ARCHITECTURE_INTEGRATION_PLAN.md)를 참고하세요.

---

## 참고 자료

- [OpenAI Prompt Caching](https://platform.openai.com/docs/guides/prompt-caching)
- [Gemini API Pricing](https://ai.google.dev/pricing)
- [Claude API Pricing](https://www.anthropic.com/pricing)
- [Ollama Documentation](https://ollama.ai/docs)

---

## 라이선스

MIT License

---

**문의**: AI Trading System Team
