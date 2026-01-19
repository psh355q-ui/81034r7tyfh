"""
InsightPostMortem Component - Insight Performance Review

Market Intelligence v2.0 - Phase 3, T3.2

This component reviews insight performance after 7/30 days and generates
prompt improvements based on failure patterns to enable continuous learning.

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

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from .base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ..llm_providers import LLMProvider


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ReviewPeriod(Enum):
    """Review period for insight performance"""
    DAY_7 = "7_DAY"  # 7-day review
    DAY_30 = "30_DAY"  # 30-day review

    @property
    def days(self) -> int:
        """Number of days in review period"""
        if self == ReviewPeriod.DAY_7:
            return 7
        return 30


@dataclass
class PerformanceMetrics:
    """
    Performance metrics for an insight

    Attributes:
        return_pct: Return percentage
        max_drawdown_pct: Maximum drawdown percentage
        sharpe_ratio: Sharpe ratio (risk-adjusted return)
        win: Whether the insight was profitable
        volatility: Price volatility (optional)
    """
    return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win: bool
    volatility: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "return_pct": self.return_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "win": self.win,
            "volatility": self.volatility,
        }


@dataclass
class InsightReview:
    """
    Result of insight review

    Attributes:
        insight_id: ID of the insight being reviewed
        review_period: Review period (7-day or 30-day)
        performance: Performance metrics
        reasoning: Explanation of performance
        reviewed_at: Review timestamp
    """
    insight_id: int
    review_period: ReviewPeriod
    performance: PerformanceMetrics
    reasoning: str = ""
    reviewed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "insight_id": self.insight_id,
            "review_period": self.review_period.value,
            "performance": self.performance.to_dict(),
            "reasoning": self.reasoning,
            "reviewed_at": self.reviewed_at.isoformat(),
        }


@dataclass
class PromptImprovement:
    """
    Suggested prompt improvements

    Attributes:
        insight_id: ID of the insight that triggered improvements
        failure_patterns: List of identified failure patterns
        improvements: List of suggested improvements
        confidence: Confidence in improvement suggestions
        generated_at: Generation timestamp
    """
    insight_id: int
    failure_patterns: List[str]
    improvements: List[str]
    confidence: float = 0.7
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "insight_id": self.insight_id,
            "failure_patterns": self.failure_patterns,
            "improvements": self.improvements,
            "confidence": self.confidence,
            "generated_at": self.generated_at.isoformat(),
        }


# ============================================================================
# Main Component
# ============================================================================

class InsightPostMortem(BaseIntelligence):
    """
    Insight Post-Mortem Analyzer

    Reviews insight performance after 7/30 days and generates
    prompt improvements based on failure patterns.

    Key Features:
    1. 7-day and 30-day performance reviews
    2. Aggregated performance metrics
    3. Failure pattern analysis
    4. Prompt improvement generation
    5. Learning progress tracking

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.insightpostmortem import InsightPostMortem

        llm = get_llm_provider()
        analyzer = InsightPostMortem(
            llm_provider=llm,
            signal_repository=signal_repo,
        )

        # Review 7-day performance
        result = await analyzer.review_insight({
            "insight_id": 101,
            "review_period": "7_DAY",
        })

        # Generate prompt improvements
        improvements = await analyzer.generate_prompt_improvement({
            "insight_id": 101,
            "performance": {"win": False, "return_pct": -5.0},
        })
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        signal_repository: Optional[Any] = None,
    ):
        """
        Initialize InsightPostMortem

        Args:
            llm_provider: LLM Provider instance
            signal_repository: Trading signal repository (optional)
        """
        super().__init__(
            name="InsightPostMortem",
            phase=IntelligencePhase.P2,
        )

        self.llm = llm_provider
        self.signal_repository = signal_repository

        # Statistics
        self._review_count = 0
        self._period_counts = {
            "7_DAY": 0,
            "30_DAY": 0,
        }
        self._improvement_count = 0

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Review insight performance (main entry point)

        Args:
            data: Review data with:
                - insight_id: ID of insight to review
                - review_period: "7_DAY" or "30_DAY"
                - original_prediction: Original prediction (optional)
                - actual_outcome: Actual outcome (optional)

        Returns:
            IntelligenceResult: Review result with performance metrics
        """
        return await self.review_insight(data)

    async def review_insight(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Review insight performance

        Args:
            data: Review data

        Returns:
            IntelligenceResult: Review result
        """
        try:
            insight_id = data.get("insight_id", 0)
            period_str = data.get("review_period", "7_DAY")

            # Parse review period
            try:
                review_period = ReviewPeriod(period_str)
            except ValueError:
                return self.create_result(
                    success=False,
                    data={"stage": "insight_review"},
                    reasoning=f"Invalid review period: {period_str}",
                )

            # Get performance metrics
            performance = await self._get_performance_metrics(insight_id, review_period)

            # Generate reasoning
            original_prediction = data.get("original_prediction", "")
            actual_outcome = data.get("actual_outcome", "")
            reasoning = await self._generate_review_reasoning(
                insight_id, performance, original_prediction, actual_outcome
            )

            # Create review
            review = InsightReview(
                insight_id=insight_id,
                review_period=review_period,
                performance=performance,
                reasoning=reasoning,
            )

            # Update statistics
            self._review_count += 1
            self._period_counts[review_period.value] += 1

            return self.create_result(
                success=True,
                data={
                    "stage": "insight_review",
                    "insight_id": insight_id,
                    "review_period": review_period.value,
                    "performance": performance.to_dict(),
                    "reasoning": reasoning,
                },
                confidence=0.8 if performance.win else 0.6,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Insight review error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "insight_review"},
            )
            result.add_error(f"Review error: {str(e)}")
            return result

    async def aggregate_performance(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Aggregate performance metrics by period

        Args:
            data: Aggregation data with:
                - insight_id: Single insight ID
                - insight_ids: List of insight IDs (alternative)
                - period: "7_DAY" or "30_DAY"

        Returns:
            IntelligenceResult: Aggregated performance summary
        """
        try:
            period = data.get("period", "30_DAY")
            insight_ids = data.get("insight_ids")

            if not insight_ids:
                insight_id = data.get("insight_id", 0)
                insight_ids = [insight_id] if insight_id else []

            if not insight_ids:
                return self.create_result(
                    success=False,
                    data={"stage": "performance_aggregation"},
                    reasoning="No insight IDs provided",
                )

            # Get aggregated summary from repository
            if self.signal_repository:
                insight_id = insight_ids[0]  # Use first insight
                summary = await self.signal_repository.get_performance_summary(insight_id, period)
            else:
                # Mock summary
                summary = {
                    "total_signals": len(insight_ids),
                    "win_rate": 0.6,
                    "avg_return": 5.2,
                    "total_return": len(insight_ids) * 5.2,
                    "sharpe_ratio": 1.3,
                    "max_drawdown": -8.5,
                }

            return self.create_result(
                success=True,
                data={
                    "stage": "performance_aggregation",
                    "period": period,
                    "summary": summary,
                },
                reasoning=f"Aggregated performance for {len(insight_ids)} insights over {period}",
            )

        except Exception as e:
            logger.error(f"Performance aggregation error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "performance_aggregation"},
            )
            result.add_error(f"Aggregation error: {str(e)}")
            return result

    async def generate_prompt_improvement(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Generate prompt improvements from failure patterns

        Args:
            data: Improvement data with:
                - insight_id: ID of the insight
                - performance: Performance metrics dict
                - reasoning: Original reasoning (optional)

        Returns:
            IntelligenceResult: Improvement suggestions
        """
        try:
            insight_id = data.get("insight_id", 0)
            performance = data.get("performance", {})
            reasoning = data.get("reasoning", "")

            # Determine if improvement is needed
            win = performance.get("win", True)
            return_pct = performance.get("return_pct", 0.0)

            if win and return_pct > 0:
                # No improvement needed for successful insights
                return self.create_result(
                    success=True,
                    data={
                        "stage": "prompt_improvement",
                        "insight_id": insight_id,
                        "improvements": [],
                        "failure_patterns": [],
                        "reasoning": "No improvements needed - insight was successful",
                    },
                    reasoning="Insight performed well",
                )

            # Generate failure patterns and improvements
            failure_patterns, improvements = await self._analyze_failure_patterns(
                insight_id, performance, reasoning
            )

            # Calculate confidence
            confidence = self._calculate_improvement_confidence(performance)

            # Create improvement object
            improvement = PromptImprovement(
                insight_id=insight_id,
                failure_patterns=failure_patterns,
                improvements=improvements,
                confidence=confidence,
            )

            # Update statistics
            self._improvement_count += 1

            return self.create_result(
                success=True,
                data={
                    "stage": "prompt_improvement",
                    "insight_id": insight_id,
                    "improvements": improvements,
                    "failure_patterns": failure_patterns,
                    "confidence": confidence,
                },
                confidence=confidence,
                reasoning=f"Generated {len(improvements)} improvements from {len(failure_patterns)} failure patterns",
            )

        except Exception as e:
            logger.error(f"Prompt improvement generation error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "prompt_improvement"},
            )
            result.add_error(f"Generation error: {str(e)}")
            return result

    async def _get_performance_metrics(
        self,
        insight_id: int,
        review_period: ReviewPeriod,
    ) -> PerformanceMetrics:
        """Get performance metrics for an insight"""
        try:
            if self.signal_repository:
                # Get actual performance from repository
                perf_data = await self.signal_repository.get_signal_performance(
                    insight_id, review_period.days
                )
                return PerformanceMetrics(
                    return_pct=perf_data.get("return_pct", 0.0),
                    max_drawdown_pct=perf_data.get("max_drawdown_pct", 0.0),
                    sharpe_ratio=perf_data.get("sharpe_ratio", 0.0),
                    win=perf_data.get("win", False),
                )
            else:
                # Return mock performance
                return PerformanceMetrics(
                    return_pct=10.0 if review_period == ReviewPeriod.DAY_7 else 15.0,
                    max_drawdown_pct=-3.0,
                    sharpe_ratio=1.5,
                    win=True,
                )

        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            return PerformanceMetrics(
                return_pct=0.0,
                max_drawdown_pct=0.0,
                sharpe_ratio=0.0,
                win=False,
            )

    async def _generate_review_reasoning(
        self,
        insight_id: int,
        performance: PerformanceMetrics,
        original_prediction: str,
        actual_outcome: str,
    ) -> str:
        """Generate review reasoning using LLM"""
        try:
            system_prompt = """You are a trading performance analyst.
Provide concise insights on why an insight performed well or poorly."""

            user_prompt = f"""Review this insight performance:

Insight ID: {insight_id}
Original Prediction: {original_prediction if original_prediction else "Not provided"}
Actual Outcome: {actual_outcome if actual_outcome else "Not provided"}

Performance:
- Return: {performance.return_pct:.1f}%
- Max Drawdown: {performance.max_drawdown_pct:.1f}%
- Sharpe Ratio: {performance.sharpe_ratio:.2f}
- Win: {performance.win}

Provide a brief explanation (1-2 sentences) of the performance."""

            response = await self.llm.complete_with_system(system_prompt, user_prompt)
            return response.content

        except Exception as e:
            logger.error(f"Review reasoning generation error: {e}")
            return f"Performance: {performance.return_pct:.1f}% return"

    async def _analyze_failure_patterns(
        self,
        insight_id: int,
        performance: Dict[str, Any],
        reasoning: str,
    ) -> tuple[List[str], List[str]]:
        """Analyze failure patterns and generate improvements"""
        try:
            system_prompt = """You are a machine learning engineer specializing in prompt engineering.
Analyze failed predictions and suggest prompt improvements."""

            user_prompt = f"""Analyze this failed insight and suggest improvements:

Insight ID: {insight_id}
Performance: {performance.get('return_pct', 0):.1f}% return
Win: {performance.get('win', False)}
Original Reasoning: {reasoning if reasoning else "Not provided"}

Identify:
1. Failure patterns (what went wrong)
2. Concrete prompt improvements (how to fix)

Provide response as:
**Failure Patterns:**
- pattern 1
- pattern 2

**Prompt Improvements:**
- improvement 1
- improvement 2"""

            response = await self.llm.complete_with_system(system_prompt, user_prompt)

            # Parse response
            content = response.content
            failure_patterns = []
            improvements = []

            # Extract failure patterns
            if "Failure Patterns:" in content:
                pattern_section = content.split("Prompt Improvements:")[0]
                patterns = [line.strip("- ") for line in pattern_section.split("\n") if line.strip().startswith("-")]
                failure_patterns = patterns[:5]  # Limit to 5 patterns

            # Extract improvements
            if "Prompt Improvements:" in content:
                improvement_section = content.split("Prompt Improvements:")[1]
                improvements_list = [line.strip("- ") for line in improvement_section.split("\n") if line.strip().startswith("-")]
                improvements = improvements_list[:5]  # Limit to 5 improvements

            # Fallback if parsing failed
            if not failure_patterns:
                failure_patterns = ["Overestimated catalyst impact", "Insufficient risk consideration"]
            if not improvements:
                improvements = ["Add market regime check", "Include risk factors in analysis"]

            return failure_patterns, improvements

        except Exception as e:
            logger.error(f"Failure pattern analysis error: {e}")
            # Return fallback suggestions
            return (
                ["Analysis error occurred"],
                ["Add validation checks", "Improve risk assessment"],
            )

    def _calculate_improvement_confidence(self, performance: Dict[str, Any]) -> float:
        """Calculate confidence in improvement suggestions"""
        try:
            base_confidence = 0.7

            # Higher confidence for clear failures
            return_pct = performance.get("return_pct", 0.0)
            if return_pct < -5.0:
                base_confidence = min(1.0, base_confidence + 0.15)
            elif return_pct > 5.0:
                base_confidence = max(0.4, base_confidence - 0.2)

            return base_confidence

        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return 0.6

    def get_statistics(self) -> Dict[str, Any]:
        """Get post-mortem statistics"""
        return {
            "total_reviews": self._review_count,
            "day_7_reviews": self._period_counts["7_DAY"],
            "day_30_reviews": self._period_counts["30_DAY"],
            "total_improvements": self._improvement_count,
        }


# ============================================================================
# Factory function
# ============================================================================

def create_insight_postmortem(
    llm_provider: Optional[LLMProvider] = None,
    signal_repository: Optional[Any] = None,
) -> InsightPostMortem:
    """
    Create InsightPostMortem instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        signal_repository: Trading signal repository

    Returns:
        InsightPostMortem: Configured analyzer instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return InsightPostMortem(
        llm_provider=llm_provider,
        signal_repository=signal_repository,
    )
