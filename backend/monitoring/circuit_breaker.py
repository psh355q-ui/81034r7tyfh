"""
Circuit Breaker & Kill Switch - System safety mechanisms

Features:
- Circuit Breaker pattern for external API calls
- Kill Switch for emergency trading halt
- Automatic recovery with exponential backoff
- Configurable thresholds per component
- Monitoring and alerting integration

Author: AI Trading System Team
Date: 2025-11-24
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = 0      # Normal operation
    HALF_OPEN = 1   # Testing if service recovered
    OPEN = 2        # Service unavailable, blocking requests


@dataclass
class CircuitConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5           # Failures before opening
    success_threshold: int = 2           # Successes to close from half-open
    timeout_seconds: int = 60            # Time before attempting half-open
    half_open_timeout_seconds: int = 30  # Time in half-open before re-opening


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests immediately fail
    - HALF_OPEN: Testing recovery, limited requests allowed

    Flow:
    CLOSED --[failures > threshold]--> OPEN
    OPEN --[timeout elapsed]--> HALF_OPEN
    HALF_OPEN --[successes >= threshold]--> CLOSED
    HALF_OPEN --[any failure]--> OPEN
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitConfig] = None,
        on_state_change: Optional[Callable] = None,
    ):
        self.name = name
        self.config = config or CircuitConfig()
        self.on_state_change = on_state_change

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.utcnow()

        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_rejected = 0

        logger.info(f"CircuitBreaker '{name}' initialized")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute (can be async or sync)
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception: If function fails
        """
        self.total_calls += 1

        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit '{self.name}' attempting half-open")
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                self.total_rejected += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN"
                )

        try:
            # Execute function (handle both sync and async)
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success
            self._on_success()
            return result

        except Exception as e:
            # Failure
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        self.total_successes += 1
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info(f"Circuit '{self.name}' closing after {self.success_count} successes")
                self._transition_to(CircuitState.CLOSED)

    def _on_failure(self):
        """Handle failed call."""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state reopens circuit
            logger.warning(f"Circuit '{self.name}' reopening after failure in half-open")
            self._transition_to(CircuitState.OPEN)

        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                logger.warning(
                    f"Circuit '{self.name}' opening after {self.failure_count} failures"
                )
                self._transition_to(CircuitState.OPEN)

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout_seconds

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state."""
        old_state = self.state
        self.state = new_state
        self.last_state_change = datetime.utcnow()

        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.success_count = 0
        elif new_state == CircuitState.OPEN:
            self.success_count = 0

        logger.info(f"Circuit '{self.name}' transitioned: {old_state.name} -> {new_state.name}")

        # Notify callback
        if self.on_state_change:
            try:
                self.on_state_change(self.name, old_state, new_state)
            except Exception as e:
                logger.error(f"Error in circuit breaker callback: {e}")

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

    def get_stats(self) -> Dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.name,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "total_rejected": self.total_rejected,
            "failure_rate": (
                self.total_failures / self.total_calls if self.total_calls > 0 else 0
            ),
            "last_state_change": self.last_state_change.isoformat(),
        }

    def reset(self):
        """Manually reset circuit to closed state."""
        logger.info(f"Circuit '{self.name}' manually reset")
        self._transition_to(CircuitState.CLOSED)


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# =============================================================================
# Kill Switch
# =============================================================================

class KillSwitchReason(Enum):
    """Reasons for kill switch activation."""
    MANUAL = "manual"                      # User activated
    DAILY_LOSS_LIMIT = "daily_loss_limit" # Hit daily loss limit
    SYSTEM_ERROR = "system_error"          # Critical system error
    DATA_QUALITY = "data_quality"          # Bad data detected
    EXCESSIVE_VOLATILITY = "volatility"    # Market too volatile
    API_FAILURE = "api_failure"            # External API failure
    RISK_THRESHOLD = "risk_threshold"      # Risk limits breached


class KillSwitch:
    """
    Emergency trading halt mechanism.

    When activated:
    - All new orders are blocked
    - Open orders can be cancelled (optional)
    - Positions can be closed (optional)
    - System enters safe mode
    - Alerts are sent to all channels
    """

    def __init__(
        self,
        alert_manager=None,
        auto_cancel_orders: bool = False,
        auto_close_positions: bool = False,
    ):
        self.alert_manager = alert_manager
        self.auto_cancel_orders = auto_cancel_orders
        self.auto_close_positions = auto_close_positions

        self.is_active = False
        self.activation_time: Optional[datetime] = None
        self.activation_reason: Optional[KillSwitchReason] = None
        self.activation_message: Optional[str] = None
        self.activation_metadata: Optional[Dict] = None

        # Callbacks
        self.on_activate_callbacks = []
        self.on_deactivate_callbacks = []

        logger.info("KillSwitch initialized")

    def register_on_activate(self, callback: Callable):
        """Register callback for kill switch activation."""
        self.on_activate_callbacks.append(callback)

    def register_on_deactivate(self, callback: Callable):
        """Register callback for kill switch deactivation."""
        self.on_deactivate_callbacks.append(callback)

    async def activate(
        self,
        reason: KillSwitchReason,
        message: str,
        metadata: Optional[Dict] = None,
    ):
        """
        Activate kill switch.

        Args:
            reason: Reason for activation
            message: Human-readable message
            metadata: Additional context
        """
        if self.is_active:
            logger.warning("Kill switch already active")
            return

        self.is_active = True
        self.activation_time = datetime.utcnow()
        self.activation_reason = reason
        self.activation_message = message
        self.activation_metadata = metadata or {}

        logger.critical(
            f"🚨 KILL SWITCH ACTIVATED 🚨\n"
            f"Reason: {reason.value}\n"
            f"Message: {message}"
        )

        # Send alert
        if self.alert_manager:
            await self.alert_manager.alert_critical_error(
                error=f"Kill Switch Activated: {message}",
                details={
                    "reason": reason.value,
                    "time": self.activation_time.isoformat(),
                    **self.activation_metadata,
                },
            )

        # Execute callbacks
        for callback in self.on_activate_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reason, message, metadata)
                else:
                    callback(reason, message, metadata)
            except Exception as e:
                logger.error(f"Error in kill switch activate callback: {e}")

    async def deactivate(self, message: Optional[str] = None):
        """
        Deactivate kill switch.

        Args:
            message: Optional message explaining deactivation
        """
        if not self.is_active:
            logger.warning("Kill switch not active")
            return

        duration = (datetime.utcnow() - self.activation_time).total_seconds()

        logger.info(
            f"Kill switch deactivated after {duration:.1f}s\n"
            f"Original reason: {self.activation_reason.value}\n"
            f"Deactivation message: {message or 'Manual deactivation'}"
        )

        self.is_active = False

        # Send alert
        if self.alert_manager:
            from .smart_alerts import AlertCategory, AlertPriority
            await self.alert_manager.send_alert(
                category=AlertCategory.SYSTEM_ERROR,
                priority=AlertPriority.HIGH,
                title="Kill Switch Deactivated",
                message=message or "System resumed normal operation",
                metadata={
                    "duration_seconds": duration,
                    "original_reason": self.activation_reason.value,
                },
            )

        # Execute callbacks
        for callback in self.on_deactivate_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"Error in kill switch deactivate callback: {e}")

    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed."""
        return not self.is_active

    def get_status(self) -> Dict:
        """Get kill switch status."""
        return {
            "is_active": self.is_active,
            "activation_time": (
                self.activation_time.isoformat() if self.activation_time else None
            ),
            "activation_reason": (
                self.activation_reason.value if self.activation_reason else None
            ),
            "activation_message": self.activation_message,
            "duration_seconds": (
                (datetime.utcnow() - self.activation_time).total_seconds()
                if self.activation_time
                else 0
            ),
            "metadata": self.activation_metadata,
        }


