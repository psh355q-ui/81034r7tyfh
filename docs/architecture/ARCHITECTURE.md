# System Architecture

**AI Constitutional Trading System**

---

## 🏗️ Overall Architecture

### 3-Branch Separation of Powers

Constitutional AI Trading System은 정치학의 **삼권분립** 원칙을 차용합니다.

```
┌─────────────────────────────────────────────────────────┐
│                    CONSTITUTION (헌법)                    │
│             ─────────────────────────────────            │
│         Pure Python | SHA256 Integrity Check            │
│           AI Cannot Modify | Human-Approved              │
│                                                           │
│  • RiskLimits (최대 손실, 포지션 제한)                      │
│  • AllocationRules (자산 배분 규칙)                        │
│  • TradingConstraints (거래 제약)                          │
│  • Circuit Breaker (강제 개입)                             │
└─────────────────────────────────────────────────────────┘
                         ▼ validates
┌─────────────────────────────────────────────────────────┐
│                  INTELLIGENCE (지성부)                    │
│             ─────────────────────────────────            │
│           Multi-Agent Debate | Consensus                │
│                                                           │
│  🧑‍💻 Trader    →  "BUY 추천" (85% 신뢰)                    │
│  👮 Risk       →  "HOLD 경고" (VIX 22)                    │
│  🕵️ Analyst   →  "BUY 펀더멘털 양호"                       │
│  🌍 Macro      →  "BUY RISK_ON"                          │
│  🏛️ Institutional → "BUY 기관 매수"                        │
│         ↓                                                 │
│  🤵 PM (중재자) → "합의: 4/5 BUY" → Proposal 생성          │
└─────────────────────────────────────────────────────────┘
                         ▼ proposes
┌─────────────────────────────────────────────────────────┐
│                   EXECUTION (실행부)                      │
│             ─────────────────────────────────            │
│         Commander Approval | Telegram Integration       │
│                                                           │
│  1. Proposal 생성                                          │
│  2. Telegram 알림 → Commander                             │
│  3. [승인] or [거부] 버튼                                   │
│       ↓ APPROVE          ↓ REJECT                        │
│  4. Order Execution   Shadow Trade (가상 추적)             │
└─────────────────────────────────────────────────────────┘
```

---

## 🧩 Core Components

### 1. Constitution Layer

**Path**: `backend/constitution/`

**Files**:
- `risk_limits.py` - 리스크 제한
- `allocation_rules.py` - 자산 배분 규칙
- `trading_constraints.py` - 거래 제약
- `constitution.py` - 통합 검증
- `check_integrity.py` - SHA256 무결성 검사

**Characteristics**:
- ✅ Pure Python (No AI dependencies)
- ✅ Immutable (SHA256 hash verification)
- ✅ Human-only modification
- ✅ Auto-verification on import

**Code Example**:

```python
from backend.constitution import Constitution

constitution = Constitution()

proposal = {
    'ticker': 'AAPL',
    'action': 'BUY',
    'position_value': 15000,
    'order_value_usd': 15000
}

context = {
    'total_capital': 100000,
    'current_allocation': {'stock': 0.75, 'cash': 0.25},
    'market_regime': 'risk_on'
}

is_valid, violations, violated_articles = constitution.validate_proposal(
    proposal, context
)

if not is_valid:
    print(f"헌법 위반: {violations}")
    print(f"위반 조항: {violated_articles}")
```

---

### 2. Intelligence Layer

**Path**: `backend/ai/debate/`

**Components**:

#### A. AIDebateEngine

5개 AI Agents의 독립적 분석 + 토론

```python
from backend.ai.debate.ai_debate_engine import AIDebateEngine

engine = AIDebateEngine(
    enable_skeptic=True,
    enable_institutional=True
)

result = engine.debate_investment_decision(
    news_item=news,
    market_context=context
)

print(f"Final Signal: {result.final_signal.action}")
print(f"Consensus: {result.consensus_confidence:.0%}")
```

#### B. ConstitutionalDebateEngine

AIDebateEngine + Constitution 통합

```python
from backend.ai.debate.constitutional_debate_engine import ConstitutionalDebateEngine

engine = ConstitutionalDebateEngine(
    db_session=db,
    strict_mode=True
)

debate_result, is_constitutional, violations = engine.debate_and_validate(
    news_item=news,
    market_context=context,
    portfolio_state=portfolio
)

if is_constitutional:
    print("✅ 헌법 준수")
else:
    print(f"❌ 헌법 위반: {violations}")
    # Shadow Trade 자동 생성됨
```

