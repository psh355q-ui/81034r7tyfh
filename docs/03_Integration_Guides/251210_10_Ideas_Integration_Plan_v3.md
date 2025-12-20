# AI Trading System - 통합 아이디어 구현 계획

**작성일**: 2025-12-08  
**버전**: 3.0 (확정)  
**목표**: ChatGPT/Gemini 아이디어를 기존 시스템에 통합하여 자율 진화형 AI 헤지펀드 시스템 구축

---

## 📋 Executive Summary

현재 시스템은 **Phase E (Defensive Consensus System)**까지 100% 완료된 상태입니다. 
ChatGPT와 Gemini가 제안한 새로운 아이디어들을 분석하여 **7개 Phase**로 구성하고, 
**F1 → F6 순서**로 진행하기로 결정했습니다. F7은 Mini PC 구입 후 진행할 미래 아이디어로 보류합니다.

### 🎯 확정된 진행 순서

| 순서 | Phase | 영역 | 핵심 기능 | 예상 기간 |
|------|-------|------|----------|----------|
| 1️⃣ | **F1** | AI 집단지성 고도화 | AI 역할 계층화, 토론 로그 데이터화 | 1-2주 |
| 2️⃣ | **F2** | 글로벌 매크로 확장 | 국가별 매크로, 나비효과 그래프 | 2주 |
| 3️⃣ | **F3** | 한국 시장 특수 리스크 | 찌라시/정치테마 탐지 | 1주 |
| 4️⃣ | **F4** | 자율 진화 시스템 | 성과 학습, 가중치 자동 조정 | 2주 |
| 5️⃣ | **F5** | 프론트엔드 시각화 | 칩 효율 지도, 추론 뷰어 | 1-2주 |
| 6️⃣ | **F6** | 비용 최적화 | 모델 차익거래, Prompt Caching | 1-2주 |
| 🔮 | **F7** | 로컬 인프라 *(미래)* | Mini PC + NAS, Ollama | *하드웨어 구입 후* |

### 💳 사용자 구독 현황

| 서비스 | 상태 | 활용 방안 |
|--------|------|----------|
| **Claude Pro** | ✅ 구독 중 | Claude Code CLI, Prompt Caching |
| **Gemini Pro** | ✅ 구독 중 | Browser Use 자동화, 무료 API 쿼터 |

---

## 🏗️ 현재 시스템 상태

### ✅ 완료된 Phase

```
Phase 0-16:   데이터 인프라 (Feature Store, RAG, Incremental Update)
Phase A:      AI 칩 분석 시스템 (UnitEconomicsEngine)
Phase B:      자동화 + 매크로 리스크
Phase C:      고급 AI (백테스트/편향/토론)
Phase D:      실전 배포 API
Phase E:      Defensive Consensus System
  ├── E1: 3-AI Voting System (완료)
  ├── E2: DCA Strategy (완료)
  └── E3: Position Tracking (완료)
```

### 🎯 현재 핵심 모듈 위치

```
backend/
├── ai/
│   ├── consensus/           # 3-AI 투표 시스템
│   ├── strategies/          # DeepReasoningStrategy
│   ├── reasoning/           # Chain-of-Thought
│   ├── debate/              # AI 토론 엔진
│   └── economics/           # UnitEconomicsEngine
├── data/
│   ├── feature_store/       # Redis + TimescaleDB
│   ├── knowledge/           # ai_value_chain.py
│   └── vector_store/        # RAG 임베딩
└── skills/
    ├── intelligence/        # AI 스킬
    ├── market_data/         # 시장 데이터
    └── trading/             # 거래 스킬
```

---

## 🚀 Phase F1: AI 집단지성 고도화

> **출처**: ChatGPT 아이디어 (chat_gpt_ideas_251208.txt)

### 목표
AI들이 단순 예측을 넘어 **서로 논쟁하고, 학습하고, 진화**하는 구조 구축

### 신규 모듈

