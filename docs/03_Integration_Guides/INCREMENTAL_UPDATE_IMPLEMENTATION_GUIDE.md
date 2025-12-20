## 🚀 증분 업데이트 시스템 구현 가이드

**목표**: API 비용 86% 절감 ($10.55/월 → $1.51/월)
**구현 완료**: 2025-11-23
**Phase**: 증분 업데이트 시스템 (Week 1 Complete)

---

## 📊 시스템 아키텍처

### 핵심 설계 원칙

1. **NAS 호환성**: 로컬 개발 + Synology NAS 배포 지원
2. **태그 기반 저장**: 계층적 폴더 구조로 빠른 검색
3. **컨텐츠 기반 중복 제거**: SHA-256 해시 활용
4. **스마트 캐싱**: Prompt 버전 추적으로 자동 무효화
5. **증분 업데이트**: 신규 데이터만 조회

### 파일 저장 전략 (NAS 호환)

```
{storage_root}/
├── sec_filings/              # SEC 공시 파일
│   ├── AAPL/
│   │   ├── 2024/
│   │   │   ├── Q3/
│   │   │   │   ├── 10-Q_20240803.txt
│   │   │   │   └── metadata.json
│   │   │   └── Q4/
│   │   │       └── 10-K_20241102.txt
│   │   └── 2023/
│   │       └── Q4/
│   │           └── 10-K_20231104.txt
│   └── MSFT/
│       └── 2024/
│           └── Q3/
│               └── 10-Q_20240731.txt
│
├── ai_cache/                 # AI 분석 캐시
│   ├── investment_decision/
│   │   └── AAPL_v2.1_abc123.json
│   └── sec_analysis/
│       └── AAPL_v1.0_def456.json
│
├── stock_prices/             # 주가 데이터 (DB only)
├── embeddings/               # RAG 벡터 임베딩
└── logs/                     # 로그 파일
```

### 태그 계층 구조

**3-Tier Tagging System**:
1. **Tier 1 (ticker)**: AAPL, MSFT, GOOGL
2. **Tier 2 (year)**: 2024, 2023, 2022
3. **Tier 3 (quarter)**: Q1, Q2, Q3, Q4

**장점**:
- 빠른 필터링: "AAPL의 2024 Q3 파일만"
- NAS 친화적: 단순 폴더 탐색
- 확장 가능: 새로운 태그 추가 용이

---

## 🛠️ 구현 완료 내역

### 1. Storage Configuration (NAS 호환)

**파일**: `backend/config/storage_config.py`

**주요 기능**:
- 자동 NAS 감지 (환경 변수 또는 /volume1 체크)
- Docker 볼륨 마운트 지원
- Local ↔ NAS 자동 전환
- 저장 위치별 용량 제한

**환경 변수**:
```bash
# .env 또는 docker-compose.yml
NAS_HOST=192.168.1.100
NAS_VOLUME=volume1
NAS_SHARE=ai_trading
DOCKER_STORAGE_PATH=/mnt/ai_trading_data
```

**사용 예시**:
```python
from backend.config.storage_config import get_storage_config, StorageLocation

config = get_storage_config()

# Get SEC filings path (auto NAS/local)
sec_path = config.get_path(StorageLocation.SEC_FILINGS)
# Returns: /volume1/ai_trading/sec_filings (NAS)
#      or: D:/code/ai-trading-system/data/sec_filings (local)

# Get file path with auto directory creation
file_path = config.get_file_path(
    StorageLocation.SEC_FILINGS,
    "AAPL/2024/Q3/10-Q_20240803.txt"
)
```

### 2. SEC File Storage (증분 다운로드)

**파일**: `backend/data/sec_file_storage.py`

**주요 기능**:
- 증분 다운로드 (신규 파일만)
- 계층적 태그 구조 (ticker/year/quarter)
- SHA-256 중복 제거
- 90일 lookback (초회 다운로드)

**비용 절감**:
- Before: 400 downloads/month × $0.0075 = $3.00/month
- After: 100 downloads/month × $0.0075 = $0.75/month
- **Savings: 75% ($2.25/month)**

