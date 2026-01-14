# 다음 단계 - 2025-12-28

**작성일**: 2025-12-27
**Phase 3 완료 후**: 내일 진행 권장 옵션

---

## 📋 Phase 3 완료 요약

### ✅ 오늘 완료된 작업 (2025-12-27)

1. **Sentiment Agent 생성** - [sentiment_agent.py](../backend/ai/debate/sentiment_agent.py)
2. **Risk Agent VaR 추가** - [risk_agent.py:380-460](../backend/ai/debate/risk_agent.py#L380)
3. **Analyst Agent 경쟁사 비교** - [analyst_agent.py:287-452](../backend/ai/debate/analyst_agent.py#L287)
4. **완료 보고서 작성** - [PHASE_3_AGENT_IMPROVEMENT_FINAL_COMPLETION.md](PHASE_3_AGENT_IMPROVEMENT_FINAL_COMPLETION.md)

### ✅ 추가 완료된 작업 (2025-12-28)

5. **Macro Agent 유가 분석 추가** - [macro_agent.py:230-292](../backend/ai/debate/macro_agent.py#L230)
   - WTI Crude 유가 분석 (HIGH > $90, LOW < $60)
   - 섹터별 영향 분석 (Energy, Airlines, Transportation, Consumer)
   - 30일 변화율 추적 (급등/급락 감지)

6. **Macro Agent 달러 인덱스 추가** - [macro_agent.py:294-353](../backend/ai/debate/macro_agent.py#L294)
   - DXY (Dollar Index) 분석 (STRONG > 105, WEAK < 95)
   - 수출 기업/다국적 기업 영향 분석
   - 금/원자재 섹터 영향 분석

7. **Macro Agent Helper 메서드** - [macro_agent.py:355-435](../backend/ai/debate/macro_agent.py#L355)
   - `_get_sector()`: 티커 섹터 매핑 (20+ 티커)
   - `_is_us_exporter()`: 수출 기업 식별 (9개 기업)
   - `_is_multinational()`: 다국적 기업 식별 (13개 기업)

8. **Macro Agent 통합 완료** - [macro_agent.py:64-276](../backend/ai/debate/macro_agent.py#L64)
   - `_analyze_with_real_data()` 메서드에 유가/달러 분석 통합
   - macro_data 포맷 업데이트 (wti_crude, dxy 추가)
   - macro_factors 출력에 유가/달러 데이터 포함

### 🎯 현재 시스템 상태

- **Agent 개수**: 8개 (Sentiment Agent 추가)
- **War Room 구성**: Risk 20% + Trader 15% + Analyst 15% + ChipWar 12% + News 10% + Macro 10% + Institutional 10% + **Sentiment 8%**
- **예상 Constitutional 통과율**: 80%+ (VaR 사전 체크)

---

## 🚀 내일 진행 권장 옵션

### 옵션 1: 실전 테스트 및 검증 (추천) ⭐

**목적**: Phase 3 개선 효과 검증 및 안정성 확인

**작업 내용**:

#### 1.1 단위 테스트 작성 (2시간)

**Sentiment Agent 테스트**:
```python
# tests/test_sentiment_agent.py
def test_fear_greed_extreme_fear():
    """Extreme Fear (< 25) 시 CONTRARIAN_BUY 신호 확인"""
    social_data = {
        "twitter_sentiment": 0.45,
        "twitter_volume": 12000,
        "reddit_sentiment": 0.30,
        "reddit_mentions": 800,
        "fear_greed_index": 18,  # EXTREME_FEAR
        "trending_rank": 25,
        "sentiment_change_24h": 0.10,
        "bullish_ratio": 0.55
    }

    result = await sentiment_agent._analyze_with_real_data("AAPL", social_data)

    assert result["action"] == "BUY"
    assert "Extreme Fear" in result["reasoning"]
    assert result["sentiment_factors"]["fear_greed"]["signal"] == "CONTRARIAN_BUY"

def test_meme_stock_detection():
    """Meme Stock 감지 테스트"""
    social_data = {
        "twitter_sentiment": 0.85,
        "twitter_volume": 125000,  # 고거래량
        "reddit_sentiment": 0.78,
        "reddit_mentions": 8500,
        "fear_greed_index": 88,  # EXTREME_GREED
        "trending_rank": 2,
        "sentiment_change_24h": 0.65,  # 급격한 변화
        "bullish_ratio": 0.92  # 과도한 낙관
    }

    result = await sentiment_agent._analyze_with_real_data("GME", social_data)

    assert result["action"] == "SELL"  # 과열 경고
    assert result["sentiment_factors"]["trending"]["is_meme_stock"] == True
```

**VaR 계산 테스트**:
```python
# tests/test_risk_agent.py
def test_var_constitutional_violation():
    """VaR < -5% 시 SELL 신호 확인 (헌법 제4조)"""
    returns = [-0.08, -0.06, -0.05, -0.03, -0.02, 0.01, 0.02, ...]  # 변동성 높음

    var_result = risk_agent._calculate_var(returns)

    assert var_result["var_1day"] < -0.05  # -5% 이하

    # 매매 신호 확인
    result = await risk_agent._analyze_with_real_data("TSLA", {...})

    assert result["action"] == "SELL"
    assert "헌법 제4조" in result["reasoning"]

def test_var_low_risk():
    """낮은 VaR 시 confidence_boost 확인"""
    returns = [0.01, -0.01, 0.02, -0.015, 0.008, ...]  # 안정적

    var_result = risk_agent._calculate_var(returns)

    assert var_result["var_1day"] > -0.02  # -2% 이상
```

**경쟁사 비교 테스트**:
```python
# tests/test_analyst_agent.py
def test_sector_leader():
    """섹터 리더 판정 시 BUY 신호 강화 확인"""
    fundamental_data = {
        "ticker": "AAPL",
        "pe_ratio": 24.2,
        "revenue_growth": 0.225,  # 22.5%
        "profit_margin": 0.283    # 28.3%
    }

    peer_comparison = analyst_agent._compare_with_peers("AAPL", fundamental_data)

    assert peer_comparison["competitive_position"] == "LEADER"
    assert peer_comparison["competitive_score"] >= 2

def test_sector_lagging():
    """섹터 열위 시 BUY 신호 약화 확인"""
    fundamental_data = {
        "ticker": "F",
        "pe_ratio": 15.5,
        "revenue_growth": 0.02,   # 2%
        "profit_margin": 0.03     # 3%
    }

    peer_comparison = analyst_agent._compare_with_peers("F", fundamental_data)

    assert peer_comparison["competitive_position"] == "LAGGING"
```

#### 1.2 Constitutional 검증 테스트 (1시간)

**VaR < -5% 시나리오**:
```python
# scripts/test_constitutional_compliance.py
async def test_constitutional_article_4():
    """헌법 제4조 위반 시나리오 테스트"""

    # 고위험 종목 (TSLA, NVDA, 변동성 높은 주식)
    high_volatility_tickers = ["TSLA", "NVDA", "GME", "AMC"]

    for ticker in high_volatility_tickers:
        # War Room 토론 실행
        debate_result = await war_room.conduct_debate(ticker)

        # Constitutional 검증
        constitutional_result = await constitutional_validator.validate(debate_result)

        # VaR < -5% 시 통과 여부 확인
        if debate_result["risk_factors"].get("var_1day", 0) < -0.05:
            if debate_result["action"] == "BUY":
                assert constitutional_result["is_constitutional"] == False
                assert "헌법 제4조" in constitutional_result["violations"]
```

#### 1.3 통합 테스트 (1시간)

**War Room 8개 Agent 투표 시뮬레이션**:
```python
# scripts/test_war_room_integration.py
async def test_8_agent_voting():
    """8개 Agent 투표 시뮬레이션"""

    ticker = "AAPL"

    # 각 Agent 투표 실행
    votes = {
        "risk": await risk_agent.vote(ticker),           # 20%
        "trader": await trader_agent.vote(ticker),       # 15%
        "analyst": await analyst_agent.vote(ticker),     # 15%
        "chipwar": await chipwar_agent.vote(ticker),     # 12%
        "news": await news_agent.vote(ticker),           # 10%
        "macro": await macro_agent.vote(ticker),         # 10%
        "institutional": await institutional_agent.vote(ticker),  # 10%
        "sentiment": await sentiment_agent.vote(ticker)   # 8%
    }

    # 가중 평균 계산
    final_decision = calculate_weighted_vote(votes)

    print(f"Final Decision: {final_decision['action']}")
    print(f"Confidence: {final_decision['confidence']:.2f}")
    print(f"Agent Votes: BUY {final_decision['buy_votes']:.0%}, SELL {final_decision['sell_votes']:.0%}")
```

---

### 옵션 2: 데이터 수집 시작 (Phase 3-2)

**목적**: 14일 데이터 수집 및 Constitutional 검증 실전 테스트

**작업 내용**:

#### 2.1 배치 파일 실행

참고: [배치파일_사용법_최종.md](../배치파일_사용법_최종.md)

**Step 1: 시스템 체크**
```
0_시스템_체크.bat 실행
```

**Step 2: DB 마이그레이션 (최초 1회)**
```
1_DB_마이그레이션.bat 실행
```

**Step 3: 5분 테스트 (선택)**
```
2_데이터수집_테스트.bat 실행
```

**Step 4: 14일 데이터 수집 시작**
```
3_데이터수집_시작.bat 실행
→ 창 닫지 말고 최소화
→ 14일 또는 100개 토론 달성 시 자동 종료
```

#### 2.2 모니터링

**실시간 모니터링**:
```
4_모니터링_대시보드.bat 실행 (별도 창)
```

**품질 리포트** (주 1-2회):
```
5_품질리포트_생성.bat 실행
```

**로그 확인** (문제 발생 시):
```
6_로그_확인.bat 실행
```

#### 2.3 목표 지표

| 지표 | 목표 |
|------|------|
| 총 토론 수 | 100개+ |
| 고유 티커 | 10개+ |
| **Constitutional 통과율** | **90%+** ⭐ |
| 평균 신뢰도 | 75%+ |
| 전체 품질 점수 | 80점+ |

---

### 옵션 3: 추가 Agent 개선 (Phase 2)

**목적**: Trader Agent 기술적 분석 + Macro Agent 거시경제 지표 강화

**작업 내용**:

#### 3.0 Macro Agent - 거시경제 지표 추가 ⭐ NEW (1시간)

**배경**:
- 현재 Macro Agent는 Fed 금리, CPI, GDP, 실업률, 수익률 곡선 분석
- **추가 필요**: 유가, 달러 인덱스 등 주요 지수 흐름 분석

**추가할 지표**:

1. **유가 (WTI Crude)** - 에너지 비용, 인플레 압력
   ```python
   def _analyze_oil_price(self, wti_price: float, wti_change_30d: float) -> Dict:
       """
       유가 분석
       - 유가 > $90: HIGH (인플레 압력 증가, 에너지 섹터 수혜)
       - 유가 < $60: LOW (소비 여력 증가, 운송 섹터 수혜)
       """
   ```

2. **달러 인덱스 (DXY)** - 통화 강도, 수출입 영향
   ```python
   def _analyze_dollar_index(self, dxy: float, dxy_change_30d: float) -> Dict:
       """
       달러 인덱스 분석
       - DXY > 105: STRONG (수출 기업 불리, 신흥국 압박)
       - DXY < 95: WEAK (수출 유리, 금/원자재 강세)
       """
   ```

**섹터별 영향 매트릭스**:

| 지표 | 상승 시 수혜 섹터 | 하락 시 수혜 섹터 |
|------|-----------------|------------------|
| **유가** | Energy (+0.10) | Airlines (+0.08), Consumer (+0.05) |
| **달러** | 내수 기업 | 수출 기업 (+0.08), 금/원자재 (+0.12) |

**매매 신호 통합**:
```python
# 유가 영향
if sector == "Energy" and oil_analysis["signal"] == "HIGH":
    confidence_boost += 0.10
    reasoning += " | 유가 고공행진 - 에너지 섹터 수혜"

# 달러 영향
if self._is_us_exporter(ticker) and dxy_analysis["signal"] == "STRONG":
    confidence_boost -= 0.08
    reasoning += " | 달러 강세 - 수출 경쟁력 약화"
```

**Expected macro_data format 업데이트**:
```python
{
    "fed_rate": 5.25,
    "fed_direction": "HIKING|CUTTING|HOLDING",
    "cpi_yoy": 3.2,
    "gdp_growth": 2.5,
    "unemployment": 3.7,
    "yield_curve": {"2y": 4.5, "10y": 4.2},

    # NEW: 추가 지표
    "wti_crude": 78.50,  # 유가 ($/barrel)
    "wti_change_30d": 8.5,  # 30일 변화율 (%)
    "dxy": 103.2,  # 달러 인덱스
    "dxy_change_30d": 2.1  # 30일 변화율 (%)
}
```

**파일**: `backend/ai/debate/macro_agent.py`

**구현 위치**:
- `_analyze_oil_price()` 메서드 추가
- `_analyze_dollar_index()` 메서드 추가
- `_analyze_with_real_data()` 업데이트 (유가/달러 통합)

---

#### 3.1 지지선/저항선 자동 탐지 (1시간)

**구현**: [251227_Agent_Improvement_Detailed_Plan.md - 2.2](251227_Agent_Improvement_Detailed_Plan.md#22-지지선저항선-자동-탐지)

**핵심 기능**:
- Pivot Point 방식 (좌우 5개 봉 확인)
- 최근 3개 지지선/저항선 추출
- 현재가와의 거리 계산

**매매 신호**:
- 지지선 2% 이내: BUY (+0.15 confidence)
- 저항선 돌파: BUY (+0.2 confidence)

#### 3.2 멀티 타임프레임 분석 (2시간)

**구현**: [251227_Agent_Improvement_Detailed_Plan.md - 2.1](251227_Agent_Improvement_Detailed_Plan.md#21-멀티-타임프레임-분석)

**핵심 기능**:
- 월봉/주봉/일봉 동시 분석
- 타임프레임 정렬도 계산 (0~1)
- 상위 타임프레임 추세 일치 시 신호 강화

**매매 신호**:
- 정렬도 > 0.8: confidence +0.2 (강한 신호)
- 정렬도 < 0.3: confidence -0.3 (혼조 신호)

#### 3.3 볼린저밴드 추가 (1시간)

**구현**: [251227_Agent_Improvement_Detailed_Plan.md - 2.3](251227_Agent_Improvement_Detailed_Plan.md#23-볼린저밴드-추가)

**핵심 기능**:
- 20일 MA + 2σ 밴드
- Percent B (현재가 위치)
- Bandwidth (변동성 지표)

**매매 신호**:
- Percent B < 0: BUY (하단 밴드 이탈)
- Percent B > 1: SELL (상단 밴드 이탈)
- Bandwidth < 0.1: HOLD (Squeeze, 변동성 돌파 대기)

---

### 옵션 4: War Room 통합 개선

**목적**: 토론 품질 및 성과 추적 강화

**작업 내용**:

#### 4.1 토론 로그 시각화 (2시간)

**구현**:
```python
# backend/monitoring/debate_visualizer.py
class DebateVisualizer:
    def generate_vote_distribution(self, debate_id: str) -> Dict:
        """에이전트별 투표 분포 시각화"""

        # 데이터 조회
        debate = await db.get_debate(debate_id)

        # 투표 분포 계산
        vote_distribution = {
            "BUY": [],
            "SELL": [],
            "HOLD": []
        }

        for agent_name, vote in debate["votes"].items():
            vote_distribution[vote["action"]].append({
                "agent": agent_name,
                "confidence": vote["confidence"],
                "weight": AGENT_WEIGHTS[agent_name]
            })

        # 시각화 데이터 생성
        return {
            "chart_data": vote_distribution,
            "final_decision": debate["final_decision"],
            "weighted_buy_pct": calculate_weighted_pct(vote_distribution["BUY"]),
            "weighted_sell_pct": calculate_weighted_pct(vote_distribution["SELL"])
        }
```

#### 4.2 Shadow Trading 성과 추적 (3시간)

**구현**:
```python
# backend/monitoring/shadow_trading.py
class ShadowTradingTracker:
    def track_debate_outcome(self, debate_id: str):
        """토론 결과를 모의 거래로 추적"""

        debate = await db.get_debate(debate_id)

        if debate["final_decision"]["action"] == "BUY":
            # 모의 매수
            shadow_position = {
                "ticker": debate["ticker"],
                "entry_price": debate["current_price"],
                "entry_time": debate["timestamp"],
                "position_size": 10000,  # $10,000 고정
                "expected_confidence": debate["final_decision"]["confidence"]
            }

            await db.save_shadow_position(shadow_position)

    async def calculate_performance(self) -> Dict:
        """모의 거래 성과 계산"""

        positions = await db.get_all_shadow_positions()

        total_pnl = 0
        wins = 0
        losses = 0

        for pos in positions:
            current_price = await market_data.get_current_price(pos["ticker"])
            pnl = (current_price - pos["entry_price"]) / pos["entry_price"]

            total_pnl += pnl

            if pnl > 0:
                wins += 1
            else:
                losses += 1

        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0

        return {
            "total_positions": len(positions),
            "win_rate": win_rate,
            "avg_pnl": total_pnl / len(positions),
            "sharpe_ratio": calculate_sharpe(positions)
        }
```

---

## 💡 권장 진행 순서

### 최우선 (내일 아침)

1. **옵션 1.1 - 단위 테스트 작성** (2시간)
   - Sentiment Agent 테스트
   - VaR 계산 테스트
   - 경쟁사 비교 테스트

2. **옵션 1.2 - Constitutional 검증 테스트** (1시간)
   - VaR < -5% 시나리오
   - 통과율 측정

### 오후

3. **옵션 2 - 데이터 수집 시작** (30분 설정 후 백그라운드)
   - `3_데이터수집_시작.bat` 실행
   - 창 최소화 후 14일간 실행

4. **옵션 3 - Trader Agent 개선** (선택, 3-4시간)
   - 지지선/저항선 탐지
   - 멀티 타임프레임 분석
   - 볼린저밴드 추가

---

## 📊 예상 결과

### 옵션 1 완료 후
- ✅ Phase 3 개선 효과 검증 완료
- ✅ Constitutional 통과율 측정 (목표: 80%+)
- ✅ 단위 테스트 커버리지 확보

### 옵션 2 완료 후 (14일 후)
- ✅ 100개+ 토론 데이터 수집
- ✅ Constitutional 검증 실전 데이터 확보
- ✅ 품질 리포트 생성

### 옵션 3 완료 후
- ✅ Trader Agent 기술적 분석 강화
- ✅ 지지선/저항선 자동 탐지
- ✅ 멀티 타임프레임 정렬도 계산

---

## 📁 참고 문서

### Phase 3 완료 보고서
- [PHASE_3_AGENT_IMPROVEMENT_FINAL_COMPLETION.md](PHASE_3_AGENT_IMPROVEMENT_FINAL_COMPLETION.md)
- [251227_work_summary.md](251227_work_summary.md)

### 개선 계획
- [251227_Agent_Improvement_Detailed_Plan.md](251227_Agent_Improvement_Detailed_Plan.md)

### 데이터 수집
- [251227_Next_Steps_Data_Accumulation.md](251227_Next_Steps_Data_Accumulation.md)
- [배치파일_사용법_최종.md](../배치파일_사용법_최종.md)
- [테스트_결과.md](../테스트_결과.md)

### 시스템 개요
- [251227_Complete_System_Overview.md](251227_Complete_System_Overview.md)
- [251227_Agent_Analysis_Report.md](251227_Agent_Analysis_Report.md)

---

**작성 완료**: 2025-12-27
**다음 리뷰**: 2025-12-28 아침
**권장 진행**: 옵션 1 (테스트) → 옵션 2 (데이터 수집) → 옵션 3 (추가 개선)
