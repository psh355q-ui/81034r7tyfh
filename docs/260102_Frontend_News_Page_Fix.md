# 프론트엔드 뉴스 페이지 오류 수정 (2026-01-02)

## 문제 상황

뉴스 페이지(`http://localhost:3002/news`)에서 500 Internal Server Error 발생
- API 엔드포인트: `/api/news/articles?actionable_only=true`
- 프론트엔드가 뉴스 데이터를 불러오지 못함

## 발견된 오류

### 1. NewsArticle 모델 속성명 불일치

**오류 메시지:**
```
AttributeError: type object 'NewsArticle' has no attribute 'published_at'.
Did you mean: 'published_date'?
```

**원인:**
- 코드에서 `NewsArticle.published_at` 사용
- 실제 데이터베이스 모델은 `published_date` 정의

**위치:**
- `backend/data/news_analyzer.py` (3곳)

### 2. GroundingSearchLog 모델 속성명 불일치

**오류 메시지:**
```
AttributeError: type object 'GroundingSearchLog' has no attribute 'created_at'
AttributeError: type object 'GroundingSearchLog' has no attribute 'cost_usd'
```

**원인:**
- 코드에서 `created_at`, `cost_usd` 사용
- 실제 모델은 `search_date`, `estimated_cost` 정의

**위치:**
- `backend/api/emergency_router.py` (7곳)

### 3. 데이터베이스 테이블 미생성

**오류 메시지:**
```
sqlite3.OperationalError: no such column: news_articles.content
```

**원인:**
- PostgreSQL 데이터베이스에 뉴스 관련 테이블이 생성되지 않음
- SQLAlchemy ORM이 존재하지 않는 테이블을 조회하려 시도

---

## 해결 방법

### 1. NewsArticle 속성명 수정

**파일:** `backend/data/news_analyzer.py`

**수정 내용:**

#### Line 402 - get_analyzed_articles()
```python
# BEFORE
return query.order_by(NewsArticle.published_at.desc()).limit(limit).all()

# AFTER
return query.order_by(NewsArticle.published_date.desc()).limit(limit).all()
```

#### Line 422 - get_ticker_news()
```python
# BEFORE
"published_at": article.published_at.isoformat() if article.published_at else None,

# AFTER
"published_at": article.published_date.isoformat() if article.published_date else None,
```

#### Line 438 - get_high_impact_news()
```python
# BEFORE
.order_by(NewsArticle.published_at.desc())

# AFTER
.order_by(NewsArticle.published_date.desc())
```

---

### 2. GroundingSearchLog 속성명 수정

**파일:** `backend/api/emergency_router.py`

**수정 내용:**

#### Line 124 - get_grounding_count_today()
```python
# BEFORE
func.date(GroundingSearchLog.created_at) == date.today()

# AFTER
func.date(GroundingSearchLog.search_date) == date.today()
```

#### Line 158 - track_grounding_search()
```python
# BEFORE
log = GroundingSearchLog(
    ticker=ticker.upper(),
    search_query=f"latest news about {ticker.upper()} stock",
    results_count=results_count,
    cost_usd=cost,
    emergency_trigger=emergency_trigger,
    was_emergency=emergency_trigger is not None
)

# AFTER
log = GroundingSearchLog(
    ticker=ticker.upper(),
    search_query=f"latest news about {ticker.upper()} stock",
    results_count=results_count,
    estimated_cost=cost,  # ✅ CHANGED
    emergency_trigger=emergency_trigger,
    was_emergency=emergency_trigger is not None
)
```

#### Lines 198, 201 - get_grounding_usage() (Today's usage)
```python
# BEFORE
today_data = db.query(
    func.count(GroundingSearchLog.id).label('count'),
    func.sum(GroundingSearchLog.cost_usd).label('cost'),
    func.count(func.distinct(GroundingSearchLog.ticker)).label('tickers')
).filter(
    func.date(GroundingSearchLog.created_at) == today
).first()

# AFTER
today_data = db.query(
    func.count(GroundingSearchLog.id).label('count'),
    func.sum(GroundingSearchLog.estimated_cost).label('cost'),  # ✅ CHANGED
    func.count(func.distinct(GroundingSearchLog.ticker)).label('tickers')
).filter(
    func.date(GroundingSearchLog.search_date) == today  # ✅ CHANGED
).first()
```

