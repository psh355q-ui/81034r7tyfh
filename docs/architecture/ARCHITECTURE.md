# AI Trading System - Architecture Overview

**Last Updated**: 2026-01-24  
**Version**: 2.3  
**Status**: Active Development

<!-- 
✅ 구현 완료 (2026-01-24)
- 전체 시스템 아키텍처 구현 완료
- Daily Briefing System v2.3 구현 완료
- MVP 3+1 Agent 구현 완료
- Market Intelligence 구현 완료
- Economic Watcher 구현 완료
- Multi-Strategy Orchestration 구현 완료
-->

## 🏛️ System Overview

AI Constitutional Trading System은 AI 멀티-에이전트 시스템과 헌법 기반 리스크 관리를 결합한 알고리즘 트레이딩 플랫폼입니다.

### Core Principles
1. **Constitutional Governance**: 모든 거래는 헌법(Constitution) 검증 통과 필수
2. **Multi-Agent Deliberation**: 5개 AI 에이전트의 토론 기반 의사결정
3. **Human-in-the-Loop**: 중요 결정은 Commander 승인 필수
4. **Risk-First Principle**: 리스크 관리가 수익보다 우선

---

## 📐 System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  CONSTITUTION (헌법)                     │
│          Pure Python | SHA256 Integrity Check           │
│        AI Cannot Modify | Human-Approved Only           │
└─────────────────────────────────────────────────────────┘
                          ▼ validates
┌─────────────────────────────────────────────────────────┐
│              INTELLIGENCE LAYER (지성부)                 │
│  • Daily Briefing System v2.3                           │
│  • Market Intelligence Engine                           │
│  • War Room MVP (Multi-Agent Debate)                    │
│  • News Processing Pipeline                             │
└─────────────────────────────────────────────────────────┘
                          ▼ proposes
┌─────────────────────────────────────────────────────────┐
│              EXECUTION LAYER (실행부)                    │
│  • Proposal System                                       │
│  • Telegram Commander Bot                               │
│  • Order Execution                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 🧩 Major Subsystems

### 1. Daily Briefing System v2.3

**Path**: `backend/ai/reporters/`

#### Evolution
- **v2.1**: 기본 리포트 생성
- **v2.2**: Enhanced 분석 추가
- **v2.3**: **"Reading Report" → "Executable Protocol" 전환** (2026-01-24 완료)

#### v2.3 Architecture

```
┌──────────────────────────────────┐
│   Briefing Mode System           │
│   (briefing_mode.py)             │
│   • CLOSING/MORNING/INTRADAY     │
│   • Time-based auto-detection    │
│   • Grammar/content validation   │
└──────────────────────────────────┘
          ▼
┌──────────────────────────────────┐
│   Prompt Builder                 │
│   (prompt_builder.py)            │
│   • Mode-specific prompts        │
│   • Dynamic generation           │
└──────────────────────────────────┘
          ▼
┌──────────────────────────────────┐
│   Market Moving Score            │
│   (market_moving_score.py)       │
│   • News filtering               │
│   • VIX-based thresholds         │
│   • Impact×0.5 + Spec×0.3 +     │
│     Reliability×0.2              │
└──────────────────────────────────┘
          ▼
┌──────────────────────────────────┐
│   Conflict Resolver              │
│   (conflict_resolver.py)         │
│   • Risk-First principle         │
│   • Size adjustment rules        │
│   • AUTO execution conditions    │
└──────────────────────────────────┘
          ▼
┌──────────────────────────────────┐
│   Funnel Generator               │
│   (funnel_generator.py)          │
│   • Market State (🟢🟡🔴)        │
│   • Actionable Scenarios         │
│   • Portfolio Impact             │
└──────────────────────────────────┘
          ▼
┌──────────────────────────────────┐
│   Trading Protocol               │
│   (trading_protocol.py)          │
│   • JSON-based executable        │
│   • Pydantic v2 schema           │
│   • JSONB storage                │
└──────────────────────────────────┘
```

#### Key Components

