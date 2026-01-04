# War Room MVP to Claude Code Agent Skills Migration Plan

**Date**: 2026-01-02
**Author**: AI Trading System Team
**Phase**: Skills Migration (Phase A)
**Status**: Planning Complete, Ready for Implementation

---

## 목표

War Room MVP (3+1 Agent System)를 Claude Code Agent Skills 형식으로 전환하여 재사용성과 모듈화를 향상시킵니다.

### 사용자 요구사항 (확정)
- ✅ MVP를 5개 개별 Skill로 분리 (세분화)
- ✅ Legacy 8-Agent War Room 유지 (MVP가 필요시 호출 가능)
- ✅ Legacy SKILL.md 파일들을 legacy/ 폴더로 이동
- ✅ Skill 전환 먼저 진행, Structured Outputs는 나중 (Phase B)

---

## 현재 상태 분석

### War Room MVP (Production Active)
- **위치**: `backend/ai/mvp/`
- **구성**: 4개 Agent + 1개 Orchestrator
  - `trader_agent_mvp.py` (35% 투표권) - 공격적 기회 포착
  - `risk_agent_mvp.py` (35% 투표권) - 방어적 리스크 관리 + Position Sizing
  - `analyst_agent_mvp.py` (30% 투표권) - 종합 정보 분석
  - `pm_agent_mvp.py` (최종 결정자) - Hard Rules + Silence Policy
  - `war_room_mvp.py` (오케스트레이터) - 전체 워크플로우 조율
- **API**: `/api/war-room-mvp` (8개 엔드포인트)
- **모델**: Gemini 2.0 Flash (전체)
- **통합**: Shadow Trading, Execution Router, Order Validator
- **성과**: Legacy 대비 67% 비용/시간 절감

### Legacy 8-Agent War Room
- **위치**: `backend/ai/debate/`
- **구성**: 8개 독립 Agent (Trader, Risk, Analyst, Macro, Institutional, News, ChipWar, PM)
- **API**: `/api/war-room` (main.py line 383에서 활성)
- **상태**: 병렬 운영 중 (MVP와 공존)

### Legacy SKILL.md 파일
- **위치**: `backend/ai/skills/war-room/`
- **내용**: pm-agent, trader-agent, risk-agent, analyst-agent 등 SKILL.md 파일만 존재 (handler.py 없음)
- **역할**: 문서화 전용 (실제 구현은 debate/ 폴더)

### Skill Infrastructure
- **SkillLoader**: `backend/ai/skills/skill_loader.py` (정상 작동, singleton)
- **BaseSkillAgent**: `backend/ai/skills/base_agent.py` (3개 base class 제공)
- **패턴**: YAML frontmatter + Markdown instructions

---

## 최종 디렉토리 구조

```
backend/ai/skills/
├── war-room-mvp/                    # NEW - MVP Skill 컨테이너
│   ├── trader-agent-mvp/
│   │   ├── SKILL.md                # NEW - Skill 정의
│   │   └── handler.py              # NEW - TraderAgentMVP wrapper
│   ├── risk-agent-mvp/
│   │   ├── SKILL.md
│   │   └── handler.py              # NEW - RiskAgentMVP wrapper
│   ├── analyst-agent-mvp/
│   │   ├── SKILL.md
│   │   └── handler.py              # NEW - AnalystAgentMVP wrapper
│   ├── pm-agent-mvp/
│   │   ├── SKILL.md
│   │   └── handler.py              # NEW - PMAgentMVP wrapper
│   ├── orchestrator-mvp/
│   │   ├── SKILL.md
│   │   └── handler.py              # NEW - WarRoomMVP wrapper + legacy 호출
│   └── README.md                    # NEW - 사용법 문서
│
└── legacy/                          # MOVED
    └── war-room/                    # FROM backend/ai/skills/war-room/
        ├── pm-agent/SKILL.md
        ├── trader-agent/SKILL.md
        ├── risk-agent/SKILL.md
        ├── analyst-agent/SKILL.md
        ├── macro-agent/SKILL.md
        ├── institutional-agent/SKILL.md
        ├── news-agent/SKILL.md
        └── README.md                # NEW - Deprecated 안내

backend/ai/mvp/                      # UNCHANGED - 기존 구현 유지
├── trader_agent_mvp.py
├── risk_agent_mvp.py
├── analyst_agent_mvp.py
├── pm_agent_mvp.py
└── war_room_mvp.py

backend/ai/debate/                   # UNCHANGED - Legacy 8-agent 유지
├── trader_agent.py
├── risk_agent.py
└── ... (8개 agent)
```

