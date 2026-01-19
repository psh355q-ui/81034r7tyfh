"""
RegimeGuard Tests

Market Intelligence v2.0 - Phase 4, T4.1

Tests for the Regime Guard component that detects market regime changes
and automatically adjusts signal strength when regimes shift.

Key Features:
1. Regime change detection (correlation shift, win rate drop, pattern collapse)
2. Signal strength adjustment during regime changes
3. Historical regime tracking
4. Automatic confidence reduction in new regimes
5. Regime recovery monitoring

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from backend.ai.intelligence.regime_guard import (
    RegimeGuard,
    RegimeState,
    RegimeType,
    RegimeChange,
    RegimeMetrics,
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

            # Return regime-specific analysis
            if "regime change" in user_prompt.lower():
                content = """**Regime Change Detected**

**Change Type**: Correlation Breakdown
**Severity**: HIGH
**Impact**: Signal patterns no longer reliable
**Recommendation**: Reduce signal strength by 50%"""
            else:
                content = "Market regime analysis complete."

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
        def __init__(self):
            # Mock historical correlations
            self.historical_correlations = [0.7, 0.72, 0.68, 0.75, 0.71]  # Stable regime
            self.current_correlation = 0.3  # Sudden drop

            # Mock win rates
            self.historical_win_rates = [0.65, 0.68, 0.63, 0.70, 0.66]  # Good performance
            self.current_win_rate = 0.45  # Significant drop

            # Mock pattern explanatory power
            self.historical_pattern_scores = [0.8, 0.82, 0.78, 0.85, 0.81]
            self.current_pattern_score = 0.5  # Pattern breakdown

        async def get_correlation_history(self, days: int = 30) -> list:
            """Get historical correlation data"""
            return self.historical_correlations

        async def get_current_correlation(self) -> float:
            """Get current market correlation"""
            return self.current_correlation

        async def get_win_rate_history(self, days: int = 30) -> list:
            """Get historical win rate data"""
            return self.historical_win_rates

        async def get_current_win_rate(self) -> float:
            """Get current win rate"""
            return self.current_win_rate

        async def get_pattern_scores(self, days: int = 30) -> list:
            """Get historical pattern scores"""
            return self.historical_pattern_scores

        async def get_current_pattern_score(self) -> float:
            """Get current pattern score"""
            return self.current_pattern_score

    return MockMarketDataProvider()


@pytest.fixture
def regime_guard(mock_llm, mock_market_data):
    """Create RegimeGuard instance"""
    return RegimeGuard(
        llm_provider=mock_llm,
        market_data=mock_market_data,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestRegimeGuardBasic:
    """Test basic RegimeGuard functionality"""

    def test_initialization(self, regime_guard):
        """Test guard initializes correctly"""
        assert regime_guard.name == "RegimeGuard"
        assert regime_guard.phase.value == "P2"
        assert regime_guard._enabled is True

    @pytest.mark.asyncio
    async def test_detect_regime_change(self, regime_guard):
        """Test regime change detection"""
        market_data = {
            "correlation_current": 0.3,
            "correlation_historical": [0.7, 0.72, 0.68, 0.75, 0.71],
            "win_rate_current": 0.45,
            "win_rate_historical": [0.65, 0.68, 0.63, 0.70, 0.66],
        }

        result = await regime_guard.detect_regime_change(market_data)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "regime_state" in result.data


# ============================================================================
# Test: Regime Change Detection
# ============================================================================

class TestRegimeChangeDetection:
    """Test regime change detection methods"""

    @pytest.mark.asyncio
    async def test_correlation_shift_detection(self, regime_guard):
        """Test detection of correlation shifts"""
        market_data = {
            "correlation_current": 0.3,  # Significant drop from 0.7
            "correlation_historical": [0.7, 0.72, 0.68, 0.75, 0.71],
        }

        result = await regime_guard.detect_regime_change(market_data)

        assert result.data["correlation_shift"] is True
        assert result.data["correlation_change_magnitude"] >= 0.3

    @pytest.mark.asyncio
    async def test_win_rate_drop_detection(self, regime_guard):
        """Test detection of win rate drops"""
        market_data = {
            "win_rate_current": 0.45,  # Drop from ~0.66
            "win_rate_historical": [0.65, 0.68, 0.63, 0.70, 0.66],
        }

        result = await regime_guard.detect_regime_change(market_data)

        assert result.data["win_rate_drop"] is True
        assert result.data["win_rate_change_magnitude"] >= 0.15

    @pytest.mark.asyncio
    async def test_pattern_collapse_detection(self, regime_guard):
        """Test detection of pattern explanatory power collapse"""
        market_data = {
            "pattern_score_current": 0.5,  # Drop from ~0.8
            "pattern_score_historical": [0.8, 0.82, 0.78, 0.85, 0.81],
        }

        result = await regime_guard.detect_regime_change(market_data)

        assert result.data["pattern_collapse"] is True
        assert result.data["pattern_score_change_magnitude"] >= 0.25

    @pytest.mark.asyncio
    async def test_no_regime_change_stable_market(self, regime_guard):
        """Test that stable market shows no regime change"""
        market_data = {
            "correlation_current": 0.71,
            "correlation_historical": [0.7, 0.72, 0.68, 0.75, 0.71],
            "win_rate_current": 0.66,
            "win_rate_historical": [0.65, 0.68, 0.63, 0.70, 0.66],
            "pattern_score_current": 0.81,
            "pattern_score_historical": [0.8, 0.82, 0.78, 0.85, 0.81],
        }

        result = await regime_guard.detect_regime_change(market_data)

        assert result.data["regime_state"] == "STABLE"
        assert result.data["regime_changed"] is False


# ============================================================================
# Test: Signal Strength Adjustment
# ============================================================================

class TestSignalStrengthAdjustment:
    """Test signal strength adjustment during regime changes"""

    @pytest.mark.asyncio
    async def test_adjust_strength_on_regime_change(self, regime_guard):
        """Test that signal strength is reduced when regime changes"""
        signal_data = {
            "original_confidence": 0.8,
            "regime_state": "CHANGED",
            "change_severity": "HIGH",
        }

        result = await regime_guard.signal_strength_adjustment(signal_data)

        assert result.success is True
        assert result.data["adjusted_confidence"] < signal_data["original_confidence"]
        assert result.data["adjustment_factor"] <= 0.7  # Should be reduced

    @pytest.mark.asyncio
    async def test_no_adjustment_in_stable_regime(self, regime_guard):
        """Test that no adjustment occurs in stable regime"""
        signal_data = {
            "original_confidence": 0.8,
            "regime_state": "STABLE",
        }

        result = await regime_guard.signal_strength_adjustment(signal_data)

        assert result.success is True
        assert result.data["adjusted_confidence"] == signal_data["original_confidence"]
        assert result.data["adjustment_factor"] == 1.0

    @pytest.mark.asyncio
    async def test_gradual_recovery_after_regime_change(self, regime_guard):
        """Test gradual signal strength recovery after regime stabilizes"""
        signal_data = {
            "original_confidence": 0.8,
            "regime_state": "RECOVERING",
            "days_since_change": 14,
        }

        result = await regime_guard.signal_strength_adjustment(signal_data)

        assert result.success is True
        # Should partially recovered but not full strength
        assert 0.5 <= result.data["adjustment_factor"] <= 0.9


# ============================================================================
# Test: Regime State Enum
# ============================================================================

class TestRegimeState:
    """Test RegimeState enum"""

    def test_stable_state(self):
        """Test STABLE regime state"""
        state = RegimeState.STABLE
        assert state.value == "STABLE"

    def test_changed_state(self):
        """Test CHANGED regime state"""
        state = RegimeState.CHANGED
        assert state.value == "CHANGED"

    def test_recovering_state(self):
        """Test RECOVERING regime state"""
        state = RegimeState.RECOVERING
        assert state.value == "RECOVERING"


# ============================================================================
# Test: Regime Type Enum
# ============================================================================

class TestRegimeType:
    """Test RegimeType enum"""

    def test_bull_market_type(self):
        """Test BULL_MARKET regime type"""
        regime_type = RegimeType.BULL_MARKET
        assert regime_type.value == "BULL_MARKET"

    def test_bear_market_type(self):
        """Test BEAR_MARKET regime type"""
        regime_type = RegimeType.BEAR_MARKET
        assert regime_type.value == "BEAR_MARKET"

    def test_sideways_type(self):
        """Test SIDEWAYS regime type"""
        regime_type = RegimeType.SIDEWAYS
        assert regime_type.value == "SIDEWAYS"


# ============================================================================
# Test: Regime Metrics Data Class
# ============================================================================

class TestRegimeMetrics:
    """Test RegimeMetrics data class"""

    def test_regime_metrics_creation(self):
        """Test creating RegimeMetrics"""
        metrics = RegimeMetrics(
            correlation_shift=True,
            correlation_change_magnitude=0.4,
            win_rate_drop=True,
            win_rate_change_magnitude=0.2,
            pattern_collapse=True,
            pattern_score_change_magnitude=0.3,
            overall_change_score=0.8,
        )

        assert metrics.correlation_shift is True
        assert metrics.overall_change_score == 0.8

    def test_regime_metrics_to_dict(self):
        """Test converting RegimeMetrics to dictionary"""
        metrics = RegimeMetrics(
            correlation_shift=False,
            correlation_change_magnitude=0.0,
            win_rate_drop=False,
            win_rate_change_magnitude=0.0,
            pattern_collapse=False,
            pattern_score_change_magnitude=0.0,
            overall_change_score=0.1,
        )

        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert metrics_dict["overall_change_score"] == 0.1


# ============================================================================
# Test: Regime Change Data Class
# ============================================================================

class TestRegimeChange:
    """Test RegimeChange data class"""

    def test_regime_change_creation(self):
        """Test creating RegimeChange"""
        change = RegimeChange(
            detected_at=datetime.now(),
            from_regime=RegimeType.BULL_MARKET,
            to_regime=RegimeType.BEAR_MARKET,
            severity="HIGH",
            metrics=RegimeMetrics(
                correlation_shift=True,
                correlation_change_magnitude=0.4,
                win_rate_drop=True,
                win_rate_change_magnitude=0.2,
                pattern_collapse=True,
                pattern_score_change_magnitude=0.3,
                overall_change_score=0.85,
            ),
        )

        assert change.from_regime == RegimeType.BULL_MARKET
        assert change.to_regime == RegimeType.BEAR_MARKET
        assert change.severity == "HIGH"

    def test_regime_change_to_dict(self):
        """Test converting RegimeChange to dictionary"""
        metrics = RegimeMetrics(
            correlation_shift=True,
            correlation_change_magnitude=0.3,
            win_rate_drop=False,
            win_rate_change_magnitude=0.0,
            pattern_collapse=False,
            pattern_score_change_magnitude=0.0,
            overall_change_score=0.6,
        )

        change = RegimeChange(
            detected_at=datetime.now(),
            from_regime=RegimeType.SIDEWAYS,
            to_regime=RegimeType.BULL_MARKET,
            severity="MEDIUM",
            metrics=metrics,
        )

        change_dict = change.to_dict()

        assert isinstance(change_dict, dict)
        assert change_dict["severity"] == "MEDIUM"


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestRegimeGuardEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_market_data(self, regime_guard):
        """Test handling of empty market data"""
        market_data = {}

        result = await regime_guard.detect_regime_change(market_data)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, regime_guard):
        """Test handling of LLM errors"""
        class ErrorLLM:
            async def complete_with_system(self, system_prompt, user_prompt, config=None):
                raise Exception("LLM Error")

        original_llm = regime_guard.llm
        regime_guard.llm = ErrorLLM()

        market_data = {"correlation_current": 0.3}

        result = await regime_guard.detect_regime_change(market_data)

        # Restore original
        regime_guard.llm = original_llm

        # Should handle error gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_extreme_correlation_shift(self, regime_guard):
        """Test handling of extreme correlation shift"""
        market_data = {
            "correlation_current": -0.5,  # Negative correlation
            "correlation_historical": [0.7, 0.72, 0.68, 0.75, 0.71],
            "win_rate_current": 0.4,  # Also add win rate drop to trigger regime change
            "win_rate_historical": [0.65, 0.68, 0.63, 0.70, 0.66],
        }

        result = await regime_guard.detect_regime_change(market_data)

        assert result.data["correlation_shift"] is True
        # With both correlation shift and win rate drop, regime should change
        assert result.data["regime_changed"] is True

    @pytest.mark.asyncio
    async def test_zero_win_rate(self, regime_guard):
        """Test handling of zero win rate"""
        market_data = {
            "win_rate_current": 0.0,
            "win_rate_historical": [0.65, 0.68, 0.63, 0.70, 0.66],
        }

        result = await regime_guard.detect_regime_change(market_data)

        assert result.data["win_rate_drop"] is True


# ============================================================================
# Test: Regime Recovery Tracking
# ============================================================================

class TestRegimeRecovery:
    """Test regime recovery tracking"""

    @pytest.mark.asyncio
    async def test_track_recovery_progress(self, regime_guard):
        """Test tracking recovery progress after regime change"""
        recovery_data = {
            "days_since_change": 30,
            "current_win_rate": 0.60,
            "baseline_win_rate": 0.66,
        }

        result = await regime_guard.check_recovery_progress(recovery_data)

        assert result.success is True
        assert "recovery_progress" in result.data
        assert result.data["recovery_progress"] >= 0.0

    @pytest.mark.asyncio
    async def test_full_recovery_detected(self, regime_guard):
        """Test detection of full recovery"""
        recovery_data = {
            "days_since_change": 60,
            "current_win_rate": 0.67,
            "baseline_win_rate": 0.66,
        }

        result = await regime_guard.check_recovery_progress(recovery_data)

        assert result.data["recovered"] is True
        assert result.data["recovery_progress"] >= 0.95


# ============================================================================
# Test: Historical Regime Tracking
# ============================================================================

class TestHistoricalRegimeTracking:
    """Test historical regime tracking"""

    @pytest.mark.asyncio
    async def test_record_regime_change(self, regime_guard):
        """Test recording a regime change"""
        change_data = {
            "from_regime": "BULL_MARKET",
            "to_regime": "BEAR_MARKET",
            "severity": "HIGH",
        }

        result = await regime_guard.record_regime_change(change_data)

        assert result.success is True
        assert "change_recorded" in result.data

    @pytest.mark.asyncio
    async def test_get_regime_history(self, regime_guard):
        """Test getting regime change history"""
        result = await regime_guard.get_regime_history({"days": 90})

        assert result.success is True
        assert "history" in result.data


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
