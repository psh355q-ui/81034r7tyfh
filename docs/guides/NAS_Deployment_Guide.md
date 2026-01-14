# AI Trading System - NAS 배포 가이드

## 📋 목차
1. [현재 개발 환경](#현재-개발-환경)
2. [NAS 배포 아키텍처](#nas-배포-아키텍처)
3. [포트 구성](#포트-구성)
4. [배포 절차](#배포-절차)
5. [환경 변수 설정](#환경-변수-설정)
6. [모니터링 및 관리](#모니터링-및-관리)

---

## 현재 개발 환경

### 로컬 개발 구성
```
개발 환경 (Windows)
├── Frontend (Vite Dev Server)  → localhost:5173
├── Backend (Uvicorn)            → localhost:8000
└── Docker Services
    ├── PostgreSQL (TimescaleDB) → localhost:5432
    ├── pgvector                 → localhost:5433
    ├── Redis                    → localhost:6379
    ├── Grafana                  → localhost:3001
    ├── Prometheus               → localhost:9090
    └── Exporters                → 9100, 9121, 9187
```

### 정리 완료 사항
✅ 중복 백엔드 프로세스 제거 (PID 37740 종료)
✅ Docker 프로덕션 컨테이너 중지 (backend, frontend, nginx)
✅ 미사용 컨테이너 제거 (ai-trading-timescaledb)
✅ 포트 충돌 해결

---

## NAS 배포 아키텍처

### 프로덕션 구성 (docker-compose.prod.yml)
```
NAS 환경
├── Nginx (Reverse Proxy)        → :80, :443
│   ├── Frontend (Static Build)  → 내부
│   └── Backend API              → 내부 :8000
├── PostgreSQL (TimescaleDB)     → :5432
├── pgvector                     → :5433
├── Redis                        → :6379
├── Grafana                      → :3001
├── Prometheus                   → :9090
└── Exporters                    → 9100, 9121, 9187
```

### 컨테이너 목록
| 컨테이너 | 이미지 | 포트 | 역할 |
|---------|--------|------|------|
| ai-trading-nginx-prod | nginx:alpine | 80, 443 | 리버스 프록시, SSL |
| ai-trading-frontend-prod | ai-trading-system-frontend | - | React 앱 (정적 파일) |
| ai-trading-backend-prod | ai-trading-system-backend | - | FastAPI 백엔드 |
| ai-trading-postgres-prod | timescale/timescaledb-ha:pg16 | 5432 | 메인 DB |
| ai-trading-pgvector | ankane/pgvector:latest | 5433 | 벡터 DB |
| ai-trading-redis-prod | redis:7-alpine | 6379 | 캐시 |
| ai-trading-grafana | grafana/grafana:latest | 3001 | 모니터링 대시보드 |
| ai-trading-prometheus | prom/prometheus:latest | 9090 | 메트릭 수집 |
| ai-trading-node-exporter | prom/node-exporter:latest | 9100 | 시스템 메트릭 |
| ai-trading-redis-exporter | oliver006/redis_exporter:latest | 9121 | Redis 메트릭 |
| ai-trading-postgres-exporter | prometheuscommunity/postgres-exporter:latest | 9187 | PostgreSQL 메트릭 |

---

## 포트 구성

### 외부 노출 포트
| 포트 | 서비스 | 용도 |
|-----|--------|------|
| **80** | Nginx | HTTP (프론트엔드 + API) |
| **443** | Nginx | HTTPS (SSL/TLS) |
| **3001** | Grafana | 모니터링 대시보드 |
| **5432** | PostgreSQL | 데이터베이스 (선택적) |
| **5433** | pgvector | 벡터 DB (선택적) |
| **6379** | Redis | 캐시 (선택적) |
| **9090** | Prometheus | 메트릭 UI |

### 내부 전용 포트
- Backend: 8000 (Nginx를 통해서만 접근)
- Frontend: 80 (컨테이너 내부)
- Exporters: 9100, 9121, 9187 (Prometheus만 접근)

---

## 배포 절차

### 1. NAS 사전 준비
```bash
# Docker 및 Docker Compose 설치 확인
docker --version
docker-compose --version

# 프로젝트 디렉토리 생성
mkdir -p /volume1/ai-trading-system
cd /volume1/ai-trading-system
```

### 2. 프로젝트 파일 복사
```bash
# Git clone 또는 직접 복사
git clone <repository-url> .

# 또는 로컬에서 rsync
rsync -avz --exclude 'node_modules' --exclude '__pycache__' \
  /path/to/ai-trading-system/ nas:/volume1/ai-trading-system/
```

### 3. 환경 변수 설정
```bash
# .env 파일 생성 (아래 "환경 변수 설정" 섹션 참고)
nano .env
```

### 4. 빌드 및 실행
```bash
# 이미지 빌드
docker-compose -f docker-compose.prod.yml build

# 컨테이너 실행
docker-compose -f docker-compose.prod.yml up -d

# 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

### 5. 데이터베이스 초기화
```bash
# 데이터베이스 테이블 생성
docker exec ai-trading-backend-prod python scripts/init_database.py

# 또는 마이그레이션 실행 (Alembic 사용 시)
docker exec ai-trading-backend-prod alembic upgrade head
```

### 6. 헬스 체크
```bash
# API 헬스 체크
curl http://localhost/api/

# Grafana 접속
# http://<NAS-IP>:3001

# Prometheus 접속
# http://<NAS-IP>:9090
```

---

## 환경 변수 설정

### .env 파일 템플릿
```bash
# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_URL=postgresql+asyncpg://ai_trading_user:YOUR_SECURE_PASSWORD@postgres:5432/ai_trading
POSTGRES_USER=ai_trading_user
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD
POSTGRES_DB=ai_trading

# =============================================================================
# pgvector Configuration
# =============================================================================
PGVECTOR_URL=postgresql://ai_trading_user:YOUR_SECURE_PASSWORD@pgvector:5432/ai_trading_vector
PGVECTOR_USER=ai_trading_user
PGVECTOR_PASSWORD=YOUR_SECURE_PASSWORD
PGVECTOR_DB=ai_trading_vector

# =============================================================================
# Redis Configuration
# =============================================================================
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=

# =============================================================================
# API Keys (필요한 경우)
# =============================================================================
GEMINI_API_KEY=your_gemini_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# =============================================================================
# Frontend Configuration
# =============================================================================
FRONTEND_URLS=http://localhost,http://<NAS-IP>

# =============================================================================
# Security
# =============================================================================
SECRET_KEY=generate_a_random_secret_key_here
JWT_SECRET=another_random_secret_for_jwt

# =============================================================================
# Monitoring
# =============================================================================
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

### 보안 권장사항
1. **강력한 비밀번호 사용**
   ```bash
   # 랜덤 비밀번호 생성
   openssl rand -base64 32
   ```

2. **환경 변수 파일 권한 설정**
   ```bash
   chmod 600 .env
   ```

3. **SSL 인증서 설정**
   ```bash
   # Let's Encrypt 또는 자체 서명 인증서
   mkdir -p nginx/ssl
   # 인증서 파일 복사
   ```

---

## 모니터링 및 관리

### 로그 확인
```bash
# 전체 로그
docker-compose -f docker-compose.prod.yml logs -f

# 특정 서비스 로그
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f postgres

# 최근 100줄
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### 컨테이너 관리
```bash
# 재시작
docker-compose -f docker-compose.prod.yml restart backend

# 중지
docker-compose -f docker-compose.prod.yml stop

# 시작
docker-compose -f docker-compose.prod.yml start

# 완전 중지 및 제거
docker-compose -f docker-compose.prod.yml down

# 볼륨까지 제거 (주의!)
docker-compose -f docker-compose.prod.yml down -v
```

### 데이터베이스 백업
```bash
# PostgreSQL 백업
docker exec ai-trading-postgres-prod pg_dump -U ai_trading_user ai_trading > backup_$(date +%Y%m%d).sql

# 복원
docker exec -i ai-trading-postgres-prod psql -U ai_trading_user ai_trading < backup_20251128.sql
```

### 업데이트 절차
```bash
# 1. 최신 코드 가져오기
git pull

# 2. 이미지 재빌드
docker-compose -f docker-compose.prod.yml build

# 3. 무중단 재시작
docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend

# 4. 헬스 체크
docker-compose -f docker-compose.prod.yml ps
```

---

## Grafana 대시보드 설정

### 초기 접속
- URL: `http://<NAS-IP>:3001`
- 기본 계정: `admin` / `admin`
- 첫 로그인 시 비밀번호 변경 필요

### 데이터 소스 추가
1. Configuration → Data Sources
2. Add data source → Prometheus
3. URL: `http://prometheus:9090`
4. Save & Test

### 대시보드 import
- 시스템 메트릭: Dashboard ID `1860` (Node Exporter Full)
- PostgreSQL: Dashboard ID `9628` (PostgreSQL Database)
- Redis: Dashboard ID `763` (Redis Dashboard)

---

## 트러블슈팅

### 문제 1: 컨테이너가 시작되지 않음
```bash
# 로그 확인
docker-compose -f docker-compose.prod.yml logs backend

# 권한 문제 확인
ls -la /volume1/ai-trading-system

# 디렉토리 권한 수정
chmod -R 755 /volume1/ai-trading-system
```

### 문제 2: 데이터베이스 연결 실패
```bash
# PostgreSQL 컨테이너 상태 확인
docker exec ai-trading-postgres-prod pg_isready -U ai_trading_user

# 연결 테스트
docker exec ai-trading-backend-prod python -c "from backend.database.repository import get_sync_session; db = get_sync_session(); print('Connected'); db.close()"
```

### 문제 3: API 500 에러
```bash
# 백엔드 로그 확인
docker logs ai-trading-backend-prod --tail 100

# 데이터베이스 테이블 확인
docker exec ai-trading-postgres-prod psql -U ai_trading_user -d ai_trading -c "\dt"

# 테이블 재생성 (필요 시)
docker exec ai-trading-backend-prod python scripts/init_database.py
```

---

## 성능 최적화

### 1. PostgreSQL 튜닝
```bash
# docker-compose.prod.yml 수정
services:
  postgres:
    environment:
      - POSTGRES_SHARED_BUFFERS=256MB
      - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
      - POSTGRES_WORK_MEM=16MB
```

### 2. Redis 메모리 제한
```bash
services:
  redis:
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 3. Nginx 캐싱
```nginx
# nginx.conf
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 보안 체크리스트

- [ ] `.env` 파일 권한 설정 (600)
- [ ] 강력한 데이터베이스 비밀번호 설정
- [ ] Grafana 기본 비밀번호 변경
- [ ] SSL/TLS 인증서 설정
- [ ] 불필요한 포트 외부 노출 차단
- [ ] 정기 백업 스크립트 설정
- [ ] 로그 로테이션 설정

---

## 참고 자료

- Docker Compose: https://docs.docker.com/compose/
- TimescaleDB: https://docs.timescale.com/
- Grafana: https://grafana.com/docs/
- Prometheus: https://prometheus.io/docs/

---

**작성일**: 2025-11-28
**버전**: 1.0
**최종 업데이트**: Phase 17-3 (Trade Execution) 완료 후
