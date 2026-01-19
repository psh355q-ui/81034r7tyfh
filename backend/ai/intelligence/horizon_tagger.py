"""
HorizonTagger Component - Time Horizon Separation

Market Intelligence v2.0 - Phase 2, T2.3

This component separates insights by time horizon to provide different
perspectives for traders (short-term), swing traders (mid-term), and
thematic investors (long-term).

Key Features:
1. Short-term horizon analysis (1-5 days, trader focus)
2. Mid-term horizon analysis (2-6 weeks, swing trading focus)
3. Long-term horizon analysis (6-18 months, thematic investing focus)
4. Horizon-specific insight generation
5. Recommended horizon determination

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from .base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ..llm_providers import LLMProvider


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class TimeHorizon(Enum):
    """Time horizon for trading/investing"""
    SHORT = "SHORT"    # 1-5 days (trading)
    MID = "MID"        # 2-6 weeks (swing)
    LONG = "LONG"      # 6-18 months (thematic)

    @property
    def days_min(self) -> int:
        """Minimum days for this horizon"""
        if self == TimeHorizon.SHORT:
            return 1
        return 14  # ~2 weeks for MID/LONG

    @property
    def days_max(self) -> int:
        """Maximum days for this horizon"""
        if self == TimeHorizon.SHORT:
            return 5
        if self == TimeHorizon.MID:
            return 42  # 6 weeks
        return 540  # 18 months

    @property
    def weeks_min(self) -> int:
        """Minimum weeks for this horizon"""
        if self == TimeHorizon.MID:
            return 2
        return 26  # 6 months for LONG

    @property
    def weeks_max(self) -> int:
        """Maximum weeks for this horizon"""
        if self == TimeHorizon.MID:
            return 6
        return 78  # 18 months

    @property
    def months_min(self) -> int:
        """Minimum months for this horizon"""
        if self == TimeHorizon.LONG:
            return 6
        return 1  # ~4 weeks for SHORT

    @property
    def months_max(self) -> int:
        """Maximum months for this horizon"""
        if self == TimeHorizon.LONG:
            return 18
        return 1  # ~4 weeks for SHORT


@dataclass
class HorizonInsight:
    """
    Insight for a specific time horizon

    Attributes:
        horizon: Time horizon (SHORT/MID/LONG)
        timeframe_days: Timeframe in days
        timeframe_weeks: Timeframe in weeks (for MID)
        timeframe_months: Timeframe in months (for LONG)
        analysis: Horizon-specific analysis text
        confidence: Confidence in this horizon's analysis
        key_points: Key points for this horizon
    """
    horizon: TimeHorizon
    timeframe_days: int = 0
    timeframe_weeks: int = 0
    timeframe_months: int = 0
    analysis: str = ""
    confidence: float = 0.8
    key_points: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "horizon": self.horizon.value,
            "timeframe_days": self.timeframe_days,
            "timeframe_weeks": self.timeframe_weeks,
            "timeframe_months": self.timeframe_months,
            "analysis": self.analysis,
            "confidence": self.confidence,
            "key_points": self.key_points,
        }


@dataclass
class HorizonAnalysis:
    """
    Result of horizon tagging analysis

    Attributes:
        topic: Topic being analyzed
        short_term: Short-term insight
        mid_term: Mid-term insight
        long_term: Long-term insight
        recommended_horizon: Recommended primary horizon
        reasoning: Explanation of recommendation
    """
    topic: str
    short_term: Optional[HorizonInsight] = None
    mid_term: Optional[HorizonInsight] = None
    long_term: Optional[HorizonInsight] = None
    recommended_horizon: TimeHorizon = TimeHorizon.MID
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "topic": self.topic,
            "short_term": self.short_term.to_dict() if self.short_term else None,
            "mid_term": self.mid_term.to_dict() if self.mid_term else None,
            "long_term": self.long_term.to_dict() if self.long_term else None,
            "recommended_horizon": self.recommended_horizon.value,
            "reasoning": self.reasoning,
        }


# ============================================================================
# Main Component
# ============================================================================

class HorizonTagger(BaseIntelligence):
    """
    Horizon Tagger

    Separates insights by time horizon to provide different perspectives
    for traders (short-term), swing traders (mid-term), and thematic
    investors (long-term).

    Key Features:
    1. Short-term: 1-5 days, catalyst-driven, technical-focused
    2. Mid-term: 2-6 weeks, trend-driven, momentum-focused
    3. Long-term: 6-18 months, fundamental-driven, thesis-focused
    4. Recommends primary horizon based on insight characteristics

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.horizon_tagger import HorizonTagger

        llm = get_llm_provider()
        tagger = HorizonTagger(
            llm_provider=llm,
            market_data_client=market_client,
        )

        # Tag horizons for an insight
        result = await tagger.tag_horizons({
            "topic": "NVDA AI Chip Demand",
            "sentiment": "BULLISH",
            "catalyst": "Earnings surprise",
        })

        short_analysis = result.data["short_term"]["analysis"]
    """

    # Confidence thresholds
    MIN_CONFIDENCE = 0.3
    DEFAULT_CONFIDENCE = 0.7

    def __init__(
        self,
        llm_provider: LLMProvider,
        market_data_client: Optional[Any] = None,
    ):
        """
        Initialize HorizonTagger

        Args:
            llm_provider: LLM Provider instance
            market_data_client: Market data API client (optional)
        """
        super().__init__(
            name="HorizonTagger",
            phase=IntelligencePhase.P1,
        )

        self.llm = llm_provider
        self.market_data_client = market_data_client

        # Statistics
        self._analysis_count = 0
        self._horizon_distribution = {
            "SHORT": 0,
            "MID": 0,
            "LONG": 0,
        }

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Analyze and tag horizons (main entry point)

        Args:
            data: Insight data with topic and context

        Returns:
            IntelligenceResult: Horizon tagging result
        """
        return await self.tag_horizons(data)

    async def tag_horizons(
        self,
        insight: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Tag insight with time horizon perspectives

        Args:
            insight: Insight data with:
                - topic: Insight topic
                - sentiment: BULLISH/BEARISH/NEUTRAL
                - catalyst: (optional) Catalyst event
                - trend: (optional) Trend direction
                - theme: (optional) Thematic focus

        Returns:
            IntelligenceResult: Horizon analysis with all perspectives
        """
        try:
            # Validate input
            if not insight:
                insight = {}

            topic = insight.get("topic", "Unknown Topic")

            # Analyze for each horizon
            short_term = await self._analyze_short_term(insight)
            mid_term = await self._analyze_mid_term(insight)
            long_term = await self._analyze_long_term(insight)

            # Determine recommended horizon
            recommended = self._determine_recommended_horizon(
                insight, short_term, mid_term, long_term
            )

            # Calculate confidences
            short_confidence = short_term.confidence if short_term else 0.0
            mid_confidence = mid_term.confidence if mid_term else 0.0
            long_confidence = long_term.confidence if long_term else 0.0

            # Build reasoning
            reasoning = self._build_reasoning(
                topic, recommended, short_term, mid_term, long_term
            )

            # Update statistics
            self._analysis_count += 1
            self._horizon_distribution[recommended.value] += 1

            return self.create_result(
                success=True,
                data={
                    "stage": "horizon_tagging",
                    "short_term": short_term.to_dict() if short_term else None,
                    "mid_term": mid_term.to_dict() if mid_term else None,
                    "long_term": long_term.to_dict() if long_term else None,
                    "recommended_horizon": recommended.value,
                    "short_confidence": short_confidence,
                    "mid_confidence": mid_confidence,
                    "long_confidence": long_confidence,
                },
                confidence=max(short_confidence, mid_confidence, long_confidence),
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Horizon tagging error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "horizon_tagging"},
            )
            result.add_error(f"Tagging error: {str(e)}")
            return result

    async def _analyze_short_term(self, insight: Dict[str, Any]) -> Optional[HorizonInsight]:
        """
        Analyze short-term (1-5 days) perspective

        Focus: Catalyst-driven, technical-focused
        """
        try:
            # Build prompt for short-term analysis
            topic = insight.get("topic", "")
            catalyst = insight.get("catalyst", "")
            sentiment = insight.get("sentiment", "NEUTRAL")

            system_prompt = """You are a short-term trading analyst.
Focus on 1-5 day trading opportunities driven by catalysts and technicals."""

            user_prompt = f"""Analyze this insight for SHORT-TERM trading (1-5 days):

Topic: {topic}
Sentiment: {sentiment}
Catalyst: {catalyst if catalyst else "Not specified"}

Provide:
1. Trading setup (entry/exit levels)
2. Key catalyst or driver
3. Risk factors
4. Expected timeframe (1-5 days)

Keep it concise and actionable."""

            response = await self.llm.complete_with_system(system_prompt, user_prompt)

            # Calculate confidence based on catalyst presence
            confidence = self.DEFAULT_CONFIDENCE
            if catalyst:
                confidence = min(1.0, confidence + 0.15)
            if insight.get("technical_breakout"):
                confidence = min(1.0, confidence + 0.1)

            return HorizonInsight(
                horizon=TimeHorizon.SHORT,
                timeframe_days=3,  # Default 3 days
                analysis=response.content,
                confidence=confidence,
            )

        except Exception as e:
            logger.error(f"Short-term analysis error: {e}")
            return HorizonInsight(
                horizon=TimeHorizon.SHORT,
                timeframe_days=3,
                analysis=f"Error: {str(e)}",
                confidence=0.0,
            )

    async def _analyze_mid_term(self, insight: Dict[str, Any]) -> Optional[HorizonInsight]:
        """
        Analyze mid-term (2-6 weeks) perspective

        Focus: Trend-driven, momentum-focused
        """
        try:
            topic = insight.get("topic", "")
            trend = insight.get("trend", "")
            sentiment = insight.get("sentiment", "NEUTRAL")

            system_prompt = """You are a swing trading analyst.
Focus on 2-6 week swing plays driven by trends and momentum."""

            user_prompt = f"""Analyze this insight for MID-TERM trading (2-6 weeks):

Topic: {topic}
Sentiment: {sentiment}
Trend: {trend if trend else "Not specified"}

Provide:
1. Momentum assessment
2. Trend analysis
3. Price target
4. Expected timeframe (2-6 weeks)

Keep it concise and focused on trend continuation."""

            response = await self.llm.complete_with_system(system_prompt, user_prompt)

            # Calculate confidence based on trend strength
            confidence = self.DEFAULT_CONFIDENCE
            if trend and trend in ["BULLISH", "BEARISH"]:
                confidence = min(1.0, confidence + 0.1)
            if insight.get("trend_strength") == "STRONG":
                confidence = min(1.0, confidence + 0.1)

            return HorizonInsight(
                horizon=TimeHorizon.MID,
                timeframe_weeks=4,  # Default 4 weeks
                analysis=response.content,
                confidence=confidence,
            )

        except Exception as e:
            logger.error(f"Mid-term analysis error: {e}")
            return HorizonInsight(
                horizon=TimeHorizon.MID,
                timeframe_weeks=4,
                analysis=f"Error: {str(e)}",
                confidence=0.0,
            )

    async def _analyze_long_term(self, insight: Dict[str, Any]) -> Optional[HorizonInsight]:
        """
        Analyze long-term (6-18 months) perspective

        Focus: Fundamental-driven, thesis-focused
        """
        try:
            topic = insight.get("topic", "")
            theme = insight.get("theme", "")
            sentiment = insight.get("sentiment", "NEUTRAL")

            system_prompt = """You are a thematic investment analyst.
Focus on 6-18 month positions driven by fundamentals and thesis."""

            user_prompt = f"""Analyze this insight for LONG-TERM investing (6-18 months):

Topic: {topic}
Theme: {theme if theme else "Not specified"}
Sentiment: {sentiment}

Provide:
1. Investment thesis
2. Fundamental analysis
3. Growth drivers
4. Valuation assessment
5. Expected timeframe (6-18 months)

Keep it concise and focused on long-term value creation."""

            response = await self.llm.complete_with_system(system_prompt, user_prompt)

            # Calculate confidence based on theme presence
            confidence = self.DEFAULT_CONFIDENCE
            if theme:
                confidence = min(1.0, confidence + 0.15)
            if insight.get("fundamental_strength") == "STRONG":
                confidence = min(1.0, confidence + 0.1)

            return HorizonInsight(
                horizon=TimeHorizon.LONG,
                timeframe_months=12,  # Default 12 months
                analysis=response.content,
                confidence=confidence,
            )

        except Exception as e:
            logger.error(f"Long-term analysis error: {e}")
            return HorizonInsight(
                horizon=TimeHorizon.LONG,
                timeframe_months=12,
                analysis=f"Error: {str(e)}",
                confidence=0.0,
            )

    def _determine_recommended_horizon(
        self,
        insight: Dict[str, Any],
        short_term: Optional[HorizonInsight],
        mid_term: Optional[HorizonInsight],
        long_term: Optional[HorizonInsight],
    ) -> TimeHorizon:
        """
        Determine recommended primary horizon

        Logic:
        - Catalyst present → SHORT
        - Strong trend but no catalyst → MID
        - Thematic/fundamental focus → LONG
        """
        # Check for catalyst (prioritize SHORT)
        if insight.get("catalyst") or insight.get("technical_breakout"):
            return TimeHorizon.SHORT

        # Check for theme (prioritize LONG)
        if insight.get("theme") or insight.get("fundamental_strength"):
            return TimeHorizon.LONG

        # Check for trend (prioritize MID)
        if insight.get("trend") or insight.get("trend_strength"):
            return TimeHorizon.MID

        # Default to MID
        return TimeHorizon.MID

    def _build_reasoning(
        self,
        topic: str,
        recommended: TimeHorizon,
        short_term: Optional[HorizonInsight],
        mid_term: Optional[HorizonInsight],
        long_term: Optional[HorizonInsight],
    ) -> str:
        """Build human-readable reasoning"""
        parts = []

        parts.append(f"Topic: {topic}")
        parts.append(f"Recommended: {recommended.value}")

        # Add confidence summary
        confidences = []
        if short_term:
            confidences.append(f"SHORT: {short_term.confidence:.0%}")
        if mid_term:
            confidences.append(f"MID: {mid_term.confidence:.0%}")
        if long_term:
            confidences.append(f"LONG: {long_term.confidence:.0%}")

        if confidences:
            parts.append(f"Confidence: {', '.join(confidences)}")

        return " | ".join(parts)

    def get_statistics(self) -> Dict[str, Any]:
        """Get horizon tagging statistics"""
        total = self._analysis_count
        if total == 0:
            return {
                "total_analyses": 0,
                "short_pct": 0.0,
                "mid_pct": 0.0,
                "long_pct": 0.0,
            }

        return {
            "total_analyses": total,
            "short_pct": round(self._horizon_distribution["SHORT"] / total, 3),
            "mid_pct": round(self._horizon_distribution["MID"] / total, 3),
            "long_pct": round(self._horizon_distribution["LONG"] / total, 3),
        }


# ============================================================================
# Factory function
# ============================================================================

def create_horizon_tagger(
    llm_provider: Optional[LLMProvider] = None,
    market_data_client: Optional[Any] = None,
) -> HorizonTagger:
    """
    Create HorizonTagger instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        market_data_client: Market data API client

    Returns:
        HorizonTagger: Configured tagger instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return HorizonTagger(
        llm_provider=llm_provider,
        market_data_client=market_data_client,
    )
