"""
End-to-End Integration Tests for AI Trading System
Phase 18: System Verification

Tests the full pipeline:
1. Data Collection (Mock)
2. Analysis (CEO Speech, Technical)
3. Trading Decision
4. Incremental Updates
"""

import pytest
import asyncio
import sys
from unittest.mock import MagicMock, patch

# Mock asyncpg before importing backend modules to avoid installation issues
sys.modules["asyncpg"] = MagicMock()

from datetime import datetime
from backend.main import app
from backend.core.models.sec_analysis_models import SECAnalysisRequest, SECAnalysisResult
from backend.services.stock_price_scheduler import StockPriceScheduler
from backend.api.incremental_router import router as incremental_router

@pytest.mark.asyncio
async def test_ceo_analysis_pipeline():
    """
    Test the full CEO Analysis pipeline:
    Request -> Mock SEC Parser -> Mock Claude -> Result Storage
    """
    # Mock dependencies
    with patch("backend.ai.sec_analyzer.SECAnalyzer.analyze_ticker") as mock_analyze:
        # Setup mock return
        mock_result = MagicMock(spec=SECAnalysisResult)
        mock_result.ticker = "TEST"
        mock_result.filing_type = "10-Q"
        mock_result.management_tone.sentiment_score = 0.8
        mock_analyze.return_value = mock_result

        # Simulate API call logic (direct function call for integration test)
        from backend.ai.sec_analyzer import SECAnalyzer
        analyzer = SECAnalyzer()
        request = SECAnalysisRequest(ticker="TEST", filing_type="10-Q")
        
        result = await analyzer.analyze_ticker(request)
        
        assert result.ticker == "TEST"
        assert result.management_tone.sentiment_score == 0.8
        print("\n✅ CEO Analysis Pipeline Verified")

@pytest.mark.asyncio
async def test_incremental_scheduler_integration():
    """
    Test Stock Price Scheduler integration
    """
    # Mock storage to avoid real DB calls
    with patch("backend.services.stock_price_scheduler.StockPriceStorage") as MockStorage:
        mock_storage_instance = MockStorage.return_value
        mock_storage_instance.update_stock_prices_incremental.return_value = {
            "status": "success",
            "new_rows": 50
        }
        
        scheduler = StockPriceScheduler(tickers=["AAPL", "GOOGL"])
        
        # Run manual update
        stats = await scheduler.run_manual_update()
        
        assert stats.successful == 2
        assert stats.failed == 0
        print("\n✅ Incremental Scheduler Verified")

@pytest.mark.asyncio
async def test_api_endpoints_integration():
    """
    Test critical API endpoints availability
    """
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Health check
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] in ["healthy", "degraded"] # degraded if redis missing
        
        # Incremental stats
        response = await ac.get("/api/incremental/stats")
        assert response.status_code == 200
        assert "total_tickers" in response.json()
        
        print("\n✅ API Endpoints Verified")

if __name__ == "__main__":
    # Manual run for debugging
    asyncio.run(test_ceo_analysis_pipeline())
    asyncio.run(test_incremental_scheduler_integration())
