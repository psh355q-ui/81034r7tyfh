# Database Architect Agent 통합 계획

**작성일**: 2026-01-02 18:00
**작성자**: AI Trading System Development Team
**관련 문서**: [260102_Claude_Code_Templates_Review.md](260102_Claude_Code_Templates_Review.md)
**우선순위**: P2 (Medium - Performance Enhancement)
**상태**: 📋 Plan Complete - Awaiting Approval

---

## 목표

Claude Code Templates의 Database Architect Agent를 기존 DB Schema Manager Agent와 통합하여 데이터베이스 최적화 및 성능 개선을 달성합니다.

**사용자 요구사항 (확정):**
- ✅ Database Architect Agent 우선 도입
- ✅ 전체 검토만 수행 (실제 설치는 보류)
- ✅ 기존 DB Schema Manager Agent와의 통합 방안 수립
- ✅ War Room MVP 15초 응답 시간 목표 달성을 위한 DB 최적화

---

## 현재 상태

### 기존 DB Schema Manager Agent

**위치**: [backend/ai/skills/system/db-schema-manager/](../backend/ai/skills/system/db-schema-manager/)

**구성**:
- 17개 JSON 스키마 정의 (schemas/)
- 3개 핵심 스크립트 (scripts/)
  - `generate_migration.py` - SQL 마이그레이션 생성
  - `compare_to_db.py` - 스키마 검증
  - `validate_data.py` - 데이터 검증
- 문서: SKILL.md, SCHEMA_REGISTRY.md, MIGRATION_GUIDE.md

**강점:**
- ✅ 단일 정보원(Single Source of Truth) 시스템
- ✅ JSON 기반 스키마 정의 (표준화된 형식)
- ✅ 자동 마이그레이션 생성
- ✅ 스키마 검증 기능

**제한사항:**
- ❌ 인덱스 최적화 분석 부재
- ❌ 쿼리 성능 분석 불가
- ❌ 파티셔닝 전략 미지원
- ❌ 제약조건 검증 제한적
- ❌ 데이터 품질 검사 부족

### 현재 데이터베이스 상태

**테이블 현황 (17개 관리 중):**
- 타임시리즈: stock_prices (1,750 레코드, TimescaleDB 미활성화)
- 뉴스: news_articles (23 레코드, 임베딩 인덱스 없음)
- 트레이딩: trading_signals, shadow_trades
- 분석: deep_reasoning_analyses, news_interpretations
- 메타: data_collection_progress, news_sources

**성능 이슈:**
1. War Room MVP 응답 시간: 10-16초 (목표: <15초)
   - DB 쿼리: 0.5-1.0초 (최적화 필요)
2. N+1 쿼리 패턴 ([repository.py](../backend/database/repository.py))
3. 복합 인덱스 누락
4. 벡터 검색 인덱스 없음
5. 구체화된 뷰 부재

---

## Database Architect Agent 통합 전략

### 핵심 아이디어: 협업 모델

Database Architect Agent는 DB Schema Manager를 **대체하는 것이 아니라 보완**합니다.

```
DB Schema Manager (기존)          Database Architect (신규)
      ↓                                  ↓
JSON 스키마 정의 유지        →    스키마 분석 및 최적화 제안
마이그레이션 생성           →    고급 SQL 기능 추가
기본 검증                  →    심화 검증 + 성능 분석
      ↓                                  ↓
        통합 워크플로우: Enhanced DB Management
```

---

## 통합 계획 (Phase별 접근)

### Phase 1: Database Architect Agent 탐색 및 설치 (보류 중)

**목표**: Claude Code Templates 확인 및 설치 준비

**작업**:
1. NPM 패키지 탐색
   ```bash
   npx claude-code-templates@latest --filter agents
   npx claude-code-templates@latest --agent database-architect --yes
   ```

2. Database Architect Agent 기능 확인
   - 제공되는 명령어/기능
   - 입력 형식 및 출력 형식
   - Claude Code와의 통합 방식