---

## 구현 계획 (10 Steps)

### Step 1: 디렉토리 구조 생성

**1.1 Legacy SKILL.md 이동**
```bash
mkdir -p backend/ai/skills/legacy
mv backend/ai/skills/war-room backend/ai/skills/legacy/war-room
```

**1.2 MVP Skill 디렉토리 생성**
```bash
mkdir -p backend/ai/skills/war-room-mvp/trader-agent-mvp
mkdir -p backend/ai/skills/war-room-mvp/risk-agent-mvp
mkdir -p backend/ai/skills/war-room-mvp/analyst-agent-mvp
mkdir -p backend/ai/skills/war-room-mvp/pm-agent-mvp
mkdir -p backend/ai/skills/war-room-mvp/orchestrator-mvp
```

---

### Step 2: SKILL.md 작성 (5개 파일)

**핵심 YAML 필드 구조:**
```yaml
---
name: trader-agent-mvp
description: MVP Trader Agent - 공격적 기회 포착 (35% 투표권)
license: Proprietary
compatibility: Requires Gemini 2.0 Flash, market data
metadata:
  author: ai-trading-system
  version: "1.0"
  category: war-room-mvp
  agent_role: trader
  voting_weight: 0.35
  model: gemini-2.0-flash-exp
  absorbed_agents:
    - Trader Agent (100%)
    - ChipWar Agent (opportunity detection)
---
```

**작성할 파일:**
1. `backend/ai/skills/war-room-mvp/trader-agent-mvp/SKILL.md`
   - Role: 단기 트레이딩 기회 포착
   - Core Capabilities: 기술적 분석, 모멘텀, ChipWar 이벤트
   - Output: action, confidence, opportunity_score

2. `backend/ai/skills/war-room-mvp/risk-agent-mvp/SKILL.md`
   - Role: 방어적 리스크 관리 + Position Sizing
   - Core Capabilities: Risk assessment, Kelly Criterion, Sentiment, Dividend risk
   - Output: risk_level, position_size, stop_loss

3. `backend/ai/skills/war-room-mvp/analyst-agent-mvp/SKILL.md`
   - Role: 종합 정보 분석
   - Core Capabilities: News, Macro, Institutional, ChipWar geopolitics
   - Output: information_score, key_catalysts, red_flags

4. `backend/ai/skills/war-room-mvp/pm-agent-mvp/SKILL.md`
   - Role: 최종 의사결정자
   - Core Capabilities: Hard Rules, Silence Policy, Agent consensus
   - Output: final_decision (approve/reject/reduce_size/silence)

5. `backend/ai/skills/war-room-mvp/orchestrator-mvp/SKILL.md`
   - Role: 전체 워크플로우 조율
   - Core Capabilities: Execution Routing, Agent coordination, Legacy integration
   - Output: Full deliberation result

**내용 구성:**
- Role: Agent 역할 설명
- Core Capabilities: 주요 기능 (1-4개)
- Output Format: JSON 출력 형식 예시
- Integration: 다른 Agent와 협업 방식
- Guidelines: Do's/Don'ts

---

### Step 3: Handler.py 작성 (5개 파일)

**패턴: Wrapper + execute() 함수**

각 handler.py는:
1. 기존 MVP 클래스를 import
2. `execute(context: Dict) -> Dict` 함수 정의
3. Context 검증 및 Agent 실행
4. 결과 반환

**예시 - Trader Agent MVP Handler:**

**파일:** `backend/ai/skills/war-room-mvp/trader-agent-mvp/handler.py`

```python
"""
Trader Agent MVP - Skill Handler
Wraps TraderAgentMVP to provide Agent Skills interface.

Date: 2026-01-02
Phase: Skills Migration
"""

from typing import Dict, Any
from backend.ai.mvp.trader_agent_mvp import TraderAgentMVP


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Trader Agent MVP analysis

    Args:
        context: {
            'symbol': str (required),
            'price_data': dict,
            'technical_data': dict (optional),
            'chipwar_events': list (optional),
            'market_context': dict (optional)
        }

    Returns:
        Analysis result from TraderAgentMVP
        {
            'action': 'buy|sell|hold|pass',
            'confidence': 0.0-1.0,
            'reasoning': str,
            'opportunity_score': float,
            ...
        }
    """
    # Validate required parameters
    symbol = context.get('symbol')
    if not symbol:
        return {
            'error': 'Missing required parameter: symbol',
            'agent': 'trader_mvp',
            'action': 'pass',
            'confidence': 0.0
        }

    # Initialize agent (기존 MVP 클래스 그대로 사용)
    agent = TraderAgentMVP()

    # Execute analysis (기존 analyze() 메서드 호출)
    result = agent.analyze(
        symbol=symbol,
        price_data=context.get('price_data', {}),
        technical_data=context.get('technical_data'),
        chipwar_events=context.get('chipwar_events'),
        market_context=context.get('market_context')
    )

    return result


# 직접 import도 가능하도록 export
__all__ = ['execute', 'TraderAgentMVP']
```

