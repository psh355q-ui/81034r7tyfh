"""
API Failover Manager

Handles API failures gracefully with fallback strategies.

Phase: 5 (Strategy Ensemble)
Task: 7 (Failover Logic)

Features:
- Health check for all AI APIs
- Automatic failover to backup models
- Circuit breaker pattern
- Graceful degradation
"""

import logging
import asyncio
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class APIStatus(Enum):
    """API health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass
class HealthCheckResult:
    """Health check result for an API"""
    status: APIStatus
    latency_ms: float
    error_message: Optional[str] = None
    last_check: datetime = None
    consecutive_failures: int = 0


class CircuitBreaker:
    """
    Circuit breaker pattern for API calls.

    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, reject calls
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before attempting recovery
            success_threshold: Successes needed to close circuit from half-open
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self.state = "CLOSED"
        self.failures = 0
        self.successes = 0
        self.last_failure_time = None

        logger.info(f"CircuitBreaker initialized: threshold={failure_threshold}, timeout={timeout_seconds}s")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to call
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is OPEN or function fails
        """
        if self.state == "OPEN":
            # Check if timeout expired
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    logger.info("Circuit breaker: Moving to HALF_OPEN")
                    self.state = "HALF_OPEN"
                    self.successes = 0
                else:
                    raise Exception(f"Circuit breaker OPEN (retry in {self.timeout_seconds - elapsed:.0f}s)")
            else:
                raise Exception("Circuit breaker OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful call"""
        self.failures = 0

        if self.state == "HALF_OPEN":
            self.successes += 1
            logger.info(f"Circuit breaker HALF_OPEN: {self.successes}/{self.success_threshold} successes")

            if self.successes >= self.success_threshold:
                logger.info("Circuit breaker: Closing circuit (service recovered)")
                self.state = "CLOSED"
                self.successes = 0

    def _on_failure(self):
        """Handle failed call"""
        self.failures += 1
        self.last_failure_time = datetime.now()

        if self.state == "HALF_OPEN":
            logger.warning("Circuit breaker HALF_OPEN: Failure detected, reopening circuit")
            self.state = "OPEN"
            self.successes = 0
        elif self.failures >= self.failure_threshold:
            logger.error(f"Circuit breaker: Opening circuit ({self.failures} consecutive failures)")
            self.state = "OPEN"


