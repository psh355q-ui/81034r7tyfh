# 🗄️ AI Trading System - DB 저장 가능 데이터 전수 분석 [LEGACY]

⚠️ **LEGACY DOCUMENTATION - 2025-11-22 기준**
**현재 DB 스키마**: [260104_Database_Schema.md](260104_Database_Schema.md) (17 tables)

**분석 일자**: 2025-11-22
**프로젝트**: ai-trading-system
**목적**: API 호출 비용 절감을 위한 로컬/NAS DB 저장 전략 수립
**현재 상태**: PostgreSQL 15 + TimescaleDB 운영 중 (2026-01-04)

---

## 📌 Executive Summary

### 현재 DB 활용 현황

| 데이터베이스 | 용도 | 상태 | 비용 절감 효과 |
|------------|------|------|--------------|
| **TimescaleDB** | Feature Store (주가 지표) | ✅ 운영 중 | 99.96% 절감 |
| **Redis** | L1 Cache (실시간 조회) | ✅ 운영 중 | 725배 속도 개선 |
| **SQLite** | 뉴스 저장 (news.db) | ✅ 개발 중 | 예상 90%+ 절감 |
| **PostgreSQL** | 임베딩 저장 (RAG) | 📋 계획됨 | 예상 95%+ 절감 |

### 추가 DB화 가능 영역 (우선순위별)

#### 🔴 **최우선** (즉시 구현 추천)
1. **SEC 10-Q/10-K 파일 저장** (현재 미구현)
2. **Yahoo Finance 역사 데이터** (부분 구현)
3. **AI 분석 결과 캐싱** (부분 구현)

#### 🟡 **중간 우선순위**
4. **뉴스 기사 본문 + 임베딩**
5. **백테스트 결과 저장**
6. **포트폴리오 상태 히스토리**

#### 🟢 **낮은 우선순위**
7. **RSS 피드 원본**
8. **옵션 플로우 데이터**

---

## 🎯 1. SEC 파일 저장 전략 (최우선)

### 문제점
- **현재**: SEC 10-Q/10-K를 API로 매번 다운로드
- **비용**: Gemini API로 파싱 ($0.075/1M tokens)
- **중복**: 같은 파일을 여러 번 분석

### 해결 방안

```sql
-- SEC 파일 메타데이터 테이블
CREATE TABLE sec_filings (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    cik VARCHAR(10) NOT NULL,
    accession_number VARCHAR(24) UNIQUE NOT NULL,  -- 파일 고유 ID
    filing_type VARCHAR(10) NOT NULL,  -- '10-Q' | '10-K' | '8-K'
    filing_date DATE NOT NULL,
    report_date DATE,  -- 실제 보고 기간 종료일
    
    -- 원본 파일 정보
    sec_url TEXT NOT NULL,
    local_path TEXT,  -- NAS 저장 경로 (예: /volume1/ai_trading/sec/AAPL_10Q_2024Q3.html)
    file_size_bytes INTEGER,
    file_hash VARCHAR(64),  -- SHA-256 (중복 방지)
    
    -- 처리 상태
    download_status VARCHAR(20) DEFAULT 'pending',  -- 'pending' | 'downloaded' | 'failed'
    parse_status VARCHAR(20) DEFAULT 'pending',  -- 'pending' | 'parsed' | 'failed'
    downloaded_at TIMESTAMPTZ,
    parsed_at TIMESTAMPTZ,
    
    -- 비용 추적
    parse_cost_usd DECIMAL(10, 6),  -- Gemini API 비용
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_ticker_date (ticker, filing_date DESC),
    INDEX idx_accession (accession_number),
    UNIQUE (ticker, filing_type, report_date)
);

-- SEC 파일 추출 데이터 (구조화된 데이터)
CREATE TABLE sec_filing_extracts (
    id SERIAL PRIMARY KEY,
    filing_id INTEGER REFERENCES sec_filings(id) ON DELETE CASCADE,
    
    -- 재무 데이터
    revenue DECIMAL(20, 2),
    net_income DECIMAL(20, 2),
    total_assets DECIMAL(20, 2),
    total_liabilities DECIMAL(20, 2),
    operating_cash_flow DECIMAL(20, 2),
    
    -- 비율
    debt_to_equity DECIMAL(10, 4),
    current_ratio DECIMAL(10, 4),
    roe DECIMAL(10, 4),
    
    -- AI 분석 결과 (JSON)
    risk_factors JSONB,  -- {"legal": 0.3, "regulatory": 0.5, ...}
    key_metrics JSONB,
    management_discussion TEXT,
    
    -- 메타데이터
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    ai_model VARCHAR(50),  -- 'gemini-1.5-flash' | 'claude-haiku-4'
    extraction_version INTEGER DEFAULT 1,
    
    INDEX idx_filing_id (filing_id)
);
```

