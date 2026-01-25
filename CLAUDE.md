# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

AI Trading System은 **Claude, ChatGPT, Gemini를 결합한 멀티-AI 앙상블 자동 주식 트레이딩 플랫폼**입니다. "Antigravity Agentic Workflow"가 구현되어 있어, AI가 트레이딩 결정뿐만 아니라 개발 프로세스(TDD, 문서화, DB 관리)까지 주도적으로 관리합니다.

**핵심 아키텍처**: FastAPI 백엔드 + React 프론트엔드, PostgreSQL + TimescaleDB, Redis 캐싱, ChromaDB 벡터 저장소. 50개 이상의 금융 소스에서 뉴스를 수집하고, AI 분석을 통해 트레이딩 시그널을 생성하며, 브로커 API(KIS Broker/페이퍼 트레이딩)를 통해 주문을 실행하고 헌법적 규칙을 통해 리스크를 관리합니다.

## 필수 명령어

### 시스템 시작
```bash
# 전체 서비스 시작 (Docker + Backend + Frontend)
start_all.bat

# 백엔드만 시작 (포트 8001)
python scripts/start_backend.py

# 프론트엔드만 시작 (포트 3002)
cd frontend && npm run dev

# 시스템 상태 체크
0_시스템_체크.bat
```

### 데이터베이스 작업
```bash
# DB 마이그레이션 실행
1_DB_마이그레이션.bat

# 구조 맵 재생성 (개발 전 실행 권장)
python backend/utils/structure_mapper.py
```

### 테스트
```bash
# 루트 레벨 - 백엔드 테스트
npm run test:backend

# 프론트엔드 - Playwright E2E 테스트
cd frontend
npm run test:e2e           # E2E 테스트 실행
npm run test:e2e:ui        # UI 디버깅 모드
npm run test:e2e:debug     # 디버그 모드
```

### 데이터 수집 및 모니터링
```bash
# 데이터 수집 시작
3_데이터수집_시작.bat

# 모니터링 대시보드 열기
4_모니터링_대시보드.bat

# 품질 리포트 생성
5_품질리포트_생성.bat
```

### 프론트엔드 빌드
```bash
cd frontend
npm run build              # 프로덕션 빌드
npm run lint               # ESLint 검사
```

## 아키텍처 & 핵심 컴포넌트

### 의사결정 파이프라인: MVP War Room 패턴
시스템은 안전한 단방향 파이프라인을 구현합니다:
```
의사결정(War Room) → 검증(Order Validator) → 실행(Broker)
```

- **War Room MVP** (`backend/ai/mvp/war_room_mvp.py`): 뉴스, 마크로, 리스크, 트레이더 등 AI 에이전트들이 토론하고 투표로 트레이딩 결정
- **Order Validator** (`backend/services/order_validator.py`): 헌법적 규칙에 대해 주문 검증
- **Order Executor** (`backend/ai/order_execution/shadow_order_executor.py`): 브로커를 통해 검증된 주문 실행

### AI 에이전트 시스템
`backend/ai/`에 위치:

- **Debate Agents** (`backend/ai/debate/`): 다양한 분석 관점을 위한 특화 에이전트:
  - `news_agent.py` - 뉴스 분석
  - `macro_agent.py` - 거시경제 분석
  - `risk_agent.py` - 리스크 평가
  - `trader_agent.py` - 트레이딩 전략
  - `chip_war_agent.py` - 반도체 산업 분석
  - `sentiment_agent.py` - 시장 심리
  - `skeptic_agent.py` - 반대 관점

- **Consensus Engine** (`backend/ai/consensus/`): 구성 가능한 투표 규칙으로 에이전트 투표 집계

- **MVP Implementation** (`backend/ai/mvp/`): 프로덕션용 단순화된 에이전트

### 데이터베이스 아키텍처 (중요 규칙)

**절대 허용하지 않는 규칙 (ZERO TOLERANCE):**
1. **단일 진실 공급원**: `backend/database/models.py`가 DB 스키마를 정의하는 유일한 곳
2. **Repository Pattern 강제**: 애플리케이션 코드에 절대 원시 SQL을 작성하지 않음. 항상 `backend/database/repository.py`의 리포지토리 클래스 사용
3. **금지된 패턴**:
   - 직접 `psycopg2.connect()` 또는 `asyncpg.connect()` 호출 금지
   - 리포지토리 외부에서 `SELECT`/`INSERT`/`UPDATE` 문 금지
   - `backend.data.news_models` 임포트 금지 (삭제됨/레거시)
   - 뉴스/트레이딩 기능에 SQLite 사용 금지

