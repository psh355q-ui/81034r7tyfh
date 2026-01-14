# Option 3 검증 보고서 - 추가 최적화

**작성일**: 2025-12-28
**Phase**: Option 3 Verification
**목표**: Agent 가중치 동적 조정, 자기학습 스케줄러, 성과 추적 대시보드 검증

---

## 목차
1. [개요](#개요)
2. [검증 결과](#검증-결과)
3. [구현 상태](#구현-상태)
4. [활성화 필요 항목](#활성화-필요-항목)
5. [다음 단계](#다음-단계)

---

## 개요

### Option 3 목표
- ✅ Agent 가중치 동적 조정 시스템 활성화
- ✅ 자기학습 스케줄러 설정 (매일 00:00 UTC)
- ✅ 성과 추적 대시보드 구축

---

## 검증 결과

### 1. Agent 가중치 동적 조정 시스템 ✅

#### 구현 파일
- [backend/ai/learning/agent_weight_manager.py](../backend/ai/learning/agent_weight_manager.py)

#### 핵심 로직
```python
class AgentWeightManager:
    """
    Manages agent voting weights based on performance metrics

    Weight Calculation Logic:
        - Accuracy >= 70%: weight = 1.2 (strong performer)
        - Accuracy >= 60%: weight = 1.0 (good performer)
        - Accuracy >= 50%: weight = 0.8 (weak performer)
        - Accuracy < 50%:  weight = 0.5 (poor performer)
    """

    ACCURACY_THRESHOLDS = {
        "strong": 0.70,    # >= 70%
        "good": 0.60,      # >= 60%
        "weak": 0.50,      # >= 50%
    }

    WEIGHT_VALUES = {
        "strong": 1.2,
        "good": 1.0,
        "weak": 0.8,
        "poor": 0.5,
    }
```

#### 주요 기능

**1) 가중치 계산** (Lines 60-160)
- 30일 lookback 기반 성과 평가
- 최소 20개 샘플 필요
- Accuracy 기반 base weight 계산
- Confidence gap 조정 (과신/과소신뢰 보정)

**2) Confidence Gap Adjustment** (Lines 181-215)
```python
def _apply_confidence_adjustment(self, base_weight, confidence_gap):
    """
    Apply confidence gap adjustment to base weight

    - Overconfident (confidence > accuracy by 15%+): Penalty (max -0.2)
    - Underconfident (accuracy > confidence by 15%+): Bonus (max +0.1)
    """
    # Overconfident: gap > 0.15
    if confidence_gap > 0.15:
        penalty = min(0.2, confidence_gap * 0.5)
        return base_weight * (1 - penalty)

    # Underconfident: gap < -0.15
    elif confidence_gap < -0.15:
        bonus = min(0.1, abs(confidence_gap) * 0.3)
        return base_weight * (1 + bonus)

    # Calibrated
    return base_weight
```

**3) Low Performer Detection** (Lines 226-278)
- Accuracy < 50% 감지
- 심각도 분류 (critical: <45%, warning: 45-50%)
- 최소 20개 샘플 필요

**4) Overconfident Agent Detection** (Lines 280-335)
- Confidence gap > 20% 감지
- 심각도 분류 (high: >30%, medium: 20-30%)

#### API 엔드포인트
- [backend/api/weight_adjustment_router.py](../backend/api/weight_adjustment_router.py)
  - `POST /api/weights/adjust` - 가중치 조정 실행
  - `GET /api/weights/current` - 현재 가중치 조회
  - `GET /api/weights/low-performers` - 저성과 Agent 조회
  - `GET /api/weights/overconfident` - 과신 Agent 조회

#### 테스트 방법
```bash
# 가중치 계산 테스트
cd d:\code\ai-trading-system\backend
python -m ai.learning.agent_weight_manager
```

**현재 상태**: ✅ **완전 구현됨** - API 통해 언제든지 실행 가능

---

### 2. 자기학습 스케줄러 설정 ✅

#### 구현 파일
- [backend/ai/learning/daily_learning_scheduler.py](../backend/ai/learning/daily_learning_scheduler.py)
- [backend/ai/learning/learning_orchestrator.py](../backend/ai/learning/learning_orchestrator.py)

#### 핵심 로직

**DailyLearningScheduler** (Lines 27-144)
```python
class DailyLearningScheduler:
    """
    Automated scheduler for daily AI learning cycles.

    Runs learning at a specific time each day (e.g., midnight).
    """

    def __init__(
        self,
        run_time: time = time(0, 0),  # Default: midnight
        retry_on_failure: bool = True,
        max_retries: int = 3
    ):
        self.run_time = run_time
        self.retry_on_failure = retry_on_failure
        self.max_retries = max_retries
        self.orchestrator = LearningOrchestrator()
```

**주요 기능**:
1. **자동 스케줄링** (Lines 66-103)
   - 매일 지정된 시간에 실행 (기본: 00:00)
   - 다음 실행까지 자동 대기
   - 무한 루프로 계속 실행

2. **재시도 로직** (Lines 104-127)
   - 최대 3회 재시도
   - Exponential backoff (5분, 10분, 15분)
   - 실패 시 알림 (TODO: 관리자 알림)

3. **학습 실행** (Lines 134-143)
   ```python
   async def run_once(self):
       """Run learning cycle once (for testing)"""
       return await self.orchestrator.run_daily_learning_cycle()
   ```

**LearningOrchestrator** - 6개 Agent 학습 조정
- NewsAgentLearning
- TraderAgentLearning
- RiskAgentLearning
- MacroAgentLearning
- InstitutionalAgentLearning
- AnalystAgentLearning

#### 현재 상태: ⚠️ **구현 완료, 활성화 필요**

**이유**: `backend/main.py`에 아직 통합되지 않음

**활성화 방법**:
```python
# backend/main.py의 @app.on_event("startup") 에 추가 필요
from backend.ai.learning.daily_learning_scheduler import DailyLearningScheduler
from datetime import time

# Startup event에 추가
@app.on_event("startup")
async def startup_event():
    # ... 기존 코드 ...

    # 🆕 Daily Learning Scheduler 시작
    try:
        scheduler = DailyLearningScheduler(run_time=time(0, 0))  # Midnight UTC
        asyncio.create_task(scheduler.start())
        logger.info("Daily Learning Scheduler started (00:00 UTC)")
    except Exception as e:
        logger.warning(f"Failed to start Daily Learning Scheduler: {e}")
```

---

### 3. 성과 추적 대시보드 ✅

#### 구현 파일
- [backend/api/performance_router.py](../backend/api/performance_router.py) - 성과 API
- [backend/monitoring/ai_trading_metrics.py](../backend/monitoring/ai_trading_metrics.py) - Prometheus 메트릭

#### API 엔드포인트

**Performance Router** (`/api/performance/`)
1. `GET /summary` - 전체 성과 요약
   - Total predictions
   - Accuracy
   - Average return
   - Best action

2. `GET /by-action` - 액션별 성과
   - BUY/SELL/HOLD/REDUCE/INCREASE/DCA 별 accuracy
   - 각 액션의 평균 수익률

3. `GET /history` - 일별 성과 추이
   - 날짜별 accuracy
   - 날짜별 평균 수익률

4. `GET /top-sessions` - 최고/최저 성과 세션
   - Best performing sessions
   - Worst performing sessions

5. `GET /agents` - Agent별 성과
   - 각 Agent의 accuracy
   - 평균 수익률
   - 투표 수

6. `GET /agents/by-action` - Agent × Action 성과
   - Risk Agent의 BUY 성과
   - Trader Agent의 SELL 성과 등

#### Prometheus 메트릭

**AI Trading Metrics** ([backend/monitoring/ai_trading_metrics.py](../backend/monitoring/ai_trading_metrics.py))

```python
# Signal Generation Metrics
signals_generated = Counter('ai_trading_signals_generated_total')
signals_by_type = Counter('ai_trading_signals_by_type', ['type'])
signals_by_ticker = Counter('ai_trading_signals_by_ticker', ['ticker', 'action'])
signals_high_confidence = Counter('ai_trading_signals_high_confidence_total')

# Performance Metrics
analysis_duration = Histogram('ai_trading_analysis_duration_seconds')
crawl_cycle_duration = Histogram('ai_trading_crawl_cycle_duration_seconds')

# API Cost Metrics
gemini_api_calls = Counter('ai_trading_gemini_api_calls_total', ['model'])
api_cost_usd = Gauge('ai_trading_api_cost_usd_total')
daily_api_cost = Gauge('ai_trading_api_cost_daily_usd')
```

#### 대시보드 접근

**API로 접근**:
```bash
# 전체 성과 요약
curl http://localhost:8000/api/performance/summary

# Agent별 성과
curl http://localhost:8000/api/performance/agents

# 액션별 성과
curl http://localhost:8000/api/performance/by-action
```

**Prometheus/Grafana로 접근**:
- Prometheus 메트릭 엔드포인트: `http://localhost:8000/metrics`
- Grafana 대시보드에서 시각화 가능

**현재 상태**: ✅ **완전 구현됨** - API로 즉시 사용 가능

---

## 구현 상태

| 항목 | 상태 | 파일 | 비고 |
|------|------|------|------|
| Agent 가중치 동적 조정 | ✅ 완료 | agent_weight_manager.py | API 통해 실행 가능 |
| Low Performer 감지 | ✅ 완료 | agent_weight_manager.py | `/api/weights/low-performers` |
| Overconfident 감지 | ✅ 완료 | agent_weight_manager.py | `/api/weights/overconfident` |
| Confidence Gap 조정 | ✅ 완료 | agent_weight_manager.py | 자동 보정 로직 |
| 자기학습 Orchestrator | ✅ 완료 | learning_orchestrator.py | 6개 Agent 학습 조정 |
| Daily Learning Scheduler | ⚠️ 활성화 필요 | daily_learning_scheduler.py | main.py 통합 필요 |
| Performance API | ✅ 완료 | performance_router.py | 6개 엔드포인트 |
| Prometheus 메트릭 | ✅ 완료 | ai_trading_metrics.py | 메트릭 수집 중 |
| Agent별 성과 추적 | ✅ 완료 | performance_router.py | `/api/performance/agents` |

---

## 활성화 필요 항목

### 1. Daily Learning Scheduler 활성화 ⚠️

**현재**: 코드는 완성, 하지만 `main.py`에서 시작 안 됨

**필요 작업**: `backend/main.py` 수정

**수정 내용**:
```python
# backend/main.py

from backend.ai.learning.daily_learning_scheduler import DailyLearningScheduler
from datetime import time
import asyncio

@app.on_event("startup")
async def startup_event():
    # ... 기존 startup 코드 ...

    # 🆕 Daily Learning Scheduler 시작
    try:
        scheduler = DailyLearningScheduler(run_time=time(0, 0))  # Midnight UTC
        asyncio.create_task(scheduler.start())
        logger.info("✅ Daily Learning Scheduler started (00:00 UTC)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start Daily Learning Scheduler: {e}")
```

**테스트 방법**:
```bash
# 단일 학습 사이클 테스트
cd d:\code\ai-trading-system\backend
python -m ai.learning.daily_learning_scheduler
```

---

### 2. Agent Weight 자동 조정 활성화 (선택)

**현재**: API로 수동 실행 가능

**자동화 옵션**:
1. **매일 자동 실행** (Learning cycle 후)
   ```python
   # learning_orchestrator.py의 run_daily_learning_cycle()에 추가
   async def run_daily_learning_cycle(self):
       # ... 학습 실행 ...

       # 🆕 학습 완료 후 가중치 자동 조정
       from backend.ai.learning.agent_weight_manager import AgentWeightManager
       weight_manager = AgentWeightManager(db)
       weights_info = weight_manager.calculate_agent_weights(lookback_days=30)
       logger.info(f"✅ Agent weights updated: {weights_info}")
   ```

2. **API 통해 수동 실행** (현재 방식)
   ```bash
   curl -X POST http://localhost:8000/api/weights/adjust
   ```

---

## 다음 단계

### Option 3 완료를 위한 작업

#### 1. Daily Learning Scheduler 활성화
```bash
# 1) main.py 수정
# 2) 서버 재시작
# 3) 로그 확인
```

**예상 소요**: 5분

#### 2. 첫 학습 사이클 실행 (테스트)
```bash
cd d:\code\ai-trading-system\backend
python -m ai.learning.daily_learning_scheduler
```

**예상 소요**: 2-3분

#### 3. 성과 대시보드 확인
```bash
# 전체 성과
curl http://localhost:8000/api/performance/summary

# Agent별 성과
curl http://localhost:8000/api/performance/agents
```

**예상 소요**: 1분

---

### Option 1으로 이동 (14일 데이터 수집)

Option 3 활성화 완료 후:

1. **14일 데이터 수집 스크립트 작성**
   - 3개 티커 (AAPL, NVDA, MSFT)
   - 1시간 간격
   - 14일 연속

2. **백그라운드 실행**
   - `nohup` 또는 systemd service
   - 로그 파일 저장

3. **데이터 검증**
   - 매일 수집 현황 확인
   - 오류 발생 시 알림

---

## 결론

### Option 3 검증 결과 ✅

| 항목 | 상태 |
|------|------|
| Agent 가중치 동적 조정 시스템 | ✅ 완전 구현 (API 즉시 사용 가능) |
| 자기학습 스케줄러 | ⚠️ 구현 완료, main.py 통합 필요 |
| 성과 추적 대시보드 | ✅ 완전 구현 (6개 API 엔드포인트) |

### 남은 작업

1. ⚠️ **Daily Learning Scheduler 활성화** (5분 소요)
   - `backend/main.py`에 스케줄러 시작 코드 추가
   - 서버 재시작

2. ✅ **테스트 실행**
   - 단일 학습 사이클 테스트
   - 성과 API 확인

3. ✅ **Option 1으로 이동**
   - 14일 데이터 수집 시작

---

**다음 문서**: [14일 데이터 수집 계획](./251228_14Day_Data_Collection_Plan.md) (다음 작성 예정)