#### 1. AI 역할 계층화 (AI Role Hierarchy)
```
AI_ROLE:
  - Macro Strategist   (거시 환경 담당)
  - Sector Specialist  (섹터 로테이션 담당)
  - Risk Controller    (리스크 관리 전용)
  - Execution Optimizer (타이밍/체결 최적화)
  - Devil's Advocate   (반대 논리 전용)
```

**파일 위치**: `backend/ai/collective/ai_role_manager.py`

#### 2. 토론 로그 데이터화 (Debate Logger)
```python
# 저장 구조
DEBATE_HISTORY
- timestamp
- ticker
- ai_votes: {"claude": "BUY", "chatgpt": "SELL", "gemini": "HOLD"}
- final_decision
- pnl_result
- volatility_context
```

**파일 위치**: `backend/ai/meta/debate_logger.py`

#### 3. Decision Protocol (품질 검증기)
- JSON Schema 강제화
- Reasoning Depth Check (최소 50단어)
- 논리 키워드 검증 (because, therefore, etc.)
- 숫자/티커 근거 확인

**파일 위치**: `backend/ai/core/decision_protocol.py`

### 구현 파일 목록

| 파일 | 설명 | 작업 |
|------|------|------|
| `backend/ai/collective/ai_role_manager.py` | AI 역할 관리 | [NEW] |
| `backend/ai/collective/collective_decision_engine.py` | 집단 의사결정 | [NEW] |
| `backend/ai/meta/debate_logger.py` | 토론 로그 저장 | [NEW] |
| `backend/ai/meta/agent_weight_trainer.py` | 가중치 조정 | [NEW] |
| `backend/ai/core/decision_protocol.py` | 응답 검증기 | [NEW] |

### DB 스키마 추가
```sql
-- 토론 기록 테이블
CREATE TABLE debate_history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    ticker VARCHAR(20),
    ai_votes JSONB,
    final_decision VARCHAR(20),
    reasoning_log TEXT,
    pnl_result DECIMAL(12,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI 성과 테이블
CREATE TABLE ai_agent_performance (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(50),
    period DATE,
    win_rate DECIMAL(5,4),
    avg_return DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    current_weight DECIMAL(5,4),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🌍 Phase F2: 글로벌 매크로 확장

> **출처**: Gemini 아이디어 (gemini_ideas_251208.txt) + ChatGPT

### 목표
개별 종목 분석을 넘어 **글로벌 나비효과(Butterfly Effect)**를 추론하는 시스템

### 핵심 구조

```
Event: "일본 BOJ 금리 인상"
    ↓
JPY_STRENGTH (엔화 강세)
    ↓
US_TECH_LIQUIDITY (-0.8) ← 엔캐리 트레이드 청산
    ↓
KOSPI (-0.4) ← 글로벌 Risk-off
    ↓
매도 시그널: QQQ, TSM, KOSPI ETF
```

### 신규 모듈

#### 1. GlobalMarketMap (글로벌 시장 지도)
```python
# 자산 간 상관관계 정의
correlations = {
    "JPY_STRENGTH": [
        {"target": "US_TECH_LIQUIDITY", "corr": -0.8, "reason": "Yen carry trade unwind"},
        {"target": "KOSPI", "corr": -0.4, "reason": "Global risk-off"},
    ],
    "CRUDE_OIL": [
        {"target": "ENERGY_SECTOR", "corr": 0.9, "reason": "Revenue increase"},
        {"target": "AIRLINE_SECTOR", "corr": -0.8, "reason": "Fuel cost surge"},
    ]
}
```

**파일 위치**: `backend/ai/macro/global_market_map.py`

#### 2. GlobalMacroStrategy (나비효과 엔진)
- 매크로 이벤트 감지
- 그래프 BFS/DFS 탐색
- 영향 경로 및 가중치 산출
- 섹터별 매수/매도 시그널 생성

**파일 위치**: `backend/ai/strategies/global_macro_strategy.py`

#### 3. CountryRiskEngine (국가별 리스크 점수)
```python
# 핵심 국가 (1단계)
CORE_COUNTRIES = ["US", "JP", "CN", "EU"]