주요 테이블:
- `news_articles` - 임베딩과 감성 분석이 포함된 크롤링 뉴스
- `trading_signals` - 생성된 시그널 (PRIMARY/HIDDEN/LOSER 타입)
- `backtest_runs` - 과거 성과 테스트
- `orders` - 실제 주문 실행
- `analysis_results` - AI 추론 결과

동기 DB 작업에는 `get_sync_session()`을 사용하세요.

### 뉴스 처리 파이프라인
```
크롤링 → 임베딩 → 분석 → 시그널 생성
```

- **News Crawler**: 50개 이상의 소스에서 수집
- **Embedding Engine** (`backend/ai/embedding_engine.py`): 시맨틱 검색을 위한 임베딩 생성
- **News Intelligence Analyzer** (`backend/ai/news_intelligence_analyzer.py`): 인사이트 추출
- **Trading Signals**: AI 합의를 기반으로 생성

### 프론트엔드 구조
`frontend/`에 위치:
- React 18 + TypeScript, Vite 빌드 도구
- TanStack Query로 서버 상태 관리
- Ant Design + Tailwind CSS로 UI 구현
- Recharts로 데이터 시각화
- 주요 페이지: 대시보드, 트레이딩 시그널, 뉴스 분석, 백테스팅

## 개발 워크플로우

### 환경설정 수정 원칙 (ZERO TOLERANCE)

**절대 허용하지 않는 규칙:**
1. **`.env` 파일 직접 수정 금지**: 사용자 개인 설정이므로 AI가 직접 수정 ❌
2. **`.env.example`만 수정**: 템플릿/가이드 제공용 ✅
3. **환경설정 변경 시**: `.env.example` 수정 후 사용자에게 적용 방법 안내
4. **API 키/비밀정보**: `.env` 파일 내용을 절대 로그에 출력하거나 요약하지 않음

**올바른 워크플로우:**
```
사용자 요청 → .env.example 수정 → 적용 방법 안내 → 사용자가 .env 직접 수정
```

### API 에러 처리 원칙 (GLM/Gemini/Anthropic)

**핵심 원칙: "잔액 부족" → 무조건 "Rate Limit" 문제로 연결**

**GLM 모델 업데이트 계획 (정기 검사):**
- **검사 주기**: 매주 또는 새로운 기능 추가 시
- **필수 확인 사이트**: https://z.ai/manage-apikey/rate-limits
- **확인 항목**:
  1. 현재 사용 중인 모델의 Concurrency Limit (QPS/TPM)
  2. 새로운 모델 출시 여부
  3. 기존 모델 deprecation 여부
  4. Rate Limit 변경 사항

**현재 GLM 모델 현황 (2026-01-17 기준):**
```
모델              | Concurrency | 속도      | 용도                 | 상태
-----------------|-------------|-----------|---------------------|--------
glm-4-plus       | 20          | Fast      | News Processing ✅ | 추천
glm-4-flash      | 20          | Fast      | General Use        | 대안
glm-4-flashx     | 20          | Very Fast | High Throughput     | 대안
glm-4.7          | 3           | Slower    | Deep Reasoning      | 한계 있음
glm-4.6v-flashx  | 3           | Very Fast | JSON Structuring    | 한계 있음
```

**모델 변경 시 체크리스트:**
1. ✅ https://z.ai/manage-apikey/rate-limits 확인
2. ✅ Concurrency Limit 확인 (뉴스 처리: 최소 20 이상 권장)
3. ✅ .env.example 업데이트
4. ✅ 사용자에게 .env 수정 방법 안내 (직접 수정 금지)
5. ✅ NEWS_GLM_RATE_LIMIT 계산:
   - 안전한 속도 = Concurrency Limit / 2
   - 예: glm-4-plus (Concurrency 20) → 안전 속도 = 10 req/sec → RATE_LIMIT = 0.1초
   - 권장: RATE_LIMIT = 0.3초 (3.3 req/sec, 保守的)

GLM API 에러 발생 시 다음 순서대로 분석 및 대응:

1. **에러 메시지 분석**:
   - `잔액 부족`, `余额不足`, `insufficient balance` → Rate Limit 문제로 해석
   - `429 Too Many Requests` → Rate Limit 문제
   - `timeout` → Rate Limit 문제일 가능성 높음

2. **자연스러운 생각의 흐름 (예시)**:
   ```
   사용자: "GLM API 잔액 부족 에러가 떠요"
   AI의 분석: "잔액 부족 메시지지만, 실제로는 Rate Limit 문제일 가능성이 높아요.
                Concurrency Limit 20을 초과했거나 요청 간격이 너무 짧을 수 있습니다.
                NEWS_GLM_RATE_LIMIT 값을 확인하고, 간격을 늘려보겠습니다."
   ```

