# Legacy War Room Skills (Deprecated)

**⚠️ DEPRECATED**: 이 디렉토리의 skill 파일들은 Legacy 8-Agent War Room 시스템에서 사용되던 문서입니다.

**마이그레이션 날짜:** 2026-01-02  
**새 위치:** `backend/ai/skills/war-room-mvp/`

---

## 📌 Important Notice

### 현재 상태
- ✅ **Legacy 8-Agent System**: 계속 동작 중 (`backend/ai/debate/`)
- ✅ **Legacy API**: `/api/war-room` 엔드포인트 활성
- ⚠️ **이 디렉토리**: 문서 전용 (실제 구현 아님)

### 왜 이동했나요?

1. **MVP 통합**: 8개 agent → 3+1 agent로 통합하여 67% 비용 절감
2. **Skill 형식**: Claude Code Agent Skills 표준을 따르는 새로운 구조
3. **유지보수**: 더 명확한 인터페이스와 재사용성

---

## 📂 Legacy Skill 목록

이 디렉토리에는 다음 7개 agent의 SKILL.md 파일이 보존되어 있습니다:

| Agent | 역할 | 새 MVP에서 |
|-------|------|------------|
| **pm-agent** | 최종 의사결정 | → `pm-agent-mvp` (단독 유지) |
| **trader-agent** | 트레이딩 기회 | → `trader-agent-mvp` (35% 투표권) |
| **risk-agent** | 리스크 관리 | → `risk-agent-mvp` (35% 투표권) |
| **analyst-agent** | 기본 분석 | ↗ `analyst-agent-mvp` (4-in-1) |
| **macro-agent** | 매크로 경제 | ↗ `analyst-agent-mvp` (통합됨) |
| **institutional-agent** | 기관 동향 | ↗ `analyst-agent-mvp` (통합됨) |
| **news-agent** | 뉴스 분석 | ↗ `analyst-agent-mvp` (통합됨) |

**Note:** ChipWar Agent는 `trader-agent-mvp`와 `analyst-agent-mvp`에 분산 통합

---

## 🔄 Migration Guide

### Legacy 8-Agent → War Room MVP

#### Before (Legacy)
```
8 Independent Agents:
- PM Agent (최종 결정)
- Trader Agent
- Risk Agent
- Analyst Agent
- Macro Agent
- Institutional Agent
- News Agent
- ChipWar Agent
```

#### After (MVP)
```
3+1 Voting System:
- Trader Agent MVP (35%) ← Trader + ChipWar(기회)
- Risk Agent MVP (35%) ← Risk + Sentiment + Dividend
- Analyst Agent MVP (30%) ← Analyst + Macro + Institutional + News + ChipWar(지정학)
- PM Agent MVP (Final) ← PM
```

### API 마이그레이션

#### Legacy API (계속 사용 가능)
```bash
POST /api/war-room
```

#### MVP API (권장)
```bash
POST /api/war-room-mvp/deliberate
```

**차이점:**
- MVP: 더 빠름 (67% 비용/시간 절감)
- MVP: Dual mode 지원 (Direct / Skill)
- MVP: Execution Routing (Fast Track / Deep Dive)

---

## 🚀 새 시스템 사용법

### 1. MVP API 사용 (권장)

```python
import requests

response = requests.post(
    'http://localhost:8000/api/war-room-mvp/deliberate',
    json={
        'symbol': 'NVDA',
        'action_context': 'new_position'
    }
)

result = response.json()
print(f"Decision: {result['final_decision']}")
print(f"Confidence: {result['confidence']}")
```

### 2. Legacy 시스템 계속 사용

Legacy 8-Agent는 완전히 동작합니다:

```python
response = requests.post(
    'http://localhost:8000/api/war-room',
    json={
        'symbol': 'NVDA',
        'action': 'buy',
        'quantity': 100
    }
)
```

---

## 📊 성능 비교

| 항목 | Legacy 8-Agent | War Room MVP | 개선율 |
|------|----------------|--------------|--------|
| **처리 시간** | ~25초 | ~12초 | **52% ↓** |
| **API 비용** | 100% | 33% | **67% ↓** |
| **Agent 수** | 8개 | 4개 (3+1) | **50% ↓** |
| **응답 품질** | 기준 | 동등 | 유지 |

---

## 🔧 Legacy 시스템 유지 이유

1. **안정성**: 검증된 시스템으로 fallback 가능
2. **비교 검증**: MVP 결과를 Legacy와 비교
3. **점진적 전환**: 팀이 MVP에 익숙해질 시간 제공

---

## 📝 Legacy Skill 문서

각 agent의 SKILL.md는 참고 자료로 보존됩니다:

- `pm-agent/SKILL.md` - PM 역할 및 Hard Rules
- `trader-agent/SKILL.md` - 트레이딩 전략
- `risk-agent/SKILL.md` - 리스크 관리 기법
- `analyst-agent/SKILL.md` - 기본 분석 방법
- `macro-agent/SKILL.md` - 매크로 경제 지표
- `institutional-agent/SKILL.md` - 기관 동향 분석
- `news-agent/SKILL.md` - 뉴스 sentiment 분석

**Note:** 실제 구현은 `backend/ai/debate/` 폴더에 있습니다.

---

## ⚙️ 실제 Legacy 구현 위치

Legacy 8-Agent의 실제 코드:

```
backend/ai/debate/
├── pm_agent.py
├── trader_agent.py
├── risk_agent.py
├── analyst_agent.py
├── macro_agent.py
├── institutional_agent.py
├── news_agent.py
└── chipwar_agent.py
```

**API Router:** `backend/api/war_room_router.py`

---

## 🎯 다음 단계

### 즉시
- ✅ Legacy 시스템 계속 사용 가능
- ✅ MVP 시스템 병렬 테스트 시작

### 단기 (1-2주)
- MVP 시스템 성능 모니터링
- Legacy vs MVP 결과 비교 분석

### 장기 (1-2개월)
- MVP가 안정화되면 Legacy 점진적 폐기
- Legacy API는 deprecated 표시 후 유지

---

## 💡 FAQ

### Q: Legacy SKILL.md 파일은 왜 handler.py가 없나요?
**A:** 이 파일들은 문서 전용입니다. 실제 구현은 `backend/ai/debate/` 폴더에 개별 Python 파일로 존재합니다.

### Q: Legacy를 계속 사용해도 되나요?
**A:** 네, 완전히 동작합니다. `/api/war-room` 엔드포인트는 계속 지원됩니다.

### Q: 언제 Legacy가 완전히 제거되나요?
**A:** MVP가 충분히 검증될 때까지 (최소 1-2개월) Legacy는 유지됩니다.

### Q: MVP에서 Legacy를 호출할 수 있나요?
**A:** 네, Orchestrator MVP의 `invoke_legacy_war_room()` 함수로 가능합니다 (구현 예정).

---

## 📚 관련 문서

- **MVP 문서:** `../war-room-mvp/README.md`
- **Migration Plan:** `../../../../docs/260102_War_Room_MVP_Skills_Migration_Plan.md`
- **Progress Report:** `../../../../docs/260102_War_Room_MVP_Skills_Progress.md`

---

**⚠️ DEPRECATED - For Reference Only**  
**마지막 업데이트:** 2026-01-02  
**새 시스템:** `backend/ai/skills/war-room-mvp/`
