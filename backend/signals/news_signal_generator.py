"""
News-Based Trading Signal Generator

Features:
- Convert news sentiment to trading signals
- Position sizing based on impact and risk
- Confidence calculation
- Ticker extraction and validation
- Integration with sector throttling

Author: AI Trading System
Date: 2025-11-15
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class SignalAction(Enum):
    """Trading signal actions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradingSignal:
    """Trading signal generated from news analysis"""
    ticker: str
    action: SignalAction
    position_size: float  # 0.0 ~ 1.0 (percentage of portfolio)
    confidence: float     # 0.0 ~ 1.0
    execution_type: str   # "MARKET" | "LIMIT"
    reason: str
    urgency: str
    created_at: datetime
    source_article_id: Optional[int] = None
    news_title: Optional[str] = None
    affected_sectors: Optional[List[str]] = None
    auto_execute: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = asdict(self)
        d["action"] = self.action.value
        d["created_at"] = self.created_at.isoformat()
        return d


class NewsSignalGenerator:
    """
    Converts news analysis results into trading signals.
    
    Signal generation logic:
    1. Sentiment determines action (BUY/SELL/HOLD)
    2. Impact magnitude determines position size
    3. Risk category adjusts position size
    4. Confidence is calculated from sentiment confidence + impact
    5. Urgency determines execution type (MARKET/LIMIT)
    """
    
    def __init__(
        self,
        base_position_size: float = 0.05,  # 5% of portfolio
        max_position_size: float = 0.10,   # 10% max
        min_confidence_threshold: float = 0.6,
        sentiment_threshold: float = 0.3,
        impact_threshold: float = 0.5,
        enable_auto_execute: bool = False,
    ):
        """
        Initialize signal generator.
        
        Args:
            base_position_size: Base position size as fraction of portfolio
            max_position_size: Maximum position size
            min_confidence_threshold: Minimum confidence to generate signal
            sentiment_threshold: Minimum sentiment score magnitude to act
            impact_threshold: Minimum impact to consider
            enable_auto_execute: Enable automatic execution (dangerous!)
        """
        self.base_position_size = base_position_size
        self.max_position_size = max_position_size
        self.min_confidence_threshold = min_confidence_threshold
        self.sentiment_threshold = sentiment_threshold
        self.impact_threshold = impact_threshold
        self.enable_auto_execute = enable_auto_execute
        
        # Statistics
        self.stats = {
            "total_analyses": 0,
            "signals_generated": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "filtered_low_impact": 0,
            "filtered_low_confidence": 0,
            "filtered_no_ticker": 0,
        }
        
        logger.info(
            f"NewsSignalGenerator initialized: "
            f"base_size={base_position_size:.1%}, max_size={max_position_size:.1%}, "
            f"min_confidence={min_confidence_threshold}"
        )
    
    def generate_signal(
        self,
        analysis: Dict[str, Any],
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal from news analysis.
        
        Args:
            analysis: NewsAnalysis data dictionary containing:
                - sentiment_overall: POSITIVE/NEGATIVE/NEUTRAL
                - sentiment_score: -1.0 to 1.0
                - sentiment_confidence: 0.0 to 1.0
                - impact_magnitude: 0.0 to 1.0
                - urgency: IMMEDIATE/HIGH/MEDIUM/LOW
                - risk_category: LOW/MEDIUM/HIGH/CRITICAL
                - trading_actionable: bool
                - related_tickers: List of ticker info
                - affected_sectors: List of sectors
                - title: News title
                - article_id: Article ID (optional)
                
        Returns:
            TradingSignal if signal should be generated, None otherwise
        """
        self.stats["total_analyses"] += 1
        
        # 0. Check if actionable
        if not analysis.get("trading_actionable", False):
            logger.debug("News not marked as trading actionable")
            return None
        
        # 1. Check impact threshold
        impact = analysis.get("impact_magnitude", 0)
        if impact < self.impact_threshold:
            self.stats["filtered_low_impact"] += 1
            logger.debug(f"Impact too low: {impact:.2f} < {self.impact_threshold}")
            return None
        
        # 2. Determine action based on sentiment
        action = self._determine_action(analysis)
        if action == SignalAction.HOLD:
            logger.debug("Sentiment indicates HOLD, no signal generated")
            return None
        
        # 3. Extract primary ticker
        ticker = self._extract_primary_ticker(analysis)
        if not ticker:
            self.stats["filtered_no_ticker"] += 1
            logger.debug("No suitable ticker found in analysis")
            return None
        
        # 4. Calculate position size
        position_size = self._calculate_position_size(analysis)
        
        # 5. Calculate confidence
        confidence = self._calculate_confidence(analysis)
        
        # 6. Check minimum confidence
        if confidence < self.min_confidence_threshold:
            self.stats["filtered_low_confidence"] += 1
            logger.debug(f"Confidence too low: {confidence:.2f} < {self.min_confidence_threshold}")
            return None
        
        # 7. Determine execution type
        urgency = analysis.get("urgency", "MEDIUM")
        execution_type = "MARKET" if urgency in ["IMMEDIATE", "HIGH"] else "LIMIT"
        
        # 8. Build reason
        reason = self._build_reason(analysis, action)
        
        # 9. Create signal
        signal = TradingSignal(
            ticker=ticker,
            action=action,
            position_size=position_size,
            confidence=confidence,
            execution_type=execution_type,
            reason=reason,
            urgency=urgency,
            created_at=datetime.now(),
            source_article_id=analysis.get("article_id"),
            news_title=analysis.get("title", "")[:100],
            affected_sectors=analysis.get("affected_sectors", []),
            auto_execute=self.enable_auto_execute and confidence >= 0.85,
        )
        
        # Update statistics
        self.stats["signals_generated"] += 1
        if action == SignalAction.BUY:
            self.stats["buy_signals"] += 1
        elif action == SignalAction.SELL:
            self.stats["sell_signals"] += 1
        
        logger.info(
            f"Signal generated: {action.value} {ticker} @ {position_size:.1%} "
            f"(confidence={confidence:.2f}, urgency={urgency})"
        )
        
        return signal
    
    def _determine_action(self, analysis: Dict[str, Any]) -> SignalAction:
        """
        Determine trading action based on sentiment.
        
        Logic:
        - Strong negative sentiment (< -threshold) → SELL
        - Strong positive sentiment (> threshold) → BUY
        - Neutral sentiment → HOLD
        """
        sentiment = analysis.get("sentiment_overall", "NEUTRAL")
        sentiment_score = analysis.get("sentiment_score", 0)
        
        # Check by sentiment label first
        if sentiment == "NEGATIVE":
            if sentiment_score <= -self.sentiment_threshold:
                return SignalAction.SELL
            else:
                return SignalAction.HOLD
        
        elif sentiment == "POSITIVE":
            if sentiment_score >= self.sentiment_threshold:
                return SignalAction.BUY
            else:
                return SignalAction.HOLD
        
        else:  # NEUTRAL
            # Could have slight positive or negative score
            if sentiment_score <= -self.sentiment_threshold:
                return SignalAction.SELL
            elif sentiment_score >= self.sentiment_threshold:
                return SignalAction.BUY
            else:
                return SignalAction.HOLD
    
    def _calculate_position_size(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate position size based on impact and risk.
        
        Logic:
        - Start with base position size
        - Scale by impact magnitude
        - Reduce for higher risk categories
        - Cap at maximum position size
        """
        base_size = self.base_position_size
        
        # Scale by impact (0.5 to 1.5x)
        impact = analysis.get("impact_magnitude", 0.5)
        impact_multiplier = 0.5 + impact  # 0.5 to 1.5
        
        size = base_size * impact_multiplier
        
        # Adjust for risk category
        risk = analysis.get("risk_category", "MEDIUM")
        risk_multipliers = {
            "LOW": 1.0,      # Full size
            "MEDIUM": 0.75,  # 75% size
            "HIGH": 0.5,     # 50% size
            "CRITICAL": 0.25, # 25% size
        }
        size *= risk_multipliers.get(risk, 0.75)
        
        # Adjust for urgency (higher urgency = smaller size for safety)
        urgency = analysis.get("urgency", "MEDIUM")
        if urgency == "IMMEDIATE":
            size *= 0.8  # Reduce 20% for immediate actions
        
        # Cap at maximum
        size = min(size, self.max_position_size)
        
        # Round to 3 decimal places
        return round(size, 3)
    
    def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate signal confidence.
        
        Components:
        - Sentiment confidence (40%)
        - Impact magnitude (30%)
        - Risk inverse (20%)
        - Urgency clarity (10%)
        """
        # Sentiment confidence (0-1)
        sent_conf = analysis.get("sentiment_confidence", 0.5)
        
        # Impact magnitude (0-1)
        impact = analysis.get("impact_magnitude", 0.5)
        
        # Risk inverse (higher risk = lower confidence)
        risk = analysis.get("risk_category", "MEDIUM")
        risk_scores = {
            "LOW": 1.0,
            "MEDIUM": 0.7,
            "HIGH": 0.4,
            "CRITICAL": 0.2,
        }
        risk_conf = risk_scores.get(risk, 0.7)
        
        # Urgency clarity (clear urgency = higher confidence)
        urgency = analysis.get("urgency", "MEDIUM")
        urgency_scores = {
            "IMMEDIATE": 0.9,
            "HIGH": 0.8,
            "MEDIUM": 0.6,
            "LOW": 0.4,
        }
        urgency_conf = urgency_scores.get(urgency, 0.6)
        
        # Weighted average
        confidence = (
            sent_conf * 0.4 +
            impact * 0.3 +
            risk_conf * 0.2 +
            urgency_conf * 0.1
        )
        
        return round(confidence, 3)
    
    def _extract_primary_ticker(self, analysis: Dict[str, Any]) -> Optional[str]:
        """
        Extract the most relevant ticker from analysis.
        
        Returns:
            Ticker symbol if found with high enough relevance, None otherwise
        """
        related_tickers = analysis.get("related_tickers", [])
        
        if not related_tickers:
            return None
        
        # Handle different formats
        if isinstance(related_tickers[0], dict):
            # Format: [{"ticker_symbol": "AAPL", "relevance_score": 90, ...}]
            sorted_tickers = sorted(
                related_tickers,
                key=lambda x: x.get("relevance_score", 0),
                reverse=True,
            )
            
            # Minimum relevance threshold
            if sorted_tickers and sorted_tickers[0].get("relevance_score", 0) >= 70:
                return sorted_tickers[0].get("ticker_symbol", "")
        
        elif isinstance(related_tickers[0], str):
            # Format: ["AAPL", "MSFT", ...]
            # Just take the first one (assumes ordered by relevance)
            return related_tickers[0]
        
        return None
    
    def _build_reason(
        self,
        analysis: Dict[str, Any],
        action: SignalAction,
    ) -> str:
        """Build human-readable reason for the signal"""
        
        sentiment = analysis.get("sentiment_overall", "NEUTRAL")
        sentiment_score = analysis.get("sentiment_score", 0)
        impact = analysis.get("impact_magnitude", 0)
        
        # Base reason
        if action == SignalAction.BUY:
            base = f"Positive news sentiment ({sentiment_score:+.2f})"
        elif action == SignalAction.SELL:
            base = f"Negative news sentiment ({sentiment_score:+.2f})"
        else:
            base = "Neutral sentiment"
        
        # Add impact
        impact_desc = "high" if impact >= 0.7 else "moderate" if impact >= 0.5 else "low"
        reason = f"{base} with {impact_desc} market impact ({impact:.0%})"
        
        # Add key facts if available
        key_facts = analysis.get("key_facts", [])
        if key_facts:
            reason += f". Key: {key_facts[0][:100]}"
        
        # Add warnings if any
        warnings = analysis.get("key_warnings", [])
        if warnings:
            reason += f". Warning: {warnings[0][:50]}"
        
        return reason[:500]  # Limit length
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get signal generation statistics"""
        
        total = self.stats["total_analyses"]
        generated = self.stats["signals_generated"]
        
        return {
            **self.stats,
            "signal_rate": generated / total if total > 0 else 0,
            "buy_ratio": (
                self.stats["buy_signals"] / generated if generated > 0 else 0
            ),
            "sell_ratio": (
                self.stats["sell_signals"] / generated if generated > 0 else 0
            ),
        }
    
    def reset_statistics(self):
        """Reset statistics"""
        for key in self.stats:
            self.stats[key] = 0
        logger.info("Signal generator statistics reset")
    
    def update_settings(
        self,
        base_position_size: Optional[float] = None,
        max_position_size: Optional[float] = None,
        min_confidence_threshold: Optional[float] = None,
        sentiment_threshold: Optional[float] = None,
        impact_threshold: Optional[float] = None,
        enable_auto_execute: Optional[bool] = None,
    ):
        """Update generator settings"""
        
        if base_position_size is not None:
            self.base_position_size = base_position_size
            logger.info(f"Base position size set to: {base_position_size:.1%}")
        
        if max_position_size is not None:
            self.max_position_size = max_position_size
            logger.info(f"Max position size set to: {max_position_size:.1%}")
        
        if min_confidence_threshold is not None:
            self.min_confidence_threshold = min_confidence_threshold
            logger.info(f"Min confidence threshold set to: {min_confidence_threshold}")
        
        if sentiment_threshold is not None:
            self.sentiment_threshold = sentiment_threshold
            logger.info(f"Sentiment threshold set to: {sentiment_threshold}")
        
        if impact_threshold is not None:
            self.impact_threshold = impact_threshold
            logger.info(f"Impact threshold set to: {impact_threshold}")
        
        if enable_auto_execute is not None:
            self.enable_auto_execute = enable_auto_execute
            logger.warning(f"Auto-execute {'ENABLED' if enable_auto_execute else 'disabled'}")


# ============================================================================
# Factory function
# ============================================================================

def create_signal_generator(
    config: Optional[Dict[str, Any]] = None,
) -> NewsSignalGenerator:
    """
    Create NewsSignalGenerator from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured NewsSignalGenerator instance
    """
    if config is None:
        import os
        config = {
            "base_position_size": float(os.getenv("SIGNAL_BASE_POSITION", "0.05")),
            "max_position_size": float(os.getenv("SIGNAL_MAX_POSITION", "0.10")),
            "min_confidence_threshold": float(os.getenv("SIGNAL_MIN_CONFIDENCE", "0.6")),
            "sentiment_threshold": float(os.getenv("SIGNAL_SENTIMENT_THRESHOLD", "0.3")),
            "impact_threshold": float(os.getenv("SIGNAL_IMPACT_THRESHOLD", "0.5")),
            "enable_auto_execute": os.getenv("SIGNAL_AUTO_EXECUTE", "false").lower() == "true",
        }
    
    return NewsSignalGenerator(**config)


# ============================================================================
# Batch processing
# ============================================================================

async def generate_signals_batch(
    analyses: List[Dict[str, Any]],
    generator: Optional[NewsSignalGenerator] = None,
) -> List[TradingSignal]:
    """
    Generate signals from a batch of news analyses.
    
    Args:
        analyses: List of NewsAnalysis dictionaries
        generator: Optional pre-configured generator
        
    Returns:
        List of generated TradingSignals
    """
    if generator is None:
        generator = create_signal_generator()
    
    signals = []
    
    for analysis in analyses:
        signal = generator.generate_signal(analysis)
        if signal:
            signals.append(signal)
    
    logger.info(f"Batch processed: {len(analyses)} analyses → {len(signals)} signals")
    
    return signals