---

### 3. Execution Layer

**Path**: `backend/notifications/`, `backend/data/models/`

**Components**:

#### A. Proposal System

```python
from backend.data.models.proposal import Proposal

proposal = Proposal(
    ticker='AAPL',
    action='BUY',
    target_price=195.50,
    is_constitutional=True,
    status='PENDING'
)

# Commander 승인
proposal.approve(approved_by="commander_username")

# 또는 거부
proposal.reject(reason="헌법 위반", rejected_by="commander")
```

#### B. Telegram Commander Bot

```python
from backend.notifications.telegram_commander_bot import TelegramCommanderBot

bot = TelegramCommanderBot(
    bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
    db_session=db,
    commander_chat_id=os.getenv('TELEGRAM_COMMANDER_CHAT_ID')
)

# 제안 전송 (버튼 포함)
await bot.send_proposal(proposal)

# 사용자가 버튼 클릭
# → handle_approval() 호출
# → Proposal 상태 업데이트
```

---

## 🛡️ Defensive Systems

### 1. Shadow Trade Tracker

**Path**: `backend/backtest/shadow_trade_tracker.py`

**Purpose**: 거부된 제안의 "방어 가치" 측정

```python
from backend.backtest.shadow_trade_tracker import ShadowTradeTracker

tracker = ShadowTradeTracker(db_session=db, yahoo_client=yahoo)

# 거부된 제안 추적
shadow = tracker.create_shadow_trade(
    proposal={'ticker': 'AAPL', 'action': 'BUY', 'entry_price': 195.50},
    rejection_reason="헌법 위반",
    violated_articles=["제3조"],
    tracking_days=7
)

# 7일 후
tracker.update_shadow_trade(shadow.id)

if shadow.status == 'DEFENSIVE_WIN':
    print(f"방어 성공! 손실 ${abs(shadow.virtual_pnl):,.0f} 회피")
```

**Workflow**:

```
AI 제안 → 헌법 검증 → 위반 감지
    ↓
Shadow Trade 생성 (entry_price 기록)
    ↓
7일간 가상 추적 (Yahoo Finance)
    ↓
exit_price 갱신 → virtual_pnl 계산
    ↓
DEFENSIVE_WIN (손실 회피) or MISSED_OPPORTUNITY
```

---

### 2. Shield Report

**Path**: `backend/reporting/shield_report_generator.py`

**Purpose**: 방어 성과 시각화

```python
from backend.reporting.shield_report_generator import ShieldReportGenerator

generator = ShieldReportGenerator(shadow_tracker=tracker)

report = generator.generate_shield_report(
    period_days=7,
    initial_capital=10_000_000,
    final_capital=9_985_000
)

# Telegram 전송
message = generator.format_telegram_message(report)
await telegram_bot.send_message(message)
```

**KPIs**:
- 자본 보존율 (Capital Preservation Rate)
- 방어한 손실 (Avoided Loss)
- 스트레스 감소 (Volatility Reduction)
- Drawdown 보호율

---

## 📊 Data Flow

### Complete Workflow

```
1. News/Signal Input
   ↓
2. AI Debate Engine
   └─→ 5 Agents analyze independently
   └─→ PM synthesizes consensus
   └─→ Creates Proposal
   ↓
3. Constitutional Validation
   └─→ validate_proposal()
   └─→ Check Circuit Breaker
        ├─→ PASS → Continue
        └─→ FAIL → Reject + Shadow Trade
   ↓
4. Proposal to DB
   └─→ INSERT INTO proposals
   └─→ status = 'PENDING'
   ↓
5. Telegram Notification
   └─→ Send to Commander
   └─→ Display [승인]/[거부] buttons
   ↓
6. Commander Decision
   ├─→ APPROVE
   │   ├─→ status = 'APPROVED'
   │   └─→ Execute Order
   │
   └─→ REJECT
       ├─→ status = 'REJECTED'
       └─→ Create Shadow Trade
           └─→ Track for 7 days
               └─→ Calculate avoided loss
   ↓
7. Shield Report
   └─→ Aggregate defensive performance
   └─→ Send weekly summary
```

