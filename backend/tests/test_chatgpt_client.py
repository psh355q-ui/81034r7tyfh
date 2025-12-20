"""
Test Suite for ChatGPT Client (Market Regime Detection)

Phase: 5 (Strategy Ensemble)
Task: 4 (ChatGPT Integration)
Author: AI Trading System Team
Date: 2025-11-14

Run with:
    pytest test_chatgpt_client.py -v
    
Mock testing (no API key required):
    pytest test_chatgpt_client.py -v -k "mock"
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.chatgpt_client import (
    ChatGPTClient,
    RegimeBasedScreener,
    MarketDataFetcher,
    MARKET_REGIMES,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_response():
    """Create mock OpenAI response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "regime": "BULL",
        "confidence": 0.85,
        "reasoning": "SPY above both moving averages with low VIX indicates bullish conditions",
        "key_factors": ["SPY > 50MA", "SPY > 200MA", "VIX < 20"],
        "risk_level": "LOW"
    })
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 800
    mock_response.usage.completion_tokens = 150
    return mock_response


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def sample_market_data():
    """Create sample market data for testing."""
    return {
        "spy_price": 495.50,
        "spy_50ma": 480.25,
        "spy_200ma": 460.80,
        "vix": 15.25,
        "vix_percentile": 35.0,
        "recent_returns": {
            "1d": 0.45,
            "5d": 1.82,
            "20d": 3.25,
            "60d": 8.50,
        },
        "credit_spreads": {
            "investment_grade_spread": 1.20,
            "high_yield_spread": 3.50,
        },
        "economic_indicators": {
            "unemployment_rate": 3.9,
            "gdp_growth": 2.8,
            "inflation_rate": 2.9,
            "consumer_sentiment": 75.0,
        },
        "earnings_season": {
            "beat_rate": 72.0,
            "avg_surprise": 5.2,
        },
    }


@pytest.fixture
def sample_candidates():
    """Create sample stock candidates for screening."""
    return [
        {"ticker": "AAPL", "sector": "Technology", "risk_score": 0.15},
        {"ticker": "MSFT", "sector": "Technology", "risk_score": 0.12},
        {"ticker": "JNJ", "sector": "Healthcare", "risk_score": 0.08},
        {"ticker": "XOM", "sector": "Energy", "risk_score": 0.25},
        {"ticker": "NEE", "sector": "Utilities", "risk_score": 0.10},
        {"ticker": "PG", "sector": "Consumer Staples", "risk_score": 0.09},
        {"ticker": "AMZN", "sector": "Consumer Discretionary", "risk_score": 0.18},
        {"ticker": "JPM", "sector": "Financials", "risk_score": 0.22},
    ]


# ============================================================================
# Unit Tests - Market Regimes
# ============================================================================

class TestMarketRegimes:
    """Test market regime definitions."""
    
    def test_all_regimes_defined(self):
        """Test all four regimes are defined."""
        expected_regimes = ["BULL", "SIDEWAYS", "RISK_OFF", "CRASH"]
        for regime in expected_regimes:
            assert regime in MARKET_REGIMES
    
    def test_regime_has_required_keys(self):
        """Test each regime has required keys."""
        required_keys = ["description", "characteristics", "sector_weights"]
        for regime, data in MARKET_REGIMES.items():
            for key in required_keys:
                assert key in data, f"{regime} missing {key}"
    
    def test_sector_weights_complete(self):
        """Test all sectors have weights in each regime."""
        expected_sectors = [
            "Technology", "Consumer Discretionary", "Industrials",
            "Financials", "Communication Services", "Materials",
            "Healthcare", "Real Estate", "Consumer Staples",
            "Utilities", "Energy"
        ]
        
        for regime, data in MARKET_REGIMES.items():
            for sector in expected_sectors:
                assert sector in data["sector_weights"], \
                    f"{regime} missing sector weight for {sector}"
    
    def test_bull_regime_weights(self):
        """Test BULL regime favors growth sectors."""
        weights = MARKET_REGIMES["BULL"]["sector_weights"]
        
        # Growth sectors should be overweight (>1.0)
        assert weights["Technology"] > 1.0
        assert weights["Consumer Discretionary"] > 1.0
        
        # Defensive sectors should be underweight (<1.0)
        assert weights["Utilities"] < 1.0
        assert weights["Consumer Staples"] < 1.0
    
    def test_crash_regime_weights(self):
        """Test CRASH regime favors defensive sectors."""
        weights = MARKET_REGIMES["CRASH"]["sector_weights"]
        
        # Defensive sectors should be overweight
        assert weights["Consumer Staples"] > 1.0
        assert weights["Utilities"] > 1.0
        
        # Growth sectors should be heavily underweight
        assert weights["Technology"] < 0.5
        assert weights["Consumer Discretionary"] < 0.5


