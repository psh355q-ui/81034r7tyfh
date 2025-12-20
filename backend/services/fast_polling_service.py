"""
Fast Polling Service for News & Economic Indicators (3-minute intervals).

Based on Gemini's Hybrid Latency Strategy:
- News/Economic Indicators: 1-3 minute polling (free, fast response)
- Market Prices: 15-minute delay (stable, Yahoo Finance)

This service focuses on "eyes" (news/indicators) while keeping "hands" (trading)
on 15-minute data for stability.

Cost: $0/month (Google News RSS + free APIs)
Risk: API blocking if too aggressive (mitigated with multiple sources)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import feedparser
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FastNewsItem:
    """Lightweight news item for 3-minute polling."""
    title: str
    source: str
    published_at: datetime
    url: str
    sentiment: Optional[float] = None  # -1 to 1
    urgency: str = "NORMAL"  # LOW, NORMAL, HIGH, CRITICAL


@dataclass
class EconomicIndicatorUpdate:
    """Real-time economic indicator update."""
    indicator: str  # "CPI", "NFP", "FOMC", etc.
    value: Optional[float]
    published_at: datetime
    impact: str  # "LOW", "MEDIUM", "HIGH"
    url: str


class FastPollingService:
    """
    3-minute polling service for news and economic indicators.

    Features:
    - Google News RSS (almost real-time, free)
    - Yahoo Finance RSS (free, fast)
    - Economic calendar scraping (Investing.com)
    - Sentiment analysis (rule-based, no AI cost)
    - Automatic alerting for critical events

    Usage:
        service = FastPollingService()
        await service.start()  # Runs every 3 minutes in background
    """

    def __init__(self, polling_interval: int = 180):
        """
        Initialize fast polling service.

        Args:
            polling_interval: Polling interval in seconds (default: 180 = 3 minutes)
        """
        self.polling_interval = polling_interval
        self.running = False
        self.last_poll_time: Optional[datetime] = None

        # RSS feeds (free, fast, reliable)
        self.rss_feeds = {
            "google_finance": "https://news.google.com/rss/search?q=stock+market&hl=en-US&gl=US&ceid=US:en",
            "yahoo_finance": "https://finance.yahoo.com/rss/",
            "reuters_business": "https://www.reuterstv.com/business/feed/",
            "bloomberg": "https://www.bloomberg.com/feed/podcast/etf-report.xml",
        }

        # Economic indicators to monitor
        self.economic_indicators = [
            "CPI",      # Consumer Price Index
            "NFP",      # Non-Farm Payrolls
            "FOMC",     # Federal Reserve Meeting
            "GDP",      # GDP Report
            "JOLTS",    # Job Openings
            "PPI",      # Producer Price Index
        ]

        # Cache to avoid duplicate alerts
        self.seen_news_urls: set = set()
        self.seen_indicators: Dict[str, datetime] = {}

    async def start(self):
        """Start the polling service (runs in background)."""
        self.running = True
        logger.info(f"Starting fast polling service (every {self.polling_interval}s)")

        while self.running:
            try:
                await self._poll_cycle()
                await asyncio.sleep(self.polling_interval)
            except Exception as e:
                logger.error(f"Error in polling cycle: {e}", exc_info=True)
                await asyncio.sleep(self.polling_interval)

    def stop(self):
        """Stop the polling service."""
        self.running = False
        logger.info("Stopping fast polling service")

    async def _poll_cycle(self):
        """Execute one polling cycle (news + indicators)."""
        poll_start = datetime.now()
        logger.info(f"Starting poll cycle at {poll_start}")

        # Parallel fetching for speed
        news_task = asyncio.create_task(self._fetch_news())
        indicators_task = asyncio.create_task(self._fetch_economic_indicators())

        news_items, indicator_updates = await asyncio.gather(
            news_task, indicators_task, return_exceptions=True
        )

        # Process news
        if isinstance(news_items, list):
            critical_news = [n for n in news_items if n.urgency in ("HIGH", "CRITICAL")]
            if critical_news:
                await self._alert_critical_news(critical_news)
            
            # Phase 15 Tier 3: Extract CEO quotes
            await self._extract_and_alert_ceo_quotes(news_items)
            
            logger.info(f"Fetched {len(news_items)} news items ({len(critical_news)} critical)")
        else:
            logger.error(f"News fetch failed: {news_items}")

        # Process indicators
        if isinstance(indicator_updates, list):
            high_impact = [i for i in indicator_updates if i.impact == "HIGH"]
            if high_impact:
                await self._alert_economic_events(high_impact)
            logger.info(f"Fetched {len(indicator_updates)} indicators ({len(high_impact)} high impact)")
        else:
            logger.error(f"Indicator fetch failed: {indicator_updates}")

        poll_duration = (datetime.now() - poll_start).total_seconds()
        logger.info(f"Poll cycle completed in {poll_duration:.2f}s")
        self.last_poll_time = poll_start

    async def _fetch_news(self) -> List[FastNewsItem]:
        """Fetch news from RSS feeds (fast, free)."""
        all_news = []

        async with aiohttp.ClientSession() as session:
            for source_name, feed_url in self.rss_feeds.items():
                try:
                    # Fetch RSS feed
                    async with session.get(feed_url, timeout=10) as response:
                        if response.status != 200:
                            logger.warning(f"Failed to fetch {source_name}: {response.status}")
                            continue

                        content = await response.text()
                        feed = feedparser.parse(content)

                        # Parse entries
                        for entry in feed.entries[:10]:  # Top 10 most recent
                            # Skip if already seen
                            url = entry.get("link", "")
                            if url in self.seen_news_urls:
                                continue

                            title = entry.get("title", "")
                            published = entry.get("published_parsed")
                            if published:
                                published_at = datetime(*published[:6])
                            else:
                                published_at = datetime.now()

                            # Rule-based sentiment & urgency
                            sentiment, urgency = self._analyze_news_urgency(title)

                            news_item = FastNewsItem(
                                title=title,
                                source=source_name,
                                published_at=published_at,
                                url=url,
                                sentiment=sentiment,
                                urgency=urgency,
                            )

                            all_news.append(news_item)
                            self.seen_news_urls.add(url)

                except Exception as e:
                    logger.error(f"Error fetching {source_name}: {e}")

        return all_news

    async def _fetch_economic_indicators(self) -> List[EconomicIndicatorUpdate]:
        """Fetch economic indicator releases (scraping or API)."""
        updates = []

        # Note: This is a simplified version. In production, you would:
        # 1. Scrape Investing.com economic calendar
        # 2. Parse release times and values
        # 3. Return only NEW releases since last poll

        # For now, return empty list (placeholder for implementation)
        # TODO: Implement Investing.com calendar scraping

        return updates

    def _analyze_news_urgency(self, title: str) -> tuple[float, str]:
        """
        Rule-based analysis of news urgency and sentiment.

        Args:
            title: News headline

        Returns:
            (sentiment, urgency) where sentiment is -1 to 1, urgency is LOW/NORMAL/HIGH/CRITICAL
        """
        title_lower = title.lower()

        # CRITICAL keywords (immediate market impact)
        critical_keywords = [
            "crash", "plunge", "emergency", "halt", "suspend",
            "bankruptcy", "default", "investigation", "fraud",
            "war", "attack", "pandemic", "lockdown"
        ]

        # HIGH urgency keywords
        high_keywords = [
            "fed", "rate hike", "rate cut", "inflation",
            "earnings", "guidance", "warning", "downgrade",
            "upgrade", "acquisition", "merger", "layoff"
        ]

        # Negative sentiment keywords
        negative_keywords = [
            "crash", "plunge", "fall", "drop", "decline",
            "loss", "miss", "disappoint", "weak", "concern",
            "risk", "fear", "uncertainty", "volatility"
        ]

        # Positive sentiment keywords
        positive_keywords = [
            "surge", "rally", "gain", "rise", "beat",
            "strong", "growth", "upgrade", "optimism",
            "record", "high", "bullish", "confidence"
        ]

        # Determine urgency
        urgency = "NORMAL"
        if any(keyword in title_lower for keyword in critical_keywords):
            urgency = "CRITICAL"
        elif any(keyword in title_lower for keyword in high_keywords):
            urgency = "HIGH"

        # Determine sentiment (-1 to 1)
        sentiment = 0.0
        neg_count = sum(1 for kw in negative_keywords if kw in title_lower)
        pos_count = sum(1 for kw in positive_keywords if kw in title_lower)

def get_fast_polling_service() -> FastPollingService:
    """Get or create the fast polling service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = FastPollingService(polling_interval=180)  # 3 minutes
    return _service_instance


async def start_fast_polling():
    """Convenience function to start the fast polling service."""
    service = get_fast_polling_service()
    await service.start()


if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_fast_polling())
