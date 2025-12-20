"""
Yahoo Finance data collector.

Fetches OHLCV data from Yahoo Finance API (free, no API key required).
Includes caching and rate limiting.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class YahooFinanceCollector:
    """
    Collects OHLCV data from Yahoo Finance.

    Features:
    - Free API (no API key required)
    - 24-hour caching (reduce redundant calls)
    - Retry logic with exponential backoff
    - Rate limiting (2000 requests/hour)
    """

    def __init__(self, cache_ttl_hours: int = 24):
        """
        Initialize Yahoo Finance collector.

        Args:
            cache_ttl_hours: Cache TTL in hours (default 24)
        """
        self.cache_ttl_hours = cache_ttl_hours
        self._cache: dict[str, tuple[pd.DataFrame, datetime]] = {}
        self.request_count = 0
        self.request_limit_per_hour = 2000
        logger.info(f"YahooFinanceCollector initialized with {cache_ttl_hours}h cache TTL")

    def _get_cache_key(
        self, ticker: str, start: datetime, end: datetime, interval: str
    ) -> str:
        """Generate cache key."""
        return f"{ticker}:{start.date()}:{end.date()}:{interval}"

    def _is_cache_valid(self, cached_time: datetime) -> bool:
        """Check if cached data is still valid."""
        age = datetime.utcnow() - cached_time
        return age < timedelta(hours=self.cache_ttl_hours)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def fetch_ohlcv(
        self,
        ticker: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "005930.KS")
            start: Start date
            end: End date
            interval: Data interval (1d, 1h, 5m, etc.)

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
            None if fetch fails

        Example:
            >>> collector = YahooFinanceCollector()
            >>> df = await collector.fetch_ohlcv("AAPL", datetime(2024, 1, 1), datetime(2024, 11, 8))
            >>> df.head()
                           Open    High     Low   Close     Volume
            Date
            2024-01-01  185.00  187.50  184.50  186.75  50000000
        """
        # Check cache
        cache_key = self._get_cache_key(ticker, start, end, interval)
        if cache_key in self._cache:
            cached_df, cached_time = self._cache[cache_key]
            if self._is_cache_valid(cached_time):
                logger.debug(f"Cache HIT for {ticker} ({start.date()} to {end.date()})")
                return cached_df.copy()
            else:
                logger.debug(f"Cache EXPIRED for {ticker}")
                del self._cache[cache_key]

        # Check rate limit
        if self.request_count >= self.request_limit_per_hour:
            logger.warning(
                f"Rate limit reached ({self.request_limit_per_hour} req/hour). Returning None."
            )
            return None

        # Fetch from Yahoo Finance
        try:
            logger.info(
                f"Fetching {ticker} data from Yahoo Finance ({start.date()} to {end.date()})"
            )
            self.request_count += 1

            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start, end=end, interval=interval)

            if df is None or df.empty:
                logger.warning(f"No data returned for {ticker}")
                return None

            # Validate columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Missing required columns for {ticker}: {df.columns}")
                return None

            # Cache the result
            self._cache[cache_key] = (df.copy(), datetime.utcnow())
            logger.info(f"Fetched {len(df)} rows for {ticker}")

            return df

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None

    async def fetch_latest_price(self, ticker: str) -> Optional[float]:
        """
        Fetch latest closing price.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest closing price or None if unavailable
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            if price:
                logger.debug(f"Latest price for {ticker}: ${price}")
                return float(price)
            else:
                logger.warning(f"No latest price available for {ticker}")
                return None
        except Exception as e:
            logger.error(f"Error fetching latest price for {ticker}: {e}")
            return None

    async def fetch_info(self, ticker: str) -> Optional[dict]:
        """
        Fetch ticker info (fundamentals, metadata).

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with ticker info (sector, industry, marketCap, etc.)
            None if unavailable
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            logger.debug(f"Fetched info for {ticker}: {info.get('shortName', 'Unknown')}")
            return info
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear all cached data."""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {cache_size} cached entries")

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache_size, oldest_entry_age, etc.
        """
        if not self._cache:
            return {'cache_size': 0, 'oldest_entry_age_hours': 0}

        now = datetime.utcnow()
        oldest_age = max((now - cached_time).total_seconds() for _, cached_time in self._cache.values())

        return {
            'cache_size': len(self._cache),
            'oldest_entry_age_hours': oldest_age / 3600,
            'request_count': self.request_count,
        }
