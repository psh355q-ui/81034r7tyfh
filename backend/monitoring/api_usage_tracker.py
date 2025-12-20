"""
API Usage Tracker - Monitor Gemini API rate limits and costs

Tracks:
- Requests per minute (RPM)
- Requests per day (RPD)
- Token usage
- Cost estimation
- Rate limit violations

Author: AI Trading System Team
Date: 2025-12-12
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass, asdict
import json


@dataclass
class APIUsageSnapshot:
    """Snapshot of API usage at a point in time"""
    timestamp: str
    requests_last_minute: int
    requests_today: int
    tokens_last_minute: int
    tokens_today: int
    estimated_cost_today: float
    rate_limit_status: str  # "OK", "WARNING", "EXCEEDED"
    next_reset_time: Optional[str] = None


@dataclass
class RateLimits:
    """Rate limits for Gemini API models"""
    model: str
    rpm: int  # Requests per minute
    rpd: int  # Requests per day
    tpm: int  # Tokens per minute

    # Free tier limits for gemini-2.0-flash-exp
    @classmethod
    def get_default(cls):
        return cls(
            model="gemini-2.0-flash-exp",
            rpm=10,
            rpd=1500,
            tpm=4_000_000
        )


class APIUsageTracker:
    """
    Tracks API usage in memory with sliding windows

    Features:
    - Sliding window for RPM tracking
    - Daily reset at midnight Pacific Time
    - Cost estimation
    - Rate limit warnings
    """

    def __init__(self, limits: Optional[RateLimits] = None):
        self.limits = limits or RateLimits.get_default()

        # Sliding window for last minute (stores timestamps)
        self.requests_last_minute: deque = deque()
        self.tokens_last_minute: deque = deque()

        # Daily counters (reset at midnight PT)
        self.daily_requests = 0
        self.daily_tokens = 0
        self.daily_reset_date = self._get_current_date_pt()

        # Cost tracking (estimated)
        # gemini-2.0-flash-exp is free, but we track for future paid tier
        self.cost_per_1k_input_tokens = 0.0  # Free tier
        self.cost_per_1k_output_tokens = 0.0  # Free tier

        # History for monitoring dashboard
        self.usage_history: List[APIUsageSnapshot] = []
        self.max_history_size = 1440  # 24 hours at 1-minute intervals

    def _get_current_date_pt(self) -> str:
        """Get current date in Pacific Time (YYYY-MM-DD)"""
        # Approximate PT as UTC-8 (ignoring DST for simplicity)
        pt_time = datetime.utcnow() - timedelta(hours=8)
        return pt_time.strftime("%Y-%m-%d")

    def _cleanup_old_entries(self):
        """Remove entries older than 1 minute from sliding windows"""
        now = time.time()
        cutoff = now - 60  # 1 minute ago

        # Clean requests
        while self.requests_last_minute and self.requests_last_minute[0] < cutoff:
            self.requests_last_minute.popleft()

        # Clean tokens
        while self.tokens_last_minute and self.tokens_last_minute[0][0] < cutoff:
            self.tokens_last_minute.popleft()

    def _check_daily_reset(self):
        """Reset daily counters if date changed"""
        current_date = self._get_current_date_pt()
        if current_date != self.daily_reset_date:
            self.daily_requests = 0
            self.daily_tokens = 0
            self.daily_reset_date = current_date

    def record_request(self, input_tokens: int = 0, output_tokens: int = 0):
        """
        Record a new API request

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
        """
        now = time.time()

        # Cleanup old entries
        self._cleanup_old_entries()
        self._check_daily_reset()

        # Record request
        self.requests_last_minute.append(now)
        self.daily_requests += 1

        # Record tokens
        total_tokens = input_tokens + output_tokens
        if total_tokens > 0:
            self.tokens_last_minute.append((now, total_tokens))
            self.daily_tokens += total_tokens

    def get_current_usage(self) -> APIUsageSnapshot:
        """Get current usage snapshot"""
        self._cleanup_old_entries()
        self._check_daily_reset()

        # Count requests in last minute
        rpm_count = len(self.requests_last_minute)

        # Count tokens in last minute
        tpm_count = sum(tokens for _, tokens in self.tokens_last_minute)

        # Estimate cost (free tier = $0, but we track for monitoring)
        estimated_cost = 0.0
        if self.cost_per_1k_input_tokens > 0:
            estimated_cost = (self.daily_tokens / 1000) * self.cost_per_1k_input_tokens

        # Determine rate limit status
        status = "OK"
        if rpm_count >= self.limits.rpm * 0.8 or self.daily_requests >= self.limits.rpd * 0.8:
            status = "WARNING"
        if rpm_count >= self.limits.rpm or self.daily_requests >= self.limits.rpd:
            status = "EXCEEDED"

        # Calculate next reset time (midnight PT)
        pt_now = datetime.utcnow() - timedelta(hours=8)
        next_midnight_pt = (pt_now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_reset = next_midnight_pt.isoformat()

        snapshot = APIUsageSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            requests_last_minute=rpm_count,
            requests_today=self.daily_requests,
            tokens_last_minute=tpm_count,
            tokens_today=self.daily_tokens,
            estimated_cost_today=estimated_cost,
            rate_limit_status=status,
            next_reset_time=next_reset
        )

        # Add to history
        self.usage_history.append(snapshot)
        if len(self.usage_history) > self.max_history_size:
            self.usage_history.pop(0)

        return snapshot

    def get_usage_stats(self) -> Dict:
        """Get detailed usage statistics"""
        snapshot = self.get_current_usage()

        return {
            "current": asdict(snapshot),
            "limits": {
                "model": self.limits.model,
                "rpm": self.limits.rpm,
                "rpd": self.limits.rpd,
                "tpm": self.limits.tpm
            },
            "utilization": {
                "rpm_percent": (snapshot.requests_last_minute / self.limits.rpm * 100) if self.limits.rpm > 0 else 0,
                "rpd_percent": (snapshot.requests_today / self.limits.rpd * 100) if self.limits.rpd > 0 else 0,
                "tpm_percent": (snapshot.tokens_last_minute / self.limits.tpm * 100) if self.limits.tpm > 0 else 0
            },
            "recommendations": self._get_recommendations(snapshot)
        }

    def _get_recommendations(self, snapshot: APIUsageSnapshot) -> List[str]:
        """Generate recommendations based on usage"""
        recommendations = []

        rpm_percent = (snapshot.requests_last_minute / self.limits.rpm * 100) if self.limits.rpm > 0 else 0
        rpd_percent = (snapshot.requests_today / self.limits.rpd * 100) if self.limits.rpd > 0 else 0

        if snapshot.rate_limit_status == "EXCEEDED":
            recommendations.append("⚠️ Rate limit exceeded. API calls will fail until reset.")
            recommendations.append(f"Daily reset at: {snapshot.next_reset_time}")
        elif snapshot.rate_limit_status == "WARNING":
            if rpm_percent >= 80:
                recommendations.append("⚠️ Approaching RPM limit. Consider throttling requests.")
            if rpd_percent >= 80:
                recommendations.append("⚠️ Approaching daily limit. Prioritize critical analysis.")

        if rpd_percent >= 50 and rpd_percent < 80:
            recommendations.append("💡 Consider upgrading to paid tier for unlimited requests.")

        if snapshot.requests_today == 0:
            recommendations.append("✅ No API usage today. All systems ready.")

        return recommendations

    def get_history(self, minutes: int = 60) -> List[Dict]:
        """Get usage history for last N minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        cutoff_str = cutoff.isoformat()

        return [
            asdict(snapshot)
            for snapshot in self.usage_history
            if snapshot.timestamp >= cutoff_str
        ]

    def should_throttle(self) -> bool:
        """Check if requests should be throttled"""
        snapshot = self.get_current_usage()

        # Throttle if we're at 90% of either limit
        rpm_percent = (snapshot.requests_last_minute / self.limits.rpm * 100) if self.limits.rpm > 0 else 0
        rpd_percent = (snapshot.requests_today / self.limits.rpd * 100) if self.limits.rpd > 0 else 0

        return rpm_percent >= 90 or rpd_percent >= 90

    def can_make_request(self) -> tuple[bool, Optional[str]]:
        """
        Check if a new request can be made

        Returns:
            (can_proceed, reason_if_blocked)
        """
        snapshot = self.get_current_usage()

        if snapshot.requests_last_minute >= self.limits.rpm:
            return False, f"RPM limit exceeded ({self.limits.rpm}/min). Wait 60 seconds."

        if snapshot.requests_today >= self.limits.rpd:
            return False, f"Daily limit exceeded ({self.limits.rpd}/day). Resets at {snapshot.next_reset_time}"

        return True, None


# Global tracker instance
_global_tracker: Optional[APIUsageTracker] = None


def get_tracker() -> APIUsageTracker:
    """Get or create global API usage tracker"""
    global _global_tracker
    if _global_tracker is None:
        # Check for custom limits from environment
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        rpm = int(os.getenv("GEMINI_RPM_LIMIT", "10"))
        rpd = int(os.getenv("GEMINI_RPD_LIMIT", "1500"))
        tpm = int(os.getenv("GEMINI_TPM_LIMIT", "4000000"))

        limits = RateLimits(model=model, rpm=rpm, rpd=rpd, tpm=tpm)
        _global_tracker = APIUsageTracker(limits)

    return _global_tracker


def reset_tracker():
    """Reset global tracker (for testing)"""
    global _global_tracker
    _global_tracker = None
