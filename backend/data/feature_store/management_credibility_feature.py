"""
Feature Store Integration for Management Credibility.

This module integrates the Management Credibility Factor into the Feature Store
with proper caching (Redis L1 + TimescaleDB L2).

Feature Definition:
- Name: management_credibility
- Category: ai_factor
- Update Frequency: quarterly (90 days)
- Data Source: Yahoo Finance + Claude API
- Cost: ~$0.043/month (100 stocks, quarterly)
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from management_credibility import ManagementCredibilityCalculator

logger = logging.getLogger(__name__)


# Feature definition for Feature Store
MANAGEMENT_CREDIBILITY_FEATURE = {
    "name": "management_credibility",
    "description": "경영진 신뢰도 점수 (0.0-1.0)",
    "category": "ai_factor",
    "data_sources": ["yahoo_finance", "claude_api"],
    "update_frequency": "quarterly",
    "ttl_seconds": 90 * 24 * 3600,  # 90 days
    "dependencies": [],
    "cost_per_calculation_usd": 0.0013,  # Claude API cost
    "calculation_time_ms": 3000,  # Estimated
}


class ManagementCredibilityFeature:
    """
    Feature Store compatible wrapper for Management Credibility.
    
    Usage in Feature Store:
        feature = ManagementCredibilityFeature()
        score = await feature.calculate("AAPL", use_ai=True)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize feature calculator.
        
        Args:
            api_key: Claude API key (optional, for testing without AI)
        """
        self.calculator = ManagementCredibilityCalculator(api_key=api_key)
        self.feature_definition = MANAGEMENT_CREDIBILITY_FEATURE
    
    async def calculate(
        self,
        ticker: str,
        as_of_date: Optional[datetime] = None,
        use_ai: bool = True,
    ) -> Dict:
        """
        Calculate management credibility for Feature Store.
        
        Args:
            ticker: Stock ticker
            as_of_date: As of date (not used, always uses latest data)
            use_ai: Whether to use Claude API for sentiment analysis
        
        Returns:
            {
                "value": 0.0-1.0 (float, for easy sorting/filtering),
                "confidence": str,
                "components": dict,
                "details": dict,
                "metadata": {
                    "calculated_at": datetime,
                    "ttl_days": 90,
                    "cost_usd": float,
                    "data_sources": list
                }
            }
        """
        logger.info(f"Calculating management_credibility for {ticker} (use_ai={use_ai})")
        
        result = await self.calculator.calculate_credibility(ticker, use_ai=use_ai)
        
        # Get cost metrics
        metrics = self.calculator.get_metrics()
        cost = metrics.get("avg_cost_per_call", 0.0) if use_ai else 0.0
        
        # Format for Feature Store
        feature_result = {
            "value": result["score"],  # Primary value for sorting/filtering
            "confidence": result["confidence"],
            "components": result["components"],
            "details": result["details"],
            "metadata": {
                "calculated_at": result["last_updated"],
                "ttl_days": result["ttl_days"],
                "cost_usd": cost,
                "data_sources": ["yahoo_finance"] + (["claude_api"] if use_ai else []),
                "feature_name": "management_credibility",
                "feature_category": "ai_factor",
            }
        }
        
        logger.info(
            f"management_credibility for {ticker}: {result['score']:.4f} "
            f"(cost: ${cost:.4f})"
        )
        
        return feature_result
    
    def get_feature_definition(self) -> Dict:
        """Get feature definition for Feature Store registration."""
        return self.feature_definition
    
    def get_metrics(self) -> Dict:
        """Get calculation metrics."""
        return self.calculator.get_metrics()


# Example usage for Feature Store integration
async def example_usage():
    """Example of how to use this in Feature Store."""
    
    # Initialize feature
    feature = ManagementCredibilityFeature()
    
    # Calculate for a stock (with AI)
    result = await feature.calculate("AAPL", use_ai=True)
    print(f"Score: {result['value']:.4f}")
    print(f"Cost: ${result['metadata']['cost_usd']:.4f}")
    
    # Calculate for a stock (without AI, cost-free)
    result_no_ai = await feature.calculate("AAPL", use_ai=False)
    print(f"Score (no AI): {result_no_ai['value']:.4f}")
    print(f"Cost (no AI): ${result_no_ai['metadata']['cost_usd']:.4f}")
    
    # Get metrics
    metrics = feature.get_metrics()
    print(f"Total API calls: {metrics['total_api_calls']}")
    print(f"Total cost: ${metrics['total_cost_usd']:.4f}")


# Feature Store registration snippet
FEATURE_STORE_REGISTRATION = """
# Add to backend/data/feature_store/features.py

from features.management_credibility_feature import (
    ManagementCredibilityFeature,
    MANAGEMENT_CREDIBILITY_FEATURE,
)

# Register feature
FEATURE_DEFINITIONS["management_credibility"] = MANAGEMENT_CREDIBILITY_FEATURE

# Add calculator
_management_credibility_calculator = ManagementCredibilityFeature()

async def calculate_management_credibility(
    ticker: str,
    as_of_date: datetime,
    use_ai: bool = True,
) -> float:
    '''
    Calculate management credibility score.
    
    Args:
        ticker: Stock ticker
        as_of_date: As of date (not used, always latest)
        use_ai: Whether to use Claude API (costs $0.0013)
    
    Returns:
        Score 0.0-1.0
    '''
    result = await _management_credibility_calculator.calculate(
        ticker=ticker,
        as_of_date=as_of_date,
        use_ai=use_ai,
    )
    return result["value"]
"""


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())