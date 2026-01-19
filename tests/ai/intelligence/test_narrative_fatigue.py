"""
NarrativeFatigue Tests

Market Intelligence v2.0 - Phase 2, T2.1

Tests for the Narrative Fatigue component that detects when narratives
become overplayed/lose impact through mention growth, price response,
and new info ratio analysis.

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta

from backend.ai.intelligence.narrative_fatigue import (
    NarrativeFatigue,
    FatigueAnalysis,
    FatigueSignal,
    FatiguePhase,
)
from backend.ai.intelligence.base import IntelligenceResult
from backend.ai.llm_providers import LLMProvider


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_news_repository():
    """Mock news repository for narrative analysis"""
    class MockNewsRepository:
        async def get_articles_by_theme(self, theme: str, days: int = 30):
            """Return mock articles for a theme"""
            # Simulate growing mentions over time
            base_count = 10
            articles = []
            for i in range(days):
                # Exponential growth pattern
                count = int(base_count * (1.1 ** i))
                articles.append({
                    "date": (datetime.now() - timedelta(days=days-i)).strftime("%Y-%m-%d"),
                    "count": count,
                    "theme": theme,
                })
            return articles

        async def get_sentiment_history(self, theme: str, days: int = 30):
            """Return mock sentiment history"""
            sentiments = []
            for i in range(days):
                # Sentiment becoming more extreme over time
                sentiment_score = 0.5 + (i / days) * 0.4  # 0.5 -> 0.9
                sentiments.append({
                    "date": (datetime.now() - timedelta(days=days-i)).strftime("%Y-%m-%d"),
                    "sentiment": sentiment_score,
                })
            return sentiments

    return MockNewsRepository()


@pytest.fixture
def mock_market_data():
    """Mock market data provider"""
    class MockMarketDataProvider:
        async def get_theme_performance(self, theme: str, period: str = "1mo"):
            """Return mock theme performance"""
            # Return diminishing returns (fatigue pattern)
            return {
                "theme": theme,
                "total_return": 15.0,  # 15% gain
                "recent_return": 1.5,   # Only 1.5% in recent days (diminishing)
                "volume_trend": "DECLINING",
                "volatility": 25.0,
            }

        async def get_proxy_symbols(self, theme: str):
            """Get proxy symbols for theme analysis"""
            theme_proxies = {
                "AI Semiconductor": ["NVDA", "AMD", "SOXX"],
                "Defense": ["LMT", "RTX", "ITA"],
                "EV": ["TSLA", "RIVN", "LCID"],
            }
            return theme_proxies.get(theme, [])

    return MockMarketDataProvider()


@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    class MockLLM:
        async def complete_with_system(self, system_prompt: str, user_prompt: str, config=None):
            from backend.ai.llm_providers import LLMResponse, ModelProvider
            return LLMResponse(
                content="Mock fatigue analysis response",
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
def fatigue_detector(mock_llm, mock_news_repository, mock_market_data):
    """Create NarrativeFatigue instance"""
    return NarrativeFatigue(
        llm_provider=mock_llm,
        news_repository=mock_news_repository,
        market_data_client=mock_market_data,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestNarrativeFatigueBasic:
    """Test basic NarrativeFatigue functionality"""

    def test_initialization(self, fatigue_detector):
        """Test detector initializes correctly"""
        assert fatigue_detector.name == "NarrativeFatigue"
        assert fatigue_detector.phase.value == "P1"
        assert fatigue_detector._enabled is True

    @pytest.mark.asyncio
    async def test_analyze_fatigue_for_theme(self, fatigue_detector):
        """Test fatigue analysis for a theme"""
        theme = "AI Semiconductor"

        result = await fatigue_detector.analyze_fatigue(theme, days=30)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "fatigue_score" in result.data
        assert "fatigue_phase" in result.data
        assert "mention_growth" in result.data
        assert "price_response" in result.data
        assert "new_info_ratio" in result.data


# ============================================================================
# Test: Fatigue Score Calculation
# ============================================================================

class TestFatigueScoreCalculation:
    """Test fatigue score calculation"""

    @pytest.mark.asyncio
    async def test_calculate_mention_growth(self, fatigue_detector):
        """Test mention growth rate calculation"""
        # Mock data with exponential growth
        mention_history = [10, 15, 25, 40, 70, 120, 200]  # Exponential growth

        growth_rate = fatigue_detector._calculate_mention_growth(mention_history)

        # High growth should be detected
        assert growth_rate > 1.0  # More than 100% growth
        assert growth_rate <= 10.0  # But not infinite

    @pytest.mark.asyncio
    async def test_calculate_price_response(self, fatigue_detector):
        """Test price response calculation"""
        # Price momentum with diminishing returns
        price_data = {
            "total_return": 20.0,    # Good overall return
            "recent_return": 1.0,    # But weak recent return (fatigue sign)
        }

        response_score = fatigue_detector._calculate_price_response(price_data)

        # Should detect diminishing response
        assert 0.0 <= response_score <= 1.0
        # Recent weak performance should lower the score
        assert response_score < 0.5  # Diminishing response

    @pytest.mark.asyncio
    async def test_calculate_new_info_ratio(self, fatigue_detector):
        """Test new info ratio calculation"""
        # Mock article content similarity (high similarity = low new info)
        article_embeddings = [
            [0.1, 0.2, 0.3],
            [0.11, 0.21, 0.31],  # Very similar to previous
            [0.12, 0.22, 0.32],  # Very similar to previous
            [0.5, 0.6, 0.7],     # Different (new info)
        ]

        new_info_ratio = fatigue_detector._calculate_new_info_ratio(article_embeddings)

        # Should detect low new info ratio (repetitive content)
        assert 0.0 <= new_info_ratio <= 1.0
        assert new_info_ratio < 0.5  # Mostly repetitive

    @pytest.mark.asyncio
    async def test_composite_fatigue_score(self, fatigue_detector):
        """Test composite fatigue score calculation"""
        mention_growth = 2.5  # High growth (fatigue signal)
        price_response = 0.2  # Low response (fatigue signal)
        new_info_ratio = 0.1  # Low new info (fatigue signal)

        # Formula: fatigue = mention_growth - price_response - new_info_ratio
        # (simplified - actual formula normalizes these)
        fatigue_score = fatigue_detector._calculate_fatigue_score(
            mention_growth, price_response, new_info_ratio
        )

        # High fatigue expected
        assert fatigue_score > 0.5
        assert fatigue_score <= 1.0


# ============================================================================
# Test: Fatigue Phase Detection
# ============================================================================

class TestFatiguePhaseDetection:
    """Test fatigue phase detection"""

    @pytest.mark.asyncio
    async def test_early_phase_low_fatigue(self, fatigue_detector):
        """Test EARLY phase with low fatigue"""
        theme = "Emerging Technology"

        # Create mock with low fatigue signals
        class LowFatigueMock:
            async def get_articles_by_theme(self, theme, days=30):
                # Consistent low mentions (no growth = low fatigue)
                return [{"date": f"2026-01-{i:02d}", "count": 5} for i in range(1, 11)]

            async def get_theme_performance(self, theme, period="1mo"):
                return {
                    "total_return": 5.0,
                    "recent_return": 3.0,  # Strong recent performance (60% of total)
                    "volume_trend": "INCREASING",
                }

        original_repo = fatigue_detector.news_repository
        original_market = fatigue_detector.market_data_client
        fatigue_detector.news_repository = LowFatigueMock()
        fatigue_detector.market_data_client = LowFatigueMock()

        result = await fatigue_detector.analyze_fatigue(theme, days=30)

        # Restore originals
        fatigue_detector.news_repository = original_repo
        fatigue_detector.market_data_client = original_market

        # With zero mention growth and strong price response, should be EARLY
        assert result.data["fatigue_phase"] in ["EARLY", "ACCELERATING"]
        assert result.data["fatigue_score"] < 0.4

    @pytest.mark.asyncio
    async def test_mature_phase_moderate_fatigue(self, fatigue_detector):
        """Test MATURE phase with moderate fatigue"""
        theme = "Mature Theme"

        # Create mock with moderate fatigue signals
        class MatureFatigueMock:
            async def get_articles_by_theme(self, theme, days=30):
                # Moderate mention growth (not exponential)
                return [{"date": f"2026-01-{i:02d}", "count": 10 + i*2} for i in range(1, 11)]

            async def get_theme_performance(self, theme, period="1mo"):
                return {
                    "total_return": 10.0,
                    "recent_return": 2.0,  # Moderate recent performance (20% of total)
                    "volume_trend": "STABLE",
                }

        original_repo = fatigue_detector.news_repository
        original_market = fatigue_detector.market_data_client
        fatigue_detector.news_repository = MatureFatigueMock()
        fatigue_detector.market_data_client = MatureFatigueMock()

        result = await fatigue_detector.analyze_fatigue(theme, days=30)

        # Restore originals
        fatigue_detector.news_repository = original_repo
        fatigue_detector.market_data_client = original_market

        # Moderate fatigue should be MATURE or CONSENSUS
        assert result.data["fatigue_phase"] in ["MATURE", "CONSENSUS"]
        assert 0.3 <= result.data["fatigue_score"] <= 0.7

    @pytest.mark.asyncio
    async def test_fatigued_phase_high_fatigue(self, fatigue_detector):
        """Test FATIGUED phase with high fatigue"""
        theme = "Overplayed Theme"

        # Create mock with high fatigue signals
        class HighFatigueMock:
            async def get_articles_by_theme(self, theme, days=30):
                # Exponential mention growth
                return [
                    {"date": f"2026-01-{i:02d}", "count": 10 * (2 ** i)}
                    for i in range(1, 11)
                ]

            async def get_theme_performance(self, theme, period="1mo"):
                return {
                    "total_return": 30.0,
                    "recent_return": 0.5,  # Very weak recent return
                    "volume_trend": "DECLINING",
                }

        original_repo = fatigue_detector.news_repository
        original_market = fatigue_detector.market_data_client
        fatigue_detector.news_repository = HighFatigueMock()
        fatigue_detector.market_data_client = HighFatigueMock()

        result = await fatigue_detector.analyze_fatigue(theme, days=30)

        # Restore originals
        fatigue_detector.news_repository = original_repo
        fatigue_detector.market_data_client = original_market

        assert result.data["fatigue_phase"] == "FATIGUED"
        assert result.data["fatigue_score"] > 0.7


# ============================================================================
# Test: Contrarian Signal Generation
# ============================================================================

class TestContrarianSignal:
    """Test contrarian signal generation"""

    @pytest.mark.asyncio
    async def test_no_signal_when_early(self, fatigue_detector):
        """Test no contrarian signal in early phase"""
        fatigue_score = 0.2
        phase = FatiguePhase.EARLY

        signal = fatigue_detector._generate_contrarian_signal(fatigue_score, phase)

        assert signal == FatigueSignal.NONE

    @pytest.mark.asyncio
    async def test_caution_signal_when_mature(self, fatigue_detector):
        """Test CAUTION signal in mature phase"""
        fatigue_score = 0.65  # > 0.6 threshold for CAUTION in MATURE phase
        phase = FatiguePhase.MATURE

        signal = fatigue_detector._generate_contrarian_signal(fatigue_score, phase)

        assert signal == FatigueSignal.CAUTION

    @pytest.mark.asyncio
    async def test_reversal_signal_when_fatigued(self, fatigue_detector):
        """Test REVERSAL signal when fatigued"""
        fatigue_score = 0.8
        phase = FatiguePhase.FATIGUED

        signal = fatigue_detector._generate_contrarian_signal(fatigue_score, phase)

        assert signal == FatigueSignal.REVERSAL

    @pytest.mark.asyncio
    async def test_strong_reversal_signal_when_extreme(self, fatigue_detector):
        """Test STRONG_REVERSAL signal at extreme fatigue"""
        fatigue_score = 0.95
        phase = FatiguePhase.FATIGUED

        signal = fatigue_detector._generate_contrarian_signal(fatigue_score, phase)

        assert signal == FatigueSignal.STRONG_REVERSAL


# ============================================================================
# Test: Volume and Coverage Analysis
# ============================================================================

class TestVolumeCoverageAnalysis:
    """Test volume and coverage analysis"""

    @pytest.mark.asyncio
    async def test_analyze_media_coverage_intensity(self, fatigue_detector):
        """Test media coverage intensity analysis"""
        theme = "AI Semiconductor"

        coverage_data = await fatigue_detector._analyze_coverage(theme, days=30)

        assert "total_mentions" in coverage_data
        assert "daily_average" in coverage_data
        assert "peak_day" in coverage_data
        assert coverage_data["total_mentions"] > 0

    @pytest.mark.asyncio
    async def test_detect_volume_anomaly(self, fatigue_detector):
        """Test volume anomaly detection"""
        normal_volume = 1000000
        current_volume = 3500000  # 3.5x normal

        anomaly = fatigue_detector._detect_volume_anomaly(
            current_volume, normal_volume
        )

        assert anomaly["is_anomalous"] is True
        assert anomaly["ratio"] == 3.5


# ============================================================================
# Test: Fatigue Trend Analysis
# ============================================================================

class TestFatigueTrend:
    """Test fatigue trend analysis over time"""

    @pytest.mark.asyncio
    async def test_calculate_fatigue_trend(self, fatigue_detector):
        """Test fatigue trend calculation"""
        # Fatigue scores over time
        fatigue_history = [0.2, 0.3, 0.45, 0.6, 0.75, 0.8]

        trend = fatigue_detector._calculate_fatigue_trend(fatigue_history)

        assert trend["direction"] == "INCREASING"
        assert trend["rate"] > 0

    @pytest.mark.asyncio
    async def test_detect_fatigue_acceleration(self, fatigue_detector):
        """Test detection of accelerating fatigue"""
        # Fatigue accelerating (increasing rate of change)
        fatigue_history = [0.2, 0.25, 0.35, 0.5, 0.7, 0.95]

        acceleration = fatigue_detector._detect_fatigue_acceleration(fatigue_history)

        assert acceleration["is_accelerating"] is True
        assert acceleration["acceleration_rate"] > 0


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestNarrativeFatigueEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_theme_name(self, fatigue_detector):
        """Test handling of empty theme name"""
        result = await fatigue_detector.analyze_fatigue("", days=30)

        # Should handle gracefully
        assert result is not None
        assert result.success is False

    @pytest.mark.asyncio
    async def test_no_news_data(self, fatigue_detector):
        """Test handling when no news data available"""
        class NoDataMock:
            async def get_articles_by_theme(self, theme, days=30):
                return []  # No articles

        original_repo = fatigue_detector.news_repository
        fatigue_detector.news_repository = NoDataMock()

        result = await fatigue_detector.analyze_fatigue("Unknown Theme", days=30)

        # Restore original
        fatigue_detector.news_repository = original_repo

        # Should handle with insufficient data status
        assert result.data["fatigue_phase"] == "INSUFFICIENT_DATA"

    @pytest.mark.asyncio
    async def test_insufficient_history(self, fatigue_detector):
        """Test handling with insufficient historical data"""
        result = await fatigue_detector.analyze_fatigue("New Theme", days=2)

        # Should handle with low confidence
        assert "confidence" in result.data
        assert result.data["confidence"] <= 0.5

    @pytest.mark.asyncio
    async def test_api_error_handling(self, fatigue_detector):
        """Test handling of API errors"""
        class ErrorMock:
            async def get_articles_by_theme(self, theme, days=30):
                raise Exception("API Error")

        original_repo = fatigue_detector.news_repository
        fatigue_detector.news_repository = ErrorMock()

        result = await fatigue_detector.analyze_fatigue("Test Theme", days=30)

        # Restore original
        fatigue_detector.news_repository = original_repo

        # Should handle error gracefully - API error returns INSUFFICIENT_DATA with success=True
        assert result is not None
        assert result.data["fatigue_phase"] == "INSUFFICIENT_DATA"

    @pytest.mark.asyncio
    async def test_extreme_mention_growth(self, fatigue_detector):
        """Test handling of extreme mention growth"""
        # Extreme growth (viral)
        mention_history = [10, 100, 1000, 10000, 100000]

        growth_rate = fatigue_detector._calculate_mention_growth(mention_history)

        # Should handle without overflow
        assert growth_rate > 0
        assert growth_rate < 1000  # Capped at reasonable value


# ============================================================================
# Test: FatigueAnalysis Data Class
# ============================================================================

class TestFatigueAnalysis:
    """Test FatigueAnalysis data class"""

    def test_fatigue_analysis_creation(self):
        """Test creating a FatigueAnalysis"""
        analysis = FatigueAnalysis(
            theme="AI Semiconductor",
            fatigue_score=0.75,
            fatigue_phase=FatiguePhase.FATIGUED,
            mention_growth=2.5,
            price_response=0.2,
            new_info_ratio=0.1,
            signal=FatigueSignal.REVERSAL,
            reasoning="High fatigue detected",
        )

        assert analysis.theme == "AI Semiconductor"
        assert analysis.fatigue_score == 0.75
        assert analysis.fatigue_phase == FatiguePhase.FATIGUED
        assert analysis.signal == FatigueSignal.REVERSAL

    def test_fatigue_analysis_to_dict(self):
        """Test converting FatigueAnalysis to dictionary"""
        analysis = FatigueAnalysis(
            theme="Defense",
            fatigue_score=0.5,
            fatigue_phase=FatiguePhase.MATURE,
            mention_growth=1.5,
            price_response=0.5,
            new_info_ratio=0.3,
            signal=FatigueSignal.CAUTION,
        )

        result_dict = analysis.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["theme"] == "Defense"
        assert result_dict["fatigue_score"] == 0.5
        assert result_dict["fatigue_phase"] == "MATURE"


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
