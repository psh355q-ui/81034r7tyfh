# Market Intelligence v2.0 구현 로드맵

**작성일**: 2026-01-18
**버전**: 1.0
**참고**: docs/discussions/260118/ (Claude, ChatGPT, Gemini 토론 기반)

<!-- 
✅ 구현 완료 (2026-01-24)
- NewsFilter (2-Stage): backend/ai/intelligence/news_filter.py
- NarrativeStateEngine: backend/ai/intelligence/narrative_state_engine.py
- FactChecker: backend/ai/intelligence/fact_checker.py
- MarketConfirmation: backend/ai/intelligence/market_confirmation.py
- NarrativeFatigue: backend/ai/intelligence/narrative_fatigue.py
- ContrarySignal: backend/ai/intelligence/contrary_signal.py
- PolicyFeasibility: backend/ai/intelligence/policy_feasibility.py
- RegimeGuard: backend/ai/intelligence/regime_guard.py
- SemanticWeightAdjuster: backend/ai/intelligence/semantic_weight_adjuster.py
- InsightPostmortem: backend/ai/intelligence/insight_postmortem.py
-->

## 1. 개요

### 1.1 배경

`docs/discussions/260118/` 폴더에는 AI 3개(Claude, ChatGPT, Gemini)가 "Market Intelligence System" 설계에 대해 토론한 7개 문서가 있습니다. 이 로드맵은 토론 내용을 현재 `ai-trading-system` 프로젝트에 통합하기 위한 실행 계획입니다.

### 1.2 현재 시스템 상태

| 구성요소 | 현재 상태 | 비고 |
|---------|----------|------|
| **AI 에이전트** | MVP War Room (프로덕션) | Trader, Risk, Analyst 3개 + PM 최종 결정 |
| **Legacy 에이전트** | Debate Agents (R&D/폐지) | News, Macro, Risk, Trader, ChipWar, Sentiment, Skeptic |
| **뉴스 처리** | NewsIntelligenceAnalyzer → TradingSignal | 단일 흐름, Fact/Narrative 미분리 |
| **데이터베이스** | Repository Pattern 강제 | models.py 단일 진실 공급원 |

### 1.3 목표

**"소수몽키 스타일 시장 분석 자동화"**를 실전 시스템으로 격상

- 기존: 뉴스 요약 → 시그널 생성
- 목표: 뉴스 → Fact/Narrative 분리 → 시장 검증 → 학습 루프

---

## 2. 핵심 보완 컴포넌트 (11개)

| 우선순위 | 컴포넌트 | 출처 | 핵심 가치 |
|---------|---------|------|----------|
| **P0** | NarrativeStateEngine | ChatGPT | 팩트 vs 내러티브 분리 |
| **P0** | MarketConfirmation | ChatGPT | 가격 교차 검증 |
| **P0** | FactChecker | Gemini | Hallucination 방지 |
| **P0** | NewsFilter (2-Stage) | Gemini | 비용 최적화 |
| **P1** | NarrativeFatigue | ChatGPT | 과열 탐지 |
| **P1** | ContrarySignal | ChatGPT | 쏠림 경고 |
| **P1** | HorizonTagger | ChatGPT | 시간축 분리 |
| **P1** | ChartGenerator | Gemini | 시각화 자동화 |
| **P2** | PolicyFeasibility | ChatGPT | 정책 실현 확률 |
| **P2** | InsightPostMortem | ChatGPT+Gemini | 학습 피드백 루프 |
| **P2** | PersonaTuning | Gemini | 소수몽키 톤앤매너 |

---

## 3. 아키텍처 변경 사항

### 3.1 기존 파이프라인

```
News → Processing → TradingSignal
```

### 3.2 새로운 파이프라인

```
News → Filter(2-stage) → Intelligence → Narrative → FactCheck → MarketConfirm → Signal
```

### 3.3 새로운 디렉토리 구조

