"""
News Context Filter API - Phase 14.5

REST API for advanced news filtering using 4-way ensemble.

Endpoints:
- POST /api/news/analyze - Analyze single news item
- POST /api/news/filter-batch - Filter batch of news
- GET /api/news/risk-clusters - Get learned risk clusters
- GET /api/news/sector-vectors - Get sector risk profiles
- POST /api/news/learn-patterns/{ticker} - Learn crash patterns
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.ai.news_context_filter import NewsContextFilter, NewsRiskScore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["News Context Filter"])


# ============================================================================
# Request/Response Models
# ============================================================================


class NewsAnalysisRequest(BaseModel):
    """Request for single news analysis."""

    ticker: str = Field(..., description="Stock ticker")
    title: str = Field(..., description="News title")
    content: str = Field(..., description="News content")
    publish_date: Optional[str] = Field(
        None, description="Publish date (ISO format, default: now)"
    )


class NewsBatchRequest(BaseModel):
    """Request for batch news filtering."""

    news_items: List[Dict[str, Any]] = Field(
        ..., description="List of news items (ticker, title, content, publish_date)"
    )
    min_risk_score: float = Field(
        0.5, ge=0.0, le=1.0, description="Minimum risk score to keep"
    )


class RiskClusterResponse(BaseModel):
    """Risk cluster information."""

    cluster_id: int
    cluster_name: str
    crash_count: int
    avg_price_drop: float
    keywords: List[str]
    example_news: List[str]


class SectorVectorResponse(BaseModel):
    """Sector vector information."""

    sector_name: str
    vector_dimension: int
    news_count: int


class LearnPatternsRequest(BaseModel):
    """Request to learn crash patterns."""

    min_price_drop: float = Field(-0.05, description="Minimum price drop (e.g., -0.05)")
    lookback_days: int = Field(730, ge=30, le=3650, description="Days to look back")


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/analyze")
async def analyze_news(
    request: NewsAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Analyze single news item for risk.

    Uses 4-way ensemble:
    1. Risk cluster proximity
    2. Sector-specific risk
    3. Crash pattern matching
    4. Sentiment trend analysis

    Returns comprehensive risk assessment.

    Args:
        request: News analysis request
        db: Database session

    Returns:
        NewsRiskScore dict
    """
    logger.info(f"Analyzing news: {request.ticker} - {request.title}")

    filter_engine = NewsContextFilter(db)

    # Parse publish date
    if request.publish_date:
        publish_date = datetime.fromisoformat(request.publish_date)
    else:
        publish_date = datetime.now()

    # Analyze
    result = await filter_engine.analyze_news(
        ticker=request.ticker,
        news_content=request.content,
        title=request.title,
        publish_date=publish_date,
    )

    return result.to_dict()