3. 설치 후 기본 테스트
   - stock_prices 테이블 분석
   - 인덱스 권장사항 확인
   - 최적화 제안 검토

**예상 소요 시간**: 2시간

**현재 상태**: ⏸️ 보류 (검토만 진행)

---

### Phase 2: 기존 스크립트 강화 (우선 검토 대상)

**목표**: Database Architect Agent의 기능을 DB Schema Manager 스크립트에 반영

#### 2.1 Enhanced generate_migration.py

**현재 기능:**
- 기본 CREATE TABLE 생성
- 기본 CREATE INDEX 생성
- 컬럼 코멘트 생성

**추가할 기능 (Database Architect에서):**

1. **고급 인덱스 생성**
   ```python
   # BRIN 인덱스 (타임시리즈용)
   if table.get("timeseries", {}).get("enabled"):
       time_column = table["timeseries"]["time_column"]
       sql += f"CREATE INDEX idx_{table_name}_{time_column}_brin "
       sql += f"ON {table_name} USING BRIN ({time_column});\n"

   # 부분 인덱스 (조건부)
   for idx in indexes:
       if "where" in idx:
           sql += f"CREATE INDEX {idx['name']} "
           sql += f"ON {table_name} ({','.join(idx['columns'])}) "
           sql += f"WHERE {idx['where']};\n"

   # GIN 인덱스 (전문 검색용)
   for col in columns:
       if col.get("full_text_search"):
           sql += f"CREATE INDEX idx_{table_name}_{col['name']}_gin "
           sql += f"ON {table_name} USING GIN (to_tsvector('english', {col['name']}));\n"
   ```

2. **제약조건 추가**
   ```python
   # CHECK 제약조건
   if "checks" in table:
       for check in table["checks"]:
           sql += f"ALTER TABLE {table_name} ADD CONSTRAINT {check['name']} "
           sql += f"CHECK ({check['condition']});\n"
   ```

3. **파티셔닝 전략**
   ```python
   # 시계열 파티셔닝
   if table.get("partition_strategy"):
       strategy = table["partition_strategy"]
       if strategy["type"] == "RANGE":
           sql += f"-- Partition strategy: {strategy['column']} by {strategy['interval']}\n"
           sql += f"SELECT create_hypertable('{table_name}', '{strategy['column']}', "
           sql += f"chunk_time_interval => INTERVAL '{strategy['interval']}');\n"
   ```

**파일**: `backend/ai/skills/system/db-schema-manager/scripts/generate_migration_enhanced.py`

**예상 개선**: +50% 더 많은 SQL 기능

---

#### 2.2 Enhanced compare_to_db.py

**현재 기능:**
- 컬럼 비교 (이름, 타입, nullable)

**추가할 기능:**

1. **인덱스 건강 검사**
   ```python
   def check_index_health(table_name: str, schema: dict, cursor):
       # 1. 정의된 인덱스 vs 실제 인덱스
       # 2. 사용되지 않는 인덱스 탐지
       # 3. 인덱스 크기 vs 테이블 크기
       # 4. 중복 인덱스 탐지

       cursor.execute("""
           SELECT indexname, indexdef, pg_size_pretty(pg_relation_size(indexname::regclass))
           FROM pg_indexes WHERE tablename = %s
       """, (table_name,))
   ```

2. **쿼리 성능 분석**
   ```python
   def analyze_query_performance(table_name: str):
       # pg_stat_user_tables 조회
       # 시퀀스 스캔 vs 인덱스 스캔 비율
       # 느린 쿼리 감지
   ```

3. **제약조건 검증**
   ```python
   def verify_constraints(table_name: str, schema: dict, cursor):
       # CHECK 제약조건 확인
       # FOREIGN KEY 무결성 확인
       # NOT NULL 누락 탐지
   ```

4. **성능 메트릭**
   ```python
   def get_table_metrics(table_name: str, cursor):
       # 테이블 크기
       # 레코드 수
       # 인덱스 사용률
       # 예상 블로트
   ```

**파일**: `backend/ai/skills/system/db-schema-manager/scripts/compare_to_db_enhanced.py`

