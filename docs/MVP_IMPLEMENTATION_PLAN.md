# MVP 구현 계획 - AI 토론 기반 시스템 재설계

**작성일**: 2025-12-31
**기반**: ChatGPT, Claude, Gemini 3개 AI 토론 결과

---

## 📋 핵심 요약

### 3개 AI의 합의된 결론

> **"설계는 훌륭하지만, 복잡도 축소 + 실전 검증 + 현실화가 필요하다"**

| 합의 사항 | 현재 상태 | MVP 목표 |
|----------|----------|---------|
| **Agent 수** | 8-9개 | 3+1개 |
| **검증 방식** | 없음 | 최소 3개월 Shadow Trading |
| **Hard Rule** | AI 해석 | 코드로 강제 |
| **책임 주기** | Daily 전부 | Daily(생각) / Weekly(행동) / Monthly(검증) |
| **Position Sizing** | 없음 | 필수 추가 |

---

## 🎯 시스템 재정의

### Before (위험)
> "자동으로 돈을 버는 AI 트레이딩 시스템"

### After (현실적 + 선구적)
> **"내 판단보다 나은지 검증 가능한 AI 전략 파트너"**

---

## 🏗️ MVP 아키텍처: 3+1 Agent 구조

### Agent 통폐합 전략

```
┌──────────────────────────────────────────────────────────────┐
│                    현재 (8-9 Agents)                          │
├──────────────────────────────────────────────────────────────┤
│  ❌ Trader (15%)                                              │
│  ❌ Risk (20%)                                                │
│  ❌ Analyst (15%)                                             │
│  ❌ News (14%)                                                │
│  ❌ Macro (14%)                                               │
│  ❌ Institutional (14%)                                       │
│  ❌ ChipWar (14%)                                             │
│  ❌ Sentiment (-)                                             │
│  ❌ DividendRisk (2%)                                         │
│                                                               │
│  문제: 9번 API 호출, 30초+ 지연, 책임 분산                    │
└──────────────────────────────────────────────────────────────┘
                          ↓ 통폐합
┌──────────────────────────────────────────────────────────────┐
│                    MVP (3+1 Agents)                           │
├──────────────────────────────────────────────────────────────┤
│                   ┌──────────────┐                            │
│                   │  PM Agent    │  ← 최종 의사결정          │
│                   │  (중재자)    │                            │
│                   └──────┬───────┘                            │
│          ┌───────────────┼───────────────┐                    │
│          ▼               ▼               ▼                    │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │ Trader   │    │   Risk   │    │ Analyst  │              │
│   │  (35%)   │    │  (35%)   │    │  (30%)   │              │
│   │  공격    │    │  방어    │    │  정보    │              │
│   └──────────┘    └──────────┘    └──────────┘              │
│                                                               │
│  장점: 3번 API 호출, <10초, 책임 명확                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 📝 Agent별 상세 설계

### 1️⃣ Trader Agent (35%) - 공격

**통합 대상**:
- ✅ 기존 Trader Agent (100%)
- 🔀 ChipWar Agent의 "기회 포착" 로직 (부분)

**역할**:
- Entry/Exit Timing 결정
- Momentum, Trend, Breakout
- 단기 수급, 가격 행동

**출력**:
```json
{
  "action": "BUY" | "SELL" | "HOLD",
  "confidence": 0.72,
  "time_horizon": "Intraday | 1-3d",
  "invalidated_if": "VWAP 하회",
  "momentum_score": 0.75,
  "entry_signal": "RSI oversold + MACD crossover"
}
```

**분석 항목**:
- 기술 지표: RSI, MACD, 이동평균, 볼린저 밴드
- 모멘텀: 가격 모멘텀, 거래량 변화, 상대강도
- 반도체 기회 (ChipWar 흡수)

---

### 2️⃣ Risk Agent (35%) - 방어

**통합 대상**:
- ✅ 기존 Risk Agent (100%)
- 🔀 Sentiment Agent의 "공포 감지" 로직 (부분)
- 🔀 DividendRisk Agent (100%)
- ⭐ **Position Sizing 신규 추가**

**역할**:
- 리스크 수준 판단
- 손절/익절 관리
- **Position Sizing 결정** (ChatGPT 제안)
- Veto Power (거부권)

**출력**:
```json
{
  "action": "BUY" | "SELL" | "HOLD" | "REDUCE",
  "confidence": 0.68,
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "EXTREME",

  // ⭐ Position Sizing (신규)
  "position_sizing": {
    "recommended_exposure": 0.15,  // 15% 노출
    "max_loss_allowed": -0.02,     // -2% 손실 한도
    "scale_in": true,               // 분할 매수 여부
    "stop_loss_pct": 0.02
  }
}
```

**분석 항목**:
- 리스크 지표: VaR, 변동성, 베타, MDD 추정
- 시장 공포 (Sentiment 흡수): VIX, Fear & Greed Index
- 배당 리스크 (DividendRisk 흡수)
- **Position Sizing**: Kelly Criterion, 계좌 리스크 기반

---

### 3️⃣ Analyst Agent (30%) - 정보

**통합 대상**:
- ✅ 기존 Analyst Agent (100%)
- 🔀 News Agent (100%)
- 🔀 Macro Agent (100%)
- 🔀 Institutional Agent (100%)
- 🔀 ChipWar Agent의 "지정학 분석" 로직 (부분)

**역할**:
- "무슨 일이 일어나고 있는지" 파악
- 방향성 (Direction) 제시
- 시장 Regime 판단

**출력**:
```json
{
  "action": "BUY" | "SELL" | "HOLD",
  "confidence": 0.65,
  "bias": "Bullish | Bearish | Neutral",
  "horizon": "1w | 1m",
  "key_driver": "Fed policy expectations",
  "info_summary": "Fed 금리 동결 + NVDA 실적 beat + 기관 매수 증가",
  "catalyst": "earnings" | "news" | "macro" | "institutional"
}
```

**분석 항목**:
- 펀더멘털: P/E, P/B, PEG, 실적 서프라이즈
- 뉴스 (News 흡수): 최근 뉴스 감성, 임팩트 스코어
- 매크로 (Macro 흡수): 금리, 인플레이션, 경기 사이클
- 기관 동향 (Institutional 흡수): 13F 변화, 내부자 거래
- 지정학 (ChipWar 부분 흡수): 반도체 수출규제

---

### 4️⃣ PM Agent - 최종 의사결정

**역할**:
- 3개 Agent 의견 종합
- 최종 Action 결정
- Position Sizing 최종 승인
- ⭐ **Hard Rules 강제** (Gemini 제안)
- ⭐ **Silence Policy** (ChatGPT 제안)

**핵심 로직**:
```python
class PMAgentMVP:
    def decide(self, trader_vote, risk_vote, analyst_vote):

        # 1. Hard Rules (AI 판단 무시) ⭐
        if risk_vote["risk_level"] == "EXTREME":
            return {
                "action": "SELL",
                "reason": "HARD_RULE: Extreme risk"
            }

        if risk_vote["position_sizing"]["max_loss_allowed"] < -0.05:
            return {
                "action": "HOLD",
                "reason": "HARD_RULE: Loss limit exceeded"
            }

        # 2. Silence Policy ⭐
        if self._should_stay_silent(trader_vote, risk_vote, analyst_vote):
            return {
                "action": "HOLD",
                "reason": "SILENCE: Low conviction across all agents"
            }

        # 3. Weighted Voting
        scores = {"BUY": 0, "SELL": 0, "HOLD": 0}

        for vote, weight in [
            (trader_vote, 0.35),
            (risk_vote, 0.35),
            (analyst_vote, 0.30)
        ]:
            action = vote["action"]
            confidence = vote["confidence"]
            scores[action] += weight * confidence

        # 4. 최종 결정
        final_action = max(scores, key=scores.get)
        final_confidence = scores[final_action]

        # 5. Position Sizing 적용
        exposure = risk_vote["position_sizing"]["recommended_exposure"]

        return {
            "action": final_action,
            "confidence": final_confidence,
            "exposure": exposure,  # ⭐ 실제 베팅 크기
            "votes": {
                "trader": trader_vote,
                "risk": risk_vote,
                "analyst": analyst_vote
            }
        }

    def _should_stay_silent(self, *votes):
        """Silence Policy: 모든 Agent confidence < 0.5면 판단 거부"""
        avg_confidence = sum(v["confidence"] for v in votes) / len(votes)
        return avg_confidence < 0.5
