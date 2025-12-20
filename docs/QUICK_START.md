# Quick Start Guide

**5분 안에 Constitutional AI Trading System 실행하기**

---

## 🚀 빠른 시작

### Step 1: Python 환경 확인

```bash
python --version
# Python 3.10 이상 필요
```

### Step 2: 프로젝트 클론

```bash
git clone https://github.com/yourusername/ai-trading-system.git
cd ai-trading-system
```

### Step 3: 의존성 설치

```bash
pip install -r requirements.txt
```

### Step 4: 데모 실행 🎯

#### Constitution 시스템 테스트

```bash
python test_constitutional_system.py
```

**예상 출력**:
```
============================================================
               🏛️ Constitutional System Test 🏛️
============================================================

=== 1. Constitution Integrity Test ===
✅ 헌법 무결성 검증 성공

=== 2. Constitution Validation Test ===
...
Total: 5/5 passed (100%)

🎉 All tests passed! Constitutional System is ready!
```

#### 전체 워크플로우 데모

```bash
python demo_constitutional_workflow.py
```

**예상 출력**:
```
============================================================
          🏛️ Constitutional AI Investment Committee 🏛️
============================================================

🎭 AI Debate Starting...
Agent Votes:
  [Trader      ] BUY  (85%)
  [Risk        ] HOLD (65%)
  [Analyst     ] BUY  (70%)
  [Macro       ] BUY  (75%)
  [Institutional] BUY  (80%)

Consensus: 4/5 (80%)

🏛️ Constitutional Validation
❌ FAIL (제3조 위반)

👤 Commander Decision
❌ REJECT (헌법 위반)

🛡️ Shadow Trade Created
  Tracking for 7 days...

📊 Shield Report
  자본 보존율: 99.85% (S등급)
```

---

## 🎓 다음 단계

### Option 1: 실제 시스템 구동 (DB 필요)

#### 1. PostgreSQL 설치 및 실행

**Windows**:
```bash
# PostgreSQL 다운로드: https://www.postgresql.org/download/windows/
# 설치 후:
net start postgresql-x64-14
```

**macOS**:
```bash
brew install postgresql
brew services start postgresql
```

**Linux**:
```bash
sudo apt-get install postgresql
sudo systemctl start postgresql
```

#### 2. 데이터베이스 생성

```bash
psql -U postgres

postgres=# CREATE DATABASE ai_trading;
postgres=# \q
```

#### 3. 환경 변수 설정

`.env` 파일 생성:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_trading

# API Keys (선택)
FRED_API_KEY=your_fred_api_key
# Yahoo Finance, SEC EDGAR는 API 키 불필요

# Telegram (선택 - Commander Mode용)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_COMMANDER_CHAT_ID=your_chat_id
```

#### 4. 마이그레이션 실행

```bash
cd backend
alembic upgrade head
```

**예상 출력**:
```
INFO  [alembic.runtime.migration] Running upgrade -> 251215_shadow_trades
INFO  [alembic.runtime.migration] Running upgrade 251215_shadow_trades -> 251215_proposals
```

#### 5. 백엔드 실행

```bash
cd backend
python main.py
```

---

### Option 2: 백테스트 실행

```bash
python -m backend.backtest.run_30day_backtest
```

**설정**:
- 초기 자본: ₩10,000,000
- 기간: 30일
- 전략: Macro Agent + Constitutional Rules

---

### Option 3: Frontend 실행 (War Room UI)

```bash
cd frontend
npm install
npm run dev
```

**브라우저**: http://localhost:3000

---

## 📱 Telegram Commander Mode 설정

### 1. Bot 생성

1. Telegram에서 @BotFather 찾기
2. `/newbot` 명령어
3. Bot 이름 입력
4. Token 받기 (예: `123456:ABC-DEF...`)

### 2. Chat ID 확인

1. Bot에게 메시지 보내기 (아무거나)
2. 브라우저에서:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
3. `chat.id` 찾기

### 3. .env에 추가

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_COMMANDER_CHAT_ID=987654321
```

### 4. 테스트

```python
import asyncio
from backend.notifications.telegram_commander_bot import TelegramCommanderBot

async def test():
    bot = TelegramCommanderBot(
        bot_token="YOUR_TOKEN",
        db_session=None,  # DB 선택
        commander_chat_id="YOUR_CHAT_ID"
    )
    
    # 테스트 메시지
    await bot.application.bot.send_message(
        chat_id="YOUR_CHAT_ID",
        text="✅ Bot 연결 성공!"
    )

asyncio.run(test())
```

---

## 🧪 주요 기능 테스트

### 1. Constitution 검증

