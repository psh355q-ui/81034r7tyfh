import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.analytics.portfolio_manager import PortfolioManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("================================================================================")
    print("                    Starting Risk Management Analysis Simulation")
    print("================================================================================")
    
    manager = PortfolioManager()
    
    # 1. Create a "Dangerous" Portfolio Scenario
    # Highly concentrated in AAPL (Tech), High correlation potential
    print("\n[Scenario 1] High Concentration & Imbalance")
    current_positions = [
        # Ticker, Quantity, Entry, Current, Weight (Approx for simulation)
        {"ticker": "AAPL", "quantity": 100, "entry_price": 150, "current_price": 220, "weight": 55.0, "value": 22000},
        {"ticker": "NVDA", "quantity": 10, "entry_price": 400, "current_price": 900, "weight": 22.5, "value": 9000},
        {"ticker": "MSFT", "quantity": 20, "entry_price": 300, "current_price": 450, "weight": 22.5, "value": 9000},
    ]
    
    # Normalize weights strictly for the test input
    total_val = sum(p["value"] for p in current_positions)
    for p in current_positions:
        p["weight"] = (p["value"] / total_val) * 100
        
    print(f"Total Portfolio Value: ${total_val:,.2f}")
    for p in current_positions:
        print(f"  - {p['ticker']}: {p['weight']:.1f}% (${p['value']:,.0f})")
    
    # 2. Run Analysis
    print("\nRunning PortfolioManager.analyze_portfolio()...")
    analysis = await manager.analyze_portfolio(current_positions)
    
    # 3. Print Results
    print("\n[Analysis Results]")
    print(f"Status: {analysis['status']}")
    
    if analysis['warnings']:
        print("\n[Warnings]")
        for w in analysis['warnings']:
            print(f"  ⚠️  {w}")
            
    if analysis['rebalancing_suggestions']:
        print("\n[Rebalancing Suggestions]")
        for s in analysis['rebalancing_suggestions']:
            print(f"  ⚡ {s['action']} {s['ticker']} -> Reason: {s['reason']} (Reduce by {s['target_weight_reduction']:.1f}%)")
            
    print("\n[Metrics]")
    for k, v in analysis['metrics'].items():
        if isinstance(v, float):
            print(f"  - {k}: {v:.4f}")
        else:
            print(f"  - {k}: {v}")

    # 4. Simulate Equity Curve for Drawdown Check
    print("\n\n[Scenario 2] Drawdown Check")
    # Simulate a drop: 100 -> 110 -> 90 (approx 18% drop from peak)
    equity_curve = [100000, 105000, 110000, 100000, 95000, 90000] 
    
    print(f"Equity Curve: {equity_curve}")
    dd_analysis = await manager.analyze_portfolio(current_positions, equity_curve)
    
    if "metrics" in dd_analysis and "max_drawdown_pct" in dd_analysis["metrics"]:
        print(f"  Max Drawdown: {dd_analysis['metrics']['max_drawdown_pct']:.2f}%")
        
    if dd_analysis['warnings']:
        print(f"  Warnings: {dd_analysis['warnings']}")

    print("\n================================================================================")
    print("Risk Analysis Simulation Complete")

if __name__ == "__main__":
    asyncio.run(main())
