"""
Additional News API Endpoints - Phase 20 Week 3-4

Processing Pipeline, Ticker Search, Tag Search, and Similar Articles
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from backend.data.news_models import NewsArticle, NewsTickerRelevance, get_db

router = APIRouter(prefix="/news", tags=["News Processing"])


@router.post("/process/{article_id}")
async def process_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Process a single article through the complete pipeline:
    - AI Analysis
    - Auto-Tagging
    - Embedding Generation
    - RAG Indexing
    """
    from backend.ai.news_processing_pipeline import NewsProcessingPipeline
    
    pipeline = NewsProcessingPipeline(db)
    results = await pipeline.process_article(article_id)
    
    return results


@router.post("/batch-process")
async def batch_process_articles(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Batch process unprocessed articles
    """
    from backend.ai.news_processing_pipeline import NewsProcessingPipeline
    
    pipeline = NewsProcessingPipeline(db)
    results = await pipeline.batch_process(limit=limit)
    
    return results


@router.get("/search/ticker/{ticker}")
async def search_by_ticker(
    ticker: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search news articles by ticker symbol
    
    Returns articles sorted by relevance and recency
    """
    # Query with join on ticker_relevance table
    articles = db.query(NewsArticle)\
        .join(NewsTickerRelevance)\
        .filter(NewsTickerRelevance.ticker == ticker.upper())\
        .order_by(
            NewsTickerRelevance.relevance.desc(),
            NewsArticle.published_at.desc()
        )\
        .limit(limit)\
        .all()
    
    # Convert to dict
    result_articles = []
    for article in articles:
        ticker_rel = db.query(NewsTickerRelevance).filter(
            NewsTickerRelevance.article_id == article.id,
            NewsTickerRelevance.ticker == ticker.upper()
        ).first()
        
        article_dict = {
            "id": article.id,
            "title": article.title,
            "source": article.source,
            "url": article.url,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "has_analysis": article.analysis is not None,
            "has_tags": article.has_tags,
            "has_embedding": article.has_embedding,
            "rag_indexed": article.rag_indexed,
            "relevance": ticker_rel.relevance if ticker_rel else 0,
            "sentiment": ticker_rel.sentiment if ticker_rel else None,
        }
        
        # Add analysis info if available
        if article.analysis:
            article_dict["analysis"] = {
                "sentiment": article.analysis.sentiment_overall,
                "impact": article.analysis.impact_magnitude,
                "actionable": article.analysis.trading_actionable,
            }
        
        result_articles.append(article_dict)
    
    return {
        "ticker": ticker.upper(),
        "count": len(result_articles),
        "articles": result_articles
    }


@router.get("/search/tag/{tag}")
async def search_by_tag(
    tag: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search articles by tag
    
    Examples:
    - sentiment:positive
    - impact:high
    - ticker:NVDA
    - keyword:ai
    """
    from backend.ai.news_auto_tagger import NewsAutoTagger
    
    tagger = NewsAutoTagger(db)
    articles = tagger.search_by_tag(tag, limit=limit)
    
    return {
        "tag": tag,
        "count": len(articles),
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "source": a.source,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "has_analysis": a.analysis is not None,
            }
            for a in articles
        ]
    }


@router.get("/articles/{article_id}/tags")
async def get_article_tags(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all tags for an article
    """
    from backend.ai.news_auto_tagger import NewsAutoTagger
    
    tagger = NewsAutoTagger(db)
    tags = tagger.get_article_tags(article_id)
    
    return {
        "article_id": article_id,
        "tags": tags
    }


@router.get("/articles/{article_id}/similar")
async def find_similar_articles(
    article_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Find similar articles based on embeddings
    """
    from backend.ai.news_embedder import NewsEmbedder
    
    embedder = NewsEmbedder(db)
    similar = embedder.find_similar_articles(article_id, limit=limit)
    
    return {
        "source_article_id": article_id,
        "similar_articles": [
            {
                "article_id": s["article"].id,
                "title": s["article"].title,
                "similarity": s["similarity"],
                "published_at": s["article"].published_at.isoformat() if s["article"].published_at else None,
            }
            for s in similar
        ]
    }


@router.get("/articles/{article_id}/status")
async def get_processing_status(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Get processing status for an article
    """
    from backend.ai.news_processing_pipeline import NewsProcessingPipeline
    
    pipeline = NewsProcessingPipeline(db)
    status = pipeline.get_processing_status(article_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return status
