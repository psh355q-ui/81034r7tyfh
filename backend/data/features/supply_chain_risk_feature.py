"""
Feature Store Integration for Supply Chain Risk.

This module integrates the Supply Chain Risk Factor into the Feature Store
with proper caching (Redis L1 + TimescaleDB L2).

Feature Definition:
- Name: supply_chain_risk
- Category: ai_factor
- Update Frequency: monthly (30 days)
- Data Source: SEC filings, Bloomberg (mock for now)
- Cost: $0/month (no AI, rule-based)
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from supply_chain_risk import SupplyChainRiskCalculator

logger = logging.getLogger(__name__)


# Feature definition for Feature Store
SUPPLY_CHAIN_RISK_FEATURE = {
    "name": "supply_chain_risk",
    "description": "공급망 리스크 점수 (0.0-1.0, 재귀 분석)",
    "category": "ai_factor",
    "data_sources": ["sec_filings", "bloomberg", "factset"],
    "update_frequency": "monthly",
    "ttl_seconds": 30 * 24 * 3600,  # 30 days
    "dependencies": ["non_standard_risk"],  # Uses direct operational risk
    "cost_per_calculation_usd": 0.0,  # No AI, free!
    "calculation_time_ms": 50,  # Very fast with caching
}


class SupplyChainRiskFeature:
    """
    Feature Store compatible wrapper for Supply Chain Risk.
    
    Usage in Feature Store:
        feature = SupplyChainRiskFeature()
        score = await feature.calculate("AAPL")
    """
    
    def __init__(self):
        """Initialize feature calculator."""
        self.calculator = SupplyChainRiskCalculator()
        self.feature_definition = SUPPLY_CHAIN_RISK_FEATURE
    
    async def calculate(
        self,
        ticker: str,
        as_of_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Calculate supply chain risk for Feature Store.
        
        Args:
            ticker: Stock ticker
            as_of_date: As of date (not used, always uses latest data)
        
        Returns:
            {
                "value": 0.0-1.0 (float, for easy sorting/filtering),
                "confidence": str,
                "components": dict,
                "details": dict,
                "metadata": {
                    "calculated_at": datetime,
                    "ttl_days": 30,
                    "cost_usd": 0.0,
                    "data_sources": list,
                    "max_depth": int,
                }
            }
        """
        logger.info(f"Calculating supply_chain_risk for {ticker}")
        
        # Calculate risk (synchronous, but wrapped in async for consistency)
        result = self.calculator.calculate_risk(ticker)
        
        # Get metrics
        metrics = self.calculator.get_metrics()
        
        # Format for Feature Store
        feature_result = {
            "value": result["score"],  # Primary value for sorting/filtering
            "confidence": result["confidence"],
            "components": result["components"],
            "details": result["details"],
            "metadata": {
                "calculated_at": result["last_updated"],
                "ttl_days": result["ttl_days"],
                "cost_usd": 0.0,  # Always free!
                "data_sources": ["supply_chain_graph", "mock_data"],
                "feature_name": "supply_chain_risk",
                "feature_category": "ai_factor",
                "cache_hit_rate": metrics["cache_hit_rate"],
                "max_depth_reached": result["details"]["max_depth_reached"],
            }
        }
        
        logger.info(
            f"supply_chain_risk for {ticker}: {result['score']:.4f} "
            f"(confidence: {result['confidence']}, "
            f"cache_hit_rate: {metrics['cache_hit_rate']:.2%})"
        )
        
        return feature_result
    
    def get_feature_definition(self) -> Dict:
        """Get feature definition for Feature Store registration."""
        return self.feature_definition
    
    def get_metrics(self) -> Dict:
        """Get calculation metrics."""
        return self.calculator.get_metrics()
    
    def clear_cache(self) -> None:
        """Clear calculator cache."""
        self.calculator.clear_cache()


# Example usage for Feature Store integration
async def example_usage():
    """Example of how to use this in Feature Store."""
    
    # Initialize feature
    feature = SupplyChainRiskFeature()
    
    # Calculate for a stock
    result = await feature.calculate("AAPL")
    print(f"AAPL Supply Chain Risk: {result['value']:.4f}")
    print(f"  Direct Risk: {result['components']['direct_risk']:.4f}")
    print(f"  Supplier Risk: {result['components']['supplier_risk']:.4f}")
    print(f"  Customer Risk: {result['components']['customer_risk']:.4f}")
    print(f"  Geographic Risk: {result['components']['geographic_risk']:.4f}")
    
    # Get metrics
    metrics = feature.get_metrics()
    print(f"\nMetrics:")
    print(f"  Total calculations: {metrics['total_calculations']}")
    print(f"  Cache hit rate: {metrics['cache_hit_rate']:.2%}")
    print(f"  Max depth reached: {metrics['max_depth_reached']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())