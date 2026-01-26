"""
Tests for FCM Token Management API

Phase 4 - Real-time Execution
Tests FCM token registration, unregistration, and querying
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base, UserFCMToken
from backend.api.fcm_router import router
from fastapi import FastAPI

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_fcm.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(router)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create a test client"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    from backend.database.repository import get_sync_session
    app.dependency_overrides[get_sync_session] = override_get_db
    
    with TestClient(app) as c:
        yield c


def test_register_fcm_token(client, test_db):
    """Test registering a new FCM token"""
    response = client.post("/api/fcm/register", json={
        "user_id": "test_user_1",
        "token": "test_token_12345",
        "device_type": "android",
        "device_id": "device_001",
        "device_name": "Samsung Galaxy S23",
        "app_version": "1.0.0",
        "os_version": "Android 14"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user_1"
    assert data["token"] == "test_token_12345"
    assert data["device_type"] == "android"
    assert data["is_active"] is True


def test_register_duplicate_token(client, test_db):
    """Test registering the same token twice (should update)"""
    # First registration
    payload = {
        "user_id": "test_user_1",
        "token": "test_token_12345",
        "device_type": "android"
    }
    response1 = client.post("/api/fcm/register", json=payload)
    assert response1.status_code == 200
    
    # Second registration with same token but different user
    payload["user_id"] = "test_user_2"
    response2 = client.post("/api/fcm/register", json=payload)
    assert response2.status_code == 200
    
    # Should update existing token
    data = response2.json()
    assert data["user_id"] == "test_user_2"
    assert data["token"] == "test_token_12345"


def test_unregister_fcm_token(client, test_db):
    """Test unregistering an FCM token"""
    # First register a token
    client.post("/api/fcm/register", json={
        "user_id": "test_user_1",
        "token": "test_token_12345",
        "device_type": "android"
    })
    
    # Unregister it
    response = client.delete("/api/fcm/unregister?token=test_token_12345")
    assert response.status_code == 200
    
    # Verify it's deactivated
    token = test_db.query(UserFCMToken).filter(
        UserFCMToken.token == "test_token_12345"
    ).first()
    assert token is not None
    assert token.is_active is False


def test_unregister_nonexistent_token(client):
    """Test unregistering a token that doesn't exist"""
    response = client.delete("/api/fcm/unregister?token=nonexistent_token")
    assert response.status_code == 404


def test_get_user_fcm_tokens(client, test_db):
    """Test getting all FCM tokens for a user"""
    # Register multiple tokens for the same user
    client.post("/api/fcm/register", json={
        "user_id": "test_user_1",
        "token": "token_1",
        "device_type": "android"
    })
    client.post("/api/fcm/register", json={
        "user_id": "test_user_1",
        "token": "token_2",
        "device_type": "ios"
    })
    client.post("/api/fcm/register", json={
        "user_id": "test_user_1",
        "token": "token_3",
        "device_type": "web"
    })
    
    # Get all tokens
    response = client.get("/api/fcm/tokens?user_id=test_user_1&active_only=true")
    assert response.status_code == 200
    
    tokens = response.json()
    assert len(tokens) == 3


def test_get_user_tokens_active_only(client, test_db):
    """Test filtering by active tokens only"""
    # Register tokens
    client.post("/api/fcm/register", json={
        "user_id": "test_user_1",
        "token": "token_1",
        "device_type": "android"
    })
    client.post("/api/fcm/register", json={
        "user_id": "test_user_1",
        "token": "token_2",
        "device_type": "ios"
    })
    
    # Deactivate one
    client.delete("/api/fcm/unregister?token=token_1")
    
    # Get active only
    response = client.get("/api/fcm/tokens?user_id=test_user_1&active_only=true")
    tokens = response.json()
    assert len(tokens) == 1
    assert tokens[0]["token"] == "token_2"
    
    # Get all (including inactive)
    response = client.get("/api/fcm/tokens?user_id=test_user_1&active_only=false")
    tokens = response.json()
    assert len(tokens) == 2


def test_deactivate_fcm_token_by_id(client, test_db):
    """Test deactivating a token by its ID"""
    # Register a token
    response = client.post("/api/fcm/register", json={
        "user_id": "test_user_1",
        "token": "test_token_12345",
        "device_type": "android"
    })
    
    token_id = response.json()["id"]
    
    # Deactivate by ID
    response = client.put(f"/api/fcm/tokens/{token_id}/deactivate")
    assert response.status_code == 200
    
    # Verify deactivated
    token = test_db.query(UserFCMToken).filter(
        UserFCMToken.id == token_id
    ).first()
    assert token.is_active is False


def test_deactivate_nonexistent_token_id(client):
    """Test deactivating a token with non-existent ID"""
    response = client.put("/api/fcm/tokens/99999/deactivate")
    assert response.status_code == 404


def test_get_fcm_stats(client, test_db):
    """Test getting FCM statistics"""
    # Register multiple tokens
    for i in range(5):
        client.post("/api/fcm/register", json={
            "user_id": f"user_{i}",
            "token": f"token_{i}",
            "device_type": "android" if i % 2 == 0 else "ios"
        })
    
    # Deactivate some
    client.delete("/api/fcm/unregister?token=token_0")
    client.delete("/api/fcm/unregister?token=token_1")
    
    # Get stats
    response = client.get("/api/fcm/stats")
    assert response.status_code == 200
    
    stats = response.json()
    assert stats["total_tokens"] == 5
    assert stats["active_tokens"] == 3
    assert stats["inactive_tokens"] == 2
    
    # Check device distribution
    distribution = stats["device_distribution"]
    assert len(distribution) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