```
backend/ai/intelligence/
├── __init__.py
├── base.py                    # Base intelligence interface
├── news_filter.py            # 2-stage filtering (P0)
├── fact_checker.py           # Numeric verification (P0)
├── narrative_state_engine.py # Fact/narrative separation (P0)
├── market_confirmation.py    # Price action verification (P0)
├── narrative_fatigue.py      # Detection of overheating (P1)
├── contrary_signal.py        # Crowding warnings (P1)
├── horizon_tagger.py         # Time horizon classification (P1)
├── policy_feasibility.py     # Policy realization probability (P2)
└── insight_postmortem.py    # Feedback loop (P2)
```

---

## 4. 데이터베이스 스키마 확장

### 4.1 NewsArticle 모델 확장

```python
# 기존 필드 유지 + 새로운 필드 추가
class NewsArticle(Base):
    # ... 기존 필드 ...

    # NEW: Narrative tracking (ChatGPT P0)
    narrative_phase = Column(String(20), nullable=True)  # EMERGING, ACCELERATING, CONSENSUS, FATIGUED, REVERSING
    narrative_strength = Column(Float, nullable=True)     # 0.0 ~ 1.0
    narrative_consensus = Column(Float, nullable=True)    # 0.0 ~ 1.0

    # NEW: Fact verification (Gemini P0)
    fact_verification_status = Column(String(20), nullable=True)  # VERIFIED, PARTIAL, MISMATCH, UNVERIFIED
    fact_confidence_adjustment = Column(Float, default=0.0)       # -0.2 ~ +0.1

    # NEW: Market confirmation (ChatGPT P0)
    price_correlation_score = Column(Float, nullable=True)  # -1.0 ~ 1.0
    confirmation_status = Column(String(20), nullable=True)  # CONFIRMED, DIVERGENT, LEADING, NOISE

    # NEW: Enhanced tagging
    narrative_tags = Column(ARRAY(String), nullable=True)   # Fact vs Narrative 태그
    horizon_tags = Column(ARRAY(String), nullable=True)     # SHORT, MEDIUM, LONG
```

### 4.2 새로운 테이블 (11개 컴포넌트용)