3. **해결 방법 우선순위**:
   - **1순위**: `NEWS_GLM_RATE_LIMIT` 값 증가 (0.3 → 0.5 → 1.0)
   - **2순위**: 배치 크기 축소 (한 번에 처리하는 뉴스 수 감소)
   - **3순위**: MockGLMClient 사용 (API 호출 없이 테스트)
   - **최후**: API 충전 필요 (가장 마지막 단계)

4. **절대 하지 말아야 할 것**:
   - ❌ "API를 충전하세요"를 첫 번째 해결책으로 제시
   - ❌ 잔액 부족을 금전 문제로 단정 짓기
   - ❌ 사용자에게 바로 결제 페이지 안내

5. **올바른 응답 예시**:
   ```
   "에러 메시지는 '잔액 부족'으로 보이지만, GLM-4-Plus의 Concurrency Limit 20을
    초과했을 가능성이 높습니다. 현재 Rate Limit 설정을 확인하고 조정하겠습니다.

    현재 설정: NEWS_GLM_RATE_LIMIT=0.3 (초당 3.3건 요청)
    제안 설정: NEWS_GLM_RATE_LIMIT=0.5 (초당 2건 요청, 더 안정적)

    이것으로 해결되지 않으면 API 충전을 고려해보시겠습니다."
   ```

**기억할 것**: 사용자는 "잔액 부족"이라고 말하지만, 실제 문제는 90% 이상이 Rate Limit입니다.

### 컨텍스트 윈도우 제한 관리 (ZERO TOLERANCE)

**현재 모델 컨텍스트 제한 (GLM-4.7):**
- **표준 컨텍스트**: 200,000 토큰
- **최대 출력**: 128,000 토큰
- **로컬 실행 시**: 131,072 토큰 (vLLM/Transformers)

**토큰 사용량 현황 표시 (모든 응답 말미에 표시):**
```
📊 Messages: XX | Est. Tokens: ~XX,XXX | Since: [시작 시점]
```

**카운팅 규칙:**
- `/clear` 또는 `/compact` 실행 후부터 메시지 수 카운트 시작
- 새 대화창에서는 1부터 카운트
- 토큰 수는 메시지 수 × 평균 2,000토큰으로 추정
- 실제 제한 발생 시 사용자가 정확한 제한值 입력

**현재 설정:**
- 메시지 수: 0 (새로운 카운트 시작 필요)
- 추정 토큰: ~0
- 실제 제한: 미정 (사용자가 테스트 후 입력 예정)

**절대 허용하지 않는 규칙:**
1. **제한에 도달하면 즉시 조치**: "API Error: The model has reached its context window limit" 에러 발생 시 즉시 대응
2. **선제적 기록 저장**: 컨텍스트 사용량이 140K-160K 토큰 (70-80%)에 도달하면 미리 대화 기록 저장
3. **대화 정리 전 기록화**: `/clear` 또는 `/compact` 실행 전 반드시 세션 기록 저장

**컨텍스트 제한 관리 워크플로우:**

```
대화 진행 → 토큰 사용량 모니터링 → 140K (70%) 경고 → 160K (80%) 기록 저장 → 200K 제한 도달 시 clear/compact
```

**1. 선제적 모니터링 (대화 중):**
- 긴 파일 읽기나 대량 코드 수정 시 토큰 사용량에 주의
- 여러 파일을 동시에 수정할 때는 컨텍스트가 빠르게 증가
- IDE에서 열린 파일이 많을수록 컨텍스트 소비 증가

**2. 140K-160K (70-80%) 도달 시 조치:**
```bash
# 현재 상태 저장
git status
git diff --stat

# 세션 기록 문서 자동 생성
# 문서 형식: docs/YYMMDD_Context_Recording_Session.md
```

**3. 세션 기록 저장 필수 항목:**
- 현재 작업 중이던 기능/버그
- 수정된 파일 목록 (`git diff --stat`)
- 완료된 태스크 목록
- 진행 중이던 태스크 상태
- 다음 세션에서 계속해야 할 작업
- 관련 커밋 해시

**4. 제한 도달 시 즉시 조치:**
```bash
# 1순위: 세션 기록 저장 (위 항목들 포함)
# 2순위: /clear 실행 (가장 최근 메시지 유지)
# 또는 /compact 실행 (전체 대화 요약)
```

