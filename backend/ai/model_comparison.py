"""
AI Model A/B Testing Module for AI Trading System.

Compare different Claude models to find optimal performance/cost balance:
- Claude 3.5 Haiku: Fast, cheap ($0.0007/analysis)
- Claude 3.5 Sonnet: Smarter, expensive ($0.003/analysis)

Methodology:
1. Run backtest with Haiku
2. Run backtest with Sonnet
3. Compare:
   - Sharpe Ratio
   - Total Return
   - Cost
   - Cost-adjusted Sharpe (Sharpe / Cost)
4. Select optimal model

Cost: ~$2.00 for comprehensive comparison (100 days × 5 stocks × 2 models)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ModelPerformance:
    """Performance metrics for a single model."""
    model_name: str
    model_id: str
    
    # Performance
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    
    # Trading
    total_trades: int
    avg_trade_return: float
    
    # Cost
    total_api_calls: int
    total_cost_usd: float
    cost_per_trade: float
    
    # Efficiency
    cost_adjusted_sharpe: float  # Sharpe / Cost
    return_per_dollar: float  # Return / Cost


class ModelComparison:
    """
    Compare different AI models for trading performance.
    
    Usage:
        comparison = ModelComparison()
        
        # Test Haiku
        result_haiku = await comparison.test_model(
            model_name="Haiku",
            model_id="claude-3-5-haiku-20241022",
            ...
        )
        
        # Test Sonnet
        result_sonnet = await comparison.test_model(
            model_name="Sonnet",
            model_id="claude-sonnet-4-20250514",
            ...
        )
        
        # Compare
        winner = comparison.compare_models([result_haiku, result_sonnet])
        print(comparison.get_comparison_report())
    """
    
    def __init__(self):
        """Initialize comparison module."""
        self.results: List[ModelPerformance] = []
        logger.info("ModelComparison initialized")
    
    async def test_model(
        self,
        model_name: str,
        model_id: str,
        backtest_engine,
        trading_agent_factory,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime,
        feature_store,
        initial_capital: float = 100000.0,
    ) -> ModelPerformance:
        """
        Test a single model with backtest.
        
        Args:
            model_name: Human-readable name (e.g., "Haiku")
            model_id: Claude model ID
            backtest_engine: BacktestEngine instance
            trading_agent_factory: Function that creates TradingAgent with specific model
            tickers: List of tickers to test
            start_date: Backtest start
            end_date: Backtest end
            feature_store: FeatureStore instance
            initial_capital: Starting capital
        
        Returns:
            ModelPerformance with all metrics
        """
        logger.info(f"Testing model: {model_name} ({model_id})")
        
        # Create agent with specific model
        agent = trading_agent_factory(model_id=model_id)
        await agent.initialize()
        
        # Run backtest
        backtest_results = await backtest_engine.run(
            trading_agent=agent,
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            feature_store=feature_store,
        )
        
        # Get Claude API metrics
        claude_metrics = agent.get_metrics().get('claude_metrics', {})
        
        # Calculate efficiency metrics
        total_cost = claude_metrics.get('total_cost_usd', 0.0)
        cost_adjusted_sharpe = (
            backtest_results['sharpe_ratio'] / total_cost
            if total_cost > 0 else 0.0
        )
        
        return_per_dollar = (
            backtest_results['total_return'] / total_cost
            if total_cost > 0 else 0.0
        )
        
        cost_per_trade = (
            total_cost / backtest_results['total_trades']
            if backtest_results['total_trades'] > 0 else 0.0
        )
        
        # Create performance object
        performance = ModelPerformance(
            model_name=model_name,
            model_id=model_id,
            total_return=backtest_results['total_return'],
            sharpe_ratio=backtest_results['sharpe_ratio'],
            max_drawdown=backtest_results['max_drawdown'],
            win_rate=backtest_results['win_rate'],
            total_trades=backtest_results['total_trades'],
            avg_trade_return=backtest_results['avg_trade_return'],
            total_api_calls=claude_metrics.get('total_requests', 0),
            total_cost_usd=total_cost,
            cost_per_trade=cost_per_trade,
            cost_adjusted_sharpe=cost_adjusted_sharpe,
            return_per_dollar=return_per_dollar,
        )
        
        self.results.append(performance)
        
        logger.info(
            f"{model_name} completed: "
            f"{performance.total_return:.2%} return, "
            f"{performance.sharpe_ratio:.2f} Sharpe, "
            f"${performance.total_cost_usd:.2f} cost"
        )
        
        await agent.close()
        
        return performance
    
    def compare_models(self, performances: List[ModelPerformance]) -> ModelPerformance:
        """
        Compare models and select winner.
        
        Selection criteria (in order):
        1. Cost-adjusted Sharpe Ratio (Sharpe / Cost)
        2. If tied, lower cost wins
        3. If still tied, higher Sharpe wins
        
        Args:
            performances: List of ModelPerformance objects
        
        Returns:
            Winning ModelPerformance
        """
        if not performances:
            raise ValueError("No performances to compare")
        
        # Sort by cost-adjusted Sharpe (descending)
        sorted_perf = sorted(
            performances,
            key=lambda p: (
                p.cost_adjusted_sharpe,
                -p.total_cost_usd,  # Lower cost is better
                p.sharpe_ratio,
            ),
            reverse=True,
        )
        
        winner = sorted_perf[0]
        
        logger.info(f"Winner: {winner.model_name} (cost-adjusted Sharpe: {winner.cost_adjusted_sharpe:.2f})")
        
        return winner
    
    def get_comparison_report(self) -> str:
        """Generate human-readable comparison report."""
        if not self.results:
            return "No models tested yet."
        
        report = """
