"""
MarketConfirmation Component - Price Action Validation

Market Intelligence v2.0 - Phase 1, T1.4

This component validates narratives against actual market price action to filter
out noise and confirm that narratives are reflected in real trading.

Key Features:
1. Price correlation calculation between sentiment and price action
2. Sector relative performance analysis
3. Multi-symbol confirmation aggregation
4. Volume confirmation for breakouts
5. Confidence adjustment based on market confirmation

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

class ConfirmationStatus(Enum):
    """Market confirmation status"""
    CONFIRMED = "CONFIRMED"  # Price action supports narrative
    STRONG_CONFIRMATION = "STRONG_CONFIRMATION"  # Strong confirmation
    CONTRADICTED = "CONTRADICTED"  # Price action opposes narrative
    NEUTRAL = "NEUTRAL"  # Inconclusive price action
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"  # Not enough data
    ERROR = "ERROR"  # Error in confirmation


class ConfirmationSignal(Enum):
    """Confirmation signal strength"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class SymbolConfirmation:
    """
    Confirmation data for a single symbol

    Attributes:
        symbol: Stock symbol
        price_change: Price change percentage
        volume_change: Volume change percentage
        correlation: Correlation with sentiment (-1 to 1)
        confirmed: Whether price action confirms narrative
        signal: Trading signal
    """
    symbol: str
    price_change: float
    volume_change: float
    correlation: float
    confirmed: bool
    signal: ConfirmationSignal
    reasoning: str = ""


@dataclass
class MarketConfirmationResult:
    """
    Result of market confirmation analysis

    Attributes:
        status: Overall confirmation status
        price_correlation: Average price correlation
        sector_relative_return: Sector performance vs market
        volume_confirmation: Volume-based confirmation
        aggregate_confirmation: Aggregate confirmation score (0-1)
        symbol_confirmations: Per-symbol confirmation data
        adjusted_confidence: Confidence after market confirmation
    """
    status: ConfirmationStatus
    price_correlation: float
    sector_relative_return: Optional[float]
    volume_confirmation: float
    aggregate_confirmation: float
    symbol_confirmations: List[SymbolConfirmation]
    adjusted_confidence: float
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "status": self.status.value,
            "price_correlation": self.price_correlation,
            "sector_relative_return": self.sector_relative_return,
            "volume_confirmation": self.volume_confirmation,
            "aggregate_confirmation": self.aggregate_confirmation,
            "symbol_confirmations": [sc.to_dict() if hasattr(sc, 'to_dict') else {
                "symbol": sc.symbol,
                "price_change": sc.price_change,
                "volume_change": sc.volume_change,
                "correlation": sc.correlation,
                "confirmed": sc.confirmed,
                "signal": sc.signal.value,
                "reasoning": sc.reasoning,
            } for sc in self.symbol_confirmations],
            "adjusted_confidence": self.adjusted_confidence,
            "reasoning": self.reasoning,
        }


# ============================================================================
# Main Component
# ============================================================================

