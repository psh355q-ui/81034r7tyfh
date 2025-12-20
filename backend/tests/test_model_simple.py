"""
Simple Model Comparison Test (No Unicode Issues)
"""

import sys
from pathlib import Path

# Set UTF-8 encoding for stdout
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.model_comparison import ModelComparison, ModelPerformance


def test_model_performance_class():
    """Test ModelPerformance class."""
    print("\n" + "="*80)
    print("TEST 1: ModelPerformance Class")
    print("="*80 + "\n")

    # Create mock performance data
    perf = ModelPerformance(
        model_name="Haiku (Test)",
        total_return=0.12,
        sharpe_ratio=1.45,
        max_drawdown=0.08,
        win_rate=0.58,
        total_trades=50,
        total_cost=0.18,
        cost_per_trade=0.0036,
    )

    print(f"Model: {perf.model_name}")
    print(f"  Total Return:        {perf.total_return:.2%}")
    print(f"  Sharpe Ratio:        {perf.sharpe_ratio:.2f}")
    print(f"  Max Drawdown:        {perf.max_drawdown:.2%}")
    print(f"  Win Rate:            {perf.win_rate:.1%}")
    print(f"  Total Cost:          ${perf.total_cost:.2f}")
    print(f"  Cost per Trade:      ${perf.cost_per_trade:.4f}")

    # Calculate efficiency metrics
    cost_adj_sharpe = perf.cost_adjusted_sharpe()
    return_per_dollar = perf.return_per_dollar()

    print(f"\nEfficiency Metrics:")
    print(f"  Cost-Adj Sharpe:     {cost_adj_sharpe:.2f}")
    print(f"  Return per $:        {return_per_dollar:.2f}x")

    assert cost_adj_sharpe > 0
    assert return_per_dollar > 0

    print("\n[PASS] ModelPerformance test passed!")
    return True


def test_model_comparison_class():
    """Test ModelComparison class."""
    print("\n" + "="*80)
    print("TEST 2: ModelComparison Class")
    print("="*80 + "\n")

    # Create mock performances
    haiku_perf = ModelPerformance(
        model_name="Haiku",
        total_return=0.12,
        sharpe_ratio=1.45,
        max_drawdown=0.08,
        win_rate=0.58,
        total_trades=50,
        total_cost=0.18,
        cost_per_trade=0.0036,
    )

    sonnet_perf = ModelPerformance(
        model_name="Sonnet",
        total_return=0.14,
        sharpe_ratio=1.55,
        max_drawdown=0.07,
        win_rate=0.60,
        total_trades=50,
        total_cost=0.68,
        cost_per_trade=0.0136,
    )

    # Create comparison
    comparison = ModelComparison()
    comparison.haiku_performance = haiku_perf
    comparison.sonnet_performance = sonnet_perf

    print("Comparing Haiku vs Sonnet...\n")

    # Determine winner
    winner = comparison.determine_winner()
    print(f"Winner: {winner}\n")

    # Get recommendations
    recommendation = comparison.get_recommendation()
    print("Recommendation:")
    print(f"  Use {recommendation['recommended_model']} for production")
    print(f"  Reason: {recommendation['reason']}")

    assert winner in ["Haiku", "Sonnet"]
    assert recommendation['recommended_model'] in ["Haiku", "Sonnet"]

    print("\n[PASS] ModelComparison test passed!")
    return True


def test_mock_comparison():
    """Test mock model comparison."""
    print("\n" + "="*80)
    print("TEST 3: Mock Model Comparison")
    print("="*80 + "\n")

    # Create mock data (realistic values)
    haiku = ModelPerformance(
        model_name="Haiku (Mock)",
        total_return=0.12,
        sharpe_ratio=1.45,
        max_drawdown=0.08,
        win_rate=0.58,
        total_trades=50,
        total_cost=0.18,
        cost_per_trade=0.0036,
    )

    sonnet = ModelPerformance(
        model_name="Sonnet (Mock)",
        total_return=0.135,
        sharpe_ratio=1.55,
        max_drawdown=0.075,
        win_rate=0.60,
        total_trades=50,
        total_cost=0.68,
        cost_per_trade=0.0136,
    )

    print("Performance Comparison:\n")
    print(f"{'Metric':<25} {'Haiku':>12} {'Sonnet':>12} {'Winner':>12}")
    print("-"*65)

    # Compare metrics
    print(f"{'Total Return':<25} {haiku.total_return:>11.2%} {sonnet.total_return:>11.2%} {'Sonnet':>12}")
    print(f"{'Sharpe Ratio':<25} {haiku.sharpe_ratio:>12.2f} {sonnet.sharpe_ratio:>12.2f} {'Sonnet':>12}")
    print(f"{'Max Drawdown':<25} {haiku.max_drawdown:>11.2%} {sonnet.max_drawdown:>11.2%} {'Sonnet':>12}")
    print(f"{'Win Rate':<25} {haiku.win_rate:>11.1%} {sonnet.win_rate:>11.1%} {'Sonnet':>12}")
    print(f"{'Total Cost':<25} ${haiku.total_cost:>11.2f} ${sonnet.total_cost:>11.2f} {'Haiku':>12}")

    print("\nEfficiency Metrics (Cost-Adjusted):\n")
    haiku_cas = haiku.cost_adjusted_sharpe()
    sonnet_cas = sonnet.cost_adjusted_sharpe()
    winner = "Haiku" if haiku_cas > sonnet_cas else "Sonnet"

    print(f"{'Cost-Adj Sharpe':<25} {haiku_cas:>12.2f} {sonnet_cas:>12.2f} {winner:>12}")
    print(f"{'Return per $':<25} {haiku.return_per_dollar():>11.2f}x {sonnet.return_per_dollar():>11.2f}x")

    print(f"\nWinner: {winner}")
    print(f"  Key Metric: Cost-Adjusted Sharpe = {haiku_cas if winner == 'Haiku' else sonnet_cas:.2f}")

    assert haiku_cas > 0 and sonnet_cas > 0
    print("\n[PASS] Mock comparison test passed!")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("AI Model Comparison - Test Suite")
    print("="*80)

    try:
        test_model_performance_class()
        test_model_comparison_class()
        test_mock_comparison()

        print("\n" + "="*80)
        print("All tests completed successfully!")
        print("="*80 + "\n")

        print("Summary:")
        print("  - ModelPerformance class: PASS")
        print("  - ModelComparison class: PASS")
        print("  - Mock comparison: PASS")
        print("\nModel comparison module is ready to use!")
        print("\nNext steps:")
        print("  - Run real A/B test: python run_ab_test.py (costs ~$0.40)")
        print("  - Check cost analysis in integration guide")

        return True

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