#### Lines 208, 211-212 - get_grounding_usage() (Month's usage)
```python
# BEFORE
month_data = db.query(
    func.count(GroundingSearchLog.id).label('count'),
    func.sum(GroundingSearchLog.cost_usd).label('cost'),
    func.count(func.distinct(GroundingSearchLog.ticker)).label('tickers')
).filter(
    extract('year', GroundingSearchLog.created_at) == now.year,
    extract('month', GroundingSearchLog.created_at) == now.month
).first()

# AFTER
month_data = db.query(
    func.count(GroundingSearchLog.id).label('count'),
    func.sum(GroundingSearchLog.estimated_cost).label('cost'),  # ✅ CHANGED
    func.count(func.distinct(GroundingSearchLog.ticker)).label('tickers')
).filter(
    extract('year', GroundingSearchLog.search_date) == now.year,  # ✅ CHANGED
    extract('month', GroundingSearchLog.search_date) == now.month  # ✅ CHANGED
).first()
```

#### Lines 269-270 - get_monthly_cost_report()
```python
# BEFORE
searches = db.query(GroundingSearchLog).filter(
    extract('year', GroundingSearchLog.created_at) == year,
    extract('month', GroundingSearchLog.created_at) == month
).all()

# AFTER
searches = db.query(GroundingSearchLog).filter(
    extract('year', GroundingSearchLog.search_date) == year,  # ✅ CHANGED
    extract('month', GroundingSearchLog.search_date) == month  # ✅ CHANGED
).all()
```

#### Line 283 - get_monthly_cost_report() (Cost calculation)
```python
# BEFORE
total_cost = sum(s.cost_usd for s in searches)

# AFTER
total_cost = sum(s.estimated_cost for s in searches)  # ✅ CHANGED
```

---

### 3. 데이터베이스 테이블 생성

**환경:**
- PostgreSQL 5433 포트 (localhost)
- 데이터베이스: `ai_trading`
- 사용자: `postgres`

**생성 스크립트:**
```python
from backend.database.models import Base, NewsArticle, NewsAnalysis, NewsTickerRelevance, AnalysisResult, GroundingSearchLog
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(db_url)

# Create all news-related tables
news_tables = [
    ('NewsArticle', NewsArticle),
    ('NewsAnalysis', NewsAnalysis),
    ('NewsTickerRelevance', NewsTickerRelevance),
    ('AnalysisResult', AnalysisResult),
    ('GroundingSearchLog', GroundingSearchLog),
]

for table_name, model_class in news_tables:
    model_class.__table__.create(bind=engine, checkfirst=True)
    print(f'✅ {table_name} table ready')
```

**생성된 테이블:**
1. ✅ `news_articles` (19개 컬럼)
   - id, title, **content**, url, source, **published_date**, crawled_at, content_hash, author, summary
   - embedding, tags, tickers, sentiment_score, sentiment_label, source_category, metadata, processed_at, embedding_model

2. ✅ `news_analysis`
   - article_id (FK), sentiment_overall, impact_magnitude, trading_actionable, etc.

3. ✅ `news_ticker_relevance`
   - article_id (FK), ticker, relevance_score, sentiment_for_ticker

4. ✅ `analysis_results`
   - article_id (FK), agent_name, analysis_data, confidence_score, etc.

5. ✅ `grounding_search_log`
   - ticker, search_query, results_count, **search_date**, **estimated_cost**, emergency_trigger, was_emergency

---

## 데이터베이스 모델 정의 (참고)

### NewsArticle (models.py:66-95)
```python
class NewsArticle(Base):
    __tablename__ = 'news_articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # ✅ EXISTS
    url = Column(String(1000), nullable=False, unique=True)
    source = Column(String(100), nullable=False)
    published_date = Column(DateTime, nullable=False)  # ✅ NOT published_at
    crawled_at = Column(DateTime, nullable=False, default=datetime.now)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    author = Column(String(200), nullable=True)
    summary = Column(Text, nullable=True)

    # NLP & Embedding Fields
    embedding = Column(ARRAY(Float), nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    tickers = Column(ARRAY(String), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(20), nullable=True)
    source_category = Column(String(50), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    embedding_model = Column(String(100), nullable=True)
```

### GroundingSearchLog (models.py:300-315)
```python
class GroundingSearchLog(Base):
    __tablename__ = 'grounding_search_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    search_query = Column(Text, nullable=False)
    results_count = Column(Integer, nullable=False, default=0)
    search_date = Column(DateTime, nullable=False, default=datetime.now, index=True)  # ✅ NOT created_at
    estimated_cost = Column(Float, nullable=False, default=0.0)  # ✅ NOT cost_usd
    emergency_trigger = Column(String(100), nullable=True)
    was_emergency = Column(Boolean, nullable=False, default=False)

    # Metadata
    user_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
```

---

## 수정 파일 요약

### 수정된 파일 (2개)
1. `backend/data/news_analyzer.py`
   - Line 402: `published_at` → `published_date`
   - Line 422: `published_at` → `published_date`
   - Line 438: `published_at` → `published_date`

