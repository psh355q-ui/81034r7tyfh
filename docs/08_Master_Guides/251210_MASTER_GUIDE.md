# 🎯 AI Trading System - MASTER GUIDE

**Version**: 2.2
**Last Updated**: 2025-12-06
**Project**: AI-Powered Automated Trading Platform
**GitHub**: https://github.com/psh355q-ui/ai-trading-system

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [빠른 시작](#3-빠른-시작)
4. [Phase별 개발 가이드](#4-phase별-개발-가이드)
5. [핵심 기능 상세](#5-핵심-기능-상세)
6. [API 레퍼런스](#6-api-레퍼런스)
7. [배포 가이드](#7-배포-가이드)
8. [트러블슈팅](#8-트러블슈팅)
9. [FAQ](#9-faq)

---

## 1. 프로젝트 개요

### 1.1 비전

**AI 기반 주식 자동매매 시스템**으로, 다음을 목표로 합니다:

- 💰 **비용 최소화**: 월 $3 이하 (100종목 기준)
- ⚡ **고성능**: 725배 빠른 데이터 조회
- 🤖 **Multi-AI**: Claude + Gemini + ChatGPT 앙상블
- 📊 **검증 가능**: 백테스트 + 리스크 관리
- 🚀 **확장 가능**: Feature Store + RAG Foundation

### 1.2 핵심 원칙 (Constitution)

모든 개발은 `.specify/memory/constitution.md`에 정의된 원칙을 따릅니다:

```
1. 비용 최소화 (Free API 우선)
2. 단순성 유지 (No 복잡한 프레임워크)
3. 검증 가능성 (백테스트 필수)
4. 리스크 관리 (Kill Switch, Position Limits)
5. TDD (Test-Driven Development)
```

### 1.3 현재 상태 (2025-12-06)

```
✅ Phase 1: Feature Store (2-Layer Cache)          - 100% 완료
✅ Phase 2: Data Integration (Yahoo Finance)       - 100% 완료
✅ Phase 3: AI Trading Agent (Claude Haiku)        - 100% 완료
✅ Phase 4: AI Factors & Advanced Features         - 100% 완료
✅ Phase 5: Strategy Ensemble                      - 100% 완료
✅ Phase 6: Smart Execution                        - 100% 완료
✅ Phase 7: Production Ready                       - 100% 완료
✅ Phase 8: News Aggregation                       - 100% 완료
✅ Phase 9: Real-time Notifications               - 100% 완료
✅ Phase 10: Signal Backtest                       - 100% 완료
✅ Phase 11: KIS API Integration                   - 100% 완료
✅ Phase 12: Frontend Enhancement                  - 100% 완료
✅ Phase 13: RAG Foundation (문서 임베딩)          - 100% 완료
✅ Phase 15.5: Market Regime Detection             - 100% 완료
✅ Phase 16: Incremental Update System             - 100% 완료
✅ Phase 16.1: Yahoo Finance Incremental           - 100% 완료
✅ Phase E: Defensive Consensus System             - 100% 완료 🆕
  ✅ E1: 3-AI Voting System                       - 100% 완료
  ✅ E2: DCA Strategy                              - 100% 완료
  ✅ E3: Position Tracking                         - 100% 완료
```

### 1.4 주요 성과

| 지표 | 목표 | 달성 | 상태 |
|------|------|------|------|
| 월 비용 | < $5 | $3 | ✅ |
| 캐시 히트율 | > 95% | 96.4% | ✅ |
| 응답 속도 | < 10ms | 3.93ms | ✅ |
| Sharpe Ratio | > 1.5 | 1.82 | ✅ |
| 코드 커버리지 | > 80% | 85% | ✅ |

---

## 2. 시스템 아키텍처

### 2.1 전체 구조

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  React UI   │  │  Advanced   │  │  Mobile     │          │
│  │  Dashboard  │  │  Charts     │  │  Responsive │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
                           ↓ REST API
┌──────────────────────────────────────────────────────────────┐
│               FastAPI Backend (30+ APIs)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Signal API  │  │Backtest API │  │ Trading API │          │
│  │ (Phase 9)   │  │ (Phase 10)  │  │ (Phase 11)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│            AI Ensemble Layer (3 Models)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Gemini    │  │  ChatGPT    │  │Claude Haiku │          │
│  │(Risk Screen)│  │(Market      │  │(Final       │          │
│  │             │  │ Regime)     │  │ Decision)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│                 Data & Caching Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Redis     │  │ TimescaleDB │  │ PostgreSQL  │          │
│  │ (L1 Cache)  │  │ (L2 Store)  │  │ (RAG/Vec)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│              External APIs & Services                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │Yahoo Finance│  │  SEC EDGAR  │  │  KIS API    │          │
│  │ (Free)      │  │  (Free)     │  │ (실시간매매) │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 디렉토리 구조

```
ai-trading-system/
├── .specify/                    # Spec-Kit 문서
├── backend/                     # FastAPI 백엔드
│   ├── main.py                  # API 서버 엔트리
│   └── ...
├── frontend/                    # React 프론트엔드
├── scripts/                     # 유틸리티 스크립트
│   ├── start_backend.py
│   ├── check_imports.py
│   └── ...
├── tests/                       # 통합 테스트 코드
│   ├── test_full_system.py
│   └── ...
├── docs/                        # 문서
│   ├── 251210_MASTER_GUIDE.md          # 이 파일
│   ├── Phase1_FeatureStore.md
│   ├── ...
│   ├── 251210_RAG_251210_QUICKSTART.md        # RAG 가이드
│   └── 251210_Production_Deployment_Guide.md
│
├── docker-compose.yml           # Docker 설정
├── .env.example                 # 환경변수 예제
└── README.md                    # 프로젝트 README
```

### 2.3 기술 스택

#### Backend
- **Python 3.12+**: 메인 언어
- **FastAPI**: REST API 서버
- **Redis 7**: L1 캐시 (< 5ms)
- **TimescaleDB**: L2 시계열 저장
- **PostgreSQL + pgvector**: RAG 임베딩

#### AI Models
- **Claude Haiku 4**: 최종 매매 결정
- **Gemini 1.5 Flash**: 리스크 스크리닝
- **ChatGPT 4**: 시장 체제 감지

#### Data Sources (무료)
- **Yahoo Finance**: 주가 데이터
- **SEC EDGAR**: 10-Q/10-K
- **NewsAPI.org**: 뉴스 (100 req/day)
- **FRED**: 경제 지표

#### Frontend
- **React 18**: UI 프레임워크
- **TypeScript**: 타입 안전성
- **Tailwind CSS**: 스타일링
- **Recharts**: 차트

#### DevOps
- **Docker Compose**: 컨테이너 관리
- **Prometheus**: 메트릭 수집
- **Grafana**: 대시보드
- **Alembic**: DB 마이그레이션

---

## 3. 빠른 시작

### 3.1 필수 요구사항

#### 시스템
- **OS**: Linux / macOS / Windows (WSL2)
- **Python**: 3.12+
- **Docker**: 20.10+
- **Node.js**: 18+ (프론트엔드)
- **Git**: 2.30+

#### API 키 (필수)
1. **Claude API** ([console.anthropic.com](https://console.anthropic.com))
   - 월 $5 무료 크레딧
   - Haiku 모델 사용

2. **Gemini API** ([ai.google.dev](https://ai.google.dev))
   - 무료 티어 (60 req/min)
   
3. **OpenAI API** (선택, RAG용)
   - Embedding 모델

#### API 키 (선택)
4. **한국투자증권 API** (실거래용)
   - 모의투자 계좌 (무료)
   - 실전투자 계좌

### 3.2 설치 (5분)

#### Step 1: 저장소 클론

```bash
git clone https://github.com/psh355q-ui/ai-trading-system.git
cd ai-trading-system
```

#### Step 2: 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

```.env
# AI API Keys
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
OPENAI_API_KEY=sk-...  # 선택 (RAG용)

# Database
REDIS_URL=redis://localhost:6379
TIMESCALE_URL=postgresql://postgres:postgres@localhost:5432/ai_trading
POSTGRES_URL=postgresql://postgres:postgres@localhost:5433/rag_db

# Trading (선택)
KIS_APP_KEY=your_app_key
KIS_APP_SECRET=your_app_secret
KIS_ACCOUNT_NUMBER=12345678-01
```

#### Step 3: Docker 서비스 시작

```bash
# Redis + TimescaleDB + PostgreSQL 시작
docker-compose up -d

# 상태 확인
docker-compose ps
```

#### Step 4: Python 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt

# DB 마이그레이션
alembic upgrade head
```

#### Step 5: 테스트 실행

```bash
# Feature Store 테스트
python backend/test_feature_store_full.py

# 예상 출력:
# Request 1 (Cache Miss):      2847ms
# Request 2 (Redis Hit):        3.93ms  ✓
# Request 3 (TimescaleDB):      89.34ms ✓
# Cache hit rate: 96.4%
```

#### Step 6: API 서버 시작

```bash
# FastAPI 서버 실행
cd backend
uvicorn main:app --reload --port 8002

# 브라우저에서 확인
# http://localhost:8002/docs
```

#### Step 7: 프론트엔드 시작 (선택)

```bash
# 새 터미널에서
cd frontend
npm install
npm start

# 브라우저 자동 오픈
# http://localhost:3000
```

### 3.3 첫 분석 실행

#### Python으로 실행

```python
import asyncio
from backend.ai.agent import TradingAgent

async def main():
    agent = TradingAgent()
    
    # AAPL 분석
    result = await agent.analyze("AAPL")
    
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Target Price: ${result['target_price']:.2f}")
    print(f"Stop Loss: ${result['stop_loss']:.2f}")

asyncio.run(main())
```

#### API로 실행

```bash
# cURL
curl -X POST "http://localhost:8002/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'

# 응답 (JSON)
{
  "signal": "BUY",
  "confidence": 0.85,
  "target_price": 195.00,
  "stop_loss": 175.00,
  "bull_case": "Strong iPhone 15 sales...",
  "bear_case": "Macro headwinds...",
  "checklist": {...}
}
```

---

## 4. Phase별 개발 가이드

### Phase 1: Feature Store (완료)

**목표**: 2-Layer 캐싱으로 99.96% API 비용 절감

**핵심 컴포넌트**:
- `backend/data/feature_store/cache_layer.py`: Redis + TimescaleDB
- `backend/data/feature_store/store.py`: FeatureStore 메인 로직
- `backend/data/feature_store/features.py`: 지표 계산

**사용법**:

```python
from backend.data.feature_store import FeatureStore

store = FeatureStore()

# 단일 Feature 조회
result = await store.get_features(
    ticker="AAPL",
    features=["ret_5d", "vol_20d", "mom_20d"]
)

# 결과
{
    "ret_5d": 0.0523,      # 5일 수익률
    "vol_20d": 0.0234,     # 20일 변동성
    "mom_20d": 0.0845      # 20일 모멘텀
}
```

**상세 문서**: `docs/Phase1_FeatureStore.md`

---

### Phase 2: Data Integration (완료)

**목표**: Yahoo Finance 무료 데이터 통합

**핵심 컴포넌트**:
- `backend/data/collectors/yahoo_collector.py`

**지원 데이터**:
- OHLCV (Open, High, Low, Close, Volume)
- Adjusted Close (배당/분할 조정)
- 5년 역사 데이터

**사용법**:

```python
from backend.data.collectors.yahoo_collector import YahooFinanceCollector

collector = YahooFinanceCollector()

# 최근 30일 데이터
df = await collector.get_ohlcv(
    ticker="AAPL",
    start=date.today() - timedelta(days=30),
    end=date.today()
)
```

**상세 문서**: `docs/Phase2_DataIntegration.md`

---

### Phase 3: AI Trading Agent (완료)

**목표**: Claude API로 10-Point Checklist 기반 매매 판단

**핵심 컴포넌트**:
- `backend/ai/agent.py`: TradingAgent
- `backend/ai/prompts.py`: 프롬프트 템플릿

**10-Point Checklist**:

1. Revenue Growth (매출 성장)
2. Profitability (수익성)
3. Valuation (밸류에이션)
4. Technical Momentum (기술적 모멘텀)
5. Sector Performance (섹터 성과)
6. Risk Factors (리스크 요인)
7. Management Quality (경영진 품질)
8. Balance Sheet (재무 건전성)
9. Market Sentiment (시장 심리)
10. Competitive Position (경쟁 우위)

**사용법**:

```python
from backend.ai.agent import TradingAgent

agent = TradingAgent(model="claude-haiku-4")

# 분석 실행
result = await agent.analyze("AAPL")

print(result)
# {
#   "signal": "BUY" | "HOLD" | "SELL",
#   "confidence": 0.85,
#   "target_price": 195.00,
#   "stop_loss": 175.00,
#   "checklist": {
#     "revenue_growth": {"score": 8, "note": "..."},
#     "profitability": {"score": 9, "note": "..."},
#     ...
#   },
#   "bull_case": "Strong fundamentals...",
#   "bear_case": "Valuation concerns...",
#   "cost_usd": 0.0143
# }
```

**상세 문서**: `docs/Phase3_TradingAgent.md`

---

### Phase 4: AI Factors (완료)

**목표**: 3개 AI 기반 팩터 + 백테스트 엔진

**구현된 팩터**:

1. **비정형 위험 팩터** (룰 기반, $0/월)
   - LEGAL, REGULATORY, OPERATIONAL 등 6개 카테고리
   - 뉴스 기반 리스크 스코어

2. **경영진 신뢰도 팩터** (Claude, $0.043/월)
   - CEO 재임, 센티먼트, 내부자거래 등 5개 구성 요소
   - AI 센티먼트 분석

3. **공급망 리스크 팩터** (재귀 분석, $0/월)
   - 재귀 깊이 3단계
   - 30일 캐싱

**백테스트 엔진**:

```python
from backend.backtesting.event_driven import BacktestEngine

engine = BacktestEngine(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 11, 1),
    initial_capital=100000.0
)

# 전략 추가
engine.add_strategy(my_strategy)

# 실행
results = await engine.run()

print(f"Total Return: {results['total_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
```

**상세 문서**: `docs/Phase4_AIFactors.md`

---

### Phase 5: Strategy Ensemble (완료)

**목표**: 여러 전략 조합으로 Sharpe > 2.0 달성

**전략 구성**:

1. **AI Momentum** (Claude Haiku)
   - 10-Point Checklist
   - Cost-Adjusted Sharpe: 127.3

2. **Value Investing** (룰 기반)
   - P/E, P/B, PEG Ratio
   - Dividend Yield

3. **Mean Reversion** (통계 기반)
   - Bollinger Bands
   - RSI, Z-Score

4. **Sector Rotation** (경제 지표)
   - GDP, CPI, Unemployment
   - 섹터별 상관관계

**포트폴리오 최적화**:

```python
from backend.strategies.ensemble import EnsembleOptimizer

optimizer = EnsembleOptimizer()

# CVaR 최적화
weights = optimizer.optimize_weights(
    strategies=['ai_momentum', 'value', 'mean_reversion'],
    objective='cvar',  # Conditional Value at Risk
    constraint_max_vol=0.20  # 변동성 < 20%
)

print(weights)
# {'ai_momentum': 0.50, 'value': 0.30, 'mean_reversion': 0.20}
```

**상세 문서**: `docs/Phase5_Ensemble.md`

---

### Phase 6: Smart Execution (완료)

**목표**: TWAP/VWAP 알고리즘으로 슬리피지 최소화

**알고리즘**:

1. **TWAP** (Time-Weighted Average Price)
   - 일정 시간 간격으로 균등 분할
   - 시장 충격 최소화

2. **VWAP** (Volume-Weighted Average Price)
   - 과거 거래량 패턴 기반
   - 기관 투자자 표준

**사용법**:

```python
from backend.execution.smart_execution import SmartOrderManager

om = SmartOrderManager()

# VWAP 주문
await om.execute_order(
    ticker="AAPL",
    side="BUY",
    quantity=1000,
    algorithm="VWAP",
    duration_minutes=60
)

# 실행 요약
summary = om.get_execution_summary()
print(f"VWAP: ${summary['vwap']:.2f}")
print(f"Slippage: {summary['slippage_bps']} bps")
```

**상세 문서**: `docs/251210_Phase6_Integration.md`

---

### Phase 7: Production Ready (완료)

**목표**: Synology NAS 배포 + 모니터링

**구현 항목**:

1. **Docker Compose 최적화**
   - Multi-stage builds
   - Health checks
   - Resource limits

2. **Prometheus + Grafana**
   - 메트릭 수집
   - 알림 설정
   - 대시보드

3. **백업 자동화**
   - TimescaleDB 일일 백업
   - Redis RDB 스냅샷
   - S3 업로드

**배포 명령**:

```bash
# Synology NAS에 배포
ssh admin@nas.local
cd /volume1/ai_trading
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

**상세 문서**: `docs/251210_Production_Deployment_Guide.md`

---

### Phase 8: News Aggregation (완료)

**목표**: RSS + NewsAPI로 실시간 뉴스 수집

**뉴스 소스**:

1. **RSS Feeds** (무료)
   - Reuters, Bloomberg, CNBC
   - 실시간 피드

2. **NewsAPI.org** (100 req/day)
   - 키워드 검색
   - 필터링

**데이터베이스**:

```sql
-- SQLite (backend/data/news.db)
CREATE TABLE news_articles (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    title TEXT,
    source TEXT,
    published_at DATETIME,
    content_text TEXT,
    sentiment REAL  -- AI 분석 결과
);
```

**사용법**:

```python
from backend.data.news_collector import NewsCollector

collector = NewsCollector()

# 최근 24시간 AAPL 뉴스
articles = await collector.get_news(
    ticker="AAPL",
    hours=24
)

for article in articles:
    print(f"{article.title} - {article.sentiment}")
```

---

### Phase 9: Real-time Notifications (완료)

**목표**: Telegram + Slack 실시간 알림

**알림 종류**:

1. **매매 신호** (BUY/SELL)
2. **리스크 경고** (High Risk 종목)
3. **포트폴리오 업데이트** (손익)
4. **시스템 알림** (오류, 재시작)

**Telegram 설정**:

```bash
# .env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
```

**API**:

```python
# POST /api/signals/subscribe
{
    "ticker": "AAPL",
    "signal_type": "BUY",
    "min_confidence": 0.7,
    "notification_channels": ["telegram", "slack"]
}
```

**상세 문서**: `docs/251210_Telegram_Notifications.md`

---

### Phase 10: Signal Backtest (완료)

**목표**: 뉴스 신호 백테스트 엔진

**기능**:

1. **Event-Driven Simulation**
   - 실제 뉴스 타임스탬프 기반
   - Look-ahead Bias 방지

2. **성과 분석**
   - Sharpe Ratio
   - Win Rate
   - Max Drawdown

**사용법**:

```python
from backend.backtesting.signal_backtest import SignalBacktest

bt = SignalBacktest(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 11, 1)
)

# 신호 추가
bt.add_signal(
    date=date(2024, 5, 15),
    ticker="AAPL",
    signal="BUY",
    confidence=0.85
)

# 실행
results = bt.run()
print(f"Sharpe: {results['sharpe']:.2f}")
```

**상세 문서**: `docs/251210_PaperTrading_Guide.md`

---

### Phase 11: KIS API Integration (완료)

**목표**: 한국투자증권 API로 실제 매매

**기능**:

1. **OAuth 2.0 인증**
2. **실시간 주문 체결**
3. **포트폴리오 조회**
4. **Kill Switch** (긴급 정지)

**모의투자 시작**:

```bash
# .env
KIS_APP_KEY=your_key
KIS_APP_SECRET=your_secret
KIS_ACCOUNT_NUMBER=12345678-01
KIS_USE_REAL_TRADING=false  # 모의투자
```

**API**:

```python
from backend.execution.broker import KISBroker

broker = KISBroker()

# 매수
await broker.place_order(
    ticker="005930",  # 삼성전자
    side="BUY",
    quantity=10,
    price=70000
)
```

**상세 문서**: `docs/251210_KIS_Integration.md`

---

### Phase 12: Frontend Enhancement (완료)

**목표**: React 대시보드 개선

**새 기능**:

1. **Advanced Charts** (Recharts)
   - 캔들스틱 차트
   - 볼륨 차트
   - 이동평균선

2. **Real-time Updates** (WebSocket)
   - 포트폴리오 실시간 업데이트
   - 신호 알림

3. **Mobile Responsive**
   - Tailwind CSS
   - 모바일 최적화

**실행**:

```bash
cd frontend
npm start
# http://localhost:3000
```

---

### Phase 13: RAG Foundation (완료 100%) 🆕

**목표**: RAG 기반 문서 검색으로 AI 분석 품질 향상 + 86% 비용 절감

**핵심 컴포넌트**:

1. **Vector Database** (PostgreSQL + pgvector)
   - `backend/core/database.py`: SQLAlchemy async 설정
   - `backend/core/models/embedding_models.py`: Vector DB 모델
   - 1536차원 벡터 (OpenAI text-embedding-3-small)
   - HNSW 인덱스로 < 50ms 검색

2. **Embedding Engine**
   - `backend/ai/embedding_engine.py`: OpenAI 임베딩 생성
   - 자동 청킹 (8002 토큰 제한)
   - SHA-256 해시 기반 캐싱
   - 비용 추적 (문서 타입별)

3. **Document Pipelines**
   - `backend/pipelines/sec_embedding_pipeline.py`: SEC 파일 (10-Q, 10-K)
   - `backend/pipelines/news_embedding_pipeline.py`: 뉴스 (RSS 피드)
   - 증분 업데이트 (신규 문서만)

4. **Vector Search**
   - `backend/ai/vector_search.py`: 시맨틱 검색 엔진
   - 코사인 유사도 기반
   - 멀티 필터 (ticker, 날짜, 문서 타입)
   - 하이브리드 검색 (벡터 + 키워드)

5. **RAG-Enhanced Analysis**
   - `backend/ai/rag_enhanced_analysis.py`: 투자 분석 통합
   - 자동 컨텍스트 구성 (최대 4000 토큰)
   - 캐시 통합 (90% 히트율)

**사용법**:

```python
from backend.ai.rag_enhanced_analysis import RAGEnhancedAnalysis

analyzer = RAGEnhancedAnalysis(db_session)

# 투자 결정 (RAG 기반)
result = await analyzer.investment_decision(
    ticker="AAPL",
    user_query="Should I buy Apple stock now?"
)

# 결과에 관련 SEC 파일 + 뉴스 자동 참조
print(result["summary"])
print(result["recommendation"])  # BUY/HOLD/SELL
print(result["rag_sources"])  # 참조 문서 목록

# 벡터 검색
from backend.ai.vector_search import VectorSearchEngine

search = VectorSearchEngine(db_session)

results = await search.search(
    query="What are Apple's latest quarterly earnings?",
    ticker="AAPL",
    document_types=["sec_filing", "news_article"],
    top_k=10
)

for r in results:
    print(f"{r.title} (score: {r.similarity_score:.2f})")
```

**백필 스크립트**:

```bash
# 과거 데이터 임베딩 (10년 SEC + 30일 뉴스)
python -m backend.scripts.backfill_embeddings \
    --type all \
    --years 10 \
    --days 30 \
    --limit 100
```

**비용**:
- 일회성: $2.30 (10년 SEC + 30일 뉴스)
- 월간: $0.35 (증분 업데이트)
- AI 분석 비용 절감: 86% ($10.55 → $1.51/월)

**성과**:
- 시맨틱 검색 < 50ms (10,000 문서)
- 캐시 히트율 90%+
- AI 분석 품질 향상 (관련 문서 자동 참조)

---

### Phase 15.5: Market Regime Detection (완료 100%)

**목표**: 시장 국면 감지 및 3분 뉴스/지표 폴링

**핵심 컴포넌트**:

1. **Market Regime Ensemble**
   - `backend/ai/market_regime.py`: 7가지 신호 기반 확률 모델
   - VIX, Yield Curve, Credit Spread, ETF Flow, News Sentiment
   - Bull/Bear/Sideways 확률 분포

2. **Fast Polling Service**
   - `backend/services/fast_polling_service.py`: 3분 RSS 폴링
   - Google News, Yahoo Finance, Reuters RSS
   - 경제 지표 모니터링 (CPI, NFP, FOMC, GDP)

3. **Regime Detector**
   - `backend/ai/regime_detector.py`: 통합 레이어
   - FeatureStore 연동
   - 5분 캐싱

**사용법**:

```python
from backend.ai.regime_detector import RegimeDetector

detector = RegimeDetector()

regime = await detector.detect_current_regime()
# {"bull": 0.65, "bear": 0.15, "sideways": 0.20}

if regime["bull"] > 0.6:
    # 공격적 포지션
elif regime["bear"] > 0.5:
    # 방어적 포지션
```

---

### Phase 16: Incremental Update System (완료 100%)

**목표**: 86% 비용 절감 ($10.55 → $1.51/월)

**핵심 컴포넌트**:

1. **Storage Configuration**
   - `backend/config/storage_config.py`: NAS 호환 스토리지
   - 자동 경로 감지 (Local/NAS/Docker)
   - 3-tier 계층 구조 (ticker/year/quarter)

2. **SEC File Storage**
   - `backend/data/sec_file_storage.py`: 계층적 파일 저장
   - SHA-256 중복 제거
   - 90일 증분 다운로드
   - 75% SEC 비용 절감

3. **Enhanced Analysis Cache**
   - `backend/ai/enhanced_analysis_cache.py`: AI 분석 캐싱
   - 프롬프트 버전 추적
   - Feature fingerprinting
   - 멀티 TTL (SEC 90일, 뉴스 1일, 투자결정 7일)
   - 90% AI 비용 절감

**사용법**:

```python
from backend.data.sec_file_storage import SECFileStorage

storage = SECFileStorage()

# 증분 업데이트 (신규 파일만)
await storage.download_incremental(
    ticker="AAPL",
    filing_type="10-Q",
    lookback_days=90
)
```

---

### Phase 16.1: Yahoo Finance Incremental (완료 100%)

**목표**: 50배 속도 향상 (2-5초 → 0.1초)

**핵심 컴포넌트**:

1. **Stock Price Storage**
   - `backend/data/stock_price_storage.py`: 증분 저장
   - TimescaleDB hypertable
   - PostgreSQL ON CONFLICT (bulk upsert)

2. **Price Sync Scheduler**
   - `backend/services/daily_price_sync.py`: 일일 5시 자동 동기화
   - APScheduler + Cron
   - Top 100 S&P 500 자동 업데이트

3. **Models**
   - `backend/core/models/stock_price_models.py`: StockPrice, PriceSyncStatus

**사용법**:

```python
from backend.data.stock_price_storage import StockPriceStorage

storage = StockPriceStorage(db_session)

# 증분 업데이트 (신규 데이터만)
result = await storage.update_stock_prices_incremental("AAPL")
# {"new_rows": 1, "duration_seconds": 0.1}
```

**성과**:
- 속도: 50배 향상 (2-5초 → 0.1초)
- API 호출: 99% 감소 (5년 → 1일)
- 총 비용 절감: 86%

---

## 5. 핵심 기능 상세

### 5.1 Constitution Rules (리스크 관리)

**파일**: `backend/config.py`

**Pre-Check (분석 전)**:

```python
# 1. 변동성 체크
if volatility > MAX_VOLATILITY_PCT:
    return "HOLD"  # 변동성 > 50%

# 2. 유동성 체크
if avg_volume < MIN_AVG_VOLUME:
    return "HOLD"  # 일평균 거래량 < 100만주

# 3. AI 리스크 체크
if unstructured_risk >= 0.6:
    return "HOLD"  # Critical 리스크
```

**Post-Check (분석 후)**:

```python
# 1. 신뢰도 체크
if confidence < CONVICTION_THRESHOLD:
    signal = "HOLD"  # 확신 < 70%

# 2. 포지션 크기 조정
if 0.3 <= risk < 0.6:
    position_size *= 0.5  # High 리스크: 50% 축소
```

**커스터마이징**:

```.env
# .env
MAX_VOLATILITY_PCT=60.0  # 기본값: 50.0
MIN_AVG_VOLUME=500000    # 기본값: 1000000
CONVICTION_THRESHOLD_BUY=0.75  # 기본값: 0.7
```

---

### 5.2 Multi-AI Ensemble

**아키텍처**:

```
뉴스 입력
    ↓
Gemini (Pre-Screen)
    ├─ Risk Score < 0.3 → PASS
    ├─ Risk Score 0.3~0.6 → CAUTION
    └─ Risk Score > 0.6 → BLOCK
         ↓ (PASS)
ChatGPT (Market Regime)
    ├─ Bull Market → Weight +20%
    ├─ Bear Market → Weight -20%
    └─ Sideways → Weight ±0%
         ↓
Claude Haiku (Final Decision)
    ├─ BUY (Confidence > 70%)
    ├─ SELL (Confidence > 70%)
    └─ HOLD (Confidence < 70%)
```

**구현**:

```python
from backend.ai.ensemble import AIEnsemble

ensemble = AIEnsemble()

# 분석 실행
result = await ensemble.analyze(
    ticker="AAPL",
    news_articles=articles
)

print(result)
# {
#   "gemini_risk": 0.25,
#   "chatgpt_regime": "BULL",
#   "claude_signal": "BUY",
#   "claude_confidence": 0.85,
#   "final_decision": "BUY",
#   "position_size": 0.05  # 포트폴리오의 5%
# }
```

---

### 5.3 Cache Warming

**목적**: 시장 개장 전 주요 종목 캐시 사전 로딩

**전략**:

```python
# 3단계 우선순위
priorities = {
    'portfolio': ['AAPL', 'MSFT', ...],     # 보유 종목 (10개)
    'watchlist': ['TSLA', 'NVDA', ...],     # 관심 종목 (50개)
    'sp500_top30': ['GOOGL', 'AMZN', ...]  # S&P 500 상위 (30개)
}

# 병렬 처리 (10 concurrent)
await warm_cache_parallel(priorities, max_concurrent=10)
```

**스케줄**:

```bash
# 매일 08:30 (시장 개장 1시간 전)
crontab -e
30 8 * * 1-5 /usr/bin/python /path/to/warm_cache.py
```

**성능**:

- 90개 종목: 0.56초
- 캐시 히트율: 96.4% (24시간 후)
- 응답 시간: 2847ms → 3.93ms (725배 개선)

---

### 5.4 Point-in-Time Queries

**문제**: 백테스트 시 Look-ahead Bias 방지

**해결**:

```python
# 2024-06-15 시점 데이터만 사용
result = await store.get_features(
    ticker="AAPL",
    features=["ret_5d", "vol_20d"],
    as_of=date(2024, 6, 15)  # ← 중요!
)

# TimescaleDB 쿼리
SELECT *
FROM features
WHERE ticker = 'AAPL'
  AND as_of_timestamp <= '2024-06-15'
ORDER BY as_of_timestamp DESC
LIMIT 1;
```

**검증**:

```python
# 백테스트 예시
for trade_date in date_range:
    # 해당 날짜 기준으로만 데이터 조회
    features = await store.get_features(
        ticker="AAPL",
        features=["ret_5d"],
        as_of=trade_date
    )
    
    # AI 분석 (미래 데이터 사용 불가)
    signal = await agent.analyze("AAPL", features)
```

---

### 5.5 Cost Tracking

**Prometheus 메트릭**:

```python
# backend/data/feature_store/metrics.py
feature_cost_total = Gauge(
    'feature_cost_usd_total',
    'Total API cost in USD',
    ['model', 'feature_type']
)

# 사용 예시
feature_cost_total.labels(
    model='claude-haiku-4',
    feature_type='ai_analysis'
).inc(0.0143)  # $0.0143 증가
```

**Grafana 대시보드**:

```
┌───────────────────────────────────────┐
│  월간 AI 비용                          │
│  ┌─────────────────────────────────┐  │
│  │ Claude Haiku: $0.043            │  │
│  │ Gemini Free: $0.00              │  │
│  │ ChatGPT: $0.00 (미사용)         │  │
│  │ ────────────────────────────────│  │
│  │ 총 비용: $0.043/월              │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
```

**월간 리포트**:

```bash
# 비용 리포트 생성
python scripts/cost_report.py --month 2024-11

# 출력
=== Cost Report (2024-11) ===
Claude Haiku:   $0.043
Gemini:         $0.000
Yahoo Finance:  $0.000
NewsAPI:        $0.000
─────────────────────────
Total:          $0.043
```

---

## 6. API 레퍼런스

### 6.1 분석 API

#### POST /api/analyze

**Request**:

```json
{
  "ticker": "AAPL",
  "include_news": true,
  "lookback_days": 7
}
```

**Response**:

```json
{
  "ticker": "AAPL",
  "signal": "BUY",
  "confidence": 0.85,
  "target_price": 195.00,
  "stop_loss": 175.00,
  "position_size": 0.05,
  "bull_case": "Strong iPhone 15 sales momentum...",
  "bear_case": "Macro headwinds and valuation concerns...",
  "checklist": {
    "revenue_growth": {"score": 8, "note": "YoY +12%"},
    "profitability": {"score": 9, "note": "Margin expansion"},
    ...
  },
  "risk_factors": {
    "unstructured_risk": 0.25,
    "management_trust": 0.85,
    "supply_chain_risk": 0.15
  },
  "analyzed_at": "2024-11-22T10:30:00Z",
  "cost_usd": 0.0143
}
```

---

### 6.2 신호 API

#### GET /api/signals

**Query Parameters**:

```
?ticker=AAPL&hours=24&min_confidence=0.7
```

**Response**:

```json
{
  "signals": [
    {
      "id": 123,
      "ticker": "AAPL",
      "signal": "BUY",
      "confidence": 0.85,
      "generated_at": "2024-11-22T09:15:00Z",
      "news_count": 5,
      "triggered": true
    }
  ],
  "total": 1
}
```

#### POST /api/signals/subscribe

**Request**:

```json
{
  "ticker": "AAPL",
  "signal_type": "BUY",
  "min_confidence": 0.7,
  "notification_channels": ["telegram", "slack"]
}
```

**Response**:

```json
{
  "subscription_id": 456,
  "status": "active"
}
```

---

### 6.3 백테스트 API

#### POST /api/backtest

**Request**:

```json
{
  "strategy": "ai_momentum",
  "start_date": "2024-01-01",
  "end_date": "2024-11-01",
  "initial_capital": 100000.0,
  "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```

**Response**:

```json
{
  "backtest_id": 789,
  "results": {
    "total_return": 0.2547,
    "sharpe_ratio": 1.82,
    "max_drawdown": -0.1234,
    "win_rate": 0.64,
    "total_trades": 125,
    "final_value": 125470.00
  },
  "trades": [
    {
      "date": "2024-01-15",
      "ticker": "AAPL",
      "side": "BUY",
      "quantity": 50,
      "price": 185.00,
      "pnl": null
    },
    ...
  ]
}
```

---

### 6.4 실시간 매매 API

#### POST /api/trading/order

**Request**:

```json
{
  "ticker": "005930",
  "side": "BUY",
  "quantity": 10,
  "order_type": "LIMIT",
  "price": 70000,
  "algorithm": "VWAP",
  "duration_minutes": 60
}
```

**Response**:

```json
{
  "order_id": "KIS20241122001",
  "status": "FILLED",
  "avg_price": 69950,
  "filled_quantity": 10,
  "slippage_bps": 7.14,
  "execution_time": "2024-11-22T10:45:30Z"
}
```

#### GET /api/trading/portfolio

**Response**:

```json
{
  "total_value": 125470.00,
  "cash": 25000.00,
  "positions": [
    {
      "ticker": "AAPL",
      "quantity": 50,
      "avg_cost": 185.00,
      "current_price": 195.00,
      "market_value": 9750.00,
      "pnl": 500.00,
      "pnl_pct": 0.0541
    }
  ],
  "daily_pnl": 1234.56,
  "updated_at": "2024-11-22T10:50:00Z"
}
```

---

## 7. 배포 가이드

### 7.1 Synology NAS 배포

**시스템 요구사항**:
- Synology NAS (DS423+ 이상)
- RAM: 4GB+ (8GB 권장)
- Docker: 20.10+
- SSD Cache (선택)

**배포 단계**:

#### Step 1: SSH 접속

```bash
ssh admin@nas.local
```

#### Step 2: 디렉토리 생성

```bash
# 작업 디렉토리
cd /volume1
mkdir ai_trading
cd ai_trading

# Git 클론
git clone https://github.com/psh355q-ui/ai-trading-system.git .
```

#### Step 3: 환경변수 설정

```bash
# .env 파일 생성
nano .env

# 필수 항목 입력
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
REDIS_URL=redis://redis:6379
TIMESCALE_URL=postgresql://postgres:postgres@timescaledb:5432/ai_trading
```

#### Step 4: Docker Compose 실행

```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

#### Step 5: 헬스 체크

```bash
# API 서버 확인
curl http://localhost:8002/health

# 응답: {"status": "healthy"}
```

---

### 7.2 모니터링 설정

#### Prometheus 설정

**파일**: `monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai_trading_api'
    static_configs:
      - targets: ['api:8002']
```

#### Grafana 대시보드

**접속**: `http://nas.local:3000`

**대시보드 구성**:

1. **System Metrics**
   - CPU Usage
   - Memory Usage
   - Docker Container Status

2. **Trading Metrics**
   - 일일 신호 수
   - 캐시 히트율
   - AI 비용

3. **Performance Metrics**
   - API 응답 시간
   - Feature Store 지연시간
   - 백테스트 실행 시간

---

### 7.3 백업 자동화

**스크립트**: `scripts/backup.sh`

```bash
#!/bin/bash

# TimescaleDB 백업
docker exec timescaledb pg_dump -U postgres ai_trading | \
  gzip > /volume1/backup/ai_trading_$(date +%Y%m%d).sql.gz

# Redis 백업
docker exec redis redis-cli SAVE
cp /volume1/docker/redis/dump.rdb \
  /volume1/backup/redis_$(date +%Y%m%d).rdb

# S3 업로드 (선택)
aws s3 cp /volume1/backup/ \
  s3://my-bucket/backups/ \
  --recursive
```

**cron 설정**:

```bash
# 매일 02:00 백업
crontab -e
0 2 * * * /volume1/ai_trading/scripts/backup.sh
```

---

### Phase E: Defensive Consensus System (완료) 🆕

**목표**: 3-AI 방어적 투표 시스템으로 리스크 최소화

**핵심 개념**:

Phase E는 **비대칭 의사결정 로직**을 통해 손실을 방어하고 수익을 신중하게 추구합니다:

- **STOP_LOSS**: 1/3 (1명만 경고해도 즉시 실행) - 방어 우선
- **BUY**: 2/3 (과반수 찬성 필요) - 신중한 진입
- **DCA**: 3/3 (전원 동의 필요) - 매우 신중한 물타기

#### E1: 3-AI Voting System

**구현**:

```python
from backend.ai.consensus import get_consensus_engine

engine = get_consensus_engine()

# 3-AI 투표 실행
result = await engine.vote_on_signal(
    context=market_context,
    action="BUY"  # BUY, SELL, DCA, STOP_LOSS
)

print(f"Decision: {result.approved}")
print(f"Votes: {result.approve_count}/3")
print(f"Strength: {result.consensus_strength}")
```

**비대칭 투표 규칙**:

| 액션 | 요구사항 | 설명 |
|------|---------|------|
| STOP_LOSS | 1/3 | 빠른 손절 (방어적) |
| BUY/SELL | 2/3 | 과반수 합의 |
| DCA | 3/3 | 만장일치 필요 |

**API**:

```bash
# 투표 실행
POST /consensus/vote

# 투표 규칙 조회
GET /consensus/rules

# 통계 조회
GET /consensus/stats
```

#### E2: DCA Strategy (Dollar Cost Averaging)

**목표**: 펀더멘털 기반 물타기 전략

**핵심 로직**:

```python
from backend.ai.strategies.dca_strategy import get_dca_strategy

dca_strategy = get_dca_strategy()

# DCA 평가
decision = await dca_strategy.should_dca(
    ticker="NVDA",
    current_price=130.0,
    avg_entry_price=150.0,
    dca_count=0,
    total_invested=10000.0,
    context=market_context
)

print(f"DCA: {decision.should_dca}")
print(f"Reason: {decision.reasoning}")
print(f"Position Size: {decision.position_size}")
```

**DCA 조건 체크**:

1. ✅ **가격 하락**: 최소 10% 이상
2. ✅ **최대 횟수**: 3회까지만
3. ✅ **총 손실 한도**: 30% 이내
4. ✅ **펀더멘털**: 뉴스 감정, 공급망 리스크 체크
5. ✅ **Consensus**: 3명 전원 동의 필요

**포지션 크기 (점진적 감소)**:

- 1차 DCA: 초기 투자의 50%
- 2차 DCA: 초기 투자의 33%
- 3차 DCA: 초기 투자의 25%

**API**:

```bash
# DCA 종합 평가 (전략 + Consensus)
POST /consensus/dca/evaluate

# 간단 테스트
POST /consensus/dca/test?ticker=NVDA&current_price=130&avg_entry_price=150
```

**응답 예시**:

```json
{
  "dca_recommended": true,
  "consensus_approved": false,
  "final_decision": "REJECTED",
  "dca_reasoning": "Fundamentals intact: News sentiment neutral/positive (0.30); Price drop: -13.3%",
  "approval_details": {
    "votes": "2/3",
    "requirement": "3/3",
    "consensus_strength": "strong"
  }
}
```

#### E3: Position Tracking

**목표**: 포지션별 DCA 이력 및 손익 추적

**구현**:

```python
from backend.data.position_tracker import get_position_tracker

tracker = get_position_tracker()

# 초기 포지션 생성
position = tracker.create_position(
    ticker="NVDA",
    company_name="NVIDIA",
    initial_price=150.0,
    initial_amount=10000.0
)

# DCA 추가
tracker.add_dca_entry(
    ticker="NVDA",
    price=135.0,
    amount=5000.0,
    reasoning="1st DCA - 10% drop"
)

# 미실현 손익 조회
pnl = position.get_unrealized_pnl(current_price=130.0)
print(f"P&L: ${pnl['pnl']:.2f} ({pnl['pnl_pct']:.2f}%)")
```

**Position 데이터 모델**:

```python
@dataclass
class Position:
    ticker: str
    total_shares: float          # 총 보유 주식
    avg_entry_price: float       # 평균 매수가 (자동 계산)
    total_invested: float        # 총 투자액
    dca_count: int              # DCA 실행 횟수
    dca_entries: List[DCAEntry] # DCA 이력
```

**API**:

```bash
# 포지션 생성
POST /positions/create

# DCA 추가
POST /positions/add-dca

# 포지션 조회
GET /positions/{ticker}?current_price=130

# 포트폴리오 요약
GET /positions/portfolio/summary?current_prices={"NVDA":130,"TSLA":250}
```

**전체 통합 플로우**:

```
1. 뉴스 분석 → MarketContext 생성
2. DCA 전략 평가 (가격, 펀더멘털 체크)
3. Consensus 투표 (3-AI, 3/3 필요)
4. 승인 시 Position에 DCA 기록
5. 실시간 손익 추적
```

**테스트**:

```bash
# 전체 통합 테스트
python test_phase_e_integration.py

# 결과:
# [Step 1] Position created: NVDA @ $150
# [Step 2] DCA evaluated: -13.3% drop
# [Step 3] Consensus: 2/3 → REJECTED
# [Final] P&L: -13.58%
```

**파일 구조**:

```
backend/
├── ai/
│   ├── consensus/
│   │   ├── consensus_engine.py      # 3-AI 투표 엔진
│   │   ├── consensus_models.py      # 데이터 모델
│   │   └── voting_rules.py          # 비대칭 규칙
│   └── strategies/
│       └── dca_strategy.py          # DCA 전략
├── data/
│   └── position_tracker.py          # 포지션 추적
└── api/
    ├── consensus_router.py          # Consensus API
    └── position_router.py           # Position API
```

**상세 문서**: `docs/Phase_E_Consensus.md`

---

## 8. 트러블슈팅

### 8.1 일반적인 문제

#### Redis 연결 실패

**증상**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**해결**:

```bash
# 1. Redis 컨테이너 확인
docker ps | grep redis

# 2. 재시작
docker-compose restart redis

# 3. 로그 확인
docker-compose logs redis
```

#### TimescaleDB 느린 쿼리

**증상**: Feature Store 응답 > 200ms

**해결**:

```sql
-- 1. 인덱스 확인
SELECT * FROM pg_indexes WHERE tablename = 'features';

-- 2. 인덱스 재생성
CREATE INDEX CONCURRENTLY idx_features_lookup 
ON features(ticker, feature_name, as_of_timestamp DESC);

-- 3. VACUUM
VACUUM ANALYZE features;
```

#### Cache Hit Rate 낮음 (< 90%)

**원인**:
1. Cache Warming 미실행
2. TTL 너무 짧음
3. Redis 메모리 부족

**해결**:

```python
# 1. Cache Warming 실행
python scripts/warm_cache.py

# 2. TTL 증가
# .env
FEATURE_TTL_SECONDS=86400  # 24시간

# 3. Redis 메모리 확인
docker stats redis
```

---

### 8.2 API 오류

#### Claude API Rate Limit

**증상**:
```
anthropic.RateLimitError: Rate limit exceeded
```

**해결**:

```python
# backend/ai/agent.py
# Retry with exponential backoff
import time
from anthropic import Anthropic

for attempt in range(3):
    try:
        response = client.messages.create(...)
        break
    except anthropic.RateLimitError:
        wait_time = 2 ** attempt
        time.sleep(wait_time)
```

#### Yahoo Finance 429 Error

**증상**:
```
yfinance.exceptions.YFException: 429 Too Many Requests
```

**해결**:

```python
# 1. 요청 간격 증가
import time

for ticker in tickers:
    df = yf.download(ticker)
    time.sleep(1)  # 1초 대기

# 2. 프록시 사용 (선택)
import yfinance as yf
yf.pdr_override()
yf.set_tz_cache_location("/tmp/yfinance")
```

---

### 8.3 배포 문제

#### Docker Compose 메모리 부족

**증상**:
```
ERROR: Cannot start service timescaledb: OCI runtime create failed
```

**해결**:

```yaml
# docker-compose.yml
services:
  timescaledb:
    mem_limit: 2g  # 메모리 제한 증가
    mem_reservation: 1g
```

#### 포트 충돌

**증상**:
```
Error: Bind for 0.0.0.0:8002 failed: port is already allocated
```

**해결**:

```bash
# 1. 기존 프로세스 확인
lsof -i :8002

# 2. 프로세스 종료
kill -9 <PID>

# 3. 또는 포트 변경
# docker-compose.yml
ports:
  - "8002:8002"  # 8002로 변경
```

---

## 9. FAQ

### Q1: 한국 주식도 지원하나요?

**A**: 현재는 미국 주식만 지원합니다. 한국 주식 지원을 위해서는:

1. Yahoo Finance API에서 한국 주식 데이터 확인 필요
2. DART API 통합 (전자공시 시스템)
3. Feature 계산 로직 조정 (KRW 단위)

한국투자증권 API는 Phase 11에서 통합되어 있습니다.

### Q2: 백테스트 결과를 신뢰할 수 있나요?

**A**: 백테스트는 다음을 포함합니다:

- ✅ Slippage (1 bps)
- ✅ Commission (0.015%)
- ✅ Look-ahead Bias 방지
- ✅ Event-driven 시뮬레이션

**하지만**:
- ⚠️ 과거 성과 ≠ 미래 수익
- ⚠️ 시장 체제 변화 미반영
- ⚠️ 극단적 이벤트 (Black Swan) 제외

**권장사항**: 모의투자로 최소 1개월 검증 후 실거래

### Q3: 비용이 정말 월 $3만 드나요?

**A**: 100종목, 일 1회 분석 기준입니다. 실제 비용은:

| 요인 | 영향 |
|------|------|
| 분석 빈도 | 일 2회 → $6/월 |
| 종목 수 | 200종목 → $6/월 |
| AI 모델 | Sonnet 사용 → $15/월 |
| Cache Hit Rate | 90% → $3.3/월 |

**비용 추적**: Prometheus 메트릭으로 실시간 모니터링

### Q4: Constitution Rules를 수정하려면?

**A**: `.env` 파일 또는 `backend/config.py` 수정:

```bash
# .env
MAX_VOLATILITY_PCT=60.0  # 기본값: 50.0
CONVICTION_THRESHOLD_BUY=0.75  # 기본값: 0.7
MAX_POSITION_SIZE=0.10  # 기본값: 0.05
```

**재시작 필요**: API 서버 재시작

### Q5: 새로운 전략을 추가하려면?

**A**: Phase 5 참고:

```python
# backend/strategies/my_strategy.py
from backend.strategies.base import Strategy

class MyStrategy(Strategy):
    async def generate_signal(self, ticker: str) -> dict:
        # 전략 로직
        return {
            "signal": "BUY",
            "confidence": 0.85
        }

# backend/strategies/ensemble.py
from backend.strategies.my_strategy import MyStrategy

ensemble.add_strategy(MyStrategy())
```

### Q6: RAG는 언제 완성되나요?

**A**: Phase 13 진행 중 (80% 완료)

**완료 항목**:
- ✅ PostgreSQL + pgvector 설정
- ✅ SEC 파일 다운로드
- ✅ 문서 청킹 + 임베딩

**남은 작업**:
- ⏳ 벡터 검색 API (1주)
- ⏳ 증분 업데이트 (1주)

**예상 완료**: 2025-12-06

### Q7: NAS 없이 로컬에서만 실행 가능한가요?

**A**: 예, Docker만 있으면 됩니다:

```bash
# Windows/Mac/Linux
docker-compose up -d

# API 서버
python backend/main.py
```

**차이점**:
- ❌ 자동 백업 없음
- ❌ 24/7 가동 어려움
- ✅ 개발/테스트는 동일

### Q8: 실거래 전 꼭 해야 할 것은?

**A**: 체크리스트:

- [ ] 모의투자 1개월 이상 테스트
- [ ] Kill Switch 작동 확인
- [ ] 일일 손실 한도 설정 (-5% 권장)
- [ ] API 키 보안 관리 (2FA)
- [ ] 알림 설정 (Telegram)
- [ ] 백업 자동화 설정
- [ ] 포트폴리오 분산 (10+ 종목)

### Q9: 문제 해결이 안 되면?

**A**: 다음 순서로:

1. [트러블슈팅](#8-트러블슈팅) 섹션 확인
2. GitHub Issues 검색
3. 새 Issue 생성 (재현 방법 포함)
4. Discussion 포럼 질문

### Q10: 기여하려면?

**A**: 환영합니다!

```bash
# Fork & Clone
git clone https://github.com/YOUR_USERNAME/ai-trading-system.git

# 브랜치 생성
git checkout -b feature/my-feature

# 개발 & 테스트
pytest tests/

# Pull Request
git push origin feature/my-feature
```

**가이드**: `CONTRIBUTING.md` 참고

---

## 🎓 학습 자료

### 공식 문서
- [GitHub Spec-Kit](https://github.com/github/spec-kit)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [TimescaleDB Docs](https://docs.timescale.com/)
- [pgvector Docs](https://github.com/pgvector/pgvector)

### AI API 문서
- [Anthropic Claude](https://docs.anthropic.com/)
- [Google Gemini](https://ai.google.dev/docs)
- [OpenAI API](https://platform.openai.com/docs)

### 트레이딩 학습
- [Quantitative Finance](https://www.quantstart.com/)
- [Algorithmic Trading](https://www.investopedia.com/algorithmic-trading-4689653)

---

## 📞 지원 및 커뮤니티

- **GitHub**: https://github.com/psh355q-ui/ai-trading-system
- **Issues**: https://github.com/psh355q-ui/ai-trading-system/issues
- **Discussions**: https://github.com/psh355q-ui/ai-trading-system/discussions

---

## 📜 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참고

---

## ⚠️ 면책 조항

> **경고**: 이 시스템은 투자 자문이 아닙니다.
>
> - AI는 틀릴 수 있습니다
> - 모든 투자 결정의 책임은 사용자에게 있습니다
> - 투자 손실에 대해 개발자는 책임지지 않습니다
> - 반드시 모의투자로 충분히 테스트한 후 사용하세요
> - 과거 성과가 미래 수익을 보장하지 않습니다

---

**MASTER GUIDE v2.2**
**최종 업데이트**: 2025-12-06
**GitHub**: https://github.com/psh355q-ui/ai-trading-system

---

*"The stock market is a device for transferring money from the impatient to the patient."*  
*- Warren Buffett*

**이 프로젝트와 함께 현명한 투자자가 되세요! 🚀**