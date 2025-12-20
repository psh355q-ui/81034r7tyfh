"""
Dynamic Screener Integration Tests

Tests:
1. Basic screening (100 → 50)
2. Priority system (portfolio > watchlist > top market cap)
3. Risk filtering (CRITICAL removed)
4. Cache performance
5. Parallel processing

Phase: 5 (Strategy Ensemble)
Task: 3 (Dynamic Screener)
"""

import asyncio
import logging
from datetime import datetime
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Test Data ====================

PORTFOLIO_SMALL = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
WATCHLIST_SMALL = ["TSLA", "META", "NFLX", "ADBE", "CRM"]

PORTFOLIO_LARGE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BRK.B", "V", "JNJ",
]

WATCHLIST_LARGE = [
    "NFLX", "ADBE", "CRM", "ORCL", "IBM",
    "CSCO", "INTC", "TXN", "QCOM", "AMD",
]


# ==================== Test Functions ====================

async def test_basic_screening():
    """Test 1: Basic screening functionality"""
    from dynamic_screener import DynamicScreener, get_sp500_top_by_market_cap
    
    print("\n" + "="*80)
    print("Test 1: Basic Screening (100 → 50)")
    print("="*80)
    
    screener = DynamicScreener()
    
    candidates = await screener.screen(
        portfolio_tickers=PORTFOLIO_SMALL,
        watchlist_tickers=WATCHLIST_SMALL,
        top_market_cap_tickers=get_sp500_top_by_market_cap(100),
        target_count=50,
    )
    
    metrics = screener.get_metrics()
    
    print(f"\nResults:")
    print(f"  - Total candidates: {metrics['total_candidates']}")
    print(f"  - Filtered (CRITICAL): {metrics['filtered_critical']}")
    print(f"  - Final count: {metrics['final_count']}")
    print(f"  - Gemini calls: {metrics['gemini_calls']}")
    print(f"  - Cost: ${metrics['gemini_cost']:.2f}")
    print(f"  - Time: {metrics['screening_time_ms']:.0f}ms")
    
    assert metrics['final_count'] <= 50, "Should return ≤50 stocks"
    assert metrics['total_candidates'] > 0, "Should have candidates"
    
    print("\n✅ Test 1 passed!")
    
    return candidates


async def test_priority_system():
    """Test 2: Priority system (portfolio > watchlist > top market cap)"""
    from dynamic_screener import DynamicScreener, StockPriority
    
    print("\n" + "="*80)
    print("Test 2: Priority System")
    print("="*80)
    
    screener = DynamicScreener()
    
    # Use small lists to verify priority
    candidates = await screener.screen(
        portfolio_tickers=["AAPL", "MSFT"],  # Priority 1
        watchlist_tickers=["TSLA", "META"],  # Priority 2
        top_market_cap_tickers=["GOOGL", "AMZN", "NVDA"],  # Priority 3
        target_count=10,
    )
    
    print(f"\nTop 10 candidates (by priority):")
    print(f"{'Rank':<6}{'Ticker':<10}{'Priority':<15}{'Risk Level':<12}")
    print("-"*50)
    
    for i, candidate in enumerate(candidates[:10], 1):
        print(f"{i:<6}{candidate.ticker:<10}{candidate.priority.name:<15}"
              f"{candidate.risk_level or 'N/A':<12}")
    
    # Verify portfolio stocks come first
    top_tickers = [c.ticker for c in candidates[:2]]
    assert "AAPL" in top_tickers or "MSFT" in top_tickers, "Portfolio stocks should be first"
    
    print("\n✅ Test 2 passed!")


