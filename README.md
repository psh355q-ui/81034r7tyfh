# 🤖💹 AI Trading System

**Multi-AI 기반 자동 주식 트레이딩 시스템**

> Claude, ChatGPT, Gemini를 활용한 앙상블 AI 투자 플랫폼

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-2.13+-orange.svg)](https://www.timescale.com/)
[![Redis](https://img.shields.io/badge/Redis-7+-red.svg)](https://redis.io/)

---

## 📊 프로젝트 개요

AI Trading System은 다중 AI 모델을 활용한 엔터프라이즈급 자동 트레이딩 플랫폼입니다. 뉴스 분석, 시그널 생성, 백테스팅, 리스크 관리, 실시간 모니터링을 통합하여 데이터 기반 투자 결정을 지원합니다.

### 🎯 핵심 가치

- **Multi-AI 앙상블**: Claude Sonnet 4.5, ChatGPT-4, Gemini Pro를 조합하여 더 정확한 시장 분석
- **실시간 뉴스 분석**: RSS 크롤링 → AI 분석 → 트레이딩 시그널 자동 생성
- **Point-in-Time 백테스팅**: Look-ahead bias 없는 정확한 전략 검증
- **2-Layer 캐싱**: Redis (L1) + TimescaleDB (L2)로 밀리초급 응답 속도
- **프로덕션 레디**: 모니터링, 알림, Circuit Breaker, 비용 추적 완비

---

## ✨ 주요 기능

### 📰 뉴스 기반 트레이딩 (Phase 1-10)
- **RSS 뉴스 크롤링**: 50+ 금융 뉴스 소스 실시간 수집
- **AI 뉴스 분석**:
  - 감성 분석 (긍정/부정/중립)
  - 시장 영향도 평가 (단기/장기)
  - 티커 관련성 스코어링
  - 리스크 카테고리 분류 (법적/규제/운영/재무/전략)
- **자동 시그널 생성**: 뉴스 → 트레이딩 시그널 변환
- **시그널 검증**: 백테스팅 기반 시그널 품질 검증
- **섹터 스로틀링**: 섹터별 포지션 제한 관리

### 🧠 Deep Reasoning (Phase 14)
- **3-Step Chain-of-Thought 추론**:
  - Step 1: 직접 영향 (Direct Impact) - 1차 수혜주 파악
  - Step 2: 간접 영향 (Secondary Impact) - 꼬리에 꼬리를 무는 연쇄 분석
  - Step 3: 전략적 결론 (Strategic Conclusion) - 숨은 수혜자 발굴
- **Hidden Beneficiary 탐색**:
  - 예시: "Google TPU v6" → 명백한 수혜주(GOOGL) + 숨은 수혜자(Broadcom - TPU 칩 설계사)
  - Knowledge Graph 기반 기업 관계 추적
- **Knowledge Graph**:
  - 파트너십, 경쟁, 공급망, 투자 관계 그래프 저장
  - 경로 탐색으로 N-hop 관계 발견
  - 실시간 웹 검색으로 관계 검증
- **Model-Agnostic AI Client**:
  - Gemini, Claude, GPT-4 통일 인터페이스
  - 역할별 AI 모델 배정 (Screener, Reasoning, Decision)
  - 비용 최적화: Gemini Flash(스크리닝) + Gemini Pro(추론)
- **A/B Backtest**: 키워드 기반 vs CoT+RAG 성과 비교

### 📊 Feature Store (Phase 2-4)
- **2-Layer 캐싱**:
  - L1: Redis (In-Memory, 15분 TTL)
  - L2: TimescaleDB (시계열 DB, 영구 저장)
- **실시간 Feature 계산**:
  - 기술적 지표: `ret_5d`, `ret_20d`, `vol_20d`, `mom_20d`
  - 펀더멘털: `pe_ratio`, `market_cap`, `dividend_yield`
  - AI 팩터: `non_standard_risk`, `management_credibility`
- **Cache Warmer**: 주요 종목 사전 캐싱으로 레이턴시 최소화
- **Vector Store**: SEC 문서 임베딩 & 시맨틱 검색

### 🧪 백테스팅 엔진 (Phase 10)
- **Signal Backtest Engine**: 뉴스 시그널 백테스팅
- **Point-in-Time 분석**: Look-ahead bias 제거
- **성과 지표**:
  - Sharpe Ratio, Sortino Ratio
  - Win Rate, Profit Factor
  - Maximum Drawdown
  - Cumulative Returns
- **최적화**: 그리드 서치로 파라미터 튜닝
- **비교 분석**: 여러 전략 성과 비교

### 📈 Advanced Analytics (Phase 15.5)
- **Performance Attribution**:
  - 전략별, 섹터별, AI 소스별, 포지션별, 시간별 성과 분해
  - PnL 기여도 분석
- **Risk Analytics**:
  - Value at Risk (VaR 95%, 99%)
  - Conditional VaR (CVaR/Expected Shortfall)
  - Maximum Drawdown & Recovery Period
  - Concentration Risk (HHI Index)
  - Correlation Matrix
  - Stress Testing
- **Trade Analytics**:
  - Win/Loss 패턴 분석
  - 실행 품질 (슬리피지, 체결 속도)
  - 보유 기간 최적화
  - AI 신뢰도 vs PnL 상관관계

### 🔔 알림 & 모니터링 (Phase 7-8)
- **Notification System**:
  - Telegram, Slack, Email 지원
  - 다중 채널 브로드캐스트
  - 우선순위 기반 라우팅
- **Health Monitoring**:
  - 시스템 health check
  - Component-level 상태 추적
  - 자동 복구 시도
- **Smart Alerts**:
  - 비정상 패턴 탐지
  - Circuit Breaker로 과부하 방지
  - 알림 중복 제거 & 그룹핑
- **비용 추적**:
  - AI API 호출 비용 실시간 추적
  - 일별/월별 사용량 리포트
  - 예산 알림

### 📋 리포팅 (Phase 15)
- **Daily/Weekly/Monthly Reports**:
  - 트레이딩 성과 요약
  - AI 사용 비용
  - 리스크 메트릭스
- **PDF Export**: 전문적인 리포트 생성
- **CSV Export**: 데이터 분석용 내보내기

### 🔐 인증 & 로깅 (Phase 7)
- **API Key 관리**: 계층적 권한 (Read/Write/Execute)
- **Audit Logging**: 모든 API 호출 추적
- **Structured Logging**: 카테고리별 로그 관리 (SYSTEM, API, TRADING, etc.)

### 🎨 프론트엔드 (Phase 15.5)
- **React + TypeScript + Tailwind CSS**
- **실시간 대시보드**: 포트폴리오, 시그널, 뉴스
- **Advanced Analytics UI**: 성과/리스크/트레이드 분석 시각화
- **CEO Analysis**: SEC 문서에서 CEO 발언 추출 & 분석
- **RSS Management**: 피드 관리 UI

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  React App   │  │  Dashboard   │  │  Analytics   │          │
│  │  (Port 3000) │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend Layer                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  21 API Routers: news, signals, backtest, reports, etc.   │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────┐ ┌────────┐ ┌──────────┐ ┌────────────────────────┐│
│  │ Auth   │ │ Alerts │ │ Metrics  │ │ Health Monitoring     ││
│  └────────┘ └────────┘ └──────────┘ └────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ News Analyzer│  │ Signal Gen   │  │ Backtest Eng │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Feature Store│  │ AI Ensemble  │  │ RAG Engine   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL   │  │ TimescaleDB  │  │ Redis Cache  │          │
│  │ (Main DB)    │  │ (Time Series)│  │ (L1 Cache)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Vector Store │  │ SQLite       │  │ File Storage │          │
│  │ (Embeddings) │  │ (RSS/Logs)   │  │ (PDFs/CSVs)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Claude API   │  │ ChatGPT API  │  │ Gemini API   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Yahoo Finance│  │ SEC EDGAR    │  │ FRED API     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ Telegram Bot │  │ Slack API    │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 프로젝트 구조

```
ai-trading-system/
├── backend/                      # FastAPI 백엔드
│   ├── main.py                   # 메인 애플리케이션
│   ├── auth.py                   # API 인증
│   ├── log_manager.py            # 구조화된 로깅
│   │
│   ├── api/                      # API 라우터 (21개)
│   │   ├── news_router.py
│   │   ├── signals_router.py
│   │   ├── backtest_router.py
│   │   ├── reports_router.py
│   │   ├── ai_review_router.py
│   │   ├── feeds_router.py
│   │   ├── logs_router.py
│   │   ├── notifications_router.py
│   │   ├── monitoring_router.py
│   │   ├── ceo_analysis_router.py
│   │   ├── forensics_router.py
│   │   ├── options_flow_router.py
│   │   ├── incremental_router.py
│   │   └── ...
│   │
│   ├── ai/                       # AI 모델 (17개 파일)
│   │   ├── trading_agent.py
│   │   ├── claude_client.py
│   │   ├── chatgpt_client.py
│   │   ├── gemini_client.py
│   │   ├── rag_enhanced_analysis.py
│   │   ├── market_regime.py
│   │   ├── analysis_validator.py
│   │   ├── ensemble_optimizer.py
│   │   └── ...
│   │
│   ├── data/                     # 데이터 관리 (42개 파일)
│   │   ├── news_models.py        # 뉴스 DB 모델
│   │   ├── news_analyzer.py
│   │   ├── rss_crawler.py
│   │   ├── sec_client.py
│   │   ├── sec_parser.py
│   │   ├── models/               # Pydantic 모델
│   │   ├── collectors/           # 데이터 수집
│   │   ├── feature_store/        # Feature Store
│   │   │   ├── store.py
│   │   │   ├── cache_layer.py
│   │   │   ├── features.py
│   │   │   └── ...
│   │   ├── vector_store/         # 벡터 DB
│   │   └── features/             # Feature 정의
│   │
│   ├── signals/                  # 시그널 생성
│   │   ├── news_signal_generator.py
│   │   ├── signal_validator.py
│   │   └── sector_throttling.py
│   │
│   ├── backtesting/              # 백테스팅 엔진
│   │   ├── signal_backtest_engine.py
│   │   ├── backtest_engine.py
│   │   ├── pit_backtest_engine.py
│   │   └── ...
│   │
│   ├── analytics/                # 고급 분석
│   │   ├── performance_attribution.py
│   │   ├── risk_analytics.py
│   │   └── trade_analytics.py
│   │
│   ├── notifications/            # 알림 시스템
│   │   ├── notification_manager.py
│   │   ├── telegram_notifier.py
│   │   ├── slack_notifier.py
│   │   └── sec_alerts.py
│   │
│   ├── monitoring/               # 모니터링
│   │   ├── metrics_collector.py
│   │   ├── health_monitor.py
│   │   ├── alert_manager.py
│   │   ├── circuit_breaker.py
│   │   └── cost_analytics.py
│   │
│   ├── reporting/                # 리포트 생성
│   ├── services/                 # 백그라운드 서비스
│   ├── core/                     # 코어 유틸리티
│   └── ...
│
├── frontend/                     # React 프론트엔드
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── AdvancedAnalytics.tsx
│   │   │   ├── Analysis.tsx
│   │   │   ├── CEOAnalysis.tsx
│   │   │   ├── Reports.tsx
│   │   │   ├── NewsAggregation.tsx
│   │   │   ├── RssFeedManagement.tsx
│   │   │   ├── AIReviewPage.tsx
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── Analytics/
│   │   │   │   ├── PerformanceAttribution.tsx
│   │   │   │   ├── RiskAnalytics.tsx
│   │   │   │   └── TradeAnalytics.tsx
│   │   │   ├── Layout/
│   │   │   └── common/
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── analyticsApi.ts
│   │   │   ├── reportsApi.ts
│   │   │   └── ...
│   │   └── ...
│   └── package.json
│
├── monitoring/                   # Prometheus & Grafana 설정
│   ├── prometheus/
│   └── grafana/
│
├── docker-compose.yml            # Docker 구성
├── .env                          # 환경 변수
├── requirements.txt              # Python 의존성
└── README.md                     # 이 파일
```

---

## 🚀 빠른 시작

### 필수 요구사항

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+

### 1. 저장소 클론 및 환경 설정

```bash
cd d:\code\ai-trading-system

# Python 가상환경 생성
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt

# 프론트엔드 의존성 설치
cd frontend
npm install
cd ..
```

### 2. 환경 변수 설정

`.env` 파일 생성:

```env
# AI API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Database
DATABASE_URL=postgresql+asyncpg://ai_trading_user:password@localhost:5432/ai_trading
TIMESCALE_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://localhost:6379/0

# Notification
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
SLACK_WEBHOOK_URL=...

# API
API_KEY=your_api_key_here
```

### 3. Docker 서비스 시작

```bash
docker-compose up -d

# 상태 확인
docker-compose ps
```

이 명령으로 다음 서비스가 시작됩니다:
- PostgreSQL + TimescaleDB (Port 5432)
- Redis (Port 6379)
- Prometheus (Port 9090)
- Grafana (Port 3001)
- MLflow (Port 5000)

### 4. 데이터베이스 초기화

```bash
# Analytics 테이블 생성
python init_analytics_db.py

# 샘플 데이터 생성 (선택사항)
python create_sample_data.py
```

### 5. 백엔드 실행

```bash
python start_backend.py
```

백엔드 서버가 `http://localhost:5000`에서 실행됩니다.

- API 문서: http://localhost:5000/docs
- Health Check: http://localhost:5000/health

### 6. 프론트엔드 실행

새 터미널에서:

```bash
cd frontend
npm run dev
```

프론트엔드가 `http://localhost:3000`에서 실행됩니다.

---

## 📊 주요 API 엔드포인트

### 뉴스 & 시그널
```http
GET  /news                          # 뉴스 목록
POST /news/analyze                  # 뉴스 AI 분석
GET  /signals                       # 트레이딩 시그널
POST /signals/generate              # 시그널 생성
```

### Deep Reasoning
```http
POST /reasoning/analyze             # 3-step 심층 추론 분석
GET  /reasoning/knowledge/{entity}  # 지식 그래프 관계 조회
GET  /reasoning/backtest            # A/B 백테스트 결과
```

### 백테스팅
```http
POST /backtest/run                  # 백테스트 실행
GET  /backtest/results              # 결과 조회
POST /backtest/optimize             # 파라미터 최적화
```

### 리포팅
```http
GET  /reports/daily                 # 일일 리포트
GET  /reports/weekly                # 주간 리포트
GET  /reports/monthly               # 월간 리포트
GET  /reports/advanced/performance-attribution  # 성과 귀속
GET  /reports/advanced/risk-metrics # 리스크 메트릭스
GET  /reports/advanced/trade-insights  # 트레이드 인사이트
```

### Feature Store
```http
POST /features                      # Feature 조회
GET  /features/health               # 캐시 상태
POST /features/warm                 # 캐시 워밍
```

### 모니터링
```http
GET  /health                        # 시스템 Health
GET  /metrics                       # Prometheus 메트릭스
GET  /alerts                        # 활성 알림
GET  /monitoring/cost               # 비용 추적
```

---

## 🔧 개발 환경 설정

### IDE 설정 (VSCode)

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": ".\\venv\\Scripts\\python.exe",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black"
}
```

### 코드 품질 도구

```bash
# Black formatting
pip install black
black backend/

# Flake8 linting
pip install flake8
flake8 backend/

# mypy type checking
pip install mypy
mypy backend/
```

---

## 📈 사용 예시

### 1. 뉴스 기반 자동 트레이딩

```python
# 백엔드에서 실행
from backend.signals.news_signal_generator import NewsSignalGenerator

generator = NewsSignalGenerator(db_session)

# 최근 뉴스에서 시그널 생성
signals = await generator.generate_signals_from_recent_news(hours=24)

for signal in signals:
    print(f"{signal.ticker}: {signal.action} (신뢰도: {signal.confidence})")
```

### 2. 백테스팅

```python
from backend.backtesting.signal_backtest_engine import SignalBacktestEngine

engine = SignalBacktestEngine()

result = await engine.run_backtest(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    initial_capital=100000,
    min_confidence=0.7
)

print(f"Sharpe Ratio: {result.sharpe_ratio}")
print(f"Win Rate: {result.win_rate}%")
print(f"Max Drawdown: {result.max_drawdown}%")
```

### 3. Advanced Analytics

```python
from backend.analytics.performance_attribution import PerformanceAttributionAnalyzer

analyzer = PerformanceAttributionAnalyzer(db_session)

# 전략별 성과 분석
attribution = await analyzer.analyze_strategy_attribution(
    start_date=date(2024, 11, 1),
    end_date=date(2024, 11, 30)
)

for strategy, metrics in attribution.items():
    print(f"{strategy}: PnL={metrics['total_pnl']}, Win Rate={metrics['win_rate']}")
```

---

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 커버리지 리포트
pytest --cov=backend tests/
```

---

## 📦 배포

### Docker로 전체 스택 배포

```bash
# 프로덕션 빌드
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose logs -f backend

# 스케일링
docker-compose up -d --scale backend=3
```

### 환경별 설정

- **개발**: `.env.development`
- **스테이징**: `.env.staging`
- **프로덕션**: `.env.production`

---

## 📚 문서

- [API 문서](http://localhost:5000/docs) - FastAPI Auto-generated
- [아키텍처 가이드](docs/architecture.md)
- [Feature Store 가이드](docs/feature-store.md)
- [백테스팅 가이드](docs/backtesting.md)
- [알림 설정 가이드](docs/notifications.md)

---

## 🛠️ 기술 스택

### 백엔드
- **Framework**: FastAPI 0.104+
- **AI**: Claude Sonnet 4.5, GPT-4, Gemini Pro
- **Database**: PostgreSQL 15, TimescaleDB 2.13
- **Cache**: Redis 7
- **Vector DB**: ChromaDB / Pinecone
- **Knowledge Graph**: 관계형 그래프 (PostgreSQL 기반)
- **Monitoring**: Prometheus, Grafana
- **Async**: asyncio, asyncpg, aiohttp

### 프론트엔드
- **Framework**: React 18, TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP**: Axios, React Query
- **Build**: Vite

### DevOps
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions (예정)
- **Logging**: Structured Logging (JSON)
- **Metrics**: Prometheus + Grafana

---

## 🐛 문제 해결

### 자주 발생하는 문제

#### 1. Import 오류
```bash
# backend/ 디렉토리를 Python 경로에 추가
export PYTHONPATH="${PYTHONPATH}:${PWD}"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%  # Windows CMD
$env:PYTHONPATH += ";$PWD"  # Windows PowerShell
```

#### 2. 데이터베이스 연결 오류
```bash
# Docker 컨테이너 상태 확인
docker-compose ps

# PostgreSQL 재시작
docker-compose restart timescaledb
```

#### 3. Redis 연결 오류
```bash
# Redis 재시작
docker-compose restart redis

# Redis CLI 접속 테스트
docker exec -it ai-trading-redis redis-cli ping
```

#### 4. Risk Analytics 데이터 부족 오류
```bash
# 더 많은 샘플 데이터 생성
python create_sample_data.py --days 180
```

---

## 🔐 보안

- **API 인증**: API Key 기반 인증
- **계층적 권한**: Read/Write/Execute
- **Audit Logging**: 모든 API 호출 기록
- **환경 변수**: 민감 정보 `.env`에 저장
- **HTTPS**: 프로덕션 환경 필수
- **Rate Limiting**: API 호출 제한

---

## 🤝 기여

기여는 언제나 환영합니다!

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📚 관련 문서

- [API Documentation](API_DOCUMENTATION.md) - 전체 API 엔드포인트 레퍼런스
- [Quick Start Guide](QUICKSTART.md) - 5분 만에 시작하기
- [Deep Reasoning Guide](docs/Phase14_DeepReasoning.md) - 심층 추론 전략 가이드
- [Master Guide](MASTER_GUIDE.md) - 전체 시스템 가이드

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

## 👥 팀

**AI Trading System Team**
- Email: support@ai-trading-system.com
- GitHub: [ai-trading-system](https://github.com/ai-trading-system)

---

## 🙏 감사의 글

이 프로젝트는 다음 오픈소스 프로젝트들을 활용합니다:

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [React](https://reactjs.org/)
- [TimescaleDB](https://www.timescale.com/)
- [Redis](https://redis.io/)
- [Prometheus](https://prometheus.io/)
- [Anthropic Claude](https://www.anthropic.com/)

---

## 📧 연락처

문의사항이 있으시면 이메일로 연락 주세요: support@ai-trading-system.com

---

**Built with ❤️ by AI Trading System Team**

**Version 1.1.0** | Last Updated: 2025-11-27 | Phase 14 Deep Reasoning Added
