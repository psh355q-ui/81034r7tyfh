# 🔌 포트 설정 가이드

## 📊 현재 포트 설정 요약

### 🎯 접속 방법

| 서비스 | 개발 모드 | Docker 프로덕션 | 상태 |
|--------|----------|----------------|------|
| **FastAPI Backend** | `localhost:8001` | Nginx를 통해서만 접근 | ✅ 개발 모드 실행 중 |
| **Nginx (프록시)** | 없음 | `localhost:80` | ⏸️ 중지됨 |
| **Frontend (React)** | `localhost:3000` | Nginx를 통해서만 접근 | ⏸️ 중지됨 |
| **Grafana** | `localhost:3001` | `localhost:3001` | ✅ 실행 중 |
| **Prometheus** | `localhost:9090` | `localhost:9090` | ✅ 실행 중 |
| **PostgreSQL** | `localhost:5432` | `localhost:5432` | ✅ 실행 중 |
| **Redis** | `localhost:6379` | `localhost:6379` | ✅ 실행 중 |

---

## 🚀 현재 실행 중인 서비스

### 개발 모드 (직접 실행)
```bash
# FastAPI Backend
uvicorn backend.api.main:app --host 0.0.0.0 --port 8001 --reload
```

**접속 URL**:
- API 랜딩: http://localhost:8001/
- Swagger UI: http://localhost:8001/docs
- Health Check: http://localhost:8001/kis/health

### Docker 컨테이너 (프로덕션 준비)

**실행 중**:
- ✅ PostgreSQL: `5432`
- ✅ Redis: `6379`
- ✅ Grafana: `3001`
- ✅ Prometheus: `9090`

**중지됨**:
- ⏸️ Backend (ai-trading-backend-prod)
- ⏸️ Frontend (ai-trading-frontend-prod)
- ⏸️ Nginx (ai-trading-nginx-prod)

---

## 🔄 Docker vs 직접 실행 비교

### Docker 프로덕션 모드
```yaml
# docker-compose.prod.yml
backend:
  - 내부 포트: 8000
  - 외부 접근: Nginx를 통해서만
  - URL: http://localhost/api/...

nginx:
  - 포트: 80, 443
  - 역할: 프록시 + 로드밸런서
  - Backend: /api/* → backend:8000
  - Frontend: /* → frontend:80
```

**접속 방법 (Docker)**:
```
http://localhost/           → Frontend (React)
http://localhost/api/docs   → Backend Swagger
http://localhost/api/kis/health → Health Check
```

### 직접 실행 모드 (현재)
```bash
# 직접 uvicorn 실행
backend:
  - 포트: 8001
  - 직접 접근: ✅ 가능
  - URL: http://localhost:8001/...
```

**접속 방법 (직접 실행)**:
```
http://localhost:8001/      → API 랜딩 페이지
http://localhost:8001/docs  → Swagger UI
http://localhost:8001/kis/health → Health Check
```

---

## 🎯 포트 충돌 주의사항

### Docker 백엔드를 시작하면?

**문제**: 현재 `uvicorn`이 `8000` 포트를 사용 중
**Docker**: `backend` 컨테이너도 내부적으로 `8000` 사용

**해결**:
1. Docker는 `8000`을 외부로 노출하지 않음 (Nginx를 통해서만)
2. 충돌 없음! 동시 실행 가능

### 동시 실행 가능 조합

✅ **가능**:
```
개발 uvicorn (8000) + Docker 인프라 (PostgreSQL, Redis)
→ 충돌 없음
```

✅ **가능**:
```
Docker 전체 (nginx:80, backend:내부8000)
→ 8000 외부 노출 안됨
```

❌ **불가능**:
```
개발 uvicorn (8000) + 다른 uvicorn (8000)
→ 포트 충돌!
```

---

## 📝 포트 변경 방법

### 개발 모드 포트 변경

**현재**: 8000
**변경하려면**:

```bash
# 포트 3000으로 변경 예시
uvicorn backend.api.main:app --host 0.0.0.0 --port 3000 --reload
```

### Docker 백엔드 포트 노출

현재는 Nginx를 통해서만 접근 가능한데, 직접 접근을 원한다면:

**docker-compose.prod.yml 수정**:
```yaml
backend:
  ports:
    - "8000:8000"  # 이 줄 추가
```

그러면:
- `localhost:8000` → Backend (직접)
- `localhost:80` → Nginx → Backend (프록시)

---

## 🔧 Docker 서비스 시작/중지

### 전체 시작
```bash
cd D:\code\ai-trading-system
docker-compose -f docker-compose.prod.yml up -d
```

### 백엔드만 시작
```bash
docker-compose -f docker-compose.prod.yml up -d backend
```

### 중지
```bash
docker-compose -f docker-compose.prod.yml down
```

### 현재 상태 확인
```bash
docker-compose -f docker-compose.prod.yml ps
```

---

## 🎯 권장 설정

### 개발 중 (현재 설정 - 권장)

```
✅ 개발 uvicorn: localhost:8000
✅ Docker PostgreSQL: localhost:5432
✅ Docker Redis: localhost:6379
✅ Docker Grafana: localhost:3001
✅ Docker Prometheus: localhost:9090
```

**장점**:
- 코드 변경 시 즉시 반영 (--reload)
- 디버깅 쉬움
- 빠른 테스트

### 프로덕션 배포 시

```
✅ Docker Backend (내부 8000)
✅ Docker Frontend (내부 80)
✅ Nginx 프록시: localhost:80
✅ Docker PostgreSQL: localhost:5432
✅ Docker Redis: localhost:6379
```

**장점**:
- 운영 환경과 동일
- 로드밸런싱
- SSL/TLS 지원
- 보안 강화

---

## 🔍 포트 확인 명령어

### Windows
```powershell
# 포트 8000 사용 확인
netstat -ano | findstr :8000

# 포트 80 사용 확인
netstat -ano | findstr :80

# Docker 컨테이너 포트 확인
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

### 현재 열린 포트
```bash
# AI Trading System 관련 포트
5432  - PostgreSQL (TimescaleDB)
5433  - pgvector (별도 DB)
6379  - Redis
8001  - FastAPI Backend (개발 모드)
9090  - Prometheus
9100  - Node Exporter
9121  - Redis Exporter
9187  - PostgreSQL Exporter
3001  - Grafana
```

---

## ⚠️ 주의사항

1. **개발 중**: `uvicorn` 직접 실행 (8000) 권장
2. **테스트**: Docker Compose로 전체 스택 실행
3. **프로덕션**: Nginx 프록시 필수
4. **포트 충돌**: 항상 `netstat`으로 확인
5. **방화벽**: 외부 접속 시 Windows Defender 설정 필요

---

**작성일**: 2025-12-03
**현재 모드**: 개발 모드 (uvicorn 직접 실행)
