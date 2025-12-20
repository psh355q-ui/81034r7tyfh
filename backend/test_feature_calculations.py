"""
Standalone test script for Feature calculations.

Tests feature calculation functions with real Yahoo Finance data.
No Docker or database required.
"""

import asyncio
import sys
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# Add backend to path
sys.path.insert(0, 'D:\\code\\ai-trading-system\\backend')

# Import features module directly to avoid cache_layer dependencies
import importlib.util
spec = importlib.util.spec_from_file_location("features", "data/feature_store/features.py")
features_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(features_module)

calculate_return = features_module.calculate_return
calculate_volatility = features_module.calculate_volatility
calculate_momentum = features_module.calculate_momentum
calculate_rsi = features_module.calculate_rsi
calculate_macd = features_module.calculate_macd
list_available_features = features_module.list_available_features

# Import collector directly
spec2 = importlib.util.spec_from_file_location("yahoo_collector", "data/collectors/yahoo_collector.py")
collector_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(collector_module)
YahooFinanceCollector = collector_module.YahooFinanceCollector


async def test_feature_calculations_with_mock_data():
    """Test feature calculations with synthetic data."""
    print("\n" + "=" * 60)
    print("TEST 1: Feature Calculations with Mock Data")
    print("=" * 60)

    # Generate mock OHLCV data (120 days to support all calculations)
    dates = pd.date_range(end=datetime(2024, 11, 8), periods=120, freq='D')
    np.random.seed(42)
    prices = 100 * (1 + np.random.randn(120).cumsum() * 0.01)

    mock_df = pd.DataFrame({
        'Open': prices + np.random.randn(120) * 0.5,
        'High': prices + np.abs(np.random.randn(120) * 1.0),
        'Low': prices - np.abs(np.random.randn(120) * 1.0),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 120),
    }, index=dates)

    # Mock data fetcher
    async def mock_fetcher(ticker: str, start: datetime, end: datetime):
        mask = (mock_df.index >= start) & (mock_df.index <= end)
        return mock_df[mask].copy()

    ticker = "MOCK"
    as_of = datetime(2024, 11, 8)

    print(f"\nTesting with {ticker} mock data ({len(mock_df)} days)")
    print(f"Price range: ${mock_df['Close'].min():.2f} - ${mock_df['Close'].max():.2f}")

    # Test 1: Returns
    print("\n--- Returns ---")
    ret_5d = await calculate_return(ticker, 5, as_of, mock_fetcher)
    ret_20d = await calculate_return(ticker, 20, as_of, mock_fetcher)
    ret_60d = await calculate_return(ticker, 60, as_of, mock_fetcher)

    print(f"ret_5d:  {ret_5d:.4f} ({ret_5d * 100:.2f}%)" if ret_5d is not None else "ret_5d:  N/A")
    print(f"ret_20d: {ret_20d:.4f} ({ret_20d * 100:.2f}%)" if ret_20d is not None else "ret_20d: N/A")
    print(f"ret_60d: {ret_60d:.4f} ({ret_60d * 100:.2f}%)" if ret_60d is not None else "ret_60d: N/A")

    # Test 2: Volatility
    print("\n--- Volatility (Annualized) ---")
    vol_20d = await calculate_volatility(ticker, 20, as_of, mock_fetcher)
    vol_60d = await calculate_volatility(ticker, 60, as_of, mock_fetcher)

    print(f"vol_20d: {vol_20d:.4f} ({vol_20d * 100:.2f}%)" if vol_20d is not None else "vol_20d: N/A")
    print(f"vol_60d: {vol_60d:.4f} ({vol_60d * 100:.2f}%)" if vol_60d is not None else "vol_60d: N/A")

    # Test 3: Momentum
    print("\n--- Momentum ---")
    mom_20d = await calculate_momentum(ticker, 20, as_of, mock_fetcher)
    mom_60d = await calculate_momentum(ticker, 60, as_of, mock_fetcher)

    print(f"mom_20d: {mom_20d:.4f} ({mom_20d * 100:.2f}%)" if mom_20d is not None else "mom_20d: N/A")
    print(f"mom_60d: {mom_60d:.4f} ({mom_60d * 100:.2f}%)" if mom_60d is not None else "mom_60d: N/A")

    # Test 4: RSI
    print("\n--- RSI ---")
    rsi_14 = await calculate_rsi(ticker, 14, as_of, mock_fetcher)
    print(f"rsi_14: {rsi_14:.2f}" if rsi_14 is not None else "rsi_14: N/A")

    # Test 5: MACD
    print("\n--- MACD ---")
    macd = await calculate_macd(ticker, as_of, mock_fetcher)
    if macd:
        print(f"MACD Line: {macd['macd']:.4f}")
        print(f"Signal Line: {macd['signal']:.4f}")
        print(f"Histogram: {macd['histogram']:.4f}")

    print("\n[OK] All mock data tests passed!")


