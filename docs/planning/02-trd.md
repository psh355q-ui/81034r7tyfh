# TRD (기술 요구사항 정의서)
# GLM-4.7 뉴스 해석 서비스

> 개발자/AI 코딩 파트너가 참조하는 기술 문서입니다.
> 기술 표현을 사용하되, "왜 이 선택인지"를 함께 설명합니다.

---

## MVP 캡슐

| # | 항목 | 내용 |
|---|------|------|
| 1 | 목표 | AI 트레이딩 시스템의 뉴스 해석 비용을 절감하고 분석 품질을 향상시키는 것 |
| 2 | 페르소나 | AI 트레이딩 시스템 개발자 (기존 시스템에 newspoller 존재, 로컬 LLM 사용 중) |
| 3 | 핵심 기능 | FEAT-1: 종목/섹터 식별 (뉴스에서 관련 종목과 섹터를 추출) |
| 4 | 성공 지표 (노스스타) | GLM API가 뉴스 분석 성공률 95% 이상, 평균 응답 시간 2초 이내 |
| 5 | 입력 지표 | GLM API 호출 성공률, 평균 응답 시간 |
| 6 | 비기능 요구 | 기존 Claude/Gemini/ChatGPT 클라이언트와 동일한 인터페이스로 통합 |
| 7 | Out-of-scope | 트레이딩 시그널 직접 생성, 포지션 사이즈 결정, 손절/익절 판단 |
| 8 | Top 리스크 | GLM API 장애 시 뉴스 분석 파이프라인 중단 |
| 9 | 완화/실험 | 기존 로컬 LLM을 Fallback으로 유지하여 A/B 테스트 |
| 10 | 다음 단계 | newspoller에 GLM 클라이언트 연동하여 실시간 뉴스 분석 테스트 |

---

## 1. 시스템 아키텍처

### 1.1 고수준 아키텍처

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   newspoller    │────▶│   GLMClient     │────▶│  GLM-4.7 API    │
│  (뉴스 수집)     │     │  (분석 요청)      │     │  (외부 API)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ NewsRepository  │
                       │  (DB 저장)       │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ PostgreSQL      │
                       │ news_articles   │
                       │ (glm_analysis)  │
                       └─────────────────┘
