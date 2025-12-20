# ELK Stack Logging Guide - AI Trading System

**작성일**: 2025-12-10
**문서 버전**: 1.0
**옵션**: Option 9 - ELK Stack 로그 중앙화

---

## 📋 목차

1. [개요](#개요)
2. [아키텍처](#아키텍처)
3. [설치 및 설정](#설치-및-설정)
4. [구조화된 로깅 사용법](#구조화된-로깅-사용법)
5. [Kibana 대시보드](#kibana-대시보드)
6. [로그 검색 및 분석](#로그-검색-및-분석)
7. [알림 설정](#알림-설정)
8. [성능 최적화](#성능-최적화)
9. [문제 해결](#문제-해결)

---

## 개요

### ELK Stack이란?

**ELK Stack**은 **Elasticsearch**, **Logstash**, **Kibana**의 약자로, 중앙화된 로그 관리 및 분석 시스템입니다.

```
Application Logs → Filebeat → Logstash → Elasticsearch → Kibana
                                                            ↓
                                                      Visualization
```

### 주요 기능

- ✅ **중앙화된 로그 수집**: 모든 서비스의 로그를 한 곳에서 관리
- ✅ **실시간 검색**: 수백만 개의 로그를 초 단위로 검색
- ✅ **구조화된 로깅**: JSON 형식으로 로그 분류 및 필터링
- ✅ **시각화**: Kibana 대시보드로 로그 트렌드 분석
- ✅ **알림**: 에러 발생 시 자동 알림
- ✅ **비용 추적**: AI API 사용량 및 비용 모니터링

### 로그 인덱스 구조

| 인덱스 | 용도 | 예시 |
|--------|------|------|
| `ai-trading-YYYY.MM.DD` | 전체 로그 | 모든 서비스 로그 |
| `ai-trading-errors-YYYY.MM.DD` | 에러 로그 | Exception, Error 레벨 |
| `ai-trading-trades-YYYY.MM.DD` | 거래 로그 | Buy/Sell 주문 |
| `ai-trading-ai-YYYY.MM.DD` | AI 요청 로그 | OpenAI API 호출, 비용 |

---

## 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Backend  │  │ Frontend │  │ Database │              │
│  │ (FastAPI)│  │ (React)  │  │(Postgres)│              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │ JSON Logs   │ Logs        │ Logs                │
└───────┼─────────────┼─────────────┼─────────────────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │       Filebeat             │ ← Docker logs collector
        │   (Log Shipper)            │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │       Logstash              │ ← Log parsing & filtering
        │  (Log Processing)           │
        │  - Parse JSON               │
        │  - Extract fields           │
        │  - Tag classification       │
        └─────────────┬───────────────┘
                      │
        ┌─────────────▼───────────────┐
        │    Elasticsearch            │ ← Storage & Search
        │   (Search Engine)           │
        │  - Index logs               │
        │  - Full-text search         │
        └─────────────┬───────────────┘
                      │
        ┌─────────────▼───────────────┐
        │       Kibana                │ ← Visualization
        │  (Dashboard & UI)           │
        │  - Dashboards               │
        │  - Alerts                   │
        └─────────────────────────────┘
```

### 로그 흐름 (Log Flow)

1. **Application**: FastAPI 앱에서 `elk_logger.info()` 호출
2. **TCP Socket**: JSON 로그를 Logstash TCP:5000으로 전송
3. **Logstash**: 로그 파싱 및 필드 추출 (ticker, price, duration 등)
4. **Elasticsearch**: 인덱스별로 저장 (일별 인덱스)
5. **Kibana**: 대시보드에서 시각화 및 검색

---

## 설치 및 설정

### 1. ELK Stack 시작

```bash
# ELK Stack 컨테이너 시작
docker-compose -f docker-compose.elk.yml up -d

# 실행 확인
docker-compose -f docker-compose.elk.yml ps
```

**예상 출력**:
```
NAME             SERVICE         STATUS
elasticsearch    elasticsearch   running (healthy)
logstash         logstash        running
kibana           kibana          running (healthy)
filebeat         filebeat        running
```

### 2. 서비스 접속 확인

| 서비스 | URL | 설명 |
|--------|-----|------|
| Elasticsearch | http://localhost:9200 | REST API |
| Kibana | http://localhost:5601 | 웹 UI |
| Logstash | localhost:5000 (TCP) | 로그 수신 |

**Elasticsearch 확인**:
```bash
curl http://localhost:9200/_cluster/health
# 예상 응답: {"status":"green",...}
```

**Kibana 확인**:
```bash
# 브라우저에서 접속
http://localhost:5601

# 초기 화면: Kibana Home
```

### 3. 인덱스 패턴 생성 (Kibana)

1. Kibana 접속: http://localhost:5601
2. **Menu → Stack Management → Index Patterns**
3. **Create index pattern** 클릭
4. 인덱스 패턴 입력: `ai-trading-*`
5. Time field 선택: `@timestamp`
6. **Create index pattern** 클릭

**추가 인덱스 패턴**:
- `ai-trading-errors-*`
- `ai-trading-trades-*`
- `ai-trading-ai-*`

### 4. 대시보드 Import

```bash
# Kibana 대시보드 Import
# Kibana → Menu → Stack Management → Saved Objects
# Import 버튼 클릭
# 파일 선택: elk/kibana/dashboards/ai-trading-dashboard.ndjson
```

---

## 구조화된 로깅 사용법

### 1. ELKLogger 초기화

```python
from backend.utils.elk_logger import get_elk_logger

# 싱글톤 인스턴스 가져오기
elk_logger = get_elk_logger(
    service_name="ai-trading-backend",
    logstash_host="localhost",
    logstash_port=5000
)
```

### 2. 기본 로깅

```python
# INFO 레벨
elk_logger.info("User logged in", user_id="user-123", ip="192.168.1.1")

# WARNING 레벨
elk_logger.warning("Slow API response", endpoint="/api/stock", duration_ms=1500)

# ERROR 레벨
elk_logger.error("Database connection failed", db_host="postgres", retry_count=3)

# CRITICAL 레벨
elk_logger.critical("System out of memory", memory_usage_gb=15.8)
```

### 3. API 요청 로깅

```python
from fastapi import FastAPI, Request
from backend.utils.elk_logger import get_elk_logger, log_api_call

app = FastAPI()
elk_logger = get_elk_logger()

# 방법 1: 데코레이터 사용 (자동 로깅)
@app.get("/stock/{ticker}")
@log_api_call(elk_logger)
async def get_stock(ticker: str, request: Request):
    return {"ticker": ticker, "price": 150.25}

# 방법 2: 수동 로깅
@app.get("/stock/{ticker}")
async def get_stock(ticker: str):
    start_time = time.time()

    # ... 비즈니스 로직 ...

    duration_ms = (time.time() - start_time) * 1000

    elk_logger.log_api_request(
        endpoint="/stock",
        method="GET",
        status_code=200,
        duration_ms=duration_ms,
        ticker=ticker,
        user_id="user-123"
    )

    return {"ticker": ticker, "price": 150.25}
```

### 4. 거래 활동 로깅

```python
elk_logger.log_trading_activity(
    action="BUY",
    ticker="AAPL",
    quantity=10,
    price=150.25,
    order_id="ORD-12345",
    strategy="momentum",
    confidence=0.85
)
```

**Elasticsearch 저장 형식**:
```json
{
  "timestamp": "2024-12-10T10:30:45.123Z",
  "level": "INFO",
  "service": "ai-trading-backend",
  "type": "trading",
  "action": "BUY",
  "ticker": "AAPL",
  "quantity": 10,
  "price": 150.25,
  "order_id": "ORD-12345",
  "strategy": "momentum",
  "confidence": 0.85
}
```

### 5. AI 요청 로깅 (비용 추적)

```python
elk_logger.log_ai_request(
    model="gpt-4",
    prompt_tokens=1500,
    completion_tokens=500,
    cost=0.105,  # USD
    duration_ms=1200,
    ticker="NVDA",
    task="stock_analysis"
)
```

**비용 계산**:
```python
# GPT-4 pricing (2024)
prompt_cost = (prompt_tokens / 1000) * 0.03
completion_cost = (completion_tokens / 1000) * 0.06
total_cost = prompt_cost + completion_cost
```

### 6. 데이터베이스 쿼리 로깅

```python
elk_logger.log_database_query(
    query="SELECT * FROM stocks WHERE ticker = 'AAPL'",
    duration_ms=12.5,
    rows_affected=1,
    ticker="AAPL"
)
```

### 7. 캐시 작업 로깅

```python
elk_logger.log_cache_operation(
    operation="GET",
    key="price:AAPL",
    hit=True,  # Cache hit
    duration_ms=0.5
)
```

### 8. 예외 로깅

```python
try:
    result = risky_operation()
except Exception as e:
    elk_logger.log_exception(
        e,
        context={
            "operation": "risky_operation",
            "ticker": "AAPL",
            "retry_count": 3
        }
    )
    raise
```

---

## Kibana 대시보드

### 1. Overview Dashboard

**URL**: http://localhost:5601/app/dashboards

**주요 패널**:
- **Log Volume**: 시간대별 로그 발생량
- **Error Rate**: 에러 발생률 (%)
- **API Response Time (p95)**: API 응답 시간 95 백분위수
- **Top Errors**: 가장 많이 발생한 에러 Top 10

### 2. Error Monitoring

**검색 쿼리**: `tags:error`

**주요 필드**:
- `timestamp`: 에러 발생 시각
- `service_name`: 에러가 발생한 서비스
- `exception_type`: 예외 타입 (ValueError, KeyError 등)
- `exception_message`: 에러 메시지
- `traceback`: 전체 스택 트레이스

**예시 쿼리**:
```
tags:error AND service_name:"ai-trading-backend" AND exception_type:"ValueError"
```

### 3. Trading Activity Dashboard

**검색 쿼리**: `tags:trading`

**주요 필드**:
- `action`: BUY, SELL
- `ticker`: 주식 티커
- `quantity`: 수량
- `price`: 가격
- `order_id`: 주문 ID

**예시 쿼리**:
```
tags:trading AND action:"BUY" AND ticker:"AAPL"
```

### 4. AI Cost Tracking

**검색 쿼리**: `type:ai_request`

**주요 메트릭**:
- **Total Cost (daily)**: 일별 총 비용
- **Cost by Model**: 모델별 비용 (GPT-4 vs GPT-3.5)
- **Token Usage**: 토큰 사용량 추이
- **Average Response Time**: AI 응답 시간

**예시 쿼리**:
```
type:ai_request AND model:"gpt-4"
```

**시각화 예시**:
```
Aggregation: Sum of cost_usd
Group by: model
Time range: Last 7 days
```

### 5. Performance Monitoring

**주요 차트**:
- **API Response Time**: 엔드포인트별 응답 시간
- **Database Query Time**: 쿼리 실행 시간 분포
- **Cache Hit Rate**: 캐시 히트율 (%)

---

## 로그 검색 및 분석

### 1. Kibana Discovery

**URL**: http://localhost:5601/app/discover

### 2. 기본 검색 문법 (KQL - Kibana Query Language)

```
# 단순 텍스트 검색
error

# 필드 검색
service_name:"ai-trading-backend"

# AND 조건
service_name:"backend" AND log_level:"ERROR"

# OR 조건
ticker:"AAPL" OR ticker:"MSFT"

# NOT 조건
NOT service_name:"frontend"

# 범위 검색
response_time_ms > 1000

# 날짜 범위
@timestamp >= "2024-12-01" AND @timestamp < "2024-12-10"

# 와일드카드
message:*exception*

# 존재 여부
ticker:*  (ticker 필드가 존재하는 로그)
```

### 3. 실전 예시 쿼리

#### 예시 1: 느린 API 조회
```
type:api_request AND response_time_ms > 1000
```

#### 예시 2: 특정 티커 관련 에러
```
tags:error AND ticker:"AAPL"
```

#### 예시 3: 최근 1시간 거래 활동
```
tags:trading AND @timestamp >= now-1h
```

#### 예시 4: GPT-4 비용이 $0.10 이상인 요청
```
type:ai_request AND model:"gpt-4" AND cost_usd >= 0.1
```

#### 예시 5: 느린 DB 쿼리 (50ms 이상)
```
type:database_query AND query_duration_ms > 50
```

### 4. Aggregation (집계)

#### 예시 1: 서비스별 에러 수
```
Search: tags:error
Aggregation: Count
Group by: service_name.keyword
```

#### 예시 2: 시간대별 거래량
```
Search: tags:trading
Aggregation: Sum of quantity
Group by: Date Histogram (@timestamp, interval: 1h)
```

#### 예시 3: 티커별 평균 가격
```
Search: tags:trading
Aggregation: Average of price
Group by: ticker.keyword
```

---

## 알림 설정

### 1. Elasticsearch Watcher (X-Pack)

**주의**: 무료 버전(Basic)에서는 Watcher 사용 불가. Alerting은 상용 버전 필요.

**대안**: Elastalert 사용

### 2. Elastalert 설정

```bash
# Elastalert 설치
pip install elastalert

# 설정 파일 생성: elk/elastalert/config.yaml
```

**elk/elastalert/config.yaml**:
```yaml
rules_folder: /etc/elastalert/rules
run_every:
  minutes: 1

buffer_time:
  minutes: 15

es_host: elasticsearch
es_port: 9200

writeback_index: elastalert_status

alert_time_limit:
  days: 2
```

**elk/elastalert/rules/error_alert.yaml**:
```yaml
name: High Error Rate Alert
type: frequency
index: ai-trading-errors-*
num_events: 10
timeframe:
  minutes: 5

filter:
- term:
    tags: "error"

alert:
- "slack"

slack_webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
slack_username_override: "ELK Alert"
slack_emoji_override: ":warning:"
```

### 3. Slack 알림 예시

```yaml
# elk/elastalert/rules/trading_alert.yaml
name: Large Trade Alert
type: any
index: ai-trading-trades-*

filter:
- range:
    quantity:
      gte: 100  # 100주 이상 거래 시 알림

alert:
- "slack"

slack_webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
slack_title: "Large Trade Executed"
slack_text: "Quantity: {quantity}, Ticker: {ticker}, Price: ${price}"
```

---

## 성능 최적화

### 1. Elasticsearch 설정

```yaml
# elasticsearch.yml
# 메모리 설정
ES_JAVA_OPTS: "-Xms512m -Xmx512m"

# 인덱스 Refresh Interval (기본 1초 → 30초)
index.refresh_interval: 30s

# Replica 비활성화 (단일 노드)
index.number_of_replicas: 0
```

### 2. 인덱스 Lifecycle Management (ILM)

```json
# 30일 이상 된 로그 자동 삭제
PUT _ilm/policy/ai-trading-policy
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_age": "1d",
            "max_size": "5gb"
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
pipeline.workers: 2  # CPU 코어 수에 맞게 조정
pipeline.batch.size: 125
pipeline.batch.delay: 50

queue.type: persisted
queue.max_bytes: 1gb
```

### 4. 디스크 사용량 모니터링

```bash
# Elasticsearch 인덱스 크기 확인
curl http://localhost:9200/_cat/indices?v

# 예상 출력:
# health index                     pri rep docs.count store.size
# green  ai-trading-2024.12.10     1   0     125000     45.2mb
# green  ai-trading-errors-2024... 1   0       1250      2.1mb
```

---

## 문제 해결

### 문제 1: Elasticsearch 시작 실패

**증상**:
```
ERROR: bootstrap checks failed
max virtual memory areas vm.max_map_count [65530] is too low
```

**해결 (Linux)**:
```bash
sudo sysctl -w vm.max_map_count=262144

# 영구 설정
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

**해결 (Windows - Docker Desktop)**:
```powershell
# WSL2 터미널에서
wsl -d docker-desktop
sysctl -w vm.max_map_count=262144
```

### 문제 2: Kibana 접속 불가

**증상**: http://localhost:5601 접속 시 "Kibana server is not ready yet"

**해결**:
```bash
# Elasticsearch 상태 확인
curl http://localhost:9200/_cluster/health

# Kibana 로그 확인
docker logs kibana

# Kibana 재시작
docker-compose -f docker-compose.elk.yml restart kibana
```

### 문제 3: 로그가 Elasticsearch에 저장되지 않음

**증상**: Kibana Discovery에서 로그가 보이지 않음

**해결**:
```bash
# 1. Logstash 로그 확인
docker logs logstash

# 2. Filebeat 상태 확인
docker logs filebeat

# 3. Elasticsearch 인덱스 확인
curl http://localhost:9200/_cat/indices?v

# 4. 수동 테스트 (Python)
python -c "
from backend.utils.elk_logger import get_elk_logger
logger = get_elk_logger()
logger.info('Test log', test=True)
"

# 5. Logstash TCP 연결 확인
telnet localhost 5000
```

### 문제 4: 디스크 공간 부족

**증상**:
```
Elasticsearch cluster_block_exception
index [ai-trading-2024.12.10] blocked by: [FORBIDDEN/12/index read-only]
```

**해결**:
```bash
# 오래된 인덱스 삭제
curl -X DELETE http://localhost:9200/ai-trading-2024.11.*

# Read-only 해제
curl -X PUT "http://localhost:9200/_all/_settings" -H 'Content-Type: application/json' -d'
{
  "index.blocks.read_only_allow_delete": null
}
'
```

### 문제 5: 검색 속도 느림

**증상**: Kibana에서 검색 시 10초 이상 소요

**해결**:
```bash
# 1. 인덱스 최적화 (Merge)
curl -X POST "http://localhost:9200/ai-trading-*/_forcemerge?max_num_segments=1"

# 2. 캐시 클리어
curl -X POST "http://localhost:9200/_cache/clear"

# 3. 검색 범위 축소 (Kibana)
# Time range: Last 7 days → Last 24 hours
```

---

## 체크리스트

### 일일 점검
- [ ] Elasticsearch 클러스터 상태: `green`
- [ ] 디스크 사용량 < 80%
- [ ] 에러 로그 확인 (Kibana → Errors Dashboard)
- [ ] AI 비용 모니터링 (일 $5 이하 목표)

### 주간 점검
- [ ] 오래된 인덱스 정리 (30일 이상)
- [ ] 느린 쿼리 분석 (query_duration_ms > 100ms)
- [ ] Logstash 파이프라인 성능 확인
- [ ] 알림 규칙 검토

### 월간 점검
- [ ] Elasticsearch 업그레이드 확인
- [ ] ILM 정책 재평가
- [ ] 대시보드 최적화
- [ ] 보안 설정 검토

---

## 참고 자료

- **Elasticsearch 공식 문서**: https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html
- **Logstash 문서**: https://www.elastic.co/guide/en/logstash/current/index.html
- **Kibana 문서**: https://www.elastic.co/guide/en/kibana/current/index.html
- **Filebeat 문서**: https://www.elastic.co/guide/en/beats/filebeat/current/index.html

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-12-10
**작성자**: AI Trading System Team
