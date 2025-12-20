"""
RSS Feed Management API Router

Features:
- List all RSS feeds
- Add new feeds
- Update existing feeds (URL, enabled status)
- Delete feeds
- Feed statistics
- Apply Gemini diagnosis suggestions

This completes the workflow where Gemini diagnoses RSS errors
and users can fix them directly from the UI.

Author: AI Trading System
Date: 2025-11-15
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, HttpUrl, validator
from sqlalchemy.orm import Session

# Import your models and dependencies
from backend.data.news_models import RSSFeed, get_db
# Uncomment if you have auth system:
# from backend.auth import require_read, require_write


router = APIRouter(prefix="/feeds", tags=["RSS Feed Management"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RSSFeedBase(BaseModel):
    name: str
    url: str
    category: str = "general"
    enabled: bool = True
    
    @validator("url")
    def validate_url(cls, v):
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("URL must start with http:// or https://")
        return v
    
    @validator("name")
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()


class RSSFeedCreate(RSSFeedBase):
    """Request model for creating a new RSS feed"""
    pass


class RSSFeedUpdate(BaseModel):
    """Request model for updating an existing RSS feed"""
    name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    enabled: Optional[bool] = None
    
    @validator("url")
    def validate_url(cls, v):
        if v and not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError("URL must start with http:// or https://")
        return v


class RSSFeedResponse(BaseModel):
    id: int
    name: str
    url: str
    category: str
    enabled: bool
    created_at: str
    last_crawled_at: Optional[str]
    success_count: int
    error_count: int
    error_rate: float
    last_error: Optional[str] = None

    class Config:
        from_attributes = True


class RSSFeedStatistics(BaseModel):
    total_feeds: int
    enabled_feeds: int
    disabled_feeds: int
    categories: List[str]
    total_success: int
    total_errors: int
    overall_success_rate: float
    feeds_needing_attention: int


class ApplyDiagnosisRequest(BaseModel):
    """Apply Gemini's diagnosis suggestion"""
    feed_id: int
    new_url: Optional[str] = None
    disable_feed: bool = False


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=List[RSSFeedResponse])
async def get_all_feeds(
    enabled_only: bool = Query(False, description="Show only enabled feeds"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_read),  # Uncomment for auth
):
    """
    Get all RSS feeds with their statistics.
    
    - **enabled_only**: Filter to show only enabled feeds
    - **category**: Filter by feed category
    """
    query = db.query(RSSFeed)
    
    if enabled_only:
        query = query.filter(RSSFeed.enabled == True)
    
    if category:
        query = query.filter(RSSFeed.category == category)
    
    feeds = query.order_by(RSSFeed.name).all()

    result = []
    for feed in feeds:
        # Use total_articles as success_count
        success_count = feed.total_articles or 0
        error_count = feed.error_count or 0
        total = success_count + error_count
        error_rate = error_count / total if total > 0 else 0.0

        result.append(RSSFeedResponse(
            id=feed.id,
            name=feed.name,
            url=feed.url,
            category=feed.category,
            enabled=feed.enabled,
            created_at=feed.created_at.isoformat() if feed.created_at else "",
            last_crawled_at=feed.last_fetched.isoformat() if feed.last_fetched else None,
            success_count=success_count,
            error_count=error_count,
            error_rate=error_rate,
            last_error=feed.last_error,
        ))

    return result


@router.get("/statistics", response_model=RSSFeedStatistics)
async def get_feed_statistics(
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_read),
):
    """
    Get overall RSS feed statistics.
    """
    feeds = db.query(RSSFeed).all()
    
    total = len(feeds)
    enabled = sum(1 for f in feeds if f.enabled)
    disabled = total - enabled
    
    categories = list(set(f.category for f in feeds))
    
    total_success = sum(f.success_count for f in feeds)
    total_errors = sum(f.error_count for f in feeds)
    total_attempts = total_success + total_errors
    
    overall_rate = total_success / total_attempts if total_attempts > 0 else 0.0
    
    # Feeds needing attention: high error rate or never crawled
    needing_attention = 0
    for feed in feeds:
        total_feed = feed.success_count + feed.error_count
        if total_feed > 0:
            error_rate = feed.error_count / total_feed
            if error_rate > 0.3:  # More than 30% errors
                needing_attention += 1
        elif not feed.last_crawled_at:  # Never crawled
            needing_attention += 1
    
    return RSSFeedStatistics(
        total_feeds=total,
        enabled_feeds=enabled,
        disabled_feeds=disabled,
        categories=categories,
        total_success=total_success,
        total_errors=total_errors,
        overall_success_rate=overall_rate,
        feeds_needing_attention=needing_attention,
    )


