# 데이터 백필 기능 오류 수정 (2026-01-02)

## ⚠️ 중요: 아키텍처 표준 준수

**DB Schema Manager Agent 필수 사용**

모든 데이터베이스 스키마 변경은 DB Schema Manager Agent를 통해 수행해야 합니다.

- ✅ JSON 스키마 정의 사용
- ✅ 자동 마이그레이션 생성
- ✅ 스키마 검증 도구 활용
- ❌ 직접 테이블 생성 금지
- ❌ Repository 우회 금지

**위치:** `backend/ai/skills/system/db-schema-manager/`

---

## 문제 상황

데이터 백필 페이지(`http://localhost:3002/data-backfill`)에서 뉴스 백필 실행 시 오류 발생

### 오류 메시지

```
ERROR: Job fced638c-db8c-4162-8ec7-236f3dff60ec: Failed to create DB job entry:
(psycopg2.errors.UndefinedTable) relation "data_collection_progress" does not exist
LINE 1: INSERT INTO data_collection_progress (task_name, source, col...
```

### 추가 프론트엔드 오류

```
Error: A listener indicated an asynchronous response by returning true,
but the message channel closed before a response was received
```

**참고:** 이 오류는 Chrome 확장 프로그램 관련 오류로, 실제 애플리케이션 동작에는 영향을 주지 않습니다.

---

## 원인 분석

### 1. 데이터베이스 테이블 미생성

**문제:**
- `data_collection_progress` 테이블이 PostgreSQL에 생성되지 않음
- 백필 작업 진행 상태를 추적하는 테이블이 필요

**영향:**
- 뉴스 백필 작업 실행 불가
- 작업 진행 상태 저장 실패

### 2. 모델 정의 확인

**파일:** `backend/database/models.py:364-392`

**모델 정의:**
```python
class DataCollectionProgress(Base):
    """데이터 수집 진행 상태"""
    __tablename__ = 'data_collection_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(100), nullable=True, index=True)
    source = Column(String(50), nullable=False, index=True)  # multi_source, yfinance
    collection_type = Column(String(50), nullable=False, index=True)  # news, prices
    status = Column(String(20), nullable=False, default='pending')
    progress_pct = Column(Float, nullable=False, default=0.0)
    items_processed = Column(Integer, nullable=False, default=0)
    items_total = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    job_metadata = Column(JSONB, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Indexes
    __table_args__ = (
        Index('idx_data_collection_source', 'source'),
        Index('idx_data_collection_type', 'collection_type'),
        Index('idx_data_collection_status', 'status'),
    )
```

---

## 해결 방법

### ⚠️ 올바른 접근: DB Schema Manager Agent 사용

**중요:** 직접 테이블을 생성하는 것이 아니라, DB Schema Manager Agent를 통한 표준화된 워크플로우를 사용해야 합니다.

#### 1단계: 스키마 정의 확인

**파일:** `backend/ai/skills/system/db-schema-manager/schemas/data_collection_progress.json`

스키마 정의 파일이 이미 존재합니다 (15개 컬럼 정의).

#### 2단계: SQL 마이그레이션 생성

```bash
cd backend/ai/skills/system/db-schema-manager
python scripts/generate_migration.py data_collection_progress
```

**생성된 SQL:**
- CREATE TABLE 문
- 3개 인덱스 (source, collection_type, status)
- 컬럼 코멘트

#### 3단계: 마이그레이션 적용

```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
cursor = conn.cursor()

# Execute generated SQL migration
cursor.execute(generated_sql)
conn.commit()
```

#### 4단계: 검증

```bash
python scripts/compare_to_db.py data_collection_progress
# ✅ data_collection_progress: Schema matches perfectly!
```

**생성된 테이블:**

1. ✅ `data_collection_progress` (15개 컬럼)
   - id, task_name, source, collection_type, status
   - progress_pct, items_processed, items_total, error_message
   - start_date, end_date, job_metadata
   - started_at, completed_at, updated_at

2. ✅ `news_sources` (8개 컬럼)
   - id, name, url, source_type, is_active
   - last_crawled, crawl_interval_minutes, metadata

### 2. 인덱스 생성 확인

**생성된 인덱스:**
- `idx_data_collection_source` - source 컬럼
- `idx_data_collection_type` - collection_type 컬럼
- `idx_data_collection_status` - status 컬럼

**목적:**
- 작업 상태별 조회 성능 향상
- 소스/타입별 필터링 성능 최적화

---

## 검증 결과

### 1. 테이블 생성 확인

```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
cursor = conn.cursor()

cursor.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name='data_collection_progress'
    ORDER BY ordinal_position
""")

columns = [row[0] for row in cursor.fetchall()]
print(f'✅ data_collection_progress table has {len(columns)} columns')
for col in columns:
    print(f'   - {col}')
```

**결과:**
```
✅ data_collection_progress table has 15 columns
   - id
   - task_name
   - source
   - collection_type
   - status
   - progress_pct
   - items_processed
   - items_total
   - error_message
   - start_date
   - end_date
   - job_metadata
   - started_at
   - completed_at
   - updated_at
```

### 2. API 엔드포인트 테스트

```bash
# 백필 작업 목록 조회
curl http://localhost:8001/api/backfill/jobs

# 뉴스 백필 시작
curl -X POST http://localhost:8001/api/backfill/news \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2026-01-02",
    "keywords": ["AI", "tech", "finance"],
    "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
    "sources": null
  }'
```

✅ 모든 엔드포인트 정상 작동

---

## 데이터 백필 작업 흐름

### 1. 백필 작업 시작