**예상 개선**: +300% 더 많은 검증 기능

---

#### 2.3 Enhanced validate_data.py

**현재 기능:**
- 기본 타입 검증 (int, float, str, bool)

**추가할 기능:**

1. **Enum 검증**
   ```python
   def validate_enum(value, column_schema):
       if "enum" in column_schema:
           if value not in column_schema["enum"]:
               raise ValueError(f"{value} not in {column_schema['enum']}")
   ```

2. **패턴 검증**
   ```python
   def validate_pattern(value, column_schema):
       if "pattern" in column_schema:
           import re
           if not re.match(column_schema["pattern"], value):
               raise ValueError(f"{value} doesn't match pattern {column_schema['pattern']}")
   ```

3. **범위 검증**
   ```python
   def validate_range(value, column_schema):
       if "min" in column_schema and value < column_schema["min"]:
           raise ValueError(f"{value} < {column_schema['min']}")
       if "max" in column_schema and value > column_schema["max"]:
           raise ValueError(f"{value} > {column_schema['max']}")
   ```

4. **비즈니스 규칙 검증**
   ```python
   def validate_business_rules(data, table_schema):
       # 예: dividend_aristocrats의 is_sp500과 is_reit 동시 1 불가
       # 예: stock_prices의 close <= high, close >= low
       # 예: trading_signals의 confidence 0-1 범위
   ```

**파일**: `backend/ai/skills/system/db-schema-manager/scripts/validate_data_enhanced.py`

**예상 개선**: +200% 더 많은 검증 규칙

---

### Phase 3: 새로운 스크립트 추가

#### 3.1 optimize_schema.py (신규)

**목적**: 스키마 최적화 제안

**기능**:
1. 테이블 설계 분석
   - 너무 넓은 테이블 감지 (50+ 컬럼)
   - 정규화 기회 식별
   - 비정규화 기회 식별

2. 인덱스 권장사항
   - 누락된 인덱스 제안
   - 복합 인덱스 제안
   - 사용되지 않는 인덱스 제거 권장

3. 타입 최적화
   - VARCHAR 길이 최적화
   - TEXT → VARCHAR(n) 변환 제안
   - NUMERIC 정밀도 최적화

**파일**: `backend/ai/skills/system/db-schema-manager/scripts/optimize_schema.py`

---

#### 3.2 analyze_performance.py (신규)

**목적**: 실시간 성능 분석

**기능**:
1. 쿼리 성능 모니터링
   - pg_stat_statements 분석
   - 느린 쿼리 Top 10
   - 쿼리 플랜 비용 분석

2. 인덱스 효율성
   - 사용되지 않는 인덱스
   - 인덱스 적중률
   - 인덱스 크기 vs 효과

3. 테이블 건강 상태
   - 테이블 블로트
   - 자동 VACUUM 상태
   - 통계 갱신 필요성

**파일**: `backend/ai/skills/system/db-schema-manager/scripts/analyze_performance.py`

---

#### 3.3 generate_documentation.py (신규)

**목적**: 자동 문서화

**기능**:
1. 데이터 사전 생성
   - 테이블별 HTML/Markdown 문서
   - 컬럼 설명 및 예시
   - 관계도 (ER Diagram)

2. 스키마 변경 이력
   - Git 커밋 기반 변경 추적
   - 마이그레이션 이력
   - 스키마 버전 관리

3. 쿼리 패턴 문서화
   - 자주 사용되는 쿼리
   - Repository 메서드 매핑
   - 성능 특성

**파일**: `backend/ai/skills/system/db-schema-manager/scripts/generate_documentation.py`

---

### Phase 4: 실전 최적화 적용 (War Room MVP 타겟)

**목표**: War Room MVP DB 쿼리 시간 0.5-1.0s → 0.2-0.3s 단축

#### 4.1 즉시 적용 가능한 최적화 (우선순위 높음)

**1. 복합 인덱스 추가**

파일: [backend/database/models.py](../backend/database/models.py)