@router.get("/{feed_id}", response_model=RSSFeedResponse)
async def get_feed_by_id(
    feed_id: int,
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_read),
):
    """
    Get a specific RSS feed by ID.
    """
    feed = db.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed with ID {feed_id} not found")
    
    total = feed.success_count + feed.error_count
    success_rate = feed.success_count / total if total > 0 else 0.0
    
    return RSSFeedResponse(
        id=feed.id,
        name=feed.name,
        url=feed.url,
        category=feed.category,
        enabled=feed.enabled,
        created_at=feed.created_at.isoformat() if feed.created_at else "",
        last_crawled_at=feed.last_crawled_at.isoformat() if feed.last_crawled_at else None,
        success_count=feed.success_count,
        error_count=feed.error_count,
        success_rate=success_rate,
    )


@router.post("", response_model=RSSFeedResponse, status_code=201)
async def create_feed(
    feed: RSSFeedCreate,
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_write),
):
    """
    Create a new RSS feed.
    
    - **name**: Display name for the feed
    - **url**: RSS feed URL
    - **category**: Category (e.g., "market", "company", "tech")
    - **enabled**: Whether to include in crawling
    """
    # Check if Name already exists (name has UNIQUE constraint)
    existing_name = db.query(RSSFeed).filter(RSSFeed.name == feed.name).first()
    if existing_name:
        raise HTTPException(
            status_code=400,
            detail=f"Feed with name '{feed.name}' already exists. Please use a different name."
        )
    
    # Check if URL already exists
    existing = db.query(RSSFeed).filter(RSSFeed.url == feed.url).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Feed with this URL already exists (ID: {existing.id})"
        )
    
    new_feed = RSSFeed(
        name=feed.name,
        url=feed.url,
        category=feed.category,
        enabled=feed.enabled,
        created_at=datetime.now(),
        total_articles=0,
        error_count=0,
    )
    
    db.add(new_feed)
    db.commit()
    db.refresh(new_feed)
    
    return RSSFeedResponse(
        id=new_feed.id,
        name=new_feed.name,
        url=new_feed.url,
        category=new_feed.category,
        enabled=new_feed.enabled,
        created_at=new_feed.created_at.isoformat(),
        last_crawled_at=None,
        success_count=0,
        error_count=0,
        error_rate=0.0,
    )


@router.put("/{feed_id}", response_model=RSSFeedResponse)
async def update_feed(
    feed_id: int,
    feed_update: RSSFeedUpdate,
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_write),
):
    """
    Update an existing RSS feed.
    
    Only provided fields will be updated.
    """
    feed = db.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed with ID {feed_id} not found")
    
    # Update only provided fields
    if feed_update.name is not None:
        feed.name = feed_update.name
    
    if feed_update.url is not None:
        # Check if new URL already exists
        existing = db.query(RSSFeed).filter(
            RSSFeed.url == feed_update.url,
            RSSFeed.id != feed_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Another feed already uses this URL (ID: {existing.id})"
            )
        feed.url = feed_update.url
        # Reset counters when URL changes
        feed.success_count = 0
        feed.error_count = 0
        feed.last_crawled_at = None
    
    if feed_update.category is not None:
        feed.category = feed_update.category
    
    if feed_update.enabled is not None:
        feed.enabled = feed_update.enabled
    
    db.commit()
    db.refresh(feed)
    
    total = feed.success_count + feed.error_count
    success_rate = feed.success_count / total if total > 0 else 0.0
    
    return RSSFeedResponse(
        id=feed.id,
        name=feed.name,
        url=feed.url,
        category=feed.category,
        enabled=feed.enabled,
        created_at=feed.created_at.isoformat() if feed.created_at else "",
        last_crawled_at=feed.last_crawled_at.isoformat() if feed.last_crawled_at else None,
        success_count=feed.success_count,
        error_count=feed.error_count,
        success_rate=success_rate,
    )


@router.delete("/{feed_id}")
async def delete_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_write),
):
    """
    Delete an RSS feed.
    
    ⚠️ This will remove the feed permanently.
    """
    feed = db.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed with ID {feed_id} not found")
    
    feed_name = feed.name
    db.delete(feed)
    db.commit()
    
    return {
        "status": "deleted",
        "feed_id": feed_id,
        "feed_name": feed_name,
    }


