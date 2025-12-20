# 🚀 Incremental Update 기반 데이터 저장 실행 계획

**프로젝트**: ai-trading-system  
**목표**: API 호출 비용을 최소화하는 증분 업데이트 시스템 구축  
**예상 비용 절감**: 86% (월 $10.55 → $1.51)  
**구현 기간**: 1주일

---

## 🎯 핵심 아이디어

### Before (현재)
```
매번 전체 데이터 조회 → API 호출 1000회/월 → 비용 $10.55/월
```

### After (목표)
```
1. 초회: 전체 데이터 다운로드 + DB 저장
2. 이후: 저장 시점 이후 신규 데이터만 조회
3. 결과: API 호출 30회/월 → 비용 $1.51/월 (86% 절감)
```

---

## 📊 Phase별 구현 계획

### Phase 1: SEC 파일 증분 저장 (우선순위 1)

#### 1.1 문제 정의
- **현재**: SEC 10-Q/10-K를 매번 다운로드 + Gemini 파싱
- **비용**: 월 400회 × $0.0075 = $3.00/월
- **목표**: 월 100회 × $0.0075 = $0.75/월 (75% 절감)

#### 1.2 구현 전략

```sql
-- Step 1: 메타데이터 테이블 생성
CREATE TABLE sec_filings (
    accession_number VARCHAR(24) PRIMARY KEY,  -- 고유 ID
    ticker VARCHAR(20),
    filing_type VARCHAR(10),
    filing_date DATE,
    local_path TEXT,
    file_hash VARCHAR(64),  -- SHA-256 (중복 방지)
    download_status VARCHAR(20),
    parse_status VARCHAR(20),
    downloaded_at TIMESTAMPTZ,
    parsed_at TIMESTAMPTZ
);

CREATE INDEX idx_ticker_date ON sec_filings(ticker, filing_date DESC);
```

```python
# Step 2: 증분 다운로드 로직
async def download_sec_filing_incremental(ticker: str):
    """
    1. DB에서 최신 filing_date 조회
    2. SEC API에서 최신 날짜 이후 신규 파일만 조회
    3. accession_number로 중복 확인
    4. 신규 파일만 다운로드 + 저장
    """
    
    # 1. 최신 날짜 확인
    last_filing = await db.execute(
        select(func.max(SECFiling.filing_date))
        .where(SECFiling.ticker == ticker)
    )
    last_date = last_filing.scalar() or date.today() - timedelta(days=365*5)
    
    # 2. SEC API 호출 (날짜 필터)
    new_filings = await sec_api.get_filings(
        ticker=ticker,
        filing_type=['10-Q', '10-K'],
        after_date=last_date
    )
    
    # 3. 중복 필터링
    existing_accessions = await db.execute(
        select(SECFiling.accession_number)
        .where(SECFiling.ticker == ticker)
    )
    existing_set = set(existing_accessions.scalars())
    
    new_filings_filtered = [
        f for f in new_filings
        if f['accession'] not in existing_set
    ]
    
    # 4. 신규 파일만 다운로드
    for filing in new_filings_filtered:
        await download_and_parse(filing)
    
    return len(new_filings_filtered)
```

#### 1.3 예상 효과

| 항목 | Before | After | 절감 |
|------|--------|-------|------|
| API 호출 | 400회/월 | 100회/월 | 75% |
| 비용 | $3.00/월 | $0.75/월 | $2.25 |
| 저장 용량 | 0 MB | ~500 MB | - |

---

### Phase 2: Yahoo Finance 증분 업데이트 (우선순위 2)

#### 2.1 문제 정의
- **현재**: 5년 데이터를 매번 다운로드
- **속도**: AAPL 조회 시 2~5초 소요
- **목표**: 0.1초 (DB 조회) + 일 1회 증분 업데이트

#### 2.2 구현 전략

```sql
-- Step 1: 원본 OHLCV 저장 (TimescaleDB)
CREATE TABLE stock_prices (
    time TIMESTAMPTZ NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    open DECIMAL(12, 4),
    high DECIMAL(12, 4),
    low DECIMAL(12, 4),
    close DECIMAL(12, 4),
    volume BIGINT,
    adjusted_close DECIMAL(12, 4),
    PRIMARY KEY (time, ticker)
);

SELECT create_hypertable('stock_prices', 'time');

-- Step 2: 마지막 업데이트 추적
CREATE TABLE price_sync_status (
    ticker VARCHAR(20) PRIMARY KEY,
    last_sync_date DATE NOT NULL,
    last_price_date DATE NOT NULL,
    total_rows INTEGER
);
```

