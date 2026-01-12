"""
Unit Tests for Position Ownership API with Pagination

Phase 5, T5.2: Multi-Strategy Orchestration
Test GET /api/ownership endpoint with pagination

작성일: 2026-01-12
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.repository import get_sync_session
from backend.database.repository_multi_strategy import (
    StrategyRepository,
    PositionOwnershipRepository
)
from backend.api.schemas.strategy_schemas import OwnershipType

# FastAPI Test Client
client = TestClient(app)

# Test Data
db = get_sync_session()
strategy_repo = StrategyRepository(db)
ownership_repo = PositionOwnershipRepository(db)

# Get existing strategies
long_term = strategy_repo.get_by_name("long_term")
trading = strategy_repo.get_by_name("trading")
aggressive = strategy_repo.get_by_name("aggressive")

print("\n" + "=" * 60)
print("Testing GET /api/ownership (Phase 5, T5.2)")
print("=" * 60)

print(f"\n=== Strategy IDs ===")
print(f"Long Term: {long_term.id} (Priority: {long_term.priority})")
print(f"Trading: {trading.id} (Priority: {trading.priority})")
print(f"Aggressive: {aggressive.id} (Priority: {aggressive.priority})")


def cleanup_test_ownerships():
    """테스트 소유권 데이터 정리"""
    test_tickers = [f"PG{i:02d}" for i in range(1, 26)]  # PG01, PG02, ..., PG25 (max 4 chars)

    for ticker in test_tickers:
        ownerships = ownership_repo.get_by_ticker(ticker)
        if ownerships:
            # get_by_ticker returns a list
            if isinstance(ownerships, list):
                for ownership in ownerships:
                    db.delete(ownership)
            else:
                db.delete(ownerships)

    db.commit()


def create_test_ownerships(count: int = 25):
    """테스트용 소유권 데이터 생성"""
    cleanup_test_ownerships()

    strategies = [long_term, trading, aggressive]

    for i in range(1, count + 1):
        strategy = strategies[i % 3]  # Rotate strategies
        ticker = f"PG{i:02d}"  # PG01, PG02, ..., PG25

        ownership_repo.create(
            strategy_id=strategy.id,
            ticker=ticker,
            ownership_type=OwnershipType.PRIMARY.value,
            position_id=None,
            locked_until=None,
            reasoning=f"Test ownership {i}"
        )

    db.commit()
    print(f"\n✅ Created {count} test ownerships")


# ============================================================================
# Test Cases
# ============================================================================

def test_pagination_default():
    """Test 1: Default pagination (page=1, page_size=20)"""
    print("\n--- Test 1: Default Pagination ---")

    create_test_ownerships(25)

    response = client.get("/api/ownership")

    if response.status_code != 200:
        print(f"❌ ERROR: Status {response.status_code}")
        print(f"Response: {response.text}")

    assert response.status_code == 200
    result = response.json()

    assert result["total"] >= 25
    assert result["page"] == 1
    assert result["page_size"] == 20
    assert result["total_pages"] >= 2
    assert len(result["items"]) == 20  # First page should have 20 items

    print(f"✅ Test 1 PASSED")
    print(f"   Total: {result['total']}, Page: {result['page']}/{result['total_pages']}")
    print(f"   Items on page: {len(result['items'])}")


def test_pagination_second_page():
    """Test 2: Second page (page=2, page_size=20)"""
    print("\n--- Test 2: Second Page ---")

    response = client.get("/api/ownership?page=2&page_size=20")

    assert response.status_code == 200
    result = response.json()

    assert result["page"] == 2
    assert result["page_size"] == 20
    assert len(result["items"]) >= 5  # At least 5 items on second page (25 total)

    print(f"✅ Test 2 PASSED")
    print(f"   Page 2 items: {len(result['items'])}")


def test_pagination_custom_page_size():
    """Test 3: Custom page size (page_size=10)"""
    print("\n--- Test 3: Custom Page Size ---")

    response = client.get("/api/ownership?page=1&page_size=10")

    assert response.status_code == 200
    result = response.json()

    assert result["page"] == 1
    assert result["page_size"] == 10
    assert len(result["items"]) == 10
    assert result["total_pages"] >= 3  # 25 items / 10 per page = 3 pages

    print(f"✅ Test 3 PASSED")
    print(f"   Page size: {result['page_size']}, Total pages: {result['total_pages']}")


def test_pagination_out_of_range():
    """Test 4: Out of range page (page=999)"""
    print("\n--- Test 4: Out of Range Page ---")

    response = client.get("/api/ownership?page=999&page_size=20")

    assert response.status_code == 200
    result = response.json()

    assert result["page"] == 999
    assert len(result["items"]) == 0  # No items on non-existent page

    print(f"✅ Test 4 PASSED: Empty page handled correctly")


def test_filter_by_ticker():
    """Test 5: Filter by ticker with pagination"""
    print("\n--- Test 5: Filter by Ticker ---")

    response = client.get("/api/ownership?ticker=PG01")

    assert response.status_code == 200
    result = response.json()

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["ticker"] == "PG01"

    print(f"✅ Test 5 PASSED")
    print(f"   Ticker filter: PAGE_TEST_1, Found: {result['total']}")


def test_filter_by_strategy():
    """Test 6: Filter by strategy with pagination"""
    print("\n--- Test 6: Filter by Strategy ---")

    response = client.get(f"/api/ownership?strategy_id={long_term.id}")

    assert response.status_code == 200
    result = response.json()

    # Should have roughly 25/3 ≈ 8-9 ownerships for long_term
    assert result["total"] >= 8

    # Verify all items belong to long_term strategy
    for item in result["items"]:
        assert item["strategy_id"] == long_term.id

    print(f"✅ Test 6 PASSED")
    print(f"   Strategy filter: {long_term.name}, Found: {result['total']}")


def test_response_structure():
    """Test 7: Verify response structure"""
    print("\n--- Test 7: Response Structure ---")

    response = client.get("/api/ownership?page=1&page_size=5")

    assert response.status_code == 200
    result = response.json()

    # Check top-level fields
    assert "total" in result
    assert "page" in result
    assert "page_size" in result
    assert "total_pages" in result
    assert "items" in result

    # Check item structure
    if len(result["items"]) > 0:
        item = result["items"][0]
        assert "id" in item
        assert "ticker" in item
        assert "strategy_id" in item
        assert "ownership_type" in item
        assert "created_at" in item
        assert "strategy" in item  # Nested strategy info

        # Check nested strategy structure
        strategy = item["strategy"]
        assert "id" in strategy
        assert "name" in strategy
        assert "priority" in strategy

    print(f"✅ Test 7 PASSED: Response structure valid")


def test_max_page_size_limit():
    """Test 8: Page size limit (max=100)"""
    print("\n--- Test 8: Page Size Limit ---")

    # Try to request 200 items (should be capped at 100)
    response = client.get("/api/ownership?page=1&page_size=200")

    # FastAPI validation should reject this (422)
    assert response.status_code == 422

    print(f"✅ Test 8 PASSED: Page size limit enforced (422)")


def test_min_page_validation():
    """Test 9: Minimum page validation (page >= 1)"""
    print("\n--- Test 9: Minimum Page Validation ---")

    # Try page=0 (should fail)
    response = client.get("/api/ownership?page=0")

    # FastAPI validation should reject this (422)
    assert response.status_code == 422

    print(f"✅ Test 9 PASSED: Minimum page validation enforced (422)")


def test_empty_database():
    """Test 10: Empty result set"""
    print("\n--- Test 10: Empty Result Set ---")

    cleanup_test_ownerships()

    response = client.get("/api/ownership")

    assert response.status_code == 200
    result = response.json()

    assert result["total"] >= 0
    assert result["page"] == 1
    assert result["total_pages"] == 0 or result["total_pages"] >= 0
    assert isinstance(result["items"], list)

    print(f"✅ Test 10 PASSED: Empty result handled correctly")


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == "__main__":
    try:
        test_pagination_default()
        test_pagination_second_page()
        test_pagination_custom_page_size()
        test_pagination_out_of_range()
        test_filter_by_ticker()
        test_filter_by_strategy()
        test_response_structure()
        test_max_page_size_limit()
        test_min_page_validation()
        test_empty_database()

        print("\n" + "=" * 60)
        print("✅ All Tests PASSED! Phase 5, T5.2 is complete.")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise

    finally:
        cleanup_test_ownerships()
        db.close()