class FailoverManager:
    """
    Manages failover between multiple AI APIs.

    Hierarchy (Task 7 final):
    1. Primary: ChatGPT (regime) + Gemini (risk) + Claude (decisions)
    2. Fallback 1: Claude only (if ChatGPT/Gemini down)
    3. Fallback 2: Rule-based (if all AI down)
    """

    def __init__(self):
        """Initialize failover manager"""
        self.health_status: Dict[str, HealthCheckResult] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            "chatgpt": CircuitBreaker(failure_threshold=5, timeout_seconds=60),
            "gemini": CircuitBreaker(failure_threshold=5, timeout_seconds=60),
            "claude": CircuitBreaker(failure_threshold=5, timeout_seconds=60),
        }

        # Failover preferences
        self.api_hierarchy = {
            "regime_detection": ["chatgpt", "claude", "rule_based"],
            "risk_screening": ["gemini", "rule_based"],
            "investment_analysis": ["claude", "rule_based"],
        }

        logger.info("FailoverManager initialized with 3 AI APIs")

    async def health_check(self, api_name: str, check_func: Callable) -> HealthCheckResult:
        """
        Perform health check on an API.

        Args:
            api_name: Name of API (chatgpt, gemini, claude)
            check_func: Async function to test API

        Returns:
            HealthCheckResult with status
        """
        start_time = datetime.now()

        try:
            await asyncio.wait_for(check_func(), timeout=5.0)
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = HealthCheckResult(
                status=APIStatus.HEALTHY,
                latency_ms=latency_ms,
                last_check=datetime.now(),
                consecutive_failures=0
            )

            logger.info(f"Health check {api_name}: HEALTHY ({latency_ms:.0f}ms)")

        except asyncio.TimeoutError:
            result = HealthCheckResult(
                status=APIStatus.DOWN,
                latency_ms=5000.0,
                error_message="Timeout",
                last_check=datetime.now(),
                consecutive_failures=self.health_status.get(api_name, HealthCheckResult(
                    APIStatus.DOWN, 0
                )).consecutive_failures + 1
            )
            logger.error(f"Health check {api_name}: DOWN (timeout)")

        except Exception as e:
            result = HealthCheckResult(
                status=APIStatus.DOWN,
                latency_ms=0.0,
                error_message=str(e),
                last_check=datetime.now(),
                consecutive_failures=self.health_status.get(api_name, HealthCheckResult(
                    APIStatus.DOWN, 0
                )).consecutive_failures + 1
            )
            logger.error(f"Health check {api_name}: DOWN ({e})")

        self.health_status[api_name] = result
        return result

    async def call_with_failover(
        self,
        task_type: str,
        primary_func: Callable,
        fallback_func: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Call function with automatic failover.

        Args:
            task_type: Type of task (regime_detection, risk_screening, etc.)
            primary_func: Primary function to call
            fallback_func: Fallback function if primary fails
            *args, **kwargs: Function arguments

        Returns:
            Function result (from primary or fallback)
        """
        # Try primary
        try:
            api_name = list(self.api_hierarchy.get(task_type, ["unknown"]))[0]
            if api_name in self.circuit_breakers:
                result = await self.circuit_breakers[api_name].call(primary_func, *args, **kwargs)
                logger.info(f"Failover: {task_type} succeeded with primary ({api_name})")
                return result
            else:
                result = await primary_func(*args, **kwargs)
                logger.info(f"Failover: {task_type} succeeded with primary (no circuit breaker)")
                return result

        except Exception as e:
            logger.warning(f"Failover: {task_type} primary failed: {e}")

            # Try fallback
            if fallback_func:
                try:
                    result = await fallback_func(*args, **kwargs)
                    logger.info(f"Failover: {task_type} succeeded with fallback")
                    return result
                except Exception as e2:
                    logger.error(f"Failover: {task_type} fallback also failed: {e2}")
                    raise Exception(f"Both primary and fallback failed for {task_type}")
            else:
                raise e

    def get_health_summary(self) -> Dict[str, Dict]:
        """
        Get health summary for all APIs.

        Returns:
            Dictionary with API health status
        """
        summary = {}

        for api_name, health in self.health_status.items():
            circuit_breaker = self.circuit_breakers.get(api_name)

            summary[api_name] = {
                "status": health.status.value,
                "latency_ms": health.latency_ms,
                "error": health.error_message,
                "last_check": health.last_check.isoformat() if health.last_check else None,
                "consecutive_failures": health.consecutive_failures,
                "circuit_breaker_state": circuit_breaker.state if circuit_breaker else None
            }

        return summary

    async def run_all_health_checks(
        self,
        check_functions: Dict[str, Callable]
    ) -> Dict[str, HealthCheckResult]:
        """
        Run health checks for all APIs in parallel.

        Args:
            check_functions: Dictionary of {api_name: check_func}

        Returns:
            Dictionary of {api_name: HealthCheckResult}
        """
        tasks = [
            self.health_check(api_name, check_func)
            for api_name, check_func in check_functions.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            api_name: result if not isinstance(result, Exception) else HealthCheckResult(
                status=APIStatus.DOWN,
                latency_ms=0.0,
                error_message=str(result),
                last_check=datetime.now()
            )
            for api_name, result in zip(check_functions.keys(), results)
        }


# Global instance
failover_manager = FailoverManager()


if __name__ == "__main__":
    """Test failover manager"""

    async def test_healthy_api():
        """Simulate healthy API"""
        await asyncio.sleep(0.1)
        return {"status": "ok"}

    async def test_slow_api():
        """Simulate slow API"""
        await asyncio.sleep(6.0)  # Timeout
        return {"status": "ok"}

    async def test_failing_api():
        """Simulate failing API"""
        raise Exception("API Error")

    async def test_failover():
        """Test failover scenarios"""
        manager = FailoverManager()

        print("=" * 60)
        print("Failover Manager Test")
        print("=" * 60)
        print()

        # Test 1: Health checks
        print("Test 1: Health Checks")
        results = await manager.run_all_health_checks({
            "api_healthy": test_healthy_api,
            "api_slow": test_slow_api,
            "api_failing": test_failing_api,
        })

        for api_name, result in results.items():
            print(f"  {api_name}: {result.status.value} ({result.latency_ms:.0f}ms)")

        print()

        # Test 2: Circuit breaker
        print("Test 2: Circuit Breaker")
        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=2)

        for i in range(5):
            try:
                await cb.call(test_failing_api)
            except Exception as e:
                print(f"  Call {i+1}: Failed (state={cb.state}, failures={cb.failures})")

        print()

        # Test 3: Failover
        print("Test 3: Failover with Fallback")
        try:
            result = await manager.call_with_failover(
                "test_task",
                test_failing_api,
                test_healthy_api
            )
            print(f"  Result: {result} (used fallback)")
        except Exception as e:
            print(f"  Failed: {e}")

        print()
        print("=" * 60)
        print("All tests completed!")
        print("=" * 60)

    # Run tests
    asyncio.run(test_failover())
