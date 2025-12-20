# 📱 Telegram Notification System for AI Trading

실시간 트레이딩 알림을 위한 Telegram Bot 통합 시스템

---

## 🎯 주요 기능

- **거래 신호 알림** (BUY/SELL/HOLD)
- **리스크 경고** (CRITICAL, HIGH, MODERATE)
- **주문 체결 보고**
- **일일/주간 포트폴리오 리포트**
- **시스템 상태 모니터링**
- **Kill Switch 알림**

---

## 🚀 Quick Start

### Step 1: Telegram Bot 생성

1. **@BotFather에게 메시지**
   ```
   Telegram에서 @BotFather 검색
   /newbot 입력
   Bot 이름: AI Trading Alert
   Bot username: your_trading_bot
   ```

2. **Bot Token 받기**
   ```
   🎉 Done! Your bot is created.
   Use this token to access the HTTP API:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

3. **Chat ID 얻기**
   - 생성한 Bot에게 아무 메시지나 보내기
   - 브라우저에서 열기:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   - JSON에서 `"chat":{"id":123456789}` 찾기

### Step 2: 설치

```bash
# 의존성 설치
pip install aiohttp

# 파일 복사 (이미 생성됨)
# - telegram_notifier.py
# - notification_manager.py
# - test_telegram.py
# - example_integration.py
```

### Step 3: 테스트

```bash
# 연결 테스트
python test_telegram.py --token YOUR_TOKEN --chat YOUR_CHAT_ID

# Interactive 모드
python test_telegram.py --token YOUR_TOKEN --chat YOUR_CHAT_ID --mode interactive
```

---

## 📁 파일 구조

```
notifications/
├── telegram_notifier.py      # 핵심 Telegram 클라이언트
├── notification_manager.py   # Trading System 통합
├── test_telegram.py          # 테스트 스크립트
├── example_integration.py    # 통합 예제
└── README_TELEGRAM.md        # 이 파일
```

---

## 💻 사용법

### 기본 알림 전송

```python
from telegram_notifier import TelegramNotifier

notifier = TelegramNotifier(
    bot_token="YOUR_TOKEN",
    chat_id="YOUR_CHAT_ID"
)

# 연결 테스트
await notifier.test_connection()

# 커스텀 메시지
await notifier.send_message("🤖 AI 트레이딩 시스템 가동!")
```

### 거래 신호 알림

```python
await notifier.send_trade_signal(
    ticker="NVDA",
    action="BUY",
    conviction=0.85,
    reasoning="AI/ML 수요 폭발. 데이터센터 매출 150% YoY 성장.",
    target_price=145.00,
    stop_loss=118.00,
    position_size=4.5,
    current_price=125.50,
)
```

**결과:**
```
🟢 BUY Signal: $NVDA

Conviction: 85.0%
Current Price: $125.50
Target Price: $145.00
Upside: 15.5%
Stop Loss: $118.00
Risk: 6.0%
Position Size: 4.5% of portfolio

Reasoning:
AI/ML 수요 폭발. 데이터센터 매출 150% YoY 성장.

⏰ 2025-11-15 14:30:00
```

### 리스크 경고

```python
await notifier.send_risk_alert(
    ticker="COIN",
    risk_type="NON_STANDARD",
    risk_score=0.75,
    risk_factors=[
        "SEC 소송 진행 중",
        "규제 불확실성",
        "내부자 매도 포착",
    ],
    action_taken="거래 차단 - Pre-check에서 필터링",
)
```

### 일일 리포트

```python
await notifier.send_daily_report(
    portfolio_value=105_750.00,
    daily_pnl=1_250.50,
    daily_pnl_pct=1.20,
    total_return_pct=5.75,
    positions=[
        {"ticker": "NVDA", "value": 25000, "pnl_pct": 12.5},
        {"ticker": "MSFT", "value": 20000, "pnl_pct": 3.2},
        {"ticker": "AAPL", "value": 18000, "pnl_pct": -1.5},
    ],
    cash=15750.00,
    trades_today=3,
)
```

### Kill Switch 알림

```python
await notifier.send_kill_switch_alert(
    reason="일일 손실 한도 초과",
    daily_loss_pct=-2.5,
    threshold_pct=-2.0,
)
```

---

## 🔧 Trading Agent 통합

### NotificationManager 사용

```python
from notification_manager import NotificationManager
from trading_agent import TradingAgent

# 매니저 초기화
manager = NotificationManager(
    bot_token="YOUR_TOKEN",
    chat_id="YOUR_CHAT_ID",
    notify_on_buy=True,
    notify_on_sell=True,
    notify_on_hold=False,  # HOLD는 보통 알림 불필요
    notify_on_risk=True,
)

# Trading Agent와 연동
agent = TradingAgent()

async def analyze_with_notification(ticker):
    decision = await agent.analyze(ticker)
    
    # 자동으로 적절한 알림 전송
    await manager.on_trading_decision(decision)
    
    return decision
```

### config.py에 설정 추가

```python
# config.py에 추가

# ==================== Telegram Notifications ====================
telegram_bot_token: str = Field(
    default="",
    description="Telegram Bot API token from @BotFather"
)

telegram_chat_id: str = Field(
    default="",
    description="Telegram chat ID (user or group)"
)

telegram_enabled: bool = Field(
    default=True,
    description="Enable/disable Telegram notifications"
)

telegram_notify_on_buy: bool = Field(
    default=True,
    description="Send notification on BUY signals"
)

telegram_notify_on_sell: bool = Field(
    default=True,
    description="Send notification on SELL signals"
)

telegram_notify_on_hold: bool = Field(
    default=False,
    description="Send notification on HOLD signals"
)

