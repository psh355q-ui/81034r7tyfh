"""
Alert Manager - Multi-channel Alerting System

Manages alerts and notifications across multiple channels.

Features:
- Priority-based alerting (LOW, MEDIUM, HIGH, CRITICAL)
- Category-based routing (SYSTEM, TRADING, RISK, PERFORMANCE)
- Multi-channel delivery (Slack, Email, Console)
- Alert throttling and deduplication
- Alert history tracking

Channels:
- Slack: Webhooks for team notifications
- Email: SMTP for critical alerts
- Console: Logging for development

Author: AI Trading System Team
Date: 2025-11-14
"""

import os
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
import json

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Alert categories for routing."""
    SYSTEM = "system"
    TRADING = "trading"
    RISK = "risk"
    PERFORMANCE = "performance"
    AI = "ai"


@dataclass
class Alert:
    """Alert data structure."""
    level: AlertLevel
    category: AlertCategory
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Optional[Dict] = None
    sent_channels: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "category": self.category.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "sent_channels": self.sent_channels,
        }


class AlertManager:
    """
    Manages system alerts and notifications.

    Features:
    - Multi-channel delivery
    - Alert throttling
    - Priority-based routing
    - History tracking
    """

    def __init__(
        self,
        slack_webhook_url: Optional[str] = None,
        email_config: Optional[Dict] = None,
        throttle_seconds: int = 300,  # 5 minutes default
    ):
        self.slack_webhook_url = slack_webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.email_config = email_config or {}
        self.throttle_seconds = throttle_seconds

        # Alert history
        self.alert_history: List[Alert] = []
        self._last_alert_times: Dict[str, datetime] = {}

        # Stats
        self.stats = {
            "total_alerts": 0,
            "by_level": {level.value: 0 for level in AlertLevel},
            "by_category": {cat.value: 0 for cat in AlertCategory},
            "throttled": 0,
        }

        logger.info("Alert Manager initialized")
        if self.slack_webhook_url:
            logger.info("Slack webhook configured")
        if self.email_config:
            logger.info("Email configured")

    async def send_alert(
        self,
        level: AlertLevel,
        category: AlertCategory,
        title: str,
        message: str,
        data: Optional[Dict] = None,
    ) -> Optional[Alert]:
        """
        Send an alert through configured channels.

        Args:
            level: Alert priority level
            category: Alert category for routing
            title: Alert title
            message: Alert message
            data: Optional additional data

        Returns:
            Alert object if sent, None if throttled
        """
        # Check throttling
        throttle_key = f"{level.value}_{category.value}_{title}"
        if self._is_throttled(throttle_key):
            self.stats["throttled"] += 1
            logger.debug(f"Alert throttled: {title}")
            return None

        # Create alert
        alert = Alert(
            level=level,
            category=category,
            title=title,
            message=message,
            data=data,
        )

        # Update stats
        self.stats["total_alerts"] += 1
        self.stats["by_level"][level.value] += 1
        self.stats["by_category"][category.value] += 1

        # Send through channels
        channels_sent = []

        # Console (always)
        self._send_to_console(alert)
        channels_sent.append("console")

        # Slack
        if self.slack_webhook_url:
            try:
                await self._send_to_slack(alert)
                channels_sent.append("slack")
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")

        # Email (for HIGH and CRITICAL only)
        if self.email_config and level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
            try:
                await self._send_to_email(alert)
                channels_sent.append("email")
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")

        alert.sent_channels = channels_sent

        # Store in history (keep last 1000)
        self.alert_history.append(alert)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

        # Update throttle time
        self._last_alert_times[throttle_key] = datetime.utcnow()

        logger.info(f"Alert sent: [{level.value}] {title}")
        return alert

    def _is_throttled(self, throttle_key: str) -> bool:
        """Check if alert should be throttled."""
        if throttle_key not in self._last_alert_times:
            return False

        last_time = self._last_alert_times[throttle_key]
        elapsed = (datetime.utcnow() - last_time).total_seconds()
        return elapsed < self.throttle_seconds

    def _send_to_console(self, alert: Alert):
        """Send alert to console/logs."""
        level_map = {
            AlertLevel.LOW: logging.INFO,
            AlertLevel.MEDIUM: logging.INFO,
            AlertLevel.HIGH: logging.WARNING,
            AlertLevel.CRITICAL: logging.ERROR,
        }

        log_level = level_map.get(alert.level, logging.INFO)
        logger.log(
            log_level,
            f"[{alert.category.value.upper()}] {alert.title}: {alert.message}"
        )

    async def _send_to_slack(self, alert: Alert):
        """Send alert to Slack via webhook."""
        if not self.slack_webhook_url:
            return

        # Color based on level
        color_map = {
            AlertLevel.LOW: "#36a64f",       # Green
            AlertLevel.MEDIUM: "#ff9900",    # Orange
            AlertLevel.HIGH: "#ff0000",      # Red
            AlertLevel.CRITICAL: "#8b0000",  # Dark red
        }

        payload = {
            "attachments": [{
                "color": color_map.get(alert.level, "#808080"),
                "title": f"[{alert.level.value.upper()}] {alert.title}",
                "text": alert.message,
                "fields": [
                    {
                        "title": "Category",
                        "value": alert.category.value.upper(),
                        "short": True
                    },
                    {
                        "title": "Time",
                        "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "short": True
                    }
                ],
                "footer": "AI Trading System",
                "ts": int(alert.timestamp.timestamp())
            }]
        }

        # Add data fields if present
        if alert.data:
            for key, value in alert.data.items():
                payload["attachments"][0]["fields"].append({
                    "title": key,
                    "value": str(value),
                    "short": True
                })

        # Send webhook (mock for now)
        logger.debug(f"Slack payload: {json.dumps(payload, indent=2)}")
        # In production: await httpx.post(self.slack_webhook_url, json=payload)

    async def _send_to_email(self, alert: Alert):
        """Send alert via email."""
        if not self.email_config:
            return

        # Email template
        subject = f"[{alert.level.value.upper()}] {alert.title}"
        body = f"""