╔════════════════════════════════════════════════════════════════╗
║              AI MODEL COMPARISON REPORT                         ║
╚════════════════════════════════════════════════════════════════╝
"""
        
        # Sort by cost-adjusted Sharpe
        sorted_results = sorted(
            self.results,
            key=lambda p: p.cost_adjusted_sharpe,
            reverse=True
        )
        
        for i, perf in enumerate(sorted_results, 1):
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            
            report += f"""
{rank_emoji} {i}. {perf.model_name} ({perf.model_id})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Performance
   Total Return:        {perf.total_return:>10.2%}
   Sharpe Ratio:        {perf.sharpe_ratio:>10.2f}
   Max Drawdown:        {perf.max_drawdown:>10.2%}
   Win Rate:            {perf.win_rate:>10.1%}

💰 Cost
   Total API Calls:     {perf.total_api_calls:>10,}
   Total Cost:          ${perf.total_cost_usd:>9.2f}
   Cost per Trade:      ${perf.cost_per_trade:>9.4f}

⚡ Efficiency (Key Metrics!)
   Cost-Adj Sharpe:     {perf.cost_adjusted_sharpe:>10.2f}  ← Winner metric
   Return per $:        {perf.return_per_dollar:>10.2f}x

📈 Trading
   Total Trades:        {perf.total_trades:>10}
   Avg Trade Return:    {perf.avg_trade_return:>10.2%}
"""
        
        # Comparison summary
        if len(sorted_results) >= 2:
            best = sorted_results[0]
            second = sorted_results[1]
            
            sharpe_diff = best.sharpe_ratio - second.sharpe_ratio
            cost_diff = best.total_cost_usd - second.total_cost_usd
            
            report += f"""
╔════════════════════════════════════════════════════════════════╗
║                    COMPARISON SUMMARY                           ║
╚════════════════════════════════════════════════════════════════╝

🏆 WINNER: {best.model_name}

Why?
• Cost-Adjusted Sharpe: {best.cost_adjusted_sharpe:.2f} vs {second.cost_adjusted_sharpe:.2f}
• Sharpe Ratio: {sharpe_diff:+.2f} {'better' if sharpe_diff > 0 else 'worse'}
• Cost: ${cost_diff:+.2f} ({'more expensive' if cost_diff > 0 else 'cheaper'})

💡 Recommendation:
"""
            
            if best.model_name == "Haiku":
                report += f"""   Use HAIKU for production
   • Similar performance to Sonnet
   • ${abs(cost_diff):.2f} cheaper per backtest
   • Cost-efficiency winner!
"""
            else:
                report += f"""   Use SONNET for production
   • {sharpe_diff:.2f} better Sharpe Ratio
   • Worth the extra ${cost_diff:.2f}
   • Performance justifies cost
"""
        
        return report
    
    def to_dataframe(self) -> pd.DataFrame:
        """Export results to DataFrame for further analysis."""
        if not self.results:
            return pd.DataFrame()
        
        data = []
        for perf in self.results:
            data.append({
                'model_name': perf.model_name,
                'model_id': perf.model_id,
                'total_return': perf.total_return,
                'sharpe_ratio': perf.sharpe_ratio,
                'max_drawdown': perf.max_drawdown,
                'win_rate': perf.win_rate,
                'total_trades': perf.total_trades,
                'total_cost_usd': perf.total_cost_usd,
                'cost_adjusted_sharpe': perf.cost_adjusted_sharpe,
                'return_per_dollar': perf.return_per_dollar,
            })
        
        df = pd.DataFrame(data)
        return df.sort_values('cost_adjusted_sharpe', ascending=False)
    
    def save_report(self, filepath: str):
        """Save comparison report to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.get_comparison_report())
        logger.info(f"Report saved to {filepath}")