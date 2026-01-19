"""
ContrarySignal Tests

Market Intelligence v2.0 - Phase 2, T2.2

Tests for the Contrary Signal component that detects market crowding
and generates contrarian trading signals when sentiment becomes extreme.

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

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta

from backend.ai.intelligence.contrary_signal import (
    ContrarySignal,
    CrowdingLevel,
    ContrarianAction,
    ContrarySignalAnalysis,
)
from backend.ai.intelligence.base import IntelligenceResult
from backend.ai.llm_providers import LLMProvider


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_market_data():
    """Mock market data provider for flow/sentiment data"""
    class MockMarketDataProvider:
        async def get_etf_flows(self, etf_ticker: str, days: int = 30):
            """Return mock ETF fund flow data"""
            # Simulate flows with some trend
            base_flow = 100_000_000  # $100M base
            flows = []
            for i in range(days):
                # Add some trend and noise
                flow = base_flow + (i * 10_000_000) + (i % 3) * 5_000_000
                flows.append({
                    "date": (datetime.now() - timedelta(days=days-i)).strftime("%Y-%m-%d"),
                    "flow": flow,
                    "etf": etf_ticker,
                })
            return flows

        async def get_sentiment_history(self, symbol: str, days: int = 30):
            """Return mock sentiment data"""
            sentiments = []
            for i in range(days):
                # Sentiment becoming more extreme over time
                sentiment_score = 0.5 + (i / days) * 0.4  # 0.5 -> 0.9
                sentiments.append({
                    "date": (datetime.now() - timedelta(days=days-i)).strftime("%Y-%m-%d"),
                    "sentiment": sentiment_score,
                })
            return sentiments

        async def get_position_data(self, symbol: str):
            """Return mock position/crowding data"""
            return {
                "symbol": symbol,
                "long_positions": 85_000_000,  # $85M long
                "short_positions": 15_000_000,  # $15M short
                "total_positions": 100_000_000,
                "institutional_long_ratio": 0.85,  # 85% institutions are long
            }

    return MockMarketDataProvider()


@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    class MockLLM:
        async def complete_with_system(self, system_prompt: str, user_prompt: str, config=None):
            from backend.ai.llm_providers import LLMResponse, ModelProvider
            return LLMResponse(
                content="Mock contrary signal analysis",
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
def contrary_detector(mock_llm, mock_market_data):
    """Create ContrarySignal instance"""
    return ContrarySignal(
        llm_provider=mock_llm,
        market_data_client=mock_market_data,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestContrarySignalBasic:
    """Test basic ContrarySignal functionality"""

    def test_initialization(self, contrary_detector):
        """Test detector initializes correctly"""
        assert contrary_detector.name == "ContrarySignal"
        assert contrary_detector.phase.value == "P1"
        assert contrary_detector._enabled is True

    @pytest.mark.asyncio
    async def test_analyze_contrary_signal(self, contrary_detector):
        """Test contrary signal analysis for a symbol"""
        symbol = "NVDA"

        result = await contrary_detector.analyze_contrary_signal(symbol, days=30)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "crowding_level" in result.data
        assert "contrarian_action" in result.data
        assert "flow_z_score" in result.data
        assert "sentiment_extreme" in result.data


# ============================================================================
# Test: Z-Score Calculation
# ============================================================================

class TestZScoreCalculation:
    """Test Z-score calculation for fund flows"""

    @pytest.mark.asyncio
    async def test_calculate_flow_z_score_positive(self, contrary_detector):
        """Test Z-score calculation with positive anomaly"""
        flow_data = [
            {"flow": 100_000_000},
            {"flow": 105_000_000},
            {"flow": 110_000_000},
            {"flow": 150_000_000},  # Anomaly
        ]

        z_score = contrary_detector._calculate_flow_z_score(flow_data)

        # Should detect positive anomaly
        assert z_score > 0
        assert z_score < 10  # Not infinite

    @pytest.mark.asyncio
    async def test_calculate_flow_z_score_negative(self, contrary_detector):
        """Test Z-score calculation with negative anomaly"""
        flow_data = [
            {"flow": 100_000_000},
            {"flow": 105_000_000},
            {"flow": 110_000_000},
            {"flow": 50_000_000},  # Negative anomaly
        ]

        z_score = contrary_detector._calculate_flow_z_score(flow_data)

        # Should detect negative anomaly
        assert z_score < 0
        assert z_score > -10  # Not infinite

    @pytest.mark.asyncio
    async def test_calculate_flow_z_score_normal(self, contrary_detector):
        """Test Z-score calculation with normal flows"""
        # Consistent flows (no anomaly)
        flow_data = [{"flow": 100_000_000 + i * 1_000_000} for i in range(10)]

        z_score = contrary_detector._calculate_flow_z_score(flow_data)

        # Should be close to zero (normal)
        assert abs(z_score) < 2.0


# ============================================================================
# Test: Sentiment Extreme Detection
# ============================================================================

class TestSentimentExtreme:
    """Test sentiment extreme value detection"""

    @pytest.mark.asyncio
    async def test_detect_bullish_extreme(self, contrary_detector):
        """Test detection of extreme bullish sentiment"""
        sentiment_history = [
            {"sentiment": 0.85},
            {"sentiment": 0.88},
            {"sentiment": 0.90},
            {"sentiment": 0.92},  # Extreme bullish
        ]

        extreme = contrary_detector._detect_sentiment_extreme(sentiment_history)

        assert extreme["is_extreme"] is True
        assert extreme["direction"] == "BULLISH"
        assert extreme["magnitude"] > 0.8

    @pytest.mark.asyncio
    async def test_detect_bearish_extreme(self, contrary_detector):
        """Test detection of extreme bearish sentiment"""
        sentiment_history = [
            {"sentiment": 0.12},
            {"sentiment": 0.10},
            {"sentiment": 0.08},
            {"sentiment": 0.05},  # Extreme bearish
        ]

        extreme = contrary_detector._detect_sentiment_extreme(sentiment_history)

        assert extreme["is_extreme"] is True
        assert extreme["direction"] == "BEARISH"
        assert extreme["magnitude"] > 0.8

    @pytest.mark.asyncio
    async def test_no_extreme_sentiment(self, contrary_detector):
        """Test handling of normal sentiment range"""
        sentiment_history = [
            {"sentiment": 0.45},
            {"sentiment": 0.50},
            {"sentiment": 0.55},
            {"sentiment": 0.52},
        ]

        extreme = contrary_detector._detect_sentiment_extreme(sentiment_history)

        assert extreme["is_extreme"] is False


# ============================================================================
# Test: Position Skew Calculation
# ============================================================================

class TestPositionSkew:
    """Test position skew/crowding calculation"""

    @pytest.mark.asyncio
    async def test_calculate_long_skew(self, contrary_detector):
        """Test calculation of long position skew"""
        position_data = {
            "long_positions": 90_000_000,
            "short_positions": 10_000_000,
            "total_positions": 100_000_000,
        }

        skew = contrary_detector._calculate_position_skew(position_data)

        # Should show long skew (positive)
        assert skew > 0.5
        assert skew <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_short_skew(self, contrary_detector):
        """Test calculation of short position skew"""
        position_data = {
            "long_positions": 20_000_000,
            "short_positions": 80_000_000,
            "total_positions": 100_000_000,
        }

        skew = contrary_detector._calculate_position_skew(position_data)

        # Should show short skew (negative)
        assert skew < -0.5
        assert skew >= -1.0

    @pytest.mark.asyncio
    async def test_calculate_balanced_positions(self, contrary_detector):
        """Test calculation with balanced positions"""
        position_data = {
            "long_positions": 50_000_000,
            "short_positions": 50_000_000,
            "total_positions": 100_000_000,
        }

        skew = contrary_detector._calculate_position_skew(position_data)

        # Should be close to zero (balanced)
        assert abs(skew) < 0.1


# ============================================================================
# Test: Crowding Level Detection
# ============================================================================

class TestCrowdingLevel:
    """Test crowding level determination"""

    @pytest.mark.asyncio
    async def test_low_crowding(self, contrary_detector):
        """Test LOW crowding level"""
        flow_z_score = 0.5
        sentiment_extreme = False
        position_skew = 0.1

        crowding = contrary_detector._determine_crowding_level(
            flow_z_score, sentiment_extreme, position_skew
        )

        assert crowding == CrowdingLevel.LOW

    @pytest.mark.asyncio
    async def test_medium_crowding(self, contrary_detector):
        """Test MEDIUM crowding level"""
        flow_z_score = 1.5
        sentiment_extreme = False
        position_skew = 0.4

        crowding = contrary_detector._determine_crowding_level(
            flow_z_score, sentiment_extreme, position_skew
        )

        assert crowding == CrowdingLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_high_crowding(self, contrary_detector):
        """Test HIGH crowding level"""
        flow_z_score = 1.8  # Below EXTREME threshold
        sentiment_extreme = True
        position_skew = 0.4  # Below medium threshold

        crowding = contrary_detector._determine_crowding_level(
            flow_z_score, sentiment_extreme, position_skew
        )

        assert crowding == CrowdingLevel.HIGH

    @pytest.mark.asyncio
    async def test_extreme_crowding(self, contrary_detector):
        """Test EXTREME crowding level"""
        flow_z_score = 3.5
        sentiment_extreme = True
        position_skew = 0.9

        crowding = contrary_detector._determine_crowding_level(
            flow_z_score, sentiment_extreme, position_skew
        )

        assert crowding == CrowdingLevel.EXTREME


# ============================================================================
# Test: Contrarian Action Generation
# ============================================================================

class TestContrarianAction:
    """Test contrarian trading action generation"""

    @pytest.mark.asyncio
    async def test_accumulate_action(self, contrary_detector):
        """Test ACCUMULATE action when crowding is low"""
        crowding = CrowdingLevel.LOW
        sentiment_direction = "BEARISH"

        action = contrary_detector._generate_contrarian_action(crowding, sentiment_direction)

        assert action == ContrarianAction.ACCUMULATE

    @pytest.mark.asyncio
    async def test_hold_action(self, contrary_detector):
        """Test HOLD action for neutral conditions"""
        crowding = CrowdingLevel.MEDIUM
        sentiment_direction = "NEUTRAL"

        action = contrary_detector._generate_contrarian_action(crowding, sentiment_direction)

        assert action == ContrarianAction.HOLD

    @pytest.mark.asyncio
    async def test_watch_for_pullback_action(self, contrary_detector):
        """Test WATCH_FOR_PULLBACK when crowding is high"""
        crowding = CrowdingLevel.HIGH
        sentiment_direction = "BULLISH"

        action = contrary_detector._generate_contrarian_action(crowding, sentiment_direction)

        assert action == ContrarianAction.WATCH_FOR_PULLBACK

    @pytest.mark.asyncio
    async def test_exit_action(self, contrary_detector):
        """Test EXIT action when crowding is extreme"""
        crowding = CrowdingLevel.EXTREME
        sentiment_direction = "BULLISH"

        action = contrary_detector._generate_contrarian_action(crowding, sentiment_direction)

        assert action == ContrarianAction.EXIT


# ============================================================================
# Test: Integration Analysis
# ============================================================================

class TestIntegrationAnalysis:
    """Test full integration analysis"""

    @pytest.mark.asyncio
    async def test_full_contrary_analysis(self, contrary_detector):
        """Test complete contrary signal analysis"""
        symbol = "TSLA"

        result = await contrary_detector.analyze_contrary_signal(symbol, days=30)

        assert result.success is True
        assert "crowding_level" in result.data
        assert "contrarian_action" in result.data
        assert "flow_z_score" in result.data
        assert "sentiment_extreme" in result.data
        assert "position_skew" in result.data
        # reasoning is in result.reasoning, not result.data
        assert result.reasoning is not None
        assert len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_analysis_with_etf(self, contrary_detector):
        """Test analysis for ETF"""
        etf_ticker = "SOXX"

        result = await contrary_detector.analyze_contrary_signal(etf_ticker, days=30)

        assert result.success is True


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestContrarySignalEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_symbol(self, contrary_detector):
        """Test handling of empty symbol"""
        result = await contrary_detector.analyze_contrary_signal("", days=30)

        # Should handle gracefully
        assert result is not None
        assert result.success is False

    @pytest.mark.asyncio
    async def test_no_flow_data(self, contrary_detector):
        """Test handling when no flow data available"""
        class NoFlowMock:
            async def get_etf_flows(self, etf_ticker, days=30):
                return []  # No data

        original_client = contrary_detector.market_data_client
        contrary_detector.market_data_client = NoFlowMock()

        result = await contrary_detector.analyze_contrary_signal("TEST", days=30)

        # Restore original
        contrary_detector.market_data_client = original_client

        # Should handle with insufficient data
        assert result is not None

    @pytest.mark.asyncio
    async def test_insufficient_history(self, contrary_detector):
        """Test handling with insufficient historical data"""
        result = await contrary_detector.analyze_contrary_signal("TEST", days=2)

        # Should handle with low confidence
        assert "confidence" in result.data
        assert result.data["confidence"] <= 0.5

    @pytest.mark.asyncio
    async def test_api_error_handling(self, contrary_detector):
        """Test handling of API errors"""
        class ErrorMock:
            async def get_etf_flows(self, etf_ticker, days=30):
                raise Exception("API Error")

        original_client = contrary_detector.market_data_client
        contrary_detector.market_data_client = ErrorMock()

        result = await contrary_detector.analyze_contrary_signal("TEST", days=30)

        # Restore original
        contrary_detector.market_data_client = original_client

        # Should handle error gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_extreme_z_score_cap(self, contrary_detector):
        """Test that extreme Z-scores are capped"""
        # Extreme flow anomaly
        flow_data = [
            {"flow": 100_000_000},
            {"flow": 100_000_000},
            {"flow": 100_000_000},
            {"flow": 1_000_000_000},  # 10x normal
        ]

        z_score = contrary_detector._calculate_flow_z_score(flow_data)

        # Should be capped at reasonable value
        assert z_score < 100


# ============================================================================
# Test: ContrarySignalAnalysis Data Class
# ============================================================================

class TestContrarySignalAnalysis:
    """Test ContrarySignalAnalysis data class"""

    def test_analysis_creation(self):
        """Test creating a ContrarySignalAnalysis"""
        analysis = ContrarySignalAnalysis(
            symbol="NVDA",
            crowding_level=CrowdingLevel.HIGH,
            flow_z_score=2.5,
            sentiment_extreme=True,
            sentiment_direction="BULLISH",
            position_skew=0.8,
            contrarian_action=ContrarianAction.WATCH_FOR_PULLBACK,
            reasoning="High crowding with extreme bullish sentiment",
        )

        assert analysis.symbol == "NVDA"
        assert analysis.crowding_level == CrowdingLevel.HIGH
        assert analysis.flow_z_score == 2.5
        assert analysis.contrarian_action == ContrarianAction.WATCH_FOR_PULLBACK

    def test_analysis_to_dict(self):
        """Test converting ContrarySignalAnalysis to dictionary"""
        analysis = ContrarySignalAnalysis(
            symbol="TSLA",
            crowding_level=CrowdingLevel.EXTREME,
            flow_z_score=3.5,
            sentiment_extreme=True,
            sentiment_direction="BULLISH",
            position_skew=0.95,
            contrarian_action=ContrarianAction.EXIT,
        )

        result_dict = analysis.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["symbol"] == "TSLA"
        assert result_dict["crowding_level"] == "EXTREME"
        assert result_dict["contrarian_action"] == "EXIT"


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