```python
# NewsArticle 테이블 (lines 98-106)
Index('idx_news_ticker_date', 'tickers', 'published_date'),  # 티커별 뉴스 조회
Index('idx_news_processed', 'published_date', where='processed_at IS NOT NULL'),  # 처리된 뉴스만

# TradingSignal 테이블
Index('idx_signal_ticker_date', 'ticker', 'created_at'),  # 티커별 최신 신호
Index('idx_signal_pending_alert', 'ticker', where='alert_sent = FALSE'),  # 대기 중 알림

# StockPrice 테이블
Index('idx_stock_ticker_time_desc', 'ticker', desc('time')),  # 최신 가격 조회

# ShadowTradingSession 테이블
Index('idx_session_status_updated', 'status', desc('updated_at')),  # 활성 세션 조회
```

**예상 효과**: War Room MVP DB 쿼리 시간 0.3-0.4s 단축

---

**2. Repository N+1 패턴 제거**

파일: [backend/database/repository.py](../backend/database/repository.py)

```python
# Line 90-92: 중복 체크 최적화
# Before:
existing = self.session.query(NewsArticle).filter_by(content_hash=hash).first()
if not existing:
    self.session.add(article)

# After (ON CONFLICT 사용):
from sqlalchemy.dialects.postgresql import insert
stmt = insert(NewsArticle).values(**article_dict)
stmt = stmt.on_conflict_do_nothing(index_elements=['content_hash'])
self.session.execute(stmt)
```

```python
# Lines 541-554: Join 최적화
# Before:
signals = self.session.query(TradingSignal).join(SignalPerformance).filter(...).all()

# After (selectinload 사용):
from sqlalchemy.orm import selectinload
signals = self.session.query(TradingSignal).options(
    selectinload(TradingSignal.performance)
).filter(...).all()
```

**예상 효과**: 0.1-0.2s 단축

---

**3. 쿼리 결과 캐싱**

파일: [backend/database/repository.py](../backend/database/repository.py)

```python
# 새로운 유틸리티
from functools import lru_cache
from datetime import datetime, timedelta

def cache_with_ttl(ttl_seconds=300):
    def decorator(func):
        cache = {}
        def wrapper(*args, **kwargs):
            now = datetime.now()
            key = str(args) + str(kwargs)
            if key in cache:
                value, timestamp = cache[key]
                if (now - timestamp).total_seconds() < ttl_seconds:
                    return value
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator

# NewsRepository에 적용
@cache_with_ttl(300)  # 5분 캐시
def get_recent_articles(self, hours=24, limit=50):
    ...
```

**예상 효과**: 반복 쿼리 0.1-0.2s 단축

---

#### 4.2 단기 최적화 (1주일 내)

**1. TimescaleDB Hypertable 활성화**

파일: `backend/database/migrations/enable_timescaledb.sql`

```sql
-- stock_prices를 hypertable로 변환
SELECT create_hypertable(
    'stock_prices',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- 압축 정책 설정 (7일 후 자동 압축)
ALTER TABLE stock_prices SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'ticker',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('stock_prices', INTERVAL '7 days');
```

**예상 효과**:
- 스토리지 5-10x 감소
- 시계열 쿼리 10-20x 고속화

---

**2. pgvector 임베딩 검색**

파일: `backend/database/migrations/add_vector_search.sql`

```sql
-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- embedding 컬럼을 pgvector 타입으로 변경
ALTER TABLE news_articles
ADD COLUMN embedding_vec vector(1536);

-- 기존 ARRAY 데이터를 vector로 변환
UPDATE news_articles
SET embedding_vec = embedding::vector
WHERE embedding IS NOT NULL;

-- HNSW 인덱스 생성 (빠른 유사도 검색)
CREATE INDEX idx_news_embedding_hnsw
ON news_articles
USING hnsw (embedding_vec vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**예상 효과**:
- 의미 검색 속도 100x+ 향상
- 유사 뉴스 탐색 < 50ms

---

**3. Materialized View 생성**

파일: `backend/database/migrations/create_materialized_views.sql`

```sql
-- 일일 뉴스 요약
CREATE MATERIALIZED VIEW mv_daily_news_summary AS
SELECT
    DATE(published_date) as date,
    source,
    COUNT(*) as article_count,
    AVG(sentiment_score) as avg_sentiment,
    array_agg(DISTINCT ticker) FILTER (WHERE ticker IS NOT NULL) as tickers
