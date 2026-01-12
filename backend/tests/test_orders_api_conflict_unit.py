"""
Unit Test for Orders API Conflict Checking Endpoint

Phase 5, Task T5.1

Tests the POST /api/orders/check-conflict endpoint using FastAPI TestClient.
Does not require a running server.

Prerequisites:
    - PostgreSQL with seed strategies loaded
    - Strategies: long_term (100), dividend (90), trading (50), aggressive (30)

Run:
    pytest backend/tests/test_orders_api_conflict_unit.py -v
    or
    python backend/tests/test_orders_api_conflict_unit.py
"""

import sys
sys.path.insert(0, 'd:/code/ai-trading-system')

from dotenv import load_dotenv
load_dotenv('d:/code/ai-trading-system/.env')

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.repository import get_sync_session
from backend.database.repository_multi_strategy import StrategyRepository, PositionOwnershipRepository
from backend.api.schemas.strategy_schemas import OrderAction

# FastAPI Test Client
client = TestClient(app)

# Setup: Get strategy IDs
db = get_sync_session()
strategy_repo = StrategyRepository(db)
ownership_repo = PositionOwnershipRepository(db)

long_term = strategy_repo.get_by_name("long_term")    # Priority: 100
trading = strategy_repo.get_by_name("trading")        # Priority: 50
aggressive = strategy_repo.get_by_name("aggressive")  # Priority: 30

TICKER = "AAPL_TEST"  # Max 10 chars per schema

# Cleanup function
def cleanup_ownership():
    existing_own = ownership_repo.get_primary_ownership(TICKER)
    if existing_own:
        db.delete(existing_own)
        db.commit()

cleanup_ownership()

def test_no_ownership_allowed():
    """Test 1: No ownership exists - Should be ALLOWED"""
    print("\n--- Test 1: No Ownership (Should be ALLOWED) ---")

    cleanup_ownership()

    payload = {
        "strategy_id": trading.id,
        "ticker": TICKER,
        "action": "buy",  # OrderAction enum value
        "quantity": 100
    }

    response = client.post("/api/orders/check-conflict", json=payload)

    if response.status_code != 200:
        print(f"❌ ERROR: Status {response.status_code}")
        print(f"Response: {response.json()}")

    assert response.status_code == 200
    result = response.json()

    assert result["has_conflict"] == False
    assert result["resolution"] == "allowed"
    assert result["can_proceed"] == True

    print(f"✅ Test 1 PASSED: {result['reasoning']}")


def test_blocked_by_higher_priority():
    """Test 2: Long-Term owns, Trading attempts - Should be BLOCKED"""
    print("\n--- Test 2: Long-Term owns, Trading attempts (Should be BLOCKED) ---")

    cleanup_ownership()

    # Assign ownership to long_term
    ownership_repo.create(long_term.id, TICKER, "primary", reasoning="Long-term hold")
    db.commit()

    payload = {
        "strategy_id": trading.id,
        "ticker": TICKER,
        "action": "buy",  # OrderAction enum value
        "quantity": 100
    }

    response = client.post("/api/orders/check-conflict", json=payload)

    assert response.status_code == 200
    result = response.json()

    assert result["has_conflict"] == True
    assert result["resolution"] == "blocked"
    assert result["can_proceed"] == False
    assert result["conflict_detail"] is not None
    assert result["conflict_detail"]["owning_strategy_name"] == "long_term"

    print(f"✅ Test 2 PASSED: {result['reasoning']}")


def test_same_strategy_allowed():
    """Test 3: Long-Term owns, Long-Term attempts - Should be ALLOWED"""
    print("\n--- Test 3: Long-Term owns, Long-Term attempts (Should be ALLOWED) ---")

    # Ownership already assigned from test 2
    payload = {
        "strategy_id": long_term.id,
        "ticker": TICKER,
        "action": "buy",  # OrderAction enum value
        "quantity": 50
    }

    response = client.post("/api/orders/check-conflict", json=payload)

    assert response.status_code == 200
    result = response.json()

    assert result["has_conflict"] == False
    assert result["resolution"] == "allowed"
    assert result["can_proceed"] == True

    print(f"✅ Test 3 PASSED: {result['reasoning']}")


def test_priority_override():
    """Test 4: Aggressive owns, Long-Term attempts - Should be PRIORITY_OVERRIDE"""
    print("\n--- Test 4: Aggressive owns, Long-Term attempts (Should be PRIORITY_OVERRIDE) ---")

    cleanup_ownership()

    # Assign ownership to aggressive
    ownership_repo.create(aggressive.id, TICKER, "primary", reasoning="Aggressive trade")
    db.commit()

    payload = {
        "strategy_id": long_term.id,
        "ticker": TICKER,
        "action": "buy",  # OrderAction enum value
        "quantity": 200
    }

    response = client.post("/api/orders/check-conflict", json=payload)

    assert response.status_code == 200
    result = response.json()

    assert result["has_conflict"] == True
    assert result["resolution"] == "priority_override"
    assert result["can_proceed"] == True
    assert result["conflict_detail"] is not None
    assert result["conflict_detail"]["owning_strategy_name"] == "aggressive"

    print(f"✅ Test 4 PASSED: {result['reasoning']}")


def test_invalid_strategy_id():
    """Test 5: Invalid Strategy ID - Should be 404"""
    print("\n--- Test 5: Invalid Strategy ID (Should be 404) ---")

    payload = {
        "strategy_id": "00000000-0000-0000-0000-000000000000",
        "ticker": TICKER,
        "action": "buy",  # OrderAction enum value
        "quantity": 100
    }

    response = client.post("/api/orders/check-conflict", json=payload)

    assert response.status_code == 404
    result = response.json()
    assert "not found" in result["detail"].lower()

    print(f"✅ Test 5 PASSED: {result['detail']}")


def test_inactive_strategy():
    """Test 6: Inactive Strategy - Should be 400"""
    print("\n--- Test 6: Inactive Strategy (Should be 400) ---")

    # Deactivate aggressive strategy
    aggressive_strat = strategy_repo.get_by_id(aggressive.id)
    strategy_repo.deactivate(aggressive.id)
    db.commit()

    payload = {
        "strategy_id": aggressive.id,
        "ticker": TICKER,
        "action": "buy",  # OrderAction enum value
        "quantity": 100
    }

    response = client.post("/api/orders/check-conflict", json=payload)

    assert response.status_code == 400
    result = response.json()
    assert "inactive" in result["detail"].lower()

    print(f"✅ Test 6 PASSED: {result['detail']}")

    # Reactivate for cleanup
    strategy_repo.activate(aggressive.id)
    db.commit()


if __name__ == "__main__":
    print("="*60)
    print("Testing POST /api/orders/check-conflict (Phase 5, T5.1)")
    print("="*60)

    print(f"\n=== Strategy IDs ===")
    print(f"Long Term: {long_term.id} (Priority: {long_term.priority})")
    print(f"Trading: {trading.id} (Priority: {trading.priority})")
    print(f"Aggressive: {aggressive.id} (Priority: {aggressive.priority})")

    try:
        test_no_ownership_allowed()
        test_blocked_by_higher_priority()
        test_same_strategy_allowed()
        test_priority_override()
        test_invalid_strategy_id()
        test_inactive_strategy()

        print("\n" + "="*60)
        print("✅ All Tests PASSED! Phase 5, T5.1 is complete.")
        print("="*60)

    finally:
        # Cleanup
        cleanup_ownership()
        db.close()
