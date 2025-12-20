# ELK Stack 로그 중앙화 가이드

**Last Updated**: 2025-12-14
**Status**: Option 9 완료
**Related**: [Production Deployment Guide](251210_Production_Deployment_Guide.md)

---

## 📋 목차

1. [개요](#개요)
2. [아키텍처](#아키텍처)
3. [설치 및 실행](#설치-및-실행)
4. [로그 구조](#로그-구조)
5. [Kibana 대시보드 사용법](#kibana-대시보드-사용법)
6. [문제 해결](#문제-해결)
7. [성능 최적화](#성능-최적화)

---

## 개요

ELK Stack (Elasticsearch + Logstash + Kibana + Filebeat)은 AI Trading System의 모든 로그를 중앙화하여 실시간으로 검색, 분석, 시각화할 수 있게 해줍니다.

### 주요 기능

✅ **중앙화된 로그 수집**: 모든 서비스의 로그를 한 곳에서 관리
✅ **실시간 검색**: Elasticsearch를 통한 빠른 로그 검색
✅ **시각화 대시보드**: Kibana를 통한 로그 분석 및 시각화
✅ **에러 추적**: 에러 로그 자동 분류 및 알림
✅ **성능 모니터링**: API 응답 시간, DB 쿼리 성능 추적
✅ **비용 추적**: AI API 호출 비용 자동 집계

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Trading System                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Backend (FastAPI)                                           │
│  └─> JSON Logs ──────────────┐                              │
│                                │                              │
│  Frontend (React)              │                              │
│  └─> Browser Logs ────────────┤                              │
│                                │                              │
│  PostgreSQL                    │                              │
│  └─> Query Logs ───────────────┤                              │
│                                │                              │
│  Redis                         │                              │
│  └─> Cache Logs ───────────────┤                              │
│                                │                              │
│                                ▼                              │
│                          ┌──────────┐                         │
│                          │ Filebeat │ (Log Shipper)          │
│                          └─────┬────┘                         │
│                                │                              │
│                                ▼                              │
│                          ┌──────────┐                         │
│                          │ Logstash │ (Log Processing)       │
│                          └─────┬────┘                         │
│                                │                              │
│                                ▼                              │
│                       ┌────────────────┐                      │
│                       │ Elasticsearch  │ (Log Storage)       │
│                       └────────┬───────┘                      │
│                                │                              │
│                                ▼                              │
│                          ┌──────────┐                         │
│                          │  Kibana  │ (Visualization)        │
│                          └──────────┘                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 컴포넌트 역할

| 컴포넌트 | 역할 | 포트 |
|---------|-----|------|
| **Filebeat** | Docker 컨테이너 로그 수집 | - |
| **Logstash** | 로그 파싱, 변환, 라우팅 | 5044, 9600 |
| **Elasticsearch** | 로그 저장 및 검색 엔진 | 9200, 9300 |
| **Kibana** | 로그 시각화 대시보드 | 5601 |

---

## 설치 및 실행

### 1. ELK Stack 시작

```bash
# 전체 스택 시작 (기존 서비스 포함)
docker-compose up -d

# ELK 서비스만 시작
docker-compose up -d elasticsearch logstash kibana filebeat

# 로그 확인
docker-compose logs -f elasticsearch
docker-compose logs -f logstash
```

### 2. 서비스 상태 확인

```bash
# Elasticsearch 상태
curl http://localhost:9200/_cluster/health?pretty

# Logstash 상태
curl http://localhost:9600/_node/stats/pipelines?pretty

# Kibana 접속
# 브라우저에서 http://localhost:5601
```

### 3. 초기 설정

Kibana에 처음 접속하면:

1. **Index Pattern 생성**
   - Management > Stack Management > Index Patterns
   - Pattern: `ai-trading-*`
   - Time field: `@timestamp`
   - Create

2. **대시보드 Import**
   ```bash
   # 대시보드 자동 로드
   curl -X POST "localhost:5601/api/saved_objects/_import" \
     -H "kbn-xsrf: true" \
     --form file=@elk/kibana/dashboards/ai-trading-dashboard.ndjson
   ```

---

## 로그 구조

### JSON 로그 형식

모든 로그는 다음과 같은 JSON 구조로 저장됩니다:

```json
{
  "timestamp": "2025-12-14T10:30:45.123Z",
  "level": "INFO",
  "logger": "backend.api.trading_router",
  "message": "Order executed successfully",
  "service": "ai-trading-backend",
  "environment": "production",

  // Trading-specific fields
  "type": "trading_action",
  "action": "buy",
  "ticker": "NVDA",
  "quantity": 10,
  "price": 850.50,
  "order_id": "KIS-20251214-001",

  // Source information
  "source": {
    "file": "/app/backend/api/trading_router.py",
    "line": 142,
    "function": "execute_order"
  }
}
```

### 로그 타입별 인덱스

Logstash는 로그를 다음과 같이 분류하여 저장합니다:

| 인덱스 패턴 | 용도 | 예시 |
|-----------|------|------|
| `ai-trading-YYYY.MM.dd` | 일반 로그 | 모든 시스템 로그 |
| `ai-trading-errors-YYYY.MM.dd` | 에러 로그 | 예외, 에러, 크리티컬 |
| `ai-trading-trades-YYYY.MM.dd` | 거래 로그 | 주문, 체결, 포지션 |
| `ai-trading-ai-YYYY.MM.dd` | AI 로그 | Claude, Gemini, OpenAI 호출 |

---

## Kibana 대시보드 사용법

### 주요 대시보드

#### 1. **Overview Dashboard** (`ai-trading-overview`)

전체 시스템 모니터링 대시보드

- 실시간 로그 스트림
- 에러율 추이
- API 응답 시간 (p95)
- 서비스별 로그 분포

**접속**: Kibana > Dashboard > "AI Trading - Overview Dashboard"

#### 2. **Error Logs Dashboard** (`ai-trading-errors`)

에러 및 예외 추적

- 최근 에러 로그 (시간순)
- 에러 타입별 분류
- 서비스별 에러율
- Exception Traceback

**검색 예시**:
```
tags:error AND service_name:"backend"
```

#### 3. **Trading Activity Dashboard** (`ai-trading-trades`)

거래 활동 모니터링

- 실시간 주문 체결 내역
- 종목별 거래량
- 주문 성공/실패율
- 평균 체결 가격

**검색 예시**:
```
tags:trading AND ticker:"NVDA"
```

#### 4. **AI Cost Tracking**

AI API 비용 추적

- 일별/주별/월별 비용 추이
- 모델별 비용 분석 (Claude, Gemini, OpenAI)
- 토큰 사용량 추적
- 비용 예측

**검색 예시**:
```
type:ai_request AND model:"claude-3-opus"
```

### 유용한 검색 쿼리 (KQL)

```bash
# 특정 시간대 에러 검색
level:ERROR AND @timestamp >= now-1h

# 특정 종목 거래 내역
ticker:"AAPL" AND tags:trading

# 느린 API 응답 (500ms 이상)
response_time_ms > 500

# Claude API 호출
type:ai_request AND model:*claude*

# 특정 사용자 활동
user_id:"12345"

# DB 느린 쿼리 (1초 이상)
query_duration_ms > 1000 AND tags:database
```

---

## 문제 해결

### 1. Elasticsearch가 시작되지 않음

**증상**: `max virtual memory areas vm.max_map_count [65530] is too low`

**해결 (Linux)**:
```bash
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

**해결 (Windows - WSL2)**:
```powershell
# PowerShell (관리자 권한)
wsl -d docker-desktop sysctl -w vm.max_map_count=262144
```

### 2. Logstash 파이프라인 오류

**로그 확인**:
```bash
docker logs ai-trading-logstash
```

**설정 검증**:
```bash
docker exec ai-trading-logstash \
  /usr/share/logstash/bin/logstash \
  --config.test_and_exit \
  -f /usr/share/logstash/pipeline/logstash.conf
```

### 3. Filebeat가 로그를 수집하지 않음

**권한 확인**:
```bash
# Filebeat는 root 권한 필요
docker-compose logs filebeat
```

**Docker 소켓 권한**:
```bash
# docker-compose.yml에서 확인
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

### 4. Kibana 대시보드가 보이지 않음

**Index Pattern 확인**:
```bash
curl http://localhost:9200/_cat/indices?v
```

**수동 Import**:
```bash
# Kibana > Management > Saved Objects > Import
# elk/kibana/dashboards/ai-trading-dashboard.ndjson 업로드
```

---

## 성능 최적화

### 1. Elasticsearch 메모리 설정

기본 설정: 512MB (소규모 시스템)

**프로덕션 권장**:
```yaml
# docker-compose.yml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # 1GB 할당
```

### 2. 로그 보존 기간 설정

**ILM (Index Lifecycle Management)** 사용:

```bash
# 30일 이후 로그 자동 삭제
PUT _ilm/policy/ai-trading-log-policy
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_age": "1d",
            "max_size": "50GB"
          }
        }
      },
      "delete": {
        "min_age": "30d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

### 3. Logstash 성능 튜닝

```yaml
# elk/logstash/config/logstash.yml
pipeline.workers: 4        # CPU 코어 수에 맞게 조정
pipeline.batch.size: 250   # 배치 크기 증가
pipeline.batch.delay: 50   # 배치 지연 시간 (ms)

queue.type: persisted      # 재시작 시 로그 유실 방지
queue.max_bytes: 2gb       # 큐 크기
```

### 4. 디스크 공간 모니터링

```bash
# Elasticsearch 디스크 사용량 확인
curl http://localhost:9200/_cat/allocation?v

# 오래된 인덱스 삭제
curl -X DELETE http://localhost:9200/ai-trading-2025.11.*
```

---

## 모니터링 메트릭

### Elasticsearch

```bash
# 클러스터 상태
curl http://localhost:9200/_cluster/health?pretty

# 인덱스 통계
curl http://localhost:9200/_cat/indices?v&s=docs.count:desc

# 노드 통계
curl http://localhost:9200/_nodes/stats?pretty
```

### Logstash

```bash
# 파이프라인 통계
curl http://localhost:9600/_node/stats/pipelines?pretty

# 처리량 확인
curl http://localhost:9600/_node/stats/events?pretty
```

---

## 비용 및 리소스

### 리소스 사용량 (기본 설정)

| 컴포넌트 | CPU | 메모리 | 디스크 (일 기준) |
|---------|-----|--------|----------------|
| Elasticsearch | 0.5-1 core | 512MB-1GB | ~500MB/day |
| Logstash | 0.2-0.5 core | 256MB-512MB | - |
| Kibana | 0.1-0.3 core | 256MB-512MB | - |
| Filebeat | 0.05-0.1 core | 50MB-100MB | - |
| **합계** | **~1-2 cores** | **~1-2GB** | **~15GB/month** |

### 로그 저장 비용 예측

```
일일 로그량: 500MB
월간 로그량: 15GB
디스크 비용 (NAS): ~$0.50/month (SSD 기준)
```

---

## 다음 단계

ELK Stack이 설치되면:

1. ✅ **Grafana 연동**: Elasticsearch를 Grafana 데이터소스로 추가
2. ✅ **Alert 설정**: Kibana Alerting으로 에러 알림 자동화
3. ✅ **ML 기능**: Elasticsearch ML로 이상 탐지
4. ✅ **APM 추가**: Elastic APM으로 애플리케이션 성능 추적

---

## 참고 자료

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash Documentation](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Filebeat Documentation](https://www.elastic.co/guide/en/beats/filebeat/current/index.html)

---

**Last Updated**: 2025-12-14
**Maintained by**: AI Trading System Team
