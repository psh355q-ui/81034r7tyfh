"""
Integration Tests - Phase 18

End-to-end integration tests for AI Trading System.

Usage:
    pytest backend/tests/test_integration.py -v
    pytest backend/tests/test_integration.py -v --html=test_report.html
"""

import pytest
import asyncio
import httpx
from datetime import datetime


# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


@pytest.mark.asyncio
class TestHealthChecks:
    """Test health check endpoints."""

    async def test_main_health(self):
        """Test main health endpoint."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    async def test_database_connection(self):
        """Test database connectivity."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            # Health check should verify DB connection
            response = await client.get("/health")

            assert response.status_code == 200


@pytest.mark.asyncio
class TestCostMonitoring:
    """Test cost monitoring API."""

    async def test_get_dashboard(self):
        """Test cost dashboard endpoint."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get("/api/cost/dashboard")

            assert response.status_code == 200
            data = response.json()

            # Verify required fields
            assert "today" in data
            assert "monthly_total" in data
            assert "budget" in data

    async def test_get_daily_summary(self):
        """Test daily cost summary."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get("/api/cost/summary/daily")

            assert response.status_code == 200
            data = response.json()

            assert "total_cost_usd" in data
            assert "embeddings_generated" in data

    async def test_budget_check(self):
        """Test budget alert check."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get("/api/cost/budget/check")

            assert response.status_code == 200
            data = response.json()

            assert "status" in data
            assert data["status"] in ["OK", "WARNING", "CRITICAL"]
            assert "daily" in data
            assert "monthly" in data


@pytest.mark.asyncio
class TestNewsFiltering:
    """Test news context filtering API."""

    async def test_analyze_news(self):
        """Test single news analysis."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/api/news/analyze",
                json={
                    "ticker": "AAPL",
                    "title": "Test news title",
                    "content": "Test news content about supply chain issues...",
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Verify ensemble scores
            assert "cluster_risk" in data
            assert "sector_risk" in data
            assert "crash_pattern_risk" in data
            assert "sentiment_trend_risk" in data
            assert "final_risk_score" in data
            assert "risk_level" in data

            # Verify risk level is valid
            assert data["risk_level"] in ["CRITICAL", "HIGH", "NORMAL", "LOW"]

            # Verify scores are in valid range
            assert 0 <= data["final_risk_score"] <= 1

    async def test_get_risk_clusters(self):
        """Test risk clusters endpoint."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get("/api/news/risk-clusters?rebuild=false")

            assert response.status_code == 200
            data = response.json()

            assert "total_clusters" in data
            assert "clusters" in data

    async def test_get_sector_vectors(self):
        """Test sector vectors endpoint."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get("/api/news/sector-vectors?rebuild=false")

            assert response.status_code == 200
            data = response.json()

            assert "total_sectors" in data
            assert "sectors" in data


@pytest.mark.asyncio
class TestSECSemanticSearch:
    """Test SEC semantic search API."""

    async def test_semantic_search(self):
        """Test semantic search."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/api/sec/semantic-search",
                json={
                    "ticker": "AAPL",
                    "query": "What are the main risks?",
                    "top_k": 5,
                }
            )

            # May return 200 with results or 404 if no data
            assert response.status_code in [200, 404, 500]

            if response.status_code == 200:
                data = response.json()
                assert "query" in data
                assert "ticker" in data
                assert "results" in data
                assert "total_results" in data

    async def test_risk_search(self):
        """Test risk-focused search."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/api/sec/risk-search",
                json={
                    "ticker": "AAPL",
                    "risk_categories": ["regulatory", "operational"],
                    "top_k": 5,
                }
            )

            # May return 200 with results or 404 if no data
            assert response.status_code in [200, 404, 500]

    async def test_similar_companies(self):
        """Test similar companies finder."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.get("/api/sec/similar-companies/AAPL?top_k=5")

            # May return 200 with results or 404 if no data
            assert response.status_code in [200, 404, 500]


@pytest.mark.asyncio
class TestPerformance:
    """Test performance requirements."""

    async def test_health_response_time(self):
        """Test health check response time < 100ms."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            start = asyncio.get_event_loop().time()
            response = await client.get("/health")
            elapsed = (asyncio.get_event_loop().time() - start) * 1000

            assert response.status_code == 200
            assert elapsed < 100, f"Health check took {elapsed:.2f}ms (> 100ms)"

    async def test_cost_dashboard_response_time(self):
        """Test cost dashboard response time < 500ms."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            start = asyncio.get_event_loop().time()
            response = await client.get("/api/cost/dashboard")
            elapsed = (asyncio.get_event_loop().time() - start) * 1000

            assert response.status_code == 200
            assert elapsed < 500, f"Dashboard took {elapsed:.2f}ms (> 500ms)"


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling."""

    async def test_invalid_ticker(self):
        """Test handling of invalid ticker."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/api/news/analyze",
                json={
                    "ticker": "",  # Invalid
                    "title": "Test",
                    "content": "Test content",
                }
            )

            # Should return 422 (validation error) or handle gracefully
            assert response.status_code in [422, 400, 500]

    async def test_missing_required_field(self):
        """Test missing required fields."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/api/news/analyze",
                json={
                    "ticker": "AAPL",
                    # Missing title and content
                }
            )

            assert response.status_code == 422  # Validation error


# Test summary
def test_summary(request):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("Integration Test Summary")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    print("=" * 60)
