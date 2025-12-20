"""
Cached Analysis Wrapper

Wraps analysis functions with semantic caching to eliminate
duplicate API costs for similar queries.

Usage:
    @cached_analysis()
    async def analyze_stock(ticker: str, query: str):
        # Expensive AI analysis here
        return result
"""

import logging
from functools import wraps
from typing import Callable, Any
from backend.caching import get_cache

logger = logging.getLogger(__name__)


def cached_analysis(
    ttl: int = 3600,
    distance_threshold: float = 0.1
):
    """
    Decorator to add semantic caching to analysis functions
    
    Args:
        ttl: Cache TTL in seconds (default: 1 hour)
        distance_threshold: Similarity threshold for cache hits
    
    Example:
        @cached_analysis(ttl=1800)  # 30 min cache
        async def analyze_sec_filing(ticker: str):
            return expensive_ai_analysis(ticker)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Build query string from function args
            query_parts = []
            
            # Add function name
            query_parts.append(f"func:{func.__name__}")
            
            # Add positional args
            for arg in args:
                query_parts.append(str(arg))
            
            # Add keyword args (sorted for consistency)
            for key in sorted(kwargs.keys()):
                query_parts.append(f"{key}={kwargs[key]}")
            
            query_str = " ".join(query_parts)
            
            # Try cache
            cache = get_cache(
                distance_threshold=distance_threshold,
                ttl=ttl
            )
            
            async def generate():
                """Call original function"""
                return await func(*args, **kwargs)
            
            result = await cache.get_or_generate(
                query=query_str,
                generate_func=generate,
                metadata={
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
            )
            
            return result
        
        return wrapper
    return decorator
