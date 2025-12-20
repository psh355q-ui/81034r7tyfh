"""
Trading Metrics - Prometheus metrics for trading operations

High-level metrics for production monitoring:
- Trade execution metrics
- Signal quality metrics
- Portfolio performance metrics
- AI cost tracking
- System reliability metrics

Author: AI Trading System Team
Date: 2025-11-24
"""

from prometheus_client import Counter, Gauge, Histogram, Summary
import time
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Trade Execution Metrics
# =============================================================================

trades_total = Counter(
    'trades_total',
    'Total number of trades executed',
    ['ticker', 'side', 'status']  # BUY/SELL, SUCCESS/FAILED
)

trade_slippage_bps = Histogram(
    'trade_slippage_bps',
    'Trade slippage in basis points',
    ['ticker', 'algorithm'],  # TWAP/VWAP/MARKET
    buckets=[0, 1, 2, 5, 10, 20, 50, 100]
)

trade_execution_duration_seconds = Histogram(
    'trade_execution_duration_seconds',
    'Time taken to execute trade',
    ['algorithm'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

trade_pnl_usd = Gauge(
    'trade_pnl_usd',
    'Realized P&L per trade in USD',
    ['ticker']
)


# =============================================================================
# Signal Quality Metrics
# =============================================================================

signals_generated_total = Counter(
    'signals_generated_total',
    'Total trading signals generated',
    ['ticker', 'signal', 'source']  # BUY/SELL/HOLD, ai/rule/ensemble
)

signal_confidence = Histogram(
    'signal_confidence',
    'Confidence level of generated signals',
    ['ticker', 'signal'],
    buckets=[0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]
)

signal_accuracy = Gauge(
    'signal_accuracy',
    'Historical accuracy of signals (win rate)',
    ['ticker', 'signal', 'lookback_days']
)

signals_triggered_total = Counter(
    'signals_triggered_total',
    'Signals that met threshold and triggered action',
    ['ticker', 'signal']
)


# =============================================================================
# Portfolio Performance Metrics
# =============================================================================

portfolio_value_usd = Gauge(
    'portfolio_value_usd',
    'Current total portfolio value in USD'
)

portfolio_cash_usd = Gauge(
    'portfolio_cash_usd',
    'Available cash in portfolio'
)

portfolio_positions_count = Gauge(
    'portfolio_positions_count',
    'Number of open positions'
)

portfolio_daily_pnl_usd = Gauge(
    'portfolio_daily_pnl_usd',
    'Daily P&L in USD'
)

portfolio_total_pnl_usd = Gauge(
    'portfolio_total_pnl_usd',
    'Total realized + unrealized P&L'
)

portfolio_sharpe_ratio = Gauge(
    'portfolio_sharpe_ratio',
    'Rolling Sharpe ratio',
    ['window_days']  # 30/90/365
)

portfolio_max_drawdown_pct = Gauge(
    'portfolio_max_drawdown_pct',
    'Maximum drawdown percentage'
)

position_concentration_pct = Gauge(
    'position_concentration_pct',
    'Largest position as % of portfolio',
    ['ticker']
)


# =============================================================================
# AI Cost Tracking
# =============================================================================

ai_api_calls_total = Counter(
    'ai_api_calls_total',
    'Total AI API calls',
    ['model', 'operation']  # claude/gemini/gpt, analysis/embedding/regime
)

ai_cost_usd_total = Counter(
    'ai_cost_usd_total',
    'Total AI API cost in USD',
    ['model', 'operation']
)

ai_tokens_used_total = Counter(
    'ai_tokens_used_total',
    'Total tokens consumed',
    ['model', 'token_type']  # input/output
)

ai_response_time_seconds = Histogram(
    'ai_response_time_seconds',
    'AI API response time',
    ['model', 'operation'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
)

ai_monthly_cost_usd = Gauge(
    'ai_monthly_cost_usd',
    'Projected monthly AI cost based on current usage',
    ['model']
)


# =============================================================================
# Data Quality Metrics
# =============================================================================

data_staleness_seconds = Gauge(
    'data_staleness_seconds',
    'Age of most recent data',
    ['data_type', 'ticker']  # price/news/sec_filing
)

data_fetch_errors_total = Counter(
    'data_fetch_errors_total',
    'Failed data fetches',
    ['source', 'error_type']  # yahoo/sec/newsapi
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage',
    ['cache_type']  # redis/timescale/local
)

cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_type']
)


# =============================================================================
# System Reliability Metrics
# =============================================================================

api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)

api_request_duration_seconds = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10]
)

background_jobs_total = Counter(
    'background_jobs_total',
    'Background jobs executed',
    ['job_name', 'status']  # success/failed
)

background_job_duration_seconds = Histogram(
    'background_job_duration_seconds',
    'Background job execution time',
    ['job_name'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800]
)

circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half_open, 2=open)',
    ['component']
)

rate_limit_hits_total = Counter(
    'rate_limit_hits_total',
    'Number of rate limit hits',
    ['api', 'limit_type']
)


# =============================================================================
# Risk Management Metrics
# =============================================================================

risk_score = Gauge(
    'risk_score',
    'Current risk score (0-1)',
    ['ticker', 'risk_type']  # unstructured/supply_chain/management
)

position_limit_usage_pct = Gauge(
    'position_limit_usage_pct',
    'Position limit usage percentage',
    ['ticker']
)

daily_loss_limit_usage_pct = Gauge(
    'daily_loss_limit_usage_pct',
    'Daily loss limit usage percentage'
)

volatility_breach_total = Counter(
    'volatility_breach_total',
    'Times volatility exceeded threshold',
    ['ticker']
)

kill_switch_activations_total = Counter(
    'kill_switch_activations_total',
    'Kill switch activation count',
    ['reason']
)


# =============================================================================
# Helper Functions
# =============================================================================

class MetricsCollector:
    """High-level metrics collection helper."""

    def __init__(self):
        self.start_time = time.time()
        logger.info("MetricsCollector initialized")

    def record_trade(
        self,
        ticker: str,
        side: str,
        status: str,
        slippage_bps: Optional[float] = None,
        algorithm: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        pnl_usd: Optional[float] = None,
    ):
        """Record trade execution metrics."""
        trades_total.labels(ticker=ticker, side=side, status=status).inc()

        if slippage_bps is not None and algorithm:
            trade_slippage_bps.labels(ticker=ticker, algorithm=algorithm).observe(slippage_bps)

        if duration_seconds is not None and algorithm:
            trade_execution_duration_seconds.labels(algorithm=algorithm).observe(duration_seconds)

        if pnl_usd is not None:
            trade_pnl_usd.labels(ticker=ticker).set(pnl_usd)

    def record_signal(
        self,
        ticker: str,
        signal: str,
        source: str,
        confidence: float,
        triggered: bool = False,
    ):
        """Record signal generation metrics."""
        signals_generated_total.labels(ticker=ticker, signal=signal, source=source).inc()
        signal_confidence.labels(ticker=ticker, signal=signal).observe(confidence)

        if triggered:
            signals_triggered_total.labels(ticker=ticker, signal=signal).inc()

    def update_portfolio_metrics(
        self,
        total_value: float,
        cash: float,
        positions_count: int,
        daily_pnl: float,
        total_pnl: float,
    ):
        """Update portfolio performance metrics."""
        portfolio_value_usd.set(total_value)
        portfolio_cash_usd.set(cash)
        portfolio_positions_count.set(positions_count)
        portfolio_daily_pnl_usd.set(daily_pnl)
        portfolio_total_pnl_usd.set(total_pnl)

    def record_ai_call(
        self,
        model: str,
        operation: str,
        cost_usd: float,
        input_tokens: int,
        output_tokens: int,
        duration_seconds: float,
    ):
        """Record AI API call metrics."""
        ai_api_calls_total.labels(model=model, operation=operation).inc()
        ai_cost_usd_total.labels(model=model, operation=operation).inc(cost_usd)
        ai_tokens_used_total.labels(model=model, token_type='input').inc(input_tokens)
        ai_tokens_used_total.labels(model=model, token_type='output').inc(output_tokens)
        ai_response_time_seconds.labels(model=model, operation=operation).observe(duration_seconds)

    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status: int,
        duration_seconds: float,
    ):
        """Record API request metrics."""
        api_requests_total.labels(
            endpoint=endpoint,
            method=method,
            status=str(status)
        ).inc()

        api_request_duration_seconds.labels(
            endpoint=endpoint,
            method=method
        ).observe(duration_seconds)

    def update_risk_metrics(
        self,
        ticker: str,
        unstructured_risk: float,
        supply_chain_risk: Optional[float] = None,
        management_trust: Optional[float] = None,
    ):
        """Update risk metrics."""
        risk_score.labels(ticker=ticker, risk_type='unstructured').set(unstructured_risk)

        if supply_chain_risk is not None:
            risk_score.labels(ticker=ticker, risk_type='supply_chain').set(supply_chain_risk)

        if management_trust is not None:
            # Convert trust (0-1 high is good) to risk (0-1 high is bad)
            mgmt_risk = 1.0 - management_trust
            risk_score.labels(ticker=ticker, risk_type='management').set(mgmt_risk)

    def activate_kill_switch(self, reason: str):
        """Record kill switch activation."""
        kill_switch_activations_total.labels(reason=reason).inc()
        logger.critical(f"Kill switch activated: {reason}")


# Global instance
metrics_collector = MetricsCollector()
