# 🚀 AI Trading System - 완전 자율화 로드맵 V2

**목적**: AI가 스스로 종목 발굴 → 전문가급 분석 → 매매까지 수행하는 완전 자율 시스템 구축

**작성일**: 2025-12-13

**검토자**: Claude (Anthropic), ChatGPT (OpenAI), Gemini (Google)

**예상 총 비용**: $3-8/월 (추가 비용)

**예상 기간**: 10-12주

---

## 📊 현재 시스템 진단 (3개 AI 합의)

### ✅ 강점
- 2-Layer Cache (Redis + TimescaleDB) 완성
- Multi-AI Ensemble (Claude/Gemini/ChatGPT) 작동
- Constitution Rules (Pre/Post-Check) 구현
- Point-in-Time Backtesting 가능
- 비용 최적화 ($3/월 이하)

### ❌ 공통 지적 문제점

| 문제 | 심각도 | 현재 상태 | 목표 |
|-----|--------|---------|------|
| **Dynamic Screener 부재** | 🔴 Critical | Watchlist 하드코딩 | AI가 매일 종목 자동 발굴 |
| **Smart Options Flow 미흡** | 🔴 Critical | Put/Call 비율만 | Bid-Ask 기반 방향성 분석 |
| **Self-Feedback Loop 부재** | 🟡 High | 학습 안 함 | 예측 vs 결과 비교 자동 보정 |
| **Macro Data 통합 미흡** | 🟡 Medium | FRED 일부만 | 선물/CDS/채권 통합 |
| **데이터 간 모순 탐지 없음** | 🔴 Critical | 단순 수집만 | GDP↑ + 금리↓ 같은 모순 탐지 |
| **회의론적 분석 없음** | 🟡 High | 낙관 편향 | 악마의 변호인 강제 적용 |

---

## 🗺️ 전체 로드맵 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                    7-Phase 완전 자율화 로드맵                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase A: Dynamic Screener (1주)                                │
│     └─ AI가 매일 20개 종목 자동 발굴                              │
│                    ↓                                             │
│  Phase B: Smart Options Flow (1주)                              │
│     └─ Bid-Ask 기반 Smart Money 추적                            │
│                    ↓                                             │
│  Phase C: Macro Pipeline (1주)                                  │
│     └─ VIX/금리/선물/CDS 통합                                    │
│                    ↓                                             │
│  Phase D: Self-Feedback Loop (1주)                              │
│     └─ AI 예측 vs 결과 자동 보정                                  │
│                    ↓                                             │
│  Phase E: AI Council Voting (2주)                               │
│     └─ 3개 AI 가중 투표 시스템                                    │
│                    ↓                                             │
│  Phase F: AI Market Intelligence (2주)         ← 신규            │
│     └─ 월가 스타일 일일 브리핑 자동 생성                           │
│                    ↓                                             │
│  Phase G: Deep Reasoning Intelligence (2주)    ← 신규            │
│     └─ 데이터 모순 탐지 + 악마의 변호인                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 비용 요약

| Phase | 기능 | 기간 | 월 비용 |
|-------|-----|-----|--------|
| A | Dynamic Screener | 1주 | $0 |
| B | Smart Options Flow | 1주 | $0-30 |
| C | Macro Pipeline | 1주 | $0 |
| D | Self-Feedback Loop | 1주 | $0 |
| E | AI Council Voting | 2주 | ~$1.50 |
| F | AI Market Intelligence | 2주 | ~$3.00 |
| G | Deep Reasoning | 2주 | ~$4.50 |
| **Total** | | **10-12주** | **$3-8/월** |

---

## 🎯 Phase A: Dynamic Screener (1주)

### 목표
> **AI가 매일 장 시작 전 분석할 종목 20개를 자동으로 선정**

### 비용: $0/월 (무료 API만 사용)

### 파일 구조
```
backend/
├── services/
│   └── market_scanner/
│       ├── __init__.py
│       ├── scanner.py           # 메인 스캐너
│       ├── filters/
│       │   ├── __init__.py
│       │   ├── volume_filter.py      # 거래량 급등
│       │   ├── volatility_filter.py  # 변동성 돌파
│       │   ├── momentum_filter.py    # 모멘텀 스크리닝
│       │   └── options_filter.py     # 옵션 이상 징후
│       ├── universe.py          # S&P 500 + NASDAQ 100
│       └── scheduler.py         # 매일 실행 스케줄러
├── api/
│   └── screener_router.py       # REST API
└── tests/
    └── test_market_scanner.py
```

### 핵심 클래스: DynamicScreener