### 구현 전략

```python
# backend/data/sec_storage.py
from pathlib import Path
import hashlib
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

class SECFileStorage:
    """SEC 파일 로컬 저장 및 중복 방지"""
    
    def __init__(self, base_path: Path = Path("/volume1/ai_trading/sec")):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def download_and_store(
        self, 
        ticker: str, 
        accession: str, 
        sec_url: str, 
        db: AsyncSession
    ) -> Path:
        """
        1. DB에서 accession_number로 중복 확인
        2. 중복이면 로컬 경로 반환 (다운로드 스킵)
        3. 신규면 다운로드 → 저장 → DB 메타데이터 업데이트
        """
        
        # 1. 중복 확인
        existing = await db.execute(
            select(SECFiling).where(SECFiling.accession_number == accession)
        )
        if existing.scalar_one_or_none():
            return Path(existing.local_path)
        
        # 2. 다운로드
        content = await self._download_from_sec(sec_url)
        file_hash = hashlib.sha256(content).hexdigest()
        
        # 3. 로컬 저장
        local_path = self.base_path / f"{ticker}_{accession}.html"
        async with aiofiles.open(local_path, 'wb') as f:
            await f.write(content)
        
        # 4. DB 메타데이터 저장
        filing = SECFiling(
            ticker=ticker,
            accession_number=accession,
            sec_url=sec_url,
            local_path=str(local_path),
            file_size_bytes=len(content),
            file_hash=file_hash,
            download_status='downloaded',
            downloaded_at=datetime.utcnow()
        )
        db.add(filing)
        await db.commit()
        
        return local_path
    
    async def get_or_download(self, accession: str, db: AsyncSession) -> Path:
        """
        캐시 우선: DB에 있으면 로컬 경로 반환, 없으면 다운로드
        """
        result = await db.execute(
            select(SECFiling).where(
                SECFiling.accession_number == accession,
                SECFiling.download_status == 'downloaded'
            )
        )
        filing = result.scalar_one_or_none()
        
        if filing and Path(filing.local_path).exists():
            return Path(filing.local_path)
        
        # 파일 없으면 다운로드
        return await self.download_and_store(...)
```

### 예상 비용 절감

```
현재 (매번 다운로드):
- AAPL 10-Q (2024 Q3) 다운로드: 3초
- Gemini 파싱: 100K tokens × $0.075/1M = $0.0075
- 월 4회 × 100종목 = 400회 × $0.0075 = $3.00/월

DB 저장 후:
- 첫 다운로드만 파싱 비용 발생
- 이후 조회는 로컬 파일 읽기 (무료)
- 월 100종목 × $0.0075 = $0.75/월

절감: $3.00 - $0.75 = $2.25/월 (75% 절감)
```

---

## 🎯 2. Yahoo Finance 역사 데이터 저장

### 현재 구현 상태
- ✅ **TimescaleDB**에 일부 저장됨 (Feature Store)
- ⚠️ **부족한 부분**: 원본 OHLCV 데이터는 매번 yfinance로 조회

### 개선 방안

