"""
Notifications Module

Real-time trading alerts via multiple channels.

Components:
- TelegramNotifier: Telegram Bot integration
- NotificationManager: Trading system integration

Author: AI Trading System Team
Date: 2025-11-15
"""

from .telegram_notifier import TelegramNotifier
from .notification_manager import NotificationManager

__all__ = [
    "TelegramNotifier",
    "NotificationManager",
]

__version__ = "1.0.0"
__author__ = "AI Trading System Team"