**사용 예시**:
```python
from backend.data.sec_file_storage import SECFileStorage

async with get_db() as db:
    storage = SECFileStorage(db)

    # Download only new AAPL filings
    stats = await storage.download_filing_incremental("AAPL")
    # Output: {"new_filings": 2, "duplicates": 1, "total_size_kb": 450}

    # List filings (fast tag-based query)
    filings = await storage.list_filings(
        ticker="AAPL",
        filing_type="10-Q",
        start_date=date(2024, 1, 1)
    )

    # Retrieve specific filing
    content = await storage.get_filing_content(
        ticker="AAPL",
        filing_type="10-Q",
        filing_date=date(2024, 8, 3)
    )
```

### 3. Enhanced AI Analysis Cache (90% 절감)

**파일**: `backend/ai/enhanced_analysis_cache.py`

**주요 기능**:
- **Prompt 버전 추적**: 프롬프트 변경 시 자동 무효화
- **Feature 핑거프린팅**: 입력 기반 캐싱
- **Multi-tier TTL**: SEC 90일, 뉴스 1일
- **Cost Analytics**: 티커별 비용 추적

**비용 절감**:
- Before: $7.50/month (중복 분석)
- After: $0.75/month (90% cache hit)
- **Savings: 90% ($6.75/month)**

**사용 예시**:
```python
from backend.ai.enhanced_analysis_cache import cached_analysis

# Decorator로 자동 캐싱
@cached_analysis("investment_decision", ttl_days=7)
async def analyze_stock(ticker: str, features: dict) -> dict:
    # AI analysis logic (Claude API)
    return await claude.analyze(...)

# 첫 호출: Cache MISS → AI 분석 실행
result1 = await analyze_stock("AAPL", {"price": 180, "volume": 50M})

# 두 번째 호출 (같은 features): Cache HIT → 즉시 반환
result2 = await analyze_stock("AAPL", {"price": 180, "volume": 50M})
```

### 4. Database Migration

**파일**: `backend/alembic/versions/add_incremental_update_tables.py`

**생성 테이블**:
1. `sec_filings`: SEC 파일 메타데이터
2. `stock_prices`: TimescaleDB hypertable (OHLCV)
3. `price_sync_status`: 증분 업데이트 추적
4. `ai_analysis_cache`: AI 분석 캐시 (prompt 버전 포함)
5. `ai_cost_analytics`: Materialized view (비용 분석)

**실행 방법**:
```bash
# 마이그레이션 실행
cd d:\code\ai-trading-system
alembic upgrade head

# 확인
psql -U postgres -d ai_trading -c "\dt"
```

---

## 📈 예상 비용 절감 효과

### Before (현재)
```
SEC 파일: $3.00/월 (매번 다운로드)
AI 분석: $7.50/월 (중복 분석)
뉴스 임베딩: $0.05/월
───────────────────────────
합계: $10.55/월
```

### After (증분 업데이트)
```
SEC 파일: $0.75/월 (신규만 다운로드)
AI 분석: $0.75/월 (90% 캐시 히트)
뉴스 임베딩: $0.01/월 (증분 업데이트)
───────────────────────────
합계: $1.51/월
```

### 절감 효과
```
월 절감: $9.04 (86% 절감)
연 절감: $108.48
```

---

## 🎯 다음 단계 (Week 2)

### 1. Yahoo Finance 증분 업데이트 (Day 1-2)

**목표**: 5년 데이터 매번 조회 → DB 조회 + 일일 업데이트

**구현 파일**: `backend/data/stock_price_storage.py`

```python
async def update_stock_prices_incremental(ticker: str):
    """
    1. DB에서 최신 날짜 조회
    2. 최신 날짜 + 1일 ~ 오늘까지만 yfinance 호출
    3. 신규 데이터만 DB 저장
    """
    # Get last sync date
    sync_status = await db.get_sync_status(ticker)

    if sync_status:
        start_date = sync_status.last_price_date + timedelta(days=1)
    else:
        start_date = date.today() - timedelta(days=365*5)  # Initial: 5 years

    # Download only new data
    if start_date >= date.today():
        return  # Already up to date

    df = yf.download(ticker, start=start_date, end=date.today())

    # Save to DB
    await db.bulk_insert_stock_prices(df)
```

**예상 효과**:
- 속도: 2~5초 → 0.1초 (50배 빠름)
- API 부하: 5년 조회 → 1일 조회 (99% 감소)

