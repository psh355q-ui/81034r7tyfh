"""
Evolution Metrics - 진화 메트릭 추적

Phase F4: 자율 진화 시스템

시스템 진화 과정을 추적하고 측정

주요 메트릭:
- 전략 성과 추이
- AI 가중치 변화
- 개선안 적용 효과
- 자율 학습 진행률

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 스키마 정의
# ═══════════════════════════════════════════════════════════════

class EvolutionStage(str, Enum):
    """진화 단계"""
    INITIAL = "initial"           # 초기 설정
    LEARNING = "learning"         # 학습 중
    ADAPTING = "adapting"         # 적응 중
    OPTIMIZING = "optimizing"     # 최적화 중
    STABLE = "stable"             # 안정화


@dataclass
class MetricSnapshot:
    """메트릭 스냅샷"""
    timestamp: datetime
    metric_name: str
    value: float
    previous_value: Optional[float] = None
    change_pct: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric_name": self.metric_name,
            "value": self.value,
            "previous_value": self.previous_value,
            "change_pct": self.change_pct,
            "metadata": self.metadata
        }


@dataclass
class EvolutionEvent:
    """진화 이벤트 (개선안 적용, 가중치 변경 등)"""
    event_id: str
    event_type: str  # weight_change, config_change, strategy_change
    description: str
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    triggered_by: str  # manual, auto, suggestion
    timestamp: datetime = field(default_factory=datetime.now)
    impact_measured: bool = False
    measured_impact: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "description": self.description,
            "before": self.before_state,
            "after": self.after_state,
            "triggered_by": self.triggered_by,
            "timestamp": self.timestamp.isoformat(),
            "impact_measured": self.impact_measured,
            "measured_impact": self.measured_impact
        }


@dataclass
class EvolutionSummary:
    """진화 요약"""
    stage: EvolutionStage
    days_active: int
    total_events: int
    improvements_applied: int
    current_performance: Dict[str, float]
    performance_trend: str  # improving, stable, declining
    next_milestone: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "days_active": self.days_active,
            "total_events": self.total_events,
            "improvements_applied": self.improvements_applied,
            "performance": self.current_performance,
            "trend": self.performance_trend,
            "next_milestone": self.next_milestone
        }


# ═══════════════════════════════════════════════════════════════
# Evolution Metrics 클래스
# ═══════════════════════════════════════════════════════════════

class EvolutionMetrics:
    """
    진화 메트릭 추적 시스템
    
    Usage:
        metrics = EvolutionMetrics()
        
        # 메트릭 기록
        metrics.record_metric("win_rate", 0.55)
        metrics.record_metric("avg_return", 0.025)
        
        # 이벤트 기록
        metrics.record_event(EvolutionEvent(...))
        
        # 요약 조회
        summary = metrics.get_summary()
    """
    
    # 목표 메트릭 (기준값)
    TARGET_METRICS = {
        "win_rate": 0.55,
        "avg_return": 0.02,
        "sharpe_ratio": 1.5,
        "max_drawdown": 0.15  # 목표: 이 이하
    }
    
    # 진화 단계 기준
    STAGE_THRESHOLDS = {
        EvolutionStage.INITIAL: 0,
        EvolutionStage.LEARNING: 7,    # 7일
        EvolutionStage.ADAPTING: 30,   # 30일
        EvolutionStage.OPTIMIZING: 90, # 90일
        EvolutionStage.STABLE: 180     # 180일
    }
    
    def __init__(self, data_dir: Optional[Path] = None):
        """초기화"""
        self.data_dir = data_dir or Path("data/evolution/metrics")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._metrics: Dict[str, List[MetricSnapshot]] = {}
        self._events: List[EvolutionEvent] = []
        self._start_date = datetime.now()
        
        # 초기 메트릭 로드
        self._load_history()
        
        logger.info("EvolutionMetrics initialized")
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MetricSnapshot:
        """메트릭 기록"""
        if metric_name not in self._metrics:
            self._metrics[metric_name] = []
        
        # 이전 값 확인
        previous = None
        change_pct = None
        if self._metrics[metric_name]:
            previous = self._metrics[metric_name][-1].value
            if previous != 0:
                change_pct = (value - previous) / abs(previous) * 100
        
        snapshot = MetricSnapshot(
            timestamp=datetime.now(),
            metric_name=metric_name,
            value=value,
            previous_value=previous,
            change_pct=change_pct,
            metadata=metadata or {}
        )
        
        self._metrics[metric_name].append(snapshot)
        logger.debug(f"Recorded {metric_name}: {value} (change: {change_pct:.1f}%)" if change_pct else f"Recorded {metric_name}: {value}")
        
        return snapshot
    
    def record_event(self, event: EvolutionEvent):
        """이벤트 기록"""
        self._events.append(event)
        logger.info(f"Evolution event: {event.event_type} - {event.description}")
    
    def record_weight_change(
        self,
        agent: str,
        old_weight: float,
        new_weight: float,
        reason: str
    ):
        """가중치 변경 기록"""
        event = EvolutionEvent(
            event_id=f"wc_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            event_type="weight_change",
            description=f"{agent} weight: {old_weight:.2f} → {new_weight:.2f}",
            before_state={"agent": agent, "weight": old_weight},
            after_state={"agent": agent, "weight": new_weight},
            triggered_by=reason
        )
        self.record_event(event)
    
    def record_config_change(
        self,
        config_key: str,
        old_value: Any,
        new_value: Any,
        reason: str
    ):
        """설정 변경 기록"""
        event = EvolutionEvent(
            event_id=f"cc_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            event_type="config_change",
            description=f"{config_key}: {old_value} → {new_value}",
            before_state={"key": config_key, "value": old_value},
            after_state={"key": config_key, "value": new_value},
            triggered_by=reason
        )
        self.record_event(event)
    
    def get_metric_history(
        self,
        metric_name: str,
        days: int = 30
    ) -> List[MetricSnapshot]:
        """메트릭 히스토리 조회"""
        if metric_name not in self._metrics:
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        return [
            s for s in self._metrics[metric_name]
            if s.timestamp >= cutoff
        ]
    
    def get_current_metrics(self) -> Dict[str, float]:
        """현재 메트릭 조회"""
        current = {}
        for name, snapshots in self._metrics.items():
            if snapshots:
                current[name] = snapshots[-1].value
        return current
    
    def get_metric_trend(self, metric_name: str, days: int = 7) -> str:
        """메트릭 추세 분석"""
        history = self.get_metric_history(metric_name, days)
        
        if len(history) < 2:
            return "insufficient_data"
        
        # 간단한 추세 분석
        first_half = history[:len(history)//2]
        second_half = history[len(history)//2:]
        
        avg_first = sum(s.value for s in first_half) / len(first_half)
        avg_second = sum(s.value for s in second_half) / len(second_half)
        
        change = (avg_second - avg_first) / abs(avg_first) if avg_first != 0 else 0
        
        if change > 0.05:
            return "improving"
        elif change < -0.05:
            return "declining"
        else:
            return "stable"
    
    def get_evolution_stage(self) -> EvolutionStage:
        """현재 진화 단계 판단"""
        days_active = (datetime.now() - self._start_date).days
        
        if days_active >= self.STAGE_THRESHOLDS[EvolutionStage.STABLE]:
            return EvolutionStage.STABLE
        elif days_active >= self.STAGE_THRESHOLDS[EvolutionStage.OPTIMIZING]:
            return EvolutionStage.OPTIMIZING
        elif days_active >= self.STAGE_THRESHOLDS[EvolutionStage.ADAPTING]:
            return EvolutionStage.ADAPTING
        elif days_active >= self.STAGE_THRESHOLDS[EvolutionStage.LEARNING]:
            return EvolutionStage.LEARNING
        else:
            return EvolutionStage.INITIAL
    
    def get_summary(self) -> EvolutionSummary:
        """진화 요약 조회"""
        stage = self.get_evolution_stage()
        days_active = (datetime.now() - self._start_date).days
        
        current_metrics = self.get_current_metrics()
        
        # 전체 추세 판단
        trends = []
        for metric in ["win_rate", "avg_return"]:
            if metric in self._metrics:
                trends.append(self.get_metric_trend(metric))
        
        if "improving" in trends:
            overall_trend = "improving"
        elif "declining" in trends:
            overall_trend = "declining"
        else:
            overall_trend = "stable"
        
        # 다음 마일스톤
        next_stage = None
        for s, threshold in self.STAGE_THRESHOLDS.items():
            if threshold > days_active:
                next_stage = s
                break
        
        next_milestone = (
            f"{next_stage.value} 단계 (D+{self.STAGE_THRESHOLDS[next_stage]})"
            if next_stage else "최종 단계 도달"
        )
        
        return EvolutionSummary(
            stage=stage,
            days_active=days_active,
            total_events=len(self._events),
            improvements_applied=sum(1 for e in self._events if e.triggered_by == "suggestion"),
            current_performance=current_metrics,
            performance_trend=overall_trend,
            next_milestone=next_milestone
        )
    
    def get_improvement_effectiveness(self) -> Dict[str, Any]:
        """개선안 효과 분석"""
        suggestion_events = [
            e for e in self._events
            if e.triggered_by == "suggestion"
        ]
        
        measured = [e for e in suggestion_events if e.impact_measured]
        
        if not measured:
            return {
                "total_improvements": len(suggestion_events),
                "measured": 0,
                "average_impact": None,
                "status": "측정 데이터 부족"
            }
        
        avg_impact = sum(e.measured_impact or 0 for e in measured) / len(measured)
        positive_count = sum(1 for e in measured if (e.measured_impact or 0) > 0)
        
        return {
            "total_improvements": len(suggestion_events),
            "measured": len(measured),
            "positive_outcomes": positive_count,
            "average_impact": avg_impact,
            "success_rate": positive_count / len(measured)
        }
    
    def _load_history(self):
        """히스토리 로드"""
        # TODO: 파일에서 로드 구현
        pass
    
    def save_state(self):
        """상태 저장"""
        state = {
            "start_date": self._start_date.isoformat(),
            "metrics": {
                name: [s.to_dict() for s in snapshots]
                for name, snapshots in self._metrics.items()
            },
            "events": [e.to_dict() for e in self._events]
        }
        
        filepath = self.data_dir / "evolution_state.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Evolution state saved: {filepath}")


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_evolution_metrics: Optional[EvolutionMetrics] = None


def get_evolution_metrics() -> EvolutionMetrics:
    """EvolutionMetrics 싱글톤 인스턴스"""
    global _evolution_metrics
    if _evolution_metrics is None:
        _evolution_metrics = EvolutionMetrics()
    return _evolution_metrics


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import random
    
    metrics = EvolutionMetrics()
    
    print("=== Evolution Metrics Test ===\n")
    
    # 메트릭 기록
    for i in range(10):
        metrics.record_metric("win_rate", 0.45 + random.uniform(0, 0.2))
        metrics.record_metric("avg_return", 0.01 + random.uniform(-0.02, 0.04))
    
    # 이벤트 기록
    metrics.record_weight_change("claude", 1.0, 0.8, "low_accuracy")
    metrics.record_config_change("STOP_LOSS", 0.1, 0.07, "suggestion")
    
    # 요약 출력
    summary = metrics.get_summary()
    print(f"Stage: {summary.stage.value}")
    print(f"Days Active: {summary.days_active}")
    print(f"Total Events: {summary.total_events}")
    print(f"Trend: {summary.performance_trend}")
    print(f"Next Milestone: {summary.next_milestone}")
    
    print(f"\nCurrent Metrics:")
    for name, value in summary.current_performance.items():
        print(f"  {name}: {value:.3f}")
