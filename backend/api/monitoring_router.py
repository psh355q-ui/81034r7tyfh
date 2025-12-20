"""
Monitoring API Router - Advanced monitoring and health check endpoints

Provides:
- Detailed health checks
- System metrics
- Circuit breaker status
- Kill switch controls
- Alert statistics
- Performance metrics

Author: AI Trading System Team
Date: 2025-11-24
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Import monitoring components
try:
    from backend.monitoring.health_monitor import HealthMonitor, HealthStatus
    from backend.monitoring.trading_metrics import metrics_collector
    from backend.monitoring.smart_alerts import SmartAlertManager, AlertCategory, AlertPriority
    from backend.monitoring.circuit_breaker import (
        CircuitBreakerManager,
        KillSwitch,
        KillSwitchReason,
        CircuitState,
    )
    MONITORING_AVAILABLE = True
except ImportError as e:
    MONITORING_AVAILABLE = False
    print(f"Monitoring components not available: {e}")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# =============================================================================
# Request/Response Models
# =============================================================================

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    components: List[Dict]
    system_resources: Dict


class KillSwitchActivateRequest(BaseModel):
    reason: str
    message: str
    metadata: Optional[Dict] = None


class KillSwitchResponse(BaseModel):
    is_active: bool
    activation_time: Optional[str]
    activation_reason: Optional[str]
    activation_message: Optional[str]
    duration_seconds: float


class CircuitBreakerResponse(BaseModel):
    name: str
    state: str
    failure_count: int
    success_count: int
    total_calls: int
    failure_rate: float


# =============================================================================
# Global Instances (initialized in main.py)
# =============================================================================

health_monitor: Optional[HealthMonitor] = None
alert_manager: Optional[SmartAlertManager] = None
circuit_breaker_manager: Optional[CircuitBreakerManager] = None
kill_switch: Optional[KillSwitch] = None


def set_monitoring_instances(
    health_mon: HealthMonitor,
    alert_mgr: SmartAlertManager,
    cb_mgr: CircuitBreakerManager,
    ks: KillSwitch,
):
    """Set global monitoring instances (called from main.py)."""
    global health_monitor, alert_manager, circuit_breaker_manager, kill_switch
    health_monitor = health_mon
    alert_manager = alert_mgr
    circuit_breaker_manager = cb_mgr
    kill_switch = ks


# =============================================================================
# Health Check Endpoints
# =============================================================================

@router.get("/health", response_model=HealthCheckResponse)
async def get_detailed_health():
    """
    Get detailed system health status.

    Returns comprehensive health information including:
    - All component health statuses
    - System resource usage
    - Response times
    """
    if not health_monitor:
        return {
            "status": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "components": [],
            "system_resources": {},
        }

    system_health = await health_monitor.get_system_health()
    return system_health.to_dict()


@router.get("/health/summary")
async def get_health_summary():
    """Get health check summary and statistics."""
    if not health_monitor:
        return {"error": "Health monitor not initialized"}

    return health_monitor.get_summary()


@router.get("/health/component/{component_name}")
async def get_component_health(component_name: str):
    """Get health status for a specific component."""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not initialized")

    health = await health_monitor.check_component(component_name)
    return health.to_dict()


# =============================================================================
# Metrics Endpoints
# =============================================================================

@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get summary of key metrics."""
    if not metrics_collector:
        return {"error": "Metrics collector not initialized"}

    # Gather key metrics from Prometheus
    try:
        from prometheus_client import REGISTRY, generate_latest

        metrics_data = generate_latest(REGISTRY).decode('utf-8')

        # Parse key metrics (simplified)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_available": True,
            "prometheus_endpoint": "/metrics",
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/metrics/trading")
async def get_trading_metrics():
    """Get trading-specific metrics."""
    # Return trading metrics summary
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "description": "Trading metrics available at /metrics endpoint",
        "key_metrics": [
            "trades_total",
            "trade_slippage_bps",
            "signals_generated_total",
            "portfolio_value_usd",
            "ai_cost_usd_total",
        ],
    }


# =============================================================================
# Alert Management Endpoints
# =============================================================================

@router.get("/alerts/statistics")
async def get_alert_statistics():
    """Get alert system statistics."""
    if not alert_manager:
        return {"error": "Alert manager not initialized"}

    return alert_manager.get_statistics()


@router.get("/alerts/recent")
async def get_recent_alerts(limit: int = 50):
    """Get recent alerts."""
    if not alert_manager:
        raise HTTPException(status_code=503, detail="Alert manager not initialized")

    recent = []
    for category, alerts in alert_manager.recent_alerts.items():
        for alert in list(alerts)[-limit:]:
            recent.append(alert.to_dict())

    # Sort by timestamp descending
    recent.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "total": len(recent),
        "alerts": recent[:limit],
    }


