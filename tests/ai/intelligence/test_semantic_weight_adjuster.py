"""
SemanticWeightAdjuster Tests

Market Intelligence v2.0 - Phase 4, T4.2

Tests for the Semantic Weight Adjuster component that prevents over-interpretation
of market narratives by adjusting semantic weights based on narrative intensity
and market novelty.

Key Features:
1. Semantic weight calculation (narrative_intensity / market_novelty)
2. Weight adjustment to prevent over-interpretation
3. Novelty decay tracking
4. Narrative intensity measurement
5. Market confirmation integration

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from backend.ai.intelligence.semantic_weight_adjuster import (
    SemanticWeightAdjuster,
    SemanticWeight,
    NoveltyLevel,
    NarrativeIntensity,
)
from backend.ai.intelligence.base import IntelligenceResult
from backend.ai.llm_providers import LLMProvider


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    class MockLLM:
        async def complete_with_system(self, system_prompt: str, user_prompt: str, config=None):
            from backend.ai.llm_providers import LLMResponse, ModelProvider

            # Return semantic analysis
            content = """**Semantic Analysis:**

**Narrative Intensity:** HIGH (0.8)
- The narrative is being discussed extensively
- Multiple sources covering the story
- Strong emotional sentiment detected

**Market Novelty:** MEDIUM (0.5)
- Story has been circulating for 2 weeks
- Some price action already occurred
- Partially priced in by market

