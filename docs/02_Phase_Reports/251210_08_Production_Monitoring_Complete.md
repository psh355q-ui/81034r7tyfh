# 08. 프로덕션 모니터링 시스템 완료

**작성일**: 2025-12-06
**상태**: ✅ 완료
**이전 단계**: [07. System Integration Complete](251210_07_System_Integration_Complete.md)

---

## 📋 목차

1. [개요](#개요)
2. [구현 내용](#구현-내용)
3. [모니터링 메트릭](#모니터링-메트릭)
4. [API 엔드포인트](#api-엔드포인트)
5. [Grafana 대시보드](#grafana-대시보드)
6. [Docker 배포](#docker-배포)
7. [다음 단계](#다음-단계)

---

## 개요

### 목표

Skill Layer의 **실시간 비용 추적**, **성능 모니터링**, **Prometheus 메트릭 수집**을 위한 프로덕션급 모니터링 시스템 구축

### 완료 항목

- ✅ **Skill Metrics Collector** 생성
- ✅ **Prometheus 메트릭** 12종 구현
- ✅ **실시간 통계 API** 3개 엔드포인트
- ✅ **Grafana 대시보드** 10개 패널
- ✅ **Docker 통합** (docker-compose.prod.yml)
- ✅ **비용 알림 시스템** 준비

---

## 구현 내용

### 1. Skill Metrics Collector

**파일**: `backend/monitoring/skill_metrics_collector.py` (540줄)

#### 주요 기능

1. **실시간 비용 추적**
   - Provider별 비용 집계 (anthropic, google, openai)
   - Skill별 비용 집계
   - 시간대별 비용 추이

2. **Token 사용량 모니터링**
   - Input/Output 토큰 분리 추적
   - 토큰 절감율 계산 (baseline 30 tools 대비)
   - Provider/Model별 토큰 사용량

3. **성능 메트릭**
   - 라우팅 지연시간 (p50, p95)
   - 신호 생성 지연시간
   - 도구 로딩 시간
   - 캐시 히트/미스율

4. **에러 추적**
   - Skill별 에러율
   - 에러 타입 분류
   - 성공률 모니터링

#### Prometheus 메트릭 (12종)

```python
# Counters (6개)
- skill_invocations_total        # Skill 호출 횟수
- api_costs_usd_total             # API 비용 (USD)
- tokens_used_total               # 토큰 사용량
- skill_errors_total              # 에러 발생 횟수
- cache_hits_total                # 캐시 히트
- cache_misses_total              # 캐시 미스

# Histograms (3개)
- routing_latency_seconds         # 라우팅 지연시간
- signal_generation_latency_seconds  # 신호 생성 지연시간
- tool_loading_time_seconds       # 도구 로딩 시간

# Gauges (3개)
- tokens_saved_percentage         # 토큰 절감율
- active_skills_total             # 활성 Skill 수
```

---

### 2. 모니터링 API 엔드포인트

#### 엔드포인트 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/ai-signals/metrics/real-time` | 실시간 통계 (최근 5분) |
| GET | `/ai-signals/metrics/cost-summary` | 기간별 비용 요약 |
| GET | `/ai-signals/metrics/prometheus` | Prometheus 메트릭 export |

#### 1. 실시간 통계

```bash
GET /ai-signals/metrics/real-time
```

**Response**:
```json
{
  "success": true,
  "timestamp": "2025-12-06T00:22:06",
  "metrics": {
    "last_5_minutes": {
      "invocations": 125,
      "cost_usd": 0.45,
      "avg_latency_ms": 450,
      "error_rate": 0.02,
      "avg_tokens_saved_pct": 58.5
    },
    "total": {
      "invocations": 5230,
      "cost_usd": 15.75,
      "cost_by_provider": {
        "gemini": 4.20,
        "anthropic": 8.50,
        "openai": 3.05
      },
      "top_skills": [
        ["Intelligence.Gemini", 2100],
        ["MarketData.News", 1800],
        ["Intelligence.Claude", 750]
      ]
    }
  }
}
```

#### 2. 비용 요약

```bash
GET /ai-signals/metrics/cost-summary?period_hours=24
```

**Response**:
```json
{
  "success": true,
  "period": {
    "start": "2025-12-05T00:22:00",
    "end": "2025-12-06T00:22:00",
    "hours": 24
  },
  "summary": {
    "total_invocations": 3200,
    "total_cost_usd": 12.50,
    "total_tokens": 1250000,
    "avg_cost_per_invocation": 0.0039,
    "avg_tokens_saved_pct": 58.3,
    "estimated_monthly_cost": 375.00
  },
  "by_provider": {
    "gemini": 3.20,
    "anthropic": 6.80,
    "openai": 2.50
  },
  "by_skill": {
    "Intelligence.Gemini": 3.20,
    "Intelligence.Claude": 6.80,
    "MarketData.News": 0.00
  },
  "top_skills": {
    "most_used": [
      ["Intelligence.Gemini", 1500],
      ["MarketData.News", 1200],
      ["Intelligence.Claude", 350]
    ],
    "most_expensive": [
      ["Intelligence.Claude", 6.80],
      ["Intelligence.Gemini", 3.20],
      ["Intelligence.GPT4o", 2.50]
    ]
  }
}
```

#### 3. Prometheus 메트릭

```bash
GET /ai-signals/metrics/prometheus
```

**Response** (Prometheus 형식):
```
# HELP skill_invocations_total Total number of skill invocations
# TYPE skill_invocations_total counter
skill_invocations_total{skill_name="Intelligence.Gemini",category="intelligence",intent="news_analysis"} 1500.0

# HELP api_costs_usd_total Total API costs in USD
# TYPE api_costs_usd_total counter
api_costs_usd_total{provider="gemini",model="gemini-1.5-flash",skill_name="Intelligence.Gemini"} 3.2

# HELP tokens_saved_percentage Percentage of tokens saved by optimization
# TYPE tokens_saved_percentage gauge
tokens_saved_percentage{intent="news_analysis"} 76.7

# HELP routing_latency_seconds Routing decision latency
# TYPE routing_latency_seconds histogram
routing_latency_seconds_bucket{intent="news_analysis",le="0.05"} 120.0
routing_latency_seconds_bucket{intent="news_analysis",le="0.1"} 180.0
...
```

---

## Grafana 대시보드

**파일**: `monitoring/grafana/dashboards/skill-layer-metrics.json`

### 대시보드 패널 (10개)

1. **Skill Invocations per Minute** (타임시리즈)
   - Skill별 분당 호출 횟수
   - 실시간 사용 추이 파악

2. **API Costs per Hour by Provider** (타임시리즈, 스택)
   - Provider별 시간당 비용
   - 비용 추이 모니터링

3. **Total Cost (24h)** (게이지)
   - 24시간 총 비용
   - 임계값 10 USD (경고)

4. **Avg Token Savings %** (게이지)
   - 평균 토큰 절감율
   - 50% 미만 황색, 70% 이상 녹색

5. **Cost Distribution by Skill (24h)** (파이 차트)
   - Skill별 비용 분포
   - 가장 비싼 Skill 시각화

6. **Routing Latency by Intent** (타임시리즈)
   - Intent별 라우팅 지연시간
   - p50, p95 백분위수

7. **Token Usage per Hour** (타임시리즈, 스택)
   - Provider/Model별 시간당 토큰 사용량
   - 토큰 소비 패턴 분석

8. **Error Rate by Skill** (타임시리즈)
   - Skill별 에러율
   - 0.1 (10%) 초과 시 경고

9. **Cache Performance** (타임시리즈, 바)
   - 캐시 히트/미스 비율
   - 캐시 타입별 성능

10. **Signal Generation Latency** (히스토그램)
    - Intent별 신호 생성 시간
    - 성능 병목 지점 파악

### 대시보드 접속

```
http://localhost:3001  # Grafana
```

기본 로그인:
- Username: `admin`
- Password: `.env`의 `GRAFANA_ADMIN_PASSWORD`

---

## Docker 배포

### 이미 구성된 서비스

`docker-compose.prod.yml`에 다음 서비스가 이미 구성되어 있습니다:

1. **PostgreSQL + TimescaleDB + pgvector**
2. **Redis Cache**
3. **FastAPI Backend** (Skill Layer 포함)
4. **React Frontend**
5. **Nginx Reverse Proxy**
6. **Prometheus** (메트릭 수집)
7. **Grafana** (대시보드)
8. **Node Exporter** (시스템 메트릭)
9. **Postgres Exporter** (DB 메트릭)
10. **Redis Exporter** (캐시 메트릭)

### 배포 방법

#### 1. 환경 변수 설정

`.env` 파일 생성:

```bash
# Database
DB_USER=ai_trading_user
DB_PASSWORD=your_secure_password

# API Keys
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
NEWS_API_KEY=your_newsapi_key

# KIS Trading
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret

# Security
SECRET_KEY=your_secret_key_for_jwt
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

#### 2. Docker Compose로 시작

```bash
# 프로덕션 배포
docker-compose -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f backend

# 서비스 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

#### 3. 접속 URL

- **API Documentation**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
- **Frontend**: http://localhost (Nginx)

#### 4. Prometheus 설정 확인

`monitoring/prometheus.yml`에 Skill Metrics 수집 설정:

```yaml
scrape_configs:
  - job_name: 'ai-trading-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/ai-signals/metrics/prometheus'
    scrape_interval: 15s
```

---

## 모니터링 메트릭

### 비용 절감 효과 추적

실시간으로 다음 항목을 모니터링:

| 메트릭 | 기존 | 최적화 | 절감율 |
|--------|------|--------|--------|
| 토큰/요청 | 3,800 | 1,500 | 60.5% |
| 비용/요청 | $0.011 | $0.004 | 63.6% |
| 월간 비용 (3K requests) | $330 | $120 | 63.6% |

### 알림 설정 (Grafana)

다음 조건에서 알림 발생:

1. **비용 초과**: 일일 비용 > $20
2. **에러율 증가**: Skill 에러율 > 10%
3. **지연시간 증가**: 라우팅 p95 > 2초
4. **토큰 절감율 저하**: 평균 절감율 < 40%

---

## 시스템 아키텍처

```
┌────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                      │
└───────────────────┬────────────────────────────────────────┘
                    │
        ┌───────────┼───────────────────┐
        │           │                   │
        ▼           ▼                   ▼
┌───────────┐ ┌──────────┐   ┌─────────────────┐
│ Nginx     │ │ Backend  │   │ Prometheus      │
│ :80       │ │ :8000    │   │ :9090           │
└───────────┘ └────┬─────┘   └────────┬────────┘
                   │                  │
        ┌──────────┼──────────────────┼───────┐
        │          │                  │       │
        ▼          ▼                  ▼       ▼
┌───────────┐ ┌──────────┐   ┌──────────┐ ┌──────────┐
│ Frontend  │ │ AI       │   │ Grafana  │ │ Exporters│
│ (React)   │ │ Signals  │   │ :3001    │ │          │
└───────────┘ │ Router   │   └──────────┘ └──────────┘
              └────┬─────┘
                   │
        ┌──────────┼──────────────────┐
        │          │                  │
        ▼          ▼                  ▼
┌───────────┐ ┌──────────┐   ┌──────────────┐
│ Semantic  │ │ Skill    │   │ Metrics      │
│ Router    │ │ Registry │   │ Collector    │
└───────────┘ └──────────┘   └──────┬───────┘
                                    │
                    ┌───────────────┴────────────┐
                    │                            │
                    ▼                            ▼
            ┌──────────────┐           ┌──────────────┐
            │ 8 Skills     │           │ Prometheus   │
            │ 38 Tools     │           │ Metrics      │
            └──────────────┘           └──────────────┘
```

---

## 다음 단계

### Phase 1: 실전 배포 (우선순위 높음)

1. **NAS 환경 설정**
   ```bash
   # Docker 설치 (NAS)
   sudo apt-get update
   sudo apt-get install docker.io docker-compose

   # 프로젝트 클론
   git clone <repository>
   cd ai-trading-system

   # 환경 변수 설정
   cp .env.example .env
   nano .env  # API 키 입력

   # 배포
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **API 키 설정**
   - 실제 API 키를 `.env`에 추가
   - 보안 그룹 설정 (포트 제한)

3. **모니터링 설정**
   - Grafana 대시보드 import
   - 알림 채널 설정 (Slack, Email)

### Phase 2: 고급 기능

1. **자동 스케일링**
   - Kubernetes 배포 (선택사항)
   - 부하 기반 자동 스케일링

2. **백업 자동화**
   - 데이터베이스 일일 백업
   - 메트릭 데이터 장기 보관

3. **보안 강화**
   - SSL 인증서 (Let's Encrypt)
   - API Rate Limiting
   - 2FA 인증

---

## 참고 자료

- [07. System Integration Complete](251210_07_System_Integration_Complete.md)
- [06. Skill Layer Complete](251210_06_Skill_Layer_Complete.md)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)

---

## 핵심 성과 요약

### 모니터링 시스템

- ✅ **12종 Prometheus 메트릭** 구현
- ✅ **3개 실시간 API** 엔드포인트
- ✅ **10개 Grafana 패널** 대시보드
- ✅ **비용 추적** 완벽 구현

### 프로덕션 준비

- ✅ **Docker Compose** 배포 준비 완료
- ✅ **모니터링 스택** 통합 (Prometheus + Grafana)
- ✅ **알림 시스템** 설정 가능
- ✅ **24/7 운영** 가능한 구조

### 비용 효율화

- ✅ **실시간 비용 추적**: Provider/Skill별
- ✅ **토큰 절감율**: 평균 58.3% 모니터링
- ✅ **월간 예상 비용**: 자동 계산
- ✅ **비용 알림**: 임계값 기반

---

**문서 버전**: 1.0
**최종 수정**: 2025-12-06
**다음 단계**: NAS 환경 배포 및 실전 테스트

**프로덕션 준비 완료!** 🎉
