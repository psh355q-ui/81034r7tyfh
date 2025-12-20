# KIS 브로커 거래 연동 가이드

**작성일**: 2025-12-03
**상태**: ✅ 완료 - 테스트 준비

---

## 📋 목차

1. [개요](#개요)
2. [시스템 구조](#시스템-구조)
3. [설정 방법](#설정-방법)
4. [사용 방법](#사용-방법)
5. [API 엔드포인트](#api-엔드포인트)
6. [테스트 가이드](#테스트-가이드)
7. [트러블슈팅](#트러블슈팅)

---

## 개요

### 기능

신호 승인 시 한국투자증권(KIS) API를 통해 실제 주문을 자동 실행합니다.

### 프로세스 흐름

```
신호 생성 → 신호 승인 → KIS 주문 실행 → 주문 체결 → 포지션 추적
```

### 주요 특징

- ✅ **모의투자 지원**: 실전 전 안전하게 테스트 (기본값)
- ✅ **자동 주문 실행**: 신호 승인 즉시 KIS API로 주문
- ✅ **주문 상태 추적**: 제출/체결/취소 상태 실시간 추적
- ✅ **재시도 로직**: 실패 시 자동 재시도 (최대 3회)
- ✅ **에러 처리**: 상세한 에러 로깅 및 사용자 피드백

---

## 시스템 구조

### 핵심 컴포넌트

#### 1. SignalExecutor (`backend/services/signal_executor.py`)

**역할**: 신호를 KIS 주문으로 변환 및 실행

**주요 메서드**:
- `execute_signal(signal, force_execute)`: 신호 실행
- `get_statistics()`: 실행 통계 조회
- `get_execution_history()`: 실행 히스토리 조회

**실행 프로세스**:
1. 신호 유효성 검증
2. KIS 클라이언트 초기화
3. 현재가 조회
4. 계좌 잔고 조회
5. 주문 수량 계산
6. 주문 실행 (시장가/지정가)
7. 결과 저장

#### 2. KIS Client (`backend/trading/kis_client.py`)

**역할**: 한국투자증권 Open API 클라이언트

**주요 기능**:
- OAuth 토큰 자동 발급/갱신
- 시세 조회
- 매수/매도 주문
- 계좌 잔고 조회
- 주문 취소/정정

#### 3. Signals Router (`backend/api/signals_router.py`)

**역할**: 신호 관리 API

**주요 엔드포인트**:
- `POST /api/signals/{signal_id}/approve`: 신호 승인
- `POST /api/signals/{signal_id}/execute`: 신호 실행 (KIS 주문)
- `POST /api/signals/{signal_id}/reject`: 신호 거부

---

## 설정 방법

### 1. KIS API 키 발급

1. [한국투자증권 OpenAPI](https://apiportal.koreainvestment.com/) 접속
2. 회원가입 및 로그인
3. **모의투자 API 키 발급** (테스트용)
   - 앱키 (App Key)
   - 앱 시크릿 (App Secret)
   - 모의투자 계좌번호

4. (선택) **실전투자 API 키 발급**
   - 실제 거래 시 필요

### 2. 환경 변수 설정

`.env` 파일에 KIS API 정보 추가:

```env
# ============================================
# KIS 한국투자증권 API (모의투자)
# ============================================

# 모의투자 앱키
KIS_PAPER_APP_KEY=your_paper_app_key_here
KIS_PAPER_APP_SECRET=your_paper_app_secret_here
KIS_PAPER_ACCOUNT=12345678  # 모의투자 계좌번호 앞 8자리

# (선택) 실전투자 앱키
KIS_APP_KEY=your_real_app_key_here
KIS_APP_SECRET=your_real_app_secret_here
KIS_ACCOUNT_NO=12345678  # 실전투자 계좌번호 앞 8자리

# HTS ID (체결통보 등에 사용)
KIS_HTS_ID=your_hts_id

# 계좌 상품코드 (01: 종합계좌)
KIS_PROD_CODE=01
```

### 3. 설정 파일 생성 (선택사항)

홈 디렉토리에 YAML 설정 파일 생성:

**위치**: `~/KIS/config/kis_devlp.yaml`

```yaml
# 모의투자
paper_app: "모의투자 앱키"
paper_sec: "모의투자 앱시크릿"
my_paper_stock: "모의투자 계좌번호"

# 실전투자
my_app: "실전투자 앱키"
my_sec: "실전투자 앱시크릿"
my_acct_stock: "실전투자 계좌번호"

# 공통
my_htsid: "HTS ID"
my_prod: "01"
```

---

## 사용 방법

### 옵션 1: 신호 승인 → 수동 실행

**1단계: 신호 승인**
```bash
curl -X PUT http://localhost:8000/api/signals/{signal_id}/approve
```

**2단계: 신호 실행** (KIS 주문)
```bash
# 모의투자로 실행 (기본, 안전)
curl -X POST "http://localhost:8000/api/signals/{signal_id}/execute?use_paper_trading=true"

# 실전투자로 실행 (⚠️ 주의!)
curl -X POST "http://localhost:8000/api/signals/{signal_id}/execute?use_paper_trading=false"
```

**응답 예시**:
```json
{
  "signal_id": "sig_1701622800",
  "status": "EXECUTED",
  "execution_result": {
    "success": true,
    "order_id": "1234567890",
    "status": "SUBMITTED",
    "message": "Order submitted: BUY 10 shares @ $450.50",
    "timestamp": "2025-12-03T15:30:00"
  },
  "message": "Order submitted: BUY 10 shares @ $450.50",
  "ticker": "NVDA",
  "action": "BUY",
  "order_id": "1234567890"
}
```

---

### 옵션 2: 강제 실행 (승인 없이)

```bash
# 승인 절차 없이 바로 실행 (force_execute=true)
curl -X POST "http://localhost:8000/api/signals/{signal_id}/execute?force_execute=true&use_paper_trading=true"
```

**주의**: 이 방법은 승인 절차를 건너뛰므로 신중하게 사용하세요.

---

## API 엔드포인트

### 1. POST `/api/signals/{signal_id}/execute`

**설명**: 신호를 KIS 브로커를 통해 실제 주문 실행

**파라미터**:
- `signal_id` (path, required): 신호 ID
- `force_execute` (query, optional): 강제 실행 (기본: false)
- `use_paper_trading` (query, optional): 모의투자 사용 (기본: true)

**예시**:
```bash
# 모의투자로 실행 (안전)
POST /api/signals/sig_123/execute?use_paper_trading=true

# 강제 실행 (승인 건너뛰기)
POST /api/signals/sig_123/execute?force_execute=true

# 실전투자로 실행 (⚠️ 위험!)
POST /api/signals/sig_123/execute?use_paper_trading=false
```

**응답 (성공)**:
```json
{
  "signal_id": "sig_123",
  "status": "EXECUTED",
  "execution_result": {
    "success": true,
    "order_id": "1234567890",
    "status": "SUBMITTED",
    "message": "Order submitted: BUY 10 shares @ $450.50",
    "kis_response": {
      "success": true,
      "order_id": "1234567890",
      "message": "정상처리되었습니다"
    },
    "error": null,
    "timestamp": "2025-12-03T15:30:00"
  },
  "message": "Order submitted: BUY 10 shares @ $450.50",
  "ticker": "NVDA",
  "action": "BUY",
  "order_id": "1234567890"
}
```

**응답 (실패)**:
```json
{
  "signal_id": "sig_123",
  "status": "FAILED",
  "execution_result": {
    "success": false,
    "order_id": null,
    "status": "FAILED",
    "message": "Insufficient balance or invalid quantity: 0",
    "error": "INSUFFICIENT_BALANCE",
    "timestamp": "2025-12-03T15:30:00"
  },
  "message": "Insufficient balance or invalid quantity: 0",
  "ticker": "NVDA",
  "action": "BUY",
  "order_id": null
}
```

**에러 코드**:
- `404`: 신호를 찾을 수 없음
- `400`: 신호가 실행 불가능한 상태 (이미 실행됨, 거부됨 등)
- `503`: SignalExecutor 서비스 사용 불가
- `500`: 실행 중 예외 발생

---

### 2. PUT `/api/signals/{signal_id}/approve`

**설명**: 신호 승인 (실행 전 단계)

**파라미터**:
- `signal_id` (path, required): 신호 ID

**응답**:
```json
{
  "signal_id": "sig_123",
  "status": "APPROVED",
  "approved_at": "2025-12-03T15:29:00",
  "message": "Signal approved successfully"
}
```

---

### 3. DELETE `/api/signals/{signal_id}/reject`

**설명**: 신호 거부

**파라미터**:
- `signal_id` (path, required): 신호 ID
- `reason` (query, optional): 거부 사유

**응답**:
```json
{
  "signal_id": "sig_123",
  "status": "REJECTED",
  "rejected_at": "2025-12-03T15:29:00",
  "reason": "Low confidence"
}
```

---

## 테스트 가이드

### 준비사항

1. **KIS API 키 설정 완료**
2. **백엔드 서버 실행 중**
3. **테스트용 신호 생성**

### 테스트 시나리오

#### 테스트 1: 모의투자 주문 실행

**목표**: 모의투자 계좌에서 안전하게 주문 테스트

```bash
# 1. 신호 생성 (수동 또는 파이프라인)
curl -X POST http://localhost:8000/api/signals/generate

# 2. 생성된 신호 확인
curl http://localhost:8000/api/signals?limit=1

# 신호 ID 확인 (예: sig_1701622800)
SIGNAL_ID="sig_1701622800"

# 3. 신호 승인
curl -X PUT "http://localhost:8000/api/signals/$SIGNAL_ID/approve"

# 4. 모의투자로 실행
curl -X POST "http://localhost:8000/api/signals/$SIGNAL_ID/execute?use_paper_trading=true"
```

**검증**:
- ✅ `execution_result.success: true`
- ✅ `order_id`가 반환됨
- ✅ KIS 모의투자 앱에서 주문 확인

---

#### 테스트 2: 강제 실행 (승인 건너뛰기)

```bash
# 승인 없이 바로 실행
curl -X POST "http://localhost:8000/api/signals/$SIGNAL_ID/execute?force_execute=true&use_paper_trading=true"
```

**검증**:
- ✅ 승인 절차 없이 실행됨
- ✅ `status: "EXECUTED"`

---

#### 테스트 3: 잔고 부족 시나리오

```bash
# 큰 position_size로 신호 생성 (잔고 초과)
# 수동으로 신호 데이터 수정하거나 position_size를 1.0으로 설정

curl -X POST "http://localhost:8000/api/signals/$SIGNAL_ID/execute?force_execute=true&use_paper_trading=true"
```

**예상 결과**:
```json
{
  "status": "FAILED",
  "execution_result": {
    "success": false,
    "error": "INSUFFICIENT_BALANCE",
    "message": "Insufficient balance or invalid quantity: 0"
  }
}
```

---

#### 테스트 4: 실행 통계 조회

```bash
# 파이프라인 상태에서 실행 통계 확인
curl http://localhost:8000/api/signals/pipeline/status
```

**응답**:
```json
{
  "pipeline_stats": {
    "signals_generated": 10,
    ...
  },
  "executor_stats": {
    "total_executions": 5,
    "successful": 4,
    "failed": 1,
    "success_rate": 0.8,
    "total_volume": 45000.0
  }
}
```

---

## 트러블슈팅

### 문제 1: KIS API 인증 실패

**증상**: `Failed to get KIS access token`

**원인**:
- API 키가 잘못됨
- 환경 변수 미설정
- 네트워크 오류

**해결**:
```bash
# 1. 환경 변수 확인
echo $KIS_PAPER_APP_KEY
echo $KIS_PAPER_APP_SECRET

# 2. .env 파일 확인
cat .env | grep KIS

# 3. kis_devlp.yaml 확인 (있는 경우)
cat ~/KIS/config/kis_devlp.yaml

# 4. 수동으로 토큰 발급 테스트
python -c "
from backend.trading.kis_client import KISClient
client = KISClient(use_paper=True)
token = client.get_access_token()
print('Token:', token)
"
```

---

### 문제 2: 주문 실패 (잔고 부족)

**증상**: `Insufficient balance or invalid quantity: 0`

**원인**:
- 계좌 잔고가 부족
- position_size가 너무 큼
- 주가가 너무 높음

**해결**:
```bash
# 1. 계좌 잔고 확인
python -c "
from backend.trading.kis_client import KISClient
client = KISClient(use_paper=True)
balance = client.get_balance()
print('Balance:', balance)
"

# 2. position_size 조정
# backend/signals/news_signal_generator.py 수정
base_position_size=0.02  # 5%에서 2%로 줄임
```

---

### 문제 3: 주문이 체결되지 않음

**증상**: `status: "SUBMITTED"` 상태에서 계속 대기

**원인**:
- 지정가 주문이 현재가와 차이가 큼
- 유동성 부족 (모의투자는 실제 호가 반영)

**해결**:
```bash
# 시장가 주문으로 변경
# signal의 execution_type을 "MARKET"으로 설정

# 또는 지정가를 현재가에 근접하게 조정
```

---

### 문제 4: SignalExecutor 서비스 사용 불가

**증상**: `503 Signal executor service not available`

**원인**: `backend/services/signal_executor.py` import 실패

**해결**:
```bash
# 1. 파일 존재 확인
ls backend/services/signal_executor.py

# 2. Import 테스트
python -c "from backend.services.signal_executor import get_signal_executor; print('OK')"

# 3. 백엔드 재시작
cd backend
uvicorn main:app --reload
```

---

## 주의사항

### 🔴 실전투자 사용 시 주의

1. **반드시 모의투자로 먼저 테스트**
```bash
# 모의투자로 충분히 테스트 후
use_paper_trading=true
```

2. **실전투자는 소액부터**
```python
# position_size를 작게 설정
base_position_size=0.01  # 1%
```

3. **자동 실행 비활성화**
```python
# 수동 승인 후에만 실행
enable_auto_execute=False
```

4. **Kill Switch 활용**
```bash
# 문제 발생 시 즉시 중지
curl -X POST http://localhost:8000/api/signals/validator/kill-switch/enable
```

---

## 설정 옵션

### SignalExecutor 설정

파일: `backend/services/signal_executor.py`

```python
executor = SignalExecutor(
    use_paper_trading=True,       # 모의투자 사용 (기본: True)
    max_retries=3,                 # 재시도 횟수
    enable_auto_execute=False,     # 자동 실행 비활성화 (안전)
)
```

### NewsSignalGenerator 설정

파일: `backend/signals/news_signal_generator.py`

```python
generator = NewsSignalGenerator(
    base_position_size=0.02,       # 2% (안전하게)
    max_position_size=0.05,        # 최대 5%
    min_confidence_threshold=0.7,  # 신뢰도 0.7 이상만
    enable_auto_execute=False,     # 자동 실행 비활성화
)
```

---

## 다음 단계

### 완료된 기능 ✅
1. ✅ KIS API 클라이언트 연동
2. ✅ SignalExecutor 서비스 구현
3. ✅ 신호 실행 API 엔드포인트
4. ✅ 주문 상태 추적
5. ✅ 에러 처리 및 재시도

### 다음 구현 예정 📝
1. **주문 체결 확인** (WebSocket 또는 폴링)
2. **포지션 자동 추적** (보유 주식 관리)
3. **손익 계산** (실현/미실현 손익)
4. **자동 익절/손절** (Stop Loss/Take Profit)
5. **거래 히스토리 DB 저장** (PostgreSQL/TimescaleDB)

---

## 요약

### 기본 사용법 (모의투자)

```bash
# 1. 신호 생성
curl -X POST http://localhost:8000/api/signals/generate

# 2. 신호 ID 확인
curl http://localhost:8000/api/signals?limit=1

# 3. 신호 승인
curl -X PUT http://localhost:8000/api/signals/SIGNAL_ID/approve

# 4. 모의투자로 실행
curl -X POST "http://localhost:8000/api/signals/SIGNAL_ID/execute?use_paper_trading=true"

# 5. 결과 확인
# - status: "EXECUTED"
# - order_id: KIS 주문번호
# - KIS 모의투자 앱에서 체결 확인
```

---

**Status**: 🎉 KIS 브로커 거래 연동 완료!
**Next**: 백엔드 누락 API 엔드포인트 구현 (뉴스/AI리뷰/리스크 등)
