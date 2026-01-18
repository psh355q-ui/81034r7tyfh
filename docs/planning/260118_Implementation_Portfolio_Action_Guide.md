# AI Portfolio Action Guide Feature Implementation Plan

**Date**: 2026-01-18
**Category**: Implementation
**Status**: Planning
**Updated**: 2026-01-18 (context-aware analysis integration)

---

## Problem Statement

Portfolio 페이지의 AI Insights 탭에서 War Room MVP 에이전트들이 포트폴리오를 검토할 때, **컨텍스트(보유/진입 등)에 따라 다른 분석 관점**을 제공해야 합니다.

**Current Issues:**
1. **잘못된 분석 관점**: 모든 분석이 "진입 타이밍" 관점으로 고정 (`action_context="new_position"` 하드코딩)
2. **Context 무시**: 프론트엔드에서 `context: 'existing_position'` 전송하지만 백엔드가 무시
3. **Persona Mode 미반영**: 프론트엔드에서 선택한 persona_mode가 War Room에 전달되지 않음
4. **구체적 액션 가이드 부족**: 보유 중인 종목에 대해 "언제 팔면 좋은지, 언제 더 사야하는지, 보유 유지 필요한지"를 명확히 안내하지 않음

---

## Goal

### Primary Goal: Context-Aware Analysis
- **Portfolio 페이지 (existing_position)**: HOLD/SELL 판단, 추가매수 여부, 구체적 가격/조건
- **Signals 페이지 (new_position)**: BUY/HOLD 판단, 진입가/목표가

### Secondary Goal: 4가지 Portfolio Action 제공

| 액션 | 설명 | UI 표시 |
|------|------|------------|
| **SELL** | 포지션 정리/일부 매도 권장 | 빨간색 카드, 하락 아이콘 |
| **BUY_MORE** | 현재 포지션 증가 권장 | 초록색 카드, 상승 아이콘 |
| **HOLD** | 현재 포지션 유지 권장 | 노란색 카드, 유지 아이콘 |
| **DO_NOT_BUY** | 신규 진입 비권장 | 회색 카드, 경고 아이콘 |

---

## Critical Files to Modify

| 파일 | 경로 | 역할 |
|------|------|------|
| **AnalyzeRequest Model** | `backend/main.py` (line 735-738) | context, persona_mode 파라미터 추가 |
| **API Endpoint** | `backend/main.py` (line 809-980) | context 전달 및 portfolio_action_guide 응답 |
| PM Schema | `backend/ai/schemas/war_room_schemas.py` | 액션 가이드 필드 추가 |
| PM Agent | `backend/ai/mvp/pm_agent_mvp.py` | 액션 결정 로직 추가 |
| War Room Agents | `backend/ai/mvp/war_room_mvp.py` | Context별 프롬프트 조정 |
| Frontend Page | `frontend/src/pages/Portfolio.tsx` | UI 표시 로직 수정 |

---

## Implementation Plan

### Phase 0: API Parameter Support (Prerequisite)

**목적**: 프론트엔드에서 보내는 `context`와 `persona_mode`를 백엔드가 War Room에 전달하도록 수정

#### 0.1 Update AnalyzeRequest Model

**File**: `backend/main.py` (line 735-738)

```python
class AnalyzeRequest(BaseModel):
    ticker: str
    urgency: str = "MEDIUM"
    market_context: Optional[Dict] = None
    # NEW: Add context and persona_mode
    context: str = "new_position"  # "new_position" | "existing_position"
    persona_mode: Optional[str] = "trading"  # "dividend" | "long_term" | "trading" | "aggressive"
```

#### 0.2 Update /api/analyze Endpoint

**File**: `backend/main.py` (line 852-857)

```python
# Pass context and persona_mode to War Room
war_room_result = await war_room.deliberate(
    symbol=request.ticker,
    action_context=request.context,  # Changed from hardcoded "new_position"
    persona_mode=request.persona_mode or "trading",  # NEW
    market_data=market_data,
    portfolio_state=portfolio_state,
    additional_data=additional_data
)
```


### Phase 1: Backend Schema Extension

#### 1.1 Update PMDecision Schema

**File**: `backend/ai/schemas/war_room_schemas.py`

