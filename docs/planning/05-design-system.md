# Design System (기초 디자인 시스템)
# GLM-4.7 뉴스 해석 서비스

> 이 시스템은 백엔드 API 모듈이므로 로깅, 에러 처리, API 응답 포맷 등 "개발자 경험(DX)"을 위한 디자인 시스템입니다.

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

## 1. 디자인 철학 (개발자 경험 중심)

### 1.1 핵심 가치

| 가치 | 설명 | 구현 방법 |
|------|------|----------|
| **일관성** | 기존 Claude/Gemini/ChatGPT 클라이언트와 동일한 패턴 | 동일한 메서드 명명, 로깅 포맷, 에러 처리 |
| **관찰 가능성** | 모든 주요 동작이 로그로 추적 가능 | 구조화된 로그, 메트릭 수집 |
| **회복성** | API 실패 시 자동 Fallback | 로컬 LLM으로 우아한 degradation |
| **투명성** | 비용, 성능, 성공률이 실시간 확인 | get_metrics() 메서드 |

### 1.2 참고 클라이언트 (무드보드)

| 클라이언트 | 참고할 점 | 참고하지 않을 점 |
|-----------|----------|-----------------|
| ClaudeClient | Prompt Caching, 메트릭 수집 | 복잡한 캐시 로직 |
| GeminiClient | 간단한 화면 리스크 스크리닝 | JSON 파싱 오류 처리 |
| ChatGPTClient | 레짐 감지, 캐싱 전략 | 복잡한 레짐 로직 |

---

## 2. API 응답 포맷 (JSON Schema)

### 2.1 성공 응답

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

### 2.2 에러 응답

```json
{
  "error": {
    "code": "GLM_API_ERROR",
    "message": "GLM API 호출 실패",
    "details": {
      "status_code": 500,
      "response": "Internal Server Error",
      "fallback_used": true,
      "fallback_model": "local_llm"
    }
  }
}
```

---

## 3. 로깅 시스템 (Log Design)

### 3.1 로그 레벨

| 레벨 | 용도 | 예시 |
|------|------|------|
| DEBUG | 개발 중 디버깅 | "GLM API request payload: {...}" |
| INFO | 주요 작업 | "GLM analysis for AAPL: tickers=['AAPL'], confidence=0.87" |
| WARNING | 예상 가능한 문제 | "GLM API timeout, falling back to local LLM" |
| ERROR | 처리 실패 | "GLM API error: rate_limit_exceeded" |

### 3.2 구조화된 로그 포맷

```python
# 성공 로그
logger.info(
    f"GLM analysis for {ticker}: "
    f"tickers={tickers}, "
    f"sectors={sectors}, "
    f"confidence={confidence:.2f}, "
    f"latency={latency_ms:.0f}ms, "
    f"cost=${cost:.4f}"
)

# 에러 로그
logger.error(
    f"GLM API error for {ticker}: "
    f"status={status_code}, "
    f"message={error_message}, "
    f"fallback={'enabled' if use_fallback else 'disabled'}"
)
```

### 3.3 메트릭 수집

```python
{
  "total_requests": 1000,
  "successful_requests": 950,
  "failed_requests": 50,
  "success_rate": 0.95,
  "avg_latency_ms": 1234.5,
  "total_cost_usd": 1.23,
  "avg_cost_per_request": 0.00123
}
```

---

## 4. 에러 처리 전략

### 4.1 에러 유형별 처리

| 에러 유형 | 처리 방법 | Fallback |
|-----------|----------|----------|
| API Key 없음 | 시스템 시작 시 에러, 종료 | 없음 (치명적) |
| 네트워크 타임아웃 | 3회 재시도 후 Fallback | 로컬 LLM |
| Rate Limit | 지수 백오프 후 재시도 | 로컬 LLM |
| JSON 파싱 실패 | Fallback | 로컬 LLM |
| DB 저장 실패 | 3회 재시도 후 로그만 | 없음 |

### 4.2 재시도 전략

```python
# Exponential Backoff
retry 1: 즉시
retry 2: 2초 후
retry 3: 4초 후
fallback: 로컬 LLM
```

---

## 5. API 인터페이스 디자인

### 5.1 GLMClient 클래스