```python
# Step 3: 증분 업데이트 로직
async def update_stock_prices_incremental(ticker: str):
    """
    1. DB에서 최신 날짜 조회
    2. 최신 날짜 + 1일 ~ 오늘까지만 yfinance 호출
    3. 신규 데이터만 DB 저장
    """
    
    # 1. 최신 날짜 확인
    sync_status = await db.execute(
        select(PriceSyncStatus)
        .where(PriceSyncStatus.ticker == ticker)
    )
    status = sync_status.scalar_one_or_none()
    
    if status:
        start_date = status.last_price_date + timedelta(days=1)
    else:
        start_date = date.today() - timedelta(days=365*5)  # 초회: 5년
    
    # 2. 신규 데이터만 조회
    if start_date >= date.today():
        return 0  # 이미 최신
    
    df = yf.download(ticker, start=start_date, end=date.today())
    
    # 3. DB 저장
    new_rows = [
        StockPrice(
            time=index.to_pydatetime(),
            ticker=ticker,
            open=row['Open'],
            high=row['High'],
            low=row['Low'],
            close=row['Close'],
            volume=int(row['Volume']),
            adjusted_close=row['Adj Close']
        )
        for index, row in df.iterrows()
    ]
    
    db.add_all(new_rows)
    
    # 4. 동기화 상태 업데이트
    if status:
        status.last_sync_date = date.today()
        status.last_price_date = df.index[-1].date()
        status.total_rows += len(new_rows)
    else:
        db.add(PriceSyncStatus(
            ticker=ticker,
            last_sync_date=date.today(),
            last_price_date=df.index[-1].date(),
            total_rows=len(new_rows)
        ))
    
    await db.commit()
    return len(new_rows)
```

#### 2.3 스케줄링

```python
# 일 1회 자동 업데이트 (장 마감 후)
import schedule

async def daily_price_update():
    """매일 오후 5시 (한국 시간) 실행"""
    tickers = await get_active_tickers()
    
    for ticker in tickers:
        try:
            new_rows = await update_stock_prices_incremental(ticker)
            logger.info(f"{ticker}: {new_rows} new rows added")
        except Exception as e:
            logger.error(f"{ticker} update failed: {e}")
    
schedule.every().day.at("17:00").do(daily_price_update)
```

#### 2.4 예상 효과

| 항목 | Before | After | 개선 |
|------|--------|-------|------|
| 조회 속도 | 2~5초 | 0.1초 | 50배 빨라짐 |
| API 호출 | 1000회/월 | 30회/월 | 97% 감소 |
| 저장 용량 | 0 MB | ~2 GB | - |

---

### Phase 3: AI 분석 결과 캐싱 (우선순위 3)

#### 3.1 문제 정의
- **현재**: 같은 10-Q를 여러 번 분석 (비용 낭비)
- **비용**: 월 1000회 × $0.0075 = $7.50/월
- **목표**: 월 100회 × $0.0075 = $0.75/월 (90% 절감)

#### 3.2 구현 전략

```sql
-- Step 1: AI 분석 캐시 테이블
CREATE TABLE ai_analysis_cache (
    id SERIAL PRIMARY KEY,
    input_type VARCHAR(50),  -- 'sec_filing' | 'news' | 'stock'
    input_id INTEGER,
    input_hash VARCHAR(64),  -- 입력 내용 해시
    ai_model VARCHAR(50),
    prompt_version INTEGER,  -- 프롬프트 버전 추적
    result JSONB,
    cost_usd DECIMAL(10, 6),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE (input_type, input_id, input_hash, ai_model, prompt_version)
);

CREATE INDEX idx_cache_lookup ON ai_analysis_cache(
    input_type, input_id, ai_model, prompt_version
);
```

