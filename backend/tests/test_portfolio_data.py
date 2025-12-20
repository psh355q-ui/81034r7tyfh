"""
Test Portfolio API with seed data

Follows test patterns from:
- backend/tests/conftest.py (TestClient setup)
- tests/test_full_system.py (integration testing)
- tests/test_kis_integration.py (complete validation)
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app


@pytest.mark.integration
def test_portfolio_with_seed_data():
    """Verify Portfolio API returns correct data after seeding"""
    client = TestClient(app)
    
    print("\n" + "=" * 80)
    print("Testing Portfolio API with Seed Data")
    print("=" * 80)
    
    response = client.get("/api/portfolio")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    
    # Validate structure (matches PortfolioResponse model)
    print("\n[Structure Validation]")
    required_fields = [
        "active_positions", "total_positions", "avg_return",
        "best_performer", "worst_performer",
        "total_value", "cash", "positions_value",
        "daily_pnl", "total_pnl",
        "daily_return_pct", "total_return_pct",
        "recent_trades"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
        print(f"  ✓ {field}")
    
    # Validate non-zero values (after seed)
    print("\n[Data Validation]")
    assert data["total_positions"] > 0, "Should have active positions"
    print(f"  ✓ Active positions: {data['total_positions']}")
    
    assert data["total_value"] > 0, "Portfolio value should be > 0"
    print(f"  ✓ Total value: ${data['total_value']:,.2f}")
    
    assert data["cash"] >= 0, "Cash should be >= 0"
    print(f"  ✓ Cash: ${data['cash']:,.2f}")
    
    assert data["positions_value"] > 0, "Positions value should be > 0"
    print(f"  ✓ Positions value: ${data['positions_value']:,.2f}")
    
    assert len(data["active_positions"]) > 0, "Should have position list"
    print(f"  ✓ Position count: {len(data['active_positions'])}")
    
    # Validate position structure
    print("\n[Position Structure Validation]")
    position = data["active_positions"][0]
    position_fields = [
        "ticker", "signal_type", "action", "confidence",
        "entry_date", "entry_price", "current_price", "quantity",
        "market_value", "unrealized_pnl", "unrealized_pnl_pct",
        "return_pct", "days_held", "reasoning"
    ]
    
    for field in position_fields:
        assert field in position, f"Position missing field: {field}"
    
    print(f"  ✓ Sample position: {position['ticker']}")
    print(f"    - Entry: ${position['entry_price']:.2f}")
    print(f"    - Current: ${position['current_price']:.2f}")
    print(f"    - Return: {position['return_pct']:.2f}%")
    
    # Validate financial calculations
    print("\n[Financial Calculations]")
    calculated_total = data["positions_value"] + data["cash"]
    assert abs(calculated_total - data["total_value"]) < 0.01, \
        f"Total value mismatch: {calculated_total} vs {data['total_value']}"
    print(f"  ✓ Total value = positions + cash: ${calculated_total:,.2f}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Portfolio API Test Summary")
    print("=" * 80)
    print(f"✅ Total Positions: {data['total_positions']}")
    print(f"✅ Total Value: ${data['total_value']:,.2f}")
    print(f"✅ Cash Available: ${data['cash']:,.2f}")
    print(f"✅ Positions Value: ${data['positions_value']:,.2f}")
    print(f"✅ Total P&L: ${data['total_pnl']:,.2f} ({data['total_return_pct']:.2f}%)")
    print(f"✅ Recent Trades: {len(data['recent_trades'])}")
    print("=" * 80)
    
    return data


if __name__ == "__main__":
    # Allow running directly for quick testing
    test_portfolio_with_seed_data()