```python
from backend.constitution import Constitution

const = Constitution()

proposal = {
    'ticker': 'AAPL',
    'action': 'BUY',
    'position_value': 25000,  # 25% (제한: 20%)
    'order_value_usd': 25000,
    'is_approved': False
}

context = {
    'total_capital': 100000,
    'current_allocation': {'stock': 0.7, 'cash': 0.3},
    'market_regime': 'risk_on',
    'daily_trades': 0,
    'weekly_trades': 0
}

is_valid, violations, articles = const.validate_proposal(proposal, context)

if not is_valid:
    print("헌법 위반!")
    print(f"사유: {violations}")
    print(f"조항: {articles}")
```

### 2. Shadow Trade 추적

```python
from backend.backtest.shadow_trade_tracker import ShadowTradeTracker
from backend.data.collectors.api_clients.yahoo_client import YahooFinanceClient

tracker = ShadowTradeTracker(
    db_session=db,
    yahoo_client=YahooFinanceClient()
)

# 거부된 제안 추적
shadow = tracker.create_shadow_trade(
    proposal={
        'ticker': 'AAPL',
        'action': 'BUY',
        'entry_price': 195.50,
        'shares': 100
    },
    rejection_reason="헌법 위반",
    violated_articles=["제3조"],
    tracking_days=7
)

print(f"Shadow Trade ID: {shadow.id}")
print(f"Status: {shadow.status}")
```

### 3. Shield Report 생성

```python
from backend.reporting.shield_report_generator import ShieldReportGenerator

generator = ShieldReportGenerator(shadow_tracker=tracker)

report = generator.generate_shield_report(
    period_days=7,
    initial_capital=10_000_000,
    final_capital=9_985_000
)

print(f"자본 보존율: {report['raw_metrics']['capital_preserved_rate']:.2f}%")
print(f"방어한 손실: ${report['raw_metrics']['total_avoided_loss']:,.0f}")
```

---

## 🎯 실전 워크플로우

### 월요일 아침

```bash
# 1. 시스템 시작
python backend/main.py

# 2. 주간 Shield Report 확인
python backend/reporting/generate_weekly_shield_report.py

# 3. Telegram 알림 대기
# Commander가 [승인]/[거부] 버튼 클릭
```

### 거래일 중

```bash
# AI가 뉴스 분석
# → Debate (5 agents)
# → Constitutional Validation
# → Telegram 알림
# → Commander 결정
```

### 주말

```bash
# Shadow Trade 업데이트 (거부된 제안 추적)
python backend/backtest/update_shadow_trades.py

# 주간 리포트 생성
python backend/reporting/generate_weekly_report.py
```

---

## 🚨 문제 해결

### ImportError: No module named 'backend'

```bash
# 프로젝트 루트에서 실행하세요
cd d:\code\ai-trading-system
python demo_constitutional_workflow.py
```

### PostgreSQL 연결 실패

```bash
# PostgreSQL 실행 확인
# Windows:
net start postgresql-x64-14

# macOS:
brew services list

# Linux:
sudo systemctl status postgresql
```

### Alembic 마이그레이션 오류

```bash
# 데이터베이스 초기화
cd backend
alembic stamp head
alembic upgrade head
```

### Telegram Bot 응답 없음

1. Bot Token 확인
2. Chat ID 확인
3. Bot이 권한을 가지고 있는지 확인

---

## 📖 다음 읽을 문서

- [Architecture](docs/ARCHITECTURE.md) - 시스템 구조 상세
- [Database Setup](docs/DATABASE_SETUP.md) - DB 설정 가이드
- [Commander Mode](docs/COMMANDER_MODE.md) - Telegram 사용법
- [War Room](docs/WAR_ROOM.md) - AI 토론 UI

---

## 💡 팁

### 1. 개발 모드

Constitution 해시 검증 스킵:

```python
# backend/constitution/check_integrity.py
DEV_MODE = True  # 개발 중에만
```

### 2. 로깅 레벨 조정

```python
# backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)  # 상세 로그
```

### 3. 빠른 테스트

```bash
# Constitution만 테스트
python -c "from backend.constitution import Constitution; print('OK')"

# Shadow Trade만 테스트
python backend/backtest/shadow_trade_tracker.py
```

---

## 🎉 성공 확인

시스템이 정상 작동하면:

1. ✅ Constitution Test 통과 (5/5)
2. ✅ Demo Workflow 실행 완료
3. ✅ DB 테이블 생성 (`proposals`, `shadow_trades`)
4. ✅ Telegram Bot 응답

**축하합니다! Constitutional AI Trading System이 준비되었습니다.** 🏛️

---

**작성일**: 2025-12-15  
**예상 소요 시간**: 5-15분
