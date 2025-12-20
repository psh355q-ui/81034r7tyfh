"""
Test Trading Agent with Management Credibility Integration.
"""
import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_agent_with_management():
    """Test trading agent with management credibility."""
    from ai.trading_agent import TradingAgent
    from ai.claude_client import MockClaudeClient

    # Use mock client to avoid API key requirement
    print("ℹ️  Using MockClaudeClient for testing (no API key needed)")
    mock_client = MockClaudeClient()
    agent = TradingAgent(claude_client=mock_client)

    # Try to initialize, but continue even if Redis is not available
    try:
        await agent.initialize()
        print("✓ Feature store initialized")
    except Exception as e:
        print(f"⚠️  Feature store initialization failed (Redis not running): {e}")
        print("ℹ️  Continuing without cache (testing basic integration only)")
    
    print("\n" + "="*80)
    print("Testing Trading Agent with Management Credibility")
    print("="*80 + "\n")
    
    # Test stocks with different management profiles
    test_cases = [
        ("AAPL", "Tim Cook - Strong leadership"),
        ("TSLA", "Elon Musk - Controversial"),
        ("MSFT", "Satya Nadella - Excellent transformation"),
    ]
    
    for ticker, description in test_cases:
        print(f"\n📊 Testing {ticker}: {description}")
        print("-" * 80)
        
        try:
            decision = await agent.analyze(ticker)
            
            print(f"Action: {decision.action}")
            print(f"Conviction: {decision.conviction:.2f}")
            print(f"Position Size: {decision.position_size:.1f}%")
            
            mgmt_cred = decision.features_used.get('management_credibility', None)
            if mgmt_cred:
                print(f"Management Credibility: {mgmt_cred:.2f}")
            else:
                print(f"Management Credibility: N/A")
            
            print(f"Reasoning: {decision.reasoning}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Get metrics
    print("\n" + "="*80)
    print("📊 Metrics")
    print("="*80)
    
    metrics = agent.get_metrics()
    print(f"Total analyses: {metrics['total_analyses']}")
    print(f"Decisions: {metrics['decisions_by_action']}")
    
    # Claude metrics
    claude_metrics = metrics.get('claude_metrics', {})
    print(f"\nClaude API:")
    print(f"  Requests: {claude_metrics.get('total_requests', 0)}")
    print(f"  Cost: ${claude_metrics.get('total_cost_usd', 0):.4f}")
    
    # Management credibility metrics
    if hasattr(agent, 'management_credibility_calc'):
        mgmt_calc = agent.management_credibility_calc
        mgmt_metrics = mgmt_calc.get_metrics()
        print(f"\nManagement Credibility:")
        print(f"  API Calls: {mgmt_metrics['total_api_calls']}")
        print(f"  Cost: ${mgmt_metrics['total_cost_usd']:.4f}")
    else:
        print("\n⚠️  Management credibility calculator not initialized")
    
    await agent.close()
    
    print("\n✅ Integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_agent_with_management())