# AI Trading System - 통합 데이터베이스 표준

> ⚠️ **AI 개발 도구 필독**: 이 문서는 VSCode, Antigravity 등 AI 개발 도구가 코드 작성/검토 시 **필수로 참조**해야 하는 표준입니다.
> 
> **자동 검토 규칙**:
> 1. DB 관련 코드 작성 시 이 문서의 체크리스트 필수 확인
> 2. 표준 위반 시 경고 및 수정 제안
> 3. 새 테이블 생성 시 db-schema-manager 스키마 먼저 작성
> 4. Repository 패턴 외 DB 접근 시 경고

## 📋 개요

AI Trading System의 모든 데이터베이스 저장/조회 작업을 위한 통합 표준 가이드입니다.

## 🗂️ 데이터 모델 분류

### 1. 시계열 데이터 (TimescaleDB)
**특징**: `time` 컬럼 필수, 자동 파티셔닝

#### StockPrice (주가 데이터)
```python
{
    "ticker": str,        # 종목 코드 (필수)
    "time": datetime,     # 타임스탬프 (필수, TimescaleDB 표준)
    "open": float,        # 시가
    "high": float,        # 고가
    "low": float,         # 저가
    "close": float,       # 종가
    "volume": int,        # 거래량
    "adjusted_close": float  # 조정 종가
}
```

**저장 규칙**:
- `time` 컬럼 사용 (date 아님)
- Repository: `StockRepository.save_prices()`
- 벌크 저장 시 5000개씩 배치 처리

---

### 2. 뉴스 & 분석 데이터

#### NewsArticle (뉴스 기사)
```python
{
    "title": str,                    # 제목 (필수, max 500)
    "content": str,                  # 본문 (필수)
    "url": str,                      # 원문 URL (필수, unique)
    "source": str,                   # 출처 (필수, max 100)
    "published_at": datetime,        # 발행일시 (필수)
    "tickers": List[str],           # 관련 종목 (ARRAY)
    "sentiment_score": float,        # 감성 점수 (-1 ~ 1)
    "embedding": List[float],        # 벡터 임베딩 (1536차원)
    "metadata": dict,                # 추가 정보 (JSONB)
    "is_analyzed": bool,             # 분석 완료 여부
    "created_at": datetime           # 생성일시 (자동)
}
```

**저장 규칙**:
- URL로 중복 체크
- embedding은 OpenAI text-embedding-3-small 사용
- Repository: `NewsRepository.save_article()`

#### AnalysisResult (AI 분석 결과)
```python
{
    "article_id": int,               # NewsArticle FK (필수)
    "ticker": str,                   # 종목 코드 (필수)
    "bull_case": str,                # 상승 근거
    "bear_case": str,                # 하락 근거
    "key_points": List[str],        # 핵심 포인트 (JSONB)
    "confidence": float,             # 신뢰도 (0~100)
    "ai_model": str,                 # 사용 AI 모델
    "created_at": datetime           # 생성일시 (자동)
}
```

---

### 3. 트레이딩 시그널 & 백테스트

#### TradingSignal (매매 시그널)
```python
{
    "ticker": str,                   # 종목 코드 (필수)
    "signal_type": str,              # BUY / SELL / HOLD
    "source": str,                   # 출처 (war_room, news, manual 등)
    "confidence": float,             # 신뢰도 (0~100)
    "target_price": float,           # 목표가
    "stop_loss": float,              # 손절가
    "reasoning": str,                # 근거
    "metadata": dict,                # 추가 정보 (JSONB)
    "status": str,                   # active / executed / cancelled
    "created_at": datetime,          # 생성일시 (자동)
    "executed_at": datetime          # 실행일시
}
```

**저장 규칙**:
- source 필수 (추적성)
- Repository: `SignalRepository.create_signal()`

---

### 4. 작업 추적 데이터

#### DataCollectionProgress (데이터 수집 진행 상황)
```python
{
    "task_name": str,                # 작업명 (nullable)
    "source": str,                   # 데이터 소스 (필수, max 50)
    "collection_type": str,          # news / prices 등 (필수, max 50)
    "status": str,                   # pending / running / completed / failed
    "progress_pct": float,           # 진행률 (0~100)
    "items_processed": int,          # 처리된 아이템 수
    "items_total": int,              # 전체 아이템 수
    "error_message": str,            # 에러 메시지
    "start_date": datetime,          # 수집 시작일
    "end_date": datetime,            # 수집 종료일
    "job_metadata": dict,            # 작업 메타데이터 (JSONB)
    "started_at": datetime,          # 시작 시각
    "completed_at": datetime,        # 완료 시각
    "updated_at": datetime           # 업데이트 시각 (자동)
}
```