```

---

## ⚡ Fast Track vs Deep Dive 시스템

### Fast Track (반사신경) - Rule-based

**트리거**:
- 손절 라인 도달
- 일일 손실 -5% 도달
- 데이터 소스 단절
- 급락 (5분간 -3%)

**행동**:
- ❌ War Room 토론 없음
- ✅ Hard Rule로 즉시 실행

**구현**:
```python
class ExecutionRouter:
    async def route(self, signal_type: str, ticker: str, context: dict):

        # ==========================================
        # FAST TRACK (Rule-based, 토론 없음)
        # ==========================================

        # 1. 손절 라인 도달 → 즉시 SELL
        if context.get("stop_loss_triggered"):
            return await self.execute_immediately(
                "SELL", ticker, reason="STOP_LOSS"
            )

        # 2. 일일 손실 -5% 도달 → Circuit Breaker
        if context.get("daily_loss") < -0.05:
            return await self.halt_trading(reason="CIRCUIT_BREAKER")

        # 3. 데이터 소스 단절 → Defensive Mode
        if not context.get("data_available"):
            return await self.enter_defensive_mode(reason="DATA_OUTAGE")

        # ==========================================
        # DEEP DIVE (War Room MVP 소집)
        # ==========================================

        # 신규 진입, 포지션 변경 등
        return await self.war_room_mvp.run_debate(ticker, context)
