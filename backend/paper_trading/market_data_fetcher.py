"""
Market Data Fetcher - Real-time Market Data

Fetches real-time market data for paper trading simulation.

Features:
- Real-time stock quotes using yfinance
- Multiple ticker support
- Price caching with TTL
- Market hours checking
- Fallback to last known price

Author: AI Trading System Team
Date: 2025-11-15
"""

import asyncio
import logging
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
from dataclasses import dataclass
import yfinance as yf
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class MarketQuote:
    """Real-time market quote."""
    ticker: str
    price: float
    timestamp: datetime
    volume: int = 0
    bid: float = 0.0
    ask: float = 0.0
    day_high: float = 0.0
    day_low: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "volume": self.volume,
            "bid": self.bid,
            "ask": self.ask,
            "day_high": self.day_high,
            "day_low": self.day_low,
        }


class MarketDataFetcher:
    """
    Fetches real-time market data for paper trading.

    Features:
    - Real-time quotes
    - Price caching
    - Market hours awareness
    - Batch fetching
    """

    def __init__(self, cache_ttl_seconds: int = 15):
        """
        Initialize market data fetcher.

        Args:
            cache_ttl_seconds: Cache time-to-live for quotes
        """
        self.cache_ttl = cache_ttl_seconds
        self._price_cache: Dict[str, MarketQuote] = {}
        self._ticker_objects: Dict[str, yf.Ticker] = {}

        logger.info(f"Market Data Fetcher initialized (cache TTL: {cache_ttl_seconds}s)")

    def _is_market_hours(self) -> bool:
        """
        Check if market is currently open.

        US market hours: 9:30 AM - 4:00 PM ET (Mon-Fri)
        For simplicity, we'll allow paper trading 24/7 but log warnings.
        """
        now = datetime.now()

        # Check if weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            logger.debug("Weekend - market closed")
            return False

        # Check time (simplified - ignoring timezone conversion)
        market_open = dt_time(9, 30)
        market_close = dt_time(16, 0)
        current_time = now.time()

        if market_open <= current_time <= market_close:
            return True
        else:
            logger.debug("Outside market hours")
            return False

    async def get_quote(self, ticker: str, use_cache: bool = True) -> Optional[MarketQuote]:
        """
        Get real-time quote for a ticker.

        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use cached price if available

        Returns:
            MarketQuote or None if failed
        """
        # Check cache first
        if use_cache and ticker in self._price_cache:
            cached_quote = self._price_cache[ticker]
            age = (datetime.now() - cached_quote.timestamp).total_seconds()

            if age < self.cache_ttl:
                logger.debug(f"Using cached price for {ticker}: ${cached_quote.price:.2f}")
                return cached_quote

        # Fetch fresh data
        try:
            # Get or create ticker object
            if ticker not in self._ticker_objects:
                self._ticker_objects[ticker] = yf.Ticker(ticker)

            ticker_obj = self._ticker_objects[ticker]

            # Fetch current data
            # Use fast_info for quick access to current price
            try:
                info = ticker_obj.fast_info
                current_price = info.last_price
            except:
                # Fallback to regular info
                info = ticker_obj.info
                current_price = info.get('regularMarketPrice') or info.get('currentPrice', 0.0)

            if current_price == 0.0:
                logger.error(f"Failed to get valid price for {ticker}")
                return None

            # Create quote
            quote = MarketQuote(
                ticker=ticker,
                price=current_price,
                timestamp=datetime.now(),
                volume=getattr(info, 'last_volume', 0) if hasattr(info, 'last_volume') else 0,
            )

            # Update cache
            self._price_cache[ticker] = quote

            logger.info(f"Fetched quote for {ticker}: ${current_price:.2f}")
            return quote

        except Exception as e:
            logger.error(f"Failed to fetch quote for {ticker}: {e}")

            # Return cached price if available (even if expired)
            if ticker in self._price_cache:
                logger.warning(f"Using stale cached price for {ticker}")
                return self._price_cache[ticker]

            return None

    async def get_quotes_batch(self, tickers: List[str]) -> Dict[str, MarketQuote]:
        """
        Get quotes for multiple tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping ticker to MarketQuote
        """
        quotes = {}

        # Fetch concurrently
        tasks = [self.get_quote(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {ticker}: {result}")
            elif result is not None:
                quotes[ticker] = result

        logger.info(f"Fetched {len(quotes)}/{len(tickers)} quotes")
        return quotes

    def get_cached_price(self, ticker: str) -> Optional[float]:
        """
        Get cached price without fetching.

        Args:
            ticker: Ticker symbol

        Returns:
            Cached price or None
        """
        if ticker in self._price_cache:
            return self._price_cache[ticker].price
        return None

    def clear_cache(self, ticker: Optional[str] = None):
        """
        Clear price cache.

        Args:
            ticker: Specific ticker to clear, or None to clear all
        """
        if ticker:
            if ticker in self._price_cache:
                del self._price_cache[ticker]
                logger.debug(f"Cleared cache for {ticker}")
        else:
            self._price_cache.clear()
            logger.debug("Cleared all price cache")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        now = datetime.now()

        fresh_count = 0
        stale_count = 0

        for quote in self._price_cache.values():
            age = (now - quote.timestamp).total_seconds()
            if age < self.cache_ttl:
                fresh_count += 1
            else:
                stale_count += 1

        return {
            "total_cached": len(self._price_cache),
            "fresh": fresh_count,
            "stale": stale_count,
            "cache_ttl_seconds": self.cache_ttl,
        }


# =============================================================================
# Historical Data Fetcher (for backtesting reference)
# =============================================================================

async def fetch_historical_data(
    ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "1d",
) -> Optional[Dict]:
    """
    Fetch historical data for a ticker.

    Args:
        ticker: Stock ticker
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval (1d, 1h, etc.)

    Returns:
        Dictionary with historical data
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(start=start_date, end=end_date, interval=interval)

        if hist.empty:
            logger.error(f"No historical data for {ticker}")
            return None

        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "data": hist.to_dict('records'),
        }

    except Exception as e:
        logger.error(f"Failed to fetch historical data for {ticker}: {e}")
        return None
