# User Flow (사용자 흐름도)
# GLM-4.7 뉴스 해석 서비스

> Mermaid 플로우차트로 핵심 기능의 주요 여정을 표현합니다.
> 이 시스템은 백엔드 모듈이므로 개발자 관점에서의 흐름을 표현합니다.

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

## 1. 전체 사용자 여정 (Overview)

```mermaid
graph TD
    A[newspoller 시작] --> B{뉴스 수집}
    B --> C[뉴스 리스트 획득]
    C --> D[GLMClient 초기화]
    D --> E{API Key 확인?}
    E -->|No| F[에러: 환경 변수 없음]
    E -->|Yes| G[FEAT-1: 뉴스 분석]
    G --> H{GLM API 호출}
    H -->|성공| I[종목/섹터 추출]
    H -->|실패| J[Fallback: 로컬 LLM]
    I --> K[DB 저장]
    J --> K
    K --> L{저장 성공?}
    L -->|Yes| M[로깅: 성공]
    L -->|No| N[로깅: 저장 실패]
    M --> O[다음 뉴스]
    N --> O
    O --> C
```

---

## 2. FEAT-1: 종목/섹터 식별 플로우

```mermaid
graph TD
    A[뉴스 텍스트 수신] --> B[GLMClient.analyze_news 호출]
    B --> C[프롬프트 생성]
    C --> D[GLM-4.7 API 요청]

    D --> E{API 응답}
    E -->|200 OK| F[JSON 파싱]
    E -->|에러| G[Fallback: 로컬 LLM]

    F --> H{JSON 유효성}
    H -->|Valid| I[GLMAnalysisResult 생성]
    H -->|Invalid| J[파싱 에러 로깅]
    J --> G

    I --> K[NewsRepository.save_glm_analysis]
    K --> L{DB 저장}
    L -->|성공| M[성공 로깅]
    L -->|실패| N[저장 에러 로깅]

    G --> O[로컬 LLM 분석]
    O --> P[DB 저장]

    M --> Q[메트릭 업데이트]
    N --> Q
    P --> Q
    Q --> R[결과 반환]
```

---

## 3. Fallback 플로우 (API 장애 시)

```mermaid
graph TD
    A[GLM API 호출] --> B{응답 대기}
    B -->|2초 경과| C[타임아웃]
    B -->|HTTP 에러| D[API 에러]
    B -->|JSON 파싱 실패| E[응답 에러]

    C --> F[Fallback 트리거]
    D --> F
    E --> F

    F --> G[로컬 LLM 호출]
    G --> H{로컬 LLM 성공?}
    H -->|Yes| I[로컬 결과 저장]
    H -->|No| J[에러 로깅]

    I --> K[Fallback 사용 로깅]
    J --> L[분석 실패 로깅]

    K --> M[결과 반환]
    L --> M
```

---

## 4. 리텐션 루프 (모니터링 & 개선)

```mermaid
graph TD
    A[뉴스 분석 완료] --> B[메트릭 수집]
    B --> C[성공률 계산]
    C --> D[응답 시간 측정]
    D --> E[비용 계산]

    E --> F{성공률 95% 미만?}
    F -->|Yes| G[알림: 성공률 저하]
    F -->|No| H[정상 운영]

    G --> I[원인 분석]
    I --> J[재시도 전략]

    E --> K{응답 시간 2초 초과?}
    K -->|Yes| L[알림: 성능 저하]
    K -->|No| H

    L --> M[최적화 검토]

    H --> N[다음 뉴스]
    J --> N
    M --> N
```

---

## 5. 에러 처리 플로우

```mermaid
graph TD
    A[에러 발생] --> B{에러 유형?}

    B -->|API Key 없음| C[환경 변수 에러]
    B -->|네트워크| D[연결 에러]
    B -->|JSON 파싱| E[응답 에러]
    B -->|DB 저장| F[저장 에러]

    C --> G[시스템 중단]
    D --> H{재시도 횟수}
    E --> I[Fallback: 로컬 LLM]
    F --> J{재시도 횟수}

    H -->|< 3회| K[API 재요청]
    H -->|≥ 3회| I

    K --> D

    J -->|< 3회| L[DB 재저장]
    J -->|≥ 3회| M[에러 로깅 후 계속]

    I --> N[로컬 LLM 호출]
    L --> N
    N --> O[결과 반환]
```

---

## 6. 개발자 플로우 (테스트 및 통합)

```mermaid
graph TD
    A[개발 시작] --> B[테스트 작성 RED]
    B --> C[Mock GLM API 응답]
    C --> D[GLMClient 구현 GREEN]
    D --> E[단위 테스트 통과]
    E --> F[NewsRepository 확장]
    F --> G[Repository 테스트]
    G --> H{통합 테스트}
    H -->|newspoller 연동| I[실제 뉴스 분석]
    I --> J{A/B 테스트}
    J --> K[GLM vs 로컬 LLM 비교]
    K --> L[성공 시 PR 생성]
```

---

## 7. 화면/컴포넌트 목록 (Component Inventory)

| 컴포넌트 ID | 컴포넌트명 | FEAT | 파일 위치 | 주요 기능 |
|------------|-----------|------|-----------|----------|
| C-01 | GLMClient | FEAT-1 | backend/ai/glm_client.py | GLM-4.7 API 호출 및 응답 처리 |
| C-02 | NewsRepository | FEAT-1 | backend/database/repository.py | DB 저장 (save_glm_analysis) |
| C-03 | newspoller | FEAT-1 | backend/news/poller.py | 뉴스 수집 및 GLMClient 호출 |
| C-04 | GLMAnalysisResult | FEAT-1 | backend/ai/glm_client.py | Pydantic 모델 (응답 스키마) |
| C-05 | FallbackHandler | FEAT-1 | backend/ai/glm_client.py | 로컬 LLM Fallback 처리 |

---

## 8. 데이터 플로우 다이어그램

```mermaid
graph LR
    A[newspoller] -->|뉴스 텍스트| B[GLMClient]
    B -->|API 요청| C[GLM-4.7 API]
    C -->|JSON 응답| B
    B -->|분석 결과| D[NewsRepository]
    D -->|SAVE| E[PostgreSQL]
    E -->|확인| F[(news_articles)]
    F -->|glm_analysis| G[War Room MVP]
```

---

## Decision Log 참조

| ID | 항목 | 선택 | 관련 흐름 |
|----|------|------|----------|
| D-06 | 사용 상황 | 실시간 뉴스 처리, DB 저장, 리포트 | 전체 여정 (1) |
| D-11 | 사용 환경 | newspoller와 연동 | newspoller 통합 (1, 8) |
| D-13 | 데이터 저장 | 기존 테이블에 JSON 컬럼 추가 | DB 플로우 (8) |
| D-18 | 검증 방식 | 실시간 뉴스 분석 테스트 | 개발자 플로우 (7) |
