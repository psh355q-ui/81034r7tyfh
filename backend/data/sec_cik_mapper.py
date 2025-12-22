"""
SEC CIK to Ticker Mapper

Maps SEC Central Index Key (CIK) numbers to stock ticker symbols.

SEC provides a JSON file with all company tickers:
https://www.sec.gov/files/company_tickers.json

Format:
{
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
    ...
}

Features:
- Automatic caching (Redis + memory)
- Daily refresh from SEC
- Bidirectional mapping (CIK <-> Ticker)
- Fuzzy company name matching

Author: AI Trading System
Date: 2025-12-22
"""

import asyncio
import aiohttp
import logging
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    from backend.config.settings import settings
    import redis.asyncio as aioredis
except ImportError:
    # Mock for standalone testing
    class MockSettings:
        REDIS_HOST = "localhost"
        REDIS_PORT = 6379
    settings = MockSettings()
    aioredis = None


logger = logging.getLogger(__name__)


@dataclass
class CompanyInfo:
    """Company information from SEC."""
    cik: str  # Zero-padded to 10 digits
    ticker: str
    name: str

    def to_dict(self) -> Dict:
        return {
            'cik': self.cik,
            'ticker': self.ticker,
            'name': self.name
        }


class SECCIKMapper:
    """
    SEC CIK to Ticker mapping service.

    Features:
    - Caches mappings in Redis (24h TTL)
    - Falls back to memory cache if Redis unavailable
    - Auto-refreshes from SEC daily
    """

    # SEC company tickers JSON (updated daily)
    SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

    # Cache keys
    REDIS_KEY_CIK_TO_TICKER = "sec:cik_to_ticker"
    REDIS_KEY_TICKER_TO_CIK = "sec:ticker_to_cik"
    REDIS_KEY_LAST_UPDATE = "sec:mapping_last_update"
    CACHE_TTL = 86400  # 24 hours

    def __init__(self, use_redis: bool = True):
        """
        Initialize CIK mapper.

        Args:
            use_redis: Use Redis for caching (falls back to memory if unavailable)
        """
        self.logger = logging.getLogger(__name__)
        self.use_redis = use_redis and aioredis is not None

        # Memory cache (fallback)
        self.cik_to_ticker: Dict[str, str] = {}
        self.ticker_to_cik: Dict[str, str] = {}
        self.cik_to_company: Dict[str, CompanyInfo] = {}
        self.last_update: Optional[datetime] = None

        # Redis client
        self.redis: Optional[aioredis.Redis] = None

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None

        # SEC requires User-Agent
        self.headers = {
            'User-Agent': 'AI Trading System (contact@example.com)',
            'Accept': 'application/json'
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self):
        """Initialize connections and load mappings."""
        # Initialize HTTP session
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)

        # Initialize Redis if enabled
        if self.use_redis:
            try:
                self.redis = await aioredis.from_url(
                    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                    decode_responses=True
                )
                await self.redis.ping()
                self.logger.info("✅ Redis connection established for SEC mapping")
            except Exception as e:
                self.logger.warning(f"⚠️ Redis unavailable, using memory cache: {e}")
                self.redis = None

        # Load mappings
        await self.load_mappings()

    async def close(self):
        """Close connections."""
        if self.session:
            await self.session.close()
            self.session = None

        if self.redis:
            await self.redis.close()
            self.redis = None

    async def load_mappings(self, force_refresh: bool = False):
        """
        Load CIK-to-ticker mappings.

        Priority:
        1. Redis cache (if available and fresh)
        2. Fetch from SEC
        3. Memory cache (fallback)

        Args:
            force_refresh: Force refresh from SEC
        """
        # Check if refresh needed
        if not force_refresh and self.last_update:
            age = datetime.now() - self.last_update
            if age < timedelta(hours=24):
                self.logger.info(f"📋 Using cached SEC mappings (age: {age.seconds // 3600}h)")
                return

        # Try loading from Redis
        if self.redis and not force_refresh:
            try:
                cached = await self.redis.hgetall(self.REDIS_KEY_CIK_TO_TICKER)
                if cached:
                    self.cik_to_ticker = cached

                    # Load reverse mapping
                    ticker_map = await self.redis.hgetall(self.REDIS_KEY_TICKER_TO_CIK)
                    self.ticker_to_cik = ticker_map

                    # Load last update time
                    last_update_str = await self.redis.get(self.REDIS_KEY_LAST_UPDATE)
                    if last_update_str:
                        self.last_update = datetime.fromisoformat(last_update_str)

                    self.logger.info(f"✅ Loaded {len(self.cik_to_ticker)} SEC mappings from Redis")
                    return
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to load from Redis: {e}")

        # Fetch from SEC
        await self.fetch_from_sec()

    async def fetch_from_sec(self):
        """Fetch company tickers from SEC."""
        try:
            self.logger.info(f"🌐 Fetching SEC company tickers from {self.SEC_TICKERS_URL}...")

            if not self.session:
                self.session = aiohttp.ClientSession(headers=self.headers)

            async with self.session.get(
                self.SEC_TICKERS_URL,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    self.logger.error(f"❌ SEC fetch failed: status {response.status}")
                    return

                data = await response.json()

            # Parse JSON
            # Format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}
            cik_to_ticker = {}
            ticker_to_cik = {}
            cik_to_company = {}

            for key, company in data.items():
                cik_raw = company.get('cik_str')
                ticker = company.get('ticker', '').upper()
                name = company.get('title', '')

                if not cik_raw or not ticker:
                    continue

                # Zero-pad CIK to 10 digits
                cik = str(cik_raw).zfill(10)

                cik_to_ticker[cik] = ticker
                ticker_to_cik[ticker] = cik
                cik_to_company[cik] = CompanyInfo(cik=cik, ticker=ticker, name=name)

            self.cik_to_ticker = cik_to_ticker
            self.ticker_to_cik = ticker_to_cik
            self.cik_to_company = cik_to_company
            self.last_update = datetime.now()

            self.logger.info(f"✅ Loaded {len(self.cik_to_ticker)} SEC company mappings")

            # Cache in Redis
            if self.redis:
                await self._cache_to_redis()

        except Exception as e:
            self.logger.error(f"❌ Failed to fetch from SEC: {e}")

    async def _cache_to_redis(self):
        """Cache mappings to Redis."""
        try:
            # Store CIK -> Ticker mapping
            if self.cik_to_ticker:
                await self.redis.delete(self.REDIS_KEY_CIK_TO_TICKER)
                await self.redis.hset(self.REDIS_KEY_CIK_TO_TICKER, mapping=self.cik_to_ticker)
                await self.redis.expire(self.REDIS_KEY_CIK_TO_TICKER, self.CACHE_TTL)

            # Store Ticker -> CIK mapping
            if self.ticker_to_cik:
                await self.redis.delete(self.REDIS_KEY_TICKER_TO_CIK)
                await self.redis.hset(self.REDIS_KEY_TICKER_TO_CIK, mapping=self.ticker_to_cik)
                await self.redis.expire(self.REDIS_KEY_TICKER_TO_CIK, self.CACHE_TTL)

            # Store last update time
            await self.redis.set(
                self.REDIS_KEY_LAST_UPDATE,
                self.last_update.isoformat(),
                ex=self.CACHE_TTL
            )

            self.logger.info(f"✅ Cached {len(self.cik_to_ticker)} mappings to Redis")

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to cache to Redis: {e}")

    async def cik_to_ticker_symbol(self, cik: str) -> Optional[str]:
        """
        Convert CIK to ticker symbol.

        Args:
            cik: CIK number (can be zero-padded or not)

        Returns:
            Ticker symbol (e.g., "AAPL") or None

        Examples:
            >>> await mapper.cik_to_ticker_symbol("0000320193")
            'AAPL'
            >>> await mapper.cik_to_ticker_symbol("320193")
            'AAPL'
        """
        # Ensure mappings loaded
        if not self.cik_to_ticker:
            await self.load_mappings()

        # Zero-pad CIK
        cik_padded = str(cik).zfill(10)

        return self.cik_to_ticker.get(cik_padded)

    async def ticker_to_cik_number(self, ticker: str) -> Optional[str]:
        """
        Convert ticker symbol to CIK.

        Args:
            ticker: Stock ticker (e.g., "AAPL")

        Returns:
            Zero-padded CIK (e.g., "0000320193") or None
        """
        # Ensure mappings loaded
        if not self.ticker_to_cik:
            await self.load_mappings()

        ticker_upper = ticker.upper()
        return self.ticker_to_cik.get(ticker_upper)

    async def get_company_info(self, cik: str) -> Optional[CompanyInfo]:
        """
        Get full company information by CIK.

        Args:
            cik: CIK number

        Returns:
            CompanyInfo with CIK, ticker, and name
        """
        # Ensure mappings loaded
        if not self.cik_to_company:
            await self.load_mappings()

        cik_padded = str(cik).zfill(10)
        return self.cik_to_company.get(cik_padded)

    async def search_by_name(self, company_name: str, fuzzy: bool = True) -> List[CompanyInfo]:
        """
        Search companies by name.

        Args:
            company_name: Company name to search
            fuzzy: Allow fuzzy matching

        Returns:
            List of matching CompanyInfo objects
        """
        # Ensure mappings loaded
        if not self.cik_to_company:
            await self.load_mappings()

        name_lower = company_name.lower()
        matches = []

        for company in self.cik_to_company.values():
            if fuzzy:
                # Fuzzy match: company name contains search term
                if name_lower in company.name.lower():
                    matches.append(company)
            else:
                # Exact match
                if company.name.lower() == name_lower:
                    matches.append(company)

        return matches

    def get_stats(self) -> Dict:
        """Get mapper statistics."""
        return {
            'total_mappings': len(self.cik_to_ticker),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'redis_enabled': self.redis is not None,
            'cache_age_hours': (
                (datetime.now() - self.last_update).total_seconds() / 3600
                if self.last_update else None
            )
        }


# Global singleton instance
_cik_mapper: Optional[SECCIKMapper] = None


async def get_cik_mapper() -> SECCIKMapper:
    """Get or create global CIK mapper instance."""
    global _cik_mapper

    if _cik_mapper is None:
        _cik_mapper = SECCIKMapper()
        await _cik_mapper.initialize()

    return _cik_mapper


# CLI for testing
if __name__ == "__main__":
    async def main():
        print("🧪 SEC CIK Mapper Test\n")

        async with SECCIKMapper() as mapper:
            # Test 1: CIK to ticker
            print("=" * 60)
            print("Test 1: CIK to Ticker")
            print("=" * 60)

            test_ciks = [
                ("0000320193", "Apple"),
                ("0000789019", "Microsoft"),
                ("0001018724", "Amazon"),
                ("0001652044", "Alphabet/Google"),
                ("0001318605", "Tesla")
            ]

            for cik, expected_company in test_ciks:
                ticker = await mapper.cik_to_ticker_symbol(cik)
                company = await mapper.get_company_info(cik)

                print(f"\nCIK: {cik}")
                print(f"  Ticker: {ticker}")
                if company:
                    print(f"  Company: {company.name}")

            # Test 2: Ticker to CIK
            print("\n" + "=" * 60)
            print("Test 2: Ticker to CIK")
            print("=" * 60)

            test_tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA"]

            for ticker in test_tickers:
                cik = await mapper.ticker_to_cik_number(ticker)
                print(f"\nTicker: {ticker}")
                print(f"  CIK: {cik}")

            # Test 3: Company name search
            print("\n" + "=" * 60)
            print("Test 3: Company Name Search")
            print("=" * 60)

            search_terms = ["Apple", "Microsoft", "Tesla"]

            for term in search_terms:
                matches = await mapper.search_by_name(term)
                print(f"\nSearch: '{term}'")
                print(f"  Found {len(matches)} matches:")
                for match in matches[:3]:  # Show first 3
                    print(f"    - {match.ticker}: {match.name}")

            # Stats
            print("\n" + "=" * 60)
            print("Mapper Statistics")
            print("=" * 60)
            stats = mapper.get_stats()
            for key, value in stats.items():
                print(f"  {key}: {value}")

    asyncio.run(main())
