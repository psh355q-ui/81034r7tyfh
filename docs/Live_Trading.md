## Live Trading Engine - Real Broker Integration

AI Trading System with real broker execution via Korea Investment & Securities API.

---

## Overview

The **Live Trading Engine** connects AI-driven trading decisions to real broker accounts through the KIS Open Trading API.

**Key Features**:
- AI Trading Agent integration
- Real broker execution (KIS API)
- Multiple trading modes (Dry-run, Paper, Live)
- Safety checks and confirmations
- Kill switch integration
- Telegram notifications

---

## Architecture

```
┌─────────────────┐
│ Trading Agent   │ ← AI decision making
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Live Trading    │ ← Orchestration + Safety
│ Engine          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ KIS Broker      │ ← Real broker execution
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Korea Investment│ ← Real market
│ & Securities    │
└─────────────────┘
```

**Data Flow**:
1. **Market Data**: KIS Broker → Real-time quotes
2. **AI Analysis**: Trading Agent → Decision (BUY/SELL/HOLD)
3. **Safety Checks**: Live Trading Engine → Validate limits
4. **Execution**: KIS Broker → Place order
5. **Notification**: Telegram → Alert user

---

## Trading Modes

### 1. Dry Run Mode (Recommended for Testing)

**Purpose**: Test the system without any real execution.

**Behavior**:
- Fetches real market data
- AI makes real decisions
- Logs execution plans
- **NO actual orders placed**

**Use Case**: Testing new strategies, debugging, system validation

```bash
python run_live_trading.py --mode dry_run --account 12345678
```

### 2. Paper Trading Mode (Virtual Money)

**Purpose**: Simulate trading with virtual account.

**Behavior**:
- Fetches real market data
- AI makes real decisions
- Executes orders in KIS virtual trading account
- Uses virtual money (모의투자)

**Use Case**: Strategy validation before real trading

```bash
python run_live_trading.py --mode paper --account 12345678
```

### 3. Live Trading Mode (Real Money)

**Purpose**: Execute real trades with real money.

**Behavior**:
- Fetches real market data
- AI makes real decisions
- Executes orders in KIS real trading account
- **USES REAL MONEY**

**Use Case**: Production trading (use with extreme caution!)

```bash
# Requires confirmation
python run_live_trading.py --mode live --account 12345678
```

---

## Configuration

### Required Setup

**1. KIS API Setup**

Follow [KIS_Integration.md](./KIS_Integration.md) for:
- Account setup
- API key generation
- Configuration file (`~/KIS/config/kis_devlp.yaml`)

**2. Environment Variables**

`.env` file should contain:
```bash
# KIS API
KIS_ACCOUNT_NUMBER=12345678
KIS_PRODUCT_CODE=01

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ENABLED=true
```

**3. AI Trading Agent**

Ensure AI components are configured:
- Claude API key
- Feature Store database
- Redis cache

---

## Usage

### Basic Usage

```bash
# Dry run with default tickers
python run_live_trading.py --mode dry_run --account 12345678

# Paper trading with custom tickers
python run_live_trading.py \
    --mode paper \
    --account 12345678 \
    --tickers AAPL NVDA TSLA

# Paper trading with faster interval (1 minute)
python run_live_trading.py \
    --mode paper \
    --account 12345678 \
    --interval 60
```

### Advanced Options

```bash
python run_live_trading.py \
    --mode paper \
    --account 12345678 \
    --tickers AAPL NVDA MSFT GOOGL TSLA AMZN META \
    --interval 300 \
    --max-positions 10 \
    --max-position-size 10000 \
    --max-daily-trades 20 \
    --log-level INFO
```

**Parameters**:
- `--mode`: Trading mode (`dry_run`, `paper`, `live`)
- `--account`: KIS account number (8 digits)
- `--tickers`: List of stock symbols to trade
- `--interval`: Decision interval in seconds (default: 300)
- `--max-positions`: Maximum number of positions (default: 10)
- `--max-position-size`: Max position size in USD (default: 10000)
- `--max-daily-trades`: Max trades per day (default: 20)
- `--no-confirm`: Disable confirmation prompts (USE WITH CAUTION)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