```python
class GLMClient:
    def __init__(self, api_key: Optional[str] = None):
        """
        GLM API 클라이언트 초기화

        Args:
            api_key: GLM API Key (없으면 환경 변수에서 로드)
        """

    async def analyze_news(
        self,
        news_text: str,
        news_url: str,
        published_at: datetime
    ) -> dict:
        """
        뉴스 분석 메서드

        Args:
            news_text: 뉴스 본문
            news_url: 뉴스 URL
            published_at: 게시 시간

        Returns:
            {
                "tickers": List[str],
                "sectors": List[str],
                "confidence": float,
                "reasoning": str,
                "analyzed_at": str,
                "model": str,
                "latency_ms": int,
                "cost_usd": float
            }
        """

    def get_metrics(self) -> dict:
        """
        API 사용 메트릭 반환

        Returns:
            {
                "total_requests": int,
                "success_rate": float,
                "avg_latency_ms": float,
                "total_cost_usd": float
            }
        """
```

### 5.2 Pydantic 모델

```python
from pydantic import BaseModel
from typing import List
from datetime import datetime

class GLMAnalysisResult(BaseModel):
    """GLM 분석 결과 모델"""
    tickers: List[str]
    sectors: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    analyzed_at: str
    model: str
    latency_ms: int
    cost_usd: float

    class Config:
        json_schema_extra = {
            "example": {
                "tickers": ["AAPL", "TSLA"],
                "sectors": ["Technology"],
                "confidence": 0.87,
                "reasoning": "전력 반도체 공급망 뉴스",
                "analyzed_at": "2026-01-15T10:30:00Z",
                "model": "glm-4-flash",
                "latency_ms": 1234,
                "cost_usd": 0.001
            }
        }
```

---

## 6. 테스트ability 디자인

### 6.1 Mock 지원

```python
class MockGLMClient:
    """테스트용 Mock GLM 클라이언트"""

    def __init__(self, mock_response: dict = None):
        self.mock_response = mock_response or self._default_mock()

    async def analyze_news(self, news_text: str, **kwargs) -> dict:
        """Mock 응답 반환"""
        return self.mock_response

    def _default_mock(self) -> dict:
        return {
            "tickers": ["MOCK"],
            "sectors": ["Technology"],
            "confidence": 0.5,
            "reasoning": "Mock response for testing",
            "analyzed_at": datetime.now().isoformat(),
            "model": "mock",
            "latency_ms": 100,
            "cost_usd": 0.0
        }
```

### 6.2 테스트 더미 데이터

```python
# 테스트용 뉴스 데이터
TEST_NEWS = {
    "title": "Apple announces new M4 chip",
    "content": "Apple unveiled its latest M4 chip...",
    "url": "https://example.com/apple-m4",
    "published_at": "2026-01-15T10:00:00Z"
}

# 예상 응답
EXPECTED_RESULT = {
    "tickers": ["AAPL"],
    "sectors": ["Technology", "Consumer Electronics"],
    "confidence": 0.9,
    "reasoning": "Apple의 신칩 발표 뉴스",
    "analyzed_at": "2026-01-15T10:30:00Z",
    "model": "glm-4-flash",
    "latency_ms": 1500,
    "cost_usd": 0.001
}
```

---

## 7. 접근성 체크리스트 (개발자 관점)

### 7.1 필수 (MVP)

- [ ] **명확한 에러 메시지**: 어떤 문제인지, 어떻게 해결할지 설명
- [ ] **메트릭 노출**: get_metrics()로 성능/비용 확인 가능
- [ ] **Fallback 명시**: Fallback 사용 시 로그에 표시
- [ ] **일관된 인터페이스**: 기존 클라이언트와 동일한 메서드 명명
- [ ] **타입 안전성**: Pydantic 모델로 입력/출력 검증

### 7.2 권장 (v2)

- [ ] OpenAPI/Swagger 문서 자동 생성
- [ ] 웹 대시보드로 실시간 메트릭 시각화
- [ ] Alerting (성공률 90% 미만 등)

---

## Decision Log 참조

| ID | 항목 | 선택 | 관련 디자인 |
|----|------|------|------------|
| D-10 | UX/UI | 기존 시스템과 호환 | 클라이언트 인터페이스 |
| D-15 | 로깅 스타일 | 기존 스타일 유지 | 구조화된 로그 포맷 |
| D-20 | AI 클라이언트 | 단일 GLM 클라이언트 클래스 | GLMClient 인터페이스 |
