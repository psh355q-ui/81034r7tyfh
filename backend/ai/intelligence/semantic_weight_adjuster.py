"""
SemanticWeightAdjuster Component - Prevent Over-Interpretation

Market Intelligence v2.0 - Phase 4, T4.2

This component prevents over-interpretation of market narratives by adjusting
semantic weights based on narrative intensity and market novelty.

Key Features:
1. Semantic weight calculation (narrative_intensity / market_novelty)
2. Weight adjustment to prevent over-interpretation
3. Novelty decay tracking
4. Narrative intensity measurement
5. Market confirmation integration

Formula: semantic_weight = narrative_intensity / market_novelty
- High intensity + Low novelty = Reduce weight (prevent over-interpretation)
- Low intensity + High novelty = Maintain weight (fresh signals OK)

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ..llm_providers import LLMProvider


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class NoveltyLevel(Enum):
    """Market novelty level"""
    HIGH = "HIGH"  # Fresh narrative, new to market
    MEDIUM = "MEDIUM"  # Some market awareness
    LOW = "LOW"  # Widely known, fully priced in


@dataclass
class NarrativeIntensity:
    """
    Narrative intensity metrics

    Attributes:
        theme: Theme or topic
        mention_count: Number of mentions
        sentiment_strength: Strength of sentiment (0-1)
        source_diversity: Diversity of sources (0-1)
        intensity_score: Overall intensity score (0-1)
    """
    theme: str
    mention_count: int
    sentiment_strength: float
    source_diversity: float
    intensity_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "theme": self.theme,
            "mention_count": self.mention_count,
            "sentiment_strength": self.sentiment_strength,
            "source_diversity": self.source_diversity,
            "intensity_score": self.intensity_score,
        }


@dataclass
class SemanticWeight:
    """
    Semantic weight for a narrative

    Attributes:
        theme: Theme or topic
        weight: Calculated weight (0-1)
        narrative_intensity: Narrative intensity score
        market_novelty: Market novelty score
        adjustment_factor: Adjustment factor applied
        calculated_at: Calculation timestamp
    """
    theme: str
    weight: float
    narrative_intensity: float
    market_novelty: float
    adjustment_factor: float
    calculated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "theme": self.theme,
            "weight": self.weight,
            "narrative_intensity": self.narrative_intensity,
            "market_novelty": self.market_novelty,
            "adjustment_factor": self.adjustment_factor,
            "calculated_at": self.calculated_at.isoformat(),
        }


# ============================================================================
# Main Component
# ============================================================================

class SemanticWeightAdjuster(BaseIntelligence):
    """
    Semantic Weight Adjuster

    Prevents over-interpretation of market narratives by adjusting
    semantic weights based on narrative intensity and market novelty.

    Key Features:
    1. Calculates semantic weight using formula: intensity / novelty
    2. Reduces weight for over-interpreted narratives
    3. Tracks novelty decay over time
    4. Integrates with market confirmation
    5. Batch processing for multiple themes

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.semantic_weight_adjuster import SemanticWeightAdjuster

        llm = get_llm_provider()
        adjuster = SemanticWeightAdjuster(
            llm_provider=llm,
            narrative_state=narrative_engine,
        )

        # Calculate weight for a theme
        result = await adjuster.calculate_weight({
            "theme": "AI Semiconductor",
            "narrative_intensity": 0.8,
            "market_novelty": 0.5,
        })

        # Adjust based on over-interpretation risk
        adjusted = await adjuster.adjust_weight({
            "theme": "AI Semiconductor",
            "original_confidence": 0.85,
            "narrative_intensity": 0.8,
            "market_novelty": 0.3,  # Low novelty = over-interpreted
        })
    """

    # Constants
    MIN_NOVELTY = 0.1  # Minimum novelty to prevent division by zero
    MAX_WEIGHT = 1.0  # Maximum weight
    OVER_INTERPRETATION_THRESHOLD = 0.6  # Threshold for reducing weight
    DECAY_RATE = 0.02  # Daily novelty decay rate

    def __init__(
        self,
        llm_provider: LLMProvider,
        narrative_state: Optional[Any] = None,
    ):
        """
        Initialize SemanticWeightAdjuster

        Args:
            llm_provider: LLM Provider instance
            narrative_state: Narrative state engine (optional)
        """
        super().__init__(
            name="SemanticWeightAdjuster",
            phase=IntelligencePhase.P2,
        )

        self.llm = llm_provider
        self.narrative_state = narrative_state

        # Statistics
        self._calculation_count = 0
        self._adjustment_count = 0

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Calculate semantic weight (main entry point)

        Args:
            data: Weight calculation data

        Returns:
            IntelligenceResult: Weight calculation result
        """
        return await self.calculate_weight(data)

    async def calculate_weight(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Calculate semantic weight using formula: intensity / novelty

        Args:
            data: Calculation data with:
                - theme: Theme or topic
                - narrative_intensity: Narrative intensity (0-1)
                - market_novelty: Market novelty (0-1)

        Returns:
            IntelligenceResult: Weight calculation result
        """
        try:
            self._calculation_count += 1

            theme = data.get("theme", "")
            intensity = data.get("narrative_intensity", 0.5)
            novelty = data.get("market_novelty", 0.5)

            # Prevent division by zero
            novelty = max(novelty, self.MIN_NOVELTY)

            # Calculate base weight
            base_weight = intensity / novelty

            # Cap at maximum
            base_weight = min(base_weight, self.MAX_WEIGHT)

            # Determine adjustment factor based on over-interpretation risk
            adjustment_factor = self._calculate_adjustment_factor(intensity, novelty)

            # Apply adjustment
            final_weight = base_weight * adjustment_factor

            # Create semantic weight object
            semantic_weight = SemanticWeight(
                theme=theme,
                weight=final_weight,
                narrative_intensity=intensity,
                market_novelty=novelty,
                adjustment_factor=adjustment_factor,
                calculated_at=datetime.now(),
            )

            return self.create_result(
                success=True,
                data={
                    "stage": "weight_calculation",
                    "theme": theme,
                    "semantic_weight": final_weight,
                    "base_weight": base_weight,
                    "adjustment_factor": adjustment_factor,
                    "narrative_intensity": intensity,
                    "market_novelty": novelty,
                },
                reasoning=f"Calculated weight {final_weight:.2f} for {theme} (intensity: {intensity:.2f}, novelty: {novelty:.2f})",
            )

        except Exception as e:
            logger.error(f"Weight calculation error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "weight_calculation"},
            )
            result.add_error(f"Calculation error: {str(e)}")
            return result

    async def adjust_weight(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Adjust weight to prevent over-interpretation

        Args:
            data: Adjustment data with:
                - theme: Theme or topic
                - original_confidence: Original confidence level
                - narrative_intensity: Narrative intensity
                - market_novelty: Market novelty
                - market_confirmation: Market confirmation status (optional)

        Returns:
            IntelligenceResult: Adjustment result
        """
        try:
            self._adjustment_count += 1

            theme = data.get("theme", "")
            original_confidence = data.get("original_confidence", 0.7)
            intensity = data.get("narrative_intensity", 0.5)
            novelty = data.get("market_novelty", 0.5)
            confirmation = data.get("market_confirmation", "NEUTRAL")

            # Calculate adjustment factor
            adjustment_factor = self._calculate_adjustment_factor(intensity, novelty)

            # Adjust based on market confirmation
            if confirmation == "CONFIRMED":
                # Boost weight for confirmed narratives
                adjustment_factor = min(1.0, adjustment_factor + 0.15)
            elif confirmation == "CONTRADICTED":
                # Reduce weight for contradicted narratives
                adjustment_factor = max(0.3, adjustment_factor - 0.25)

            # Apply adjustment
            adjusted_weight = original_confidence * adjustment_factor

            return self.create_result(
                success=True,
                data={
                    "stage": "weight_adjustment",
                    "theme": theme,
                    "original_confidence": original_confidence,
                    "adjusted_weight": adjusted_weight,
                    "adjustment_factor": adjustment_factor,
                    "market_confirmation": confirmation,
                },
                reasoning=f"Adjusted confidence from {original_confidence:.2f} to {adjusted_weight:.2f} based on semantic factors",
            )

        except Exception as e:
            logger.error(f"Weight adjustment error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "weight_adjustment"},
            )
            result.add_error(f"Adjustment error: {str(e)}")
            return result

    async def calculate_decay(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Calculate novelty decay over time

        Args:
            data: Decay data with:
                - theme: Theme or topic
                - days_in_market: Days since narrative entered market
                - initial_novelty: Initial novelty score

        Returns:
            IntelligenceResult: Decay calculation result
        """
        try:
            theme = data.get("theme", "")
            days_in_market = data.get("days_in_market", 0)
            initial_novelty = data.get("initial_novelty", 1.0)

            # Calculate decay
            decay_amount = days_in_market * self.DECAY_RATE
            decayed_novelty = max(0.1, initial_novelty - decay_amount)

            return self.create_result(
                success=True,
                data={
                    "stage": "decay_calculation",
                    "theme": theme,
                    "days_in_market": days_in_market,
                    "initial_novelty": initial_novelty,
                    "decayed_novelty": decayed_novelty,
                    "decay_amount": decay_amount,
                },
                reasoning=f"Novelty decayed from {initial_novelty:.2f} to {decayed_novelty:.2f} over {days_in_market} days",
            )

        except Exception as e:
            logger.error(f"Decay calculation error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "decay_calculation"},
            )
            result.add_error(f"Decay error: {str(e)}")
            return result

    async def calculate_weights_batch(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Calculate weights for multiple themes in batch

        Args:
            data: Batch data with:
                - themes: List of theme data dictionaries

        Returns:
            IntelligenceResult: Batch calculation result
        """
        try:
            themes_data = data.get("themes", [])
            weights = []

            for theme_data in themes_data:
                result = await self.calculate_weight(theme_data)
                if result.success:
                    weights.append({
                        "theme": theme_data.get("theme", ""),
                        "weight": result.data["semantic_weight"],
                        "adjustment_factor": result.data.get("adjustment_factor", 1.0),
                    })

            return self.create_result(
                success=True,
                data={
                    "stage": "batch_calculation",
                    "weights": weights,
                    "total_themes": len(themes_data),
                },
                reasoning=f"Calculated weights for {len(weights)} themes",
            )

        except Exception as e:
            logger.error(f"Batch calculation error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "batch_calculation"},
            )
            result.add_error(f"Batch error: {str(e)}")
            return result

    def _calculate_adjustment_factor(
        self,
        intensity: float,
        novelty: float,
    ) -> float:
        """
        Calculate adjustment factor based on over-interpretation risk

        High intensity + Low novelty = High risk of over-interpretation
        """
        # Calculate over-interpretation risk
        # High intensity (close to 1.0) with low novelty (close to 0) = high risk
        over_interpretation_risk = intensity * (1.0 - novelty)

        if over_interpretation_risk >= self.OVER_INTERPRETATION_THRESHOLD:
            # Reduce weight significantly
            return 0.6
        elif over_interpretation_risk >= 0.4:
            # Moderate reduction
            return 0.8
        else:
            # Minimal or no adjustment
            return 1.0

    def get_statistics(self) -> Dict[str, Any]:
        """Get semantic weight adjuster statistics"""
        return {
            "total_calculations": self._calculation_count,
            "total_adjustments": self._adjustment_count,
        }


# ============================================================================
# Factory function
# ============================================================================

def create_semantic_weight_adjuster(
    llm_provider: Optional[LLMProvider] = None,
    narrative_state: Optional[Any] = None,
) -> SemanticWeightAdjuster:
    """
    Create SemanticWeightAdjuster instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        narrative_state: Narrative state engine

    Returns:
        SemanticWeightAdjuster: Configured adjuster instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return SemanticWeightAdjuster(
        llm_provider=llm_provider,
        narrative_state=narrative_state,
    )