**저장 규칙**:
- Repository: `DataCollectionRepository.create_job()`
- 진행률 업데이트: `update_progress()`

---

## 📝 통합 저장 규칙

### 1. 필수 필드
**모든 테이블**:
- `created_at`: 자동 생성 (default=datetime.now)
- `id`: Auto-increment primary key

**시계열 테이블**:
- `time`: TimescaleDB 표준 타임스탬프 컬럼

### 2. 네이밍 컨벤션
- 테이블명: `snake_case` (복수형)
- 컬럼명: `snake_case`
- 시간 컬럼: `time` (TimescaleDB), `*_at` (일반 timestamp)
- 불린: `is_*`, `has_*`
- 관계: `*_id` (FK)

### 3. 데이터 타입 표준
```python
# 문자열
short_string = String(50)      # 코드, 상태
medium_string = String(100)    # 소스, 이름
long_string = String(500)      # 제목
text = Text                    # 본문, 긴 텍스트

# 숫자
integer = Integer              # ID, 카운트
bigint = BigInteger           # 큰 숫자 (거래량)
float = Float                 # 가격, 비율
numeric = Numeric(10, 2)      # 정밀 금액

# 시간
timestamp = DateTime          # 일반 시각
timestamptz = DateTime(timezone=True)  # 시계열 데이터

# JSON
metadata = JSONB              # 유연한 메타데이터
array = ARRAY(String)         # 리스트 데이터

# 벡터
embedding = Vector(1536)      # OpenAI embedding
```

### 4. 인덱스 전략
```python
# 필수 인덱스
Index('idx_{table}_ticker', 'ticker')  # 종목 검색
Index('idx_{table}_time', 'time')      # 시계열 검색
Index('idx_{table}_created_at', 'created_at')  # 생성일 검색

# 복합 인덱스
Index('idx_{table}_ticker_time', 'ticker', 'time')  # 종목+시간 검색
```

---

## 🔧 Repository 패턴

### 기본 구조
```python
class BaseRepository:
    def __init__(self, session):
        self.session = session
    
    def save(self, obj):
        """단일 객체 저장"""
        self.session.add(obj)
        self.session.commit()
        return obj
    
    def bulk_save(self, objs, batch_size=5000):
        """벌크 저장 (배치 처리)"""
        for i in range(0, len(objs), batch_size):
            batch = objs[i:i+batch_size]
            self.session.add_all(batch)
            self.session.commit()
    
    def get_by_id(self, model_class, obj_id):
        """ID로 조회"""
        return self.session.query(model_class).filter_by(id=obj_id).first()
    
    def filter(self, model_class, **filters):
        """필터 조회"""
        return self.session.query(model_class).filter_by(**filters).all()
```

### 사용 예시
```python
# 뉴스 저장
async with get_db_session() as session:
    repo = NewsRepository(session)
    article = repo.save_article({
        "title": "AI Stock Surge",
        "content": "...",
        "url": "https://...",
        "source": "Reuters",
        "published_at": datetime.now(),
        "tickers": ["NVDA", "MSFT"]
    })

# 주가 벌크 저장
async with get_db_session() as session:
    repo = StockRepository(session)
    prices = [
        {"ticker": "AAPL", "time": datetime(...), "close": 150.0, ...},
        {"ticker": "AAPL", "time": datetime(...), "close": 151.0, ...},
        # ... 수천 개
    ]
    repo.save_prices(prices)
```

---

## 🔍 조회 패턴

### 1. 단순 조회
```python
# ID로 조회
article = repo.get_by_id(NewsArticle, 123)

# 필터 조회
articles = repo.filter(NewsArticle, source="Reuters", is_analyzed=True)
```

### 2. 시계열 조회
```python
# 기간별 주가 조회
prices = session.query(StockPrice).filter(
    StockPrice.ticker == "AAPL",
    StockPrice.time >= start_date,
    StockPrice.time <= end_date
).order_by(StockPrice.time).all()
```

### 3. 복잡한 조회 (JOIN)
```python
# 뉴스 + 분석 결과
results = session.query(NewsArticle, AnalysisResult).join(
    AnalysisResult, NewsArticle.id == AnalysisResult.article_id
).filter(
    NewsArticle.ticker == "NVDA"
).all()
```

---

## ⚡ 성능 최적화

