# AI Trading System - NAS 기반 인프라 구성

**Hardware**: Synology DS718+  
**Strategy**: Local Dev → NAS Production → AWS Migration

---

## 🏗️ 3단계 인프라 로드맵

```
Phase 1 (현재)        Phase 2 (1-2개월)      Phase 3 (고도화 후)
┌─────────────┐      ┌─────────────┐        ┌─────────────┐
│ 로컬 PC     │      │ NAS DS718+  │        │ AWS RDS     │
│ PostgreSQL  │ ───→ │ Docker      │  ───→  │ Multi-AZ    │
│ 18          │      │ PostgreSQL  │        │ Auto Scale  │
└─────────────┘      └─────────────┘        └─────────────┘
    개발환경              운영환경                클라우드
```

---

## 📍 Phase 1: 로컬 개발 환경 (현재)

### ✅ 현재 구성
```
PC: Windows 개발 환경
DB: PostgreSQL 18 (localhost:5432)
DB Name: ai_trading
User: postgres
```

**유지 이유**:
- ✅ 빠른 개발 속도
- ✅ 오프라인 작업 가능
- ✅ 재시작 불필요
- ✅ IDE 통합 용이

---

## 🏠 Phase 2: NAS 운영 환경 구축

### Synology DS718+ 스펙

```
CPU: Intel Celeron J3455 (4코어)
RAM: 최대 6GB (권장: 6GB로 업그레이드)
HDD: 2 Bay (RAID 1 권장)
네트워크: Gigabit Ethernet x2
```

### 1. Docker Container Station 설정

#### Step 1: Container Station 설치
```
1. DSM 패키지 센터
2. Docker → Container Station 설치
3. Container Station 실행
```

#### Step 2: PostgreSQL + TimescaleDB 컨테이너 배포

**compose.yml** (NAS에 저장)
```yaml
version: '3.8'

services:
  postgres-prod:
    image: timescale/timescaledb-ha:pg16-latest
    container_name: ai-trading-postgres
    
    environment:
      POSTGRES_DB: ai_trading
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # .env 파일에서 로드
      TIMESCALEDB_TELEMETRY: off
      
    ports:
      - "5432:5432"
    
    volumes:
      # NAS 볼륨에 데이터 저장
      - /volume1/docker/postgres/data:/var/lib/postgresql/data
      - /volume1/docker/postgres/backups:/backups
      - /volume1/docker/postgres/init:/docker-entrypoint-initdb.d
    
    restart: unless-stopped
    
    # 리소스 제한 (NAS 보호)
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          memory: 1G
    
    # 헬스체크
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # pgAdmin (선택사항 - 웹 관리)
  pgadmin:
    image: dpage/pgadmin4
    container_name: ai-trading-pgadmin
    
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@aitrading.com
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    
    ports:
      - "5050:80"
    
    volumes:
      - /volume1/docker/pgadmin:/var/lib/pgadmin
    
    restart: unless-stopped

networks:
  default:
    name: ai-trading-network
```

#### Step 3: 환경 변수 설정
```bash
# NAS SSH 접속
ssh admin@<NAS_IP>

# .env 파일 생성
cd /volume1/docker/postgres/
nano .env

# 내용
DB_PASSWORD=<강력한_비밀번호>
PGADMIN_PASSWORD=<관리자_비밀번호>
```

#### Step 4: 컨테이너 시작
```bash
cd /volume1/docker/postgres/
docker-compose up -d

# 로그 확인
docker-compose logs -f postgres-prod
```

### 2. NAS 네트워크 설정

#### 고정 IP 설정 (권장)
```
DSM → 제어판 → 네트워크 → 네트워크 인터페이스
→ LAN → 편집 → 수동 설정

예시:
IP: 192.168.1.100
서브넷: 255.255.255.0
게이트웨이: 192.168.1.1
DNS: 8.8.8.8, 8.8.4.4
```

#### 포트 포워딩 (외부 접속 시)
```
라우터 설정:
외부 포트: 5433 → NAS IP:5432 (PostgreSQL)
외부 포트: 5050 → NAS IP:5050 (pgAdmin)

보안 권장:
- VPN 사용 (DSM VPN Server)
- 또는 Tailscale/ZeroTier로 secure tunnel
```

### 3. 자동 백업 설정 (NAS)

#### Task Scheduler 백업 스크립트
```bash
# /volume1/docker/postgres/scripts/backup.sh

#!/bin/bash

BACKUP_DIR="/volume1/backups/ai_trading"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# PostgreSQL 백업
docker exec ai-trading-postgres pg_dump \
    -U postgres -d ai_trading \
    -F c -f /backups/ai_trading_$TIMESTAMP.dump

# 압축
gzip /volume1/docker/postgres/backups/ai_trading_$TIMESTAMP.dump

# 오래된 백업 삭제 (30일 이상)
find $BACKUP_DIR -name "*.dump.gz" -mtime +$RETENTION_DAYS -delete

# 로그
echo "$(date): Backup completed - ai_trading_$TIMESTAMP.dump.gz" >> /volume1/logs/backup.log

# Synology Drive/Cloud Sync로 클라우드 백업 (선택)
# /volume1/backups는 Google Drive/OneDrive와 자동 동기화 설정
```

