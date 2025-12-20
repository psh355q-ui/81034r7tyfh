"""
Load Testing Script - Phase 18

Tests system performance under load using Locust.

Usage:
    # Install locust
    pip install locust

    # Run load test
    locust -f backend/tests/load_test.py --host=http://localhost:8000

    # Run headless (no web UI)
    locust -f backend/tests/load_test.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 5m --headless

    # With reporting
    locust -f backend/tests/load_test.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 5m --headless \
           --html load_test_report.html
"""

import random
from locust import HttpUser, task, between, events
import logging

logger = logging.getLogger(__name__)


class AITradingUser(HttpUser):
    """
    Simulated user for AI Trading System.

    Performs typical user workflows:
    - Health checks
    - News filtering
    - SEC semantic search
    - Cost monitoring
    """

    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)

    # Test data
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META"]
    queries = [
        "supply chain risks",
        "revenue growth",
        "competitive advantages",
        "regulatory challenges",
    ]

    @task(10)
    def health_check(self):
        """Health check endpoint (most frequent)."""
        self.client.get("/health", name="/health")

    @task(5)
    def get_cost_dashboard(self):
        """Get cost monitoring dashboard."""
        self.client.get("/api/cost/dashboard", name="/api/cost/dashboard")

    @task(3)
    def analyze_news(self):
        """Analyze single news item."""
        ticker = random.choice(self.tickers)

        self.client.post(
            "/api/news/analyze",
            json={
                "ticker": ticker,
                "title": f"{ticker} faces challenges",
                "content": "Company announces strategic changes...",
            },
            name="/api/news/analyze",
        )

    @task(2)
    def sec_semantic_search(self):
        """SEC semantic search."""
        ticker = random.choice(self.tickers)
        query = random.choice(self.queries)

        self.client.post(
            "/api/sec/semantic-search",
            json={
                "ticker": ticker,
                "query": query,
                "top_k": 5,
            },
            name="/api/sec/semantic-search",
        )

    @task(2)
    def risk_search(self):
        """Risk-focused search."""
        ticker = random.choice(self.tickers)

        self.client.post(
            "/api/sec/risk-search",
            json={
                "ticker": ticker,
                "risk_categories": ["regulatory", "operational"],
                "top_k": 5,
            },
            name="/api/sec/risk-search",
        )

    @task(1)
    def get_risk_clusters(self):
        """Get news risk clusters."""
        self.client.get(
            "/api/news/risk-clusters?rebuild=false",
            name="/api/news/risk-clusters",
        )

    @task(1)
    def get_daily_cost_summary(self):
        """Get daily cost summary."""
        self.client.get("/api/cost/summary/daily", name="/api/cost/summary/daily")

    def on_start(self):
        """Called when a simulated user starts."""
        logger.info("User started")

    def on_stop(self):
        """Called when a simulated user stops."""
        logger.info("User stopped")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    print("=== Load Test Started ===")
    print(f"Host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    stats = environment.runner.stats

    print("\n=== Load Test Results ===")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min response time: {stats.total.min_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print(f"Failure rate: {(stats.total.num_failures / stats.total.num_requests * 100) if stats.total.num_requests > 0 else 0:.2f}%")

    # Performance thresholds
    if stats.total.avg_response_time > 1000:
        print("\n⚠️  WARNING: Average response time > 1000ms")

    if stats.total.num_failures / stats.total.num_requests > 0.01:
        print("\n⚠️  WARNING: Failure rate > 1%")

    print("\n=== Top Endpoints ===")
    for name, stat in stats.entries.items():
        if stat.num_requests > 0:
            print(f"{name}:")
            print(f"  Requests: {stat.num_requests}")
            print(f"  Avg Response Time: {stat.avg_response_time:.2f}ms")
            print(f"  Failures: {stat.num_failures}")