@router.patch("/{feed_id}/toggle")
async def toggle_feed(
    feed_id: int,
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_write),
):
    """
    Toggle the enabled status of a feed.
    
    Quick way to enable/disable without full update.
    """
    feed = db.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed with ID {feed_id} not found")
    
    feed.enabled = not feed.enabled
    db.commit()
    
    return {
        "feed_id": feed_id,
        "name": feed.name,
        "enabled": feed.enabled,
        "message": f"Feed {'enabled' if feed.enabled else 'disabled'}",
    }


@router.post("/apply-diagnosis")
async def apply_gemini_diagnosis(
    request: ApplyDiagnosisRequest,
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_write),
):
    """
    Apply Gemini's diagnosis suggestion to a feed.
    
    This allows users to fix RSS feed issues directly from the UI
    based on Gemini's error diagnosis.
    
    - **feed_id**: ID of the feed to update
    - **new_url**: New URL suggested by Gemini
    - **disable_feed**: Set to True to disable the feed
    """
    feed = db.query(RSSFeed).filter(RSSFeed.id == request.feed_id).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed with ID {request.feed_id} not found")
    
    changes = []
    
    if request.new_url:
        # Check if new URL already exists
        existing = db.query(RSSFeed).filter(
            RSSFeed.url == request.new_url,
            RSSFeed.id != request.feed_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Another feed already uses this URL (ID: {existing.id})"
            )
        
        old_url = feed.url
        feed.url = request.new_url
        feed.success_count = 0
        feed.error_count = 0
        feed.last_crawled_at = None
        changes.append(f"URL updated from {old_url} to {request.new_url}")
    
    if request.disable_feed:
        feed.enabled = False
        changes.append("Feed disabled")
    
    if not changes:
        raise HTTPException(
            status_code=400,
            detail="No changes to apply. Provide new_url or set disable_feed=True"
        )
    
    db.commit()
    db.refresh(feed)
    
    return {
        "status": "diagnosis_applied",
        "feed_id": feed.id,
        "feed_name": feed.name,
        "changes": changes,
        "new_state": {
            "url": feed.url,
            "enabled": feed.enabled,
        }
    }


@router.post("/reset-counters/{feed_id}")
async def reset_feed_counters(
    feed_id: int,
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_write),
):
    """
    Reset success/error counters for a feed.
    
    Useful after fixing a feed's URL.
    """
    feed = db.query(RSSFeed).filter(RSSFeed.id == feed_id).first()
    
    if not feed:
        raise HTTPException(status_code=404, detail=f"Feed with ID {feed_id} not found")
    
    old_success = feed.total_articles or 0
    old_error = feed.error_count or 0
    
    feed.total_articles = 0
    feed.error_count = 0
    
    db.commit()
    
    return {
        "feed_id": feed_id,
        "name": feed.name,
        "reset": {
            "old_success_count": old_success,
            "old_error_count": old_error,
            "new_success_count": 0,
            "new_error_count": 0,
        }
    }


@router.get("/health/summary")
async def get_health_summary(
    db: Session = Depends(get_db),
):
    """
    Get health summary of all RSS feeds.
    """
    feeds = db.query(RSSFeed).all()

    total_feeds = len(feeds)
    active_feeds = sum(1 for f in feeds if f.enabled)
    inactive_feeds = total_feeds - active_feeds

    # Calculate healthy vs problematic feeds (error_rate > 0.3)
    healthy_feeds = 0
    problematic_feeds = 0
    feeds_needing_attention = []
    total_error_rate = 0.0

    for feed in feeds:
        success_count = feed.total_articles or 0
        error_count = feed.error_count or 0
        total = success_count + error_count
        error_rate = error_count / total if total > 0 else 0.0
        total_error_rate += error_rate

        if error_rate > 0.3:
            problematic_feeds += 1
            feeds_needing_attention.append({
                "id": feed.id,
                "name": feed.name,
                "error_rate": round(error_rate, 2),
                "last_error": feed.last_error or "No error message",
                "suggestion": "Check feed URL or contact source"
            })
        else:
            healthy_feeds += 1

    average_error_rate = total_error_rate / total_feeds if total_feeds > 0 else 0.0

    return {
        "total_feeds": total_feeds,
        "active_feeds": active_feeds,
        "inactive_feeds": inactive_feeds,
        "healthy_feeds": healthy_feeds,
        "problematic_feeds": problematic_feeds,
        "average_error_rate": round(average_error_rate, 2),
        "feeds_needing_attention": feeds_needing_attention
    }