```sql
-- 내러티브 상태 추적 (ChatGPT P0)
CREATE TABLE narrative_states (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(50) NOT NULL,
    fact_layer TEXT,
    narrative_layer TEXT,
    market_expectation TEXT,
    expectation_gap FLOAT,
    phase VARCHAR(20),
    change_velocity FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 시장 확인 로그 (ChatGPT P0)
CREATE TABLE market_confirmations (
    id SERIAL PRIMARY KEY,
    theme VARCHAR(50) NOT NULL,
    news_intensity FLOAT,
    price_momentum FLOAT,
    volume_anomaly FLOAT,
    signal VARCHAR(20),
    divergence_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 내러티브 피로도 (ChatGPT P1)
CREATE TABLE narrative_fatigue (
    id SERIAL PRIMARY KEY,
    theme VARCHAR(50) NOT NULL,
    fatigue_score FLOAT,
    signal VARCHAR(20),
    mention_growth FLOAT,
    price_response FLOAT,
    new_info_ratio FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 역발상 시그널 (ChatGPT P1)
CREATE TABLE contrary_signals (
    id SERIAL PRIMARY KEY,
    theme VARCHAR(50) NOT NULL,
    crowding_level VARCHAR(20),
    contrarian_signal VARCHAR(30),
    indicators JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 정책 실현 확률 (ChatGPT P2)
CREATE TABLE policy_feasibility (
    id SERIAL PRIMARY KEY,
    policy_name VARCHAR(255) NOT NULL,
    feasibility_score FLOAT,
    factors JSONB,
    risks TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- 시간축 태깅 (ChatGPT P1)
CREATE TABLE horizon_tags (
    id SERIAL PRIMARY KEY,
    insight_id INTEGER REFERENCES insights(id),
    short_term TEXT,
    mid_term TEXT,
    long_term TEXT,
    recommended_horizon VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 인사이트 사후 분석 (ChatGPT+Gemini P2)
CREATE TABLE insight_reviews (
    id SERIAL PRIMARY KEY,
    insight_id INTEGER REFERENCES insights(id),
    predicted_direction VARCHAR(20),
    actual_outcome_7d FLOAT,
    actual_outcome_30d FLOAT,
    success BOOLEAN,
    accuracy_score FLOAT,
    failure_reason TEXT,
    lesson_learned TEXT,
    reviewed_at TIMESTAMP DEFAULT NOW()
);

-- 사용자 피드백 (Gemini P2 - Active Learning)
CREATE TABLE user_feedback_intelligence (
    id SERIAL PRIMARY KEY,
    insight_id INTEGER REFERENCES insights(id),
    feedback_type VARCHAR(20),  -- 'WRONG_THEME', 'BAD_SUMMARY', 'GOOD'
    user_comment TEXT,
    corrected_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 프롬프트 버전 관리 (Gemini P2)
CREATE TABLE prompt_versions (
    id SERIAL PRIMARY KEY,
    prompt_name VARCHAR(100) NOT NULL,
    version INTEGER DEFAULT 1,
    prompt_text TEXT NOT NULL,
    performance_score FLOAT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 생성된 차트 로그 (Gemini P1)
CREATE TABLE generated_charts (
    id SERIAL PRIMARY KEY,
    chart_type VARCHAR(50),
    parameters JSONB,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. Legacy Agent 재사용/재작성 결정

| Legacy 컴포넌트 | 재사용 여부 | 이유 |
|----------------|-----------|------|
| **NewsIntelligenceAnalyzer** | ✅ 재사용 + 확장 | Narrative 분석 후 훅 추가 |
| **NewsAutoTagger** | ✅ 재사용 + 확장 | Horizon/Fact 태그 추가 |
| **EmbeddingEngine** | ✅ 유지 | 시맨틱 검색용 |
| **Debate Agents** | ❌ 폐지 | MVP로 이미 대체됨 |
| **Consensus Engine** | ❌ 폐지 | MVP 투표로 대체됨 |

---

## 6. 단계별 구현 로드맵

### Phase 1: P0 핵심 컴포넌트 (Week 1-2)

#### 1.1 NewsFilter (2-Stage) - Gemini P0

**목적**: 비용 최적화 (90% 절감)

```python
# backend/ai/intelligence/news_filter.py
class NewsFilter:
    """2단계 필터링으로 비용 90% 절감"""

    def __init__(self):
        self.light_model = "gpt-4o-mini"  # $0.15/1M tokens
        self.heavy_model = "claude-sonnet"  # $3/1M tokens

    async def stage1_relevance_check(self, headline: str) -> bool:
        """제목만 보고 투자 관련성 판단 (Yes/No)"""
        # 구현 상세는 v2.0 설계 문서 참조

    async def stage2_deep_analysis(self, article: Dict) -> Dict:
        """통과한 뉴스만 정밀 분석"""
        # 기존 NewsIntelligenceAnalyzer 호출
```

**작업 항목**:
- [ ] NewsFilter 클래스 구현
- [ ] Stage 1 관련성 체크 로직
- [ ] Stage 2 기존 파이프라인 연동
- [ ] 비용 추적 로그 추가
- [ ] 테스트 케이스 작성

#### 1.2 NarrativeStateEngine - ChatGPT P0

**목적**: 팩트(사실)와 내러티브(해석)의 분리

```python
# backend/ai/intelligence/narrative_state_engine.py
class NarrativeStateEngine:
    """팩트와 내러티브를 분리하여 추적하는 엔진"""

    NARRATIVE_PHASES = {
        "EMERGING": "새로운 내러티브 형성 중",
        "ACCELERATING": "확산 및 가속",
        "CONSENSUS": "시장 컨센서스 형성",
        "FATIGUED": "피로감/둔화",
        "REVERSING": "반전 조짐"
    }

    async def analyze_news(self, news_tags: Dict) -> NarrativeState:
        """뉴스 태그에서 팩트/내러티브 분리"""

    async def detect_narrative_shift(self, topic: str, days: int = 7) -> Optional[Dict]:
        """내러티브 변화 감지"""
