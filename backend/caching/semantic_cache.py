"""
RedisVL Semantic Cache

Uses vector similarity to detect semantically similar queries
and return cached responses, eliminating duplicate API calls.

Key Features:
- Vector-based similarity (cosine distance)
- Configurable distance threshold
- TTL-based expiration
- Cost tracking
- Hit rate metrics

Reference: https://docs.redisvl.com/
"""

import logging
import os
import hashlib
from typing import Optional, Dict, Any, Callable
from datetime import datetime

try:
    from redisvl.extensions.llmcache import SemanticCache
    REDISVL_AVAILABLE = True
except ImportError:
    REDISVL_AVAILABLE = False
    SemanticCache = None

logger = logging.getLogger(__name__)


class TradingSemanticCache:
    """
    Semantic caching for trading queries using RedisVL
    
    Prevents duplicate LLM calls for similar questions by using
    vector similarity matching.
    
    Example:
        >>> cache = TradingSemanticCache()
        >>> 
        >>> # First call - cache miss
        >>> result = await cache.get_or_generate(
        ...     "What are the risks in AAPL's latest 10-K?",
        ...     generate_func=lambda q: analyze_sec(q)
        ... )
        >>> # result['source'] == 'llm', result['cost'] == 0.05
        >>> 
        >>> # Similar question - cache hit!
        >>> result2 = await cache.get_or_generate(
        ...     "Tell me about Apple's risk factors in their 10-K",
        ...     generate_func=lambda q: analyze_sec(q)
        ... )
        >>> # result2['source'] == 'cache', result2['cost'] == 0
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        distance_threshold: float = 0.1,
        ttl: int = 3600,
        cache_name: str = "trading_intelligence"
    ):
        """
        Initialize semantic cache
        
        Args:
            redis_url: Redis connection URL (default: from env or localhost)
            distance_threshold: Max cosine distance for cache hit (0.1 = very similar)
                - 0.0 = exact match only
                - 0.1 = very similar (recommended for trading)
                - 0.2 = moderately similar
                - 0.3+ = loose matching (risky)
            ttl: Cache TTL in seconds (default: 1 hour)
            cache_name: Cache identifier
        """
        if not REDISVL_AVAILABLE:
            logger.warning("⚠️  RedisVL not available, caching disabled")
            self.cache = None
            self._hits = 0
            self._misses = 0
            self._total_saved = 0.0
            return
        
        # Get Redis URL from env or use default
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.distance_threshold = distance_threshold
        self.ttl = ttl
        self.cache_name = cache_name
        
        # Metrics
        self._hits = 0
        self._misses = 0
        self._total_saved = 0.0
        
        try:
            logger.info(f"🔗 Connecting to Redis: {self.redis_url}")
            
            self.cache = SemanticCache(
                name=cache_name,
                redis_url=self.redis_url,
                distance_threshold=distance_threshold,
                ttl=ttl
            )
            
            logger.info(
                f"✅ Semantic cache initialized: "
                f"threshold={distance_threshold}, ttl={ttl}s"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis semantic cache: {e}")
            logger.warning("⚠️ Caching disabled - all queries will be fresh")
            self.cache = None
    
    def is_enabled(self) -> bool:
        """Check if caching is enabled"""
        return self.cache is not None
    
    async def get_or_generate(
        self,
        query: str,
        generate_func: Callable,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get cached response or generate new one
        
        Args:
            query: User query text
            generate_func: Async function to call on cache miss
                Should return the response dict
            metadata: Optional metadata to store with cache entry
        
        Returns:
            {
                'response': <generated or cached response>,
                'source': 'cache' | 'llm',
                'cost': <API cost in USD>,
                'cached_at': <timestamp if from cache>,
                'distance': <similarity distance if from cache>
            }
        """
        if not self.is_enabled():
            # Caching disabled - always generate fresh
            response = await generate_func(query)
            return {
                'response': response,
                'source': 'llm',
                'cost': self._estimate_cost(response),
                'cache_disabled': True
            }
        
        # Try cache first
        try:
            cached = self.cache.check(prompt=query)
            
            if cached:
                # Cache HIT
                self._hits += 1
                
                # Extract cached data
                cached_response = cached[0].get('response') if isinstance(cached, list) else cached.get('response')
                distance = cached[0].get('distance', 0.0) if isinstance(cached, list) else 0.0
                
                logger.info(
                    f"💚 Cache HIT (distance: {distance:.3f}): '{query[:50]}...'"
                )
                
                return {
                    'response': cached_response,
                    'source': 'cache',
                    'cost': 0.0,  # No API cost!
                    'cached_at': datetime.now().isoformat(),
                    'distance': distance,
                    'hit_rate': self.get_hit_rate()
                }
            
        except Exception as e:
            logger.warning(f"⚠️ Cache check failed: {e}, proceeding to generate")
        
        # Cache MISS - generate fresh response
        self._misses += 1
        logger.info(f"🔴 Cache MISS: '{query[:50]}...'")
        
        try:
            response = await generate_func(query)
            cost = self._estimate_cost(response)
            
            # Store in cache for future hits
            try:
                self.cache.store(
                    prompt=query,
                    response=response,
                    metadata=metadata or {}
                )
                logger.debug(f"💾 Stored in cache: '{query[:50]}...'")
            except Exception as e:
                logger.warning(f"⚠️ Failed to store in cache: {e}")
            
            return {
                'response': response,
                'source': 'llm',
                'cost': cost,
                'hit_rate': self.get_hit_rate()
            }
            
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            raise
    
    def clear(self):
        """Clear all cached entries"""
        if not self.is_enabled():
            return
        
        try:
            self.cache.clear()
            logger.info("🗑️ Cache cleared")
        except Exception as e:
            logger.error(f"❌ Failed to clear cache: {e}")
    
    def get_hit_rate(self) -> float:
        """
        Calculate cache hit rate
        
        Returns:
            Hit rate as percentage (0.0 to 1.0)
        """
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics
        
        Returns:
            {
                'hits': int,
                'misses': int,
                'hit_rate': float,
                'total_saved': float (USD)
            }
        """
        return {
            'hits': self._hits,
            'misses': self._misses,
            'total_queries': self._hits + self._misses,
            'hit_rate': self.get_hit_rate(),
            'total_saved_usd': self._total_saved
        }
    
    def _estimate_cost(self, response: Any) -> float:
        """
        Estimate API cost of response
        
        Quick estimate based on response size
        (real cost tracking should be done by caller)
        """
        try:
            # Rough estimate: ~1 token per 4 characters
            response_str = str(response)
            estimated_tokens = len(response_str) / 4
            
            # Assume Claude Sonnet: ~$3/1M input + $15/1M output
            # Conservative estimate: assume half input, half output
            cost = (estimated_tokens / 1_000_000) * 9.0
            
            return round(cost, 6)
        except:
            return 0.0


# Singleton instance
_cache_instance: Optional[TradingSemanticCache] = None


def get_cache(
    distance_threshold: float = 0.1,
    ttl: int = 3600
) -> TradingSemanticCache:
    """
    Get singleton cache instance
    
    Args:
        distance_threshold: Similarity threshold (only used on first call)
        ttl: Cache TTL in seconds (only used on first call)
    
    Returns:
        TradingSemanticCache instance
    """
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = TradingSemanticCache(
            distance_threshold=distance_threshold,
            ttl=ttl
        )
    
    return _cache_instance


def clear_cache():
    """Clear singleton cache"""
    global _cache_instance
    
    if _cache_instance:
        _cache_instance.clear()
