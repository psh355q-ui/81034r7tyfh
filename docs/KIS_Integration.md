## 한국투자증권 API 통합 가이드

AI Trading System의 실거래를 위한 한국투자증권 Open Trading API 통합

---

## 🎯 개요

한국투자증권 Open Trading API를 통해 **실제 브로커 계좌**로 거래할 수 있습니다.

**지원 기능**:
- 해외 주식 거래 (US: NASDAQ, NYSE, AMEX)
- 실시간 시세 조회
- 계좌 잔고 조회
- 시장가/지정가 주문
- 가상 투자 (모의투자) 지원

---

## 📋 사전 준비

### 1. 한국투자증권 계좌 개설

1. [한국투자증권](https://securities.koreainvestment.com/) 방문
2. 계좌 개설 (해외주식 거래 가능 계좌)

### 2. KIS Developers API 신청

1. [KIS Developers](https://apiportal.koreainvestment.com/) 접속
2. 회원가입 및 로그인
3. "API 신청" → "앱 등록"
4. **APP KEY** 와 **APP SECRET** 발급 받기
5. 모의투자 신청 (실거래 전 필수!)

---

## ⚙️ 설정

### 1. KIS 설정 파일 생성

KIS API는 홈 디렉토리에 설정 파일이 필요합니다:

```bash
# Windows
mkdir %USERPROFILE%\KIS\config

# Linux/Mac
mkdir -p ~/KIS/config
```

### 2. kis_devlp.yaml 생성

`~/KIS/config/kis_devlp.yaml` 파일을 생성하고 다음 내용 입력:

```yaml
# KIS Open Trading API Configuration
my_app: "YOUR_APP_KEY"
my_sec: "YOUR_APP_SECRET"
my_acct: "YOUR_ACCOUNT_NUMBER"  # 8자리 계좌번호
my_prod: "01"  # 01: 종합계좌
my_agent: "AI-Trading-System/1.0"

# Virtual Trading (모의투자)
vps:
  url: "https://openapivts.koreainvestment.com:29443"

# Real Trading (실거래) - 주의!
prod:
  url: "https://openapi.koreainvestment.com:9443"
```

**중요**: APP KEY와 APP SECRET은 절대 Git에 커밋하지 마세요!

### 3. 환경 변수 설정 (선택사항)

`.env` 파일에 추가:

```bash
# KIS API
KIS_ACCOUNT_NUMBER=12345678
KIS_PRODUCT_CODE=01
KIS_IS_VIRTUAL=true  # false for real trading
```

---

## 🚀 사용법

### 기본 사용

```python
from brokers import KISBroker

# Initialize broker (virtual trading)
broker = KISBroker(
    account_no="12345678",
    is_virtual=True  # 모의투자
)

# Get broker info
info = broker.get_info()
print(f"Broker: {info['broker']}")
print(f"Mode: {info['mode']}")

# Get current price
price = broker.get_price("AAPL", exchange="NASDAQ")
print(f"AAPL: ${price['current_price']:.2f}")

# Get account balance
balance = broker.get_account_balance()
print(f"Total Value: ${balance['total_value']:,.2f}")
print(f"Positions: {len(balance['positions'])}")

# Place market buy order
result = broker.buy_market_order(
    symbol="NVDA",
    quantity=10,
    exchange="NASDAQ"
)
print(f"Order placed: {result['status']}")

# Place limit buy order
result = broker.buy_limit_order(
    symbol="MSFT",
    quantity=5,
    price=400.00,
    exchange="NASDAQ"
)
```

### Paper Trading과 통합

Paper Trading에서 실거래로 전환:

```python
from paper_trading import PaperTradingEngine, PaperTradingConfig
from brokers import KISBroker

# Create broker instance
broker = KISBroker(
    account_no="12345678",
    is_virtual=True
)

# Paper Trading Engine에서 거래 신호 받기
# → KIS Broker로 실제 주문 실행
```

### AI Trading Agent와 통합

```python
from ai import TradingAgent
from brokers import KISBroker

agent = TradingAgent()
broker = KISBroker(account_no="12345678", is_virtual=True)

# Analyze stock
decision = await agent.analyze("AAPL")

# Execute if BUY signal
if decision.action == "BUY":
    # Calculate shares from position size
    balance = broker.get_account_balance()
    total_value = balance['total_value']
    target_value = (decision.position_size / 100) * total_value

    current_price = broker.get_price("AAPL")['current_price']
    shares = int(target_value / current_price)

    # Place order
    result = broker.buy_market_order("AAPL", shares)
    print(f"Executed: {result}")
```

---

## 🧪 테스트

### 테스트 스크립트 실행

```bash
cd backend/brokers

# Basic tests (price quotes, balance)
python test_kis.py --account 12345678

# Test order execution (virtual trading only!)
python test_kis.py --account 12345678 --test-order
```

**테스트 결과 예시**:
```
======================================================================
KIS BROKER INTEGRATION TEST
======================================================================
Account: 12345678
Mode: Virtual Trading
======================================================================

Initializing KIS Broker...
KIS authentication successful

TEST 1: Broker Information
======================================================================
Broker: Korea Investment & Securities
Account: 12345678
Mode: Virtual
Server: vps
Available: True
OK: Broker info retrieved

TEST 2: Price Quotes
======================================================================

AAPL:
  Name: Apple Inc.
  Price: $273.20
  Change: $+2.50 (+0.92%)
  Volume: 45,234,567

NVDA:
  Name: NVIDIA Corp
  Price: $186.69
  Change: $+4.23 (+2.32%)
  Volume: 123,456,789

OK: Price quotes retrieved

TEST 3: Account Balance
======================================================================
Total Value: $100,000.00
Cash: $100,000.00
Positions: 0

No current positions

OK: Account balance retrieved

======================================================================
TEST SUMMARY
======================================================================
All basic tests completed successfully!

KIS Broker is ready for trading.
======================================================================
```

---

## 📊 지원 기능

### Market Data

| 기능 | 메서드 | 설명 |
|------|--------|------|
| 현재가 조회 | `get_price(symbol, exchange)` | 실시간 주가 |
| 계좌 잔고 | `get_account_balance()` | 잔고 및 포지션 |
| 시장 상태 | `is_market_open(exchange)` | 개장 여부 |

### Order Execution

| 주문 유형 | 메서드 | 설명 |
|----------|--------|------|
| 시장가 매수 | `buy_market_order(symbol, qty, exchange)` | 즉시 체결 |
| 시장가 매도 | `sell_market_order(symbol, qty, exchange)` | 즉시 체결 |
| 지정가 매수 | `buy_limit_order(symbol, qty, price, exchange)` | 가격 지정 |

### Supported Exchanges

| Exchange | Code | 설명 |
|----------|------|------|
| NASDAQ | "NASDAQ" | 나스닥 |
| NYSE | "NYSE" | 뉴욕증권거래소 |
| AMEX | "AMEX" | 아멕스 |

---

## ⚠️ 주의사항

### 1. 모의투자 먼저!

**실거래 전 반드시 모의투자로 충분히 테스트하세요!**

```python
# 모의투자 (Virtual Trading)
broker = KISBroker(account_no="12345678", is_virtual=True)

# 실거래 (Real Trading) - 주의!
broker = KISBroker(account_no="12345678", is_virtual=False)
```

### 2. API 호출 제한 (Rate Limits)

**REST API 유량 제한**:
- **실전투자**: 1초당 20건 (계좌 단위)
- **모의투자**: 1초당 2건 (계좌 단위)
- **토큰 발급** (`/oauth2/tokenP`): 1초당 1건

**WebSocket 유량 제한**:
- **1세션당**: 실시간 데이터 합산 41건까지 등록 가능
- **구독 항목**: 실시간체결가 + 호가 + 예상체결 + 체결통보 등
- **범위**: 국내주식/해외주식/국내파생/해외파생 모든 상품 합산
- **세션 제한**: 계좌(앱키) 단위로 1세션
- **다중 세션**: 1개 PC에서 여러 계좌(앱키)로 세션 연결 가능

**⚠️ 중요 사항**:
- 유량 제한은 **계좌(앱키) 단위**로 적용
- 제한 초과 시 일시적 차단 가능
- 초과 유량에 대한 과금 정책 없음
- 유량 확대 불가 (다른 계좌 API 신청 필요)

**Live Trading Engine 권장 설정**:
```python
# 실전투자 (1초당 20건)
decision_interval_seconds = 300  # 5분마다 의사결정
max_tickers = 5                  # 동시 분석 종목 수 제한

# 모의투자 (1초당 2건)
decision_interval_seconds = 600  # 10분마다 의사결정
max_tickers = 2                  # 동시 분석 종목 수 제한
```

**API 호출 최적화**:
- 가격 조회 캐싱 (15초)
- 계좌 잔고 조회 최소화
- 배치 처리 대신 순차 처리

### 3. 거래 시간

**미국 시장 (ET)**:
- 정규장: 09:30 - 16:00
- 프리마켓: 04:00 - 09:30
- 애프터마켓: 16:00 - 20:00

**한국 시간 (KST)**:
- 정규장: 23:30 - 06:00 (다음날)
- 프리마켓: 18:00 - 23:30
- 애프터마켓: 06:00 - 10:00

### 4. 보안

- ⚠️ **APP KEY/SECRET 노출 금지**
- ⚠️ **GitHub에 절대 커밋하지 말 것**
- ⚠️ **토큰 파일 보안 유지**

---

## 🔧 문제 해결

### 인증 실패

```
ERROR: KIS authentication failed
```

**해결**:
1. `~/KIS/config/kis_devlp.yaml` 파일 확인
2. APP KEY, APP SECRET 올바른지 확인
3. 모의투자 신청 완료 여부 확인

### 모듈 import 오류

```
ImportError: KIS API not available
```

**해결**:
```bash
# KIS API 경로 확인
echo $KIS_API_PATH

# kis_broker.py에서 KIS_API_PATH 수정
KIS_API_PATH = r"D:\code\open-trading-api-main\examples_user"
```

### 주문 실패

```
ERROR: Failed to place BUY order
```

**해결**:
1. 계좌 잔고 충분한지 확인
2. 거래 시간 확인 (시장 개장 시간)
3. 종목 코드 (symbol) 올바른지 확인
4. 모의투자 계좌로 테스트

---

## 📈 실거래 전 체크리스트

실거래로 전환하기 전 반드시 확인:

- [ ] 모의투자로 충분히 테스트 (최소 1주일)
- [ ] AI 전략 백테스팅 완료
- [ ] Paper Trading 성공적 수행
- [ ] 리스크 관리 룰 설정 (Kill Switch, Stop Loss)
- [ ] Telegram 알림 설정 완료
- [ ] 거래 로그 모니터링 준비
- [ ] 투자 가능 금액 확인
- [ ] 감정적 거래 방지 준비

---

## 📚 참고 자료

- [KIS Developers 포털](https://apiportal.koreainvestment.com/)
- [KIS Open Trading API GitHub](https://github.com/koreainvestment/open-trading-api)
- [한국투자증권 고객센터](https://securities.koreainvestment.com/)

---

## 💰 수수료

**해외 주식 거래 수수료** (한국투자증권):
- 매수/매도: 0.25%
- SEC Fee: 변동
- TAF Fee: 변동

자세한 내용은 한국투자증권에 문의하세요.

---

**면책조항**: 이 시스템은 교육 및 개인 투자 목적으로만 사용하세요. 투자 손실에 대한 책임은 본인에게 있습니다.

---

*Generated by AI Trading System Team*
*Date: 2025-11-15*