**Recommended Weight:** 0.6 (reduced from 0.9)
**Reasoning:** High narrative intensity but medium novelty suggests potential over-interpretation."""

            return LLMResponse(
                content=content,
                model="mock",
                provider=ModelProvider.MOCK,
                tokens_used=50,
                latency_ms=50,
            )

        def create_stage1_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK)

        def create_stage2_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK)

    return MockLLM()


@pytest.fixture
def mock_narrative_state():
    """Mock narrative state engine"""
    class MockNarrativeState:
        async def get_narrative_intensity(self, theme: str) -> Dict[str, Any]:
            """Get narrative intensity for a theme"""
            return {
                "theme": theme,
                "mention_count": 150,
                "sentiment_strength": 0.8,
                "source_diversity": 0.7,
                "intensity_score": 0.75,
            }

        async def get_novelty_level(self, theme: str) -> Dict[str, Any]:
            """Get novelty level for a theme"""
            return {
                "theme": theme,
                "novelty_score": 0.5,
                "days_in_market": 14,
                "price_action": "PARTIALLY_PRICED",
                "level": "MEDIUM",
            }

    return MockNarrativeState()


@pytest.fixture
def semantic_weight_adjuster(mock_llm, mock_narrative_state):
    """Create SemanticWeightAdjuster instance"""
    return SemanticWeightAdjuster(
        llm_provider=mock_llm,
        narrative_state=mock_narrative_state,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestSemanticWeightAdjusterBasic:
    """Test basic SemanticWeightAdjuster functionality"""

    def test_initialization(self, semantic_weight_adjuster):
        """Test adjuster initializes correctly"""
        assert semantic_weight_adjuster.name == "SemanticWeightAdjuster"
        assert semantic_weight_adjuster.phase.value == "P2"
        assert semantic_weight_adjuster._enabled is True

    @pytest.mark.asyncio
    async def test_calculate_semantic_weight(self, semantic_weight_adjuster):
        """Test semantic weight calculation"""
        data = {
            "theme": "AI Semiconductor",
            "narrative_intensity": 0.8,
            "market_novelty": 0.5,
        }

        result = await semantic_weight_adjuster.calculate_weight(data)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "semantic_weight" in result.data


# ============================================================================
# Test: Semantic Weight Formula
# ============================================================================

class TestSemanticWeightFormula:
    """Test semantic weight formula: narrative_intensity / market_novelty"""

    @pytest.mark.asyncio
    async def test_weight_formula_components(self, semantic_weight_adjuster):
        """Test weight = narrative_intensity / market_novelty"""
        data = {
            "theme": "AI Semiconductor",
            "narrative_intensity": 0.8,
            "market_novelty": 0.5,
        }

        result = await semantic_weight_adjuster.calculate_weight(data)

        # Expected: 0.8 / 0.5 = 1.6, but capped at 1.0
        # Then adjusted for over-interpretation prevention
        assert 0.0 <= result.data["semantic_weight"] <= 1.0

    @pytest.mark.asyncio
    async def test_high_intensity_low_novelty(self, semantic_weight_adjuster):
        """Test high narrative intensity with low market novelty"""
        data = {
            "theme": "New AI Breakthrough",
            "narrative_intensity": 0.9,
            "market_novelty": 0.2,  # Very new
        }

        result = await semantic_weight_adjuster.calculate_weight(data)

        # High intensity / Low novelty = High weight (but may be adjusted)
        assert result.data["semantic_weight"] >= 0.5

    @pytest.mark.asyncio
    async def test_low_intensity_high_novelty(self, semantic_weight_adjuster):
        """Test low narrative intensity with high market novelty"""
        data = {
            "theme": "Niche Sector Rotation",
            "narrative_intensity": 0.3,
            "market_novelty": 0.8,  # Old story
        }

        result = await semantic_weight_adjuster.calculate_weight(data)

        # Low intensity / High novelty = Low weight
        assert result.data["semantic_weight"] <= 0.5

    @pytest.mark.asyncio
    async def test_balanced_intensity_and_novelty(self, semantic_weight_adjuster):
        """Test balanced intensity and novelty"""
        data = {
            "theme": "Balanced Tech Story",
            "narrative_intensity": 0.5,
            "market_novelty": 0.5,
        }

        result = await semantic_weight_adjuster.calculate_weight(data)

        # Balanced = 0.5/0.5 = 1.0, capped at MAX_WEIGHT
        assert result.data["semantic_weight"] == 1.0


# ============================================================================
# Test: Weight Adjustment
# ============================================================================

class TestWeightAdjustment:
    """Test weight adjustment to prevent over-interpretation"""

    @pytest.mark.asyncio
    async def test_adjust_weight_down_for_over_interpretation(self, semantic_weight_adjuster):
        """Test that weight is reduced for over-interpreted narratives"""
        data = {
            "theme": "Hyped AI Story",
            "narrative_intensity": 0.9,  # Very high
            "market_novelty": 0.3,  # Low novelty (old story)
            "original_confidence": 0.85,
        }

        result = await semantic_weight_adjuster.adjust_weight(data)

        assert result.success is True
        assert result.data["adjusted_weight"] < data["original_confidence"]

    @pytest.mark.asyncio
    async def test_no_adjustment_for_fresh_narrative(self, semantic_weight_adjuster):
        """Test that fresh narratives maintain weight"""
        data = {
            "theme": "Breaking News",
            "narrative_intensity": 0.7,
            "market_novelty": 0.9,  # High novelty (fresh)
            "original_confidence": 0.75,
        }

        result = await semantic_weight_adjuster.adjust_weight(data)

        # Should maintain or slightly reduce weight
        assert result.data["adjusted_weight"] >= 0.6


# ============================================================================
# Test: Novelty Level Enum
# ============================================================================

class TestNoveltyLevel:
    """Test NoveltyLevel enum"""

    def test_high_novelty(self):
        """Test HIGH novelty level"""
        level = NoveltyLevel.HIGH
        assert level.value == "HIGH"

    def test_medium_novelty(self):
        """Test MEDIUM novelty level"""
        level = NoveltyLevel.MEDIUM
        assert level.value == "MEDIUM"

    def test_low_novelty(self):
        """Test LOW novelty level"""
        level = NoveltyLevel.LOW
        assert level.value == "LOW"


# ============================================================================
# Test: Narrative Intensity
# ============================================================================

class TestNarrativeIntensity:
    """Test NarrativeIntensity data class"""

    def test_narrative_intensity_creation(self):
        """Test creating NarrativeIntensity"""
        intensity = NarrativeIntensity(
            theme="AI Semiconductor",
            mention_count=150,
            sentiment_strength=0.8,
            source_diversity=0.7,
            intensity_score=0.75,
        )

        assert intensity.theme == "AI Semiconductor"
        assert intensity.intensity_score == 0.75

    def test_narrative_intensity_to_dict(self):
        """Test converting NarrativeIntensity to dictionary"""
        intensity = NarrativeIntensity(
            theme="Defense",
            mention_count=80,
            sentiment_strength=0.6,
            source_diversity=0.5,
            intensity_score=0.55,
        )

        intensity_dict = intensity.to_dict()

        assert isinstance(intensity_dict, dict)
        assert intensity_dict["intensity_score"] == 0.55


# ============================================================================
# Test: Semantic Weight Data Class
# ============================================================================

class TestSemanticWeight:
    """Test SemanticWeight data class"""

    def test_semantic_weight_creation(self):
        """Test creating SemanticWeight"""
        weight = SemanticWeight(
            theme="AI Semiconductor",
            weight=0.75,
            narrative_intensity=0.8,
            market_novelty=0.5,
            adjustment_factor=1.0,
            calculated_at=datetime.now(),
        )

        assert weight.theme == "AI Semiconductor"
        assert weight.weight == 0.75

    def test_semantic_weight_to_dict(self):
        """Test converting SemanticWeight to dictionary"""
        weight = SemanticWeight(
            theme="Defense",
            weight=0.6,
            narrative_intensity=0.7,
            market_novelty=0.4,
            adjustment_factor=0.85,
            calculated_at=datetime.now(),
        )

        weight_dict = weight.to_dict()

        assert isinstance(weight_dict, dict)
        assert weight_dict["weight"] == 0.6


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestSemanticWeightAdjusterEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_zero_market_novelty(self, semantic_weight_adjuster):
        """Test handling of zero market novelty (division by zero)"""
        data = {
            "theme": "Test Theme",
            "narrative_intensity": 0.5,
            "market_novelty": 0.0,  # Would cause division by zero
        }

        result = await semantic_weight_adjuster.calculate_weight(data)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_extreme_values(self, semantic_weight_adjuster):
        """Test handling of extreme values"""
        data = {
            "theme": "Extreme Case",
            "narrative_intensity": 1.0,
            "market_novelty": 0.01,  # Almost zero
        }

        result = await semantic_weight_adjuster.calculate_weight(data)

        # Should handle gracefully
        assert 0.0 <= result.data["semantic_weight"] <= 1.0

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, semantic_weight_adjuster):
        """Test handling of LLM errors"""
        class ErrorLLM:
            async def complete_with_system(self, system_prompt, user_prompt, config=None):
                raise Exception("LLM Error")

        original_llm = semantic_weight_adjuster.llm
        semantic_weight_adjuster.llm = ErrorLLM()

        data = {"theme": "Test", "narrative_intensity": 0.5}

        result = await semantic_weight_adjuster.calculate_weight(data)

        # Restore original
        semantic_weight_adjuster.llm = original_llm

        # Should handle error gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_empty_theme(self, semantic_weight_adjuster):
        """Test handling of empty theme"""
        data = {
            "theme": "",
            "narrative_intensity": 0.5,
            "market_novelty": 0.5,
        }

        result = await semantic_weight_adjuster.calculate_weight(data)

        # Should handle gracefully
        assert result is not None


# ============================================================================
# Test: Decay Tracking
# ============================================================================

class TestDecayTracking:
    """Test novelty decay over time"""

    @pytest.mark.asyncio
    async def test_track_novelty_decay(self, semantic_weight_adjuster):
        """Test tracking novelty decay over time"""
        data = {
            "theme": "Aging Narrative",
            "days_in_market": 30,  # 1 month old
            "initial_novelty": 0.9,
        }

        result = await semantic_weight_adjuster.calculate_decay(data)

        assert result.success is True
        assert "decayed_novelty" in result.data
        assert result.data["decayed_novelty"] < data["initial_novelty"]

    @pytest.mark.asyncio
    async def test_fresh_narrative_no_decay(self, semantic_weight_adjuster):
        """Test that fresh narratives have minimal decay"""
        data = {
            "theme": "Fresh Breaking News",
            "days_in_market": 1,  # 1 day old
            "initial_novelty": 0.95,
        }

        result = await semantic_weight_adjuster.calculate_decay(data)

        assert result.success is True
        # Should have minimal decay
        assert result.data["decayed_novelty"] >= 0.85


# ============================================================================
# Test: Integration with Market Confirmation
# ============================================================================

class TestMarketConfirmationIntegration:
    """Test integration with market confirmation"""

    @pytest.mark.asyncio
    async def test_adjust_weight_based_on_confirmation(self, semantic_weight_adjuster):
        """Test that confirmed narratives get weight boost"""
        data = {
            "theme": "Confirmed AI Trend",
            "narrative_intensity": 0.7,
            "market_novelty": 0.5,
            "market_confirmation": "CONFIRMED",  # Price action confirms narrative
        }

        result = await semantic_weight_adjuster.adjust_weight(data)

        assert result.success is True
        # Confirmed narratives should have higher weight
        assert result.data["adjustment_factor"] >= 0.8

    @pytest.mark.asyncio
    async def test_reduce_weight_for_contradicted_narrative(self, semantic_weight_adjuster):
        """Test that contradicted narratives get weight reduction"""
        data = {
            "theme": "Contradicted Story",
            "narrative_intensity": 0.7,
            "market_novelty": 0.5,
            "market_confirmation": "CONTRADICTED",  # Price action contradicts
        }

        result = await semantic_weight_adjuster.adjust_weight(data)

        assert result.success is True
        # Contradicted narratives should have reduced weight (0.8 - 0.25 = 0.55, but min is 0.3, so stays at 0.55)
        assert result.data["adjustment_factor"] <= 0.8


# ============================================================================
# Test: Batch Weight Calculation
# ============================================================================

class TestBatchWeightCalculation:
    """Test batch calculation for multiple themes"""

    @pytest.mark.asyncio
    async def test_calculate_multiple_weights(self, semantic_weight_adjuster):
        """Test calculating weights for multiple themes"""
        data = {
            "themes": [
                {"theme": "AI", "narrative_intensity": 0.8, "market_novelty": 0.5},
                {"theme": "Defense", "narrative_intensity": 0.6, "market_novelty": 0.7},
                {"theme": "EV", "narrative_intensity": 0.4, "market_novelty": 0.6},
            ]
        }

        result = await semantic_weight_adjuster.calculate_weights_batch(data)

        assert result.success is True
        assert "weights" in result.data
        assert len(result.data["weights"]) == 3


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