```

**작업 항목**:
- [ ] NarrativeStateEngine 클래스 구현
- [ ] NarrativePhase enum 정의
- [ ] 내러티브 변화 감지 로직
- [ ] narrative_states 테이블 마이그레이션
- [ ] NewsArticle 모델 확장

#### 1.3 FactChecker - Gemini P0

**목적**: LLM Hallucination 방지 (수치 교차 검증)

```python
# backend/ai/intelligence/fact_checker.py
class FactChecker:
    """LLM이 추출한 정량 정보를 실제 데이터와 교차 검증"""

    def __init__(self):
        self.yfinance = YFinanceClient()
        self.sec_api = SECEdgarClient()
        self.fred = FREDClient()

    async def verify_earnings(self, ticker: str, extracted: Dict) -> Dict:
        """실적 관련 수치 검증"""

    async def verify_policy_numbers(self, policy_type: str, extracted: Dict) -> Dict:
        """정책 관련 수치 검증"""

    async def verify_all(self, news_tags: Dict) -> Dict:
        """모든 검증 가능한 수치 종합 검증"""
```

**작업 항목**:
- [ ] FactChecker 클래스 구현
- [ ] YFinance/SEC/FRED API 연동
- [ ] 수치 검증 로직 (허용 오차 ±5%)
- [ ] NewsArticle 모델에 verification 필드 추가
- [ ] 외부 API 모의 테스트 (Mock)

#### 1.4 MarketConfirmation - ChatGPT P0

**목적**: 뉴스와 시장 가격의 교차 검증

```python
# backend/ai/intelligence/market_confirmation.py
class MarketConfirmationEngine:
    """뉴스 강도와 시장 반응을 교차 검증"""

    THEME_TO_PROXY = {
        "DEFENSE": ["ITA", "SHLD", "LMT", "RTX"],
        "AI_TECH": ["SOXX", "SMH", "NVDA", "AMD"],
        "GEOPOLITICS": ["GLD", "SLV", "XLE", "REMX"],
    }

    async def analyze(self, theme: str, news_stats: Dict, days: int = 7) -> MarketConfirmation:
        """테마별 뉴스-시장 교차 분석"""
```

**작업 항목**:
- [ ] MarketConfirmationEngine 클래스 구현
- [ ] 프록시 자산 매핑 (테마 → ETF/종목)
- [ ] 시그널 판정 로직 (CONFIRMED, DIVERGENT, LEADING, NOISE)
- [ ] market_confirmations 테이블 마이그레이션
- [ ] 기존 StockPrice 테이블 연동

---

### Phase 2: P1 고급 분석 (Week 3-4)

#### 2.1 NarrativeFatigue - ChatGPT P1

**목적**: 테마 과열/피크 탐지

```python
# backend/ai/intelligence/narrative_fatigue.py
class NarrativeFatigueDetector:
    """
    테마 피로도 탐지

    공식: fatigue_score = mention_growth - price_response - new_info_ratio
    """

    async def analyze(self, theme: str, days: int = 30) -> FatigueAnalysis:
        """테마 피로도 분석"""
```

#### 2.2 ContrarySignal - ChatGPT P1

**목적**: 시장 쏠림/과열 경고

```python
# backend/ai/intelligence/contrary_signal.py
class ContrarySignalDetector:
    """
    역발상 시그널 탐지

    탐지 대상: ETF 자금 유입 급증, 감성 극단값, 포지션 쏠림
    """
