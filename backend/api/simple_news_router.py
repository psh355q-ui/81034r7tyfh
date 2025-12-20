"""
Simple News API Router - PostgreSQL 기반
메인 데이터베이스의 news_articles 테이블 사용
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import asyncio
import json
import feedparser
import hashlib
import html

from backend.database.repository import get_sync_session
from backend.database.models import NewsArticle, AnalysisResult


router = APIRouter(prefix="/news", tags=["News"])


# ============================================================================
# Response Models
# ============================================================================

class NewsArticleResponse(BaseModel):
    id: int
    title: str
    content: Optional[str]
    url: str
    source: str
    published_date: Optional[datetime]
    published_at: Optional[datetime] = None  # Alias for frontend compatibility
    crawled_at: datetime
    keywords: List[str] = []  # Frontend expects this
    analyzed: bool = False  # Frontend expects this
    authors: List[str] = []  # Frontend expects this for NewsDetail
    related_tickers: List[dict] = []  # Frontend expects this for NewsDetailModal
    analysis: Optional[dict] = None  # Frontend expects this

    class Config:
        from_attributes = True


class NewsStatsResponse(BaseModel):
    total_articles: int
    analyzed_articles: int
    unanalyzed_articles: int  # Frontend expects this
    pending_analysis: int  # Deprecated but kept for compatibility
    sources: dict
    recent_24h: int
    sentiment_distribution: dict = {
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "mixed": 0
    }
    actionable_count: int = 0
    gemini_usage: dict = {
        "date": "",
        "requests_used": 0,
        "requests_remaining": 1500,
        "total_tokens": 0,
        "cost": "$0.00"
    }


# ============================================================================
# Dependencies
# ============================================================================

def get_db():
    """Database session dependency"""
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/articles", response_model=List[NewsArticleResponse])
async def get_news_articles(
    limit: int = Query(50, ge=1, le=200),
    hours: int = Query(24, ge=1, le=168),
    actionable_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    뉴스 기사 목록 조회

    Args:
        limit: 최대 개수
        hours: 최근 N시간 이내
        actionable_only: 분석된 기사만 (현재는 무시)
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)

    # Exclude KIS_API source (those are account sync events, not real news)
    query = db.query(NewsArticle).filter(
        NewsArticle.crawled_at >= cutoff_time,
        NewsArticle.source != "KIS_API"
    ).order_by(desc(NewsArticle.published_date)).limit(limit)

    articles = query.all()

    # Get article IDs that have analysis
    analyzed_ids = set(
        row[0] for row in db.query(AnalysisResult.article_id)
        .filter(AnalysisResult.article_id.in_([a.id for a in articles]))
        .distinct()
        .all()
    ) if articles else set()

    return [
        NewsArticleResponse(
            id=article.id,
            title=article.title,
            content=article.content[:500] if article.content else None,  # 500자 제한
            url=article.url,
            source=article.source,
            published_date=article.published_date,
            published_at=article.published_date,  # Frontend compatibility
            crawled_at=article.crawled_at,
            keywords=[],  # TODO: Extract from analysis if available
            analyzed=article.id in analyzed_ids,
            authors=[],  # TODO: Extract from article metadata if available
            related_tickers=[],  # TODO: Extract from analysis if available
            analysis=None  # TODO: Get from analysis_results if available
        )
        for article in articles
    ]


@router.get("/articles/{article_id}", response_model=NewsArticleResponse)
async def get_news_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """특정 뉴스 기사 상세 조회"""
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Check if article has analysis
    has_analysis = db.query(AnalysisResult).filter(
        AnalysisResult.article_id == article_id
    ).first() is not None

    return NewsArticleResponse(
        id=article.id,
        title=article.title,
        content=article.content,
        url=article.url,
        source=article.source,
        published_date=article.published_date,
        published_at=article.published_date,  # Frontend compatibility
        crawled_at=article.crawled_at,
        keywords=[],  # TODO: Extract from analysis if available
        analyzed=has_analysis,
        authors=[],  # TODO: Extract from article metadata if available
        related_tickers=[],  # TODO: Extract from analysis if available
        analysis=None  # TODO: Get from analysis_results if available
    )


@router.get("/stats", response_model=NewsStatsResponse)
async def get_news_stats(db: Session = Depends(get_db)):
    """뉴스 통계 조회"""
    from datetime import date

    # 전체 뉴스 개수 (KIS_API 제외)
    total_articles = db.query(NewsArticle).filter(
        NewsArticle.source != "KIS_API"
    ).count()

    # 분석된 뉴스 개수 (analysis_results와 연결된 것, KIS_API 제외)
    analyzed_articles = db.query(NewsArticle).join(
        AnalysisResult,
        NewsArticle.id == AnalysisResult.article_id
    ).filter(
        NewsArticle.source != "KIS_API"
    ).count()

    unanalyzed_articles = total_articles - analyzed_articles

    # 소스별 개수 (KIS_API 제외)
    source_counts = db.query(
        NewsArticle.source,
        func.count(NewsArticle.id)
    ).filter(
        NewsArticle.source != "KIS_API"
    ).group_by(NewsArticle.source).all()

    sources = {source: count for source, count in source_counts}

    # 최근 24시간 뉴스 (KIS_API 제외)
    cutoff = datetime.now() - timedelta(hours=24)
    recent_24h = db.query(NewsArticle).filter(
        NewsArticle.crawled_at >= cutoff,
        NewsArticle.source != "KIS_API"
    ).count()

    # TODO: Get real sentiment distribution from analysis_results
    # For now, return mock data
    sentiment_distribution = {
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "mixed": 0
    }

    # TODO: Count actionable articles (those with trading signals)
    actionable_count = 0

    # TODO: Get real Gemini usage from cost tracking system
    gemini_usage = {
        "date": date.today().isoformat(),
        "requests_used": 0,
        "requests_remaining": 1500,
        "total_tokens": 0,
        "cost": "$0.00"
    }

    return NewsStatsResponse(
        total_articles=total_articles,
        analyzed_articles=analyzed_articles,
        unanalyzed_articles=unanalyzed_articles,
        pending_analysis=unanalyzed_articles,
        sources=sources,
        recent_24h=recent_24h,
        sentiment_distribution=sentiment_distribution,
        actionable_count=actionable_count,
        gemini_usage=gemini_usage
    )


@router.get("/health")
async def news_health():
    """Health check endpoint"""
    return {"status": "ok", "service": "news"}


# ============================================================================
# RSS Crawling with SSE
# ============================================================================

# RSS Feeds to crawl
RSS_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Reuters": "http://feeds.reuters.com/reuters/technologyNews",
    "CNBC Tech": "https://www.cnbc.com/id/19854910/device/rss/rss.html",
}


async def crawl_rss_feeds_with_progress():
    """
    RSS 피드를 크롤링하고 실시간으로 진행상황을 SSE로 전송
    """
    total_feeds = len(RSS_FEEDS)
    processed_feeds = 0
    total_articles = 0
    new_articles = 0
    skipped_articles = 0
    errors = []

    # 초기 상태 전송
    yield f"data: {json.dumps({
        'status': 'running',
        'message': 'Starting RSS crawl...',
        'total_feeds': total_feeds,
        'current_index': 0,
        'progress_percent': 0,
        'articles_found': 0,
        'current_feed': None,
        'errors': []
    })}\n\n"
    await asyncio.sleep(0.1)

    db = get_sync_session()
    try:
        for source_name, feed_url in RSS_FEEDS.items():
            try:
                # 진행상황 업데이트
                progress_percent = (processed_feeds / total_feeds) * 100
                yield f"data: {json.dumps({
                    'status': 'running',
                    'message': f'Processing {source_name}...',
                    'total_feeds': total_feeds,
                    'current_index': processed_feeds,
                    'progress_percent': progress_percent,
                    'articles_found': new_articles,
                    'current_feed': source_name,
                    'errors': errors
                })}\n\n"
                await asyncio.sleep(0.1)

                # RSS 피드 파싱
                loop = asyncio.get_event_loop()
                feed = await loop.run_in_executor(None, feedparser.parse, feed_url)

                for entry in feed.entries[:20]:  # 최근 20개만
                    try:
                        total_articles += 1

                        # UTF-8 안전하게 처리
                        title = entry.get('title', 'No Title')
                        content = entry.get('summary', entry.get('description', ''))
                        url = entry.get('link', '')

                        # HTML 엔티티 디코딩
                        title = html.unescape(title)
                        content = html.unescape(content)

                        # 특수 문자를 ASCII 호환 문자로 변환
                        replacements = {
                            '\u2019': "'",  # Right single quotation mark
                            '\u2018': "'",  # Left single quotation mark
                            '\u201c': '"',  # Left double quotation mark
                            '\u201d': '"',  # Right double quotation mark
                            '\u2013': '-',  # En dash
                            '\u2014': '--', # Em dash
                            '\u2026': '...', # Ellipsis
                            '\xa0': ' ',    # Non-breaking space
                        }

                        for old_char, new_char in replacements.items():
                            title = title.replace(old_char, new_char)
                            content = content.replace(old_char, new_char)

                        # 남은 non-ASCII 문자 제거
                        title = title.encode('ascii', errors='ignore').decode('ascii')
                        content = content.encode('ascii', errors='ignore').decode('ascii')

                        # 발행일 파싱
                        published_date = datetime.now()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            from time import mktime
                            published_date = datetime.fromtimestamp(mktime(entry.published_parsed))

                        # 해시 계산 (중복 체크) - ASCII로 인코딩
                        content_hash = hashlib.sha256(f"{title}{content}".encode('ascii', errors='ignore')).hexdigest()

                        # 중복 체크
                        existing = db.query(NewsArticle).filter(
                            NewsArticle.content_hash == content_hash
                        ).first()

                        if existing:
                            skipped_articles += 1
                            continue

                        # 새 기사 저장
                        article = NewsArticle(
                            title=title,
                            content=content,
                            url=url,
                            source=source_name,
                            published_date=published_date,
                            crawled_at=datetime.now(),
                            content_hash=content_hash
                        )
                        db.add(article)
                        new_articles += 1
                    except Exception as article_error:
                        # 개별 기사 처리 실패는 무시하고 계속 진행
                        continue

                db.commit()
                processed_feeds += 1

                # 피드 완료 알림
                progress_percent = (processed_feeds / total_feeds) * 100
                yield f"data: {json.dumps({
                    'status': 'running',
                    'message': f'Completed {source_name}',
                    'total_feeds': total_feeds,
                    'current_index': processed_feeds,
                    'progress_percent': progress_percent,
                    'articles_found': new_articles,
                    'current_feed': source_name,
                    'errors': errors
                })}\n\n"
                await asyncio.sleep(0.1)

            except Exception as e:
                # 트랜잭션 롤백
                db.rollback()

                error_info = {'feed': source_name, 'error': str(e)}
                errors.append(error_info)
                progress_percent = (processed_feeds / total_feeds) * 100 if total_feeds > 0 else 0
                yield f"data: {json.dumps({
                    'status': 'running',
                    'message': f'Error processing {source_name}',
                    'total_feeds': total_feeds,
                    'current_index': processed_feeds,
                    'progress_percent': progress_percent,
                    'articles_found': new_articles,
                    'current_feed': source_name,
                    'errors': errors
                })}\n\n"
                await asyncio.sleep(0.1)

        # 완료 메시지
        result = {
            'status': 'completed',
            'message': f'Crawl complete! Found {new_articles} new articles',
            'total_feeds': total_feeds,
            'current_index': processed_feeds,
            'progress_percent': 100,
            'articles_found': new_articles,
            'current_feed': None,
            'errors': errors,
            'total_articles': total_articles,
            'skipped_articles': skipped_articles,
            'feeds_processed': processed_feeds,
            'timestamp': datetime.now().isoformat()
        }
        yield f"data: {json.dumps(result)}\n\n"

    finally:
        db.close()


@router.get("/crawl/stream")
async def crawl_rss_stream(extract_content: bool = True):
    """
    RSS 피드 크롤링 (Server-Sent Events)

    프론트엔드에서 실시간으로 진행상황을 모니터링할 수 있습니다.
    """
    return StreamingResponse(
        crawl_rss_feeds_with_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