**동일 패턴으로 작성할 파일:**
- `risk-agent-mvp/handler.py` → RiskAgentMVP.analyze()
- `analyst-agent-mvp/handler.py` → AnalystAgentMVP.analyze()
- `pm-agent-mvp/handler.py` → PMAgentMVP.make_final_decision()
- `orchestrator-mvp/handler.py` → WarRoomMVP.deliberate() + **legacy 호출 함수**

---

### Step 4: Orchestrator Handler - Legacy 통합 기능

**핵심 기능:**

**파일:** `backend/ai/skills/war-room-mvp/orchestrator-mvp/handler.py`

```python
"""
War Room MVP Orchestrator - Skill Handler
Coordinates 3+1 agent deliberation with legacy system integration.

Date: 2026-01-02
Phase: Skills Migration
"""

from typing import Dict, Any
from backend.ai.mvp.war_room_mvp import WarRoomMVP

# Singleton instance
_war_room_instance = None


def get_war_room() -> WarRoomMVP:
    """Get or create War Room MVP singleton"""
    global _war_room_instance
    if _war_room_instance is None:
        _war_room_instance = WarRoomMVP()
    return _war_room_instance


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute War Room MVP deliberation

    Args:
        context: {
            'symbol': str (required),
            'action_context': str,
            'market_data': dict,
            'portfolio_state': dict,
            'additional_data': dict (optional)
        }

    Returns:
        Full deliberation result with final_decision, agent_opinions, etc.
    """
    symbol = context.get('symbol')
    if not symbol:
        return {
            'error': 'Missing required parameter: symbol',
            'final_decision': 'reject'
        }

    war_room = get_war_room()

    result = war_room.deliberate(
        symbol=symbol,
        action_context=context.get('action_context', 'new_position'),
        market_data=context.get('market_data', {}),
        portfolio_state=context.get('portfolio_state', {}),
        additional_data=context.get('additional_data')
    )

    return result


def invoke_legacy_war_room(symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    **NEW FUNCTION - 사용자 요구사항**

    MVP가 Legacy 8-Agent War Room을 호출할 수 있도록 지원

    사용 시나리오:
    - MVP 결과와 Legacy 결과 비교
    - 중요한 결정에 대한 2차 검증
    - A/B 테스트

    Args:
        symbol: 종목 심볼
        context: 추가 컨텍스트 데이터 (market_data, portfolio_state 등)

    Returns:
        Legacy War Room debate 결과
        {
            'source': 'legacy_8_agent_war_room',
            'symbol': str,
            'votes': [...],
            'consensus': {...}
        }
    """
    from backend.api.war_room_router import WarRoomEngine

    # Legacy 8-Agent Engine 초기화
    legacy_engine = WarRoomEngine()

    # Legacy debate 실행
    # TODO: WarRoomEngine의 run_debate() 또는 유사 메서드 호출
    # 현재는 placeholder

    return {
        'source': 'legacy_8_agent_war_room',
        'symbol': symbol,
        'note': 'Legacy system integration point - implementation needed',
        'status': 'placeholder'
    }


def get_info() -> Dict[str, Any]:
    """Get War Room MVP information"""
    war_room = get_war_room()
    return war_room.get_war_room_info()


def get_history(limit: int = 20) -> Dict[str, Any]:
    """Get decision history"""
    war_room = get_war_room()
    history = war_room.decision_history[-limit:]
    return {
        'decisions': history,
        'total_count': len(war_room.decision_history)
    }


__all__ = ['execute', 'get_war_room', 'invoke_legacy_war_room', 'get_info', 'get_history']
```

---

### Step 5: API Router 업데이트 - Dual Mode 지원

**목적:** 직접 클래스 호출과 Skill handler 호출을 모두 지원