```python
"""
Dynamic Market Screener

매일 아침 Pre-Market (08:00 EST)에 실행하여
AI가 분석할 종목 후보군을 자동 선정합니다.

선정 기준:
1. 거래량 급등: 어제 거래량 > 20일 평균의 200%
2. 변동성 돌파: ATR 기반 돌파 감지
3. 옵션 이상: Unusual Options Activity 감지
4. 뉴스 모멘텀: 24시간 내 긍정적 뉴스
"""

@dataclass
class ScreenerCandidate:
    """스크리너 후보 종목"""
    ticker: str
    score: float                    # 종합 점수 (0-100)
    volume_score: float             # 거래량 점수
    volatility_score: float         # 변동성 점수
    momentum_score: float           # 모멘텀 점수
    options_score: float            # 옵션 이상 점수
    news_score: float               # 뉴스 점수
    volume_ratio: float             # 거래량 비율 (vs 20일 평균)
    price_change_pct: float         # 가격 변동률
    sector: str                     # 섹터
    reasons: List[str]              # 선정 사유


class DynamicScreener:
    def __init__(
        self,
        max_candidates: int = 20,
        min_market_cap: float = 1e9,      # 최소 시가총액 $1B
        min_volume: int = 500_000,         # 최소 일평균 거래량
    ):
        self.weights = {
            "volume": 0.25,
            "volatility": 0.20,
            "momentum": 0.20,
            "options": 0.25,
            "news": 0.10
        }
    
    async def scan(self, universe: List[str] = None) -> List[ScreenerCandidate]:
        """시장 전체를 스캔하여 후보 종목 선정"""
        pass
    
    async def _check_volume(self, ticker: str) -> dict:
        """거래량 필터 (200% 이상 → 100점)"""
        pass
    
    async def _check_volatility(self, ticker: str) -> dict:
        """변동성 필터 (ATR 기반)"""
        pass
    
    async def _check_momentum(self, ticker: str) -> dict:
        """모멘텀 필터 (5일 수익률)"""
        pass
    
    async def _check_options(self, ticker: str) -> dict:
        """옵션 이상 필터"""
        pass
```

### 스케줄러: ScreenerScheduler

```python
class ScreenerScheduler:
    """
    스케줄러 실행 시간:
    - Pre-Market: 08:00 EST (종목 선정)
    - Mid-Day: 12:00 EST (재스캔)
    """
    
    def start(self):
        # APScheduler로 cron job 등록
        self.scheduler.add_job(
            self._run_scan,
            CronTrigger(hour=8, minute=0),
            id="premarket_scan"
        )
```

### API 엔드포인트

```python
# GET /api/screener/candidates - 오늘의 후보 종목
# POST /api/screener/scan - 수동 스캔 실행
# GET /api/screener/history - 스캔 히스토리
```

### 성공 기준
- [ ] 매일 08:00 EST 자동 실행
- [ ] S&P 500 + NASDAQ 100 전체 스캔 < 5분
- [ ] 상위 20개 종목 자동 선정
- [ ] Redis에 결과 캐싱
- [ ] API로 결과 조회 가능

---

## 🎯 Phase B: Smart Options Flow (1주)

### 목표
> **단순 Put/Call 비율이 아닌, 실제 돈이 어디로 흐르는지 추적**

### 비용: $0-30/월

### 핵심 개념: Bid-Ask 기반 방향성 판별

```
Put Volume 증가 시:

Case A: 체결가가 Ask(매도호가) 근처
  → 매수자가 급함 (Aggressive Buy)
  → Put 매수 = 하락 베팅 🐻

Case B: 체결가가 Bid(매수호가) 근처
  → 매도자가 급함 (Aggressive Sell)
  → Put 매도 = 상승/횡보 베팅 🐂
```

### 핵심 클래스: SmartOptionsAnalyzer

```python
"""
Smart Options Analyzer

Bid-Ask Spread 기반으로 매수/매도 성향을 판별하고
실제 자금 흐름(Net Premium, Net Delta)을 추적합니다.
"""

@dataclass
class SmartOptionFlow:
    ticker: str
    timestamp: datetime
    
    # Premium 흐름
    net_call_premium: float       # Call 순매수 금액
    net_put_premium: float        # Put 순매수 금액
    total_premium: float          # 총 거래 금액
    
    # Delta 흐름 (방향성)
    net_delta: float              # -1 (약세) ~ +1 (강세)
    delta_interpretation: str     # BULLISH / BEARISH / NEUTRAL
    
    # 고래 주문
    whale_orders: List[Dict]      # $50,000+ 대형 주문
    whale_bullish_pct: float      # 고래 중 강세 비율
    
    # 센티먼트
    sentiment: str
    sentiment_score: float


class SmartOptionsAnalyzer:
    def __init__(
        self,
        whale_threshold: float = 50_000,
        bid_ask_buy_pct: float = 0.40,
    ):
        pass
    
    async def analyze_flow(
        self,
        ticker: str,
        chain_data: pd.DataFrame,
        current_price: float
    ) -> SmartOptionFlow:
        """옵션 체인 데이터 분석"""
        pass
    
    def _determine_trade_side(
        self, last: float, bid: float, ask: float
    ) -> str:
        """
        체결가 위치로 매수/매도 판별
        
        Ask 쪽 40% 내 → BUY (급한 매수)
        Bid 쪽 40% 내 → SELL (급한 매도)
        중간 → NEUTRAL
        """
        spread = ask - bid
        if last >= (ask - spread * 0.4):
            return 'BUY'
        elif last <= (bid + spread * 0.4):
            return 'SELL'
        return 'NEUTRAL'
```

### 성공 기준
- [ ] Bid-Ask 기반 BUY/SELL 구분 정확도 > 80%
- [ ] 고래 주문 ($50K+) 실시간 감지
- [ ] Net Delta 기반 방향성 예측
- [ ] Trading Agent Pre-Check에 통합

---

## 🎯 Phase C: Macro Data Pipeline (1주)

### 목표
> **거시경제 데이터를 체계적으로 수집하여 AI 분석에 반영**

