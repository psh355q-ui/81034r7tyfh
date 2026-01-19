"""
NarrativeFatigue Component - Theme Overheating Detection

Market Intelligence v2.0 - Phase 2, T2.1

This component detects when narratives become overplayed/lose impact by analyzing
mention growth, price response, and new info ratio to generate contrarian signals.

Key Features:
1. Fatigue score calculation (mention growth - price response - new info ratio)
2. Fatigue phase detection (EARLY, ACCELERATING, CONSENSUS, MATURE, FATIGUED)
3. Volume and coverage analysis
4. Contrarian signal generation
5. Fatigue trend and acceleration detection

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

class FatiguePhase(Enum):
    """Narrative fatigue phase"""
    EARLY = "EARLY"                      # New narrative, low fatigue
    ACCELERATING = "ACCELERATING"        # Gaining momentum
    CONSENSUS = "CONSENSUS"              # Market consensus forming
    MATURE = "MATURE"                    # Established narrative
    FATIGUED = "FATIGUED"                # Overplayed, losing impact
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class FatigueSignal(Enum):
    """Contrarian signal strength"""
    NONE = "NONE"                        # No signal
    CAUTION = "CAUTION"                  # Be cautious
    REVERSAL = "REVERSAL"                # Potential reversal
    STRONG_REVERSAL = "STRONG_REVERSAL"  # High probability reversal


@dataclass
class FatigueAnalysis:
    """
    Result of narrative fatigue analysis

    Attributes:
        theme: Theme being analyzed
        fatigue_score: Composite fatigue score (0-1)
        fatigue_phase: Current fatigue phase
        mention_growth: Mention growth rate
        price_response: Price response score
        new_info_ratio: New information ratio
        signal: Contrarian trading signal
        reasoning: Explanation of fatigue analysis
    """
    theme: str
    fatigue_score: float
    fatigue_phase: FatiguePhase
    mention_growth: float
    price_response: float
    new_info_ratio: float
    signal: FatigueSignal
    reasoning: str = ""
    confidence: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "theme": self.theme,
            "fatigue_score": self.fatigue_score,
            "fatigue_phase": self.fatigue_phase.value,
            "mention_growth": self.mention_growth,
            "price_response": self.price_response,
            "new_info_ratio": self.new_info_ratio,
            "signal": self.signal.value,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
        }


# ============================================================================
# Main Component
# ============================================================================

class NarrativeFatigue(BaseIntelligence):
    """
    Narrative Fatigue Detector

    Detects when narratives become overplayed/lose impact through analysis of
    mention growth, price response, and new info ratio.

    Key Features:
    1. Calculates composite fatigue score
    2. Detects fatigue phase (EARLY → FATIGUED)
    3. Generates contrarian trading signals
    4. Analyzes volume and coverage patterns
    5. Tracks fatigue trends and acceleration

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.narrative_fatigue import NarrativeFatigue

        llm = get_llm_provider()
        detector = NarrativeFatigue(
            llm_provider=llm,
            news_repository=news_repo,
            market_data_client=market_client,
        )

        # Analyze fatigue for a theme
        result = await detector.analyze_fatigue("AI Semiconductor", days=30)

        if result.data["fatigue_phase"] == "FATIGUED":
            print("Theme is overplayed - consider contrarian position")
    """

    # Fatigue thresholds
    FATIGUE_THRESHOLD_LOW = 0.3      # Below = EARLY/ACCELERATING
    FATIGUE_THRESHOLD_MEDIUM = 0.5   # Below = CONSENSUS
    FATIGUE_THRESHOLD_HIGH = 0.7     # Below = MATURE, Above = FATIGUED
    FATIGUE_THRESHOLD_EXTREME = 0.9  # Above = STRONG_REVERSAL

    # Mention growth thresholds
    MENTION_GROWTH_LOW = 0.5         # 50% growth = low
    MENTION_GROWTH_HIGH = 2.0        # 200% growth = high

    # Price response thresholds
    PRICE_RESPONSE_WEAK = 0.3        # Below = weak response (fatigue sign)
    PRICE_RESPONSE_STRONG = 0.7      # Above = strong response

    # New info ratio thresholds
    NEW_INFO_LOW = 0.2               # Below = repetitive (fatigue sign)
    NEW_INFO_HIGH = 0.6              # Above = fresh content

    def __init__(
        self,
        llm_provider: LLMProvider,
        news_repository: Optional[Any] = None,
        market_data_client: Optional[Any] = None,
    ):
        """
        Initialize NarrativeFatigue

        Args:
            llm_provider: LLM Provider instance
            news_repository: News repository for article data
            market_data_client: Market data API client
        """
        super().__init__(
            name="NarrativeFatigue",
            phase=IntelligencePhase.P1,
        )

        self.llm = llm_provider
        self.news_repository = news_repository
        self.market_data_client = market_data_client

        # Statistics
        self._analysis_count = 0
        self._fatigue_detected_count = 0

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Analyze and detect fatigue (main entry point)

        Args:
            data: Data with theme and days parameters

        Returns:
            IntelligenceResult: Fatigue analysis result
        """
        theme = data.get("theme", "")
        days = data.get("days", 30)
        return await self.analyze_fatigue(theme, days)

    async def analyze_fatigue(
        self,
        theme: str,
        days: int = 30,
    ) -> IntelligenceResult:
        """
        Analyze narrative fatigue for a theme

        Args:
            theme: Theme to analyze (e.g., "AI Semiconductor", "Defense")
            days: Number of days to analyze (default: 30)

        Returns:
            IntelligenceResult: Fatigue analysis with phase and signal
        """
        try:
            # Validate input
            if not theme or not theme.strip():
                return self.create_result(
                    success=False,
                    data={"stage": "narrative_fatigue"},
                    reasoning="Theme name is required",
                )

            # Get mention data
            mention_data = await self._get_mention_data(theme, days)
            if not mention_data or mention_data.get("total_mentions", 0) == 0:
                return self.create_result(
                    success=True,
                    data={
                        "stage": "narrative_fatigue",
                        "fatigue_phase": "INSUFFICIENT_DATA",
                        "fatigue_score": 0.0,
                        "signal": "NONE",
                        "reasoning": f"No news data found for theme: {theme}",
                    },
                    confidence=0.0,
                    reasoning=f"Insufficient data for theme: {theme}",
                )

            # Calculate mention growth
            mention_growth = self._calculate_mention_growth_from_data(mention_data)

            # Get market performance
            market_data = await self._get_market_data(theme)
            price_response = self._calculate_price_response(market_data)

            # Calculate new info ratio (simplified - would use embeddings in production)
            new_info_ratio = self._calculate_new_info_ratio_simple(mention_data)

            # Calculate composite fatigue score
            fatigue_score = self._calculate_fatigue_score(
                mention_growth, price_response, new_info_ratio
            )

            # Determine fatigue phase
            fatigue_phase = self._determine_fatigue_phase(fatigue_score, mention_growth, price_response)

            # Generate contrarian signal
            signal = self._generate_contrarian_signal(fatigue_score, fatigue_phase)

            # Build reasoning
            reasoning = self._build_reasoning(
                theme, fatigue_score, fatigue_phase, mention_growth,
                price_response, new_info_ratio, signal
            )

            # Calculate confidence based on data quality
            confidence = self._calculate_confidence(mention_data, days)

            # Update statistics
            self._analysis_count += 1
            if fatigue_phase in [FatiguePhase.FATIGUED, FatiguePhase.MATURE]:
                self._fatigue_detected_count += 1

            return self.create_result(
                success=True,
                data={
                    "stage": "narrative_fatigue",
                    "fatigue_score": fatigue_score,
                    "fatigue_phase": fatigue_phase.value,
                    "mention_growth": mention_growth,
                    "price_response": price_response,
                    "new_info_ratio": new_info_ratio,
                    "signal": signal.value,
                    "total_mentions": mention_data.get("total_mentions", 0),
                    "daily_average": mention_data.get("daily_average", 0),
                    "confidence": confidence,
                },
                confidence=confidence,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Narrative fatigue analysis error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "narrative_fatigue"},
            )
            result.add_error(f"Analysis error: {str(e)}")
            return result

    async def _get_mention_data(self, theme: str, days: int) -> Optional[Dict[str, Any]]:
        """Get mention data for theme"""
        try:
            if self.news_repository is None:
                return None

            articles = await self.news_repository.get_articles_by_theme(theme, days)
            if not articles:
                return None

            # Calculate mention statistics
            total_mentions = sum(a.get("count", 1) for a in articles)
            daily_average = total_mentions / len(articles) if articles else 0

            # Find peak day
            peak_day = max(articles, key=lambda x: x.get("count", 0), default={})

            return {
                "articles": articles,
                "total_mentions": total_mentions,
                "daily_average": daily_average,
                "peak_day": peak_day,
            }

        except Exception as e:
            logger.error(f"Error getting mention data: {e}")
            return None

    async def _get_market_data(self, theme: str) -> Dict[str, Any]:
        """Get market performance data for theme"""
        try:
            if self.market_data_client is None:
                # Return default values if no market data client
                return {
                    "total_return": 10.0,
                    "recent_return": 2.0,
                    "volume_trend": "NEUTRAL",
                }

            return await self.market_data_client.get_theme_performance(theme, "1mo")

        except Exception as e:
            logger.warning(f"Error getting market data: {e}")
            return {
                "total_return": 0.0,
                "recent_return": 0.0,
                "volume_trend": "UNKNOWN",
            }

    def _calculate_mention_growth_from_data(self, mention_data: Dict[str, Any]) -> float:
        """Calculate mention growth rate from data"""
        articles = mention_data.get("articles", [])
        if len(articles) < 2:
            return 0.0

        # Calculate growth rate (simple linear regression slope approximation)
        counts = [a.get("count", 0) for a in articles]
        if len(counts) < 2:
            return 0.0

        # Simple growth rate: (latest - earliest) / earliest
        earliest = counts[0] if counts[0] > 0 else 1
        latest = counts[-1]

        growth_rate = (latest - earliest) / earliest

        # Normalize to 0-3 range (0% to 300% growth)
        return max(0.0, min(3.0, growth_rate))

    def _calculate_mention_growth(self, mention_history: List[float]) -> float:
        """Calculate mention growth rate from list of counts"""
        if len(mention_history) < 2:
            return 0.0

        earliest = mention_history[0] if mention_history[0] > 0 else 1
        latest = mention_history[-1]

        growth_rate = (latest - earliest) / earliest

        # Cap at reasonable values
        return max(0.0, min(10.0, growth_rate))

    def _calculate_price_response(self, market_data: Dict[str, Any]) -> float:
        """
        Calculate price response score

        High recent returns relative to total returns = strong response (low fatigue)
        Low recent returns relative to total returns = weak response (high fatigue)
        """
        total_return = market_data.get("total_return", 0.0)
        recent_return = market_data.get("recent_return", 0.0)

        if total_return == 0:
            return 0.5  # Neutral

        # Calculate ratio of recent to total return
        # If recent_return is much smaller than total_return/periods, response is weakening
        response_ratio = abs(recent_return) / (abs(total_return) + 0.01)

        # Normalize to 0-1 range
        # High ratio = strong response, Low ratio = weak response (fatigue)
        return max(0.0, min(1.0, response_ratio))

    def _calculate_new_info_ratio_simple(self, mention_data: Dict[str, Any]) -> float:
        """
        Calculate new info ratio (simplified version)

        In production, this would use embeddings to detect semantic similarity.
        For now, we use a heuristic based on mention distribution.
        """
        articles = mention_data.get("articles", [])
        if len(articles) < 2:
            return 0.5  # Neutral

        counts = [a.get("count", 0) for a in articles]

        # Calculate variance (low variance = repetitive, high variance = diverse)
        if len(counts) < 2:
            return 0.5

        try:
            mean = statistics.mean(counts)
            if mean == 0:
                return 0.5  # Neutral instead of 0

            # Coefficient of variation (normalized variance)
            cv = statistics.stdev(counts) / mean if len(counts) > 1 else 0

            # If all values are the same (cv = 0), treat as neutral (not repetitive)
            if cv == 0:
                return 0.5  # Neutral - consistent but not necessarily repetitive

            # Higher variance = more diverse/new info
            # Normalize to 0-1 range
            return max(0.0, min(1.0, cv / 2.0))

        except statistics.StatisticsError:
            return 0.5

    def _calculate_new_info_ratio(self, article_embeddings: List[List[float]]) -> float:
        """
        Calculate new info ratio using embeddings

        Low semantic similarity = high new info
        High semantic similarity = low new info (repetitive)
        """
        if len(article_embeddings) < 2:
            return 0.5

        # Calculate average pairwise cosine similarity
        # Simplified: for demonstration, we'll use a heuristic
        # In production, use actual cosine similarity

        # For now, return a mock value
        return 0.3

    def _calculate_fatigue_score(
        self,
        mention_growth: float,
        price_response: float,
        new_info_ratio: float,
    ) -> float:
        """
        Calculate composite fatigue score

        Formula components:
        - High mention growth: increases fatigue
        - Low price response: increases fatigue
        - Low new info ratio: increases fatigue

        Returns:
            float: Fatigue score (0-1, higher = more fatigue)
        """
        # Normalize components to 0-1 range
        normalized_growth = min(1.0, mention_growth / 3.0)  # 300% growth = max
        normalized_response = price_response  # Already 0-1
        normalized_new_info = new_info_ratio  # Already 0-1

        # Composite score:
        # Fatigue = (0.4 * growth) + (0.3 * (1 - response)) + (0.3 * (1 - new_info))
        # High growth = high fatigue
        # Low response = high fatigue
        # Low new info = high fatigue

        fatigue_score = (
            0.4 * normalized_growth +
            0.3 * (1.0 - normalized_response) +
            0.3 * (1.0 - normalized_new_info)
        )

        return max(0.0, min(1.0, fatigue_score))

    def _determine_fatigue_phase(
        self,
        fatigue_score: float,
        mention_growth: float,
        price_response: float,
    ) -> FatiguePhase:
        """Determine fatigue phase based on metrics"""
        if fatigue_score < self.FATIGUE_THRESHOLD_LOW:
            # Low fatigue
            if mention_growth > self.MENTION_GROWTH_HIGH:
                return FatiguePhase.ACCELERATING
            return FatiguePhase.EARLY

        elif fatigue_score < self.FATIGUE_THRESHOLD_MEDIUM:
            return FatiguePhase.CONSENSUS

        elif fatigue_score < self.FATIGUE_THRESHOLD_HIGH:
            return FatiguePhase.MATURE

        else:
            # High fatigue
            return FatiguePhase.FATIGUED

    def _generate_contrarian_signal(
        self,
        fatigue_score: float,
        phase: FatiguePhase,
    ) -> FatigueSignal:
        """Generate contrarian trading signal"""
        if phase == FatiguePhase.EARLY or phase == FatiguePhase.ACCELERATING:
            return FatigueSignal.NONE

        elif phase == FatiguePhase.CONSENSUS:
            return FatigueSignal.CAUTION

        elif phase == FatiguePhase.MATURE:
            if fatigue_score > 0.6:
                return FatigueSignal.CAUTION
            return FatigueSignal.NONE

        elif phase == FatiguePhase.FATIGUED:
            if fatigue_score > self.FATIGUE_THRESHOLD_EXTREME:
                return FatigueSignal.STRONG_REVERSAL
            return FatigueSignal.REVERSAL

        return FatigueSignal.NONE

    def _build_reasoning(
        self,
        theme: str,
        fatigue_score: float,
        phase: FatiguePhase,
        mention_growth: float,
        price_response: float,
        new_info_ratio: float,
        signal: FatigueSignal,
    ) -> str:
        """Build human-readable reasoning"""
        parts = []

        # Theme and phase
        parts.append(f"Theme: {theme}")
        parts.append(f"Phase: {phase.value}")

        # Metrics
        parts.append(f"Mention Growth: {mention_growth:.1%}")
        parts.append(f"Price Response: {price_response:.2f}")

        # Fatigue assessment
        if fatigue_score < 0.3:
            parts.append("Narrative is early - low fatigue")
        elif fatigue_score < 0.5:
            parts.append("Narrative gaining consensus - moderate fatigue")
        elif fatigue_score < 0.7:
            parts.append("Narrative is mature - elevated fatigue")
        else:
            parts.append("Narrative is overplayed - high fatigue")

        # Signal
        if signal != FatigueSignal.NONE:
            parts.append(f"Signal: {signal.value}")

        return " | ".join(parts)

    def _calculate_confidence(self, mention_data: Optional[Dict[str, Any]], days: int) -> float:
        """Calculate confidence in analysis based on data quality"""
        if not mention_data:
            return 0.0

        total_mentions = mention_data.get("total_mentions", 0)

        # Low confidence if insufficient data
        if total_mentions < 10:
            return 0.3
        if total_mentions < 50:
            return 0.5

        # Low confidence if short time period
        if days < 7:
            return 0.4
        if days < 14:
            return 0.6

        return 0.8

    async def _analyze_coverage(self, theme: str, days: int) -> Dict[str, Any]:
        """Analyze media coverage intensity"""
        mention_data = await self._get_mention_data(theme, days)
        if not mention_data:
            return {
                "total_mentions": 0,
                "daily_average": 0,
                "peak_day": None,
            }

        return {
            "total_mentions": mention_data.get("total_mentions", 0),
            "daily_average": mention_data.get("daily_average", 0),
            "peak_day": mention_data.get("peak_day"),
        }

    def _detect_volume_anomaly(
        self,
        current_volume: float,
        normal_volume: float,
    ) -> Dict[str, Any]:
        """Detect volume anomaly"""
        if normal_volume == 0:
            return {"is_anomalous": False, "ratio": 0}

        ratio = current_volume / normal_volume

        return {
            "is_anomalous": ratio > 2.0,  # 2x normal = anomaly
            "ratio": ratio,
        }

    def _calculate_fatigue_trend(self, fatigue_history: List[float]) -> Dict[str, Any]:
        """Calculate fatigue trend over time"""
        if len(fatigue_history) < 2:
            return {"direction": "UNKNOWN", "rate": 0}

        # Simple linear trend
        earliest = fatigue_history[0]
        latest = fatigue_history[-1]

        change = latest - earliest

        if change > 0.1:
            direction = "INCREASING"
        elif change < -0.1:
            direction = "DECREASING"
        else:
            direction = "STABLE"

        return {
            "direction": direction,
            "rate": change / len(fatigue_history),
        }

    def _detect_fatigue_acceleration(self, fatigue_history: List[float]) -> Dict[str, Any]:
        """Detect if fatigue is accelerating"""
        if len(fatigue_history) < 3:
            return {"is_accelerating": False, "acceleration_rate": 0}

        # Calculate second derivative (rate of change of rate of change)
        changes = [
            fatigue_history[i] - fatigue_history[i-1]
            for i in range(1, len(fatigue_history))
        ]

        if len(changes) < 2:
            return {"is_accelerating": False, "acceleration_rate": 0}

        acceleration = changes[-1] - changes[0]

        return {
            "is_accelerating": acceleration > 0.05,
            "acceleration_rate": acceleration,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get fatigue detection statistics"""
        fatigue_rate = (
            self._fatigue_detected_count / self._analysis_count
            if self._analysis_count > 0
            else 0
        )

        return {
            "total_analyses": self._analysis_count,
            "fatigue_detected": self._fatigue_detected_count,
            "fatigue_rate": round(fatigue_rate, 3),
        }


# ============================================================================
# Factory function
# ============================================================================

def create_narrative_fatigue(
    llm_provider: Optional[LLMProvider] = None,
    news_repository: Optional[Any] = None,
    market_data_client: Optional[Any] = None,
) -> NarrativeFatigue:
    """
    Create NarrativeFatigue instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        news_repository: News repository for article data
        market_data_client: Market data API client

    Returns:
        NarrativeFatigue: Configured detector instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return NarrativeFatigue(
        llm_provider=llm_provider,
        news_repository=news_repository,
        market_data_client=market_data_client,
    )
