"""
Credit Regime Factor for Feature Store Integration

Purpose: Calculate credit stress signals for trading decisions
Cost: $0 (FRED data is free, rule-based analysis)
Update: Daily (synced with FRED data releases)

This factor provides EARLY WARNING for:
- Liquidity crises
- Risk-off events
- Market regime shifts

Integration Points:
- Feature Store: Cached with 24h TTL
- ChatGPTStrategy: Enhances regime detection
- EnsembleStrategy: Triggers defensive positioning

Phase: Credit Regime Enhancement (Post-Phase 5)
Author: AI Trading System Team
Date: 2025-11-14

Based on:
- ChatGPT recommendation: Credit spread as macro indicator
- Gemini recommendation: AI arms race liquidity drain detection
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Import FRED collector (from Q1)
try:
    from .fred_collector import FREDCollector, CREDIT_STRESS_THRESHOLDS
    FRED_AVAILABLE = True
except ImportError:
    try:
        from fred_collector import FREDCollector, CREDIT_STRESS_THRESHOLDS
        FRED_AVAILABLE = True
    except ImportError:
        FRED_AVAILABLE = False
        logger.warning("FREDCollector not available")


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class CreditRegimeState:
    """
    Credit market regime state.
    """
    # Main indicators
    stress_factor: float  # % above 1-year average (0.0 = normal)
    stress_level: str     # NORMAL | ELEVATED | HIGH | CRITICAL
    
    # Raw values
    hy_spread: float      # High Yield spread (%)
    ig_spread: float      # Investment Grade spread (%)
    ted_spread: float     # Interbank stress (%)
    
    # Context
    vix: float            # Market volatility
    yield_curve: float    # 10Y - 2Y spread (inverted = recession warning)
    
    # Signals
    liquidity_crunch_warning: bool  # Gemini's scenario
    above_2sigma: bool              # ChatGPT's threshold
    
    # Metadata
    date: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stress_factor": self.stress_factor,
            "stress_level": self.stress_level,
            "hy_spread": self.hy_spread,
            "ig_spread": self.ig_spread,
            "ted_spread": self.ted_spread,
            "vix": self.vix,
            "yield_curve": self.yield_curve,
            "liquidity_crunch_warning": self.liquidity_crunch_warning,
            "above_2sigma": self.above_2sigma,
            "date": self.date,
            "timestamp": self.timestamp,
        }
    
    def get_regime_impact(self) -> str:
        """
        Determine impact on market regime.
        
        Returns:
            Regime override suggestion: NONE | RISK_OFF | CRASH
        """
        if self.stress_level == "CRITICAL" or self.liquidity_crunch_warning:
            return "CRASH"
        elif self.stress_level == "HIGH":
            return "RISK_OFF"
        elif self.stress_level == "ELEVATED" and self.above_2sigma:
            return "RISK_OFF"
        else:
            return "NONE"


# ============================================================================
# Credit Regime Factor Calculator
# ============================================================================

class CreditRegimeFactor:
    """
    Calculate credit regime factors for integration with Feature Store.
    
    This class serves as the bridge between:
    1. FRED data (raw credit spreads)
    2. Feature Store (cached factors)
    3. AI Strategies (regime detection)
    
    Key Features:
    - Credit stress calculation
    - Liquidity crunch detection (Gemini scenario)
    - 2-sigma threshold check (ChatGPT recommendation)
    - Feature Store compatible output
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize credit regime factor calculator.
        
        Args:
            redis_client: Redis client for caching
        """
        if not FRED_AVAILABLE:
            logger.warning("FRED Collector not available. Using fallback values.")
            self.fred_collector = None
        else:
            self.fred_collector = FREDCollector(cache_client=redis_client)
        
        self.redis = redis_client
        self.cache_ttl = 86400  # 24 hours
        
        # State tracking
        self.latest_state: Optional[CreditRegimeState] = None
        
        # Metrics
        self.metrics = {
            "total_calculations": 0,
            "regime_overrides": 0,
            "liquidity_warnings": 0,
            "last_update": None,
        }
        
        logger.info("Credit Regime Factor initialized")
    
    async def calculate(self, force_refresh: bool = False) -> CreditRegimeState:
        """
        Calculate current credit regime state.
        
        This is the main entry point for Feature Store integration.
        
        Args:
            force_refresh: Skip cache and recalculate
        
        Returns:
            CreditRegimeState with all indicators
        """
        # Check cache first
        if not force_refresh and self.latest_state:
            # Check if state is recent (< 6 hours old)
            state_time = datetime.fromisoformat(self.latest_state.timestamp)
            age_hours = (datetime.utcnow() - state_time).total_seconds() / 3600
            
            if age_hours < 6:
                logger.debug("Using cached credit regime state")
                return self.latest_state
        
        # Calculate new state
        if self.fred_collector is None:
            logger.warning("Using fallback credit regime state")
            return self._get_fallback_state()
        
        try:
            # Get credit stress data
            stress_data = await self.fred_collector.calculate_credit_stress_factor()
            
            if stress_data.get("error"):
                logger.error(f"Credit stress calculation error: {stress_data['error']}")
                return self._get_fallback_state()
            
            # Get latest spreads for additional context
            latest = await self.fred_collector.get_latest_spreads()
            
            # Calculate yield curve
            t10y = latest.get("T10Y", 4.0)
            t2y = latest.get("T2Y", 4.0)
            yield_curve = t10y - t2y  # Negative = inverted (recession signal)
            
            # Check for liquidity crunch warning (Gemini's scenario)
            liquidity_warning = self.fred_collector.detect_liquidity_crunch_warning(stress_data)
            
            # Create state object
            state = CreditRegimeState(
                stress_factor=stress_data["stress_factor"],
                stress_level=stress_data["stress_level"],
                hy_spread=stress_data["hy_spread_current"],
                ig_spread=stress_data["ig_spread_current"],
                ted_spread=latest.get("TED_SPREAD", 0),
                vix=latest.get("VIX", 20),
                yield_curve=yield_curve,
                liquidity_crunch_warning=liquidity_warning,
                above_2sigma=stress_data["above_2sigma"],
                date=stress_data["date"],
                timestamp=datetime.utcnow().isoformat(),
            )
            
            # Update metrics
            self.metrics["total_calculations"] += 1
            self.metrics["last_update"] = state.timestamp
            
            if liquidity_warning:
                self.metrics["liquidity_warnings"] += 1
            
            if state.get_regime_impact() != "NONE":
                self.metrics["regime_overrides"] += 1
            
            # Cache the state
            self.latest_state = state
            
            logger.info(
                f"Credit regime: {state.stress_level}, "
                f"stress: {state.stress_factor:+.2%}, "
                f"HY: {state.hy_spread:.2f}%, "
                f"liquidity_warning: {state.liquidity_crunch_warning}"
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error calculating credit regime: {e}")
            return self._get_fallback_state()
    
    def _get_fallback_state(self) -> CreditRegimeState:
        """
        Return conservative fallback state when data is unavailable.
        """
        return CreditRegimeState(
            stress_factor=0.0,
            stress_level="UNKNOWN",
            hy_spread=4.5,  # Average historical value
            ig_spread=1.2,
            ted_spread=0.25,
            vix=20.0,
            yield_curve=0.5,
            liquidity_crunch_warning=False,
            above_2sigma=False,
            date="fallback",
            timestamp=datetime.utcnow().isoformat(),
        )
    
    async def get_feature_store_values(self) -> Dict[str, float]:
        """
        Get values formatted for Feature Store integration.
        
        Returns:
            Dict with feature names and values
        """
        state = await self.calculate()
        
        return {
            # Main factor (0.0 = normal, 0.5+ = critical)
            "credit_stress_factor": state.stress_factor,
            
            # Normalized stress level (0-1 scale)
            "credit_stress_score": self._normalize_stress_level(state.stress_level),
            
            # Raw spreads (for analysis)
            "hy_spread": state.hy_spread,
            "ig_spread": state.ig_spread,
            "ted_spread": state.ted_spread,
            
            # Binary signals (1.0 = true, 0.0 = false)
            "liquidity_crunch_warning": 1.0 if state.liquidity_crunch_warning else 0.0,
            "credit_above_2sigma": 1.0 if state.above_2sigma else 0.0,
            
            # Yield curve (negative = inverted)
            "yield_curve_10y_2y": state.yield_curve,
        }
    
    def _normalize_stress_level(self, level: str) -> float:
        """
        Convert stress level to 0-1 score.
        """
        mapping = {
            "NORMAL": 0.0,
            "ELEVATED": 0.3,
            "HIGH": 0.6,
            "CRITICAL": 1.0,
            "UNKNOWN": 0.5,  # Conservative middle value
        }
        return mapping.get(level, 0.5)
    
    def should_override_regime(self, current_regime: str) -> Optional[str]:
        """
        Check if credit conditions should override current regime.
        
        This implements the "pre-check" logic suggested by ChatGPT.
        Credit stress can FORCE regime change even if stock market looks good.
        
        Args:
            current_regime: Current regime from ChatGPTStrategy
        
        Returns:
            New regime if override needed, None otherwise
        """
        if self.latest_state is None:
            return None
        
        impact = self.latest_state.get_regime_impact()
        
        if impact == "NONE":
            return None
        
        # Credit stress can upgrade risk level, but not downgrade
        # (i.e., credit warning can turn BULL to RISK_OFF, but not CRASH to BULL)
        regime_severity = {
            "BULL": 1,
            "SIDEWAYS": 2,
            "RISK_OFF": 3,
            "CRASH": 4,
        }
        
        current_severity = regime_severity.get(current_regime, 2)
        impact_severity = regime_severity.get(impact, 2)
        
        if impact_severity > current_severity:
            logger.warning(
                f"Credit stress override: {current_regime} -> {impact} "
                f"(stress: {self.latest_state.stress_level})"
            )
            return impact
        
        return None
    
    def adjust_position_size(
        self,
        base_size: float,
        current_regime: str
    ) -> float:
        """
        Adjust position size based on credit conditions.
        
        This implements ChatGPT's recommendation:
        "When credit stress is HIGH, reduce all position sizes"
        
        Args:
            base_size: Original position size
            current_regime: Current market regime
        
        Returns:
            Adjusted position size
        """
        if self.latest_state is None:
            return base_size
        
        # Adjustment based on stress level
        if self.latest_state.stress_level == "CRITICAL":
            # Reduce to 30% of base size
            return base_size * 0.3
        elif self.latest_state.stress_level == "HIGH":
            # Reduce to 50% of base size
            return base_size * 0.5
        elif self.latest_state.stress_level == "ELEVATED":
            # Reduce to 80% of base size
            return base_size * 0.8
        else:
            return base_size
    
    def get_recommended_cash_allocation(self) -> float:
        """
        Get recommended cash allocation based on credit conditions.
        
        This implements Gemini's recommendation:
        "기관들처럼 선제적으로 현금을 확보"
        
        Returns:
            Recommended cash percentage (0.0 to 1.0)
        """
        if self.latest_state is None:
            return 0.3  # Default 30% cash
        
        # Base on credit stress
        if self.latest_state.stress_level == "CRITICAL":
            return 0.9  # 90% cash
        elif self.latest_state.liquidity_crunch_warning:
            return 0.7  # 70% cash (Gemini's scenario)
        elif self.latest_state.stress_level == "HIGH":
            return 0.6  # 60% cash
        elif self.latest_state.stress_level == "ELEVATED":
            return 0.4  # 40% cash
        else:
            return 0.3  # Normal 30% cash
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get factor metrics."""
        metrics = self.metrics.copy()
        
        if self.latest_state:
            metrics["current_state"] = self.latest_state.to_dict()
        
        return metrics


