"""
Feature Store Integration for Non-Standard Risk (Dual Mode)

Updates Feature Store to support A/B testing between rule-based and Gemini

Phase: 5 (Strategy Ensemble)
Task: 2 (Risk Migration)
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from data.features.non_standard_risk_dual import (
    NonStandardRiskCalculator,
    RiskMode,
)

logger = logging.getLogger(__name__)


# ==================== Feature Store Integration ====================

async def calculate_non_standard_risk_feature(
    ticker: str,
    as_of_date: datetime,
    mode: str = "dual",  # "rule_based", "gemini", or "dual"
) -> Dict:
    """
    Calculate non-standard risk feature for Feature Store.
    
    This function integrates with Feature Store and supports:
    - V1: Rule-based (Phase 4, $0 cost)
    - V2: Gemini (Phase 5, $0.0003 cost)
    - DUAL: A/B testing mode (both, use V1 result)
    
    Args:
        ticker: Stock ticker
        as_of_date: Date for feature calculation
        mode: "rule_based", "gemini", or "dual"
    
    Returns:
        {
            "ticker": str,
            "as_of_date": str,
            "risk_score": float (0-1),
            "risk_level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
            "categories": {...},
            "mode": str,
            "v1_result": Dict (if dual mode),
            "v2_result": Dict (if dual mode),
            "agreement": bool (if dual mode),
        }
    
    Feature Store Usage:
        features = await feature_store.get_features(
            ticker="AAPL",
            feature_names=["non_standard_risk_score", "non_standard_risk_level"]
        )
    """
    # Initialize calculator
    risk_mode = RiskMode[mode.upper()]
    calculator = NonStandardRiskCalculator(mode=risk_mode)
    
    # Get news headlines (from existing news collector)
    try:
        from data.collectors.news_collector import NewsCollector
        news_collector = NewsCollector()
        news_data = await news_collector.collect_news(ticker, max_age_days=7)
        news_headlines = [item["title"] for item in news_data.get("articles", [])]
    except Exception as e:
        logger.warning(f"Failed to collect news for {ticker}: {e}")
        news_headlines = []
    
    # Get recent events (optional, not implemented in Phase 4)
    recent_events = []
    
    # Calculate risk
    result = await calculator.calculate(
        ticker=ticker,
        news_headlines=news_headlines,
        recent_events=recent_events,
    )
    
    # Add as_of_date
    result["as_of_date"] = as_of_date.isoformat()
    
    # Log for A/B testing
    if mode == "dual":
        logger.info(
            f"A/B Test {ticker}: "
            f"V1={result['v1_result']['risk_level']}({result['v1_result']['risk_score']:.2f}) "
            f"V2={result['v2_result']['risk_level']}({result['v2_result']['risk_score']:.2f}) "
            f"Agreement: {result['agreement']}"
        )
    
    return result


# ==================== Feature Definitions for Feature Store ====================

FEATURE_DEFINITIONS = {
    "non_standard_risk_score": {
        "description": "Non-standard risk score (0=safe, 1=critical)",
        "category": "ai_factor",
        "update_frequency": "hourly",
        "ttl_seconds": 3600,  # 1 hour cache
        "calculation_function": "calculate_non_standard_risk_feature",
        "cost_per_calculation": 0.0003,  # Gemini cost (if used)
        "dependencies": ["news_headlines"],
    },
    "non_standard_risk_level": {
        "description": "Non-standard risk level (LOW/MODERATE/HIGH/CRITICAL)",
        "category": "ai_factor",
        "update_frequency": "hourly",
        "ttl_seconds": 3600,
        "calculation_function": "calculate_non_standard_risk_feature",
        "cost_per_calculation": 0.0003,
        "dependencies": ["news_headlines"],
    },
    "non_standard_risk_categories": {
        "description": "Risk breakdown by category (legal, regulatory, etc.)",
        "category": "ai_factor",
        "update_frequency": "hourly",
        "ttl_seconds": 3600,
        "calculation_function": "calculate_non_standard_risk_feature",
        "cost_per_calculation": 0.0003,
        "dependencies": ["news_headlines"],
    },
}


# ==================== Cache Key Generation ====================

def get_cache_key(ticker: str, mode: str) -> str:
    """
    Generate cache key for non-standard risk.
    
    Cache Strategy:
    - V1 (rule-based): Cache 1 hour (stable, cheap to recalculate)
    - V2 (Gemini): Cache 1 hour (expensive, avoid redundant calls)
    - DUAL: Cache V1 result (use V1 in production during A/B test)
    
    Args:
        ticker: Stock ticker
        mode: "rule_based", "gemini", or "dual"
    
    Returns:
        Cache key string
    """
    return f"non_standard_risk:{ticker}:{mode}"


async def get_cached_risk(
    ticker: str,
    mode: str,
    redis_client,
) -> Optional[Dict]:
    """
    Get cached risk score from Redis.
    
    Args:
        ticker: Stock ticker
        mode: Risk calculation mode
        redis_client: Redis client instance
    
    Returns:
        Cached risk dict or None if not found
    """
    import json
    
    cache_key = get_cache_key(ticker, mode)
    cached = await redis_client.get(cache_key)
    
    if cached:
        logger.info(f"Cache hit for {ticker} ({mode})")
        return json.loads(cached)
    
    return None


async def set_cached_risk(
    ticker: str,
    mode: str,
    risk_data: Dict,
    redis_client,
    ttl_seconds: int = 3600,
):
    """
    Cache risk score in Redis.
    
    Args:
        ticker: Stock ticker
        mode: Risk calculation mode
        risk_data: Risk calculation result
        redis_client: Redis client instance
        ttl_seconds: Cache TTL (default 1 hour)
    """
    import json
    
    cache_key = get_cache_key(ticker, mode)
    await redis_client.setex(
        cache_key,
        ttl_seconds,
        json.dumps(risk_data)
    )
    logger.info(f"Cached risk for {ticker} ({mode}), TTL={ttl_seconds}s")


# ==================== Example Integration ====================

async def example_feature_store_integration():
    """
    Example: How to integrate with Feature Store.
    
    This shows how TradingAgent would use the dual mode feature.
    """
    from data.feature_store.store import FeatureStore
    
    # Initialize Feature Store
    feature_store = FeatureStore()
    
    # Get features for a stock
    ticker = "AAPL"
    features = await feature_store.get_features(
        ticker=ticker,
        as_of_date=datetime.now(),
        feature_names=[
            "ret_5d",
            "vol_20d",
            "mom_20d",
            "non_standard_risk_score",  # NEW: Dual mode
            "non_standard_risk_level",   # NEW: Dual mode
        ],
    )
    
    # Check risk level
    risk_level = features.get("non_standard_risk_level", "UNKNOWN")
    risk_score = features.get("non_standard_risk_score", 0.0)
    
    print(f"{ticker} Risk: {risk_level} ({risk_score:.2f})")
    
    # Trading decision based on risk
    if risk_level == "CRITICAL":
        decision = "HOLD (CRITICAL risk detected)"
    elif risk_level == "HIGH":
        decision = "HOLD or reduce position (HIGH risk)"
    elif risk_level == "MODERATE":
        decision = "Proceed with caution (MODERATE risk)"
    else:
        decision = "Normal trading (LOW risk)"
    
    print(f"Decision: {decision}")
    
    return features


# ==================== A/B Testing Report Generator ====================

async def generate_ab_test_report(calculator: NonStandardRiskCalculator) -> str:
    """
    Generate A/B testing report.
    
    Args:
        calculator: NonStandardRiskCalculator instance with metrics
    
    Returns:
        Formatted report string
    """
    metrics = calculator.get_ab_metrics()
    
    report = f"""