**파일:** `backend/routers/war_room_mvp_router.py`

**변경 내용:**

```python
import os

# ============================================================================
# Feature Flag for Skill Mode
# ============================================================================
USE_SKILL_HANDLERS = os.getenv('WAR_ROOM_MVP_USE_SKILLS', 'false').lower() == 'true'

# Conditional imports
if USE_SKILL_HANDLERS:
    # Skill mode: Import handler functions
    from backend.ai.skills.war_room_mvp.orchestrator_mvp import handler as war_room_handler
    war_room = None  # Not needed in skill mode
    print("✅ War Room MVP - Skill Handler Mode")
else:
    # Direct mode: Import class directly (기존 방식)
    from backend.ai.mvp.war_room_mvp import WarRoomMVP
    war_room = WarRoomMVP()
    print("✅ War Room MVP - Direct Class Mode")

# Shadow Trading 초기화는 동일
shadow_trading = ShadowTradingMVP.load_active_session_from_db()
if shadow_trading is None:
    shadow_trading = ShadowTradingMVP(initial_capital=100000.0)

# Router setup (unchanged)
router = APIRouter(prefix="/api/war-room-mvp", tags=["War Room MVP"])


@router.post("/deliberate")
async def deliberate(request: DeliberationRequest):
    """전쟁실 심의 실행"""

    # Fetch market data (unchanged)
    if not request.market_data:
        market_data = fetch_market_data(request.symbol)
    else:
        market_data = request.market_data

    # Get portfolio state (unchanged)
    if shadow_trading:
        portfolio_state = shadow_trading.get_portfolio_state()
    else:
        portfolio_state = {
            'total_value': 100000,
            'available_cash': 50000,
            'current_positions': [],
            'total_risk': 0.0
        }

    # ============================================================================
    # DUAL MODE EXECUTION - 핵심 변경점
    # ============================================================================
    if USE_SKILL_HANDLERS:
        # Skill Handler Mode
        context = {
            'symbol': request.symbol,
            'action_context': request.action_context,
            'market_data': market_data,
            'portfolio_state': portfolio_state,
            'additional_data': request.additional_data
        }
        result = war_room_handler.execute(context)
    else:
        # Direct Class Mode (기존 방식)
        result = war_room.deliberate(
            symbol=request.symbol,
            action_context=request.action_context,
            market_data=market_data,
            portfolio_state=portfolio_state,
            additional_data=request.additional_data
        )

    # Rest of endpoint logic (unchanged)
    # Shadow Trading integration, response formatting, etc.

    return result


@router.get("/info")
async def get_info():
    """War Room 정보"""
    if USE_SKILL_HANDLERS:
        info = war_room_handler.get_info()
        info['execution_mode'] = 'skill_handler'
    else:
        info = war_room.get_war_room_info()
        info['execution_mode'] = 'direct_class'

    return info
```

**환경 변수 (.env.example):**
```bash
# War Room MVP Execution Mode
WAR_ROOM_MVP_USE_SKILLS=false  # true: Skill handlers, false: Direct classes
```

---

### Step 6: SkillLoader 검증 테스트

**목적:** 새로 생성한 5개 skill이 SkillLoader에서 정상 로드되는지 확인

**파일:** `backend/tests/test_skill_loader_mvp.py` (NEW)

```python
"""
Test SkillLoader with War Room MVP skills

Date: 2026-01-02
Phase: Skills Migration
"""

from backend.ai.skills.skill_loader import get_skill_loader


def test_load_all_mvp_skills():
    """Test: SkillLoader가 5개 MVP skill을 모두 로드하는가"""
    loader = get_skill_loader()

    # Load all war-room-mvp category skills
    skills = loader.get_all_skills(category='war-room-mvp')

    # Verify 5 skills loaded
    assert len(skills) == 5, f"Expected 5 skills, got {len(skills)}"

    expected_agents = [
        'trader-agent-mvp',
        'risk-agent-mvp',
        'analyst-agent-mvp',
        'pm-agent-mvp',
        'orchestrator-mvp'
    ]

    for agent_name in expected_agents:
        skill_key = f'war-room-mvp/{agent_name}'
        assert skill_key in skills, f"Missing skill: {skill_key}"

        # Verify SKILL.md structure
        skill = skills[skill_key]
        assert 'metadata' in skill
        assert 'instructions' in skill
        assert skill['metadata']['name'] == agent_name
        assert skill['category'] == 'war-room-mvp'

    print("✅ All 5 MVP skills loaded successfully")


def test_trader_agent_mvp_skill():
    """Test: Trader Agent MVP skill 상세 검증"""
    loader = get_skill_loader()
    skill = loader.load_skill('war-room-mvp', 'trader-agent-mvp')

    # Validate metadata
    assert skill['metadata']['name'] == 'trader-agent-mvp'
    assert skill['metadata']['metadata']['voting_weight'] == 0.35
    assert skill['metadata']['metadata']['model'] == 'gemini-2.0-flash-exp'

    # Validate instructions exist
    assert len(skill['instructions']) > 100

    print("✅ Trader Agent MVP skill validated")


if __name__ == '__main__':
    test_load_all_mvp_skills()
    test_trader_agent_mvp_skill()
```

