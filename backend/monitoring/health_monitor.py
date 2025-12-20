"""
Health Monitor - System Health Checking

Monitors system health and component availability.

Features:
- Component health checks (Database, Redis, AI APIs)
- System resource monitoring (Disk, Memory, CPU)
- Periodic health checks
- Automatic alerting on failures
- Health history tracking

Author: AI Trading System Team
Date: 2025-11-14
"""

import asyncio
import logging
try:
    import psutil
    import shutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None
    shutil = None
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a single component."""
    name: str
    status: HealthStatus
    message: str
    last_check: datetime
    response_time_ms: float = 0.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "last_check": self.last_check.isoformat(),
            "response_time_ms": self.response_time_ms,
            "metadata": self.metadata,
        }


@dataclass
class SystemHealth:
    """Overall system health."""
    status: HealthStatus
    timestamp: datetime
    components: List[ComponentHealth]
    system_resources: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "components": [c.to_dict() for c in self.components],
            "system_resources": self.system_resources,
        }


class HealthMonitor:
    """
    Monitors system health and component availability.

    Features:
    - Registered health checks
    - Periodic monitoring
    - Alert integration
    - Health history
    """

    def __init__(
        self,
        check_interval_seconds: int = 60,
        alert_manager = None,
    ):
        self.check_interval = check_interval_seconds
        self.alert_manager = alert_manager

        # Health checks registry
        self._health_checks: Dict[str, Callable[[], Awaitable[ComponentHealth]]] = {}

        # Health history (keep last 100 checks)
        self.health_history: List[SystemHealth] = []

        # Background task
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("Health Monitor initialized")

    def register_check(
        self,
        name: str,
        check_func: Callable[[], Awaitable[ComponentHealth]],
    ):
        """
        Register a health check function.

        Args:
            name: Component name
            check_func: Async function that returns ComponentHealth
        """
        self._health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")

    def unregister_check(self, name: str):
        """Unregister a health check."""
        if name in self._health_checks:
            del self._health_checks[name]
            logger.info(f"Unregistered health check: {name}")

    async def check_component(self, name: str) -> ComponentHealth:
        """
        Run health check for a single component.

        Args:
            name: Component name

        Returns:
            ComponentHealth result
        """
        if name not in self._health_checks:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="Health check not registered",
                last_check=datetime.utcnow(),
            )

        try:
            start_time = datetime.utcnow()
            health = await self._health_checks[name]()
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            health.response_time_ms = elapsed_ms
            return health

        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}",
                last_check=datetime.utcnow(),
            )

    async def get_system_health(self) -> SystemHealth:
        """
        Get overall system health.

        Returns:
            SystemHealth with all component statuses
        """
        # Run all health checks
        component_healths = []
        for name in self._health_checks.keys():
            health = await self.check_component(name)
            component_healths.append(health)

        # Determine overall status
        if not component_healths:
            overall_status = HealthStatus.UNKNOWN
        elif any(c.status == HealthStatus.UNHEALTHY for c in component_healths):
            overall_status = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in component_healths):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        # Get system resources
        system_resources = _get_system_resources()

        system_health = SystemHealth(
            status=overall_status,
            timestamp=datetime.utcnow(),
            components=component_healths,
            system_resources=system_resources,
        )

        # Store in history
        self.health_history.append(system_health)
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]

        # Send alert if unhealthy
        if overall_status == HealthStatus.UNHEALTHY and self.alert_manager:
            unhealthy_components = [
                c.name for c in component_healths
                if c.status == HealthStatus.UNHEALTHY
            ]
            await self.alert_manager.alert_system_error(
                error_message=f"System unhealthy. Failed components: {', '.join(unhealthy_components)}",
                error_type="HealthCheck",
            )

        return system_health

    async def start_monitoring(self):
        """Start periodic health monitoring."""
        if self._running:
            logger.warning("Health monitoring already running")
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started health monitoring (interval: {self.check_interval}s)")

    async def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                await self.get_system_health()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
                await asyncio.sleep(self.check_interval)

    def stop(self):
        """Stop periodic health monitoring."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
        logger.info("Stopped health monitoring")

    def get_summary(self) -> Dict:
        """Get health monitor summary."""
        recent_checks = self.health_history[-10:]  # Last 10 checks

        return {
            "registered_checks": list(self._health_checks.keys()),
            "check_interval_seconds": self.check_interval,
            "monitoring_active": self._running,
            "total_checks": len(self.health_history),
            "recent_checks": [h.to_dict() for h in recent_checks],
        }


# =============================================================================
# Built-in Health Checks
# =============================================================================

async def check_redis_health(redis_client=None) -> ComponentHealth:
    """Check Redis health."""
    try:
        if redis_client:
            # Actual Redis ping
            await redis_client.ping()
            return ComponentHealth(
                name="Redis",
                status=HealthStatus.HEALTHY,
                message="Redis is operational",
                last_check=datetime.utcnow(),
            )
        else:
            # Mock check
            return ComponentHealth(
                name="Redis",
                status=HealthStatus.UNKNOWN,
                message="Redis client not configured",
                last_check=datetime.utcnow(),
            )
    except Exception as e:
        return ComponentHealth(
            name="Redis",
            status=HealthStatus.UNHEALTHY,
            message=f"Redis check failed: {str(e)}",
            last_check=datetime.utcnow(),
        )


