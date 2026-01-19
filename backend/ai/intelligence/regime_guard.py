"""
RegimeGuard Component - Market Regime Change Detection

Market Intelligence v2.0 - Phase 4, T4.1

This component detects market regime changes and automatically adjusts
signal strength when regimes shift to prevent losses from outdated patterns.

Key Features:
1. Regime change detection (correlation shift, win rate drop, pattern collapse)
2. Signal strength adjustment during regime changes
3. Historical regime tracking
4. Automatic confidence reduction in new regimes
5. Regime recovery monitoring

Regime Change Indicators:
- Correlation breakdown: Historical relationships break down
- Win rate collapse: Signal performance drops significantly
- Pattern failure: Explanatory power of patterns diminishes

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import statistics

from .base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ..llm_providers import LLMProvider


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class RegimeState(Enum):
    """Market regime state"""
    STABLE = "STABLE"  # Stable regime, no changes
    CHANGED = "CHANGED"  # Regime has changed
    RECOVERING = "RECOVERING"  # Recovering from regime change


class RegimeType(Enum):
    """Type of market regime"""
    BULL_MARKET = "BULL_MARKET"  # Bull market regime
    BEAR_MARKET = "BEAR_MARKET"  # Bear market regime
    SIDEWAYS = "SIDEWAYS"  # Sideways/range-bound regime
    HIGH_VOLATILITY = "HIGH_VOLATILITY"  # High volatility regime


@dataclass
class RegimeMetrics:
    """
    Metrics indicating regime change

    Attributes:
        correlation_shift: Whether correlation has shifted significantly
        correlation_change_magnitude: Magnitude of correlation change
        win_rate_drop: Whether win rate has dropped significantly
        win_rate_change_magnitude: Magnitude of win rate change
        pattern_collapse: Whether pattern explanatory power has collapsed
        pattern_score_change_magnitude: Magnitude of pattern score change
        overall_change_score: Combined score (0-1) indicating regime change
    """
    correlation_shift: bool
    correlation_change_magnitude: float
    win_rate_drop: bool
    win_rate_change_magnitude: float
    pattern_collapse: bool
    pattern_score_change_magnitude: float
    overall_change_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "correlation_shift": self.correlation_shift,
            "correlation_change_magnitude": self.correlation_change_magnitude,
            "win_rate_drop": self.win_rate_drop,
            "win_rate_change_magnitude": self.win_rate_change_magnitude,
            "pattern_collapse": self.pattern_collapse,
            "pattern_score_change_magnitude": self.pattern_score_change_magnitude,
            "overall_change_score": self.overall_change_score,
        }


@dataclass
class RegimeChange:
    """
    Record of a regime change event

    Attributes:
        detected_at: When the change was detected
        from_regime: Previous regime type
        to_regime: New regime type
        severity: Severity of change (LOW/MEDIUM/HIGH)
        metrics: Metrics that triggered the change
    """
    detected_at: datetime
    from_regime: RegimeType
    to_regime: RegimeType
    severity: str
    metrics: RegimeMetrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "detected_at": self.detected_at.isoformat(),
            "from_regime": self.from_regime.value,
            "to_regime": self.to_regime.value,
            "severity": self.severity,
            "metrics": self.metrics.to_dict(),
        }


# ============================================================================
# Main Component
# ============================================================================

class RegimeGuard(BaseIntelligence):
    """
    Regime Guard

    Detects market regime changes and automatically adjusts signal strength
    to prevent losses from outdated patterns.

    Key Features:
    1. Monitors correlation, win rate, and pattern metrics
    2. Detects regime changes when metrics shift significantly
    3. Automatically reduces signal confidence during regime changes
    4. Tracks recovery progress after regime stabilizes
    5. Maintains history of regime changes

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.regime_guard import RegimeGuard

        llm = get_llm_provider()
        guard = RegimeGuard(
            llm_provider=llm,
            market_data=market_client,
        )

        # Detect regime changes
        result = await guard.detect_regime_change({
            "correlation_current": 0.3,
            "correlation_historical": [0.7, 0.72, 0.68],
        })

        # Adjust signal strength based on regime
        adjusted = await guard.signal_strength_adjustment({
            "original_confidence": 0.8,
            "regime_state": result.data["regime_state"],
        })
    """

    # Thresholds for regime change detection
    CORRELATION_SHIFT_THRESHOLD = 0.3  # 30% change in correlation
    WIN_RATE_DROP_THRESHOLD = 0.15  # 15% drop in win rate
    PATTERN_COLLAPSE_THRESHOLD = 0.2  # 20% drop in pattern score
    OVERALL_CHANGE_THRESHOLD = 0.6  # Combined score threshold

    # Signal strength adjustment factors
    HIGH_SEVERITY_REDUCTION = 0.5  # Reduce to 50%
    MEDIUM_SEVERITY_REDUCTION = 0.7  # Reduce to 70%
    LOW_SEVERITY_REDUCTION = 0.85  # Reduce to 85%

    def __init__(
        self,
        llm_provider: LLMProvider,
        market_data: Optional[Any] = None,
    ):
        """
        Initialize RegimeGuard

        Args:
            llm_provider: LLM Provider instance
            market_data: Market data provider (optional)
        """
        super().__init__(
            name="RegimeGuard",
            phase=IntelligencePhase.P2,
        )

        self.llm = llm_provider
        self.market_data = market_data

        # State tracking
        self._current_regime = RegimeType.SIDEWAYS
        self._current_state = RegimeState.STABLE
        self._regime_history: List[RegimeChange] = []
        self._last_regime_check: Optional[datetime] = None

        # Statistics
        self._detection_count = 0
        self._adjustment_count = 0
        self._regime_change_count = 0

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Detect regime changes (main entry point)

        Args:
            data: Market metrics data

        Returns:
            IntelligenceResult: Regime detection result
        """
        return await self.detect_regime_change(data)

    async def detect_regime_change(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Detect market regime changes

        Args:
            data: Market data with:
                - correlation_current: Current correlation value
                - correlation_historical: Historical correlations
                - win_rate_current: Current win rate
                - win_rate_historical: Historical win rates
                - pattern_score_current: Current pattern score
                - pattern_score_historical: Historical pattern scores

        Returns:
            IntelligenceResult: Detection result with regime state
        """
        try:
            self._detection_count += 1
            self._last_regime_check = datetime.now()

            # Extract data
            corr_current = data.get("correlation_current", 0.0)
            corr_historical = data.get("correlation_historical", [])
            win_current = data.get("win_rate_current", 0.0)
            win_historical = data.get("win_rate_historical", [])
            pattern_current = data.get("pattern_score_current", 0.0)
            pattern_historical = data.get("pattern_score_historical", [])

            # Calculate metrics
            metrics = self._calculate_regime_metrics(
                corr_current, corr_historical,
                win_current, win_historical,
                pattern_current, pattern_historical,
            )

            # Determine regime state
            regime_changed = metrics.overall_change_score >= self.OVERALL_CHANGE_THRESHOLD
            regime_state = RegimeState.CHANGED if regime_changed else RegimeState.STABLE

            # Update current state
            if regime_changed and self._current_state != RegimeState.CHANGED:
                self._regime_change_count += 1
                self._current_state = RegimeState.CHANGED

            # Determine severity
            severity = self._determine_severity(metrics.overall_change_score)

            # Generate reasoning
            reasoning = await self._generate_regime_reasoning(metrics, regime_state, severity)

            return self.create_result(
                success=True,
                data={
                    "stage": "regime_detection",
                    "regime_state": regime_state.value,
                    "regime_changed": regime_changed,
                    "severity": severity,
                    "correlation_shift": metrics.correlation_shift,
                    "correlation_change_magnitude": metrics.correlation_change_magnitude,
                    "win_rate_drop": metrics.win_rate_drop,
                    "win_rate_change_magnitude": metrics.win_rate_change_magnitude,
                    "pattern_collapse": metrics.pattern_collapse,
                    "pattern_score_change_magnitude": metrics.pattern_score_change_magnitude,
                    "overall_change_score": metrics.overall_change_score,
                },
                confidence=0.8,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Regime detection error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "regime_detection"},
            )
            result.add_error(f"Detection error: {str(e)}")
            return result

    async def signal_strength_adjustment(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Adjust signal strength based on regime state

        Args:
            data: Signal data with:
                - original_confidence: Original confidence level
                - regime_state: Current regime state
                - change_severity: Severity of regime change (optional)
                - days_since_change: Days since regime changed (optional)

        Returns:
            IntelligenceResult: Adjustment result
        """
        try:
            self._adjustment_count += 1

            original_confidence = data.get("original_confidence", 0.7)
            regime_state_str = data.get("regime_state", "STABLE")
            severity = data.get("change_severity", "MEDIUM")
            days_since_change = data.get("days_since_change", 0)

            # Determine adjustment factor
            if regime_state_str == "STABLE":
                adjustment_factor = 1.0
            elif regime_state_str == "RECOVERING":
                # Gradual recovery based on days since change
                recovery_progress = min(1.0, days_since_change / 60)  # Full recovery after 60 days
                if severity == "HIGH":
                    adjustment_factor = self.HIGH_SEVERITY_REDUCTION + (1 - self.HIGH_SEVERITY_REDUCTION) * recovery_progress
                elif severity == "MEDIUM":
                    adjustment_factor = self.MEDIUM_SEVERITY_REDUCTION + (1 - self.MEDIUM_SEVERITY_REDUCTION) * recovery_progress
                else:
                    adjustment_factor = self.LOW_SEVERITY_REDUCTION + (1 - self.LOW_SEVERITY_REDUCTION) * recovery_progress
            else:  # CHANGED
                if severity == "HIGH":
                    adjustment_factor = self.HIGH_SEVERITY_REDUCTION
                elif severity == "MEDIUM":
                    adjustment_factor = self.MEDIUM_SEVERITY_REDUCTION
                else:
                    adjustment_factor = self.LOW_SEVERITY_REDUCTION

            # Apply adjustment
            adjusted_confidence = original_confidence * adjustment_factor

            return self.create_result(
                success=True,
                data={
                    "stage": "signal_adjustment",
                    "original_confidence": original_confidence,
                    "adjusted_confidence": adjusted_confidence,
                    "adjustment_factor": adjustment_factor,
                    "regime_state": regime_state_str,
                    "severity": severity,
                },
                reasoning=f"Adjusted confidence from {original_confidence:.2f} to {adjusted_confidence:.2f} based on regime state",
            )

        except Exception as e:
            logger.error(f"Signal adjustment error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "signal_adjustment"},
            )
            result.add_error(f"Adjustment error: {str(e)}")
            return result

    async def check_recovery_progress(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Check recovery progress after regime change

        Args:
            data: Recovery data with:
                - days_since_change: Days since regime changed
                - current_win_rate: Current win rate
                - baseline_win_rate: Baseline win rate before change

        Returns:
            IntelligenceResult: Recovery progress result
        """
        try:
            days_since_change = data.get("days_since_change", 0)
            current_win_rate = data.get("current_win_rate", 0.0)
            baseline_win_rate = data.get("baseline_win_rate", 0.65)

            # Calculate recovery progress
            win_rate_gap = baseline_win_rate - current_win_rate
            recovery_progress = max(0.0, 1.0 - (win_rate_gap / (baseline_win_rate * 0.15)))

            # Determine if fully recovered
            recovered = recovery_progress >= 0.95 and days_since_change >= 30

            # Update state if recovered
            if recovered:
                self._current_state = RegimeState.STABLE

            return self.create_result(
                success=True,
                data={
                    "stage": "recovery_check",
                    "recovery_progress": recovery_progress,
                    "recovered": recovered,
                    "days_since_change": days_since_change,
                    "current_win_rate": current_win_rate,
                    "baseline_win_rate": baseline_win_rate,
                },
                reasoning=f"Recovery progress: {recovery_progress:.1%}, {'Recovered' if recovered else 'Still recovering'}",
            )

        except Exception as e:
            logger.error(f"Recovery check error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "recovery_check"},
            )
            result.add_error(f"Recovery check error: {str(e)}")
            return result

    async def record_regime_change(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Record a regime change event

        Args:
            data: Change data with:
                - from_regime: Previous regime
                - to_regime: New regime
                - severity: Change severity

        Returns:
            IntelligenceResult: Recording result
        """
        try:
            from_regime = RegimeType(data.get("from_regime", "SIDEWAYS"))
            to_regime = RegimeType(data.get("to_regime", "SIDEWAYS"))
            severity = data.get("severity", "MEDIUM")

            # Create metrics (placeholder)
            metrics = RegimeMetrics(
                correlation_shift=True,
                correlation_change_magnitude=0.5,
                win_rate_drop=True,
                win_rate_change_magnitude=0.2,
                pattern_collapse=True,
                pattern_score_change_magnitude=0.3,
                overall_change_score=0.7,
            )

            # Create regime change record
            change = RegimeChange(
                detected_at=datetime.now(),
                from_regime=from_regime,
                to_regime=to_regime,
                severity=severity,
                metrics=metrics,
            )

            self._regime_history.append(change)
            self._current_regime = to_regime

            return self.create_result(
                success=True,
                data={
                    "stage": "record_change",
                    "change_recorded": True,
                    "change_id": len(self._regime_history),
                },
                reasoning=f"Recorded regime change from {from_regime.value} to {to_regime.value}",
            )

        except Exception as e:
            logger.error(f"Record regime change error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "record_change"},
            )
            result.add_error(f"Record error: {str(e)}")
            return result

    async def get_regime_history(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Get regime change history

        Args:
            data: Query data with:
                - days: Number of days to look back

        Returns:
            IntelligenceResult: History result
        """
        try:
            days = data.get("days", 90)
            cutoff_date = datetime.now() - timedelta(days=days)

            # Filter history by date
            relevant_changes = [
                change for change in self._regime_history
                if change.detected_at >= cutoff_date
            ]

            return self.create_result(
                success=True,
                data={
                    "stage": "regime_history",
                    "history": [change.to_dict() for change in relevant_changes],
                    "total_changes": len(relevant_changes),
                },
                reasoning=f"Found {len(relevant_changes)} regime changes in last {days} days",
            )

        except Exception as e:
            logger.error(f"Get regime history error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "regime_history"},
            )
            result.add_error(f"History error: {str(e)}")
            return result

    def _calculate_regime_metrics(
        self,
        corr_current: float,
        corr_historical: List[float],
        win_current: float,
        win_historical: List[float],
        pattern_current: float,
        pattern_historical: List[float],
    ) -> RegimeMetrics:
        """Calculate regime change metrics"""
        # Correlation shift
        correlation_shift = False
        correlation_change_magnitude = 0.0
        if corr_historical:
            avg_historical_corr = statistics.mean(corr_historical)
            correlation_change_magnitude = abs(corr_current - avg_historical_corr)
            correlation_shift = correlation_change_magnitude >= self.CORRELATION_SHIFT_THRESHOLD

        # Win rate drop
        win_rate_drop = False
        win_rate_change_magnitude = 0.0
        if win_historical:
            avg_historical_win = statistics.mean(win_historical)
            win_rate_change_magnitude = avg_historical_win - win_current
            win_rate_drop = win_rate_change_magnitude >= self.WIN_RATE_DROP_THRESHOLD

        # Pattern collapse
        pattern_collapse = False
        pattern_score_change_magnitude = 0.0
        if pattern_historical:
            avg_historical_pattern = statistics.mean(pattern_historical)
            pattern_score_change_magnitude = avg_historical_pattern - pattern_current
            pattern_collapse = pattern_score_change_magnitude >= self.PATTERN_COLLAPSE_THRESHOLD

        # Overall change score (normalized 0-1)
        change_indicators = 0
        if correlation_shift:
            change_indicators += 1
        if win_rate_drop:
            change_indicators += 1
        if pattern_collapse:
            change_indicators += 1

        # Weighted score based on magnitudes
        overall_change_score = (
            (1 if correlation_shift else 0) * 0.4 +
            (1 if win_rate_drop else 0) * 0.4 +
            (1 if pattern_collapse else 0) * 0.2
        )

        return RegimeMetrics(
            correlation_shift=correlation_shift,
            correlation_change_magnitude=correlation_change_magnitude,
            win_rate_drop=win_rate_drop,
            win_rate_change_magnitude=win_rate_change_magnitude,
            pattern_collapse=pattern_collapse,
            pattern_score_change_magnitude=pattern_score_change_magnitude,
            overall_change_score=overall_change_score,
        )

    def _determine_severity(self, change_score: float) -> str:
        """Determine severity of regime change"""
        if change_score >= 0.8:
            return "HIGH"
        elif change_score >= 0.5:
            return "MEDIUM"
        return "LOW"

    async def _generate_regime_reasoning(
        self,
        metrics: RegimeMetrics,
        regime_state: RegimeState,
        severity: str,
    ) -> str:
        """Generate reasoning using LLM"""
        try:
            if regime_state == RegimeState.STABLE:
                return "Market regime is stable. No significant changes detected."

            system_prompt = """You are a market regime analyst.
Explain what regime changes mean for trading strategies."""

            user_prompt = f"""Analyze this regime change:

**Change Indicators:**
- Correlation Shift: {metrics.correlation_shift} (magnitude: {metrics.correlation_change_magnitude:.2f})
- Win Rate Drop: {metrics.win_rate_drop} (magnitude: {metrics.win_rate_change_magnitude:.2f})
- Pattern Collapse: {metrics.pattern_collapse} (magnitude: {metrics.pattern_score_change_magnitude:.2f})
- Overall Change Score: {metrics.overall_change_score:.2f}

**Severity:** {severity}

Provide a brief explanation (1-2 sentences) of what this means for signal reliability."""

            response = await self.llm.complete_with_system(system_prompt, user_prompt)
            return response.content

        except Exception as e:
            logger.error(f"Reasoning generation error: {e}")
            return f"Regime change detected with severity {severity}"

    def get_statistics(self) -> Dict[str, Any]:
        """Get regime guard statistics"""
        return {
            "total_detections": self._detection_count,
            "total_adjustments": self._adjustment_count,
            "regime_changes": self._regime_change_count,
            "current_regime": self._current_regime.value,
            "current_state": self._current_state.value,
        }


# ============================================================================
# Factory function
# ============================================================================

def create_regime_guard(
    llm_provider: Optional[LLMProvider] = None,
    market_data: Optional[Any] = None,
) -> RegimeGuard:
    """
    Create RegimeGuard instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        market_data: Market data provider

    Returns:
        RegimeGuard: Configured guard instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return RegimeGuard(
        llm_provider=llm_provider,
        market_data=market_data,
    )