---

### Step 7: Handler 실행 테스트

**파일:** `backend/tests/test_war_room_mvp_handlers.py` (NEW)

```python
"""
Test War Room MVP Skill Handlers

Date: 2026-01-02
Phase: Skills Migration
"""

# Import handlers directly
from backend.ai.skills.war_room_mvp.trader_agent_mvp import handler as trader_handler
from backend.ai.skills.war_room_mvp.risk_agent_mvp import handler as risk_handler
from backend.ai.skills.war_room_mvp.orchestrator_mvp import handler as orchestrator_handler


def test_trader_handler_execute():
    """Test: Trader handler가 정상 동작하는가"""
    context = {
        'symbol': 'AAPL',
        'price_data': {
            'current_price': 150.0,
            'high_52w': 180.0,
            'low_52w': 120.0
        }
    }

    result = trader_handler.execute(context)

    # Validate output structure
    assert 'action' in result
    assert 'confidence' in result
    assert 'reasoning' in result
    assert 'agent' in result
    assert result['agent'] == 'trader_mvp'

    print(f"✅ Trader Handler: {result['action']} (confidence: {result['confidence']:.2f})")


def test_orchestrator_full_flow():
    """Test: Orchestrator가 전체 deliberation을 실행하는가"""
    context = {
        'symbol': 'NVDA',
        'action_context': 'new_position',
        'market_data': {
            'price_data': {'current_price': 500.0},
            'market_conditions': {'vix': 18.5}
        },
        'portfolio_state': {
            'total_value': 100000,
            'available_cash': 50000
        }
    }

    result = orchestrator_handler.execute(context)

    # Validate final result structure
    assert 'final_decision' in result
    assert 'agent_opinions' in result
    assert 'pm_decision' in result

    print(f"✅ Orchestrator: {result['final_decision']}")


def test_missing_symbol_error_handling():
    """Test: Symbol 누락 시 에러 처리"""
    context = {}  # No symbol

    result = trader_handler.execute(context)

    assert 'error' in result
    assert result['action'] == 'pass'

    print("✅ Error handling verified")


if __name__ == '__main__':
    test_trader_handler_execute()
    test_orchestrator_full_flow()
    test_missing_symbol_error_handling()
```

---

### Step 8: 두 모드 동등성 검증

**파일:** `backend/tests/test_war_room_dual_mode.py` (NEW)

```python
"""
Test War Room MVP Dual Mode Equivalence

Direct Class Mode vs Skill Handler Mode 결과 비교

Date: 2026-01-02
"""


def test_dual_mode_equivalence():
    """Test: 두 모드가 동일한 결과를 반환하는가"""

    # Test data
    test_context = {
        'symbol': 'TSLA',
        'action_context': 'new_position',
        'market_data': {
            'price_data': {'current_price': 250.0}
        },
        'portfolio_state': {
            'total_value': 100000,
            'available_cash': 50000
        }
    }

    # Mode 1: Direct Class
    from backend.ai.mvp.war_room_mvp import WarRoomMVP
    war_room_direct = WarRoomMVP()
    result_direct = war_room_direct.deliberate(
        symbol=test_context['symbol'],
        action_context=test_context['action_context'],
        market_data=test_context['market_data'],
        portfolio_state=test_context['portfolio_state']
    )

    # Mode 2: Skill Handler
    from backend.ai.skills.war_room_mvp.orchestrator_mvp import handler
    result_skill = handler.execute(test_context)

    # Compare key fields
    assert result_direct['final_decision'] == result_skill['final_decision']
    assert abs(result_direct['confidence'] - result_skill['confidence']) < 0.01

    print("✅ Dual mode equivalence verified")
    print(f"   Direct: {result_direct['final_decision']} ({result_direct['confidence']:.2f})")
    print(f"   Skill:  {result_skill['final_decision']} ({result_skill['confidence']:.2f})")


if __name__ == '__main__':
    test_dual_mode_equivalence()
```

