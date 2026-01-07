
"""
Test Tax Optimizer
==================
Tests the TaxOptimizer logic for maximizing the 2.5m KRW annual deduction.
"""
import sys
import os

# Add project root path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ai.portfolio.tax_optimizer import TaxOptimizer

def test_tax_optimizer():
    print("💰 Testing Tax Optimizer (Korean Market)...\n")
    
    # Scene: Use FX Rate 1400. Deduction Limit 2,500,000 KRW.
    optimizer = TaxOptimizer(fx_rate_krw=1400.0)
    
    # Test Case 1: Big Gain in NVDA, Small Gain in AAPL
    portfolio = [
        {
            "symbol": "NVDA", 
            "quantity": 10, 
            "average_price": 400.0, 
            "current_price": 500.0  # Gain $100/share = 140,000 KRW/share
        },
        {
            "symbol": "AAPL", 
            "quantity": 50, 
            "average_price": 150.0, 
            "current_price": 160.0  # Gain $10/share = 14,000 KRW/share
        }
    ]
    
    # We have 0 realized gain so far.
    # Total deduction available: 2,500,000 KRW.
    # NVDA gain: 140,000 * 10 = 1,400,000 KRW.
    # AAPL gain: 14,000 * 50 = 700,000 KRW.
    # Total potential gain: 2,100,000 KRW.
    # Should recommend selling ALL because 2.1m < 2.5m.
    
    print("--- Case 1: Gains < Limit ---")
    result1 = optimizer.optimize_sales(portfolio, realized_gain_ytd_krw=0)
    print(f"Status: {result1['status']}")
    print(f"Total Expected Gain: {result1['expected_total_gain_krw']:,.0f} KRW")
    for rec in result1['recommendations']:
        print(f"  Sell {rec['quantity']} {rec['symbol']} (~{rec['estimated_gain_krw']:,.0f} KRW)")
        
    print("\n")
    
    # Test Case 2: Huge Gain exceeding Limit
    # NVDA gain: 140,000 KRW per share.
    # We have 100 shares. Total potential 14,000,000 KRW.
    # Takes 2,500,000 / 140,000 = ~17.8 shares.
    # Should recommend selling 17 shares (2,380,000 KRW).
    
    portfolio2 = [
        {
            "symbol": "NVDA", 
            "quantity": 100, 
            "average_price": 400.0, 
            "current_price": 500.0  # Gain 140k/share
        }
    ]
    
    print("--- Case 2: Gains > Limit ---")
    result2 = optimizer.optimize_sales(portfolio2, realized_gain_ytd_krw=0)
    
    print(f"Status: {result2['status']}")
    print(f"Total Expected Gain: {result2['expected_total_gain_krw']:,.0f} KRW")
    for rec in result2['recommendations']:
        print(f"  Sell {rec['quantity']} {rec['symbol']} (~{rec['estimated_gain_krw']:,.0f} KRW)")
        
    # Check Math
    # 17 shares * 140,000 = 2,380,000.
    # 18 shares * 140,000 = 2,520,000 (Exceeds limit by 20k).
    # Logic should be conservative (17 shares).
    
    print("\n")
    
    if result2['recommendations'][0]['quantity'] == 17:
        print("✅ SUCCESS: Correctly calculated max shares to sell under limit.")
    else:
        print(f"❌ FAIL: Expected 17 shares, got {result2['recommendations'][0]['quantity']}")

if __name__ == "__main__":
    test_tax_optimizer()