@router.post("/alerts/test")
async def test_alert(
    category: str = "SYSTEM_ERROR",
    priority: str = "MEDIUM",
    message: str = "Test alert from monitoring API",
):
    """Send a test alert."""
    if not alert_manager:
        raise HTTPException(status_code=503, detail="Alert manager not initialized")

    try:
        category_enum = AlertCategory[category.upper()]
        priority_enum = AlertPriority[priority.upper()]

        success = await alert_manager.send_alert(
            category=category_enum,
            priority=priority_enum,
            title="Test Alert",
            message=message,
            force=True,  # Bypass filters for test
        )

        return {
            "success": success,
            "message": "Test alert sent" if success else "Test alert filtered",
        }

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category or priority: {e}")


# =============================================================================
# Circuit Breaker Endpoints
# =============================================================================

@router.get("/circuit-breakers")
async def get_all_circuit_breakers():
    """Get status of all circuit breakers."""
    if not circuit_breaker_manager:
        return {"error": "Circuit breaker manager not initialized"}

    stats = circuit_breaker_manager.get_all_stats()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_breakers": len(stats),
        "breakers": stats,
    }


@router.get("/circuit-breakers/{name}")
async def get_circuit_breaker(name: str):
    """Get status of a specific circuit breaker."""
    if not circuit_breaker_manager:
        raise HTTPException(status_code=503, detail="Circuit breaker manager not initialized")

    breaker = circuit_breaker_manager.get_breaker(name)
    if not breaker:
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")

    return breaker.get_stats()


@router.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(name: str):
    """Manually reset a circuit breaker."""
    if not circuit_breaker_manager:
        raise HTTPException(status_code=503, detail="Circuit breaker manager not initialized")

    breaker = circuit_breaker_manager.get_breaker(name)
    if not breaker:
        raise HTTPException(status_code=404, detail=f"Circuit breaker '{name}' not found")

    breaker.reset()

    return {
        "success": True,
        "message": f"Circuit breaker '{name}' reset to CLOSED state",
    }


@router.post("/circuit-breakers/reset-all")
async def reset_all_circuit_breakers():
    """Reset all circuit breakers."""
    if not circuit_breaker_manager:
        raise HTTPException(status_code=503, detail="Circuit breaker manager not initialized")

    circuit_breaker_manager.reset_all()

    return {
        "success": True,
        "message": "All circuit breakers reset",
        "count": len(circuit_breaker_manager.breakers),
    }


# =============================================================================
# Kill Switch Endpoints
# =============================================================================

@router.get("/kill-switch", response_model=KillSwitchResponse)
async def get_kill_switch_status():
    """Get kill switch status."""
    if not kill_switch:
        raise HTTPException(status_code=503, detail="Kill switch not initialized")

    return kill_switch.get_status()


@router.post("/kill-switch/activate")
async def activate_kill_switch(request: KillSwitchActivateRequest):
    """
    Activate kill switch.

    WARNING: This will halt all trading operations!
    """
    if not kill_switch:
        raise HTTPException(status_code=503, detail="Kill switch not initialized")

    try:
        reason = KillSwitchReason[request.reason.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reason. Valid reasons: {[r.name for r in KillSwitchReason]}",
        )

    await kill_switch.activate(
        reason=reason,
        message=request.message,
        metadata=request.metadata,
    )

    return {
        "success": True,
        "message": "Kill switch activated",
        "status": kill_switch.get_status(),
    }


@router.post("/kill-switch/deactivate")
async def deactivate_kill_switch(message: Optional[str] = None):
    """
    Deactivate kill switch and resume trading operations.
    """
    if not kill_switch:
        raise HTTPException(status_code=503, detail="Kill switch not initialized")

    if not kill_switch.is_active:
        raise HTTPException(status_code=400, detail="Kill switch is not active")

    await kill_switch.deactivate(message=message)

    return {
        "success": True,
        "message": "Kill switch deactivated",
        "status": kill_switch.get_status(),
    }


# =============================================================================
# System Information Endpoints
# =============================================================================

@router.get("/system/info")
async def get_system_info():
    """Get comprehensive system information."""
    info = {
        "timestamp": datetime.utcnow().isoformat(),
        "monitoring": {
            "health_monitor": health_monitor is not None,
            "alert_manager": alert_manager is not None,
            "circuit_breaker_manager": circuit_breaker_manager is not None,
            "kill_switch": kill_switch is not None,
        },
        "kill_switch_active": kill_switch.is_active if kill_switch else False,
    }

    # Add circuit breaker summary
    if circuit_breaker_manager:
        breaker_states = {}
        for name, breaker in circuit_breaker_manager.breakers.items():
            breaker_states[name] = breaker.get_state().name

        info["circuit_breakers"] = breaker_states

    return info


@router.get("/system/status")
async def get_system_status():
    """Get quick system status (healthy/degraded/unhealthy)."""
    if not health_monitor:
        return {
            "status": "unknown",
            "message": "Health monitor not initialized",
        }

    system_health = await health_monitor.get_system_health()

    return {
        "status": system_health.status.value,
        "timestamp": system_health.timestamp.isoformat(),
        "components_count": len(system_health.components),
        "unhealthy_components": [
            c.name
            for c in system_health.components
            if c.status == HealthStatus.UNHEALTHY
        ],
    }