```

### 1.2 컴포넌트 설명

| 컴포넌트 | 역할 | 왜 이 선택? |
|----------|------|-------------|
| newspoller | 50개 이상의 소스에서 실시간 뉴스 수집 | 기존 시스템 컴포넌트 활용 |
| GLMClient | GLM-4.7 API 호출 및 응답 처리 | 기존 클라이언트 패턴 따르기 |
| NewsRepository | Repository Pattern으로 DB 저장 | 기존 시스템 규칙 준수 |
| PostgreSQL | 기존 news_articles 테이블에 JSON 컬럼 추가 | 스키마 변경 최소화 |

---

## 2. 권장 기술 스택

### 2.1 백엔드

| 항목 | 선택 | 이유 | 벤더 락인 리스크 |
|------|------|------|-----------------|
| 프레임워크 | FastAPI | 기존 시스템과 동일, 자동 API 문서, 비동기 지원 | 낮음 |
| 언어 | Python 3.11+ | 기존 시스템과 동일, GLM SDK 지원 | - |
| AI 클라이언트 | 단일 GLMClient 클래스 | Claude/Gemini/ChatGPT 클라이언트와 동일 패턴 | 낮음 |
| ORM | SQLAlchemy 2.0 | 기존 시스템 Repository Pattern | 낮음 |
| 검증 | Pydantic v2 | 기존 시스템 데이터 검증 | 낮음 |

### 2.2 데이터베이스

| 항목 | 선택 | 이유 |
|------|------|------|
| 메인 DB | PostgreSQL 15+ | 기존 시스템, news_articles 테이블 존재 |
| 저장 방식 | JSONB 컬럼 (glm_analysis) | 유연한 구조, 기존 스키마 최소화 |

### 2.3 외부 API

| 항목 | 선택 | 이유 |
|------|------|------|
| AI API | GLM-4.7 | 금융 텍스트 강점, 가성비, GPT-4급 추론력 |
| 인증 | API Key | 환경 변수 관리 (GLM_API_KEY) |

---

## 3. 비기능 요구사항

### 3.1 성능

| 항목 | 요구사항 | 측정 방법 |
|------|----------|----------|
| API 응답 시간 | < 2초 (평균) | GLMClient 로깅 |
| API 성공률 | ≥ 95% | API 모니터링 |
| DB 저장 성공률 | ≥ 99% | Repository 로깅 |

### 3.2 보안

| 항목 | 요구사항 |
|------|----------|
| API Key | 환경 변수로 관리 (.env 파일) |
| 로깅 | 민감 정보 (API Key) 로그 제외 |
| 에러 처리 | API 실패 시 Fallback (로컬 LLM) |

### 3.3 확장성

| 항목 | 현재 | 목표 |
|------|------|------|
| 일일 뉴스 처리 | MVP: 100건 | v2: 1,000건 |
| 동시 API 호출 | MVP: 5개 | v2: 20개 (배치 처리) |

---

## 4. 외부 API 연동

### 4.1 GLM-4.7 API

| 항목 | 값 |
|------|------|
| 기본 URL | https://open.bigmodel.cn/api/paas/v4/chat/completions |
| 모델 | glm-4-flash 또는 glm-4-plus |
| 인증 | Bearer Token (Authorization 헤더) |
| 콘텐츠 타입 | application/json |

### 4.2 API 응답 JSON 스키마

```json
{
  "id": "string",
  "created": 1234567890,
  "model": "glm-4-flash",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{\"tickers\": [\"AAPL\", \"TSLA\"], \"sectors\": [\"Technology\"]}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

### 4.3 GLMClient 메서드

```python
class GLMClient:
    async def analyze_news(
        self,
        news_text: str,
        news_url: str,
        published_at: datetime
    ) -> GLMAnalysisResult:
        """
        뉴스 분석 메서드

        Args:
            news_text: 뉴스 본문
            news_url: 뉴스 URL
            published_at: 게시 시간

        Returns:
            GLMAnalysisResult:
                - tickers: List[str] (식별된 종목 티커)
                - sectors: List[str] (관련 섹터)
                - confidence: float (0.0-1.0)
                - reasoning: str (분석 이유)
                - timestamp: str (ISO 8601)
        """
```

---

## 5. 데이터 생명주기

### 5.1 뉴스 분석 데이터 흐름

```
수집 → 분석 → 저장 → 활용 → 보관
```

### 5.2 데이터 보존

| 데이터 유형 | 보존 기간 | 삭제/익명화 |
|------------|----------|------------|
| 뉴스 원문 | 영구 | 보관 |
| GLM 분석 결과 | 영구 | JSONB로 저장 |
| API 호출 로그 | 30일 | 자동 삭제 |

---

## 6. 테스트 전략 (Contract-First TDD)

### 6.1 개발 방식: Contract-First Development

본 프로젝트는 **계약 우선 개발(Contract-First Development)** 방식을 채택합니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    Contract-First 흐름                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 계약 정의 (Phase 0)                                     │
│     ├─ GLM API 응답 JSON 스키마 정의                        │
│     ├─ GLMAnalysisResult Pydantic 모델                     │
│     └─ NewsRepository 메서드 시그니처                       │
│                                                             │
│  2. 테스트 선행 작성 (🔴 RED)                               │
│     ├─ GLMClient 테스트: tests/ai/test_glm_client.py       │
│     └─ 모든 테스트가 실패하는 상태 (정상!)                  │
│                                                             │
│  3. Mock 생성                                               │
│     └─ Mock GLM API 응답                                  │
│                                                             │
│  4. 구현 (🔴→🟢)                                           │
│     ├─ GLMClient 구현                                      │
│     └─ NewsRepository 확장                                  │
│                                                             │
│  5. 통합 검증                                               │
│     └─ newspoller 연동, 실제 GLM API 호출                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 테스트 피라미드

| 레벨 | 도구 | 커버리지 목표 | 위치 |
|------|------|-------------|------|
| Unit | pytest | ≥ 80% | tests/unit/ |
| Integration | pytest + httpx | Critical paths | tests/integration/ |
| E2E | newspoller 실제 연동 | Key flows | tests/e2e/ |

### 6.3 테스트 도구

| 도구 | 용도 |
|------|------|
| pytest | 테스트 실행 |
| pytest-asyncio | 비동기 테스트 |
| httpx | Mock API 클라이언트 |
| pytest-cov | 커버리지 측정 |
| faker | 테스트 데이터 생성 |

### 6.4 TDD 사이클

```
🔴 RED    → 실패하는 테스트 먼저 작성
🟢 GREEN  → 테스트를 통과하는 최소한의 코드 구현
🔵 REFACTOR → 테스트 통과 유지하며 코드 개선
```

### 6.5 품질 게이트

**병합 전 필수 통과:**
- [ ] 모든 단위 테스트 통과
- [ ] 커버리지 ≥ 80%
- [ ] 린트 통과 (ruff)
- [ ] 타입 체크 통과 (mypy)

**검증 명령어:**
```bash
# 백엔드
pytest tests/ai/test_glm_client.py --cov=backend/ai --cov-report=term-missing
ruff check backend/ai/
mypy backend/ai/
```

---

## 7. API 설계 원칙

### 7.1 GLMClient 인터페이스

기존 Claude/Gemini/ChatGPT 클라이언트와 동일한 패턴을 따릅니다.

```python
class GLMClient:
    def __init__(self, api_key: Optional[str] = None):
        """GLM API 클라이언트 초기화"""

    async def analyze_news(
        self,
        news_text: str,
        news_url: str,
        published_at: datetime
    ) -> dict:
        """뉴스 분석 메서드"""

    def get_metrics(self) -> dict:
        """API 사용 메트릭 반환"""
```

### 7.2 로깅 포맷

기존 스타일 유지 (구조화된 로그):

```python
logger.info(
    f"GLM analysis for {ticker}: "
    f"tickers={tickers}, "
    f"sectors={sectors}, "
    f"confidence={confidence:.2f}, "
    f"latency={latency_ms:.0f}ms, "
    f"cost=${cost:.4f}"
)
```

### 7.3 에러 처리

```python
try:
    result = await self._call_glm_api(prompt)
except GLMAPIError as e:
    logger.error(f"GLM API error: {e}")
    # Fallback to local LLM
    return await self._fallback_to_local_llm(news_text)
```

---

## 8. DB 스키마 설계

### 8.1 news_articles 테이블 확장

```sql
-- 기존 테이블에 JSONB 컬럼 추가
ALTER TABLE news_articles
ADD COLUMN glm_analysis JSONB;

-- 인덱스 생성 (선택)
CREATE INDEX idx_news_articles_glm_analysis
ON news_articles USING GIN (glm_analysis);
```

### 8.2 glm_analysis JSONB 구조

```json
{
  "tickers": ["AAPL", "TSLA", "NVDA"],
  "sectors": ["Technology", "Consumer Electronics"],
  "confidence": 0.87,
  "reasoning": "뉴스에서 Apple, Tesla의 전력 반도체 공급망 언급",
  "analyzed_at": "2026-01-15T10:30:00Z",
  "model": "glm-4-flash",
  "latency_ms": 1234,
  "cost_usd": 0.001
}
```

---

## 9. 파일 구조

### 9.1 백엔드

```
backend/
├── ai/
│   ├── glm_client.py           # GLM-4.7 API 클라이언트
│   ├── claude_client.py        # 기존
│   ├── gemini_client.py        # 기존
│   └── chatgpt_client.py       # 기존
├── database/
│   ├── models.py               # 기존 (glm_analysis 컬럼 추가)
│   └── repository.py           # NewsRepository 확장
└── tests/
    ├── ai/
    │   └── test_glm_client.py  # GLMClient 테스트
    └── database/
        └── test_repository.py  # Repository 테스트
```

---

## Decision Log 참조

| ID | 항목 | 선택 | 근거 | 영향 |
|----|------|------|------|------|
| D-19 | 백엔드 | FastAPI (기존 시스템과 동일) | 기존 패턴 유지 | 아키텍처 |
| D-20 | AI 클라이언트 | 단일 GLM 클라이언트 클래스 | 코드 일관성, 유지보수 용이 | 클래스 설계 |
| D-21 | DB 저장 | NewsRepository 확장 | Repository Pattern 유지 | 코드 구조 |
