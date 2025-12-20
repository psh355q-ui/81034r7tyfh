"""
Metrics Collector - Prometheus Integration

Collects and exposes system metrics for monitoring.

Metrics Categories:
- System: Uptime, heartbeat
- Trading: Decisions, executions, P&L
- AI: API calls, costs, latency
- Portfolio: Value, positions, returns
- Risk: Exposure, limits, kill switch
- Performance: Slippage, win rate, execution quality

Author: AI Trading System Team
Date: 2025-11-14
"""

from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import prometheus_client
try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        Summary,
        Info,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed. Metrics will be collected in memory only.")


class MetricsCollector:
    """
    Collects metrics for Prometheus monitoring.

    If Prometheus client is not available, stores metrics in memory
    for basic tracking.
    """

    def __init__(self):
        self.start_time = datetime.utcnow()
        self._in_memory_metrics = {}

        if PROMETHEUS_AVAILABLE:
            self._init_prometheus_metrics()
        else:
            logger.info("Running in memory-only metrics mode")

    def _init_prometheus_metrics(self):
        """Initialize all Prometheus metrics."""

        # ===== System Metrics =====
        self.system_info = Info("ai_trading_system", "System information")
        self.system_info.info({
            "version": "1.0.0",
            "phase": "7",
        })

        self.system_up = Gauge("ai_trading_system_up", "System is up (1) or down (0)")
        self.system_up.set(1)

        self.heartbeat_counter = Counter(
            "ai_trading_heartbeat_total",
            "Total number of heartbeats"
        )

        # ===== Trading Metrics =====
        self.trading_decisions = Counter(
            "ai_trading_decisions_total",
            "Total trading decisions",
            ["ticker", "action"]
        )

        self.trading_conviction = Histogram(
            "ai_trading_conviction",
            "Trading decision conviction scores",
            buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )

        self.trading_latency = Histogram(
            "ai_trading_decision_latency_seconds",
            "Time to make trading decision",
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )

        # ===== Execution Metrics =====
        self.executions = Counter(
            "ai_trading_executions_total",
            "Total trade executions",
            ["ticker", "action", "algorithm"]
        )

        self.execution_slippage = Histogram(
            "ai_trading_execution_slippage_bps",
            "Execution slippage in basis points",
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
        )

        self.execution_volume = Counter(
            "ai_trading_execution_volume_shares",
            "Total shares traded"
        )

        self.execution_commission = Counter(
            "ai_trading_execution_commission_usd",
            "Total commission paid"
        )

        # ===== AI Metrics =====
        self.ai_calls = Counter(
            "ai_trading_ai_calls_total",
            "Total AI API calls",
            ["provider", "model"]
        )

        self.ai_tokens = Counter(
            "ai_trading_ai_tokens_total",
            "Total AI tokens used",
            ["provider", "model", "type"]  # type: input/output
        )

        self.ai_cost = Counter(
            "ai_trading_ai_cost_usd",
            "Total AI cost in USD",
            ["provider"]
        )

        self.ai_latency = Histogram(
            "ai_trading_ai_latency_seconds",
            "AI API call latency",
            ["provider"],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )

        # ===== Portfolio Metrics =====
        self.portfolio_value = Gauge(
            "ai_trading_portfolio_value_usd",
            "Current portfolio value"
        )

        self.portfolio_cash = Gauge(
            "ai_trading_portfolio_cash_usd",
            "Cash balance"
        )

        self.portfolio_positions = Gauge(
            "ai_trading_portfolio_positions",
            "Number of open positions"
        )

        self.portfolio_pnl = Gauge(
            "ai_trading_portfolio_pnl_usd",
            "Total realized P&L"
        )

        self.portfolio_return = Gauge(
            "ai_trading_portfolio_return_pct",
            "Portfolio return percentage"
        )

        self.daily_pnl = Gauge(
            "ai_trading_daily_pnl_usd",
            "Daily P&L"
        )

        # ===== Risk Metrics =====
        self.risk_kill_switch = Gauge(
            "ai_trading_risk_kill_switch",
            "Kill switch status (1=active, 0=inactive)"
        )

        self.risk_daily_trades = Gauge(
            "ai_trading_risk_daily_trades",
            "Number of trades today"
        )

        self.risk_exposure = Gauge(
            "ai_trading_risk_exposure_pct",
            "Portfolio exposure percentage"
        )

        # ===== Performance Metrics =====
        self.win_rate = Gauge(
            "ai_trading_win_rate",
            "Win rate (0-1)"
        )

        # ===== Error Metrics =====
        self.errors = Counter(
            "ai_trading_errors_total",
            "Total errors",
            ["component", "error_type"]
        )

    def heartbeat(self):
        """Record a heartbeat."""
        if PROMETHEUS_AVAILABLE:
            self.heartbeat_counter.inc()
        self._in_memory_metrics["last_heartbeat"] = datetime.utcnow()

    def record_trading_decision(
        self,
        ticker: str,
        action: str,
        conviction: float,
        latency_seconds: float,
    ):
        """Record a trading decision."""
        if PROMETHEUS_AVAILABLE:
            self.trading_decisions.labels(ticker=ticker, action=action).inc()
            self.trading_conviction.observe(conviction)
            self.trading_latency.observe(latency_seconds)

        # In-memory tracking
        key = f"decision_{ticker}_{action}"
        self._in_memory_metrics[key] = {
            "conviction": conviction,
            "latency": latency_seconds,
            "timestamp": datetime.utcnow(),
        }

    def record_execution(
        self,
        ticker: str,
        action: str,
        shares: int,
        price: float,
        slippage_bps: float,
        algorithm: str,
        commission: float = 0.0,
    ):
        """Record a trade execution."""
        if PROMETHEUS_AVAILABLE:
            self.executions.labels(
                ticker=ticker,
                action=action,
                algorithm=algorithm
            ).inc()
            self.execution_slippage.observe(slippage_bps)
            self.execution_volume.inc(shares)
            if commission > 0:
                self.execution_commission.inc(commission)

        # In-memory tracking
        key = f"execution_{ticker}_{datetime.utcnow().isoformat()}"
        self._in_memory_metrics[key] = {
            "action": action,
            "shares": shares,
            "price": price,
            "slippage_bps": slippage_bps,
            "algorithm": algorithm,
        }

    def record_ai_call(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        latency_seconds: float,
    ):
        """Record an AI API call."""
        if PROMETHEUS_AVAILABLE:
            self.ai_calls.labels(provider=provider, model=model).inc()
            self.ai_tokens.labels(
                provider=provider,
                model=model,
                type="input"
            ).inc(input_tokens)
            self.ai_tokens.labels(
                provider=provider,
                model=model,
                type="output"
            ).inc(output_tokens)
            self.ai_cost.labels(provider=provider).inc(cost_usd)
            self.ai_latency.labels(provider=provider).observe(latency_seconds)

        # In-memory tracking
        key = f"ai_{provider}"
        if key not in self._in_memory_metrics:
            self._in_memory_metrics[key] = {
                "calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
            }

        self._in_memory_metrics[key]["calls"] += 1
        self._in_memory_metrics[key]["total_tokens"] += input_tokens + output_tokens
        self._in_memory_metrics[key]["total_cost"] += cost_usd

    def update_portfolio(
        self,
        total_value: float,
        num_positions: int,
        total_pnl: float,
        cash: float,
        return_pct: float,
    ):
        """Update portfolio metrics."""
        if PROMETHEUS_AVAILABLE:
            self.portfolio_value.set(total_value)
            self.portfolio_positions.set(num_positions)
            self.portfolio_pnl.set(total_pnl)
            self.portfolio_cash.set(cash)
            self.portfolio_return.set(return_pct)

        # In-memory tracking
        self._in_memory_metrics["portfolio"] = {
            "total_value": total_value,
            "num_positions": num_positions,
            "total_pnl": total_pnl,
            "cash": cash,
            "return_pct": return_pct,
            "timestamp": datetime.utcnow(),
        }

    def update_daily_pnl(self, pnl: float):
        """Update daily P&L."""
        if PROMETHEUS_AVAILABLE:
            self.daily_pnl.set(pnl)

        self._in_memory_metrics["daily_pnl"] = {
            "value": pnl,
            "timestamp": datetime.utcnow(),
        }

    def update_risk_status(
        self,
        kill_switch_active: bool,
        daily_trades: int,
        exposure_pct: float = 0.0,
    ):
        """Update risk metrics."""
        if PROMETHEUS_AVAILABLE:
            self.risk_kill_switch.set(1 if kill_switch_active else 0)
            self.risk_daily_trades.set(daily_trades)
            if exposure_pct > 0:
                self.risk_exposure.set(exposure_pct)

        self._in_memory_metrics["risk"] = {
            "kill_switch_active": kill_switch_active,
            "daily_trades": daily_trades,
            "exposure_pct": exposure_pct,
            "timestamp": datetime.utcnow(),
        }

    def record_error(self, component: str, error_type: str):
        """Record an error."""
        if PROMETHEUS_AVAILABLE:
            self.errors.labels(component=component, error_type=error_type).inc()

        key = f"error_{component}_{error_type}"
        if key not in self._in_memory_metrics:
            self._in_memory_metrics[key] = 0
        self._in_memory_metrics[key] += 1

    def set_system_down(self):
        """Mark system as down."""
        if PROMETHEUS_AVAILABLE:
            self.system_up.set(0)

    def get_summary(self) -> Dict:
        """Get summary of collected metrics."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "uptime_seconds": uptime,
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "in_memory_metrics": len(self._in_memory_metrics),
            "portfolio": self._in_memory_metrics.get("portfolio", {}),
            "risk": self._in_memory_metrics.get("risk", {}),
            "daily_pnl": self._in_memory_metrics.get("daily_pnl", {}),
            "ai_usage": {
                provider: data
                for provider, data in self._in_memory_metrics.items()
                if provider.startswith("ai_")
            },
        }


# Singleton instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