---

## Safety Features

### 1. Position Size Limits

**Purpose**: Prevent oversized positions

**Configuration**:
```python
config = LiveTradingConfig(
    max_position_size_usd=10000.0,  # Max $10k per position
)
```

**Behavior**:
- AI suggests position size (e.g., 5% of portfolio)
- Engine caps at `max_position_size_usd`
- Logs warning if capped

### 2. Daily Trade Limit

**Purpose**: Prevent overtrading

**Configuration**:
```python
config = LiveTradingConfig(
    max_daily_trades=20,  # Max 20 trades per day
)
```

**Behavior**:
- Tracks trades per day
- Rejects new trades after limit reached
- Resets at midnight

### 3. Kill Switch

**Purpose**: Emergency stop on large losses

**Configuration**:
```python
config = LiveTradingConfig(
    max_daily_loss_pct=2.0,  # -2% daily loss triggers kill switch
)
```

**Behavior**:
- Monitors daily P&L
- Activates kill switch if loss exceeds threshold
- Pauses all trading until manually deactivated

**Manual Activation**:
```python
engine.activate_kill_switch("Manual override")
```

**Manual Deactivation**:
```python
engine.deactivate_kill_switch()
```

### 4. Confirmation Prompts

**Purpose**: Manual approval for live trades

**Configuration**:
```python
config = LiveTradingConfig(
    require_confirmation=True,  # Enabled for LIVE mode
)
```

**Behavior**:
- Displays execution plan
- Waits for user confirmation
- Skips if user declines

**Example**:
```
============================================================
EXECUTION PLAN
============================================================
Action: BUY
Ticker: AAPL
Shares: 10
Price: $273.20
Total Value: $2,732.00
Conviction: 0.85
Mode: LIVE
============================================================

Execute this trade? (yes/no): yes
```

### 5. Trading Hours Check

**Purpose**: Prevent trading outside market hours

**Configuration**:
```python
config = LiveTradingConfig(
    trading_start_hour=9,   # 9 AM ET
    trading_end_hour=16,    # 4 PM ET
)
```

**Behavior**:
- Checks if current time is within trading hours
- Pauses trading outside hours
- Resumes automatically when market opens

---

## Decision Flow

### Step 1: Market Data

```python
# Get current price
price_data = broker.get_price("AAPL")
# → {"current_price": 273.20, "change": 2.50, ...}

# Get account balance
balance = broker.get_account_balance()
# → {"total_value": 100000, "cash": 50000, "positions": [...]}
```

### Step 2: AI Analysis

```python
# AI analyzes stock
decision = await agent.analyze(
    ticker="AAPL",
    market_context=None,
    portfolio_context=balance,
)
# → TradingDecision(action="BUY", conviction=0.85, position_size=5.0)
```

### Step 3: Safety Checks

```python
# Check daily trade limit
if daily_trades >= max_daily_trades:
    reject()

# Check position size
if position_value > max_position_size_usd:
    cap_position_size()

# Check kill switch
if kill_switch_active:
    pause()
```

### Step 4: Execution

```python
# Execute order
if mode == DRY_RUN:
    log_only()
elif mode == PAPER:
    broker.buy_market_order(symbol, shares)  # Virtual account
elif mode == LIVE:
    confirm_with_user()
    broker.buy_market_order(symbol, shares)  # Real account
```

### Step 5: Notification

```python
# Send Telegram alert
await notifier.send_execution_report(
    ticker="AAPL",
    side="BUY",
    quantity=10,
    avg_price=273.20,
    total_value=2732.00,
)
```

---

## Example Session

### Dry Run Mode

