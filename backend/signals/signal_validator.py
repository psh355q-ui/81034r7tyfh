"""
Trading Signal Validator

Features:
- Validate signals before execution
- Safety checks (position size, daily limits, confidence)
- Kill switch integration
- Daily loss limit enforcement
- Sector throttling integration

Author: AI Trading System
Date: 2025-11-15
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any, List

from .news_signal_generator import TradingSignal, SignalAction

logger = logging.getLogger(__name__)


class SignalValidator:
    """
    Validates trading signals before execution.
    
    Safety Features:
    - Minimum confidence threshold
    - Maximum position size
    - Daily trade count limit
    - Daily loss limit (Kill Switch)
    - Market hours check
    - Consecutive loss protection
    """
    
    def __init__(
        self,
        min_confidence: float = 0.7,
        max_position_size: float = 0.10,
        daily_trade_limit: int = 20,
        daily_loss_limit_pct: float = 5.0,
        max_consecutive_losses: int = 5,
        market_hours_only: bool = True,
    ):
        """
        Initialize validator.
        
        Args:
            min_confidence: Minimum confidence to execute
            max_position_size: Maximum position as % of portfolio
            daily_trade_limit: Max trades per day
            daily_loss_limit_pct: Max daily loss before kill switch (%)
            max_consecutive_losses: Max consecutive losses before pause
            market_hours_only: Only allow during market hours
        """
        self.min_confidence = min_confidence
        self.max_position_size = max_position_size
        self.daily_trade_limit = daily_trade_limit
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.market_hours_only = market_hours_only
        
        # State tracking
        self._daily_trades: List[datetime] = []
        self._daily_pnl: float = 0.0
        self._consecutive_losses: int = 0
        self._kill_switch_active: bool = False
        self._kill_switch_reason: str = ""
        
        # Statistics
        self.stats = {
            "total_validated": 0,
            "approved": 0,
            "rejected": 0,
            "rejected_confidence": 0,
            "rejected_position_size": 0,
            "rejected_daily_limit": 0,
            "rejected_loss_limit": 0,
            "rejected_kill_switch": 0,
            "rejected_market_hours": 0,
        }
        
        logger.info(
            f"SignalValidator initialized: min_conf={min_confidence}, "
            f"max_pos={max_position_size:.1%}, daily_limit={daily_trade_limit}"
        )
    
    def validate_signal(
        self,
        signal: TradingSignal,
        current_portfolio_value: float = 100000.0,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a trading signal.
        
        Args:
            signal: TradingSignal to validate
            current_portfolio_value: Current portfolio value (for position sizing)
            
        Returns:
            Tuple of (approved, reason, recommendation)
        """
        self.stats["total_validated"] += 1
        
        # 1. Kill Switch Check
        if self._kill_switch_active:
            self.stats["rejected_kill_switch"] += 1
            self.stats["rejected"] += 1
            return (
                False,
                f"Kill switch active: {self._kill_switch_reason}",
                "Manual intervention required to reset kill switch",
            )
        
        # 2. Confidence Check
        if signal.confidence < self.min_confidence:
            self.stats["rejected_confidence"] += 1
            self.stats["rejected"] += 1
            return (
                False,
                f"Confidence too low: {signal.confidence:.2f} < {self.min_confidence}",
                f"Wait for higher confidence signal (>= {self.min_confidence})",
            )
        
        # 3. Position Size Check
        if signal.position_size > self.max_position_size:
            self.stats["rejected_position_size"] += 1
            self.stats["rejected"] += 1
            return (
                False,
                f"Position size too large: {signal.position_size:.2%} > {self.max_position_size:.2%}",
                f"Reduce position size to max {self.max_position_size:.2%}",
            )
        
        # 4. Daily Trade Limit Check
        self._cleanup_old_trades()
        if len(self._daily_trades) >= self.daily_trade_limit:
            self.stats["rejected_daily_limit"] += 1
            self.stats["rejected"] += 1
            return (
                False,
                f"Daily trade limit reached: {len(self._daily_trades)}/{self.daily_trade_limit}",
                "Daily limit reached. Resume tomorrow.",
            )
        
        # 5. Daily Loss Limit Check
        if self._daily_pnl <= -self.daily_loss_limit_pct:
            self._activate_kill_switch(f"Daily loss limit exceeded: {self._daily_pnl:.2f}%")
            self.stats["rejected_loss_limit"] += 1
            self.stats["rejected"] += 1
            return (
                False,
                f"Daily loss limit exceeded: {self._daily_pnl:.2f}% <= -{self.daily_loss_limit_pct}%",
                "Stop trading for today. Review strategy.",
            )
        
        # 6. Consecutive Losses Check
        if self._consecutive_losses >= self.max_consecutive_losses:
            self.stats["rejected"] += 1
            return (
                False,
                f"Too many consecutive losses: {self._consecutive_losses}",
                f"Pause trading after {self.max_consecutive_losses} consecutive losses",
            )
        
        # 7. Market Hours Check (simplified - US market)
        if self.market_hours_only and not self._is_market_open():
            self.stats["rejected_market_hours"] += 1
            self.stats["rejected"] += 1
            return (
                False,
                "Market is closed",
                "Signal will be queued for market open",
            )
        
        # 8. Calculate actual position value
        position_value = current_portfolio_value * signal.position_size
        if position_value > current_portfolio_value * self.max_position_size:
            return (
                False,
                "Calculated position exceeds maximum",
                f"Max position value: ${current_portfolio_value * self.max_position_size:,.2f}",
            )
        
        # All checks passed!
        self.stats["approved"] += 1
        
        recommendation = f"Signal approved. Position value: ${position_value:,.2f}"
        if signal.auto_execute:
            recommendation = "⚡ AUTO-EXECUTE ENABLED - " + recommendation
        
        logger.info(
            f"Signal validated: {signal.action.value} {signal.ticker} "
            f"@ {signal.position_size:.1%} (confidence={signal.confidence:.2f})"
        )
        
        return (True, "Signal validated successfully", recommendation)
    
    def _cleanup_old_trades(self):
        """Remove trades older than 24 hours"""
        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        self._daily_trades = [t for t in self._daily_trades if t >= cutoff]
    
    def _is_market_open(self) -> bool:
        """
        Check if market is open (simplified US market hours).
        
        Market hours: 9:30 AM - 4:00 PM EST, Mon-Fri
        """
        now = datetime.now()
        
        # Check weekday (0=Mon, 6=Sun)
        if now.weekday() >= 5:  # Weekend
            return False
        
        # Check time (simplified, assumes EST timezone)
        hour = now.hour
        minute = now.minute
        
        # 9:30 AM = 9.5, 4:00 PM = 16.0
        current_time = hour + minute / 60
        
        if 9.5 <= current_time < 16.0:
            return True
        
        return False
    
    def record_trade_result(self, profit_pct: float):
        """
        Record the result of an executed trade.
        
        Args:
            profit_pct: Profit/loss as percentage (positive = profit)
        """
        # Update daily P&L
        self._daily_pnl += profit_pct
        
        # Update consecutive losses
        if profit_pct < 0:
            self._consecutive_losses += 1
            logger.warning(
                f"Trade loss recorded: {profit_pct:.2f}%. "
                f"Consecutive losses: {self._consecutive_losses}"
            )
        else:
            self._consecutive_losses = 0
            logger.info(f"Trade profit recorded: {profit_pct:.2f}%")
        
        # Record trade time
        self._daily_trades.append(datetime.now())
        
        # Check if kill switch should activate
        if self._daily_pnl <= -self.daily_loss_limit_pct:
            self._activate_kill_switch(f"Daily loss limit: {self._daily_pnl:.2f}%")
    
    def _activate_kill_switch(self, reason: str):
        """Activate kill switch"""
        self._kill_switch_active = True
        self._kill_switch_reason = reason
        logger.critical(f"🚨 KILL SWITCH ACTIVATED: {reason}")
    
    def reset_kill_switch(self):
        """Reset kill switch (admin action)"""
        if self._kill_switch_active:
            logger.warning(
                f"Kill switch deactivated. Was active for: {self._kill_switch_reason}"
            )
            self._kill_switch_active = False
            self._kill_switch_reason = ""
            self._consecutive_losses = 0
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at market close)"""
        self._daily_pnl = 0.0
        self._daily_trades = []
        self._consecutive_losses = 0
        logger.info("Daily statistics reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current validator status"""
        self._cleanup_old_trades()
        
        return {
            "kill_switch_active": self._kill_switch_active,
            "kill_switch_reason": self._kill_switch_reason,
            "daily_trades_count": len(self._daily_trades),
            "daily_trade_limit": self.daily_trade_limit,
            "daily_pnl": self._daily_pnl,
            "daily_loss_limit": self.daily_loss_limit_pct,
            "consecutive_losses": self._consecutive_losses,
            "max_consecutive_losses": self.max_consecutive_losses,
            "market_open": self._is_market_open(),
            "statistics": self.stats,
        }
    
    def update_settings(
        self,
        min_confidence: Optional[float] = None,
        max_position_size: Optional[float] = None,
        daily_trade_limit: Optional[int] = None,
        daily_loss_limit_pct: Optional[float] = None,
        max_consecutive_losses: Optional[int] = None,
        market_hours_only: Optional[bool] = None,
    ):
        """Update validator settings"""
        
        if min_confidence is not None:
            self.min_confidence = min_confidence
            logger.info(f"Min confidence set to: {min_confidence}")
        
        if max_position_size is not None:
            self.max_position_size = max_position_size
            logger.info(f"Max position size set to: {max_position_size:.1%}")
        
        if daily_trade_limit is not None:
            self.daily_trade_limit = daily_trade_limit
            logger.info(f"Daily trade limit set to: {daily_trade_limit}")
        
        if daily_loss_limit_pct is not None:
            self.daily_loss_limit_pct = daily_loss_limit_pct
            logger.info(f"Daily loss limit set to: {daily_loss_limit_pct}%")
        
        if max_consecutive_losses is not None:
            self.max_consecutive_losses = max_consecutive_losses
            logger.info(f"Max consecutive losses set to: {max_consecutive_losses}")
        
        if market_hours_only is not None:
            self.market_hours_only = market_hours_only
            logger.info(f"Market hours only: {market_hours_only}")


