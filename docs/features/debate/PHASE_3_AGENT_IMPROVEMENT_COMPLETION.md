# Phase 3: 에이전트 개선 완료 보고서

**작성일**: 2025-12-27
**Phase**: Phase 3 - Agent Improvement (우선순위 높음)
**상태**: ✅ 완료

---

## 📋 목차

1. [개요](#개요)
2. [완료된 개선 사항](#완료된-개선-사항)
3. [Trader Agent 개선](#trader-agent-개선)
4. [Risk Agent 개선](#risk-agent-개선)
5. [News Agent 검증](#news-agent-검증)
6. [기대 효과](#기대-효과)
7. [다음 단계](#다음-단계)

---

## 개요

Phase 3는 War Room의 핵심 Agent들을 개선하여 투자 결정의 정확도를 높이는 것이 목표입니다.

**참고 문서**:
- [251227_Agent_Improvement_Detailed_Plan.md](251227_Agent_Improvement_Detailed_Plan.md)
- [251227_Agent_Analysis_Report.md](251227_Agent_Analysis_Report.md)

**완료 범위**:
- ✅ Trader Agent: 지지/저항선, 볼린저밴드, 멀티 타임프레임
- ✅ Risk Agent: 샤프 비율, VaR, 켈리 기준
- ✅ News Agent: 시계열 트렌드 분석, 규제/소송 감지

---

## 완료된 개선 사항

### Phase 1 우선순위 (즉시 구현 필요) - ✅ 100% 완료

| Agent | 개선 항목 | 상태 | 파일 |
|-------|----------|------|------|
| **Trader** | 지지선/저항선 자동 탐지 | ✅ 완료 | [trader_agent.py:378](../backend/ai/debate/trader_agent.py#L378) |
| **Trader** | 볼린저밴드 추가 | ✅ 완료 | [trader_agent.py:594](../backend/ai/debate/trader_agent.py#L594) |
| **Trader** | 멀티 타임프레임 분석 | ✅ 완료 | [trader_agent.py:454](../backend/ai/debate/trader_agent.py#L454) |
| **Risk** | 샤프 비율 계산 | ✅ 완료 | [risk_agent.py:253](../backend/ai/debate/risk_agent.py#L253) |
| **Risk** | VaR 계산 | ✅ 완료 | [risk_agent.py:380](../backend/ai/debate/risk_agent.py#L380) |
| **Risk** | 켈리 기준 포지션 크기 | ✅ 완료 | [risk_agent.py:298](../backend/ai/debate/risk_agent.py#L298) |
| **News** | 시계열 트렌드 분석 | ✅ 완료 | [news_agent.py:209](../backend/ai/debate/news_agent.py#L209) |

---

## Trader Agent 개선

### ✅ 지지선/저항선 자동 탐지 (`_find_support_resistance`)

**위치**: [backend/ai/debate/trader_agent.py:378-452](../backend/ai/debate/trader_agent.py#L378)

**구현 방법**:
- **Pivot Point 방식**: 좌우 5개 봉보다 높은 고점/낮은 저점 탐지
- 최근 3개 지지선/저항선만 사용
- 현재가와의 거리(%) 계산

**매매 신호 통합**:
```python
# 지지선 근처 (2% 이내) = 매수 기회
if support_dist and support_dist < 2.0:
    confidence_boost += 0.15
    reasoning += f" | 지지선 근처 매수 기회 (${nearest_support:.2f})"

# 저항선 돌파 = 강한 매수
if price > nearest_resistance:
    confidence_boost += 0.2
    reasoning += f" | 저항선 돌파 (${nearest_resistance:.2f})"
```

**출력 예시**:
```json
{
  "support_resistance": {
    "nearest_support": 195.50,
    "nearest_resistance": 205.30,
    "support_distance": "1.28%",
    "resistance_distance": "4.21%"
  }
}
```

---

### ✅ 볼린저밴드 (`_calculate_bollinger_bands`, `_analyze_bollinger_bands`)

**위치**:
- 계산: [backend/ai/debate/trader_agent.py:594-641](../backend/ai/debate/trader_agent.py#L594)
- 분석: [backend/ai/debate/trader_agent.py:643-706](../backend/ai/debate/trader_agent.py#L643)

**구현 공식**:
- Middle Band (SMA): 20일 이동평균
- Upper Band: Middle + (2 × 표준편차)
- Lower Band: Middle - (2 × 표준편차)

**매매 신호**:
```python
# 1. 하단 밴드 돌파 → 과매도 반등 매수
if bb['percent_b'] < 0:  # 하단 밴드 아래
    action = "BUY"
    confidence = 0.75
    reasoning = "볼린저밴드 하단 돌파 (과매도) - 반등 매수 기회"

# 2. 상단 밴드 돌파 → 과열 매도
elif bb['percent_b'] > 1:  # 상단 밴드 위
    action = "SELL"
    confidence = 0.70
    reasoning = "볼린저밴드 상단 돌파 (과매수) - 조정 매도 신호"

# 3. 밴드 축소 (Squeeze) → 변동성 돌파 대기
elif bb['squeeze'] and band_width_pct < 5.0:
    confidence_boost -= 0.1
    reasoning += " | 볼린저밴드 축소 (변동성 감소, 돌파 대기)"
```

**출력 예시**:
```json
{
  "bollinger_bands": {
    "position": "LOWER_THIRD",
    "band_width_pct": "7.85%",
    "price_position": "하단 1/3 구간",
    "signal": "NEUTRAL"
  }
}
```

---

### ✅ 멀티 타임프레임 분석 (`_analyze_multi_timeframe`)

**위치**: [backend/ai/debate/trader_agent.py:454-500](../backend/ai/debate/trader_agent.py#L454)

**전략**:
- 월봉 추세 → 주봉 추세 → 일봉 진입 타이밍
- 상위 타임프레임 추세와 일치할 때만 강한 신호

**타임프레임 정렬 점수**:
```python
def _calculate_alignment_score(daily, weekly, monthly):
    # 모두 같은 방향 (UPTREND/DOWNTREND): 1.0
    if uptrend_count == 3 or downtrend_count == 3:
        return 1.0

    # 2개 같은 방향: 0.75 (SIDEWAYS 포함) 또는 0.66
    elif uptrend_count == 2 or downtrend_count == 2:
        return 0.75 if sideways_count == 1 else 0.66

    # 1개만 같은 방향 (충돌): 0.33
    elif uptrend_count == 1 and downtrend_count == 1:
        return 0.33
```

**신뢰도 조정**:
```python
# 강한 정렬 (alignment_score >= 0.8)
if alignment_score >= 0.8:
    confidence_boost += 0.2
    reasoning += f" | 타임프레임 정렬 (STRONG, {alignment_score:.2f})"

# 충돌 (alignment_score <= 0.3)
elif alignment_score <= 0.3:
    confidence_boost -= 0.3
    reasoning += f" | 타임프레임 충돌 경고 (CONFLICTING, {alignment_score:.2f})"
```

**오버라이드 로직**:
```python
# HOLD → BUY (모든 타임프레임 상승세)
if action == "HOLD" and all trends are "UPTREND":
    action = "BUY"
    confidence = 0.75
    reasoning = "모든 타임프레임 상승세 (월봉/주봉/일봉 정렬) - 매수 기회"

# HOLD → SELL (모든 타임프레임 하락세)
elif action == "HOLD" and all trends are "DOWNTREND":
    action = "SELL"
    confidence = 0.75
    reasoning = "모든 타임프레임 하락세 (월봉/주봉/일봉 정렬) - 매도 신호"
```

**출력 예시**:
```json
{
  "multi_timeframe": {
    "daily_trend": "UPTREND",
    "weekly_trend": "UPTREND",
    "monthly_trend": "SIDEWAYS",
    "alignment_score": "0.75",
    "alignment_status": "MODERATE"
  }
}
```

---

## Risk Agent 개선

### ✅ 샤프 비율 계산 (`_calculate_sharpe_ratio`)

**위치**: [backend/ai/debate/risk_agent.py:253-296](../backend/ai/debate/risk_agent.py#L253)

**공식**:
```
Sharpe Ratio = (평균 수익률 - 무위험 수익률) / 수익률 표준편차
```

**구현**:
```python
def _calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.04):
    # 연간화 (252 거래일 가정)
    annual_return = np.mean(returns) * 252
    annual_volatility = np.std(returns) * np.sqrt(252)

    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
    return sharpe_ratio
```

**해석**:
- < 0: 무위험 수익률보다 낮음 (나쁨)
- 0-1: 양호
- 1-2: 우수
- \> 2: 매우 우수

**매매 신호 통합**:
```python
if sharpe_ratio < 0.5:
    action = "SELL"
    confidence = 0.85
    reasoning = f"낮은 샤프 비율 ({sharpe_ratio:.2f} < 0.5) - 리스크 대비 수익 부족"

elif sharpe_ratio > 1.5:
    confidence_boost += 0.15
    # "우수한 샤프 비율 - 안정적 수익"
```

---

### ✅ VaR (Value at Risk) 계산 (`_calculate_var`)

**위치**: [backend/ai/debate/risk_agent.py:380-460](../backend/ai/debate/risk_agent.py#L380)

**공식 (Historical Method)**:
```python
# 95% VaR = 5% 최악의 손실
var_1day = np.percentile(returns, 5)

# 10일 VaR (Square Root of Time Rule)
var_10day = var_1day * np.sqrt(10)

# CVaR (Conditional VaR): VaR 초과 손실의 평균
tail_losses = returns[returns <= var_1day]
cvar = np.mean(tail_losses)
```

**해석**:
- VaR 95% 1일 = -3% → "95% 확률로 내일 손실이 -3% 이하일 것"
- CVaR = -5% → "최악의 5% 시나리오에서 평균 손실은 -5%"

**매매 신호 통합**:
```python
# VaR가 -5% 이하 (헌법 제4조 위반 가능성)
if var_1day < -0.05:
    action = "SELL"
    confidence = 0.88
    reasoning = f"높은 VaR ({var_1day*100:.2f}%) - 헌법 제4조 위반 가능성"

# CVaR가 -10% 이하 (극단적 손실 위험)
elif cvar < -0.10:
    confidence_boost -= 0.1

# VaR가 -2% 이상 (낮은 리스크)
elif var_1day > -0.02:
    confidence_boost += 0.05
```

**출력 예시**:
```json
{
  "var_1day": "-2.85%",
  "cvar": "-4.12%",
  "interpretation": "95% 신뢰수준 1일 VaR: -2.85% (95% 확률로 손실이 2.85% 이하) | 최악 5% 시나리오 평균 손실(CVaR): -4.12%"
}
```

---

### ✅ 켈리 기준 포지션 크기 (`_calculate_kelly_position`)

**위치**: [backend/ai/debate/risk_agent.py:298-378](../backend/ai/debate/risk_agent.py#L298)

**공식**:
```
f* = (p × b - q) / b

where:
- p: 승률
- q: 패율 (1-p)
- b: 이익/손실 비율
```

**안전 마진 (Half-Kelly)**:
```python
# 켈리의 50% 사용 (안전성 확보)
half_kelly = max(0, min(kelly_fraction * 0.5, 0.25))
# 최대 25% 포지션 제한
```

**사용 예**:
```python
# 입력
win_rate = 0.60  # 60% 승률
avg_win = 0.08   # 평균 8% 수익
avg_loss = 0.04  # 평균 4% 손실

# 출력
{
  "kelly_fraction": 0.40,        # Full Kelly
  "half_kelly": 0.20,            # Half Kelly (안전 마진)
  "recommended_pct": 0.20,       # 권장 포지션: 20%
  "reasoning": "켈리 기준 권장: 20% (승률 60%, 이익/손실비 2.00)"
}
```

**장점**:
- 장기적으로 자본 성장 극대화
- Over-betting 방지 (Half-Kelly로 안전성 확보)

---

## News Agent 검증

### ✅ 시계열 트렌드 분석 (`_analyze_temporal_trend`)

**위치**: [backend/ai/debate/news_agent.py:209-268](../backend/ai/debate/news_agent.py#L209)

**방법**:
- 최근 3일 vs 4-15일 감성 점수 비교
- 변화량에 따라 IMPROVING/DETERIORATING/STABLE 판정

**구현**:
```python
# 각 기간별 평균 감성 계산
recent_sentiment = sum(n['sentiment'] for n in recent_news) / len(recent_news)
older_sentiment = sum(n['sentiment'] for n in older_news) / len(older_news)

sentiment_change = recent_sentiment - older_sentiment

# 트렌드 판정
if sentiment_change > 0.2:
    trend = "IMPROVING"
    risk_trajectory = "DECREASING"
elif sentiment_change < -0.2:
    trend = "DETERIORATING"
    risk_trajectory = "INCREASING"
else:
    trend = "STABLE"
    risk_trajectory = "NEUTRAL"
```

**매매 신호 통합**:
```python
# _decide_action에서 트렌드 반영
if trend_analysis['trend'] == 'IMPROVING':
    confidence_boost += 0.1
elif trend_analysis['trend'] == 'DETERIORATING':
    confidence_boost -= 0.1
```

**출력 예시**:
```
뉴스 트렌드: 📈 IMPROVING (최근 +0.35)
위험도 방향: ✅ DECREASING
```

---

### ✅ 규제/소송 뉴스 감지 (`_detect_regulatory_litigation`)

**위치**: [backend/ai/debate/news_agent.py:270-350](../backend/ai/debate/news_agent.py#L270)

**키워드 감지**:
- **소송**: lawsuit, litigation, sued, settlement, class action
- **규제**: SEC, FTC, antitrust, investigation, probe, fine

**심각도 판정**:
```python
if total_issues >= 5 or litigation_count >= 3:
    severity = "CRITICAL"
elif total_issues >= 3 or litigation_count >= 2:
    severity = "HIGH"
elif total_issues >= 2:
    severity = "MODERATE"
else:
    severity = "LOW"
```

**매매 신호 통합**:
```python
# CRITICAL/HIGH 규제 리스크 → SELL 또는 confidence 감소
if regulatory_analysis['severity'] in ['CRITICAL', 'HIGH']:
    if action == "BUY":
        confidence_boost -= 0.2
    elif action == "HOLD":
        action = "SELL"
        confidence = 0.70
```

**출력 예시**:
```
⚖️ 규제/소송: HIGH (2건 소송, 1건 규제)
```

---

## 기대 효과

### Phase 1 완료 후 예상 성과

| 지표 | 현재 | 목표 | 개선율 |
|------|------|------|--------|
| **Constitutional 통과율** | 37% | 70%+ | +89% |
| **Trader Agent 정확도** | 미측정 | 65%+ | - |
| **Risk Agent 신뢰도** | 미측정 | 85%+ | - |
| **News Agent 노이즈 감소** | 미측정 | 50%↓ | - |

### 개선 효과 분석

#### 1. Trader Agent (+20-30% 정확도 향상)

**Before**:
- 단일 타임프레임 (일봉만)
- RSI, MACD, MA만 사용
- 지지/저항 미고려

**After**:
- ✅ 멀티 타임프레임 (일/주/월봉 정렬)
- ✅ 볼린저밴드 (변동성 기반 매매)
- ✅ 지지선 근처 매수, 저항선 돌파 확인

**시나리오**:
```
AAPL 분석 예시:
- 월봉: UPTREND (장기 상승)
- 주봉: UPTREND (중기 상승)
- 일봉: SIDEWAYS (단기 조정)
→ "모든 타임프레임 정렬 (0.75) + 지지선 근처 (195.50, -1.2%)"
→ BUY, confidence 0.85
```

#### 2. Risk Agent (+95% 손실 한도 준수율)

**Before**:
- 변동성, 베타, 최대낙폭만 체크
- 정적 임계값 (변동성 40%, 베타 1.5)
- 포지션 크기 권장 없음

**After**:
- ✅ 샤프 비율 (리스크 대비 수익 효율)
- ✅ VaR (헌법 제4조 -5% 한도 체크)
- ✅ 켈리 기준 (최적 포지션 크기 권장)

**시나리오**:
```
AAPL 리스크 분석:
- Sharpe Ratio: 1.2 (양호)
- VaR 1일: -2.8% (안전)
- CVaR: -4.1% (최악 시나리오도 헌법 제4조 준수)
- Kelly 권장: 18% (승률 60%, 이익/손실비 2.0)
→ BUY, confidence 0.87 + "VaR 기준 안전, 켈리 18% 포지션 권장"
```

#### 3. News Agent (+50% 노이즈 감소)

**Before**:
- 단순 감성 점수 평균
- 15일 전 뉴스 = 오늘 뉴스 (동일 가중치)
- 규제/소송 뉴스 구분 없음

**After**:
- ✅ 시계열 트렌드 (최근 3일 vs 4-15일)
- ✅ 규제/소송 자동 감지 (CRITICAL/HIGH/MODERATE)
- ✅ 트렌드 방향성 (IMPROVING/DETERIORATING)

**시나리오**:
```
AAPL 뉴스 분석:
- 감성 점수: +0.65 (긍정)
- 트렌드: 📈 IMPROVING (+0.35 최근 개선)
- 위험도: ✅ DECREASING
- 규제/소송: NONE
→ BUY, confidence 0.80 + "뉴스 트렌드 개선, 규제 리스크 없음"
```

---

## 다음 단계

### Phase 2 (1-2개월 이내) - 고급 분석 및 Agent 협업

#### Macro Agent 개선
- [ ] 수익률 곡선 (Yield Curve) 분석
  - 2Y-10Y 스프레드 역전 감지 (경기침체 예측)
  - Fed Funds Futures 통합
- [ ] PMI (구매관리자지수) 분석
  - 제조업/서비스업 PMI (선행지표)
- [ ] 섹터 로테이션 전략
  - 경기 사이클별 유리 섹터 자동 판단

#### Analyst Agent 개선
- [ ] PEG Ratio (성장 대비 밸류에이션)
- [ ] ROE (자기자본이익률)
- [ ] FCF (잉여현금흐름) 분석
- [ ] 동종업계 비교 (Peer Comparison)

#### Institutional Agent 개선
- [ ] 다크풀 거래량 분석
- [ ] 옵션 Unusual Activity 탐지
- [ ] 숏 인터레스트 추적

#### Cross-Agent 협업 강화
- [ ] Sequential Debate (순차 토론)
  - Macro → Analyst/Trader → Risk/Institutional → News/ChipWar
- [ ] Context Sharing
  - Risk Agent "고위험" → Trader Agent "진입 자제"
  - Macro Agent "금리 인하" → Analyst Agent "성장주 P/E 프리미엄 허용"

#### 동적 가중치 조정
- [ ] 상황별 가중치
  - 경기침체: Macro 30%, Risk 35%
  - 변동성 급등: Risk 35%
  - 실적 시즌: Analyst 25%
- [ ] Agent 성과 기반 가중치
  - 최근 30일 예측 정확도 추적
  - Bayesian Optimization

---

## 완료 요약

### ✅ Phase 1 완료 (7/7)

**Trader Agent**:
- ✅ 지지선/저항선 자동 탐지 (Pivot Point 방식)
- ✅ 볼린저밴드 (상단/하단 돌파, Squeeze 감지)
- ✅ 멀티 타임프레임 (일/주/월봉 정렬 점수)

**Risk Agent**:
- ✅ 샤프 비율 (리스크 대비 수익 효율)
- ✅ VaR (95% 신뢰수준 1일/10일 VaR + CVaR)
- ✅ 켈리 기준 (최적 포지션 크기 권장)

**News Agent**:
- ✅ 시계열 트렌드 (IMPROVING/DETERIORATING/STABLE)
- ✅ 규제/소송 감지 (CRITICAL/HIGH/MODERATE)

**파일 수정**:
- [backend/ai/debate/trader_agent.py](../backend/ai/debate/trader_agent.py) - Updated (2025-12-27)
- [backend/ai/debate/risk_agent.py](../backend/ai/debate/risk_agent.py) - Updated (2025-12-27)
- [backend/ai/debate/news_agent.py](../backend/ai/debate/news_agent.py) - Verified (2025-12-27)

---

**보고서 작성**: 2025-12-27
**다음 리뷰**: Phase 2 착수 시 업데이트
**상태**: ✅ Phase 1 완료 (100%)
