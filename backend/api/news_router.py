"""
News Aggregation API Router

Features:
- RSS 크롤링 트리거
- 뉴스 조회 (필터링)
- AI 분석 트리거
- 티커별 뉴스
- 통계 조회
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json
import asyncio

from backend.data.news_models import (
    NewsArticle,
    NewsAnalysis,
    NewsTickerRelevance,
    RSSFeed,
    get_db,
    init_db,
)
from backend.data.rss_crawler import RSSCrawler, get_recent_articles, get_unanalyzed_articles, get_feed_stats
from backend.data.news_analyzer import (
    NewsDeepAnalyzer,
    get_analyzed_articles,
    get_ticker_news,
    get_high_impact_news,
    get_warning_news,
    get_daily_usage,
)
from backend.ai.gemini_client import GeminiClient


router = APIRouter(prefix="/news", tags=["News Aggregation"])


# ============================================================================
# Response Models
# ============================================================================

class NewsArticleResponse(BaseModel):
    id: int
    url: str
    title: str
    source: str
    feed_source: str
    published_at: Optional[str]
    content_summary: Optional[str]
    keywords: List[str]
    crawled_at: str
    has_analysis: bool
    sentiment: Optional[str] = None
    urgency: Optional[str] = None
    actionable: Optional[bool] = None
    related_tickers: List[str] = []
    
    class Config:
        from_attributes = True


class NewsAnalysisResponse(BaseModel):
    sentiment_overall: str
    sentiment_score: float
    sentiment_confidence: float
    urgency: str
    market_impact_short: str
    market_impact_long: str
    impact_magnitude: float
    affected_sectors: List[str]
    key_facts: List[str]
    key_warnings: List[str]
    trading_actionable: bool
    risk_category: str
    recommendation: str
    red_flags: List[str]
    analyzed_at: str
    tokens_used: int


class NewsDetailResponse(BaseModel):
    id: int
    url: str
    title: str
    source: str
    published_at: Optional[str]
    content_text: Optional[str]
    content_summary: Optional[str]
    keywords: List[str]
    authors: List[str]
    analysis: Optional[NewsAnalysisResponse]
    related_tickers: List[dict]


class CrawlResponse(BaseModel):
    total_articles: int
    feeds_processed: int
    articles_new: int
    articles_skipped: int
    content_extracted: int
    errors: List[dict]
    timestamp: str


class AnalyzeResponse(BaseModel):
    analyzed: int
    skipped: int
    errors: int
    remaining_requests: int
    details: List[dict]


# ============================================================================
# Initialize Database
# ============================================================================

@router.on_event("startup")
async def startup():
    init_db()


# ============================================================================
# Crawling Endpoints
# ============================================================================

@router.get("/crawl/stream")
async def crawl_rss_feeds_stream(
    extract_content: bool = True,
    use_gemini_diagnosis: bool = True,
    db: Session = Depends(get_db)
):
    """
    RSS 피드 크롤링 (Server-Sent Events 스트리밍)

    실시간 진행 상황을 스트리밍으로 전송

    Args:
        extract_content: 콘텐츠 전체 추출 여부
        use_gemini_diagnosis: 에러 발생 시 Gemini API로 진단 및 제안
    """
    async def event_generator():
        gemini_client = None
        if use_gemini_diagnosis:
            try:
                gemini_client = GeminiClient()
            except Exception as e:
                # Gemini 초기화 실패 시 경고하고 계속 진행
                print(f"Warning: Failed to initialize Gemini client: {e}")
                gemini_client = None

        try:
            crawler = RSSCrawler(db)
            feeds = db.query(RSSFeed).filter(RSSFeed.enabled == True).all()
            total_feeds = len(feeds)

            if total_feeds == 0:
                yield f"data: {json.dumps({'status': 'error', 'message': 'No active feeds found', 'progress_percent': 0})}\n\n"
                return

            articles_found = 0
            errors_list = []

            for index, feed in enumerate(feeds, 1):
                # 진행 상황 전송
                progress = {
                    'status': 'running',
                    'current_feed': feed.name,
                    'current_index': index,
                    'total_feeds': total_feeds,
                    'progress_percent': (index / total_feeds) * 100,
                    'articles_found': articles_found,
                    'errors': errors_list,
                    'message': f'Processing {feed.name}...'
                }
                yield f"data: {json.dumps(progress)}\n\n"
                await asyncio.sleep(0.1)  # Allow client to receive

                try:
                    # 피드 크롤링
                    articles = crawler.crawl_feed(feed, extract_content)
                    articles_found += len(articles)

                except Exception as e:
                    error_msg = str(e)
                    error_entry = {
                        'feed': feed.name,
                        'error': error_msg,
                        'suggestion': None
                    }

                    # Gemini API로 에러 진단 및 제안
                    if gemini_client:
                        try:
                            diagnosis = await gemini_client.diagnose_rss_feed_error(
                                feed_url=feed.url,
                                feed_name=feed.name,
                                error_message=error_msg
                            )
                            error_entry['suggestion'] = diagnosis['suggested_fix']
                            error_entry['diagnosis'] = diagnosis['diagnosis']
                            error_entry['likely_cause'] = diagnosis['likely_cause']
                            error_entry['alternative_urls'] = diagnosis.get('alternative_urls', [])
                        except Exception as gemini_error:
                            print(f"Gemini diagnosis failed for {feed.name}: {gemini_error}")

                    errors_list.append(error_entry)

                await asyncio.sleep(0.5)  # Rate limiting

            # 완료 메시지
            completion = {
                'status': 'completed',
                'current_feed': '',
                'current_index': total_feeds,
                'total_feeds': total_feeds,
                'progress_percent': 100,
                'articles_found': articles_found,
                'errors': errors_list,
                'message': f'Completed! Found {articles_found} articles.'
            }
            yield f"data: {json.dumps(completion)}\n\n"

        except Exception as e:
            error_response = {
                'status': 'error',
                'message': f'Fatal error: {str(e)}',
                'progress_percent': 0
            }
            yield f"data: {json.dumps(error_response)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_rss_feeds(
    extract_content: bool = True,
    db: Session = Depends(get_db)
):
    """
    모든 RSS 피드 크롤링 (기존 방식)

    - extract_content: 본문 전체 추출 여부 (기본 True)
    - 비용: $0 (무료)
    """
    crawler = RSSCrawler(db)
    result = crawler.crawl_all_feeds(extract_content=extract_content)

    return CrawlResponse(
        total_articles=result["total_articles"],
        feeds_processed=result["stats"]["feeds_processed"],
        articles_new=result["stats"]["articles_new"],
        articles_skipped=result["stats"]["articles_skipped"],
        content_extracted=result["stats"]["content_extracted"],
        errors=result["stats"]["errors"],
        timestamp=result["timestamp"]
    )


@router.post("/crawl/ticker/{ticker}")
async def crawl_ticker_news(
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    특정 티커 관련 뉴스 크롤링 (Yahoo Finance RSS)
    """
    crawler = RSSCrawler(db)
    articles = crawler.crawl_ticker_news(ticker.upper())
    
    return {
        "ticker": ticker.upper(),
        "articles_found": len(articles),
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "url": a.url,
                "published_at": a.published_at.isoformat() if a.published_at else None
            }
            for a in articles
        ]
    }