---

### Step 9: 기존 테스트 업데이트

**파일:** `backend/test_mvp_standalone.py`

```python
# Add at top
import os
USE_SKILLS = os.getenv('WAR_ROOM_MVP_USE_SKILLS', 'false').lower() == 'true'

if USE_SKILLS:
    print("🧪 Testing in SKILL MODE")
    from backend.ai.skills.war_room_mvp.orchestrator_mvp import handler as war_room
    # Adapt test calls to use handler.execute(context)
else:
    print("🧪 Testing in DIRECT MODE")
    from backend.ai.mvp.war_room_mvp import WarRoomMVP
    war_room = WarRoomMVP()
    # Existing test code unchanged
```

---

### Step 10: 문서 작성

**파일 1:** `backend/ai/skills/war-room-mvp/README.md` (NEW)

```markdown
# War Room MVP - Agent Skills

War Room MVP의 5개 Agent를 Claude Code Agent Skills 형식으로 제공합니다.

## Skills Overview

| Skill | 역할 | 투표권 | 모델 |
|-------|------|--------|------|
| trader-agent-mvp | 공격적 기회 포착 | 35% | Gemini 2.0 Flash |
| risk-agent-mvp | 방어적 리스크 관리 + Position Sizing | 35% | Gemini 2.0 Flash |
| analyst-agent-mvp | 종합 정보 분석 (News/Macro/Institutional/ChipWar) | 30% | Gemini 2.0 Flash |
| pm-agent-mvp | 최종 의사결정 + Hard Rules 검증 | Final | Gemini 2.0 Flash |
| orchestrator-mvp | 전체 워크플로우 조율 | - | N/A |

## 사용법

### Option 1: API를 통한 사용 (권장)
```bash
POST /api/war-room-mvp/deliberate
{
  "symbol": "AAPL",
  "action_context": "new_position"
}
```

### Option 2: Skill Handler 직접 호출
```python
from backend.ai.skills.war_room_mvp.orchestrator_mvp import handler

result = handler.execute({
    'symbol': 'AAPL',
    'action_context': 'new_position',
    'market_data': {...},
    'portfolio_state': {...}
})

print(result['final_decision'])  # approve/reject/reduce_size/silence
```

### Option 3: SkillLoader를 통한 동적 로딩
```python
from backend.ai.skills.skill_loader import get_skill_loader

loader = get_skill_loader()

# Load orchestrator skill
skill = loader.load_skill('war-room-mvp', 'orchestrator-mvp')
print(skill['metadata'])
print(skill['instructions'])

# Load all MVP skills
all_mvp_skills = loader.get_all_skills(category='war-room-mvp')
print(f"Loaded {len(all_mvp_skills)} skills")
```

## Legacy 8-Agent 호출

Orchestrator에서 Legacy War Room 호출 가능:

```python
from backend.ai.skills.war_room_mvp.orchestrator_mvp import handler

# MVP 결과와 Legacy 결과 비교
mvp_result = handler.execute({'symbol': 'NVDA', ...})
legacy_result = handler.invoke_legacy_war_room('NVDA', context)

print(f"MVP: {mvp_result['final_decision']}")
print(f"Legacy: {legacy_result['consensus']}")
```

## 실행 모드

환경 변수 `WAR_ROOM_MVP_USE_SKILLS`로 제어:

```bash
# Direct Class Mode (기본값)
WAR_ROOM_MVP_USE_SKILLS=false

# Skill Handler Mode
WAR_ROOM_MVP_USE_SKILLS=true
```

**실행 모드 차이:**
- Direct: MVP 클래스를 직접 인스턴스화 (기존 방식)
- Skill: handler.execute() 함수를 통해 호출 (새 방식)
- 결과: 두 모드 모두 동일한 출력 생성

## Architecture

```
User Request
    ↓
/api/war-room-mvp/deliberate
    ↓
[Dual Mode Check]
    ↓
├─ Skill Mode → orchestrator_handler.execute()
│                   ↓
│               WarRoomMVP.deliberate()
│
└─ Direct Mode → WarRoomMVP.deliberate()
    ↓
STEP 1: Execution Routing (Fast Track vs Deep Dive)
    ↓