# 표준 데이터 스펙
CountryMacroData:
  - country_code
  - base_rate
  - bond_10y, bond_2y
  - yield_spread
  - cpi_yoy, ppi_yoy
  - currency_index
```

**파일 위치**: `backend/ai/macro/country_risk_engine.py`

### 데이터 소스

| 국가 | 소스 | 지표 |
|------|------|------|
| 🇺🇸 미국 | FRED API | 기준금리, 10Y/2Y, CPI, VIX |
| 🇯🇵 일본 | BOJ / FRED | 기준금리, JPY Index |
| 🇨🇳 중국 | WorldBank | GDP, PMI, 위안화 |
| 🇪🇺 유럽 | ECB | 기준금리, EU CPI |

### 구현 파일 목록

| 파일 | 설명 | 작업 |
|------|------|------|
| `backend/ai/macro/global_market_map.py` | 글로벌 상관관계 그래프 | [NEW] |
| `backend/ai/macro/global_event_graph.py` | 이벤트 전파 그래프 | [NEW] |
| `backend/ai/strategies/global_macro_strategy.py` | 매크로 전략 엔진 | [NEW] |
| `backend/ai/macro/country_risk_engine.py` | 국가별 리스크 점수 | [NEW] |
| `backend/data/macro/fred_global_collector.py` | 글로벌 데이터 수집 | [NEW] |
| `backend/data/models/global_macro.py` | Pydantic 스키마 | [NEW] |

---

## 🇰🇷 Phase F3: 한국 시장 특수 리스크

> **출처**: ChatGPT + Gemini 공통 제안

### 목표
정치테마주, 찌라시, 선반영 구조를 **AI가 정량적으로 감지**

### 핵심 로직

```
ThemeRiskScore =
  PriceSpikeScore (1일 +20%: +30점)
  + VolumeSpikeScore (5일 평균 400%: +25점)
  + No-DART-News Penalty (+30점)
  + CommunitySource Weight (+20점)

→ 70점 이상: 자동 경고
→ 85점 이상: 매수 금지 / 포지션 축소
```

### 감지 신호

| 신호 | 조건 | 점수 |
|------|------|------|
| 가격 급등 | 1일 +20% | +30 |
| 거래량 폭증 | 5일 평균 대비 400% | +25 |
| DART 공시 없음 | 공시 미존재 | +30 |
| 커뮤니티 출처 | 디시/블로그 뉴스 | +20 |
| 정치 키워드 | 대선/총선/관련주 | +15 |

### 구현 파일 목록

| 파일 | 설명 | 작업 |
|------|------|------|
| `backend/ai/risk/theme_risk_detector.py` | 테마주 리스크 탐지 | [NEW] |
| `backend/ai/risk/political_keyword_scanner.py` | 정치 키워드 스캐너 | [NEW] |
| `backend/data/collectors/dart_collector.py` | DART 공시 수집 | [MODIFY] |

---

## 🔄 Phase F4: 자율 진화 시스템

> **출처**: ChatGPT + Gemini 공통 제안

### 목표
AI가 **스스로 평가하고, 개선점을 만들어** 시스템이 진화

### 핵심 구조

```
Daily Review Cycle:
  1. 거래 로그 수집
  2. AI별 성과 분석 (Win Rate, Avg Return, Max DD)
  3. 가중치 자동 조정
  4. 전략 파라미터 제안

Weekly Strategy Refiner:
  1. 월간 매매 패턴 분석
  2. "반성문 및 개선안" 생성
  3. Config/Prompt 수정 제안
```

### 가중치 조정 공식

```python
new_weight = (
    (win_rate * 0.5)
    + (avg_return * 0.3)
    - (max_drawdown * 0.2)
)

