# 🚀 Phase 7: Production Deployment Guide

**버전**: 1.0.0  
**작성일**: 2025-11-14  
**상태**: ✅ 완료  

---

## 📋 개요

Phase 7은 AI Trading System을 프로덕션 환경에 안정적으로 배포하기 위한 모든 도구와 설정을 제공합니다.

### 핵심 구성 요소

1. **📊 Prometheus Metrics** - 시스템 메트릭 수집
2. **📈 Grafana Dashboard** - 시각화 및 모니터링
3. **🔔 Alert Manager** - 알림 라우팅
4. **❤️ Health Monitor** - 상태 체크 및 자동 복구
5. **🐳 Docker Compose** - 프로덕션 스택 구성

### 비용 분석

| 구성 요소 | 월간 비용 |
|-----------|-----------|
| Prometheus | $0 (자체 호스팅) |
| Grafana | $0 (자체 호스팅) |
| Alertmanager | $0 (자체 호스팅) |
| Health Monitor | $0 (자체 코드) |
| Docker Compose | $0 |
| **총 Phase 7** | **$0/월** |

---

## 📁 파일 구조

```
phase7_production/
├── metrics_collector.py              # Prometheus 메트릭 수집
├── alert_manager.py                  # 알림 시스템
├── health_monitor.py                 # 상태 모니터링
├── docker-compose.production.yml     # 프로덕션 스택
├── monitoring/
│   ├── prometheus.yml                # Prometheus 설정
│   ├── alert.rules.yml               # 알림 규칙
│   ├── alertmanager.yml              # 알림 라우팅
│   └── grafana/
│       └── dashboards/
│           └── trading_dashboard.json  # Grafana 대시보드
└── PRODUCTION_DEPLOYMENT_GUIDE.md    # 이 문서
```

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │ Backend │────▶│  Redis  │     │TimescaleDB│             │
│  │   API   │     │  Cache  │     │ Database │             │
│  └────┬────┘     └─────────┘     └─────────┘              │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│  │Prometheus│────▶│ Grafana │     │AlertMgr │             │
│  │ Metrics │     │Dashboard│     │  Alerts │             │
│  └─────────┘     └─────────┘     └────┬────┘              │
│                                       │                    │
│                               ┌───────┴───────┐            │
│                               ▼               ▼            │
│                           ┌─────┐        ┌─────┐          │
│                           │Slack│        │Email│          │
│                           └─────┘        └─────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 배포 단계

### 1. 사전 준비

#### 1.1 필수 요구사항

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM (권장 8GB)
- 20GB+ 디스크 공간
- 네트워크 포트: 3000, 5432, 6379, 8000, 9090, 9091, 9093

#### 1.2 환경 변수 설정

`.env` 파일 생성:

```bash
# Database
DB_PASSWORD=your_secure_password_here

# AI APIs
ANTHROPIC_API_KEY=sk-ant-xxxxx
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# Monitoring
GRAFANA_USER=admin
GRAFANA_PASSWORD=secure_grafana_password

# Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx
ALERT_EMAIL=your-email@example.com
```

### 2. 프로젝트 구조 설정

```bash
# 디렉토리 생성
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards
mkdir -p logs
mkdir -p data
mkdir -p init-db
```

### 3. Grafana 데이터소스 설정

`monitoring/grafana/provisioning/datasources/prometheus.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

`monitoring/grafana/provisioning/dashboards/default.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
```

### 4. Docker Compose 실행

```bash
# 모든 서비스 시작
docker-compose -f docker-compose.production.yml up -d

# 로그 확인
docker-compose -f docker-compose.production.yml logs -f

# 상태 확인
docker-compose -f docker-compose.production.yml ps
```

### 5. 서비스 접속

| 서비스 | URL | 기본 인증 |
|--------|-----|----------|
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Prometheus** | http://localhost:9091 | - |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Alertmanager** | http://localhost:9093 | - |

---

## 📊 모니터링 설정

### Prometheus 메트릭 확인

1. http://localhost:9091 접속
2. Status → Targets 확인
3. 모든 타겟이 "UP" 상태인지 확인

### Grafana 대시보드 설정

1. http://localhost:3000 접속
2. admin/admin 로그인 (첫 로그인 시 비밀번호 변경)
3. Dashboards → Import
4. `trading_dashboard.json` 업로드
5. 대시보드 확인

### 알림 설정

#### Slack Webhook 설정

1. Slack 앱 생성: https://api.slack.com/apps
2. Incoming Webhooks 활성화
3. Webhook URL 복사
4. `alertmanager.yml`에 URL 설정

#### Email 설정 (Gmail 예시)

1. Google 계정에서 앱 비밀번호 생성
2. `alertmanager.yml` 수정:
   ```yaml
   smtp_smarthost: 'smtp.gmail.com:587'
   smtp_auth_username: 'your-email@gmail.com'
   smtp_auth_password: 'your-app-password'
   ```

---

## ❤️ 상태 모니터링

### Health Check API

```python
from health_monitor import HealthMonitor

monitor = HealthMonitor()
monitor.register_check("Redis", check_redis_health)
monitor.register_check("TimescaleDB", check_timescaledb_health)

# 상태 확인
health = await monitor.get_system_health()
print(health.to_dict())
```

### FastAPI 통합

```python
from fastapi import FastAPI
from health_monitor import HealthMonitor

app = FastAPI()
monitor = HealthMonitor()