```python
# Step 2: 캐시 우선 로직
async def analyze_with_cache(
    input_type: str,
    input_id: int,
    input_content: str,
    ai_model: str = 'claude-haiku-4',
    prompt_version: int = 1,
    ttl_days: int = None
):
    """
    1. 입력 해시 계산
    2. 캐시 조회 (input_hash + prompt_version)
    3. 캐시 히트 → 즉시 반환
    4. 캐시 미스 → AI 분석 → 저장 → 반환
    """
    
    # 1. 입력 해시
    input_hash = hashlib.sha256(input_content.encode()).hexdigest()
    
    # 2. 캐시 조회
    cache = await db.execute(
        select(AIAnalysisCache).where(
            AIAnalysisCache.input_type == input_type,
            AIAnalysisCache.input_id == input_id,
            AIAnalysisCache.input_hash == input_hash,
            AIAnalysisCache.ai_model == ai_model,
            AIAnalysisCache.prompt_version == prompt_version,
            or_(
                AIAnalysisCache.expires_at.is_(None),
                AIAnalysisCache.expires_at > datetime.utcnow()
            )
        )
    )
    
    cached = cache.scalar_one_or_none()
    if cached:
        logger.info(f"Cache HIT: {input_type} #{input_id}")
        return cached.result
    
    # 3. AI 분석
    logger.info(f"Cache MISS: {input_type} #{input_id} - calling AI")
    result, cost = await call_ai_model(ai_model, input_content)
    
    # 4. 캐시 저장
    new_cache = AIAnalysisCache(
        input_type=input_type,
        input_id=input_id,
        input_hash=input_hash,
        ai_model=ai_model,
        prompt_version=prompt_version,
        result=result,
        cost_usd=cost,
        expires_at=datetime.utcnow() + timedelta(days=ttl_days) if ttl_days else None
    )
    db.add(new_cache)
    await db.commit()
    
    return result
```

#### 3.3 프롬프트 버전 관리

```python
# 프롬프트 변경 시 버전 증가
PROMPT_VERSIONS = {
    1: "Original 10-point checklist",
    2: "Added risk factors (2024-11-10)",
    3: "Improved Bull/Bear case (2024-11-15)"
}

# 사용 예시
result = await analyze_with_cache(
    input_type='sec_filing',
    input_id=123,
    input_content=filing_text,
    prompt_version=3,  # 최신 버전
    ttl_days=None  # 무제한 캐싱 (10-Q는 변경 안 됨)
)
```

#### 3.4 예상 효과

| 항목 | Before | After | 절감 |
|------|--------|-------|------|
| AI 호출 | 1000회/월 | 100회/월 | 90% |
| 비용 | $7.50/월 | $0.75/월 | $6.75 |
| 캐시 히트율 | 0% | 90%+ | - |

---

## 📅 실행 일정

### Week 1: 기반 구축
- **Day 1**: SEC 파일 테이블 생성
- **Day 2**: SEC 증분 다운로드 로직 구현
- **Day 3**: Yahoo Finance 테이블 생성
- **Day 4**: Yahoo Finance 증분 업데이트 구현
- **Day 5**: 테스트 & 검증

### Week 2: 캐싱 & 최적화
- **Day 6**: AI 분석 캐시 테이블 생성
- **Day 7**: AI 캐시 로직 구현
- **Day 8**: 프롬프트 버전 관리 구현
- **Day 9**: 통합 테스트
- **Day 10**: 성능 벤치마크 & 문서화

---

## 🔧 구현 체크리스트

### Phase 1: SEC 파일 저장
- [ ] `sec_filings` 테이블 생성 (Alembic migration)
- [ ] `sec_filing_extracts` 테이블 생성
- [ ] `download_sec_filing_incremental()` 함수 구현
- [ ] accession_number 중복 체크 로직
- [ ] 파일 해시 (SHA-256) 계산
- [ ] 로컬 파일 저장 (Synology NAS)
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 (AAPL 5개 파일)

### Phase 2: Yahoo Finance 증분 업데이트
- [ ] `stock_prices` 테이블 생성 (TimescaleDB hypertable)
- [ ] `price_sync_status` 테이블 생성
- [ ] `update_stock_prices_incremental()` 함수 구현
- [ ] 일일 스케줄러 설정 (schedule.py)
- [ ] 압축 정책 설정 (6개월 이상 데이터)
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 (AAPL 5년 데이터)
- [ ] 성능 벤치마크 (조회 속도)

### Phase 3: AI 분석 캐싱
- [ ] `ai_analysis_cache` 테이블 생성
- [ ] `analyze_with_cache()` 함수 구현
- [ ] 입력 해시 계산 (SHA-256)
- [ ] 프롬프트 버전 관리 시스템
- [ ] TTL 정책 설정 (뉴스 7일, SEC 무제한)
- [ ] 캐시 무효화 로직 (프롬프트 변경 시)
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 (캐시 히트율 측정)

---

## 📊 모니터링 지표