#### DSM Task Scheduler 설정
```
제어판 → 작업 스케줄러 → 생성 → Scheduled Task → User-defined script

태스크 이름: AI Trading DB Backup
사용자: root
스케줄: 매일 03:00
스크립트: bash /volume1/docker/postgres/scripts/backup.sh
```

### 4. 모니터링 설정

#### Prometheus + Grafana (선택사항)
```yaml
# docker-compose.monitoring.yml
services:
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://postgres:${DB_PASSWORD}@postgres-prod:5432/ai_trading?sslmode=disable"
    ports:
      - "9187:9187"

  prometheus:
    image: prom/prometheus
    volumes:
      - /volume1/docker/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - /volume1/docker/monitoring/data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=90d'

  grafana:
    image: grafana/grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - /volume1/docker/monitoring/grafana:/var/lib/grafana
    ports:
      - "3000:3000"
```

#### NAS 리소스 모니터링
```
DSM → 리소스 모니터
- CPU 사용률
- 메모리 사용률
- 네트워크 트래픽
- 디스크 I/O
```

---

## 🔄 로컬 ↔ NAS 연결

### 개발 환경에서 NAS DB 접속

```python
# .env (로컬)
# 개발 DB
DB_HOST_DEV=localhost
DB_PORT_DEV=5432

# NAS 운영 DB
DB_HOST_PROD=192.168.1.100  # NAS IP
DB_PORT_PROD=5432

# 환경 선택
ENVIRONMENT=development  # 또는 production
```

```python
# backend/database/connection.py
import os

ENV = os.getenv('ENVIRONMENT', 'development')

if ENV == 'production':
    DB_HOST = os.getenv('DB_HOST_PROD')
    DB_PORT = os.getenv('DB_PORT_PROD')
else:
    DB_HOST = os.getenv('DB_HOST_DEV')
    DB_PORT = os.getenv('DB_PORT_DEV')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

### 로컬 → NAS 배포 스크립트

```powershell
# deploy_to_nas.ps1

# 1. 로컬에서 최신 스키마 SQL 생성
python backend/ai/skills/system/db-schema-manager/scripts/generate_migration.py --all

# 2. NAS에 파일 전송 (SMB)
Copy-Item -Path ".\migrations\*.sql" -Destination "\\192.168.1.100\docker\postgres\migrations\"

# 3. NAS SSH 접속하여 마이그레이션 실행
ssh admin@192.168.1.100 "
    cd /volume1/docker/postgres/migrations
    docker exec -i ai-trading-postgres psql -U postgres -d ai_trading -f latest_migration.sql
"

# 4. 검증
python backend/ai/skills/system/db-schema-manager/scripts/compare_to_db.py --host 192.168.1.100 stock_prices
```

---

## 📊 Phase 3: AWS 마이그레이션 (향후)

### 언제 이동?
- ✅ 데이터베이스 크기 > 100GB
- ✅ 동시 사용자 > 50명
- ✅ 24/7 고가용성 필요
- ✅ 글로벌 접속 필요

### 마이그레이션 절차

```bash
# 1. NAS에서 최종 백업
docker exec ai-trading-postgres pg_dump -U postgres -d ai_trading -F c -f /backups/final_backup.dump

# 2. AWS RDS PostgreSQL 생성
# AWS Console에서 RDS 인스턴스 생성
# - PostgreSQL 16
# - db.t3.medium
# - Multi-AZ
# - Auto Scaling

# 3. 백업 복원
pg_restore -h <rds-endpoint>.rds.amazonaws.com \
    -U postgres -d ai_trading \
    final_backup.dump

# 4. 애플리케이션 DNS 업데이트
# .env: DB_HOST=<rds-endpoint>.rds.amazonaws.com

# 5. 검증 후 NAS 서비스 중지
```

---

## ✅ 실행 체크리스트

### Phase 1: 로컬 환경 (완료)
- [x] PostgreSQL 18 설치
- [x] ai_trading DB 생성
- [ ] 자동 백업 스크립트 (로컬)

### Phase 2: NAS 구축 (다음 단계)
- [ ] NAS RAM 6GB로 업그레이드 (권장)
- [ ] Container Station 설치
- [ ] PostgreSQL + TimescaleDB 컨테이너 배포
- [ ] 고정 IP 설정
- [ ] 자동 백업 Task 설정
- [ ] pgAdmin 웹 접속 테스트
- [ ] 로컬에서 NAS DB 접속 테스트

### Phase 3: 모니터링 (선택)
- [ ] Grafana 대시보드 구축
- [ ] Slack 알림 연동
- [ ] 디스크 공간 경고 설정

### Phase 4: AWS 준비 (미래)
- [ ] AWS 계정 생성
- [ ] RDS 비용 분석
- [ ] 마이그레이션 계획 수립

---

## 💰 비용 분석

| 항목 | 비용 | 비고 |
|------|------|------|
| **NAS DS718+ (보유)** | $0 | 기존 장비 활용 |
| RAM 업그레이드 (4GB→6GB) | ~$30 | 일회성 |
| HDD (RAID 1용) | ~$200 | 2TB x 2개 |
| 전기세 | ~$5/월 | 24/7 가동 |
| **합계 (초기)** | **~$230** | |
| **합계 (월간)** | **~$5** | |
| | | |
| **AWS RDS (비교)** | $100-200/월 | 나중에 필요시 |

**결론**: NAS 활용이 매우 경제적 ✅

---

**다음 단계**: NAS Container Station 설정부터 시작하시겠습니까?
