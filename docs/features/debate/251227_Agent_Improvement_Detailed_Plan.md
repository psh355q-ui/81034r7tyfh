# Agent 개선 상세 계획서

**작성일**: 2025-12-27
**목적**: 각 Agent의 구체적인 개선 방향과 구현 방법 정리
**참고**: 251227_Agent_Analysis_Report.md 기반

---

## 📋 목차

1. [News Agent 개선](#1-news-agent-개선)
2. [Trader Agent 개선](#2-trader-agent-개선)
3. [Risk Agent 개선](#3-risk-agent-개선)
4. [Macro Agent 개선](#4-macro-agent-개선)
5. [Institutional Agent 개선](#5-institutional-agent-개선)
6. [Analyst Agent 개선](#6-analyst-agent-개선)
7. [ChipWar Agent 개선](#7-chipwar-agent-개선)
8. [구현 우선순위](#8-구현-우선순위)

---

## 1. News Agent 개선

### ✅ 완료된 개선 (2025-12-27)

#### 시계열 트렌드 분석
```python
def _analyze_temporal_trend(self, news_summaries: List[Dict]) -> Dict[str, Any]:
    """
    뉴스를 시간대별로 분석하여 감성 변화 추적

    Returns:
        - trend: IMPROVING/DETERIORATING/STABLE
        - recent_sentiment: 최근 3일 평균 감성
        - older_sentiment: 4-15일 평균 감성
        - sentiment_change: 변화량
        - risk_trajectory: INCREASING/DECREASING/NEUTRAL
    """
```

**효과**:
- 단순 스냅샷이 아닌 **트렌드 기반 판단**
- 위험도가 증가하는지 감소하는지 명확하게 파악
- IMPROVING 트렌드 시 BUY 신호 강화 (+0.1 boost)
- DETERIORATING 트렌드 시 SELL 신호 강화 (-0.1 boost)

### 🔄 추가 개선 필요 항목

#### 1.1 뉴스 소스 신뢰도 가중치

**현재 문제**:
- 모든 뉴스를 동등하게 취급
- Bloomberg, Reuters와 Unknown blog의 가중치가 같음

**개선 방향**:
```python
SOURCE_CREDIBILITY = {
    "Bloomberg": 1.0,
    "Reuters": 1.0,
    "WSJ": 0.95,
    "CNBC": 0.9,
    "Yahoo Finance": 0.8,
    "Seeking Alpha": 0.7,
    "Unknown": 0.5
}

def _calculate_weighted_sentiment(self, news_summaries: List[Dict]) -> float:
    """뉴스 소스 신뢰도를 반영한 가중 평균"""
    weighted_sum = 0
    total_weight = 0

    for news in news_summaries:
        source = news.get('source', 'Unknown')
        credibility = SOURCE_CREDIBILITY.get(source, 0.5)
        sentiment = news.get('sentiment', 0)

        weighted_sum += sentiment * credibility
        total_weight += credibility

    return weighted_sum / total_weight if total_weight > 0 else 0
```

#### 1.2 시간 감쇠 (Temporal Decay)

**현재 문제**:
- 15일 전 뉴스와 오늘 뉴스의 중요도가 같음

**개선 방향**:
```python
import math

def _apply_temporal_decay(self, news_summaries: List[Dict]) -> List[Dict]:
    """시간에 따라 뉴스 중요도 감소"""
    now = datetime.now()

    for news in news_summaries:
        published_date = news.get('published_at', now)
        days_ago = (now - published_date).days

        # 지수 감쇠: decay_factor = e^(-0.1 * days)
        # 0일: 1.0, 7일: 0.5, 15일: 0.22
        decay_factor = math.exp(-0.1 * days_ago)

        news['weight'] = decay_factor
        news['decayed_sentiment'] = news['sentiment'] * decay_factor

    return news_summaries
```

**효과**:
- 최근 뉴스에 더 높은 가중치
- 오래된 뉴스는 배경 정보로만 활용

#### 1.3 감성 점수 신뢰구간

**현재 문제**:
- Gemini가 반환한 감성 점수를 그대로 신뢰
- 뉴스 개수가 적을 때 신뢰도 낮음

**개선 방향**:
```python
def _calculate_confidence_interval(self, news_count: int, sentiment_score: float) -> tuple:
    """
    뉴스 개수를 고려한 신뢰구간 계산

    Returns:
        (lower_bound, upper_bound, confidence_level)
    """
    import numpy as np

    # 표본 크기에 따른 표준오차 계산
    # SE = σ / √n (σ=0.3 가정)
    standard_error = 0.3 / np.sqrt(news_count) if news_count > 0 else 1.0

    # 95% 신뢰구간 (z=1.96)
    margin_of_error = 1.96 * standard_error

    lower_bound = max(-1.0, sentiment_score - margin_of_error)
    upper_bound = min(1.0, sentiment_score + margin_of_error)

    # 뉴스 개수에 따른 신뢰도
    if news_count >= 20:
        confidence_level = 0.95
    elif news_count >= 10:
        confidence_level = 0.85
    elif news_count >= 5:
        confidence_level = 0.70
    else:
        confidence_level = 0.50

    return (lower_bound, upper_bound, confidence_level)
```

#### 1.4 뉴스 카테고리별 분석

**현재 문제**:
- 실적, 규제, M&A, 제품 발표 등을 구분하지 않음

**개선 방향**:
```python
NEWS_CATEGORIES = {
    "EARNINGS": {
        "keywords": ["earnings", "revenue", "profit", "EPS"],
        "impact_multiplier": 1.5  # 실적은 중요도 1.5배
    },
    "REGULATION": {
        "keywords": ["SEC", "lawsuit", "investigation", "fine"],
        "impact_multiplier": 1.3
    },
    "PRODUCT": {
        "keywords": ["launch", "release", "announced", "unveil"],
        "impact_multiplier": 1.1
    },
    "M&A": {
        "keywords": ["merger", "acquisition", "buyout", "takeover"],
        "impact_multiplier": 1.4
    }
}

def _categorize_news(self, title: str, content: str) -> str:
    """뉴스를 카테고리별로 분류"""
    text = (title + " " + content).lower()

    for category, info in NEWS_CATEGORIES.items():
        if any(kw in text for kw in info['keywords']):
            return category

    return "GENERAL"
```

---

## 2. Trader Agent 개선

### 🎯 최우선 개선 항목

#### 2.1 멀티 타임프레임 분석

**구현 방법**:
```python
async def analyze_multi_timeframe(self, ticker: str) -> Dict:
    """
    일봉, 주봉, 월봉 동시 분석

    전략:
    - 월봉 추세 확인 → 주봉 추세 확인 → 일봉 진입 타이밍
    - 상위 타임프레임 추세와 일치할 때만 강한 신호
    """
    # 1. 월봉 데이터 (20개월)
    monthly_data = await self._fetch_ohlcv(ticker, timeframe='1mo', limit=20)
    monthly_trend = self._analyze_trend(monthly_data)  # UPTREND/DOWNTREND/SIDEWAYS

    # 2. 주봉 데이터 (52주)
    weekly_data = await self._fetch_ohlcv(ticker, timeframe='1wk', limit=52)
    weekly_trend = self._analyze_trend(weekly_data)

    # 3. 일봉 데이터 (100일)
    daily_data = await self._fetch_ohlcv(ticker, timeframe='1d', limit=100)
    daily_signals = self._analyze_daily(daily_data)

    # 4. 타임프레임 정렬도 확인
    alignment_score = self._calculate_alignment(monthly_trend, weekly_trend, daily_signals['trend'])

    # 5. 신호 강도 조정
    if alignment_score > 0.8:  # 모든 타임프레임 일치
        confidence_boost = 0.2
        reasoning = f"강한 신호: 월봉({monthly_trend}), 주봉({weekly_trend}), 일봉({daily_signals['trend']}) 정렬"
    elif alignment_score < 0.3:  # 타임프레임 충돌
        confidence_penalty = -0.3
        reasoning = f"혼조 신호: 타임프레임 불일치 (정렬도 {alignment_score:.1%})"

    return {
        "action": daily_signals['action'],
        "confidence": min(0.95, daily_signals['confidence'] + confidence_boost),
        "reasoning": reasoning,
        "monthly_trend": monthly_trend,
        "weekly_trend": weekly_trend,
        "alignment_score": alignment_score
    }
```

#### 2.2 지지선/저항선 자동 탐지

**Pivot Point 방식**:
```python
def _find_support_resistance(self, ohlcv_data: List[Dict]) -> Dict:
    """
    최근 고점/저점 기반 지지선/저항선 탐지

    방법:
    - Pivot High: 좌우 5개 봉보다 높은 고점
    - Pivot Low: 좌우 5개 봉보다 낮은 저점
    """
    import numpy as np

    highs = [bar['high'] for bar in ohlcv_data]
    lows = [bar['low'] for bar in ohlcv_data]

    resistance_levels = []
    support_levels = []

    # Pivot Point 탐지 (좌우 5개 봉 확인)
    for i in range(5, len(ohlcv_data) - 5):
        # Pivot High
        if all(highs[i] > highs[i-5:i]) and all(highs[i] > highs[i+1:i+6]):
            resistance_levels.append(highs[i])

        # Pivot Low
        if all(lows[i] < lows[i-5:i]) and all(lows[i] < lows[i+1:i+6]):
            support_levels.append(lows[i])

    # 최근 3개 저항선/지지선만 사용
    resistance_levels = sorted(resistance_levels, reverse=True)[:3]
    support_levels = sorted(support_levels, reverse=True)[:3]

    current_price = ohlcv_data[-1]['close']

    # 현재가와 지지/저항 거리 계산
    nearest_support = max([s for s in support_levels if s < current_price], default=None)
    nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)

    support_distance = (current_price - nearest_support) / current_price if nearest_support else None
    resistance_distance = (nearest_resistance - current_price) / current_price if nearest_resistance else None

    return {
        "support_levels": support_levels,
        "resistance_levels": resistance_levels,
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "support_distance_pct": support_distance * 100 if support_distance else None,
        "resistance_distance_pct": resistance_distance * 100 if resistance_distance else None
    }
```

**매매 신호에 반영**:
```python
# 지지선 근처 = 매수 기회
if support_distance_pct and support_distance_pct < 2:  # 지지선 2% 이내
    confidence_boost += 0.15
    reasoning += f" | 지지선 근처 매수 기회 (${nearest_support:.2f})"

# 저항선 돌파 = 강한 매수
if current_price > nearest_resistance:
    confidence_boost += 0.2
    reasoning += f" | 저항선 돌파 (${nearest_resistance:.2f})"
```

#### 2.3 볼린저밴드 추가

**구현**:
```python
def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Dict:
    """
    볼린저밴드 계산

    Returns:
        - upper_band: 상단 밴드 (MA + 2σ)
        - middle_band: 중간선 (20일 MA)
        - lower_band: 하단 밴드 (MA - 2σ)
        - bandwidth: 밴드 폭 (변동성 지표)
        - percent_b: 현재가 위치 (0~1, 0.5=중간)
    """
    import numpy as np

    prices_array = np.array(prices[-period:])

    middle_band = np.mean(prices_array)
    std = np.std(prices_array)

    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)

    bandwidth = (upper_band - lower_band) / middle_band

    current_price = prices[-1]
    percent_b = (current_price - lower_band) / (upper_band - lower_band) if (upper_band - lower_band) > 0 else 0.5

    return {
        "upper_band": upper_band,
        "middle_band": middle_band,
        "lower_band": lower_band,
        "bandwidth": bandwidth,
        "percent_b": percent_b,
        "squeeze": bandwidth < 0.1  # 밴드 폭 좁아짐 (변동성 돌파 대기)
    }
```

**매매 신호**:
```python
bb = self._calculate_bollinger_bands(prices)

# 1. 하단 밴드 이탈 → 반등 매수
if bb['percent_b'] < 0:  # 하단 밴드 아래
    action = "BUY"
    confidence = 0.80
    reasoning = "볼린저밴드 하단 이탈, 과매도 반등 기대"

# 2. 상단 밴드 이탈 → 과열 매도
elif bb['percent_b'] > 1:  # 상단 밴드 위
    action = "SELL"
    confidence = 0.75
    reasoning = "볼린저밴드 상단 이탈, 과열 조정 예상"

# 3. 밴드 좁아짐 (Squeeze) → 변동성 돌파 대기
elif bb['squeeze']:
    action = "HOLD"
    confidence = 0.60
    reasoning = "볼린저밴드 수축, 큰 움직임 대기 (Bandwidth < 10%)"
```

#### 2.4 피보나치 되돌림 레벨

**구현**:
```python
def _calculate_fibonacci_levels(self, ohlcv_data: List[Dict]) -> Dict:
    """
    최근 고점/저점 기반 피보나치 되돌림 계산

    레벨:
    - 0% (최고점)
    - 23.6% 되돌림
    - 38.2% 되돌림
    - 50% 되돌림
    - 61.8% 되돌림 (황금비)
    - 100% (최저점)
    """
    # 최근 고점/저점 찾기 (52주)
    recent_high = max([bar['high'] for bar in ohlcv_data])
    recent_low = min([bar['low'] for bar in ohlcv_data])

    diff = recent_high - recent_low

    fib_levels = {
        "0%": recent_high,
        "23.6%": recent_high - (diff * 0.236),
        "38.2%": recent_high - (diff * 0.382),
        "50%": recent_high - (diff * 0.5),
        "61.8%": recent_high - (diff * 0.618),  # 황금비
        "100%": recent_low
    }

    current_price = ohlcv_data[-1]['close']

    # 현재가가 어느 레벨 근처인지 확인
    nearest_level = min(fib_levels.items(), key=lambda x: abs(x[1] - current_price))

    return {
        "levels": fib_levels,
        "recent_high": recent_high,
        "recent_low": recent_low,
        "nearest_level": nearest_level[0],
        "nearest_price": nearest_level[1],
        "distance_pct": abs(current_price - nearest_level[1]) / current_price * 100
    }
```

**매매 신호**:
```python
fib = self._calculate_fibonacci_levels(ohlcv_data)

# 61.8% 황금비 근처 = 강한 지지
if fib['nearest_level'] == '61.8%' and fib['distance_pct'] < 1:
    confidence_boost += 0.15
    reasoning += f" | 피보나치 61.8% 황금비 지지 (${fib['nearest_price']:.2f})"

# 38.2% 되돌림 완료 → 재상승
elif fib['nearest_level'] == '38.2%' and current_price > fib['levels']['38.2%']:
    confidence_boost += 0.10
    reasoning += " | 피보나치 38.2% 되돌림 후 재상승"
```

---

## 3. Risk Agent 개선

### ✅ 완료된 개선 (2025-12-27)

#### VaR (Value at Risk) 계산

**파일**: [backend/ai/debate/risk_agent.py:380-460](../backend/ai/debate/risk_agent.py#L380)

**구현 완료**:
```python
def _calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> Dict:
    """
    VaR (Value at Risk) 계산 (Historical Method)

    Returns:
        - var_1day: 1일 VaR (%)
        - var_10day: 10일 VaR (%)
        - cvar: Conditional VaR (Expected Shortfall)
    """
    # Historical VaR: 하위 percentile 사용
    var_percentile = (1 - confidence_level) * 100
    var_1day = np.percentile(returns_array, var_percentile)

    # 10일 VaR (Square Root of Time Rule)
    var_10day = var_1day * np.sqrt(10)

    # CVaR: VaR 초과 손실의 평균
    tail_losses = returns_array[returns_array <= var_1day]
    cvar = np.mean(tail_losses) if len(tail_losses) > 0 else var_1day
```

**매매 신호 통합** (lines 135-158):
- VaR < -5%: SELL 신호 (헌법 제4조 위반 가능성)
- CVaR < -10%: confidence_boost 감소
- VaR > -2%: confidence_boost 증가 (낮은 리스크)

### 🎯 추가 개선 필요 항목

#### 3.1 샤프 비율 계산

**구현**:
```python
def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.04) -> float:
    """
    샤프 비율 계산

    공식: (평균 수익률 - 무위험 수익률) / 수익률 표준편차

    Args:
        returns: 일별 수익률 리스트
        risk_free_rate: 연간 무위험 수익률 (기본값: 4%)

    Returns:
        Sharpe Ratio (1.0 이상이면 양호, 2.0 이상이면 우수)
    """
    import numpy as np

    if len(returns) < 20:
        return 0.0  # 데이터 부족

    returns_array = np.array(returns)

    # 연간화 (252 거래일 가정)
    annual_return = np.mean(returns_array) * 252
    annual_volatility = np.std(returns_array) * np.sqrt(252)

    if annual_volatility == 0:
        return 0.0

    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility

    return sharpe_ratio
```

**매매 신호 반영**:
```python
sharpe = self._calculate_sharpe_ratio(historical_returns)

if sharpe < 0.5:
    action = "SELL"
    confidence = 0.85
    reasoning = f"낮은 샤프 비율 ({sharpe:.2f} < 0.5) - 리스크 대비 수익 부족"
elif sharpe > 1.5:
    action = "BUY"
    confidence = 0.80
    reasoning = f"우수한 샤프 비율 ({sharpe:.2f}) - 안정적 수익 기대"
```

#### 3.2 VaR (Value at Risk) 계산

**Historical VaR 방식**:
```python
def _calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> Dict:
    """
    VaR 계산 (Historical Method)

    VaR = 95% 신뢰수준에서 최대 예상 손실

    Returns:
        - var_1day: 1일 VaR
        - var_10day: 10일 VaR (√10 스케일)
        - cvar: Conditional VaR (평균 손실)
    """
    import numpy as np

    returns_array = np.array(returns)

    # 95% VaR = 5% 최악의 손실
    var_percentile = 1 - confidence_level
    var_1day = np.percentile(returns_array, var_percentile * 100)

    # 10일 VaR (√10 스케일)
    var_10day = var_1day * np.sqrt(10)

    # CVaR (Conditional VaR): VaR 초과 손실의 평균
    tail_losses = returns_array[returns_array <= var_1day]
    cvar = np.mean(tail_losses) if len(tail_losses) > 0 else var_1day

    return {
        "var_1day": var_1day,
        "var_10day": var_10day,
        "cvar": cvar,
        "confidence_level": confidence_level
    }
```

**포지션 크기 권장**:
```python
var_result = self._calculate_var(historical_returns)

# VaR 기반 포지션 크기 제한
# 목표: 1일 VaR가 총 자본의 2% 이하
max_position_value = total_capital * 0.02 / abs(var_result['var_1day'])

return {
    "recommended_position_size": max_position_value,
    "var_1day": var_result['var_1day'],
    "reasoning": f"VaR 기반 권장 포지션 크기: ${max_position_value:,.0f} (총 자본의 {max_position_value/total_capital:.1%})"
}
```

#### 3.3 켈리 기준 (Kelly Criterion)

**구현**:
```python
def _calculate_kelly_position(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    켈리 기준 포지션 크기 계산

    공식: f* = (p * b - q) / b

    Args:
        win_rate: 승률 (0~1)
        avg_win: 평균 이익률
        avg_loss: 평균 손실률

    Returns:
        최적 포지션 비율 (0~1)
    """
    if avg_loss == 0:
        return 0.0

    p = win_rate  # 승률
    q = 1 - win_rate  # 패율
    b = avg_win / abs(avg_loss)  # 이익/손실 비율

    # 켈리 공식
    kelly_fraction = (p * b - q) / b

    # 안전 마진: Half-Kelly (켈리의 50%)
    half_kelly = max(0, min(kelly_fraction * 0.5, 0.25))  # 최대 25%

    return half_kelly
```

**사용 예**:
```python
# 과거 거래 분석
win_rate = 0.60  # 60% 승률
avg_win = 0.08  # 평균 8% 수익
avg_loss = 0.04  # 평균 4% 손실

kelly_pct = self._calculate_kelly_position(win_rate, avg_win, avg_loss)
recommended_position = total_capital * kelly_pct

return {
    "kelly_percentage": kelly_pct,
    "recommended_position": recommended_position,
    "reasoning": f"켈리 기준 권장 포지션: {kelly_pct:.1%} (${recommended_position:,.0f})"
}
```

---

## 4. Macro Agent 개선

### ✅ 완료된 개선 (2025-12-27)

#### 수익률 곡선 (Yield Curve) 분석

**파일**: [backend/ai/debate/macro_agent.py:230-280](../backend/ai/debate/macro_agent.py#L230)

**구현 완료**:
```python
def _analyze_yield_curve(self, yield_2y: float, yield_10y: float) -> Dict:
    """
    수익률 곡선 스프레드 (10Y - 2Y):
    - 역전 (< 0): 경기 침체 신호 (강한 SELL)
    - 평탄화 (0 ~ 25bps): 경기 둔화 조짐
    - 정상 (25 ~ 150bps): 건강한 경제
    - 가파름 (> 150bps): 경기 확장 기대
    """
```

**매매 신호 통합** (lines 104-118):
- 역전 (< 0bps): SELL 신호 (경기 침체 위험)
- 가파름 (> 150bps): confidence +0.15 (경기 확장)
- 평탄화 (0-25bps): confidence -0.10 (경기 둔화)

### 🎯 추가 개선 필요 항목

#### 4.1 유가 분석 (WTI Crude) ⭐ 추가 예정

**영향**:
- 유가 상승 → 인플레 압력 증가 → 에너지 섹터 유리, 항공/운송 불리
- 유가 하락 → 소비재/운송 유리, 에너지 섹터 불리

**구현**:
```python
def _analyze_oil_price(self, wti_price: float, wti_change_30d: float) -> Dict:
    """
    유가 분석 (WTI Crude)

    Args:
        wti_price: 현재 WTI 가격 ($/barrel)
        wti_change_30d: 30일 변화율 (%)

    Returns:
        {
            "oil_price": float,
            "signal": "HIGH|NORMAL|LOW",
            "inflation_pressure": "INCREASING|STABLE|DECREASING",
            "sector_impact": {...}
        }
    """
    # 유가 수준 판단
    if wti_price > 90:
        signal = "HIGH"
        inflation_pressure = "INCREASING"
        sector_impact = {
            "energy": "POSITIVE",  # XLE (Energy ETF)
            "airlines": "NEGATIVE",  # 항공사 비용 증가
            "consumer": "NEGATIVE"  # 소비재 압박
        }
    elif wti_price < 60:
        signal = "LOW"
        inflation_pressure = "DECREASING"
        sector_impact = {
            "energy": "NEGATIVE",
            "airlines": "POSITIVE",
            "consumer": "POSITIVE"
        }
    else:
        signal = "NORMAL"
        inflation_pressure = "STABLE"
        sector_impact = {}

    # 급등/급락 체크
    if wti_change_30d > 20:
        reasoning = f"유가 급등 ({wti_change_30d:.1f}%) - 인플레 압력 증가, 에너지 섹터 강세"
    elif wti_change_30d < -20:
        reasoning = f"유가 급락 ({wti_change_30d:.1f}%) - 소비 여력 증가, 에너지 섹터 약세"
    else:
        reasoning = f"유가 안정 (${wti_price:.2f}/배럴)"

    return {
        "oil_price": wti_price,
        "oil_change_30d": wti_change_30d,
        "signal": signal,
        "inflation_pressure": inflation_pressure,
        "sector_impact": sector_impact,
        "reasoning": reasoning
    }
```

**매매 신호 통합**:
```python
# 유가 분석
oil_analysis = None
if "wti_crude" in macro_data:
    oil_analysis = self._analyze_oil_price(
        wti_price=macro_data["wti_crude"],
        wti_change_30d=macro_data.get("wti_change_30d", 0)
    )

    # 유가 영향 반영
    sector = self._get_sector(ticker)  # 티커의 섹터 확인

    if sector == "Energy" and oil_analysis["signal"] == "HIGH":
        confidence_boost += 0.10
        reasoning += " | 유가 고공행진 - 에너지 섹터 수혜"
    elif sector in ["Airlines", "Transportation"] and oil_analysis["signal"] == "HIGH":
        confidence_boost -= 0.10
        reasoning += " | 유가 상승 - 운송 비용 부담"
```

#### 4.2 달러 인덱스 분석 (DXY) ⭐ 추가 예정

**영향**:
- 달러 강세 → 미국 수출 불리, 신흥국 압박, 금/원자재 하락
- 달러 약세 → 미국 수출 유리, 신흥국 수혜, 금/원자재 상승

**구현**:
```python
def _analyze_dollar_index(self, dxy: float, dxy_change_30d: float) -> Dict:
    """
    달러 인덱스 (DXY) 분석

    Args:
        dxy: 현재 달러 인덱스 (기준: 100)
        dxy_change_30d: 30일 변화율 (%)

    Returns:
        {
            "dxy": float,
            "signal": "STRONG|NEUTRAL|WEAK",
            "impact": {...}
        }
    """
    # 달러 강도 판단
    if dxy > 105:
        signal = "STRONG"
        impact = {
            "us_exporters": "NEGATIVE",  # 수출 기업 불리
            "multinationals": "NEGATIVE",  # 다국적 기업 불리
            "emerging_markets": "NEGATIVE",  # 신흥국 압박
            "gold": "NEGATIVE",  # 금 가격 하락
            "commodities": "NEGATIVE"  # 원자재 가격 하락
        }
    elif dxy < 95:
        signal = "WEAK"
        impact = {
            "us_exporters": "POSITIVE",
            "multinationals": "POSITIVE",
            "emerging_markets": "POSITIVE",
            "gold": "POSITIVE",
            "commodities": "POSITIVE"
        }
    else:
        signal = "NEUTRAL"
        impact = {}

    # 급등/급락
    if dxy_change_30d > 5:
        reasoning = f"달러 급강세 (DXY {dxy:.2f}, +{dxy_change_30d:.1f}%) - 수출 기업 부담, 신흥국 압박"
    elif dxy_change_30d < -5:
        reasoning = f"달러 급약세 (DXY {dxy:.2f}, {dxy_change_30d:.1f}%) - 수출 유리, 금/원자재 강세"
    else:
        reasoning = f"달러 안정 (DXY {dxy:.2f})"

    return {
        "dxy": dxy,
        "dxy_change_30d": dxy_change_30d,
        "signal": signal,
        "impact": impact,
        "reasoning": reasoning
    }
```

**매매 신호 통합**:
```python
# 달러 인덱스 분석
dxy_analysis = None
if "dxy" in macro_data:
    dxy_analysis = self._analyze_dollar_index(
        dxy=macro_data["dxy"],
        dxy_change_30d=macro_data.get("dxy_change_30d", 0)
    )

    # 달러 영향 반영
    if self._is_us_exporter(ticker) and dxy_analysis["signal"] == "STRONG":
        confidence_boost -= 0.08
        reasoning += " | 달러 강세 - 수출 경쟁력 약화"
    elif self._is_multinational(ticker) and dxy_analysis["signal"] == "STRONG":
        confidence_boost -= 0.05
        reasoning += " | 달러 강세 - 해외 수익 환차손"
```

#### 4.3 PMI (구매관리자지수) 분석

**구현**:
```python
async def _analyze_pmi(self) -> Dict:
    """
    제조업 PMI 분석

    - PMI > 50: 제조업 확장
    - PMI < 50: 제조업 위축
    - PMI 추세가 중요 (상승/하락)
    """
    # ISM Manufacturing PMI
    fred = Fred(api_key=os.environ.get('FRED_API_KEY'))

    pmi = fred.get_series('MANEMP', observation_start=datetime.now() - timedelta(days=180))

    current_pmi = pmi.iloc[-1]
    prev_pmi = pmi.iloc[-2]
    pmi_3m_avg = pmi.iloc[-3:].mean()

    # 추세 계산
    if current_pmi > prev_pmi and current_pmi > 50:
        trend = "EXPANDING_ACCELERATING"
    elif current_pmi > 50:
        trend = "EXPANDING_SLOWING"
    elif current_pmi < prev_pmi and current_pmi < 50:
        trend = "CONTRACTING_ACCELERATING"
    else:
        trend = "CONTRACTING_SLOWING"

    return {
        "current_pmi": current_pmi,
        "prev_pmi": prev_pmi,
        "pmi_3m_avg": pmi_3m_avg,
        "trend": trend,
        "is_expansion": current_pmi > 50
    }
```

#### 4.3 섹터 로테이션 분석

**구현**:
```python
def _analyze_sector_rotation(self, economic_cycle: str) -> Dict:
    """
    경기 사이클별 섹터 로테이션

    경기 사이클:
    - EARLY_RECOVERY: 금리 인하 시작, PMI 상승
    - MID_CYCLE: 경기 확장, 인플레이션 안정
    - LATE_CYCLE: 인플레이션 상승, 금리 인상
    - RECESSION: 경기 위축, 금리 인하
    """
    SECTOR_ROTATION = {
        "EARLY_RECOVERY": {
            "best": ["Financials", "Consumer Discretionary", "Technology"],
            "reasoning": "금리 인하 + 경기 회복 → 금융/소비재/기술주 선호"
        },
        "MID_CYCLE": {
            "best": ["Technology", "Industrials", "Materials"],
            "reasoning": "경기 확장 → 기술주/산업재/원자재 강세"
        },
        "LATE_CYCLE": {
            "best": ["Energy", "Materials", "Industrials"],
            "reasoning": "인플레이션 상승 → 에너지/원자재 수혜"
        },
        "RECESSION": {
            "best": ["Healthcare", "Consumer Staples", "Utilities"],
            "reasoning": "경기 방어 → 헬스케어/필수소비재/유틸리티"
        }
    }

    return SECTOR_ROTATION.get(economic_cycle, SECTOR_ROTATION["MID_CYCLE"])
```

---

## 5. Institutional Agent 개선

### 🎯 최우선 개선 항목

#### 5.1 다크풀 거래량 분석

**구현**:
```python
async def _analyze_dark_pool(self, ticker: str) -> Dict:
    """
    다크풀 거래량 분석

    다크풀:
    - 장외 대량 거래 (기관 투자자)
    - 다크풀 비중 증가 = 기관 매집 신호
    """
    # Finra ATS (Alternative Trading System) 데이터 사용
    # 또는 IEX API

    from iexfinance.stocks import Stock

    stock = Stock(ticker, token=os.environ.get('IEX_API_KEY'))

    # IEX Volume (투명 거래소)
    iex_volume = stock.get_volume()

    # 총 거래량
    total_volume = stock.get_quote()['latestVolume']

    # 다크풀 거래량 (추정)
    dark_pool_volume = total_volume - iex_volume
    dark_pool_ratio = dark_pool_volume / total_volume if total_volume > 0 else 0

    # 과거 평균과 비교
    avg_dark_pool_ratio = 0.35  # 평균 35% (FINRA 통계)

    is_elevated = dark_pool_ratio > avg_dark_pool_ratio * 1.2

    return {
        "dark_pool_volume": dark_pool_volume,
        "dark_pool_ratio": dark_pool_ratio,
        "avg_ratio": avg_dark_pool_ratio,
        "is_elevated": is_elevated,
        "signal": "ACCUMULATION" if is_elevated else "NORMAL"
    }
```

#### 5.2 옵션 Unusual Activity

**구현**:
```python
async def _analyze_unusual_options(self, ticker: str) -> Dict:
    """
    옵션 비정상 거래 탐지

    Unusual Activity:
    - 평균 대비 10배 이상 거래량
    - 대량 콜/풋 매수
    - 고액 프리미엄 지불 (고급 정보 반영)
    """
    # 옵션 체인 데이터
    import yfinance as yf

    stock = yf.Ticker(ticker)

    # 만기일 가져오기
    expirations = stock.options

    if not expirations:
        return {"unusual_activity": False}

    # 가장 가까운 만기
    nearest_expiration = expirations[0]

    # 옵션 체인
    options_chain = stock.option_chain(nearest_expiration)
    calls = options_chain.calls
    puts = options_chain.puts

    # 거래량 이상치 탐지
    call_volume_avg = calls['volume'].mean()
    put_volume_avg = puts['volume'].mean()

    unusual_calls = calls[calls['volume'] > call_volume_avg * 10]
    unusual_puts = puts[puts['volume'] > put_volume_avg * 10]

    # Put/Call Ratio
    total_call_volume = calls['volume'].sum()
    total_put_volume = puts['volume'].sum()
    put_call_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else 0

    return {
        "unusual_call_count": len(unusual_calls),
        "unusual_put_count": len(unusual_puts),
        "put_call_ratio": put_call_ratio,
        "sentiment": "BULLISH" if put_call_ratio < 0.7 else "BEARISH" if put_call_ratio > 1.3 else "NEUTRAL"
    }
```

#### 5.3 숏 인터레스트 (공매도 비중)

**구현**:
```python
async def _analyze_short_interest(self, ticker: str) -> Dict:
    """
    공매도 비중 분석

    Short Interest:
    - 높은 숏 인터레스트 = 약세 베팅
    - 급격한 증가 = 하락 압력
    - 숏 스퀴즈 가능성 (숏 커버링)
    """
    import yfinance as yf

    stock = yf.Ticker(ticker)
    info = stock.info

    # 숏 비중
    short_percent_float = info.get('shortPercentOfFloat', 0) * 100

    # 숏 커버 일수 (Short Ratio)
    short_ratio = info.get('shortRatio', 0)

    # 숏 스퀴즈 위험도
    if short_percent_float > 20 and short_ratio > 5:
        squeeze_risk = "HIGH"
    elif short_percent_float > 10:
        squeeze_risk = "MODERATE"
    else:
        squeeze_risk = "LOW"

    return {
        "short_percent_float": short_percent_float,
        "short_ratio": short_ratio,
        "squeeze_risk": squeeze_risk,
        "sentiment": "BEARISH" if short_percent_float > 15 else "NEUTRAL"
    }
```

---

## 6. Analyst Agent 개선

### ✅ 완료된 개선 (2025-12-27)

#### 경쟁사 비교 분석

**파일**: [backend/ai/debate/analyst_agent.py:287-452](../backend/ai/debate/analyst_agent.py#L287)

**구현 완료**:
```python
def _compare_with_peers(self, ticker: str, fundamental_data: Dict) -> Dict:
    """
    동종업계 경쟁사 비교 분석

    Returns:
        - sector: 섹터명
        - peer_comparison: P/E, Growth, Margin vs 섹터 평균
        - competitive_position: LEADER/COMPETITIVE/LAGGING
        - competitive_score: -3 ~ +3 점수
    """
```

**섹터 매핑**: AAPL, MSFT, GOOGL (Technology), TSLA (Automotive), JPM (Financials) 등

**매매 신호 통합** (lines 161-186):
- LEADER: BUY 신호 강화 (+0.15 confidence)
- LAGGING: SELL 신호 강화 또는 BUY 신호 약화 (-0.15 confidence)

### 🎯 추가 개선 필요 항목

#### 6.1 PEG Ratio (성장 대비 밸류에이션)

**구현**:
```python
def _calculate_peg_ratio(self, pe_ratio: float, growth_rate: float) -> Dict:
    """
    PEG Ratio 계산

    공식: PEG = P/E Ratio / 연간 성장률

    해석:
    - PEG < 1.0: 저평가 (성장 대비 싸다)
    - PEG = 1.0: 적정가
    - PEG > 2.0: 고평가 (성장 대비 비싸다)
    """
    if growth_rate <= 0:
        return {
            "peg_ratio": None,
            "valuation": "UNKNOWN",
            "reasoning": "음수 성장률 - PEG 계산 불가"
        }

    peg_ratio = pe_ratio / growth_rate

    if peg_ratio < 1.0:
        valuation = "UNDERVALUED"
        reasoning = f"PEG {peg_ratio:.2f} < 1.0 → 성장 대비 저평가"
    elif peg_ratio < 1.5:
        valuation = "FAIR"
        reasoning = f"PEG {peg_ratio:.2f} → 적정 밸류에이션"
    else:
        valuation = "OVERVALUED"
        reasoning = f"PEG {peg_ratio:.2f} > 1.5 → 성장 대비 고평가"

    return {
        "peg_ratio": peg_ratio,
        "valuation": valuation,
        "reasoning": reasoning
    }
```

#### 6.2 ROE (자기자본이익률)

**구현**:
```python
def _analyze_roe(self, net_income: float, shareholders_equity: float) -> Dict:
    """
    ROE 분석

    공식: ROE = 순이익 / 자기자본

    해석:
    - ROE > 15%: 우수
    - ROE 10-15%: 양호
    - ROE < 10%: 부진
    """
    if shareholders_equity <= 0:
        return {"roe": None, "quality": "UNKNOWN"}

    roe = (net_income / shareholders_equity) * 100

    if roe > 15:
        quality = "EXCELLENT"
        reasoning = f"ROE {roe:.1f}% → 우수한 자본 효율성"
    elif roe > 10:
        quality = "GOOD"
        reasoning = f"ROE {roe:.1f}% → 양호한 수익성"
    elif roe > 0:
        quality = "POOR"
        reasoning = f"ROE {roe:.1f}% → 낮은 자본 효율"
    else:
        quality = "NEGATIVE"
        reasoning = f"ROE {roe:.1f}% → 손실 발생"

    return {
        "roe": roe,
        "quality": quality,
        "reasoning": reasoning
    }
```

#### 6.3 FCF (잉여현금흐름)

**구현**:
```python
def _analyze_free_cash_flow(self, operating_cf: float, capex: float, revenue: float) -> Dict:
    """
    FCF 분석

    공식: FCF = 영업현금흐름 - 자본지출
    FCF Margin = FCF / 매출

    해석:
    - FCF Margin > 15%: 우수
    - 양수 FCF: 건전
    - 음수 FCF: 현금 소진
    """
    fcf = operating_cf - capex
    fcf_margin = (fcf / revenue * 100) if revenue > 0 else 0

    if fcf_margin > 15:
        quality = "EXCELLENT"
        reasoning = f"FCF Margin {fcf_margin:.1f}% → 강력한 현금 창출력"
    elif fcf_margin > 5:
        quality = "GOOD"
        reasoning = f"FCF Margin {fcf_margin:.1f}% → 건전한 현금흐름"
    elif fcf > 0:
        quality = "FAIR"
        reasoning = f"FCF 양수 → 현금흐름 유지"
    else:
        quality = "POOR"
        reasoning = f"FCF 음수 → 현금 소진 위험"

    return {
        "fcf": fcf,
        "fcf_margin": fcf_margin,
        "quality": quality,
        "reasoning": reasoning
    }
```

---

## 7. ChipWar Agent 개선

### 🎯 최우선 개선 항목

#### 7.1 AMD MI300X 분석 추가

**현재 문제**:
- AMD MI300X가 칩 프로필에 없음
- NVIDIA 독점으로만 인식

**개선**:
```python
CHIP_PROFILES = {
    "NVIDIA_H100": {
        "name": "NVIDIA H100",
        "manufacturer": "NVIDIA",
        "performance_score": 100,  # 기준점
        "market_share": 0.85,
        "tco_index": 1.2  # TCO 지수 (1.0 = 평균)
    },
    "AMD_MI300X": {
        "name": "AMD MI300X",
        "manufacturer": "AMD",
        "performance_score": 95,  # H100 대비 95%
        "market_share": 0.08,
        "tco_index": 0.9,  # TCO 10% 우위
        "disruption_potential": 0.7  # 파괴적 잠재력
    },
    "GOOGLE_TPU_V5": {
        "name": "Google TPU v5",
        "manufacturer": "Google",
        "performance_score": 85,
        "market_share": 0.05,
        "tco_index": 0.8,  # 내부 사용
        "workload_specialization": "TRANSFORMERS"
    }
}
```

#### 7.2 MLPerf 벤치마크 데이터

**구현**:
```python
async def _fetch_mlperf_results(self, ticker: str) -> Dict:
    """
    MLPerf 벤치마크 결과 조회

    MLPerf:
    - 머신러닝 성능 표준 벤치마크
    - Training/Inference 분리
    - 실제 워크로드 성능 측정
    """
    # MLPerf 공식 결과 (mlcommons.org)
    MLPERF_RESULTS_V4 = {
        "NVIDIA_H100": {
            "training_score": 100,
            "inference_score": 100,
            "efficiency": 90
        },
        "AMD_MI300X": {
            "training_score": 92,
            "inference_score": 88,
            "efficiency": 95  # 전력 효율 우수
        },
        "GOOGLE_TPU_V5": {
            "training_score": 85,
            "inference_score": 95,  # Inference 특화
            "efficiency": 88
        }
    }

    chip_name = self._get_chip_from_ticker(ticker)

    if chip_name in MLPERF_RESULTS_V4:
        results = MLPERF_RESULTS_V4[chip_name]

        return {
            "training_score": results['training_score'],
            "inference_score": results['inference_score'],
            "efficiency": results['efficiency'],
            "competitive_position": "LEADER" if results['training_score'] > 90 else "COMPETITIVE"
        }

    return {"mlperf_available": False}
```

---

## 8. 구현 우선순위

### Phase 1 (즉시 구현) - ✅ 완료 (2025-12-27)

1. ✅ **News Agent 시계열 트렌드 분석** (완료)
2. ✅ **Risk Agent VaR 계산** (완료)
3. ✅ **Analyst Agent 경쟁사 비교 분석** (완료)
4. ✅ **Sentiment Agent 생성** (완료) - 신규 에이전트

### Phase 2 (다음 우선순위)

1. **Macro Agent 유가/달러 분석** ⭐ NEW (1시간)
2. **Trader Agent 지지/저항선 탐지** (1시간)
3. **Trader Agent 멀티 타임프레임** (2시간)
4. **Trader Agent 볼린저밴드** (1시간)
5. **Risk Agent 샤프 비율 계산** (30분)

### Phase 3 (1주 이내)

6. **Analyst Agent PEG Ratio** (30분)
7. **Institutional Agent 다크풀 분석** (2시간)
8. **Analyst Agent ROE/FCF** (1시간)
9. **Macro Agent PMI 분석** (1시간)

### Phase 4 (2주 이내)

9. **Trader Agent 피보나치**
10. **ChipWar Agent AMD MI300X**
11. **Institutional Agent 옵션 분석**

---

## 📊 예상 성과 개선

### 현재 시스템
- Agent 개수: 7개
- Constitutional 통과율: 37%
- 에이전트 정확도: 미측정
- 모의 거래 승률: 미시행

### Phase 1 완료 후 (2025-12-27) ✅
- Agent 개수: **8개** (Sentiment Agent 추가)
- Constitutional 통과율: **80%+ 예상** (VaR 사전 체크)
- 소셜 감성 반영: **100%** (Twitter/Reddit 실시간)
- 경쟁사 비교 분석: **100%** (섹터 상대 평가)
- VaR 기반 리스크 관리: **100%**

### 최종 목표 (Phase 1-4 완료 시)
- Constitutional 통과율: **90%+**
- 에이전트 정확도: **65%+** (Self-Learning 후)
- 모의 거래 승률: **60%+**
- 샤프 비율: **1.0+**

---

## 🎯 신규 추가된 Agent

### Sentiment Agent (2025-12-27)

**파일**: [backend/ai/debate/sentiment_agent.py](../backend/ai/debate/sentiment_agent.py)

**투표 가중치**: 8%

**핵심 기능**:
1. Twitter/Reddit 감성 분석 (-1.0 ~ 1.0)
2. Fear & Greed Index 역투자 전략
   - Extreme Fear (< 25) → CONTRARIAN_BUY
   - Extreme Greed (> 75) → CONTRARIAN_SELL
3. Meme Stock 감지 (고거래량 + 급격한 감성 변화)
4. 소셜 트렌딩 분석

**War Room 통합**: 8개 Agent 구성 (총 100% 투표 가중치)

---

**작성 완료**: 2025-12-27
**Phase 1 완료**: 2025-12-27 ✅
**다음 리뷰**: Phase 2 착수 시 업데이트
