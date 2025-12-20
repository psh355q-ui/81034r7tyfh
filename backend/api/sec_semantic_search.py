"""
SEC Semantic Search API - Phase 13.5

Advanced semantic search for SEC filings using RAG.
Provides investor-focused search capabilities:
1. Natural language semantic search
2. Risk-focused search
3. Trend analysis (time-series comparison)
4. Similar companies finder

Usage:
    POST /api/sec/semantic-search
    POST /api/sec/risk-search
    POST /api/sec/trend-search
    GET /api/sec/similar-companies/{ticker}
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.ai.vector_search import VectorSearch
from backend.ai.embedding_engine import EmbeddingEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sec", tags=["SEC Semantic Search"])


# ============================================================================
# Request/Response Models
# ============================================================================


class SemanticSearchRequest(BaseModel):
    """Semantic search request."""

    ticker: str = Field(..., description="Stock ticker (e.g., AAPL)")
    query: str = Field(..., description="Natural language query")
    top_k: int = Field(5, ge=1, le=20, description="Number of results")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    filing_types: Optional[List[str]] = Field(
        None, description="Filing types (10-K, 10-Q, 8-K)"
    )


class RiskSearchRequest(BaseModel):
    """Risk-focused search request."""

    ticker: str = Field(..., description="Stock ticker")
    risk_categories: Optional[List[str]] = Field(
        None,
        description="Risk categories (regulatory, operational, market, legal, etc.)",
    )
    top_k: int = Field(5, ge=1, le=20)
    severity_threshold: float = Field(
        0.0, ge=0.0, le=1.0, description="Minimum risk severity"
    )


class TrendSearchRequest(BaseModel):
    """Trend analysis search request."""

    ticker: str = Field(..., description="Stock ticker")
    query: str = Field(..., description="Topic to track over time")
    start_year: int = Field(..., description="Start year")
    end_year: int = Field(..., description="End year")
    filing_type: str = Field("10-K", description="Filing type (10-K or 10-Q)")


class SearchResult(BaseModel):
    """Single search result."""

    score: float = Field(..., description="Similarity score (0-1)")
    ticker: str
    filing_type: str
    filing_date: str
    content: str = Field(..., description="Relevant text excerpt")
    metadata: Optional[Dict[str, Any]] = None


class SemanticSearchResponse(BaseModel):
    """Semantic search response."""

    query: str
    ticker: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float


class TrendPoint(BaseModel):
    """Single point in trend analysis."""

    year: int
    quarter: Optional[int] = None
    filing_date: str
    relevance_score: float
    summary: str
    key_excerpts: List[str]


class TrendSearchResponse(BaseModel):
    """Trend analysis response."""

    ticker: str
    query: str
    period: str
    trend_points: List[TrendPoint]
    overall_trend: str  # "increasing", "decreasing", "stable"
    insights: List[str]


class SimilarCompany(BaseModel):
    """Similar company result."""

    ticker: str
    similarity_score: float
    common_themes: List[str]
    sector: Optional[str] = None
    market_cap: Optional[float] = None


class SimilarCompaniesResponse(BaseModel):
    """Similar companies response."""

    ticker: str
    similar_companies: List[SimilarCompany]
    basis: str  # "10-K filings", "risk factors", etc.


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SemanticSearchResponse:
    """
    Advanced semantic search for SEC filings.

    Finds relevant sections based on natural language query.
    Uses vector similarity to find semantically related content.

    Example queries:
    - "What are the company's supply chain risks?"
    - "How has revenue growth been discussed?"
    - "What challenges does management mention?"
    - "Competitive advantages and moats"

    Args:
        request: Search request
        db: Database session

    Returns:
        Search results with similarity scores
    """
    import time

    start_time = time.time()

    logger.info(
        f"Semantic search: ticker={request.ticker}, query='{request.query}'"
    )

    # Initialize engines
    embedding_engine = EmbeddingEngine(db)
    vector_search = VectorSearch(db)

    # Parse date filters
    date_from = None
    date_to = None
    if request.date_from:
        date_from = datetime.strptime(request.date_from, "%Y-%m-%d")
    if request.date_to:
        date_to = datetime.strptime(request.date_to, "%Y-%m-%d")

    # Perform vector search
    results = await vector_search.semantic_search(
        query=request.query,
        ticker=request.ticker,
        document_type="sec_filing",
        top_k=request.top_k,
        date_from=date_from,
        date_to=date_to,
    )

    # Format results
    search_results = []
    for result in results:
        search_results.append(
            SearchResult(
                score=result["similarity"],
                ticker=result["ticker"],
                filing_type=result.get("metadata", {}).get("filing_type", "Unknown"),
                filing_date=result["source_date"].strftime("%Y-%m-%d"),
                content=result["content"],
                metadata=result.get("metadata", {}),
            )
        )

    search_time = (time.time() - start_time) * 1000

    return SemanticSearchResponse(
        query=request.query,
        ticker=request.ticker,
        results=search_results,
        total_results=len(search_results),
        search_time_ms=search_time,
    )


@router.post("/risk-search", response_model=SemanticSearchResponse)
async def risk_search(
    request: RiskSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SemanticSearchResponse:
    """
    Risk-focused semantic search.

    Searches specifically for risk factors and warning signals.
    Automatically filters for risk-related content.

    Risk categories:
    - regulatory: Regulatory changes, compliance issues
    - operational: Supply chain, production, operations
    - market: Competition, market conditions, pricing
    - legal: Lawsuits, investigations, legal risks
    - financial: Debt, liquidity, credit risks
    - technology: Cybersecurity, system failures
    - reputational: Brand damage, public perception

    Args:
        request: Risk search request
        db: Database session

    Returns:
        Risk-focused search results
    """
    import time

    start_time = time.time()

    logger.info(f"Risk search: ticker={request.ticker}")

    # Build risk-focused query
    risk_keywords = {
        "regulatory": "regulatory compliance changes government policy",
        "operational": "supply chain operations production disruption",
        "market": "competition market conditions pricing pressure",
        "legal": "lawsuit litigation investigation legal proceedings",
        "financial": "debt liquidity credit financial distress",
        "technology": "cybersecurity data breach system failure",
        "reputational": "reputation brand damage public perception",
    }

    # Combine requested categories
    if request.risk_categories:
        query_parts = [
            risk_keywords.get(cat, cat) for cat in request.risk_categories
        ]
        query = "risk factors: " + " ".join(query_parts)
    else:
        query = "risk factors warnings uncertainties challenges threats"

    # Initialize engines
    vector_search = VectorSearch(db)

    # Search with risk focus
    results = await vector_search.semantic_search(
        query=query,
        ticker=request.ticker,
        document_type="sec_filing",
        top_k=request.top_k * 2,  # Get more, then filter
    )

    # Filter by severity threshold
    filtered_results = []
    for result in results:
        # Risk severity heuristic: keyword density + similarity
        content = result["content"].lower()
        risk_count = sum(
            content.count(word)
            for word in ["risk", "adverse", "uncertain", "threat", "challenge"]
        )
        severity = min(risk_count / 100 + result["similarity"] * 0.5, 1.0)

        if severity >= request.severity_threshold:
            filtered_results.append(
                SearchResult(
                    score=severity,
                    ticker=result["ticker"],
                    filing_type=result.get("metadata", {}).get(
                        "filing_type", "Unknown"
                    ),
                    filing_date=result["source_date"].strftime("%Y-%m-%d"),
                    content=result["content"],
                    metadata={
                        **result.get("metadata", {}),
                        "risk_severity": severity,
                        "risk_keyword_count": risk_count,
                    },
                )
            )

    # Sort by severity and limit
    filtered_results.sort(key=lambda x: x.score, reverse=True)
    filtered_results = filtered_results[: request.top_k]

    search_time = (time.time() - start_time) * 1000

    return SemanticSearchResponse(
        query=query,
        ticker=request.ticker,
        results=filtered_results,
        total_results=len(filtered_results),
        search_time_ms=search_time,
    )


@router.post("/trend-search", response_model=TrendSearchResponse)
async def trend_search(
    request: TrendSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> TrendSearchResponse:
    """
    Time-series trend analysis.

    Tracks how a specific topic evolves over multiple years.
    Compares year-over-year changes in discussion.

    Use cases:
    - "How has discussion of AI changed over time?"
    - "Track mentions of supply chain issues 2020-2023"
    - "Evolution of competitive landscape"

    Args:
        request: Trend search request
        db: Database session

    Returns:
        Trend analysis with year-over-year insights
    """
    import time
    from collections import defaultdict

    start_time = time.time()

    logger.info(
        f"Trend search: ticker={request.ticker}, "
        f"query='{request.query}', years={request.start_year}-{request.end_year}"
    )

    vector_search = VectorSearch(db)

    # Collect data points for each year
    trend_points = []

    for year in range(request.start_year, request.end_year + 1):
        # Search within this year
        year_start = datetime(year, 1, 1)
        year_end = datetime(year, 12, 31)

        results = await vector_search.semantic_search(
            query=request.query,
            ticker=request.ticker,
            document_type="sec_filing",
            top_k=3,
            date_from=year_start,
            date_to=year_end,
        )

        if results:
            # Calculate average relevance for this year
            avg_score = sum(r["similarity"] for r in results) / len(results)

            # Extract key excerpts
            excerpts = [r["content"][:200] + "..." for r in results[:2]]

            # Determine quarter if 10-Q
            filing_date = results[0]["source_date"]
            quarter = (filing_date.month - 1) // 3 + 1 if request.filing_type == "10-Q" else None

            trend_points.append(
                TrendPoint(
                    year=year,
                    quarter=quarter,
                    filing_date=filing_date.strftime("%Y-%m-%d"),
                    relevance_score=avg_score,
                    summary=f"Year {year}: Average relevance {avg_score:.2f}",
                    key_excerpts=excerpts,
                )
            )

    # Determine overall trend
    if len(trend_points) >= 2:
        scores = [p.relevance_score for p in trend_points]
        trend_direction = scores[-1] - scores[0]

        if trend_direction > 0.1:
            overall_trend = "increasing"
        elif trend_direction < -0.1:
            overall_trend = "decreasing"
        else:
            overall_trend = "stable"
    else:
        overall_trend = "insufficient_data"

    # Generate insights
    insights = []
    if trend_points:
        max_year = max(trend_points, key=lambda p: p.relevance_score)
        insights.append(
            f"Peak relevance in {max_year.year} (score: {max_year.relevance_score:.2f})"
        )

        if overall_trend == "increasing":
            insights.append(
                f"Discussion of '{request.query}' has increased from "
                f"{trend_points[0].year} to {trend_points[-1].year}"
            )
        elif overall_trend == "decreasing":
            insights.append(
                f"Discussion of '{request.query}' has decreased over time"
            )

    search_time = (time.time() - start_time) * 1000
    logger.info(f"Trend search completed in {search_time:.0f}ms")

    return TrendSearchResponse(
        ticker=request.ticker,
        query=request.query,
        period=f"{request.start_year}-{request.end_year}",
        trend_points=trend_points,
        overall_trend=overall_trend,
        insights=insights,
    )


@router.get("/similar-companies/{ticker}", response_model=SimilarCompaniesResponse)
async def find_similar_companies(
    ticker: str,
    top_k: int = Query(5, ge=1, le=20, description="Number of similar companies"),
    basis: str = Query(
        "risk_factors",
        description="Similarity basis: risk_factors, business_model, all",
    ),
    db: AsyncSession = Depends(get_db),
) -> SimilarCompaniesResponse:
    """
    Find companies with similar SEC filing content.

    Uses vector similarity to find companies that:
    - Face similar risks
    - Have similar business models
    - Operate in similar markets

    Useful for:
    - Sector analysis
    - Peer comparison
    - Portfolio diversification

    Args:
        ticker: Reference ticker
        top_k: Number of similar companies
        basis: What to compare (risk_factors, business_model, all)
        db: Database session

    Returns:
        List of similar companies with similarity scores
    """
    logger.info(f"Finding companies similar to {ticker} (basis={basis})")

    from sqlalchemy import select, func, and_, distinct
    from backend.core.models.embedding_models import DocumentEmbedding

    # Get representative embedding for the ticker
    # We'll use the average of all embeddings for this ticker
    result = await db.execute(
        select(
            func.avg(DocumentEmbedding.embedding).label("avg_embedding"),
        ).where(
            and_(
                DocumentEmbedding.ticker == ticker.upper(),
                DocumentEmbedding.document_type == "sec_filing",
            )
        )
    )

    row = result.one_or_none()
    if not row or not row.avg_embedding:
        raise HTTPException(
            status_code=404,
            detail=f"No SEC filings found for ticker {ticker}",
        )

    reference_embedding = row.avg_embedding

    # Find similar companies
    # Query for other tickers with high cosine similarity
    similarity_query = select(
        DocumentEmbedding.ticker,
        (1 - DocumentEmbedding.embedding.cosine_distance(reference_embedding)).label(
            "similarity"
        ),
    ).where(
        and_(
            DocumentEmbedding.ticker != ticker.upper(),
            DocumentEmbedding.document_type == "sec_filing",
        )
    )

    result = await db.execute(similarity_query)
    rows = result.fetchall()

    # Aggregate by ticker
    from collections import defaultdict

    ticker_scores = defaultdict(list)
    for row in rows:
        ticker_scores[row.ticker].append(row.similarity)

    # Calculate average similarity per ticker
    ticker_avg = {
        t: sum(scores) / len(scores) for t, scores in ticker_scores.items()
    }

    # Sort and get top K
    sorted_tickers = sorted(ticker_avg.items(), key=lambda x: x[1], reverse=True)[
        :top_k
    ]

    # Build response
    similar_companies = []
    for similar_ticker, score in sorted_tickers:
        similar_companies.append(
            SimilarCompany(
                ticker=similar_ticker,
                similarity_score=score,
                common_themes=["Risk factors", "Business model"],  # TODO: Extract themes
                sector=None,  # TODO: Add sector mapping
                market_cap=None,  # TODO: Add market cap
            )
        )

    return SimilarCompaniesResponse(
        ticker=ticker.upper(),
        similar_companies=similar_companies,
        basis=basis,
    )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SEC Semantic Search API",
        "version": "1.0.0",
        "features": [
            "semantic_search",
            "risk_search",
            "trend_analysis",
            "similar_companies",
        ],
    }


# Example usage documentation
@router.get("/docs/examples")
async def get_examples() -> Dict[str, Any]:
    """
    Get API usage examples.

    Returns:
        Example requests and responses
    """
    return {
        "semantic_search": {
            "description": "Natural language search for SEC filings",
            "request": {
                "ticker": "AAPL",
                "query": "What are the main supply chain risks?",
                "top_k": 5,
                "date_from": "2022-01-01",
            },
            "use_cases": [
                "Find specific topics in lengthy filings",
                "Research company risks and opportunities",
                "Compare discussion across time periods",
            ],
        },
        "risk_search": {
            "description": "Search specifically for risk factors",
            "request": {
                "ticker": "TSLA",
                "risk_categories": ["regulatory", "operational"],
                "top_k": 5,
                "severity_threshold": 0.5,
            },
            "use_cases": [
                "Due diligence for investments",
                "Risk assessment for portfolio",
                "Regulatory compliance monitoring",
            ],
        },
        "trend_search": {
            "description": "Track topic evolution over time",
            "request": {
                "ticker": "NVDA",
                "query": "artificial intelligence GPU computing",
                "start_year": 2020,
                "end_year": 2023,
                "filing_type": "10-K",
            },
            "use_cases": [
                "Track strategic focus changes",
                "Monitor emerging risks",
                "Identify business model evolution",
            ],
        },
        "similar_companies": {
            "description": "Find companies with similar profiles",
            "endpoint": "/api/sec/similar-companies/AAPL?top_k=5",
            "use_cases": [
                "Peer comparison",
                "Sector analysis",
                "Portfolio diversification ideas",
            ],
        },
    }