# ============================================================================
# Unit Tests - ChatGPT Client
# ============================================================================

class TestChatGPTClient:
    """Test ChatGPT client functionality."""
    
    @pytest.mark.asyncio
    async def test_detect_regime_mock(
        self,
        mock_openai_response,
        mock_redis,
        sample_market_data
    ):
        """Test regime detection with mocked API."""
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI") as mock_async:
                        mock_client = AsyncMock()
                        mock_client.chat.completions.create = AsyncMock(
                            return_value=mock_openai_response
                        )
                        mock_async.return_value = mock_client
                        
                        client = ChatGPTClient(redis_client=mock_redis)
                        result = await client.detect_regime(sample_market_data)
                        
                        assert result["regime"] == "BULL"
                        assert result["confidence"] == 0.85
                        assert "sector_weights" in result
                        assert "cost_usd" in result
                        assert result["cost_usd"] > 0
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, mock_redis, sample_market_data):
        """Test cache hit scenario."""
        cached_data = {
            "regime": "SIDEWAYS",
            "confidence": 0.75,
            "reasoning": "Cached data",
            "sector_weights": MARKET_REGIMES["SIDEWAYS"]["sector_weights"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))
        
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI"):
                        client = ChatGPTClient(redis_client=mock_redis)
                        result = await client.detect_regime(sample_market_data)
                        
                        assert result["regime"] == "SIDEWAYS"
                        assert client.metrics["cache_hits"] == 1
    
    @pytest.mark.asyncio
    async def test_fallback_on_error(self, mock_redis, sample_market_data):
        """Test fallback to rule-based detection on API error."""
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI") as mock_async:
                        mock_client = AsyncMock()
                        mock_client.chat.completions.create = AsyncMock(
                            side_effect=Exception("API Error")
                        )
                        mock_async.return_value = mock_client
                        
                        client = ChatGPTClient(redis_client=mock_redis)
                        result = await client.detect_regime(sample_market_data)
                        
                        # Should use fallback
                        assert result.get("fallback") is True
                        assert result["cost_usd"] == 0.0
                        assert result["regime"] in MARKET_REGIMES
    
    def test_cost_calculation(self):
        """Test cost calculation accuracy."""
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI"):
                        client = ChatGPTClient()
                        
                        # GPT-4 Turbo: $0.01/1K input, $0.03/1K output
                        cost = client._calculate_cost(1000, 1000)
                        expected = 0.01 + 0.03  # $0.04
                        assert abs(cost - expected) < 0.001
    
    def test_get_sector_weight(self):
        """Test sector weight retrieval."""
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI"):
                        client = ChatGPTClient()
                        
                        # BULL regime - Technology overweight
                        weight = client.get_sector_weight("BULL", "Technology")
                        assert weight == 1.5
                        
                        # CRASH regime - Technology underweight
                        weight = client.get_sector_weight("CRASH", "Technology")
                        assert weight == 0.3
                        
                        # Unknown sector defaults to 1.0
                        weight = client.get_sector_weight("BULL", "Unknown")
                        assert weight == 1.0
    
    def test_adjust_position_size(self):
        """Test position size adjustment."""
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI"):
                        client = ChatGPTClient()
                        
                        base_size = 1000.0
                        
                        # BULL + Technology = 1.5x
                        adjusted = client.adjust_position_size(
                            base_size, "BULL", "Technology"
                        )
                        assert adjusted == 1500.0
                        
                        # CRASH + Technology = 0.3x
                        adjusted = client.adjust_position_size(
                            base_size, "CRASH", "Technology"
                        )
                        assert adjusted == 300.0


