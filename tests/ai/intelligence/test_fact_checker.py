"""
FactChecker Tests

Market Intelligence v2.0 - Phase 1, T1.3

Tests for the Fact Checker component that validates LLM-extracted data against
external sources (YFinance, SEC, FRED) to prevent hallucinations.

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime

from backend.ai.intelligence.fact_checker import (
    FactChecker,
    FactCheckResult,
    FactVerificationStatus,
)
from backend.ai.intelligence.base import IntelligenceResult
from backend.ai.llm_providers import LLMProvider


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_apis():
    """Mock external API clients"""
    class MockYFinance:
        async def get_latest_earnings(self, ticker: str):
            # Return mock earnings data
            # Simulate "not found" for specific tickers
            if ticker == "NOTFOUND":
                return None
            return {
                "ticker": ticker,
                "revenue": 60.9,  # Billion dollars
                "eps": 3.25,
                "quarter": "Q4",
                "fiscal_year": 2025,
            }

        async def get_current_price(self, ticker: str):
            return {
                "ticker": ticker,
                "price": 150.0,
                "change_percent": 2.5,
            }

    class MockSEC:
        async def get_filing(self, ticker: str, form_type: str = "10-K", year: int = None):
            return {
                "ticker": ticker,
                "form_type": form_type,
                "fiscal_year": year or 2025,
                "revenue": 60.9,
                "r_and_d": 10.4,
            }

        async def verify_policy_number(self, policy_name: str, extracted_amount: float, tolerance: float = 0.05):
            # Mock policy verification
            policies = {
                "chips act": 52.7,
                "inflation reduction act": 369,
            }
            actual = policies.get(policy_name.lower())
            if actual is None:
                return {"verified": False, "reason": "Policy not found"}
            diff_pct = abs(extracted_amount - actual) / actual
            return {
                "verified": diff_pct <= tolerance,
                "extracted": extracted_amount,
                "actual": actual,
                "diff_pct": diff_pct,
            }

    class MockFRED:
        async def get_latest_value(self, series_id: str):
            # Mock economic data
            data = {
                "FEDFUNDS": 5.25,  # Federal funds rate
                "UNRATE": 4.1,     # Unemployment rate
                "CPIAUCSL": 310.5, # CPI
            }
            return data.get(series_id)

        async def verify_economic_indicator(self, indicator_name: str, extracted_value: float, tolerance: float = 0.02):
            # Map indicator names to series IDs and values
            indicators = {
                "fed funds rate": ("FEDFUNDS", 5.25),
                "unemployment rate": ("UNRATE", 4.1),
                "cpi": ("CPIAUCSL", 310.5),
            }
            key = indicator_name.lower()
            if key not in indicators:
                return {"verified": False, "reason": "Indicator not found"}
            series_id, actual = indicators[key]
            diff_pct = abs(extracted_value - actual) / actual
            return {
                "verified": diff_pct <= tolerance,
                "extracted": extracted_value,
                "actual": actual,
                "series_id": series_id,
                "diff_pct": diff_pct,
            }

    return {
        "yfinance": MockYFinance(),
        "sec": MockSEC(),
        "fred": MockFRED(),
    }


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
def checker(mock_llm, mock_apis):
    """Create FactChecker instance"""
    return FactChecker(
        llm_provider=mock_llm,
        yfinance_client=mock_apis["yfinance"],
        sec_client=mock_apis["sec"],
        fred_client=mock_apis["fred"],
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestFactCheckerBasic:
    """Test basic FactChecker functionality"""

    def test_initialization(self, checker):
        """Test checker initializes correctly"""
        assert checker.name == "FactChecker"
        assert checker.phase.value == "P0"
        assert checker._enabled is True

    @pytest.mark.asyncio
    async def test_verify_earnings_data(self, checker):
        """Test verification of earnings data"""
        extracted_data = {
            "ticker": "NVDA",
            "revenue": 61.0,  # Slightly different from mock (60.9)
            "eps": 3.2,       # Slightly different from mock (3.25)
        }

        result = await checker.verify_earnings(extracted_data)

        assert isinstance(result, FactCheckResult)
        assert result.data_type == "earnings"
        assert result.verified is True  # Within tolerance
        assert result.extracted_value == 61.0
        assert result.actual_value == 60.9

    @pytest.mark.asyncio
    async def test_verify_economic_indicator(self, checker):
        """Test verification of economic indicators"""
        extracted_data = {
            "indicator_name": "fed funds rate",
            "value": 5.30,  # Slightly different from mock (5.25)
        }

        result = await checker.verify_economic_indicator(extracted_data)

        assert isinstance(result, FactCheckResult)
        assert result.data_type == "economic_indicator"
        assert result.verified is True  # Within 2% tolerance
        assert abs(result.diff_percentage) < 0.02

    @pytest.mark.asyncio
    async def test_verify_policy_number(self, checker):
        """Test verification of policy-related numbers"""
        extracted_data = {
            "policy_name": "CHIPS Act",
            "allocated_amount": 53.0,  # Slightly different from mock (52.7)
        }

        result = await checker.verify_policy(extracted_data)

        assert isinstance(result, FactCheckResult)
        assert result.data_type == "policy"
        assert result.verified is True  # Within 5% tolerance


# ============================================================================
# Test: Verification Tolerance
# ============================================================================

class TestVerificationTolerance:
    """Test verification tolerance thresholds"""

    @pytest.mark.asyncio
    async def test_within_tolerance_passes(self, checker):
        """Test that values within tolerance pass verification"""
        extracted_data = {
            "ticker": "NVDA",
            "revenue": 62.0,  # About 1.8% off from 60.9
        }

        result = await checker.verify_earnings(extracted_data, tolerance=0.05)

        assert result.verified is True
        assert abs(result.diff_percentage) <= 0.05

    @pytest.mark.asyncio
    async def test_outside_tolerance_fails(self, checker):
        """Test that values outside tolerance fail verification"""
        extracted_data = {
            "ticker": "NVDA",
            "revenue": 70.0,  # About 15% off from 60.9
        }

        result = await checker.verify_earnings(extracted_data, tolerance=0.05)

        assert result.verified is False
        assert abs(result.diff_percentage) > 0.05

    @pytest.mark.asyncio
    async def test_custom_tolerance(self, checker):
        """Test custom tolerance levels"""
        extracted_data = {
            "ticker": "NVDA",
            "revenue": 65.0,  # About 6.7% off from 60.9
        }

        # Should fail with 5% tolerance
        result1 = await checker.verify_earnings(extracted_data, tolerance=0.05)
        assert result1.verified is False

        # Should pass with 10% tolerance
        result2 = await checker.verify_earnings(extracted_data, tolerance=0.10)
        assert result2.verified is True


# ============================================================================
# Test: Data Type Detection
# ============================================================================

class TestDataTypeDetection:
    """Test automatic detection of data types"""

    @pytest.mark.asyncio
    async def test_detect_earnings_type(self, checker):
        """Test detection of earnings data type"""
        data = {
            "ticker": "AAPL",
            "revenue": 100.0,
            "eps": 2.0,
        }

        detected = checker._detect_data_type(data)
        assert detected == "earnings"

    @pytest.mark.asyncio
    async def test_detect_economic_indicator_type(self, checker):
        """Test detection of economic indicator type"""
        data = {
            "indicator_name": "unemployment rate",
            "value": 4.0,
        }

        detected = checker._detect_data_type(data)
        assert detected == "economic_indicator"

    @pytest.mark.asyncio
    async def test_detect_policy_type(self, checker):
        """Test detection of policy data type"""
        data = {
            "policy_name": "Inflation Reduction Act",
            "allocated_amount": 400.0,
        }

        detected = checker._detect_data_type(data)
        assert detected == "policy"

    @pytest.mark.asyncio
    async def test_unknown_type(self, checker):
        """Test handling of unknown data types"""
        data = {
            "unknown_field": "some_value",
        }

        detected = checker._detect_data_type(data)
        assert detected == "unknown"


# ============================================================================
# Test: Confidence Adjustment
# ============================================================================

class TestConfidenceAdjustment:
    """Test confidence score adjustment based on verification"""

    @pytest.mark.asyncio
    async def test_confidence_boost_on_verification(self, checker):
        """Test that verified facts boost confidence"""
        original_confidence = 0.75
        result = FactCheckResult(
            verified=True,
            data_type="earnings",
            extracted_value=61.0,
            actual_value=60.9,
            diff_percentage=0.0016,
            confidence_adjustment=0.1,  # Explicitly set adjustment
        )

        adjusted = checker._adjust_confidence(original_confidence, result)
        assert adjusted > original_confidence  # Should be boosted
        assert adjusted <= 1.0  # But capped at 1.0

    @pytest.mark.asyncio
    async def test_confidence_penalty_on_failure(self, checker):
        """Test that failed verification penalizes confidence"""
        original_confidence = 0.75
        result = FactCheckResult(
            verified=False,
            data_type="earnings",
            extracted_value=70.0,
            actual_value=60.9,
            diff_percentage=0.15,
            confidence_adjustment=-0.2,  # Explicitly set adjustment
        )

        adjusted = checker._adjust_confidence(original_confidence, result)
        assert adjusted < original_confidence  # Should be penalized
        assert adjusted >= 0.0  # But not below 0.0

    @pytest.mark.asyncio
    async def test_no_change_for_small_discrepancy(self, checker):
        """Test that very small discrepancies don't change confidence much"""
        original_confidence = 0.85
        result = FactCheckResult(
            verified=True,
            data_type="earnings",
            extracted_value=60.91,
            actual_value=60.9,
            diff_percentage=0.00016,
            confidence_adjustment=0.001,  # Very small adjustment
        )

        adjusted = checker._adjust_confidence(original_confidence, result)
        # Should be very close to original
        assert abs(adjusted - original_confidence) < 0.01