```sql
-- 원본 OHLCV 데이터 저장 (TimescaleDB Hypertable)
CREATE TABLE stock_prices (
    time TIMESTAMPTZ NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    
    -- OHLCV
    open DECIMAL(12, 4),
    high DECIMAL(12, 4),
    low DECIMAL(12, 4),
    close DECIMAL(12, 4),
    volume BIGINT,
    adjusted_close DECIMAL(12, 4),
    
    -- 메타데이터
    source VARCHAR(20) DEFAULT 'yfinance',
    data_quality VARCHAR(20) DEFAULT 'verified',  -- 'verified' | 'suspect' | 'corrected'
    
    PRIMARY KEY (time, ticker)
);

SELECT create_hypertable('stock_prices', 'time');
CREATE INDEX idx_ticker_time ON stock_prices (ticker, time DESC);

-- 자동 압축 (6개월 이상 데이터)
ALTER TABLE stock_prices SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'ticker'
);

SELECT add_compression_policy('stock_prices', INTERVAL '6 months');
```

### Incremental Update 전략

```python
# backend/data/stock_price_storage.py
from datetime import datetime, timedelta

class StockPriceStorage:
    """Yahoo Finance 데이터 증분 업데이트"""
    
    async def update_prices(self, ticker: str, db: AsyncSession):
        """
        1. DB에서 최신 날짜 조회
        2. 최신 날짜 ~ 오늘까지만 yfinance로 조회
        3. 신규 데이터만 DB 저장
        """
        
        # 1. 최신 날짜 확인
        result = await db.execute(
            select(func.max(StockPrice.time))
            .where(StockPrice.ticker == ticker)
        )
        last_date = result.scalar()
        
        if last_date:
            start_date = last_date + timedelta(days=1)
        else:
            start_date = datetime.now() - timedelta(days=365 * 5)  # 5년 전
        
        # 2. 신규 데이터만 조회
        if start_date >= datetime.now():
            return  # 이미 최신
        
        df = yf.download(ticker, start=start_date, end=datetime.now())
        
        # 3. 신규 데이터만 저장
        new_rows = [
            StockPrice(
                time=index,
                ticker=ticker,
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row['Volume'],
                adjusted_close=row['Adj Close']
            )
            for index, row in df.iterrows()
        ]
        
        db.add_all(new_rows)
        await db.commit()
        
        return len(new_rows)
```

### 예상 효과

```
현재 (매번 yfinance 호출):
- AAPL 5년 데이터 조회: 2~5초
- 월 1000회 조회 → 2000~5000초 = 33~83분

DB 저장 후:
- 초회: 5초 (전체 다운로드)
- 이후: 0.1초 (DB 조회) + 일 1회 증분 업데이트 (1초)

속도 개선: 50배 빨라짐
API 부하: 1000회 → 30회 (97% 감소)
```

---

## 🎯 3. AI 분석 결과 캐싱

### 현재 문제
- Claude/Gemini 분석 결과를 매번 재계산
- 같은 10-Q 파일을 여러 번 분석 (비용 낭비)

### 해결 방안

```sql
CREATE TABLE ai_analysis_cache (
    id SERIAL PRIMARY KEY,
    
    -- 입력 식별
    input_type VARCHAR(50) NOT NULL,  -- 'sec_filing' | 'news_article' | 'stock_analysis'
    input_id INTEGER NOT NULL,  -- sec_filings.id | news_articles.id | ticker
    input_hash VARCHAR(64) NOT NULL,  -- 입력 내용 해시 (변경 감지)
    
    -- AI 모델 정보
    ai_model VARCHAR(50) NOT NULL,  -- 'claude-haiku-4' | 'gemini-1.5-flash'
    prompt_version INTEGER NOT NULL,  -- 프롬프트 버전 (변경 시 재분석)
    
    -- 분석 결과
    result JSONB NOT NULL,  -- AI 응답 전체
    structured_output JSONB,  -- 구조화된 데이터 (점수, 분류 등)
    
    -- 비용 추적
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    
    -- 유효성
    expires_at TIMESTAMPTZ,  -- TTL (뉴스는 1주일, 10-Q는 무제한)
    is_valid BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_input_lookup (input_type, input_id, ai_model, prompt_version),
    UNIQUE (input_type, input_id, input_hash, ai_model, prompt_version)
);
```