### 비용: $0/월 (무료 소스만 사용)

### 데이터 소스

| 지표 | 소스 | 업데이트 주기 |
|-----|------|-------------|
| VIX | Yahoo Finance | 실시간 |
| 10Y Treasury | FRED | 일별 |
| Credit Spread | FRED (ICE BofA) | 일별 |
| Dollar Index (DXY) | Yahoo Finance | 실시간 |
| S&P 500 Futures (ES=F) | Yahoo Finance | 실시간 |
| Gold/Oil | Yahoo Finance | 실시간 |
| Fed Funds Rate | FRED | 일별 |

### 핵심 클래스: MacroDataCollector

```python
@dataclass
class MacroSnapshot:
    """거시경제 스냅샷"""
    timestamp: datetime
    
    # 변동성
    vix: float
    vix_term_structure: str       # Contango / Backwardation
    
    # 금리
    treasury_10y: float
    treasury_2y: float
    yield_curve: float            # 10Y - 2Y (역전 여부)
    fed_funds_rate: float
    credit_spread: float
    
    # 통화/상품
    dxy: float
    gold: float
    oil_wti: float
    
    # 종합 지표
    risk_on_score: float          # 0 (Risk-Off) ~ 100 (Risk-On)
    market_regime: str            # BULL / BEAR / SIDEWAYS / CRASH


class MacroDataCollector:
    async def get_snapshot(self) -> MacroSnapshot:
        """현재 매크로 스냅샷 조회"""
        pass
    
    async def get_regime(self) -> str:
        """
        시장 국면 판단
        
        VIX > 30 → CRASH
        VIX > 20 & Yield Curve < 0 → BEAR
        VIX < 15 & Risk-On > 70 → BULL
        else → SIDEWAYS
        """
        pass
```

### Trading Agent 통합

```python
# Pre-Check 추가
if macro.market_regime == "CRASH":
    return TradingDecision(
        action="HOLD",
        reasoning="Market in CRASH regime (VIX > 30). All buying suspended."
    )
```

### 성공 기준
- [ ] 10+ 매크로 지표 실시간 수집
- [ ] 시장 국면 자동 판단
- [ ] Risk-On/Off 점수 계산
- [ ] Trading Agent Pre-Check에 통합

---

## 🎯 Phase D: Self-Feedback Loop (1주)

### 목표
> **AI 예측 vs 실제 결과를 비교하여 자동 보정**

### 비용: $0/월

### 데이터 모델

```sql
CREATE TABLE ai_predictions (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    predicted_at TIMESTAMPTZ NOT NULL,
    
    -- 예측 내용
    action VARCHAR(10) NOT NULL,         -- BUY, SELL, HOLD
    conviction FLOAT NOT NULL,
    target_price FLOAT,
    stop_loss FLOAT,
    reasoning TEXT,
    model_used VARCHAR(50),
    
    -- 결과 (나중에 업데이트)
    actual_return_1d FLOAT,
    actual_return_5d FLOAT,
    actual_return_20d FLOAT,
    prediction_correct BOOLEAN,
    evaluated_at TIMESTAMPTZ
);
```

### 핵심 클래스: FeedbackLoop

```python
@dataclass
class ModelPerformance:
    """모델 성과"""
    model_name: str
    total_predictions: int
    correct_predictions: int
    accuracy: float
    buy_accuracy: float
    sell_accuracy: float
    avg_conviction_when_correct: float
    avg_conviction_when_wrong: float
    confidence_calibration: float  # 이상적으로 1.0


class FeedbackLoop:
    async def record_prediction(
        self, ticker: str, action: str, conviction: float, **kwargs
    ) -> int:
        """예측 기록 저장"""
        pass
    
    async def evaluate_predictions(self) -> int:
        """
        미평가 예측들을 평가
        - 1일, 5일, 20일 후 실제 수익률 계산
        - 방향 예측 정확성 평가
        """
        pass
    
    async def get_calibration_adjustment(self, model_name: str) -> Dict:
        """
        Conviction 보정값 계산
        
        예: 80% 확신 예측의 실제 정확도가 60%라면
            보정값 = 0.75 (60/80)
        """
        pass
    
    async def generate_weekly_report(self) -> str:
        """주간 성과 리포트 생성"""
        pass
```

### 성공 기준
- [ ] 모든 예측 자동 기록
- [ ] 1일/5일/20일 후 자동 평가
- [ ] 모델별 정확도 추적
- [ ] Conviction 자동 보정
- [ ] 주간 리포트 생성

---

## 🎯 Phase E: AI Council Voting (2주)

### 목표
> **단일 AI가 아닌, 여러 AI의 가중 투표로 최종 결정**

### 비용: ~$0.05/판단 (3개 AI 각각 호출)

### 아키텍처

```
┌───────────────────────────────────────────┐
│              AI Council                    │
│                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │Fundamental│  │  Insider │  │  Macro   │ │
│  │  Agent   │  │  Agent   │  │  Agent   │ │
│  │ (Claude) │  │ (Gemini) │  │ (GPT)    │ │
│  │          │  │          │  │          │ │
│  │ 재무/뉴스 │  │옵션/공매도│  │ 시장국면 │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│       ↓              ↓             ↓      │
│   Score: 80     Score: 95     Score: 20   │
│   (w=0.30)      (w=0.40)      (w=0.30)    │
│                                            │
│   Final: (80×0.3)+(95×0.4)+(20×0.3) = 68  │
│                                            │
│   Threshold: 75점 → HOLD                   │
└───────────────────────────────────────────┘
```

