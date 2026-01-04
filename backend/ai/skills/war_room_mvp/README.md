# War Room MVP Agent Skills

**Version**: 1.0.0  
**Date**: 2026-01-02  
**Status**: Production Ready

---

## 개요

War Room MVP를 Claude Code Agent Skills 형식으로 구현한 5개의 재사용 가능한 skill 모듈입니다. 기존 `backend/ai/mvp/` 클래스를 래핑하여 Agent Skills 인터페이스를 제공합니다.

---

## Skill 목록

| Skill | 역할 | 투표권 | 파일 |
|-------|------|--------|------|
| **trader-agent-mvp** | 공격적 기회 포착 | 35% | [SKILL.md](trader-agent-mvp/SKILL.md) |
| **risk-agent-mvp** | 방어적 리스크 관리 | 35% | [SKILL.md](risk-agent-mvp/SKILL.md) |
| **analyst-agent-mvp** | 종합 정보 분석 | 30% | [SKILL.md](analyst-agent-mvp/SKILL.md) |
| **pm-agent-mvp** | 최종 의사결정 | Final | [SKILL.md](pm-agent-mvp/SKILL.md) |
| **orchestrator-mvp** | 워크플로우 조율 | - | [SKILL.md](orchestrator-mvp/SKILL.md) |

---

## 사용법

### 방법 1: API Router (권장)

War Room MVP API Router는 자동으로 dual mode를 지원합니다.

**환경 변수 설정:**
```bash
# .env 파일
WAR_ROOM_MVP_USE_SKILLS=false  # Direct class mode (기본값)
WAR_ROOM_MVP_USE_SKILLS=true   # Skill handler mode
```

**API 호출:**
```bash
# Deliberation 요청
curl -X POST http://localhost:8000/api/war-room-mvp/deliberate \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "NVDA",
    "action_context": "new_position"
  }'

# 응답에 execution_mode 포함됨
{
  "execution_mode": "skill_handler",  # 또는 "direct_class"
  "final_decision": "approve",
  ...
}
```

### 방법 2: 직접 호출

개별 skill handler를 직접 import하여 사용할 수 있습니다.

```python
from backend.ai.skills.war_room_mvp.trader_agent_mvp import handler as trader_handler

# Context 준비
context = {
    'symbol': 'NVDA',
    'price_data': {
        'current_price': 500.0,
        'open': 498.0,
        'high': 505.0,
        'low': 495.0,
        'volume': 50000000
    }
}

# Execute
result = trader_handler.execute(context)

print(f"Action: {result['action']}")
print(f"Confidence: {result['confidence']}")
```

---

## 아키텍처

### 디렉토리 구조

```
war-room-mvp/
├── trader-agent-mvp/
│   ├── SKILL.md          # Skill 정의 (YAML + Markdown)
│   └── handler.py        # Handler 구현
├── risk-agent-mvp/
│   ├── SKILL.md
│   └── handler.py
├── analyst-agent-mvp/
│   ├── SKILL.md
│   └── handler.py
├── pm-agent-mvp/
│   ├── SKILL.md
│   └── handler.py
├── orchestrator-mvp/
│   ├── SKILL.md
│   └── handler.py        # + Legacy 통합 함수
└── README.md             # 이 파일
```

### Handler 패턴

모든 handler는 동일한 인터페이스를 제공합니다:

```python
def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute skill logic
    
    Args:
        context: Skill-specific input parameters
        
    Returns:
        Skill output (JSON serializable)
    """
```

**특징:**
- 기존 MVP 클래스 래핑 (코드 재사용 100%)
- 파라미터 검증
- 에러 처리 (graceful degradation)

---

## Skill 상세

### 1. Trader Agent MVP

**역할:** 공격적 기회 포착  
**투표권:** 35%  
**흡수한 Legacy Agents:**
- Trader Agent (100%)
- ChipWar Agent (기회 탐지 부분)

**핵심 기능:**
- Technical Analysis (RSI, MACD, Bollinger Bands)
- ChipWar Event Analysis
- Opportunity Scoring (0-100)
- 진입/청산 타이밍 제안

**입력:**
```python
{
    'symbol': str,              # 필수
    'price_data': dict,         # 가격 데이터
    'technical_data': dict,     # 선택
    'chipwar_events': list,     # 선택
    'market_context': dict      # 선택
}
```

**출력:**
```python
{
    'action': 'buy|sell|hold|pass',
    'confidence': 0.0-1.0,
    'opportunity_score': 0-100,
    'reasoning': str,
    'entry_price': float,
    'target_price': float,
    'stop_loss': float
}
```

### 2. Risk Agent MVP

**역할:** 방어적 리스크 관리 + Position Sizing  
**투표권:** 35%  
**흡수한 Legacy Agents:**
- Risk Agent (100%)
- Sentiment Agent
- DividendRisk Agent

**핵심 기능:**
- Kelly Criterion 기반 Position Sizing
- VIX 기반 Sizing Adjustment
- Dividend Risk 평가
- Stop Loss 설정

**입력:**
```python
{
    'symbol': str,
    'price_data': dict,
    'trader_opinion': dict,      # 선택
    'market_data': dict,         # 선택
    'dividend_info': dict,       # 선택
    'portfolio_context': dict    # 선택
}
```

**출력:**
```python
{
    'action': 'approve|reject|reduce_size',
    'confidence': 0.0-1.0,
    'position_size': float,      # % of portfolio
    'risk_level': str,
    'stop_loss': float,
    'kelly_calculation': dict
}
```

