"""
Monitoring Module - Phase 7

Production monitoring and alerting system.

Components:
- MetricsCollector: Prometheus metrics collection
- AlertManager: Multi-channel alerting
- HealthMonitor: System health checking

Author: AI Trading System Team
Date: 2025-11-14
"""

from .metrics_collector import MetricsCollector, PROMETHEUS_AVAILABLE, get_metrics_collector
from .alert_manager import AlertManager, Alert, AlertLevel, AlertCategory
from .health_monitor import (
    HealthMonitor,
    HealthStatus,
    ComponentHealth,
    SystemHealth,
    check_redis_health,
    check_database_health,
    check_disk_space,
    check_memory_usage,
    check_cpu_usage,
)

# Skill Layer Metrics (Phase D - Production)
try:
    from .skill_metrics_collector import (
        SkillMetricsCollector,
        get_metrics_collector as get_skill_metrics_collector,
        SkillInvocation,
        RoutingMetrics,
        CostSummary
    )
    SKILL_METRICS_AVAILABLE = True
except ImportError:
    SKILL_METRICS_AVAILABLE = False
    SkillMetricsCollector = None
    get_skill_metrics_collector = None
    SkillInvocation = None
    RoutingMetrics = None
    CostSummary = None

__all__ = [
    # Metrics
    "MetricsCollector",
    "PROMETHEUS_AVAILABLE",
    "get_metrics_collector",
    # Skill Metrics (NEW!)
    "SkillMetricsCollector",
    "get_skill_metrics_collector",
    "SkillInvocation",
    "RoutingMetrics",
    "CostSummary",
    "SKILL_METRICS_AVAILABLE",
    # Alerts
    "AlertManager",
    "Alert",
    "AlertLevel",
    "AlertCategory",
    # Health
    "HealthMonitor",
    "HealthStatus",
    "ComponentHealth",
    "SystemHealth",
    "check_redis_health",
    "check_database_health",
    "check_disk_space",
    "check_memory_usage",
    "check_cpu_usage",
]

__version__ = "1.0.0"
__author__ = "AI Trading System Team"
__phase__ = 7
