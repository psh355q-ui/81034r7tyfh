"""
Locust Load Test for AI Trading System
Phase 18: Performance Verification

Simulates user traffic patterns:
1. Dashboard User (Read-heavy)
2. Analyst User (Compute-heavy)
3. Admin User (System checks)
"""

from locust import HttpUser, task, between
import random

class DashboardUser(HttpUser):
    wait_time = between(1, 5)
    weight = 3  # Most common user type

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/incremental/stats")

    @task(2)
    def view_storage(self):
        self.client.get("/api/incremental/storage")

    @task(1)
    def check_health(self):
        self.client.get("/health")

class AnalystUser(HttpUser):
    wait_time = between(5, 15)
    weight = 1

    @task
    def analyze_ticker(self):
        # Mock analysis request
        tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
        ticker = random.choice(tickers)
        
        # Note: In a real load test, we might want to mock the backend 
        # to avoid hitting real LLM APIs and incurring costs.
        # For this test, we'll hit a lightweight endpoint or mock endpoint.
        self.client.post("/analyze", json={
            "ticker": ticker,
            "urgency": "LOW"
        })

class AdminUser(HttpUser):
    wait_time = between(10, 30)
    weight = 1

    @task
    def check_system_status(self):
        self.client.get("/api/incremental/scheduler-status")
        self.client.get("/api/incremental/cost-savings")
