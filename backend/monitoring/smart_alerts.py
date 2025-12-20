"""
Smart Alert System - Intelligent alert filtering and prioritization

Features:
- Alert prioritization (Critical, High, Medium, Low)
- Alert deduplication (prevent spam)
- Rate limiting per alert type
- Smart filtering (only actionable alerts)
- Alert aggregation (batch similar alerts)
- Quiet hours support

Author: AI Trading System Team
Date: 2025-11-24
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels."""
    CRITICAL = 1  # Immediate action required
    HIGH = 2      # Action needed soon
    MEDIUM = 3    # Informational, action optional
    LOW = 4       # Nice to know


class AlertCategory(Enum):
    """Alert categories for filtering."""
    SYSTEM_ERROR = "system_error"
    TRADING_SIGNAL = "trading_signal"
    RISK_WARNING = "risk_warning"
    PORTFOLIO_UPDATE = "portfolio_update"
    DATA_QUALITY = "data_quality"
    COST_ALERT = "cost_alert"
    PERFORMANCE = "performance"


@dataclass
class Alert:
    """Represents a single alert."""
    category: AlertCategory
    priority: AlertPriority
    title: str
    message: str
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)
    alert_id: Optional[str] = None

    def __post_init__(self):
        if not self.alert_id:
            # Generate unique ID based on category + message hash
            self.alert_id = f"{self.category.value}_{hash(self.message) % 10000:04d}"

    def to_dict(self) -> Dict:
        return {
            "id": self.alert_id,
            "category": self.category.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class AlertRule:
    """Configuration for alert filtering and routing."""
    category: AlertCategory
    min_priority: AlertPriority
    max_per_hour: int = 10
    dedupe_window_minutes: int = 60
    quiet_hours: bool = True
    enabled: bool = True


class SmartAlertManager:
    """
    Intelligent alert manager with filtering and prioritization.

    Features:
    - Deduplication: Prevent duplicate alerts within time window
    - Rate limiting: Limit alerts per category per time period
    - Priority-based routing: Critical alerts bypass filters
    - Quiet hours: Suppress low-priority alerts during configured hours
    - Alert aggregation: Batch similar alerts
    """

    def __init__(
        self,
        telegram_bot = None,
        slack_client = None,
        quiet_hours_start: int = 22,  # 10 PM
        quiet_hours_end: int = 7,     # 7 AM
    ):
        self.telegram = telegram_bot
        self.slack = slack_client
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end

        # Alert tracking
        self.recent_alerts: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alert_counts: Dict[str, int] = defaultdict(int)
        self.last_alert_time: Dict[str, datetime] = {}

        # Alert rules
        self.rules: Dict[AlertCategory, AlertRule] = self._default_rules()

        # Pending aggregated alerts
        self.pending_aggregated: Dict[str, List[Alert]] = defaultdict(list)

        logger.info("SmartAlertManager initialized")

    def _default_rules(self) -> Dict[AlertCategory, AlertRule]:
        """Default alert rules."""
        return {
            AlertCategory.SYSTEM_ERROR: AlertRule(
                category=AlertCategory.SYSTEM_ERROR,
                min_priority=AlertPriority.HIGH,
                max_per_hour=5,
                dedupe_window_minutes=30,
                quiet_hours=False,  # Always send
            ),
            AlertCategory.TRADING_SIGNAL: AlertRule(
                category=AlertCategory.TRADING_SIGNAL,
                min_priority=AlertPriority.MEDIUM,
                max_per_hour=20,
                dedupe_window_minutes=15,
                quiet_hours=True,
            ),
            AlertCategory.RISK_WARNING: AlertRule(
                category=AlertCategory.RISK_WARNING,
                min_priority=AlertPriority.HIGH,
                max_per_hour=10,
                dedupe_window_minutes=60,
                quiet_hours=False,
            ),
            AlertCategory.PORTFOLIO_UPDATE: AlertRule(
                category=AlertCategory.PORTFOLIO_UPDATE,
                min_priority=AlertPriority.LOW,
                max_per_hour=4,  # Every 15 min max
                dedupe_window_minutes=15,
                quiet_hours=True,
            ),
            AlertCategory.DATA_QUALITY: AlertRule(
                category=AlertCategory.DATA_QUALITY,
                min_priority=AlertPriority.MEDIUM,
                max_per_hour=5,
                dedupe_window_minutes=120,
                quiet_hours=True,
            ),
            AlertCategory.COST_ALERT: AlertRule(
                category=AlertCategory.COST_ALERT,
                min_priority=AlertPriority.MEDIUM,
                max_per_hour=2,
                dedupe_window_minutes=360,  # 6 hours
                quiet_hours=True,
            ),
            AlertCategory.PERFORMANCE: AlertRule(
                category=AlertCategory.PERFORMANCE,
                min_priority=AlertPriority.LOW,
                max_per_hour=3,
                dedupe_window_minutes=120,
                quiet_hours=True,
            ),
        }

    def update_rule(self, rule: AlertRule):
        """Update an alert rule."""
        self.rules[rule.category] = rule
        logger.info(f"Updated alert rule for {rule.category.value}")

    async def send_alert(
        self,
        category: AlertCategory,
        priority: AlertPriority,
        title: str,
        message: str,
        metadata: Optional[Dict] = None,
        force: bool = False,
    ) -> bool:
        """
        Send an alert with smart filtering.

        Args:
            category: Alert category
            priority: Alert priority
            title: Alert title
            message: Alert message
            metadata: Additional metadata
            force: Force send, bypass all filters

        Returns:
            True if alert was sent, False if filtered
        """
        alert = Alert(
            category=category,
            priority=priority,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        # Store in recent alerts
        self.recent_alerts[category.value].append(alert)

        # Force send bypasses all filters
        if force:
            await self._send_to_channels(alert)
            return True

        # Apply filters
        if not self._should_send_alert(alert):
            logger.debug(f"Alert filtered: {alert.alert_id}")
            return False

        # Send alert
        await self._send_to_channels(alert)
        self.last_alert_time[alert.alert_id] = datetime.utcnow()
        self.alert_counts[category.value] += 1

        return True

    def _should_send_alert(self, alert: Alert) -> bool:
        """Apply filtering logic."""
        rule = self.rules.get(alert.category)
        if not rule or not rule.enabled:
            return False

        # Priority check
        if alert.priority.value > rule.min_priority.value:
            return False

        # Critical alerts always go through
        if alert.priority == AlertPriority.CRITICAL:
            return True

        # Quiet hours check
        if rule.quiet_hours and self._is_quiet_hours():
            if alert.priority.value > AlertPriority.HIGH.value:
                return False

        # Deduplication check
        if self._is_duplicate(alert, rule.dedupe_window_minutes):
            return False

        # Rate limit check
        if self._is_rate_limited(alert.category, rule.max_per_hour):
            return False

        return True

    def _is_quiet_hours(self) -> bool:
        """Check if currently in quiet hours."""
        now = datetime.now()
        current_hour = now.hour

        if self.quiet_hours_start < self.quiet_hours_end:
            # Normal case: 22-7 (10 PM to 7 AM)
            return self.quiet_hours_start <= current_hour < self.quiet_hours_end
        else:
            # Wraps around midnight: 23-2 (11 PM to 2 AM)
            return current_hour >= self.quiet_hours_start or current_hour < self.quiet_hours_end

    def _is_duplicate(self, alert: Alert, window_minutes: int) -> bool:
        """Check if alert is duplicate within time window."""
        if alert.alert_id not in self.last_alert_time:
            return False

        last_time = self.last_alert_time[alert.alert_id]
        time_diff = (datetime.utcnow() - last_time).total_seconds() / 60

        return time_diff < window_minutes

    def _is_rate_limited(self, category: AlertCategory, max_per_hour: int) -> bool:
        """Check if alert category is rate limited."""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)

        # Count recent alerts in this category
        recent = self.recent_alerts[category.value]
        count = sum(1 for a in recent if a.timestamp > one_hour_ago)

        return count >= max_per_hour

    async def _send_to_channels(self, alert: Alert):
        """Send alert to configured channels."""
        formatted_message = self._format_alert(alert)

        # Send to Telegram
        if self.telegram:
            try:
                await self.telegram.send_message(formatted_message)
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")

        # Send to Slack
        if self.slack:
            try:
                await self.slack.send_message(formatted_message)
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")

        logger.info(f"Alert sent: {alert.category.value} - {alert.title}")

    def _format_alert(self, alert: Alert) -> str:
        """Format alert for human readability."""
        emoji = self._get_priority_emoji(alert.priority)
        category_emoji = self._get_category_emoji(alert.category)

        lines = [
            f"{emoji} {category_emoji} **{alert.title}**",
            f"",
            f"{alert.message}",
        ]

        # Add metadata if present
        if alert.metadata:
            lines.append("")
            lines.append("📊 **Details:**")
            for key, value in alert.metadata.items():
                lines.append(f"  • {key}: {value}")

        lines.append("")
        lines.append(f"⏰ {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        return "\n".join(lines)

    def _get_priority_emoji(self, priority: AlertPriority) -> str:
        """Get emoji for priority level."""
        return {
            AlertPriority.CRITICAL: "🚨",
            AlertPriority.HIGH: "⚠️",
            AlertPriority.MEDIUM: "ℹ️",
            AlertPriority.LOW: "💬",
        }.get(priority, "📢")

    def _get_category_emoji(self, category: AlertCategory) -> str:
        """Get emoji for alert category."""
        return {
            AlertCategory.SYSTEM_ERROR: "💥",
            AlertCategory.TRADING_SIGNAL: "📈",
            AlertCategory.RISK_WARNING: "⚡",
            AlertCategory.PORTFOLIO_UPDATE: "💼",
            AlertCategory.DATA_QUALITY: "📊",
            AlertCategory.COST_ALERT: "💰",
            AlertCategory.PERFORMANCE: "⚡",
        }.get(category, "📢")

    # =============================================================================
    # Convenience Methods
    # =============================================================================

    async def alert_critical_error(self, error: str, details: Optional[Dict] = None):
        """Send critical system error alert."""
        await self.send_alert(
            category=AlertCategory.SYSTEM_ERROR,
            priority=AlertPriority.CRITICAL,
            title="Critical System Error",
            message=error,
            metadata=details,
            force=True,  # Critical errors always go through
        )

    async def alert_trading_signal(
        self,
        ticker: str,
        signal: str,
        confidence: float,
        details: Optional[Dict] = None,
    ):
        """Send trading signal alert."""
        priority = AlertPriority.HIGH if confidence >= 0.8 else AlertPriority.MEDIUM

        await self.send_alert(
            category=AlertCategory.TRADING_SIGNAL,
            priority=priority,
            title=f"Trading Signal: {signal} {ticker}",
            message=f"Signal: {signal} | Confidence: {confidence:.1%}",
            metadata=details or {"ticker": ticker, "confidence": confidence},
        )

    async def alert_risk_warning(
        self,
        ticker: str,
        risk_type: str,
        risk_score: float,
        message: str,
    ):
        """Send risk warning alert."""
        priority = AlertPriority.CRITICAL if risk_score >= 0.8 else AlertPriority.HIGH

        await self.send_alert(
            category=AlertCategory.RISK_WARNING,
            priority=priority,
            title=f"Risk Warning: {ticker}",
            message=message,
            metadata={
                "ticker": ticker,
                "risk_type": risk_type,
                "risk_score": risk_score,
            },
        )

    async def alert_portfolio_update(
        self,
        daily_pnl: float,
        total_value: float,
        details: Optional[Dict] = None,
    ):
        """Send portfolio update alert."""
        # Only alert if significant change
        pnl_pct = (daily_pnl / total_value) * 100

        if abs(pnl_pct) < 1.0:
            return  # < 1% change, don't alert

        priority = AlertPriority.HIGH if abs(pnl_pct) >= 5.0 else AlertPriority.MEDIUM

        await self.send_alert(
            category=AlertCategory.PORTFOLIO_UPDATE,
            priority=priority,
            title=f"Portfolio Update: {pnl_pct:+.2f}%",
            message=f"Daily P&L: ${daily_pnl:,.2f} ({pnl_pct:+.2f}%)\nTotal Value: ${total_value:,.2f}",
            metadata=details,
        )

    async def alert_high_cost(
        self,
        service: str,
        cost_usd: float,
        threshold_usd: float,
    ):
        """Send cost alert."""
        await self.send_alert(
            category=AlertCategory.COST_ALERT,
            priority=AlertPriority.HIGH,
            title=f"High Cost Alert: {service}",
            message=f"Cost ${cost_usd:.2f} exceeded threshold ${threshold_usd:.2f}",
            metadata={"service": service, "cost": cost_usd, "threshold": threshold_usd},
        )

    def get_statistics(self) -> Dict:
        """Get alert statistics."""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        twenty_four_hours_ago = now - timedelta(days=1)

        stats = {
            "total_alerts_sent": sum(self.alert_counts.values()),
            "alerts_by_category": dict(self.alert_counts),
            "alerts_last_hour": {},
            "alerts_last_24h": {},
            "currently_in_quiet_hours": self._is_quiet_hours(),
        }

        for category, alerts in self.recent_alerts.items():
            stats["alerts_last_hour"][category] = sum(
                1 for a in alerts if a.timestamp > one_hour_ago
            )
            stats["alerts_last_24h"][category] = sum(
                1 for a in alerts if a.timestamp > twenty_four_hours_ago
            )

        return stats
