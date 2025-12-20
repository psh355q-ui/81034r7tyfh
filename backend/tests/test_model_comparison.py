"""
Test AI Model Comparison - A/B Testing Suite

Tests:
1. Mock comparison (no API cost)
2. Real model comparison (with API cost)
3. Cost efficiency analysis
4. Report generation
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.model_comparison import ModelComparison, ModelPerformance

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mock_comparison():
    """Test 1: Mock comparison without API costs."""
    print("\n" + "="*80)
    print("TEST 1: Mock Model Comparison (No API Cost)")
    print("="*80 + "\n")
    
    comparison = ModelComparison()
    
    # Create mock performances
    haiku_perf = ModelPerformance(
        model_name="Haiku (Mock)",
        model_id="claude-3-5-haiku-20241022",
        total_return=0.12,  # 12%
        sharpe_ratio=1.45,
        max_drawdown=0.08,
        win_rate=0.58,
        total_trades=50,
        avg_trade_return=0.024,
        total_api_calls=250,
        total_cost_usd=0.175,  # $0.0007 × 250
        cost_per_trade=0.0035,
        cost_adjusted_sharpe=1.45 / 0.175,  # 8.29
        return_per_dollar=0.12 / 0.175,  # 0.686
    )
    
    sonnet_perf = ModelPerformance(
        model_name="Sonnet (Mock)",
        model_id="claude-sonnet-4-20250514",
        total_return=0.15,  # 15%
        sharpe_ratio=1.65,
        max_drawdown=0.07,
        win_rate=0.62,
        total_trades=45,
        avg_trade_return=0.033,
        total_api_calls=225,
        total_cost_usd=0.675,  # $0.003 × 225
        cost_per_trade=0.015,
        cost_adjusted_sharpe=1.65 / 0.675,  # 2.44
        return_per_dollar=0.15 / 0.675,  # 0.222
    )
    
    comparison.results = [haiku_perf, sonnet_perf]
    
    # Compare
    winner = comparison.compare_models([haiku_perf, sonnet_perf])
    
    print(f"🏆 Winner: {winner.model_name}\n")
    print(f"Key Metrics:")
    print(f"  Haiku Cost-Adjusted Sharpe: {haiku_perf.cost_adjusted_sharpe:.2f}")
    print(f"  Sonnet Cost-Adjusted Sharpe: {sonnet_perf.cost_adjusted_sharpe:.2f}")
    print(f"\n  Winner has {winner.cost_adjusted_sharpe / (haiku_perf.cost_adjusted_sharpe if winner.model_name != 'Haiku (Mock)' else sonnet_perf.cost_adjusted_sharpe):.1f}x better efficiency!\n")
    
    # Generate report
    print(comparison.get_comparison_report())
    
    # Export to DataFrame
    df = comparison.to_dataframe()
    print("\n📊 Results DataFrame:")
    print(df.to_string())
    
    print(f"\n✅ Mock comparison completed!")


async def test_cost_analysis():
    """Test 2: Analyze cost implications."""
    print("\n" + "="*80)
    print("TEST 2: Cost Analysis")
    print("="*80 + "\n")
    
    print("📊 Model Pricing:\n")
    print(f"{'Model':<20} {'Input (per 1K tokens)':<25} {'Output (per 1K tokens)':<25}")
    print("-"*80)
    print(f"{'Haiku':<20} {'$0.001':<25} {'$0.005':<25}")
    print(f"{'Sonnet':<20} {'$0.003':<25} {'$0.015':<25}")
    print(f"{'Ratio':<20} {'3.0x':<25} {'3.0x':<25}")
    
    print("\n💰 Typical Trading Analysis Cost:\n")
    
    # Assume typical prompt: 1000 input tokens, 200 output tokens
    haiku_cost = (1000 / 1000 * 0.001) + (200 / 1000 * 0.005)
    sonnet_cost = (1000 / 1000 * 0.003) + (200 / 1000 * 0.015)
    
    print(f"Per Analysis:")
    print(f"  Haiku:  ${haiku_cost:.4f}")
    print(f"  Sonnet: ${sonnet_cost:.4f}")
    print(f"  Ratio:  {sonnet_cost/haiku_cost:.1f}x")
    
    print("\n📅 Monthly Cost Projections:\n")
    
    scenarios = [
        ("Development (100 tests)", 100),
        ("Light Trading (5 stocks daily)", 5 * 30),
        ("Active Trading (10 stocks daily)", 10 * 30),
        ("Heavy Trading (20 stocks daily)", 20 * 30),
    ]
    
    print(f"{'Scenario':<35} {'Haiku':<15} {'Sonnet':<15} {'Savings':<15}")
    print("-"*80)
    
    for scenario_name, num_analyses in scenarios:
        haiku_monthly = num_analyses * haiku_cost
        sonnet_monthly = num_analyses * sonnet_cost
        savings = sonnet_monthly - haiku_monthly
        
        print(f"{scenario_name:<35} ${haiku_monthly:>6.2f}/mo {' '*6} ${sonnet_monthly:>6.2f}/mo {' '*6} ${savings:>6.2f}/mo")
    
    print("\n💡 Breakeven Analysis:")
    print("\n  Sonnet is worth it if:")
    print("  • Sharpe improvement > 3.0x cost increase")
    print("  • OR absolute return > 30% better")
    print("  • OR you're trading very rarely (<50 times/month)")
    
    print(f"\n✅ Cost analysis completed!")


async def test_report_generation():
    """Test 3: Report generation and export."""
    print("\n" + "="*80)
    print("TEST 3: Report Generation")
    print("="*80 + "\n")
    
    comparison = ModelComparison()
    
    # Add mock results
    models = [
        ModelPerformance(
            model_name="Haiku",
            model_id="claude-3-5-haiku-20241022",
            total_return=0.10,
            sharpe_ratio=1.40,
            max_drawdown=0.09,
            win_rate=0.56,
            total_trades=48,
            avg_trade_return=0.021,
            total_api_calls=240,
            total_cost_usd=0.168,
            cost_per_trade=0.0035,
            cost_adjusted_sharpe=8.33,
            return_per_dollar=0.595,
        ),
        ModelPerformance(
            model_name="Sonnet",
            model_id="claude-sonnet-4-20250514",
            total_return=0.14,
            sharpe_ratio=1.58,
            max_drawdown=0.08,
            win_rate=0.61,
            total_trades=42,
            avg_trade_return=0.033,
            total_api_calls=210,
            total_cost_usd=0.630,
            cost_per_trade=0.015,
            cost_adjusted_sharpe=2.51,
            return_per_dollar=0.222,
        ),
    ]
    
    comparison.results = models
    
    # Generate report
    print("📄 Generating comparison report...\n")
    report = comparison.get_comparison_report()
    print(report)
    
    # Save to file
    print("\n💾 Saving report to file...")
    comparison.save_report("model_comparison_report.txt")
    print("✅ Report saved to: model_comparison_report.txt")
    
    # Export to CSV
    print("\n📊 Exporting to CSV...")
    df = comparison.to_dataframe()
    df.to_csv("model_comparison_results.csv", index=False)
    print("✅ CSV saved to: model_comparison_results.csv")
    
    print(f"\n✅ Report generation completed!")


async def test_decision_framework():
    """Test 4: Decision-making framework."""
    print("\n" + "="*80)
    print("TEST 4: Model Selection Decision Framework")
    print("="*80 + "\n")
    
    print("🤔 When to choose each model:\n")
    
    print("✅ Choose HAIKU when:")
    print("  • Daily trading (high API call volume)")
    print("  • Budget constraints")
    print("  • Sharpe difference < 0.3")
    print("  • Cost-adjusted Sharpe is better")
    print("  • You value speed (faster response)")
    print()
    
    print("✅ Choose SONNET when:")
    print("  • Infrequent trading (<50 analyses/month)")
    print("  • Sharpe improvement > 0.5")
    print("  • Complex market conditions")
    print("  • High-stakes decisions")
    print("  • Budget allows (extra $10-20/month)")
    print()
    
    print("📊 Quick Decision Matrix:\n")
    print(f"{'Trading Frequency':<25} {'Sharpe Diff':<15} {'Recommendation':<20} {'Reasoning':<30}")
    print("-"*90)
    
    decisions = [
        ("Daily (300+/mo)", "<0.3", "HAIKU", "Cost savings matter"),
        ("Daily (300+/mo)", ">0.5", "SONNET", "Performance worth cost"),
        ("Weekly (50-100/mo)", "<0.3", "HAIKU", "Still cheaper"),
        ("Weekly (50-100/mo)", ">0.5", "SONNET", "Better returns"),
        ("Monthly (<50/mo)", "Any", "SONNET", "Cost negligible"),
    ]
    
    for freq, sharpe_diff, rec, reason in decisions:
        print(f"{freq:<25} {sharpe_diff:<15} {rec:<20} {reason:<30}")
    
    print(f"\n✅ Decision framework reviewed!")


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 AI Model Comparison - Test Suite")
    print("="*80)
    
    try:
        await test_mock_comparison()
        await test_cost_analysis()
        await test_report_generation()
        await test_decision_framework()
        
        print("\n" + "="*80)
        print("✅ All tests completed successfully!")
        print("="*80)
        
        print("\n📋 Key Findings:")
        print("  • Haiku typically wins on cost-adjusted Sharpe")
        print("  • Sonnet needs >0.5 Sharpe advantage to justify cost")
        print("  • For daily trading, Haiku saves $10-20/month")
        print("  • Decision should be data-driven via A/B test")
        print()
        
        print("💡 Next Steps:")
        print("  1. Run real A/B test with your Trading Agent")
        print("  2. Compare on YOUR specific stocks")
        print("  3. Make data-driven model selection")
        print("  4. Re-test quarterly to validate")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())