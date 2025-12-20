# 01. AI Trading System - 시스템 아키텍처

**문서 시리즈**: AI Trading System Spec-Kit 문서  
**문서 번호**: 01/06  
**작성일**: 2025-12-06  
**이전 문서**: [251210_00_Project_Overview.md](251210_00_Project_Overview.md)  
**다음 문서**: [251210_02_Development_Roadmap.md](251210_02_Development_Roadmap.md)

---

## 📋 목차

1. [전체 시스템 아키텍처](#1-전체-시스템-아키텍처)
2. [레이어별 상세 설계](#2-레이어별-상세-설계)
3. [데이터 플로우](#3-데이터-플로우)
4. [기술 스택 상세](#4-기술-스택-상세)
5. [인프라 아키텍처](#5-인프라-아키텍처)
6. [보안 아키텍처](#6-보안-아키텍처)

---

## 1. 전체 시스템 아키텍처

### 1.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Dashboard  │  │  Analytics  │  │ CEO Analysis│          │
│  │   Trading   │  │    Risk     │  │  RSS  Feeds │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│         React 18 + TypeScript + Tailwind CSS                 │
│                        Port 3000                              │
└──────────────────────────────────────────────────────────────┘
                            ↓ REST API (JSON)
┌──────────────────────────────────────────────────────────────┐
│               FastAPI Backend (30+ APIs)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ News API    │  │Backtest API │  │Consensus API│          │
│  │ Signal API  │  │ Trading API │  │ Phase API   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│         FastAPI 0.104+ + Pydantic v2 + Async                 │
│                        Port 5000/8000                         │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│            AI Ensemble Layer (3 Models)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Gemini    │  │  ChatGPT    │  │Claude Haiku │          │
│  │   1.5 Pro   │  │    GPT-4    │  │    4.0      │          │
│  │ (Reasoning) │  │(Market Regime)│ │(Decision)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│         Consensus Engine (3-AI Voting System)                │
│    STOP_LOSS: 1/3 | BUY: 2/3 | DCA: 3/3                      │
└────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                 Data & Caching Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Redis 7   │  │ TimescaleDB │  │ PostgreSQL  │          │
│  │ (L1 Cache)  │  │   2.13      │  │     15      │          │
│  │  TTL 15min  │  │(Time Series)│  │(RAG/Vector) │          │
│  │  < 5ms      │  │   < 100ms   │  │  + pgvector │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐                                             │
│  │   SQLite    │ (뉴스, 로그, KnowledgeGraph)                │
│  │   (Local)   │                                             │
│  └─────────────┘                                             │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│              External APIs & Services (무료)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │Yahoo Finance│  │  SEC EDGAR  │  │  NewsAPI    │          │
│  │   (OHLCV)   │  │  (10-Q/K)   │  │ (100/day)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  RSS Feeds  │  │  FRED API   │  │  KIS API    │          │
│  │  (50+)      │  │  (경제지표)  │  │  (실거래)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 핵심 설계 원칙

**1. 2-Layer 캐싱 전략**
- L1 (Redis): In-Memory, < 5ms, 15분 TTL
- L2 (TimescaleDB): 시계열 DB, < 100ms, 영구 보관
- 캐시 히트율: 96.4%

**2. AI 모델 역할 분리**
- Gemini Flash: 스크리닝 (저비용, 빠름)
- Gemini Pro: 심층 추론 (Deep Reasoning)
- Claude Haiku: 최종 매매 결정 (균형)
- ChatGPT-4: 시장 체제 감지

**3. 비동기 처리**
- FastAPI + asyncio 전면 사용
- 병렬 AI 호출 (asyncio.gather)
- Non-blocking DB 쿼리 (asyncpg)

**4. 보안 최우선**
- 4계층 방어 (URL, 텍스트, 웹훅, 유니코드)
- API Key 인증 (계층적 권한)
- Audit Logging (모든 API 호출)

---

## 2. 레이어별 상세 설계

### 2.1 Frontend Layer

**기술 스택**:
```
React 18.2+ (UI 프레임워크)
├── TypeScript 5.0+ (타입 안전성)
├── Tailwind CSS 3.3+ (스타일링)
├── Recharts (차트 시각화)
├── Axios (HTTP 클라이언트)
├── React Query (상태 관리)
└── Vite (빌드 툴)
```

**주요 페이지**:
- Dashboard.tsx - 메인 대시보드 (포트폴리오, 시그널)
- AdvancedAnalytics.tsx - 성과/리스크/트레이드 분석
- CEOAnalysis.tsx - SEC 문서 CEO 발언 분석
- RssFeedManagement.tsx - RSS 피드 관리
- AIReviewPage.tsx - AI 검토 결과

**컴포넌트 구조**:
```
src/
├── pages/ (페이지 컴포넌트)
├── components/
│   ├── Analytics/ (분석 차트)
│   ├── Layout/ (레이아웃)
│   └── common/ (공통 컴포넌트)
└── services/
    ├── api.ts (API 클라이언트)
    ├── analyticsApi.ts
    └── reportsApi.ts
```

### 2.2 Backend API Layer

**라우터 구조** (29개 API 라우터):

```python
backend/api/
├── news_router.py              # 뉴스 조회/분석
├── signals_router.py           # 트레이딩 시그널
├── backtest_router.py          # 백테스팅
├── consensus_router.py         # Consensus 투표 (Phase E1)
├── reasoning_api.py            # Deep Reasoning (Phase 14)
├── trading_router.py           # 실거래 (KIS)
├── reports_router.py           # 리포팅
├── ai_review_router.py         # AI 검토
├── feeds_router.py             # RSS 피드 관리
├── ceo_analysis_router.py      # CEO 분석
├── forensics_router.py         # Forensic Accounting
├── options_flow_router.py      # 옵션 플로우
├── incremental_router.py       # 증분 업데이트
└── ... (16개 추가 라우터)
```

**API 패턴**:
```python
# 전형적인 API 엔드포인트 구조
@router.post("/api/consensus/vote")
async def vote_on_signal(
    request: VoteRequest,
    api_key: APIKey = Depends(get_api_key)
):
    # 1. 인증 (API Key)
    # 2. 입력 검증 (Pydantic)
    # 3. 비즈니스 로직 (AI 호출)
    # 4. Audit Logging
    # 5. 응답 반환 (JSON)
    pass
```

### 2.3 AI Ensemble Layer

**Consensus Engine 구조**:

```python
# backend/ai/consensus/consensus_engine.py
class ConsensusEngine:
    async def vote_on_signal(
        context: MarketContext,
        action: str
    ) -> ConsensusResult:
        # 3개 AI 병렬 투표
        votes = await asyncio.gather(
            self.claude.vote(context, action),
            self.chatgpt.vote(context, action),
            self.gemini.vote(context, action)
        )
        
        # 비대칭 규칙 적용
        approved = VotingRules.is_approved(action, votes)
        
        return ConsensusResult(
            approved=approved,
            votes=votes,
            consensus_strength=self.calc_strength(votes)
        )
```

**Deep Reasoning 구조**:

```python
# backend/ai/reasoning/deep_reasoning.py
class DeepReasoningStrategy:
    async def analyze_news(news_text: str):
        # Step 1: Direct Impact
        primary = await self.find_primary_beneficiary(news_text)
        
        # Step 2: Secondary Impact (꼬리 물기)
        secondary = await self.find_secondary_impact(primary)
        
        # Step 3: Strategic Conclusion
        hidden = await self.find_hidden_beneficiary(secondary)
        
        return ReasoningResult(
            primary=primary,
            hidden=hidden,
            reasoning_trace=[...]
        )
```

### 2.4 Data Layer

**Redis (L1 Cache)**:
```python
# backend/data/feature_store/cache_layer.py
class CacheLayer:
    def __init__(self):
        self.redis = Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        self.ttl = 900  # 15분
    
    async def get(self, key: str):
        # 캐시 조회 (< 5ms)
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: dict):
        # 캐시 저장
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(value)
        )
```

**TimescaleDB (L2 Store)**:
```sql
-- 시계열 Hypertable
CREATE TABLE features (
    ticker VARCHAR(20),
    feature_name VARCHAR(50),
    value DOUBLE PRECISION,
    as_of_timestamp TIMESTAMPTZ,  -- Point-in-Time
    calculated_at TIMESTAMPTZ,
    version INTEGER,
    PRIMARY KEY (ticker, feature_name, as_of_timestamp)
);

SELECT create_hypertable('features', 'as_of_timestamp');

-- 자동 압축 (90일 이후)
SELECT add_compression_policy('features', INTERVAL '90 days');
```

**PostgreSQL (RAG + Vector)**:
```sql
-- pgvector 확장
CREATE EXTENSION IF NOT EXISTS vector;

-- 임베딩 테이블
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(100),
    chunk_text TEXT,
    embedding vector(1536),  -- OpenAI ada-002
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 벡터 인덱스 (HNSW)
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);
```

---

## 3. 데이터 플로우

### 3.1 뉴스 기반 트레이딩 플로우

```
1. RSS Crawler (24/7 실행)
   ↓
2. News DB (SQLite) 저장
   ↓
3. AI News Analyzer
   - 감성 분석 (긍정/부정/중립)
   - 티커 관련성 스코어링
   - 리스크 카테고리 분류
   ↓
4. Signal Generator
   - 매수/매도 시그널 생성
   - 목표가/손절가 계산
   ↓
5. Consensus Engine (Phase E1)
   - 3-AI 투표
   - 비대칭 의사결정
   ↓
6. Position Tracker (Phase E3)
   - 포지션 업데이트
   - DCA 횟수 추적
   ↓
7. KIS Broker (자동 주문)
   - 실거래 주문 실행
   ↓
8. Telegram/Slack 알림
```

### 3.2 Deep Reasoning 플로우

```
1. 뉴스 입력 ("Google TPU v6 발표")
   ↓
2. Entity Extraction
   - "Google", "TPU", "v6" 추출
   ↓
3. Knowledge Graph Lookup
   - Google → Broadcom 관계 조회
   ↓
4. Live Verification (웹 검색)
   - "Broadcom TPU interconnect" 검색
   ↓
5. 3-Step CoT Reasoning
   - Step 1: Google 직접 호재
   - Step 2: TPU 확대 → Nvidia 의존↓
   - Step 3: Broadcom(TPU 설계) 수혜
   ↓
6. Actionable Signals
   - Primary: GOOGL (BUY)
   - Hidden: AVGO (BUY)
   - Loser: NVDA (TRIM)
```

### 3.3 백테스팅 플로우

```
1. Backtest Request
   - 시작일/종료일 설정
   - 전략 선택 (DCA + Consensus)
   ↓
2. Historical Data Loader
   - Yahoo Finance 과거 데이터
   - Point-in-Time 뉴스
   ↓
3. Event-Driven Simulation
   - 각 날짜별 시뮬레이션
   - Lookahead Bias 제거
   ↓
4. Consensus 투표 (과거 데이터)
   - 3-AI 투표 재현
   ↓
5. Portfolio Update
   - 포지션 추가/제거
   - PnL 계산
   ↓
6. Performance Report
   - Sharpe Ratio, Win Rate
   - Max Drawdown
   - AI별 정확도
```

---

## 4. 기술 스택 상세

### 4.1 Backend Stack

**프레임워크 \u0026 라이브러리**:
```python
# requirements.txt (주요 항목)
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.2
pydantic-settings==2.1.0

# Database
redis==5.0.1
asyncpg==0.29.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# AI APIs
anthropic==0.7.8
google-generativeai==0.3.2
openai==1.3.7

# Data
yfinance==0.2.33
pandas==2.1.4
numpy==1.26.2

# Monitoring
prometheus-client==0.19.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

**Python 버전**: 3.11+ (필수)

### 4.2 Database Versions

```
Redis: 7.2.3
TimescaleDB: 2.13.0 (PostgreSQL 15 기반)
PostgreSQL: 15.5 (pgvector 0.5.1)
SQLite: 3.42+
```

### 4.3 AI Model Versions

```
Claude: Sonnet 4.5, Haiku 4.0
Gemini: 1.5 Pro, 1.5 Flash
GPT: GPT-4, GPT-4o-mini
```

---

## 5. 인프라 아키텍처

### 5.1 Docker Compose 구성

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
  
  timescaledb:
    image: timescale/timescaledb:2.13.0-pg15
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: ${TIMESCALE_PASSWORD}
      POSTGRES_DB: ai_trading
    volumes:
      - timescale_data:/var/lib/postgresql/data
  
  postgres:
    image: pgvector/pgvector:pg15
    ports:
      - "5433:5432"
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: rag_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  prometheus:
    image: prom/prometheus:v2.48.0
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
  
  grafana:
    image: grafana/grafana:10.2.2
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
```

### 5.2 Deployment 옵션

**옵션 1: 로컬 개발**
```bash
docker-compose up -d
python backend/main.py
cd frontend && npm run dev
```

**옵션 2: Synology NAS 배포**
```bash
# NAS SSH 접속
ssh admin@nas.local

# 프로젝트 복사
cd /volume1/ai_trading
git pull

# Docker 빌드 및 실행
docker-compose -f docker-compose.prod.yml up -d --build
```

**옵션 3: 클라우드 (AWS/GCP)**
```bash
# Docker Hub 푸시
docker build -t ai-trading-backend -f Dockerfile.prod .
docker push username/ai-trading-backend

# Kubernetes 배포 (선택)
kubectl apply -f k8s/deployment.yaml
```

---

## 6. 보안 아키텍처

### 6.1 4계층 방어 구조

```
┌─────────────────────────────────────────┐
│ Layer 1: URL 검증                        │
│ - Data Exfiltration 도메인 차단         │
│ - URL Shortener 차단                    │
│ - Typosquatting 탐지                    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ Layer 2: 텍스트 살균 (★ 핵심)           │
│ - Prompt Injection 패턴 차단 (95%)      │
│ - HTML 숨김 텍스트 제거                 │
│ - 시스템 파일 접근 차단 (cat .env)      │
│ - Zero-width characters 제거            │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ Layer 3: 웹훅 보안                       │
│ - SSRF 공격 차단 (localhost, 내부 IP)   │
│ - HTTPS 강제 (MITM 방어)                │
│ - HMAC 서명 검증                        │
│ - Replay Attack 탐지                    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ Layer 4: 유니코드 검증                   │
│ - Homograph 공격 탐지 (85%)             │
│ - RTL Override 차단                     │
│ - Mixed Script 탐지                     │
└─────────────────────────────────────────┘
```

### 6.2 API 인증 체계

```python
# backend/auth.py
class APIKeyAuth:
    def __init__(self):
        self.keys = {
            "admin_key": {"role": "admin", "permissions": ["read", "write", "execute"]},
            "read_key": {"role": "readonly", "permissions": ["read"]},
            "trade_key": {"role": "trader", "permissions": ["read", "write"]}
        }
    
    def verify(self, api_key: str, required_permission: str) -> bool:
        if api_key not in self.keys:
            raise HTTPException(401, "Invalid API key")
        
        permissions = self.keys[api_key]["permissions"]
        if required_permission not in permissions:
            raise HTTPException(403, "Insufficient permissions")
        
        return True
```

### 6.3 Audit Logging

```python
# backend/log_manager.py
async def log_api_call(
    endpoint: str,
    api_key: str,
    request_body: dict,
    response: dict,
    duration_ms: float
):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "api_key_role": get_role(api_key),
        "request_size_bytes": len(json.dumps(request_body)),
        "response_status": response.get("status"),
        "duration_ms": duration_ms,
        "ip_address": get_client_ip()
    }
    
    # SQLite 저장
    await db.insert("audit_logs", log_entry)
    
    # Prometheus 메트릭
    api_calls_total.labels(endpoint=endpoint).inc()
    api_duration.labels(endpoint=endpoint).observe(duration_ms / 1000)
```

---

## 📊 성능 벤치마크

### 캐시 성능
```
Request 1 (Cache Miss):      2847.23 ms  [████████████████████]
Request 2 (Redis Hit):          3.93 ms  [█] 725x faster
Request 3 (TimescaleDB):       89.34 ms  [██] 32x faster
```

### API 응답 시간 (p99)
```
GET  /news:               15ms
POST /signals/generate:   45ms
POST /consensus/vote:     120ms (3-AI 호출)
POST /backtest/run:       8500ms (시뮬레이션)
```

### 동시 처리 능력
```
최대 동시 요청:  100 req/sec
평균 레이턴시:   45ms
에러율:         < 0.01%
```

---

## 🔗 관련 문서

- **이전**: [251210_00_Project_Overview.md](251210_00_Project_Overview.md)
- **다음**: [251210_02_Development_Roadmap.md](251210_02_Development_Roadmap.md)
- **참조**: [251210_MASTER_GUIDE.md](251210_MASTER_GUIDE.md)

---

**문서 버전**: 1.0  
**작성자**: AI Trading System Team  
**마지막 업데이트**: 2025-12-06
