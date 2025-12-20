"""
Gemini Real-Time News Search Router
Premium feature: On-demand ticker news search using Gemini grounding
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from backend.data.gemini_news_fetcher import GeminiNewsFetcher

router = APIRouter(prefix="/news/gemini", tags=["Gemini News Search"])


class GeminiNewsResponse(BaseModel):
    """Response model for Gemini news search"""
    ticker: Optional[str] = None
    query: str
    articles: list
    source_type: str = "gemini_grounded"
    cost_info: dict


@router.get("/search/ticker/{ticker}")
async def search_ticker_realtime(
    ticker: str,
    max_articles: int = Query(default=5, ge=1, le=10)
):
    """
    Real-time ticker news search using Gemini
    
    Premium feature - uses Gemini 2.0 Flash with Google Search grounding
    Currently FREE (experimental), will cost $0.04/search after Jan 2026
    """
    try:
        fetcher = GeminiNewsFetcher()
        articles = fetcher.fetch_ticker_news(ticker.upper(), max_articles=max_articles)
        
        return {
            "ticker": ticker.upper(),
            "query": f"latest news about {ticker.upper()} stock",
            "articles": articles,
            "source_type": "gemini_grounded",
            "cost_info": {
                "current_cost": "$0.00 (Free during experimental)",
                "future_cost": "~$0.04 per search (starting Jan 2026)",
                "billing_start": "2026-01-05"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search")
async def search_news_realtime(
    query: str = Query(..., min_length=3),
    max_articles: int = Query(default=5, ge=1, le=10)
):
    """
    Real-time news search using Gemini
    
    Generic search for any query
    """
    try:
        fetcher = GeminiNewsFetcher()
        articles = fetcher.fetch_news(query, max_articles=max_articles)
        
        return {
            "query": query,
            "articles": articles,
            "source_type": "gemini_grounded",
            "cost_info": {
                "current_cost": "$0.00 (Free during experimental)",
                "future_cost": "~$0.04 per search",
                "billing_start": "2026-01-05"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/breaking")
async def get_breaking_news():
    """
    Fetch breaking market news using Gemini
    """
    try:
        fetcher = GeminiNewsFetcher()
        articles = fetcher.fetch_breaking_news()
        
        return {
            "query": "breaking stock market news",
            "articles": articles,
            "source_type": "gemini_grounded",
            "timestamp": articles[0].get("fetched_at") if articles else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch breaking news: {str(e)}")