@router.post("/filter-batch")
async def filter_news_batch(
    request: NewsBatchRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Filter batch of news, keeping only high-risk items.

    Eliminates noise and identifies true risk signals.

    Args:
        request: Batch filter request
        db: Database session

    Returns:
        Filtered news list with statistics
    """
    logger.info(
        f"Filtering {len(request.news_items)} news items "
        f"(threshold={request.min_risk_score})"
    )

    filter_engine = NewsContextFilter(db)

    # Parse dates
    news_list = []
    for item in request.news_items:
        news_dict = dict(item)

        if "publish_date" in news_dict and isinstance(news_dict["publish_date"], str):
            news_dict["publish_date"] = datetime.fromisoformat(news_dict["publish_date"])
        elif "publish_date" not in news_dict:
            news_dict["publish_date"] = datetime.now()

        news_list.append(news_dict)

    # Filter
    filtered_results = await filter_engine.filter_news_batch(
        news_list,
        min_risk_score=request.min_risk_score
    )

    # Calculate statistics
    total_count = len(request.news_items)
    filtered_count = len(filtered_results)
    pass_rate = (filtered_count / total_count * 100) if total_count > 0 else 0

    # Risk level distribution
    risk_distribution = {
        "CRITICAL": sum(1 for r in filtered_results if r.risk_level == "CRITICAL"),
        "HIGH": sum(1 for r in filtered_results if r.risk_level == "HIGH"),
        "NORMAL": sum(1 for r in filtered_results if r.risk_level == "NORMAL"),
        "LOW": sum(1 for r in filtered_results if r.risk_level == "LOW"),
    }

    return {
        "total_input": total_count,
        "filtered_output": filtered_count,
        "pass_rate_pct": pass_rate,
        "min_risk_score": request.min_risk_score,
        "risk_distribution": risk_distribution,
        "filtered_news": [r.to_dict() for r in filtered_results],
    }


@router.get("/risk-clusters")
async def get_risk_clusters(
    rebuild: bool = Query(False, description="Rebuild clusters from scratch"),
    n_clusters: int = Query(5, ge=2, le=20, description="Number of clusters"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get learned risk clusters.

    Risk clusters are patterns from historical crash days.
    News similar to these clusters indicates potential risk.

    Args:
        rebuild: Force rebuild clusters
        n_clusters: Number of clusters to create
        db: Database session

    Returns:
        List of risk clusters
    """
    logger.info(f"Getting risk clusters (rebuild={rebuild})")

    filter_engine = NewsContextFilter(db)

    if rebuild or not filter_engine.risk_clusters:
        clusters = await filter_engine.learn_risk_clusters(n_clusters=n_clusters)
    else:
        clusters = filter_engine.risk_clusters or []

    cluster_responses = []
    for cluster in clusters:
        cluster_responses.append(
            RiskClusterResponse(
                cluster_id=cluster.cluster_id,
                cluster_name=cluster.cluster_name,
                crash_count=cluster.crash_count,
                avg_price_drop=cluster.avg_price_drop,
                keywords=cluster.keywords,
                example_news=cluster.example_news,
            )
        )

    return {
        "total_clusters": len(cluster_responses),
        "clusters": [c.dict() for c in cluster_responses],
    }


@router.get("/sector-vectors")
async def get_sector_vectors(
    rebuild: bool = Query(False, description="Rebuild sector vectors"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get sector risk vectors.

    Each sector has a characteristic risk profile.
    News is compared against sector-specific patterns.

    Args:
        rebuild: Force rebuild vectors
        db: Database session

    Returns:
        Sector vector information
    """
    logger.info(f"Getting sector vectors (rebuild={rebuild})")

    filter_engine = NewsContextFilter(db)

    if rebuild or not filter_engine.sector_vectors:
        sector_vectors = await filter_engine.build_sector_vectors()
    else:
        sector_vectors = filter_engine.sector_vectors

    sector_responses = []
    for sector_name, vector in sector_vectors.items():
        sector_responses.append(
            SectorVectorResponse(
                sector_name=sector_name,
                vector_dimension=len(vector),
                news_count=0,  # TODO: Track news count
            )
        )

    return {
        "total_sectors": len(sector_responses),
        "sectors": [s.dict() for s in sector_responses],
    }


@router.post("/learn-patterns/{ticker}")
async def learn_crash_patterns(
    ticker: str,
    request: LearnPatternsRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Learn company-specific crash patterns.

    Analyzes historical crash days to identify
    news patterns that preceded price drops.

    Args:
        ticker: Stock ticker
        request: Learning parameters
        db: Database session

    Returns:
        Learned patterns
    """
    logger.info(f"Learning crash patterns for {ticker}")

    filter_engine = NewsContextFilter(db)

    patterns = await filter_engine.learn_crash_patterns(
        ticker=ticker.upper(),
        min_price_drop=request.min_price_drop,
        lookback_days=request.lookback_days,
    )

    return {
        "ticker": ticker.upper(),
        "total_patterns": len(patterns),
        "min_price_drop": request.min_price_drop,
        "lookback_days": request.lookback_days,
        "patterns": patterns,
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "News Context Filter API",
        "version": "1.0.0",
        "ensemble_methods": [
            "risk_cluster_learning",
            "sector_risk_vectors",
            "crash_pattern_matching",
            "sentiment_trend_analysis",
        ],
        "ensemble_weights": NewsContextFilter.WEIGHTS,
    }


@router.get("/docs/examples")
async def get_examples() -> Dict[str, Any]:
    """
    Get API usage examples.

    Returns:
        Example requests and use cases
    """
    return {
        "analyze_single_news": {
            "description": "Analyze single news item for risk",
            "request": {
                "ticker": "AAPL",
                "title": "Apple supplier faces production delays",
                "content": "Apple's main supplier announced production delays due to supply chain issues...",
                "publish_date": "2023-11-23T10:00:00",
            },
            "response_fields": {
                "cluster_risk": "Risk from similar crash patterns",
                "sector_risk": "Technology sector risk",
                "crash_pattern_risk": "AAPL-specific crash patterns",
                "sentiment_trend_risk": "Sentiment shift detection",
                "final_risk_score": "Weighted ensemble (0-1)",
                "risk_level": "CRITICAL/HIGH/NORMAL/LOW",
            },
        },
        "filter_batch": {
            "description": "Filter 100 news to top 10 high-risk",
            "request": {
                "news_items": [
                    {
                        "ticker": "AAPL",
                        "title": "...",
                        "content": "...",
                        "publish_date": "2023-11-23T10:00:00",
                    }
                ],
                "min_risk_score": 0.7,
            },
            "use_cases": [
                "Eliminate clickbait headlines",
                "Focus on material news only",
                "Reduce false positive alerts",
                "Improve signal-to-noise ratio",
            ],
        },
        "risk_clusters": {
            "description": "Get learned risk patterns",
            "endpoint": "/api/news/risk-clusters?rebuild=false&n_clusters=5",
            "use_cases": [
                "Understand common crash triggers",
                "Pattern-based early warning",
                "Market regime detection",
            ],
        },
        "sector_vectors": {
            "description": "Get sector risk profiles",
            "endpoint": "/api/news/sector-vectors?rebuild=false",
            "use_cases": [
                "Sector rotation analysis",
                "Industry-specific risk",
                "Peer comparison",
            ],
        },
    }
