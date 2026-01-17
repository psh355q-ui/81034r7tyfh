# Coding Convention & AI Collaboration Guide
# GLM-4.7 뉴스 해석 서비스

> 고품질/유지보수/보안을 위한 인간-AI 협업 운영 지침서입니다.
> 기존 시스템의 규칙(.cursorrules)을 준수합니다.

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

## 1. 핵심 원칙

### 1.1 신뢰하되, 검증하라 (Don't Trust, Verify)

AI가 생성한 코드는 반드시 검증해야 합니다:

- [ ] **코드 리뷰**: 생성된 코드 직접 확인
- [ ] **테스트 실행**: 자동화 테스트 통과 확인
- [ ] **보안 검토**: API Key 노출 여부 확인
- [ ] **동작 확인**: 실제로 실행하여 기대 동작 확인

### 1.2 최종 책임은 인간에게

- AI는 도구이고, 최종 결정과 책임은 개발자에게 있습니다
- 이해하지 못하는 코드는 사용하지 않습니다
- 의심스러운 부분은 반드시 질문합니다

---

## 2. 프로젝트 구조

### 2.1 디렉토리 구조

```
backend/
├── ai/
│   ├── glm_client.py           # GLM-4.7 API 클라이언트 (신규)
│   ├── claude_client.py        # 기존
│   ├── gemini_client.py        # 기존
│   └── chatgpt_client.py       # 기존
├── database/
│   ├── models.py               # 기존 (glm_analysis 컬럼 추가)
│   └── repository.py           # NewsRepository 확장
├── news/
│   └── poller.py               # newspoller (기존, GLM 연동)
└── tests/
    ├── ai/
    │   └── test_glm_client.py  # GLMClient 테스트 (신규)
    └── database/
        └── test_repository.py  # Repository 테스트
```

### 2.2 네이밍 규칙

| 대상 | 규칙 | 예시 |
|------|------|------|
| 파일 (Python) | snake_case | `glm_client.py` |
| 클래스 | PascalCase | `GLMClient` |
| 함수/메서드 | snake_case | `analyze_news` |
| 변수 | snake_case | `news_text`, `tickers` |
| 상수 | UPPER_SNAKE | `GLM_API_URL`, `MAX_RETRIES` |

---

## 3. 아키텍처 원칙

### 3.1 Repository Pattern (절대 준수)

```python
# ✅ 올바른 예
from backend.database.repository import NewsRepository

repo = NewsRepository()
repo.save_glm_analysis(news_id, glm_result)

# ❌ 금지된 예
import psycopg2
conn = psycopg2.connect(...)
cursor.execute("INSERT INTO news_articles ...")  # 절대 금지!
```

### 3.2 기존 클라이언트 패턴 따르기

```python
# Claude/Gemini/ChatGPT 클라이언트와 동일한 구조
class GLMClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GLM_API_KEY")
        self.model = "glm-4-flash"
        self.metrics = {
            "total_requests": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
        }

    async def analyze_news(self, news_text: str, **kwargs) -> dict:
        # Claude/Gemini/ChatGPT와 동일한 시그니처
        pass

    def get_metrics(self) -> dict:
        # 메트릭 반환 (다른 클라이언트와 동일)
        pass
```

### 3.3 작은 모듈로 분해

- 한 파일에 200줄 이하 권장
- 한 함수에 50줄 이하 권장
- 단일 책임 원칙: GLMClient는 API 호출만 담당

---

## 4. AI 소통 원칙

### 4.1 컨텍스트 명시

**좋은 예:**
> "TRD 섹션 4의 GLMClient 인터페이스를 구현해주세요.
> Database Design의 glm_analysis JSONB 구조를 참조하고,
> 기존 ClaudeClient의 로깅 패턴을 따라주세요."

**나쁜 예:**
> "GLM 클라이언트 만들어줘"

### 4.2 기존 코드 재사용

- 새로 만들기 전에 기존 Claude/Gemini/ChatGPT 클라이언트 확인 요청
- 중복 코드 방지
- 일관성 유지

### 4.3 프롬프트 템플릿

```
## 작업
GLMClient 클래스 구현 (backend/ai/glm_client.py)

## 참조 문서
- TRD 섹션 4: GLMClient 인터페이스
- Database Design 섹션 2: glm_analysis JSONB 구조
- 기존 ClaudeClient: 로깅 패턴, 에러 처리

## 제약 조건
- Repository Pattern 준수 (직접 SQL 금지)
- API Key는 환경 변수에서 로드
- Fallback: 로컬 LLM 사용

## 예상 결과
- backend/ai/glm_client.py
- tests/ai/test_glm_client.py
```