```python
class PMDecision(BaseModel):
    # ... existing fields ...

    # NEW: Portfolio Action Guide fields
    portfolio_action: Optional[str] = Field(
        default="hold",
        description="Portfolio-level action: sell | buy_more | hold | do_not_buy"
    )
    action_reason: Optional[str] = Field(
        default="",
        description="Reasoning for the portfolio action (Korean)"
    )
    action_strength: Optional[str] = Field(
        default="moderate",
        description="Strength: weak | moderate | strong"
    )
    position_adjustment_pct: Optional[float] = Field(
        default=0.0,
        description="Suggested adjustment (+0.2 = add 20%, -0.5 = sell 50%)"
    )
```

#### 1.2 Update PM Agent Prompt (Context-Aware)

**File**: `backend/ai/mvp/pm_agent_mvp.py` (line 118-161)

Extend system prompt to include **context-aware guidance** and action guide:

```python
self.system_prompt = """당신은 포트폴리오 매니저입니다.

... existing instructions ...

## Context-Aware Analysis (NEW)

`action_context` 파라미터에 따라 분석 관점을 조정하세요:

### 1. existing_position (보유 중인 종목)
- **목적**: HOLD vs SELL 판단, 추가매수 여부 결정
- **분석 초점**:
  - 현재 포지션 유지 권장 여부
  - 추가 매수 타이밍 및 가격대 (구체적)
  - 익절/손절 레벨 (평균가 대비 %)
  - Stop-loss 조정 권장
  - 포지션 축소/확대 비율
  - 투자 논리(Thesis) 유효성 재확인
  - 다음 재평가 시점 (실적 발표, 이벤트)

### 2. new_position (신규 진입 검토)
- **목적**: BUY vs HOLD 판단
- **분석 초점**:
  - 진입 타이밍 및 진입가
  - 목표가 및 손절가
  - 포지션 사이즈 권장

## Portfolio Action Guide
보유 종목에 대해 다음 4가지 액션 중 하나를 선택하세요:

1. **SELL (매도 추천)**: 리스크 급증, 손절가 도달, 목표가 도달, 기술적 약세
   - 언제: 구체적 가격 레벨 또는 조건 (예: "$185 저항 돌파 실패 시")
   - 얼마나: 일부 익절(50%) vs 전량 청산
   
2. **BUY_MORE (추가 매수)**: 강한 모멘텀, 긍정적 촉매, 낮은 리스크
   - 언제: 구체적 매수 타이밍 (예: "지지선 $176 유지 시")
   - 얼마나: 추가 매수 비중 (ex: 현재 대비 +20%)
   
3. **HOLD (보유 유지)**: 중립적 신호, 촉매 대기 중
   - 추가 매수 불필요 명시
   - 다음 재평가 시점 제시 (예: "실적 발표 2026-02-15 후")
   - Stop-loss 조정 여부
   
4. **DO_NOT_BUY (미진입/관망)**: 높은 리스크, 불확실한 테마

출력 형식:
{
    ... existing fields ...,
    "portfolio_action": "buy_more" | "sell" | "hold" | "do_not_buy",
    "action_reason": "액션 선택 이유 (한국어, 구체적 가격/조건 포함)",
    "action_strength": "weak" | "moderate" | "strong",
    "position_adjustment_pct": -1.0 ~ 1.0  // -0.5 = 50% 매도, +0.2 = 20% 추가매수
}

**중요**: action_reason에는 반드시 구체적인 가격 레벨과 조건을 포함하세요.
예: "평균가 $175 대비 현재가 $178 (+1.7%), 저항선 $185 돌파 시 50% 익절 권장"
"""
```

#### 1.3 Add Action Decision Helper

**File**: `backend/ai/mvp/pm_agent_mvp.py`

Add helper method after `_build_prompt()`:

```python
def _determine_portfolio_action(
    self,
    final_decision: str,
    recommended_action: str,
    confidence: float,
    risk_level: str
) -> Dict[str, Any]:
    """
    Determine portfolio-level action from agent inputs.

    Mapping:
    - approve + sell → SELL
    - approve + buy + confidence > 0.7 → BUY_MORE
    - approve + buy + confidence 0.5-0.7 → HOLD
    - reject + extreme risk → SELL
    - reject + medium/high risk → HOLD
    - silence → HOLD
    """
    action_map = {
        ("approve", "sell"): ("sell", "strong"),
        ("approve", "buy"): ("buy_more" if confidence > 0.7 else "hold", "moderate"),
        ("reject", "extreme"): ("sell", "strong"),
        ("reject", "high"): ("hold", "moderate"),
        ("silence", ""): ("hold", "weak"),
    }

    key = (final_decision, risk_level if risk_level == "extreme" else "")
    portfolio_action, strength = action_map.get(key, ("hold", "moderate"))

    return {
        "portfolio_action": portfolio_action,
        "action_strength": strength,
        "position_adjustment_pct": self._calculate_position_adjustment(
            portfolio_action, confidence
        )
    }

def _calculate_position_adjustment(self, action: str, confidence: float) -> float:
    """Calculate position adjustment percentage."""
    adjustments = {
        "sell": -0.5,  # Sell 50%
        "buy_more": 0.2,  # Add 20%
        "hold": 0.0,
        "do_not_buy": 0.0
    }
    base = adjustments.get(action, 0.0)
    return base * confidence  # Scale by confidence
```

