# Docker PostgreSQL 컨테이너 재생성 스크립트

## 현재 컨테이너 백업 및 제거

```bash
# 1. 데이터 백업 (중요!)
docker exec -e PGPASSWORD=Qkqhdi1! ai-trading-postgres-prod \
  pg_dump -U ai_trading_user -d ai_trading > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 현재 컨테이너 중지 및 제거
docker stop ai-trading-postgres-prod
docker rm ai-trading-postgres-prod

# 3. 볼륨 제거 (완전히 새로 시작)
docker volume rm ai-trading-system_postgres-prod-data
```

## 새 컨테이너 생성

```bash
# timescale/timescaledb-ha:pg16 이미지로 새 컨테이너 생성
docker run -d \
  --name ai-trading-postgres-prod \
  --network ai-trading-net \
  -p 5432:5432 \
  -e POSTGRES_DB=ai_trading \
  -e POSTGRES_USER=ai_trading_user \
  -e POSTGRES_PASSWORD=Qkqhdi1! \
  -e TZ=Asia/Seoul \
  -v postgres-prod-data:/var/lib/postgresql/data \
  timescale/timescaledb-ha:pg16
```

## Extensions 설치

```bash
# 컨테이너가 준비될 때까지 대기 (약 10초)
timeout /t 10

# pgvector extension 설치
docker exec -e PGPASSWORD=Qkqhdi1! ai-trading-postgres-prod \
  psql -U ai_trading_user -d ai_trading \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"

# timescaledb는 이미 포함되어 있음
docker exec -e PGPASSWORD=Qkqhdi1! ai-trading-postgres-prod \
  psql -U ai_trading_user -d ai_trading \
  -c "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'timescaledb');"
```

## 테이블 생성

```bash
# data_collection_progress 테이블 생성
docker cp backend\database\migrations\create_data_collection_progress.sql ai-trading-postgres-prod:/tmp/
docker exec -e PGPASSWORD=Qkqhdi1! ai-trading-postgres-prod \
  psql -U ai_trading_user -d ai_trading \
  -f /tmp/create_data_collection_progress.sql
```

## 다른 테이블 생성 (필요 시)

```bash
# 전체 스키마 생성 (SQLAlchemy 모델 기반)
# backend/database/__init__.py에서 create_all() 실행
python -c "from backend.database import engine; from backend.database.models import Base; Base.metadata.create_all(engine)"
```

## 검증

```bash
# 테이블 목록 확인
docker exec -e PGPASSWORD=Qkqhdi1! ai-trading-postgres-prod \
  psql -U ai_trading_user -d ai_trading -c "\dt"

# Extensions 확인
docker exec -e PGPASSWORD=Qkqhdi1! ai-trading-postgres-prod \
  psql -U ai_trading_user -d ai_trading \
  -c "SELECT extname FROM pg_extension;"
```

## PowerShell 원라이너 (전체 재생성)

```powershell
# 주의: 모든 데이터가 삭제됩니다!
docker stop ai-trading-postgres-prod; docker rm ai-trading-postgres-prod; docker volume rm postgres-prod-data; docker run -d --name ai-trading-postgres-prod --network ai-trading-net -p 5432:5432 -e POSTGRES_DB=ai_trading -e POSTGRES_USER=ai_trading_user -e POSTGRES_PASSWORD=Qkqhdi1! -e TZ=Asia/Seoul -v postgres-prod-data:/var/lib/postgresql/data timescale/timescaledb-ha:pg16; Start-Sleep -Seconds 10; docker exec -e PGPASSWORD=Qkqhdi1! ai-trading-postgres-prod psql -U ai_trading_user -d ai_trading -c "CREATE EXTENSION IF NOT EXISTS vector;"; docker cp backend\database\migrations\create_data_collection_progress.sql ai-trading-postgres-prod:/tmp/; docker exec -e PGPASSWORD=Qkqhdi1! ai-trading-postgres-prod psql -U ai_trading_user -d ai_trading -f /tmp/create_data_collection_progress.sql
```
