---
name: report-orchestrator-agent
description: Calculates News Interpretation Accuracy (NIA), tracks AI prediction accuracy, and generates accountability sections for reports
license: Proprietary
compatibility: Requires news_interpretations, news_market_reactions, news_decision_links tables
metadata:
  author: ai-trading-system
  version: "1.0"
  category: reporting
  agent_role: accountability_tracker
---

# Report Orchestrator Agent - AI 판단 책임 추적

## Role
AI 판단의 정확도를 측정하고, 리포트에 accountability 섹션을 생성하는 전문 Agent

## Core Capabilities

### 1. News Interpretation Accuracy (NIA) 계산

**정의**: AI가 뉴스를 해석한 대로 시장이 움직였는가?

**계산 로직**:
```
NIA = (정확한 해석 수) / (검증된 전체 해석 수) × 100

정확한 해석:
- headline_bias = "BULLISH" → 실제 가격 상승
- headline_bias = "BEARISH" → 실제 가격 하락
- headline_bias = "NEUTRAL" → 실제 가격 변동 < 1%
```

**Time Horizon별 검증**:
- `IMMEDIATE`: 10분 후 가격
- `INTRADAY`: 1일 후 가격
- `MULTI_DAY`: 3일 후 가격

### 2. Timeframe별 NIA

#### Daily NIA
- **대상**: 오늘 생성된 해석 중 이미 검증된 것
- **사용처**: Daily Report의 실시간 정확도 표시

#### Weekly NIA
- **대상**: 최근 7일 해석
- **사용처**: Weekly Report의 "AI 판단 진화 로그"
- **추가 분석**: 전주 대비 개선도

#### Annual NIA
- **대상**: 올해 전체 해석
- **사용처**: Annual Report의 "AI Accountability Report"
- **추가 분석**: 유형별 정확도 (Macro, Earnings, Geopolitics)

### 3. Report Data Aggregation
**정의**: 다양한 시스템 컴포넌트로부터 데이터를 수집하여 종합 리포트 생성

**데이터 소스**:
- **Portfolio**: `AccountPartitionManager` (Core/Income/Satellite 비중, 수익률)
- **News**: `NewsInterpretation` (War Room 분석 결과, 감성, 영향도)
- **Deep Reasoning**: `AnalysisResult` (3단계 심층 분석), `TradingSignal` (생성된 시그널)

**출력물**:
- Daily Briefing (시장/포트폴리오/이슈/전략 종합)
- Weekly/Annual Report (Accountability 포함)

### 3. 리포트 섹션 생성

#### Daily Report Enhancement
```python
{
  "accuracy_percentage": 92,
  "narrative_enhancement": "(해석 정확도: 92%)"
}
```

#### Weekly Accountability Section
```python
{
  "nia_score": 75,
  "improvement": "+5%p",
  "best_judgment": {
    "ticker": "NVDA",
    "headline": "실적 발표",
    "prediction": "상승",
    "actual": "+8%",
    "accuracy": 100
  },
  "worst_judgment": {
    "ticker": "TSLA",
    "headline": "Fed 발언",
    "prediction": "하락",
    "actual": "+2%",
    "accuracy": 0
  },
  "lesson_learned": "숏커버 가능성을 고려 못함"
}
```

#### Annual Accountability Report
```python
{
  "nia_overall": 68,
  "by_type": {
    "EARNINGS": 85,
    "MACRO": 72,
    "GEOPOLITICS": 45
  },
  "top_3_failures": [
    {
      "description": "Ukraine 전쟁 초기 → 과도한 비관",
      "lesson": "지정학적 리스크는 priced-in 빠름",
      "fix": "macro_context에 geopolitical_risk_decay_rate 추가"
    },
    ...
  ],
  "system_improvements": [
    {
      "date": "2025-03-15",
      "improvement": "Fed tone tracker weight 증가",
      "before_nia": 68,
      "after_nia": 72
    },
    ...
  ]
}
```

## Core Functions

### `calculate_news_interpretation_accuracy(timeframe="daily")`
**목적**: NIA 계산

**Args**:
- `timeframe`: "daily" | "weekly" | "annual"

