"""
HorizonTagger Tests

Market Intelligence v2.0 - Phase 2, T2.3

Tests for the Horizon Tagger component that separates insights by time horizon
(short-term trading, mid-term swing, long-term thematic investing).

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

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta

from backend.ai.intelligence.horizon_tagger import (
    HorizonTagger,
    TimeHorizon,
    HorizonInsight,
    HorizonAnalysis,
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

            # Return horizon-specific analysis based on prompt
            if "short" in user_prompt.lower():
                content = "Short-term: Focus on 1-5 day trading opportunities. Key catalyst: Earnings surprise expected. Technical: Breaking resistance at $165."
            elif "mid" in user_prompt.lower():
                content = "Mid-term: 2-6 week swing play. Trend: Momentum building post-earnings. Target: $180 based on analyst upgrades."
            elif "long" in user_prompt.lower():
                content = "Long-term: 6-18 month thematic position. Thesis: AI semiconductor demand growth catalyst. Valuation: PEG ratio attractive for growth."
            else:
                content = "Comprehensive analysis across all time horizons."

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
def mock_market_data():
    """Mock market data provider"""
    class MockMarketDataProvider:
        async def get_technical_indicators(self, symbol: str):
            """Return mock technical indicators"""
            return {
                "symbol": symbol,
                "rsi": 65.0,
                "macd": 0.5,
                "trend": "BULLISH",
                "support": 150.0,
                "resistance": 175.0,
            }

        async def get_fundamental_data(self, symbol: str):
            """Return mock fundamental data"""
            return {
                "symbol": symbol,
                "pe_ratio": 35.0,
                "peg_ratio": 1.2,
                "revenue_growth": 0.25,
                "debt_to_equity": 0.3,
            }

        async def get_option_flows(self, symbol: str, days: int = 5):
            """Return mock option flow data"""
            return {
                "symbol": symbol,
                "call_premium": 150_000_000,
                "put_premium": 50_000_000,
                "implied_volatility": 0.35,
            }

    return MockMarketDataProvider()


@pytest.fixture
def horizon_tagger(mock_llm, mock_market_data):
    """Create HorizonTagger instance"""
    return HorizonTagger(
        llm_provider=mock_llm,
        market_data_client=mock_market_data,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestHorizonTaggerBasic:
    """Test basic HorizonTagger functionality"""

    def test_initialization(self, horizon_tagger):
        """Test tagger initializes correctly"""
        assert horizon_tagger.name == "HorizonTagger"
        assert horizon_tagger.phase.value == "P1"
        assert horizon_tagger._enabled is True

    @pytest.mark.asyncio
    async def test_tag_horizons(self, horizon_tagger):
        """Test horizon tagging for an insight"""
        insight = {
            "topic": "NVDA AI Chip Demand",
            "sentiment": "BULLISH",
            "symbols": ["NVDA"],
            "key_points": ["Data center revenue growth", "AI infrastructure spending"],
        }

        result = await horizon_tagger.tag_horizons(insight)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "short_term" in result.data
        assert "mid_term" in result.data
        assert "long_term" in result.data
        assert "recommended_horizon" in result.data


# ============================================================================
# Test: Short-Term Horizon Analysis
# ============================================================================

class TestShortTermHorizon:
    """Test short-term horizon (1-5 days) analysis"""

    @pytest.mark.asyncio
    async def test_analyze_short_term_trading_setup(self, horizon_tagger):
        """Test short-term trading setup analysis"""
        insight = {
            "topic": "NVDA Earnings Beat",
            "sentiment": "BULLISH",
            "catalyst": "Earnings surprise",
            "technical_breakout": True,
        }

        short_term = await horizon_tagger._analyze_short_term(insight)

        assert isinstance(short_term, HorizonInsight)
        assert short_term.horizon == TimeHorizon.SHORT
        assert short_term.timeframe_days >= 1
        assert short_term.timeframe_days <= 5
        assert "trading_setup" in short_term.analysis.lower() or "catalyst" in short_term.analysis.lower()

    @pytest.mark.asyncio
    async def test_short_term_focus_on_technicals(self, horizon_tagger):
        """Test that short-term focuses on technical indicators"""
        insight = {
            "topic": "NVDA Breakout",
            "technical_breakout": True,
        }

        short_term = await horizon_tagger._analyze_short_term(insight)

        # Short-term should mention technical levels
        assert any(keyword in short_term.analysis.lower() for keyword in
                   ["resistance", "support", "breakout", "momentum", "catalyst"])


# ============================================================================
# Test: Mid-Term Horizon Analysis
# ============================================================================

class TestMidTermHorizon:
    """Test mid-term horizon (2-6 weeks) analysis"""

    @pytest.mark.asyncio
    async def test_analyze_mid_term_swing_setup(self, horizon_tagger):
        """Test mid-term swing trading analysis"""
        insight = {
            "topic": "NVDA Post-Earnings Momentum",
            "sentiment": "BULLISH",
            "trend_strength": "STRONG",
        }

        mid_term = await horizon_tagger._analyze_mid_term(insight)

        assert isinstance(mid_term, HorizonInsight)
        assert mid_term.horizon == TimeHorizon.MID
        assert mid_term.timeframe_weeks >= 2
        assert mid_term.timeframe_weeks <= 6

    @pytest.mark.asyncio
    async def test_mid_term_focus_on_trend(self, horizon_tagger):
        """Test that mid-term focuses on trend and momentum"""
        insight = {
            "topic": "NVDA Trend Following",
            "trend": "BULLISH",
        }

        mid_term = await horizon_tagger._analyze_mid_term(insight)

        # Mid-term should mention trend and momentum
        assert any(keyword in mid_term.analysis.lower() for keyword in
                   ["trend", "momentum", "swing", "target"])


# ============================================================================
# Test: Long-Term Horizon Analysis
# ============================================================================

class TestLongTermHorizon:
    """Test long-term horizon (6-18 months) analysis"""

    @pytest.mark.asyncio
    async def test_analyze_long_term_thematic(self, horizon_tagger):
        """Test long-term thematic investing analysis"""
        insight = {
            "topic": "AI Semiconductor Revolution",
            "sentiment": "BULLISH",
            "theme": "AI Infrastructure",
        }

        long_term = await horizon_tagger._analyze_long_term(insight)

        assert isinstance(long_term, HorizonInsight)
        assert long_term.horizon == TimeHorizon.LONG
        assert long_term.timeframe_months >= 6
        assert long_term.timeframe_months <= 18

    @pytest.mark.asyncio
    async def test_long_term_focus_on_fundamentals(self, horizon_tagger):
        """Test that long-term focuses on fundamentals and thesis"""
        insight = {
            "topic": "NVDA Long-Term Growth",
            "fundamental_strength": "STRONG",
        }

        long_term = await horizon_tagger._analyze_long_term(insight)

        # Long-term should mention fundamentals and thesis
        assert any(keyword in long_term.analysis.lower() for keyword in
                   ["thesis", "fundamental", "growth", "thematic", "valuation"])


# ============================================================================
# Test: Recommended Horizon Determination
# ============================================================================

class TestRecommendedHorizon:
    """Test recommended horizon determination"""

    @pytest.mark.asyncio
    async def test_recommend_short_for_catalyst(self, horizon_tagger):
        """Test SHORT recommendation for catalyst-driven insights"""
        insight = {
            "topic": "NVDA Earnings Surprise",
            "catalyst": "Earnings beat",
            "time_sensitivity": "HIGH",
        }

        result = await horizon_tagger.tag_horizons(insight)
        recommended = result.data["recommended_horizon"]

        assert recommended == "SHORT"

    @pytest.mark.asyncio
    async def test_recommend_mid_for_trend(self, horizon_tagger):
        """Test MID recommendation for trend-driven insights"""
        insight = {
            "topic": "NVDA Momentum Trade",
            "trend": "BULLISH",
            "time_sensitivity": "MEDIUM",
        }

        result = await horizon_tagger.tag_horizons(insight)
        recommended = result.data["recommended_horizon"]

        assert recommended == "MID"

    @pytest.mark.asyncio
    async def test_recommend_long_for_thematic(self, horizon_tagger):
        """Test LONG recommendation for thematic insights"""
        insight = {
            "topic": "AI Semiconductor Demand Growth",
            "theme": "AI Infrastructure",
            "time_sensitivity": "LOW",
        }

        result = await horizon_tagger.tag_horizons(insight)
        recommended = result.data["recommended_horizon"]

        assert recommended == "LONG"


# ============================================================================
# Test: Horizon Analysis Data Class
# ============================================================================

class TestHorizonAnalysis:
    """Test HorizonAnalysis data class"""

    def test_horizon_analysis_creation(self):
        """Test creating a HorizonAnalysis"""
        analysis = HorizonAnalysis(
            topic="NVDA Analysis",
            short_term=HorizonInsight(
                horizon=TimeHorizon.SHORT,
                timeframe_days=3,
                analysis="Short-term breakout play",
                confidence=0.8,
            ),
            mid_term=HorizonInsight(
                horizon=TimeHorizon.MID,
                timeframe_weeks=4,
                analysis="Mid-term momentum trade",
                confidence=0.75,
            ),
            long_term=HorizonInsight(
                horizon=TimeHorizon.LONG,
                timeframe_months=12,
                analysis="Long-term AI theme",
                confidence=0.85,
            ),
            recommended_horizon=TimeHorizon.SHORT,
        )

        assert analysis.topic == "NVDA Analysis"
        assert analysis.short_term.horizon == TimeHorizon.SHORT
        assert analysis.recommended_horizon == TimeHorizon.SHORT

    def test_horizon_analysis_to_dict(self):
        """Test converting HorizonAnalysis to dictionary"""
        short = HorizonInsight(
            horizon=TimeHorizon.SHORT,
            timeframe_days=5,
            analysis="Short-term trading",
            confidence=0.8,
        )

        result_dict = short.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["horizon"] == "SHORT"
        assert result_dict["timeframe_days"] == 5


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestHorizonTaggerEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_insight(self, horizon_tagger):
        """Test handling of empty insight"""
        insight = {}

        result = await horizon_tagger.tag_horizons(insight)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_no_topic(self, horizon_tagger):
        """Test handling when no topic provided"""
        insight = {
            "sentiment": "BULLISH",
        }

        result = await horizon_tagger.tag_horizons(insight)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, horizon_tagger):
        """Test handling of LLM errors"""
        class ErrorLLM:
            async def complete_with_system(self, system_prompt, user_prompt, config=None):
                raise Exception("LLM Error")

        original_llm = horizon_tagger.llm
        horizon_tagger.llm = ErrorLLM()

        insight = {"topic": "Test"}

        result = await horizon_tagger.tag_horizons(insight)

        # Restore original
        horizon_tagger.llm = original_llm

        # Should handle error gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_mixed_signals(self, horizon_tagger):
        """Test handling of mixed signals across horizons"""
        insight = {
            "topic": "NVDA Mixed Signals",
            "short_term": "BEARISH",
            "mid_term": "NEUTRAL",
            "long_term": "BULLISH",
        }

        result = await horizon_tagger.tag_horizons(insight)

        # Should handle mixed signals
        assert result.success is True


# ============================================================================
# Test: Time Horizon Enum
# ============================================================================

class TestTimeHorizon:
    """Test TimeHorizon enum"""

    def test_short_horizon_properties(self):
        """Test SHORT horizon properties"""
        horizon = TimeHorizon.SHORT

        assert horizon.value == "SHORT"
        assert horizon.days_min == 1
        assert horizon.days_max == 5

    def test_mid_horizon_properties(self):
        """Test MID horizon properties"""
        horizon = TimeHorizon.MID

        assert horizon.value == "MID"
        assert horizon.weeks_min == 2
        assert horizon.weeks_max == 6

    def test_long_horizon_properties(self):
        """Test LONG horizon properties"""
        horizon = TimeHorizon.LONG

        assert horizon.value == "LONG"
        assert horizon.months_min == 6
        assert horizon.months_max == 18


# ============================================================================
# Test: Confidence Calculation
# ============================================================================

class TestConfidenceCalculation:
    """Test confidence calculation for horizon recommendations"""

    @pytest.mark.asyncio
    async def test_high_confidence_for_clear_catalyst(self, horizon_tagger):
        """Test high confidence for clear catalyst"""
        insight = {
            "topic": "NVDA Earnings Beat",
            "catalyst": "Earnings surprise 20%",
            "technical_confirmation": True,
        }

        result = await horizon_tagger.tag_horizons(insight)

        # Should have high confidence for SHORT
        assert result.data["short_confidence"] > 0.7

    @pytest.mark.asyncio
    async def test_moderate_confidence_for_trend(self, horizon_tagger):
        """Test moderate confidence for trend-based insights"""
        insight = {
            "topic": "NVDA Momentum",
            "trend": "BULLISH",
        }

        result = await horizon_tagger.tag_horizons(insight)

        # Should have moderate confidence
        assert 0.5 <= result.data["mid_confidence"] <= 0.8


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
