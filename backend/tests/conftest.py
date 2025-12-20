import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
import os

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["KIS_MOCK_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from backend.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client() -> Generator:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_kis_client():
    """Mock KIS API client for testing."""
    class MockKISClient:
        def __init__(self):
            self.authenticated = True
        
        async def buy(self, ticker, quantity):
            return {"order_id": "TEST123", "status": "filled"}
        
        async def sell(self, ticker, quantity):
            return {"order_id": "TEST456", "status": "filled"}
    
    return MockKISClient()