---

## 🗄️ Database Schema

### Tables

#### 1. `proposals`

```sql
CREATE TABLE proposals (
    id UUID PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    target_price FLOAT NOT NULL,
    
    -- AI Analysis
    confidence FLOAT,
    consensus_level FLOAT,
    debate_summary TEXT,
    model_votes JSONB,
    
    -- Constitutional
    is_constitutional BOOLEAN DEFAULT FALSE,
    violated_articles TEXT,
    
    -- Approval
    status VARCHAR(20) DEFAULT 'PENDING',
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    rejection_reason VARCHAR(200),
    
    -- Telegram
    telegram_message_id VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. `shadow_trades`

```sql
CREATE TABLE shadow_trades (
    id UUID PRIMARY KEY,
    proposal_id UUID,
    ticker VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    
    -- Prices
    entry_price FLOAT NOT NULL,
    exit_price FLOAT,
    
    -- Virtual P&L
    virtual_pnl FLOAT DEFAULT 0.0,
    virtual_pnl_pct FLOAT DEFAULT 0.0,
    
    -- Rejection
    rejection_reason VARCHAR(200),
    violated_articles TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'TRACKING',
    tracking_days INTEGER DEFAULT 7,
    
    created_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP
);
```

---

## 🎨 Frontend Architecture

### War Room UI

**Path**: `frontend/src/components/war-room/`

**Tech Stack**:
- React + TypeScript
- CSS with animations
- Real-time updates (WebSocket planned)

**Components**:

```tsx
<WarRoom>
  <WarRoomHeader>
    <ConsensusMeter />
  </WarRoomHeader>
  
  <DebateMessages>
    {agents.map(agent => (
      <Message
        agent={agent}
        action={agent.action}
        confidence={agent.confidence}
        reasoning={agent.reasoning}
      />
    ))}
    
    <ConstitutionalResult
      isValid={result.isValid}
      violations={result.violations}
    />
  </DebateMessages>
  
  <WarRoomFooter>
    <Statistics />
  </WarRoomFooter>
</WarRoom>
```

---

## 🔒 Security & Integrity

### 1. Constitution Immutability

SHA256 hash verification on startup:

```python
# backend/constitution/__init__.py

from .check_integrity import verify_on_startup

# Auto-verify on import
is_valid = verify_on_startup()

if not is_valid:
    raise SystemFreeze("헌법 파일이 변조되었습니다!")
```

### 2. Human-in-the-Loop

All trades require explicit human approval:

```python
# backend/constitution/trading_constraints.py

REQUIRE_HUMAN_APPROVAL = True  # 헌법 제3조

# AI cannot change this
```

### 3. Circuit Breaker

Automatic trading halt on dangerous conditions:

```python
should_trigger, reason = constitution.validate_circuit_breaker_trigger(
    daily_loss=-0.04,  # -4%
    total_drawdown=-0.08,
    vix=25
)

if should_trigger:
    # 거래 즉시 중단
    # Commander에게 긴급 알림
    raise CircuitBreakerTriggered(reason)
```

---

## 📈 Scaling & Performance

### Current Capacity

- AI Debate: ~5-10 seconds per decision
- Constitutional Validation: <100ms
- Shadow Trade Updates: Batch processing (daily)
- Telegram Response: <1 second

### Future Optimizations

1. **Parallel Agent Execution**
   - Currently: Sequential
   - Future: Async parallel (3-5x faster)

2. **Caching Layer**
   - Redis for market data
   - Reduce API calls

3. **Horizontal Scaling**
   - Multiple Commander instances
   - Load balancer for API

---

## 🧪 Testing Architecture

### Test Levels

1. **Unit Tests**
   - Constitution rules
   - Individual agents
   - Shadow Trade calculations

2. **Integration Tests**
   - `test_constitutional_system.py`
   - Full workflow validation

3. **Demo/E2E**
   - `demo_constitutional_workflow.py`
   - User-facing demonstration

---

## 📚 References

- [README.md](../README.md) - Project Overview
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - Database Configuration
- [251215_System_Redesign_Blueprint.md](00_Spec_Kit/251215_System_Redesign_Blueprint.md) - Original Design

---

**Last Updated**: 2025-12-15  
**Version**: 2.0.0 (Constitutional Release)
