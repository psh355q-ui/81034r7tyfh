import logging

logger = logging.getLogger(__name__)


# =============================================================================
# RSS Feed Discovery (NEW)
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
            'feeds': List[Dict]
        }
    """
    from backend.data.rss_feed_discovery import discover_and_update_rss_feeds
    
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
        if '.' not in source_name or len(source_name) > 30:  # Exclude domain-only entries
            feeds.append({
                'source_name': source_name,
                'rss_url': rss_url,
                'category': 'global'
            })
    
    return {
        "count": len(feeds),
        "feeds": feeds
    }