---

## 5. 보안 체크리스트

### 5.1 절대 금지

- [ ] **API Key 하드코딩 금지**: `.env` 파일에서만 관리
- [ ] **직접 SQL 금지**: Repository Pattern만 사용
- [ ] **로깅 시 민감 정보 제외**: API Key, 개인정보

### 5.2 필수 적용

- [ ] API Key: 환경 변수 `GLM_API_KEY`
- [ ] 입력 검증: Pydantic 모델로 검증
- [ ] 에러 처리: 민감 정보 로그 제외
- [ ] 재시도 전략: 최대 3회, Exponential Backoff

### 5.3 환경 변수 관리

```bash
# .env.example (커밋 O)
GLM_API_KEY=your-glm-api-key-here
GLM_MODEL=glm-4-flash

# .env (커밋 X)
GLM_API_KEY=real-key-from-glm-platform
```

---

## 6. 테스트 워크플로우

### 6.1 TDD 사이클 준수

```
🔴 RED    → 실패하는 테스트 먼저 작성
🟢 GREEN  → 테스트를 통과하는 최소한의 코드 구현
🔵 REFACTOR → 테스트 통과 유지하며 코드 개선
```

### 6.2 테스트 명령어

```bash
# 단위 테스트
pytest tests/ai/test_glm_client.py -v

# 커버리지
pytest tests/ai/test_glm_client.py --cov=backend/ai --cov-report=term-missing

# 통합 테스트
pytest tests/integration/test_glm_integration.py -v
```

### 6.3 오류 로그 공유 규칙

오류 발생 시 AI에게 전달할 정보:

1. 전체 에러 메시지
2. 관련 코드 스니펫
3. 재현 단계
4. 이미 시도한 해결책

**예시:**
```
## 에러
GLM API Error: 401 Unauthorized

## 코드
glm_client.py line 85:
response = await self.async_client.chat.completions.create(...)

## 재현
1. GLM_API_KEY 환경 변수 설정
2. analyze_news() 호출
3. 401 에러 발생

## 시도한 것
- API Key 확인: 정상
- 토큰 재발급: 시도해볼까요?
```

---

## 7. Git 워크플로우

### 7.1 브랜치 전략

```
main          # 프로덕션
├── feature/glm-client     # GLM 클라이언트 구현
├── feature/glm-repository  # Repository 확장
└── fix/glm-fallback       # Fallback 로직 수정
```

### 7.2 커밋 메시지

```
feat(ai): GLM-4.7 뉴스 해석 클라이언트 구현

- GLMClient 클래스 구현 (backend/ai/glm_client.py)
- NewsRepository 확장 (save_glm_analysis 메서드)
- newspoller 연동
- TRD 섹션 4, Database Design 섹션 2 구현 완료

Refs: docs/planning/01-prd.md, 02-trd.md
```

---

## 8. 코드 품질 도구

### 8.1 필수 설정

| 도구 | 설정 | 용도 |
|------|------|------|
| Ruff | `ruff check backend/ai/` | 린터 |
| Black | `black backend/ai/glm_client.py` | 포매터 |
| mypy | `mypy backend/ai/` | 타입 체크 (선택) |
| pytest | `pytest tests/` | 테스트 |

### 8.2 Pre-commit 훅

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff
        name: Ruff Lint
        entry: ruff check backend/ai/
        language: system
      - id: black
        name: Black Format
        entry: black backend/ai/glm_client.py
        language: system
      - id: pytest
        name: Run Tests
        entry: pytest tests/ai/test_glm_client.py
        language: system
```

---

## 9. .cursorrules 준수 (절대)

### 9.1 데이터베이스 규칙

1. **Single Source of Truth**: `backend/database/models.py`가 유일한 스키마 정의
2. **Repository Pattern Only**:
   - 절대 직접 SQL 금지
   - `NewsRepository` 사용
   - `get_sync_session()` 사용
3. **Legacy Patterns Prohibited**:
   - `backend.data.news_models` 임포트 금지
   - SQLite 사용 금지

---

## Decision Log 참조

| ID | 항목 | 선택 | 관련 규칙 |
|----|------|------|------------|
| D-13 | 데이터 저장 | 기존 테이블에 JSON 컬럼 추가 | Repository Pattern |
| D-20 | AI 클라이언트 | 단일 GLM 클라이언트 클래스 | 기존 패턴 따르기 |
| D-21 | DB 저장 | NewsRepository 확장 | 직접 SQL 금지 |
