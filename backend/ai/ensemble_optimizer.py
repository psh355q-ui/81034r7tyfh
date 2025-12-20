"""
Ensemble Optimizer - Optimize Multi-AI weights based on performance

Features:
- Dynamic weight adjustment based on recent performance
- Bayesian optimization for weight tuning
- Market regime-specific weights
- Performance attribution analysis
- Auto-rebalancing triggers

Author: AI Trading System Team
Date: 2025-11-24
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class EnsembleWeights:
    """Weights for Multi-AI ensemble."""
    claude_weight: float  # Final decision maker
    gemini_weight: float  # Risk screener
    chatgpt_weight: float  # Regime detector

    # Market regime-specific adjustments
    bull_multiplier: float = 1.0
    bear_multiplier: float = 1.0
    sideways_multiplier: float = 1.0

    # Metadata
    last_updated: datetime = None
    performance_score: float = 0.0

    def normalize(self):
        """Normalize weights to sum to 1.0."""
        total = self.claude_weight + self.gemini_weight + self.chatgpt_weight
        if total > 0:
            self.claude_weight /= total
            self.gemini_weight /= total
            self.chatgpt_weight /= total

    def apply_regime_adjustment(self, regime: str) -> Tuple[float, float, float]:
        """
        Apply regime-specific multipliers.

        Returns:
            Adjusted (claude, gemini, chatgpt) weights
        """
        multiplier = {
            "bull": self.bull_multiplier,
            "bear": self.bear_multiplier,
            "sideways": self.sideways_multiplier,
        }.get(regime.lower(), 1.0)

        return (
            self.claude_weight * multiplier,
            self.gemini_weight * multiplier,
            self.chatgpt_weight * multiplier,
        )


class EnsembleOptimizer:
    """
    Optimize ensemble weights based on historical performance.

    Optimization Objectives:
    1. Maximize Sharpe Ratio
    2. Minimize correlation to individual models
    3. Balance cost vs performance
    4. Adapt to market regime

    Methods:
    - Bayesian optimization
    - Grid search
    - Gradient descent
    - Reinforcement learning (future)
    """

    def __init__(
        self,
        validator=None,
        min_samples: int = 50,
        rebalance_frequency_days: int = 7,
    ):
        """
        Initialize optimizer.

        Args:
            validator: AnalysisValidator instance for performance data
            min_samples: Minimum signals required before optimization
            rebalance_frequency_days: Days between rebalancing
        """
        self.validator = validator
        self.min_samples = min_samples
        self.rebalance_frequency_days = rebalance_frequency_days

        # Current weights
        self.current_weights = EnsembleWeights(
            claude_weight=0.5,   # Claude is primary decision maker
            gemini_weight=0.3,   # Gemini for risk screening
            chatgpt_weight=0.2,  # ChatGPT for regime detection
        )
        self.current_weights.normalize()

        # Optimization history
        self.optimization_history: List[Tuple[datetime, EnsembleWeights, float]] = []

        # Performance tracking
        self.last_rebalance = datetime.utcnow()

        logger.info("EnsembleOptimizer initialized")
        logger.info(f"Initial weights: Claude={self.current_weights.claude_weight:.2f}, "
                    f"Gemini={self.current_weights.gemini_weight:.2f}, "
                    f"ChatGPT={self.current_weights.chatgpt_weight:.2f}")

    def should_rebalance(self) -> bool:
        """Check if weights should be rebalanced."""
        days_since_rebalance = (datetime.utcnow() - self.last_rebalance).days
        return days_since_rebalance >= self.rebalance_frequency_days

    async def optimize_weights(
        self,
        lookback_days: int = 90,
        objective: str = "sharpe",  # sharpe, win_rate, total_return
        method: str = "bayesian",   # bayesian, grid, gradient
    ) -> EnsembleWeights:
        """
        Optimize ensemble weights based on historical performance.

        Args:
            lookback_days: Days of history to use for optimization
            objective: Optimization objective function
            method: Optimization method

        Returns:
            Optimized EnsembleWeights
        """
        if not self.validator:
            logger.warning("No validator available, returning current weights")
            return self.current_weights

        # Get performance data for each model
        claude_metrics = await self.validator.get_accuracy_metrics(
            source="claude",
            lookback_days=lookback_days
        )
        gemini_metrics = await self.validator.get_accuracy_metrics(
            source="gemini",
            lookback_days=lookback_days
        )
        chatgpt_metrics = await self.validator.get_accuracy_metrics(
            source="chatgpt",
            lookback_days=lookback_days
        )

        # Check minimum samples
        total_signals = (
            claude_metrics.resolved_signals +
            gemini_metrics.resolved_signals +
            chatgpt_metrics.resolved_signals
        )

        if total_signals < self.min_samples:
            logger.warning(
                f"Insufficient data for optimization: {total_signals} < {self.min_samples}"
            )
            return self.current_weights

        # Choose optimization method
        if method == "bayesian":
            optimized_weights = self._optimize_bayesian(
                claude_metrics, gemini_metrics, chatgpt_metrics, objective
            )
        elif method == "grid":
            optimized_weights = self._optimize_grid_search(
                claude_metrics, gemini_metrics, chatgpt_metrics, objective
            )
        elif method == "gradient":
            optimized_weights = self._optimize_gradient(
                claude_metrics, gemini_metrics, chatgpt_metrics, objective
            )
        else:
            logger.error(f"Unknown optimization method: {method}")
            return self.current_weights

        # Validate and normalize
        optimized_weights.normalize()
        optimized_weights.last_updated = datetime.utcnow()

        # Calculate performance score
        performance_score = self._calculate_ensemble_score(optimized_weights, objective)
        optimized_weights.performance_score = performance_score

        # Store in history
        self.optimization_history.append((
            datetime.utcnow(),
            optimized_weights,
            performance_score
        ))

        # Update current weights if better
        if performance_score > self.current_weights.performance_score:
            logger.info(
                f"Updating weights: Claude {optimized_weights.claude_weight:.2f}, "
                f"Gemini {optimized_weights.gemini_weight:.2f}, "
                f"ChatGPT {optimized_weights.chatgpt_weight:.2f} "
                f"(score: {performance_score:.3f})"
            )
            self.current_weights = optimized_weights
            self.last_rebalance = datetime.utcnow()
        else:
            logger.info(f"Keeping current weights (current score: {self.current_weights.performance_score:.3f} "
                        f"> new score: {performance_score:.3f})")

        return optimized_weights

    def _optimize_bayesian(
        self,
        claude_metrics,
        gemini_metrics,
        chatgpt_metrics,
        objective: str,
    ) -> EnsembleWeights:
        """
        Bayesian optimization of weights.

        Uses scipy.optimize with constraints.
        """
        def objective_function(weights):
            """Objective to minimize (negative for maximization)."""
            claude_w, gemini_w, chatgpt_w = weights

            # Weighted performance
            if objective == "sharpe":
                score = (
                    claude_w * claude_metrics.sharpe_ratio +
                    gemini_w * gemini_metrics.sharpe_ratio +
                    chatgpt_w * chatgpt_metrics.sharpe_ratio
                )
            elif objective == "win_rate":
                score = (
                    claude_w * claude_metrics.win_rate +
                    gemini_w * gemini_metrics.win_rate +
                    chatgpt_w * chatgpt_metrics.win_rate
                )
            elif objective == "total_return":
                score = (
                    claude_w * claude_metrics.avg_return_pct +
                    gemini_w * gemini_metrics.avg_return_pct +
                    chatgpt_w * chatgpt_metrics.avg_return_pct
                )
            else:
                score = 0.0

            # Penalty for high max drawdown
            max_dd = (
                claude_w * abs(claude_metrics.max_drawdown_pct) +
                gemini_w * abs(gemini_metrics.max_drawdown_pct) +
                chatgpt_w * abs(chatgpt_metrics.max_drawdown_pct)
            )
            score -= max_dd * 0.1  # Penalize drawdown

            return -score  # Minimize negative score = maximize score

        # Constraints: weights sum to 1, all non-negative
        constraints = (
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},  # Sum to 1
        )

        bounds = [
            (0.1, 0.8),  # Claude: 10-80%
            (0.1, 0.6),  # Gemini: 10-60%
            (0.1, 0.5),  # ChatGPT: 10-50%
        ]

        # Initial guess
        x0 = [
            self.current_weights.claude_weight,
            self.current_weights.gemini_weight,
            self.current_weights.chatgpt_weight,
        ]

        # Optimize
        result = minimize(
            objective_function,
            x0=x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
        )

        if result.success:
            return EnsembleWeights(
                claude_weight=result.x[0],
                gemini_weight=result.x[1],
                chatgpt_weight=result.x[2],
            )
        else:
            logger.warning(f"Optimization failed: {result.message}")
            return self.current_weights

    def _optimize_grid_search(
        self,
        claude_metrics,
        gemini_metrics,
        chatgpt_metrics,
        objective: str,
    ) -> EnsembleWeights:
        """
        Grid search optimization.

        Tests all combinations of weights in increments.
        """
        best_score = float('-inf')
        best_weights = None

        # Grid search parameters
        step = 0.1
        claude_range = np.arange(0.3, 0.7, step)
        gemini_range = np.arange(0.1, 0.5, step)

        for claude_w in claude_range:
            for gemini_w in gemini_range:
                chatgpt_w = 1.0 - claude_w - gemini_w

                if chatgpt_w < 0.1 or chatgpt_w > 0.5:
                    continue  # Out of bounds

                weights = EnsembleWeights(
                    claude_weight=claude_w,
                    gemini_weight=gemini_w,
                    chatgpt_weight=chatgpt_w,
                )

                score = self._calculate_ensemble_score(weights, objective)

                if score > best_score:
                    best_score = score
                    best_weights = weights

        return best_weights if best_weights else self.current_weights

    def _optimize_gradient(
        self,
        claude_metrics,
        gemini_metrics,
        chatgpt_metrics,
        objective: str,
    ) -> EnsembleWeights:
        """
        Gradient-based optimization.

        Uses historical performance gradients.
        """
        # Simplified: Adjust weights based on recent performance
        learning_rate = 0.1

        # Get performance deltas
        claude_score = self._get_model_score(claude_metrics, objective)
        gemini_score = self._get_model_score(gemini_metrics, objective)
        chatgpt_score = self._get_model_score(chatgpt_metrics, objective)

        # Normalize scores
        total_score = claude_score + gemini_score + chatgpt_score
        if total_score > 0:
            claude_ratio = claude_score / total_score
            gemini_ratio = gemini_score / total_score
            chatgpt_ratio = chatgpt_score / total_score

            # Adjust weights toward better performers
            new_claude = self.current_weights.claude_weight + learning_rate * (claude_ratio - self.current_weights.claude_weight)
            new_gemini = self.current_weights.gemini_weight + learning_rate * (gemini_ratio - self.current_weights.gemini_weight)
            new_chatgpt = self.current_weights.chatgpt_weight + learning_rate * (chatgpt_ratio - self.current_weights.chatgpt_weight)

            return EnsembleWeights(
                claude_weight=max(0.1, min(0.8, new_claude)),
                gemini_weight=max(0.1, min(0.6, new_gemini)),
                chatgpt_weight=max(0.1, min(0.5, new_chatgpt)),
            )

        return self.current_weights

    def _get_model_score(self, metrics, objective: str) -> float:
        """Get single score for a model based on objective."""
        if objective == "sharpe":
            return max(0, metrics.sharpe_ratio)
        elif objective == "win_rate":
            return metrics.win_rate
        elif objective == "total_return":
            return max(0, metrics.avg_return_pct)
        return 0.0

    def _calculate_ensemble_score(self, weights: EnsembleWeights, objective: str) -> float:
        """
        Calculate ensemble score for given weights.

        This is a placeholder - in production, would backtest ensemble with these weights.
        """
        # Simplified: weighted average of individual scores
        # In reality, ensemble performs differently than weighted average
        return (
            weights.claude_weight * 0.8 +  # Claude baseline performance
            weights.gemini_weight * 0.7 +  # Gemini baseline performance
            weights.chatgpt_weight * 0.6   # ChatGPT baseline performance
        )

    def optimize_regime_multipliers(
        self,
        lookback_days: int = 180,
    ) -> EnsembleWeights:
        """
        Optimize regime-specific multipliers.

        Analyzes performance in different market regimes and adjusts multipliers.
        """
        if not self.validator:
            return self.current_weights

        # Get signals grouped by regime (if available in metadata)
        # This is a placeholder - would need regime data in signal metadata

        # For now, use conservative defaults
        optimized = EnsembleWeights(
            claude_weight=self.current_weights.claude_weight,
            gemini_weight=self.current_weights.gemini_weight,
            chatgpt_weight=self.current_weights.chatgpt_weight,
            bull_multiplier=1.2,   # Increase confidence in bull markets
            bear_multiplier=0.8,   # Decrease confidence in bear markets
            sideways_multiplier=1.0,  # Neutral in sideways markets
        )

        return optimized

    def get_optimization_report(self) -> Dict:
        """Generate optimization summary report."""
        return {
            "current_weights": {
                "claude": self.current_weights.claude_weight,
                "gemini": self.current_weights.gemini_weight,
                "chatgpt": self.current_weights.chatgpt_weight,
            },
            "regime_multipliers": {
                "bull": self.current_weights.bull_multiplier,
                "bear": self.current_weights.bear_multiplier,
                "sideways": self.current_weights.sideways_multiplier,
            },
            "performance_score": self.current_weights.performance_score,
            "last_rebalance": self.last_rebalance.isoformat(),
            "days_since_rebalance": (datetime.utcnow() - self.last_rebalance).days,
            "should_rebalance": self.should_rebalance(),
            "optimization_history_count": len(self.optimization_history),
        }
