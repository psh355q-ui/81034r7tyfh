"""
ContrarySignal Component - Market Crowding Detection

Market Intelligence v2.0 - Phase 2, T2.2

This component detects market crowding and generates contrarian trading signals
when sentiment becomes extreme through fund flow analysis, sentiment detection,
and position skew calculation.

Key Features:
1. ETF fund flow Z-score calculation
2. Sentiment extreme value detection
3. Position skew (crowding) calculation
4. Crowding level determination (LOW, MEDIUM, HIGH, EXTREME)
5. Contrarian signal generation (ACCUMULATE, HOLD, WATCH_FOR_PULLBACK, EXIT)

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

class CrowdingLevel(Enum):
    """Market crowding level"""
    LOW = "LOW"                      # No crowding
    MEDIUM = "MEDIUM"                # Moderate crowding
    HIGH = "HIGH"                    # High crowding
    EXTREME = "EXTREME"              # Extreme crowding (danger zone)


class ContrarianAction(Enum):
    """Contrarian trading action"""
    ACCUMULATE = "ACCUMULATE"                    # Buy when others are fearful
    HOLD = "HOLD"                                # Hold current position
    WATCH_FOR_PULLBACK = "WATCH_FOR_PULLBACK"    # Be cautious, watch for reversal
    EXIT = "EXIT"                                # Sell/short when euphoric


@dataclass
class ContrarySignalAnalysis:
    """
    Result of contrary signal analysis

    Attributes:
        symbol: Symbol being analyzed
        crowding_level: Current crowding level
        flow_z_score: Z-score of fund flows
        sentiment_extreme: Whether sentiment is extreme
        sentiment_direction: Direction of extreme sentiment (BULLISH/BEARISH/NEUTRAL)
        position_skew: Position skew (-1 to 1, negative=short skew, positive=long skew)
        contrarian_action: Recommended contrarian action
        reasoning: Explanation of analysis
    """
    symbol: str
    crowding_level: CrowdingLevel
    flow_z_score: float
    sentiment_extreme: bool
    sentiment_direction: str
    position_skew: float
    contrarian_action: ContrarianAction
    reasoning: str = ""
    confidence: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "crowding_level": self.crowding_level.value,
            "flow_z_score": self.flow_z_score,
            "sentiment_extreme": self.sentiment_extreme,
            "sentiment_direction": self.sentiment_direction,
            "position_skew": self.position_skew,
            "contrarian_action": self.contrarian_action.value,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
        }


# ============================================================================
# Main Component
# ============================================================================

class ContrarySignal(BaseIntelligence):
    """
    Contrary Signal Detector

    Detects market crowding and generates contrarian trading signals when
    sentiment becomes extreme through fund flow analysis, sentiment detection,
    and position skew calculation.

    Key Features:
    1. Calculates Z-score of ETF fund flows
    2. Detects extreme sentiment values
    3. Calculates position skew (long vs short)
    4. Determines crowding level
    5. Generates contrarian trading actions

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.contrary_signal import ContrarySignal

        llm = get_llm_provider()
        detector = ContrarySignal(
            llm_provider=llm,
            market_data_client=market_client,
        )

        # Analyze contrary signal for a symbol
        result = await detector.analyze_contrary_signal("NVDA", days=30)

        if result.data["contrarian_action"] == "EXIT":
            print("Extreme crowding - consider exiting long position")
    """

    # Z-score thresholds
    Z_SCORE_MEDIUM = 1.0         # Medium crowding threshold
    Z_SCORE_HIGH = 2.0           # High crowding threshold
    Z_SCORE_EXTREME = 3.0        # Extreme crowding threshold

    # Sentiment thresholds
    SENTIMENT_EXTREME_BULLISH = 0.85   # Above = extreme bullish
    SENTIMENT_EXTREME_BEARISH = 0.15   # Below = extreme bearish

    # Position skew thresholds
    SKEW_MEDIUM = 0.5            # Medium skew threshold
    SKEW_HIGH = 0.7              # High skew threshold
    SKEW_EXTREME = 0.85          # Extreme skew threshold

    def __init__(
        self,
        llm_provider: LLMProvider,
        market_data_client: Optional[Any] = None,
    ):
        """
        Initialize ContrarySignal

        Args:
            llm_provider: LLM Provider instance
            market_data_client: Market data API client for flows/sentiment/positions
        """
        super().__init__(
            name="ContrarySignal",
            phase=IntelligencePhase.P1,
        )

        self.llm = llm_provider
        self.market_data_client = market_data_client

        # Statistics
        self._analysis_count = 0
        self._extreme_signal_count = 0

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Analyze and detect crowding (main entry point)

        Args:
            data: Data with symbol and days parameters

        Returns:
            IntelligenceResult: Contrary signal analysis result
        """
        symbol = data.get("symbol", "")
        days = data.get("days", 30)
        return await self.analyze_contrary_signal(symbol, days)

    async def analyze_contrary_signal(
        self,
        symbol: str,
        days: int = 30,
    ) -> IntelligenceResult:
        """
        Analyze contrary signal for a symbol

        Args:
            symbol: Symbol to analyze (e.g., "NVDA", "SOXX")
            days: Number of days to analyze (default: 30)

        Returns:
            IntelligenceResult: Contrary signal analysis with action
        """
        try:
            # Validate input
            if not symbol or not symbol.strip():
                return self.create_result(
                    success=False,
                    data={"stage": "contrary_signal"},
                    reasoning="Symbol is required",
                )

            # Get fund flow data
            flow_z_score = 0.0
            if self.market_data_client:
                try:
                    flow_data = await self.market_data_client.get_etf_flows(symbol, days)
                    if flow_data:
                        flow_z_score = self._calculate_flow_z_score(flow_data)
                except Exception as e:
                    logger.warning(f"Failed to get flow data: {e}")

            # Get sentiment data
            sentiment_extreme = False
            sentiment_direction = "NEUTRAL"
            if self.market_data_client:
                try:
                    sentiment_data = await self.market_data_client.get_sentiment_history(symbol, days)
                    if sentiment_data:
                        extreme_result = self._detect_sentiment_extreme(sentiment_data)
                        sentiment_extreme = extreme_result["is_extreme"]
                        sentiment_direction = extreme_result.get("direction", "NEUTRAL")
                except Exception as e:
                    logger.warning(f"Failed to get sentiment data: {e}")

            # Get position data
            position_skew = 0.0
            if self.market_data_client:
                try:
                    position_data = await self.market_data_client.get_position_data(symbol)
                    if position_data:
                        position_skew = self._calculate_position_skew(position_data)
                except Exception as e:
                    logger.warning(f"Failed to get position data: {e}")

            # Determine crowding level
            crowding_level = self._determine_crowding_level(
                flow_z_score, sentiment_extreme, position_skew
            )

            # Generate contrarian action
            contrarian_action = self._generate_contrarian_action(
                crowding_level, sentiment_direction
            )

            # Build reasoning
            reasoning = self._build_reasoning(
                symbol, crowding_level, flow_z_score, sentiment_extreme,
                sentiment_direction, position_skew, contrarian_action
            )

            # Calculate confidence
            confidence = self._calculate_confidence(days, flow_z_score, sentiment_extreme)

            # Update statistics
            self._analysis_count += 1
            if crowding_level in [CrowdingLevel.HIGH, CrowdingLevel.EXTREME]:
                self._extreme_signal_count += 1

            return self.create_result(
                success=True,
                data={
                    "stage": "contrary_signal",
                    "crowding_level": crowding_level.value,
                    "flow_z_score": flow_z_score,
                    "sentiment_extreme": sentiment_extreme,
                    "sentiment_direction": sentiment_direction,
                    "position_skew": position_skew,
                    "contrarian_action": contrarian_action.value,
                    "confidence": confidence,
                },
                confidence=confidence,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Contrary signal analysis error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "contrary_signal"},
            )
            result.add_error(f"Analysis error: {str(e)}")
            return result

    def _calculate_flow_z_score(self, flow_data: List[Dict[str, Any]]) -> float:
        """
        Calculate Z-score of fund flows

        Args:
            flow_data: List of flow data points

        Returns:
            float: Z-score of the most recent flow
        """
        if len(flow_data) < 3:
            return 0.0

        flows = [f.get("flow", 0) for f in flow_data]

        try:
            mean = statistics.mean(flows)
            stdev = statistics.stdev(flows) if len(flows) > 1 else 0

            if stdev == 0:
                return 0.0

            # Calculate Z-score for most recent flow
            latest_flow = flows[-1]
            z_score = (latest_flow - mean) / stdev

            # Cap at reasonable values
            return max(-10.0, min(10.0, z_score))

        except statistics.StatisticsError:
            return 0.0

    def _detect_sentiment_extreme(self, sentiment_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect if sentiment is at extreme levels

        Args:
            sentiment_data: List of sentiment data points

        Returns:
            Dict with is_extreme, direction, magnitude
        """
        if len(sentiment_data) < 3:
            return {"is_extreme": False, "direction": "NEUTRAL", "magnitude": 0.0}

        # Get recent sentiment values (last 5 days)
        recent_sentiments = [s.get("sentiment", 0.5) for s in sentiment_data[-5:]]

        # Calculate average recent sentiment
        avg_sentiment = statistics.mean(recent_sentiments)

        # Determine if extreme
        is_extreme = False
        direction = "NEUTRAL"
        magnitude = 0.0

        if avg_sentiment >= self.SENTIMENT_EXTREME_BULLISH:
            is_extreme = True
            direction = "BULLISH"
            magnitude = avg_sentiment
        elif avg_sentiment <= self.SENTIMENT_EXTREME_BEARISH:
            is_extreme = True
            direction = "BEARISH"
            magnitude = 1.0 - avg_sentiment

        return {
            "is_extreme": is_extreme,
            "direction": direction,
            "magnitude": magnitude,
        }

    def _calculate_position_skew(self, position_data: Dict[str, Any]) -> float:
        """
        Calculate position skew (long vs short bias)

        Args:
            position_data: Position data with long_positions and short_positions

        Returns:
            float: Skew score (-1 to 1)
                   -1 = all short, 0 = balanced, 1 = all long
        """
        long_positions = position_data.get("long_positions", 0)
        short_positions = position_data.get("short_positions", 0)
        total_positions = position_data.get("total_positions", 1)

        if total_positions == 0:
            return 0.0

        # Calculate skew: (long - short) / total
        skew = (long_positions - short_positions) / total_positions

        return max(-1.0, min(1.0, skew))

    def _determine_crowding_level(
        self,
        flow_z_score: float,
        sentiment_extreme: bool,
        position_skew: float,
    ) -> CrowdingLevel:
        """
        Determine crowding level based on multiple indicators

        Args:
            flow_z_score: Z-score of fund flows
            sentiment_extreme: Whether sentiment is extreme
            position_skew: Position skew score

        Returns:
            CrowdingLevel: Determined crowding level
        """
        # Calculate crowding score (0-1)
        crowding_score = 0.0

        # Flow contribution (40%)
        flow_contribution = min(1.0, abs(flow_z_score) / self.Z_SCORE_EXTREME)
        crowding_score += 0.4 * flow_contribution

        # Sentiment contribution (30%)
        if sentiment_extreme:
            crowding_score += 0.3

        # Position skew contribution (30%)
        skew_contribution = min(1.0, abs(position_skew) / self.SKEW_EXTREME)
        crowding_score += 0.3 * skew_contribution

        # Determine level based on score
        if crowding_score < 0.3:
            return CrowdingLevel.LOW
        elif crowding_score < 0.5:
            return CrowdingLevel.MEDIUM
        elif crowding_score < 0.7:
            return CrowdingLevel.HIGH
        else:
            return CrowdingLevel.EXTREME

    def _generate_contrarian_action(
        self,
        crowding_level: CrowdingLevel,
        sentiment_direction: str,
    ) -> ContrarianAction:
        """
        Generate contrarian trading action

        Args:
            crowding_level: Current crowding level
            sentiment_direction: Direction of sentiment

        Returns:
            ContrarianAction: Recommended action
        """
        if crowding_level == CrowdingLevel.LOW:
            # Low crowding - depends on sentiment
            if sentiment_direction == "BEARISH":
                return ContrarianAction.ACCUMULATE  # Buy when fearful
            return ContrarianAction.HOLD

        elif crowding_level == CrowdingLevel.MEDIUM:
            return ContrarianAction.HOLD

        elif crowding_level == CrowdingLevel.HIGH:
            # High crowding - be cautious
            if sentiment_direction == "BULLISH":
                return ContrarianAction.WATCH_FOR_PULLBACK
            return ContrarianAction.HOLD

        elif crowding_level == CrowdingLevel.EXTREME:
            # Extreme crowding - exit or short
            if sentiment_direction == "BULLISH":
                return ContrarianAction.EXIT  # Euphoria - exit
            elif sentiment_direction == "BEARISH":
                return ContrarianAction.ACCUMULATE  # Panic - buy
            return ContrarianAction.HOLD

        return ContrarianAction.HOLD

    def _build_reasoning(
        self,
        symbol: str,
        crowding_level: CrowdingLevel,
        flow_z_score: float,
        sentiment_extreme: bool,
        sentiment_direction: str,
        position_skew: float,
        action: ContrarianAction,
    ) -> str:
        """Build human-readable reasoning"""
        parts = []

        # Symbol and crowding
        parts.append(f"Symbol: {symbol}")
        parts.append(f"Crowding: {crowding_level.value}")

        # Flow analysis
        if abs(flow_z_score) > 1.0:
            parts.append(f"Flow Z-Score: {flow_z_score:.2f} ({'Inflow' if flow_z_score > 0 else 'Outflow'} anomaly)")

        # Sentiment analysis
        if sentiment_extreme:
            parts.append(f"Sentiment: Extreme {sentiment_direction}")

        # Position skew
        if abs(position_skew) > 0.3:
            skew_desc = "Long-biased" if position_skew > 0 else "Short-biased"
            parts.append(f"Position: {skew_desc} ({abs(position_skew):.0%})")

        # Action
        parts.append(f"Action: {action.value}")

        return " | ".join(parts)

    def _calculate_confidence(
        self,
        days: int,
        flow_z_score: float,
        sentiment_extreme: bool,
    ) -> float:
        """Calculate confidence in analysis"""
        confidence = 0.5  # Base confidence

        # More data = higher confidence
        if days >= 30:
            confidence += 0.2
        elif days >= 14:
            confidence += 0.1

        # Extreme signals = higher confidence
        if abs(flow_z_score) > 2.0:
            confidence += 0.15
        if sentiment_extreme:
            confidence += 0.15

        return min(1.0, confidence)

    def get_statistics(self) -> Dict[str, Any]:
        """Get signal detection statistics"""
        extreme_rate = (
            self._extreme_signal_count / self._analysis_count
            if self._analysis_count > 0
            else 0
        )

        return {
            "total_analyses": self._analysis_count,
            "extreme_signals": self._extreme_signal_count,
            "extreme_signal_rate": round(extreme_rate, 3),
        }


# ============================================================================
# Factory function
# ============================================================================

def create_contrary_signal(
    llm_provider: Optional[LLMProvider] = None,
    market_data_client: Optional[Any] = None,
) -> ContrarySignal:
    """
    Create ContrarySignal instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        market_data_client: Market data API client

    Returns:
        ContrarySignal: Configured detector instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return ContrarySignal(
        llm_provider=llm_provider,
        market_data_client=market_data_client,
    )