### 핵심 클래스: AICouncil

```python
@dataclass
class AgentVote:
    agent_name: str
    action: str                    # BUY, SELL, HOLD
    score: float                   # 0-100
    confidence: float              # 0-1
    reasoning: str
    key_factors: List[str]


@dataclass
class CouncilDecision:
    ticker: str
    final_action: str
    final_score: float
    votes: List[AgentVote]
    unanimous: bool
    dissenting_agent: Optional[str]
    bull_case: str
    bear_case: str
    key_risks: List[str]


class AICouncil:
    def __init__(self):
        self.weights = {
            "fundamental": 0.30,
            "insider": 0.40,
            "macro": 0.30
        }
        self.thresholds = {
            "buy": 75,
            "sell": 70,
        }
    
    async def deliberate(
        self, ticker: str, data_context: Dict
    ) -> CouncilDecision:
        """
        병렬로 3개 Agent 호출 후 가중 투표
        """
        votes = await asyncio.gather(
            self._get_fundamental_vote(ticker, data_context),
            self._get_insider_vote(ticker, data_context),
            self._get_macro_vote(ticker, data_context),
        )
        
        final_score, final_action = self._weighted_vote(votes)
        return CouncilDecision(...)
```

### 동적 가중치 조정

```python
class AdaptiveWeightManager:
    """
    Agent 가중치를 성과에 따라 동적 조정
    - 정확도 높은 Agent의 가중치 증가
    - 최근 30일 성과 기반
    - 최소/최대 가중치 제한 (0.15 ~ 0.50)
    """
    
    async def get_adjusted_weights(self) -> Dict[str, float]:
        pass
```

### 성공 기준
- [ ] 3개 Agent 병렬 호출 < 5초
- [ ] 가중 투표 로직 작동
- [ ] 만장일치 보너스 적용
- [ ] 동적 가중치 조정
- [ ] Trading Agent에 통합

---

## 🎯 Phase F: AI Market Intelligence (2주) - 신규

### 목표
> **"김현석의 월스트리트나우" 스타일 일일 브리핑 자동 생성**

### 비용: ~$0.10/일

### 분석 구조 (월스트리트나우 패턴)

```
1️⃣ 간밤 시황 요약
   └─ 주요 지수 등락폭 + 이유
   └─ 특징주 움직임

2️⃣ 핵심 이벤트 분석
   └─ Fed 발언/FOMC 결과 해석
   └─ 경제 지표 (CPI, PCE, 고용) 분석
   └─ 기업 실적 발표 평가

3️⃣ 월가 전문가 의견 인용
   └─ JP모건, 골드만삭스 등 리서치
   └─ WSJ, CNBC, Bloomberg 기사

4️⃣ 데이터 기반 분석
   └─ 채권 금리, 달러, VIX, 유가

5️⃣ 전망 및 주목 포인트
   └─ 이번 주 이벤트 캘린더
```

### 파일 구조

```
backend/
├── intelligence/
│   ├── __init__.py
│   ├── collector/
│   │   ├── fed_calendar.py       # Fed 일정 및 발언 수집
│   │   ├── economic_calendar.py  # 경제 지표 발표 일정
│   │   ├── earnings_calendar.py  # 실적 발표 일정
│   │   └── analyst_quotes.py     # 전문가 코멘트 추출
│   ├── reporter/
│   │   ├── daily_briefing.py     # 일일 브리핑 생성
│   │   ├── fed_analyzer.py       # Fed 발언 분석
│   │   └── economic_analyzer.py  # 경제 지표 해석
│   └── prompts/
│       ├── briefing_prompt.txt
│       └── fed_analysis_prompt.txt
```

### 핵심 클래스: WallStreetIntelCollector

```python
"""
Wall Street Intelligence Collector

월가 분석 수준의 데이터 수집
"""

@dataclass
class FedEvent:
    date: datetime
    event_type: str           # FOMC, SPEECH, MINUTES
    speaker: str              # Powell, Waller, etc.
    summary: str
    hawkish_score: float      # -1 (dovish) ~ +1 (hawkish)


@dataclass
class EconomicEvent:
    date: datetime
    indicator: str            # CPI, PCE, NFP, PMI
    actual: float
    expected: float
    previous: float
    surprise: float           # actual - expected
    market_reaction: str


@dataclass
class AnalystQuote:
    source: str               # JP Morgan, Goldman Sachs
    analyst: str
    quote: str
    sentiment: str            # BULLISH, BEARISH, NEUTRAL
    topic: str


class WallStreetIntelCollector:
    async def get_fed_events(self, days: int = 7) -> List[FedEvent]:
        """Fed 일정 및 발언 수집"""
        pass
    
    async def get_economic_calendar(self, days: int = 7) -> List[EconomicEvent]:
        """경제 지표 발표 일정"""
        pass
    
    async def get_earnings_calendar(self, days: int = 7) -> List[dict]:
        """실적 발표 일정"""
        pass
    
    async def extract_analyst_quotes(self, news_text: str) -> List[AnalystQuote]:
        """
        뉴스에서 전문가 코멘트 추출
        
        패턴:
        - "XXX 전략가는 'YYY'라고 말했다"
        - "골드만삭스에 따르면..."
        """
        pass
```

