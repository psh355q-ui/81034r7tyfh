"""
Sector-Based Signal Throttling System

Features:
- Prevents overconcentration in single sector
- Tracks signals per sector with time windows
- Configurable limits per sector
- Correlation-based risk detection

This prevents scenarios where multiple news articles about the same topic
(e.g., "Semiconductor subsidies") generate 10+ BUY signals for related stocks,
causing dangerous sector overexposure.

Author: AI Trading System
Date: 2025-11-15
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class SectorThrottleConfig:
    """Configuration for sector-based throttling"""
    
    # Maximum trades per sector per time window
    max_trades_per_sector_per_hour: int = 3
    max_trades_per_sector_per_day: int = 10
    
    # Time windows
    hourly_window_minutes: int = 60
    daily_window_hours: int = 24
    
    # Overall limits
    max_total_trades_per_hour: int = 10
    max_total_trades_per_day: int = 30
    
    # Sector correlation limits
    max_correlated_sectors_per_day: int = 5  # Limit highly correlated sector trades
    
    # Emergency brake
    enable_emergency_brake: bool = True
    emergency_brake_threshold: float = 0.3  # 30% portfolio in one sector = stop


# Default sector groupings (can be extended)
SECTOR_MAPPING: Dict[str, str] = {
    # Technology
    "AAPL": "TECHNOLOGY",
    "MSFT": "TECHNOLOGY",
    "GOOGL": "TECHNOLOGY",
    "META": "TECHNOLOGY",
    "AMZN": "TECHNOLOGY",
    
    # Semiconductors
    "NVDA": "SEMICONDUCTORS",
    "AMD": "SEMICONDUCTORS",
    "INTC": "SEMICONDUCTORS",
    "QCOM": "SEMICONDUCTORS",
    "AVGO": "SEMICONDUCTORS",
    "TSM": "SEMICONDUCTORS",
    "ASML": "SEMICONDUCTORS",
    
    # Finance
    "JPM": "FINANCE",
    "BAC": "FINANCE",
    "GS": "FINANCE",
    "MS": "FINANCE",
    "WFC": "FINANCE",
    
    # Healthcare
    "JNJ": "HEALTHCARE",
    "UNH": "HEALTHCARE",
    "PFE": "HEALTHCARE",
    "MRK": "HEALTHCARE",
    "ABBV": "HEALTHCARE",
    
    # Energy
    "XOM": "ENERGY",
    "CVX": "ENERGY",
    "COP": "ENERGY",
    "SLB": "ENERGY",
    
    # Consumer
    "WMT": "CONSUMER_STAPLES",
    "KO": "CONSUMER_STAPLES",
    "PG": "CONSUMER_STAPLES",
    "COST": "CONSUMER_STAPLES",
    
    # Industrial
    "BA": "INDUSTRIAL",
    "CAT": "INDUSTRIAL",
    "GE": "INDUSTRIAL",
    "HON": "INDUSTRIAL",
}


# Correlated sector pairs (trade in one affects the other)
CORRELATED_SECTORS: Dict[str, List[str]] = {
    "SEMICONDUCTORS": ["TECHNOLOGY"],
    "TECHNOLOGY": ["SEMICONDUCTORS", "CONSUMER_DISCRETIONARY"],
    "ENERGY": ["INDUSTRIAL"],
    "FINANCE": ["REAL_ESTATE"],
}


# ============================================================================
# Signal Tracking
# ============================================================================

@dataclass
class SignalRecord:
    """Record of a generated signal"""
    ticker: str
    sector: str
    action: str  # BUY, SELL
    timestamp: datetime
    confidence: float
    news_source_id: Optional[int] = None
    executed: bool = False


@dataclass
class ThrottleDecision:
    """Decision from throttle system"""
    allowed: bool
    reason: str
    sector: str
    current_count_hourly: int
    current_count_daily: int
    limit_hourly: int
    limit_daily: int
    recommendation: str = ""


class SectorSignalTracker:
    """
    Tracks signal generation per sector with time-based windows.
    """
    
    def __init__(self, config: Optional[SectorThrottleConfig] = None):
        self.config = config or SectorThrottleConfig()
        
        # Signal history
        self._signals: List[SignalRecord] = []
        
        # Statistics
        self.stats = {
            "total_signals": 0,
            "throttled_signals": 0,
            "executed_signals": 0,
            "throttle_by_sector": defaultdict(int),
        }
        
        logger.info(
            f"SectorSignalTracker initialized: "
            f"max {self.config.max_trades_per_sector_per_hour}/hour, "
            f"{self.config.max_trades_per_sector_per_day}/day per sector"
        )
    
    def get_ticker_sector(self, ticker: str) -> str:
        """Get sector for a ticker"""
        return SECTOR_MAPPING.get(ticker.upper(), "UNKNOWN")
    
    def can_generate_signal(
        self,
        ticker: str,
        action: str,
        sectors_from_news: Optional[List[str]] = None,
    ) -> ThrottleDecision:
        """
        Check if a new signal for this ticker should be allowed.
        
        Args:
            ticker: Stock symbol
            action: BUY or SELL
            sectors_from_news: Sectors mentioned in the news analysis
            
        Returns:
            ThrottleDecision with allow/deny and reason
        """
        now = datetime.now()
        
        # 1. Determine sector
        sector = self.get_ticker_sector(ticker)
        if sectors_from_news and len(sectors_from_news) > 0:
            # Use sector from news analysis if available
            sector = sectors_from_news[0].upper()
        
        # 2. Count signals in time windows
        hourly_cutoff = now - timedelta(minutes=self.config.hourly_window_minutes)
        daily_cutoff = now - timedelta(hours=self.config.daily_window_hours)
        
        hourly_sector_count = sum(
            1 for s in self._signals
            if s.sector == sector and s.timestamp >= hourly_cutoff
        )
        
        daily_sector_count = sum(
            1 for s in self._signals
            if s.sector == sector and s.timestamp >= daily_cutoff
        )
        
        hourly_total_count = sum(
            1 for s in self._signals
            if s.timestamp >= hourly_cutoff
        )
        
        daily_total_count = sum(
            1 for s in self._signals
            if s.timestamp >= daily_cutoff
        )
        
        # 3. Check limits
        
        # Check hourly sector limit
        if hourly_sector_count >= self.config.max_trades_per_sector_per_hour:
            self.stats["throttled_signals"] += 1
            self.stats["throttle_by_sector"][sector] += 1
            return ThrottleDecision(
                allowed=False,
                reason=f"Sector hourly limit reached: {sector}",
                sector=sector,
                current_count_hourly=hourly_sector_count,
                current_count_daily=daily_sector_count,
                limit_hourly=self.config.max_trades_per_sector_per_hour,
                limit_daily=self.config.max_trades_per_sector_per_day,
                recommendation=f"Wait {self.config.hourly_window_minutes} minutes or diversify to other sectors",
            )
        
        # Check daily sector limit
        if daily_sector_count >= self.config.max_trades_per_sector_per_day:
            self.stats["throttled_signals"] += 1
            self.stats["throttle_by_sector"][sector] += 1
            return ThrottleDecision(
                allowed=False,
                reason=f"Sector daily limit reached: {sector}",
                sector=sector,
                current_count_hourly=hourly_sector_count,
                current_count_daily=daily_sector_count,
                limit_hourly=self.config.max_trades_per_sector_per_hour,
                limit_daily=self.config.max_trades_per_sector_per_day,
                recommendation=f"Daily limit for {sector} reached. Resume tomorrow.",
            )
        
        # Check total hourly limit
        if hourly_total_count >= self.config.max_total_trades_per_hour:
            self.stats["throttled_signals"] += 1
            return ThrottleDecision(
                allowed=False,
                reason="Total hourly trade limit reached",
                sector=sector,
                current_count_hourly=hourly_sector_count,
                current_count_daily=daily_sector_count,
                limit_hourly=self.config.max_trades_per_sector_per_hour,
                limit_daily=self.config.max_trades_per_sector_per_day,
                recommendation="Too many trades this hour. Wait or review strategy.",
            )
        
        # Check total daily limit
        if daily_total_count >= self.config.max_total_trades_per_day:
            self.stats["throttled_signals"] += 1
            return ThrottleDecision(
                allowed=False,
                reason="Total daily trade limit reached",
                sector=sector,
                current_count_hourly=hourly_sector_count,
                current_count_daily=daily_sector_count,
                limit_hourly=self.config.max_trades_per_sector_per_hour,
                limit_daily=self.config.max_trades_per_sector_per_day,
                recommendation="Daily trade limit reached. Resume tomorrow.",
            )
        
        # Check correlated sectors
        correlated = CORRELATED_SECTORS.get(sector, [])
        for corr_sector in correlated:
            corr_hourly = sum(
                1 for s in self._signals
                if s.sector == corr_sector and s.timestamp >= hourly_cutoff
            )
            if corr_hourly >= self.config.max_trades_per_sector_per_hour:
                logger.warning(
                    f"Correlated sector {corr_sector} is at limit, "
                    f"reducing priority for {sector}"
                )
                # Don't block, but warn
                return ThrottleDecision(
                    allowed=True,
                    reason=f"Allowed but correlated sector {corr_sector} is near limit",
                    sector=sector,
                    current_count_hourly=hourly_sector_count,
                    current_count_daily=daily_sector_count,
                    limit_hourly=self.config.max_trades_per_sector_per_hour,
                    limit_daily=self.config.max_trades_per_sector_per_day,
                    recommendation=f"Consider reducing position size due to {corr_sector} exposure",
                )
        
        # All checks passed
        return ThrottleDecision(
            allowed=True,
            reason="Signal allowed",
            sector=sector,
            current_count_hourly=hourly_sector_count,
            current_count_daily=daily_sector_count,
            limit_hourly=self.config.max_trades_per_sector_per_hour,
            limit_daily=self.config.max_trades_per_sector_per_day,
            recommendation="",
        )
    
    def record_signal(
        self,
        ticker: str,
        action: str,
        confidence: float,
        sectors_from_news: Optional[List[str]] = None,
        news_source_id: Optional[int] = None,
        executed: bool = False,
    ):
        """
        Record a generated signal.
        
        Args:
            ticker: Stock symbol
            action: BUY or SELL
            confidence: Signal confidence
            sectors_from_news: Sectors from news analysis
            news_source_id: ID of source news article
            executed: Whether signal was actually executed
        """
        sector = self.get_ticker_sector(ticker)
        if sectors_from_news and len(sectors_from_news) > 0:
            sector = sectors_from_news[0].upper()
        
        record = SignalRecord(
            ticker=ticker,
            sector=sector,
            action=action,
            timestamp=datetime.now(),
            confidence=confidence,
            news_source_id=news_source_id,
            executed=executed,
        )
        
        self._signals.append(record)
        self.stats["total_signals"] += 1
        if executed:
            self.stats["executed_signals"] += 1
        
        logger.info(
            f"Recorded signal: {action} {ticker} ({sector}) "
            f"confidence={confidence:.2f} executed={executed}"
        )
        
        # Cleanup old signals (older than 7 days)
        self._cleanup_old_signals()
    
    def _cleanup_old_signals(self):
        """Remove signals older than 7 days to prevent memory bloat"""
        cutoff = datetime.now() - timedelta(days=7)
        initial_count = len(self._signals)
        self._signals = [s for s in self._signals if s.timestamp >= cutoff]
        removed = initial_count - len(self._signals)
        if removed > 0:
            logger.debug(f"Cleaned up {removed} old signal records")
    
    def get_sector_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary of signals per sector.
        
        Returns:
            Dictionary with sector statistics
        """
        now = datetime.now()
        hourly_cutoff = now - timedelta(minutes=self.config.hourly_window_minutes)
        daily_cutoff = now - timedelta(hours=self.config.daily_window_hours)
        
        summary = {}
        
        # Get all unique sectors
        sectors = set(s.sector for s in self._signals)
        
        for sector in sectors:
            sector_signals = [s for s in self._signals if s.sector == sector]
            
            hourly_count = sum(1 for s in sector_signals if s.timestamp >= hourly_cutoff)
            daily_count = sum(1 for s in sector_signals if s.timestamp >= daily_cutoff)
            
            executed_count = sum(1 for s in sector_signals if s.executed)
            
            summary[sector] = {
                "hourly_count": hourly_count,
                "daily_count": daily_count,
                "hourly_limit": self.config.max_trades_per_sector_per_hour,
                "daily_limit": self.config.max_trades_per_sector_per_day,
                "hourly_remaining": max(0, self.config.max_trades_per_sector_per_hour - hourly_count),
                "daily_remaining": max(0, self.config.max_trades_per_sector_per_day - daily_count),
                "total_signals": len(sector_signals),
                "executed_signals": executed_count,
            }
        
        return summary
    
    def get_hot_sectors(self) -> List[Tuple[str, int]]:
        """
        Get sectors with high recent activity (potential overconcentration).
        
        Returns:
            List of (sector, count) tuples sorted by activity
        """
        now = datetime.now()
        hourly_cutoff = now - timedelta(minutes=self.config.hourly_window_minutes)
        
        sector_counts = defaultdict(int)
        for signal in self._signals:
            if signal.timestamp >= hourly_cutoff:
                sector_counts[signal.sector] += 1
        
        # Sort by count, descending
        hot_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)
        
        return hot_sectors