@app.get("/health")
async def health():
    return await monitor.get_system_health()

@app.get("/readiness")
async def readiness():
    health = await monitor.get_system_health()
    if health.status == HealthStatus.UNHEALTHY:
        raise HTTPException(status_code=503)
    return {"status": "ready"}
```

---

## 🔔 알림 규칙

### 주요 알림

| 알림 이름 | 심각도 | 조건 |
|-----------|--------|------|
| **SystemDown** | CRITICAL | 시스템 1분 이상 다운 |
| **KillSwitchActivated** | CRITICAL | Kill switch 활성화 |
| **CriticalDailyLoss** | CRITICAL | 일일 손실 > $2,000 |
| **HighExecutionSlippage** | WARNING | 슬리피지 > 10 bps |
| **LowCacheHitRate** | WARNING | 캐시 히트율 < 80% |
| **HighAICost** | WARNING | 일일 비용 > $10 |

### 알림 테스트

```bash
# Alertmanager 설정 검증
docker exec ai_trading_alertmanager amtool check-config /etc/alertmanager/alertmanager.yml

# 테스트 알림 발송
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "This is a test alert",
      "description": "Testing alerting pipeline"
    }
  }]'
```

---

## 🐳 Docker 관리

### 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f prometheus
```

### 서비스 재시작

```bash
# 특정 서비스 재시작
docker-compose restart backend

# 모든 서비스 재시작
docker-compose restart
```

### 업데이트 배포

```bash
# 이미지 재빌드
docker-compose build backend

# 무중단 배포
docker-compose up -d --no-deps backend
```

### 백업

```bash
# Redis 데이터 백업
docker exec ai_trading_redis redis-cli BGSAVE
docker cp ai_trading_redis:/data/dump.rdb ./backup/

# TimescaleDB 백업
docker exec ai_trading_timescaledb pg_dump -U trading trading_db > backup/db_backup.sql
```

---

## 🔧 문제 해결

### 일반적인 문제

#### 1. 서비스 시작 실패

```bash
# 컨테이너 상태 확인
docker-compose ps

# 실패한 컨테이너 로그
docker logs ai_trading_backend

# 재시작
docker-compose down
docker-compose up -d
```

#### 2. 메모리 부족

```bash
# Docker 메모리 사용량 확인
docker stats

# Redis 메모리 설정 조정 (docker-compose.yml)
command: redis-server --maxmemory 1gb
```

#### 3. 디스크 공간 부족

```bash
# Docker 사용량 확인
docker system df

# 사용하지 않는 이미지 정리
docker image prune -a

# 볼륨 정리 (주의!)
docker volume prune
```

#### 4. 네트워크 문제

```bash
# 네트워크 확인
docker network ls
docker network inspect ai_trading_network

# 네트워크 재생성
docker-compose down
docker network prune
docker-compose up -d
```

---

## 📈 성능 최적화

### Redis 최적화

```bash
# Redis 메모리 정책
maxmemory 2gb
maxmemory-policy allkeys-lru

# 연결 풀 설정
tcp-keepalive 300
timeout 0
```

### PostgreSQL 최적화

```sql
-- 연결 풀 설정
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
```

### Docker 리소스 제한

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
```

---

## ✅ 프로덕션 체크리스트

### 배포 전

- [ ] 모든 API 키 설정
- [ ] 환경 변수 검증
- [ ] Docker 이미지 빌드 성공
- [ ] 네트워크 포트 확인
- [ ] 디스크 공간 확인 (20GB+)
- [ ] 메모리 확인 (4GB+)

### 배포 후

- [ ] 모든 컨테이너 정상 실행
- [ ] Health check 통과
- [ ] Prometheus 메트릭 수집 확인
- [ ] Grafana 대시보드 동작
- [ ] 알림 테스트 성공
- [ ] 로그 정상 기록

### 일일 점검

- [ ] 시스템 상태 확인
- [ ] 일일 P&L 검토
- [ ] 알림 확인
- [ ] 로그 이상 여부
- [ ] 디스크/메모리 사용량
- [ ] AI 비용 모니터링

---

## 📞 지원 및 문서

### 추가 자료

- **251210_MASTER_GUIDE.md**: 전체 시스템 문서
- **251210_PROJECT_GUIDE.md**: 개발 가이드
- **Phase 1-6 문서**: 각 단계별 상세 설명

### 버전 관리

```bash
# Git 태그로 버전 관리
git tag -a v1.0.0 -m "Production Release"
git push origin v1.0.0
```

### 롤백 절차

```bash
# 이전 버전으로 롤백
git checkout v0.9.0
docker-compose down
docker-compose up -d --build
```

---

## 🎉 Phase 7 완료!

**프로젝트 전체 완료!**

```
✅ Phase 1: Feature Store              - 100% 완료
✅ Phase 2: Data Integration           - 100% 완료
✅ Phase 3: AI Trading Agent           - 100% 완료
✅ Phase 4: AI Factors & Backtest      - 100% 완료
✅ Phase 5: Strategy Ensemble          - 100% 완료
✅ Phase 6: Smart Execution            - 100% 완료
✅ Phase 7: Production Ready           - 100% 완료 🎉

전체 진행률: 7/7 Phases = 100% 완료! 🚀
```

**축하합니다! AI Trading System이 프로덕션 준비를 완료했습니다!**

---

**작성자**: AI Trading System Team  
**버전**: 1.0.0  
**최종 업데이트**: 2025-11-14