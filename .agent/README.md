# AI Trading System - Agent Configuration

이 디렉토리는 AI 코딩 어시스턴트(Antigravity, Claude Code 등)를 위한 프로젝트 컨텍스트를 제공합니다.

## 🎯 프로젝트 개요

**AI Trading System**은 한국투자증권(KIS) API를 기반으로 한 자동 투자 시스템입니다.

### 기술 스택
- **Backend**: Python 3.11+, FastAPI, PostgreSQL
- **Frontend**: React 18, TypeScript, Recharts
- **Data Sources**: KIS API, Yahoo Finance, News APIs

### 주요 기능
1. 포트폴리오 관리 (KIS API 연동)
2. 배당 대시보드 (KIS + Yahoo Finance)
3. AI 기반 트레이딩 시그널
4. Deep Reasoning 분석

## 📚 필수 읽기 문서

### 1. 코딩 표준 (반드시 준수)
👉 **[coding_standards.md](./coding_standards.md)**

모든 코드는 다음을 포함해야 합니다:
- 📊 Data Sources: 어디서 데이터를 가져오는지
- 🔗 External Dependencies: 사용하는 외부 라이브러리
- 📤 API Endpoints: 제공하는 API (해당하는 경우)
- 🔄 Called By: 이 코드를 사용하는 곳

**예시:**
```python
"""
portfolio_router.py - 포트폴리오 조회 API

📊 Data Sources:
    - KIS API: 해외주식 잔고 조회 (TTTS3012R)
    - Yahoo Finance: 배당/섹터 정보 (Fallback)

🔗 External Dependencies:
    - fastapi: API 라우팅
    - yfinance: Yahoo Finance 데이터

📤 API Endpoints:
    - GET /api/portfolio: 전체 포트폴리오 조회
"""
```

### 2. 워크플로우
- `/add-docstrings`: 파일에 표준 주석 추가

## 🔑 중요 규칙

### 코드 작성 시
1. **파일 헤더 주석 필수** - Data Sources 명시
2. **Public 함수에 docstring 필수** - Args, Returns 포함
3. **API 호출 전 주석** - 어떤 endpoint 호출하는지
4. **복잡한 로직에 설명** - 비즈니스 의도 명시

### 데이터 소스 우선순위
1. **KIS API** (Primary) → `backend/trading/kis_client.py`
2. **Yahoo Finance** (Fallback) → `backend/data_sources/yahoo_finance.py`
3. **PostgreSQL** (Cache) → `backend/database/models.py`

### API 명명 규칙
- Router 파일: `{resource}_router.py`
- Endpoint: `/api/{resource}`
- Model: `{Resource}Response`

## 📂 프로젝트 구조

```
ai-trading-system/
├── backend/
│   ├── api/              # FastAPI routers
│   ├── brokers/          # KIS broker integration
│   ├── data_sources/     # External data (Yahoo Finance)
│   ├── trading/          # KIS API client
│   └── database/         # PostgreSQL models
├── frontend/
│   ├── src/
│   │   ├── pages/        # Main pages
│   │   └── components/   # Reusable components
└── .agent/               # AI configuration (이 디렉토리)
```

## 🚫 절대 하지 말 것

1. ❌ Data Source 주석 없이 외부 API 호출
2. ❌ Docstring 없는 public 함수
3. ❌ 하드코딩된 credentials (환경 변수 사용)
4. ❌ KIS API 호출 시 에러 처리 누락

## 📖 참고 문서

- `docs/KIS_Integration.md`: KIS API 통합 가이드
- `docs/PHASE_MASTER_INDEX.md`: 개발 단계별 문서
- `.env.example`: 필요한 환경 변수

## 🤖 AI 어시스턴트 가이드

### 코드 분석 시
1. 파일 헤더의 Data Sources 섹션 먼저 확인
2. 복잡한 코드는 docstring과 주석 참조
3. API 호출은 endpoint 주석 확인

### 새 기능 추가 시
1. `coding_standards.md` 템플릿 사용
2. 데이터 소스 명시
3. 워크플로우 문서 업데이트

### 버그 수정 시
1. 관련 Data Source 확인
2. API 응답 형식 검증
3. 에러 로깅 추가

---

**마지막 업데이트**: 2025-12-25
**담당자**: AI Trading System Team
