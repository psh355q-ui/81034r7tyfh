"""
Trading Decision Model

Represents an AI-generated trading decision with reasoning.

Author: AI Trading System Team
Date: 2025-11-15
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class TradingDecision:
    """
    AI-generated trading decision.

    Represents the output of the TradingAgent after analyzing
    a stock with features, pre-checks, and post-checks.
    """

    # Basic decision
    ticker: str
    action: str  # "BUY", "SELL", "HOLD"
    conviction: float  # 0.0 to 1.0

    # Reasoning and context
    reasoning: str
    risk_factors: List[str] = field(default_factory=list)

    # Pricing and position sizing
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: float = 0.0  # Percentage of portfolio (0-100)

    # Feature snapshot
    features_used: Dict = field(default_factory=dict)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    model_version: str = "v1.0"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "ticker": self.ticker,
            "action": self.action,
            "conviction": self.conviction,
            "reasoning": self.reasoning,
            "risk_factors": self.risk_factors,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "position_size": self.position_size,
            "features_used": self.features_used,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "model_version": self.model_version,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"TradingDecision({self.ticker}): "
            f"{self.action} (conviction={self.conviction:.2f}, "
            f"position_size={self.position_size:.1f}%)"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"TradingDecision(ticker='{self.ticker}', action='{self.action}', "
            f"conviction={self.conviction:.2f}, position_size={self.position_size:.1f}%)"
        )

    @property
    def is_actionable(self) -> bool:
        """Check if decision requires action (not HOLD)."""
        return self.action in ["BUY", "SELL"]

    @property
    def has_high_conviction(self) -> bool:
        """Check if conviction is high (>= 0.7)."""
        return self.conviction >= 0.7

    @property
    def risk_level(self) -> str:
        """Get overall risk level based on risk factors."""
        num_risks = len(self.risk_factors)
        if num_risks == 0:
            return "LOW"
        elif num_risks <= 2:
            return "MEDIUM"
        else:
            return "HIGH"
