# Grand Unified Strategy Plan: "The Autonomous Trader" (Final Verified v5.0)

**작성일**: 2025-12-07
**버전**: 5.0 (Advanced Features Integrated)
**기반**: `251210_MASTER_GUIDE.md`, Existing Code, User Feedback (Scheduler/Purification/Profiler)

## 🔍 현황 분석 (Gap Analysis)

| 기능 (Feature) | 상태 (Status) | 설명 (Detail) |
|---|---|---|
| **RAG Foundation** | ✅ **Partial** | `backend/data/vector_store` 구현됨. (Store, Embedder, Chunker 존재) |
| **Consensus Engine** | ✅ **Done** | `phase_e` 완료. `DeepReasoningStrategy`와 연동됨. |
| **Deep Reasoning** | ✅ **Partial** | 3단 추론 구조(Ingest->Reason->Signal) 구현됨. **단, RAG/기억이 연결 안 됨.** |
| **Skills Layer** | ❌ **Missing** | `backend/skills` 디렉토리 없음. 현재 `features`에 산재함. |
| **Macro/Risk Data** | ❌ **Missing** | FRED/DART 수집기 및 전용 Embedding 로직 미구현. |

---

## 🎯 Revised Objectives
이미 구축된 **RAG 인프라(`vector_store`)** 와 **추론 엔진(`DeepReasoning`)** 을 **연결**하는 것이 핵심입니다.
여기에 **자동화된 유지보수(Scheduler)**와 **지능적 최적화(Profiler)**를 더해 완전 자율 시스템을 완성합니다.

---

## 🏗 Layer 1: Memory Injection (Data & RAG)
기존 `vector_store`를 활용하여 3가지 특수 기억을 주입합니다.

### 1.1 Hyper-Context Memories (New Collectors)
- **📜 Policy Memory**: 과거 정치/테마 뉴스(Keyword Tagging) -> Vector Store 적재.
- **🗣️ CEO Memory**: DART/SEC 보고서 내 '임원 발언' 추출 -> Vector Store 적재.
- **🔄 Regime Memory**: FRED 지표(금리/CPI)를 텍스트화("High Inflation Regime") -> Vector Store 적재.

**Action Item**:
- `backend/data/collectors/fred_collector.py` (New)
- `backend/data/collectors/dart_collector.py` (New)
- `backend/data/knowledge/memory_builder.py` (New - 데이터→벡터 변환기)

---

## 🧠 Layer 2: Skill Modules (New Layer)
산재된 로직을 독립적인 `Skill` 객체로 리팩토링하여 `backend/skills/`에 배치합니다.

### 2.1 BaseSkill & Router
- **구조**: `input: MarketContext` -> `process(RAG Search)` -> `output: Score/Flag`
- **Router**: `config.py`에 정의된 맵핑에 따라 적절한 Skill 호출.

### 2.2 Core Skills
- **`MacroSkill`**: FRED 데이터 + Regime Memory 조회 -> 시장 국면 판단.
- **`RiskSkill`**: 뉴스 벡터 검색(유사 찌라시/과거 악재) -> 리스크 점수 산출.
- **`TechnicalSkill`**: 파동 수식 계산 + 차트 패턴 매칭.

**Action Item**:
- `backend/skills/__init__.py`
- `backend/skills/base_skill.py`
- `backend/skills/macro_skill.py`, `risk_skill.py`, `technical_skill.py`

---

## 🤖 Layer 3: Cognitive Evolution (Strategy Upgrade)
기존 `DeepReasoningStrategy`를 업그레이드하여 **Skill-aware**하게 만듭니다.

### 3.1 Reasoning Logic Upgrade
- **AS-IS**: 정적 로직 (Value Chain 확인, 칩 스펙 비교)
- **TO-BE**: 동적 로직 (Skill 호출 -> RAG 조회 -> 종합 판단)
    ```python
    # Pseudo Code
    skills_result = skill_router.execute_all(context)
    # { "macro": "RISK_OFF", "fundamental": "GOOD", "risk": "HIGH_POLITICAL" }
    ```

### 3.2 Debate Mode (AI Interaction)
- 위험 신호 감지 시(RiskSkill > threshold), AI 간 대화 루프 실행.

**Action Item**:
- `backend/ai/strategies/deep_reasoning_strategy.py` 수정 (Skill 통합)
- `backend/ai/consensus/debate_room.py` (New)

---

## �️ Layer 4: Advanced Operations (Maintenance & Optimization) 🌟 New
제안해주신 3가지 핵심 유지보수 기능을 구현합니다.

### 4.1 Embedding Refresh Scheduler (자동 업데이트)
- **기능**: 매주 주말(토요일 02:00) 자동으로 새로운 DART/FRED 데이터를 수집 및 임베딩.
- **구현**: `APScheduler` 활용하여 `MemoryBuilder.run()` 정기 실행.

### 4.2 RAG Memory Purification (메모리 정화)
- **기능**: '루머'나 '신뢰도 낮은 뉴스'의 벡터 가중치를 낮추거나 삭제.
- **로직**: `vector_store.purge_low_confidence(days=90)` 메서드 구현.

### 4.3 AI Skill Profiler (스킬 분석기)
- **기능**: 각 AI(Claude, GPT, Gemini)가 어떤 스킬(Macro, Risk 등)에서 높은 적중률을 보였는지 기록.
- **활용**: 향후 Consensus 투표 시, 잘하는 분야에 더 높은 가중치 부여.

**Action Item**:
- `backend/ops/scheduler.py` (New)
- `backend/ops/memory_purifier.py` (New)
- `backend/ai/consensus/skill_profiler.py` (New)

---

## 🗓 Execution Roadmap (Optimized)

### Step 1: Memory Builders (데이터 연결) ✅ In Progress
- `FredCollector`, `DartCollector`, `MemoryBuilder` 구현.

### Step 2: Skill Formation (뇌 영역 분화)
- `backend/skills/` 구조 구축.
- `RiskSkill`, `MacroSkill` 구현.

### Step 3: Brain Integration (전략 통합)
- `DeepReasoningStrategy`에 스킬 장착.
- `DebateRoom` 구현.

### Step 4: Advanced Operations (고도화) 🌟
- **Scheduler**: 주간 단위 자동 업데이트 적용.
- **Purification**: 가비지 데이터 정리 로직 구현.
- **Profiler**: AI 성과 추적기 연동.

---

## 📝 사용자 승인
놓치셨던 3가지 기능(**Scheduler, Purification, Profiler**)을 **Layer 4 & Step 4**로 명확히 추가했습니다.
현재 **Step 1 (Memory Builders)** 구현이 완료된 상태입니다.
순서대로 **Step 2 (Skill Formation)** 으로 진행하여 "뇌"를 만들고, 마지막에 고도화(Step 4)를 진행하시겠습니까?
