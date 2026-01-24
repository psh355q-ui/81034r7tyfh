# 텔레그램 봇 설정 가이드

이 가이드는 AI Trading System에서 텔레그램 봇을 설정하고 사용하는 방법을 안내합니다.

## 📋 목차

1. [Telegram Bot 생성](#1-telegram-bot-생성)
2. [Chat ID 얻기](#2-chat-id-얻기)
3. [TelegramNotifier 설정](#3-telegramnotifier-설정)
4. [TelegramCommandBot 설정](#4-telegramcommandbot-설정)
5. [사용 예시](#5-사용-예시)
6. [테스트 방법](#6-테스트-방법)

---

## 1. Telegram Bot 생성

### 1.1 @BotFather와 대화 시작

1. Telegram 앱에서 [`@BotFather`](https://t.me/BotFather)를 검색하여 대화 시작
2. `/newbot` 명령어 입력

```
/newbot
```

### 1.2 Bot 이름 설정

BotFather가 요청할 때 다음 정보를 입력:

1. **Bot 이름** (사용자에게 표시되는 이름)
   ```
   예: AI Trading System Bot
   ```

2. **Bot 사용자명** (반드시 `bot`으로 끝나야 함)
   ```
   예: ai_trading_system_bot
   ```

### 1.3 Bot Token 저장

BotFather가 제공하는 **API Token**을 안전하게 저장:

```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

⚠️ **중요**: 이 토큰은 비밀번호와 같으므로 절대 공개하지 마세요!

---

## 2. Chat ID 얻기

### 2.1 개인 Chat ID 얻기

1. Telegram 앱에서 [`@userinfobot`](https://t.me/userinfobot) 또는 [`@myidbot`](https://t.me/myidbot)를 검색하여 대화 시작
2. `/start` 명령어 입력
3. Bot이 당신의 **Chat ID**를 반환

```
예: 123456789
```

### 2.2 그룹/채널 Chat ID 얻기

1. Bot을 그룹/채널에 초대
2. 그룹/채널에서 메시지 전송
3. 다음 API 호출로 Chat ID 확인:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

응답에서 `chat` 객체의 `id` 값이 Chat ID입니다:

```json
{
  "message": {
    "chat": {
      "id": -1001234567890,
      "title": "AI Trading Alerts"
    }
  }
}
```

---

## 3. TelegramNotifier 설정

### 3.1 환경 변수 설정

`.env` 파일 또는 환경 변수에 다음을 추가:

```bash
# Telegram Bot 설정
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### 3.2 TelegramNotifier 초기화

```python
import os
from backend.notifications.telegram_notifier import TelegramNotifier

# 환경 변수에서 설정 로드
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

# TelegramNotifier 초기화
telegram_notifier = TelegramNotifier(
    bot_token=bot_token,
    chat_id=chat_id,
    enabled=True,
    rate_limit_per_minute=20,
    min_priority=None,  # 모든 우선순위 전송
    throttle_minutes=5,
)
```

### 3.3 기본 메시지 전송

```python
import asyncio

async def send_test_message():
    # 텍스트 메시지 전송
    success = await telegram_notifier.send_message(
        text="🚀 텔레그램 봇 테스트 메시지!",
        parse_mode="HTML",
        disable_notification=False,
    )
    
    if success:
        print("✅ 메시지 전송 성공!")
    else:
        print("❌ 메시지 전송 실패!")

# 실행
asyncio.run(send_test_message())
```

### 3.4 파일 전송

```python
async def send_test_file():
    # 파일 전송
    success = await telegram_notifier.send_file(
        file_path="path/to/file.txt",
        caption="📄 테스트 파일입니다.",
        disable_notification=False,
    )
    
    if success:
        print("✅ 파일 전송 성공!")
    else:
        print("❌ 파일 전송 실패!")

# 실행
asyncio.run(send_test_file())
```

---

## 4. TelegramCommandBot 설정

### 4.1 TelegramCommandBot 초기화

```python
import os
from backend.notifications.telegram_notifier import TelegramNotifier
from backend.notifications.telegram_command_bot import TelegramCommandBot
from backend.services.portfolio_analyzer import PortfolioAnalyzer
from backend.services.economic_calendar_manager import EconomicCalendarManager
from backend.brokers.kis_broker import KISBroker

# TelegramNotifier 초기화
telegram_notifier = TelegramNotifier(
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
    chat_id=os.getenv("TELEGRAM_CHAT_ID"),
    enabled=True,
)

# KIS Broker 초기화
kis_broker = KISBroker()

# PortfolioAnalyzer 초기화
portfolio_analyzer = PortfolioAnalyzer(
    kis_broker=kis_broker,
    telegram_notifier=telegram_notifier,
)

# EconomicCalendarManager 초기화
economic_calendar_manager = EconomicCalendarManager(
    telegram_notifier=telegram_notifier,
)

# TelegramCommandBot 초기화
command_bot = TelegramCommandBot(
    telegram_notifier=telegram_notifier,
    portfolio_analyzer=portfolio_analyzer,
    economic_calendar_manager=economic_calendar_manager,
)
```

### 4.2 명령어 처리

```python
async def handle_commands():
    # /status 명령어
    response = await command_bot.handle_command("/status")
    print(response)

    # /portfolio 명령어
    response = await command_bot.handle_command("/portfolio")
    print(response)

    # /schedule 명령어
    response = await command_bot.handle_command("/schedule")
    print(response)

    # /economic 명령어
    response = await command_bot.handle_command("/economic")
    print(response)

    # /help 명령어
    response = await command_bot.handle_command("/help")
    print(response)

# 실행
asyncio.run(handle_commands())
```

### 4.3 경제지표 알림 전송

```python
async def send_economic_alert():
    # 경제지표 이벤트 예시
    event = {
        "event_name": "Non-Farm Payrolls",
        "country": "US",
        "currency": "USD",
        "importance": "high",
        "actual": 200,
        "forecast": 180,
        "previous": 170,
        "timestamp": datetime.now(),
    }

    # Surprise 분석 예시
    analysis = {
        "surprise_pct": 11.11,  # (200 - 180) / 180 * 100
        "impact": "positive",    # "positive", "negative", "neutral"
        "interpretation": "고용 증가가 예상보다 높아 경제가 강력함을 보여줍니다.",
    }

    # 경제지표 알림 전송
    await command_bot.send_economic_alert(event, analysis)

# 실행
asyncio.run(send_economic_alert())
```

---

## 5. 사용 예시

### 5.1 트레이딩 시그널 알림

```python
async def send_trade_signal():
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

### 5.2 일일 리포트 전송

```python
async def send_daily_report():
    success = await telegram_notifier.send_daily_report(
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
    
    if success:
        print("✅ 일일 리포트 전송 성공!")

# 실행
asyncio.run(send_daily_report())
```

### 5.3 시스템 알림 전송

```python
from backend.notifications.telegram_notifier import AlertType

async def send_system_alert():
    success = await telegram_notifier.send_system_alert(
        alert_type=AlertType.CRITICAL,
        title="시스템 오류 발생",
        message="데이터베이스 연결 실패. 자동 재시도 중...",
        details={
            "error": "Connection timeout",
            "retry_count": 3,
            "last_attempt": datetime.now().isoformat(),
        },
    )
    
    if success:
        print("✅ 시스템 알림 전송 성공!")

# 실행
asyncio.run(send_system_alert())
```

---

## 6. 테스트 방법

### 6.1 간단한 테스트 스크립트

`test_telegram.py` 파일 생성:

```python
import asyncio
import os
from backend.notifications.telegram_notifier import TelegramNotifier
from backend.notifications.telegram_command_bot import TelegramCommandBot
from backend.services.portfolio_analyzer import PortfolioAnalyzer
from backend.services.economic_calendar_manager import EconomicCalendarManager
from backend.brokers.kis_broker import KISBroker

async def main():
    # TelegramNotifier 초기화
    telegram_notifier = TelegramNotifier(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        enabled=True,
    )

    # 테스트 1: 기본 메시지 전송
    print("[1] 기본 메시지 전송 테스트...")
    success = await telegram_notifier.send_message("🚀 텔레그램 봇 테스트 메시지!")
    print(f"결과: {'✅ 성공' if success else '❌ 실패'}\n")

    # 테스트 2: 파일 전송
    print("[2] 파일 전송 테스트...")
    test_file = "test_telegram.txt"
    with open(test_file, "w") as f:
        f.write("테스트 파일 내용입니다.")
    
    success = await telegram_notifier.send_file(
        file_path=test_file,
        caption="📄 테스트 파일입니다.",
    )
    print(f"결과: {'✅ 성공' if success else '❌ 실패'}\n")

    # 테스트 3: TelegramCommandBot 명령어 테스트
    print("[3] TelegramCommandBot 명령어 테스트...")
    command_bot = TelegramCommandBot(
        telegram_notifier=telegram_notifier,
        portfolio_analyzer=None,  # 테스트용으로 None
        economic_calendar_manager=None,  # 테스트용으로 None
    )

    commands = ["/status", "/schedule", "/help"]
    for cmd in commands:
        print(f"  {cmd} 명령어 테스트...")
        response = await command_bot.handle_command(cmd)
        print(f"  결과: {response[:100]}...\n")

    print("✅ 모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main())
```

### 6.2 테스트 실행

```bash
# 환경 변수 설정
export TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="123456789"

# 테스트 실행
python test_telegram.py
```

### 6.3 텔레그램에서 확인

1. Telegram 앱을 열고 봇과의 대화를 확인
2. 테스트 메시지가 정상적으로 수신되었는지 확인
3. 파일이 첨부되었는지 확인

---

## 🔧 문제 해결

### 문제 1: "Unauthorized" 오류

**원인**: Bot Token이 잘못되었거나 만료됨

**해결**:
1. @BotFather에서 새로운 Bot Token 발급
2. 환경 변수 업데이트
3. 애플리케이션 재시작

### 문제 2: "Bad Request: chat not found" 오류

**원인**: Chat ID가 잘못됨

**해결**:
1. @userinfobot 또는 @myidbot으로 Chat ID 재확인
2. Bot을 그룹/채널에 다시 초대
3. 환경 변수 업데이트

### 문제 3: 메시지가 도착하지 않음

**원인**:
- Bot이 차단됨
- 인터넷 연결 문제
- Rate Limit 초과

**해결**:
1. Bot이 차단되지 않았는지 확인
2. 인터넷 연결 확인
3. Rate Limit 준수 (분당 20개 메시지)

### 문제 4: 파일 전송 실패

**원인**:
- 파일이 존재하지 않음
- 파일 크기가 50MB 초과
- 파일 형식이 지원되지 않음

**해결**:
1. 파일 경로 확인
2. 파일 크기 확인 (최대 50MB)
3. 지원되는 파일 형식 사용

---

## 📞 추가 지원

- **Telegram Bot API 문서**: https://core.telegram.org/bots/api
- **@BotFather**: https://t.me/BotFather
- **Telegram Bot API Group**: https://t.me/BotTalk

---

## 📝 요약

1. **@BotFather**에서 Bot 생성 및 Token 획득
2. **@userinfobot** 또는 **@myidbot**으로 Chat ID 획득
3. 환경 변수 설정 (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`)
4. `TelegramNotifier` 초기화 및 메시지 전송
5. `TelegramCommandBot` 초기화 및 명령어 처리
6. 테스트 스크립트로 동작 확인

✅ 이제 텔레그램 봇을 사용하여 AI Trading System에서 알림을 받을 수 있습니다!