#### 1.4 Update make_final_decision()

**File**: `backend/ai/mvp/pm_agent_mvp.py` (line 163-335)

In the AI response section (after line 284), add action determination:

```python
# After line 304: result = decision.model_dump()

# Add portfolio action guide
action_guide = self._determine_portfolio_action(
    final_decision=result.get('final_decision', 'hold'),
    recommended_action=result.get('recommended_action', 'hold'),
    confidence=result.get('confidence', 0.5),
    risk_level=risk_opinion.get('risk_level', 'medium')
)
result.update(action_guide)
```


---

### Phase 2: API Response Update

#### 2.1 Update /api/analyze Response

**File**: `backend/main.py` (line 875-920)

Modify the response mapping to include portfolio action guide:

```python
result = {
    "ticker": request.ticker,
    "final_decision": {
        "action": normalize_action(pm_decision.get("final_decision", "HOLD")),
        "confidence": war_room_result.get("confidence", 0.5),
        "reasoning": pm_decision.get("reasoning", "No reasoning provided")
    },
    # NEW: Portfolio Action Guide
    "portfolio_action_guide": {
        "action": pm_decision.get("portfolio_action", "hold").upper(),  # SELL | BUY_MORE | HOLD | DO_NOT_BUY
        "reason": pm_decision.get("action_reason", ""),
        "strength": pm_decision.get("action_strength", "moderate"),  # weak | moderate | strong
        "confidence": pm_decision.get("confidence", 0.5),
        "position_adjustment_pct": pm_decision.get("position_adjustment_pct", 0.0),
        "stop_loss_pct": agents.get("risk", {}).get("stop_loss_pct", 0.05),
        "take_profit_pct": agents.get("risk", {}).get("take_profit_pct", 0.10)
    },
    "agents_analysis": {
        # ... existing agent analysis ...
    },
    # ... rest of response ...
}
```

---

### Phase 3: Frontend UI Update

#### 3.1 Update Portfolio.tsx Interfaces

**File**: `frontend/src/pages/Portfolio.tsx` (line 80-106)

```typescript
interface PortfolioActionGuide {
    action: 'SELL' | 'BUY_MORE' | 'HOLD' | 'DO_NOT_BUY';
    reason: string;
    strength: 'weak' | 'moderate' | 'strong';
    confidence: number;
    position_adjustment_pct: number;
    current_position_pct: number;
    target_position_pct: number;
    stop_loss_pct: number;
    take_profit_pct: number;
}

interface AgentAnalysis {
    trader_agent?: AgentOpinion;
    risk_agent?: AgentOpinion;
    analyst_agent?: AgentOpinion;
    pm_agent?: {
        action: 'BUY' | 'SELL' | 'HOLD';
        confidence: number;
        reasoning: string;
        hard_rules_passed: string[];
        hard_rules_violations: string[];
    };
    // NEW: Portfolio action guide
    portfolio_action_guide?: PortfolioActionGuide;
}
```

#### 3.2 Add Action Guide Display Component

**File**: `frontend/src/pages/Portfolio.tsx` (line 767+)