| Component | Path | Purpose |
|-----------|------|---------|
| **Briefing Mode** | `reporters/briefing_mode.py` | 시점 분리 (Closing/Morning) |
| **Prompt Builder** | `reporters/prompt_builder.py` | 동적 프롬프트 생성 |
| **Trading Protocol** | `reporters/schemas/trading_protocol.py` | JSON 프로토콜 스키마 |
| **Market Moving Score** | `intelligence/market_moving_score.py` | 뉴스 필터링 |
| **Conflict Resolver** | `mvp/conflict_resolver.py` | Risk/Trader 충돌 해결 |
| **Funnel Generator** | `reporters/funnel_generator.py` | 3단 깔때기 구조 |

#### Database Schema

```sql
-- ai_trade_decisions 테이블 (v2.3)
CREATE TABLE ai_trade_decisions (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP,
    mode VARCHAR(20),              -- CLOSING, MORNING, INTRADAY
    execution_intent VARCHAR(20),  -- AUTO, HUMAN_APPROVAL
    market_trend VARCHAR(10),      -- UP, SIDE, DOWN
    risk_level VARCHAR(10),        -- LOW, MEDIUM, HIGH
    risk_score INTEGER,            -- 0-100
    full_report_json JSONB,        -- 전체 프로토콜
    -- Backtest fields
    actual_profit_loss NUMERIC,
    is_strategy_correct BOOLEAN,
    validated_at TIMESTAMP,
    -- Version control
    model_version VARCHAR(100),
    prompt_version VARCHAR(50)
);

-- Indexes
CREATE INDEX idx_ai_decisions_created_at ON ai_trade_decisions(created_at);
CREATE INDEX idx_ai_decisions_mode ON ai_trade_decisions(mode);
CREATE INDEX idx_ai_decisions_risk ON ai_trade_decisions(risk_level);
CREATE INDEX idx_ai_decisions_json_gin ON ai_trade_decisions USING GIN(full_report_json);
```

---

### 2. Market Intelligence System (Roadmap - 260118)

**Path**: `backend/ai/intelligence/`

#### Planned Components (P0 Priority)

| Component | Status | Purpose |
|-----------|--------|---------|
| **NewsFilter (2-Stage)** | 📋 Planned | 비용 90% 절감 |
| **NarrativeStateEngine** | 📋 Planned | Fact/Narrative 분리 |
| **FactChecker** | 📋 Planned | LLM Hallucination 방지 |
| **MarketConfirmation** | 📋 Planned | 뉴스-가격 교차 검증 |

#### Architecture (Planned)

```
News → Filter(2-stage) → Intelligence → Narrative → FactCheck → MarketConfirm → Signal
```

#### Database Extensions (Planned)

```sql
-- narrative_states (P0)
CREATE TABLE narrative_states (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(50),
    fact_layer TEXT,
    narrative_layer TEXT,
    phase VARCHAR(20),  -- EMERGING, ACCELERATING, CONSENSUS, FATIGUED, REVERSING
    created_at TIMESTAMP
);

-- market_confirmations (P0)
CREATE TABLE market_confirmations (
    id SERIAL PRIMARY KEY,
    theme VARCHAR(50),
    news_intensity FLOAT,
    price_momentum FLOAT,
    signal VARCHAR(20),  -- CONFIRMED, DIVERGENT, LEADING, NOISE
    created_at TIMESTAMP
);
```

---

### 3. Portfolio Action Guide (260118)

**Path**: `backend/ai/mvp/pm_agent_mvp.py`, `frontend/src/pages/Portfolio.tsx`

#### Context-Aware Analysis

| Context | Focus | Key Questions |
|---------|-------|---------------|
| **existing_position** | HOLD/SELL 판단 | 계속 보유? 추가매수? 익절/손절? |
| **new_position** | BUY/HOLD 판단 | 언제 진입? 목표가? 손절가? |

#### Portfolio Actions

| Action | Condition | UI Display |
|--------|-----------|------------|
| **SELL** | 리스크급증, 손절도달, 목표도달 | 🔴 빨간색 카드 |
| **BUY_MORE** | 강한모멘텀, 낮은리스크 | 🟢 초록색 카드 |
| **HOLD** | 중립신호, 촉매대기 | 🟡 노란색 카드 |
| **DO_NOT_BUY** | 높은리스크, 불확실성 | ⚪ 회색 카드 |

#### API Response Structure

