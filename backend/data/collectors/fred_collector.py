"""
FRED Data Collector for Credit Regime Analysis

Purpose: Fetch credit spread data from Federal Reserve Economic Data (FRED)
Cost: $0 (FREE API, no key required for basic usage)
Update Frequency: Daily (FRED data updates daily)

Credit spreads are LEADING INDICATORS that move before:
- Stock market crashes
- Liquidity crises
- Risk-off events

Phase: Credit Regime Enhancement
Author: AI Trading System Team
Date: 2025-11-14

References:
- ChatGPT suggestion: Credit spread as macro hedge fund indicator
- Gemini suggestion: AI arms race → liquidity drain detection
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

logger = logging.getLogger(__name__)

# Check for pandas-datareader
try:
    import pandas as pd
    import pandas_datareader.data as web
    PANDAS_DATAREADER_AVAILABLE = True
except ImportError:
    PANDAS_DATAREADER_AVAILABLE = False
    logger.warning(
        "pandas-datareader not installed. "
        "Install with: pip install pandas-datareader"
    )


# ============================================================================
# FRED Data Tickers
# ============================================================================

FRED_CREDIT_TICKERS = {
    # 1. US High Yield (HY) Spread - MOST IMPORTANT
    # BofA US High Yield Index Option-Adjusted Spread
    # Measures: Junk bond risk premium over Treasuries
    # Signal: Rising = Fear in credit markets
    "HY_SPREAD": "BAMLH0A0HYM2",
    
    # 2. US Investment Grade (IG) Spread
    # BofA US Corporate Index Option-Adjusted Spread
    # Measures: Corporate borrowing cost premium
    # Signal: Rising = Tightening financial conditions
    "IG_SPREAD": "BAMLC0A0CM",
    
    # 3. TED Spread (optional, less critical)
    # 3-Month LIBOR minus 3-Month T-Bill
    # Measures: Interbank lending stress
    # Signal: Spikes = Banking system stress (2008, 2020)
    "TED_SPREAD": "TEDRATE",
    
    # 4. VIX (for context)
    # CBOE Volatility Index
    "VIX": "VIXCLS",
    
    # 5. 10-Year Treasury Yield (context)
    "T10Y": "DGS10",
    
    # 6. 2-Year Treasury Yield (context)
    "T2Y": "DGS2",
}

# Thresholds for credit stress detection (based on historical data)
CREDIT_STRESS_THRESHOLDS = {
    "HY_SPREAD": {
        "normal": 4.0,        # < 4% = Normal
        "elevated": 5.0,      # 4-5% = Slightly elevated
        "warning": 6.0,       # 5-6% = Warning
        "critical": 8.0,      # > 8% = Critical (2008, 2020 levels)
    },
    "IG_SPREAD": {
        "normal": 1.2,
        "elevated": 1.5,
        "warning": 2.0,
        "critical": 3.0,
    },
    "TED_SPREAD": {
        "normal": 0.25,
        "elevated": 0.50,
        "warning": 0.75,
        "critical": 1.0,
    },
}


# ============================================================================
# FRED Collector
# ============================================================================

class FREDCollector:
    """
    Collect credit spread data from FRED (Federal Reserve Economic Data).
    
    Use Cases:
    1. Daily credit market health check
    2. Liquidity stress early warning
    3. Macro regime detection enhancement
    
    Data Characteristics:
    - Updated daily (with 1-day lag)
    - Free, no API key required
    - Highly reliable government source
    
    Integration:
    - FeatureStore caches with 24h TTL
    - ChatGPTStrategy uses for regime detection
    - EnsembleStrategy uses for position sizing
    """
    
    def __init__(self, cache_client=None):
        """
        Initialize FRED collector.
        
        Args:
            cache_client: Optional Redis client for caching
        """
        if not PANDAS_DATAREADER_AVAILABLE:
            raise ImportError(
                "pandas-datareader not installed. "
                "Install with: pip install pandas-datareader"
            )
        
        self.cache = cache_client
        self.cache_ttl = 86400  # 24 hours (data updates daily)
        
        # Metrics
        self.metrics = {
            "total_fetches": 0,
            "cache_hits": 0,
            "last_fetch": None,
            "fetch_errors": 0,
        }
        
        logger.info("FRED Collector initialized")
    
    async def fetch_credit_spreads(
        self,
        days_lookback: int = 365 * 2,
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Fetch credit spread data from FRED.
        
        Args:
            days_lookback: Number of days of historical data (default 2 years)
            force_refresh: Skip cache and fetch fresh data
        
        Returns:
            DataFrame with columns: HY_SPREAD, IG_SPREAD, TED_SPREAD, etc.
            Index: DatetimeIndex
        """
        logger.info(f"Fetching credit spreads (lookback: {days_lookback} days)")
        
        # Check cache first
        if not force_refresh and self.cache:
            cached = await self._get_cached_spreads()
            if cached is not None:
                self.metrics["cache_hits"] += 1
                logger.info("Using cached credit spread data")
                return cached
        
        # Fetch from FRED
        try:
            start_date = datetime.now() - timedelta(days=days_lookback)
            end_date = datetime.now()
            
            # Use pandas_datareader to fetch FRED data
            # This is a synchronous call, but we wrap it for async compatibility
            df = await asyncio.to_thread(
                self._fetch_fred_data,
                start_date,
                end_date
            )
            
            if df is None or df.empty:
                logger.error("Failed to fetch FRED data")
                return None
            
            # Update metrics
            self.metrics["total_fetches"] += 1
            self.metrics["last_fetch"] = datetime.utcnow().isoformat()
            
            # Cache the data
            if self.cache:
                await self._cache_spreads(df)
            
            logger.info(
                f"Fetched credit spreads: {len(df)} days, "
                f"latest date: {df.index[-1].date()}"
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching FRED data: {e}")
            self.metrics["fetch_errors"] += 1
            return None
    
    def _fetch_fred_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Synchronous FRED data fetch (called in thread).
        """
        try:
            # Fetch all tickers at once
            ticker_list = list(FRED_CREDIT_TICKERS.values())
            
            df = web.DataReader(
                ticker_list,
                'fred',
                start_date,
                end_date
            )
            
            # Rename columns to readable names
            reverse_map = {v: k for k, v in FRED_CREDIT_TICKERS.items()}
            df = df.rename(columns=reverse_map)
            
            # Forward-fill missing values (weekends, holidays)
            df = df.ffill()
            
            # Fill remaining NaN with 0 (start of series)
            df = df.fillna(0.0)
            
            return df
            
        except Exception as e:
            logger.error(f"FRED fetch error: {e}")
            return None
    
    async def get_latest_spreads(self) -> Dict[str, float]:
        """
        Get the latest credit spread values.
        
        Returns:
            Dict with latest values for each spread
        """
        df = await self.fetch_credit_spreads(days_lookback=30)
        
        if df is None or df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        return {
            "HY_SPREAD": float(latest.get("HY_SPREAD", 0)),
            "IG_SPREAD": float(latest.get("IG_SPREAD", 0)),
            "TED_SPREAD": float(latest.get("TED_SPREAD", 0)),
            "VIX": float(latest.get("VIX", 0)),
            "T10Y": float(latest.get("T10Y", 0)),
            "T2Y": float(latest.get("T2Y", 0)),
            "date": str(df.index[-1].date()),
        }
    
    async def calculate_credit_stress_factor(
        self,
        lookback_days: int = 365
    ) -> Dict[str, Any]:
        """
        Calculate credit stress factor based on ChatGPT's suggestion.
        
        Formula: (Current HY Spread / 1-Year Avg) - 1
        
        Thresholds:
        - < 0.1 (10%): Normal
        - 0.1 - 0.3: Elevated
        - 0.3 - 0.5: Warning
        - > 0.5: Critical
        
        Returns:
            Dict with stress factor and analysis
        """
        df = await self.fetch_credit_spreads(days_lookback=lookback_days)
        
        if df is None or df.empty:
            return {
                "stress_factor": 0.0,
                "stress_level": "UNKNOWN",
                "error": "Failed to fetch data",
            }
        
        # Calculate for HY Spread (most important)
        hy_latest = df["HY_SPREAD"].iloc[-1]
        hy_mean = df["HY_SPREAD"].mean()
        hy_std = df["HY_SPREAD"].std()
        
        # Stress factor (% above average)
        stress_factor = (hy_latest / hy_mean) - 1.0
        
        # 2-Sigma threshold (ChatGPT's recommendation)
        threshold_2sigma = hy_mean + (2 * hy_std)
        
        # Determine stress level
        if hy_latest > threshold_2sigma:
            stress_level = "CRITICAL"
        elif stress_factor > 0.3:
            stress_level = "HIGH"
        elif stress_factor > 0.1:
            stress_level = "ELEVATED"
        else:
            stress_level = "NORMAL"
        
        # Also check absolute levels
        if hy_latest > CREDIT_STRESS_THRESHOLDS["HY_SPREAD"]["critical"]:
            stress_level = "CRITICAL"
        
        return {
            "stress_factor": stress_factor,
            "stress_level": stress_level,
            "hy_spread_current": hy_latest,
            "hy_spread_1y_avg": hy_mean,
            "hy_spread_1y_std": hy_std,
            "hy_spread_2sigma_threshold": threshold_2sigma,
            "above_2sigma": hy_latest > threshold_2sigma,
            "ig_spread_current": df["IG_SPREAD"].iloc[-1],
            "ted_spread_current": df["TED_SPREAD"].iloc[-1] if "TED_SPREAD" in df.columns else 0,
            "date": str(df.index[-1].date()),
        }
    
    def detect_liquidity_crunch_warning(
        self,
        credit_data: Dict[str, Any]
    ) -> bool:
        """
        Detect potential liquidity crunch based on Gemini's scenario.
        
        Signals:
        1. HY Spread rising rapidly
        2. IG Spread widening
        3. Credit stress above 2-sigma
        
        Returns:
            True if liquidity crunch warning should be issued
        """
        if credit_data.get("error"):
            return False
        
        # Check multiple conditions
        conditions_met = 0
        
        # 1. Stress factor above threshold
        if credit_data.get("stress_factor", 0) > 0.3:
            conditions_met += 1
        
        # 2. Above 2-sigma threshold
        if credit_data.get("above_2sigma", False):
            conditions_met += 1
        
        # 3. Absolute HY spread critical
        hy_current = credit_data.get("hy_spread_current", 0)
        if hy_current > CREDIT_STRESS_THRESHOLDS["HY_SPREAD"]["warning"]:
            conditions_met += 1
        
        # 4. IG spread elevated
        ig_current = credit_data.get("ig_spread_current", 0)
        if ig_current > CREDIT_STRESS_THRESHOLDS["IG_SPREAD"]["warning"]:
            conditions_met += 1
        
        # Trigger if 2+ conditions met
        return conditions_met >= 2
    
    async def _get_cached_spreads(self) -> Optional[pd.DataFrame]:
        """Get cached spread data from Redis."""
        if not self.cache:
            return None
        
        try:
            # Cache key
            cache_key = "fred:credit_spreads:latest"
            cached = await self.cache.get(cache_key)
            
            if cached:
                import json
                data = json.loads(cached)
                df = pd.DataFrame(data["values"])
                df.index = pd.to_datetime(data["dates"])
                return df
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    async def _cache_spreads(self, df: pd.DataFrame):
        """Cache spread data in Redis."""
        if not self.cache:
            return
        
        try:
            import json
            
            # Prepare data for JSON serialization
            data = {
                "dates": [str(d) for d in df.index],
                "values": df.to_dict(orient="list"),
                "cached_at": datetime.utcnow().isoformat(),
            }
            
            cache_key = "fred:credit_spreads:latest"
            await self.cache.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data)
            )
            
            logger.debug("Cached credit spread data (TTL: %ds)", self.cache_ttl)
            
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collector metrics."""
        return self.metrics.copy()


# ============================================================================
# Demo and Testing
# ============================================================================

async def run_fred_demo():
    """
    Demonstrate FRED Collector functionality.
    """
    print("=" * 60)
    print("FRED Credit Spread Collector Demo")
    print("=" * 60)
    
    collector = FREDCollector()
    
    # 1. Fetch latest spreads
    print("\n1. Fetching latest credit spreads...")
    latest = await collector.get_latest_spreads()
    
    if latest:
        print(f"\nLatest Credit Spreads ({latest['date']}):")
        print(f"  HY Spread:  {latest['HY_SPREAD']:.2f}%")
        print(f"  IG Spread:  {latest['IG_SPREAD']:.2f}%")
        print(f"  TED Spread: {latest['TED_SPREAD']:.3f}%")
        print(f"  VIX:        {latest['VIX']:.2f}")
    else:
        print("  Failed to fetch data")
    
    # 2. Calculate stress factor
    print("\n2. Calculating credit stress factor...")
    stress = await collector.calculate_credit_stress_factor()
    
    if not stress.get("error"):
        print(f"\nCredit Stress Analysis ({stress['date']}):")
        print(f"  Stress Factor:  {stress['stress_factor']:+.2%}")
        print(f"  Stress Level:   {stress['stress_level']}")
        print(f"  Current HY:     {stress['hy_spread_current']:.2f}%")
        print(f"  1Y Avg HY:      {stress['hy_spread_1y_avg']:.2f}%")
        print(f"  2-Sigma Line:   {stress['hy_spread_2sigma_threshold']:.2f}%")
        print(f"  Above 2-Sigma:  {stress['above_2sigma']}")
    else:
        print(f"  Error: {stress['error']}")
    
    # 3. Detect liquidity crunch warning
    print("\n3. Checking for liquidity crunch warning...")
    warning = collector.detect_liquidity_crunch_warning(stress)
    
    if warning:
        print("  ⚠️  WARNING: Liquidity crunch conditions detected!")
        print("  → Recommend: Switch to RISK_OFF regime")
        print("  → Recommend: Increase cash allocation to 60-90%")
    else:
        print("  ✅ No liquidity crunch warning")
    
    # 4. Show metrics
    print("\n4. Collector Metrics:")
    metrics = collector.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    """
    Run demo when executed directly.
    
    Usage:
        python fred_collector.py
    
    Requirements:
        pip install pandas-datareader
    """
    asyncio.run(run_fred_demo())