# A/B Testing Report: Rule-based (V1) vs Gemini (V2)

## Summary
- Total Comparisons: {metrics['total_comparisons']}
- Agreement Rate: {metrics['agreement_rate']:.1%}
- Average Difference: {metrics['avg_difference']:.2f}

## Score Distribution
- V1 Higher: {metrics['v1_higher_rate']:.1%} ({metrics['v1_higher']} cases)
- V2 Higher: {metrics['v2_higher_rate']:.1%} ({metrics['v2_higher']} cases)
- Same: {100 - (metrics['v1_higher_rate'] + metrics['v2_higher_rate']):.1%}

## Recommendation
{metrics['recommendation']}

## Decision Criteria
- If agreement rate > 80%: Both methods work well, keep cheaper one (V1)
- If V2 detects significantly more risks (>60% higher, >0.2 diff): Consider V2
- If V1 more conservative (>60% higher, >0.2 diff): Keep V1 for safety
- Otherwise: Need more data (target: 100+ comparisons)

## Next Steps
1. Continue A/B testing for 1 week (700 stocks total)
2. Analyze false positives/negatives manually (sample 20 stocks)
3. Make final decision: V1 or V2
4. If V2 chosen, update Feature Store to use Gemini by default
"""
    
    return report


if __name__ == "__main__":
    import asyncio
    
    async def test_integration():
        """Test Feature Store integration"""
        
        # Test dual mode
        result = await calculate_non_standard_risk_feature(
            ticker="AAPL",
            as_of_date=datetime.now(),
            mode="dual",
        )
        
        print("\n" + "="*60)
        print("Feature Store Integration Test")
        print("="*60)
        print(f"Ticker: {result['ticker']}")
        print(f"Risk Score: {result['risk_score']:.2f}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Mode: {result['mode']}")
        
        if result['mode'] == 'dual':
            print(f"\nV1 (Rule): {result['v1_result']['risk_level']} ({result['v1_result']['risk_score']:.2f})")
            print(f"V2 (Gemini): {result['v2_result']['risk_level']} ({result['v2_result']['risk_score']:.2f})")
            print(f"Agreement: {result['agreement']}")
        
        print("="*60 + "\n")
    
    asyncio.run(test_integration())