```

#### 2.3 HorizonTagger - ChatGPT P1

**목적**: 시간축별 인사이트 분리

```python
# backend/ai/intelligence/horizon_tagger.py
class HorizonTagger:
    """
    동일 인사이트를 시간축별로 재해석

    - 단기: 1~5일 (트레이더용)
    - 중기: 2~6주 (스윙용)
    - 장기: 6~18개월 (테마투자용)
    """
```

#### 2.4 ChartGenerator - Gemini P1

**목적**: 소수몽키 스타일 시각화 자동 생성

```python
# backend/visualization/chart_generator.py
class ChartGenerator:
    """
    소수몽키 스타일 시각 자료 자동 생성

    생성 차트: 테마 버블 차트, 지정학 타임라인, 섹터 퍼포먼스 바 차트
    """
```

---

### Phase 3: P2 학습 및 피드백 (Week 5-6)

#### 3.1 PolicyFeasibility - ChatGPT P2

**목적**: 정책 발언의 실현 확률 계산

```python
# backend/ai/intelligence/policy_feasibility.py
class PolicyFeasibilityAnalyzer:
    """
    정책 발언의 실현 확률 계산

    공식: feasibility = presidential_power + congressional_alignment + historical_precedent - opposition_strength
    """
```

#### 3.2 InsightPostMortem - ChatGPT+Gemini P2

**목적**: 인사이트 결과 복기 및 학습

```python
# backend/ai/intelligence/insight_postmortem.py
class InsightPostMortemEngine:
    """
    인사이트 사후 분석 및 학습 엔진

    "맞았는지 틀렸는지 복기 없이는 시스템이 진화할 수 없다"
    """
```

#### 3.3 PersonaTuning - Gemini P2

**목적**: 소수몽키 톤앤매너 완벽 재현

```python
# backend/ai/intelligence/prompts/persona_tuned_prompts.py
SOSUMONKEY_PERSONA = """
당신은 '소수몽키'라는 페르소나를 가진 주식 시장 분석가입니다.

1. 두괄식 결론
2. 연결고리 강조
3. 쉬운 비유
4. 객관적 데이터 기반
5. 반대 의견 제시
"""
```

---

## 7. Reality Layer 보완 (ChatGPT 결론 기반)

### 7.1 RegimeGuard (Reality Risk 1)

**목적**: "정답처럼 보이는 잘못된 일관성" 방지

```python
# backend/ai/intelligence/regime_guard.py
class RegimeGuard:
    """
    체제 전환(Regime Change) 탐지

    IF 상관관계 급변 OR 기존 승률 급락 OR 과거 패턴 설명력 붕괴
    THEN 판단 보류, 신호 강도 자동 축소
    """
```

### 7.2 SemanticWeightAdjuster (Reality Risk 2)

**목적**: 정성 → 정량 변환 왜곡 방지

```python
# backend/ai/intelligence/semantic_weight_adjuster.py
class SemanticWeightAdjuster:
    """
    의미 과대 해석 방지

    공식: semantic_weight = narrative_intensity / market_novelty
    """
