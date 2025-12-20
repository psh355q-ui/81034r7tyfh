"""
Health Monitor
Monitors system health and component status
"""

from enum import Enum
from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel

class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"

class ComponentHealth(BaseModel):
    """Health status of a component"""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    last_check: str

class SystemHealth(BaseModel):
    """Overall system health"""
    status: HealthStatus
    components: Dict[str, ComponentHealth]
    timestamp: str

class HealthMonitor:
    """Monitors system and component health"""

    def __init__(self, alert_manager=None):
        self.components: Dict[str, ComponentHealth] = {}
        self.alert_manager = alert_manager
        self.health_checks: Dict[str, callable] = {}
        self._initialize_components()

    def _initialize_components(self):
        """Initialize component health tracking"""
        components = ["redis", "timescaledb", "claude_api", "market_data", "broker"]
        for component in components:
            self.components[component] = ComponentHealth(
                name=component,
                status=HealthStatus.UNKNOWN,
                message="Not yet checked",
                last_check=datetime.now().isoformat()
            )

    def register_check(self, name: str, check_func: callable):
        """Register a health check function"""
        self.health_checks[name] = check_func

    async def run_checks(self):
        """Run all registered health checks"""
        for name, check_func in self.health_checks.items():
            try:
                result = check_func()
                # Assume checks return True for healthy, False for unhealthy
                if result:
                    self.update_component_health(
                        name.lower().replace(" ", "_"),
                        HealthStatus.HEALTHY,
                        "Check passed"
                    )
                else:
                    self.update_component_health(
                        name.lower().replace(" ", "_"),
                        HealthStatus.UNHEALTHY,
                        "Check failed"
                    )
            except Exception as e:
                self.update_component_health(
                    name.lower().replace(" ", "_"),
                    HealthStatus.UNHEALTHY,
                    f"Error: {str(e)}"
                )

    def update_component_health(
        self,
        component: str,
        status: HealthStatus,
        message: Optional[str] = None
    ):
        """Update health status of a component"""
        self.components[component] = ComponentHealth(
            name=component,
            status=status,
            message=message,
            last_check=datetime.now().isoformat()
        )

    def get_component_health(self, component: str) -> Optional[ComponentHealth]:
        """Get health status of a specific component"""
        return self.components.get(component)

    def get_system_health(self) -> SystemHealth:
        """Get overall system health"""
        # Determine overall status
        statuses = [comp.status for comp in self.components.values()]

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall = HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        else:
            overall = HealthStatus.UNKNOWN

        return SystemHealth(
            status=overall,
            components=self.components,
            timestamp=datetime.now().isoformat()
        )

    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        health = self.get_system_health()
        return health.status == HealthStatus.HEALTHY

    def get_unhealthy_components(self) -> list[str]:
        """Get list of unhealthy components"""
        return [
            name for name, comp in self.components.items()
            if comp.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]
        ]


# Utility functions
def check_disk_space() -> float:
    """Check available disk space (GB)"""
    import shutil
    try:
        stat = shutil.disk_usage(".")
        return stat.free / (1024**3)  # Convert to GB
    except Exception:
        return 0.0


def check_memory_usage() -> float:
    """Check memory usage percentage"""
    try:
        import psutil
        return psutil.virtual_memory().percent
    except ImportError:
        # psutil not installed
        return 0.0
    except Exception:
        return 0.0
