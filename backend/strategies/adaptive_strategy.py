"""
Adaptive Strategy - Automatic strategy switching based on market regime

Features:
- Market regime detection (Bull/Bear/Sideways)
- Strategy selection per regime
- Smooth transitions between strategies
- Performance-based adaptation
- Risk management per regime

Author: AI Trading System Team
Date: 2025-11-24
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime types."""
    BULL = "bull"           # Rising market, high momentum
    BEAR = "bear"           # Falling market, flight to quality
    SIDEWAYS = "sideways"   # Range-bound, mean reversion
    VOLATILE = "volatile"   # High volatility, reduce exposure
    UNKNOWN = "unknown"     # Insufficient data


@dataclass
class RegimeSignals:
    """Signals indicating current market regime."""
    # Trend indicators
    ma_20_above_50: bool  # Short-term trend
    ma_50_above_200: bool  # Long-term trend
    price_above_ma_20: bool

    # Momentum
    rsi_14: float  # 0-100
    macd_signal: str  # bullish/bearish/neutral

    # Volatility
    vix_level: float
    realized_volatility_20d: float

    # Breadth
    advancing_pct: float  # % of stocks advancing
    new_highs_ratio: float  # New highs / New lows

    # Sentiment
    put_call_ratio: float
    fear_greed_index: float  # 0-100

    timestamp: datetime


@dataclass
class StrategyConfig:
    """Configuration for a trading strategy."""
    name: str

    # Position sizing
    max_position_size_pct: float
    max_portfolio_positions: int

    # Risk management
    stop_loss_pct: float
    take_profit_pct: float
    max_drawdown_trigger_pct: float

    # Signal thresholds
    min_confidence: float
    min_sharpe_ratio: float

    # Metadata
    target_regime: MarketRegime
    description: str