```bash
$ python run_live_trading.py --mode dry_run --account 12345678 --tickers AAPL NVDA

================================================================================
LIVE TRADING ENGINE STARTED
================================================================================
Mode: DRY_RUN
Account: 12345678
Tickers: AAPL, NVDA
Max Daily Trades: 20
Max Position Size: $10,000.00
Kill Switch Threshold: -2.0%
================================================================================

============================================================
Processing AAPL
============================================================
Current price: $273.20
Account value: $100,000.00
Cash: $50,000.00
Positions: 0

Decision: BUY
Conviction: 0.85
Position Size: 5.0%
Reasoning: Strong momentum + positive AI factors

============================================================
EXECUTION PLAN
============================================================
Action: BUY
Ticker: AAPL
Shares: 18
Price: $273.20
Total Value: $4,917.60
Conviction: 0.85
Mode: DRY_RUN
============================================================

[DRY RUN] Would have executed trade (no actual execution)

============================================================
Processing NVDA
============================================================
...
```

### Paper Trading Mode

```bash
$ python run_live_trading.py --mode paper --account 12345678

# Same as dry run, but actually executes orders in virtual account

OK: Order executed - SUBMITTED
```

---

## Monitoring

### Session Metrics

The engine logs metrics every decision cycle:

```
============================================================
SESSION METRICS
============================================================
Runtime: 0:15:32
Total Decisions: 15
Total Executions: 8
  BUY: 5
  SELL: 3
  HOLD: 7
Rejected: 2
Errors: 0
Daily Trades: 8/20
============================================================
```

### Executed Trades Log

At shutdown, the engine logs all executed trades:

```
Executed Trades:
  10:30:15 | BUY  10 AAPL  @ $273.20 = $2,732.00
  10:35:20 | BUY   5 NVDA  @ $186.69 = $933.45
  10:40:25 | SELL  3 MSFT  @ $425.00 = $1,275.00
```

### Telegram Notifications

Real-time alerts via Telegram:
- **Startup Message**: Engine started
- **Execution Reports**: Trade executed
- **Risk Alerts**: Kill switch activated
- **Daily Reports**: End-of-day summary

---

## Integration with Paper Trading

You can run both systems simultaneously:

```bash
# Terminal 1: Paper Trading (simulation)
python run_paper_trading.py

# Terminal 2: Live Trading (real broker, dry run)
python run_live_trading.py --mode dry_run --account 12345678
```

**Use Case**: Compare AI decisions in simulation vs. real broker environment

---

## Troubleshooting

### Issue 1: KIS Authentication Failed

```
ERROR: KIS authentication failed
```

**Solution**:
1. Check `~/KIS/config/kis_devlp.yaml` exists
2. Verify APP KEY and APP SECRET are correct
3. Ensure virtual trading account is activated

### Issue 2: No Price Data

```
WARNING: No price data for AAPL - skipping
```

**Solution**:
1. Check internet connection
2. Verify KIS API is accessible
3. Try different ticker symbol

### Issue 3: Daily Trade Limit Reached

```
WARNING: Daily trade limit reached (20) - skipping execution
```

**Solution**:
- Wait until next day (resets at midnight)
- Increase `--max-daily-trades` if appropriate

### Issue 4: AI Analysis Failed

```
ERROR: AI analysis failed for AAPL: Feature Store unavailable
```

**Solution**:
1. Check Redis is running
2. Verify TimescaleDB is accessible
3. Ensure Claude API key is valid

### Issue 5: KIS API Rate Limit Exceeded

```
ERROR: API call failed - rate limit exceeded
```

**Solution**:

**Rate Limits (한국투자증권 공식)**:
- **실전투자**: 1초당 20건 (계좌 단위)
- **모의투자**: 1초당 2건 (계좌 단위)
- **토큰 발급**: 1초당 1건

**권장 설정 - 실전투자**:
```bash
python run_live_trading.py \
    --mode live \
    --account 12345678 \
    --interval 300 \
    --tickers AAPL NVDA MSFT GOOGL AMZN  # 최대 5종목
```

**권장 설정 - 모의투자**:
```bash
python run_live_trading.py \
    --mode paper \
    --account 12345678 \
    --interval 600 \
    --tickers AAPL NVDA  # 최대 2종목
```

**API 호출 최적화**:
1. `decision_interval_seconds` 증가 (300초 이상)
2. 동시 분석 종목 수 감소
3. 가격 조회 캐싱 활용
4. 계좌 잔고 조회 최소화