```typescript
{/* NEW: Portfolio Action Guide Card */}
{agents?.portfolio_action_guide && (
    <div className={`mx-6 mt-4 p-4 rounded-lg border-2 ${
        agents.portfolio_action_guide.action === 'SELL' ? 'bg-red-50 border-red-200' :
        agents.portfolio_action_guide.action === 'BUY_MORE' ? 'bg-green-50 border-green-200' :
        'bg-yellow-50 border-yellow-200'
    }`}>
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
                {agents.portfolio_action_guide.action === 'SELL' && <TrendingDown className="w-6 h-6 text-red-600" />}
                {agents.portfolio_action_guide.action === 'BUY_MORE' && <TrendingUp className="w-6 h-6 text-green-600" />}
                {agents.portfolio_action_guide.action === 'HOLD' && <MinusCircle className="w-6 h-6 text-yellow-600" />}
                {agents.portfolio_action_guide.action === 'DO_NOT_BUY' && <AlertCircle className="w-6 h-6 text-gray-600" />}
                <div>
                    <h4 className="font-bold text-sm">
                        {agents.portfolio_action_guide.action === 'SELL' && '📉 매도 추천'}
                        {agents.portfolio_action_guide.action === 'BUY_MORE' && '📈 추가 매수'}
                        {agents.portfolio_action_guide.action === 'HOLD' && '⏸️ 보유 유지'}
                        {agents.portfolio_action_guide.action === 'DO_NOT_BUY' && '⚠️ 관망 권장'}
                    </h4>
                    <p className="text-xs text-gray-600 mt-1">{agents.portfolio_action_guide.reason}</p>
                </div>
            </div>
            <div className="text-right">
                <span className={`text-xs px-2 py-1 rounded ${
                    agents.portfolio_action_guide.strength === 'strong' ? 'bg-green-200' :
                    agents.portfolio_action_guide.strength === 'weak' ? 'bg-gray-200' :
                    'bg-yellow-200'
                }`}>
                    {agents.portfolio_action_guide.strength === 'strong' && '강한 신호'}
                    {agents.portfolio_action_guide.strength === 'moderate' && '보통 신호'}
                    {agents.portfolio_action_guide.strength === 'weak' && '약한 신호'}
                </span>
                <p className="text-xs text-gray-500 mt-1">
                    신뢰도 {(agents.portfolio_action_guide.confidence * 100).toFixed(0)}%
                </p>
            </div>
        </div>
        {agents.portfolio_action_guide.action !== 'DO_NOT_BUY' && (
            <div className="mt-3 grid grid-cols-4 gap-2 text-xs border-t border-gray-200 pt-2">
                <div><span className="text-gray-500">현재 비중</span><p className="font-medium">{(agents.portfolio_action_guide.current_position_pct * 100).toFixed(1)}%</p></div>
                <div><span className="text-gray-500">목표 비중</span><p className="font-medium">{(agents.portfolio_action_guide.target_position_pct * 100).toFixed(1)}%</p></div>
                <div><span className="text-gray-500">손절가</span><p className="font-medium text-red-600">{(agents.portfolio_action_guide.stop_loss_pct * 100).toFixed(1)}%</p></div>
                <div><span className="text-gray-500">목표가</span><p className="font-medium text-green-600">{(agents.portfolio_action_guide.take_profit_pct * 100).toFixed(1)}%</p></div>
            </div>
        )}
    </div>
)}
```

#### 3.3 Update API Response Parsing

**File**: `frontend/src/pages/Portfolio.tsx` (line 298-396)

```typescript
// NEW: Parse portfolio action guide
if (data.portfolio_action_guide) {
    analyses[position.symbol].portfolio_action_guide = {
        action: data.portfolio_action_guide.action,
        reason: data.portfolio_action_guide.reason,
        strength: data.portfolio_action_guide.strength,
        confidence: data.portfolio_action_guide.confidence,
        position_adjustment_pct: data.portfolio_action_guide.position_adjustment_pct,
        current_position_pct: pos.market_value / portfolio.total_value,
        target_position_pct: (pos.market_value / portfolio.total_value) + data.portfolio_action_guide.position_adjustment_pct,
        stop_loss_pct: data.portfolio_action_guide.stop_loss_pct,
        take_profit_pct: data.portfolio_action_guide.take_profit_pct
    };
    setAgentAnalysis({ ...analyses });
}
```

---

## Action Decision Mapping Logic

| final_decision | recommended_action | confidence | risk_level | → portfolio_action | strength |
|----------------|-------------------|------------|------------|-------------------|----------|
| approve | sell | any | any | **SELL** | strong |
| approve | buy | > 0.7 | low/medium | **BUY_MORE** | moderate |
| approve | buy | 0.5-0.7 | low/medium | **HOLD** | moderate |
| reject | - | any | extreme | **SELL** | strong |
| reject | - | any | high/medium | **HOLD** | moderate |
| silence | - | any | any | **HOLD** | weak |
| reduce_size | - | any | any | **SELL** (partial) | moderate |

---

## Testing & Verification

### 1. Backend Unit Test
```bash
cd backend
python -m pytest tests/test_pm_agent_action_guide.py -v
```