class AdaptiveStrategyManager:
    """
    Automatically switch strategies based on market regime.

    Strategy Profiles:
    1. Bull Market Strategy
       - Momentum-focused
       - Higher risk tolerance
       - Larger position sizes

    2. Bear Market Strategy
       - Defensive, quality-focused
       - Lower risk tolerance
       - Smaller positions, more cash

    3. Sideways Strategy
       - Mean reversion
       - Moderate risk
       - Range trading

    4. Volatile Strategy
       - Risk-off mode
       - Minimal exposure
       - Short-term only
    """

    def __init__(
        self,
        regime_detector=None,
        performance_tracker=None,
        alert_manager=None,
    ):
        """
        Initialize adaptive strategy manager.

        Args:
            regime_detector: Market regime detection service
            performance_tracker: Strategy performance tracking
            alert_manager: Alert manager for regime changes
        """
        self.regime_detector = regime_detector
        self.performance_tracker = performance_tracker
        self.alert_manager = alert_manager

        # Strategy configurations
        self.strategies = self._init_strategies()

        # Current state
        self.current_regime = MarketRegime.UNKNOWN
        self.current_strategy = None
        self.last_regime_check = None
        self.regime_confidence = 0.0

        # Transition management
        self.regime_change_cooldown_hours = 6  # Avoid whipsaw
        self.last_regime_change = datetime.utcnow()

        # Performance tracking
        self.regime_history: List[Tuple[datetime, MarketRegime, float]] = []

        logger.info("AdaptiveStrategyManager initialized")

    def _init_strategies(self) -> Dict[MarketRegime, StrategyConfig]:
        """Initialize strategy configurations for each regime."""
        return {
            MarketRegime.BULL: StrategyConfig(
                name="Bull Market Momentum",
                max_position_size_pct=10.0,  # 10% per position
                max_portfolio_positions=15,   # More positions
                stop_loss_pct=8.0,            # Wider stops
                take_profit_pct=15.0,         # Higher targets
                max_drawdown_trigger_pct=15.0,
                min_confidence=0.70,          # Lower threshold
                min_sharpe_ratio=1.5,
                target_regime=MarketRegime.BULL,
                description="Aggressive growth strategy for bull markets",
            ),

            MarketRegime.BEAR: StrategyConfig(
                name="Bear Market Defense",
                max_position_size_pct=5.0,   # 5% per position
                max_portfolio_positions=8,    # Fewer positions
                stop_loss_pct=5.0,            # Tight stops
                take_profit_pct=8.0,          # Quick profits
                max_drawdown_trigger_pct=8.0,
                min_confidence=0.80,          # Higher threshold
                min_sharpe_ratio=2.0,
                target_regime=MarketRegime.BEAR,
                description="Defensive strategy for bear markets",
            ),

            MarketRegime.SIDEWAYS: StrategyConfig(
                name="Range Trading",
                max_position_size_pct=7.0,
                max_portfolio_positions=12,
                stop_loss_pct=6.0,
                take_profit_pct=10.0,
                max_drawdown_trigger_pct=10.0,
                min_confidence=0.75,
                min_sharpe_ratio=1.8,
                target_regime=MarketRegime.SIDEWAYS,
                description="Mean reversion for range-bound markets",
            ),

            MarketRegime.VOLATILE: StrategyConfig(
                name="Low Volatility Mode",
                max_position_size_pct=3.0,   # Very small positions
                max_portfolio_positions=5,    # Minimal exposure
                stop_loss_pct=4.0,            # Very tight stops
                take_profit_pct=6.0,          # Quick exits
                max_drawdown_trigger_pct=5.0,
                min_confidence=0.85,          # Very high threshold
                min_sharpe_ratio=2.5,
                target_regime=MarketRegime.VOLATILE,
                description="Risk-off mode for volatile markets",
            ),
        }

    async def detect_regime(
        self,
        signals: Optional[RegimeSignals] = None,
    ) -> Tuple[MarketRegime, float]:
        """
        Detect current market regime.

        Args:
            signals: Pre-computed regime signals (optional)

        Returns:
            (MarketRegime, confidence_score)
        """
        if not signals and not self.regime_detector:
            logger.warning("No regime signals or detector available")
            return MarketRegime.UNKNOWN, 0.0

        if not signals:
            # Fetch signals from regime detector
            signals = await self.regime_detector.get_signals()

        # Calculate regime scores
        bull_score = self._calculate_bull_score(signals)
        bear_score = self._calculate_bear_score(signals)
        sideways_score = self._calculate_sideways_score(signals)
        volatile_score = self._calculate_volatile_score(signals)

        # Determine dominant regime
        scores = {
            MarketRegime.BULL: bull_score,
            MarketRegime.BEAR: bear_score,
            MarketRegime.SIDEWAYS: sideways_score,
            MarketRegime.VOLATILE: volatile_score,
        }

        regime = max(scores, key=scores.get)
        confidence = scores[regime]

        logger.info(
            f"Regime detected: {regime.value} (confidence={confidence:.2f})\n"
            f"Scores: Bull={bull_score:.2f}, Bear={bear_score:.2f}, "
            f"Sideways={sideways_score:.2f}, Volatile={volatile_score:.2f}"
        )

        self.last_regime_check = datetime.utcnow()
        self.regime_history.append((datetime.utcnow(), regime, confidence))

        return regime, confidence

    def _calculate_bull_score(self, signals: RegimeSignals) -> float:
        """Calculate bull market score (0-1)."""
        score = 0.0

        # Trend (40% weight)
        if signals.ma_20_above_50 and signals.ma_50_above_200:
            score += 0.4
        elif signals.ma_20_above_50:
            score += 0.2

        # Momentum (30% weight)
        if signals.rsi_14 > 50:
            score += 0.15
        if signals.macd_signal == "bullish":
            score += 0.15

        # Breadth (20% weight)
        if signals.advancing_pct > 60:
            score += 0.2

        # Volatility (10% weight) - low volatility is bullish
        if signals.vix_level < 20:
            score += 0.1

        return min(1.0, score)

    def _calculate_bear_score(self, signals: RegimeSignals) -> float:
        """Calculate bear market score (0-1)."""
        score = 0.0

        # Trend (40% weight)
        if not signals.ma_20_above_50 and not signals.ma_50_above_200:
            score += 0.4
        elif not signals.ma_20_above_50:
            score += 0.2

        # Momentum (30% weight)
        if signals.rsi_14 < 50:
            score += 0.15
        if signals.macd_signal == "bearish":
            score += 0.15

        # Breadth (20% weight)
        if signals.advancing_pct < 40:
            score += 0.2

        # Sentiment (10% weight)
        if signals.put_call_ratio > 1.0:  # More puts than calls
            score += 0.1

        return min(1.0, score)

    def _calculate_sideways_score(self, signals: RegimeSignals) -> float:
        """Calculate sideways market score (0-1)."""
        score = 0.0

        # Weak trend signals
        if not signals.ma_20_above_50 and not (not signals.ma_50_above_200):
            score += 0.3  # Mixed signals = sideways

        # Moderate momentum
        if 45 <= signals.rsi_14 <= 55:
            score += 0.3

        # Balanced breadth
        if 45 <= signals.advancing_pct <= 55:
            score += 0.2

        # Low volatility
        if 15 <= signals.vix_level <= 25:
            score += 0.2

        return min(1.0, score)

    def _calculate_volatile_score(self, signals: RegimeSignals) -> float:
        """Calculate volatile market score (0-1)."""
        score = 0.0

        # High VIX (50% weight)
        if signals.vix_level > 30:
            score += 0.5
        elif signals.vix_level > 25:
            score += 0.25

        # High realized volatility (30% weight)
        if signals.realized_volatility_20d > 40:
            score += 0.3
        elif signals.realized_volatility_20d > 30:
            score += 0.15

        # Extreme sentiment (20% weight)
        if signals.fear_greed_index < 20 or signals.fear_greed_index > 80:
            score += 0.2

        return min(1.0, score)

    async def update_strategy(self, force: bool = False) -> Optional[StrategyConfig]:
        """
        Update active strategy based on current regime.

        Args:
            force: Force strategy update even within cooldown period

        Returns:
            New StrategyConfig if changed, None otherwise
        """
        # Check cooldown
        hours_since_change = (datetime.utcnow() - self.last_regime_change).total_seconds() / 3600
        if not force and hours_since_change < self.regime_change_cooldown_hours:
            logger.debug(f"Within cooldown period ({hours_since_change:.1f}h < {self.regime_change_cooldown_hours}h)")
            return None

        # Detect regime
        new_regime, confidence = await self.detect_regime()

        # Require high confidence for regime change
        if confidence < 0.6:
            logger.info(f"Insufficient confidence for regime change ({confidence:.2f} < 0.60)")
            return None

        # Check if regime changed
        if new_regime == self.current_regime:
            logger.debug(f"Regime unchanged: {new_regime.value}")
            return None

        # Update regime and strategy
        old_regime = self.current_regime
        old_strategy = self.current_strategy

        self.current_regime = new_regime
        self.regime_confidence = confidence
        self.current_strategy = self.strategies[new_regime]
        self.last_regime_change = datetime.utcnow()

        logger.info(
            f"Regime changed: {old_regime.value if old_regime else 'None'} → {new_regime.value}\n"
            f"Strategy switched: {old_strategy.name if old_strategy else 'None'} → {self.current_strategy.name}"
        )

        # Send alert
        if self.alert_manager:
            await self.alert_manager.send_alert(
                category="PERFORMANCE",
                priority="HIGH" if new_regime in [MarketRegime.BEAR, MarketRegime.VOLATILE] else "MEDIUM",
                title=f"Market Regime Changed: {new_regime.value}",
                message=f"Switched to {self.current_strategy.name} strategy",
                metadata={
                    "old_regime": old_regime.value if old_regime else None,
                    "new_regime": new_regime.value,
                    "confidence": confidence,
                },
            )

        return self.current_strategy

    def get_current_strategy(self) -> Optional[StrategyConfig]:
        """Get current active strategy."""
        return self.current_strategy

    def get_position_size(
        self,
        ticker: str,
        signal_confidence: float,
        portfolio_value: float,
    ) -> float:
        """
        Calculate position size based on current strategy and signal confidence.

        Args:
            ticker: Stock ticker
            signal_confidence: AI confidence (0-1)
            portfolio_value: Current portfolio value

        Returns:
            Position size in USD
        """
        if not self.current_strategy:
            logger.warning("No active strategy, using conservative 5% position size")
            max_position_pct = 5.0
        else:
            max_position_pct = self.current_strategy.max_position_size_pct

        # Adjust by confidence
        confidence_multiplier = signal_confidence  # Linear scaling

        # Calculate position size
        position_size_pct = max_position_pct * confidence_multiplier
        position_size_usd = portfolio_value * (position_size_pct / 100)

        logger.debug(
            f"Position size for {ticker}: ${position_size_usd:,.2f} "
            f"({position_size_pct:.2f}% of portfolio)"
        )

        return position_size_usd

    def should_take_signal(
        self,
        signal: str,
        confidence: float,
        sharpe_ratio: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """
        Determine if signal meets current strategy criteria.

        Returns:
            (should_take, reason)
        """
        if not self.current_strategy:
            return False, "No active strategy"

        # Check confidence threshold
        if confidence < self.current_strategy.min_confidence:
            return False, f"Confidence {confidence:.2f} below threshold {self.current_strategy.min_confidence}"

        # Check Sharpe ratio (if available)
        if sharpe_ratio is not None:
            if sharpe_ratio < self.current_strategy.min_sharpe_ratio:
                return False, f"Sharpe {sharpe_ratio:.2f} below threshold {self.current_strategy.min_sharpe_ratio}"

        return True, "Signal meets strategy criteria"

    def get_status_report(self) -> Dict:
        """Generate status report."""
        return {
            "current_regime": self.current_regime.value if self.current_regime else None,
            "regime_confidence": self.regime_confidence,
            "current_strategy": {
                "name": self.current_strategy.name,
                "max_position_size_pct": self.current_strategy.max_position_size_pct,
                "min_confidence": self.current_strategy.min_confidence,
                "stop_loss_pct": self.current_strategy.stop_loss_pct,
            } if self.current_strategy else None,
            "last_regime_check": self.last_regime_check.isoformat() if self.last_regime_check else None,
            "last_regime_change": self.last_regime_change.isoformat(),
            "hours_since_change": (datetime.utcnow() - self.last_regime_change).total_seconds() / 3600,
            "cooldown_remaining_hours": max(
                0,
                self.regime_change_cooldown_hours - (datetime.utcnow() - self.last_regime_change).total_seconds() / 3600
            ),
            "regime_history_count": len(self.regime_history),
        }