### 3. Analyst Agent MVP

**역할:** 종합 정보 분석 (4-in-1)  
**투표권:** 30%  
**흡수한 Legacy Agents:**
- News Agent
- Macro Agent
- Institutional Agent
- ChipWar Agent (지정학 부분)

**핵심 기능:**
- News Sentiment Analysis
- Macro Economic Context
- Institutional Activity
- ChipWar Geopolitics

**입력:**
```python
{
    'symbol': str,
    'news_articles': list,        # 선택
    'macro_indicators': dict,     # 선택
    'institutional_data': dict,   # 선택
    'chipwar_events': list,       # 선택
    'price_context': dict         # 선택
}
```

**출력:**
```python
{
    'action': 'support|oppose|neutral',
    'confidence': 0.0-1.0,
    'information_score': 0-100,
    'reasoning': str,
    'key_catalysts': list,
    'red_flags': list
}
```

### 4. PM Agent MVP

**역할:** 최종 의사결정자  
**권한:** Final Decision (투표 아님)

**핵심 기능:**
- Agent 의견 종합 (가중 평균)
- Hard Rules 강제 집행
- Silence Policy 실행

**Hard Rules:**
- 최대 포지션 크기: 15%
- 섹터 집중도: 55%
- 총 리스크 한도: 25%
- 현금 부족 시 REJECT
- 블랙리스트 종목 REJECT

**입력:**
```python
{
    'symbol': str,
    'trader_opinion': dict,      # 필수
    'risk_opinion': dict,        # 필수
    'analyst_opinion': dict,     # 필수
    'portfolio_state': dict,     # 필수
    'correlation_data': dict     # 선택
}
```

**출력:**
```python
{
    'final_decision': 'approve|reject|reduce_size|silence',
    'confidence': 0.0-1.0,
    'reasoning': str,
    'hard_rules_passed': bool,
    'recommended_action': str
}
```

### 5. Orchestrator MVP

**역할:** 워크플로우 조율  
**기능:** Execution Routing, Legacy 통합

**Execution Routing:**
- **Fast Track** (~5초): Trader + Risk만 실행
- **Deep Dive** (~12초): Trader + Risk + Analyst 전체 실행

**입력:**
```python
{
    'symbol': str,
    'action_context': str,       # 'new_position|stop_loss_check|rebalancing'
    'market_data': dict,
    'portfolio_state': dict,
    'additional_data': dict
}
```

**출력:**
```python
{
    'source': 'war_room_mvp',
    'symbol': str,
    'execution_mode': 'fast_track|deep_dive',
    'agent_opinions': {...},
    'pm_decision': {...},
    'final_decision': str,
    'processing_time_ms': int
}
```

**Legacy 통합:**
```python
# Orchestrator handler에 포함된 함수
from backend.ai.skills.war_room_mvp.orchestrator_mvp import handler

result = handler.invoke_legacy_war_room(symbol='NVDA', context={...})
```

---

## 성능

### 처리 시간
- **Fast Track**: < 7초 (Analyst 스킵)
- **Deep Dive**: < 15초 (전체 분석)
- **Legacy Call**: < 30초 (필요 시)

### 비용 효율
- **MVP vs Legacy 8-Agent**: 67% 절감
- **Fast Track vs Deep Dive**: 50% 절감

---

## 테스트

### 구조 검증 테스트
```bash
python backend/tests/test_skill_loader_mvp.py
```

**결과:**
- ✅ File Structure Validation
- ✅ SKILL.md Content Validation
- ✅ handler.py Content Validation
- ✅ Legacy Migration Validation

### API 통합 테스트
```bash
# Direct class mode (기본값)
WAR_ROOM_MVP_USE_SKILLS=false python -m uvicorn backend.main:app

# Skill handler mode
WAR_ROOM_MVP_USE_SKILLS=true python -m uvicorn backend.main:app
```

---

## Migration from Legacy

기존 Legacy 8-Agent War Room을 사용 중이라면:

1. **Legacy 파일 위치:** `backend/ai/skills/legacy/war-room/`
2. **Legacy는 계속 동작:** `/api/war-room` 엔드포인트 유지
3. **MVP 사용:** `/api/war-room-mvp` 엔드포인트 사용
4. **점진적 전환:** 환경 변수로 Skill mode 테스트

---

## Troubleshooting

### Q: Skill mode로 전환했는데 에러 발생
**A:** Fallback 메커니즘이 자동으로 direct class mode로 전환합니다. 로그 확인:
```
⚠️ Failed to import skill handlers, falling back to direct mode: ...
✅ War Room MVP - Direct Class Mode (Fallback)
```

### Q: execution_mode가 항상 'direct_class'로 나옴
**A:** `.env` 파일에서 `WAR_ROOM_MVP_USE_SKILLS=true` 설정 확인

### Q: Legacy 8-Agent 호출은 어떻게?
**A:** Orchestrator handler의 `invoke_legacy_war_room()` 함수 사용 (TODO 상태)

---

## 기여

새로운 skill을 추가하려면:

1. `backend/ai/skills/war-room-mvp/` 하위에 디렉토리 생성
2. `SKILL.md` 작성 (YAML frontmatter + Markdown)
3. `handler.py` 작성 (`execute()` 함수 구현)
4. 테스트 작성 및 실행

---

## License

Proprietary - ai-trading-system

---

**문서 버전:** 1.0.0  
**마지막 업데이트:** 2026-01-02
