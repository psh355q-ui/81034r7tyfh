# AI Trading System - 인프라 및 데이터베이스 관리 가이드

**Last Updated**: 2025-12-27

---

## 📋 목차
1. [환경별 추천 인프라](#환경별-추천-인프라)
2. [데이터베이스 관리 도구](#데이터베이스-관리-도구)
3. [백업 전략](#백업-전략)
4. [모니터링 및 알림](#모니터링-및-알림)
5. [마이그레이션 관리](#마이그레이션-관리)
6. [성능 최적화](#성능-최적화)
7. [보안 관리](#보안-관리)

---

## 🏗️ 환경별 추천 인프라

### 개발 환경 (현재)

**✅ 추천: 로컬 PostgreSQL**
```
현재 구성:
- PostgreSQL 18 (로컬 설치)
- 포트: 5432
- DB: ai_trading
```

**장점**:
- ✅ 빠른 접근 속도
- ✅ 재시작 없음 (컨테이너 이슈 없음)
- ✅ 간단한 관리
- ✅ IDE 통합 용이

**관리 방법**:
```bash
# PostgreSQL 서비스 관리
# PowerShell (관리자 권한)
Get-Service postgresql*  # 상태 확인
Start-Service postgresql-x64-18  # 시작
Stop-Service postgresql-x64-18   # 중지
Restart-Service postgresql-x64-18  # 재시작

# 설정 파일 위치
C:\Program Files\PostgreSQL\18\data\postgresql.conf
C:\Program Files\PostgreSQL\18\data\pg_hba.conf
```

---

### 스테이징/테스트 환경

**✅ 추천: Docker Compose**
```yaml
version: '3.8'
services:
  postgres:
    image: timescale/timescaledb-ha:pg16
    container_name: ai-trading-postgres-staging
    environment:
      POSTGRES_DB: ai_trading_staging
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5433:5432"
    volumes:
      - postgres-staging-data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

volumes:
  postgres-staging-data:
```

**장점**:
- ✅ 운영 환경과 동일한 구성
- ✅ 격리된 환경
- ✅ 쉬운 reset/재현
- ✅ CI/CD 통합 용이

---

### 운영 환경 (Production)

**✅ 추천: 클라우드 관리형 DB**

#### Option 1: AWS RDS PostgreSQL (권장)
```
서비스: Amazon RDS for PostgreSQL
추천 스펙:
- 인스턴스: db.t3.medium (2 vCPU, 4GB RAM) → 시작
- 스토리지: 100GB SSD (Auto Scaling)
- Multi-AZ: Yes (고가용성)
- 자동 백업: 7일 보관
- 모니터링: CloudWatch 통합

장점:
✅ 자동 백업
✅ 자동 패치
✅ 고가용성 (Multi-AZ)
✅ 읽기 복제본 지원
✅ 모니터링 내장

월 비용: ~$100-200
```

#### Option 2: Supabase (빠른 시작)
```
서비스: Supabase PostgreSQL
추천 플랜: Pro ($25/month)

장점:
✅ 무료 플랜 있음
✅ 즉시 사용 가능
✅ REST API / Realtime 내장
✅ 백업/복원 UI
✅ 벡터 검색 지원 (pgvector)

단점:
⚠️ 커스터마이징 제한
⚠️ 대량 트래픽 시 비용 증가
```

#### Option 3: 자체 호스팅 (NAS/서버)
```
구성:
- Synology NAS 또는 전용 서버
- PostgreSQL 18 + TimescaleDB
- Docker 또는 직접 설치

장점:
✅ 완전한 제어
✅ 고정 비용
✅ 데이터 소유권

단점:
❌ 직접 관리 필요
❌ 고가용성 구성 복잡
❌ 백업/복원 자동화 필요

추천 도구:
- pgBackRest (백업)
- Patroni (고가용성)
- pgBouncer (연결 풀링)
```

**🎯 현재 프로젝트 추천**:
1. **개발**: 로컬 PostgreSQL 18 유지 ✅
2. **운영**: Supabase Pro → 나중에 AWS RDS로 마이그레이션

---

## 🛠️ 데이터베이스 관리 도구

### 1. GUI 관리 도구

#### ✅ DBeaver (무료, 추천)
```
다운로드: https://dbeaver.io/
특징:
- 모든 DB 지원
- SQL 에디터
- ERD 자동 생성
- 데이터 export/import
- SSH 터널링 지원

설정:
1. 연결 생성: PostgreSQL
2. Host: localhost, Port: 5432
3. Database: ai_trading
4. Username: postgres
5. Password: Qkqhdi1!
```

#### pgAdmin 4 (PostgreSQL 공식)
```
이미 설치됨 (PostgreSQL 설치 시 포함)
접속: http://localhost/pgadmin4
```

### 2. CLI 도구

#### psql (기본)
```bash
# 접속
psql -U postgres -d ai_trading

# 유용한 명령어
\dt          # 테이블 목록
\d 테이블명   # 테이블 구조
\di          # 인덱스 목록
\l           # 데이터베이스 목록
\x           # 세로 출력 모드
\timing      # 쿼리 실행 시간
```

#### ✅ pgcli (개선된 CLI, 추천)
```bash
# 설치
pip install pgcli

# 사용
pgcli -h localhost -U postgres -d ai_trading

# 특징
- 자동 완성
- 구문 강조
- 쿼리 결과 페이징
```

### 3. 스키마 관리

#### ✅ db-schema-manager (자체 구축) ✅
```bash
# 위치
backend/ai/skills/system/db-schema-manager/

# 사용
python scripts/compare_to_db.py {table}
python scripts/validate_data.py {table} '{data}'
python scripts/generate_migration.py {table}
```

#### Alembic (마이그레이션)
```bash
# 설치
pip install alembic

# 초기화
cd backend/database
alembic init migrations

# 마이그레이션 생성
alembic revision --autogenerate -m "add new column"

# 적용
alembic upgrade head

# 롤백
alembic downgrade -1
```

---

## 💾 백업 전략

### 1. 자동 백업 스크립트

```powershell
# backup_db.ps1
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "D:\backups\ai_trading"
$filename = "ai_trading_$timestamp.sql"

# 디렉토리 생성
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir
}

# 백업 실행
$env:PGPASSWORD = 'Qkqhdi1!'
pg_dump -U postgres -h localhost -p 5432 `
    -d ai_trading `
    -f "$backupDir\$filename" `
    --verbose

# 7일 이상 된 백업 삭제
Get-ChildItem $backupDir -Filter "*.sql" | 
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | 
    Remove-Item

Write-Host "✅ Backup completed: $filename"
```

### 2. 백업 스케줄 (Windows Task Scheduler)

```powershell
# 매일 오전 3시 자동 백업 설정
$action = New-ScheduledTaskAction -Execute 'PowerShell.exe' `
    -Argument '-File D:\backups\backup_db.ps1'

$trigger = New-ScheduledTaskTrigger -Daily -At 3AM

Register-ScheduledTask -Action $action -Trigger $trigger `
    -TaskName "AI Trading DB Backup" `
    -Description "Daily PostgreSQL backup"
```

### 3. 백업 유형

```bash
# 1. Full Backup (전체)
pg_dump -U postgres -d ai_trading -f backup_full.sql

# 2. Schema Only (구조만)
pg_dump -U postgres -d ai_trading --schema-only -f backup_schema.sql

# 3. Data Only (데이터만)
pg_dump -U postgres -d ai_trading --data-only -f backup_data.sql

# 4. 특정 테이블만
pg_dump -U postgres -d ai_trading -t stock_prices -f backup_prices.sql

# 5. 압축 백업
pg_dump -U postgres -d ai_trading -Fc -f backup.dump
# 복원: pg_restore -U postgres -d ai_trading backup.dump
```

### 4. 클라우드 백업 (권장)

```powershell
# AWS S3로 백업 업로드
aws s3 cp $backupFile s3://ai-trading-backups/

# Google Drive (rclone 사용)
rclone copy $backupFile gdrive:ai-trading-backups/
```

---

## 📊 모니터링 및 알림

### 1. PostgreSQL 내장 모니터링

```sql
-- 현재 연결 수
SELECT COUNT(*) FROM pg_stat_activity;

-- 데이터베이스 크기
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;

-- 테이블별 크기
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 느린 쿼리 (pg_stat_statements 필요)
SELECT 
    query,
    calls,
    total_exec_time / calls as avg_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY avg_time DESC
LIMIT 10;

-- 캐시 히트율
SELECT 
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit)  as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

### 2. 모니터링 도구

#### ✅ pgAdmin 4 Dashboard
```
- CPU/메모리 사용률
- 활성 쿼리
- 데이터베이스 통계
- 그래프 시각화
```

#### Prometheus + Grafana (운영 환경)
```yaml
# docker-compose.yml
services:
  postgres_exporter:
    image: prometheuscommunity/postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://postgres:password@postgres:5432/ai_trading?sslmode=disable"
    ports:
      - "9187:9187"

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### 3. 알림 설정

```python
# backend/monitoring/db_health_check.py
import psycopg2
import requests

def check_db_health():
    try:
        conn = psycopg2.connect(...)
        cursor = conn.cursor()
        
        # 연결 수 체크
        cursor.execute("SELECT COUNT(*) FROM pg_stat_activity;")
        connections = cursor.fetchone()[0]
        
        if connections > 80:  # 임계값
            send_alert(f"⚠️ High DB connections: {connections}")
        
        # DB 크기 체크
        cursor.execute("SELECT pg_database_size('ai_trading');")
        size_bytes = cursor.fetchone()[0]
        size_gb = size_bytes / (1024**3)
        
        if size_gb > 50:  # 50GB 초과
            send_alert(f"⚠️ DB size alert: {size_gb:.2f} GB")
        
        conn.close()
        
    except Exception as e:
        send_alert(f"❌ DB connection failed: {e}")

def send_alert(message):
    # Slack webhook
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})
```

---

## 🔄 마이그레이션 관리

### 1. Alembic 설정 (권장)

```python
# alembic/env.py
from backend.database.models import Base

target_metadata = Base.metadata

# alembic.ini
sqlalchemy.url = postgresql://postgres:password@localhost/ai_trading
```

### 2. 마이그레이션 워크플로우

```bash
# 1. 모델 변경
# backend/database/models.py 수정

# 2. 마이그레이션 생성
alembic revision --autogenerate -m "add sentiment_score column"

# 3. 검토
# migrations/versions/xxx_add_sentiment_score.py 확인

# 4. 테스트 DB에 적용
alembic upgrade head

# 5. 검증
python scripts/compare_to_db.py news_articles

# 6. 운영 적용
# (백업 후)
alembic upgrade head
```

### 3. 수동 마이그레이션

```sql
-- migrations/manual/2025_12_27_optimize_columns.sql
BEGIN;

-- 변경 사항
ALTER TABLE news_articles DROP COLUMN published_date;
ALTER TABLE news_articles DROP COLUMN crawled_at;

-- 검증
SELECT COUNT(*) FROM news_articles;

COMMIT;
```

---

## ⚡ 성능 최적화

### 1. 인덱스 최적화

```sql
-- 사용되지 않는 인덱스 찾기
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- 중복 인덱스 찾기
SELECT
    a.tablename,
    a.indexname as index1,
    b.indexname as index2
FROM pg_indexes a
JOIN pg_indexes b
    ON a.tablename = b.tablename
    AND a.indexdef = b.indexdef
    AND a.indexname < b.indexname;
```

### 2. VACUUM 및 ANALYZE

```sql
-- 자동 vacuum 설정 확인
SHOW autovacuum;

-- 수동 vacuum
VACUUM ANALYZE news_articles;

-- Full vacuum (테이블 잠금, 주의!)
VACUUM FULL news_articles;
```

### 3. 연결 풀링 (pgBouncer)

```ini
# pgbouncer.ini
[databases]
ai_trading = host=localhost port=5432 dbname=ai_trading

[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
```

---

## 🔒 보안 관리

### 1. 비밀번호 관리

```bash
# ✅ .env 사용 (현재)
DB_PASSWORD=Qkqhdi1!

# ✅ AWS Secrets Manager (운영)
aws secretsmanager get-secret-value --secret-id ai-trading/db/password

# ✅ 정기적인 비밀번호 변경
ALTER USER postgres PASSWORD 'new_password';
```

### 2. 접근 제어

```sql
-- 읽기 전용 사용자 생성
CREATE USER readonly_user PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE ai_trading TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- 특정 테이블만 접근
GRANT SELECT, INSERT, UPDATE ON news_articles TO app_user;
```

### 3. SSL/TLS 연결

```python
# SQLAlchemy connection with SSL
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"
```

---

## 📝 체크리스트

### 매일
- [ ] 백업 성공 확인
- [ ] 디스크 공간 확인
- [ ] 에러 로그 확인

### 매주
- [ ] 느린 쿼리 분석
- [ ] 인덱스 사용률 확인
- [ ] VACUUM ANALYZE 실행

### 매월
- [ ] 데이터 정리 (오래된 로그 등)
- [ ] 보안 패치 확인
- [ ] 백업 복원 테스트

---

**다음 단계**: 이 가이드를 바탕으로 어떤 부분을 먼저 구현하시겠습니까?