**유량 확대 방법**:
- 유량 제한은 계좌(앱키) 단위
- 추가 계좌로 API 신청하여 새 앱키 발급
- 여러 앱키로 분산 처리

---

## Best Practices

### 1. Start with Dry Run

Always test new strategies in dry run mode:
```bash
python run_live_trading.py --mode dry_run --account 12345678
```

### 2. Validate with Paper Trading

After dry run, use paper trading for at least 1 week:
```bash
python run_live_trading.py --mode paper --account 12345678
```

### 3. Set Conservative Limits

Start with small position sizes:
```bash
python run_live_trading.py \
    --mode paper \
    --account 12345678 \
    --max-position-size 1000 \
    --max-daily-trades 5
```

### 4. Monitor Continuously

- Check logs regularly
- Monitor Telegram notifications
- Review daily metrics

### 5. Use Kill Switch

Set aggressive kill switch threshold initially:
```python
config = LiveTradingConfig(
    max_daily_loss_pct=1.0,  # -1% daily loss
)
```

---

## Checklist Before Live Trading

Before switching to `--mode live`:

- [ ] Tested in dry run mode for at least 3 days
- [ ] Validated in paper trading for at least 1 week
- [ ] AI strategy backtesting completed successfully
- [ ] Risk management rules configured (stop loss, position limits)
- [ ] Telegram notifications tested and working
- [ ] Kill switch tested and verified
- [ ] Trading capital allocated (only use money you can afford to lose)
- [ ] Emotional discipline prepared (stick to the system)
- [ ] Monitoring plan in place (check logs daily)

---

## API Reference

### LiveTradingEngine

```python
from live_trading_engine import LiveTradingEngine, LiveTradingConfig, TradingMode

# Configuration
config = LiveTradingConfig(
    kis_account_no="12345678",
    mode=TradingMode.PAPER,
    tickers=["AAPL", "NVDA"],
    decision_interval_seconds=300,
    max_positions=10,
    max_position_size_usd=10000.0,
    max_daily_trades=20,
    max_daily_loss_pct=2.0,
    require_confirmation=True,
    enable_notifications=True,
)

# Create engine
engine = LiveTradingEngine(config=config)

# Start trading
await engine.start()

# Activate kill switch
engine.activate_kill_switch("Manual override")

# Deactivate kill switch
engine.deactivate_kill_switch()

# Get metrics
metrics = engine.get_metrics()

# Stop engine
await engine.stop()
```

---

## FAQ

**Q: What's the difference between Paper Trading and Live Trading (paper mode)?**

A:
- **Paper Trading** (`run_paper_trading.py`): Internal simulation with yfinance data
- **Live Trading - Paper Mode** (`run_live_trading.py --mode paper`): Real KIS virtual trading account

Both use virtual money, but Live Trading uses the actual broker API.

**Q: How much money do I need to start?**

A:
- Paper/Dry Run: $0 (no real money)
- Live Trading: Minimum depends on position sizes. With `max_position_size_usd=1000` and `max_positions=10`, you need at least $10,000.

**Q: Can I run multiple instances?**

A: Not recommended. Running multiple instances with the same KIS account may cause conflicts.

**Q: What happens if the system crashes?**

A:
- Open orders may still execute
- No automatic cleanup
- Manually check account status via KIS website
- Resume trading after verifying state

**Q: Can I trade Korean stocks?**

A: Not yet. Currently only supports US stocks (NASDAQ, NYSE, AMEX). Korean stock support is planned.

---

## Support

- **Documentation**: [docs/](./README.md)
- **KIS API Issues**: [KIS Developers](https://apiportal.koreainvestment.com/)
- **GitHub Issues**: [Report a bug](https://github.com/your-repo/issues)

---

**Disclaimer**: This system is for educational purposes only. Trading involves risk. Past performance does not guarantee future results. Only trade with money you can afford to lose.

---

*Generated by AI Trading System Team*
*Date: 2025-11-15*