2. `backend/api/emergency_router.py`
   - Line 124: `created_at` → `search_date`
   - Line 158: `cost_usd` → `estimated_cost`
   - Line 198: `cost_usd` → `estimated_cost`
   - Line 201: `created_at` → `search_date`
   - Line 208: `cost_usd` → `estimated_cost`
   - Line 211-212: `created_at` → `search_date` (2곳)
   - Line 269-270: `created_at` → `search_date` (2곳)
   - Line 283: `cost_usd` → `estimated_cost`

### 변경 없음
- `backend/database/models.py` - 모델 정의는 이미 올바름
- `backend/api/news_router.py` - 엔드포인트는 정상

---

## 검증 결과

### 1. 코드 수정 검증
```bash
# news_analyzer.py 확인
grep -n "published_at\|published_date" backend/data/news_analyzer.py

# emergency_router.py 확인
grep -n "created_at\|search_date\|cost_usd\|estimated_cost" backend/api/emergency_router.py
```

✅ 모든 속성명이 올바르게 수정됨

### 2. 데이터베이스 테이블 검증
```python
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, user='postgres', password='Qkqhdi1!', database='ai_trading')
cursor = conn.cursor()

cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='news_articles' ORDER BY ordinal_position")
columns = [row[0] for row in cursor.fetchall()]

print(f"✅ news_articles table has {len(columns)} columns")
print(f"   content column: {'✅ EXISTS' if 'content' in columns else '❌ MISSING'}")
print(f"   published_date column: {'✅ EXISTS' if 'published_date' in columns else '❌ MISSING'}")
```

**결과:**
```
✅ news_articles table has 19 columns
   content column: ✅ EXISTS
   published_date column: ✅ EXISTS
```

### 3. API 엔드포인트 테스트
```bash
# 뉴스 목록 조회 (actionable_only=false)
curl http://localhost:8001/api/news/articles?limit=50&hours=24&actionable_only=false

# 뉴스 목록 조회 (actionable_only=true)
curl http://localhost:8001/api/news/articles?limit=50&hours=24&actionable_only=true

# Emergency 상태 확인
curl http://localhost:8001/api/emergency/status

# Grounding 사용량 확인
curl http://localhost:8001/api/emergency/grounding/usage
```

✅ 모든 API 엔드포인트 정상 작동

---

## 재발 방지 방안

### 1. 타입 체크 강화
```python
# backend/data/news_analyzer.py
from typing import List, Dict, Any
from backend.database.models import NewsArticle

def get_analyzed_articles(db: Session, limit: int, sentiment: str = None, actionable_only: bool = False) -> List[NewsArticle]:
    """타입 힌트를 명시하여 IDE에서 자동완성 지원"""
    # ...
```

### 2. 모델 속성 상수화
```python
# backend/database/models.py
class NewsArticle(Base):
    __tablename__ = 'news_articles'

    # Column constants for autocomplete
    COLUMN_PUBLISHED_DATE = 'published_date'  # NOT published_at
    COLUMN_CONTENT = 'content'

    published_date = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
```

### 3. 통합 테스트 추가
```python
# backend/tests/test_news_api.py
def test_news_articles_api():
    """뉴스 API 엔드포인트 통합 테스트"""
    response = client.get("/api/news/articles?limit=10&actionable_only=true")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

### 4. 데이터베이스 마이그레이션 자동화
```bash
# Alembic 마이그레이션 스크립트 개선
cd backend
python -m alembic revision --autogenerate -m "Add news tables"
python -m alembic upgrade head
```

---

## 참고 자료

### 관련 파일
- `backend/database/models.py` - 데이터베이스 모델 정의
- `backend/data/news_analyzer.py` - 뉴스 분석 로직
- `backend/api/news_router.py` - 뉴스 API 라우터
- `backend/api/emergency_router.py` - Emergency 상태 API

### 관련 문서
- `docs/260101_Claude_Features_Analysis.md` - Claude 신기능 분석
- `docs/260102_War_Room_MVP_Skills_Migration_Plan.md` - War Room MVP Skills 마이그레이션 계획

### 환경 설정
- `.env` - 데이터베이스 연결 정보
  - `DB_HOST=localhost`
  - `DB_PORT=5433`
  - `DB_NAME=ai_trading`
  - `DB_USER=postgres`
  - `DB_PASSWORD=Qkqhdi1!`

---

## 타임라인

| 시간 | 작업 | 상태 |
|------|------|------|
| 11:30 | 뉴스 페이지 500 오류 발견 | ❌ |
| 11:35 | NewsArticle.published_at 오류 식별 | 🔍 |
| 11:40 | news_analyzer.py 3곳 수정 완료 | ✅ |
| 11:45 | GroundingSearchLog 오류 식별 | 🔍 |
| 11:50 | emergency_router.py 7곳 수정 완료 | ✅ |
| 11:55 | 백엔드 재시작 후 DB 테이블 미생성 발견 | ❌ |
| 12:00 | PostgreSQL 연결 확인 (port 5433) | ✅ |
| 12:05 | 뉴스 관련 테이블 5개 생성 완료 | ✅ |
| 12:10 | 백엔드 재시작 및 검증 완료 | ✅ |
| 12:15 | 프론트엔드 뉴스 페이지 정상 작동 | ✅ |

---

## 최종 상태

### ✅ 해결 완료
- [x] NewsArticle 속성명 불일치 수정 (3곳)
- [x] GroundingSearchLog 속성명 불일치 수정 (7곳)
- [x] PostgreSQL 데이터베이스 테이블 생성 (5개)
- [x] 백엔드 API 정상 작동 확인
- [x] 프론트엔드 뉴스 페이지 정상 표시

### 🎉 성공 기준 충족
- ✅ `/api/news/articles` 엔드포인트 200 OK
- ✅ `/api/emergency/status` 엔드포인트 정상
- ✅ `/api/emergency/grounding/usage` 엔드포인트 정상
- ✅ 프론트엔드 뉴스 페이지 로딩 성공
- ✅ 데이터베이스 스키마 일치

---

## 추가 개선: 뉴스 날짜 표시 기능 (2026-01-02 13:00)

### 요구사항
뉴스 목록에서 RSS 크롤링으로 받아온 뉴스의 정확한 날짜/시간을 표시하여 나중에 확인하기 편하도록 개선

### 구현 내용

#### 1. 날짜 포맷팅 함수 추가

**파일:** `frontend/src/services/newsService.ts`

**추가된 함수:**

```typescript
/**
 * 정확한 날짜/시간 포맷팅
 * 예: "2026-01-02 11:30"
 */
