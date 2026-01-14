"""
Cache Layer Abstraction for Feature Store.

Provides:
- CacheLayer: Abstract interface for caching
- RedisCache: In-memory cache (< 5ms latency)
- TimescaleCache: Persistent cache (< 100ms latency)
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

# Optional asyncpg import (only needed for TimescaleDB)
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None

logger = logging.getLogger(__name__)


class CacheLayer(ABC):
    """
    Abstract interface for cache implementations.

    All cache layers must implement: get, set, exists, delete.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Retrieve value by key. Returns None if not found."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> None:
        """Store key-value pair with TTL (time-to-live in seconds)."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connections and cleanup resources."""
        pass


class RedisCache(CacheLayer):
    """
    Redis-based in-memory cache.

    Features:
    - < 5ms latency (p99)
    - Connection pooling (max 50 connections)
    - Automatic reconnection on failure
    - LRU eviction policy (maxmemory-policy=allkeys-lru)

    Key Schema:
        feature:{ticker}:{feature_name}:{as_of_date}
        Example: feature:AAPL:ret_5d:2024-11-08
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
    ):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connection pool size
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout in seconds
        """
        # Check environment variable first (for Docker/production deployments)
        import os
        redis_url = os.environ.get("REDIS_URL", redis_url)
        self.redis_url = redis_url
        self.pool = ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=True,  # Automatically decode bytes to str
        )
        self._client: Optional[redis.Redis] = None
        logger.info(f"RedisCache initialized with URL: {redis_url}")

    async def _get_client(self) -> redis.Redis:
        """Lazy initialization of Redis client."""
        if self._client is None:
            self._client = redis.Redis(connection_pool=self.pool)
            # Test connection
            await self._client.ping()
            logger.info("Redis client connected successfully")
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """Retrieve value from Redis. Soft fail on error."""
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value:
                logger.debug(f"Redis cache HIT: {key}")
            else:
                logger.debug(f"Redis cache MISS: {key}")
            return value
        except Exception as e:
            logger.warning(f"Redis get error for key {key} (Soft Fail): {e}")
            return None

    async def set(self, key: str, value: str, ttl: int) -> None:
        """Store key-value in Redis with TTL. Soft fail on error."""
        try:
            client = await self._get_client()
            await client.setex(key, ttl, value)
            logger.debug(f"Redis set: {key} (TTL={ttl}s)")
        except Exception as e:
            logger.warning(f"Redis set error for key {key} (Soft Fail): {e}")

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis. Soft fail on error."""
        try:
            client = await self._get_client()
            return bool(await client.exists(key))
        except Exception as e:
            logger.warning(f"Redis exists error for key {key} (Soft Fail): {e}")
            return False

    async def delete(self, key: str) -> None:
        """Delete key from Redis. Soft fail on error."""
        try:
            client = await self._get_client()
            await client.delete(key)
            logger.debug(f"Redis delete: {key}")
        except Exception as e:
            logger.warning(f"Redis delete error for key {key} (Soft Fail): {e}")

    async def close(self) -> None:
        """Close Redis connection pool."""
        if self._client:
            await self._client.close()
            await self.pool.disconnect()
            logger.info("Redis client closed")


class TimescaleCache(CacheLayer):
    """
    TimescaleDB-based persistent cache.

    Features:
    - < 100ms latency (p99)
    - Point-in-time queries (for backtesting)
    - Hypertable for time-series optimization
    - Connection pooling (5-20 connections)

    Schema:
        CREATE TABLE features (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(20) NOT NULL,
            feature_name VARCHAR(50) NOT NULL,
            value DOUBLE PRECISION,
            as_of_timestamp TIMESTAMPTZ NOT NULL,
            calculated_at TIMESTAMPTZ NOT NULL,
            version INTEGER DEFAULT 1,
            metadata JSONB,
            UNIQUE(ticker, feature_name, as_of_timestamp, version)
        );
        SELECT create_hypertable('features', 'as_of_timestamp');
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "ai_trading",
        user: str = "postgres",
        password: str = "postgres",
        min_pool_size: int = 5,
        max_pool_size: int = 20,
    ):
        """
        Initialize TimescaleDB cache.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_pool_size: Minimum connection pool size
            max_pool_size: Maximum connection pool size
        """
        if not ASYNCPG_AVAILABLE:
            logger.warning(
                "asyncpg not available - TimescaleDB caching disabled. "
                "Install asyncpg to enable TimescaleDB support."
            )

        # Check environment variables first (for Docker/production deployments)
        import os
        self.host = os.environ.get("TIMESCALE_HOST", host)
        self.port = int(os.environ.get("TIMESCALE_PORT", port))
        self.database = os.environ.get("TIMESCALE_DATABASE", database)
        self.user = os.environ.get("TIMESCALE_USER", user)
        self.password = os.environ.get("TIMESCALE_PASSWORD", password)
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self._pool = None
        logger.info(f"TimescaleCache initialized for {self.host}:{self.port}/{self.database}")

    async def _get_pool(self):
        """Lazy initialization of connection pool."""
        if not ASYNCPG_AVAILABLE:
            return None

        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size,
            )
            logger.info("TimescaleDB connection pool created")
        return self._pool

    def _parse_key(self, key: str) -> tuple[str, str, str]:
        """
        Parse Redis-style key to extract ticker, feature_name, as_of_date.

        Key format: feature:{ticker}:{feature_name}:{as_of_date}
        Example: feature:AAPL:ret_5d:2024-11-08 -> ("AAPL", "ret_5d", "2024-11-08")
        """
        parts = key.split(":")
        if len(parts) != 4 or parts[0] != "feature":
            raise ValueError(f"Invalid key format: {key}")
        return parts[1], parts[2], parts[3]

    def _normalize_date(self, date_input: str | datetime) -> datetime:
        """
        Normalize date input to datetime object.
        
        🔧 BUG FIX: Ensures as_of_date is always a datetime object
        
        Args:
            date_input: Either ISO date string ("2025-11-08") or datetime object
            
        Returns:
            datetime object
        """
        if isinstance(date_input, datetime):
            return date_input
        elif isinstance(date_input, str):
            # Handle ISO format date strings
            try:
                return datetime.fromisoformat(date_input.replace("Z", "+00:00"))
            except ValueError:
                # Try parsing just the date part
                return datetime.strptime(date_input, "%Y-%m-%d")
        else:
            raise ValueError(f"Invalid date input type: {type(date_input)}")

    async def get(self, key: str) -> Optional[str]:
        """
        Retrieve feature value from TimescaleDB.

        Returns JSON-serialized Feature object or None if not found.
        """
        try:
            ticker, feature_name, as_of_date_str = self._parse_key(key)
            pool = await self._get_pool()
            if pool is None:
                return None

            # 🔧 BUG FIX: Convert string to datetime
            as_of_date = self._normalize_date(as_of_date_str)

            query = """
                SELECT value, calculated_at, version, metadata
                FROM features
                WHERE ticker = $1
                  AND feature_name = $2
                  AND as_of_timestamp::date = $3::date
                ORDER BY calculated_at DESC
                LIMIT 1
            """
            row = await pool.fetchrow(query, ticker, feature_name, as_of_date)

            if row:
                logger.debug(f"TimescaleDB cache HIT: {key}")
                result = {
                    "value": row["value"],
                    "calculated_at": row["calculated_at"].isoformat(),
                    "version": row["version"],
                    "metadata": row["metadata"],
                }
                return json.dumps(result)
            else:
                logger.debug(f"TimescaleDB cache MISS: {key}")
                return None

        except Exception as e:
            # Downgrade to warning for connection issues
            logger.warning(f"TimescaleDB get error for key {key} (Soft Fail): {e}")
            return None

    async def set(self, key: str, value: str, ttl: int) -> None:
        """
        Store feature value in TimescaleDB.

        Note: TTL is ignored (TimescaleDB is persistent).
        Value should be JSON-serialized Feature object.
        """
        try:
            ticker, feature_name, as_of_date_str = self._parse_key(key)
            pool = await self._get_pool()
            if pool is None:
                return

            # 🔧 BUG FIX: Convert string to datetime
            as_of_date = self._normalize_date(as_of_date_str)

            # Parse value JSON
            data = json.loads(value)
            feature_value = data.get("value")
            calculated_at = datetime.fromisoformat(data.get("calculated_at"))
            version = data.get("version", 1)
            metadata = data.get("metadata")

            query = """
                INSERT INTO features (ticker, feature_name, value, as_of_timestamp, calculated_at, version, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (ticker, feature_name, as_of_timestamp, version)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    calculated_at = EXCLUDED.calculated_at,
                    metadata = EXCLUDED.metadata
            """
            await pool.execute(
                query,
                ticker,
                feature_name,
                feature_value,
                as_of_date,
                calculated_at,
                version,
                metadata,
            )
            logger.debug(f"TimescaleDB set: {key}")

        except Exception as e:
            logger.warning(f"TimescaleDB set error for key {key} (Soft Fail): {e}")

    async def exists(self, key: str) -> bool:
        """Check if feature exists in TimescaleDB."""
        try:
            ticker, feature_name, as_of_date_str = self._parse_key(key)
            pool = await self._get_pool()
            if pool is None:
                return False

            # 🔧 BUG FIX: Convert string to datetime
            as_of_date = self._normalize_date(as_of_date_str)

            query = """
                SELECT 1 FROM features
                WHERE ticker = $1
                  AND feature_name = $2
                  AND as_of_timestamp::date = $3::date
                LIMIT 1
            """
            row = await pool.fetchrow(query, ticker, feature_name, as_of_date)
            return row is not None

        except Exception as e:
            logger.warning(f"TimescaleDB exists error for key {key} (Soft Fail): {e}")
            return False

    async def delete(self, key: str) -> None:
        """Delete feature from TimescaleDB."""
        try:
            ticker, feature_name, as_of_date_str = self._parse_key(key)
            pool = await self._get_pool()
            if pool is None:
                return

            # 🔧 BUG FIX: Convert string to datetime
            as_of_date = self._normalize_date(as_of_date_str)

            query = """
                DELETE FROM features
                WHERE ticker = $1
                  AND feature_name = $2
                  AND as_of_timestamp::date = $3::date
            """
            await pool.execute(query, ticker, feature_name, as_of_date)
            logger.debug(f"TimescaleDB delete: {key}")

        except Exception as e:
            logger.warning(f"TimescaleDB delete error for key {key} (Soft Fail): {e}")

    async def close(self) -> None:
        """Close TimescaleDB connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("TimescaleDB connection pool closed")