# ============================================================================
# Test: Integration with Intelligence Components
# ============================================================================

class TestIntelligenceIntegration:
    """Test integration with intelligence components"""

    @pytest.mark.asyncio
    async def test_verify_narrative_analysis(self, checker):
        """Test verification of data from narrative analysis"""
        narrative_result = {
            "topic": "NVDA Earnings",
            "fact_layer": "NVDA reported Q4 revenue of $61B, beating estimates.",
            "extracted_data": {
                "ticker": "NVDA",
                "revenue": 61.0,
            },
            "confidence": 0.85,
        }

        result = await checker.verify_intelligence_result(narrative_result)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "verification_status" in result.data
        assert "adjusted_confidence" in result.data

    @pytest.mark.asyncio
    async def test_batch_verify_multiple_facts(self, checker):
        """Test verification of multiple facts at once"""
        facts_to_verify = [
            {
                "type": "earnings",
                "ticker": "NVDA",
                "revenue": 61.0,
            },
            {
                "type": "economic_indicator",
                "indicator_name": "fed funds rate",
                "value": 5.30,
            },
            {
                "type": "policy",
                "policy_name": "CHIPS Act",
                "allocated_amount": 53.0,
            },
        ]

        results = await checker.batch_verify(facts_to_verify)

        assert len(results) == 3
        assert all(isinstance(r, FactCheckResult) for r in results)
        assert sum(1 for r in results if r.verified) >= 2  # At least 2 should pass


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestFactCheckerEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_missing_ticker(self, checker):
        """Test handling of missing ticker symbol"""
        extracted_data = {
            "revenue": 61.0,  # Missing ticker
        }

        result = await checker.verify_earnings(extracted_data)

        assert result.verified is False
        assert "missing ticker" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_api_error_handling(self, checker):
        """Test handling of API errors"""
        # Make the API raise an error
        async def failing_get_latest_earnings(ticker):
            raise Exception("API Error")

        checker.yfinance_client.get_latest_earnings = failing_get_latest_earnings

        extracted_data = {
            "ticker": "INVALID",
            "revenue": 61.0,
        }

        result = await checker.verify_earnings(extracted_data)

        assert result.verified is False
        assert "api error" in result.reasoning.lower() or "error" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_data_not_found(self, checker):
        """Test handling when data is not found in external source"""
        extracted_data = {
            "ticker": "NOTFOUND",  # Non-existent ticker
            "revenue": 61.0,
        }

        result = await checker.verify_earnings(extracted_data)

        assert result.verified is False
        assert "not found" in result.reasoning.lower() or "no earnings" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_zero_value_handling(self, checker):
        """Test handling of zero values"""
        extracted_data = {
            "indicator_name": "fed funds rate",
            "value": 0.0,  # Zero value
        }

        result = await checker.verify_economic_indicator(extracted_data)

        # Should handle gracefully
        assert result is not None
        # Zero value is unlikely to match actual rate (5.25)
        assert result.verified is False

    @pytest.mark.asyncio
    async def test_negative_value_handling(self, checker):
        """Test handling of negative values"""
        extracted_data = {
            "ticker": "NVDA",
            "revenue": -50.0,  # Negative revenue (invalid)
        }

        result = await checker.verify_earnings(extracted_data)

        # Should handle but fail verification
        assert result.verified is False


# ============================================================================
# Test: FactCheckResult Data Class
# ============================================================================

class TestFactCheckResult:
    """Test FactCheckResult data class"""

    def test_fact_check_result_creation(self):
        """Test creating a FactCheckResult"""
        result = FactCheckResult(
            verified=True,
            data_type="earnings",
            extracted_value=61.0,
            actual_value=60.9,
            diff_percentage=0.0016,
            reasoning="Values match within tolerance",
        )

        assert result.verified is True
        assert result.data_type == "earnings"
        assert result.extracted_value == 61.0
        assert result.actual_value == 60.9
        assert abs(result.diff_percentage - 0.0016) < 0.0001

    def test_fact_check_result_to_dict(self):
        """Test converting FactCheckResult to dictionary"""
        result = FactCheckResult(
            verified=True,
            data_type="earnings",
            extracted_value=61.0,
            actual_value=60.9,
            diff_percentage=0.0016,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["verified"] is True
        assert result_dict["data_type"] == "earnings"
        assert result_dict["extracted_value"] == 61.0
        assert result_dict["actual_value"] == 60.9


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