```

### Deep Dive (숙고) - AI Debate

**트리거**:
- 신규 진입
- 포트폴리오 리밸런싱
- 대규모 뉴스 이벤트

**행동**:
- ✅ War Room MVP 소집 (3개 Agent)
- ✅ PM 최종 승인

---

## 💾 Position Sizing MVP 구현

### 설계 원칙 (ChatGPT 제안)

- 이론 ❌
- 안정성 ⭕
- 설명 가능성 ⭕
- Hard Rule 기반 ⭕

### 공식

```python
# Step 1. 기본 리스크 예산
ACCOUNT_RISK_PER_TRADE = 0.01  # 계좌의 1%

# Step 2. Risk Agent에서 받은 손절폭
stop_loss_pct = risk_agent.stop_loss_pct  # 예: 2%

# Step 3. 최대 포지션 크기 계산
position_size = ACCOUNT_RISK_PER_TRADE / stop_loss_pct
# 예: 0.01 / 0.02 = 0.50 (50%)

# Step 4. Confidence 보정
adjusted_size = position_size * PM_confidence
# 예: 0.50 * 0.6 = 0.30 (30%)

# Step 5. Risk Hard Cap 적용
final_size = min(adjusted_size, risk_agent.max_position_pct)
# 예: min(0.30, 0.20) = 0.20 (20%)
```

### Hard Rule

```python
# AI 무시하고 강제 적용
if final_size > ABSOLUTE_RISK_LIMIT:  # 예: 0.30
    reject_order()
    log_violation("HARD_LIMIT: Position size exceeded")
```

---

## 📊 책임 주기 분리 (ChatGPT 제안)

### Daily (생각) - "What we think"

**목적**: 사고 기록, 가설 제시

**내용**:
- 뉴스 해석
- 시장 관찰
- Agent 의견 요약

**금지**:
- ❌ Failure Vault 연결
- ❌ Shadow Penalty
- ❌ 가중치 조정

---

### Weekly (행동) - "What we did"

**목적**: 판단 책임

**내용**:
- 실제 매매 결정
- Position 변경 기록
- 손익 추적

---

### Monthly (검증) - "Were we right"

**목적**: 결과 책임

**내용**:
- NIA 점수 계산
- 실패 분석 (Failure Vault)
- 가중치 조정 (월 1회 또는 분기 1회)

---

## 🛡️ Hard Rules (Gemini 제안)

### 헌법의 기술적 강제성

**원칙**: 헌법은 AI가 해석 ❌ → 코드로 강제 ⭕

**구현**:
```python
class OrderValidator:
    """
    AI 판단과 무관하게 실행 단계에서 차단
    """

    def validate(self, order: Order) -> bool:
        # 1. Position Size 한도
        if order.size > self.risk_limit.max_position_pct:
            raise OrderRejected("Hard limit: Position size exceeded")

        # 2. 일일 손실 한도
        if self.account.daily_loss < -0.05:
            raise OrderRejected("Hard limit: Daily loss -5% reached")

        # 3. 계좌 잔고 부족
        if order.cost > self.account.buying_power:
            raise OrderRejected("Hard limit: Insufficient funds")

        # 4. 데이터 신뢰도
        if self.data_quality.score < 0.7:
            raise OrderRejected("Hard limit: Low data quality")

        return True
```

---

## 🚨 Silence Policy (ChatGPT 제안)

### "침묵할 권리" 명시

**조건**:
```python
# 1. 모든 Agent confidence < 0.5
avg_confidence = (trader.confidence + risk.confidence + analyst.confidence) / 3
if avg_confidence < 0.5:
    return SILENCE

# 2. Agent 의견 극단 분산
if (max_confidence - min_confidence) > 0.6:
    return SILENCE  # 의견 불일치

# 3. 데이터 부족
if data_points < 10:
    return SILENCE

# 4. 시장 비정상 (VIX > 40)
if market_regime == "EXTREME_VOLATILITY":
    return SILENCE
