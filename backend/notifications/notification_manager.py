"""
Unified Notification Manager for AI Trading System

Features:
- Centralized notification dispatch
- Multi-channel support (Telegram, Slack)
- Priority-based routing
- Settings persistence
- Statistics aggregation

Author: AI Trading System
Date: 2025-11-15
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path
import json

from .telegram_notifier import TelegramNotifier, AlertPriority, create_telegram_notifier
from .slack_notifier import SlackNotifier, create_slack_notifier

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Available notification channels"""
    TELEGRAM = "telegram"
    SLACK = "slack"
    ALL = "all"


class NotificationManager:
    """
    Centralized notification manager for all alert types.
    
    Features:
    - Route alerts to appropriate channels
    - Manage settings for all notifiers
    - Aggregate statistics
    - Filter based on priority and type
    """
    
    def __init__(
        self,
        telegram_notifier: Optional[TelegramNotifier] = None,
        slack_notifier: Optional[SlackNotifier] = None,
        settings_path: Optional[str] = None,
    ):
        """
        Initialize notification manager.
        
        Args:
            telegram_notifier: TelegramNotifier instance (or creates from env)
            slack_notifier: SlackNotifier instance (or creates from env)
            settings_path: Path to save/load settings
        """
        self.telegram = telegram_notifier or create_telegram_notifier()
        self.slack = slack_notifier or create_slack_notifier()
        
        self.settings_path = settings_path or "./config/notification_settings.json"
        
        # Alert history
        self._history: List[Dict[str, Any]] = []
        self._max_history = 1000
        
        # Load saved settings
        self._load_settings()
        
        logger.info(
            f"NotificationManager initialized: "
            f"Telegram={self.telegram.enabled}, Slack={self.slack.enabled}"
        )
    
    def _load_settings(self):
        """Load settings from file"""
        try:
            path = Path(self.settings_path)
            if path.exists():
                with open(path, "r") as f:
                    settings = json.load(f)
                
                # Apply Telegram settings
                if "telegram" in settings:
                    tg = settings["telegram"]
                    self.telegram.update_settings(
                        enabled=tg.get("enabled"),
                        min_priority=getattr(AlertPriority, tg.get("min_priority", "HIGH")),
                        rate_limit=tg.get("rate_limit_per_minute"),
                        throttle_minutes=tg.get("throttle_minutes"),
                    )
                
                # Apply Slack settings
                if "slack" in settings:
                    sl = settings["slack"]
                    self.slack.update_settings(
                        enabled=sl.get("enabled"),
                        rate_limit=sl.get("rate_limit_per_minute"),
                    )
                
                logger.info(f"Settings loaded from {self.settings_path}")
        except Exception as e:
            logger.warning(f"Could not load settings: {e}")
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            path = Path(self.settings_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            settings = {
                "telegram": {
                    "enabled": self.telegram.enabled,
                    "min_priority": self.telegram.min_priority.value,
                    "rate_limit_per_minute": self.telegram.rate_limit,
                    "throttle_minutes": self.telegram.throttle_minutes,
                },
                "slack": {
                    "enabled": self.slack.enabled,
                    "rate_limit_per_minute": self.slack.rate_limit,
                },
                "updated_at": datetime.now().isoformat(),
            }
            
            with open(path, "w") as f:
                json.dump(settings, f, indent=2)
            
            logger.info(f"Settings saved to {self.settings_path}")
        except Exception as e:
            logger.error(f"Could not save settings: {e}")
    
    def _record_alert(
        self,
        alert_type: str,
        channels: List[str],
        success: bool,
        priority: str,
        data: Dict[str, Any],
    ):
        """Record alert in history"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "alert_type": alert_type,
            "channels": channels,
            "success": success,
            "priority": priority,
            "data_summary": str(data)[:200],
        }
        
        self._history.append(record)
        
        # Trim history
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
    
    # =========================================================================
    # News Alerts
    # =========================================================================
    
    async def send_news_alert(
        self,
        analysis: Dict[str, Any],
        priority: str = "HIGH",
        channels: NotificationChannel = NotificationChannel.ALL,
    ) -> Dict[str, bool]:
        """
        Send news alert to specified channels.
        
        Args:
            analysis: NewsAnalysis data
            priority: Alert priority (LOW, MEDIUM, HIGH, CRITICAL)
            channels: Which channels to send to
            
        Returns:
            Dict with success status per channel
        """
        results = {}
        used_channels = []
        
        alert_priority = getattr(AlertPriority, priority, AlertPriority.HIGH)
        
        # Send to Telegram
        if channels in [NotificationChannel.TELEGRAM, NotificationChannel.ALL]:
            if self.telegram.enabled:
                success = await self.telegram.send_news_alert(analysis, alert_priority)
                results["telegram"] = success
                used_channels.append("telegram")
        
        # Send to Slack
        if channels in [NotificationChannel.SLACK, NotificationChannel.ALL]:
            if self.slack.enabled:
                success = await self.slack.send_news_alert(analysis, priority)
                results["slack"] = success
                used_channels.append("slack")
        
        # Record in history
        overall_success = any(results.values()) if results else False
        self._record_alert("NEWS", used_channels, overall_success, priority, analysis)
        
        logger.info(
            f"News alert sent: priority={priority}, channels={used_channels}, "
            f"results={results}"
        )
        
        return results
    
    async def send_trading_signal(
        self,
        signal: Dict[str, Any],
        priority: str = "HIGH",
        channels: NotificationChannel = NotificationChannel.ALL,
    ) -> Dict[str, bool]:
        """
        Send trading signal notification.
        
        Args:
            signal: TradingSignal data
            priority: Alert priority
            channels: Which channels to send to
            
        Returns:
            Dict with success status per channel
        """
        results = {}
        used_channels = []
        
        alert_priority = getattr(AlertPriority, priority, AlertPriority.HIGH)
        
        # Send to Telegram
        if channels in [NotificationChannel.TELEGRAM, NotificationChannel.ALL]:
            if self.telegram.enabled:
                success = await self.telegram.send_trading_signal(signal, alert_priority)
                results["telegram"] = success
                used_channels.append("telegram")
        
        # Send to Slack
        if channels in [NotificationChannel.SLACK, NotificationChannel.ALL]:
            if self.slack.enabled:
                success = await self.slack.send_trading_signal(signal, priority)
                results["slack"] = success
                used_channels.append("slack")
        
        # Record
        overall_success = any(results.values()) if results else False
        self._record_alert("SIGNAL", used_channels, overall_success, priority, signal)
        
        logger.info(
            f"Signal alert sent: {signal.get('ticker')} {signal.get('action')}, "
            f"channels={used_channels}, results={results}"
        )
        
        return results
    
    async def send_risk_warning(
        self,
        warning_type: str,
        details: Dict[str, Any],
        channels: NotificationChannel = NotificationChannel.ALL,
    ) -> Dict[str, bool]:
        """
        Send risk warning to all channels.
        
        Args:
            warning_type: Type of warning
            details: Warning details
            channels: Which channels to send to
            
        Returns:
            Dict with success status per channel
        """
        results = {}
        used_channels = []
        
        # Send to Telegram
        if channels in [NotificationChannel.TELEGRAM, NotificationChannel.ALL]:
            if self.telegram.enabled:
                success = await self.telegram.send_risk_warning(warning_type, details)
                results["telegram"] = success
                used_channels.append("telegram")
        
        # Send to Slack
        if channels in [NotificationChannel.SLACK, NotificationChannel.ALL]:
            if self.slack.enabled:
                success = await self.slack.send_risk_warning(warning_type, details)
                results["slack"] = success
                used_channels.append("slack")
        
        # Record
        overall_success = any(results.values()) if results else False
        self._record_alert("RISK_WARNING", used_channels, overall_success, "CRITICAL", details)
        
        logger.warning(
            f"Risk warning sent: {warning_type}, channels={used_channels}, "
            f"results={results}"
        )
        
        return results
    
    async def send_daily_summary(
        self,
        summary: Dict[str, Any],
        channels: NotificationChannel = NotificationChannel.TELEGRAM,
    ) -> Dict[str, bool]:
        """
        Send daily trading summary.
        
        Args:
            summary: Summary data
            channels: Which channels to send to
            
        Returns:
            Dict with success status per channel
        """
        results = {}
        
        if channels in [NotificationChannel.TELEGRAM, NotificationChannel.ALL]:
            if self.telegram.enabled:
                success = await self.telegram.send_daily_summary(summary)
                results["telegram"] = success
        
        return results
    
    async def send_test_notification(
        self,
        channels: NotificationChannel = NotificationChannel.ALL,
    ) -> Dict[str, bool]:
        """
        Send test notification to verify setup.
        
        Args:
            channels: Which channels to test
            
        Returns:
            Dict with success status per channel
        """
        results = {}
        
        if channels in [NotificationChannel.TELEGRAM, NotificationChannel.ALL]:
            if self.telegram.enabled:
                success = await self.telegram.send_test_notification()
                results["telegram"] = success
        
        if channels in [NotificationChannel.SLACK, NotificationChannel.ALL]:
            if self.slack.enabled:
                success = await self.slack.send_test_notification()
                results["slack"] = success
        
        logger.info(f"Test notifications sent: {results}")
        return results
    
    # =========================================================================
    # Settings Management
    # =========================================================================
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings for all channels"""
        return {
            "telegram": {
                "enabled": self.telegram.enabled,
                "min_priority": self.telegram.min_priority.value,
                "rate_limit_per_minute": self.telegram.rate_limit,
                "throttle_minutes": self.telegram.throttle_minutes,
            },
            "slack": {
                "enabled": self.slack.enabled,
                "rate_limit_per_minute": self.slack.rate_limit,
            },
        }
    
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Update settings for all channels.
        
        Args:
            settings: Dictionary with channel settings
                {
                    "telegram": {"enabled": bool, "min_priority": str, ...},
                    "slack": {"enabled": bool, ...}
                }
                
        Returns:
            True if successful
        """
        try:
            if "telegram" in settings:
                tg = settings["telegram"]
                min_priority = None
                if "min_priority" in tg:
                    min_priority = getattr(AlertPriority, tg["min_priority"], None)
                
                self.telegram.update_settings(
                    enabled=tg.get("enabled"),
                    min_priority=min_priority,
                    rate_limit=tg.get("rate_limit_per_minute"),
                    throttle_minutes=tg.get("throttle_minutes"),
                )
            
            if "slack" in settings:
                sl = settings["slack"]
                self.slack.update_settings(
                    enabled=sl.get("enabled"),
                    rate_limit=sl.get("rate_limit_per_minute"),
                )
            
            # Save to file
            self.save_settings()
            
            logger.info("Notification settings updated")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregated statistics"""
        
        # Count history by type
        alert_counts = {
            "NEWS": 0,
            "SIGNAL": 0,
            "RISK_WARNING": 0,
        }
        success_counts = {
            "NEWS": 0,
            "SIGNAL": 0,
            "RISK_WARNING": 0,
        }
        
        for record in self._history:
            alert_type = record.get("alert_type", "")
            if alert_type in alert_counts:
                alert_counts[alert_type] += 1
                if record.get("success"):
                    success_counts[alert_type] += 1
        
        return {
            "telegram": self.telegram.get_stats(),
            "slack": self.slack.get_stats(),
            "history_size": len(self._history),
            "alert_counts": alert_counts,
            "success_counts": success_counts,
            "overall_success_rate": (
                sum(success_counts.values()) / sum(alert_counts.values())
                if sum(alert_counts.values()) > 0
                else 0.0
            ),
        }
    
    def get_alert_history(
        self,
        limit: int = 50,
        alert_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent alert history.
        
        Args:
            limit: Maximum number of records
            alert_type: Filter by type (NEWS, SIGNAL, RISK_WARNING)
            
        Returns:
            List of alert records
        """
        history = self._history
        
        if alert_type:
            history = [h for h in history if h.get("alert_type") == alert_type]
        
        return history[-limit:]
    
    def clear_history(self):
        """Clear alert history"""
        self._history = []
        logger.info("Alert history cleared")


# ============================================================================
# Factory function
# ============================================================================

def create_notification_manager(
    settings_path: Optional[str] = None,
) -> NotificationManager:
    """
    Create NotificationManager with notifiers from environment variables.
    
    Args:
        settings_path: Path to settings file
        
    Returns:
        Configured NotificationManager instance
    """
    return NotificationManager(
        telegram_notifier=create_telegram_notifier(),
        slack_notifier=create_slack_notifier(),
        settings_path=settings_path or "./config/notification_settings.json",
    )


# ============================================================================
# Convenience function for quick alerts
# ============================================================================

_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get global NotificationManager instance (singleton pattern)"""
    global _manager
    if _manager is None:
        _manager = create_notification_manager()
    return _manager


async def quick_news_alert(analysis: Dict[str, Any], priority: str = "HIGH"):
    """Quick function to send news alert"""
    manager = get_notification_manager()
    return await manager.send_news_alert(analysis, priority)


async def quick_signal_alert(signal: Dict[str, Any], priority: str = "HIGH"):
    """Quick function to send signal alert"""
    manager = get_notification_manager()
    return await manager.send_trading_signal(signal, priority)


async def quick_risk_warning(warning_type: str, details: Dict[str, Any]):
    """Quick function to send risk warning"""
    manager = get_notification_manager()
    return await manager.send_risk_warning(warning_type, details)
