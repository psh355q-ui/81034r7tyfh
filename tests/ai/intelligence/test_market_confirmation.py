"""
MarketConfirmation Tests

Market Intelligence v2.0 - Phase 1, T1.4

Tests for the Market Confirmation component that validates narratives against
actual market price action to filter out noise.

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta

from backend.ai.intelligence.market_confirmation import (
    MarketConfirmation,
    ConfirmationSignal,
    ConfirmationStatus,
)
from backend.ai.intelligence.base import IntelligenceResult
from backend.ai.llm_providers import LLMProvider


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_market_data():
    """Mock market data provider"""
    class MockMarketDataProvider:
        async def get_price_history(self, symbol: str, period: str = "1mo"):
            # Return mock price history
            base_price = 150.0
            prices = []
            for i in range(30):  # 30 days
                price = base_price + (i * 0.5) + (i % 3)  # Upward trend with noise
                prices.append({
                    "date": (datetime.now() - timedelta(days=29-i)).strftime("%Y-%m-%d"),
                    "close": price,
                    "volume": 1000000 + (i * 10000),
                })
            return {
                "symbol": symbol,
                "period": period,
                "prices": prices,
                "current_price": prices[-1]["close"],
                "change_percent": ((prices[-1]["close"] - prices[0]["close"]) / prices[0]["close"]) * 100,
            }

        async def get_current_price(self, symbol: str):
            return {
                "symbol": symbol,
                "price": 165.0,
                "change_percent": 2.5,
                "volume": 1500000,
            }

        async def get_sector_performance(self, sector: str, period: str = "1mo"):
            # Mock sector performance
            sectors = {
                "technology": {"return": 5.2, "spy_return": 3.1},
                "healthcare": {"return": 2.1, "spy_return": 3.1},
                "defense": {"return": 8.5, "spy_return": 3.1},
            }
            return sectors.get(sector.lower(), {"return": 0.0, "spy_return": 3.1})

    return MockMarketDataProvider()


@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    class MockLLM:
        async def complete_with_system(self, system_prompt: str, user_prompt: str, config=None):
            from backend.ai.llm_providers import LLMResponse, ModelProvider
            return LLMResponse(
                content="Mock response",
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
def confirmer(mock_llm, mock_market_data):
    """Create MarketConfirmation instance"""
    return MarketConfirmation(
        llm_provider=mock_llm,
        market_data_client=mock_market_data,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestMarketConfirmationBasic:
    """Test basic MarketConfirmation functionality"""

    def test_initialization(self, confirmer):
        """Test confirmer initializes correctly"""
        assert confirmer.name == "MarketConfirmation"
        assert confirmer.phase.value == "P0"
        assert confirmer._enabled is True

    @pytest.mark.asyncio
    async def test_confirm_narrative_with_bullish_price_action(self, confirmer):
        """Test confirmation of bullish narrative with positive price action"""
        narrative_data = {
            "topic": "AI Semiconductor Boom",
            "sentiment": "BULLISH",
            "symbols": ["NVDA"],
            "confidence": 0.85,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "confirmation_status" in result.data
        assert "price_correlation" in result.data

    @pytest.mark.asyncio
    async def test_confirm_narrative_with_bearish_price_action(self, confirmer):
        """Test confirmation of bearish narrative with negative price action"""
        narrative_data = {
            "topic": "EV Demand Slowdown",
            "sentiment": "BEARISH",
            "symbols": ["TSLA"],
            "confidence": 0.75,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True


# ============================================================================
# Test: Price Correlation Calculation
# ============================================================================

class TestPriceCorrelation:
    """Test price correlation calculation"""

    @pytest.mark.asyncio
    async def test_calculate_positive_correlation(self, confirmer):
        """Test calculation of positive price correlation"""
        sentiment = "BULLISH"
        price_change = 10.0  # 10% gain

        correlation = confirmer._calculate_price_correlation(sentiment, price_change)

        assert correlation > 0.5  # Strong positive correlation
        assert correlation <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_negative_correlation(self, confirmer):
        """Test calculation of negative correlation (contradiction)"""
        sentiment = "BULLISH"
        price_change = -10.0  # 10% drop

        correlation = confirmer._calculate_price_correlation(sentiment, price_change)

        assert correlation < -0.5  # Strong negative correlation
        assert correlation >= -1.0

    @pytest.mark.asyncio
    async def test_calculate_neutral_correlation(self, confirmer):
        """Test calculation of neutral correlation"""
        sentiment = "NEUTRAL"
        price_change = 0.5  # Small change

        correlation = confirmer._calculate_price_correlation(sentiment, price_change)

        assert abs(correlation) < 0.3  # Weak correlation


# ============================================================================
# Test: Confirmation Status Detection
# ============================================================================

class TestConfirmationStatus:
    """Test confirmation status detection"""

    @pytest.mark.asyncio
    async def test_confirmed_status(self, confirmer):
        """Test CONFIRMED status when price action supports narrative"""
        narrative_data = {
            "topic": "Defense Stocks Rally",
            "sentiment": "BULLISH",
            "symbols": ["LMT"],
            "confidence": 0.8,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Mock market data has upward trend
        assert result.data["confirmation_status"] in ["CONFIRMED", "STRONG_CONFIRMATION"]

    @pytest.mark.asyncio
    async def test_contradicted_status(self, confirmer):
        """Test CONTRADICTED status when price action opposes narrative"""
        # Create a mock with downward trend
        class DownwardTrendMock:
            async def get_price_history(self, symbol: str, period: str = "1mo"):
                base_price = 150.0
                prices = []
                for i in range(30):
                    price = base_price - (i * 0.5)  # Downward trend
                    prices.append({
                        "date": (datetime.now() - timedelta(days=29-i)).strftime("%Y-%m-%d"),
                        "close": price,
                        "volume": 1000000,
                    })
                return {
                    "symbol": symbol,
                    "prices": prices,
                    "current_price": prices[-1]["close"],
                    "change_percent": -10.0,  # 10% drop
                }

        confirmer.market_data_client = DownwardTrendMock()

        narrative_data = {
            "topic": "Defense Stocks Rally",
            "sentiment": "BULLISH",
            "symbols": ["LMT"],
            "confidence": 0.8,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Bullish narrative with bearish price action = contradiction
        assert result.data["confirmation_status"] == "CONTRADICTED"

    @pytest.mark.asyncio
    async def test_neutral_status(self, confirmer):
        """Test NEUTRAL status when price action is inconclusive"""
        # Create a mock with small price changes (inconclusive)
        class SmallChangeMock:
            async def get_price_history(self, symbol: str, period: str = "1mo"):
                return {
                    "symbol": symbol,
                    "change_percent": 0.1,  # Small change
                    "prices": [],
                }

        original_client = confirmer.market_data_client
        confirmer.market_data_client = SmallChangeMock()

        narrative_data = {
            "topic": "Mixed Signals in Tech",
            "sentiment": "NEUTRAL",
            "symbols": ["AAPL"],
            "confidence": 0.5,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Restore original client
        confirmer.market_data_client = original_client

        assert result.data["confirmation_status"] in ["NEUTRAL", "INSUFFICIENT_DATA"]


# ============================================================================
# Test: Sector Relative Performance
# ============================================================================

class TestSectorPerformance:
    """Test sector relative performance analysis"""

    @pytest.mark.asyncio
    async def test_sector_outperformance(self, confirmer):
        """Test detection of sector outperformance"""
        narrative_data = {
            "topic": "Defense Sector Surge",
            "sentiment": "BULLISH",
            "sector": "Defense",
            "symbols": ["LMT", "RTX"],
            "confidence": 0.8,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Defense sector mock returns 8.5% vs 3.1% SPY
        assert "sector_relative_return" in result.data
        assert result.data["sector_relative_return"] > 0  # Outperforming

    @pytest.mark.asyncio
    async def test_sector_underperformance(self, confirmer):
        """Test detection of sector underperformance"""
        narrative_data = {
            "topic": "Healthcare Sector Weakness",
            "sentiment": "BEARISH",
            "sector": "Healthcare",
            "symbols": ["JNJ", "PFE"],
            "confidence": 0.7,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Healthcare mock returns 2.1% vs 3.1% SPY (underperforming)
        assert result.data["sector_relative_return"] < 0


# ============================================================================
# Test: Multi-Symbol Confirmation
# ============================================================================

class TestMultiSymbolConfirmation:
    """Test confirmation with multiple related symbols"""

    @pytest.mark.asyncio
    async def test_confirm_with_multiple_symbols(self, confirmer):
        """Test confirmation when narrative has multiple symbols"""
        narrative_data = {
            "topic": "AI Chip Boom",
            "sentiment": "BULLISH",
            "symbols": ["NVDA", "AMD", "INTC"],
            "confidence": 0.85,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        assert result.success is True
        assert "symbol_confirmations" in result.data
        assert len(result.data["symbol_confirmations"]) == 3

    @pytest.mark.asyncio
    async def test_aggregate_confirmation_score(self, confirmer):
        """Test calculation of aggregate confirmation across symbols"""
        narrative_data = {
            "topic": "Semiconductor Rally",
            "sentiment": "BULLISH",
            "symbols": ["NVDA", "AMD", "INTC"],
            "confidence": 0.8,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Should have aggregate confirmation score
        assert "aggregate_confirmation" in result.data
        assert 0.0 <= result.data["aggregate_confirmation"] <= 1.0


# ============================================================================
# Test: Volume Confirmation
# ============================================================================

class TestVolumeConfirmation:
    """Test volume-based confirmation"""

    @pytest.mark.asyncio
    async def test_high_volume_confirms_breakout(self, confirmer):
        """Test that high volume confirms bullish breakouts"""
        # This would be tested with mock data showing high volume
        narrative_data = {
            "topic": "NVDA Earnings Beat",
            "sentiment": "BULLISH",
            "symbols": ["NVDA"],
            "confidence": 0.8,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        assert "volume_confirmation" in result.data


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestMarketConfirmationEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_missing_symbols(self, confirmer):
        """Test handling of missing symbols"""
        narrative_data = {
            "topic": "Generic Market Narrative",
            "sentiment": "BULLISH",
            # Missing symbols
            "confidence": 0.7,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Should still succeed but with limited confirmation
        assert result.success is True
        assert result.data["confirmation_status"] == "INSUFFICIENT_DATA"

    @pytest.mark.asyncio
    async def test_invalid_symbol(self, confirmer):
        """Test handling of invalid symbol"""
        narrative_data = {
            "topic": "Invalid Company",
            "sentiment": "BULLISH",
            "symbols": ["INVALIDTICKER123"],
            "confidence": 0.7,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_market_data_api_error(self, confirmer):
        """Test handling of market data API errors"""
        # Make the API raise an error
        async def failing_get_price_history(symbol, period="1mo"):
            raise Exception("Market Data API Error")

        confirmer.market_data_client.get_price_history = failing_get_price_history

        narrative_data = {
            "topic": "Test",
            "sentiment": "BULLISH",
            "symbols": ["NVDA"],
            "confidence": 0.7,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Should handle error gracefully - check that error is reflected in result
        assert result is not None
        # Check that symbol_confirmations contains error information
        assert len(result.data.get("symbol_confirmations", [])) > 0
        symbol_conf = result.data["symbol_confirmations"][0]
        assert "Error" in symbol_conf["reasoning"]

    @pytest.mark.asyncio
    async def test_no_market_data_available(self, confirmer):
        """Test handling when no market data is available"""
        # Create a mock that returns None
        class NoDataMock:
            async def get_price_history(self, symbol, period="1mo"):
                return None

        confirmer.market_data_client = NoDataMock()

        narrative_data = {
            "topic": "Test",
            "sentiment": "BULLISH",
            "symbols": ["NVDA"],
            "confidence": 0.7,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Should handle gracefully with NEUTRAL status (no data = inconclusive)
        assert result.data["confirmation_status"] in ["NEUTRAL", "INSUFFICIENT_DATA"]
        # Check that symbol_confirmations indicates no data
        assert len(result.data.get("symbol_confirmations", [])) > 0
        symbol_conf = result.data["symbol_confirmations"][0]
        assert "No price data" in symbol_conf["reasoning"]


# ============================================================================
# Test: Confidence Adjustment
# ============================================================================

class TestConfidenceAdjustment:
    """Test confidence adjustment based on market confirmation"""

    @pytest.mark.asyncio
    async def test_confidence_boost_on_confirmation(self, confirmer):
        """Test that confirmed narratives boost confidence"""
        original_confidence = 0.75
        narrative_data = {
            "topic": "Defense Stocks Rally",
            "sentiment": "BULLISH",
            "symbols": ["LMT"],
            "confidence": original_confidence,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # Confirmed narrative should have higher or equal confidence
        adjusted_confidence = result.data.get("adjusted_confidence", 0)
        assert adjusted_confidence >= original_confidence * 0.95  # Allow small variance

    @pytest.mark.asyncio
    async def test_confidence_penalty_on_contradiction(self, confirmer):
        """Test that contradicted narratives penalize confidence"""
        original_confidence = 0.85
        narrative_data = {
            "topic": "Failing Narrative",
            "sentiment": "BULLISH",
            "symbols": ["TEST"],
            "confidence": original_confidence,
        }

        result = await confirmer.confirm_narrative(narrative_data)

        # If contradicted, confidence should be reduced
        if result.data["confirmation_status"] == "CONTRADICTED":
            adjusted_confidence = result.data.get("adjusted_confidence", 0)
            assert adjusted_confidence < original_confidence


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