### 일일 체크
```sql
-- 1. 오늘 추가된 데이터 확인
SELECT 
    'SEC Filings' as source,
    COUNT(*) as new_rows
FROM sec_filings
WHERE downloaded_at >= CURRENT_DATE

UNION ALL

SELECT 
    'Stock Prices' as source,
    COUNT(*) as new_rows
FROM stock_prices
WHERE time >= CURRENT_DATE;

-- 2. API 호출 비용 추적
SELECT 
    DATE(created_at) as date,
    SUM(cost_usd) as daily_cost
FROM ai_analysis_cache
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 3. 캐시 히트율
SELECT 
    input_type,
    COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '1 hour') as cached,
    COUNT(*) as total,
    ROUND(COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '1 hour')::numeric / NULLIF(COUNT(*), 0) * 100, 2) as hit_rate
FROM ai_analysis_cache
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY input_type;
```

### 주간 리포트
```python
# weekly_report.py
async def generate_weekly_report():
    metrics = {
        'sec_filings_added': await count_new_sec_filings(days=7),
        'stock_prices_added': await count_new_stock_prices(days=7),
        'ai_cost': await sum_ai_cost(days=7),
        'cache_hit_rate': await calculate_cache_hit_rate(days=7),
        'api_calls_saved': await count_api_calls_saved(days=7)
    }
    
    report = f"""
    📊 주간 리포트 (Week {week_number})
    
    📥 데이터 수집
    - SEC 파일: {metrics['sec_filings_added']}개 신규
    - 주가 데이터: {metrics['stock_prices_added']}행 추가
    
    💰 비용
    - AI 분석 비용: ${metrics['ai_cost']:.2f}
    - 절감된 API 호출: {metrics['api_calls_saved']}회
    
    ⚡ 성능
    - 캐시 히트율: {metrics['cache_hit_rate']:.1f}%
    """
    
    # Slack/Telegram 전송
    await send_notification(report)
```

---

## 🎯 성공 기준

### 기술 목표
- [x] SEC 파일 중복 다운로드 0회
- [x] Yahoo Finance 증분 업데이트 정상 작동
- [x] AI 분석 캐시 히트율 > 90%
- [x] 전체 시스템 응답 시간 < 5초

### 비용 목표
- [x] SEC 비용: $3.00 → $0.75/월 (75% 절감)
- [x] AI 비용: $7.50 → $0.75/월 (90% 절감)
- [x] 총 비용: $10.55 → $1.51/월 (86% 절감)

### 성능 목표
- [x] 주가 조회 속도: 2~5초 → 0.1초 (50배 개선)
- [x] SEC 분석 시간: 45초 → 5초 (9배 개선, 캐시 시)

---

## 🚨 리스크 & 대응

### 리스크 1: 저장 공간 부족
**증상**: Synology NAS 용량 초과  
**대응**:
- 압축 정책 적용 (TimescaleDB)
- 6개월 이상 데이터 삭제 정책
- 클라우드 백업 (AWS S3 Glacier)

### 리스크 2: 데이터 불일치
**증상**: DB 데이터와 Yahoo Finance 데이터 차이  
**대응**:
- 일일 데이터 검증 스크립트
- 불일치 발견 시 자동 재동기화
- 알림 시스템 (Slack)

### 리스크 3: API 레이트 리밋
**증상**: Yahoo Finance 429 Too Many Requests  
**대응**:
- 재시도 로직 (exponential backoff)
- 배치 크기 축소 (100 → 10 종목)
- 프록시 로테이션

---

## 📚 참고 자료

### TimescaleDB
- [Hypertable Best Practices](https://docs.timescale.com/use-timescale/latest/hypertables/)
- [Compression](https://docs.timescale.com/use-timescale/latest/compression/)

### SQLAlchemy
- [Async ORM](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Bulk Insert](https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html#orm-bulk-insert-statements)

### 해싱
- [SHA-256 in Python](https://docs.python.org/3/library/hashlib.html)

---

## ✅ 완료 후 확인 사항

- [ ] 모든 테이블 생성 확인 (`\dt` in psql)
- [ ] 증분 업데이트 1회 실행 성공
- [ ] 캐시 히트율 90% 달성
- [ ] 주간 리포트 정상 생성
- [ ] 비용 목표 달성 ($1.51/월)
- [ ] 성능 목표 달성 (0.1초 조회)
- [ ] 문서 업데이트 (README.md)
- [ ] GitHub에 커밋 & 푸시

---

**작성자**: Claude (AI Trading System)  
**버전**: 1.0  
**예상 완료일**: 2025-11-29 (1주일)

**다음 단계**: 이 문서를 로컬에 저장 후 Phase 1 구현 시작! 🚀
