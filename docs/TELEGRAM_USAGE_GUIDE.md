# 텔레그램 봇 사용 가이드

이 가이드는 AI Trading System에서 텔레그램 봇을 사용하여 메시지를 보내는 방법을 안내합니다.

## ✅ 사전 준비 완료

이미 다음 설정이 완료되어 있습니다:

- ✅ `.env` 파일에 텔레그램 설정 완료
  - `TELEGRAM_BOT_TOKEN=8537935678:AAEFWI4p5BKcDgeFTzSxRguKDjLsA5FVQfA`
  - `TELEGRAM_CHAT_ID=6869034465`
  - `TELEGRAM_COMMANDER_CHAT_ID=6869034465`
  - `TELEGRAM_ENABLED=true`

- ✅ PDF 파일 전송 테스트 완료

## 📋 텔레그램 봇 시스템 구성

### 1. TelegramNotifier (기본 알림 시스템)
- 파일: `backend/notifications/telegram_notifier.py`
- 기능: 텍스트 메시지, 파일 전송, 트레이딩 시그널, 시스템 알림

### 2. TelegramCommandBot (명령어 봇)
- 파일: `backend/notifications/telegram_command_bot.py`
- 기능: 사용자 명령어 처리 (`/status`, `/portfolio`, `/schedule`, `/economic`, `/help`)

### 3. TelegramCommanderBot (제안 승인/거부 봇)
- 파일: `backend/notifications/telegram_commander_bot.py`
- 기능: AI 제안 승인/거부, 헌법 관리

---

## 🚀 빠른 시작

### 방법 1: 기본 텍스트 메시지 전송

```python
import asyncio
import os
from backend.notifications.telegram_notifier import TelegramNotifier

async def send_message():
    # TelegramNotifier 초기화 (환경 변수에서 자동 로드)
    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enabled=True,
    )
    
    # 텍스트 메시지 전송
    success = await telegram_notifier.send_message(
        text="🚀 테스트 메시지입니다!",
        parse_mode="HTML",
        disable_notification=False,
    )
    
    if success:
        print("✅ 메시지 전송 성공!")
    else:
        print("❌ 메시지 전송 실패!")

# 실행
asyncio.run(send_message())
```

### 방법 2: 파일 전송

```python
async def send_file():
    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enabled=True,
    )
    
    # 파일 전송
    success = await telegram_notifier.send_file(
        file_path="path/to/file.pdf",
        caption="📄 테스트 파일입니다.",
        disable_notification=False,
    )
    
    if success:
        print("✅ 파일 전송 성공!")

# 실행
asyncio.run(send_file())
```

### 방법 3: 트레이딩 시그널 전송

```python
async def send_trade_signal():
    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enabled=True,
    )
    
    # BUY 시그널 전송
    success = await telegram_notifier.send_trade_signal(
        ticker="AAPL",
        action="BUY",
        conviction=0.85,
        reasoning="강력한 실적 발표와 기술적 상승 패턴",
        target_price=195.0,
        stop_loss=175.0,
        position_size=5.0,
        current_price=182.5,
    )
    
    if success:
        print("✅ 트레이딩 시그널 전송 성공!")

# 실행
asyncio.run(send_trade_signal())
```

---

## 📊 TelegramCommandBot 사용 (명령어 봇)

### 초기화

```python
import asyncio
import os
from backend.notifications.telegram_notifier import TelegramNotifier
from backend.notifications.telegram_command_bot import TelegramCommandBot

async def test_command_bot():
    # TelegramNotifier 초기화
    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enabled=True,
    )
    
    # TelegramCommandBot 초기화
    command_bot = TelegramCommandBot(
        telegram_notifier=telegram_notifier,
        portfolio_analyzer=None,  # 필요시 PortfolioAnalyzer 초기화
        economic_calendar_manager=None,  # 필요시 EconomicCalendarManager 초기화
    )
    
    # 명령어 테스트
    response = await command_bot.handle_command("/status")
    print(response)
    
    response = await command_bot.handle_command("/help")
    print(response)

# 실행
asyncio.run(test_command_bot())
```

### 사용 가능한 명령어

| 명령어 | 설명 |
|--------|------|
| `/status` | 현재 시장 현황 |
| `/portfolio` | 포트폴리오 요약 |
| `/schedule` | 오늘 브리핑 스케줄 |
| `/economic` | 오늘의 경제 일정 |
| `/help` | 도움말 |

---

## 🧪 테스트 스크립트 실행

### 1. 기본 테스트 (test_telegram.py)

```bash
# 전체 테스트 실행
python backend/notifications/test_telegram.py

# 또는 환경 변수 지정
python backend/notifications/test_telegram.py --token YOUR_TOKEN --chat YOUR_CHAT_ID
```

**테스트 항목:**
- 연결 테스트
- 트레이딩 시그널 (BUY/SELL/HOLD)
- 리스크 알림
- 실행 리포트
- 포트폴리오 리포트
- 시스템 알림

### 2. PDF 전송 테스트 (test_pdf_send.py)

```bash
# PDF 생성 및 전송 테스트
python backend/notifications/test_pdf_send.py
```

### 3. 대화형 테스트

```bash
# 대화형 테스트 모드
python backend/notifications/test_telegram.py --mode interactive
```

**대화형 옵션:**
1. 사용자 정의 메시지 전송
2. BUY 시그널 전송
3. SELL 시그널 전송
4. 리스크 알림 전송
5. 일일 리포트 전송
6. 시스템 알림 전송
7. 통계 확인

---

