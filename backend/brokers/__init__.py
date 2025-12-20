"""
Brokers Module

Integration with real brokers for live trading.

Components:
- KISBroker: Korea Investment & Securities broker

Author: AI Trading System Team
Date: 2025-11-15
"""

from .kis_broker import KISBroker

__all__ = [
    "KISBroker",
]

__version__ = "1.0.0"
__author__ = "AI Trading System Team"