### 핵심 클래스: AIMarketReporter

```python
@dataclass
class MarketBriefing:
    timestamp: datetime
    
    # 시황 요약
    market_summary: str
    index_changes: Dict[str, float]
    
    # 핵심 이벤트
    key_events: List[str]
    fed_analysis: Optional[str]
    economic_analysis: Optional[str]
    
    # 특징주
    featured_stocks: List[dict]
    
    # 전문가 의견
    analyst_views: List[AnalystQuote]
    
    # 전망
    outlook: str
    watch_points: List[str]
    
    # 메타데이터
    data_sources: List[str]


class AIMarketReporter:
    async def generate_daily_briefing(self) -> MarketBriefing:
        """
        일일 시황 브리핑 생성
        """
        # 1. 데이터 수집
        market_data = await self.get_overnight_market_data()
        fed_events = await self.intel_collector.get_fed_events()
        economic_events = await self.intel_collector.get_economic_calendar()
        analyst_quotes = await self.get_latest_analyst_views()
        
        # 2. AI 분석 생성
        prompt = self._build_briefing_prompt(
            market_data, fed_events, economic_events, analyst_quotes
        )
        analysis = await self.claude_client.generate(prompt)
        
        return MarketBriefing(...)
    
    async def analyze_fed_statement(self, statement: str) -> dict:
        """
        Fed 발언 분석
        
        Returns:
            {
                "hawkish_score": 7,
                "key_message": "인플레 일시적 주장 유지",
                "policy_implication": "연내 테이퍼링 가능",
                "market_impact": "기술주 단기 부정적"
            }
        """
        pass
    
    async def analyze_economic_data(
        self, indicator: str, actual: float, expected: float
    ) -> dict:
        """경제 지표 발표 분석"""
        pass
```

### 브리핑 프롬프트

```python
DAILY_BRIEFING_PROMPT = """
당신은 월스트리트 전문 애널리스트입니다.
김현석의 월스트리트나우 스타일로 일일 시황을 분석해주세요.

## 분석 데이터
{market_data}
{fed_events}
{economic_data}
{analyst_quotes}

## 분석 지침

1. **시황 요약** (200자 이내)
   - 주요 지수 등락폭과 핵심 이유

2. **핵심 이벤트 분석**
   - Fed 발언/정책의 시장 영향
   - 경제 지표 해석

3. **전문가 인용**
   - "JP모건의 XXX는 'YYY'라고 밝혔습니다"

4. **오늘의 주목 포인트**
   - 향후 이벤트 일정
   - 투자 시사점

## 출력 형식
- 자연스러운 한국어 문체
- 전문적이면서도 이해하기 쉽게
- 숫자와 데이터를 적극 활용
"""
```

### 성공 기준
- [ ] Fed 캘린더 & 발언 자동 수집
- [ ] 경제 지표 발표 즉시 분석
- [ ] 전문가 코멘트 자동 추출
- [ ] 일일 브리핑 자동 생성
- [ ] Telegram/Slack 알림 연동

---

## 🎯 Phase G: Deep Reasoning Intelligence (2주) - 신규

### 목표
> **데이터 간 모순 탐지 + 악마의 변호인으로 전문가급 분석**

### 비용: ~$0.15/일

### 핵심 개념 (Gemini 분석 기반)

```
영상 속 전문가의 3단계 사고 과정:

1️⃣ 데이터 수집 (Fact)
   "연준이 GDP 성장률 전망을 1.8% → 2.3%로 올렸다"

2️⃣ 모순 발견 (Detection)
   "경기가 좋아지는데(GDP↑), 금리는 왜 내린다고 하지?(금리↓)"
   → Logical Conflict 발생!

3️⃣ 가설 수립 (Inference)
   "데이터가 앞뒤가 안 맞는다. 이건 '정치적 압력'이나 
    '우리가 모르는 유동성 위기'가 있다는 방증이다."
   → Devil's Advocate(반대 의견) 제시
```

### 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│              Phase G: Deep Reasoning Intelligence            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ G1: Macro    │  │ G2: Skeptic  │  │ G3: Deep     │      │
│  │ Consistency  │  │ Agent        │  │ Profiling    │      │
│  │ Checker      │  │ (Devil's     │  │ (인물/정책   │      │
│  │ (모순 탐지)   │  │ Advocate)    │  │  분석)       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           ↓                                 │
│              ┌──────────────────────┐                       │
│              │  G4: Synthesis AI    │                       │
│              │  (종합 판단 + 리포트) │                       │
│              └──────────────────────┘                       │
│                           ↓                                 │
│              ┌──────────────────────┐                       │
│              │  Deep Insight Report │                       │
│              │  (시장의 맹점 포함)   │                       │
│              └──────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### G1: Macro Consistency Checker (매크로 정합성 검증기)

