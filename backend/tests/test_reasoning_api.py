import pytest
from fastapi.testclient import TestClient

@pytest.mark.unit
def test_reasoning_health(client: TestClient):
    """Test reasoning engine health endpoint."""
    response = client.get("/api/reasoning/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

@pytest.mark.integration
@pytest.mark.asyncio
async def test_reasoning_analyze_mock(client: TestClient):
    """Test reasoning analysis with mock data."""
    payload = {
        "ticker": "NVDA",
        "news_context": "Test news",
        "technical_summary": {"rsi": 65},
        "use_mock": True
    }
    response = client.post("/api/reasoning/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "ticker" in data
    assert data["ticker"] == "NVDA"
    assert "reasoning_trace" in data
    assert isinstance(data["reasoning_trace"], list)
