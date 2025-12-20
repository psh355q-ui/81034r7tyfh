"""
Skill Layer Metrics Collector

실시간 비용 추적, 성능 모니터링, Prometheus 메트릭 수집

Features:
- Skill별 API 호출 비용 추적
- Token 사용량 및 절감율 모니터링
- 라우팅 성능 메트릭
- Prometheus 메트릭 export

Author: AI Trading System
Date: 2025-12-06
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import asyncio
import logging

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST
)

logger = logging.getLogger(__name__)


# ============================================================================
# Prometheus Metrics
# ============================================================================

# Skill 사용 카운터
skill_invocations = Counter(
    'skill_invocations_total',
    'Total number of skill invocations',
    ['skill_name', 'category', 'intent']
)

# API 비용 카운터
api_costs = Counter(
    'api_costs_usd_total',
    'Total API costs in USD',
    ['provider', 'model', 'skill_name']
)

# Token 사용량
tokens_used = Counter(
    'tokens_used_total',
    'Total tokens used',
    ['provider', 'model', 'token_type']  # token_type: input, output, total
)

# Token 절감율
tokens_saved_percentage = Gauge(
    'tokens_saved_percentage',
    'Percentage of tokens saved by optimization',
    ['intent']
)

# 라우팅 지연시간
routing_latency = Histogram(
    'routing_latency_seconds',
    'Routing decision latency',
    ['intent'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# 신호 생성 지연시간
signal_generation_latency = Histogram(
    'signal_generation_latency_seconds',
    'Signal generation latency',
    ['intent', 'ticker'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# 활성 Skill 수
active_skills = Gauge(
    'active_skills_total',
    'Number of active skills'
)

# 도구 로딩 시간
tool_loading_time = Histogram(
    'tool_loading_time_seconds',
    'Time to load tools dynamically',
    ['tool_group'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# 에러 카운터
skill_errors = Counter(
    'skill_errors_total',
    'Total number of skill execution errors',
    ['skill_name', 'error_type']
)

# 캐시 히트/미스
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']  # routing, tool_definitions, embeddings
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)


# ============================================================================
# Cost Tracking Data Classes
# ============================================================================

@dataclass
class SkillInvocation:
    """Skill 호출 기록"""
    timestamp: datetime
    skill_name: str
    category: str
    intent: str
    tool_name: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class RoutingMetrics:
    """라우팅 메트릭"""
    timestamp: datetime
    user_input: str
    intent: str
    intent_confidence: float
    selected_tool_groups: List[str]
    tools_count: int
    baseline_tools: int
    tokens_saved_pct: float
    provider: str
    model: str
    routing_time_ms: float


@dataclass
class CostSummary:
    """비용 요약"""
    period_start: datetime
    period_end: datetime
    total_invocations: int
    total_cost_usd: float
    total_tokens: int
    cost_by_provider: Dict[str, float]
    cost_by_skill: Dict[str, float]
    avg_tokens_saved_pct: float
    most_used_skills: List[tuple]  # [(skill_name, count), ...]
    most_expensive_skills: List[tuple]  # [(skill_name, cost), ...]


# ============================================================================
# Metrics Collector
# ============================================================================

class SkillMetricsCollector:
    """Skill Layer 메트릭 수집 및 추적"""

    def __init__(self):
        self.invocations: List[SkillInvocation] = []
        self.routing_history: List[RoutingMetrics] = []
        self._lock = asyncio.Lock()

        # 실시간 집계
        self.total_cost = 0.0
        self.total_invocations = 0
        self.cost_by_provider = defaultdict(float)
        self.cost_by_skill = defaultdict(float)
        self.invocations_by_skill = defaultdict(int)

    async def record_skill_invocation(
        self,
        skill_name: str,
        category: str,
        intent: str,
        tool_name: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_ms: float,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Skill 호출 기록"""
        async with self._lock:
            invocation = SkillInvocation(
                timestamp=datetime.now(),
                skill_name=skill_name,
                category=category,
                intent=intent,
                tool_name=tool_name,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                success=success,
                error=error
            )

            self.invocations.append(invocation)

            # 실시간 집계 업데이트
            self.total_cost += cost_usd
            self.total_invocations += 1
            self.cost_by_provider[provider] += cost_usd
            self.cost_by_skill[skill_name] += cost_usd
            self.invocations_by_skill[skill_name] += 1

            # Prometheus 메트릭 업데이트
            skill_invocations.labels(
                skill_name=skill_name,
                category=category,
                intent=intent
            ).inc()

            api_costs.labels(
                provider=provider,
                model=model,
                skill_name=skill_name
            ).inc(cost_usd)

            tokens_used.labels(
                provider=provider,
                model=model,
                token_type='input'
            ).inc(input_tokens)

            tokens_used.labels(
                provider=provider,
                model=model,
                token_type='output'
            ).inc(output_tokens)

            tokens_used.labels(
                provider=provider,
                model=model,
                token_type='total'
            ).inc(input_tokens + output_tokens)

            if not success and error:
                error_type = error.split(':')[0] if ':' in error else 'Unknown'
                skill_errors.labels(
                    skill_name=skill_name,
                    error_type=error_type
                ).inc()

        logger.info(
            f"Recorded skill invocation: {skill_name}.{tool_name} "
            f"[{provider}/{model}] ${cost_usd:.4f} ({latency_ms:.0f}ms)"
        )

    async def record_routing_metrics(
        self,
        user_input: str,
        intent: str,
        intent_confidence: float,
        selected_tool_groups: List[str],
        tools_count: int,
        baseline_tools: int,
        provider: str,
        model: str,
        routing_time_ms: float
    ):
        """라우팅 메트릭 기록"""
        async with self._lock:
            tokens_saved_pct = ((baseline_tools - tools_count) / baseline_tools) * 100

            metrics = RoutingMetrics(
                timestamp=datetime.now(),
                user_input=user_input[:100],  # 처음 100자만
                intent=intent,
                intent_confidence=intent_confidence,
                selected_tool_groups=selected_tool_groups,
                tools_count=tools_count,
                baseline_tools=baseline_tools,
                tokens_saved_pct=tokens_saved_pct,
                provider=provider,
                model=model,
                routing_time_ms=routing_time_ms
            )

            self.routing_history.append(metrics)

            # Prometheus 메트릭 업데이트
            tokens_saved_percentage.labels(intent=intent).set(tokens_saved_pct)
            routing_latency.labels(intent=intent).observe(routing_time_ms / 1000)

        logger.info(
            f"Routing metrics: intent={intent} ({intent_confidence:.2f}), "
            f"tools={tools_count} (saved {tokens_saved_pct:.1f}%), "
            f"time={routing_time_ms:.0f}ms"
        )

    async def record_signal_generation(
        self,
        intent: str,
        ticker: str,
        latency_seconds: float
    ):
        """신호 생성 지연시간 기록"""
        signal_generation_latency.labels(
            intent=intent,
            ticker=ticker
        ).observe(latency_seconds)

    def record_cache_hit(self, cache_type: str):
        """캐시 히트 기록"""
        cache_hits.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str):
        """캐시 미스 기록"""
        cache_misses.labels(cache_type=cache_type).inc()

    async def get_cost_summary(
        self,
        period_hours: int = 24
    ) -> CostSummary:
        """기간별 비용 요약"""
        async with self._lock:
            now = datetime.now()
            period_start = now - timedelta(hours=period_hours)

            # 기간 내 invocation 필터링
            period_invocations = [
                inv for inv in self.invocations
                if inv.timestamp >= period_start
            ]

            if not period_invocations:
                return CostSummary(
                    period_start=period_start,
                    period_end=now,
                    total_invocations=0,
                    total_cost_usd=0.0,
                    total_tokens=0,
                    cost_by_provider={},
                    cost_by_skill={},
                    avg_tokens_saved_pct=0.0,
                    most_used_skills=[],
                    most_expensive_skills=[]
                )

            # 집계
            total_cost = sum(inv.cost_usd for inv in period_invocations)
            total_tokens = sum(
                inv.input_tokens + inv.output_tokens
                for inv in period_invocations
            )

            cost_by_provider = defaultdict(float)
            cost_by_skill = defaultdict(float)
            invocations_by_skill = defaultdict(int)

            for inv in period_invocations:
                cost_by_provider[inv.provider] += inv.cost_usd
                cost_by_skill[inv.skill_name] += inv.cost_usd
                invocations_by_skill[inv.skill_name] += 1

            # 기간 내 routing 메트릭
            period_routing = [
                r for r in self.routing_history
                if r.timestamp >= period_start
            ]
            avg_tokens_saved_pct = (
                sum(r.tokens_saved_pct for r in period_routing) / len(period_routing)
                if period_routing else 0.0
            )

            # 상위 항목
            most_used_skills = sorted(
                invocations_by_skill.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            most_expensive_skills = sorted(
                cost_by_skill.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            return CostSummary(
                period_start=period_start,
                period_end=now,
                total_invocations=len(period_invocations),
                total_cost_usd=total_cost,
                total_tokens=total_tokens,
                cost_by_provider=dict(cost_by_provider),
                cost_by_skill=dict(cost_by_skill),
                avg_tokens_saved_pct=avg_tokens_saved_pct,
                most_used_skills=most_used_skills,
                most_expensive_skills=most_expensive_skills
            )

    async def get_real_time_stats(self) -> Dict[str, Any]:
        """실시간 통계"""
        async with self._lock:
            recent_invocations = [
                inv for inv in self.invocations
                if inv.timestamp >= datetime.now() - timedelta(minutes=5)
            ]

            recent_routing = [
                r for r in self.routing_history
                if r.timestamp >= datetime.now() - timedelta(minutes=5)
            ]

            return {
                "last_5_minutes": {
                    "invocations": len(recent_invocations),
                    "cost_usd": sum(inv.cost_usd for inv in recent_invocations),
                    "avg_latency_ms": (
                        sum(inv.latency_ms for inv in recent_invocations) / len(recent_invocations)
                        if recent_invocations else 0
                    ),
                    "error_rate": (
                        sum(1 for inv in recent_invocations if not inv.success) / len(recent_invocations)
                        if recent_invocations else 0
                    ),
                    "avg_tokens_saved_pct": (
                        sum(r.tokens_saved_pct for r in recent_routing) / len(recent_routing)
                        if recent_routing else 0
                    )
                },
                "total": {
                    "invocations": self.total_invocations,
                    "cost_usd": self.total_cost,
                    "cost_by_provider": dict(self.cost_by_provider),
                    "top_skills": sorted(
                        self.invocations_by_skill.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                }
            }

    def export_prometheus_metrics(self) -> bytes:
        """Prometheus 메트릭 export"""
        return generate_latest()


# ============================================================================
# Global Singleton
# ============================================================================

_metrics_collector: Optional[SkillMetricsCollector] = None


def get_metrics_collector() -> SkillMetricsCollector:
    """메트릭 수집기 싱글톤 인스턴스"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = SkillMetricsCollector()
    return _metrics_collector
