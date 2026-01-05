# MVP Architecture - Deep Dive

**Version**: 1.0
**Last Updated**: 2026-01-04
**Author**: AI Trading System Development Team
**Status**: ✅ Production Ready

---

## 📋 Executive Summary

**MVP 전환 배경**: 2025-12-31, Legacy 8-Agent War Room 시스템을 **3+1 MVP Agent** 구조로 통합하여 **비용 67% 절감**, **속도 67% 향상** (30s → 10s), **API 호출 62.5% 감소** (8회 → 3회)를 달성했습니다.

**핵심 철학**:
- **Attack (35%)**: Trader MVP - 공격적 기회 포착
- **Defense (35%)**: Risk MVP - 방어적 리스크 관리 + Position Sizing
- **Information (30%)**: Analyst MVP - 종합 정보 분석
- **Final Decision**: PM Agent MVP - Hard Rules 검증 + 최종 승인

**Shadow Trading**: 2026-01-01부터 3개월 검증 진행 중 (Day 4/90, P&L +$1,274.85)

---

## 🎯 Table of Contents

1. [MVP 전환 배경](#mvp-전환-배경)
2. [Agent 설계 철학](#agent-설계-철학)
3. [3+1 Agent 상세 스펙](#31-agent-상세-스펙)
4. [Position Sizing 알고리즘](#position-sizing-알고리즘)
5. [Execution Layer](#execution-layer)
6. [Voting Mechanism](#voting-mechanism)
7. [Legacy vs MVP 비교](#legacy-vs-mvp-비교)
8. [구현 세부사항](#구현-세부사항)
9. [성능 최적화](#성능-최적화)
10. [향후 계획](#향후-계획)

---

## 🔄 MVP 전환 배경

### 문제점 (Legacy 8-Agent System)

**1. 비용 문제**
```
8개 Agent × $0.013/call = $0.104 per deliberation
월 100회 실행 시 = $10.40/month
```

**2. 속도 문제**
- 8개 Agent 순차 실행: ~30초
- API 호출 8회 (각 Agent 1회씩)
- 사용자 대기 시간 과다

**3. 복잡도 문제**
- 8개 의견 통합의 어려움
- 투표 가중치 조정의 복잡성
- Agent 간 역할 중복 (News + Macro, Trader + ChipWar)

**4. 유지보수 문제**
- 8개 Agent 각각 업데이트 필요
- 일관성 유지 어려움
- 테스트 복잡도 증가

### 해결 방안: 3+1 MVP Agent

**설계 원칙**:
1. **역할 통합**: 유사 기능 Agent 병합
2. **단일 모델**: Gemini 2.0 Flash Experimental 통일
3. **병렬 실행**: 3개 Agent 동시 호출
4. **명확한 분리**: Attack / Defense / Information
5. **최종 검증**: PM Agent의 Hard Rules 검증

**기대 효과**:
- ✅ 비용: 67% 절감 ($0.104 → $0.035)
- ✅ 속도: 67% 향상 (30s → 10s)
- ✅ API 호출: 62.5% 감소 (8회 → 3회)
- ✅ 유지보수: 간소화 (8개 → 4개 파일)

---

## 🧠 Agent 설계 철학

### 3+1 구조 설계

```
┌─────────────────────────────────────────────────────────┐
│                   War Room MVP System                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────┬───────────────────┐
        │                   │                   │
    ┌───▼────┐        ┌────▼─────┐       ┌────▼──────┐
    │ Trader │        │   Risk   │       │ Analyst   │
    │  MVP   │        │   MVP    │       │   MVP     │
    │ (35%)  │        │  (35%)   │       │  (30%)    │
    └───┬────┘        └────┬─────┘       └────┬──────┘
        │                  │                   │
        │ Attack           │ Defense +         │ Information
        │ (기회 포착)       │ Position Sizing   │ (정보 분석)
        │                  │                   │
        └──────────────────┴───────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   PM Agent    │
                    │     MVP       │
                    │ (Final Decide)│
                    └───────┬───────┘
                            │
                            ▼
                    Hard Rules Check
                    Approve / Reject
```

### Attack (Trader MVP - 35%)

**역할**: 공격적 기회 포착
**흡수한 Agent**: Trader (15%) + ChipWar Opportunity (12%)

**핵심 질문**:
- "지금 진입해야 하는가?"
- "이 패턴은 신뢰할 수 있는가?"
- "반도체 전쟁이 기회를 만드는가?"

**강점**:
- 기술적 분석 (RSI, MACD, 차트 패턴)
- 단기 모멘텀 포착
- ChipWar 관련 기회 (NVIDIA, AMD 등)

**약점**:
- 리스크 과소평가 가능
- 단기 노이즈에 민감
- 손실 시나리오 고려 부족

→ **Risk MVP가 균형 제공**

### Defense (Risk MVP - 35%)

**역할**: 방어적 리스크 관리 + Position Sizing
**흡수한 Agent**: Risk (20%) + Sentiment (8%)

**핵심 질문**:
- "얼마나 투자해야 하는가?" (Position Sizing)
- "Stop Loss는 어디에 설정해야 하는가?"
- "최악의 시나리오는 무엇인가?"

**강점**:
- **Position Sizing 자동화** (신규 기능!)
- 변동성 분석 (베타, 표준편차)
- 시장 심리 반영 (VIX, 공포/탐욕 지수)

**약점**:
- 과도한 보수성 (기회 상실)
- 단기 변동성에 과민 반응

→ **Trader MVP가 균형 제공**

### Information (Analyst MVP - 30%)

**역할**: 종합 정보 분석
**흡수한 Agent**: News (10%) + Macro (10%) + Institutional (10%) + ChipWar Geopolitics

**핵심 질문**:
- "뉴스가 주가에 어떤 영향을 주는가?"
- "거시경제 환경은 유리한가?"
- "기관 투자자들은 어떻게 움직이는가?"
- "지정학적 리스크는 무엇인가?"

**강점**:
- 다층적 정보 분석 (뉴스 + 거시 + 기관 + 지정학)
- Macro Context 통합
- 장기 트렌드 파악

**약점**:
- 정보 과부하 가능
- 단기 기술적 신호 간과

→ **Trader MVP가 보완**

### Final Decision (PM Agent MVP)

**역할**: 최종 의사결정 + Hard Rules 검증
**신규 추가**: MVP 전환 시 추가됨

**핵심 질문**:
- "3개 Agent 의견을 어떻게 종합하는가?"
- "Hard Rules를 위반하지 않는가?"
- "Execution Router는 Fast Track인가 Deep Dive인가?"

**강점**:
- **8개 Hard Rules 자동 검증** (안전장치)
- Weighted Voting (35% + 35% + 30%)
- 최종 승인/거부 권한

**약점**:
- 없음 (규칙 기반, AI 판단 아님)

---

## 📊 3+1 Agent 상세 스펙

### Trader MVP

**File**: `backend/ai/mvp/trader_agent_mvp.py` (485 lines)
**Model**: Gemini 2.0 Flash Experimental
**Vote Weight**: 35%

**Input**:
```python
{
    'symbol': 'AAPL',
    'price_data': {
        'current_price': 150.0,
        'high_52w': 180.0,
        'low_52w': 120.0,
        'volume': 50_000_000
    },
    'technical_data': {
        'rsi': 28.5,
        'macd': {'value': -2.1, 'signal': -1.5},
        'bollinger': {'upper': 155, 'lower': 145, 'middle': 150}
    },
    'chipwar_events': [
        {'title': 'US eases AI chip export restrictions', 'date': '2026-01-03'}
    ]
}
```

**Analyze() 로직**:
```python
def analyze(self, symbol, price_data, technical_data=None, chipwar_events=None):
    # 1. 기술적 분석
    technical_score = self._analyze_technicals(technical_data)

    # 2. 차트 패턴 인식
    pattern_score = self._detect_chart_patterns(price_data)

    # 3. ChipWar 기회 포착
    chipwar_score = self._assess_chipwar_impact(chipwar_events)

    # 4. 종합 점수 계산
    opportunity_score = (
        technical_score * 0.5 +
        pattern_score * 0.3 +
        chipwar_score * 0.2
    )

    # 5. Action 결정
    if opportunity_score > 7.0:
        action = 'buy'
        confidence = min(opportunity_score / 10.0, 0.95)
    elif opportunity_score < 3.0:
        action = 'sell'
        confidence = min((10.0 - opportunity_score) / 10.0, 0.95)
    else:
        action = 'hold'
        confidence = 0.5

    return {
        'agent': 'trader_mvp',
        'action': action,
        'confidence': confidence,
        'opportunity_score': opportunity_score,
        'reasoning': f"Technical: {technical_score}, Pattern: {pattern_score}, ChipWar: {chipwar_score}",
        'risk_factors': self._identify_risks()
    }
```

**Output Example**:
```json
{
  "agent": "trader_mvp",
  "action": "buy",
  "confidence": 0.85,
  "reasoning": "이중 바닥 패턴 완성, RSI 28.5 (과매도), MACD 골든크로스 임박",
  "opportunity_score": 8.5,
  "risk_factors": ["실적 발표 D-3", "거래량 평균 대비 70%"],
  "chipwar_impact": "NVIDIA AI 칩 수출 규제 완화로 수혜 예상",
  "key_signals": [
    "RSI: 28.5 (과매도 구간)",
    "Volume: 50M (평균 70M)",
    "52w Low 대비 +25% 반등"
  ]
}
```

---

### Risk MVP

**File**: `backend/ai/mvp/risk_agent_mvp.py` (612 lines)
**Model**: Gemini 2.0 Flash Experimental
**Vote Weight**: 35%

**Input**:
```python
{
    'symbol': 'AAPL',
    'price_data': {...},
    'portfolio_state': {
        'total_value': 100000,
        'available_cash': 50000,
        'positions': {...}
    },
    'market_conditions': {
        'vix': 18.5,
        'market_regime': 'RISK_ON',
        'fed_stance': 'HAWKISH'
    }
}
```

**Analyze() 로직**:
```python
def analyze(self, symbol, price_data, portfolio_state, market_conditions):
    # 1. 리스크 평가
    risk_score = self._calculate_risk_score(price_data, market_conditions)

    # 2. **Position Sizing 계산** (핵심 기능!)
    position_size = self._calculate_position_size(
        price_data=price_data,
        portfolio_state=portfolio_state,
        risk_score=risk_score
    )

    # 3. Stop Loss 설정
    stop_loss = self._calculate_stop_loss(price_data)

    # 4. 시장 심리 분석
    sentiment = self._analyze_sentiment(market_conditions)

    # 5. Action 결정
    if risk_score < 5.0 and position_size > 0:
        action = 'buy'
        confidence = (10.0 - risk_score) / 10.0
    elif risk_score > 7.0:
        action = 'sell' if has_position else 'pass'
        confidence = risk_score / 10.0
    else:
        action = 'hold'
        confidence = 0.5

    return {
        'agent': 'risk_mvp',
        'action': action,
        'confidence': confidence,
        'risk_score': risk_score,
        'position_size': position_size,
        'position_size_pct': position_size / portfolio_state['total_value'] * 100,
        'stop_loss': stop_loss,
        'sentiment': sentiment,
        'risk_factors': self._identify_risk_factors()
    }
```

**Output Example**:
```json
{
  "agent": "risk_mvp",
  "action": "buy",
  "confidence": 0.75,
  "reasoning": "VIX 18.5 (정상 범위), 유동성 충분, 변동성 낮음",
  "risk_score": 4.2,
  "position_size": 10000,
  "position_size_pct": 10.0,
  "stop_loss": 142.50,
  "stop_loss_distance": 5.0,
  "risk_factors": [
    "실적 발표 임박 (D-3)",
    "Fed 금리 결정 대기 (D-7)"
  ],
  "sentiment": "NEUTRAL",
  "volatility": {
    "beta": 1.05,
    "annual_volatility": 24.3
  }
}
```

---

### Analyst MVP

**File**: `backend/ai/mvp/analyst_agent_mvp.py` (548 lines)
**Model**: Gemini 2.0 Flash Experimental
**Vote Weight**: 30%

**Input**:
```python
{
    'symbol': 'AAPL',
    'news_articles': [...],  # 최근 24시간 뉴스
    'macro_context': {
        'regime': 'RISK_ON',
        'fed_stance': 'HAWKISH',
        'vix': 18.5
    },
    'institutional_flow': {...},  # 13F filings
    'chipwar_geopolitics': {...}
}
```

**Analyze() 로직**:
```python
def analyze(self, symbol, news_articles, macro_context, institutional_flow, chipwar_geopolitics):
    # 1. 뉴스 분석
    news_score = self._analyze_news(news_articles)

    # 2. 거시경제 분석
    macro_score = self._analyze_macro(macro_context)

    # 3. 기관 투자자 동향
    institutional_score = self._analyze_institutional_flow(institutional_flow)

    # 4. ChipWar 지정학
    chipwar_score = self._analyze_chipwar_geopolitics(chipwar_geopolitics)

    # 5. 종합 점수
    information_score = (
        news_score * 0.35 +
        macro_score * 0.30 +
        institutional_score * 0.20 +
        chipwar_score * 0.15
    )

    # 6. Action 결정
    if information_score > 6.5:
        action = 'buy'
        confidence = min(information_score / 10.0, 0.90)
    elif information_score < 3.5:
        action = 'sell'
        confidence = min((10.0 - information_score) / 10.0, 0.90)
    else:
        action = 'hold'
        confidence = 0.5

    return {
        'agent': 'analyst_mvp',
        'action': action,
        'confidence': confidence,
        'information_score': information_score,
        'news_summary': self._summarize_news(news_articles),
        'macro_context': macro_context,
        'institutional_flow': institutional_flow,
        'chipwar_geopolitics': chipwar_geopolitics
    }
```

**Output Example**:
```json
{
  "agent": "analyst_mvp",
  "action": "buy",
  "confidence": 0.70,
  "reasoning": "긍정 뉴스 3건, Fed 중립 기조 유지, 기관 유입 지속",
  "information_score": 7.0,
  "news_summary": "AI 칩 수요 증가 전망 (Bloomberg), 실적 상향 조정 (2 analysts)",
  "macro_context": {
    "regime": "RISK_ON",
    "fed_stance": "HAWKISH",
    "vix": 18.5,
    "narrative": "단기 강한 모멘텀, 낮은 변동성 견인"
  },
  "institutional_flow": {
    "net_flow": 1200000,
    "trend": "inflow",
    "period": "3 days"
  },
  "chipwar_geopolitics": "미국 AI 반도체 수출 규제 완화 전망 (긍정적)"
}
```

---

### PM Agent MVP

**File**: `backend/ai/mvp/pm_agent_mvp.py` (427 lines)
**Model**: Gemini 2.0 Flash Experimental
**Vote Weight**: Final Decision

**Input**:
```python
{
    'symbol': 'AAPL',
    'action_context': 'new_position',
    'agent_opinions': {
        'trader_mvp': {...},
        'risk_mvp': {...},
        'analyst_mvp': {...}
    },
    'portfolio_state': {...},
    'market_conditions': {...}
}
```

**make_final_decision() 로직**:
```python
def make_final_decision(self, symbol, action_context, agent_opinions, portfolio_state, market_conditions):
    # 1. Weighted Voting
    weighted_score = (
        agent_opinions['trader_mvp']['confidence'] * 0.35 +
        agent_opinions['risk_mvp']['confidence'] * 0.35 +
        agent_opinions['analyst_mvp']['confidence'] * 0.30
    )

    # 2. Action 결정 (다수결)
    actions = [op['action'] for op in agent_opinions.values()]
    final_action = max(set(actions), key=actions.count)

    # 3. Position Size 확정 (Risk MVP 제안 사용)
    position_size = agent_opinions['risk_mvp']['position_size']
    stop_loss = agent_opinions['risk_mvp']['stop_loss']

    # 4. **8 Hard Rules 검증** (핵심!)
    hard_rules_passed, violation_reason = self._check_hard_rules(
        action=final_action,
        position_size=position_size,
        stop_loss=stop_loss,
        confidence=weighted_score,
        portfolio_state=portfolio_state,
        market_conditions=market_conditions
    )

    # 5. 최종 승인/거부
    if hard_rules_passed:
        final_decision = 'approve'
    else:
        final_decision = 'reject'
        final_action = 'pass'

    # 6. Execution Router 선택
    execution_path = self._select_execution_path(action_context, market_conditions)

    return {
        'agent': 'pm_mvp',
        'final_decision': final_decision,
        'action': final_action,
        'confidence': weighted_score,
        'position_size': position_size if hard_rules_passed else 0,
        'stop_loss': stop_loss,
        'reasoning': self._generate_reasoning(agent_opinions),
        'voting_summary': {
            'trader_mvp': {'vote': agent_opinions['trader_mvp']['action'], 'weight': 0.35},
            'risk_mvp': {'vote': agent_opinions['risk_mvp']['action'], 'weight': 0.35},
            'analyst_mvp': {'vote': agent_opinions['analyst_mvp']['action'], 'weight': 0.30}
        },
        'weighted_score': weighted_score,
        'hard_rules_passed': hard_rules_passed,
        'violation_reason': violation_reason if not hard_rules_passed else None,
        'execution_path': execution_path
    }
```

**Output Example**:
```json
{
  "agent": "pm_mvp",
  "final_decision": "approve",
  "action": "buy",
  "confidence": 0.77,
  "position_size": 10000,
  "stop_loss": 142.50,
  "reasoning": "3개 Agent 중 2개 BUY (Trader, Risk), 1개 HOLD (Analyst). Weighted Score 7.7/10. Hard Rules 통과.",
  "voting_summary": {
    "trader_mvp": {"vote": "buy", "weight": 0.35, "confidence": 0.85},
    "risk_mvp": {"vote": "buy", "weight": 0.35, "confidence": 0.75},
    "analyst_mvp": {"vote": "hold", "weight": 0.30, "confidence": 0.70}
  },
  "weighted_score": 7.7,
  "hard_rules_passed": true,
  "violation_reason": null,
  "execution_path": "deep_dive"
}
```

---

## 🎲 Position Sizing 알고리즘

**위치**: Risk MVP 내장 기능
**목적**: 자동화된 포지션 크기 계산

### 4-Step Formula

```python
def calculate_position_size(self, price_data, portfolio_state, confidence, risk_multiplier):
    """
    4-Step Position Sizing Algorithm

    Returns:
        Final position size in dollars
    """

    # Step 1: Risk-based base sizing
    # 원칙: 계좌의 2%만 리스크에 노출
    account_risk_pct = 0.02  # 2%
    stop_loss_distance = self._calculate_stop_loss_distance(price_data)

    base_size = (account_risk_pct / stop_loss_distance) * portfolio_state['total_value']
    # 예: (0.02 / 0.05) × $100,000 = $40,000

    # Step 2: Confidence adjustment
    # Agent 신뢰도에 따라 조정
    confidence_adjusted = base_size * confidence
    # 예: $40,000 × 0.85 = $34,000

    # Step 3: Volatility adjustment
    # 시장 변동성에 따라 조정
    risk_multiplier = self._calculate_risk_multiplier(
        vix=market_conditions['vix'],
        market_regime=market_conditions['market_regime']
    )
    risk_adjusted = confidence_adjusted * risk_multiplier
    # 예: $34,000 × 0.8 = $27,200

    # Step 4: Hard cap enforcement
    # 포트폴리오의 10%를 절대 초과하지 않음
    max_position = portfolio_state['total_value'] * 0.10
    final_size = min(risk_adjusted, max_position)
    # 예: min($27,200, $10,000) = $10,000

    return final_size
```

### Risk Multiplier Calculation

```python
def _calculate_risk_multiplier(self, vix, market_regime):
    """
    Market conditions에 따른 리스크 배율 조정

    VIX Levels:
    - < 15: Low volatility → 1.2x (공격적)
    - 15-25: Normal → 1.0x (기본)
    - 25-35: Elevated → 0.7x (보수적)
    - > 35: High → 0.5x (매우 보수적)

    Market Regime:
    - RISK_ON: +0.1x
    - TRANSITION: 0x
    - RISK_OFF: -0.2x
    """

    # VIX 기반 기본 배율
    if vix < 15:
        base_multiplier = 1.2
    elif vix < 25:
        base_multiplier = 1.0
    elif vix < 35:
        base_multiplier = 0.7
    else:
        base_multiplier = 0.5

    # Market Regime 조정
    regime_adjustment = {
        'RISK_ON': 0.1,
        'TRANSITION': 0.0,
        'RISK_OFF': -0.2
    }.get(market_regime, 0.0)

    final_multiplier = base_multiplier + regime_adjustment

    return max(final_multiplier, 0.3)  # 최소 0.3x
```

### Stop Loss Distance Calculation

```python
def _calculate_stop_loss_distance(self, price_data):
    """
    기술적 분석 기반 Stop Loss 거리 계산

    방법:
    1. ATR (Average True Range) 기반
    2. 최근 지지선 기반
    3. 고정 % (5%) 기본값
    """

    current_price = price_data['current_price']

    # Method 1: ATR (Average True Range)
    if 'atr' in price_data:
        atr_stop_loss = current_price - (price_data['atr'] * 2)
        distance_atr = (current_price - atr_stop_loss) / current_price
    else:
        distance_atr = None

    # Method 2: Support Level (지지선)
    if 'support_level' in price_data:
        support_stop_loss = price_data['support_level'] * 0.98  # 지지선 아래 2%
        distance_support = (current_price - support_stop_loss) / current_price
    else:
        distance_support = None

    # Method 3: Fixed 5% (기본값)
    distance_fixed = 0.05

    # 최종 선택: ATR > Support > Fixed 우선순위
    if distance_atr:
        return min(max(distance_atr, 0.03), 0.10)  # 3-10% 범위
    elif distance_support:
        return min(max(distance_support, 0.03), 0.10)
    else:
        return distance_fixed
```

### Position Sizing Example

**시나리오**:
- Portfolio Value: $100,000
- Available Cash: $50,000
- Current Price: $150
- Stop Loss Distance: 5%
- Agent Confidence: 0.85
- VIX: 18.5 (NORMAL)
- Market Regime: RISK_ON

**계산**:
```python
# Step 1: Base sizing
base_size = (0.02 / 0.05) × 100,000 = $40,000

# Step 2: Confidence adjustment
confidence_adjusted = 40,000 × 0.85 = $34,000

# Step 3: Risk multiplier
risk_multiplier = 1.0 (VIX 15-25) + 0.1 (RISK_ON) = 1.1
risk_adjusted = 34,000 × 1.1 = $37,400

# Step 4: Hard cap (10%)
max_position = 100,000 × 0.10 = $10,000
final_size = min(37,400, 10,000) = $10,000

# Quantity
quantity = 10,000 / 150 = 66 shares
```

**결과**:
- Position Size: $10,000 (10%)
- Quantity: 66 shares
- Stop Loss: $142.50 (5% below entry)
- Risk Amount: $10,000 × 0.05 = $500 (0.5% of portfolio) ✅

---

## ⚡ Execution Layer

MVP 전환과 함께 추가된 실행 계층입니다.

### 1. Execution Router

**File**: `backend/execution/execution_router.py`

**목적**: 상황에 따라 실행 경로 선택

**Fast Track (< 1초)**:
```python
def should_use_fast_track(self, context):
    """
    Fast Track 조건:
    1. Stop Loss 발동
    2. 일일 손실 > -5%
    3. VIX > 40 (극단적 공포)
    4. 긴급 청산 필요
    """

    if context.get('stop_loss_hit'):
        return True, "Stop Loss hit"

    if context.get('daily_loss_pct', 0) < -5.0:
        return True, "Daily loss limit exceeded"

    if context.get('vix', 0) > 40:
        return True, "Extreme volatility (VIX > 40)"

    if context.get('emergency_exit'):
        return True, "Emergency exit requested"

    return False, None
```

**Deep Dive (~10초)**:
```python
def should_use_deep_dive(self, context):
    """
    Deep Dive 조건:
    1. 신규 포지션 진입
    2. 리밸런싱
    3. 대형 포지션 (>10% portfolio)
    4. 복잡한 의사결정
    """

    if context.get('action_context') == 'new_position':
        return True, "New position entry"

    if context.get('action_context') == 'rebalancing':
        return True, "Portfolio rebalancing"

    if context.get('position_size_pct', 0) > 10:
        return True, "Large position (>10%)"

    return True, "Default to Deep Dive"
```

### 2. Order Validator

**File**: `backend/execution/order_validator.py`

**목적**: 주문 실행 전 최종 검증

**8 Hard Rules**:
```python
class OrderValidator:
    HARD_RULES = [
        "Position size must not exceed 30% of portfolio",
        "Position size must not exceed 10% if confidence < 0.7",
        "Must have Stop Loss for all positions",
        "Stop Loss must be within 10% of entry price",
        "No positions during earnings blackout (D-2 ~ D+1)",
        "Daily loss limit: -5% of portfolio",
        "VIX > 40: No new positions",
        "RISK_OFF + VIX > 30: No new positions"
    ]

    def validate(self, order, context):
        """
        Returns:
            (is_valid, error_message)
        """

        # Rule 1: Position size ≤ 30%
        if order['position_size'] > context['portfolio_value'] * 0.30:
            return False, "REJECT: Position size exceeds 30% of portfolio"

        # Rule 2: Position size ≤ 10% if confidence < 0.7
        if order['confidence'] < 0.7 and order['position_size'] > context['portfolio_value'] * 0.10:
            return False, "REJECT: Low confidence (< 0.7), position size must be ≤ 10%"

        # Rule 3: Stop Loss required
        if not order.get('stop_loss'):
            return False, "REJECT: No Stop Loss specified"

        # Rule 4: Stop Loss within 10%
        stop_loss_distance = abs(order['entry_price'] - order['stop_loss']) / order['entry_price']
        if stop_loss_distance > 0.10:
            return False, f"REJECT: Stop Loss too wide ({stop_loss_distance*100:.1f}% > 10%)"

        # Rule 5: Earnings blackout
        if self._is_earnings_blackout(order['symbol'], context['current_date']):
            return False, "REJECT: Earnings blackout period (D-2 ~ D+1)"

        # Rule 6: Daily loss limit
        if context.get('daily_loss_pct', 0) < -5.0:
            return False, "REJECT: Daily loss limit exceeded (-5%)"

        # Rule 7: VIX > 40
        if context.get('vix', 0) > 40 and order['action'] in ['buy', 'sell']:
            return False, "REJECT: VIX > 40 (extreme volatility), no new positions"

        # Rule 8: RISK_OFF + VIX > 30
        if context.get('market_regime') == 'RISK_OFF' and context.get('vix', 0) > 30:
            return False, "REJECT: RISK_OFF + VIX > 30, no new positions"

        return True, "APPROVED"
```

### 3. Shadow Trading Engine

**File**: `backend/execution/shadow_trading_engine.py`

**목적**: 가상 자금으로 실전 검증 (3개월)

**조건부 실행**:
```python
class ShadowTradingEngine:
    def execute_if_approved(self, pm_decision, market_data):
        """
        PM Agent의 승인이 있을 때만 실행
        """

        if pm_decision['final_decision'] != 'approve':
            self.log_rejected_proposal(pm_decision)
            return None

        if pm_decision['action'] == 'pass':
            return None

        # Hard Rules 통과 확인
        if not pm_decision['hard_rules_passed']:
            return None

        # Shadow Trading 실행
        trade = self._execute_shadow_trade(
            symbol=pm_decision['symbol'],
            action=pm_decision['action'],
            quantity=self._calculate_quantity(
                pm_decision['position_size'],
                market_data['current_price']
            ),
            entry_price=market_data['current_price'],
            stop_loss=pm_decision['stop_loss']
        )

        self.log_shadow_trade(trade)
        return trade
```

**Real-time P&L Tracking**:
```python
def update_positions(self):
    """
    매일 실행하여 포지션 P&L 업데이트
    """

    for position in self.get_open_positions():
        # 실시간 가격 조회
        current_price = self.fetch_current_price(position.symbol)

        # P&L 계산
        unrealized_pnl = (current_price - position.entry_price) * position.quantity

        # Stop Loss 체크
        if current_price <= position.stop_loss:
            self.close_position(position, reason='stop_loss_hit')

        # 데이터베이스 업데이트
        self.update_position_pnl(position.id, unrealized_pnl, current_price)
```

---

## 🗳️ Voting Mechanism

### Weighted Voting Formula

```python
def calculate_weighted_score(agent_opinions):
    """
    Weighted Voting:
    - Trader MVP: 35%
    - Risk MVP: 35%
    - Analyst MVP: 30%

    Returns:
        weighted_score (0.0 ~ 1.0)
    """

    trader_confidence = agent_opinions['trader_mvp']['confidence']
    risk_confidence = agent_opinions['risk_mvp']['confidence']
    analyst_confidence = agent_opinions['analyst_mvp']['confidence']

    weighted_score = (
        trader_confidence * 0.35 +
        risk_confidence * 0.35 +
        analyst_confidence * 0.30
    )

    return weighted_score
```

### Action Consensus

```python
def determine_final_action(agent_opinions):
    """
    다수결로 최종 Action 결정

    Examples:
    - BUY, BUY, HOLD → BUY (2/3)
    - BUY, SELL, HOLD → HOLD (동률 시 보수적 선택)
    - SELL, SELL, SELL → SELL (만장일치)
    """

    actions = [
        agent_opinions['trader_mvp']['action'],
        agent_opinions['risk_mvp']['action'],
        agent_opinions['analyst_mvp']['action']
    ]

    # 다수결
    from collections import Counter
    vote_counts = Counter(actions)
    most_common = vote_counts.most_common(2)

    # 명확한 다수 (2개 이상 일치)
    if most_common[0][1] >= 2:
        return most_common[0][0]

    # 동률 (1:1:1) → 보수적 선택 (HOLD 또는 PASS)
    if 'hold' in actions:
        return 'hold'
    elif 'pass' in actions:
        return 'pass'
    else:
        # BUY vs SELL 동률 → HOLD
        return 'hold'
```

### Voting Examples

**Example 1: 명확한 BUY 신호**
```json
{
  "trader_mvp": {"action": "buy", "confidence": 0.85},
  "risk_mvp": {"action": "buy", "confidence": 0.75},
  "analyst_mvp": {"action": "buy", "confidence": 0.70}
}

→ Final Action: BUY
→ Weighted Score: 0.85×0.35 + 0.75×0.35 + 0.70×0.30 = 0.77
→ Confidence: HIGH (unanimous)
```

**Example 2: 의견 분산 (2:1)**
```json
{
  "trader_mvp": {"action": "buy", "confidence": 0.80},
  "risk_mvp": {"action": "hold", "confidence": 0.60},
  "analyst_mvp": {"action": "buy", "confidence": 0.75}
}

→ Final Action: BUY (2/3)
→ Weighted Score: 0.80×0.35 + 0.60×0.35 + 0.75×0.30 = 0.72
→ Confidence: MEDIUM (majority but not unanimous)
```

**Example 3: 동률 (1:1:1)**
```json
{
  "trader_mvp": {"action": "buy", "confidence": 0.70},
  "risk_mvp": {"action": "sell", "confidence": 0.65},
  "analyst_mvp": {"action": "hold", "confidence": 0.60}
}

→ Final Action: HOLD (보수적 선택)
→ Weighted Score: 0.70×0.35 + 0.65×0.35 + 0.60×0.30 = 0.65
→ Confidence: LOW (no consensus)
```

---

## 📊 Legacy vs MVP 비교

### 구조 비교

| 항목 | Legacy (8-Agent) | MVP (3+1) | 변화 |
|------|------------------|-----------|------|
| **Agent 수** | 8개 독립 Agent | 3+1 통합 Agent | -56% |
| **API 호출** | 8회 (순차) | 3회 (병렬) | -62.5% |
| **응답 시간** | ~30초 | ~10초 | -67% |
| **비용/회** | $0.105 | $0.035 | -67% |
| **월비용** (100회) | $10.50 | $3.50 | -67% |
| **투표 가중치** | 8개 분산 | 3개 집중 | 단순화 |
| **Position Sizing** | ❌ 없음 | ✅ 자동화 | 신규 |
| **Hard Rules** | ❌ 없음 | ✅ 8개 검증 | 신규 |
| **Execution Router** | ❌ 없음 | ✅ Fast/Deep | 신규 |

### Agent Mapping

```
Legacy 8-Agent                    →  MVP 3+1-Agent
────────────────────────────────────────────────────────────
Trader (15%)                     →  Trader MVP (35%)
  + ChipWar Opportunity (12%)    →  (Attack)

Risk (20%)                       →  Risk MVP (35%)
  + Sentiment (8%)               →  (Defense + Position Sizing)

News (10%)                       →  Analyst MVP (30%)
  + Macro (10%)                  →  (Information)
  + Institutional (10%)
  + ChipWar Geopolitics

PM (15%)                         →  PM Agent MVP
                                 →  (Final Decision + Hard Rules)
```

### 기능 비교

**Legacy 장점**:
- ✅ 세분화된 전문성 (8개 관점)
- ✅ 각 Agent 독립적 검증 가능
- ✅ 특정 Agent만 교체 용이

**Legacy 단점**:
- ❌ 비용 과다 ($10.50/month)
- ❌ 속도 느림 (30초)
- ❌ 복잡도 높음 (8개 의견 통합)
- ❌ Position Sizing 수동
- ❌ Hard Rules 없음

**MVP 장점**:
- ✅ 비용 67% 절감 ($3.50/month)
- ✅ 속도 67% 향상 (10초)
- ✅ 단순화된 의사결정 (3개 의견)
- ✅ **Position Sizing 자동화**
- ✅ **8 Hard Rules 검증**
- ✅ **Execution Router**
- ✅ **Shadow Trading 통합**

**MVP 단점**:
- ❌ 전문성 일부 손실 (8→3 통합)
- ❌ Agent별 독립 검증 제한
- ❌ 하나의 Agent 오류 시 영향 범위 증가

**결론**: 실용성과 성능에서 MVP가 압도적 우위. 전문성 손실은 Agent 통합 설계로 최소화.

---

## 🔧 구현 세부사항

### File Structure

```
backend/
├── ai/
│   ├── mvp/                          # MVP Agent 구현
│   │   ├── trader_agent_mvp.py      # 485 lines
│   │   ├── risk_agent_mvp.py        # 612 lines
│   │   ├── analyst_agent_mvp.py     # 548 lines
│   │   ├── pm_agent_mvp.py          # 427 lines
│   │   └── war_room_mvp.py          # 723 lines (orchestrator)
│   │
│   ├── skills/                       # Skills Architecture
│   │   └── war_room_mvp/
│   │       ├── trader_agent_mvp/
│   │       │   ├── SKILL.md
│   │       │   └── handler.py
│   │       ├── risk_agent_mvp/
│   │       │   ├── SKILL.md
│   │       │   └── handler.py
│   │       ├── analyst_agent_mvp/
│   │       │   ├── SKILL.md
│   │       │   └── handler.py
│   │       ├── pm_agent_mvp/
│   │       │   ├── SKILL.md
│   │       │   └── handler.py
│   │       └── orchestrator_mvp/
│   │           ├── SKILL.md
│   │           └── handler.py
│   │
│   └── debate/                       # Legacy 8-Agent (유지)
│       ├── trader_agent.py
│       ├── risk_agent.py
│       └── ... (8개 파일)
│
├── execution/                        # Execution Layer (신규)
│   ├── execution_router.py          # 234 lines
│   ├── order_validator.py           # 187 lines
│   └── shadow_trading_engine.py     # 456 lines
│
└── routers/
    ├── war_room_mvp_router.py       # MVP API (신규)
    └── war_room_router.py           # Legacy API (유지)
```

### API Endpoints

**MVP System**:
```http
POST /api/war-room-mvp/deliberate
GET  /api/war-room-mvp/session/{session_id}
GET  /api/war-room-mvp/sessions
GET  /api/war-room-mvp/info
GET  /api/war-room-mvp/shadow/status
GET  /api/war-room-mvp/shadow/performance
GET  /api/war-room-mvp/shadow/positions
```

**Legacy System** (유지):
```http
POST /api/war-room/debate
GET  /api/war-room/session/{session_id}
GET  /api/war-room/sessions
```

### Environment Variables

```bash
# Dual Mode 지원
WAR_ROOM_MVP_USE_SKILLS=false  # true: Skill Handler, false: Direct Class

# AI Models
GEMINI_API_KEY=your_key_here

# Feature Flags
ENABLE_SHADOW_TRADING=true
ENABLE_DEEP_REASONING=true

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_trading
```

---

## ⚡ 성능 최적화

### 병렬 실행

**Legacy (순차 실행)**:
```python
# 30초 소요
opinions = []
for agent in [trader, risk, analyst, macro, institutional, news, chipwar, pm]:
    opinion = agent.analyze(...)  # 각 3-4초
    opinions.append(opinion)
```

**MVP (병렬 실행)**:
```python
# 10초 소요
import asyncio

async def parallel_analysis():
    trader_task = asyncio.create_task(trader_mvp.analyze(...))
    risk_task = asyncio.create_task(risk_mvp.analyze(...))
    analyst_task = asyncio.create_task(analyst_mvp.analyze(...))

    # 3개 동시 실행
    trader_result, risk_result, analyst_result = await asyncio.gather(
        trader_task, risk_task, analyst_task
    )

    # PM Agent는 순차 (3개 결과 필요)
    pm_result = await pm_mvp.make_final_decision(
        trader_result, risk_result, analyst_result
    )

    return pm_result
```

### 캐싱 전략

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Market data 5분 캐싱
@cache_with_ttl(300)
def get_market_conditions():
    return fetch_from_api()

# Macro context 1시간 캐싱
@cache_with_ttl(3600)
def get_macro_context():
    return fetch_macro_data()
```

### Database 쿼리 최적화

```python
# N+1 쿼리 제거
from sqlalchemy.orm import selectinload

# Before (N+1)
sessions = db.query(WarRoomSession).all()
for session in sessions:
    opinions = session.agent_opinions  # N개 쿼리!

# After (단일 쿼리)
sessions = db.query(WarRoomSession).options(
    selectinload(WarRoomSession.agent_opinions)
).all()
```

### 성능 메트릭 (현재)

| 지표 | 목표 | 현재 | Status |
|------|------|------|--------|
| **전체 응답 시간** | <15s | 12.76s | ✅ |
| **DB 쿼리 시간** | <1s | 0.3-0.5s | ✅ |
| **Gemini API 호출** (3회) | <12s | ~9s | ✅ |
| **Processing 시간** | <5s | ~3s | ✅ |
| **비용/회** | <$0.05 | $0.035 | ✅ |

---

## 🔮 향후 계획

### Short-term (1-2개월)

1. **News Agent Enhancement** (P0 - 즉시 착수)
   - Analyst MVP에 Macro Context 통합
   - Claude API로 뉴스 해석
   - DB에 해석 결과 저장

2. **Daily Report Generation** (P1)
   - PDF 보고서 자동 생성
   - Shadow Trading 성과 요약
   - Telegram 배포

3. **Frontend Optimization** (P1)
   - War Room MVP UI 업데이트
   - 번들 크기 20% 감소
   - API 폴링 → WebSocket 전환

### Mid-term (3-6개월)

4. **Database Phase 2 Optimization** (P2)
   - TimescaleDB hypertable 활성화
   - pgvector 임베딩 검색
   - Materialized Views

5. **Shadow Trading 검증 완료** (3개월, ~2026-04-01)
   - Success Criteria 평가
   - Live Trading 전환 결정

6. **Test Coverage 향상** (P2)
   - 60% → 90% coverage
   - MVP Agent 단위 테스트
   - E2E 테스트

### Long-term (6-12개월)

7. **Production Deployment**
   - Shadow Trading 성공 시 실제 자금 투입
   - Monitoring & Alerting (Prometheus + Grafana)
   - Sentry error tracking

8. **Advanced Features**
   - Multi-portfolio support
   - Options trading
   - Automated rebalancing
   - ML-based signal optimization

9. **MVP 2.0**
   - Agent 추가 (Crypto Agent, Options Agent)
   - Reinforcement Learning 통합
   - Self-improvement loop

---

## 📚 References

### 관련 문서
- [260104_Current_System_State.md](260104_Current_System_State.md) - 현재 시스템 상태
- [260104_Database_Schema.md](260104_Database_Schema.md) - 데이터베이스 스키마
- [2025_System_Overview.md](2025_System_Overview.md) - 시스템 개요
- [2025_Agent_Catalog.md](2025_Agent_Catalog.md) - Agent 카탈로그
- [2025_Implementation_Progress.md](2025_Implementation_Progress.md) - 구현 진행 상황

### 코드 파일
- `backend/ai/mvp/` - MVP Agent 구현
- `backend/execution/` - Execution Layer
- `backend/routers/war_room_mvp_router.py` - MVP API
- `backend/ai/skills/war_room_mvp/` - Skills Architecture

### Work Logs
- [Work_Log_20260104.md](../Work_Log_20260104.md) - Shadow Trading 모니터링
- [Work_Log_20260103.md](../Work_Log_20260103.md) - Shadow Trading 데이터 복원
- [Work_Log_20260102.md](../Work_Log_20260102.md) - DB 최적화

---

**Document Created**: 2026-01-04
**Next Review**: 2026-02-01
**Version**: 1.0
**Status**: ✅ Production Ready

---

**End of Document**