# ============================================================================
# Unit Tests - Regime Based Screener
# ============================================================================

class TestRegimeBasedScreener:
    """Test regime-based stock screening."""
    
    @pytest.mark.asyncio
    async def test_filter_bull_regime(self, sample_candidates):
        """Test filtering in BULL regime."""
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI"):
                        client = ChatGPTClient()
                        screener = RegimeBasedScreener(client)
                        
                        filtered = await screener.filter_by_regime(
                            sample_candidates,
                            "BULL",
                            min_weight=0.8
                        )
                        
                        # Technology and Consumer Discretionary should be included
                        tickers = [c["ticker"] for c in filtered]
                        assert "AAPL" in tickers  # Technology: 1.5
                        assert "MSFT" in tickers  # Technology: 1.5
                        assert "AMZN" in tickers  # Consumer Discretionary: 1.3
                        
                        # Utilities (0.6) should be excluded
                        assert "NEE" not in tickers
    
    @pytest.mark.asyncio
    async def test_filter_crash_regime(self, sample_candidates):
        """Test filtering in CRASH regime."""
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI"):
                        client = ChatGPTClient()
                        screener = RegimeBasedScreener(client)
                        
                        filtered = await screener.filter_by_regime(
                            sample_candidates,
                            "CRASH",
                            min_weight=0.8
                        )
                        
                        # Only defensive sectors should remain
                        tickers = [c["ticker"] for c in filtered]
                        
                        # Healthcare (1.2) and Consumer Staples (1.5) should be included
                        assert "JNJ" in tickers
                        assert "PG" in tickers
                        
                        # Technology (0.3) should be excluded
                        assert "AAPL" not in tickers
                        assert "MSFT" not in tickers
    
    @pytest.mark.asyncio
    async def test_filter_preserves_regime_weight(self, sample_candidates):
        """Test that regime weight is added to candidates."""
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI"):
                        client = ChatGPTClient()
                        screener = RegimeBasedScreener(client)
                        
                        filtered = await screener.filter_by_regime(
                            sample_candidates,
                            "SIDEWAYS",
                            min_weight=0.0  # Include all
                        )
                        
                        for candidate in filtered:
                            assert "regime_weight" in candidate
    
    def test_get_regime_strategy(self):
        """Test strategy recommendations by regime."""
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI"):
                        client = ChatGPTClient()
                        screener = RegimeBasedScreener(client)
                        
                        # BULL strategy
                        bull_strategy = screener.get_regime_strategy("BULL")
                        assert bull_strategy["position_size_multiplier"] > 1.0
                        assert bull_strategy["max_positions"] == 20
                        
                        # CRASH strategy
                        crash_strategy = screener.get_regime_strategy("CRASH")
                        assert crash_strategy["position_size_multiplier"] < 1.0
                        assert crash_strategy["max_positions"] == 5


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for the complete flow."""
    
    @pytest.mark.asyncio
    async def test_full_regime_detection_flow(
        self,
        mock_openai_response,
        mock_redis,
        sample_market_data,
        sample_candidates
    ):
        """Test complete flow: detect regime -> filter candidates."""
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI") as mock_async:
                        mock_client = AsyncMock()
                        mock_client.chat.completions.create = AsyncMock(
                            return_value=mock_openai_response
                        )
                        mock_async.return_value = mock_client
                        
                        # Detect regime
                        client = ChatGPTClient(redis_client=mock_redis)
                        regime_result = await client.detect_regime(sample_market_data)
                        
                        # Filter candidates based on regime
                        screener = RegimeBasedScreener(client)
                        filtered = await screener.filter_by_regime(
                            sample_candidates,
                            regime_result["regime"]
                        )
                        
                        # Verify flow
                        assert regime_result["regime"] == "BULL"
                        assert len(filtered) < len(sample_candidates)
                        
                        # Top candidates should have high regime weights
                        if filtered:
                            top_weight = filtered[0]["regime_weight"]
                            assert top_weight >= 0.8
    
    @pytest.mark.asyncio
    async def test_caching_reduces_costs(
        self,
        mock_openai_response,
        mock_redis,
        sample_market_data
    ):
        """Test that caching reduces API costs."""
        # First call - cache miss
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI") as mock_async:
                        mock_client = AsyncMock()
                        mock_client.chat.completions.create = AsyncMock(
                            return_value=mock_openai_response
                        )
                        mock_async.return_value = mock_client
                        
                        client = ChatGPTClient(redis_client=mock_redis)
                        
                        # First call - API hit
                        result1 = await client.detect_regime(sample_market_data)
                        assert result1["cost_usd"] > 0
                        
                        # Second call - cache hit
                        cached_data = json.dumps(result1)
                        mock_redis.get = AsyncMock(return_value=cached_data)
                        
                        result2 = await client.detect_regime(sample_market_data)
                        
                        # Cache hit should not increase cost
                        assert client.metrics["cache_hits"] == 1
                        assert client.metrics["total_requests"] == 1


# ============================================================================
# Scenario Tests
# ============================================================================

class TestScenarios:
    """Test real-world scenarios."""
    
    @pytest.mark.asyncio
    async def test_market_crash_scenario(self):
        """Test behavior during market crash."""
        crash_market_data = {
            "spy_price": 380.00,
            "spy_50ma": 420.00,
            "spy_200ma": 450.00,
            "vix": 45.0,
            "vix_percentile": 95.0,
            "recent_returns": {
                "1d": -3.5,
                "5d": -12.0,
                "20d": -18.0,
                "60d": -25.0,
            },
            "credit_spreads": {
                "investment_grade_spread": 3.50,
                "high_yield_spread": 8.00,
            },
            "economic_indicators": {
                "unemployment_rate": 6.5,
                "gdp_growth": -1.5,
                "inflation_rate": 4.5,
                "consumer_sentiment": 55.0,
            },
            "earnings_season": {
                "beat_rate": 48.0,
                "avg_surprise": -8.0,
            },
        }
        
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI"):
                        client = ChatGPTClient()
                        
                        # Fallback should detect CRASH
                        result = client._get_fallback_regime(crash_market_data)
                        
                        assert result["regime"] == "CRASH"
                        assert result["risk_level"] == "HIGH"
                        assert result["fallback"] is True
    
    @pytest.mark.asyncio
    async def test_bull_market_scenario(self):
        """Test behavior during bull market."""
        bull_market_data = {
            "spy_price": 520.00,
            "spy_50ma": 505.00,
            "spy_200ma": 480.00,
            "vix": 12.5,
            "vix_percentile": 15.0,
            "recent_returns": {
                "1d": 0.8,
                "5d": 2.5,
                "20d": 5.0,
                "60d": 12.0,
            },
            "credit_spreads": {
                "investment_grade_spread": 1.00,
                "high_yield_spread": 3.00,
            },
            "economic_indicators": {
                "unemployment_rate": 3.5,
                "gdp_growth": 3.2,
                "inflation_rate": 2.5,
                "consumer_sentiment": 82.0,
            },
            "earnings_season": {
                "beat_rate": 78.0,
                "avg_surprise": 8.5,
            },
        }
        
        with patch("chatgpt_client.OPENAI_AVAILABLE", True):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                with patch("chatgpt_client.OpenAI"):
                    with patch("chatgpt_client.AsyncOpenAI"):
                        client = ChatGPTClient()
                        
                        # Fallback should detect BULL
                        result = client._get_fallback_regime(bull_market_data)
                        
                        assert result["regime"] == "BULL"
                        assert result["confidence"] >= 0.6


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "--tb=short"])
