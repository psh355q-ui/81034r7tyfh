"""
Feature Store - 2-Layer Caching System.

Architecture:
    Layer 1: Redis (in-memory, < 5ms latency)
    Layer 2: TimescaleDB (persistent, < 100ms latency)
    Layer 3: Computation (lazy, only on cache miss)

Usage:
    >>> from data.feature_store import FeatureStore
    >>> store = FeatureStore()
    >>> await store.get_features("AAPL", ["ret_5d", "vol_20d"])
    {"ret_5d": 0.0523, "vol_20d": 0.0234}
"""

from .cache_layer import CacheLayer, RedisCache, TimescaleCache
from .store import FeatureStore

__all__ = ["FeatureStore", "CacheLayer", "RedisCache", "TimescaleCache"]