## 📝 실제 사용 예시

### 예시 1: 일일 브리핑 전송

```python
async def send_daily_briefing():
    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enabled=True,
    )
    
    # 일일 리포트 전송
    await telegram_notifier.send_daily_report(
        portfolio_value=125000.50,
        daily_pnl=2500.75,
        daily_pnl_pct=2.04,
        total_return_pct=15.5,
        positions=[
            {"ticker": "AAPL", "value": 50000, "pnl_pct": 2.5},
            {"ticker": "MSFT", "value": 35000, "pnl_pct": 1.8},
            {"ticker": "GOOGL", "value": 20000, "pnl_pct": -0.5},
        ],
        cash=20000.0,
        trades_today=5,
    )

# 실행
asyncio.run(send_daily_briefing())
```

### 예시 2: 경제지표 알림 전송

```python
from datetime import datetime

async def send_economic_alert():
    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enabled=True,
    )
    
    # 경제지표 알림 메시지
    message = f"""
📈 <b>경제지표 발표</b>

<b>Non-Farm Payrolls</b>
• Actual: 200K
• Forecast: 180K
• Previous: 170K
• Surprise: +11.1%

<b>해석:</b>
고용 증가가 예상보다 높아 경제가 강력함을 보여줍니다.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await telegram_notifier.send_message(message, parse_mode="HTML")

# 실행
asyncio.run(send_economic_alert())
```

### 예시 3: 시스템 알림 전송

```python
from backend.notifications.telegram_notifier import AlertType

async def send_system_alert():
    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enabled=True,
    )
    
    # 시스템 알림 전송
    await telegram_notifier.send_system_alert(
        alert_type=AlertType.HIGH,
        title="데이터베이스 연결 실패",
        message="Redis 연결이 끊어졌습니다. 자동 재시도 중...",
        action_required="Redis 컨테이너 상태 확인: docker ps",
    )

# 실행
asyncio.run(send_system_alert())
```

---

## 🔧 문제 해결

### 문제 1: 메시지가 도착하지 않음

**원인:**
- Bot이 차단됨
- 인터넷 연결 문제
- Rate Limit 초과

**해결:**
1. Telegram에서 Bot이 차단되지 않았는지 확인
2. 인터넷 연결 확인
3. Rate Limit 준수 (분당 20개 메시지)

### 문제 2: "Unauthorized" 오류

**원인:** Bot Token이 잘못됨

**해결:**
1. `.env` 파일에서 `TELEGRAM_BOT_TOKEN` 확인
2. @BotFather에서 새로운 Token 발급 필요시 재발급

### 문제 3: "Bad Request: chat not found" 오류

**원인:** Chat ID가 잘못됨

**해결:**
1. `.env` 파일에서 `TELEGRAM_CHAT_ID` 확인
2. @userinfobot 또는 @myidbot으로 Chat ID 재확인

### 문제 4: 파일 전송 실패

**원인:**
- 파일이 존재하지 않음
- 파일 크기가 50MB 초과
- 파일 형식이 지원되지 않음

**해결:**
1. 파일 경로 확인
2. 파일 크기 확인 (최대 50MB)
3. 지원되는 파일 형식 사용

---

## 📊 TelegramNotifier 주요 메서드

### 텍스트 메시지
```python
await telegram_notifier.send_message(
    text="메시지 내용",
    parse_mode="HTML",  # 또는 "Markdown"
    disable_notification=False,
)
```

### 파일 전송
```python
await telegram_notifier.send_file(
    file_path="path/to/file.pdf",
    caption="파일 설명",
    disable_notification=False,
)
```

### 트레이딩 시그널
```python
await telegram_notifier.send_trade_signal(
    ticker="AAPL",
    action="BUY",  # 또는 "SELL", "HOLD"
    conviction=0.85,
    reasoning="매매 근거",
    target_price=195.0,
    stop_loss=175.0,
    position_size=5.0,
    current_price=182.5,
)
```

### 리스크 알림
```python
await telegram_notifier.send_risk_alert(
    ticker="AAPL",
    risk_type="MARKET",
    risk_score=0.5,
    risk_factors=["리스크 요인 1", "리스크 요인 2"],
    action_taken="취한 조치",
)
```

### 일일 리포트
```python
await telegram_notifier.send_daily_report(
    portfolio_value=125000.50,
    daily_pnl=2500.75,
    daily_pnl_pct=2.04,
    total_return_pct=15.5,
    positions=[...],
    cash=20000.0,
    trades_today=5,
)
```

### 시스템 알림
```python
from backend.notifications.telegram_notifier import AlertType

await telegram_notifier.send_system_alert(
    alert_type=AlertType.HIGH,  # 또는 CRITICAL, MEDIUM, LOW, SUCCESS
    title="알림 제목",
    message="알림 내용",
    action_required="필요한 조치",
)
```

---

## 📞 추가 지원

- **Telegram Bot API 문서**: https://core.telegram.org/bots/api
- **@BotFather**: https://t.me/BotFather
- **Telegram Bot API Group**: https://t.me/BotTalk

---

## 📝 요약

1. **환경 설정**: `.env` 파일에 이미 설정 완료
2. **TelegramNotifier**: 기본 알림 시스템 사용
3. **TelegramCommandBot**: 명령어 봇 사용
4. **테스트**: `test_telegram.py` 또는 `test_pdf_send.py` 실행
5. **실제 사용**: 위 예시 코드 참조

✅ 이제 텔레그램 봇을 사용하여 AI Trading System의 알림을 받을 수 있습니다!