```python
"""
Macro Consistency Checker

경제 지표 간의 논리적 모순을 탐지합니다.

탐지 규칙:
1. GDP ↑ + 금리 ↓ = Over-Stimulus Warning
2. 실업률 ↓ + 인플레 ↑ = Sticky Inflation
3. VIX ↓ + Credit Spread ↑ = Hidden Stress
4. GDP 전망 ↑ + Rate Path ↓ = Policy Contradiction
"""

class AnomalyType(Enum):
    OVER_STIMULUS = "과잉 부양 경고"
    STICKY_INFLATION = "고착 인플레이션"
    HIDDEN_STRESS = "숨겨진 스트레스"
    POLICY_CONTRADICTION = "정책 모순"


@dataclass
class MacroContradiction:
    anomaly_type: AnomalyType
    severity: float                  # 0-1
    
    indicator_a: str
    indicator_a_value: float
    indicator_a_trend: str
    
    indicator_b: str
    indicator_b_value: float
    indicator_b_trend: str
    
    contradiction_description: str
    possible_explanations: List[str]
    historical_precedents: List[str]
    market_implication: str
    risk_level: str


class MacroConsistencyChecker:
    def __init__(self):
        self.rules = [
            {
                "name": "GDP vs Interest Rate",
                "indicators": ("gdp_growth", "fed_rate_change"),
                "contradiction": lambda gdp, rate: gdp > 0 and rate < 0,
                "type": AnomalyType.OVER_STIMULUS,
            },
            {
                "name": "Unemployment vs Inflation",
                "indicators": ("unemployment_rate", "cpi_yoy"),
                "contradiction": lambda unemp, cpi: unemp < 4.0 and cpi > 3.0,
                "type": AnomalyType.STICKY_INFLATION,
            },
            {
                "name": "VIX vs Credit Spread",
                "indicators": ("vix", "credit_spread"),
                "contradiction": lambda vix, spread: vix < 15 and spread > 1.5,
                "type": AnomalyType.HIDDEN_STRESS,
            },
        ]
    
    async def detect_contradictions(
        self, macro_data: Dict[str, float]
    ) -> List[MacroContradiction]:
        """모든 규칙을 검사하여 모순 탐지"""
        contradictions = []
        
        for rule in self.rules:
            ind_a, ind_b = rule["indicators"]
            val_a = macro_data.get(ind_a)
            val_b = macro_data.get(ind_b)
            
            if val_a and val_b and rule["contradiction"](val_a, val_b):
                contradiction = await self._build_contradiction(rule, val_a, val_b)
                contradictions.append(contradiction)
        
        return contradictions
    
    async def _generate_explanations(
        self, rule_name: str, val_a: float, val_b: float
    ) -> List[str]:
        """AI를 통해 모순의 가능한 설명 생성"""
        prompt = f"""
        다음 매크로 경제 모순을 분석하세요:
        
        모순: {rule_name}
        데이터: 값A={val_a}, 값B={val_b}
        
        이 모순이 발생한 가능한 이유 3가지:
        1. 정치적/정책적 이유
        2. 시장 구조적 이유
        3. 데이터/측정 오류 가능성
        """
        # Claude API 호출
        pass
```

### G2: Skeptic Agent (악마의 변호인)

```python
"""
Skeptic Agent (Devil's Advocate)

다른 AI들이 "매수"를 외칠 때,
강제로 반대 논리를 찾아 "시장의 맹점"을 보고합니다.
"""

@dataclass
class SkepticAnalysis:
    ticker: str
    
    # 다른 AI들의 견해
    consensus_view: str
    consensus_confidence: float
    
    # 회의론적 반박
    counter_arguments: List[str]
    overlooked_risks: List[str]
    data_reliability_issues: List[str]
    
    # 역사적 유사 실패 사례
    historical_failures: List[str]
    
    # "모두가 아는 사실"의 허점
    blind_spots: List[str]
    
    # 최악의 시나리오
    worst_case_scenario: str
    worst_case_probability: float
    
    # 종합
    skeptic_score: float             # 0-100
    recommendation: str              # PROCEED, CAUTION, AVOID


class SkepticAgent:
    async def analyze(
        self,
        ticker: str,
        consensus_analysis: Dict,
        market_data: Dict,
        news_data: List[str]
    ) -> SkepticAnalysis:
        """회의론적 분석 수행"""
        
        # 1. 반대 논거 생성
        counter_arguments = await self._generate_counter_arguments(
            ticker, consensus_analysis
        )
        
        # 2. 간과된 리스크 발굴
        overlooked_risks = await self._find_overlooked_risks(ticker)
        
        # 3. 데이터 신뢰성 검증
        data_issues = await self._check_data_reliability(market_data)
        
        # 4. 시장의 맹점 찾기
        blind_spots = await self._identify_blind_spots(ticker, consensus_analysis)
        
        # 5. 역사적 실패 사례 검색
        historical_failures = await self._search_historical_failures(ticker)
        
        # 6. 최악의 시나리오
        worst_case = await self._construct_worst_case(ticker)
        
        return SkepticAnalysis(...)
    
    async def _generate_counter_arguments(
        self, ticker: str, consensus: dict
    ) -> List[str]:
        """낙관론에 대한 반대 논거 생성"""
        
        prompt = f"""
        당신은 "악마의 변호인" 역할입니다.
        다음 분석에 대해 강제로 반대 논거를 찾으세요.
        
        종목: {ticker}
        시장 합의: {consensus.get('action')}
        합의 근거: {consensus.get('reasoning')}
        
        규칙:
        1. 어떤 상황에서도 긍정적 의견 금지
        2. 숨겨진 약점, 과대평가된 요소 찾기
        3. "이미 주가에 반영됨" 논리 활용
        4. 구체적인 숫자와 데이터로 반박
        
        3가지 반대 논거:
        """
        pass
    
    async def _identify_blind_spots(
        self, ticker: str, consensus: dict
    ) -> List[str]:
        """시장의 맹점 찾기"""
        
        prompt = f"""
        "{ticker}"에 대해 시장이 합의를 보이고 있습니다.
        
        "모두가 알고 있는 사실"이지만 실제로는 틀릴 수 있는 
        가정(assumption)을 3가지 찾으세요.
        
        예시:
        - "AI 수요는 계속 증가할 것이다" → 실제: 포화점 도달 가능
        - "경쟁자가 없다" → 실제: 숨은 경쟁자 존재
        """
        pass
    
    async def _search_historical_failures(self, ticker: str) -> List[str]:
        """유사한 합의가 틀렸던 역사적 사례"""
        # RAG 검색
        return [
            "2000년 시스코: '인터넷 인프라 필수' 합의 → 80% 폭락",
            "2021년 줌비디오: '재택근무 영구화' 합의 → 70% 폭락",
        ]
```

