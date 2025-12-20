"""
Redis Cache Configuration for AI Trading System

Provides caching for:
- Real-time stock prices (10s TTL)
- Macro indicators (1h TTL)
- API responses (configurable TTL)
"""

import os
import json
import logging
from typing import Optional, Any, Dict
from datetime import timedelta

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


# Redis connection settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# TTL settings (seconds)
TTL_REALTIME_PRICE = 10      # 실시간 시세
TTL_MACRO_DATA = 3600        # 매크로 데이터 (1시간)
TTL_SECTOR_DATA = 86400      # 섹터 데이터 (24시간)
TTL_NEWS_CACHE = 1800        # 뉴스 캐시 (30분)
TTL_API_RESPONSE = 300       # API 응답 (5분)


class RedisCache:
    """
    Async Redis cache manager.
    
    Usage:
        cache = RedisCache()
        await cache.connect()
        await cache.set("key", {"data": "value"}, ttl=60)
        data = await cache.get("key")
    """
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not installed. Using in-memory fallback.")
            return False
        
        try:
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
            )
            await self.client.ping()
            self._connected = True
            logger.info(f"Redis connected: {REDIS_HOST}:{REDIS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self._connected = False
            logger.info("Redis disconnected")
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._connected:
            return None
        
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = TTL_API_RESPONSE
    ) -> bool:
        """Set value in cache with TTL."""
        if not self._connected:
            return False
        
        try:
            await self.client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._connected:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    async def get_price(self, ticker: str) -> Optional[Dict]:
        """Get cached stock price."""
        return await self.get(f"price:{ticker}")
    
    async def set_price(self, ticker: str, price_data: Dict) -> bool:
        """Cache stock price."""
        return await self.set(f"price:{ticker}", price_data, TTL_REALTIME_PRICE)
    
    async def get_macro(self, key: str) -> Optional[Dict]:
        """Get cached macro data."""
        return await self.get(f"macro:{key}")
    
    async def set_macro(self, key: str, data: Dict) -> bool:
        """Cache macro data."""
        return await self.set(f"macro:{key}", data, TTL_MACRO_DATA)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self._connected:
            return 0
        
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis INVALIDATE error: {e}")
            return 0


# In-memory fallback cache
class InMemoryCache:
    """Simple in-memory cache fallback when Redis unavailable."""
    
    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self._connected = True
    
    async def connect(self) -> bool:
        return True
    
    async def disconnect(self):
        self._cache.clear()
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def get(self, key: str) -> Optional[Any]:
        import time
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry > time.time():
                return value
            del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = TTL_API_RESPONSE) -> bool:
        import time
        self._cache[key] = (value, time.time() + ttl)
        return True
    
    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
        return True
    
    async def get_price(self, ticker: str) -> Optional[Dict]:
        return await self.get(f"price:{ticker}")
    
    async def set_price(self, ticker: str, price_data: Dict) -> bool:
        return await self.set(f"price:{ticker}", price_data, TTL_REALTIME_PRICE)
    
    async def get_macro(self, key: str) -> Optional[Dict]:
        return await self.get(f"macro:{key}")
    
    async def set_macro(self, key: str, data: Dict) -> bool:
        return await self.set(f"macro:{key}", data, TTL_MACRO_DATA)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        # Simple implementation - delete exact match only
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._cache[k]
            return len(keys_to_delete)
        return 0


# Global cache instance
_cache: Optional[RedisCache | InMemoryCache] = None


async def get_cache() -> RedisCache | InMemoryCache:
    """Get or create cache instance."""
    global _cache
    
    if _cache is None:
        _cache = RedisCache()
        connected = await _cache.connect()
        
        if not connected:
            logger.warning("Falling back to in-memory cache")
            _cache = InMemoryCache()
            await _cache.connect()
    
    return _cache