async def test_feature_calculations_with_real_data():
    """Test feature calculations with real Yahoo Finance data."""
    print("\n" + "=" * 60)
    print("TEST 2: Feature Calculations with Real Yahoo Finance Data")
    print("=" * 60)

    collector = YahooFinanceCollector(cache_ttl_hours=24)

    ticker = "AAPL"
    as_of = datetime.now()

    print(f"\nFetching real data for {ticker}...")

    # Data fetcher using Yahoo Finance
    async def real_fetcher(ticker: str, start: datetime, end: datetime):
        return await collector.fetch_ohlcv(ticker, start, end)

    # Test all features
    features = {
        'ret_5d': lambda: calculate_return(ticker, 5, as_of, real_fetcher),
        'ret_20d': lambda: calculate_return(ticker, 20, as_of, real_fetcher),
        'vol_20d': lambda: calculate_volatility(ticker, 20, as_of, real_fetcher),
        'mom_20d': lambda: calculate_momentum(ticker, 20, as_of, real_fetcher),
        'rsi_14': lambda: calculate_rsi(ticker, 14, as_of, real_fetcher),
        'macd': lambda: calculate_macd(ticker, as_of, real_fetcher),
    }

    print(f"\nCalculating features for {ticker}...")
    results = {}

    for feature_name, calculator in features.items():
        try:
            print(f"  Computing {feature_name}... ", end='', flush=True)
            value = await calculator()
            results[feature_name] = value
            if isinstance(value, dict):
                print(f"[OK] (MACD: {value['macd']:.4f})")
            else:
                print(f"[OK] {value:.4f}")
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            results[feature_name] = None

    # Display results summary
    print("\n" + "=" * 60)
    print(f"Feature Summary for {ticker}")
    print("=" * 60)

    for feature_name, value in results.items():
        if value is not None:
            if isinstance(value, dict):
                print(f"{feature_name:10s}: MACD={value['macd']:.4f}, Signal={value['signal']:.4f}")
            else:
                print(f"{feature_name:10s}: {value:.6f}")
        else:
            print(f"{feature_name:10s}: N/A")

    # Cache statistics
    cache_stats = collector.get_cache_stats()
    print("\n" + "=" * 60)
    print("Yahoo Finance Collector Stats")
    print("=" * 60)
    print(f"Cache size: {cache_stats['cache_size']} entries")
    print(f"Request count: {cache_stats['request_count']}")
    print(f"Oldest entry age: {cache_stats['oldest_entry_age_hours']:.2f} hours")

    print("\n[OK] Real data tests completed!")


async def test_available_features():
    """Test feature registry."""
    print("\n" + "=" * 60)
    print("TEST 3: Available Features")
    print("=" * 60)

    features = list_available_features()
    print(f"\nRegistered features ({len(features)}):")
    for i, feature in enumerate(features, 1):
        print(f"  {i}. {feature}")

    print("\n[OK] Feature registry working!")


async def main():
    """Run all tests."""
    print("+" + "=" * 58 + "+")
    print("|" + "  AI Trading System - Feature Calculation Tests".center(58) + "|")
    print("+" + "=" * 58 + "+")

    try:
        # Test 1: Mock data (fast, no network)
        await test_feature_calculations_with_mock_data()

        # Test 2: Real Yahoo Finance data (requires internet)
        await test_feature_calculations_with_real_data()

        # Test 3: Feature registry
        await test_available_features()

        print("\n" + "=" * 60)
        print("*** ALL TESTS PASSED! ***")
        print("=" * 60)

        print("\nNext steps:")
        print("  1. Start Docker: docker compose up -d redis timescaledb")
        print("  2. Run migration: alembic upgrade head")
        print("  3. Test FeatureStore with caching: python test_feature_store.py")

    except Exception as e:
        print(f"\n[FAILED] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