# ============================================================================
# Feature Store Integration Helper
# ============================================================================

async def calculate_credit_regime_feature(
    ticker: str,
    as_of: datetime,
    data_fetcher
) -> float:
    """
    Feature Store compatible calculator function.
    
    This function signature matches FeatureStore.compute_feature() requirements.
    
    Note: Credit regime is market-wide, not ticker-specific.
    But we return the same value for all tickers to maintain compatibility.
    
    Args:
        ticker: Stock ticker (ignored for market-wide factor)
        as_of: Point-in-time (used for caching)
        data_fetcher: Data fetcher function (not used)
    
    Returns:
        Credit stress factor (-1.0 to +inf, 0.0 = normal)
    """
    factor = CreditRegimeFactor()
    state = await factor.calculate()
    return state.stress_factor


async def calculate_liquidity_warning_feature(
    ticker: str,
    as_of: datetime,
    data_fetcher
) -> float:
    """
    Binary liquidity crunch warning feature.
    
    Returns:
        1.0 if warning active, 0.0 otherwise
    """
    factor = CreditRegimeFactor()
    state = await factor.calculate()
    return 1.0 if state.liquidity_crunch_warning else 0.0


# ============================================================================
# ChatGPTStrategy Integration
# ============================================================================

def enhance_regime_detection(
    current_regime: str,
    market_context: Dict[str, Any],
    credit_state: CreditRegimeState
) -> str:
    """
    Enhance ChatGPTStrategy's regime detection with credit factors.
    
    This is the Q3 integration point suggested by ChatGPT.
    
    Logic:
    1. Check credit stress FIRST (leading indicator)
    2. If credit stress is HIGH/CRITICAL, override regime
    3. Otherwise, use normal regime detection
    
    Args:
        current_regime: Regime from ChatGPTStrategy
        market_context: Market data (VIX, SPY, etc.)
        credit_state: Credit regime state
    
    Returns:
        Final regime after credit adjustment
    """
    # Step 1: Credit stress override (highest priority)
    if credit_state.stress_level == "CRITICAL":
        logger.warning("Credit CRITICAL: Forcing CRASH regime")
        return "CRASH"
    
    # Step 2: Liquidity crunch warning (Gemini's scenario)
    if credit_state.liquidity_crunch_warning:
        logger.warning("Liquidity crunch warning: Forcing RISK_OFF regime")
        if current_regime == "CRASH":
            return "CRASH"  # Don't downgrade from CRASH
        return "RISK_OFF"
    
    # Step 3: High credit stress
    if credit_state.stress_level == "HIGH":
        if current_regime in ["BULL", "SIDEWAYS"]:
            logger.warning("High credit stress: Upgrading to RISK_OFF")
            return "RISK_OFF"
    
    # Step 4: 2-Sigma breach (ChatGPT's threshold)
    if credit_state.above_2sigma:
        if current_regime == "BULL":
            logger.warning("Credit above 2-sigma: BULL -> SIDEWAYS")
            return "SIDEWAYS"
    
    # No override needed
    return current_regime