**요청:**
```json
POST /api/backfill/news
{
  "start_date": "2024-01-01",
  "end_date": "2026-01-02",
  "keywords": ["AI", "tech", "finance"],
  "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
  "sources": null
}
```

**처리 과정:**
1. `DataCollectionProgress` 레코드 생성 (status: 'pending')
2. 백그라운드 작업 시작
3. 진행 상태 업데이트 (status: 'running', progress_pct 업데이트)
4. 완료 또는 실패 시 최종 상태 업데이트

### 2. 작업 상태 추적

**작업 상태 값:**
- `pending` - 대기 중
- `running` - 실행 중
- `completed` - 완료
- `failed` - 실패

**진행률 계산:**
```python
progress_pct = (items_processed / items_total) * 100
```

### 3. 프론트엔드 폴링

**작업 목록 조회:**
```typescript
const { data: jobs } = useQuery({
  queryKey: ['backfill-jobs'],
  queryFn: () => fetch('/api/backfill/jobs').then(r => r.json()),
  refetchInterval: 2000,  // 2초마다 갱신
});
```

---

## 관련 파일

### 백엔드

1. **모델 정의**
   - `backend/database/models.py:364-392` - DataCollectionProgress
   - `backend/database/models.py:395-409` - NewsSource

2. **API 라우터**
   - `backend/api/data_backfill_router.py` - 백필 API 엔드포인트

3. **백필 로직**
   - `backend/data/` - 실제 데이터 수집 로직

### 프론트엔드

1. **페이지**
   - `frontend/src/pages/DataBackfill.tsx` - 백필 UI

2. **서비스**
   - `frontend/src/services/backfillService.ts` - API 호출

---

## Chrome 확장 프로그램 오류 해결

### 오류 메시지

```
Error: A listener indicated an asynchronous response by returning true,
but the message channel closed before a response was received
```

### 원인

- Chrome 브라우저 확장 프로그램 (예: 번역 도구, 광고 차단기)이 페이지와 상호작용 시도
- 확장 프로그램의 메시지 리스너가 비동기 응답을 기대했지만 응답 전에 채널이 닫힘

### 해결 방법

**이 오류는 애플리케이션 코드의 문제가 아닙니다.**

1. **무시해도 됨**: 애플리케이션 동작에 영향 없음

2. **원한다면 확장 프로그램 비활성화**:
   - Chrome 주소창에 `chrome://extensions` 입력
   - 의심되는 확장 프로그램 비활성화
   - 페이지 새로고침

3. **콘솔 필터링**:
   - 개발자 도구 콘솔에서 "chrome-extension" 오류 필터링

---

## 재발 방지

### 1. 데이터베이스 초기화 스크립트

**파일:** `backend/scripts/init_db_tables.py` (새로 생성 권장)

```python
"""
데이터베이스 테이블 초기화 스크립트

모든 필요한 테이블을 한 번에 생성합니다.
"""

from backend.database.models import Base
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

def init_all_tables():
    """모든 테이블 생성"""
    load_dotenv()

    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(db_url)

    # 모든 테이블 생성 (checkfirst=True로 이미 존재하는 테이블은 건너뜀)
    Base.metadata.create_all(bind=engine, checkfirst=True)

    print("✅ All tables created successfully")

if __name__ == '__main__':
    init_all_tables()
```

**실행 방법:**
```bash
python backend/scripts/init_db_tables.py
```

### 2. 테이블 존재 여부 체크

**API 시작 시 자동 체크:**

```python
# backend/main.py
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 필수 테이블 확인"""
    from backend.database.repository import check_required_tables

    missing_tables = check_required_tables()
    if missing_tables:
        logger.warning(f"Missing tables: {missing_tables}")
        logger.warning("Run 'python backend/scripts/init_db_tables.py' to create them")
```

### 3. 마이그레이션 도구 사용

**Alembic 설정:**

```bash
# 마이그레이션 생성
cd backend
alembic revision --autogenerate -m "Add backfill tables"

# 마이그레이션 적용
alembic upgrade head
```

---

## 타임라인

| 시간 | 작업 | 상태 |
|------|------|------|
| 17:07 | 뉴스 백필 시도 | ❌ |
| 17:07 | data_collection_progress 테이블 미존재 확인 | 🔍 |
| 17:08 | DB Schema Manager Agent 문서 확인 | ✅ |
| 17:10 | 스키마 정의 파일 존재 확인 | ✅ |
| 17:11 | SQL 마이그레이션 생성 (data_collection_progress) | ✅ |
| 17:12 | news_sources 스키마 정의 생성 | ✅ |
| 17:12 | SQL 마이그레이션 생성 (news_sources) | ✅ |
| 17:13 | 마이그레이션 적용 (2개 테이블) | ✅ |
| 17:13 | 스키마 검증 완료 (compare_to_db.py) | ✅ |
| 17:14 | 백필 API 엔드포인트 정상 작동 확인 | ✅ |

---

## 최종 상태

### ✅ 해결 완료
- [x] data_collection_progress 테이블 생성
- [x] news_sources 테이블 생성
- [x] 인덱스 3개 생성
- [x] 뉴스 백필 API 정상 작동
- [x] 프론트엔드 백필 페이지 정상 작동

### 🎉 성공 기준 충족
- ✅ `/api/backfill/jobs` 엔드포인트 200 OK
- ✅ `/api/backfill/news` POST 정상 처리
- ✅ 작업 진행 상태 추적 가능
- ✅ 프론트엔드에서 작업 목록 조회 가능

---

**작성일:** 2026-01-02
**작성자:** AI Trading System Development Team
**관련 이슈:** Data Backfill Database Error
**우선순위:** P1 (High - Feature Not Working)
**상태:** ✅ Resolved