telegram_notify_on_risk: bool = Field(
    default=True,
    description="Send notification on risk alerts"
)

telegram_daily_report_hour: int = Field(
    default=21,
    description="Hour to send daily report (0-23)"
)
```

### .env 파일 설정

```bash
# .env

# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
TELEGRAM_ENABLED=true
TELEGRAM_NOTIFY_ON_BUY=true
TELEGRAM_NOTIFY_ON_SELL=true
TELEGRAM_NOTIFY_ON_HOLD=false
TELEGRAM_NOTIFY_ON_RISK=true
TELEGRAM_DAILY_REPORT_HOUR=21
```

---

## 📊 알림 유형

| 유형 | Emoji | 설명 | 소리 |
|------|-------|------|------|
| BUY Signal | 🟢 | 매수 신호 | ✅ |
| SELL Signal | 🔴 | 매도 신호 | ✅ |
| HOLD Signal | ⚪ | 보유 유지 | 🔇 |
| CRITICAL Risk | 🚨 | 치명적 리스크 | ✅ |
| HIGH Risk | ⚠️ | 높은 리스크 | ✅ |
| Execution | 📈/📉 | 주문 체결 | ✅ |
| Daily Report | 📊 | 일일 리포트 | 🔇 |
| Kill Switch | 🚨🚨🚨 | 시스템 중단 | ✅ |
| System Alert | ℹ️/⚠️/🚨 | 시스템 상태 | 상황별 |

---

## ⚙️ 고급 설정

### Rate Limiting

```python
notifier = TelegramNotifier(
    bot_token="...",
    chat_id="...",
    rate_limit_per_minute=20,  # 분당 최대 20개 메시지
)
```

### 스케줄링 (자동 리포트)

```python
from notification_manager import NotificationScheduler

scheduler = NotificationScheduler(
    notification_manager=manager,
    portfolio_provider=get_portfolio_data,  # 콜백 함수
)

# 시작
await scheduler.start()

# 종료
await scheduler.stop()
```

### 그룹 채팅 지원

Bot을 그룹에 초대하고 그룹의 Chat ID 사용:
```
https://api.telegram.org/bot<TOKEN>/getUpdates
```
그룹 Chat ID는 보통 음수 (예: -123456789)

---

## 🔐 보안 권장사항

1. **Bot Token 보안**
   - .env 파일에만 저장
   - 코드에 하드코딩 금지
   - Git에 커밋하지 않음

2. **권한 설정**
   - Bot에 최소 권한만 부여
   - 민감한 정보는 알림에 포함하지 않음

3. **Rate Limiting**
   - 기본 20메시지/분 제한
   - Telegram API 제한 준수

---

## 📝 예제 시나리오

### 시나리오 1: 아침 시장 분석

```python
async def morning_analysis():
    watchlist = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
    
    await notifier.send_startup_message()
    
    for ticker in watchlist:
        decision = await agent.analyze(ticker)
        await manager.on_trading_decision(decision)
```

### 시나리오 2: 실시간 리스크 모니터링

```python
async def monitor_risks():
    while market_open:
        for position in portfolio.positions:
            risk = await calculate_risk(position.ticker)
            
            if risk >= 0.6:  # CRITICAL
                await manager.on_risk_detected(
                    ticker=position.ticker,
                    risk_type="REAL_TIME_MONITOR",
                    risk_score=risk,
                    risk_factors=["Market volatility spike"],
                    action_taken="Consider reducing position",
                )
        
        await asyncio.sleep(300)  # 5분마다 체크
```

### 시나리오 3: 일일 마감 보고

```python
async def end_of_day_report():
    portfolio = await get_portfolio_snapshot()
    
    await manager.send_daily_portfolio_report({
        "value": portfolio.total_value,
        "daily_pnl": portfolio.daily_pnl,
        "daily_pnl_pct": portfolio.daily_pnl_pct,
        "total_return_pct": portfolio.total_return_pct,
        "positions": portfolio.positions,
        "cash": portfolio.cash,
        "trades_today": portfolio.trades_count,
    })
```

---

## 🐛 트러블슈팅

### 연결 오류

```
Error: Telegram API error: 401 - Unauthorized
```
**해결**: Bot Token이 올바른지 확인

### Chat ID 오류

```
Error: Telegram API error: 400 - Bad Request: chat not found
```
**해결**: 
1. Bot에 먼저 메시지 보내기
2. Chat ID가 올바른지 확인
3. 그룹의 경우 음수 ID 사용

### Rate Limit 초과

```
Warning: Rate limit reached (20/min)
```
**해결**: 메시지 간격 늘리기 또는 rate_limit_per_minute 조정

### 메시지 포맷 오류

```
Error: Can't parse entities
```
**해결**: HTML 태그가 올바르게 닫혔는지 확인

---

## 📈 다음 단계

1. **프로덕션 배포**: NAS에 통합
2. **그룹 알림**: 여러 사용자에게 동시 전송
3. **명령어 지원**: Bot 명령어로 상태 조회
4. **웹훅 모드**: Polling 대신 웹훅 사용
5. **다중 채널**: Discord, Slack 등 추가

---

## 📚 참고 자료

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [aiohttp 문서](https://docs.aiohttp.org/)
- [MASTER_GUIDE.md](../MASTER_GUIDE.md)
- [trading_agent.py](../trading_agent.py)

---

**구현 완료**: 2025-11-15  
**총 코드**: ~1,500 lines  
**예상 비용**: $0/월 (Telegram API 무료)  
**구현 시간**: 1일

---

🎉 **축하합니다! Telegram 알림 시스템 구현 완료!**