# ============================================================================
# Enhanced Signal Validator with Sector Throttling
# ============================================================================

class EnhancedSignalValidator:
    """
    Validates trading signals with sector-based throttling.
    Integrates with existing SignalValidator from Phase 9.
    """
    
    def __init__(
        self,
        sector_tracker: Optional[SectorSignalTracker] = None,
        min_confidence: float = 0.7,
        max_position_size: float = 0.10,
        daily_trade_limit: int = 20,
    ):
        self.sector_tracker = sector_tracker or SectorSignalTracker()
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        self.daily_trade_limit = daily_trade_limit
        
        # Track daily trades
        self._daily_trades: List[datetime] = []
        
        logger.info("EnhancedSignalValidator initialized with sector throttling")
    
    def validate_signal(
        self,
        signal,  # TradingSignal from Phase 9
        news_analysis: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a trading signal.
        
        Args:
            signal: TradingSignal object
            news_analysis: Optional news analysis data
            
        Returns:
            Tuple of (allowed, reason, recommendation)
        """
        
        # 1. Basic validation
        if signal.confidence < self.min_confidence:
            return (
                False,
                f"Confidence too low: {signal.confidence:.2f} < {self.min_confidence}",
                "Increase confidence threshold or wait for better signal",
            )
        
        if signal.position_size > self.max_position_size:
            return (
                False,
                f"Position size too large: {signal.position_size:.2f} > {self.max_position_size}",
                f"Reduce position size to max {self.max_position_size:.2%}",
            )
        
        # 2. Check daily trade count
        now = datetime.now()
        daily_cutoff = now - timedelta(hours=24)
        self._daily_trades = [t for t in self._daily_trades if t >= daily_cutoff]
        
        if len(self._daily_trades) >= self.daily_trade_limit:
            return (
                False,
                f"Daily trade limit reached: {len(self._daily_trades)}/{self.daily_trade_limit}",
                "Daily limit reached. Resume tomorrow.",
            )
        
        # 3. Sector throttling check
        sectors = []
        if news_analysis and "affected_sectors" in news_analysis:
            sectors = news_analysis["affected_sectors"]
        
        throttle_decision = self.sector_tracker.can_generate_signal(
            ticker=signal.ticker,
            action=signal.action.value if hasattr(signal.action, 'value') else str(signal.action),
            sectors_from_news=sectors,
        )
        
        if not throttle_decision.allowed:
            return (
                False,
                throttle_decision.reason,
                throttle_decision.recommendation,
            )
        
        # 4. All checks passed
        recommendation = throttle_decision.recommendation if throttle_decision.recommendation else "Signal approved"
        
        return (True, "Signal validated", recommendation)
    
    def record_execution(
        self,
        signal,
        news_analysis: Optional[Dict[str, Any]] = None,
    ):
        """
        Record that a signal was executed.
        
        Args:
            signal: TradingSignal that was executed
            news_analysis: Optional news analysis data
        """
        # Record in sector tracker
        sectors = []
        if news_analysis and "affected_sectors" in news_analysis:
            sectors = news_analysis["affected_sectors"]
        
        self.sector_tracker.record_signal(
            ticker=signal.ticker,
            action=signal.action.value if hasattr(signal.action, 'value') else str(signal.action),
            confidence=signal.confidence,
            sectors_from_news=sectors,
            executed=True,
        )
        
        # Track daily trade
        self._daily_trades.append(datetime.now())
        
        logger.info(f"Recorded execution: {signal.ticker}")
    
    def get_throttle_status(self) -> Dict[str, Any]:
        """Get current throttle status"""
        return {
            "sector_summary": self.sector_tracker.get_sector_summary(),
            "hot_sectors": self.sector_tracker.get_hot_sectors(),
            "daily_trades": len(self._daily_trades),
            "daily_limit": self.daily_trade_limit,
            "statistics": self.sector_tracker.stats,
        }


# ============================================================================
# Integration with Phase 9 NewsSignalGenerator
# ============================================================================

"""
How to integrate with Phase 9 NewsSignalGenerator:

from sector_throttling import EnhancedSignalValidator, SectorSignalTracker

# Initialize
tracker = SectorSignalTracker()
validator = EnhancedSignalValidator(sector_tracker=tracker)

# In NewsSignalGenerator
class NewsSignalGenerator:
    def __init__(self):
        self.validator = EnhancedSignalValidator()
    
    def generate_signal(self, analysis):
        signal = self._create_signal_from_analysis(analysis)
        
        if not signal:
            return None
        
        # Validate with sector throttling
        allowed, reason, recommendation = self.validator.validate_signal(
            signal=signal,
            news_analysis={
                "affected_sectors": analysis.affected_sectors,
                "sentiment_overall": analysis.sentiment_overall,
            }
        )
        
        if not allowed:
            logger.warning(f"Signal throttled: {reason}")
            logger.info(f"Recommendation: {recommendation}")
            return None
        
        # Record signal
        self.validator.record_execution(signal)
        
        return signal
"""


# ============================================================================
# API Router Integration Example
# ============================================================================

"""
Example FastAPI endpoints for throttle monitoring:

from fastapi import APIRouter, Depends
from sector_throttling import EnhancedSignalValidator

router = APIRouter(prefix="/api/throttle", tags=["Signal Throttling"])

# Global validator instance (or inject via dependency)
validator = EnhancedSignalValidator()

@router.get("/status")
async def get_throttle_status():
    '''Get current throttle status'''
    return validator.get_throttle_status()

@router.get("/sectors")
async def get_sector_summary():
    '''Get signals per sector'''
    return validator.sector_tracker.get_sector_summary()

@router.get("/hot-sectors")
async def get_hot_sectors():
    '''Get sectors with high activity'''
    return validator.sector_tracker.get_hot_sectors()

@router.post("/reset-hourly")
async def reset_hourly_counters():
    '''Emergency reset of hourly counters (admin only)'''
    # Implementation here
    pass
"""


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create tracker
    tracker = SectorSignalTracker(SectorThrottleConfig(
        max_trades_per_sector_per_hour=3,
        max_trades_per_sector_per_day=10,
    ))
    
    # Simulate semiconductor news flood
    print("Simulating semiconductor news flood...")
    
    tickers = ["NVDA", "AMD", "INTC", "QCOM", "AVGO", "TSM"]
    
    for ticker in tickers:
        decision = tracker.can_generate_signal(
            ticker=ticker,
            action="BUY",
            sectors_from_news=["SEMICONDUCTORS"],
        )
        
        print(f"\n{ticker}:")
        print(f"  Allowed: {decision.allowed}")
        print(f"  Reason: {decision.reason}")
        print(f"  Sector: {decision.sector}")
        print(f"  Hourly: {decision.current_count_hourly}/{decision.limit_hourly}")
        print(f"  Daily: {decision.current_count_daily}/{decision.limit_daily}")
        
        if decision.allowed:
            tracker.record_signal(
                ticker=ticker,
                action="BUY",
                confidence=0.8,
                sectors_from_news=["SEMICONDUCTORS"],
                executed=True,
            )
        else:
            print(f"  ⚠️ THROTTLED: {decision.recommendation}")
    
    # Show summary
    print("\n" + "="*50)
    print("Sector Summary:")
    for sector, stats in tracker.get_sector_summary().items():
        print(f"  {sector}:")
        print(f"    Hourly: {stats['hourly_count']}/{stats['hourly_limit']}")
        print(f"    Daily: {stats['daily_count']}/{stats['daily_limit']}")
        print(f"    Remaining (hourly): {stats['hourly_remaining']}")
    
    print("\nHot Sectors:")
    for sector, count in tracker.get_hot_sectors():
        print(f"  {sector}: {count} signals")
    
    print("\nStatistics:")
    print(f"  Total signals: {tracker.stats['total_signals']}")
    print(f"  Throttled: {tracker.stats['throttled_signals']}")
    print(f"  Executed: {tracker.stats['executed_signals']}")
