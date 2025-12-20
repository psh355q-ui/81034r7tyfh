"""
Simplified Dry Run Test for Constitutional AI Trading System

This script demonstrates the core Constitutional system functionality
without requiring external API credentials (KIS, Telegram, AI models).

Author: AI Trading System Team
Date: 2025-12-18
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.constitution.constitution import Constitution
from backend.data.models.proposal import Proposal
from backend.backtesting.constitutional_backtest_engine import ConstitutionalBacktestEngine
from backend.backtesting.portfolio_manager import PortfolioManager

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def simulate_trading_proposal(ticker: str, action: str, price: float, confidence: float):
    """Simulate a trading proposal without AI models."""
    proposal = Proposal(
        ticker=ticker,
        action=action,
        target_price=price,
        confidence=confidence,
        reasoning=f"Simulated {action} decision for {ticker} based on mock analysis",
        created_at=datetime.utcnow(),
        status='PENDING'
    )
    return proposal

def main():
    print_section("🏛️  Constitutional AI Trading System - Dry Run Test")
    
    # 1. Initialize Constitution
    print("\n✅ Step 1: Initializing Constitution...")
    constitution = Constitution()
    print(f"   Version: {constitution.VERSION}")
    print(f"   Articles: {len(constitution.get_constitution_summary().split('제'))-1}")
    
    # 2. Create Portfolio Manager
    print("\n✅ Step 2: Initializing Portfolio Manager...")
    portfolio = PortfolioManager(initial_capital=100000.0)
    print(f"   Initial Capital: ${portfolio.initial_capital:,.2f}")
    print(f"   Cash Available: ${portfolio.cash:,.2f}")
    
    # 3. Simulate Trading Proposals
    print_section("📊 Trading Proposal Simulation")
    
    test_cases = [
        {"ticker": "AAPL", "action": "BUY", "price": 150.0, "confidence": 0.85, "shares": 100},
        {"ticker": "TSLA", "action": "BUY", "price": 250.0, "confidence": 0.75, "shares": 80},
        {"ticker": "MSFT", "action": "BUY", "price": 380.0, "confidence": 0.90, "shares": 50},
    ]
    
    approved_count = 0
    rejected_count = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Proposal {i}: {test['action']} {test['ticker']} ---")
        
        # Create proposal
        proposal = simulate_trading_proposal(
            test['ticker'], test['action'], test['price'], test['confidence']
        )
        
        # Get current portfolio state
        current_prices = {t['ticker']: t['price'] for t in test_cases}
        total_equity = portfolio.get_current_equity(current_prices)
        
        portfolio_context = {
            "cash": portfolio.cash,
            "total_equity": total_equity,
           "positions": portfolio.positions
        }
        
        # Constitution Validation (convert Proposal ORM to dict)
        proposal_dict = {
            'ticker': proposal.ticker,
            'action': proposal.action,
            'position_value': test['shares'] * test['price'],
            'order_value_usd': test['shares'] * test['price'],
            'is_approved': False
        }
        
        is_valid, violations, violated_articles = constitution.validate_proposal(proposal_dict, portfolio_context)
        
        if is_valid:
            print(f"   ✅ 헌법 승인 (통과)")
            print(f"   거래 실행 중: {test['shares']} 주 @ ${test['price']}")
            
            success = portfolio.execute_trade(
                ticker=test['ticker'],
                action=test['action'],
                amount=test['shares'],
                price=test['price'],
                date=datetime.utcnow(),
                reason="Constitutional Approval"
            )
            
            if success:
                approved_count += 1
                print(f"   ✅ 거래 실행 완료")
            else:
                print(f"   ⚠️  거래 실행 실패 (자금 부족?)")
        else:
            print(f"   ❌ 헌법 거부")
            print(f"   위반 사유: {violations}")
            if violated_articles:
                print(f"   위반 조항: {violated_articles}")
            rejected_count += 1
    
    # 4. Portfolio Summary
    print_section("💼 Portfolio Summary")
    final_equity = portfolio.get_current_equity(current_prices)
    print(f"   Initial Capital: ${portfolio.initial_capital:,.2f}")
    print(f"   Final Equity: ${final_equity:,.2f}")
    print(f"   Cash Remaining: ${portfolio.cash:,.2f}")
    print(f"   Total Return: {((final_equity - portfolio.initial_capital) / portfolio.initial_capital * 100):.2f}%")
    print(f"\n   Open Positions: {len(portfolio.positions)}")
    for ticker, pos in portfolio.positions.items():
        print(f"      - {ticker}: {pos['shares']} shares @ ${pos['entry_price']:.2f}")
    
    # 5. Trading Statistics
    print_section("📈 Trading Statistics")
    print(f"   Proposals Submitted: {len(test_cases)}")
    print(f"   ✅ Approved: {approved_count}")
    print(f"   ❌ Rejected: {rejected_count}")
    print(f"   Approval Rate: {(approved_count/len(test_cases)*100):.1f}%")
    print(f"   Total Trades: {len(portfolio.trades)}")
    
    # 6. Constitutional Metrics
    print_section("🏛️  Constitutional Performance")
    metrics = portfolio.get_metrics()
    print(f"   Capital Preservation: {((final_equity / portfolio.initial_capital) * 100):.2f}%")
    print(f"   Risk Management: {'✅ Active' if constitution else '❌ Disabled'}")
    print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
    
    print("\n" + "="*60)
    print("✅ Dry Run Test Completed Successfully!")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during dry run: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
