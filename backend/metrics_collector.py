"""
Metrics Collector for Prometheus
Simple implementation for monitoring system metrics
"""

import time
from typing import Dict, Any

# Check if prometheus_client is available
try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: prometheus_client not installed. Metrics collection disabled.")

class MetricsCollector:
    """Collects and exposes application metrics"""

    def __init__(self):
        self.enabled = PROMETHEUS_AVAILABLE

        if not self.enabled:
            return

        # Trading metrics
        self.trades_total = Counter('trades_total', 'Total number of trades executed', ['action', 'ticker'])
        self.trades_value = Histogram('trades_value_dollars', 'Trade value in dollars')
        self.portfolio_value = Gauge('portfolio_value_dollars', 'Current portfolio value')
        self.portfolio_return = Gauge('portfolio_return_percent', 'Portfolio return percentage')

        # System metrics
        self.api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
        self.api_latency = Histogram('api_latency_seconds', 'API request latency', ['endpoint'])
        self.errors_total = Counter('errors_total', 'Total errors', ['type'])

        # AI metrics
        self.ai_decisions = Counter('ai_decisions_total', 'AI decisions made', ['action'])
        self.ai_conviction = Histogram('ai_conviction_score', 'AI decision conviction score')

    def record_trade(self, action: str, ticker: str, value: float):
        """Record a trade execution"""
        if not self.enabled:
            return
        self.trades_total.labels(action=action, ticker=ticker).inc()
        self.trades_value.observe(value)

    def update_portfolio(self, value: float, return_pct: float):
        """Update portfolio metrics"""
        if not self.enabled:
            return
        self.portfolio_value.set(value)
        self.portfolio_return.set(return_pct)

    def record_api_request(self, endpoint: str, method: str, latency: float):
        """Record an API request"""
        if not self.enabled:
            return
        self.api_requests.labels(endpoint=endpoint, method=method).inc()
        self.api_latency.labels(endpoint=endpoint).observe(latency)

    def record_error(self, error_type: str):
        """Record an error"""
        if not self.enabled:
            return
        self.errors_total.labels(type=error_type).inc()

    def record_ai_decision(self, action: str, conviction: float):
        """Record an AI decision"""
        if not self.enabled:
            return
        self.ai_decisions.labels(action=action).inc()
        self.ai_conviction.observe(conviction)

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        if not self.enabled:
            return "# Prometheus client not installed\n"
        return generate_latest().decode('utf-8')

    def get_content_type(self) -> str:
        """Get the content type for metrics"""
        if not self.enabled:
            return "text/plain"
        return CONTENT_TYPE_LATEST

    def heartbeat(self):
        """Heartbeat to keep metrics collector alive"""
        # This is a no-op for now, but can be used for periodic tasks
        pass