class MarketConfirmation(BaseIntelligence):
    """
    Market Confirmation

    Validates narratives against actual market price action to filter out noise.

    Key Features:
    1. Calculates correlation between narrative sentiment and price action
    2. Analyzes sector relative performance
    3. Aggregates confirmation across multiple symbols
    4. Adjusts confidence based on market confirmation

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.market_confirmation import MarketConfirmation

        llm = get_llm_provider()
        confirmer = MarketConfirmation(
            llm_provider=llm,
            market_data_client=market_data_client,
        )

        # Confirm narrative against market data
        result = await confirmer.confirm_narrative({
            "topic": "AI Semiconductor Boom",
            "sentiment": "BULLISH",
            "symbols": ["NVDA", "AMD"],
            "confidence": 0.85,
        })

        if result.data["confirmation_status"] == "CONFIRMED":
            print("Narrative confirmed by market!")
    """

    # Confirmation thresholds
    CORRELATION_THRESHOLD = 0.3  # Minimum correlation for confirmation
    STRONG_CORRELATION_THRESHOLD = 0.7  # Threshold for strong confirmation
    CONTRADICTION_THRESHOLD = -0.3  # Threshold for contradiction

    # Volume confirmation thresholds
    VOLUME_SPIKE_THRESHOLD = 1.5  # 50% above average = volume spike

    def __init__(
        self,
        llm_provider: LLMProvider,
        market_data_client: Optional[Any] = None,
    ):
        """
        Initialize MarketConfirmation

        Args:
            llm_provider: LLM Provider instance
            market_data_client: Market data API client (YFinance, etc.)
        """
        super().__init__(
            name="MarketConfirmation",
            phase=IntelligencePhase.P0,
        )

        self.llm = llm_provider
        self.market_data_client = market_data_client

        # Statistics
        self._confirmation_count = 0
        self._contradiction_count = 0

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Analyze and confirm narrative (main entry point)

        Args:
            data: Narrative data with sentiment and symbols

        Returns:
            IntelligenceResult: Confirmation result
        """
        return await self.confirm_narrative(data)

    async def confirm_narrative(
        self,
        narrative_data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Confirm narrative against market price action

        Args:
            narrative_data: Narrative data with:
                - topic: Narrative topic
                - sentiment: BULLISH/BEARISH/NEUTRAL
                - symbols: Related stock symbols
                - sector: (optional) Sector name
                - confidence: Original confidence

        Returns:
            IntelligenceResult: Confirmation result with adjusted confidence
        """
        try:
            sentiment = narrative_data.get("sentiment", "NEUTRAL")
            symbols = narrative_data.get("symbols", [])
            sector = narrative_data.get("sector")
            original_confidence = narrative_data.get("confidence", 0.7)

            # Check for insufficient data
            if not symbols and not sector:
                return self.create_result(
                    success=True,
                    data={
                        "stage": "market_confirmation",
                        "confirmation_status": "INSUFFICIENT_DATA",
                        "reason": "No symbols or sector provided",
                        "adjusted_confidence": original_confidence * 0.8,
                    },
                    confidence=original_confidence * 0.8,
                    reasoning="Insufficient data for market confirmation",
                )

            # Get symbol confirmations
            symbol_confirmations = []
            if symbols:
                for symbol in symbols:
                    confirmation = await self._confirm_symbol(symbol, sentiment)
                    symbol_confirmations.append(confirmation)

            # Get sector relative performance
            sector_relative_return = None
            if sector and self.market_data_client:
                try:
                    sector_data = await self.market_data_client.get_sector_performance(sector)
                    if sector_data:
                        sector_relative_return = sector_data["return"] - sector_data["spy_return"]
                except Exception as e:
                    logger.warning(f"Failed to get sector performance: {e}")

            # Calculate aggregate confirmation
            confirmation_result = self._calculate_aggregate_confirmation(
                sentiment,
                symbol_confirmations,
                sector_relative_return,
            )

            # Adjust confidence based on confirmation
            adjusted_confidence = self._adjust_confidence(
                original_confidence,
                confirmation_result,
            )

            # Update statistics
            self._confirmation_count += 1
            if confirmation_result.status == ConfirmationStatus.CONTRADICTED:
                self._contradiction_count += 1

            return self.create_result(
                success=True,
                data={
                    "stage": "market_confirmation",
                    "confirmation_status": confirmation_result.status.value,
                    "price_correlation": confirmation_result.price_correlation,
                    "sector_relative_return": sector_relative_return,
                    "volume_confirmation": confirmation_result.volume_confirmation,
                    "aggregate_confirmation": confirmation_result.aggregate_confirmation,
                    "symbol_confirmations": [sc.to_dict() if hasattr(sc, 'to_dict') else {
                        "symbol": sc.symbol,
                        "price_change": sc.price_change,
                        "volume_change": sc.volume_change,
                        "correlation": sc.correlation,
                        "confirmed": sc.confirmed,
                        "signal": sc.signal.value,
                        "reasoning": sc.reasoning,
                    } for sc in symbol_confirmations],
                    "adjusted_confidence": adjusted_confidence,
                },
                confidence=adjusted_confidence,
                reasoning=confirmation_result.reasoning,
            )

        except Exception as e:
            logger.error(f"Market confirmation error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "market_confirmation"},
            )
            result.add_error(f"Confirmation error: {str(e)}")
            return result

    async def _confirm_symbol(
        self,
        symbol: str,
        sentiment: str,
    ) -> SymbolConfirmation:
        """
        Confirm narrative for a single symbol

        Args:
            symbol: Stock symbol
            sentiment: Narrative sentiment

        Returns:
            SymbolConfirmation: Confirmation data for the symbol
        """
        try:
            if self.market_data_client is None:
                return SymbolConfirmation(
                    symbol=symbol,
                    price_change=0.0,
                    volume_change=0.0,
                    correlation=0.0,
                    confirmed=False,
                    signal=ConfirmationSignal.HOLD,
                    reasoning="No market data client",
                )

            # Get price history
            price_data = await self.market_data_client.get_price_history(symbol, "1mo")
            if price_data is None:
                return SymbolConfirmation(
                    symbol=symbol,
                    price_change=0.0,
                    volume_change=0.0,
                    correlation=0.0,
                    confirmed=False,
                    signal=ConfirmationSignal.HOLD,
                    reasoning="No price data available",
                )

            # Extract metrics
            price_change = price_data.get("change_percent", 0.0)

            # Calculate correlation with sentiment
            correlation = self._calculate_price_correlation(sentiment, price_change)

            # Determine confirmation
            confirmed = correlation >= self.CORRELATION_THRESHOLD

            # Determine signal
            signal = self._determine_signal(sentiment, price_change, correlation)

            # Volume confirmation (simplified)
            volume_confirmation = 1.0  # Placeholder

            reasoning = f"{symbol}: {price_change:+.1f}% vs {sentiment} sentiment (correlation: {correlation:.2f})"

            return SymbolConfirmation(
                symbol=symbol,
                price_change=price_change,
                volume_change=volume_confirmation,
                correlation=correlation,
                confirmed=confirmed,
                signal=signal,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Symbol confirmation error for {symbol}: {e}")
            return SymbolConfirmation(
                symbol=symbol,
                price_change=0.0,
                volume_change=0.0,
                correlation=0.0,
                confirmed=False,
                signal=ConfirmationSignal.HOLD,
                reasoning=f"Error: {str(e)}",
            )

    def _calculate_price_correlation(
        self,
        sentiment: str,
        price_change: float,
    ) -> float:
        """
        Calculate correlation between sentiment and price action

        Args:
            sentiment: BULLISH/BEARISH/NEUTRAL
            price_change: Price change percentage

        Returns:
            float: Correlation score (-1 to 1)
        """
        if sentiment == "BULLISH":
            # Positive price change = positive correlation
            if price_change > 0:
                # Normalize: 5% change = 1.0 correlation
                return min(1.0, price_change / 5.0)
            else:
                # Negative price change = negative correlation
                return max(-1.0, price_change / 5.0)

        elif sentiment == "BEARISH":
            # Negative price change = positive correlation
            if price_change < 0:
                # Normalize: -5% change = 1.0 correlation
                return min(1.0, abs(price_change) / 5.0)
            else:
                # Positive price change = negative correlation
                return max(-1.0, -price_change / 5.0)

        else:  # NEUTRAL
            # Small changes are neutral
            return max(-0.5, min(0.5, -price_change / 10.0))

    def _determine_signal(
        self,
        sentiment: str,
        price_change: float,
        correlation: float,
    ) -> ConfirmationSignal:
        """
        Determine trading signal based on sentiment, price, and correlation

        Args:
            sentiment: Narrative sentiment
            price_change: Price change percentage
            correlation: Price correlation

        Returns:
            ConfirmationSignal: Trading signal
        """
        if correlation >= self.STRONG_CORRELATION_THRESHOLD:
            if sentiment == "BULLISH" or price_change > 5:
                return ConfirmationSignal.STRONG_BUY
            elif sentiment == "BEARISH" or price_change < -5:
                return ConfirmationSignal.STRONG_SELL
        elif correlation >= self.CORRELATION_THRESHOLD:
            if sentiment == "BULLISH" or price_change > 2:
                return ConfirmationSignal.BUY
            elif sentiment == "BEARISH" or price_change < -2:
                return ConfirmationSignal.SELL

        return ConfirmationSignal.HOLD

    def _calculate_aggregate_confirmation(
        self,
        sentiment: str,
        symbol_confirmations: List[SymbolConfirmation],
        sector_relative_return: Optional[float],
    ) -> MarketConfirmationResult:
        """
        Calculate aggregate confirmation across all symbols

        Args:
            sentiment: Narrative sentiment
            symbol_confirmations: Per-symbol confirmations
            sector_relative_return: Sector relative performance

        Returns:
            MarketConfirmationResult: Aggregate confirmation result
        """
        if not symbol_confirmations:
            return MarketConfirmationResult(
                status=ConfirmationStatus.INSUFFICIENT_DATA,
                price_correlation=0.0,
                sector_relative_return=sector_relative_return,
                volume_confirmation=0.0,
                aggregate_confirmation=0.0,
                symbol_confirmations=[],
                adjusted_confidence=0.5,
                reasoning="No symbol confirmations available",
            )

        # Calculate average correlation
        avg_correlation = sum(sc.correlation for sc in symbol_confirmations) / len(symbol_confirmations)

        # Calculate confirmation score
        confirmed_count = sum(1 for sc in symbol_confirmations if sc.confirmed)
        confirmation_score = confirmed_count / len(symbol_confirmations)

        # Determine status
        if avg_correlation >= self.STRONG_CORRELATION_THRESHOLD:
            status = ConfirmationStatus.STRONG_CONFIRMATION
            reasoning = f"Strong confirmation: {confirmed_count}/{len(symbol_confirmations)} symbols confirmed"
        elif avg_correlation >= self.CORRELATION_THRESHOLD:
            status = ConfirmationStatus.CONFIRMED
            reasoning = f"Confirmed: {confirmed_count}/{len(symbol_confirmations)} symbols confirmed"
        elif avg_correlation <= self.CONTRADICTION_THRESHOLD:
            status = ConfirmationStatus.CONTRADICTED
            reasoning = f"Contradicted: Price action opposes narrative"
        elif abs(avg_correlation) < 0.2:
            status = ConfirmationStatus.NEUTRAL
            reasoning = f"Neutral: Inconclusive price action"
        else:
            status = ConfirmationStatus.NEUTRAL
            reasoning = f"Mixed signals: Some confirmation, some contradiction"

        # Volume confirmation (placeholder)
        volume_confirmation = 1.0

        return MarketConfirmationResult(
            status=status,
            price_correlation=avg_correlation,
            sector_relative_return=sector_relative_return,
            volume_confirmation=volume_confirmation,
            aggregate_confirmation=confirmation_score,
            symbol_confirmations=symbol_confirmations,
            adjusted_confidence=0.0,  # Will be set by caller
            reasoning=reasoning,
        )

    def _adjust_confidence(
        self,
        original_confidence: float,
        confirmation_result: MarketConfirmationResult,
    ) -> float:
        """
        Adjust confidence based on market confirmation

        Args:
            original_confidence: Original confidence from narrative
            confirmation_result: Market confirmation result

        Returns:
            float: Adjusted confidence
        """
        status = confirmation_result.status
        correlation = confirmation_result.price_correlation
        aggregate = confirmation_result.aggregate_confirmation

        if status == ConfirmationStatus.STRONG_CONFIRMATION:
            # Strong boost for strong confirmation
            adjustment = 0.15
        elif status == ConfirmationStatus.CONFIRMED:
            # Moderate boost for confirmation
            adjustment = 0.1 * aggregate
        elif status == ConfirmationStatus.CONTRADICTED:
            # Significant penalty for contradiction
            adjustment = -0.2 * abs(correlation)
        elif status == ConfirmationStatus.NEUTRAL:
            # Small penalty for neutral/inconclusive
            adjustment = -0.05
        else:  # INSUFFICIENT_DATA or ERROR
            # Moderate penalty for lack of data
            adjustment = -0.1

        adjusted = original_confidence + adjustment

        # Clamp to [0, 1]
        return max(0.0, min(1.0, adjusted))

    def get_statistics(self) -> Dict[str, Any]:
        """Get confirmation statistics"""
        contradiction_rate = (
            self._contradiction_count / self._confirmation_count
            if self._confirmation_count > 0
            else 0
        )

        return {
            "total_confirmations": self._confirmation_count,
            "contradictions": self._contradiction_count,
            "contradiction_rate": round(contradiction_rate, 3),
        }


# ============================================================================
# Factory function
# ============================================================================

def create_market_confirmation(
    llm_provider: Optional[LLMProvider] = None,
    market_data_client: Optional[Any] = None,
) -> MarketConfirmation:
    """
    Create MarketConfirmation instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        market_data_client: Market data API client (optional)

    Returns:
        MarketConfirmation: Configured confirmer instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return MarketConfirmation(
        llm_provider=llm_provider,
        market_data_client=market_data_client,
    )
