"""
Market Data Price Fetcher

실시간 주식 가격 데이터 가져오기

Supports:
- Yahoo Finance (무료, 제한 없음)
- Alpha Vantage (무료 500 calls/day)
- IEX Cloud (무료 50k calls/month)

Primary: Yahoo Finance (yfinance)
Fallback: Alpha Vantage

Usage:
    from backend.market_data.price_fetcher import get_current_price, get_multiple_prices

    # Single ticker
    price = get_current_price("AAPL")

    # Multiple tickers
    prices = get_multiple_prices(["AAPL", "MSFT", "NVDA"])
"""

import yfinance as yf
import requests
import os
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PriceFetcher:
    """
    Price fetcher with multiple data sources

    Priority:
    1. Yahoo Finance (primary, free)
    2. Alpha Vantage (fallback, 500 calls/day)
    3. Cache (1-minute cache)
    """

    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.cache: Dict[str, tuple] = {}  # {ticker: (price, timestamp)}
        self.cache_duration = 60  # seconds

    def get_cached_price(self, ticker: str) -> Optional[float]:
        """Get price from cache if not expired"""
        if ticker in self.cache:
            price, timestamp = self.cache[ticker]
            age = (datetime.now() - timestamp).total_seconds()

            if age < self.cache_duration:
                logger.debug(f"Cache hit for {ticker}: ${price:.2f} (age: {age:.1f}s)")
                return price

        return None

    def set_cache(self, ticker: str, price: float):
        """Set price in cache"""
        self.cache[ticker] = (price, datetime.now())

    def get_price_yahoo(self, ticker: str) -> Optional[float]:
        """
        Get current price from Yahoo Finance

        Returns:
            float: Current price or None if failed
        """
        try:
            stock = yf.Ticker(ticker)

            # Try to get current price from info
            info = stock.info

            # Try different price fields
            price = (
                info.get('currentPrice') or
                info.get('regularMarketPrice') or
                info.get('previousClose')
            )

            if price and price > 0:
                logger.debug(f"Yahoo Finance: {ticker} = ${price:.2f}")
                return float(price)

            # Fallback: Get latest close from history
            hist = stock.history(period='1d')
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                logger.debug(f"Yahoo Finance (history): {ticker} = ${price:.2f}")
                return float(price)

            logger.warning(f"Yahoo Finance: No price data for {ticker}")
            return None

        except Exception as e:
            logger.error(f"Yahoo Finance error for {ticker}: {e}")
            return None

    def get_price_alpha_vantage(self, ticker: str) -> Optional[float]:
        """
        Get current price from Alpha Vantage

        Requires: ALPHA_VANTAGE_API_KEY in .env

        Returns:
            float: Current price or None if failed
        """
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None

        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': ticker,
                'apikey': self.alpha_vantage_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                price = float(data['Global Quote']['05. price'])
                logger.debug(f"Alpha Vantage: {ticker} = ${price:.2f}")
                return price

            logger.warning(f"Alpha Vantage: No price data for {ticker}")
            return None

        except Exception as e:
            logger.error(f"Alpha Vantage error for {ticker}: {e}")
            return None

    def get_current_price(self, ticker: str, use_cache: bool = True) -> Optional[float]:
        """
        Get current price for a ticker

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            use_cache: Use cached price if available (default: True)

        Returns:
            float: Current price or None if all sources failed
        """
        # Check cache first
        if use_cache:
            cached_price = self.get_cached_price(ticker)
            if cached_price is not None:
                return cached_price

        # Try Yahoo Finance
        price = self.get_price_yahoo(ticker)

        # Fallback to Alpha Vantage
        if price is None:
            logger.info(f"Yahoo Finance failed for {ticker}, trying Alpha Vantage...")
            price = self.get_price_alpha_vantage(ticker)

        # Cache the result
        if price is not None:
            self.set_cache(ticker, price)
            logger.info(f"✓ {ticker}: ${price:.2f}")
        else:
            logger.error(f"✗ {ticker}: Failed to fetch price from all sources")

        return price

    def get_multiple_prices(
        self,
        tickers: List[str],
        use_cache: bool = True
    ) -> Dict[str, Optional[float]]:
        """
        Get current prices for multiple tickers

        Args:
            tickers: List of stock tickers
            use_cache: Use cached prices if available

        Returns:
            dict: {ticker: price} or {ticker: None} if failed
        """
        results = {}

        for ticker in tickers:
            results[ticker] = self.get_current_price(ticker, use_cache=use_cache)

        return results

    def get_price_history(
        self,
        ticker: str,
        period: str = "1mo"
    ) -> Optional[Dict]:
        """
        Get historical price data

        Args:
            ticker: Stock ticker
            period: Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

        Returns:
            dict: {
                'dates': [...],
                'open': [...],
                'high': [...],
                'low': [...],
                'close': [...],
                'volume': [...]
            }
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)

            if hist.empty:
                return None

            return {
                'dates': hist.index.tolist(),
                'open': hist['Open'].tolist(),
                'high': hist['High'].tolist(),
                'low': hist['Low'].tolist(),
                'close': hist['Close'].tolist(),
                'volume': hist['Volume'].tolist()
            }

        except Exception as e:
            logger.error(f"Failed to get history for {ticker}: {e}")
            return None


# Global singleton instance
_price_fetcher: Optional[PriceFetcher] = None


def get_price_fetcher() -> PriceFetcher:
    """Get global PriceFetcher instance"""
    global _price_fetcher
    if _price_fetcher is None:
        _price_fetcher = PriceFetcher()
    return _price_fetcher


# Convenience functions
def get_current_price(ticker: str, use_cache: bool = True) -> Optional[float]:
    """Get current price for a ticker"""
    return get_price_fetcher().get_current_price(ticker, use_cache=use_cache)


def get_multiple_prices(tickers: List[str], use_cache: bool = True) -> Dict[str, Optional[float]]:
    """Get current prices for multiple tickers"""
    return get_price_fetcher().get_multiple_prices(tickers, use_cache=use_cache)


def get_price_history(ticker: str, period: str = "1mo") -> Optional[Dict]:
    """Get historical price data"""
    return get_price_fetcher().get_price_history(ticker, period=period)


# ============================================
# Demo & Testing
# ============================================

def demo():
    """Demo price fetching"""
    print("=" * 80)
    print("Market Data Price Fetcher Demo")
    print("=" * 80)

    # Single ticker
    print("\n[Test 1] Single ticker (AAPL)")
    price = get_current_price("AAPL")
    if price:
        print(f"✓ AAPL: ${price:.2f}")
    else:
        print("✗ Failed to fetch AAPL price")

    # Multiple tickers
    print("\n[Test 2] Multiple tickers")
    tickers = ["AAPL", "MSFT", "NVDA", "TSM", "AMD"]
    prices = get_multiple_prices(tickers)

    print("\nResults:")
    for ticker, price in prices.items():
        if price:
            print(f"  ✓ {ticker:6} ${price:8.2f}")
        else:
            print(f"  ✗ {ticker:6} Failed")

    # Cache test
    print("\n[Test 3] Cache test (should be instant)")
    import time
    start = time.time()
    price2 = get_current_price("AAPL")
    elapsed = time.time() - start
    print(f"✓ AAPL (cached): ${price2:.2f} ({elapsed*1000:.1f}ms)")

    # History
    print("\n[Test 4] Price history (1 month)")
    history = get_price_history("AAPL", period="1mo")
    if history:
        print(f"✓ Got {len(history['dates'])} days of data")
        print(f"  Latest close: ${history['close'][-1]:.2f}")
        print(f"  Month high: ${max(history['high']):.2f}")
        print(f"  Month low: ${min(history['low']):.2f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    demo()
