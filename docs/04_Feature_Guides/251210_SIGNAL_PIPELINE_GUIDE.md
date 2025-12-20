# 실시간 신호 생성 파이프라인 가이드

**작성일**: 2025-12-03
**상태**: ✅ 완료 - 테스트 준비

---

## 📋 목차

1. [개요](#개요)
2. [시스템 구조](#시스템-구조)
3. [사용 방법](#사용-방법)
4. [API 엔드포인트](#api-엔드포인트)
5. [테스트 가이드](#테스트-가이드)
6. [트러블슈팅](#트러블슈팅)

---

## 개요

### 기능

실시간으로 뉴스를 수집하고 AI 분석을 통해 트레이딩 신호를 자동 생성하는 파이프라인입니다.

### 프로세스 흐름

```
뉴스 크롤링 → AI 분석 (Gemini) → 신호 생성 → WebSocket 브로드캐스트 → 프론트엔드 표시
```

### 주요 특징

- ✅ **자동화**: 30분마다 자동으로 신호 생성 (설정 가능)
- ✅ **실시간**: WebSocket으로 즉시 프론트엔드에 전송
- ✅ **중복 제거**: 같은 티커의 신호가 30분 내 중복되면 필터링
- ✅ **품질 관리**: 낮은 신뢰도(<0.6) 신호 자동 필터링
- ✅ **통계 추적**: 신호 생성 통계 실시간 조회 가능

---

## 시스템 구조

### 핵심 컴포넌트

#### 1. SignalPipeline (`backend/services/signal_pipeline.py`)

**역할**: 뉴스 → AI 분석 → 신호 생성 파이프라인 통합

**주요 메서드**:
- `process_latest_news()`: 최신 뉴스 처리 및 신호 생성
- `get_statistics()`: 파이프라인 통계 조회
- `get_recent_signals()`: 최근 생성된 신호 조회

**프로세스**:
1. 미분석 뉴스 조회 (최근 24시간)
2. Gemini API로 AI 분석 실행
3. `NewsSignalGenerator`로 신호 생성
4. 중복 제거 및 품질 필터링
5. 신호 히스토리에 저장

#### 2. NewsSignalGenerator (`backend/signals/news_signal_generator.py`)

**역할**: 뉴스 분석 결과를 트레이딩 신호로 변환

**신호 생성 로직**:
- **Action 결정**: 감정 점수 기반 (BUY/SELL/HOLD)
- **Position Size**: 영향도 × 리스크 조정
- **Confidence**: 감정 신뢰도 + 영향도 + 리스크 역수
- **Execution Type**: 긴급도에 따라 MARKET/LIMIT

#### 3. SignalScheduler (`backend/services/signal_pipeline.py`)

**역할**: 주기적 자동 신호 생성

**기능**:
- 설정된 간격(기본 30분)마다 파이프라인 실행
- 생성된 신호를 WebSocket으로 자동 브로드캐스트
- 시작/중지 제어 가능

#### 4. WebSocket Broadcast (`backend/main.py`)

**역할**: 실시간 신호 전송

**메시지 형식**:
```json
{
  "type": "signal",
  "data": {
    "ticker": "NVDA",
    "action": "BUY",
    "position_size": 0.075,
    "confidence": 0.82,
    "execution_type": "MARKET",
    "reason": "Positive news sentiment (+0.65) with high market impact (80%)",
    "urgency": "HIGH",
    "created_at": "2025-12-03T15:30:00",
    "source_article_id": 123,
    "news_title": "NVIDIA announces breakthrough AI chip..."
  }
}
```

---

## 사용 방법

### 옵션 1: 수동 신호 생성

즉시 신호를 생성하고 싶을 때 사용합니다.

**API 호출**:
```bash
curl -X POST http://localhost:8002/api/signals/generate
```

**응답**:
```json
{
  "success": true,
  "signals_count": 3,
  "message": "Generated 3 signals"
}
```

**프로세스**:
1. 미분석 뉴스 최대 10개 조회
2. AI 분석 실행
3. 신호 생성 및 필터링
4. WebSocket으로 브로드캐스트

### 옵션 2: 자동 스케줄러 사용 (권장)

주기적으로 자동 실행하고 싶을 때 사용합니다.

**1. 스케줄러 시작**:
```bash
# 30분 간격 (기본값)
curl -X POST http://localhost:8002/api/signals/scheduler/start

# 10분 간격으로 시작
curl -X POST "http://localhost:8002/api/signals/scheduler/start?interval_minutes=10"
```

**응답**:
```json
{
  "success": true,
  "message": "Scheduler started with 30 minute interval",
  "interval_minutes": 30
}
```

**2. 스케줄러 중지**:
```bash
curl -X POST http://localhost:8002/api/signals/scheduler/stop
```

**3. 상태 확인**:
```bash
curl http://localhost:8002/api/signals/pipeline/status
```

**응답**:
```json
{
  "scheduler_running": true,
  "interval_minutes": 30,
  "pipeline_stats": {
    "total_cycles": 5,
    "news_processed": 45,
    "news_analyzed": 12,
    "signals_generated": 8,
    "signals_duplicates": 2,
    "signals_low_quality": 1,
    "last_run": "2025-12-03T15:30:00",
    "signal_rate": 0.67
  },
  "recent_signals": [...]
}
```

---

## API 엔드포인트

### 1. POST `/api/signals/generate`

**설명**: 수동으로 신호 생성 트리거

**파라미터**: 없음

**응답**:
```json
{
  "success": true,
  "signals_count": 3,
  "message": "Generated 3 signals"
}
```

---

### 2. POST `/api/signals/scheduler/start`

**설명**: 자동 신호 생성 스케줄러 시작

**파라미터**:
- `interval_minutes` (query, optional): 실행 간격 (기본: 30분)

**예시**:
```bash
POST /api/signals/scheduler/start?interval_minutes=15
```

**응답**:
```json
{
  "success": true,
  "message": "Scheduler started with 15 minute interval",
  "interval_minutes": 15
}
```

---

### 3. POST `/api/signals/scheduler/stop`

**설명**: 스케줄러 중지

**파라미터**: 없음

**응답**:
```json
{
  "success": true,
  "message": "Scheduler stopped successfully"
}
```

---

### 4. GET `/api/signals/pipeline/status`

**설명**: 파이프라인 및 스케줄러 상태 조회

**응답**:
```json
{
  "scheduler_running": true,
  "interval_minutes": 30,
  "pipeline_stats": {
    "total_cycles": 10,
    "news_processed": 95,
    "news_analyzed": 28,
    "signals_generated": 15,
    "signals_duplicates": 5,
    "signals_low_quality": 3,
    "last_run": "2025-12-03T16:00:00",
    "signal_rate": 0.54
  },
  "recent_signals": [
    {
      "ticker": "NVDA",
      "action": "BUY",
      "confidence": 0.85,
      "created_at": "2025-12-03T15:45:00"
    }
  ]
}
```

---

### 5. WebSocket `/ws/signals`

**설명**: 실시간 신호 수신

**연결**:
```javascript
const ws = new WebSocket('ws://localhost:8002/ws/signals');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'signal') {
    console.log('New signal:', data.data);
    // 신호 처리 로직
  }

  if (data.type === 'ping') {
    // Keepalive ping (30초마다)
  }
};
```

**수신 메시지 타입**:

1. **신호 메시지**:
```json
{
  "type": "signal",
  "data": {
    "ticker": "AAPL",
    "action": "SELL",
    "position_size": 0.05,
    "confidence": 0.78,
    "execution_type": "LIMIT",
    "reason": "Negative news sentiment (-0.45) with moderate market impact (60%)",
    "urgency": "MEDIUM",
    "created_at": "2025-12-03T15:30:00",
    "auto_execute": false
  }
}
```

2. **Keepalive Ping** (30초마다):
```json
{
  "type": "ping",
  "timestamp": "2025-12-03T15:30:30"
}
```

---

## 테스트 가이드

### 준비 사항

1. **백엔드 서버 실행 중**:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

2. **필수 환경 변수 설정** (`.env`):
```env
# Gemini API (무료)
GEMINI_API_KEY=your_gemini_api_key

# NewsAPI (선택)
NEWS_API_KEY=your_news_api_key
```

3. **테스트용 뉴스 데이터 준비**:

RSS 피드 크롤링으로 테스트 데이터 생성:
```bash
curl -X POST http://localhost:8002/api/news/crawl?extract_content=true
```

---

### 테스트 시나리오

#### 테스트 1: 수동 신호 생성

```bash
# 1. 신호 생성 트리거
curl -X POST http://localhost:8002/api/signals/generate

# 예상 결과:
# {
#   "success": true,
#   "signals_count": 2,
#   "message": "Generated 2 signals"
# }
```

**검증**:
- ✅ `signals_count > 0` 이면 성공
- ✅ WebSocket에 연결된 클라이언트가 신호 수신
- ✅ 백엔드 로그에 "Signal generated" 메시지 확인

---

#### 테스트 2: 자동 스케줄러

```bash
# 1. 스케줄러 시작 (5분 간격으로 테스트)
curl -X POST "http://localhost:8002/api/signals/scheduler/start?interval_minutes=5"

# 2. 상태 확인
curl http://localhost:8002/api/signals/pipeline/status

# 3. 5분 대기 후 다시 상태 확인 (자동 실행 확인)
sleep 300
curl http://localhost:8002/api/signals/pipeline/status

# 4. 스케줄러 중지
curl -X POST http://localhost:8002/api/signals/scheduler/stop
```

**검증**:
- ✅ `scheduler_running: true`
- ✅ `total_cycles`가 5분마다 증가
- ✅ `signals_generated`가 증가
- ✅ 중지 후 `scheduler_running: false`

---

#### 테스트 3: WebSocket 실시간 수신

**JavaScript (브라우저):**
```javascript
const ws = new WebSocket('ws://localhost:8002/ws/signals');

ws.onopen = () => {
  console.log('✅ WebSocket connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('📨 Received:', data);

  if (data.type === 'signal') {
    console.log('🔔 New Trading Signal:', data.data);
  }
};

ws.onerror = (error) => {
  console.error('❌ WebSocket error:', error);
};

// 신호 생성 트리거
fetch('http://localhost:8002/api/signals/generate', { method: 'POST' })
  .then(() => console.log('✅ Signal generation triggered'));
```

**검증**:
- ✅ WebSocket 연결 성공
- ✅ 30초마다 ping 수신
- ✅ 신호 생성 시 `type: "signal"` 메시지 수신

---

#### 테스트 4: 신호 품질 검증

생성된 신호의 품질을 확인합니다.

```bash
curl http://localhost:8002/api/signals/pipeline/status | jq '.recent_signals'
```

**검증 기준**:
- ✅ `confidence >= 0.6` (최소 신뢰도)
- ✅ `position_size >= 0.01` (최소 포지션 크기)
- ✅ `ticker`가 유효한 심볼
- ✅ `action`이 BUY 또는 SELL
- ✅ `reason`에 구체적인 설명

---

## 트러블슈팅

### 문제 1: 신호가 생성되지 않음

**증상**: `signals_count: 0`

**원인 및 해결**:

1. **미분석 뉴스가 없음**:
```bash
# 뉴스 크롤링 먼저 실행
curl -X POST http://localhost:8002/api/news/crawl
```

2. **모든 뉴스가 이미 분석됨**:
```bash
# 미분석 뉴스 확인
curl http://localhost:8002/api/news/stats
# "unanalyzed_articles"가 0이면 새 뉴스 크롤링 필요
```

3. **분석 결과가 trading_actionable=False**:
- 뉴스의 영향도가 낮음
- 신호 생성 임계값 조정 필요
```python
# backend/services/signal_pipeline.py
signal_generator = NewsSignalGenerator(
    impact_threshold=0.4,  # 0.5에서 0.4로 낮춤
    min_confidence_threshold=0.5  # 0.6에서 0.5로 낮춤
)
```

---

### 문제 2: WebSocket 연결 끊김

**증상**: WebSocket이 바로 종료됨

**원인 및 해결**:

1. **CORS 설정 확인**:
프론트엔드와 백엔드 포트가 다른 경우 CORS 허용 필요.

2. **Nginx/프록시 설정**:
WebSocket을 지원하도록 프록시 설정:
```nginx
location /ws/ {
    proxy_pass http://localhost:8002;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

3. **타임아웃 설정**:
WebSocket은 30초마다 ping을 보내므로 타임아웃은 60초 이상 권장.

---

### 문제 3: Gemini API 할당량 초과

**증상**: `429 Too Many Requests` 또는 `quota exceeded`

**원인**: Gemini 무료 티어 한도 (1,500 requests/day)

**해결**:
```bash
# 사용량 확인
curl http://localhost:8002/api/news/stats | jq '.gemini_usage'

# 배치 크기 조정 (backend/services/signal_pipeline.py)
pipeline = SignalPipeline(
    analysis_batch_size=3,  # 5에서 3으로 줄임
    max_news_per_cycle=5    # 10에서 5로 줄임
)
```

---

### 문제 4: 중복 신호가 계속 생성됨

**증상**: 같은 티커의 신호가 반복 생성

**원인**: 중복 제거 로직 미작동

**확인**:
```bash
curl http://localhost:8002/api/signals/pipeline/status | jq '.pipeline_stats.signals_duplicates'
```

**해결**:
- 파이프라인 재시작
- 히스토리 초기화 (코드 수정 필요)

---

## 설정 옵션

### SignalGenerator 설정

파일: `backend/signals/news_signal_generator.py`

```python
generator = NewsSignalGenerator(
    base_position_size=0.05,      # 기본 포지션 크기 (5%)
    max_position_size=0.10,        # 최대 포지션 크기 (10%)
    min_confidence_threshold=0.6,  # 최소 신뢰도
    sentiment_threshold=0.3,       # 감정 점수 임계값
    impact_threshold=0.5,          # 영향도 임계값
    enable_auto_execute=False,     # 자동 실행 (위험!)
)
```

### Pipeline 설정

파일: `backend/services/signal_pipeline.py`

```python
pipeline = SignalPipeline(
    max_news_per_cycle=10,    # 사이클당 최대 뉴스 개수
    analysis_batch_size=5,    # 배치 분석 크기
)
```

### Scheduler 설정

```bash
# API 호출 시 간격 설정
curl -X POST "http://localhost:8002/api/signals/scheduler/start?interval_minutes=15"
```

---

## 다음 단계

### 완료된 기능 ✅
1. ✅ 뉴스 → AI 분석 파이프라인
2. ✅ 신호 생성 로직
3. ✅ WebSocket 실시간 브로드캐스트
4. ✅ 자동 스케줄러
5. ✅ API 엔드포인트

### 다음 구현 예정 📝
1. **KIS 브로커 연동** (신호 승인 시 실제 주문)
2. **신호 승인/거부 UI** (프론트엔드)
3. **신호 히스토리 DB 저장** (PostgreSQL/TimescaleDB)
4. **백테스트 통합** (과거 신호 성과 분석)
5. **알림 시스템** (이메일/텔레그램)

---

## 요약

### 기본 사용법

```bash
# 1. 뉴스 크롤링
curl -X POST http://localhost:8002/api/news/crawl

# 2. 자동 신호 생성 시작 (30분 간격)
curl -X POST http://localhost:8002/api/signals/scheduler/start

# 3. 상태 확인
curl http://localhost:8002/api/signals/pipeline/status

# 4. 중지
curl -X POST http://localhost:8002/api/signals/scheduler/stop
```

### 프론트엔드 연동

```javascript
// WebSocket 연결
const ws = new WebSocket('ws://localhost:8002/ws/signals');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'signal') {
    // Trading Dashboard에 신호 추가
    addSignalToUI(data.data);
  }
};
```

---

**Status**: 🎉 실시간 신호 생성 파이프라인 완료!
**Next**: KIS 브로커 거래 연동