# =============================================================================
# Circuit Breaker Manager
# =============================================================================

class CircuitBreakerManager:
    """Manages multiple circuit breakers."""

    def __init__(self, alert_manager=None):
        self.alert_manager = alert_manager
        self.breakers: Dict[str, CircuitBreaker] = {}
        logger.info("CircuitBreakerManager initialized")

    def create_breaker(
        self,
        name: str,
        config: Optional[CircuitConfig] = None,
    ) -> CircuitBreaker:
        """Create and register a circuit breaker."""
        if name in self.breakers:
            logger.warning(f"Circuit breaker '{name}' already exists")
            return self.breakers[name]

        breaker = CircuitBreaker(
            name=name,
            config=config,
            on_state_change=self._on_state_change,
        )

        self.breakers[name] = breaker
        logger.info(f"Created circuit breaker: {name}")
        return breaker

    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self.breakers.get(name)

    def _on_state_change(
        self,
        name: str,
        old_state: CircuitState,
        new_state: CircuitState,
    ):
        """Handle circuit breaker state change."""
        if new_state == CircuitState.OPEN and self.alert_manager:
            asyncio.create_task(
                self._send_circuit_open_alert(name)
            )

    async def _send_circuit_open_alert(self, name: str):
        """Send alert when circuit opens."""
        if self.alert_manager:
            from .smart_alerts import AlertCategory, AlertPriority
            await self.alert_manager.send_alert(
                category=AlertCategory.SYSTEM_ERROR,
                priority=AlertPriority.HIGH,
                title=f"Circuit Breaker Opened: {name}",
                message=f"Component '{name}' is experiencing failures and has been circuit-broken",
                metadata={"component": name},
            )

    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self.breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self.breakers.values():
            breaker.reset()
        logger.info("Reset all circuit breakers")