### G3: Deep Profiling Agent (인물/정책 심층 분석)

```python
"""
Deep Profiling Agent

주요 인물의 과거 발언, 행동 패턴, 실패 사례를 추적하여
현재 발언의 신뢰도를 평가합니다.
"""

@dataclass
class PersonProfile:
    name: str
    role: str
    
    # 성향 분석
    hawkish_dovish_score: float      # -1 ~ +1
    optimism_bias: float             # 0-1
    credibility_score: float         # 0-1
    
    # 과거 기록
    past_predictions: List[dict]
    accuracy_rate: float
    flip_flop_count: int             # 말 바꾸기 횟수
    
    # 이해관계
    known_biases: List[str]
    conflicts_of_interest: List[str]


class DeepProfilingAgent:
    async def profile_person(self, name: str) -> PersonProfile:
        """인물 프로파일 생성"""
        pass
    
    async def analyze_statement_credibility(
        self, person: str, statement: str
    ) -> dict:
        """
        발언 신뢰도 분석
        
        Returns:
            {
                "credibility": 0.7,
                "past_accuracy": 0.6,
                "potential_biases": [...],
                "confidence_adjustment": -0.15
            }
        """
        pass
    
    async def detect_flip_flop(
        self, person: str, current_statement: str
    ) -> Optional[dict]:
        """
        말 바꾸기 탐지
        
        Returns:
            {
                "detected": True,
                "previous_statement": "...",
                "contradiction_level": "HIGH"
            }
        """
        pass
```

### G4: Deep Insight Report (최종 리포트)

```python
@dataclass
class DeepInsightReport:
    """Deep Insight 최종 리포트"""
    
    timestamp: datetime
    report_type: str
    
    # 섹션 1: 시황 요약
    market_summary: str
    key_events: List[str]
    
    # 섹션 2: 컨센서스 분석
    consensus_view: str
    consensus_reasoning: str
    
    # 섹션 3: 매크로 모순 (G1)
    macro_contradictions: List[MacroContradiction]
    
    # 섹션 4: 시장의 맹점 (G2)
    blind_spots: List[str]
    overlooked_risks: List[str]
    
    # 섹션 5: 인물 신뢰도 (G3)
    key_person_analysis: Dict[str, PersonProfile]
    
    # 섹션 6: 최종 판단
    final_assessment: str
    risk_level: str
    action_items: List[str]
```

### Deep Insight 프롬프트

```python
DEEP_INSIGHT_PROMPT = """
당신은 월가 최고의 매크로 전략가입니다.
슈카/전석재 스타일로 심층 분석 리포트를 작성하세요.

## 분석 데이터
{macro_contradictions}
{skeptic_analysis}
{person_profiles}
{market_data}

## 리포트 작성 지침

1. **시장의 통념을 의심하라**
   - "모두가 알고 있는 사실"의 허점 지적
   - 데이터 간 모순이 있으면 반드시 언급

2. **숫자로 증명하라**
   - 추상적 주장 금지
   - GDP, 금리, 실업률 등 구체적 수치 인용

3. **인물의 신뢰도를 평가하라**
   - 파월의 과거 예측 적중률
   - 정치인 발언의 이해관계

4. **최악의 시나리오를 제시하라**
   - "만약 ~한다면" 시나리오 필수

5. **실행 가능한 인사이트를 도출하라**
   - 구체적인 포지션 조정 제안

## 출력 형식

📊 **오늘의 핵심 모순**
[가장 중요한 데이터 모순 1개]

🎯 **시장이 간과한 것**
[3가지 blind spots]

🔍 **인물 신뢰도 체크**
[주요 발언자의 과거 적중률]

⚠️ **최악의 시나리오**
[발생 확률과 영향]

💡 **실행 제안**
[구체적인 행동 지침]
"""
```

### 성공 기준
- [ ] 매크로 지표 간 모순 자동 탐지
- [ ] Skeptic Agent 강제 비관 분석
- [ ] 인물 프로파일링 (파월, 옐런 등)
- [ ] Deep Insight Report 자동 생성
- [ ] 시장의 맹점 섹션 포함

---

## 📋 전체 구현 체크리스트