# ============================================================================
# Demo
# ============================================================================

async def run_credit_regime_demo():
    """
    Demonstrate credit regime factor functionality.
    """
    print("=" * 60)
    print("Credit Regime Factor Demo")
    print("=" * 60)
    
    factor = CreditRegimeFactor()
    
    # 1. Calculate credit regime
    print("\n1. Calculating credit regime state...")
    state = await factor.calculate()
    
    print(f"\nCredit Regime State:")
    print(f"  Stress Factor:  {state.stress_factor:+.2%}")
    print(f"  Stress Level:   {state.stress_level}")
    print(f"  HY Spread:      {state.hy_spread:.2f}%")
    print(f"  IG Spread:      {state.ig_spread:.2f}%")
    print(f"  Yield Curve:    {state.yield_curve:.2f}%")
    print(f"  Above 2-Sigma:  {state.above_2sigma}")
    print(f"  Liquidity Warning: {state.liquidity_crunch_warning}")
    
    # 2. Feature Store values
    print("\n2. Feature Store integration values:")
    features = await factor.get_feature_store_values()
    for name, value in features.items():
        print(f"  {name}: {value:.4f}")
    
    # 3. Regime override check
    print("\n3. Testing regime override logic:")
    test_regimes = ["BULL", "SIDEWAYS", "RISK_OFF", "CRASH"]
    for regime in test_regimes:
        override = factor.should_override_regime(regime)
        if override:
            print(f"  {regime} -> {override} (OVERRIDE)")
        else:
            print(f"  {regime} -> {regime} (no change)")
    
    # 4. Position size adjustment
    print("\n4. Position size adjustment:")
    base_size = 1000.0
    adjusted = factor.adjust_position_size(base_size, "BULL")
    print(f"  Base: ${base_size:.0f}")
    print(f"  Adjusted: ${adjusted:.0f}")
    print(f"  Reduction: {((base_size - adjusted) / base_size * 100):.1f}%")
    
    # 5. Cash allocation recommendation
    print("\n5. Recommended cash allocation:")
    cash_pct = factor.get_recommended_cash_allocation()
    print(f"  Cash: {cash_pct:.1%}")
    print(f"  Risk Assets: {(1 - cash_pct):.1%}")
    
    # 6. Metrics
    print("\n6. Factor Metrics:")
    metrics = factor.get_metrics()
    for key, value in metrics.items():
        if key != "current_state":
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_credit_regime_demo())
