"""
InsightPostMortem Tests

Market Intelligence v2.0 - Phase 3, T3.2

Tests for the Insight Post-Mortem component that reviews insight performance
after 7/30 days and generates prompt improvements based on failure patterns.

Key Features:
1. Review insight performance (7-day and 30-day reviews)
2. Aggregate performance metrics by period
3. Generate prompt improvements from failure patterns
4. Track learning progress over time
5. Connect to insight_reviews table

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from backend.ai.intelligence.insight_postmortem import (
    InsightPostMortem,
    ReviewPeriod,
    InsightReview,
    PerformanceMetrics,
    PromptImprovement,
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

            # Return post-mortem specific analysis
            if "failure pattern" in user_prompt.lower() or "improvement" in user_prompt.lower():
                content = """Based on the review:

**Failure Patterns:**
1. Overestimated short-term catalyst impact
2. Insufficient consideration of market regime
3. Neglected sector rotation signals

**Prompt Improvements:**
- Add market regime check before generating signals
- Include sector momentum as required input
- Emphasize risk factors in prompt template
- Reduce confidence for catalyst-driven plays"""
            else:
                content = "Post-mortem analysis complete. Insight reviewed with performance metrics."

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
def mock_signal_repository():
    """Mock trading signal repository"""
    class MockSignalRepository:
        def __init__(self):
            # Mock signal data
            self.signals = {
                1: {
                    "id": 1,
                    "insight_id": 101,
                    "symbol": "NVDA",
                    "signal_type": "PRIMARY",
                    "generated_at": datetime.now() - timedelta(days=35),
                    "entry_price": 150.0,
                }
            }

        async def get_signal_performance(self, signal_id: int, period_days: int) -> Dict[str, Any]:
            """Return mock signal performance"""
            return {
                "signal_id": signal_id,
                "period_days": period_days,
                "entry_price": 150.0,
                "current_price": 165.0 if period_days >= 7 else 155.0,
                "max_price": 170.0,
                "min_price": 145.0,
                "return_pct": 10.0 if period_days >= 7 else 3.3,
                "max_drawdown_pct": -3.3,
                "sharpe_ratio": 1.5,
                "win": True,
            }

        async def get_insight_signals(self, insight_id: int) -> list:
            """Get all signals for an insight"""
            return [self.signals.get(1)]

        async def get_performance_summary(self, insight_id: int, period: str) -> Dict[str, Any]:
            """Get aggregated performance summary"""
            return {
                "insight_id": insight_id,
                "period": period,
                "total_signals": 5,
                "win_rate": 0.6,
                "avg_return": 5.2,
                "total_return": 26.0,
                "sharpe_ratio": 1.3,
                "max_drawdown": -8.5,
            }

    return MockSignalRepository()


@pytest.fixture
def insight_postmortem(mock_llm, mock_signal_repository):
    """Create InsightPostMortem instance"""
    return InsightPostMortem(
        llm_provider=mock_llm,
        signal_repository=mock_signal_repository,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestInsightPostMortemBasic:
    """Test basic InsightPostMortem functionality"""

    def test_initialization(self, insight_postmortem):
        """Test analyzer initializes correctly"""
        assert insight_postmortem.name == "InsightPostMortem"
        assert insight_postmortem.phase.value == "P2"
        assert insight_postmortem._enabled is True

    @pytest.mark.asyncio
    async def test_review_insight(self, insight_postmortem):
        """Test insight review"""
        review_data = {
            "insight_id": 101,
            "review_period": "7_DAY",
            "original_prediction": "NVDA will rise 15% on AI chip demand",
            "actual_outcome": "NVDA rose 10% with strong momentum",
        }

        result = await insight_postmortem.review_insight(review_data)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "performance" in result.data
        assert "review_period" in result.data


# ============================================================================
# Test: Review Periods
# ============================================================================

class TestReviewPeriods:
    """Test review period handling"""

    def test_7_day_review_period(self):
        """Test 7-day review period enum"""
        period = ReviewPeriod.DAY_7
        assert period.value == "7_DAY"
        assert period.days == 7

    def test_30_day_review_period(self):
        """Test 30-day review period enum"""
        period = ReviewPeriod.DAY_30
        assert period.value == "30_DAY"
        assert period.days == 30

    @pytest.mark.asyncio
    async def test_review_7_day_performance(self, insight_postmortem):
        """Test 7-day performance review"""
        review_data = {
            "insight_id": 101,
            "review_period": "7_DAY",
        }

        result = await insight_postmortem.review_insight(review_data)

        assert result.data["review_period"] == "7_DAY"
        assert "return_pct" in result.data["performance"]

    @pytest.mark.asyncio
    async def test_review_30_day_performance(self, insight_postmortem):
        """Test 30-day performance review"""
        review_data = {
            "insight_id": 101,
            "review_period": "30_DAY",
        }

        result = await insight_postmortem.review_insight(review_data)

        assert result.data["review_period"] == "30_DAY"
        assert "return_pct" in result.data["performance"]


# ============================================================================
# Test: Performance Metrics
# ============================================================================

class TestPerformanceMetrics:
    """Test performance metrics calculation"""

    @pytest.mark.asyncio
    async def test_calculate_return_percentage(self, insight_postmortem):
        """Test return percentage calculation"""
        review_data = {
            "insight_id": 101,
            "review_period": "7_DAY",
        }

        result = await insight_postmortem.review_insight(review_data)

        performance = result.data["performance"]
        assert "return_pct" in performance
        assert isinstance(performance["return_pct"], (int, float))

    @pytest.mark.asyncio
    async def test_track_max_drawdown(self, insight_postmortem):
        """Test max drawdown tracking"""
        review_data = {
            "insight_id": 101,
            "review_period": "7_DAY",
        }

        result = await insight_postmortem.review_insight(review_data)

        performance = result.data["performance"]
        assert "max_drawdown_pct" in performance
        assert performance["max_drawdown_pct"] <= 0  # Should be negative or zero

    @pytest.mark.asyncio
    async def test_calculate_sharpe_ratio(self, insight_postmortem):
        """Test Sharpe ratio calculation"""
        review_data = {
            "insight_id": 101,
            "review_period": "30_DAY",
        }

        result = await insight_postmortem.review_insight(review_data)

        performance = result.data["performance"]
        assert "sharpe_ratio" in performance


# ============================================================================
# Test: Aggregate Performance
# ============================================================================

class TestAggregatePerformance:
    """Test performance aggregation by period"""

    @pytest.mark.asyncio
    async def test_aggregate_7_day_performance(self, insight_postmortem):
        """Test 7-day performance aggregation"""
        result = await insight_postmortem.aggregate_performance({
            "insight_id": 101,
            "period": "7_DAY",
        })

        assert result.success is True
        assert "summary" in result.data
        assert "win_rate" in result.data["summary"]

    @pytest.mark.asyncio
    async def test_aggregate_30_day_performance(self, insight_postmortem):
        """Test 30-day performance aggregation"""
        result = await insight_postmortem.aggregate_performance({
            "insight_id": 101,
            "period": "30_DAY",
        })

        assert result.success is True
        assert "total_return" in result.data["summary"]

    @pytest.mark.asyncio
    async def test_aggregate_multiple_insights(self, insight_postmortem):
        """Test aggregating across multiple insights"""
        result = await insight_postmortem.aggregate_performance({
            "insight_ids": [101, 102, 103],
            "period": "30_DAY",
        })

        assert result.success is True
        assert "summary" in result.data


# ============================================================================
# Test: Prompt Improvement Generation
# ============================================================================

class TestPromptImprovement:
    """Test prompt improvement generation from failure patterns"""

    @pytest.mark.asyncio
    async def test_generate_prompt_improvement(self, insight_postmortem):
        """Test generating prompt improvements"""
        review_data = {
            "insight_id": 101,
            "review_period": "30_DAY",
            "performance": {
                "return_pct": -5.0,  # Loss
                "win": False,
            },
            "original_prediction": "Strong rally expected",
            "actual_outcome": "Market declined due to Fed concerns",
        }

        result = await insight_postmortem.generate_prompt_improvement(review_data)

        assert result.success is True
        assert "improvements" in result.data
        assert "failure_patterns" in result.data

    @pytest.mark.asyncio
    async def test_identify_failure_patterns(self, insight_postmortem):
        """Test failure pattern identification"""
        review_data = {
            "insight_id": 101,
            "performance": {"win": False, "return_pct": -10.0},
            "reasoning": "Overestimated catalyst impact",
        }

        result = await insight_postmortem.generate_prompt_improvement(review_data)

        assert "failure_patterns" in result.data
        assert len(result.data["failure_patterns"]) > 0

    @pytest.mark.asyncio
    async def test_generate_concrete_improvements(self, insight_postmortem):
        """Test generating concrete improvement suggestions"""
        review_data = {
            "insight_id": 101,
            "performance": {"win": False},
        }

        result = await insight_postmortem.generate_prompt_improvement(review_data)

        assert "improvements" in result.data
        assert len(result.data["improvements"]) > 0


# ============================================================================
# Test: Data Classes
# ============================================================================

class TestDataClasses:
    """Test data classes for post-mortem analysis"""

    def test_performance_metrics_creation(self):
        """Test PerformanceMetrics creation"""
        metrics = PerformanceMetrics(
            return_pct=10.5,
            max_drawdown_pct=-3.2,
            sharpe_ratio=1.8,
            win=True,
        )

        assert metrics.return_pct == 10.5
        assert metrics.win is True

    def test_performance_metrics_to_dict(self):
        """Test PerformanceMetrics to dictionary"""
        metrics = PerformanceMetrics(
            return_pct=5.0,
            max_drawdown_pct=-5.0,
            sharpe_ratio=1.2,
            win=True,
        )

        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert metrics_dict["return_pct"] == 5.0

    def test_insight_review_creation(self):
        """Test InsightReview creation"""
        metrics = PerformanceMetrics(
            return_pct=8.0,
            max_drawdown_pct=-2.0,
            sharpe_ratio=1.5,
            win=True,
        )

        review = InsightReview(
            insight_id=101,
            review_period=ReviewPeriod.DAY_7,
            performance=metrics,
            reviewed_at=datetime.now(),
        )

        assert review.insight_id == 101
        assert review.review_period == ReviewPeriod.DAY_7

    def test_prompt_improvement_creation(self):
        """Test PromptImprovement creation"""
        improvement = PromptImprovement(
            insight_id=101,
            failure_patterns=["Overestimated catalyst"],
            improvements=["Add regime check"],
            confidence=0.8,
        )

        assert improvement.insight_id == 101
        assert len(improvement.failure_patterns) > 0


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestInsightPostMortemEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_insufficient_data_for_review(self, insight_postmortem):
        """Test handling insufficient data for review"""
        review_data = {
            "insight_id": 999,  # Non-existent insight
            "review_period": "7_DAY",
        }

        result = await insight_postmortem.review_insight(review_data)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_review_period(self, insight_postmortem):
        """Test handling invalid review period"""
        review_data = {
            "insight_id": 101,
            "review_period": "INVALID_PERIOD",
        }

        result = await insight_postmortem.review_insight(review_data)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, insight_postmortem):
        """Test handling of LLM errors"""
        class ErrorLLM:
            async def complete_with_system(self, system_prompt, user_prompt, config=None):
                raise Exception("LLM Error")

        original_llm = insight_postmortem.llm
        insight_postmortem.llm = ErrorLLM()

        review_data = {
            "insight_id": 101,
            "review_period": "7_DAY",
        }

        result = await insight_postmortem.generate_prompt_improvement(review_data)

        # Restore original
        insight_postmortem.llm = original_llm

        # Should handle error gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_zero_performance(self, insight_postmortem):
        """Test handling zero performance (flat market)"""
        review_data = {
            "insight_id": 101,
            "performance": {"return_pct": 0.0, "win": False},
        }

        result = await insight_postmortem.generate_prompt_improvement(review_data)

        # Should handle flat performance
        assert result.success is True


# ============================================================================
# Test: Learning Progress
# ============================================================================

class TestLearningProgress:
    """Test learning progress tracking"""

    @pytest.mark.asyncio
    async def test_track_review_count(self, insight_postmortem):
        """Test tracking number of reviews performed"""
        initial_count = insight_postmortem.get_statistics()["total_reviews"]

        await insight_postmortem.review_insight({"insight_id": 101, "review_period": "7_DAY"})

        stats = insight_postmortem.get_statistics()
        assert stats["total_reviews"] >= initial_count

    @pytest.mark.asyncio
    async def test_track_performance_trend(self, insight_postmortem):
        """Test tracking performance trend over time"""
        # Perform multiple reviews
        for insight_id in [101, 102, 103]:
            await insight_postmortem.review_insight({
                "insight_id": insight_id,
                "review_period": "7_DAY",
            })

        stats = insight_postmortem.get_statistics()
        assert "avg_return" in stats or "total_reviews" in stats


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