Create `tests/test_pm_agent_action_guide.py`:
```python
def test_portfolio_action_mapping():
    """Test action decision logic"""
    assert _determine_portfolio_action("approve", "sell", 0.8, "medium") == ("sell", "strong")
    assert _determine_portfolio_action("approve", "buy", 0.8, "low") == ("buy_more", "moderate")
    assert _determine_portfolio_action("approve", "buy", 0.6, "low") == ("hold", "moderate")
    assert _determine_portfolio_action("reject", "buy", 0.5, "extreme") == ("sell", "strong")
```

### 2. API Response Test
```bash
# Test existing_position context
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "persona_mode": "trading", "context": "existing_position"}'

# Verify response includes portfolio_action_guide field
```

### 3. Frontend Integration Test
**Steps:**
1. Start backend: `python backend/main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to `http://localhost:3002/portfolio`
4. Click "AI Insights" tab
5. Verify action guide card appears with:
   - ✅ Correct color (red/green/yellow/gray)
   - ✅ Korean action reason with specific prices
   - ✅ Strength badge
   - ✅ Position metrics (current/target/stop-loss/take-profit)

### 4. E2E Scenarios

| 시나리오 | 조건 | 예상 액션 | 예상 UI |
|---------|------|----------|---------|
| 수익성 포지션 + 강한 모멘텀 | confidence > 0.7, buy 신호 | **BUY_MORE** | 초록색, "추가 20% 매수 권장" |
| 손절가 도달 | stop loss hit, extreme risk | **SELL** | 빨간색, "손절가 도달, 전량 청산" |
| 중립적 신호 | 대기 중, confidence 0.5-0.7 | **HOLD** | 노란색, "실적 발표 후 재평가" |
| 신규 종목 + 높은 리스크 | extreme risk, reject | **DO_NOT_BUY** | 회색, "진입 비권장" |

### 5. Context-Specific Verification

**Portfolio page (existing_position context):**
- ✅ Trader Agent: mentions "평균가 대비" or "현재 포지션"
- ✅ Risk Agent: mentions "Stop-loss 조정" or "포지션 축소/확대"
- ✅ Analyst Agent: mentions "논리 유효성" or "보유 지속"
- ✅ PM Agent: action is HOLD/SELL focused (BUY rare)
- ✅ Portfolio Action Guide: specific price levels in Korean

**Signals page (new_position context):**
- ✅ Analysis focuses on "진입 타이밍"
- ✅ Action is BUY/HOLD focused
- ✅ Reasoning includes entry/target/stop-loss for new positions

### Success Criteria

- [ ] Backend context parameter passed to War Room
- [ ] Backend persona_mode parameter passed to War Room
- [ ] Backend returns `portfolio_action_guide` in response
- [ ] Portfolio Action Guide card displays on frontend
- [ ] Action reason includes specific Korean guidance with prices
- [ ] Card color and icon match action type
- [ ] Position metrics calculate correctly
- [ ] Context differentiation works (existing vs new)
- [ ] No console errors or API failures

---

## Summary of Changes

| Component | File | Lines | Change Type |
|-----------|------|-------|-------------|
| **Phase 0: Context Support** | | | |
| AnalyzeRequest | `backend/main.py` | 735-738 | Add context, persona_mode fields |
| API Endpoint | `backend/main.py` | 852-857 | Pass context to War Room |
| **Phase 1: Schema & Logic** | | | |
| PM Schema | `backend/ai/schemas/war_room_schemas.py` | N/A | Add 4 new fields |
| PM Agent | `backend/ai/mvp/pm_agent_mvp.py` | ~118, ~163, ~285 | Extend prompt, add helpers |
| **Phase 2: API Response** | | | |
| API Response | `backend/main.py` | ~875-920 | Add portfolio_action_guide |
| **Phase 3: Frontend** | | | |
| Frontend | `frontend/src/pages/Portfolio.tsx` | ~95, ~310, ~770 | Interface + parsing + UI |

**Total estimated changes**: ~200 lines across 5 files

**Implementation Priority**:
1. **Phase 0** (필수): Context parameter 지원 - 이게 없으면 기존 분석도 제대로 작동 안함
2. Phase 1: PM Schema + Action Logic
3. Phase 2: API Response 구조 추가
4. Phase 3: Frontend UI 구현

---

## Related Files

- [pm_agent_mvp.py](d:/code/ai-trading-system/backend/ai/mvp/pm_agent_mvp.py) - PM Agent 구현
- [Portfolio.tsx](d:/code/ai-trading-system/frontend/src/pages/Portfolio.tsx) - Portfolio 페이지
- [structuring_agent.py](d:/code/ai-trading-system/backend/ai/mvp/structuring_agent.py) - JSON 구조화 에이전트
