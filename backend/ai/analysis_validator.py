"""
AI Analysis Validator - Measure and validate AI analysis quality

Features:
- Signal accuracy tracking (win rate, sharpe ratio)
- Confidence calibration (predicted vs actual)
- RAG relevance scoring
- Multi-AI agreement analysis
- Performance attribution
- Backtesting integration

Author: AI Trading System Team
Date: 2025-11-24
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class SignalOutcome(Enum):
    """Outcome of a trading signal."""
    WIN = "win"           # Signal was profitable
    LOSS = "loss"         # Signal was unprofitable
    NEUTRAL = "neutral"   # No significant move
    PENDING = "pending"   # Not yet resolved


@dataclass
class SignalRecord:
    """Record of a single AI-generated signal."""
    signal_id: str
    ticker: str
    timestamp: datetime
    signal: str  # BUY/SELL/HOLD
    confidence: float
    source: str  # claude/gemini/ensemble/rag

    # Prediction details
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    time_horizon_days: int = 5

    # Features used
    features_hash: Optional[str] = None
    rag_documents_used: int = 0
    rag_relevance_score: float = 0.0

    # Outcome (filled later)
    outcome: SignalOutcome = SignalOutcome.PENDING
    actual_return_pct: Optional[float] = None
    days_to_resolution: Optional[int] = None
    exit_price: Optional[float] = None

    # Metadata
    metadata: Dict = field(default_factory=dict)


@dataclass
class AccuracyMetrics:
    """Accuracy metrics for a set of signals."""
    total_signals: int
    resolved_signals: int
    win_count: int
    loss_count: int
    neutral_count: int

    win_rate: float
    avg_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float

    # Confidence calibration
    avg_confidence: float
    confidence_correlation: float  # Correlation between confidence and outcome

    # By signal type
    buy_accuracy: float
    sell_accuracy: float

    # Time-based
    avg_days_to_resolution: float


class AnalysisValidator:
    """
    Validates AI analysis quality and tracks performance.

    Usage:
        validator = AnalysisValidator(db_session)

        # Record signal
        await validator.record_signal(
            ticker="AAPL",
            signal="BUY",
            confidence=0.85,
            source="claude",
            target_price=195.00,
        )

        # Update outcomes (run daily)
        await validator.update_outcomes()

        # Get accuracy metrics
        metrics = await validator.get_accuracy_metrics(
            source="claude",
            lookback_days=30
        )
    """

    def __init__(self, db_session=None, price_fetcher=None):
        """
        Initialize validator.

        Args:
            db_session: Database session for persistence
            price_fetcher: Function to fetch historical prices
        """
        self.db_session = db_session
        self.price_fetcher = price_fetcher

        # In-memory storage (replace with DB in production)
        self.signals: List[SignalRecord] = []
        self.signal_index: Dict[str, SignalRecord] = {}

        # Performance cache
        self.metrics_cache: Dict[str, Tuple[datetime, AccuracyMetrics]] = {}
        self.cache_ttl_seconds = 3600  # 1 hour

        logger.info("AnalysisValidator initialized")

    async def record_signal(
        self,
        ticker: str,
        signal: str,
        confidence: float,
        source: str,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        time_horizon_days: int = 5,
        rag_documents_used: int = 0,
        rag_relevance_score: float = 0.0,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Record an AI-generated signal for later validation.

        Returns:
            signal_id: Unique identifier for the signal
        """
        signal_id = f"{ticker}_{source}_{datetime.utcnow().timestamp()}"

        record = SignalRecord(
            signal_id=signal_id,
            ticker=ticker,
            timestamp=datetime.utcnow(),
            signal=signal,
            confidence=confidence,
            source=source,
            target_price=target_price,
            stop_loss=stop_loss,
            time_horizon_days=time_horizon_days,
            rag_documents_used=rag_documents_used,
            rag_relevance_score=rag_relevance_score,
            metadata=metadata or {},
        )

        self.signals.append(record)
        self.signal_index[signal_id] = record

        logger.info(
            f"Recorded signal: {ticker} {signal} (conf={confidence:.2f}, source={source})"
        )

        return signal_id

    async def update_outcomes(self, current_prices: Optional[Dict[str, float]] = None):
        """
        Update outcomes for pending signals.

        Args:
            current_prices: Dict of ticker -> current price
                           If None, fetch from price_fetcher
        """
        if not current_prices and not self.price_fetcher:
            logger.warning("No prices available to update outcomes")
            return

        updated_count = 0

        for record in self.signals:
            if record.outcome != SignalOutcome.PENDING:
                continue  # Already resolved

            # Check if time horizon passed
            days_since_signal = (datetime.utcnow() - record.timestamp).days
            if days_since_signal < record.time_horizon_days:
                continue  # Not yet ready to resolve

            # Get current price
            if current_prices:
                current_price = current_prices.get(record.ticker)
            else:
                current_price = await self.price_fetcher(record.ticker)

            if not current_price:
                logger.warning(f"No price for {record.ticker}, skipping outcome update")
                continue

            # Calculate return
            # Note: Need entry price (assume it's in metadata or fetch historical)
            entry_price = record.metadata.get("entry_price")
            if not entry_price:
                logger.warning(f"No entry price for {record.signal_id}, skipping")
                continue

            return_pct = ((current_price - entry_price) / entry_price) * 100

            # Determine outcome
            if record.signal == "BUY":
                if return_pct >= 2.0:  # 2% gain threshold
                    outcome = SignalOutcome.WIN
                elif return_pct <= -1.0:  # 1% loss threshold
                    outcome = SignalOutcome.LOSS
                else:
                    outcome = SignalOutcome.NEUTRAL

            elif record.signal == "SELL":
                if return_pct <= -2.0:  # 2% drop threshold (profit for short)
                    outcome = SignalOutcome.WIN
                elif return_pct >= 1.0:  # 1% gain threshold (loss for short)
                    outcome = SignalOutcome.LOSS
                else:
                    outcome = SignalOutcome.NEUTRAL

            else:  # HOLD
                outcome = SignalOutcome.NEUTRAL

            # Update record
            record.outcome = outcome
            record.actual_return_pct = return_pct
            record.exit_price = current_price
            record.days_to_resolution = days_since_signal

            updated_count += 1
            logger.info(
                f"Resolved signal {record.signal_id}: {outcome.value} "
                f"(return={return_pct:.2f}%, days={days_since_signal})"
            )

        logger.info(f"Updated {updated_count} signal outcomes")

    async def get_accuracy_metrics(
        self,
        source: Optional[str] = None,
        ticker: Optional[str] = None,
        lookback_days: int = 30,
        min_confidence: Optional[float] = None,
    ) -> AccuracyMetrics:
        """
        Calculate accuracy metrics for signals.

        Args:
            source: Filter by AI source (claude/gemini/ensemble)
            ticker: Filter by ticker
            lookback_days: Only include signals from last N days
            min_confidence: Only include signals above confidence threshold

        Returns:
            AccuracyMetrics
        """
        # Check cache
        cache_key = f"{source}_{ticker}_{lookback_days}_{min_confidence}"
        if cache_key in self.metrics_cache:
            cached_time, cached_metrics = self.metrics_cache[cache_key]
            if (datetime.utcnow() - cached_time).total_seconds() < self.cache_ttl_seconds:
                return cached_metrics

        # Filter signals
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        filtered_signals = [
            s for s in self.signals
            if s.timestamp >= cutoff_date
            and (source is None or s.source == source)
            and (ticker is None or s.ticker == ticker)
            and (min_confidence is None or s.confidence >= min_confidence)
            and s.outcome != SignalOutcome.PENDING  # Only resolved signals
        ]

        if not filtered_signals:
            logger.warning(f"No signals found for {cache_key}")
            return AccuracyMetrics(
                total_signals=0,
                resolved_signals=0,
                win_count=0,
                loss_count=0,
                neutral_count=0,
                win_rate=0.0,
                avg_return_pct=0.0,
                sharpe_ratio=0.0,
                max_drawdown_pct=0.0,
                avg_confidence=0.0,
                confidence_correlation=0.0,
                buy_accuracy=0.0,
                sell_accuracy=0.0,
                avg_days_to_resolution=0.0,
            )

        # Calculate metrics
        total_signals = len(self.signals)
        resolved_signals = len(filtered_signals)

        win_count = sum(1 for s in filtered_signals if s.outcome == SignalOutcome.WIN)
        loss_count = sum(1 for s in filtered_signals if s.outcome == SignalOutcome.LOSS)
        neutral_count = sum(1 for s in filtered_signals if s.outcome == SignalOutcome.NEUTRAL)

        win_rate = win_count / resolved_signals if resolved_signals > 0 else 0.0

        # Returns
        returns = [s.actual_return_pct for s in filtered_signals if s.actual_return_pct is not None]
        avg_return_pct = np.mean(returns) if returns else 0.0

        # Sharpe ratio (assuming daily returns)
        if len(returns) > 1:
            sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        # Max drawdown
        cumulative_returns = np.cumsum(returns) if returns else []
        if len(cumulative_returns) > 0:
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = cumulative_returns - running_max
            max_drawdown_pct = np.min(drawdown) if len(drawdown) > 0 else 0.0
        else:
            max_drawdown_pct = 0.0

        # Confidence metrics
        avg_confidence = np.mean([s.confidence for s in filtered_signals])

        # Confidence calibration (correlation between confidence and returns)
        confidences = [s.confidence for s in filtered_signals]
        if len(returns) > 1 and len(confidences) == len(returns):
            confidence_correlation = np.corrcoef(confidences, returns)[0, 1]
        else:
            confidence_correlation = 0.0

        # By signal type
        buy_signals = [s for s in filtered_signals if s.signal == "BUY"]
        buy_accuracy = (
            sum(1 for s in buy_signals if s.outcome == SignalOutcome.WIN) / len(buy_signals)
            if buy_signals else 0.0
        )

        sell_signals = [s for s in filtered_signals if s.signal == "SELL"]
        sell_accuracy = (
            sum(1 for s in sell_signals if s.outcome == SignalOutcome.WIN) / len(sell_signals)
            if sell_signals else 0.0
        )

        # Time to resolution
        avg_days_to_resolution = np.mean([
            s.days_to_resolution for s in filtered_signals
            if s.days_to_resolution is not None
        ]) if filtered_signals else 0.0

        metrics = AccuracyMetrics(
            total_signals=total_signals,
            resolved_signals=resolved_signals,
            win_count=win_count,
            loss_count=loss_count,
            neutral_count=neutral_count,
            win_rate=win_rate,
            avg_return_pct=avg_return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=max_drawdown_pct,
            avg_confidence=avg_confidence,
            confidence_correlation=confidence_correlation,
            buy_accuracy=buy_accuracy,
            sell_accuracy=sell_accuracy,
            avg_days_to_resolution=avg_days_to_resolution,
        )

        # Cache result
        self.metrics_cache[cache_key] = (datetime.utcnow(), metrics)

        return metrics

    def get_confidence_calibration(
        self,
        source: Optional[str] = None,
        lookback_days: int = 90,
    ) -> Dict[str, List[float]]:
        """
        Analyze confidence calibration.

        Returns:
            Dict with confidence buckets and actual win rates
            {
                "confidence_buckets": [0.5, 0.6, 0.7, 0.8, 0.9],
                "actual_win_rates": [0.45, 0.58, 0.72, 0.81, 0.88]
            }
        """
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        filtered_signals = [
            s for s in self.signals
            if s.timestamp >= cutoff_date
            and (source is None or s.source == source)
            and s.outcome != SignalOutcome.PENDING
        ]

        if not filtered_signals:
            return {"confidence_buckets": [], "actual_win_rates": []}

        # Create confidence buckets
        buckets = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        bucket_win_rates = []

        for i in range(len(buckets) - 1):
            lower = buckets[i]
            upper = buckets[i + 1]

            bucket_signals = [
                s for s in filtered_signals
                if lower <= s.confidence < upper
            ]

            if bucket_signals:
                win_rate = sum(
                    1 for s in bucket_signals if s.outcome == SignalOutcome.WIN
                ) / len(bucket_signals)
                bucket_win_rates.append(win_rate)
            else:
                bucket_win_rates.append(0.0)

        return {
            "confidence_buckets": buckets[:-1],
            "actual_win_rates": bucket_win_rates,
        }

    def get_rag_impact_analysis(self, lookback_days: int = 90) -> Dict[str, float]:
        """
        Analyze impact of RAG on signal quality.

        Returns:
            {
                "with_rag_win_rate": 0.72,
                "without_rag_win_rate": 0.64,
                "rag_improvement": 0.08,
                "avg_rag_relevance": 0.85
            }
        """
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        filtered_signals = [
            s for s in self.signals
            if s.timestamp >= cutoff_date
            and s.outcome != SignalOutcome.PENDING
        ]

        with_rag = [s for s in filtered_signals if s.rag_documents_used > 0]
        without_rag = [s for s in filtered_signals if s.rag_documents_used == 0]

        with_rag_win_rate = (
            sum(1 for s in with_rag if s.outcome == SignalOutcome.WIN) / len(with_rag)
            if with_rag else 0.0
        )

        without_rag_win_rate = (
            sum(1 for s in without_rag if s.outcome == SignalOutcome.WIN) / len(without_rag)
            if without_rag else 0.0
        )

        avg_rag_relevance = (
            np.mean([s.rag_relevance_score for s in with_rag])
            if with_rag else 0.0
        )

        return {
            "with_rag_win_rate": with_rag_win_rate,
            "without_rag_win_rate": without_rag_win_rate,
            "rag_improvement": with_rag_win_rate - without_rag_win_rate,
            "avg_rag_relevance": avg_rag_relevance,
            "signals_with_rag": len(with_rag),
            "signals_without_rag": len(without_rag),
        }

    def get_source_comparison(self, lookback_days: int = 90) -> Dict[str, AccuracyMetrics]:
        """
        Compare performance across AI sources.

        Returns:
            {
                "claude": AccuracyMetrics(...),
                "gemini": AccuracyMetrics(...),
                "ensemble": AccuracyMetrics(...)
            }
        """
        sources = set(s.source for s in self.signals)

        comparison = {}
        for source in sources:
            metrics = asyncio.run(self.get_accuracy_metrics(
                source=source,
                lookback_days=lookback_days
            ))
            comparison[source] = metrics

        return comparison

    def get_summary_report(self, lookback_days: int = 30) -> Dict:
        """
        Generate comprehensive summary report.
        """
        overall_metrics = asyncio.run(self.get_accuracy_metrics(lookback_days=lookback_days))
        source_comparison = self.get_source_comparison(lookback_days=lookback_days)
        rag_impact = self.get_rag_impact_analysis(lookback_days=lookback_days)
        confidence_calibration = self.get_confidence_calibration(lookback_days=lookback_days)

        return {
            "period": f"Last {lookback_days} days",
            "generated_at": datetime.utcnow().isoformat(),
            "overall_metrics": overall_metrics,
            "by_source": source_comparison,
            "rag_impact": rag_impact,
            "confidence_calibration": confidence_calibration,
        }
