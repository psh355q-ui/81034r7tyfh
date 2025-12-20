"""
Example: How to Use Semantic Caching in Your API Routers

This shows how to integrate TradingSemanticCache with existing endpoints
to eliminate duplicate API costs for similar queries.
"""

from fastapi import APIRouter
from backend.caching import get_cache

router = APIRouter()


# ============================================================================
# Example 1: Manual Cache Integration
# ============================================================================

@router.post("/analyze")
async def analyze_stock(ticker: str, query: str):
    """
    Stock analysis with manual semantic caching
    
    Similar queries like:
    - "What are AAPL's risks?"
    - "Tell me about Apple's risk factors"
    - "Analyze risk for AAPL"
    
    ...will hit the cache and cost $0!
    """
    # Get cache instance
    cache = get_cache(
        distance_threshold=0.1,  # Only very similar queries
        ttl=3600  # 1 hour cache
    )
    
    # Build cache query (combine ticker + query for uniqueness)
    cache_query = f"analyze {ticker}: {query}"
    
    # Define expensive AI function
    async def expensive_analysis():
        # This is what costs money - call Claude/Gemini here
        result = await call_claude_api(ticker, query)
        return result
    
    # Get from cache or generate
    cached_result = await cache.get_or_generate(
        query=cache_query,
        generate_func=expensive_analysis
    )
    
    return {
        "ticker": ticker,
        "analysis": cached_result['response'],
        "cached": cached_result['source'] == 'cache',
        "cost": cached_result['cost'],
        "cache_metrics": cache.get_metrics()
    }


# ============================================================================
# Example 2: Using Decorator (Recommended)
# ============================================================================

from backend.caching import cached_analysis

@router.post("/sec-analysis")
@cached_analysis(ttl=7200, distance_threshold=0.15)  # 2 hour cache, slightly looser
async def analyze_sec_filing(ticker: str, filing_type: str = "10-K"):
    """
    SEC filing analysis with decorator caching
    
    The decorator automatically:
    - Builds cache key from function args
    - Checks cache before calling
    - Stores result on cache miss
    - Tracks metrics
    """
    # Your expensive analysis here
    from backend.ai.sec_analyzer import SECAnalyzer
    
    analyzer = SECAnalyzer(...)
    result = await analyzer.analyze_ticker(ticker=ticker, filing_type=filing_type)
    
    return result  # Decorator handles caching automatically!


# ============================================================================
# Example 3: News Analysis with Caching
# ============================================================================

@router.get("/news-summary/{ticker}")
async def get_news_summary(ticker: str):
    """
    News summary with caching
    
    Cache similar requests like:
    - GET /news-summary/AAPL
    - GET /news-summary/AAPL  (within TTL)
    
    Second request costs $0!
    """
    cache = get_cache(distance_threshold=0.05)  # Strict for same ticker
    
    async def fetch_and_summarize():
        # Fetch news
        articles = await fetch_news(ticker)
        
        # Summarize with AI (costs money)
        summary = await summarize_with_ai(articles)
        return summary
    
    result = await cache.get_or_generate(
        query=f"news_summary:{ticker}",
        generate_func=fetch_and_summarize
    )
    
    return {
        "ticker": ticker,
        "summary": result['response'],
        "from_cache": result['source'] == 'cache',
        "savings": f"${result.get('cost', 0):.4f}"
    }


# ============================================================================
# Example 4: Metrics Endpoint
# ============================================================================

@router.get("/cache/metrics")
async def get_cache_metrics():
    """
    Get cache performance metrics
    
    Returns:
        - Hit rate
        - Total queries
        - Total saved
    """
    cache = get_cache()
    
    if not cache.is_enabled():
        return {"error": "Cache not available (Redis not connected)"}
    
    metrics = cache.get_metrics()
    
    return {
        "cache_enabled": True,
        "metrics": metrics,
        "performance": {
            "hit_rate_pct": f"{metrics['hit_rate'] * 100:.1f}%",
            "total_saved": f"${metrics['total_saved_usd']:.2f}"
        }
    }


# ============================================================================
# Example 5: Clear Cache (Admin)
# ============================================================================

@router.post("/cache/clear")
async def clear_cache_admin():
    """
    Clear all cached entries (admin only)
    """
    from backend.caching import clear_cache
    
    clear_cache()
    
    return {"status": "Cache cleared"}


# ============================================================================
# Helper Functions (Example)
# ============================================================================

async def call_claude_api(ticker: str, query: str):
    """Example: Expensive AI call"""
    import anthropic
    client = anthropic.Anthropic()
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"Analyze {ticker}: {query}"
        }]
    )
    
    return response.content[0].text


async def fetch_news(ticker: str):
    """Example: Fetch news articles"""
    # Implementation here
    return []


async def summarize_with_ai(articles: list):
    """Example: AI summarization"""
    # Implementation here
    return "Summary..."
