"""
Prometheus metrics for Feature Store monitoring.

Exposes metrics via /metrics endpoint for Prometheus scraping.
"""

from prometheus_client import Counter, Gauge, Histogram

# Counters
feature_requests_total = Counter(
    'feature_requests_total',
    'Total number of feature requests',
    ['ticker', 'feature_name', 'cache_layer']
)

feature_computation_total = Counter(
    'feature_computation_total',
    'Total number of feature computations',
    ['feature_name']
)

feature_errors_total = Counter(
    'feature_errors_total',
    'Total number of feature errors',
    ['error_type']
)

# Histograms (latency tracking)
feature_latency_seconds = Histogram(
    'feature_latency_seconds',
    'Feature retrieval latency',
    ['operation'],  # get, compute, save
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

# Gauges (current state)
cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate',
    ['cache_layer']  # redis, timescale
)

cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_layer']
)

active_tickers_count = Gauge(
    'active_tickers_count',
    'Number of active tickers being tracked'
)

monthly_cost_usd = Gauge(
    'monthly_cost_usd',
    'Cumulative monthly cost in USD'
)