### 1. 벌크 작업
- **항상 배치 처리**: 5000개씩
- **트랜잭션 관리**: 배치마다 commit

### 2. 인덱스 활용
- 검색 컬럼에 인덱스 추가
- EXPLAIN으로 쿼리 플랜 확인

### 3. 세션 관리
```python
# ✅ 올바른 방법 - context manager
async with get_db_session() as session:
    # 작업 수행
    pass  # 자동 commit/rollback

# ❌ 잘못된 방법 - 세션 재사용
session = get_db_session()
# ... 여러 작업
session.close()  # 수동 관리 필요
```

---

## 📊 데이터 무결성

### 1. 중복 방지
```python
# URL로 중복 체크
existing = session.query(NewsArticle).filter_by(url=url).first()
if existing:
    return existing
```

### 2. 외래 키
```python
# 관계 정의
article = relationship("NewsArticle", back_populates="analyses")

# 저장 시 FK 검증
analysis = AnalysisResult(
    article_id=123,  # 존재하는 article ID
    ticker="NVDA"
)
```

### 3. 유효성 검증
```python
# 범위 검증
assert 0 <= confidence <= 100
assert -1 <= sentiment_score <= 1

# NULL 체크
assert ticker is not None
assert time is not None
```

---

## 🚀 마이그레이션

### 새 테이블 추가
```bash
python backend/database/migrations/create_all_tables.py
```

### 컬럼 추가
```python
# 1. models.py에 컬럼 추가
# 2. Alembic 마이그레이션 생성
alembic revision --autogenerate -m "add_new_column"

# 3. 마이그레이션 실행
alembic upgrade head
```

---

## 🤖 AI 개발 도구용 자동 검증 규칙

### ✅ 새 DB 코드 작성 시 필수 체크리스트

#### Phase 1: 계획 (코드 작성 전)
- [ ] `db-schema-manager/schemas/{table}.json` 파일 존재 확인
- [ ] 없으면 먼저 스키마 JSON 작성 요청
- [ ] 스키마 파일이 표준 형식 준수 확인 (primary_key, columns, indexes)

#### Phase 2: 모델 정의
```python
# ✅ 올바른 예시
class MyTable(Base):
    __tablename__ = 'my_table'  # snake_case, 복수형
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # 필수
    time = Column(DateTime(timezone=True))  # 시계열이면 time 사용
    created_at = Column(DateTime, default=datetime.now)  # 필수
    
# ❌ 잘못된 예시
class MyTable(Base):
    __tablename__ = 'MyTable'  # camelCase 금지
    date = Column(DateTime)  # 시계열인데 date 사용 금지
    # created_at 없음 - 필수 필드 누락
```

#### Phase 3: Repository 사용
```python
# ✅ 올바른 예시
async with get_db_session() as session:
    repo = MyRepository(session)
    repo.save(data)

# ❌ 잘못된 예시 - 직접 SQL 사용
conn = psycopg2.connect(...)  # Repository 사용 필수!
cursor.execute("INSERT INTO ...")
```

### 🚫 자동 거부 패턴 (즉시 경고)

1. **직접 DB 연결**
```python
# ❌ 절대 금지
import psycopg2
conn = psycopg2.connect("postgresql://...")

# ❌ 절대 금지
import asyncpg
conn = await asyncpg.connect("postgresql://...")

# ✅ 대신 이렇게
from backend.database.connection import get_db_session
async with get_db_session() as session:
    ...
```

2. **하드코딩된 비밀번호**
```python
# ❌ 절대 금지
DB_PASSWORD = "mypassword123"
conn_str = "postgresql://user:password@localhost/db"

# ✅ 대신 이렇게
DB_PASSWORD = os.getenv('DB_PASSWORD')
```

3. **시계열 테이블에 date 사용**
```python
# ❌ 잘못됨 - TimescaleDB는 time 필수
class StockPrice(Base):
    date = Column(DateTime)  # 'time'이어야 함

# ✅ 올바름
class StockPrice(Base):
    time = Column(DateTime(timezone=True))
```

4. **Repository 없이 session.add 직접 사용** (특수 케이스 제외)
```python
# ⚠️ 경고 - Repository가 있으면 사용 필수
session.add(NewsArticle(...))  # NewsRepository 사용해야 함

# ✅ 예외 허용: 테스트 코드, 마이그레이션 스크립트
```

### 📋 코드 리뷰 체크리스트

#### 새 파일이 DB와 상호작용하는 경우

