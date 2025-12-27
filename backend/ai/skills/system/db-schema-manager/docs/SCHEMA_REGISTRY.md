# DB Schema Manager - Schema Registry

## 📋 전체 스키마 목록

### 시계열 데이터
- **stock_prices**: 주가 OHLCV 데이터 (TimescaleDB Hypertable)
  - Primary Key: id
  - Time Column: time
  - Indexes: ticker, time, ticker+time

### 콘텐츠 데이터
- **news_articles**: 뉴스 기사
  - Primary Key: id
  - Unique Key: url
  - Special: Vector embedding (pgvector), JSONB metadata

### 트레이딩 데이터
- **trading_signals**: AI 매매 시그널
  - Primary Key: id
  - Indexes: ticker, signal_type, created_at, source

### 추적 데이터
- **data_collection_progress**: 데이터 수집 작업 추적
  - Primary Key: id
  - Indexes: source, collection_type, status

### 배당 데이터
- **dividend_aristocrats**: 배당 귀족주 (25+ 연속 배당 증가)
  - Primary Key: ticker
  - Indexes: sector, consecutive_years

---

## 🔍 스키마 표준

### 필수 컬럼
- **모든 테이블**: `id` (Primary Key), `created_at` (생성 시각)
- **시계열 테이블**: `time` (TimescaleDB 표준)
- **업데이트 테이블**: `updated_at` (수정 시각)

### 네이밍 컨벤션
- 테이블명: `snake_case` (복수형)
- 컬럼명: `snake_case`
- 시간 컬럼: `time` (시계열), `*_at` (일반)
- 불린: `is_*`, `has_*`
- 외래키: `*_id`

### 데이터 타입 매핑

| 용도 | PostgreSQL 타입 | 예시 |
|------|----------------|------|
| 짧은 문자열 | VARCHAR(50) | 코드, 상태 |
| 중간 문자열 | VARCHAR(100) | 소스, 이름 |
| 긴 문자열 | VARCHAR(500) | 제목 |
| 긴 텍스트 | TEXT | 본문 |
| 정수 | INTEGER | ID, 카운트 |
| 큰 정수 | BIGINT | 거래량 |
| 실수 | NUMERIC | 가격 |
| 시간 | TIMESTAMP | 일반 시각 |
| 시계열 시간 | TIMESTAMP WITH TIME ZONE | TimescaleDB |
| JSON | JSONB | 메타데이터 |
| 배열 | VARCHAR[] | 티커 목록 |
| 벡터 | VECTOR(1536) | OpenAI embedding |

---

## 📖 사용 가이드

### 새 테이블 추가 절차
1. `schemas/{table_name}.json` 파일 생성
2. `python scripts/validate_schema.py {table_name}` 실행
3. `python scripts/generate_migration.py {table_name}` 실행
4. 생성된 SQL로 테이블 생성
5. `backend/database/models.py`에 SQLAlchemy 모델 추가
6. `backend/database/repository.py`에 Repository 추가

### 스키마 변경 절차
1. `schemas/{table_name}.json` 수정
2. `python scripts/compare_to_db.py {table_name}` 실행
3. 차이 확인
4. Alembic migration 생성 (권장) 또는 수동 ALTER TABLE

### 데이터 삽입 전 검증
```python
# 1. 스키마 검증
python scripts/validate_data.py table_name '{"field": "value"}'

# 2. 통과하면 Repository 사용
from backend.database.repository import YourRepository
repo = YourRepository(session)
repo.save(data)
```

---

## 🔗 관련 문서

- **[Database Standards](../../../../../../.gemini/antigravity/brain/c360bcf5-0a4d-48b1-b58b-0e2ef4000b25/database_standards.md)**: 전체 DB 사용 규칙
- **[Database Usage Analysis](../../../../../../.gemini/antigravity/brain/c360bcf5-0a4d-48b1-b58b-0e2ef4000b25/walkthrough.md)**: 현재 DB 사용  현황
- **[models.py](../../../../database/models.py)**: SQLAlchemy 모델 정의
- **[repository.py](../../../../database/repository.py)**: Repository 패턴 구현

---

**Last Updated**: 2025-12-27