**5. 기록 저장 예시:**
```markdown
# 260118_Context_Recording_Session.md

**Date**: 2026-01-18
**Category**: Development Session
**Status**: In Progress

## Current Work
- 기능/버그 설명

## Modified Files
- file1.ts (+10, -5)
- file2.py (+100, -0)

## Completed Tasks
1. Task 1 완료
2. Task 2 완료

## In Progress Tasks
1. Task 3 (50% 완료)
2. Task 4 (시작 전)

## Next Steps
1. Task 3 계속
2. Task 4 시작
```

**6. 절대 하지 말아야 할 것:**
- ❌ 컨텍스트 제한 도달 시 `/clear` 먼저 실행 (기록 손실)
- ❌ 세션 기록 없이 대화 종료
- ❌ "기억 안 나요"라고 답변 (기록 저장 실패 의미)

### DB 스키마 변경 (`/db-schema-change` 사용)
데이터베이스 수정 시:
1. `backend/database/models.py`에서 기존 스키마 확인
2. 모델 변경 사항을 먼저 제안
3. `backend/database/migrations/`에 마이그레이션 스크립트 생성
4. 적용 전 로컬 테스트
5. 프로덕션 DB는 절대 직접 수정 금지

### 헌법 수정 (`/constitution-amendment` 사용)
핵심 규칙(리스크 한도, 손절 규칙)은 다음 필요:
- 엄격한 승인 프로세스
- 백테스트 검증
- 문서 업데이트

### 문서화 표준
- **파일 명명**: `YYMMDD_Category_Description.md` (예: `260114_Implementation_Feature.md`)
- **위치**: 적절한 하위 폴더와 함께 `docs/`

### 구조 맵 업데이트 (ZERO TOLERANCE)

**절대 허용하지 않는 규칙:**

모든 개발 작업 시 `structure-map.md` 업데이트 **필수**:

```bash
python backend/utils/structure_mapper.py
```

**업데이트 시점:**
1. **개발 시작 전**: 현재 구조 파악
2. **개발 완료 후**: 변경사항 반영 (커밋 전 필수!)
3. **파일/폴더 추가/삭제 시**: 즉시 업데이트

**워크플로우:**
```
개발 시작 → structure_mapper.py 실행 → 코드 작업 → structure_mapper.py 실행 → 커밋
```

**Note**: `docs/architecture/structure-map.md`는 자동 생성 파일입니다.
직접 수정하지 말고 항상 스크립트로 업데이트하세요.

### Git 커밋 (`/github-commit` 사용)
초급자(Main만)부터 고급(GitFlow)까지 수준별 가이드 제공

## 기술 스택

### 백엔드
- Python 3.11+, FastAPI
- AI: Anthropic (Claude), OpenAI (ChatGPT), Google (Gemini)
- Database: PostgreSQL 15+ with TimescaleDB
- Cache: Redis
- Vector Store: ChromaDB + pgvector
- ML: scikit-learn, sentence-transformers

### 프론트엔드
- React 18, TypeScript, Vite
- State: TanStack Query
- UI: Tailwind CSS, Ant Design, Recharts

### DevOps
- Git Hooks: Husky + commitlint
- Testing: Playwright (E2E)
- Monitoring: Prometheus 메트릭

## 중요 파일 위치

- **백엔드 모델**: `backend/database/models.py` (단일 진실 공급원)
- **리포지토리**: `backend/database/repository.py` (모든 DB 접근)
- **마이그레이션**: `backend/database/migrations/`
- **API 라우트**: `backend/api/`
- **AI 에이전트**: `backend/ai/debate/` 및 `backend/ai/mvp/`
- **프론트엔드**: `frontend/src/`
- **테스트**: `tests/` 및 `frontend/tests/e2e/`

## 환경 설정

1. 가상환경 생성: `python -m venv venv && .\venv\Scripts\activate`
2. 의존성 설치: `pip install -r requirements.txt`
3. 프론트엔드 설치: `cd frontend && npm install`
4. `.env` 파일 설정 (`.env.example` 참조)
5. 마이그레이션 실행: `1_DB_마이그레이션.bat`

## 빠른 참조

- **백엔드 포트**: 8001
- **프론트엔드 포트**: 3002
- **API 문서**: 백엔드 실행 시 사용 가능
- **구조 맵**: `docs/architecture/structure-map.md` (자동 생성)
- **빠른 시작 가이드**: `docs/guides/QUICK_START.md`
- **커서 규칙**: `.cursorrules` (중요한 DB 규칙 포함)

## Antigravity 통합

이 시스템은 자율 개발을 위한 Antigravity 에이전트 워크플로우를 구현합니다:
- TDD 강제 지원
- 자동 문서화 생성
- 자가 치유 및 학습 능력
- 지속적 통합/배포 파이프라인
