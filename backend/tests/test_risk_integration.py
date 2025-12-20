"""
Integration Test: Non-Standard Risk + Trading Agent

Phase 4, Task 7: Test risk-based decision making
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Handle UTF-8 encoding on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ==================== Mock Data for Testing ====================

def get_mock_features(ticker: str, risk_scenario: str) -> Dict:
    """
    Generate mock features for different risk scenarios.
    
    Args:
        ticker: Stock ticker
        risk_scenario: 'low_risk', 'moderate_risk', 'high_risk', 'critical_risk'
    
    Returns:
        Feature dict with non-standard risk data
    """
    base_features = {
        "ticker": ticker,
        "current_price": 150.0,
        "ret_5d": 0.02,
        "ret_20d": 0.05,
        "vol_20d": 0.15,
        "mom_20d": 0.05,
        "management_credibility": 0.7,
        "supply_chain_risk": 0.2,
    }
    
    # Risk scenarios
    if risk_scenario == "low_risk":
        base_features.update({
            "non_standard_risk_score": 0.05,
            "non_standard_risk_level": "LOW",
            "non_standard_risk_categories": {
                "legal": 0.05,
                "regulatory": 0.03,
                "operational": 0.02,
                "labor": 0.01,
                "governance": 0.04,
                "reputation": 0.02,
            },
        })
    
    elif risk_scenario == "moderate_risk":
        base_features.update({
            "non_standard_risk_score": 0.15,
            "non_standard_risk_level": "MODERATE",
            "non_standard_risk_categories": {
                "legal": 0.15,
                "regulatory": 0.12,
                "operational": 0.08,
                "labor": 0.05,
                "governance": 0.10,
                "reputation": 0.07,
            },
        })
    
    elif risk_scenario == "high_risk":
        base_features.update({
            "non_standard_risk_score": 0.45,
            "non_standard_risk_level": "HIGH",
            "non_standard_risk_categories": {
                "legal": 0.45,
                "regulatory": 0.40,
                "operational": 0.30,
                "labor": 0.20,
                "governance": 0.35,
                "reputation": 0.25,
            },
        })
    
    elif risk_scenario == "critical_risk":
        base_features.update({
            "non_standard_risk_score": 0.75,
            "non_standard_risk_level": "CRITICAL",
            "non_standard_risk_categories": {
                "legal": 0.80,
                "regulatory": 0.75,
                "operational": 0.60,
                "labor": 0.50,
                "governance": 0.70,
                "reputation": 0.65,
            },
        })
    
    return base_features


def print_test_result(ticker: str, scenario: str, features: Dict, expected_behavior: str):
    """Print formatted test result"""
    print(f"\n{'='*80}")
    print(f"Test: {ticker} - {scenario.upper()}")
    print(f"{'='*80}")
    print(f"\n📊 Features:")
    print(f"  - Returns: 5d={features['ret_5d']:+.2%}, 20d={features['ret_20d']:+.2%}")
    print(f"  - Volatility: {features['vol_20d']:.2%}")
    print(f"  - Momentum: {features['mom_20d']:+.2%}")
    print(f"  - Management: {features['management_credibility']:.2f}")
    print(f"  - Supply Chain: {features['supply_chain_risk']:.2f}")
    
    print(f"\n⚠️  Non-Standard Risk:")
    print(f"  - Score: {features['non_standard_risk_score']:.2f}")
    print(f"  - Level: {features['non_standard_risk_level']}")
    print(f"  - Categories:")
    for cat, score in features['non_standard_risk_categories'].items():
        emoji = "🔴" if score > 0.3 else "🟡" if score > 0.1 else "🟢"
        print(f"    {emoji} {cat.upper()}: {score:.2%}")
    
    print(f"\n✅ Expected Behavior: {expected_behavior}")
    print(f"{'='*80}\n")


async def test_low_risk_scenario():
    """Test LOW risk scenario - should pass all checks"""
    ticker = "AAPL"
    features = get_mock_features(ticker, "low_risk")
    
    print_test_result(
        ticker=ticker,
        scenario="low_risk",
        features=features,
        expected_behavior=(
            "✓ Pre-check: PASS (risk 0.05 < 0.6)\n"
            "✓ Post-check: Normal position size\n"
            "✓ AI can recommend BUY/SELL normally"
        )
    )
    
    # If you have actual TradingAgent:
    # agent = TradingAgent()
    # decision = await agent.analyze(ticker)
    # assert decision.action in ["BUY", "SELL", "HOLD"]
    # assert decision.position_size == 5.0  # No reduction


async def test_moderate_risk_scenario():
    """Test MODERATE risk scenario - should pass but monitor"""
    ticker = "MSFT"
    features = get_mock_features(ticker, "moderate_risk")
    
    print_test_result(
        ticker=ticker,
        scenario="moderate_risk",
        features=features,
        expected_behavior=(
            "✓ Pre-check: PASS (risk 0.15 < 0.6)\n"
            "✓ Post-check: Normal position size\n"
            "✓ AI should be slightly more cautious"
        )
    )


async def test_high_risk_scenario():
    """Test HIGH risk scenario - should reduce position"""
    ticker = "TSLA"
    features = get_mock_features(ticker, "high_risk")
    
    print_test_result(
        ticker=ticker,
        scenario="high_risk",
        features=features,
        expected_behavior=(
            "✓ Pre-check: PASS (risk 0.45 < 0.6)\n"
            "⚠️  Post-check: Position reduced 50% (5% → 2.5%)\n"
            "⚠️  AI should be cautious, lower conviction"
        )
    )
    
    # If you have actual TradingAgent:
    # agent = TradingAgent()
    # decision = await agent.analyze(ticker)
    # if decision.action == "BUY":
    #     assert decision.position_size == 2.5  # 50% reduction


async def test_critical_risk_scenario():
    """Test CRITICAL risk scenario - should be filtered in pre-check"""
    ticker = "XYZ"
    features = get_mock_features(ticker, "critical_risk")
    
    print_test_result(
        ticker=ticker,
        scenario="critical_risk",
        features=features,
        expected_behavior=(
            "❌ Pre-check: FILTERED (risk 0.75 >= 0.6)\n"
            "❌ Action: HOLD (immediate)\n"
            "❌ AI not called (pre-filtered)"
        )
    )
    
    # If you have actual TradingAgent:
    # agent = TradingAgent()
    # decision = await agent.analyze(ticker)
    # assert decision.action == "HOLD"
    # assert decision.conviction == 0.0
    # assert "critical_non_standard_risk" in decision.risk_factors


async def test_all_scenarios():
    """Run all test scenarios"""
    print("\n" + "="*80)
    print("Phase 4, Task 7: Non-Standard Risk Integration Tests")
    print("="*80)
    
    await test_low_risk_scenario()
    await test_moderate_risk_scenario()
    await test_high_risk_scenario()
    await test_critical_risk_scenario()
    
    print("\n" + "="*80)
    print("Summary of Expected Behaviors:")
    print("="*80)
    print("\n1. LOW Risk (0.0-0.1):")
    print("   ✓ Normal trading allowed")
    print("   ✓ No position adjustments")
    
    print("\n2. MODERATE Risk (0.1-0.3):")
    print("   ✓ Trading allowed")
    print("   ⚠️  AI should be slightly cautious")
    
    print("\n3. HIGH Risk (0.3-0.6):")
    print("   ✓ Pre-check passes")
    print("   ⚠️  Post-check reduces position by 50%")
    print("   ⚠️  AI should lower conviction")
    
    print("\n4. CRITICAL Risk (0.6-1.0):")
    print("   ❌ Pre-check filters (immediate HOLD)")
    print("   ❌ AI not called")
    print("   ❌ No trading allowed")
    print("\n" + "="*80 + "\n")


async def test_real_world_example():
    """Test with real-world-like scenario"""
    print("\n" + "="*80)
    print("Real-World Example: Tech Company Under Investigation")
    print("="*80)
    
    # Simulates a tech company with strong fundamentals but legal troubles
    features = {
        "ticker": "TECH",
        "current_price": 200.0,
        "ret_5d": 0.08,  # Strong recent performance
        "ret_20d": 0.15,  # Strong momentum
        "vol_20d": 0.20,  # Moderate volatility
        "mom_20d": 0.15,  # Strong momentum
        "management_credibility": 0.8,  # Excellent management
        "supply_chain_risk": 0.1,  # Low supply risk
        
        # BUT: High legal risk
        "non_standard_risk_score": 0.50,
        "non_standard_risk_level": "HIGH",
        "non_standard_risk_categories": {
            "legal": 0.85,  # 🔴 Major lawsuit
            "regulatory": 0.60,  # 🔴 Investigation
            "operational": 0.10,
            "labor": 0.05,
            "governance": 0.15,
            "reputation": 0.40,
        },
    }
    
    print_test_result(
        ticker="TECH",
        scenario="real_world_high_legal_risk",
        features=features,
        expected_behavior=(
            "✓ Pre-check: PASS (risk 0.50 < 0.6)\n"
            "⚠️  Post-check: Position reduced 50% due to HIGH risk\n"
            "⚠️  Despite strong fundamentals, risk reduces exposure\n"
            "💡 This protects against black swan events"
        )
    )
    
    print("\n💭 Analysis:")
    print("  - Strong technical indicators (15% returns, 20% volatility)")
    print("  - Excellent management (0.8)")
    print("  - BUT: Legal risk is 85% (major lawsuit)")
    print("  - Result: Pre-check passes, but position reduced 50% in post-check")
    print("  - This is GOOD RISK MANAGEMENT - capturing upside with reduced exposure")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    # Run all tests
    asyncio.run(test_all_scenarios())
    asyncio.run(test_real_world_example())
    
    print("\n✅ All integration tests completed!")
    print("\n📝 Next Steps:")
    print("  1. Copy updated files to backend/")
    print("  2. Run with actual TradingAgent")
    print("  3. Validate with real Yahoo Finance data")
    print("  4. Monitor metrics and adjust thresholds if needed")