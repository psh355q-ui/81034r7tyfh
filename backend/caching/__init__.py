"""
Semantic Caching Module

Implements RedisVL-based semantic caching to eliminate API costs
for semantically similar queries using vector similarity.
"""

from .semantic_cache import TradingSemanticCache, get_cache
from .decorators import cached_analysis

__all__ = ['TradingSemanticCache', 'get_cache', 'cached_analysis']