1. **스키마 검증**
   - [ ] `db-schema-manager/schemas/{table}.json` 존재?
   - [ ] 스키마 파일이 최신인가?
   - [ ] `python scripts/compare_to_db.py {table}` 통과?

2. **네이밍 검증**
   - [ ] 테이블명이 `snake_case`인가?
   - [ ] 컬럼명이 `snake_case`인가?
   - [ ] 시간 컬럼이 `*_at` 또는 `time` 형식인가?
   - [ ] 불린 컬럼이 `is_*` 또는 `has_*`인가?

3. **필수 필드 검증**
   - [ ] `id` (primary key) 있는가?
   - [ ] `created_at` 있는가?
   - [ ] 시계열이면 `time` (not `date`) 있는가?

4. **Repository 패턴 검증**
   - [ ] Repository 클래스가 존재하는가?
   - [ ] `get_db_session()` context manager 사용하는가?
   - [ ] 직접 `psycopg2.connect()` 사용하지 않는가?
   - [ ] 직접 `asyncpg.connect()` 사용하지 않는가?

5. **인덱스 검증**
   - [ ] 자주 검색하는 컬럼에 인덱스 있는가?
   - [ ] 시계열 테이블에 time 인덱스 있는가?
   - [ ] 복합 검색 패턴에 복합 인덱스 있는가?

6. **보안 검증**
   - [ ] 비밀번호가 하드코딩되지 않았는가?
   - [ ] 환경 변수로 설정 로드하는가?
   - [ ] SQL injection 취약점 없는가?

### 🎯 자동 제안 패턴

#### 발견 시 자동 제안

1. **Repository 미사용 발견**
```python
# 발견: session.add(NewsArticle(...))
# 제안: "NewsRepository.save_article() 사용을 권장합니다"
```

2. **직접 SQL 연결 발견**
```python
# 발견: psycopg2.connect(...)
# 제안: "get_db_session() context manager 사용 필수"
# 예외: migrations/, tests/ 디렉토리는 허용
```

3. **필수 필드 누락 발견**
```python
# 발견: created_at 필드 없음
# 제안: "created_at = Column(DateTime, default=datetime.now) 추가 필요"
```

4. **잘못된 컬럼명 발견**
```python
# 발견: publishedAt (camelCase)
# 제안: "published_at (snake_case)로 변경 필요"
```

### 📍 위치별 검증 규칙

#### `backend/database/models.py`
- ✅ SQLAlchemy 모델만 허용
- ✅ 모든 모델이 Base 상속
- ✅ `__tablename__` 필수
- ✅ 인덱스 정의 필수

#### `backend/database/repository.py`
- ✅ Repository 패턴만 허용
- ✅ `__init__(self, session)` 필수
- ✅ `self.session` 사용 필수
- ❌ 직접 connection 생성 금지

#### `backend/api/*.py`
- ✅ `get_db_session()` 사용 필수
- ❌ 직접 DB 연결 금지
- ✅ Repository를 통한 데이터 접근만 허용

#### `backend/data/collectors/*.py`
- ⚠️ Repository 사용 권장
- ⚠️ `asyncpg` 직접 사용 시 이유 필요

#### `backend/scripts/*.py`
- ✅ 일회성 스크립트는 직접 연결 허용
- ⚠️ 반복 실행 스크립트는 Repository 권장

#### `backend/database/migrations/*.py`
- ✅ 직접 연결 허용 (마이그레이션 목적)
- ✅ `psycopg2` 또는 `asyncpg` 사용 가능

---

## 📌 체크리스트

새 데이터 모델 추가 시:
- [ ] `db-schema-manager/schemas/{table}.json` 작성
- [ ] `python scripts/validate_schema.py {table}` 통과
- [ ] `models.py`에 SQLAlchemy 모델 정의
- [ ] 필수 필드 포함 (id, created_at)
- [ ] 인덱스 정의
- [ ] Repository 클래스 생성
- [ ] `python scripts/generate_migration.py {table}` 실행
- [ ] 마이그레이션 SQL 실행
- [ ] `python scripts/compare_to_db.py {table}` 검증
- [ ] 테스트 작성

새 DB 접근 코드 작성 시:
- [ ] Repository 패턴 사용
- [ ] `get_db_session()` context manager 사용
- [ ] 환경 변수로 설정 로드
- [ ] 에러 핸들링 추가
- [ ] 벌크 작업 시 배치 처리 (5000개)
- [ ] 트랜잭션 관리 확인
- [ ] 인덱스 활용 확인