FROM news_articles
GROUP BY DATE(published_date), source;

CREATE INDEX ON mv_daily_news_summary (date DESC);

-- 신호 성과 요약
CREATE MATERIALIZED VIEW mv_signal_performance_daily AS
SELECT
    DATE(created_at) as date,
    signal_type,
    action,
    COUNT(*) as signal_count,
    AVG(confidence) as avg_confidence,
    COUNT(*) FILTER (WHERE outcome = 'WIN') * 100.0 / COUNT(*) as win_rate
FROM trading_signals ts
LEFT JOIN signal_performance sp ON ts.id = sp.signal_id
GROUP BY DATE(created_at), signal_type, action;

-- 4시간마다 자동 갱신
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_news_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_signal_performance_daily;
END;
$$ LANGUAGE plpgsql;

-- 크론잡 등록 (pg_cron 필요)
SELECT cron.schedule('refresh-views', '0 */4 * * *', 'SELECT refresh_materialized_views()');
```

**예상 효과**:
- 대시보드 조회 100x 고속화
- 집계 쿼리 부하 제거

---

### Phase 5: 스키마 정의 업데이트

**목표**: JSON 스키마에 Database Architect 권장사항 반영

#### 5.1 stock_prices.json 업데이트

```json
{
  "table_name": "stock_prices",
  "indexes": [
    {
      "name": "idx_stock_price_time_brin",
      "columns": ["time"],
      "type": "BRIN",
      "description": "타임시리즈 데이터용 BRIN 인덱스"
    },
    {
      "name": "idx_stock_ticker_time",
      "columns": ["ticker", "time"],
      "order": "ASC, DESC"
    },
    {
      "name": "idx_stock_recent",
      "columns": ["ticker", "time"],
      "where": "time > CURRENT_DATE - INTERVAL '1 year'",
      "description": "최근 1년 데이터 부분 인덱스"
    }
  ],
  "checks": [
    {
      "name": "chk_stock_price_ohlc",
      "condition": "close >= low AND close <= high AND high >= low"
    },
    {
      "name": "chk_stock_price_positive",
      "condition": "open > 0 AND high > 0 AND low > 0 AND close > 0"
    }
  ],
  "partition_strategy": {
    "type": "RANGE",
    "column": "time",
    "interval": "1 day"
  }
}
```

#### 5.2 news_articles.json 업데이트

```json
{
  "table_name": "news_articles",
  "columns": [
    {
      "name": "embedding_vec",
      "type": "vector(1536)",
      "nullable": true,
      "description": "pgvector 임베딩 (의미 검색용)"
    },
    {
      "name": "ticker",
      "type": "VARCHAR(10)",
      "pattern": "^[A-Z]{1,5}[0-9]?$",
      "description": "주식 티커 (1-5자 대문자 + 선택적 숫자)"
    }
  ],
  "indexes": [
    {
      "name": "idx_news_embedding_hnsw",
      "columns": ["embedding_vec"],
      "type": "HNSW",
      "parameters": {
        "m": 16,
        "ef_construction": 64
      }
    },
    {
      "name": "idx_news_fulltext",
      "columns": ["title", "content"],
      "type": "GIN",
      "expression": "to_tsvector('english', title || ' ' || content)"
    },
    {
      "name": "idx_news_ticker_date",
      "columns": ["tickers", "published_date"]
    },
    {
      "name": "idx_news_processed_only",
      "columns": ["published_date"],
      "where": "processed_at IS NOT NULL"
    }
  ],
  "checks": [
    {
      "name": "chk_news_dates",
      "condition": "published_date <= crawled_at"
    }
  ]
}
```

#### 5.3 trading_signals.json 업데이트

```json
{
  "table_name": "trading_signals",
  "columns": [
    {
      "name": "action",
      "type": "VARCHAR(10)",
      "enum": ["BUY", "SELL", "HOLD", "PASS"],
      "nullable": false
    },
    {
      "name": "confidence",
      "type": "NUMERIC(5,2)",
      "min": 0,
      "max": 100,
      "description": "신뢰도 (0-100)"
    }
  ],
  "indexes": [
    {
      "name": "idx_signal_ticker_date",
      "columns": ["ticker", "created_at"],
      "order": "ASC, DESC"
    },
    {
      "name": "idx_signal_pending_alerts",
      "columns": ["ticker"],
      "where": "alert_sent = FALSE"
    }
  ],
  "checks": [
    {
      "name": "chk_signal_confidence",
      "condition": "confidence >= 0 AND confidence <= 100"
    },
    {
      "name": "chk_signal_target_price",
      "condition": "target_price IS NULL OR target_price > 0"
    }
  ]
}
```

---

## 구현 로드맵

### Week 1: 검토 및 계획 (현재)
- [x] Database Architect Agent 검토 완료
- [x] 기존 시스템 분석 완료
- [x] 통합 계획 수립 완료
- [ ] 사용자 승인 대기

### Week 2: 즉시 최적화 (Database Architect 없이도 가능)
- [ ] 복합 인덱스 추가 (models.py)
- [ ] Repository N+1 패턴 제거
- [ ] 쿼리 캐싱 구현
- [ ] War Room MVP 성능 측정

**예상 효과**: DB 쿼리 0.5-1.0s → 0.3-0.5s

### Week 3-4: Database Architect Agent 설치 및 통합
- [ ] NPM 패키지 설치
- [ ] Enhanced 스크립트 개발
  - [ ] generate_migration_enhanced.py
  - [ ] compare_to_db_enhanced.py
  - [ ] validate_data_enhanced.py
- [ ] 신규 스크립트 개발
  - [ ] optimize_schema.py
  - [ ] analyze_performance.py
  - [ ] generate_documentation.py

**예상 효과**: 자동화된 최적화 권장 시스템 구축

### Month 2: 고급 최적화
- [ ] TimescaleDB hypertable 활성화
- [ ] pgvector 임베딩 검색 구현
- [ ] Materialized View 생성
- [ ] 스키마 정의 업데이트 (17개 테이블)

**예상 효과**: DB 쿼리 0.3-0.5s → 0.2-0.3s

### Month 3: 모니터링 및 튜닝
- [ ] pg_stat_statements 활성화
- [ ] 성능 대시보드 구축
- [ ] 자동 문서 생성
- [ ] 지속적 최적화 프로세스 확립

---

## 성공 기준

### 기술적 지표
- [ ] War Room MVP DB 쿼리 시간 < 0.3s
- [ ] 전체 응답 시간 < 13s (안정적으로 15s 이내)
- [ ] 뉴스 임베딩 검색 < 50ms
- [ ] 복합 인덱스 적용률 100%
- [ ] N+1 쿼리 패턴 0개

### 운영 지표
- [ ] 테이블 크기 50% 감소 (압축 후)
- [ ] 인덱스 사용률 > 90%
- [ ] 사용되지 않는 인덱스 0개
- [ ] 스키마 검증 자동화 100%

### 문서화
- [ ] 17개 테이블 자동 문서 생성
- [ ] ER 다이어그램 자동 생성
- [ ] 성능 가이드라인 문서화

---

## 핵심 파일 리스트

### 수정할 파일 (12개)

**Backend - Database Models**
1. [backend/database/models.py](../backend/database/models.py) - 복합 인덱스 추가

**Backend - Repository**
2. [backend/database/repository.py](../backend/database/repository.py) - N+1 패턴 제거, 캐싱 추가

**DB Schema Manager - 기존 스크립트 강화**
3. `backend/ai/skills/system/db-schema-manager/scripts/generate_migration_enhanced.py`
4. `backend/ai/skills/system/db-schema-manager/scripts/compare_to_db_enhanced.py`
5. `backend/ai/skills/system/db-schema-manager/scripts/validate_data_enhanced.py`

**DB Schema Manager - 신규 스크립트**
6. `backend/ai/skills/system/db-schema-manager/scripts/optimize_schema.py`
7. `backend/ai/skills/system/db-schema-manager/scripts/analyze_performance.py`
8. `backend/ai/skills/system/db-schema-manager/scripts/generate_documentation.py`

**Migrations**
9. `backend/database/migrations/20260102_add_composite_indexes.sql`
10. `backend/database/migrations/20260102_enable_timescaledb.sql`
11. `backend/database/migrations/20260102_add_vector_search.sql`
12. `backend/database/migrations/20260102_create_materialized_views.sql`

### 업데이트할 스키마 (3개 우선)
13. [backend/ai/skills/system/db-schema-manager/schemas/stock_prices.json](../backend/ai/skills/system/db-schema-manager/schemas/stock_prices.json)
14. [backend/ai/skills/system/db-schema-manager/schemas/news_articles.json](../backend/ai/skills/system/db-schema-manager/schemas/news_articles.json)
15. [backend/ai/skills/system/db-schema-manager/schemas/trading_signals.json](../backend/ai/skills/system/db-schema-manager/schemas/trading_signals.json)

---

## 리스크 및 완화 전략

### 리스크

**1. TimescaleDB 변환 리스크**
- 기존 데이터 마이그레이션 시 다운타임 가능
- **완화책**: Blue-Green 배포, 읽기 전용 복제본에서 먼저 테스트

**2. pgvector 확장 설치**
- PostgreSQL 확장 설치 권한 필요
- **완화책**: Docker 환경에서 사전 테스트, 단계적 롤아웃

**3. 인덱스 추가 부하**
- 대량 인덱스 생성 시 DB 부하
- **완화책**: CONCURRENTLY 옵션 사용, 비피크 시간 적용

**4. Repository 변경 영향**
- N+1 패턴 제거 시 기존 코드 영향
- **완화책**: 단위 테스트 작성, 단계적 적용

### 롤백 전략

**즉시 롤백 (< 5분)**
```sql
-- 인덱스 제거
DROP INDEX CONCURRENTLY idx_news_ticker_date;
DROP INDEX CONCURRENTLY idx_signal_ticker_date;

