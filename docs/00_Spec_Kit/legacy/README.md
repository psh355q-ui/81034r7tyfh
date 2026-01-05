# Legacy Documentation Archive

⚠️ **이 폴더는 Legacy 문서 보관소입니다.**

## 보관 정책

이 폴더의 문서들은 역사적 참고 자료로 유지되며, 더 이상 현재 시스템 상태를 반영하지 않습니다.

**현재 시스템 문서**: 상위 폴더 (`00_Spec_Kit/`) 참조
- [260104_Current_System_State.md](../260104_Current_System_State.md) ⭐ 최신 시스템 상태
- [260104_MVP_Architecture.md](../260104_MVP_Architecture.md) - MVP 아키텍처
- [260104_Database_Schema.md](../260104_Database_Schema.md) - 데이터베이스 스키마

---

## 보관된 문서

### 251210 시리즈 (2025-12-10 기준)
역사적 스냅샷 - 초기 시스템 설계 단계

- `251210_00_Project_Overview.md` - 프로젝트 개요
- `251210_01_System_Architecture.md` - 시스템 아키텍처
- `251210_02_Development_Roadmap.md` - 개발 로드맵
- `251210_03_Implementation_Status.md` - 구현 상태

### 251214 시리즈 (2025-12-14 기준)
통합 개발 계획

- `251214_Integrated_Development_Plan.md` - 통합 개발 계획

### 251215 시리즈 (2025-12-15 기준)
외부 시스템 분석 및 재설계

- `251215_External_Analysis_Index.md` - 외부 분석 인덱스
- `251215_External_System_Analysis.md` - 외부 시스템 분석
- `251215_MD_Files_Analysis.md` - MD 파일 분석
- `251215_Redesign_Executive_Summary.md` - 재설계 요약
- `251215_Redesign_Gap_Analysis.md` - Gap 분석
- `251215_System_Redesign_Blueprint.md` - 시스템 재설계 청사진

### 251228 시리즈 (2025-12-28 기준)
Legacy 8-Agent War Room 시스템

- `251228_War_Room_Complete.md` - War Room 완료 보고서 (8-Agent)

---

## 주요 변경 이력

### 2025-12-31: MVP 전환
- **8 Legacy Agents** → **3+1 MVP Agents**
- 비용: 67% 절감 ($0.105 → $0.035)
- 속도: 67% 향상 (30s → 10s)
- API 호출: 8회 → 3회

**MVP Agent 구성**:
- Trader MVP (35%) - Attack
- Risk MVP (35%) - Defense + Position Sizing
- Analyst MVP (30%) - Information
- PM Agent MVP - Final Decision + Hard Rules

**Legacy Agent 매핑**:
```
Legacy 8-Agent              →  MVP 3+1-Agent
─────────────────────────────────────────────
Trader (15%)                →  Trader MVP (35%)
ChipWar (12%)               ↗

Risk (20%)                  →  Risk MVP (35%)
Sentiment (8%)              ↗

News (10%)                  →  Analyst MVP (30%)
Macro (10%)                 ↗
Institutional (10%)         ↗
ChipWar geopolitics         ↗

PM (15%)                    →  PM Agent MVP (Final Decision)
```

---

## Legacy 코드 위치

Legacy 8-Agent 시스템은 여전히 코드베이스에 존재합니다:

**디렉토리**: `backend/ai/debate/`

**파일 목록** (13개):
1. `risk_agent.py` - Risk Agent (20%)
2. `trader_agent.py` - Trader Agent (15%)
3. `analyst_agent.py` - Analyst Agent (15%)
4. `chip_war_agent.py` - ChipWar Agent (12%)
5. `news_agent.py` - News Agent (10%)
6. `macro_agent.py` - Macro Agent (10%)
7. `institutional_agent.py` - Institutional Agent (10%)
8. `sentiment_agent.py` - Sentiment Agent (8%)
9. `pm_agent.py` - PM Agent (15%)
10. `war_room.py` - War Room Orchestrator
11. `agent_base.py` - Base Agent Class
12. `debate_manager.py` - Debate Manager
13. `voting_system.py` - Voting System

**호출 방법**:
```python
from backend.ai.debate.war_room import WarRoom

# Legacy 8-Agent War Room 실행
war_room = WarRoom()
result = war_room.deliberate(ticker='AAPL')
```

---

## 왜 Legacy로 분류되었나?

### 문제점
1. **높은 비용**: 8개 Agent × Gemini API = $0.105/deliberation
2. **느린 속도**: 평균 30초 응답 시간
3. **복잡한 구조**: 8개 Agent 관리 오버헤드
4. **중복 기능**: Agent 간 역할 중복 (ChipWar 분할 등)

### MVP의 장점
1. **비용 절감**: 3개 Agent × Gemini API = $0.035/deliberation (-67%)
2. **속도 향상**: 평균 10초 응답 시간 (-67%)
3. **단순화**: 명확한 Attack/Defense/Information 분리
4. **Position Sizing**: Risk Agent에 통합 (새로운 기능)
5. **Hard Rules**: PM Agent에 8개 검증 규칙 추가

---

## 유지 정책

**보관 사유**: 역사적 참고 자료, 기술적 의사결정 추적

**삭제 금지**: 이 폴더의 문서는 절대 삭제하지 마세요.

**업데이트 금지**: 이 폴더의 문서는 수정하지 마세요 (시간 스냅샷 보존).

**질문/이슈**: 상위 폴더의 최신 문서를 참조하세요.

---

**보관일**: 2026-01-04
**관리자**: AI Trading System Development Team