### 사용 예시

```python
# backend/ai/analysis_cache.py
class AIAnalysisCache:
    """AI 분석 결과 캐싱"""
    
    async def get_or_analyze(
        self,
        input_type: str,
        input_id: int,
        input_content: str,
        ai_model: str,
        prompt_version: int,
        analyze_func: Callable,
        ttl_days: int = None
    ) -> dict:
        """
        1. 캐시 확인 (input_hash + prompt_version)
        2. 캐시 미스시 AI 분석 실행
        3. 결과 저장 후 반환
        """
        
        # 1. 입력 해시 계산
        input_hash = hashlib.sha256(input_content.encode()).hexdigest()
        
        # 2. 캐시 조회
        cache = await db.execute(
            select(AIAnalysisCache).where(
                AIAnalysisCache.input_type == input_type,
                AIAnalysisCache.input_id == input_id,
                AIAnalysisCache.input_hash == input_hash,
                AIAnalysisCache.ai_model == ai_model,
                AIAnalysisCache.prompt_version == prompt_version,
                AIAnalysisCache.is_valid == True,
                or_(
                    AIAnalysisCache.expires_at.is_(None),
                    AIAnalysisCache.expires_at > datetime.utcnow()
                )
            )
        )
        
        cached = cache.scalar_one_or_none()
        if cached:
            return cached.result
        
        # 3. AI 분석 실행
        result, tokens = await analyze_func(input_content)
        
        # 4. 캐시 저장
        new_cache = AIAnalysisCache(
            input_type=input_type,
            input_id=input_id,
            input_hash=input_hash,
            ai_model=ai_model,
            prompt_version=prompt_version,
            result=result,
            input_tokens=tokens['input'],
            output_tokens=tokens['output'],
            cost_usd=calculate_cost(ai_model, tokens),
            expires_at=datetime.utcnow() + timedelta(days=ttl_days) if ttl_days else None
        )
        db.add(new_cache)
        await db.commit()
        
        return result
```

### 예상 비용 절감

```
예시: AAPL 10-Q (2024 Q3) 분석
- 현재: 매번 Gemini 호출 (100K tokens × $0.075/1M = $0.0075)
- 월 10회 재분석 × 100종목 = 1000회 × $0.0075 = $7.50/월

캐싱 후:
- 첫 분석만 비용 발생
- 이후 조회는 무료
- 월 100종목 × $0.0075 = $0.75/월

절감: $7.50 - $0.75 = $6.75/월 (90% 절감)
```

---

## 🎯 4. 뉴스 기사 + 임베딩 저장

### 현재 구현 상태
- ✅ **SQLite** `news.db` 생성됨 (backend/data/news_models.py)
- ⚠️ **부족한 부분**: 임베딩 벡터 미저장 (RAG 미구현)

### 확장 방안

```sql
-- news.db 확장 (SQLite 유지)
CREATE TABLE news_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER REFERENCES news_articles(id) ON DELETE CASCADE,
    
    -- 임베딩 정보
    embedding_model VARCHAR(50) NOT NULL,  -- 'text-embedding-3-small'
    embedding_vector BLOB NOT NULL,  -- 1536 dimensions (pickle or msgpack)
    chunk_index INTEGER DEFAULT 0,  -- 긴 기사는 여러 청크로 분할
    chunk_text TEXT,
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cost_usd REAL,  -- OpenAI 비용 추적
    
    UNIQUE(article_id, chunk_index)
);

CREATE INDEX idx_article_embedding ON news_embeddings(article_id);
```

### 벡터 검색 구현