# ============================================================================
# Analysis Endpoints
# ============================================================================

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_unanalyzed_articles(
    max_count: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    분석되지 않은 기사 AI 분석
    
    - Gemini 무료 API 사용
    - 비용: $0 (1,500회/일)
    """
    unanalyzed = get_unanalyzed_articles(db, limit=max_count)
    
    if not unanalyzed:
        return AnalyzeResponse(
            analyzed=0,
            skipped=0,
            errors=0,
            remaining_requests=1500 - get_daily_usage()["request_count"],
            details=[]
        )
    
    analyzer = NewsDeepAnalyzer(db)
    result = analyzer.analyze_batch(unanalyzed, max_count=max_count)
    
    usage = get_daily_usage()
    
    return AnalyzeResponse(
        analyzed=result["analyzed"],
        skipped=result["skipped"],
        errors=result["errors"],
        remaining_requests=1500 - usage["request_count"],
        details=result["details"]
    )


@router.post("/analyze/{article_id}")
async def analyze_single_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """단일 기사 분석"""
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if article.analysis:
        return {
            "message": "Already analyzed",
            "analysis": article.analysis
        }
    
    analyzer = NewsDeepAnalyzer(db)
    analysis = analyzer.analyze_article(article)
    
    if not analysis:
        raise HTTPException(status_code=400, detail="Analysis failed (no content or parse error)")
    
    return {
        "message": "Analysis complete",
        "article_id": article_id,
        "sentiment": analysis.sentiment_overall,
        "score": analysis.sentiment_score,
        "actionable": analysis.trading_actionable,
        "remaining_requests": 1500 - get_daily_usage()["request_count"]
    }


# ============================================================================
# Query Endpoints
# ============================================================================

@router.get("/articles", response_model=List[NewsArticleResponse])
async def get_news_articles(
    limit: int = Query(default=50, ge=1, le=200),
    hours: int = Query(default=24, ge=1, le=168),
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    actionable_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    뉴스 기사 조회
    
    - limit: 최대 개수
    - hours: 최근 N시간
    - source: 소스 필터
    - sentiment: 감정 필터 (positive/negative/neutral/mixed)
    - actionable_only: 행동 가능한 것만
    """
    if sentiment or actionable_only:
        articles = get_analyzed_articles(db, limit, sentiment, actionable_only)
    else:
        articles = get_recent_articles(db, limit, hours, source)
    
    return [
        NewsArticleResponse(
            id=a.id,
            url=a.url,
            title=a.title,
            source=a.source or "",
            feed_source=a.feed_source or "rss",
            published_at=a.published_at.isoformat() if a.published_at else None,
            content_summary=a.content_summary[:500] if a.content_summary else None,
            keywords=a.keywords or [],
            crawled_at=a.crawled_at.isoformat() if a.crawled_at else datetime.utcnow().isoformat(),
            has_analysis=a.analysis is not None,
            sentiment=a.analysis.sentiment_overall if a.analysis else None,
            urgency=a.analysis.urgency if a.analysis else None,
            actionable=a.analysis.trading_actionable if a.analysis else None,
            related_tickers=[rel.ticker for rel in a.ticker_relevances] if a.ticker_relevances else []
        )
        for a in articles
    ]


@router.get("/articles/{article_id}", response_model=NewsDetailResponse)
async def get_news_detail(
    article_id: int,
    db: Session = Depends(get_db)
):
    """기사 상세 조회 (분석 포함)"""
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    analysis_response = None
    if article.analysis:
        a = article.analysis
        analysis_response = NewsAnalysisResponse(
            sentiment_overall=a.sentiment_overall or "neutral",
            sentiment_score=a.sentiment_score or 0.0,
            sentiment_confidence=a.sentiment_confidence or 0.5,
            urgency=a.urgency or "medium",
            market_impact_short=a.market_impact_short or "neutral",
            market_impact_long=a.market_impact_long or "neutral",
            impact_magnitude=a.impact_magnitude or 0.0,
            affected_sectors=a.affected_sectors or [],
            key_facts=a.key_facts or [],
            key_warnings=a.key_warnings or [],
            trading_actionable=a.trading_actionable or False,
            risk_category=a.risk_category or "none",
            recommendation=a.recommendation or "",
            red_flags=a.red_flags or [],
            analyzed_at=a.analyzed_at.isoformat() if a.analyzed_at else datetime.utcnow().isoformat(),
            tokens_used=a.tokens_used or 0
        )
    
    related_tickers = [
        {
            "ticker": rel.ticker,
            "relevance": rel.relevance_score,
            "sentiment": rel.sentiment_for_ticker
        }
        for rel in article.ticker_relevances
    ]
    
    return NewsDetailResponse(
        id=article.id,
        url=article.url,
        title=article.title,
        source=article.source or "",
        published_at=article.published_at.isoformat() if article.published_at else None,
        content_text=article.content_text,
        content_summary=article.content_summary,
        keywords=article.keywords or [],
        authors=article.authors or [],
        analysis=analysis_response,
        related_tickers=related_tickers
    )


@router.get("/ticker/{ticker}")
async def get_news_by_ticker(
    ticker: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """특정 티커 관련 뉴스"""
    news = get_ticker_news(db, ticker.upper(), limit)
    return {
        "ticker": ticker.upper(),
        "count": len(news),
        "articles": news
    }


@router.get("/high-impact")
async def get_high_impact_articles(
    min_magnitude: float = Query(default=0.6, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """높은 영향도 뉴스"""
    articles = get_high_impact_news(db, min_magnitude)
    return {
        "count": len(articles),
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "source": a.source,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "impact_magnitude": a.analysis.impact_magnitude if a.analysis else 0,
                "sentiment": a.analysis.sentiment_overall if a.analysis else "unknown",
                "affected_sectors": a.analysis.affected_sectors if a.analysis else []
            }
            for a in articles
        ]
    }


@router.get("/warnings")
async def get_warning_articles(db: Session = Depends(get_db)):
    """경고 신호가 있는 뉴스"""
    articles = get_warning_news(db)
    return {
        "count": len(articles),
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "source": a.source,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "warnings": a.analysis.key_warnings if a.analysis else [],
                "red_flags": a.analysis.red_flags if a.analysis else [],
                "recommendation": a.analysis.recommendation if a.analysis else ""
            }
            for a in articles
        ]
    }


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats")
async def get_news_statistics(db: Session = Depends(get_db)):
    """뉴스 통계"""
    total_articles = db.query(NewsArticle).count()
    analyzed_articles = db.query(NewsAnalysis).count()
    
    # 감정별 통계
    positive = db.query(NewsAnalysis).filter(NewsAnalysis.sentiment_overall == "positive").count()
    negative = db.query(NewsAnalysis).filter(NewsAnalysis.sentiment_overall == "negative").count()
    neutral = db.query(NewsAnalysis).filter(NewsAnalysis.sentiment_overall == "neutral").count()
    
    # 행동 가능한 뉴스
    actionable = db.query(NewsAnalysis).filter(NewsAnalysis.trading_actionable == True).count()
    
    # Gemini 사용량
    usage = get_daily_usage()
    
    return {
        "total_articles": total_articles,
        "analyzed_articles": analyzed_articles,
        "unanalyzed_articles": total_articles - analyzed_articles,
        "sentiment_distribution": {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "mixed": analyzed_articles - positive - negative - neutral
        },
        "actionable_count": actionable,
        "gemini_usage": {
            "date": usage["date"],
            "requests_used": usage["request_count"],
            "requests_remaining": 1500 - usage["request_count"],
            "total_tokens": usage["total_input_tokens"] + usage["total_output_tokens"],
            "cost": "$0.00 (무료 티어)"
        }
    }


@router.get("/feeds")
async def get_rss_feeds(db: Session = Depends(get_db)):
    """RSS 피드 목록 및 통계"""
    return get_feed_stats(db)


@router.post("/feeds")
async def add_rss_feed(
    name: str,
    url: str,
    category: str = "global",
    db: Session = Depends(get_db)
):
    """새 RSS 피드 추가"""
    existing = db.query(RSSFeed).filter(RSSFeed.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feed with this name already exists")
    
    feed = RSSFeed(name=name, url=url, category=category, enabled=True)
    db.add(feed)
    db.commit()
    db.refresh(feed)
    
    return {
        "message": "Feed added",
        "id": feed.id,
        "name": feed.name,
        "url": feed.url
    }


@router.put("/feeds/{feed_id}/toggle")
async def toggle_feed(
    feed_id: int,
    db: Session = Depends(get_db)
):
    """피드 활성화/비활성화 토글"""
    feed = db.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    feed.enabled = not feed.enabled
    db.commit()
    
    return {
        "id": feed.id,
        "name": feed.name,
        "enabled": feed.enabled
    }