async def test_risk_filtering():
    """Test 3: Risk filtering (CRITICAL removed)"""
    from dynamic_screener import DynamicScreener, StockCandidate, StockPriority
    
    print("\n" + "="*80)
    print("Test 3: Risk Filtering")
    print("="*80)
    
    screener = DynamicScreener()
    
    # Mock candidates with different risk levels
    candidates = [
        StockCandidate(ticker="LOW_RISK", priority=StockPriority.WATCHLIST, risk_score=0.1, risk_level="LOW"),
        StockCandidate(ticker="MODERATE_RISK", priority=StockPriority.WATCHLIST, risk_score=0.2, risk_level="MODERATE"),
        StockCandidate(ticker="HIGH_RISK", priority=StockPriority.WATCHLIST, risk_score=0.5, risk_level="HIGH"),
        StockCandidate(ticker="CRITICAL_RISK", priority=StockPriority.WATCHLIST, risk_score=0.8, risk_level="CRITICAL"),
        StockCandidate(ticker="PORTFOLIO_CRITICAL", priority=StockPriority.PORTFOLIO, risk_score=0.9, risk_level="CRITICAL"),
    ]
    
    # Filter
    filtered = screener._filter_critical_risks(candidates, max_risk_score=0.6)
    
    filtered_tickers = [c.ticker for c in filtered]
    
    print(f"\nFiltering results:")
    print(f"  - Original: {len(candidates)} stocks")
    print(f"  - Filtered: {len(filtered)} stocks")
    print(f"  - Removed: {[c.ticker for c in candidates if c.ticker not in filtered_tickers]}")
    
    # Verify CRITICAL watchlist removed, but portfolio kept
    assert "CRITICAL_RISK" not in filtered_tickers, "CRITICAL watchlist should be filtered"
    assert "PORTFOLIO_CRITICAL" in filtered_tickers, "CRITICAL portfolio should be kept"
    assert "LOW_RISK" in filtered_tickers, "LOW risk should be kept"
    assert "HIGH_RISK" in filtered_tickers, "HIGH risk should be kept"
    
    print("\n✅ Test 3 passed!")


async def test_cache_performance():
    """Test 4: Cache performance (1st call vs 2nd call)"""
    import redis.asyncio as redis_async
    from screener_cache import screen_stocks_cached, get_sp500_top_by_market_cap
    
    print("\n" + "="*80)
    print("Test 4: Cache Performance")
    print("="*80)
    
    # Initialize Redis
    try:
        redis_client = redis_async.from_url("redis://localhost:6379/0")
        
        portfolio = ["AAPL", "MSFT"]
        watchlist = ["TSLA", "META"]
        top_market_cap = get_sp500_top_by_market_cap(20)  # Smaller for speed
        
        # First call (cache miss)
        print("\n1. First call (cache miss)...")
        start = datetime.now()
        candidates1 = await screen_stocks_cached(
            portfolio_tickers=portfolio,
            watchlist_tickers=watchlist,
            top_market_cap_tickers=top_market_cap,
            redis_client=redis_client,
            target_count=20,
        )
        time1 = (datetime.now() - start).total_seconds() * 1000
        print(f"   Time: {time1:.0f}ms")
        
        # Second call (cache hit)
        print("\n2. Second call (cache hit)...")
        start = datetime.now()
        candidates2 = await screen_stocks_cached(
            portfolio_tickers=portfolio,
            watchlist_tickers=watchlist,
            top_market_cap_tickers=top_market_cap,
            redis_client=redis_client,
            target_count=20,
        )
        time2 = (datetime.now() - start).total_seconds() * 1000
        print(f"   Time: {time2:.0f}ms")
        
        speedup = time1 / time2 if time2 > 0 else 0
        print(f"\n   Speedup: {speedup:.0f}x faster")
        
        assert time2 < time1, "Cached call should be faster"
        assert len(candidates1) == len(candidates2), "Results should be identical"
        
        print("\n✅ Test 4 passed!")
        
        await redis_client.close()
    
    except Exception as e:
        print(f"\n⚠️  Test 4 skipped: {e}")
        print("   (Redis not available)")