**Returns**:
```python
{
  "overall_accuracy": 0.75,
  "by_impact": {
    "HIGH": 0.85,
    "MEDIUM": 0.72,
    "LOW": 0.68
  },
  "by_type": {
    "EARNINGS": 0.85,
    "MACRO": 0.72,
    "GEOPOLITICS": 0.45
  },
  "best_call": {
    "interpretation_id": 123,
    "ticker": "NVDA",
    "headline": "실적 발표",
    "bias": "BULLISH",
    "actual_change": 8.5,
    "correct": true
  },
  "worst_call": {...}
}
```

### `generate_weekly_accountability_section()`
**목적**: Weekly Report용 AI 판단 진화 로그 생성

**Returns**:
```python
{
  "nia_score": 75,
  "improvement": "+5%p",
  "best_judgment": "...",
  "worst_judgment": "...",
  "lesson_learned": "..."
}
```

### `generate_annual_accountability_report()`
**목적**: Annual Report용 전체 accountability 리포트 생성

**Returns**:
```python
{
  "nia_overall": 68,
  "by_type": {...},
  "top_3_failures": [...],
  "system_improvements": [...]
}
```

### `enhance_daily_report_with_accountability(report_data)`
**목적**: Daily Report에 정확도 삽입

**Args**:
- `report_data`: 기존 리포트 데이터

**Returns**:
- 정확도가 강화된 리포트 데이터

## Integration Points

### 1. Price Tracking Scheduler
**역할**: 1h/1d/3d 후 실제 가격 측정

```python
# backend/automation/price_tracking_verifier.py
class PriceTrackingVerifier:
    async def verify_interpretations(self, time_horizon="1h"):
        # 1. 검증 대기 중인 interpretations 조회
        pending = reaction_repo.get_pending_verifications(time_horizon)

        # 2. 현재 가격 조회 (KIS API)
        for reaction in pending:
            current_price = await kis_api.get_current_price(reaction.ticker)

            # 3. 가격 변화율 계산
            price_change = (current_price - reaction.price_at_news) / reaction.price_at_news

            # 4. 해석 정확도 판정
            interpretation = reaction.interpretation
            correct = self._check_correctness(interpretation.headline_bias, price_change)

            # 5. DB 업데이트
            reaction_repo.update(reaction, {
                "price_1h_after": current_price,
                "actual_price_change_1h": price_change,
                "interpretation_correct": correct,
                "verified_at": datetime.now()
            })
```

### 2. Report Generators
```python
# Daily Report
from backend.ai.skills.reporting.report_orchestrator import ReportOrchestrator

orchestrator = ReportOrchestrator(db)
enhanced_data = orchestrator.enhance_daily_report_with_accountability(report_data)

# Weekly Report
weekly_section = orchestrator.generate_weekly_accountability_section()

# Annual Report
annual_report = orchestrator.generate_annual_accountability_report()
```

## Decision Framework

### Interpretation Correctness 판정

```python
def _check_correctness(headline_bias: str, actual_price_change: float) -> bool:
    """
    해석이 맞았는지 판정

    Args:
        headline_bias: "BULLISH" | "BEARISH" | "NEUTRAL"
        actual_price_change: 실제 가격 변화율 (%)

    Returns:
        bool: 정확 여부
    """
    if headline_bias == "BULLISH":
        return actual_price_change > 1.0  # 1% 이상 상승
    elif headline_bias == "BEARISH":
        return actual_price_change < -1.0  # 1% 이상 하락
    else:  # NEUTRAL
        return -1.0 <= actual_price_change <= 1.0  # ±1% 이내
```

### Impact vs Magnitude 정확도

```python
def _calculate_magnitude_accuracy(expected_impact: str, actual_change: float) -> float:
    """
    예상 크기와 실제 크기의 정확도

    Args:
        expected_impact: "HIGH" (5%+) | "MEDIUM" (2-5%) | "LOW" (<2%)
        actual_change: 실제 가격 변화율 (%)

    Returns:
        float: 0.0 ~ 1.0 (정확도)
    """
    actual_abs = abs(actual_change)

    if expected_impact == "HIGH":
        if actual_abs >= 5:
            return 1.0  # Perfect
        elif actual_abs >= 2:
            return 0.5  # Partial
        else:
            return 0.0  # Wrong
    elif expected_impact == "MEDIUM":
        if 2 <= actual_abs < 5:
            return 1.0
        elif actual_abs >= 1:
            return 0.7
        else:
            return 0.3
    else:  # LOW
        if actual_abs < 2:
            return 1.0
        elif actual_abs < 5:
            return 0.5
        else:
            return 0.0
```

