# RAG Foundation - Quick Start Guide

## 🚀 Task 1.1-1.2: pgvector 설치 및 데이터베이스 초기화

### Step 1: 디렉토리 구조 준비

로컬 프로젝트에서 다음 파일들을 복사하세요:

```bash
D:\code\ai-trading-system\
├── docker-compose.yml           # 이 파일로 교체
├── init-scripts/
│   └── 01-init-pgvector.sh     # 새로 추가
└── backend/
    └── alembic/
        └── versions/
```

### Step 2: Docker Compose 시작

```bash
# 1. 기존 컨테이너 중지 (이미 실행 중이라면)
docker compose down

# 2. 볼륨 삭제 (깨끗한 설치를 위해)
docker volume rm ai-trading-system_timescaledb-data

# 3. 새 컨테이너 시작
docker compose up -d

# 4. 로그 확인 (초기화 스크립트 실행 확인)
docker compose logs -f timescaledb

# 출력 예상:
# ✅ pgvector extension installed successfully
# ✅ TimescaleDB extension verified
# ✅ Vector store schema created successfully
# ✅ Database initialization complete!
```

### Step 3: 설치 검증

```bash
# pgvector 설치 확인
docker exec -it ai-trading-timescaledb psql -U postgres -d ai_trading -c \
  "SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'timescaledb');"

# 예상 출력:
#   extname    | extversion
# -------------+------------
#  vector      | 0.5.1
#  timescaledb | 2.13.0

# 테이블 생성 확인
docker exec -it ai-trading-timescaledb psql -U postgres -d ai_trading -c \
  "\dt"

# 예상 출력:
#  Schema |         Name          | Type  |  Owner
# --------+-----------------------+-------+----------
#  public | document_embeddings   | table | postgres
#  public | document_tags         | table | postgres
#  public | document_sync_status  | table | postgres
#  public | embedding_costs       | table | postgres
#  public | features              | table | postgres

# Hypertable 확인
docker exec -it ai-trading-timescaledb psql -U postgres -d ai_trading -c \
  "SELECT hypertable_name FROM timescaledb_information.hypertables;"

# 예상 출력:
#   hypertable_name
# ----------------------
#  document_embeddings
#  embedding_costs
#  features

# Vector 인덱스 확인
docker exec -it ai-trading-timescaledb psql -U postgres -d ai_trading -c \
  "SELECT indexname FROM pg_indexes WHERE tablename = 'document_embeddings';"

# 예상 출력:
#           indexname
# ------------------------------
#  idx_embedding_ivfflat
#  idx_doc_ticker_type
#  idx_doc_hash
#  idx_doc_date
#  idx_doc_created
```

### Step 4: 간단한 테스트

```bash
# 샘플 벡터 삽입 테스트
docker exec -it ai-trading-timescaledb psql -U postgres -d ai_trading <<EOF
INSERT INTO document_embeddings 
  (ticker, doc_type, content, content_hash, embedding, document_date)
VALUES 
  ('TEST', '10K', 'Sample document', 'test_hash_123', 
   ARRAY(SELECT random() FROM generate_series(1, 1536))::vector(1536),
   NOW());
EOF

# 벡터 검색 테스트
docker exec -it ai-trading-timescaledb psql -U postgres -d ai_trading <<EOF
SELECT 
  ticker, 
  doc_type,
  1 - (embedding <=> ARRAY(SELECT random() FROM generate_series(1, 1536))::vector(1536)) AS similarity
FROM document_embeddings
ORDER BY embedding <=> ARRAY(SELECT random() FROM generate_series(1, 1536))::vector(1536)
LIMIT 5;
EOF
```

### Step 5: 문제 해결

#### 문제 1: pgvector 설치 실패
```bash
# 로그 확인
docker compose logs timescaledb | grep -i error

# 컨테이너 재시작
docker compose restart timescaledb
```

#### 문제 2: 초기화 스크립트 미실행
```bash
# init-scripts 디렉토리 권한 확인
chmod +x init-scripts/01-init-pgvector.sh

# 볼륨 삭제 후 재시작
docker compose down
docker volume rm ai-trading-system_timescaledb-data
docker compose up -d
```

#### 문제 3: 포트 충돌
```bash
# 사용 중인 프로세스 확인
lsof -i :5432

# docker-compose.yml에서 포트 변경
ports:
  - "15432:5432"  # 호스트 포트 변경
```

---

## ✅ Task 1.1-1.2 완료 체크리스트

- [ ] Docker Compose 업데이트 완료
- [ ] init-scripts/01-init-pgvector.sh 생성
- [ ] docker compose up -d 실행
- [ ] pgvector extension 설치 확인
- [ ] 5개 테이블 생성 확인 (document_embeddings, document_tags, document_sync_status, embedding_costs, features)
- [ ] Hypertable 생성 확인 (3개)
- [ ] Vector 인덱스 생성 확인
- [ ] 샘플 데이터 삽입/검색 테스트 성공

---

## 📊 예상 시간

- Task 1.1: pgvector 설치 - **완료** ✅
- Task 1.2: 스키마 생성 - **완료** ✅
- **총 소요 시간**: 15분 (Docker 빌드 포함)

---

## 🎯 다음 단계

Task 1.3: 환경 설정 (OpenAI API 키 추가)

```bash
# backend/.env 파일 생성
cp backend/.env.example backend/.env

# .env 파일에 추가
OPENAI_API_KEY=sk-proj-your-key-here
```

---

**Created**: 2025-11-22
**Status**: Task 1.1-1.2 구현 완료
**Next**: Task 1.3 (Environment Configuration)