# 하한/상한
agent.weight = max(0.1, min(new_weight, 3.0))
```

### 구현 파일 목록

| 파일 | 설명 | 작업 |
|------|------|------|
| `backend/analytics/performance_reviewer.py` | 일일 성과 리뷰 | [MODIFY] |
| `backend/ai/meta/strategy_refiner.py` | 전략 정제기 | [NEW] |
| `backend/ai/meta/agent_weight_trainer.py` | 가중치 조정 | [NEW] |
| `backend/monitoring/evolution_metrics.py` | 진화 메트릭 | [NEW] |

---

## 🎨 Phase F5: 프론트엔드 시각화

> **출처**: Gemini 아이디어

### 신규 컴포넌트

#### 1. ChipEfficiencyMap (칩 효율성 지도)
- X축: 가격, Y축: 성능 산점도
- Pareto Frontier (가성비 라인) 표시
- 클릭 시 UnitEconomics 상세 팝업

#### 2. ValueChainGraph (밸류체인 네트워크)
- React Flow 기반 노드-링크 다이어그램
- 뉴스 언급 시 관련 노드 하이라이트
- 실시간 관계 변화 애니메이션

#### 3. LogicTraceViewer (추론 과정 뷰어)
- 타임라인/아코디언 스타일
- Step별 추론 과정 표시
- 3-AI 토론 요약

#### 4. GlobalMacroPanel (글로벌 매크로 패널)
- 국가별 리스크 점수 대시보드
- 나비효과 전파 시각화
- 실시간 매크로 알림

### 구현 파일 목록

| 파일 | 설명 | 작업 |
|------|------|------|
| `frontend/src/pages/ChipAnalysis.tsx` | 칩 효율 분석 | [NEW] |
| `frontend/src/components/ChipEfficiencyMap.tsx` | 효율 지도 | [NEW] |
| `frontend/src/components/ValueChainGraph.tsx` | 밸류체인 그래프 | [NEW] |
| `frontend/src/components/LogicTraceViewer.tsx` | 추론 뷰어 | [NEW] |
| `frontend/src/pages/GlobalMacro.tsx` | 글로벌 매크로 | [NEW] |

---

## 📊 Skill Layer 통합 계획

### 현재 Skill 구조

```
backend/skills/
├── intelligence/    # AI 분석 스킬
├── market_data/     # 시장 데이터 스킬
├── technical/       # 기술적 분석
└── trading/         # 거래 실행
```

### 추가 Skill 제안

| Skill | 영역 | 기능 |
|-------|------|------|
| `GlobalMacroSkill` | Intelligence | 글로벌 매크로 분석 |
| `EventPropagationSkill` | Intelligence | 이벤트 전파 추론 |
| `ThemeRiskSkill` | Risk | 테마주 리스크 평가 |
| `DebateSkill` | Intelligence | AI 토론 관리 |
| `SelfEvolutionSkill` | Meta | 자율 학습/개선 |

---

## 📈 정보 임베딩 및 RAG 활용 계획

### 현재 RAG 상태
- ✅ SEC 문서 임베딩 (pgvector)
- ✅ 뉴스 벡터 검색
- ✅ Knowledge Graph (ai_value_chain.py)

### 확장 계획

#### 1. 글로벌 이벤트 임베딩
```sql
-- 이벤트 임베딩 테이블
CREATE TABLE event_embeddings (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    event_description TEXT,
    embedding VECTOR(1536),
    affected_sectors JSONB,
    impact_score DECIMAL(5,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 2. 토론 로그 임베딩
- 과거 토론 기록을 벡터화
- 유사한 상황의 과거 결정 참조
- 성공/실패 패턴 학습

#### 3. 매크로 컨텍스트 임베딩
- 국가별 경제 상황 벡터화
- 유사한 매크로 환경 검색
- 역사적 패턴 매칭

---

## 🗓️ 구현 로드맵

### Week 1-2: Phase F1 (AI 집단지성)
- [ ] AI 역할 관리자 구현
- [ ] 토론 로그 시스템 구축
- [ ] Decision Protocol 검증기 구현
- [ ] DB 스키마 추가

### Week 3-4: Phase F2 (글로벌 매크로)
- [ ] GlobalMarketMap 구현
- [ ] GlobalMacroStrategy 구현
- [ ] FRED Global Collector 확장
- [ ] 국가별 리스크 엔진 구현

### Week 5: Phase F3 (한국 시장 리스크)
- [ ] ThemeRiskDetector 구현
- [ ] 정치 키워드 스캐너 구현
- [ ] DART 연동 강화

### Week 6-7: Phase F4 (자율 진화)
- [ ] PerformanceReviewer 고도화
- [ ] StrategyRefiner 구현
- [ ] 가중치 자동 조정 시스템

### Week 8-9: Phase F5 (프론트엔드)
- [ ] ChipAnalysis 페이지
- [ ] GlobalMacro 대시보드
- [ ] LogicTraceViewer 컴포넌트

---

## ⚠️ User Review Required

> [!IMPORTANT]
> **결정이 필요한 사항들:**
> 1. Phase 우선순위: F1(AI 집단지성) vs F2(글로벌 매크로) 중 먼저 진행할 것?
> 2. 한국 시장 테마 리스크 탐지 임계값 (70점/85점) 적절한가?
> 3. 프론트엔드 기술 스택: React Flow vs D3.js 선호도?

> [!WARNING]
> **잠재적 리스크:**
> - 글로벌 데이터 수집 시 API 비용 증가 예상 (FRED 무료, 일부 유료)
> - AI 호출 3배 증가로 월 $15-30 예상 (현재 $3)

---

## 💰 Phase F6: 비용 최적화 전략 (Cost Optimization)

> **출처**: `ideas/new/AI 모델 비용 및 성능 비교 분석.md`, `ideas/new/API 사용량 절감 계획 수립.md`, `ideas/new/구독 모델(Fixed Cost) 활용방안.md`

### 목표
API 비용을 **90% 이상 절감**하면서 시스템 지능 유지

### ✅ 구독 모델 활용 (Claude Pro + Gemini Pro)

현재 **Claude Pro**와 **Gemini Pro** 구독 중이므로, 이를 최대한 활용하여 API 비용을 "0"에 가깝게 만들 수 있습니다.

#### Claude Code CLI 활용
```bash
# Claude Pro 구독 쿼터 내에서 무제한 사용
claude -p "이 뉴스가 포트폴리오에 미칠 영향 분석해서 report.md에 저장해"
```
- 복잡한 심층 분석 → 파일로 저장
- 장 마감 후 배치 작업에 최적
- API 비용: **$0** (구독료에 포함)

#### Gemini Pro 활용
- 무료 API 쿼터 (분당 15회)
- Browser Use로 웹 인터페이스 자동화
- 팩트 체크 및 Google Search 연동

### 핵심 전략

#### 1. 모델 차익거래 (Model Arbitrage)

| 작업 유형 | 추천 모델 (1순위) | 비용 | 기존 대비 절감 |
|----------|------------------|------|--------------|
| **일반/고속** | Gemini 2.0 Flash | $0.10/1M | 90%+ (GPT-4o 대비) |
| **심층 추론** | DeepSeek R1 | $0.55/1M | 80%+ (o1 대비) |
| **코딩/문맥** | Claude Pro (구독) | **$0** | 100% (구독 활용) |
| **보안/금융** | OpenAI / Gemini Enterprise | - | 비용보다 안전 |

#### 2. Prompt Caching 활용

```
Claude Prompt Caching:
- 기본 입력: $3.00/1M
- 캐시 쓰기: $3.75/1M (1.25배, 최초 1회)
- 캐시 읽기: $0.30/1M (10%, 재사용 시)

→ 10회 이상 호출 시 DeepSeek 수준 비용으로 SOTA 성능
```

#### 3. LLMLingua-2 프롬프트 압축

```python
from llmlingua import PromptCompressor

compressor = PromptCompressor(
    model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
    use_llmlingua2=True
)

# 원본의 33%만 남기고 압축 → 66% 토큰 절감
compressed = compressor.compress_prompt(context, rate=0.33)
```

#### 4. RedisVL 시맨틱 캐싱

```python
from redisvl.extensions.llmcache import SemanticCache

llmcache = SemanticCache(
    name="graphrag_cache",
    redis_url="redis://localhost:6379",
    distance_threshold=0.1,  # 의미적 유사도 임계값
    ttl=3600
)

# 유사 질문 캐시 적중 시 API 호출 0
if cached := llmcache.check(prompt=query):
    return cached['response']
```

#### 5. GraphRAG 동적 커뮤니티 선택

```bash
# 관련 없는 커뮤니티 배제 → 77% 토큰 절감
graphrag query \
  --dynamic-community-selection \
  --community-level 2
```

### 비용 절감 시뮬레이션

| 단계 | 적용 기술 | 절감 효과 | 누적 비용 지수 |
|------|----------|----------|--------------|
| Base | GPT-4o Only | 0% | 100 |
| Step 1 | 시맨틱 캐싱 | 20% | 80 |
| Step 2 | 동적 커뮤니티 선택 | 70% | 24 |
| Step 3 | LLMLingua-2 압축 | 66% | 8 |
| Step 4 | 모델 차익거래 | 90% | **0.8** |

### 구현 파일 목록

| 파일 | 설명 | 작업 |
|------|------|------|
| `backend/ai/optimization/model_router.py` | 하이브리드 모델 라우터 | [NEW] |
| `backend/ai/optimization/prompt_compressor.py` | LLMLingua-2 래퍼 | [NEW] |
| `backend/ai/optimization/semantic_cache.py` | RedisVL 시맨틱 캐시 | [NEW] |
| `backend/ai/optimization/prompt_caching.py` | Claude 캐싱 관리 | [NEW] |

---

## 🔮 Phase F7: 로컬 인프라 구축 (Local-First) - *미래 아이디어*

> **출처**: `ideas/new/나중에 내가 minipc를 구입하면 갈 방향_로컬 데이터 레이크 구축 및 용량 관리.md`

> [!NOTE]
> **상태**: Mini PC 구입 후 진행 예정 (현재 보류)
> **하드웨어 계획**: Mini PC + NAS 혼용 구성

### 목표
**API 비용 "0"**에 수렴하는 로컬 우선 아키텍처

### 아키텍처 개요

```
┌─────────────────────────────────────────────────────┐
│                  NAS / Mini PC                       │
├─────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  MinIO   │  │ LanceDB  │  │  Ollama  │          │
│  │ (Object) │  │ (Vector) │  │  (LLM)   │          │
│  │   9000   │  │  File    │  │  11434   │          │
│  └──────────┘  └──────────┘  └──────────┘          │
│       ↓              ↓              ↓               │
│  ┌──────────────────────────────────────────────┐  │
│  │         Python Data Manager                  │  │
│  │  - 뉴스 수집/저장                              │  │
│  │  - 벡터 인덱싱                                 │  │
│  │  - 의미론적 압축                               │  │
│  │  - 자율 보정 (Gap Detection)                  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 핵심 구성요소

#### 1. MinIO (객체 스토리지)
- S3 호환 로컬 스토리지
- raw-news 버킷: 원본 뉴스
- archive-news 버킷: 압축된 요약

#### 2. LanceDB (벡터 데이터베이스)
- 서버리스 (In-process)
- 디스크 기반 인덱싱 → RAM 절약
- NVMe SSD에서 고속 검색

#### 3. Ollama (로컬 LLM)
- DeepSeek-R1-Distill-Llama-8B
- 4-bit 양자화 → 5-6GB RAM
- API 비용 $0

### 의미론적 압축 (Semantic Compression)

```
원본 기사: 4KB
    ↓ LLM 요약 (3문장 + 태그 5개)
압축 객체: 300 Byte

압축률: 92% (13:1)
→ 10년 데이터 < 1TB 유지 가능
```

#### 수명주기 관리

| 단계 | 기간 | 저장소 | 처리 |
|------|------|--------|------|
| Hot | 0-90일 | MinIO raw + LanceDB Full | 원본 유지 |
| Cold | 91일+ | MinIO archive + LanceDB Summary | 요약 압축 |

### 로컬 우선 검색 (Check-Local-First)

```python
def retrieve_market_intel(ticker, date):
    # 1. 로컬 LanceDB 먼저 확인
    local = lancedb.query().where(f"ticker='{ticker}'").limit(10)
    
    if not local.empty:
        return local  # 비용 $0
    
    # 2. 로컬에 없을 때만 외부 API
    external = external_api.fetch(ticker, date)
    
    # 3. 자율 보정 - 외부 데이터를 로컬에 저장
    minio.save(external)
    lancedb.add(ollama.embed(external))
    
    return external
```

### 구독 모델 활용

```
┌─────────────────────────────────────────┐
│   Claude Pro / Gemini Advanced 구독     │
│         (월 $20 Fixed Cost)             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        Claude Code CLI (공식)           │
│   - 터미널에서 에이전트 실행             │
│   - 구독 쿼터 내 무제한 사용             │
│   - 복잡한 분석 → 파일 저장             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Browser Use (자동화)            │
│   - 로컬 LLM이 브라우저 조작            │
│   - Gemini 웹에서 질의응답              │
│   - API 비용 $0                         │
└─────────────────────────────────────────┘
```

### Docker Compose 예시

```yaml
version: '3.8'
services:
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9090"
    volumes:
      - /volume1/docker/minio/data:/data
    ports:
      - "9000:9000"
      - "9090:9090"

  ollama:
    image: ollama/ollama:latest
    volumes:
      - /volume1/docker/ollama:/root/.ollama
    ports:
      - "11434:11434"

  data_manager:
    build: ./app
    volumes:
      - /volume1/docker/lancedb:/data/lancedb
    depends_on:
      - minio
      - ollama
    environment:
      LANCEDB_URI: /data/lancedb
      MINIO_ENDPOINT: minio:9000
      OLLAMA_HOST: http://ollama:11434
```

### TCO 비교 (5년 기준)

| 항목 | 클라우드 | 로컬 NAS | 절감 |
|------|---------|---------|------|
| 스토리지 | $1,380 | $0 (하드웨어 포함) | 100% |
| API/송신 | $500+ | $0 | 100% |
| 벡터 DB | $4,200+ | $0 (LanceDB 무료) | 100% |
| LLM 추론 | $10,000+ | $100 (전기세) | 99% |
| **합계** | **$16,000+** | **$1,200** | **92%+** |

### 구현 파일 목록

| 파일 | 설명 | 작업 |
|------|------|------|
| `backend/data/local_lake/minio_client.py` | MinIO S3 클라이언트 | [NEW] |
| `backend/data/local_lake/lance_store.py` | LanceDB 래퍼 | [NEW] |
| `backend/data/local_lake/ollama_client.py` | Ollama 추론 클라이언트 | [NEW] |
| `backend/data/local_lake/lifecycle_manager.py` | 수명주기 관리 | [NEW] |
| `backend/data/local_lake/gap_detector.py` | 누락 감지/보정 | [NEW] |
| `docker/docker-compose.local-lake.yml` | 로컬 인프라 구성 | [NEW] |

---

## 🗓️ 확정된 구현 로드맵

```
┌──────────────────────────────────────────────────────────────────┐
│  F1 AI 집단지성  →  F2 글로벌 매크로  →  F3 한국 리스크          │
│     (Week 1-2)        (Week 3-4)          (Week 5)              │
│                                                                   │
│  F4 자율 진화   →  F5 프론트엔드  →  F6 비용 최적화             │
│    (Week 6-7)        (Week 8-9)       (Week 10-11)              │
│                                                                   │
│  ════════════════════════════════════════════════════           │
│  F7 로컬 인프라 (Mini PC 구입 후 진행)                           │
└──────────────────────────────────────────────────────────────────┘
```

### 1️⃣ Week 1-2: Phase F1 (AI 집단지성)
- [ ] AI 역할 관리자 구현
- [ ] 토론 로그 시스템 구축
- [ ] Decision Protocol 검증기 구현
- [ ] DB 스키마 추가 (debate_history, ai_agent_performance)

### 2️⃣ Week 3-4: Phase F2 (글로벌 매크로)
- [ ] GlobalMarketMap 구현
- [ ] GlobalMacroStrategy 구현
- [ ] FRED Global Collector 확장
- [ ] 국가별 리스크 엔진 구현

### 3️⃣ Week 5: Phase F3 (한국 시장 리스크)
- [ ] ThemeRiskDetector 구현
- [ ] 정치 키워드 스캐너 구현
- [ ] DART 공시 연동 강화

### 4️⃣ Week 6-7: Phase F4 (자율 진화)
- [ ] PerformanceReviewer 고도화
- [ ] StrategyRefiner 구현
- [ ] 가중치 자동 조정 시스템

### 5️⃣ Week 8-9: Phase F5 (프론트엔드)
- [ ] ChipAnalysis 페이지
- [ ] GlobalMacro 대시보드
- [ ] LogicTraceViewer 컴포넌트

### 6️⃣ Week 10-11: Phase F6 (비용 최적화)
- [ ] 모델 라우터 구현 (Gemini Flash, DeepSeek R1)
- [ ] Claude Code CLI 통합 (구독 활용)
- [ ] LLMLingua-2 압축 미들웨어
- [ ] RedisVL 시맨틱 캐시
- [ ] Claude Prompt Caching 적용

### 🔮 미래: Phase F7 (로컬 인프라)
> Mini PC + NAS 구입 후 진행
- [ ] Docker 인프라 구성
- [ ] MinIO + LanceDB + Ollama 배포
- [ ] 의미론적 압축 파이프라인
- [ ] 자율 보정 시스템

---

## ✅ 사용자 결정 사항 (확정)

| 항목 | 결정 |
|------|------|
| **Phase 순서** | F1 → F2 → F3 → F4 → F5 → F6 순서대로 진행 |
| **F7 상태** | 미래 아이디어로 보류 (Mini PC 구입 후) |
| **하드웨어 계획** | Mini PC + NAS 혼용 예정 |
| **구독 서비스** | Claude Pro ✅, Gemini Pro ✅ 활용 |

---

## 🔗 관련 문서

- [기존 통합 분석](file:///d:/code/ai-trading-system/docs/03_Integration_Guides/251210_09_AI_Ideas_Integration_Analysis.md)
- [시스템 아키텍처](file:///d:/code/ai-trading-system/docs/00_Spec_Kit/251210_01_System_Architecture.md)
- [RAG Foundation](file:///d:/code/ai-trading-system/docs/04_Feature_Guides/251210_rag-foundation-plan.md)
- [AI 모델 비용 분석](file:///d:/code/ai-trading-system/ideas/new/AI%20모델%20비용%20및%20성능%20비교%20분석.md)
- [API 사용량 절감](file:///d:/code/ai-trading-system/ideas/new/API%20사용량%20절감%20계획%20수립.md)
- [로컬 데이터 레이크](file:///d:/code/ai-trading-system/ideas/new/나중에%20내가%20minipc를%20구입하면%20갈%20방향_로컬%20데이터%20레이크%20구축%20및%20용량%20관리.md)

---

**작성**: AI Trading System Team  
**버전**: 2.0  
**마지막 업데이트**: 2025-12-08