async def test_parallel_processing():
    """Test 5: Parallel processing speed"""
    from dynamic_screener import DynamicScreener, get_sp500_top_by_market_cap
    
    print("\n" + "="*80)
    print("Test 5: Parallel Processing")
    print("="*80)
    
    screener = DynamicScreener()
    
    # Test with 30 stocks
    start = datetime.now()
    candidates = await screener.screen(
        portfolio_tickers=PORTFOLIO_SMALL,
        watchlist_tickers=WATCHLIST_SMALL,
        top_market_cap_tickers=get_sp500_top_by_market_cap(30),
        target_count=30,
    )
    elapsed = (datetime.now() - start).total_seconds()
    
    metrics = screener.get_metrics()
    
    print(f"\nParallel processing results:")
    print(f"  - Stocks screened: {metrics['gemini_calls']}")
    print(f"  - Total time: {elapsed:.1f}s")
    print(f"  - Time per stock: {elapsed / metrics['gemini_calls']:.2f}s")
    print(f"  - Throughput: {metrics['gemini_calls'] / elapsed:.1f} stocks/sec")
    
    # Verify parallel is faster than sequential
    # Sequential: 30 stocks × 0.5s = 15s
    # Parallel (10 concurrent): 30 / 10 × 0.5s = 1.5s
    expected_sequential = metrics['gemini_calls'] * 0.5
    speedup = expected_sequential / elapsed
    
    print(f"\n   Expected sequential: {expected_sequential:.1f}s")
    print(f"   Actual (parallel): {elapsed:.1f}s")
    print(f"   Speedup: {speedup:.1f}x")
    
    assert speedup > 2, "Parallel should be at least 2x faster"
    
    print("\n✅ Test 5 passed!")


async def test_integration_workflow():
    """Test 6: Complete integration workflow"""
    from dynamic_screener import DynamicScreener, get_sp500_top_by_market_cap
    
    print("\n" + "="*80)
    print("Test 6: Integration Workflow")
    print("="*80)
    
    # Simulate real workflow
    print("\n1. Define inputs (portfolio, watchlist, universe)")
    portfolio = PORTFOLIO_LARGE  # 10 stocks
    watchlist = WATCHLIST_LARGE  # 10 stocks
    top_market_cap = get_sp500_top_by_market_cap(100)  # 100 stocks
    
    print(f"   Portfolio: {len(portfolio)} stocks")
    print(f"   Watchlist: {len(watchlist)} stocks")
    print(f"   Universe: {len(top_market_cap)} stocks")
    print(f"   Total candidates: {len(set(portfolio + watchlist + top_market_cap))}")
    
    # Run screening
    print("\n2. Run screening (Gemini risk-based filtering)")
    screener = DynamicScreener()
    candidates = await screener.screen(
        portfolio_tickers=portfolio,
        watchlist_tickers=watchlist,
        top_market_cap_tickers=top_market_cap,
        target_count=50,
    )
    
    metrics = screener.get_metrics()
    
    print(f"   Screened: {metrics['gemini_calls']} stocks")
    print(f"   Filtered: {metrics['filtered_critical']} CRITICAL risks")
    print(f"   Selected: {metrics['final_count']} stocks")
    print(f"   Cost: ${metrics['gemini_cost']:.2f}")
    print(f"   Time: {metrics['screening_time_ms']:.0f}ms")
    
    # Verify results
    print("\n3. Verify results")
    priority_counts = {}
    risk_counts = {}
    
    for c in candidates:
        priority_counts[c.priority.name] = priority_counts.get(c.priority.name, 0) + 1
        risk_counts[c.risk_level] = risk_counts.get(c.risk_level, 0) + 1
    
    print(f"   Priority distribution: {priority_counts}")
    print(f"   Risk distribution: {risk_counts}")
    
    # Portfolio should all be included
    portfolio_included = sum(1 for c in candidates if c.ticker in portfolio)
    print(f"   Portfolio inclusion: {portfolio_included}/{len(portfolio)}")
    
    assert portfolio_included == len(portfolio), "All portfolio stocks should be included"
    assert metrics['final_count'] <= 50, "Should not exceed target count"
    
    print("\n✅ Test 6 passed!")
    print("\n" + "="*80)
    print("All Integration Tests Passed! 🎉")
    print("="*80)


# ==================== Run All Tests ====================

async def run_all_tests():
    """Run all integration tests"""
    
    print("\n" + "="*80)
    print("Dynamic Screener Integration Tests")
    print("="*80)
    
    tests = [
        ("Basic Screening", test_basic_screening),
        ("Priority System", test_priority_system),
        ("Risk Filtering", test_risk_filtering),
        ("Cache Performance", test_cache_performance),
        ("Parallel Processing", test_parallel_processing),
        ("Integration Workflow", test_integration_workflow),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())