async def check_database_health(db_connection=None) -> ComponentHealth:
    """Check database health."""
    try:
        if db_connection:
            # Actual database query
            result = await db_connection.execute("SELECT 1")
            return ComponentHealth(
                name="Database",
                status=HealthStatus.HEALTHY,
                message="Database is operational",
                last_check=datetime.utcnow(),
            )
        else:
            # Mock check
            return ComponentHealth(
                name="Database",
                status=HealthStatus.UNKNOWN,
                message="Database connection not configured",
                last_check=datetime.utcnow(),
            )
    except Exception as e:
        return ComponentHealth(
            name="Database",
            status=HealthStatus.UNHEALTHY,
            message=f"Database check failed: {str(e)}",
            last_check=datetime.utcnow(),
        )


async def check_disk_space(threshold_pct: float = 90.0) -> ComponentHealth:
    if not PSUTIL_AVAILABLE or not shutil:
        return ComponentHealth(
            name="Disk Space",
            status=HealthStatus.UNKNOWN,
            message="psutil not installed",
            last_check=datetime.utcnow(),
        )
    
    """Check disk space."""
    try:
        usage = shutil.disk_usage("/")
        used_pct = (usage.used / usage.total) * 100

        if used_pct >= threshold_pct:
            status = HealthStatus.UNHEALTHY
            message = f"Disk usage critical: {used_pct:.1f}%"
        elif used_pct >= threshold_pct * 0.8:  # 72% for 90% threshold
            status = HealthStatus.DEGRADED
            message = f"Disk usage high: {used_pct:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk usage normal: {used_pct:.1f}%"

        return ComponentHealth(
            name="Disk Space",
            status=status,
            message=message,
            last_check=datetime.utcnow(),
            metadata={
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": usage.free / (1024**3),
                "used_pct": used_pct,
            },
        )
    except Exception as e:
        return ComponentHealth(
            name="Disk Space",
            status=HealthStatus.UNKNOWN,
            message=f"Disk check failed: {str(e)}",
            last_check=datetime.utcnow(),
        )


async def check_memory_usage(threshold_pct: float = 90.0) -> ComponentHealth:
    if not PSUTIL_AVAILABLE or not psutil:
        return ComponentHealth(
            name="Memory",
            status=HealthStatus.UNKNOWN,
            message="psutil not installed",
            last_check=datetime.utcnow(),
        )
    
    """Check memory usage."""
    try:
        memory = psutil.virtual_memory()
        used_pct = memory.percent

        if used_pct >= threshold_pct:
            status = HealthStatus.UNHEALTHY
            message = f"Memory usage critical: {used_pct:.1f}%"
        elif used_pct >= threshold_pct * 0.8:
            status = HealthStatus.DEGRADED
            message = f"Memory usage high: {used_pct:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory usage normal: {used_pct:.1f}%"

        return ComponentHealth(
            name="Memory",
            status=status,
            message=message,
            last_check=datetime.utcnow(),
            metadata={
                "total_gb": memory.total / (1024**3),
                "used_gb": memory.used / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_pct": used_pct,
            },
        )
    except Exception as e:
        return ComponentHealth(
            name="Memory",
            status=HealthStatus.UNKNOWN,
            message=f"Memory check failed: {str(e)}",
            last_check=datetime.utcnow(),
        )


async def check_cpu_usage(threshold_pct: float = 80.0, interval_seconds: float = 1.0) -> ComponentHealth:
    if not PSUTIL_AVAILABLE or not psutil:
        return ComponentHealth(
            name="CPU",
            status=HealthStatus.UNKNOWN,
            message="psutil not installed",
            last_check=datetime.utcnow(),
        )
    
    """Check CPU usage."""
    try:
        cpu_pct = psutil.cpu_percent(interval=interval_seconds)

        if cpu_pct >= threshold_pct:
            status = HealthStatus.UNHEALTHY
            message = f"CPU usage critical: {cpu_pct:.1f}%"
        elif cpu_pct >= threshold_pct * 0.8:
            status = HealthStatus.DEGRADED
            message = f"CPU usage high: {cpu_pct:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"CPU usage normal: {cpu_pct:.1f}%"

        return ComponentHealth(
            name="CPU",
            status=status,
            message=message,
            last_check=datetime.utcnow(),
            metadata={
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": cpu_pct,
            },
        )
    except Exception as e:
        return ComponentHealth(
            name="CPU",
            status=HealthStatus.UNKNOWN,
            message=f"CPU check failed: {str(e)}",
            last_check=datetime.utcnow(),
        )


def _get_system_resources() -> Dict:
    if not PSUTIL_AVAILABLE or not psutil or not shutil:
        return {}
    
    """Get current system resource usage."""
    try:
        cpu_pct = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = shutil.disk_usage("/")

        return {
            "cpu_percent": cpu_pct,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_used_percent": (disk.used / disk.total) * 100,
            "disk_free_gb": disk.free / (1024**3),
        }
    except Exception as e:
        logger.error(f"Failed to get system resources: {e}")
        return {}