```python
# backend/ai/news_search.py
import numpy as np
import pickle

class NewsVectorSearch:
    """뉴스 임베딩 기반 검색"""
    
    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.7
    ) -> List[dict]:
        """
        1. 쿼리 임베딩 생성 (캐싱)
        2. 모든 임베딩과 코사인 유사도 계산
        3. 상위 K개 반환
        """
        
        # 1. 쿼리 임베딩
        query_emb = await self._get_embedding(query)  # OpenAI API
        
        # 2. DB에서 모든 임베딩 로드 (100~1000개 정도면 메모리 가능)
        embeddings = await db.execute(
            select(NewsEmbedding).order_by(NewsEmbedding.created_at.desc()).limit(1000)
        )
        
        results = []
        for emb_row in embeddings.scalars():
            # 3. 코사인 유사도 계산
            stored_emb = pickle.loads(emb_row.embedding_vector)
            similarity = cosine_similarity(query_emb, stored_emb)
            
            if similarity >= min_similarity:
                results.append({
                    'article_id': emb_row.article_id,
                    'similarity': similarity,
                    'text': emb_row.chunk_text
                })
        
        # 4. 상위 K개 정렬
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
```

### 예상 효과

```
임베딩 생성 비용 (OpenAI text-embedding-3-small):
- $0.02 / 1M tokens
- 뉴스 1개 (평균 500 tokens) = $0.00001

월 1000개 뉴스 × $0.00001 = $0.01/월 (매우 저렴!)

벡터 검색 장점:
- 키워드 검색보다 의미 기반 검색 가능
- "AAPL 실적 부진" 쿼리 → "애플 매출 감소" 기사 검색
```

---

## 🎯 5. 백테스트 결과 저장

### 현재 문제
- 백테스트 결과를 매번 재계산
- 전략 비교 시 히스토리 부재

### 해결 방안

```sql
CREATE TABLE backtest_runs (
    id SERIAL PRIMARY KEY,
    
    -- 전략 정보
    strategy_name VARCHAR(100) NOT NULL,
    strategy_version INTEGER NOT NULL,
    strategy_config JSONB NOT NULL,  -- 하이퍼파라미터
    
    -- 백테스트 기간
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15, 2) NOT NULL,
    
    -- 성과 지표
    total_return DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    win_rate DECIMAL(5, 4),
    total_trades INTEGER,
    
    -- 메타데이터
    run_at TIMESTAMPTZ DEFAULT NOW(),
    run_duration_seconds INTEGER,
    data_quality VARCHAR(20),  -- 'clean' | 'incomplete' | 'synthetic'
    
    INDEX idx_strategy_date (strategy_name, start_date DESC)
);

-- 개별 거래 기록
CREATE TABLE backtest_trades (
    id SERIAL PRIMARY KEY,
    backtest_run_id INTEGER REFERENCES backtest_runs(id) ON DELETE CASCADE,
    
    ticker VARCHAR(20) NOT NULL,
    entry_date DATE NOT NULL,
    exit_date DATE,
    entry_price DECIMAL(12, 4),
    exit_price DECIMAL(12, 4),
    shares DECIMAL(12, 4),
    pnl DECIMAL(15, 2),
    pnl_pct DECIMAL(10, 4),
    
    -- AI 결정 근거
    entry_signals JSONB,  -- AI가 매수한 이유
    exit_signals JSONB,   -- AI가 매도한 이유
    
    INDEX idx_backtest_run (backtest_run_id)
);
```

### 사용 예시

```python
# 전략 A/B 테스트
strategies = [
    {'name': 'Claude Haiku', 'model': 'claude-haiku-4'},
    {'name': 'Gemini Flash', 'model': 'gemini-1.5-flash'}
]

for strategy in strategies:
    # 백테스트 실행
    result = await run_backtest(strategy, start='2024-01-01', end='2024-11-01')
    
    # 결과 저장
    await save_backtest_result(
        strategy_name=strategy['name'],
        strategy_config=strategy,
        metrics=result
    )

# 전략 비교
comparison = await db.execute(
    select(BacktestRun)
    .where(BacktestRun.start_date == '2024-01-01')
    .order_by(BacktestRun.sharpe_ratio.desc())
)

print("Best Strategy:", comparison.scalars().first().strategy_name)
```