```

**행동**:
- Action: HOLD
- Reason: "SILENCE: 판단 거부 사유 기록"
- Log: Governance Ledger에 기록

---

## 📁 파일 구조 변경안

```
backend/
├── ai/
│   ├── agents/
│   │   ├── mvp/                    # ⭐ 신규
│   │   │   ├── __init__.py
│   │   │   ├── trader_agent_mvp.py     # Trader 35%
│   │   │   ├── risk_agent_mvp.py       # Risk 35% + Position Sizing
│   │   │   ├── analyst_agent_mvp.py    # Analyst 30% (4개 통합)
│   │   │   └── pm_agent_mvp.py         # PM (Hard Rules + Silence)
│   │   │
│   │   └── legacy/                 # 기존 Agent 동결
│   │       ├── trader_agent.py
│   │       ├── risk_agent.py
│   │       ├── analyst_agent.py
│   │       ├── news_agent.py
│   │       ├── macro_agent.py
│   │       ├── institutional_agent.py
│   │       ├── chip_war_agent.py
│   │       └── dividend_risk_agent.py
│   │
│   └── war_room/
│       ├── war_room_mvp.py         # 3+1 War Room
│       └── execution_router.py     # Fast Track / Deep Dive
│
├── services/
│   ├── position_sizer.py           # ⭐ 신규: Position Sizing
│   └── order_validator.py          # ⭐ 신규: Hard Rules
│
└── schedulers/
    ├── daily_reporter.py           # Daily: 사고 기록
    ├── weekly_reporter.py          # ⭐ 신규: Weekly 판단 책임
    └── monthly_learner.py          # ⭐ 수정: 월 1회 학습
```

---

## 🎯 구현 우선순위

### Week 1: Agent 통폐합

```
□ [1] Risk Agent MVP 작성 (Position Sizing 포함)
□ [2] Trader Agent MVP 작성
□ [3] Analyst Agent MVP 작성 (4개 Agent 통합)
□ [4] PM Agent MVP 작성 (Hard Rules + Silence Policy)
□ [5] 기존 Agent → legacy/ 폴더로 이동
```

### Week 2: Execution Layer

```
□ [6] execution_router.py 작성 (Fast Track / Deep Dive)
□ [7] order_validator.py 작성 (Hard Rules)
□ [8] position_sizer.py 작성 (Position Sizing)
□ [9] war_room_mvp.py 작성 (3+1 투표)
```

### Week 3: 책임 주기 분리

```
□ [10] daily_reporter.py 수정 (Failure Vault 제거)
□ [11] weekly_reporter.py 신규 작성
□ [12] monthly_learner.py 수정 (월 1회 가중치 조정)
```

### Week 4: Shadow Trading 준비

```
□ [13] shadow_trading.py 작성 (조건부 Shadow)
□ [14] dashboard에 Alpha/Win Rate/Profit Factor 추가
□ [15] "시스템 실패 조건" 문서 작성
```

### Week 5-8: 검증 (소액 실전)

```
□ [16] $100 실전 테스트 (Gemini 제안)
□ [17] 3개월 Shadow Trading (조건부)
□ [18] SPY 대비 성과 측정
□ [19] Agent별 기여도 분석
```

---

## 📈 성공 지표

### 1년 뒤 평가 기준

**핵심 지표**: Risk-Adjusted Alpha

```
Risk-Adjusted Alpha = (내 수익률 - SPY 수익률) / 내 MDD
```

**성공 기준**:
- Risk-Adjusted Alpha > 1.0
- Win Rate > 55%
- Profit Factor > 1.5
- MDD < -15%

---

## ⚠️ 실패 조건 명세

### 이 시스템이 반드시 실패하는 조건

**시장 환경**:
- 고변동성 + 저유동성 (VIX > 40, Volume < 평균 50%)
- 이벤트 리스크 중첩 (전쟁 + 금리 급변 + 실적 시즌)
- Flash Crash / Circuit Breaker 발동

**데이터 환경**:
- 데이터 소스 3개 이상 동시 단절
- YFinance API 변경
- 뉴스 크롤링 차단 (Cloudflare)

**AI 환경**:
- Gemini API 장애 1시간 이상
- 3개 Agent 모두 confidence < 0.3
- 토론 무한 루프 (의견 수렴 실패)

---

## 💡 최종 조언 (3개 AI 합의)

### ChatGPT
> **"6개월 동안 이 시스템이 '나보다 더 나은 판단을 했는지' 증명한다"**

### Claude
> **"복잡도와 수익률은 비례하지 않는다. 단순화하라"**

### Gemini
> **"$100이라도 진짜 돈을 태워보라. 그 1주일이 지난 몇 달의 개발보다 더 많은 걸 알려줄 것"**

---

## 🚀 Next Steps

### 즉시 실행

1. **Agent 3+1 통폐합 설계 확정**
2. **Hard Rule 리스트 작성**
3. **Position Sizing 로직 설계**

### 1-3개월

4. **Shadow Trading 3개월** (실제 돈 없이)
5. **Daily → Weekly 책임 추적으로 변경**
6. **Fast Track / Deep Dive 분리**

### 3-6개월

7. **$100 소액 실전 테스트**
8. **SPY Buy & Hold 대비 성과 측정**
9. **Agent별 기여도 분석**

---

**"3명의 정예 요원, 2개의 속도, 1개의 절대 원칙"**

이것만 있으면 충분합니다.
