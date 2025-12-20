"""
Trading Signals Module

Components:
- NewsSignalGenerator: Generate trading signals from news analysis
- SignalValidator: Validate and filter trading signals
- SectorThrottlingManager: Manage sector position limits
"""

from .news_signal_generator import NewsSignalGenerator, TradingSignal, SignalAction
from .signal_validator import SignalValidator

try:
    from .sector_throttling import SectorThrottlingManager
    SECTOR_THROTTLING_AVAILABLE = True
except ImportError:
    SECTOR_THROTTLING_AVAILABLE = False
    SectorThrottlingManager = None

__all__ = [
    "NewsSignalGenerator",
    "TradingSignal",
    "SignalAction",
    "SignalValidator",
    "SectorThrottlingManager",
]
