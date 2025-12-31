# AI Trading System - 전체 시스템 아키텍처

**Last Updated**: 2025-12-30
**Version**: 1.0.0
**Author**: AI Trading System Development Team

---

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [기술 스택](#기술-스택)
3. [데이터베이스 아키텍처](#데이터베이스-아키텍처)
4. [백엔드 아키텍처](#백엔드-아키텍처)
5. [프론트엔드 아키텍처](#프론트엔드-아키텍처)
6. [AI 에이전트 시스템](#ai-에이전트-시스템)
7. [데이터 흐름](#데이터-흐름)
8. [스케줄러 시스템](#스케줄러-시스템)
9. [API 엔드포인트](#api-엔드포인트)
10. [보안 및 인증](#보안-및-인증)
11. [배포 및 운영](#배포-및-운영)

---

## 시스템 개요

### 프로젝트 목적

AI Trading System은 **다중 AI 에이전트 기반 자동 트레이딩 시스템**입니다. 뉴스 분석, 기술적 분석, 리스크 관리, 포트폴리오 최적화 등을 AI 에이전트들이 협업하여 수행하고, 최종적으로 PM(Portfolio Manager) 에이전트가 의사결정을 내립니다.

### 핵심 특징

1. **Multi-Agent War Room**: 9개의 전문 AI 에이전트가 협업
2. **News-Driven Trading**: 뉴스 해석 및 시장 반응 예측
3. **Auto-Learning**: NIA(News Interpretation Accuracy) 기반 가중치 자동 조정
4. **Portfolio Optimization**: Modern Portfolio Theory 기반 최적화
5. **Risk Management**: 실시간 리스크 모니터링 및 손절 자동화
6. **Accountability System**: AI 의사결정 추적 및 실패 학습

### 시스템 구성

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│                    (React + TypeScript)                          │
└────────────────────┬────────────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  API Router  │  │  Schedulers  │  │  AI Agents   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────┬────────────────────────────────────────────┘
                     │ SQLAlchemy ORM
┌────────────────────▼────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Core Data   │  │  AI Data     │  │  System Data │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 기술 스택

### Backend

| 구분 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **Framework** | FastAPI | 0.104+ | REST API 서버 |
| **ORM** | SQLAlchemy | 2.0+ | 데이터베이스 ORM |
| **Database** | PostgreSQL | 14+ | 메인 데이터베이스 |
| **AI SDK** | Google Gemini | 2.0 Flash | AI 에이전트 추론 |
| **Scheduler** | APScheduler | 3.10+ | 스케줄 작업 관리 |
| **Data Analysis** | Pandas | 2.0+ | 데이터 분석 및 처리 |
| **Financial Data** | yfinance | 0.2+ | 주가 데이터 다운로드 |
| **Optimization** | scipy | 1.11+ | 포트폴리오 최적화 |
| **HTTP Client** | httpx | 0.24+ | 비동기 HTTP 요청 |
| **Validation** | Pydantic | 2.0+ | 데이터 검증 |

### Frontend

| 구분 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **Framework** | React | 18+ | UI 프레임워크 |
| **Language** | TypeScript | 5.0+ | 타입 안전성 |
| **Routing** | React Router | 6.0+ | 클라이언트 라우팅 |
| **State Management** | React Query | 4.0+ | 서버 상태 관리 |
| **Charts** | Recharts | 2.5+ | 차트 시각화 |
| **Icons** | Lucide React | 0.263+ | 아이콘 라이브러리 |
| **Styling** | Tailwind CSS | 3.0+ | 유틸리티 CSS |
| **Build Tool** | Vite | 4.0+ | 빌드 도구 |

### Infrastructure

| 구분 | 기술 | 용도 |
|------|------|------|
| **Containerization** | Docker | 개발/배포 환경 |
| **Orchestration** | Docker Compose | 멀티 컨테이너 관리 |
| **Reverse Proxy** | Nginx | 프록시 서버 |
| **Process Manager** | Uvicorn | ASGI 서버 |

---

## 데이터베이스 아키텍처

### ERD 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                         Core Trading Data                        │
├─────────────────────────────────────────────────────────────────┤
│  - trading_signals        (트레이딩 시그널)                      │
│  - orders                 (주문 내역)                            │
│  - positions              (포지션 정보)                          │
│  - portfolio_history      (포트폴리오 히스토리)                  │
│  - multi_asset_config     (멀티 자산 설정)                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         News & Analysis                          │
├─────────────────────────────────────────────────────────────────┤
│  - news_articles          (뉴스 기사)                            │
│  - news_interpretations   (뉴스 해석)                            │
│  - news_market_reactions  (시장 반응 예측)                       │
│  - news_decision_links    (의사결정 연결)                        │
│  - news_narratives        (뉴스 내러티브)                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      AI Agent & Learning                         │
├─────────────────────────────────────────────────────────────────┤
│  - war_room_conversations (War Room 대화 기록)                   │
│  - agent_weights_history  (에이전트 가중치 히스토리)             │
│  - failure_analysis       (실패 분석)                            │
│  - decision_logs          (의사결정 로그)                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Portfolio & Risk Management                    │
├─────────────────────────────────────────────────────────────────┤
│  - asset_correlations     (자산 상관계수)                        │
│  - portfolio_optimization (포트폴리오 최적화 결과)               │
│  - risk_assessments       (리스크 평가)                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         System & Metadata                        │
├─────────────────────────────────────────────────────────────────┤
│  - macro_context_snapshots (매크로 컨텍스트)                     │
│  - rss_feeds              (RSS 피드)                             │
│  - api_usage_logs         (API 사용 로그)                        │
└─────────────────────────────────────────────────────────────────┘
```

### 주요 테이블 상세

#### 1. trading_signals

트레이딩 시그널 생성 및 추적

```sql
CREATE TABLE trading_signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL,  -- 'BUY', 'SELL', 'HOLD'
    confidence DECIMAL(5, 2),           -- 0.00 ~ 100.00
    reasoning TEXT,                     -- AI 추론 내용
    created_at TIMESTAMP DEFAULT NOW(),
    source VARCHAR(50),                 -- 'war_room', 'technical', 'news'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'executed', 'cancelled'

    -- Price Targets
    entry_price DECIMAL(12, 2),
    target_price DECIMAL(12, 2),
    stop_loss DECIMAL(12, 2),

    -- Execution
    executed_at TIMESTAMP,
    execution_price DECIMAL(12, 2),

    -- Performance Tracking
    pnl DECIMAL(12, 2),
    pnl_percentage DECIMAL(10, 4),

    -- Metadata
    metadata JSONB
);

-- Indexes
CREATE INDEX idx_signals_symbol ON trading_signals(symbol);
CREATE INDEX idx_signals_created ON trading_signals(created_at DESC);
CREATE INDEX idx_signals_status ON trading_signals(status);
```

**필드 설명**:
- `signal_type`: BUY(매수), SELL(매도), HOLD(보유)
- `confidence`: AI의 확신도 (0~100%)
- `reasoning`: AI 에이전트들의 추론 내용 (War Room 대화)
- `source`: 시그널 출처 (War Room, 기술적 분석, 뉴스 분석)
- `metadata`: 추가 정보 (JSON 형태)

**연결 테이블**:
- `orders`: signal_id로 연결
- `war_room_conversations`: 시그널 생성 시 대화 기록

---

#### 2. news_interpretations

뉴스 해석 및 시장 영향 분석

```sql
CREATE TABLE news_interpretations (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES news_articles(id),
    symbol VARCHAR(20) NOT NULL,

    -- Interpretation
    sentiment VARCHAR(20),              -- 'bullish', 'bearish', 'neutral'
    impact_score DECIMAL(5, 2),         -- 0.00 ~ 10.00
    reasoning TEXT,                     -- 해석 근거

    -- Market Impact Prediction
    predicted_direction VARCHAR(20),    -- 'up', 'down', 'sideways'
    predicted_magnitude DECIMAL(10, 4), -- 예상 변동폭 (%)
    time_horizon VARCHAR(20),           -- '1d', '1w', '1m'

    -- AI Agent Info
    agent_name VARCHAR(50),             -- 'news_agent'
    model_version VARCHAR(50),          -- 'gemini-2.0-flash'

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    -- Metadata
    metadata JSONB
);

-- Indexes
CREATE INDEX idx_interp_article ON news_interpretations(article_id);
CREATE INDEX idx_interp_symbol ON news_interpretations(symbol);
CREATE INDEX idx_interp_created ON news_interpretations(created_at DESC);
```

**필드 설명**:
- `sentiment`: 뉴스의 감성 (상승/하락/중립)
- `impact_score`: 시장 영향도 (0~10점)
- `predicted_direction`: 예측 방향
- `predicted_magnitude`: 예측 변동폭 (%)
- `time_horizon`: 예측 시간 범위

**연결 테이블**:
- `news_articles`: article_id로 연결
- `news_market_reactions`: interpretation_id로 연결 (검증)

---

#### 3. news_market_reactions

뉴스 예측 검증 및 정확도 추적

```sql
CREATE TABLE news_market_reactions (
    id SERIAL PRIMARY KEY,
    interpretation_id INTEGER REFERENCES news_interpretations(id),

    -- Prediction
    predicted_direction VARCHAR(20),
    predicted_magnitude DECIMAL(10, 4),

    -- Actual Market Movement
    actual_direction VARCHAR(20),
    actual_magnitude DECIMAL(10, 4),

    -- Accuracy Metrics (1d)
    accuracy_1d DECIMAL(5, 4),          -- 0.0000 ~ 1.0000
    verified_at_1d TIMESTAMP,

    -- Accuracy Metrics (1w)
    accuracy_1w DECIMAL(5, 4),
    verified_at_1w TIMESTAMP,

    -- Accuracy Metrics (1m)
    accuracy_1m DECIMAL(5, 4),
    verified_at_1m TIMESTAMP,

    -- Price Data
    price_at_prediction DECIMAL(12, 2),
    price_after_1d DECIMAL(12, 2),
    price_after_1w DECIMAL(12, 2),
    price_after_1m DECIMAL(12, 2),

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reaction_interp ON news_market_reactions(interpretation_id);
CREATE INDEX idx_reaction_verified_1d ON news_market_reactions(verified_at_1d);
```

**필드 설명**:
- `accuracy_1d/1w/1m`: 1일/1주/1개월 후 정확도
- `verified_at_*`: 검증 완료 시각
- `price_at_prediction`: 예측 시점 가격
- `price_after_*`: 1d/1w/1m 후 실제 가격

**사용처**:
- NIA(News Interpretation Accuracy) 점수 계산
- 실패 학습 (Failure Learning)
- 에이전트 가중치 자동 조정

---

#### 4. agent_weights_history

War Room 에이전트 가중치 히스토리

```sql
CREATE TABLE agent_weights_history (
    id SERIAL PRIMARY KEY,

    -- Timestamp & Source
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by VARCHAR(100),            -- 'system', 'admin', 'FailureLearningScheduler'
    reason TEXT,                        -- 조정 이유

    -- Agent Weights (합계 = 1.0)
    trader_agent DECIMAL(5, 4),         -- 기본 0.15
    risk_agent DECIMAL(5, 4),           -- 기본 0.15
    analyst_agent DECIMAL(5, 4),        -- 기본 0.12
    macro_agent DECIMAL(5, 4),          -- 기본 0.14
    institutional_agent DECIMAL(5, 4),  -- 기본 0.14
    news_agent DECIMAL(5, 4),           -- 기본 0.14 (NIA 기반 조정)
    chip_war_agent DECIMAL(5, 4),       -- 기본 0.14
    dividend_risk_agent DECIMAL(5, 4),  -- 기본 0.02
    pm_agent DECIMAL(5, 4) DEFAULT 0    -- PM은 가중치 없음 (최종 의사결정자)
);

-- Indexes
CREATE INDEX idx_weights_changed ON agent_weights_history(changed_at DESC);
CREATE INDEX idx_weights_changedby ON agent_weights_history(changed_by);
```

**필드 설명**:
- `changed_by`: 변경 주체 (시스템/관리자/자동학습)
- `reason`: 조정 이유 (예: "NIA below 60% - decreasing News Agent weight")
- `*_agent`: 각 에이전트의 가중치 (합계 1.0)

**자동 조정 규칙**:
```python
if NIA < 60%:
    news_agent -= 0.02  # 성능 저하 시 가중치 감소
elif NIA >= 80%:
    news_agent += 0.02  # 성능 우수 시 가중치 증가
```

**사용처**:
- War Room 최종 의사결정 시 가중치 적용
- Auto-Learning Dashboard 시각화
- 성능 추적 및 최적화

---

#### 5. asset_correlations

자산 간 상관계수 (포트폴리오 분산 최적화)

```sql
CREATE TABLE asset_correlations (
    id SERIAL PRIMARY KEY,

    -- Asset Pair
    symbol1 VARCHAR(20) NOT NULL,
    symbol2 VARCHAR(20) NOT NULL,

    -- Correlation Coefficients
    correlation_30d DECIMAL(10, 6),     -- 30일 상관계수
    correlation_90d DECIMAL(10, 6),     -- 90일 상관계수
    correlation_1y DECIMAL(10, 6),      -- 1년 상관계수

    -- Metadata
    calculated_at TIMESTAMP DEFAULT NOW(),

    -- Unique Constraint
    UNIQUE(symbol1, symbol2)
);

-- Indexes
CREATE INDEX idx_correlation_pair ON asset_correlations(symbol1, symbol2);
CREATE INDEX idx_correlation_calculated ON asset_correlations(calculated_at DESC);
```

**필드 설명**:
- `symbol1, symbol2`: 자산 페어 (예: AAPL, MSFT)
- `correlation_30d/90d/1y`: 기간별 상관계수 (-1.0 ~ 1.0)
- `calculated_at`: 계산 시각

**상관계수 해석**:
- `> 0.7`: 강한 양의 상관관계 (함께 움직임)
- `0.3 ~ 0.7`: 약한 양의 상관관계
- `-0.3 ~ 0.3`: 무상관
- `< -0.3`: 음의 상관관계 (반대로 움직임)

**계산 방식**:
```python
# Pearson Correlation on Returns
returns1 = prices1.pct_change()
returns2 = prices2.pct_change()
correlation = returns1.corr(returns2)
```

**사용처**:
- 포트폴리오 분산 최적화
- Correlation Dashboard 시각화
- Hedging 전략 수립

---

#### 6. multi_asset_config

멀티 자산 트레이딩 설정

```sql
CREATE TABLE multi_asset_config (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,

    -- Asset Info
    asset_name VARCHAR(100),
    asset_type VARCHAR(50),             -- 'stock', 'etf', 'crypto', 'commodity'
    sector VARCHAR(50),

    -- Trading Config
    is_active BOOLEAN DEFAULT true,     -- 트레이딩 활성화 여부
    max_position_size DECIMAL(12, 2),   -- 최대 포지션 크기 ($)
    allocation_percentage DECIMAL(5, 2), -- 포트폴리오 할당 비율 (%)

    -- Risk Parameters
    stop_loss_percentage DECIMAL(5, 2), -- 손절 비율 (%)
    take_profit_percentage DECIMAL(5, 2), -- 익절 비율 (%)

    -- Metadata
    added_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_asset_symbol ON multi_asset_config(symbol);
CREATE INDEX idx_asset_active ON multi_asset_config(is_active);
```

**필드 설명**:
- `symbol`: 자산 심볼 (AAPL, BTC-USD, GLD 등)
- `asset_type`: 자산 유형 (주식/ETF/암호화폐/원자재)
- `is_active`: 트레이딩 활성화 여부
- `allocation_percentage`: 포트폴리오 내 목표 비중

**사용처**:
- Multi-Asset Dashboard
- Portfolio Optimization
- Correlation Calculation (활성 자산만)

---

#### 7. war_room_conversations

War Room AI 에이전트 대화 기록

```sql
CREATE TABLE war_room_conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,   -- 세션 ID (UUID)

    -- Context
    symbol VARCHAR(20),
    question TEXT,                      -- PM의 질문

    -- Agent Responses
    trader_response TEXT,
    risk_response TEXT,
    analyst_response TEXT,
    macro_response TEXT,
    institutional_response TEXT,
    news_response TEXT,
    chip_war_response TEXT,
    dividend_risk_response TEXT,

    -- PM Decision
    pm_decision TEXT,                   -- 최종 의사결정
    pm_reasoning TEXT,                  -- 의사결정 근거

    -- Result
    final_decision VARCHAR(20),         -- 'BUY', 'SELL', 'HOLD'
    confidence DECIMAL(5, 2),           -- 확신도

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    duration_seconds DECIMAL(10, 2),    -- 대화 소요 시간

    -- Signal Link
    signal_id INTEGER REFERENCES trading_signals(id)
);

-- Indexes
CREATE INDEX idx_warroom_session ON war_room_conversations(session_id);
CREATE INDEX idx_warroom_symbol ON war_room_conversations(symbol);
CREATE INDEX idx_warroom_created ON war_room_conversations(created_at DESC);
```

**필드 설명**:
- `session_id`: War Room 세션 ID
- `*_response`: 각 에이전트의 응답
- `pm_decision`: PM의 최종 의사결정
- `final_decision`: 최종 액션 (BUY/SELL/HOLD)
- `signal_id`: 생성된 트레이딩 시그널 ID

**대화 흐름**:
```
PM: "AAPL에 대한 매수 의견을 듣고 싶습니다."
  ↓
Trader Agent: "기술적으로 상승 추세..."
Risk Agent: "현재 변동성 높음, 주의 필요..."
Analyst Agent: "실적 전망 긍정적..."
News Agent: "최근 긍정적 뉴스 다수..."
Macro Agent: "연준 금리 동결 예상..."
...
  ↓
PM: "종합 의견: 매수 추천, 확신도 75%"
  ↓
Trading Signal 생성
```

---

#### 8. failure_analysis

AI 실패 분석 및 학습

```sql
CREATE TABLE failure_analysis (
    id SERIAL PRIMARY KEY,

    -- Link to Prediction
    interpretation_id INTEGER REFERENCES news_interpretations(id),

    -- Failure Details
    predicted_direction VARCHAR(20),
    actual_direction VARCHAR(20),
    accuracy DECIMAL(5, 4),             -- 정확도 (0.0 ~ 1.0)

    -- AI Analysis
    failure_reason TEXT,                -- 실패 원인 분석
    missed_factors TEXT[],              -- 놓친 요인들
    suggested_improvements TEXT,        -- 개선 제안

    -- Agent Responsibility
    responsible_agent VARCHAR(50),      -- 주 책임 에이전트

    -- Learning Action
    action_taken VARCHAR(100),          -- 취한 조치
    weight_adjustment DECIMAL(5, 4),    -- 가중치 조정량

    -- Metadata
    analyzed_at TIMESTAMP DEFAULT NOW(),
    analyzer_agent VARCHAR(50) DEFAULT 'failure_learning_agent'
);

-- Indexes
CREATE INDEX idx_failure_interp ON failure_analysis(interpretation_id);
CREATE INDEX idx_failure_analyzed ON failure_analysis(analyzed_at DESC);
```

**필드 설명**:
- `failure_reason`: AI가 분석한 실패 원인
- `missed_factors`: 예측 시 고려하지 못한 요인들
- `responsible_agent`: 주 책임 에이전트
- `action_taken`: 취한 조치 (가중치 조정, 학습 등)

**실패 분석 프로세스**:
```python
1. 낮은 정확도 예측 수집 (accuracy < 0.5)
2. Gemini AI로 실패 원인 분석
3. 놓친 요인 식별
4. 개선 제안 생성
5. 가중치 조정 (필요 시)
6. failure_analysis 테이블에 저장
```

**사용처**:
- Accountability Dashboard
- Auto-Learning Dashboard
- 에이전트 성능 개선

---

### 데이터베이스 관계도

```
news_articles (1) ──────┬─── (N) news_interpretations
                        │
                        └─── (N) news_decision_links

news_interpretations (1) ─── (1) news_market_reactions
                        │
                        └─── (1) failure_analysis

trading_signals (1) ────┬─── (N) orders
                        │
                        └─── (1) war_room_conversations

multi_asset_config (N) ─── (1) portfolio_optimization

asset_correlations (pair) ─── portfolio_optimization
```

---

## 백엔드 아키텍처

### 디렉토리 구조

```
backend/
├── main.py                      # FastAPI 앱 진입점
├── database/
│   ├── models.py                # SQLAlchemy 모델 정의
│   ├── repository.py            # 데이터베이스 세션 관리
│   └── migrations/              # Alembic 마이그레이션
├── api/
│   ├── trading_router.py        # 트레이딩 API
│   ├── news_router.py           # 뉴스 API
│   ├── war_room_router.py       # War Room API
│   ├── portfolio_router.py      # 포트폴리오 API
│   ├── correlation_router.py    # 상관계수 API
│   ├── failure_learning_router.py # 자동학습 API
│   └── ...
├── ai/
│   ├── agents/
│   │   ├── trader_agent.py      # Trader Agent
│   │   ├── risk_agent.py        # Risk Agent
│   │   ├── news_agent.py        # News Agent
│   │   ├── pm_agent.py          # PM Agent
│   │   ├── failure_learning_agent.py
│   │   └── ...
│   ├── prompts/
│   │   ├── trader_prompt.txt
│   │   ├── news_prompt.txt
│   │   └── ...
│   └── utils/
│       ├── gemini_client.py     # Gemini API 클라이언트
│       └── prompt_loader.py     # 프롬프트 로더
├── schedulers/
│   ├── news_scheduler.py        # 뉴스 수집 스케줄러
│   ├── verification_scheduler.py # 예측 검증 스케줄러
│   ├── failure_learning_scheduler.py # 자동학습 스케줄러
│   ├── correlation_scheduler.py  # 상관계수 계산 스케줄러
│   └── ...
├── services/
│   ├── portfolio_optimizer.py   # 포트폴리오 최적화
│   ├── risk_calculator.py       # 리스크 계산
│   └── ...
└── utils/
    ├── logger.py                # 로깅 유틸
    └── config.py                # 설정 관리
```

### FastAPI 라우터 구조

#### 라우터 등록 (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Trading System")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from backend.api.trading_router import router as trading_router
from backend.api.news_router import router as news_router
from backend.api.war_room_router import router as war_room_router
from backend.api.portfolio_router import router as portfolio_router
from backend.api.correlation_router import router as correlation_router
from backend.api.failure_learning_router import router as failure_learning_router

app.include_router(trading_router)
app.include_router(news_router)
app.include_router(war_room_router)
app.include_router(portfolio_router)
app.include_router(correlation_router)
app.include_router(failure_learning_router)

@app.get("/")
async def root():
    return {"message": "AI Trading System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

#### API Router 구조 예시 (correlation_router.py)

```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime

router = APIRouter(prefix="/api/correlation", tags=["Correlation"])

@router.post("/calculate")
async def calculate_correlations():
    """
    상관계수 수동 계산 트리거

    Returns:
        - timestamp: 계산 시각
        - success: 성공 여부
        - assets_count: 자산 수
        - pairs_calculated: 계산된 페어 수
    """
    try:
        scheduler = CorrelationScheduler()
        result = scheduler.calculate_all_correlations()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    """
    계산 상태 조회

    Returns:
        - total_pairs: 저장된 페어 수
        - expected_pairs: 기대 페어 수
        - coverage: 커버리지 %
        - last_calculated: 마지막 계산 시각
    """
    # Implementation
    pass

@router.get("/heatmap")
async def get_heatmap(
    period: str = Query("90d", regex="^(30d|90d|1y)$"),
    min_correlation: Optional[float] = Query(None, ge=-1.0, le=1.0)
):
    """
    히트맵 데이터 조회

    Args:
        period: 기간 (30d, 90d, 1y)
        min_correlation: 최소 상관계수 필터

    Returns:
        - matrix: 상관계수 행렬
        - heatmap_data: 차트용 데이터
    """
    # Implementation
    pass

@router.get("/pairs")
async def get_top_pairs(
    period: str = Query("90d"),
    sort_by: str = Query("highest", regex="^(highest|lowest)$"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Top 상관 페어 조회

    Args:
        period: 기간
        sort_by: 정렬 (highest/lowest)
        limit: 최대 결과 수

    Returns:
        - pairs: 상관 페어 리스트
    """
    # Implementation
    pass
```

**FastAPI 특징**:
- **자동 문서화**: `/docs` (Swagger UI), `/redoc` (ReDoc)
- **타입 검증**: Pydantic 모델 자동 검증
- **비동기 지원**: `async/await` 패턴
- **의존성 주입**: Dependency Injection

---

### AI 에이전트 시스템

#### 에이전트 계층 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                      PM Agent (최종 의사결정)                     │
│                   Portfolio Manager Agent                        │
└───────────────────────┬─────────────────────────────────────────┘
                        │ (가중치 기반 종합)
        ┌───────────────┼───────────────┬───────────────┐
        ▼               ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Trader Agent  │ │ Risk Agent   │ │Analyst Agent │ │ Macro Agent  │
│(기술적 분석) │ │(리스크 관리) │ │(기본적 분석) │ │(매크로 분석) │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Institutional │ │  News Agent  │ │Chip War Agent│ │Dividend Risk │
│    Agent     │ │(뉴스 분석)   │ │(반도체 분석) │ │    Agent     │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

#### 에이전트 구현 예시 (news_agent.py)

```python
"""
News Agent

뉴스 해석 및 시장 영향 예측 전문 AI 에이전트
"""

import os
from datetime import datetime
from typing import Dict, Optional
import google.generativeai as genai

class NewsAgent:
    """
    뉴스 분석 에이전트

    역할:
    - 뉴스 기사 해석
    - 시장 영향 예측
    - 감성 분석
    """

    def __init__(self):
        """Initialize News Agent"""
        self.agent_name = "news_agent"
        self.model_version = "gemini-2.0-flash-exp"

        # Gemini API 설정
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(self.model_version)

        # 프롬프트 로드
        with open("backend/ai/prompts/news_agent_prompt.txt", "r") as f:
            self.system_prompt = f.read()

    def interpret_news(
        self,
        article: Dict,
        symbol: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        뉴스 해석 및 시장 영향 예측

        Args:
            article: 뉴스 기사 정보
            symbol: 종목 심볼
            context: 추가 컨텍스트 (매크로 환경 등)

        Returns:
            {
                'sentiment': 'bullish' | 'bearish' | 'neutral',
                'impact_score': 0.0 ~ 10.0,
                'reasoning': '해석 근거',
                'predicted_direction': 'up' | 'down' | 'sideways',
                'predicted_magnitude': 예상 변동폭 (%),
                'time_horizon': '1d' | '1w' | '1m',
                'confidence': 0.0 ~ 1.0
            }
        """
        # 프롬프트 구성
        user_prompt = f"""
**뉴스 분석 요청**

종목: {symbol}
제목: {article['title']}
본문: {article['content']}
출처: {article['source']}
발행일: {article['published_at']}

**컨텍스트**:
{context if context else '없음'}

위 뉴스를 분석하여 다음을 제공하세요:
1. 감성 (bullish/bearish/neutral)
2. 시장 영향도 (0~10점)
3. 해석 근거
4. 예상 방향 (up/down/sideways)
5. 예상 변동폭 (%)
6. 시간 범위 (1d/1w/1m)
7. 확신도 (0.0~1.0)

JSON 형태로 반환하세요.
"""

        # Gemini API 호출
        response = self.model.generate_content(
            [self.system_prompt, user_prompt],
            generation_config={
                "temperature": 0.3,  # 낮은 온도로 일관성 유지
                "top_p": 0.95,
                "max_output_tokens": 1000
            }
        )

        # JSON 파싱
        result = self._parse_response(response.text)

        # 메타데이터 추가
        result['agent_name'] = self.agent_name
        result['model_version'] = self.model_version
        result['analyzed_at'] = datetime.now().isoformat()

        return result

    def _parse_response(self, text: str) -> Dict:
        """Gemini 응답 파싱 (JSON 추출)"""
        import json
        import re

        # JSON 블록 추출
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # 파싱 실패 시 기본값 반환
            return {
                'sentiment': 'neutral',
                'impact_score': 5.0,
                'reasoning': text,
                'predicted_direction': 'sideways',
                'predicted_magnitude': 0.0,
                'time_horizon': '1d',
                'confidence': 0.5
            }
```

#### PM Agent (Portfolio Manager)

```python
"""
PM Agent - Portfolio Manager

최종 의사결정자
모든 에이전트의 의견을 종합하여 최종 결정
"""

class PMAgent:
    """
    Portfolio Manager Agent

    역할:
    - 모든 에이전트 의견 수집
    - 가중치 기반 종합 판단
    - 최종 의사결정 (BUY/SELL/HOLD)
    - War Room 대화 진행
    """

    def __init__(self):
        self.agent_name = "pm_agent"
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # 다른 에이전트 인스턴스
        self.trader = TraderAgent()
        self.risk = RiskAgent()
        self.analyst = AnalystAgent()
        self.macro = MacroAgent()
        self.institutional = InstitutionalAgent()
        self.news = NewsAgent()
        self.chip_war = ChipWarAgent()
        self.dividend_risk = DividendRiskAgent()

    def make_decision(
        self,
        symbol: str,
        question: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        War Room 대화를 통한 최종 의사결정

        Process:
        1. PM이 질문 제시
        2. 각 에이전트 의견 수집
        3. 가중치 적용하여 종합
        4. PM이 최종 결정
        5. Trading Signal 생성

        Args:
            symbol: 종목 심볼
            question: PM의 질문
            context: 추가 컨텍스트

        Returns:
            {
                'session_id': UUID,
                'final_decision': 'BUY' | 'SELL' | 'HOLD',
                'confidence': 0.0 ~ 100.0,
                'reasoning': PM의 추론,
                'agent_responses': {...},
                'signal_id': int (생성된 시그널 ID)
            }
        """
        import uuid
        session_id = str(uuid.uuid4())

        # 1. 각 에이전트 의견 수집
        responses = {}
        responses['trader'] = self.trader.analyze(symbol, context)
        responses['risk'] = self.risk.assess(symbol, context)
        responses['analyst'] = self.analyst.analyze(symbol, context)
        responses['macro'] = self.macro.analyze(context)
        responses['institutional'] = self.institutional.analyze(symbol, context)
        responses['news'] = self.news.get_latest_sentiment(symbol)
        responses['chip_war'] = self.chip_war.analyze(symbol, context)
        responses['dividend_risk'] = self.dividend_risk.analyze(symbol, context)

        # 2. 가중치 가져오기
        weights = self._get_current_weights()

        # 3. PM의 종합 판단
        pm_prompt = f"""
**War Room 의사결정**

질문: {question}
종목: {symbol}

**에이전트 의견**:

Trader Agent (가중치: {weights['trader_agent']:.2%}):
{responses['trader']}

Risk Agent (가중치: {weights['risk_agent']:.2%}):
{responses['risk']}

Analyst Agent (가중치: {weights['analyst_agent']:.2%}):
{responses['analyst']}

Macro Agent (가중치: {weights['macro_agent']:.2%}):
{responses['macro']}

Institutional Agent (가중치: {weights['institutional_agent']:.2%}):
{responses['institutional']}

News Agent (가중치: {weights['news_agent']:.2%}):
{responses['news']}

Chip War Agent (가중치: {weights['chip_war_agent']:.2%}):
{responses['chip_war']}

Dividend Risk Agent (가중치: {weights['dividend_risk_agent']:.2%}):
{responses['dividend_risk']}

---

위 의견들을 종합하여 최종 의사결정을 내려주세요:
1. 최종 결정 (BUY/SELL/HOLD)
2. 확신도 (0~100%)
3. 의사결정 근거
4. 목표가, 손절가

JSON 형태로 반환하세요.
"""

        # PM 의사결정
        pm_response = self.model.generate_content(pm_prompt)
        pm_decision = self._parse_pm_response(pm_response.text)

        # 4. War Room 대화 기록 저장
        self._save_war_room_conversation(
            session_id=session_id,
            symbol=symbol,
            question=question,
            responses=responses,
            pm_decision=pm_decision
        )

        # 5. Trading Signal 생성
        signal_id = self._create_trading_signal(
            symbol=symbol,
            decision=pm_decision,
            session_id=session_id
        )

        return {
            'session_id': session_id,
            'final_decision': pm_decision['action'],
            'confidence': pm_decision['confidence'],
            'reasoning': pm_decision['reasoning'],
            'target_price': pm_decision['target_price'],
            'stop_loss': pm_decision['stop_loss'],
            'agent_responses': responses,
            'signal_id': signal_id
        }

    def _get_current_weights(self) -> Dict[str, float]:
        """현재 에이전트 가중치 조회"""
        from backend.database.repository import get_sync_session
        from backend.database.models import AgentWeightsHistory

        with get_sync_session() as session:
            latest = session.query(AgentWeightsHistory).order_by(
                AgentWeightsHistory.changed_at.desc()
            ).first()

            if latest:
                return {
                    'trader_agent': float(latest.trader_agent),
                    'risk_agent': float(latest.risk_agent),
                    'analyst_agent': float(latest.analyst_agent),
                    'macro_agent': float(latest.macro_agent),
                    'institutional_agent': float(latest.institutional_agent),
                    'news_agent': float(latest.news_agent),
                    'chip_war_agent': float(latest.chip_war_agent),
                    'dividend_risk_agent': float(latest.dividend_risk_agent)
                }
            else:
                # 기본 가중치
                return {
                    'trader_agent': 0.15,
                    'risk_agent': 0.15,
                    'analyst_agent': 0.12,
                    'macro_agent': 0.14,
                    'institutional_agent': 0.14,
                    'news_agent': 0.14,
                    'chip_war_agent': 0.14,
                    'dividend_risk_agent': 0.02
                }
```

---

### Gemini API 통합

#### Gemini Client (gemini_client.py)

```python
"""
Gemini API Client

Google Gemini 2.0 Flash API 통합
"""

import os
import logging
from typing import List, Dict, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Gemini API 클라이언트

    Features:
    - API 키 관리
    - 모델 선택
    - 프롬프트 전송
    - 응답 파싱
    - 에러 핸들링
    - 비용 추적
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Initialize Gemini Client

        Args:
            model_name: Gemini 모델명
            temperature: 생성 온도 (0.0 ~ 1.0)
            max_tokens: 최대 토큰 수
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # API 키 설정
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

        logger.info(f"✅ Gemini Client initialized: {model_name}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Gemini API로 텍스트 생성

        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (옵션)
            temperature: 생성 온도 (옵션)
            max_tokens: 최대 토큰 수 (옵션)

        Returns:
            생성된 텍스트
        """
        try:
            # 프롬프트 구성
            messages = []
            if system_prompt:
                messages.append(system_prompt)
            messages.append(prompt)

            # Generation Config
            config = {
                "temperature": temperature or self.temperature,
                "top_p": 0.95,
                "max_output_tokens": max_tokens or self.max_tokens
            }

            # API 호출
            response = self.model.generate_content(
                messages,
                generation_config=config
            )

            # 비용 추적 (옵션)
            self._track_usage(response)

            return response.text

        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
            raise

    def _track_usage(self, response):
        """API 사용량 추적 (비용 관리)"""
        try:
            # Usage metadata 추출
            usage = response.usage_metadata

            # DB에 저장
            from backend.database.repository import get_sync_session
            from backend.database.models import APIUsageLog

            with get_sync_session() as session:
                log = APIUsageLog(
                    provider="gemini",
                    model=self.model_name,
                    prompt_tokens=usage.prompt_token_count,
                    completion_tokens=usage.candidates_token_count,
                    total_tokens=usage.total_token_count,
                    estimated_cost=self._calculate_cost(usage)
                )
                session.add(log)
                session.commit()

        except Exception as e:
            logger.warning(f"⚠️ Usage tracking failed: {e}")

    def _calculate_cost(self, usage) -> float:
        """
        비용 계산

        Gemini 2.0 Flash Pricing:
        - Input: $0.075 / 1M tokens
        - Output: $0.30 / 1M tokens
        """
        input_cost = (usage.prompt_token_count / 1_000_000) * 0.075
        output_cost = (usage.candidates_token_count / 1_000_000) * 0.30
        return input_cost + output_cost
```

---

## 스케줄러 시스템

### 스케줄러 개요

시스템에는 여러 자동화된 스케줄러가 실행됩니다:

| 스케줄러 | 실행 주기 | 역할 |
|---------|----------|------|
| **NewsScheduler** | 15분마다 | RSS 뉴스 수집 |
| **VerificationScheduler** | 매일 01:00 | 뉴스 예측 검증 (1d/1w/1m) |
| **FailureLearningScheduler** | 매일 00:00 | NIA 점수 계산 및 가중치 조정 |
| **CorrelationScheduler** | 매일 01:00 | 자산 상관계수 계산 |

### Failure Learning Scheduler 상세

**파일**: `backend/schedulers/failure_learning_scheduler.py`

```python
"""
Failure Learning Scheduler

매일 자정에 실행:
1. NIA 점수 계산
2. 실패 예측 분석
3. War Room 가중치 자동 조정
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy import and_

class FailureLearningScheduler:
    """자동 학습 스케줄러"""

    def __init__(self):
        self.agent = FailureLearningAgent()
        self.scheduler_name = "FailureLearningScheduler"

    def calculate_nia_score(self, lookback_days: int = 30) -> Optional[float]:
        """
        NIA (News Interpretation Accuracy) 점수 계산

        Process:
        1. 지난 N일간 검증된 예측 조회
        2. accuracy_1d 평균 계산
        3. NIA 점수 반환 (0.0 ~ 1.0)

        Args:
            lookback_days: 조회 기간

        Returns:
            NIA score or None
        """
        with get_sync_session() as session:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)

            # 검증된 예측 조회
            results = session.query(
                NewsMarketReaction.accuracy_1d
            ).filter(
                and_(
                    NewsMarketReaction.accuracy_1d.isnot(None),
                    NewsMarketReaction.verified_at_1d >= cutoff_date
                )
            ).all()

            if not results:
                return None

            # 평균 계산
            accuracies = [r[0] for r in results]
            nia_score = sum(accuracies) / len(accuracies)

            logger.info(f"✅ NIA Score: {nia_score:.2%}")
            return nia_score

    def adjust_weights_based_on_nia(
        self,
        nia_score: float,
        current_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        NIA 점수 기반 가중치 자동 조정

        규칙:
        - NIA < 60%: News Agent -2%
        - 60% <= NIA < 80%: 변화 없음
        - NIA >= 80%: News Agent +2%

        Args:
            nia_score: NIA 점수
            current_weights: 현재 가중치

        Returns:
            조정된 가중치
        """
        new_weights = current_weights.copy()
        news_weight = new_weights['news_agent']

        if nia_score < 0.60:
            # 성능 저하 - 가중치 감소
            adjustment = -0.02
            reason = f"NIA below 60% ({nia_score:.1%})"
        elif nia_score >= 0.80:
            # 성능 우수 - 가중치 증가
            adjustment = 0.02
            reason = f"NIA above 80% ({nia_score:.1%})"
        else:
            # 유지
            return new_weights

        # News Agent 가중치 조정 (0.05 ~ 0.25 범위)
        new_news_weight = max(0.05, min(0.25, news_weight + adjustment))
        actual_adjustment = new_news_weight - news_weight

        if actual_adjustment == 0:
            return new_weights

        new_weights['news_agent'] = new_news_weight

        # 다른 에이전트에 재분배
        other_agents = [
            'trader_agent', 'risk_agent', 'analyst_agent',
            'macro_agent', 'institutional_agent',
            'chip_war_agent', 'dividend_risk_agent'
        ]

        redistribution = -actual_adjustment / len(other_agents)
        for agent in other_agents:
            new_weights[agent] = max(0.01, new_weights[agent] + redistribution)

        # 정규화 (합계 = 1.0)
        total = sum(new_weights.values())
        for agent in new_weights:
            new_weights[agent] /= total

        logger.info(f"✅ Weights adjusted: {reason}")
        return new_weights

    def run_daily_learning_cycle(self) -> Dict:
        """
        일일 학습 사이클 실행

        Returns:
            {
                'timestamp': ISO datetime,
                'success': bool,
                'nia_score': float,
                'weight_adjusted': bool,
                'failure_analysis': {...}
            }
        """
        logger.info("🚀 Starting daily learning cycle")

        results = {
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'nia_score': None,
            'weight_adjusted': False
        }

        try:
            # 1. NIA 점수 계산
            nia_score = self.calculate_nia_score(lookback_days=30)
            results['nia_score'] = nia_score

            if nia_score is None:
                return results

            # 2. 실패 분석
            failed_predictions = self.agent.collect_failed_predictions(
                lookback_days=7,
                accuracy_threshold=0.5
            )

            if failed_predictions:
                analysis = self.agent.analyze_failures_batch(failed_predictions)
                results['failure_analysis'] = analysis

            # 3. 가중치 조정
            current_weights = self._get_current_weights()
            new_weights = self.adjust_weights_based_on_nia(nia_score, current_weights)

            # 변화 확인
            weights_changed = any(
                abs(new_weights[a] - current_weights[a]) > 0.001
                for a in current_weights
            )

            if weights_changed:
                saved = self._save_weight_adjustment(
                    old_weights=current_weights,
                    new_weights=new_weights,
                    reason=f"Auto-adjusted based on NIA {nia_score:.2%}"
                )
                results['weight_adjusted'] = saved

            results['success'] = True
            logger.info("✅ Daily learning cycle completed")

        except Exception as e:
            logger.error(f"❌ Learning cycle failed: {e}")
            results['error'] = str(e)

        return results
```

**실행 방법**:

```bash
# 수동 실행
python -m backend.schedulers.failure_learning_scheduler

# APScheduler로 자동 실행 (main.py에서)
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=FailureLearningScheduler().run_daily_learning_cycle,
    trigger='cron',
    hour=0,
    minute=0,
    id='daily_learning',
    name='Daily Failure Learning Cycle'
)
scheduler.start()
```

---

### Correlation Scheduler 상세

**파일**: `backend/schedulers/correlation_scheduler.py`

```python
"""
Correlation Scheduler

매일 01:00 실행:
1. 활성 자산 조회
2. YFinance에서 가격 데이터 다운로드
3. 30d/90d/1y 상관계수 계산
4. asset_correlations 테이블 업데이트
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional

class CorrelationScheduler:
    """상관계수 자동 계산 스케줄러"""

    def __init__(self):
        self.scheduler_name = "CorrelationScheduler"

    def fetch_price_data(
        self,
        symbols: List[str],
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        YFinance에서 가격 데이터 다운로드

        Args:
            symbols: 자산 심볼 리스트
            period: 기간 ('30d', '90d', '1y')

        Returns:
            DataFrame (columns: symbols, index: dates)
        """
        logger.info(f"📥 Downloading price data for {len(symbols)} assets")

        # YFinance 다운로드
        raw_data = yf.download(
            symbols,
            period=period,
            progress=False,
            group_by='ticker'
        )

        # MultiIndex 처리
        if len(symbols) == 1:
            # 단일 심볼
            prices = raw_data['Close'].to_frame(name=symbols[0])
        else:
            # 복수 심볼
            prices = pd.DataFrame()
            for symbol in symbols:
                if (symbol, 'Close') in raw_data.columns:
                    prices[symbol] = raw_data[(symbol, 'Close')]

        # NaN 제거
        prices = prices.dropna()

        logger.info(f"✅ Downloaded {len(prices)} days of data")
        return prices

    def calculate_correlation(
        self,
        prices: pd.DataFrame,
        symbol1: str,
        symbol2: str
    ) -> Optional[float]:
        """
        두 자산 간 상관계수 계산

        Process:
        1. 수익률 계산 (pct_change)
        2. 데이터 정렬
        3. Pearson 상관계수 계산

        Args:
            prices: 가격 DataFrame
            symbol1: 첫 번째 자산
            symbol2: 두 번째 자산

        Returns:
            상관계수 (-1.0 ~ 1.0) or None
        """
        try:
            # 수익률 계산
            returns1 = prices[symbol1].pct_change().dropna()
            returns2 = prices[symbol2].pct_change().dropna()

            # 데이터 정렬
            aligned = pd.concat([returns1, returns2], axis=1).dropna()

            # 최소 데이터 포인트 확인
            if len(aligned) < 10:
                return None

            # Pearson 상관계수
            corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])

            return float(corr) if not np.isnan(corr) else None

        except Exception as e:
            logger.warning(f"⚠️ Correlation calc failed for {symbol1}-{symbol2}: {e}")
            return None

    def calculate_all_correlations(self) -> Dict:
        """
        모든 자산 페어의 상관계수 계산

        Returns:
            {
                'timestamp': ISO datetime,
                'success': bool,
                'assets_count': int,
                'pairs_calculated': int,
                'records_saved': int
            }
        """
        logger.info("🚀 Starting correlation calculation")
        start_time = datetime.now()

        results = {
            'timestamp': start_time.isoformat(),
            'success': False,
            'assets_count': 0,
            'pairs_calculated': 0,
            'records_saved': 0
        }

        try:
            # 1. 활성 자산 조회
            symbols = self._get_active_symbols()
            results['assets_count'] = len(symbols)

            if len(symbols) < 2:
                logger.warning("⚠️ Need at least 2 assets")
                return results

            # 2. 가격 데이터 다운로드
            prices_30d = self.fetch_price_data(symbols, period='30d')
            prices_90d = self.fetch_price_data(symbols, period='90d')
            prices_1y = self.fetch_price_data(symbols, period='1y')

            # 3. 모든 페어 계산
            pairs_calculated = 0
            records_saved = 0

            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i+1:]:
                    # 상관계수 계산
                    corr_30d = self.calculate_correlation(prices_30d, symbol1, symbol2)
                    corr_90d = self.calculate_correlation(prices_90d, symbol1, symbol2)
                    corr_1y = self.calculate_correlation(prices_1y, symbol1, symbol2)

                    pairs_calculated += 1

                    # DB 저장 (Upsert)
                    if any([corr_30d, corr_90d, corr_1y]):
                        saved = self._save_correlation(
                            symbol1=symbol1,
                            symbol2=symbol2,
                            corr_30d=corr_30d,
                            corr_90d=corr_90d,
                            corr_1y=corr_1y
                        )
                        if saved:
                            records_saved += 1

            results['pairs_calculated'] = pairs_calculated
            results['records_saved'] = records_saved
            results['success'] = True

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Correlation calculation completed in {duration:.1f}s")

        except Exception as e:
            logger.error(f"❌ Correlation calculation failed: {e}")
            results['error'] = str(e)

        return results

    def _get_active_symbols(self) -> List[str]:
        """활성 자산 심볼 조회"""
        with get_sync_session() as session:
            from backend.database.models import MultiAssetConfig

            assets = session.query(MultiAssetConfig).filter(
                MultiAssetConfig.is_active == True
            ).all()

            return [asset.symbol for asset in assets]

    def _save_correlation(
        self,
        symbol1: str,
        symbol2: str,
        corr_30d: Optional[float],
        corr_90d: Optional[float],
        corr_1y: Optional[float]
    ) -> bool:
        """상관계수 저장 (Upsert)"""
        try:
            with get_sync_session() as session:
                from backend.database.models import AssetCorrelation

                # Upsert (PostgreSQL)
                stmt = insert(AssetCorrelation).values(
                    symbol1=symbol1,
                    symbol2=symbol2,
                    correlation_30d=corr_30d,
                    correlation_90d=corr_90d,
                    correlation_1y=corr_1y,
                    calculated_at=datetime.now()
                ).on_conflict_do_update(
                    index_elements=['symbol1', 'symbol2'],
                    set_={
                        'correlation_30d': corr_30d,
                        'correlation_90d': corr_90d,
                        'correlation_1y': corr_1y,
                        'calculated_at': datetime.now()
                    }
                )

                session.execute(stmt)
                session.commit()
                return True

        except Exception as e:
            logger.error(f"❌ Failed to save correlation: {e}")
            return False
```

---

## 프론트엔드 아키텍처

### 디렉토리 구조

```
frontend/
├── src/
│   ├── main.tsx                 # 진입점
│   ├── App.tsx                  # 라우팅 설정
│   ├── pages/
│   │   ├── Dashboard.tsx        # 메인 대시보드
│   │   ├── WarRoomPage.tsx      # War Room
│   │   ├── TradingDashboard.tsx # 트레이딩 시그널
│   │   ├── Portfolio.tsx        # 포트폴리오
│   │   ├── MultiAssetDashboard.tsx # 멀티 자산 (개발중)
│   │   ├── PortfolioOptimizationPage.tsx # 포트폴리오 최적화 (개발중)
│   │   ├── CorrelationDashboard.tsx # 자산 상관계수 (개발중)
│   │   ├── FailureLearningDashboard.tsx # 자동 학습
│   │   ├── AccountabilityDashboard.tsx # 책임 추적
│   │   └── ...
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Layout.tsx       # 레이아웃 컨테이너
│   │   │   ├── Sidebar.tsx      # 사이드바
│   │   │   └── Header.tsx       # 헤더
│   │   ├── common/
│   │   │   ├── Card.tsx         # 카드 컴포넌트
│   │   │   ├── Button.tsx       # 버튼 컴포넌트
│   │   │   ├── Badge.tsx        # 배지 컴포넌트
│   │   │   └── ...
│   │   ├── Charts/
│   │   │   ├── LineChart.tsx
│   │   │   ├── BarChart.tsx
│   │   │   └── ...
│   │   └── News/
│   │       ├── NewsCard.tsx
│   │       └── ...
│   ├── contexts/
│   │   └── AnalysisContext.tsx  # 전역 상태 관리
│   ├── hooks/
│   │   └── useQuery.ts          # React Query 훅
│   └── utils/
│       ├── api.ts               # API 클라이언트
│       └── formatters.ts        # 포맷팅 유틸
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### 라우팅 구조 (App.tsx)

```typescript
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout/Layout';

const App: React.FC = () => {
  return (
    <Router>
      <Layout>
        <Routes>
          {/* Overview */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/dividend" element={<DividendDashboard />} />

          {/* Trading & Strategy */}
          <Route path="/war-room" element={<WarRoomPage />} />
          <Route path="/trading" element={<TradingDashboard />} />
          <Route path="/backtest" element={<BacktestDashboard />} />
          <Route path="/deep-reasoning" element={<DeepReasoning />} />

          {/* Analysis */}
          <Route path="/global-macro" element={<GlobalMacro />} />
          <Route path="/ceo-analysis" element={<CEOAnalysis />} />
          <Route path="/analysis" element={<Analysis />} />

          {/* Data & News */}
          <Route path="/data-backfill" element={<DataBackfill />} />
          <Route path="/news" element={<NewsAggregation />} />
          <Route path="/rss-management" element={<RssFeedManagement />} />

          {/* System & Operations */}
          <Route path="/monitor" element={<Monitor />} />
          <Route path="/accountability" element={<AccountabilityDashboard />} />
          <Route path="/learning" element={<FailureLearningDashboard />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/settings" element={<Settings />} />

          {/* Under Development */}
          <Route path="/signal-consolidation" element={<SignalConsolidationPage />} />
          <Route path="/multi-asset" element={<MultiAssetDashboard />} />
          <Route path="/portfolio-optimization" element={<PortfolioOptimizationPage />} />
          <Route path="/correlation" element={<CorrelationDashboard />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
```

### 사이드바 구조 (Sidebar.tsx)

```typescript
const navCategories: NavCategory[] = [
  {
    title: 'Overview',
    items: [
      { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      { path: '/portfolio', icon: PieChart, label: 'Portfolio' },
      { path: '/dividend', icon: DollarSign, label: 'Dividend Intelligence' },
    ]
  },
  {
    title: 'Trading & Strategy',
    items: [
      { path: '/war-room', icon: MessageSquare, label: 'AI War Room' },
      { path: '/trading', icon: Zap, label: 'Trading Signals' },
      { path: '/backtest', icon: TestTube2, label: 'Backtest' },
      { path: '/deep-reasoning', icon: Brain, label: 'Deep Reasoning' },
    ]
  },
  {
    title: 'Analysis',
    items: [
      { path: '/global-macro', icon: Globe, label: 'Global Macro' },
      { path: '/ceo-analysis', icon: MessageSquare, label: 'CEO Analysis' },
      { path: '/analysis', icon: TrendingUp, label: 'Analysis' },
      { path: '/cost-report', icon: DollarSign, label: 'Emergency Cost' },
      { path: '/advanced-analytics', icon: LineChart, label: 'Advanced Analytics' },
      { path: '/ai-review', icon: FileText, label: 'AI Review' },
    ]
  },
  {
    title: 'Data & News',
    items: [
      { path: '/data-backfill', icon: Database, label: 'Data Backfill' },
      { path: '/news', icon: Newspaper, label: 'News' },
      { path: '/rss-management', icon: Rss, label: 'RSS Management' },
    ]
  },
  {
    title: 'System & Operations',
    items: [
      { path: '/monitor', icon: Activity, label: 'Monitor' },
      { path: '/accountability', icon: Target, label: 'Accountability' },
      { path: '/learning', icon: GraduationCap, label: 'Auto-Learning' },
      { path: '/reports', icon: BarChart3, label: 'Reports' },
      { path: '/incremental', icon: TrendingDown, label: 'Cost Savings' },
      { path: '/logs', icon: FileSearch, label: 'Logs' },
      { path: '/settings', icon: Settings, label: 'Settings' },
    ]
  },
  {
    title: 'Under Development',
    items: [
      { path: '/signal-consolidation', icon: BarChart3, label: 'Signal Consolidation' },
      { path: '/multi-asset', icon: Coins, label: 'Multi-Asset' },
      { path: '/portfolio-optimization', icon: Target, label: 'Portfolio Optimization' },
      { path: '/correlation', icon: Network, label: 'Asset Correlation' },
    ]
  }
];
```

### React Query 사용 예시

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// GET 요청 (자동 refetch)
const { data, isLoading, error } = useQuery({
  queryKey: ['correlation-status'],
  queryFn: async () => {
    const response = await fetch('/api/correlation/status');
    return response.json();
  },
  refetchInterval: 60000  // 1분마다 자동 갱신
});

// POST 요청 (Mutation)
const queryClient = useQueryClient();

const mutation = useMutation({
  mutationFn: async () => {
    const response = await fetch('/api/correlation/calculate', {
      method: 'POST'
    });
    return response.json();
  },
  onSuccess: () => {
    // 성공 시 관련 쿼리 무효화 (자동 refetch)
    queryClient.invalidateQueries({ queryKey: ['correlation-status'] });
    queryClient.invalidateQueries({ queryKey: ['correlation-pairs'] });
  }
});

// UI에서 사용
<button onClick={() => mutation.mutate()}>
  Calculate Correlations
</button>
```

---

## 데이터 흐름

### War Room 의사결정 프로세스

```
[사용자] → [War Room UI] → [POST /api/war-room/decide]
                                      ↓
                            [PM Agent 호출]
                                      ↓
           ┌──────────────────────────┴──────────────────────────┐
           │              각 에이전트 병렬 실행                    │
           ├────────┬────────┬────────┬────────┬────────┬────────┤
           ▼        ▼        ▼        ▼        ▼        ▼        ▼
        Trader   Risk   Analyst  Macro  Instit  News   Chip   Dividend
        Agent    Agent   Agent   Agent  Agent   Agent  Agent   Agent
           │        │        │        │        │        │        │
           └────────┴────────┴────────┴────────┴────────┴────────┘
                                      ↓
                            [가중치 적용 종합]
                                      ↓
                          [PM 최종 의사결정]
                                      ↓
                ┌───────────────────┴───────────────────┐
                ▼                                       ▼
       [Trading Signal 생성]              [War Room 대화 저장]
                ↓                                       ↓
         [trading_signals]                [war_room_conversations]
                ↓
         [Response to UI]
```

### 뉴스 분석 → 예측 → 검증 → 학습 사이클

```
[RSS 피드] → [NewsScheduler (15분)] → [news_articles]
                                              ↓
                                    [News Agent 해석]
                                              ↓
                                  [news_interpretations]
                                              ↓
                              [시장 반응 예측 저장]
                                              ↓
                                [news_market_reactions]
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
          [+1일 후 검증]              [+1주 후 검증]              [+1개월 후 검증]
       (VerificationScheduler)    (VerificationScheduler)    (VerificationScheduler)
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              ↓
                                    [accuracy_1d/1w/1m 업데이트]
                                              ↓
                              [FailureLearningScheduler (매일 00:00)]
                                              ↓
                                    [NIA 점수 계산]
                                              ↓
                                  [실패 예측 분석]
                                              ↓
                                 [가중치 자동 조정]
                                              ↓
                             [agent_weights_history 저장]
                                              ↓
                                [다음 War Room에 반영]
```

---

## API 엔드포인트

### 전체 API 목록

#### Trading APIs (`/api/trading`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trading/signals` | 트레이딩 시그널 목록 |
| GET | `/api/trading/signals/{id}` | 시그널 상세 |
| POST | `/api/trading/signals` | 시그널 생성 (수동) |
| PUT | `/api/trading/signals/{id}/execute` | 시그널 실행 |
| DELETE | `/api/trading/signals/{id}` | 시그널 취소 |

#### War Room APIs (`/api/war-room`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/war-room/decide` | War Room 의사결정 실행 |
| GET | `/api/war-room/conversations` | 대화 기록 조회 |
| GET | `/api/war-room/conversations/{id}` | 특정 대화 상세 |
| GET | `/api/war-room/weights` | 현재 에이전트 가중치 |

#### News APIs (`/api/news`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/news/articles` | 뉴스 기사 목록 |
| GET | `/api/news/articles/{id}` | 기사 상세 |
| GET | `/api/news/interpretations` | 뉴스 해석 목록 |
| POST | `/api/news/analyze` | 뉴스 분석 (수동) |
| GET | `/api/news/nia-score` | NIA 점수 조회 |

#### Portfolio APIs (`/api/portfolio`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portfolio/summary` | 포트폴리오 요약 |
| GET | `/api/portfolio/positions` | 현재 포지션 |
| GET | `/api/portfolio/history` | 히스토리 |
| POST | `/api/portfolio/optimize` | 포트폴리오 최적화 |

#### Correlation APIs (`/api/correlation`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/correlation/calculate` | 상관계수 계산 (수동) |
| GET | `/api/correlation/status` | 계산 상태 |
| GET | `/api/correlation/heatmap` | 히트맵 데이터 |
| GET | `/api/correlation/pairs` | Top 상관 페어 |

#### Learning APIs (`/api/learning`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/learning/run` | 학습 사이클 실행 (수동) |
| GET | `/api/learning/nia` | NIA 점수 조회 |
| GET | `/api/learning/history` | 가중치 히스토리 |
| GET | `/api/learning/recommendations` | 가중치 조정 제안 |
| GET | `/api/learning/current-weights` | 현재 가중치 |

#### Accountability APIs (`/api/accountability`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/accountability/decisions` | 의사결정 로그 |
| GET | `/api/accountability/failures` | 실패 분석 |
| GET | `/api/accountability/performance` | 에이전트 성능 |

---

## 보안 및 인증

### 환경 변수 관리

**파일**: `.env`

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_trading

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Application
SECRET_KEY=your_secret_key_here
DEBUG=false

# CORS
CORS_ORIGINS=http://localhost:3002,http://localhost:3000

# Trading (Paper Trading)
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### API 인증 (Future)

현재는 인증 없이 로컬에서만 실행되지만, 향후 추가 예정:

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@router.get("/protected")
async def protected_route(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    # JWT 검증
    user = verify_jwt_token(token)
    return {"user": user}
```

---

## 배포 및 운영

### Docker Compose 구성

**파일**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14
    container_name: ai-trading-db
    environment:
      POSTGRES_USER: ai_trading
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: ai_trading
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ai-trading-network

  # Backend (FastAPI)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ai-trading-backend
    environment:
      DATABASE_URL: postgresql://ai_trading:secure_password@postgres:5432/ai_trading
      GEMINI_API_KEY: ${GEMINI_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    networks:
      - ai-trading-network
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000

  # Frontend (React + Vite)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ai-trading-frontend
    ports:
      - "3002:3002"
    depends_on:
      - backend
    networks:
      - ai-trading-network

  # Nginx (Reverse Proxy)
  nginx:
    image: nginx:alpine
    container_name: ai-trading-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    networks:
      - ai-trading-network

volumes:
  postgres_data:

networks:
  ai-trading-network:
    driver: bridge
```

### 실행 방법

```bash
# 개발 환경
cd backend && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev

# Docker Compose
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 중지
docker-compose down
```

---

## 주요 프로세스 정리

### 1. 시스템 초기화

```
1. PostgreSQL 데이터베이스 시작
2. FastAPI 백엔드 시작
   - DB 연결 확인
   - 라우터 등록
   - 스케줄러 시작
3. React 프론트엔드 시작
4. 사용자 접속 (http://localhost:3002)
```

### 2. War Room 의사결정

```
1. 사용자가 종목 선택 (예: AAPL)
2. PM Agent에게 질문 ("AAPL 매수 의견은?")
3. PM이 8개 에이전트에게 질문 배포
4. 각 에이전트가 Gemini API로 분석
5. PM이 가중치 기반으로 종합 판단
6. Trading Signal 생성
7. War Room 대화 저장
8. 사용자에게 결과 표시
```

### 3. 뉴스 분석 및 학습

```
1. NewsScheduler가 15분마다 RSS 수집
2. News Agent가 뉴스 해석
3. 시장 반응 예측 저장
4. 1일/1주/1개월 후 검증
5. NIA 점수 계산
6. 낮은 정확도 예측 분석
7. 가중치 자동 조정
8. 다음 War Room에 반영
```

### 4. 포트폴리오 최적화

```
1. 사용자가 최적화 목표 선택 (Max Sharpe)
2. 활성 자산 조회
3. 가격 데이터 다운로드 (YFinance)
4. 상관계수 조회
5. scipy.optimize로 최적 가중치 계산
6. 결과 저장 및 표시
7. 백테스트 실행 (옵션)
```

### 5. 상관계수 계산

```
1. CorrelationScheduler 매일 01:00 실행
2. 활성 자산 조회 (multi_asset_config)
3. YFinance에서 30d/90d/1y 가격 다운로드
4. 모든 페어 조합 (N*(N-1)/2)
5. Pearson 상관계수 계산
6. asset_correlations 테이블 upsert
7. Correlation Dashboard에 표시
```

---

## 성능 최적화

### 데이터베이스 최적화

```sql
-- 인덱스 추가
CREATE INDEX idx_signals_symbol_created ON trading_signals(symbol, created_at DESC);
CREATE INDEX idx_news_symbol_created ON news_interpretations(symbol, created_at DESC);
CREATE INDEX idx_correlation_symbols ON asset_correlations(symbol1, symbol2);

-- 파티셔닝 (대용량 데이터)
CREATE TABLE trading_signals_2025 PARTITION OF trading_signals
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### API 캐싱

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# Redis 캐싱
@router.get("/status")
@cache(expire=60)  # 60초 캐시
async def get_status():
    # 무거운 계산
    pass
```

### React Query 최적화

```typescript
// Stale time 설정
const { data } = useQuery({
  queryKey: ['heavy-data'],
  queryFn: fetchHeavyData,
  staleTime: 5 * 60 * 1000,  // 5분간 fresh
  cacheTime: 10 * 60 * 1000  // 10분간 캐시 유지
});
```

---

## 모니터링 및 로깅

### 로깅 설정

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

logger.info("✅ Server started")
logger.warning("⚠️ High API usage detected")
logger.error("❌ Database connection failed")
```

### 헬스 체크

```python
@app.get("/health")
async def health_check():
    """시스템 헬스 체크"""
    try:
        # DB 연결 확인
        with get_sync_session() as session:
            session.execute("SELECT 1")

        # Gemini API 확인
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        return {
            "status": "healthy",
            "database": "connected",
            "gemini_api": "available",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## 결론

이 문서는 AI Trading System의 전체 아키텍처를 다룹니다:

✅ **데이터베이스**: PostgreSQL 테이블 구조 및 관계
✅ **백엔드**: FastAPI 라우터, AI 에이전트, 스케줄러
✅ **프론트엔드**: React 컴포넌트, 라우팅, 상태 관리
✅ **데이터 흐름**: War Room, 뉴스 분석, 학습 사이클
✅ **API**: 전체 엔드포인트 목록
✅ **배포**: Docker Compose 구성

**다음 단계**:
- 실전 트레이딩 연동 (Alpaca API)
- 백테스트 엔진 고도화
- 리스크 관리 자동화
- 알림 시스템 구축
