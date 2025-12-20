"""
Prometheus Monitoring Metrics (Phase 7)

MASTER_GUIDE.md (Section 7, 8) based implementation.
Integrates with docker-compose.yml Prometheus/Grafana services.

Dependencies:
    pip install prometheus-client
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    start_http_server,
)

logger = logging.getLogger(__name__)


# =============================================================================
# AI AGENT & CLAUDE API METRICS
# =============================================================================

# Total AI analyses performed
AGENT_ANALYSES_TOTAL = Counter(
    "agent_analyses_total",
    "Total number of stock analyses performed by AI agent",
)

# AI decisions by ticker and action
AGENT_DECISIONS_TOTAL = Counter(
    "agent_decisions_total",
    "Total trading decisions made by AI agent",
    ["ticker", "action"],  # action: BUY, SELL, HOLD
)

# Claude API request count
AI_API_REQUESTS_TOTAL = Counter(
    "ai_api_requests_total",
    "Total requests made to Claude API",
    ["model_name"],  # claude-3-haiku-20240307, etc.
)

# Claude API total cost
AI_API_COST_USD_TOTAL = Counter(
    "ai_api_cost_usd_total",
    "Total cost of Claude API calls in USD",
    ["model_name"],
)

# Claude API response latency
AI_API_LATENCY_SECONDS = Histogram(
    "ai_api_latency_seconds",
    "Claude API request latency in seconds",
    ["model_name"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

# Conviction score distribution
AGENT_CONVICTION_HISTOGRAM = Histogram(
    "agent_conviction_score",
    "Distribution of AI agent conviction scores",
    ["action"],  # BUY, SELL, HOLD
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)


# =============================================================================
# FEATURE STORE & CACHE METRICS
# =============================================================================

# Cache hits by layer
CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["layer"],  # L1_Redis, L2_TimescaleDB
)

# Cache misses (triggers calculation)
CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total cache misses requiring feature calculation",
)

# Current cache hit rate
CACHE_HIT_RATE = Gauge(
    "cache_hit_rate",
    "Current cache hit rate (0.0 - 1.0)",
)

# Feature calculation latency
FEATURE_CALCULATION_LATENCY_SECONDS = Histogram(
    "feature_calculation_latency_seconds",
    "Latency for calculating new features",
    ["feature_name"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

# Feature Store query latency
FEATURE_STORE_QUERY_LATENCY_SECONDS = Histogram(
    "feature_store_query_latency_seconds",
    "Total latency for feature store queries",
    buckets=(0.001, 0.002, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
)


# =============================================================================
# TRADING & PORTFOLIO METRICS
# =============================================================================

# Total executed trades
TRADES_TOTAL = Counter(
    "trades_total",
    "Total number of executed trades",
    ["ticker", "side"],  # side: BUY, SELL
)

# Current number of open positions
CURRENT_POSITIONS_GAUGE = Gauge(
    "current_positions_count",
    "Current number of open positions",
)

# Portfolio total value
PORTFOLIO_VALUE_GAUGE = Gauge(
    "portfolio_total_value",
    "Current total value of portfolio (cash + holdings) in USD",
)

# Portfolio cash
PORTFOLIO_CASH_GAUGE = Gauge(
    "portfolio_cash",
    "Current cash balance in USD",
)

# Daily PnL
DAILY_PNL_GAUGE = Gauge(
    "daily_pnl",
    "Daily profit/loss in USD",
)

# Total return percentage
TOTAL_RETURN_PCT_GAUGE = Gauge(
    "total_return_pct",
    "Total portfolio return percentage",
)


# =============================================================================
# CONSTITUTION RULES & RISK METRICS
# =============================================================================

# Kill Switch status
KILL_SWITCH_STATUS = Gauge(
    "kill_switch_status",
    "Kill switch status (1 = ACTIVE/Halted, 0 = Inactive/Running)",
)

# Constitution rule violations
CONSTITUTION_VIOLATIONS_TOTAL = Counter(
    "constitution_violations_total",
    "Total number of Constitution rule violations",
    ["rule_name"],  # max_position_size, max_positions, conviction_threshold, etc.
)

# Constitution rule checks
CONSTITUTION_CHECKS_TOTAL = Counter(
    "constitution_checks_total",
    "Total number of Constitution rule checks",
    ["rule_name", "result"],  # result: PASS, FAIL
)

# Max Drawdown
MAX_DRAWDOWN_PCT_GAUGE = Gauge(
    "max_drawdown_pct",
    "Maximum drawdown percentage from peak",
)


# =============================================================================
# SYSTEM HEALTH METRICS
# =============================================================================

# Application uptime
SYSTEM_UPTIME_SECONDS = Gauge(
    "system_uptime_seconds",
    "Application uptime in seconds",
)

# TimescaleDB connection status
TIMESCALE_CONNECTION_STATUS = Gauge(
    "timescale_connection_status",
    "TimescaleDB connection status (1 = Connected, 0 = Disconnected)",
)

# Redis connection status
REDIS_CONNECTION_STATUS = Gauge(
    "redis_connection_status",
    "Redis connection status (1 = Connected, 0 = Disconnected)",
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def start_monitoring_server(port: int = 8001):
    """
    Start standalone Prometheus metrics HTTP server.

    Args:
        port: HTTP port (default: 8001)

    Note:
        - Access metrics at http://localhost:8001/metrics
        - Prometheus scrapes this endpoint (configured in prometheus.yml)
        - For FastAPI integration, use make_asgi_app() instead
    """
    try:
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on http://0.0.0.0:{port}")
        logger.info(f"Metrics available at http://0.0.0.0:{port}/metrics")
    except OSError as e:
        logger.warning(
            f"Prometheus server port {port} already in use. "
            f"Assuming monitoring is already running."
        )


def update_cache_metrics(hits: int, misses: int):
    """
    Update cache hit rate gauge based on current hits/misses.

    Args:
        hits: Number of cache hits
        misses: Number of cache misses
    """
    total = hits + misses
    if total > 0:
        hit_rate = hits / total
        CACHE_HIT_RATE.set(hit_rate)
        logger.debug(f"Cache hit rate updated: {hit_rate:.2%}")


@contextmanager
def track_ai_request(model_name: str, cost_usd: float):
    """
    Context manager to track AI API request metrics.

    Args:
        model_name: Model identifier (e.g., 'claude-3-haiku-20240307')
        cost_usd: Cost of this request in USD

    Usage:
        with track_ai_request('claude-3-haiku-20240307', 0.0007):
            response = await claude_client.analyze(...)
    """
    start_time = time.time()

    try:
        yield
    finally:
        # Record latency
        latency = time.time() - start_time
        AI_API_LATENCY_SECONDS.labels(model_name=model_name).observe(latency)

        # Record request count
        AI_API_REQUESTS_TOTAL.labels(model_name=model_name).inc()

        # Record cost
        AI_API_COST_USD_TOTAL.labels(model_name=model_name).inc(cost_usd)

        logger.debug(
            f"AI request tracked: {model_name}, {latency:.3f}s, ${cost_usd:.6f}"
        )


def track_trade(ticker: str, side: str, quantity: float, fill_price: float):
    """
    Track executed trade metrics.

    Args:
        ticker: Stock symbol
        side: 'BUY' or 'SELL'
        quantity: Number of shares
        fill_price: Execution price
    """
    TRADES_TOTAL.labels(ticker=ticker, side=side).inc()
    logger.info(f"Trade tracked: {side} {quantity} {ticker} @ ${fill_price:.2f}")


def track_constitution_check(rule_name: str, passed: bool):
    """
    Track Constitution rule check.

    Args:
        rule_name: Name of the rule (e.g., 'max_position_size')
        passed: Whether check passed
    """
    result = "PASS" if passed else "FAIL"
    CONSTITUTION_CHECKS_TOTAL.labels(rule_name=rule_name, result=result).inc()

    if not passed:
        CONSTITUTION_VIOLATIONS_TOTAL.labels(rule_name=rule_name).inc()
        logger.warning(f"Constitution violation: {rule_name}")


@contextmanager
def track_feature_calculation(feature_name: str):
    """
    Context manager to track feature calculation latency.

    Args:
        feature_name: Feature identifier (e.g., 'mom_20d')

    Usage:
        with track_feature_calculation('mom_20d'):
            value = calculate_momentum(...)
    """
    start_time = time.time()

    try:
        yield
    finally:
        latency = time.time() - start_time
        FEATURE_CALCULATION_LATENCY_SECONDS.labels(
            feature_name=feature_name
        ).observe(latency)
        logger.debug(f"Feature calculation: {feature_name} took {latency:.4f}s")


def update_portfolio_metrics(
    total_value: float,
    cash: float,
    num_positions: int,
    daily_pnl: float,
    total_return_pct: float,
    max_drawdown_pct: float,
):
    """
    Update all portfolio-related metrics at once.

    Args:
        total_value: Total portfolio value
        cash: Current cash balance
        num_positions: Number of open positions
        daily_pnl: Daily profit/loss
        total_return_pct: Total return percentage
        max_drawdown_pct: Maximum drawdown percentage
    """
    PORTFOLIO_VALUE_GAUGE.set(total_value)
    PORTFOLIO_CASH_GAUGE.set(cash)
    CURRENT_POSITIONS_GAUGE.set(num_positions)
    DAILY_PNL_GAUGE.set(daily_pnl)
    TOTAL_RETURN_PCT_GAUGE.set(total_return_pct)
    MAX_DRAWDOWN_PCT_GAUGE.set(max_drawdown_pct)

    logger.debug(
        f"Portfolio metrics updated: ${total_value:,.2f}, "
        f"{num_positions} positions, "
        f"return {total_return_pct:.2f}%"
    )


def update_system_health(
    uptime_seconds: float,
    timescale_connected: bool,
    redis_connected: bool,
    kill_switch_active: bool,
):
    """
    Update system health metrics.

    Args:
        uptime_seconds: Application uptime
        timescale_connected: TimescaleDB connection status
        redis_connected: Redis connection status
        kill_switch_active: Kill switch status
    """
    SYSTEM_UPTIME_SECONDS.set(uptime_seconds)
    TIMESCALE_CONNECTION_STATUS.set(1 if timescale_connected else 0)
    REDIS_CONNECTION_STATUS.set(1 if redis_connected else 0)
    KILL_SWITCH_STATUS.set(1 if kill_switch_active else 0)


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    """
    Run demo monitoring server.
    """
    import random

    logging.basicConfig(level=logging.INFO)

    # Start server
    start_monitoring_server(port=8001)

    logger.info("\nSimulating metrics for 30 seconds...")
    logger.info("Visit http://localhost:8001/metrics to see Prometheus metrics")
    logger.info("Press Ctrl+C to stop\n")

    try:
        start_time = time.time()

        while True:
            # Simulate AI request
            with track_ai_request("claude-3-haiku-20240307", 0.0007):
                time.sleep(random.uniform(0.5, 2.0))

            AGENT_ANALYSES_TOTAL.inc()

            # Simulate decision
            action = random.choice(["BUY", "SELL", "HOLD"])
            AGENT_DECISIONS_TOTAL.labels(ticker="AAPL", action=action).inc()

            # Simulate cache metrics
            if random.random() > 0.1:  # 90% hit rate
                CACHE_HITS_TOTAL.labels(layer="L1_Redis").inc()
            else:
                CACHE_MISSES_TOTAL.inc()

            update_cache_metrics(hits=90, misses=10)

            # Simulate portfolio
            update_portfolio_metrics(
                total_value=100000 + random.uniform(-5000, 5000),
                cash=50000,
                num_positions=random.randint(5, 10),
                daily_pnl=random.uniform(-500, 500),
                total_return_pct=random.uniform(-5, 15),
                max_drawdown_pct=random.uniform(-10, 0),
            )

            # Update system health
            update_system_health(
                uptime_seconds=time.time() - start_time,
                timescale_connected=True,
                redis_connected=True,
                kill_switch_active=False,
            )

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("\nMonitoring demo stopped")