# ============================================================================
# Enhanced Validator with Sector Throttling
# ============================================================================

class EnhancedSignalValidator(SignalValidator):
    """
    Enhanced validator with sector throttling integration.
    
    Additional Features:
    - Sector concentration limits
    - Correlation-based risk detection
    - Portfolio exposure checks
    """
    
    def __init__(
        self,
        sector_tracker=None,
        **kwargs
    ):
        """
        Initialize enhanced validator.
        
        Args:
            sector_tracker: SectorSignalTracker instance (from sector_throttling module)
            **kwargs: Arguments for parent SignalValidator
        """
        super().__init__(**kwargs)
        self.sector_tracker = sector_tracker
    
    def validate_signal(
        self,
        signal: TradingSignal,
        current_portfolio_value: float = 100000.0,
        news_analysis: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate signal with sector throttling.
        
        Args:
            signal: TradingSignal to validate
            current_portfolio_value: Current portfolio value
            news_analysis: Optional news analysis for sector info
            
        Returns:
            Tuple of (approved, reason, recommendation)
        """
        # First run parent validation
        approved, reason, recommendation = super().validate_signal(
            signal, current_portfolio_value
        )
        
        if not approved:
            return (approved, reason, recommendation)
        
        # Then check sector throttling
        if self.sector_tracker:
            sectors = []
            if news_analysis and "affected_sectors" in news_analysis:
                sectors = news_analysis["affected_sectors"]
            
            throttle_decision = self.sector_tracker.can_generate_signal(
                ticker=signal.ticker,
                action=signal.action.value,
                sectors_from_news=sectors,
            )
            
            if not throttle_decision.allowed:
                self.stats["rejected"] += 1
                return (
                    False,
                    throttle_decision.reason,
                    throttle_decision.recommendation,
                )
            
            # Check for warning (allowed but risky)
            if throttle_decision.recommendation:
                recommendation = f"{recommendation}. NOTE: {throttle_decision.recommendation}"
        
        return (True, reason, recommendation)
    
    def record_execution(
        self,
        signal: TradingSignal,
        news_analysis: Optional[Dict[str, Any]] = None,
    ):
        """
        Record that a signal was executed (for sector tracking).
        
        Args:
            signal: Executed signal
            news_analysis: Optional news analysis data
        """
        if self.sector_tracker:
            sectors = []
            if news_analysis and "affected_sectors" in news_analysis:
                sectors = news_analysis["affected_sectors"]
            
            self.sector_tracker.record_signal(
                ticker=signal.ticker,
                action=signal.action.value,
                confidence=signal.confidence,
                sectors_from_news=sectors,
                executed=True,
            )
        
        self._daily_trades.append(datetime.now())


# ============================================================================
# Factory function
# ============================================================================

def create_signal_validator(
    config: Optional[Dict[str, Any]] = None,
    sector_tracker=None,
) -> SignalValidator:
    """
    Create SignalValidator from configuration.
    
    Args:
        config: Configuration dictionary
        sector_tracker: Optional sector tracker for enhanced validation
        
    Returns:
        Configured SignalValidator instance
    """
    if config is None:
        import os
        config = {
            "min_confidence": float(os.getenv("VALIDATOR_MIN_CONFIDENCE", "0.7")),
            "max_position_size": float(os.getenv("VALIDATOR_MAX_POSITION", "0.10")),
            "daily_trade_limit": int(os.getenv("VALIDATOR_DAILY_LIMIT", "20")),
            "daily_loss_limit_pct": float(os.getenv("VALIDATOR_LOSS_LIMIT", "5.0")),
            "max_consecutive_losses": int(os.getenv("VALIDATOR_MAX_CONSECUTIVE", "5")),
            "market_hours_only": os.getenv("VALIDATOR_MARKET_HOURS", "true").lower() == "true",
        }
    
    if sector_tracker:
        return EnhancedSignalValidator(sector_tracker=sector_tracker, **config)
    else:
        return SignalValidator(**config)
