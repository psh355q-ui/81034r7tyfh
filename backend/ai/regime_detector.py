"""
Market Regime Detector Integration Layer.

Integrates the Market Regime Ensemble (from market_regime.py) with the AI Trading System.
Provides real-time regime detection (Bull/Bear/Sideways) based on multiple signals.

Based on ChatGPT's Market Regime & Replay Engine implementation.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

from backend.ai.market_regime import MarketRegimeEnsemble
from backend.data.feature_store.store import FeatureStore

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Real-time market regime detection using ensemble of signals.

    Features:
    - VIX-based volatility detection
    - Yield curve analysis (2Y-10Y spread)
    - Credit spread monitoring (HY-IG)
    - ETF flow analysis (SPY inflow/outflow)
    - News sentiment integration (from FastPollingService)
    - AI confidence aggregation

    Output: Probability distribution over {Bull, Bear, Sideways}

    Usage:
        detector = RegimeDetector(feature_store)
        regime = await detector.detect_current_regime()
        # regime = {'bull': 0.12, 'bear': 0.80, 'sideways': 0.08}
    """

    def __init__(
        self,
        feature_store: FeatureStore,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize regime detector.

        Args:
            feature_store: FeatureStore instance for data retrieval
            weights: Optional custom weights for ensemble (default: balanced)
        """
        self.feature_store = feature_store
        self.ensemble = MarketRegimeEnsemble(weights=weights)

        # Cache for regime detection (5-minute TTL)
        self.cached_regime: Optional[Dict[str, float]] = None
        self.cache_timestamp: Optional[datetime] = None
        self.cache_ttl = timedelta(minutes=5)

    async def detect_current_regime(self) -> Dict[str, float]:
        """
        Detect current market regime.

        Returns:
            Dictionary with probabilities: {'bull': 0.x, 'bear': 0.y, 'sideways': 0.z}
        """
        # Check cache
        if self._is_cache_valid():
            logger.info("Using cached regime detection")
            return self.cached_regime

        # Gather features
        features = await self._gather_features()

        # Run ensemble
        regime_proba = self.ensemble.predict_proba(features)

        # Update cache
        self.cached_regime = regime_proba
        self.cache_timestamp = datetime.now()

        logger.info(f"Detected regime: {regime_proba}")
        return regime_proba

    async def get_regime_label(self) -> str:
        """
        Get current regime as a single label (BULL/BEAR/SIDEWAYS).

        Returns:
            "BULL", "BEAR", or "SIDEWAYS"
        """
        proba = await self.detect_current_regime()
        max_regime = max(proba, key=proba.get)
        return max_regime.upper()

    async def _gather_features(self) -> Dict[str, Any]:
        """
        Gather all features needed for regime detection.

        Returns:
            Dictionary with feature values
        """
        features = {}

        # 1. VIX (volatility index)
        features['vix'] = await self._get_vix()

        # 2. VIX 1-day change (%)
        features['vix_change_1d'] = await self._get_vix_change()

        # 3. Yield curve (2Y-10Y spread)
        features['yield_curve_2y10y'] = await self._get_yield_curve()

        # 4. Credit spread (HY-IG in bps)
        features['credit_spread_hy_ig'] = await self._get_credit_spread()

        # 5. ETF flow (SPY net inflow in $)
        features['etf_flow_sp500_1d'] = await self._get_etf_flow()

        # 6. News sentiment (from FastPollingService)
        features['news_sentiment_30m'] = await self._get_news_sentiment()

        # 7. AI confidence (consensus among AI models)
        features['ai_confidence_ensemble'] = await self._get_ai_confidence()

        logger.debug(f"Gathered features: {features}")
        return features

    async def _get_vix(self) -> Optional[float]:
        """Fetch current VIX value."""
        try:
            # VIX ticker: ^VIX
            vix_data = await self.feature_store.get(
                ticker="^VIX",
                feature_name="close",
                as_of_timestamp=datetime.now()
            )
            return vix_data.value if vix_data else None
        except Exception as e:
            logger.error(f"Error fetching VIX: {e}")
            return None

    async def _get_vix_change(self) -> Optional[float]:
        """Calculate VIX 1-day percent change."""
        try:
            now = datetime.now()
            yesterday = now - timedelta(days=1)

            vix_today = await self.feature_store.get("^VIX", "close", now)
            vix_yesterday = await self.feature_store.get("^VIX", "close", yesterday)

            if vix_today and vix_yesterday and vix_yesterday.value != 0:
                pct_change = ((vix_today.value - vix_yesterday.value) / vix_yesterday.value) * 100
                return pct_change
            return None
        except Exception as e:
            logger.error(f"Error calculating VIX change: {e}")
            return None

    async def _get_yield_curve(self) -> Optional[float]:
        """Fetch 2Y-10Y Treasury yield spread."""
        try:
            now = datetime.now()

            # Tickers: ^TNX (10Y), ^FVX (5Y) - use as proxy
            # Note: For accurate 2Y-10Y spread, you may need FRED API
            y10 = await self.feature_store.get("^TNX", "close", now)
            y2 = await self.feature_store.get("^IRX", "close", now)  # 13-week T-bill as proxy

            if y10 and y2:
                spread = y10.value - y2.value
                return spread
            return None
        except Exception as e:
            logger.error(f"Error fetching yield curve: {e}")
            return None

    async def _get_credit_spread(self) -> Optional[float]:
        """Fetch HY-IG credit spread (in bps)."""
        try:
            # ETF proxies: HYG (High Yield), LQD (Investment Grade)
            # Spread = HYG yield - LQD yield
            # Note: This is simplified. Production would use actual credit indices.
            now = datetime.now()

            hyg = await self.feature_store.get("HYG", "close", now)
            lqd = await self.feature_store.get("LQD", "close", now)

            if hyg and lqd:
                # Approximate spread (very rough)
                # In reality, you'd need yield-to-maturity data
                spread_approx = (hyg.value - lqd.value) * 10  # Rough conversion
                return spread_approx
            return None
        except Exception as e:
            logger.error(f"Error fetching credit spread: {e}")
            return None

    async def _get_etf_flow(self) -> Optional[float]:
        """Fetch SPY ETF net flow (1-day)."""
        try:
            # Note: ETF flow data requires specialized data provider (e.g., ETF.com API)
            # For now, use volume as proxy
            now = datetime.now()
            yesterday = now - timedelta(days=1)

            spy_today = await self.feature_store.get("SPY", "volume", now)
            spy_yesterday = await self.feature_store.get("SPY", "volume", yesterday)

            if spy_today and spy_yesterday:
                # Positive volume change = net inflow (approximation)
                flow_proxy = (spy_today.value - spy_yesterday.value)
                return flow_proxy
            return None
        except Exception as e:
            logger.error(f"Error fetching ETF flow: {e}")
            return None

    async def _get_news_sentiment(self) -> Optional[float]:
        """Get aggregated news sentiment (last 30 minutes)."""
        try:
            # Integration with FastPollingService
            # For now, return neutral (0.0) as placeholder
            # TODO: Implement sentiment aggregation from FastPollingService
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching news sentiment: {e}")
            return None

    async def _get_ai_confidence(self) -> Optional[float]:
        """Get AI ensemble confidence (consensus level)."""
        try:
            # Placeholder: Return moderate confidence
            # TODO: Integrate with AI ensemble voting system
            return 0.5
        except Exception as e:
            logger.error(f"Error fetching AI confidence: {e}")
            return None

    def _is_cache_valid(self) -> bool:
        """Check if cached regime is still valid."""
        if self.cached_regime is None or self.cache_timestamp is None:
            return False

        age = datetime.now() - self.cache_timestamp
        return age < self.cache_ttl


# Example usage and testing
async def demo_regime_detection():
    """Demo: Detect current market regime."""
    from backend.data.feature_store.store import FeatureStore
    from backend.data.feature_store.cache_layer import CacheLayer

    # Initialize dependencies (in real app, use dependency injection)
    cache_layer = CacheLayer(
        redis_url="redis://localhost:6379",
        db_url="postgresql://user:pass@localhost/trading"
    )
    feature_store = FeatureStore(cache_layer)
    detector = RegimeDetector(feature_store)

    # Detect regime
    regime = await detector.detect_current_regime()
    label = await detector.get_regime_label()

    print(f"Current Market Regime: {label}")
    print(f"Probabilities: {regime}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo_regime_detection())