@router.get("/categories/list")
async def get_categories(
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_read),
):
    """
    Get all unique feed categories.
    """
    feeds = db.query(RSSFeed).all()
    categories = list(set(f.category for f in feeds))
    categories.sort()

    return {
        "categories": categories,
        "count": len(categories),
    }


@router.get("/problematic")
async def get_problematic_feeds(
    error_rate_threshold: float = Query(0.3, description="Error rate threshold (0-1)"),
    db: Session = Depends(get_db),
    # api_key: str = Depends(require_read),
):
    """
    Get feeds with high error rates that need attention.
    
    - **error_rate_threshold**: Feeds with error rate above this are returned (default 0.3 = 30%)
    """
    feeds = db.query(RSSFeed).filter(RSSFeed.enabled == True).all()
    
    problematic = []
    for feed in feeds:
        total = feed.success_count + feed.error_count
        if total > 0:
            error_rate = feed.error_count / total
            if error_rate >= error_rate_threshold:
                problematic.append({
                    "id": feed.id,
                    "name": feed.name,
                    "url": feed.url,
                    "error_rate": error_rate,
                    "success_count": feed.success_count,
                    "error_count": feed.error_count,
                    "last_crawled_at": feed.last_crawled_at.isoformat() if feed.last_crawled_at else None,
                    "recommendation": "Consider updating URL or disabling feed",
                })
    
    # Sort by error rate, highest first
    problematic.sort(key=lambda x: x["error_rate"], reverse=True)
    
    return {
        "count": len(problematic),
        "threshold": error_rate_threshold,
        "feeds": problematic,
    }


@router.post("/test-url")
async def test_rss_url(request: dict):
    """
    Test if a URL is a valid RSS feed
    
    Request body: {"url": "https://example.com/rss"}
    
    Returns:
        {
            "valid": bool,
            "title": str (if valid),
            "entry_count": int (if valid),
            "error": str (if invalid)
        }
    """
    import aiohttp
    import feedparser
    
    url = request.get("url")
    if not url:
        return {"valid": False, "error": "URL is required"}
    
    try:
        # Fetch the feed
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return {
                        "valid": False,
                        "error": f"HTTP {response.status}: {response.reason}"
                    }
                
                content = await response.text()
        
        # Parse with feedparser
        feed = feedparser.parse(content)
        
        if feed.bozo:  # feedparser sets bozo=1 for malformed feeds
            return {
                "valid": False,
                "error": "Invalid RSS/Atom feed format"
            }
        
        # Valid feed
        return {
            "valid": True,
            "title": feed.feed.get("title", "Unknown"),
            "entry_count": len(feed.entries),
            "description": feed.feed.get("description", "")
        }
        
    except asyncio.TimeoutError:
        return {"valid": False, "error": "Request timeout"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


# =============================================================================
# RSS Feed Discovery (NEW - Phase 20)
# =============================================================================


# =============================================================================
# RSS Feed Discovery (NEW - Phase 20)
# =============================================================================

@router.post("/discover")
async def discover_rss_feeds(db: Session = Depends(get_db)):
    """
    Auto-discover RSS feeds from Finviz sources
    
    Scans Finviz news pages for sources and attempts to find their RSS feeds
    
    Returns:
        {
            'discovered': int,
            'added': int,
            'timestamp': str
        }
    """
    from backend.data.rss_feed_discovery import discover_and_update_rss_feeds
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        stats = await discover_and_update_rss_feeds(db=db)
        
        return {
            "success": True,
            "discovered": stats.get('discovered', 0),
            "added": stats.get('added', 0),
            "timestamp": stats.get('timestamp')
        }
    except Exception as e:
        logger.error(f"RSS discovery error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/discover/available")
async def get_available_feeds():
    """
    Get list of known RSS feed mappings
    
    Returns pre-configured feed sources that can be added
    """
    from backend.data.rss_feed_discovery import RSS_FEED_MAPPINGS
    
    feeds = []
    for source_name, rss_url in RSS_FEED_MAPPINGS.items():
        # Exclude domain-only entries (they have dots and are short)
        if '.' not in source_name or len(source_name) > 30:
            feeds.append({
                'source_name': source_name,
                'rss_url': rss_url,
                'category': 'global'
            })
    
    return {
        "count": len(feeds),
        "feeds": feeds
    }