## Performance Metrics

### 목표 NIA
- **Overall**: 70% 이상
- **HIGH Impact**: 80% 이상
- **EARNINGS**: 85% 이상
- **MACRO**: 70% 이상
- **GEOPOLITICS**: 60% 이상 (가장 어려움)

### Monitoring
- Daily NIA 추적 → Telegram 알림 (< 60% 시)
- Weekly NIA 전주 대비 비교
- Monthly 트렌드 분석

## Output Examples

### Example 1: Daily Report Enhancement

**Input**:
```python
report_data = {
  "page1": {
    "narratives": [
      {
        "text": "Fed 매파 발언으로 시장 하락 예상",
        "interpretation_id": 123
      }
    ]
  }
}
```

**Output**:
```python
{
  "page1": {
    "narratives": [
      {
        "text": "Fed 매파 발언으로 시장 하락 예상 (해석 정확도: 92%)",
        "interpretation_id": 123
      }
    ]
  }
}
```

### Example 2: Weekly Accountability Section

**Output**:
```python
{
  "nia_score": 75,
  "improvement": "+5%p",
  "best_judgment": "NVDA 실적 발표 → 상승 예측 → 실제 +8% (정확도: 100%)",
  "worst_judgment": "Fed 발언 → 하락 예측 → 실제 +2% (정확도: 0%)",
  "lesson_learned": "숏커버 가능성을 고려 못함. 다음 주부터 단기 포지션 청산 패턴 모니터링 강화"
}
```

### Example 3: Annual Accountability Report

**Output**:
```python
{
  "nia_overall": 68,
  "by_type": {
    "EARNINGS": 85,
    "MACRO": 72,
    "GEOPOLITICS": 45
  },
  "top_3_failures": [
    {
      "description": "Ukraine 전쟁 초기 → 과도한 비관 (예상: -10%, 실제: -2%)",
      "lesson": "지정학적 리스크는 priced-in 빠름 (평균 3일 내)",
      "fix": "macro_context에 geopolitical_risk_decay_rate 추가 (3일 후 50% 감소)"
    },
    {
      "description": "Fed pivot 예측 → 6개월 일찍 판단",
      "lesson": "중앙은행 발언은 literal하게 해석 (wishful thinking 금지)",
      "fix": "Fed tone tracker weight 20% → 35% 증가"
    },
    {
      "description": "AI 칩 규제 → 과소평가 (예상: -2%, 실제: -8%)",
      "lesson": "정부 규제는 산업 게임 체인저 (단순 단기 이슈 아님)",
      "fix": "regulatory_risk agent 신설 (2026 Q2)"
    }
  ],
  "system_improvements": [
    {
      "date": "2025-03-15",
      "improvement": "Fed tone tracker weight 증가",
      "before_nia": 68,
      "after_nia": 72,
      "impact": "+4%p"
    },
    {
      "date": "2025-06-01",
      "improvement": "Geopolitical risk decay rate 모델 추가",
      "before_nia": 42,
      "after_nia": 58,
      "impact": "+16%p (Geopolitics 카테고리)"
    }
  ]
}
```

## Guidelines

### Do's ✅
- 검증된 해석만 NIA 계산에 포함 (verified_at NOT NULL)
- Time horizon에 맞는 가격 사용 (IMMEDIATE → 1h, INTRADAY → 1d, MULTI_DAY → 3d)
- 유형별/Impact별 세분화된 분석
- 틀린 판단에서 구체적인 교훈 도출
- 개선 사항의 효과 추적 (before/after NIA)

### Don'ts ❌
- 아직 검증되지 않은 해석을 NIA 계산에 포함 금지
- 단순 정확도만 보고 근본 원인 무시 금지
- 일회성 실수를 시스템 문제로 과대평가 금지
- 개선 조치 없이 실패만 나열 금지

## Version History

- **v1.0** (2025-12-29): Initial release with NIA calculation and accountability reporting

## Related Files

- `backend/ai/skills/reporting/report-orchestrator-agent/report_orchestrator.py`
- `backend/automation/price_tracking_verifier.py`
- `backend/services/complete_5page_report_generator.py`
- `backend/database/repository.py` (NewsInterpretationRepository, NewsMarketReactionRepository)