export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}`;
};

/**
 * 한국어 날짜 포맷팅
 * 예: "2026년 1월 2일 오전 11:30"
 */
export const formatDateTimeKorean = (dateString: string): string => {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hours = date.getHours();
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const ampm = hours < 12 ? '오전' : '오후';
  const displayHours = hours % 12 || 12;

  return `${year}년 ${month}월 ${day}일 ${ampm} ${displayHours}:${minutes}`;
};
```

#### 2. 뉴스 목록 화면 업데이트

**파일:** `frontend/src/pages/NewsAggregation.tsx`

**변경 전:**
```tsx
<span>{article.published_at ? getTimeAgo(article.published_at) : '날짜 없음'}</span>
```

**변경 후:**
```tsx
{article.published_at ? (
  <span
    title={formatDateTimeKorean(article.published_at)}
    className="cursor-help"
  >
    {getTimeAgo(article.published_at)} ({formatDateTimeKorean(article.published_at)})
  </span>
) : (
  <span>날짜 없음</span>
)}
```

#### 3. 표시 형식

**상대 시간 + 정확한 날짜 함께 표시:**
- "3시간 전 (2026년 1월 2일 오전 11:30)"
- "1일 전 (2026년 1월 1일 오후 2:15)"
- "12분 전 (2026년 1월 2일 오후 12:48)"

**툴팁 기능:**
- 날짜 텍스트에 마우스 오버 시 정확한 날짜 툴팁 표시
- `cursor-help` 클래스로 물음표 커서 표시

### 사용자 경험 개선

1. ✅ **상대 시간 유지**: "3시간 전" 같은 직관적인 표현 유지
2. ✅ **정확한 날짜 추가**: 괄호 안에 정확한 날짜/시간 표시
3. ✅ **한국어 포맷**: "2026년 1월 2일 오전 11:30" 형식으로 읽기 쉽게
4. ✅ **툴팁 지원**: 마우스 오버 시 정확한 날짜 재확인 가능

### 장점

- **정보 제공**: 뉴스가 언제 발행되었는지 정확히 알 수 있음
- **검색 편의성**: 특정 날짜/시간대의 뉴스 찾기 용이
- **히스토리 추적**: 과거 뉴스 확인 시 정확한 시점 파악 가능
- **UX 개선**: 상대 시간과 절대 시간 모두 제공하여 사용자 선택권 제공

### 수정 파일 요약

1. ✅ `frontend/src/services/newsService.ts`
   - `formatDateTime()` 함수 추가
   - `formatDateTimeKorean()` 함수 추가

2. ✅ `frontend/src/pages/NewsAggregation.tsx`
   - `formatDateTimeKorean` import 추가
   - ArticleItem 컴포넌트 날짜 표시 개선

---

**작성일:** 2026-01-02
**작성자:** AI Trading System Development Team
**관련 이슈:** Frontend News Page 500 Error + Date Display Enhancement
**우선순위:** P0 (Critical - Production Blocker) → P1 (Enhancement)
**상태:** ✅ Resolved + Enhanced
