"""
A/B Testing Script: Rule-based vs Gemini

Purpose: Run 1-week A/B test to compare V1 and V2
Target: 100 stocks/day × 7 days = 700 comparisons
Cost: 700 × $0.0003 = $0.21

Phase: 5 (Strategy Ensemble)
Task: 2 (Risk Migration)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

from non_standard_risk_dual import NonStandardRiskCalculator, RiskMode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==================== Test Configuration ====================

TEST_CONFIG = {
    "duration_days": 7,
    "stocks_per_day": 100,
    "output_dir": "ab_test_results",
    "save_detailed_results": True,
    "save_summary_daily": True,
}

# S&P 500 sample stocks for testing
SAMPLE_STOCKS = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "ADBE", "CRM",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "USB",
    # Healthcare
    "UNH", "JNJ", "PFE", "ABBV", "TMO", "LLY", "MRK", "ABT", "DHR", "BMY",
    # Consumer
    "WMT", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "COST", "TJX", "DG",
    # Industrial
    "BA", "CAT", "HON", "UPS", "RTX", "LMT", "GE", "MMM", "DE", "EMR",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
    # Materials
    "LIN", "APD", "SHW", "ECL", "DD", "NEM", "FCX", "NUE", "DOW", "PPG",
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "PEG", "XEL", "ED",
    # Real Estate
    "AMT", "PLD", "CCI", "EQIX", "PSA", "DLR", "WELL", "AVB", "EQR", "SPG",
    # Communication
    "GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "CHTR", "DISH",
][:100]  # Top 100


# ==================== Mock News Data (for testing without API) ====================

MOCK_NEWS_DATA = {
    "normal": [
        "{ticker} reports quarterly earnings",
        "{ticker} announces new product",
        "Analysts upgrade {ticker} stock",
    ],
    "legal": [
        "{ticker} faces class action lawsuit",
        "Shareholders sue {ticker} management",
        "{ticker} settles litigation for $100M",
    ],
    "regulatory": [
        "SEC investigates {ticker}",
        "FDA rejects {ticker} drug application",
        "{ticker} faces antitrust probe",
    ],
    "operational": [
        "{ticker} recalls products due to defect",
        "{ticker} data breach affects millions",
        "{ticker} plant shuts down unexpectedly",
    ],
}


def get_mock_news(ticker: str, scenario: str = "normal") -> List[str]:
    """Get mock news for testing"""
    templates = MOCK_NEWS_DATA.get(scenario, MOCK_NEWS_DATA["normal"])
    return [t.format(ticker=ticker) for t in templates]


# ==================== A/B Test Runner ====================

class ABTestRunner:
    """
    A/B Test Runner for risk calculation methods.
    
    Runs V1 (rule-based) vs V2 (Gemini) comparison over multiple days.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.calculator = NonStandardRiskCalculator(mode=RiskMode.DUAL)
        
        # Results storage
        self.daily_results = []
        self.detailed_results = []
        
        # Create output directory
        self.output_dir = Path(config["output_dir"])
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"ABTestRunner initialized: {config}")
    
    async def run_test(self, stocks: List[str], use_mock: bool = True):
        """
        Run A/B test on a list of stocks.
        
        Args:
            stocks: List of stock tickers to test
            use_mock: Use mock news data (True) or real API (False)
        """
        logger.info(f"Starting A/B test on {len(stocks)} stocks")
        
        results = []
        
        for i, ticker in enumerate(stocks):
            try:
                # Get news (mock or real)
                if use_mock:
                    # Randomly assign scenarios for variety
                    import random
                    scenario = random.choice(["normal", "normal", "normal", "legal", "regulatory", "operational"])
                    news = get_mock_news(ticker, scenario)
                else:
                    # Real news collection (requires NewsCollector)
                    from data.collectors.news_collector import NewsCollector
                    collector = NewsCollector()
                    news_data = await collector.collect_news(ticker)
                    news = [item["title"] for item in news_data.get("articles", [])]
                
                # Calculate risk (dual mode)
                result = await self.calculator.calculate(
                    ticker=ticker,
                    news_headlines=news,
                )
                
                # Save result
                results.append(result)
                self.detailed_results.append(result)
                
                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i + 1}/{len(stocks)} stocks analyzed")
            
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {e}")
        
        return results
    
    def analyze_results(self, results: List[Dict]) -> Dict:
        """
        Analyze A/B test results.
        
        Returns:
            Summary statistics
        """
        if not results:
            return {}
        
        # Count agreements/disagreements
        agreements = sum(1 for r in results if r.get("agreement", False))
        total = len(results)
        
        # Count risk level distributions
        v1_levels = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
        v2_levels = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
        
        for r in results:
            v1_level = r["v1_result"]["risk_level"]
            v2_level = r["v2_result"]["risk_level"]
            v1_levels[v1_level] += 1
            v2_levels[v2_level] += 1
        
        # Calculate metrics
        metrics = self.calculator.get_ab_metrics()
        
        return {
            "total_stocks": total,
            "agreement_count": agreements,
            "agreement_rate": agreements / total if total > 0 else 0,
            "v1_levels": v1_levels,
            "v2_levels": v2_levels,
            "ab_metrics": metrics,
            "timestamp": datetime.now().isoformat(),
        }
    
    def save_results(self, day: int, results: List[Dict], summary: Dict):
        """Save results to files"""
        
        # Save detailed results
        if self.config["save_detailed_results"]:
            detailed_file = self.output_dir / f"day{day}_detailed.json"
            with open(detailed_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Saved detailed results to {detailed_file}")
        
        # Save daily summary
        if self.config["save_summary_daily"]:
            summary_file = self.output_dir / f"day{day}_summary.json"
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Saved summary to {summary_file}")
    
    def generate_final_report(self) -> str:
        """
        Generate final A/B test report.
        
        Returns:
            Markdown formatted report
        """
        metrics = self.calculator.get_ab_metrics()
        
        report = f"""# A/B Test Final Report: Rule-based vs Gemini

**Test Period**: {self.config['duration_days']} days
**Total Comparisons**: {metrics['total_comparisons']}
**Date**: {datetime.now().strftime('%Y-%m-%d')}

---

## Summary Statistics

### Agreement Rate
- **Agreement**: {metrics['agreement_rate']:.1%} ({metrics['agreement_count']} cases)
- **Disagreement**: {100 - metrics['agreement_rate'] * 100:.1%}

### Score Distribution
- **V1 Higher**: {metrics['v1_higher_rate']:.1%} ({metrics['v1_higher']} cases)
- **V2 Higher**: {metrics['v2_higher_rate']:.1%} ({metrics['v2_higher']} cases)
- **Average Difference**: {metrics['avg_difference']:.2f}

---

## Interpretation

### When Agreement Rate > 80%
- Both methods produce similar results
- **Recommendation**: Keep V1 (rule-based) to save $0.90/month
- V2 adds minimal value if scores are similar

### When V2 Detects More Risks (>60% higher)
- Gemini catches risks that keyword matching misses
- **Recommendation**: Switch to V2 (Gemini) for better detection
- Worth the $0.90/month cost for improved accuracy

### When V1 More Conservative (>60% higher)
- Rule-based method may be too sensitive
- **Recommendation**: Keep V1 but review keyword lists
- Or switch to V2 for more nuanced analysis

---

## Final Recommendation

**{metrics['recommendation']}**

### Cost-Benefit Analysis

**If Keeping V1 (Rule-based)**:
- ✅ Cost: $0/month
- ✅ Speed: < 1ms
- ❌ Accuracy: Keyword-based, no context

**If Switching to V2 (Gemini)**:
- ✅ Accuracy: Context-aware, semantic understanding
- ✅ Detection: Better at nuanced risks
- ❌ Cost: $0.90/month (100 stocks/day)
- ❌ Speed: ~500ms (still acceptable)

---

## Next Steps

1. **If switching to V2**:
   - Update Feature Store to use `mode="gemini"` by default
   - Update config.py with new setting
   - Deploy to NAS

2. **If keeping V1**:
   - Review and refine keyword lists
   - Consider hybrid approach (V1 for screening, V2 for high-risk only)

3. **Hybrid Approach** (Best of both):
   - Use V1 for initial screening (free, fast)
   - Use V2 only for borderline cases (0.3-0.6 range)
   - Estimated cost: $0.20/month (60% reduction)

---

**Test Cost**: {metrics['total_comparisons']} × $0.0003 = ${metrics['total_comparisons'] * 0.0003:.2f}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report


# ==================== Main Test Execution ====================

async def run_full_ab_test(use_mock: bool = True):
    """
    Run full 7-day A/B test.
    
    Args:
        use_mock: Use mock data (True) or real API (False)
    """
    config = TEST_CONFIG
    runner = ABTestRunner(config)
    
    logger.info("="*60)
    logger.info("Starting A/B Test: Rule-based vs Gemini")
    logger.info("="*60)
    logger.info(f"Duration: {config['duration_days']} days")
    logger.info(f"Stocks per day: {config['stocks_per_day']}")
    logger.info(f"Total comparisons: {config['duration_days'] * config['stocks_per_day']}")
    logger.info(f"Mock mode: {use_mock}")
    logger.info("="*60 + "\n")
    
    # Run test for each day
    for day in range(1, config["duration_days"] + 1):
        logger.info(f"\n--- Day {day}/{config['duration_days']} ---")
        
        # Run tests
        results = await runner.run_test(SAMPLE_STOCKS, use_mock=use_mock)
        
        # Analyze results
        summary = runner.analyze_results(results)
        
        # Save results
        runner.save_results(day, results, summary)
        
        # Log summary
        logger.info(f"Day {day} Summary:")
        logger.info(f"  - Stocks analyzed: {summary['total_stocks']}")
        logger.info(f"  - Agreement rate: {summary['agreement_rate']:.1%}")
        logger.info(f"  - Avg difference: {summary['ab_metrics']['avg_difference']:.2f}")
    
    # Generate final report
    logger.info("\n" + "="*60)
    logger.info("Generating Final Report")
    logger.info("="*60)
    
    report = runner.generate_final_report()
    
    # Save report
    report_file = runner.output_dir / "final_report.md"
    with open(report_file, "w") as f:
        f.write(report)
    
    logger.info(f"\nFinal report saved to: {report_file}")
    logger.info("\n" + report)
    
    logger.info("="*60)
    logger.info("A/B Test Complete!")
    logger.info("="*60)


async def run_quick_test():
    """
    Quick test with 10 stocks (for validation).
    
    Use this to verify everything works before running full 7-day test.
    """
    logger.info("Running Quick Test (10 stocks)...")
    
    runner = ABTestRunner({
        "duration_days": 1,
        "stocks_per_day": 10,
        "output_dir": "ab_test_quick",
        "save_detailed_results": True,
        "save_summary_daily": True,
    })
    
    # Test with 10 stocks
    test_stocks = SAMPLE_STOCKS[:10]
    results = await runner.run_test(test_stocks, use_mock=True)
    
    # Analyze
    summary = runner.analyze_results(results)
    
    # Save
    runner.save_results(1, results, summary)
    
    # Report
    report = runner.generate_final_report()
    print("\n" + report)
    
    logger.info("\nQuick test complete! Check ab_test_quick/ directory")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick test mode
        asyncio.run(run_quick_test())
    else:
        # Full 7-day test
        asyncio.run(run_full_ab_test(use_mock=True))