### Phase A: Dynamic Screener
- [ ] `DynamicScreener` 클래스 구현
- [ ] 5개 필터 (Volume, Volatility, Momentum, Options, News)
- [ ] `ScreenerScheduler` 구현 (08:00, 12:00 EST)
- [ ] Redis 캐싱 연동
- [ ] API 엔드포인트 추가
- [ ] 테스트 케이스 작성

### Phase B: Smart Options Flow
- [ ] `SmartOptionsAnalyzer` 클래스 구현
- [ ] Trade Side Detection (BUY/SELL/NEUTRAL)
- [ ] Net Premium/Delta 계산
- [ ] 고래 주문 감지
- [ ] 기존 `options_flow_tracker.py` 통합
- [ ] API 엔드포인트 추가

### Phase C: Macro Pipeline
- [ ] `MacroDataCollector` 구현
- [ ] FRED API 연동 확장
- [ ] Yahoo Finance 매크로 데이터 연동
- [ ] 시장 국면 판단 로직
- [ ] Risk-On/Off 점수 계산
- [ ] Trading Agent Pre-Check 통합

### Phase D: Self-Feedback Loop
- [ ] `ai_predictions` 테이블 생성
- [ ] `FeedbackLoop` 클래스 구현
- [ ] 자동 평가 스케줄러
- [ ] Conviction 보정 로직
- [ ] 주간 리포트 생성
- [ ] Trading Agent 통합

### Phase E: AI Council Voting
- [ ] `AICouncil` 클래스 구현
- [ ] 3개 Agent 프롬프트 작성
- [ ] 가중 투표 로직
- [ ] `AdaptiveWeightManager` 구현
- [ ] Trading Agent 대체 통합
- [ ] 테스트 케이스 작성

### Phase F: AI Market Intelligence
- [ ] `WallStreetIntelCollector` 구현
- [ ] Fed 캘린더 & 발언 수집기
- [ ] 경제 지표 캘린더
- [ ] 전문가 코멘트 추출 AI
- [ ] `AIMarketReporter` 구현
- [ ] 일일 브리핑 생성기
- [ ] Telegram/Slack 알림 연동

### Phase G: Deep Reasoning Intelligence
- [ ] `MacroConsistencyChecker` 구현 (모순 탐지)
- [ ] `SkepticAgent` 구현 (악마의 변호인)
- [ ] `DeepProfilingAgent` 구현 (인물 분석)
- [ ] `DeepInsightReport` 템플릿
- [ ] 종합 판단 AI
- [ ] 시장의 맹점 섹션 자동 생성

---

## 🚀 실행 방법

### Claude Code에서 실행

```bash
# 1. 로드맵 파일 확인
cat AUTONOMOUS_TRADING_ROADMAP_V2.md

# 2. Phase A부터 순차 구현
# 각 Phase의 파일 구조와 클래스 설계에 따라 구현

# 3. 테스트 실행
python -m pytest backend/tests/ -v

# 4. 다음 Phase로 진행
```

### 우선순위 제안

```
1️⃣ Phase A (Dynamic Screener) - 가장 기본, 먼저 구현
2️⃣ Phase D (Self-Feedback) - 독립적, 병렬 구현 가능
3️⃣ Phase C (Macro Pipeline) - 기존 코드 확장
4️⃣ Phase B (Smart Options) - 기존 코드 확장
5️⃣ Phase E (AI Council) - A-D 완료 후
6️⃣ Phase F (Market Intelligence) - E 완료 후
7️⃣ Phase G (Deep Reasoning) - 최종 통합
```

---

## 📊 최종 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    완전 자율 AI 트레이딩 시스템                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Data Collection Layer                   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │   │
│  │  │ Dynamic │ │  Smart  │ │  Macro  │ │  Intel  │      │   │
│  │  │Screener │ │ Options │ │Pipeline │ │Collector│      │   │
│  │  │ (A)     │ │  (B)    │ │  (C)    │ │  (F)    │      │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Analysis Layer                         │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │   │
│  │  │    Macro    │ │   Skeptic   │ │    Deep     │       │   │
│  │  │ Consistency │ │   Agent     │ │  Profiling  │       │   │
│  │  │   (G1)      │ │   (G2)      │ │    (G3)     │       │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Decision Layer                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │                 AI Council (E)                   │    │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │    │   │
│  │  │  │Fundamental│ │ Insider │ │  Macro   │        │    │   │
│  │  │  │  Agent   │ │  Agent  │ │  Agent   │        │    │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘        │    │   │
│  │  │              ↓ Weighted Vote ↓                  │    │   │
│  │  │         ┌──────────────────────┐               │    │   │
│  │  │         │   Final Decision     │               │    │   │
│  │  │         └──────────────────────┘               │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Learning Layer                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │            Self-Feedback Loop (D)                │    │   │
│  │  │  Prediction → Result → Evaluation → Calibration  │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Output Layer                           │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │   │
│  │  │ Trading │ │  Deep   │ │ Daily   │ │ Alerts  │      │   │
│  │  │ Signal  │ │ Insight │ │Briefing │ │(Telegram│      │   │
│  │  │         │ │ Report  │ │  (F)    │ │ /Slack) │      │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📞 지원

질문이 있으면 프로젝트 README의 이슈 트래커를 사용하세요.

**작성**: Claude (Anthropic) + ChatGPT (OpenAI) + Gemini (Google) 공동 검토

**버전**: 2.0.0

**최종 수정**: 2025-12-13
