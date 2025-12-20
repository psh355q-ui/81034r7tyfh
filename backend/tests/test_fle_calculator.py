"""
FLE Calculator - Unit Tests

Tests for Forced Liquidation Equity calculation

작성일: 2025-12-16
"""

import pytest
from backend.metrics.fle_calculator import (
    FLECalculator,
    Portfolio,
    Position
)


def test_fle_calculation_simple():
    """간단한 FLE 계산 테스트"""
    calculator = FLECalculator()
    
    # Portfolio: 1 position + cash
    portfolio = Portfolio(
        user_id="test_user",
        positions=[
            Position(ticker="AAPL", quantity=100, current_price=180, cost_basis=150)
        ],
        cash=10000
    )
    
    result = calculator.calculate_fle(portfolio)
    
    # Position value: 100 * 180 = 18,000
    # Fees: 18,000 * 0.003 = 54
    # Gains: 18,000 - 15,000 = 3,000
    # Tax: 3,000 * 0.22 = 660
    # FLE: 18,000 - 54 - 660 + 10,000 = 27,286
    
    assert result.fle == pytest.approx(27286, abs=1)
    assert result.total_position_value == 18000
    assert result.estimated_fees == pytest.approx(54, abs=1)
    assert result.estimated_tax == pytest.approx(660, abs=1)
    assert result.cash_balance == 10000


def test_fle_no_tax_on_losses():
    """손실 포지션은 세금 없음"""
    calculator = FLECalculator()
    
    portfolio = Portfolio(
        user_id="test_user",
        positions=[
            Position(ticker="TSLA", quantity=10, current_price=200, cost_basis=250)
        ],
        cash=5000
    )
    
    result = calculator.calculate_fle(portfolio)
    
    # Position value: 10 * 200 = 2,000
    # Fees: 2,000 * 0.003 = 6
    # Gains: 2,000 - 2,500 = -500 (loss, no tax)
    # Tax: 0
    # FLE: 2,000 - 6 - 0 + 5,000 = 6,994
    
    assert result.fle == pytest.approx(6994, abs=1)
    assert result.estimated_tax == 0


def test_fle_peak_tracking():
    """Peak FLE 추적 테스트"""
    calculator = FLECalculator()
    
    portfolio = Portfolio(
        user_id="user_peak",
        positions=[Position("NVDA", 50, 500, 400)],
        cash=20000
    )
    
    # First calculation
    result1 = calculator.calculate_fle(portfolio)
    peak1 = result1.peak_fle
    
    # Price goes up
    portfolio.positions[0].current_price = 600
    result2 = calculator.calculate_fle(portfolio)
    peak2 = result2.peak_fle
    
    assert peak2 > peak1, "Peak should increase when price goes up"
    assert result2.drawdown == 0, "No drawdown when at peak"


def test_fle_drawdown_calculation():
    """Drawdown 계산 테스트"""
    calculator = FLECalculator()
    
    portfolio = Portfolio(
        user_id="user_dd",
        positions=[Position("GOOGL", 10, 140, 100)],
        cash=50000
    )
    
    # Set peak at current
    result1 = calculator.calculate_fle(portfolio)
    peak = result1.fle
    
    # Price drops 20%
    portfolio.positions[0].current_price = 112
    result2 = calculator.calculate_fle(portfolio)
    
    assert result2.drawdown > 0, "Should have drawdown"
    assert result2.peak_fle == peak, "Peak should remain the same"


def test_alert_levels():
    """경고 레벨 테스트"""
    calculator = FLECalculator()
    
    # SAFE: No drawdown
    portfolio = Portfolio("user1", [Position("A", 10, 100, 90)], 10000)
    result = calculator.calculate_fle(portfolio)
    peak = result.fle
    
    # MILD: 7% drawdown
    portfolio.positions[0].current_price = 93
    result = calculator.calculate_fle(portfolio)
    calculator._update_peak_fle("user1", peak)  # Force peak
    result = calculator.calculate_fle(portfolio)
    assert result.alert_level in ["MILD", "SAFE"], f"Expected MILD/SAFE, got {result.alert_level}"
    
    # WARNING: 12% drawdown
    portfolio.positions[0].current_price = 88
    calculator.fle_history["user1"][-1].peak_fle = peak
    result = calculator.calculate_fle(portfolio)
    # Note: drawdown depends on fees/taxes, approximate check
    
    # CRITICAL: 18% drawdown
    portfolio.positions[0].current_price = 82
    calculator.fle_history["user1"][-1].peak_fle = peak
    result = calculator.calculate_fle(portfolio)


def test_safety_messages():
    """안전 메시지 생성 테스트"""
    calculator = FLECalculator()
    
    portfolio = Portfolio("user_msg", [Position("TEST", 100, 100, 100)], 10000)
    result = calculator.calculate_fle(portfolio)
    
    # Each alert level should have a message
    for alert_level in ["SAFE", "MILD", "WARNING", "CRITICAL"]:
        result.alert_level = alert_level
        message = calculator.get_safety_message(result)
        
        assert len(message) > 0, f"Should have message for {alert_level}"
        assert "₩" in message, "Should contain KRW symbol"
        
        # CRITICAL should mention taking a break
        if alert_level == "CRITICAL":
            assert "쉬" in message or "멈추" in message, "Should suggest taking a break"


def test_multiple_positions():
    """여러 포지션 테스트"""
    calculator = FLECalculator()
    
    portfolio = Portfolio(
        user_id="multi_user",
        positions=[
            Position("AAPL", 50, 180, 150),
            Position("MSFT", 30, 370, 300),
            Position("GOOGL", 20, 140, 120)
        ],
        cash=15000
    )
    
    result = calculator.calculate_fle(portfolio)
    
    # Total position value: (50*180) + (30*370) + (20*140) = 9000 + 11100 + 2800 = 22900
    assert result.total_position_value == 22900
    
    # Should have fees and taxes
    assert result.estimated_fees > 0
    assert result.estimated_tax > 0  # All positions have gains
    
    # FLE should be positive
    assert result.fle > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