```json
{
  "portfolio_action_guide": {
    "action": "BUY_MORE",
    "reason": "평균가 $175 대비 현재가 $178 (+1.7%), 저항선 $185 돌파 시 추가 20% 매수 권장",
    "strength": "moderate",
    "confidence": 0.75,
    "position_adjustment_pct": 0.2,
    "stop_loss_pct": 0.05,
    "take_profit_pct": 0.10
  }
}
```

---

### 4. War Room MVP (Multi-Agent System)

**Path**: `backend/ai/mvp/`

#### Agent Architecture

```
┌─────────────────────────────────────────────┐
│           War Room Debate System            │
└─────────────────────────────────────────────┘
          │
          ├─→ Trader Agent (trader_agent_mvp.py)
          │   • Technical analysis
          │   • Entry/exit timing
          │
          ├─→ Risk Agent (risk_agent_mvp.py)
          │   • Risk assessment
          │   • Position sizing
          │   • Stop-loss calculation
          │
          ├─→ Analyst Agent (analyst_agent_mvp.py)
          │   • Fundamental analysis
          │   • Thesis validation
          │
          ▼
   PM Agent (pm_agent_mvp.py)
   • Final decision synthesis
   • Hard rules validation
   • Action recommendation
```

#### Decision Flow

```python
1. Each agent analyzes independently
2. PM Agent synthesizes opinions
3. Conflict Resolver applies Risk-First rules:
   - LOW Risk (≤30): 100% position
   - MEDIUM Risk (31-70): 50% position
   - HIGH Risk (>70) + Confidence ≥0.9: 20% scout
   - HIGH Risk (>70) + Confidence <0.9: REJECT
4. AUTO execution ONLY if:
   - Confidence > 0.85 AND Risk = LOW
```

---

### 5. Constitution System

**Path**: `backend/constitution/`

#### Core Principles

1. **Immutability**: SHA256 hash verification
2. **Human-Only Modification**: AI cannot change rules
3. **Hard Rules Priority**: Override AI recommendations
4. **Risk Limits**: Maximum loss/position constraints

#### Files

| File | Purpose |
|------|---------|
| `risk_limits.py` | 리스크 제한 규칙 |
| `allocation_rules.py` | 자산 배분 규칙 |
| `trading_constraints.py` | 거래 제약 조건 |
| `constitution.py` | 통합 검증 엔진 |
| `check_integrity.py` | SHA256 무결성 검사 |

#### Validation Flow

```python
proposal = {...}
context = {...}

is_valid, violations, violated_articles = constitution.validate_proposal(
    proposal, context
)

if not is_valid:
    # Shadow Trade 생성
    create_shadow_trade(proposal, violations)
```

---

## 🗄️ Database Architecture

### Core Tables

#### AI Analysis Tables
```sql
-- Trading signals from AI
ai_trade_decisions       -- v2.3 JSON protocols (NEW)
ai_signals               -- Legacy signals (keep for history)
war_room_debates         -- Agent debate logs
```

#### Market Data Tables
```sql
news_articles            -- News with intelligence tags
stock_prices             -- Price data
market_indicators        -- VIX, US10Y, DXY, etc.
```

#### Trading Tables
```sql
proposals                -- Trade proposals
shadow_trades            -- Rejected trade tracking
kis_positions            -- Actual positions
orders                   -- Order history
```

#### Intelligence Tables (Planned)
```sql
narrative_states         -- Fact/Narrative tracking
market_confirmations     -- News-price verification
narrative_fatigue        -- Theme overheating detection
insight_reviews          -- Post-mortem analysis
```

---

## 📊 Data Flow

### Complete Trading Workflow

```
1. News/Signal Input
   ↓
2. Market Moving Score Filter (v2.3)
   • Impact × 0.5
   • Specificity × 0.3
   • Reliability × 0.2
   • VIX-based dynamic threshold
   ↓
3. War Room Debate
   • Trader Agent
   • Risk Agent
   • Analyst Agent
   ↓
4. PM Agent Synthesis
   ↓
5. Conflict Resolution (v2.3)
   • Risk-First rules
   • Size adjustment
   ↓
6. Constitutional Validation
   • validate_proposal()
   • Check circuit breaker
   ├→ PASS → Continue
   └→ FAIL → Shadow Trade
   ↓
7. Funnel Generator (v2.3)
   • Market State (🟢🟡🔴)
   • Actionable Scenarios
   • Portfolio Impact
   ↓
8. Trading Protocol (v2.3)
   • JSON format
   • JSONB storage
   ↓
9. Telegram Commander
   • Notification
   • [승인]/[거부] buttons
   ↓
10. Execute or Shadow Trade
```