### 2. Phase 13 RAG Foundation 완성 (Day 3-7)

**목표**: 10,000+ 문서 임베딩

**주요 작업**:
- SEC 파일 백필 (10년 × 100 종목 = 20,000 filings)
- 뉴스 백필 (30일 × 100 종목 = 30,000 articles)
- 벡터 검색 통합 (AI 분석에 RAG 활용)

**비용**:
- 초기 백필: $0.40 (일회성)
- 월간 운영: $0.003 (~4원)

---

## 🔧 설치 및 설정

### 1. 의존성 설치

```bash
pip install aiofiles sqlalchemy[asyncio] alembic
```

### 2. 환경 변수 설정

```bash
# .env
NAS_HOST=192.168.1.100           # NAS IP (선택)
NAS_VOLUME=volume1                # NAS 볼륨 (선택)
NAS_SHARE=ai_trading              # NAS 공유 폴더 (선택)
DOCKER_STORAGE_PATH=/mnt/data     # Docker 마운트 (선택)
```

### 3. 데이터베이스 마이그레이션

```bash
# 마이그레이션 실행
alembic upgrade head

# TimescaleDB 확인
psql -U postgres -d ai_trading -c "SELECT * FROM timescaledb_information.hypertables;"
```

### 4. 초기 데이터 백필

```python
from backend.data.sec_file_storage import SECFileStorage

async with get_db() as db:
    storage = SECFileStorage(db)

    # Top 100 S&P 500 stocks
    tickers = ["AAPL", "MSFT", "GOOGL", ...]  # 100 stocks

    for ticker in tickers:
        stats = await storage.download_filing_incremental(ticker)
        print(f"{ticker}: {stats['new_filings']} new filings")
```

---

## 📊 모니터링 및 분석

### 1. 저장소 통계

```python
from backend.config.storage_config import get_storage_config

config = get_storage_config()
stats = config.get_storage_stats()

for location, stat in stats.items():
    print(f"{location}:")
    print(f"  Size: {stat['size_mb']:.2f} MB")
    print(f"  Files: {stat['file_count']}")
    print(f"  Usage: {stat['usage_pct']:.1f}%")
```

### 2. AI 비용 분석

```python
from backend.ai.enhanced_analysis_cache import EnhancedAnalysisCache

async with get_db() as db:
    cache = EnhancedAnalysisCache(db)
    analytics = await cache.get_cost_analytics()

    print(f"Cache hit rate: {analytics['cache_hit_rate']:.1%}")
    print(f"Total cost: ${analytics['total_cost_usd']:.2f}")
    print(f"Saved cost: ${analytics['saved_cost_usd']:.2f}")
```

---

## ✅ 체크리스트

### Week 1 (완료)
- [x] NAS 호환 스토리지 설정
- [x] SEC 파일 증분 저장
- [x] AI 분석 캐싱 강화
- [x] 데이터베이스 마이그레이션

### Week 2 (완료 ✅)
- [x] Yahoo Finance 증분 업데이트 (Phase 16.1 완료)
- [x] Phase 13 RAG 문서 임베딩 (100% 완료)
- [x] 비용 모니터링 대시보드
- [x] 자동 백업 스크립트

### Week 3 (완료 ✅)
- [x] 비용 모니터링 대시보드 (Cost Analytics + React UI)
- [x] 자동 백업 스크립트 (NAS 연동 + 성능 벤치마크)
- [ ] Phase 14 공급망 리스크 분석
- [ ] 통합 테스트 및 성능 최적화

### Week 4 (다음 단계)
- [ ] Phase 14 공급망 리스크 분석 (Supply Chain Risk)
- [ ] Phase 17 프로덕션 배포 준비
- [ ] 통합 테스트 및 성능 최적화
- [ ] 전체 시스템 검증

---

## 📚 참고 문서

- [01_DB_Storage_Analysis.md](01_DB_Storage_Analysis.md) - DB화 분석
- [03_Incremental_Update_Plan.md](03_Incremental_Update_Plan.md) - 상세 계획
- [04_Unified_Tagging_System.md](04_Unified_Tagging_System.md) - RAG 태깅

---

**작성자**: Claude (AI Trading System)
**버전**: 1.0
**최종 업데이트**: 2025-11-23

**준비 완료! 🚀 Week 2로 진행합니다!**