```

### 7.3 반대 시나리오 강제 표시 (Reality Risk 3)

**목적**: 사용자가 '판단 책임'을 AI에게 넘기는 것 방지

```python
# 모든 출력에 포함할 필수 항목
{
    "headline": "결론",
    "contrarian_view": "반대 시나리오",
    "invalidation_conditions": ["무효화 조건1", "무효화 조건2"],
    "failure_triggers": ["이 판단이 깨지는 트리거"]
}
```

---

## 8. 통합 파이프라인 설계

```python
# backend/ai/intelligence/enhanced_news_pipeline.py
class EnhancedNewsProcessingPipeline:
    """Market Intelligence v2.0 파이프라인"""

    def __init__(self):
        # Stage 1: 필터링 & 검증
        self.news_filter = NewsFilter()          # NEW: 비용 최적화
        self.intelligence_analyzer = NewsIntelligenceAnalyzer()
        self.narrative_engine = NarrativeStateEngine()  # NEW
        self.fact_checker = FactChecker()          # NEW

        # Stage 2: 패턴 감지 (4중 검증)
        self.market_confirmation = MarketConfirmation()  # NEW
        self.narrative_fatigue = NarrativeFatigue()     # NEW
        self.contrary_signal = ContrarySignal()         # NEW

        # Stage 3: 인사이트 생성
        self.horizon_tagger = HorizonTagger()      # NEW
        self.policy_feasibility = PolicyFeasibility()  # NEW

        # Stage 4: 피드백 루프
        self.postmortem = InsightPostMortemEngine()    # NEW

    async def process_article(self, article_id: int):
        """향상된 뉴스 처리 흐름"""
        # 1. 2-stage 필터링
        filtered = await self.news_filter.filter_stage1(article_id)
        if not filtered:
            return False

        # 2. Intelligence 분석
        analyzed = await self.intelligence_analyzer.analyze(article_id)

        # 3. Fact/Narrative 분리
        narrative = await self.narrative_engine.separate_facts_and_narrative(analyzed)

        # 4. 수치 검증
        verified = await self.fact_checker.verify_numerics(narrative)

        # 5. 시장 검증 (4중)
        confirmed = await self.market_confirmation.verify_price_correlation(verified)
        fatigue = await self.narrative_fatigue.analyze(confirmed.theme)
        contrary = await self.contrary_signal.analyze(confirmed.theme)

        # 6. 시간축 분리
        horizon = await self.horizon_tagger.tag_horizons(confirmed)

        # 7. 정책 실현 확률
        feasible = await self.policy_feasibility.analyze(confirmed)

        # 8. 최종 인사이트 저장
        insight = await self._save_insight({
            "original": confirmed,
            "horizon": horizon,
            "fatigue": fatigue,
            "contrary": contrary,
            "feasible": feasible
        })

        return insight
```

---

## 9. 구현 순서 (Gemini 제안: 심리적 지속성 기준)

### Week 1: 빠른 성공 (Quick Win)

1. **NewsFilter (2-Stage)**: 1주 차에 텔레그램으로 "소수몽키 스타일 메시지" 도착
2. **FactChecker**: 신뢰도 향상

### Week 2-3: 핵심 기능

3. **NarrativeStateEngine**: Fact/Narrative 분리
4. **MarketConfirmation**: 시장 검증

### Week 4-5: 고급 기능

5. **NarrativeFatigue**: 과열 탐지
6. **ContrarySignal**: 쏠림 경고
7. **HorizonTagger**: 시간축 분리

### Week 6-8: 학습 및 시각화

8. **ChartGenerator**: 시각화 자동화
9. **InsightPostMortem**: 피드백 루프
10. **RegimeGuard**: Reality Layer

---

## 10. 다음 단계

### 10.1 즉시 시작할 작업

1. **데이터베이스 마이그레이션 스크립트 작성**
   - narrative_states 테이블
   - market_confirmations 테이블
   - NewsArticle 모델 확장

2. **NewsFilter 구현 시작**
   - backend/ai/intelligence/ 디렉토리 생성
   - news_filter.py 구현

### 10.2 필요한 외부 API

- Yahoo Finance (가격/실적 데이터)
- SEC Edgar (공시 데이터)
- FRED (경제 데이터)

### 10.3 주의 사항

1. **.env 파일 직접 수정 금지**: .env.example만 수정 후 사용자에게 안내
2. **Hard Rule 우선**: LLM은 보조 추론 엔진, 결정권은 Hard Rule/Time Logic/Market Data
3. **의심 강제**: 모든 출력에 반대 시나리오 포함

---

**작성 완료**: 2026-01-18
**다음 작업**: 데이터베이스 마이그레이션 스크립트 작성 또는 NewsFilter 구현 시작