AI Trading System Alert

Level: {alert.level.value.upper()}
Category: {alert.category.value.upper()}
Time: {alert.timestamp.isoformat()}

{alert.message}
"""

        if alert.data:
            body += "\n\nAdditional Data:\n"
            for key, value in alert.data.items():
                body += f"  {key}: {value}\n"

        logger.debug(f"Email: {subject}")
        logger.debug(f"Body: {body}")
        # In production: send via SMTP

    # ===== Convenience Methods =====

    async def alert_system_error(self, error_message: str, error_type: str = "Unknown"):
        """Send system error alert."""
        return await self.send_alert(
            level=AlertLevel.HIGH,
            category=AlertCategory.SYSTEM,
            title="System Error",
            message=error_message,
            data={"error_type": error_type},
        )

    async def alert_kill_switch_activated(self, reason: str):
        """Send kill switch activation alert."""
        return await self.send_alert(
            level=AlertLevel.CRITICAL,
            category=AlertCategory.RISK,
            title="Kill Switch Activated",
            message=f"Trading has been halted. Reason: {reason}",
            data={"reason": reason},
        )

    async def alert_daily_loss_limit(self, current_loss: float, limit: float):
        """Send daily loss limit alert."""
        return await self.send_alert(
            level=AlertLevel.CRITICAL,
            category=AlertCategory.RISK,
            title="Daily Loss Limit Reached",
            message=f"Daily loss of ${current_loss:.2f} has reached limit of ${limit:.2f}",
            data={"current_loss": current_loss, "limit": limit},
        )

    async def alert_high_slippage(self, ticker: str, slippage_bps: float):
        """Send high slippage alert."""
        return await self.send_alert(
            level=AlertLevel.MEDIUM,
            category=AlertCategory.PERFORMANCE,
            title="High Execution Slippage",
            message=f"{ticker}: Execution slippage of {slippage_bps:.2f} bps exceeds normal range",
            data={"ticker": ticker, "slippage_bps": slippage_bps},
        )

    async def alert_ai_cost_warning(self, daily_cost: float, limit: float):
        """Send AI cost warning alert."""
        return await self.send_alert(
            level=AlertLevel.MEDIUM,
            category=AlertCategory.AI,
            title="High AI Cost",
            message=f"Daily AI cost of ${daily_cost:.2f} approaching limit of ${limit:.2f}",
            data={"daily_cost": daily_cost, "limit": limit},
        )

    async def alert_trade_executed(
        self,
        ticker: str,
        action: str,
        shares: int,
        price: float,
    ):
        """Send trade execution notification."""
        return await self.send_alert(
            level=AlertLevel.LOW,
            category=AlertCategory.TRADING,
            title=f"Trade Executed: {ticker}",
            message=f"{action} {shares} shares at ${price:.2f}",
            data={
                "ticker": ticker,
                "action": action,
                "shares": shares,
                "price": price,
            },
        )

    async def alert_position_closed(
        self,
        ticker: str,
        pnl: float,
        return_pct: float,
    ):
        """Send position closed notification."""
        level = AlertLevel.LOW if pnl >= 0 else AlertLevel.MEDIUM

        return await self.send_alert(
            level=level,
            category=AlertCategory.TRADING,
            title=f"Position Closed: {ticker}",
            message=f"P&L: ${pnl:.2f} ({return_pct:+.2f}%)",
            data={
                "ticker": ticker,
                "pnl": pnl,
                "return_pct": return_pct,
            },
        )

    def get_summary(self) -> Dict:
        """Get alert manager summary."""
        recent_alerts = self.alert_history[-10:]  # Last 10 alerts

        return {
            "stats": self.stats,
            "recent_alerts": [alert.to_dict() for alert in recent_alerts],
            "channels": {
                "slack": self.slack_webhook_url is not None,
                "email": bool(self.email_config),
            },
            "throttle_seconds": self.throttle_seconds,
        }

    def get_alerts_by_level(self, level: AlertLevel, limit: int = 20) -> List[Alert]:
        """Get recent alerts by level."""
        return [
            alert for alert in self.alert_history[-limit:]
            if alert.level == level
        ]

    def get_alerts_by_category(self, category: AlertCategory, limit: int = 20) -> List[Alert]:
        """Get recent alerts by category."""
        return [
            alert for alert in self.alert_history[-limit:]
            if alert.category == category
        ]