---

## 🔑 Key Design Patterns

### 1. Repository Pattern (Enforced)
- All database access through `backend/database/repository.py`
- `models.py` = Single Source of Truth

### 2. Multi-Agent Deliberation
- Independent analysis → Synthesis → Decision
- No single agent has final authority

### 3. Defensive Architecture
- Shadow Trades for rejected proposals
- Shield Reports for performance tracking
- Post-mortem analysis for learning

### 4. JSON-based Protocols (v2.3)
- Structured, executable output
- Database-stored for backtesting
- Version-controlled prompts

---

## 🚀 Recent Additions (January 2026)

### Week of 2026-01-18
- ✅ Portfolio Action Guide (context-aware analysis)
- ✅ Market Intelligence Roadmap (11 components planned)

### Week of 2026-01-22
- ✅ Daily Briefing v2.1 (basic reports)
- ✅ Daily Briefing v2.2 (enhanced analysis)

### Day of 2026-01-24
- ✅ **Daily Briefing v2.3** (5 phases complete)
  - Briefing Mode System
  - Prompt Builder
  - Trading Protocol Schema  
  - Market Moving Score
  - Conflict Resolver
  - Funnel Generator

---

## 📁 Directory Structure

```
backend/
├── ai/
│   ├── reporters/              # Daily Briefing v2.3
│   │   ├── briefing_mode.py    [NEW]
│   │   ├── prompt_builder.py   [NEW]
│   │   ├── funnel_generator.py [NEW]
│   │   └── schemas/
│   │       └── trading_protocol.py [NEW]
│   ├── intelligence/           # Market Intelligence
│   │   └── market_moving_score.py [NEW]
│   ├── mvp/                    # War Room MVP
│   │   ├── trader_agent_mvp.py
│   │   ├── risk_agent_mvp.py
│   │   ├── analyst_agent_mvp.py
│   │   ├── pm_agent_mvp.py
│   │   ├── conflict_resolver.py [NEW]
│   │   └── war_room_mvp.py
│   └── debate/                 # Legacy agents (deprecated)
├── constitution/               # Constitutional rules
│   ├── constitution.py
│   ├── risk_limits.py
│   ├── allocation_rules.py
│   └── trading_constraints.py
├── database/
│   ├── models.py              # SQLAlchemy models
│   ├── repository.py          # Data access layer
│   └── migrations/
│       └── add_ai_trade_decisions_table.py [NEW]
└── api/
    └── main.py                # FastAPI endpoints
```

---

## 🔮 Roadmap

### Near-Term (Phase 1-2)
- [ ] Market Intelligence P0 components
  - [ ] NewsFilter (2-stage)
  - [ ] NarrativeStateEngine
  - [ ] FactChecker
  - [ ] MarketConfirmation

### Mid-Term (Phase 3-4)
- [ ] Market Intelligence P1 components
  - [ ] NarrativeFatigue
  - [ ] ContrarySignal
  - [ ] HorizonTagger
  - [ ] ChartGenerator

### Long-Term (Phase 5-6)
- [ ] Market Intelligence P2 components
  - [ ] PolicyFeasibility
  - [ ] InsightPostMortem
  - [ ] PersonaTuning
- [ ] Daily Briefing v2.4
  - [ ] Real-time streaming
  - [ ] Backtest automation
  - [ ] AUTO execution integration

---

## 📚 Related Documents

- [Implementation Plan - v2.3](../planning/260124_Daily_Briefing_v2.3_Protocol_Implementation_Plan.md)
- [Market Intelligence Roadmap](../planning/260118_market_intelligence_roadmap.md)
- [Portfolio Action Guide](../planning/260118_Implementation_Portfolio_Action_Guide.md)
- [Walkthrough - v2.3](../../.gemini/antigravity/brain/.../walkthrough.md)

---

**Version History**:
- 2026-01-24: v2.3 - Added Daily Briefing v2.3 components
- 2026-01-18: v2.2 - Added Market Intelligence and Portfolio Action Guide
- 2025-12-15: v2.0 - Constitutional Release

**Maintainers**: AI Trading Team  
**Status**: Active Development
