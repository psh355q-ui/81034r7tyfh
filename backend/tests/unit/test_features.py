"""
Unit tests for feature calculation functions.

Tests each feature calculation function in isolation with mock data.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from data.feature_store.features import (
    calculate_return,
    calculate_volatility,
    calculate_momentum,
    calculate_rsi,
    calculate_macd,
)


@pytest.fixture
def mock_ohlcv_data():
    """
    Generate mock OHLCV data for testing.

    Returns 60 days of data with realistic price movements.
    """
    dates = pd.date_range(end=datetime(2024, 11, 8), periods=60, freq='D')

    # Generate synthetic price data with trend and volatility
    np.random.seed(42)
    prices = 100 * (1 + np.random.randn(60).cumsum() * 0.01)

    df = pd.DataFrame({
        'Open': prices + np.random.randn(60) * 0.5,
        'High': prices + np.abs(np.random.randn(60) * 1.0),
        'Low': prices - np.abs(np.random.randn(60) * 1.0),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 60),
    }, index=dates)

    return df


@pytest.fixture
async def mock_data_fetcher(mock_ohlcv_data):
    """Mock data fetcher that returns pre-generated OHLCV data."""
    async def fetcher(ticker: str, start: datetime, end: datetime):
        # Filter data by date range
        mask = (mock_ohlcv_data.index >= start) & (mock_ohlcv_data.index <= end)
        return mock_ohlcv_data[mask].copy()

    return fetcher


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_return_5d(mock_data_fetcher):
    """Test 5-day return calculation."""
    ticker = "TEST"
    as_of = datetime(2024, 11, 8)

    result = await calculate_return(ticker, 5, as_of, mock_data_fetcher)

    assert result is not None
    assert isinstance(result, float)
    assert -1.0 < result < 1.0  # Reasonable return range


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_return_insufficient_data():
    """Test return calculation with insufficient data."""
    async def empty_fetcher(ticker: str, start: datetime, end: datetime):
        return pd.DataFrame()  # Empty dataframe

    result = await calculate_return("TEST", 5, datetime(2024, 11, 8), empty_fetcher)

    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_volatility_20d(mock_data_fetcher):
    """Test 20-day volatility calculation."""
    ticker = "TEST"
    as_of = datetime(2024, 11, 8)

    result = await calculate_volatility(ticker, 20, as_of, mock_data_fetcher)

    assert result is not None
    assert isinstance(result, float)
    assert 0.0 < result < 2.0  # Reasonable volatility range (annualized)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_momentum_20d(mock_data_fetcher):
    """Test 20-day momentum calculation."""
    ticker = "TEST"
    as_of = datetime(2024, 11, 8)

    result = await calculate_momentum(ticker, 20, as_of, mock_data_fetcher)

    assert result is not None
    assert isinstance(result, float)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_rsi_14(mock_data_fetcher):
    """Test RSI calculation."""
    ticker = "TEST"
    as_of = datetime(2024, 11, 8)

    result = await calculate_rsi(ticker, 14, as_of, mock_data_fetcher)

    assert result is not None
    assert isinstance(result, float)
    assert 0.0 <= result <= 100.0  # RSI range


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_macd(mock_data_fetcher):
    """Test MACD calculation."""
    ticker = "TEST"
    as_of = datetime(2024, 11, 8)

    result = await calculate_macd(ticker, as_of, mock_data_fetcher)

    assert result is not None
    assert isinstance(result, dict)
    assert 'macd' in result
    assert 'signal' in result
    assert 'histogram' in result
    assert all(isinstance(v, float) for v in result.values())


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_return_known_values():
    """Test return calculation with known expected values."""
    # Create data with known prices
    dates = pd.date_range(end=datetime(2024, 11, 8), periods=10, freq='D')
    df = pd.DataFrame({
        'Open': [100] * 10,
        'High': [105] * 10,
        'Low': [95] * 10,
        'Close': [100, 102, 104, 103, 105, 107, 106, 108, 110, 110],  # 10% gain over 9 days
        'Volume': [1000000] * 10,
    }, index=dates)

    async def known_fetcher(ticker: str, start: datetime, end: datetime):
        mask = (df.index >= start) & (df.index <= end)
        return df[mask].copy()

    # Calculate 5-day return
    # Price now = 110, Price 5 days ago = 105
    # Expected return = (110 - 105) / 105 = 0.0476 (4.76%)
    result = await calculate_return("TEST", 5, datetime(2024, 11, 8), known_fetcher)

    assert result is not None
    assert abs(result - 0.0476) < 0.01  # Within 1% tolerance