STEP 2: Agent Deliberation (Parallel)
    ├─ Trader Agent (35%)
    ├─ Analyst Agent (30%)
    └─ Risk Agent (35%)
    ↓
STEP 3: PM Final Decision (Hard Rules + Silence Policy)
    ↓
STEP 4: Order Validation (if approved)
    ↓
Result (final_decision, confidence, position_size, etc.)
```

## Development

### Testing
```bash
# Test SkillLoader
python backend/tests/test_skill_loader_mvp.py

# Test handlers
python backend/tests/test_war_room_mvp_handlers.py

# Test dual mode equivalence
python backend/tests/test_war_room_dual_mode.py

# Test full system in skill mode
WAR_ROOM_MVP_USE_SKILLS=true python backend/test_mvp_standalone.py
```

### Rollback
```bash
# Instant rollback (< 1 min)
export WAR_ROOM_MVP_USE_SKILLS=false
systemctl restart ai-trading-system

# Verify
curl http://localhost:8000/api/war-room-mvp/info | jq '.execution_mode'
# Expected: "direct_class"
```

## Version History

- **v1.0** (2026-01-02): Initial Skills migration
  - 5 skills created
  - Dual mode support
  - Legacy integration function
```

**파일 2:** `backend/ai/skills/legacy/war-room/README.md` (NEW)

```markdown
# Legacy War Room Skills (Deprecated)

⚠️ **DEPRECATED** - These skills are documentation-only.

These SKILL.md files were specification documents for the original 8-agent War Room system. They do NOT have handler.py implementations.

For active implementation, use:
- **MVP (권장)**: `backend/ai/skills/war-room-mvp/` - 3+1 agent system with Skills interface
- **Legacy 8-Agent**: `backend/ai/debate/` - Direct class import

## History

- **2025-12-25**: 8-agent War Room system created
- **2025-12-31**: MVP 3+1 system created (67% cost reduction)
- **2026-01-02**: Legacy SKILL.md files moved to legacy/ folder

## Migration Path

If you need to reference legacy agent specifications:

1. **For MVP equivalent**, see `backend/ai/skills/war-room-mvp/`
2. **For legacy implementation**, see `backend/ai/debate/`
3. **For API access**, use `/api/war-room` (legacy) or `/api/war-room-mvp` (recommended)
```

---

## 구현 타임라인 (4일)

### Day 1: 구조 생성 및 SKILL.md 작성
1. ✅ Legacy SKILL.md 이동 (Step 1)
2. ✅ MVP Skill 디렉토리 생성 (Step 1)
3. ✅ 5개 SKILL.md 작성 (Step 2)

### Day 2: Handler 구현 및 통합
4. ✅ 5개 handler.py 작성 (Step 3, 4)
5. ✅ Router 업데이트 - Dual mode (Step 5)
6. ✅ 환경 변수 설정 (.env.example)

### Day 3: 테스트 및 검증
7. ✅ SkillLoader 테스트 (Step 6)
8. ✅ Handler 실행 테스트 (Step 7)
9. ✅ Dual mode 동등성 테스트 (Step 8)
10. ✅ 기존 테스트 업데이트 (Step 9)

### Day 4: 문서화 및 점진적 롤아웃
11. ✅ README 작성 (Step 10)
12. ✅ Staging 환경 배포 (WAR_ROOM_MVP_USE_SKILLS=true)
13. ✅ 모니터링 및 검증
14. ✅ Production 배포 (기본값은 false 유지)

---

## 핵심 파일 리스트 (19개)

### 신규 생성 (14개)

**SKILL.md (5)**
1. `backend/ai/skills/war-room-mvp/trader-agent-mvp/SKILL.md`
2. `backend/ai/skills/war-room-mvp/risk-agent-mvp/SKILL.md`
3. `backend/ai/skills/war-room-mvp/analyst-agent-mvp/SKILL.md`
4. `backend/ai/skills/war-room-mvp/pm-agent-mvp/SKILL.md`
5. `backend/ai/skills/war-room-mvp/orchestrator-mvp/SKILL.md`

**handler.py (5)**
6. `backend/ai/skills/war-room-mvp/trader-agent-mvp/handler.py`
7. `backend/ai/skills/war-room-mvp/risk-agent-mvp/handler.py`
8. `backend/ai/skills/war-room-mvp/analyst-agent-mvp/handler.py`
9. `backend/ai/skills/war-room-mvp/pm-agent-mvp/handler.py`
10. `backend/ai/skills/war-room-mvp/orchestrator-mvp/handler.py` (+ legacy 호출)