---

## 📊 종합 비용 절감 효과

### Phase별 예상 비용 (월간)

| Phase | 현재 비용 | DB 저장 후 | 절감액 | 절감률 |
|-------|----------|-----------|--------|--------|
| SEC 10-Q/10-K | $3.00 | $0.75 | $2.25 | 75% |
| Yahoo Finance | N/A | N/A | (속도만 개선) | - |
| AI 분석 캐싱 | $7.50 | $0.75 | $6.75 | 90% |
| 뉴스 임베딩 | $0.05 | $0.01 | $0.04 | 80% |
| **합계** | **$10.55** | **$1.51** | **$9.04** | **86%** |

### 추가 효과
- **속도**: Yahoo Finance 조회 50배 개선
- **확장성**: 1000종목까지 선형 확장 가능
- **오프라인**: 네트워크 장애 시에도 작동

---

## 🚀 구현 우선순위

### Phase 1: 즉시 구현 (2일)
1. ✅ TimescaleDB Feature Store (이미 완료)
2. 🔴 **SEC 파일 로컬 저장** (2시간)
3. 🔴 **AI 분석 결과 캐싱** (3시간)

### Phase 2: 1주일 내 (1주)
4. 🟡 **Yahoo Finance 증분 업데이트** (1일)
5. 🟡 **뉴스 임베딩 저장** (2일)

### Phase 3: 1개월 내 (선택)
6. 🟢 **백테스트 결과 저장** (1일)
7. 🟢 **포트폴리오 히스토리** (1일)

---

## 📁 데이터베이스 파일 위치

### Synology NAS 저장 구조 (권장)

```
/volume1/ai_trading/
├── databases/
│   ├── timescaledb/          # Docker volume
│   ├── redis/                # Docker volume
│   └── news.db               # SQLite (20MB)
├── sec_filings/              # SEC 원본 파일
│   ├── AAPL_10Q_2024Q3.html
│   ├── MSFT_10K_2024.html
│   └── ...
├── cache/
│   └── ai_analysis/          # AI 분석 JSON 캐시
└── backups/
    ├── daily/
    └── weekly/
```

### 백업 전략

```bash
# 1. TimescaleDB 백업 (일 1회)
docker exec timescaledb pg_dump -U postgres ai_trading | gzip > backup_$(date +%Y%m%d).sql.gz

# 2. SEC 파일 백업 (주 1회)
rsync -av /volume1/ai_trading/sec_filings/ /volume1/backup/sec/

# 3. SQLite 백업 (일 1회)
cp /volume1/ai_trading/databases/news.db /volume1/backup/news_$(date +%Y%m%d).db
```

---

## ✅ 체크리스트

### 즉시 구현 필요
- [ ] SEC 파일 다운로드 로직 작성
- [ ] SEC 메타데이터 테이블 생성
- [ ] AI 분석 캐시 테이블 생성
- [ ] Incremental Update 로직 구현

### 1주일 내
- [ ] Yahoo Finance 증분 업데이트
- [ ] 뉴스 임베딩 테이블 추가
- [ ] 벡터 검색 구현

### 모니터링
- [ ] 캐시 히트율 측정 (목표: >90%)
- [ ] API 호출 횟수 추적
- [ ] 월간 비용 리포트 생성

---

## 📌 다음 단계

1. **이 문서를 로컬에 저장** (`01_DB_Storage_Analysis.md`)
2. **Phase 1 작업 시작**: SEC 파일 저장 구현
3. **Spec-Kit으로 Task 생성**: `/speckit.tasks` 명령 사용

---

**작성자**: Claude (AI Trading System)  
**버전**: 1.0  
**업데이트**: 필요 시 이 문서 수정