-- Repository 변경 롤백
git checkout backend/database/repository.py
systemctl restart ai-trading-system
```

**완전 롤백 (< 30분)**
```sql
-- Materialized View 제거
DROP MATERIALIZED VIEW mv_daily_news_summary;
DROP MATERIALIZED VIEW mv_signal_performance_daily;

-- pgvector 제거
ALTER TABLE news_articles DROP COLUMN embedding_vec;

-- TimescaleDB 비활성화 (복잡, 백업 필수)
-- 별도 롤백 스크립트 준비
```

---

## 최종 권장사항

### 즉시 실행 (사용자 승인 후)

1. ✅ **복합 인덱스 추가** (2시간, 영향도 낮음)
   - models.py 수정
   - 마이그레이션 SQL 실행
   - 성능 측정

2. ✅ **Repository 최적화** (4시간, 단계적 적용)
   - N+1 패턴 제거
   - 캐싱 구현
   - 단위 테스트

**예상 효과**: War Room MVP 응답 시간 즉시 2-3초 단축

### 차기 진행

3. ⏸️ **Database Architect Agent 설치** (검토 완료, 실행 보류)
4. ⏸️ **고급 최적화** (TimescaleDB, pgvector, Materialized Views)

---

## 참고 자료

- [Claude Code Templates Review](260102_Claude_Code_Templates_Review.md)
- [DB Schema Manager SKILL.md](../backend/ai/skills/system/db-schema-manager/SKILL.md)
- [Schema Registry](../backend/ai/skills/system/db-schema-manager/SCHEMA_REGISTRY.md)
- [Migration Guide](../backend/ai/skills/system/db-schema-manager/MIGRATION_GUIDE.md)