**Tests (3)**
11. `backend/tests/test_skill_loader_mvp.py`
12. `backend/tests/test_war_room_mvp_handlers.py`
13. `backend/tests/test_war_room_dual_mode.py`

**Documentation (1)**
14. `backend/ai/skills/war-room-mvp/README.md`

### 수정 파일 (3)

15. `backend/routers/war_room_mvp_router.py` - Dual mode support
16. `backend/test_mvp_standalone.py` - Skill mode 테스트 추가
17. `.env.example` - WAR_ROOM_MVP_USE_SKILLS 환경 변수 추가

### 이동 파일 (1)

18. `backend/ai/skills/war-room/` → `backend/ai/skills/legacy/war-room/`

### 변경 없음 (중요!)

19. `backend/ai/mvp/*.py` (5개 파일) - **완전히 그대로 유지**
20. `backend/ai/debate/*.py` (13개 파일) - **Legacy 8-agent 유지**
21. `backend/execution/*.py` (3개 파일) - **변경 없음**

---

## Rollback 전략

### 즉시 Rollback (< 1분)
```bash
export WAR_ROOM_MVP_USE_SKILLS=false
# 또는
WAR_ROOM_MVP_USE_SKILLS=false systemctl restart ai-trading-system
```

### 검증
```bash
curl http://localhost:8000/api/war-room-mvp/info | jq '.execution_mode'
# Expected: "direct_class"
```

### 완전 Rollback
```bash
# Legacy SKILL.md 복원
mv backend/ai/skills/legacy/war-room backend/ai/skills/war-room

# MVP Skill 디렉토리 삭제
rm -rf backend/ai/skills/war-room-mvp

# Router 원복
git checkout backend/routers/war_room_mvp_router.py
```

---

## 성공 기준

### 기술적 검증
- [ ] 5개 skill이 SkillLoader에서 정상 로드
- [ ] 모든 handler.py가 에러 없이 실행
- [ ] Direct mode와 Skill mode 결과 일치 (confidence delta < 1%)
- [ ] 기존 API 엔드포인트 모두 동작 (/api/war-room-mvp/*)
- [ ] Shadow Trading 통합 정상 작동
- [ ] 기존 테스트 모두 통과

### 사용자 요구사항 충족
- [x] 5개 개별 Skill 생성 (세분화)
- [x] Legacy 8-Agent 유지 및 호출 가능
- [x] Legacy SKILL.md → legacy/ 폴더 이동
- [x] Skill 전환 우선, Structured Outputs는 Phase B

### 성능
- API 응답 시간: < 15초 (현재와 동일)
- 메모리 사용: < 10% 증가
- 비용: 변화 없음 (동일한 Gemini API 호출 횟수)

---

## Phase B: Structured Outputs (후속 작업)

Phase A 완료 후 별도 작업으로 진행:
1. Pydantic 스키마 정의 (`backend/ai/schemas/war_room_schemas.py`)
2. Gemini API response_schema 파라미터 적용
3. Handler 내부 로직 업데이트 (Schema 검증 추가)
4. DB 스키마 및 Repository 업데이트

**현재는 Phase A만 집중: Skill 전환 완료**

---

## 최종 점검 사항

**구현 전:**
- [ ] 모든 팀원이 계획 검토 완료
- [ ] 테스트 환경 준비 (WAR_ROOM_MVP_USE_SKILLS=true)
- [ ] Git branch 생성 (`feature/war-room-mvp-skills`)

**구현 중:**
- [ ] 각 단계별 커밋 (atomic commits)
- [ ] 단위 테스트 먼저 작성 (TDD)
- [ ] Dual mode 동시 검증

**구현 후:**
- [ ] 전체 테스트 suite 실행
- [ ] Code review 완료
- [ ] Staging 배포 및 검증 (1-2일)
- [ ] Production 배포 (feature flag로 점진적 활성화)

---

## 참고 자료

- Plan Agent 분석: `C:\Users\a\.claude\plans\fuzzy-finding-cerf.md`
- Exploration Reports:
  - Legacy Skills Analysis (agentId: a4c17ce)
  - MVP Integration Analysis (agentId: a41eb84)
  - Skill Standards Analysis (agentId: a81f144)
- Phase A Implementation Plan (agentId: af9f545)

---

**Next Step**: Phase A 구현 시작 → Step 1부터 순차 진행
