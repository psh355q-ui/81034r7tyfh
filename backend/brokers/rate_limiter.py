"""
KIS API Rate Limiter

Implements rate limiting for Korea Investment & Securities API calls.

Official Rate Limits:
- Real Trading: 20 calls/second per account
- Virtual Trading: 2 calls/second per account
- Token Issuance: 1 call/second

Author: AI Trading System Team
Date: 2025-11-15
"""

import time
import logging
from threading import Lock
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for KIS API.

    Prevents exceeding KIS API rate limits by tracking call timestamps
    and enforcing delays when necessary.
    """

    def __init__(
        self,
        calls_per_second: float = 2.0,
        is_virtual: bool = True,
    ):
        """
        Initialize rate limiter.

        Args:
            calls_per_second: Maximum calls per second
            is_virtual: Virtual (2/s) or Real (20/s) trading
        """
        # Set rate limit based on trading mode
        if is_virtual:
            self.calls_per_second = 2.0  # Virtual trading: 2/s
            self.mode = "Virtual"
        else:
            self.calls_per_second = 20.0  # Real trading: 20/s
            self.mode = "Real"

        # Override if explicitly set
        if calls_per_second != 2.0:
            self.calls_per_second = calls_per_second

        self.min_interval = 1.0 / self.calls_per_second

        # Track call timestamps (last N calls within 1 second window)
        self.call_history = deque(maxlen=int(self.calls_per_second))
        self.lock = Lock()

        # Statistics
        self.total_calls = 0
        self.total_delays = 0
        self.total_delay_time = 0.0

        logger.info(
            f"RateLimiter initialized: {self.calls_per_second} calls/s "
            f"({self.mode} Trading)"
        )

    def acquire(self) -> float:
        """
        Acquire permission to make an API call.

        Blocks if rate limit would be exceeded, returns immediately otherwise.

        Returns:
            Delay time in seconds (0 if no delay needed)
        """
        with self.lock:
            now = time.time()

            # Remove calls older than 1 second
            while self.call_history and (now - self.call_history[0] > 1.0):
                self.call_history.popleft()

            # Check if we're at the limit
            if len(self.call_history) >= self.calls_per_second:
                # Calculate required delay
                oldest_call = self.call_history[0]
                required_delay = 1.0 - (now - oldest_call)

                if required_delay > 0:
                    logger.debug(
                        f"Rate limit reached, delaying {required_delay:.3f}s "
                        f"({len(self.call_history)}/{self.calls_per_second} calls)"
                    )

                    # Release lock during sleep
                    self.lock.release()
                    time.sleep(required_delay)
                    self.lock.acquire()

                    # Update statistics
                    self.total_delays += 1
                    self.total_delay_time += required_delay

                    # Recalculate now after sleep
                    now = time.time()

                    # Clean up old calls again
                    while self.call_history and (now - self.call_history[0] > 1.0):
                        self.call_history.popleft()

                    delay = required_delay
                else:
                    delay = 0.0
            else:
                delay = 0.0

            # Record this call
            self.call_history.append(now)
            self.total_calls += 1

            return delay

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        with self.lock:
            return {
                "mode": self.mode,
                "calls_per_second": self.calls_per_second,
                "total_calls": self.total_calls,
                "total_delays": self.total_delays,
                "total_delay_time": self.total_delay_time,
                "avg_delay": (
                    self.total_delay_time / self.total_delays
                    if self.total_delays > 0
                    else 0.0
                ),
                "current_calls_in_window": len(self.call_history),
            }

    def reset_stats(self):
        """Reset statistics."""
        with self.lock:
            self.total_calls = 0
            self.total_delays = 0
            self.total_delay_time = 0.0
            logger.info("Rate limiter statistics reset")


class KISRateLimiter:
    """
    Specialized rate limiter for KIS API with separate limits for different endpoints.

    Manages rate limits for:
    - General REST API calls
    - Token issuance calls (stricter limit)
    """

    def __init__(self, is_virtual: bool = True):
        """
        Initialize KIS rate limiter.

        Args:
            is_virtual: Virtual (2/s) or Real (20/s) trading
        """
        self.is_virtual = is_virtual

        # General API rate limiter
        self.api_limiter = RateLimiter(
            calls_per_second=(2.0 if is_virtual else 20.0),
            is_virtual=is_virtual,
        )

        # Token issuance rate limiter (1/s for all modes)
        self.token_limiter = RateLimiter(
            calls_per_second=1.0,
            is_virtual=is_virtual,
        )

        logger.info(
            f"KIS RateLimiter initialized - "
            f"Mode: {'Virtual' if is_virtual else 'Real'}"
        )

    def acquire_api(self) -> float:
        """
        Acquire permission for general API call.

        Returns:
            Delay time in seconds
        """
        return self.api_limiter.acquire()

    def acquire_token(self) -> float:
        """
        Acquire permission for token issuance call.

        Returns:
            Delay time in seconds
        """
        return self.token_limiter.acquire()

    def get_stats(self) -> dict:
        """Get statistics for all limiters."""
        return {
            "api_limiter": self.api_limiter.get_stats(),
            "token_limiter": self.token_limiter.get_stats(),
        }

    def reset_stats(self):
        """Reset all statistics."""
        self.api_limiter.reset_stats()
        self.token_limiter.reset_stats()


# Example usage
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test_rate_limiter():
        """Test rate limiter functionality."""
        print("=" * 60)
        print("KIS API RATE LIMITER TEST")
        print("=" * 60)

        # Test virtual trading rate limiter (2 calls/second)
        print("\nTest 1: Virtual Trading (2 calls/second)")
        print("-" * 60)

        limiter = KISRateLimiter(is_virtual=True)

        print("Making 10 calls...")
        start = time.time()

        for i in range(10):
            delay = limiter.acquire_api()
            elapsed = time.time() - start
            print(f"Call {i+1:2d}: delay={delay:.3f}s, elapsed={elapsed:.3f}s")

        total_time = time.time() - start
        print(f"\nTotal time: {total_time:.3f}s")
        print(f"Expected: ~{10/2:.1f}s (10 calls / 2 per second)")

        stats = limiter.get_stats()
        print(f"\nStatistics:")
        print(f"  Total calls: {stats['api_limiter']['total_calls']}")
        print(f"  Total delays: {stats['api_limiter']['total_delays']}")
        print(f"  Avg delay: {stats['api_limiter']['avg_delay']:.3f}s")

        # Test real trading rate limiter (20 calls/second)
        print("\n" + "=" * 60)
        print("Test 2: Real Trading (20 calls/second)")
        print("-" * 60)

        limiter = KISRateLimiter(is_virtual=False)

        print("Making 30 calls...")
        start = time.time()

        for i in range(30):
            delay = limiter.acquire_api()
            elapsed = time.time() - start
            if i < 5 or i >= 25:  # Only print first 5 and last 5
                print(f"Call {i+1:2d}: delay={delay:.3f}s, elapsed={elapsed:.3f}s")
            elif i == 5:
                print("...")

        total_time = time.time() - start
        print(f"\nTotal time: {total_time:.3f}s")
        print(f"Expected: ~{30/20:.1f}s (30 calls / 20 per second)")

        stats = limiter.get_stats()
        print(f"\nStatistics:")
        print(f"  Total calls: {stats['api_limiter']['total_calls']}")
        print(f"  Total delays: {stats['api_limiter']['total_delays']}")
        print(f"  Avg delay: {stats['api_limiter']['avg_delay']:.3f}s")

        # Test token limiter (1 call/second)
        print("\n" + "=" * 60)
        print("Test 3: Token Issuance (1 call/second)")
        print("-" * 60)

        limiter = KISRateLimiter(is_virtual=True)

        print("Making 5 token calls...")
        start = time.time()

        for i in range(5):
            delay = limiter.acquire_token()
            elapsed = time.time() - start
            print(f"Token {i+1}: delay={delay:.3f}s, elapsed={elapsed:.3f}s")

        total_time = time.time() - start
        print(f"\nTotal time: {total_time:.3f}s")
        print(f"Expected: ~{5/1:.1f}s (5 calls / 1 per second)")

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    asyncio.run(test_rate_limiter())
