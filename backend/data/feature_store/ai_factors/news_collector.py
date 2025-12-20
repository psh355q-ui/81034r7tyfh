"""
News Collector for Non-Standard Risk Factor.

Fetches news from multiple sources:
- NewsAPI.org (100 free requests/day)
- RSS feeds (Bloomberg, Reuters - unlimited)
- Yahoo Finance news (via yfinance)

No AI used - pure rule-based keyword matching.
Cost: $0
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio

import aiohttp
import yfinance as yf

logger = logging.getLogger(__name__)


class NewsArticle:
    """Simple news article container."""

    def __init__(
        self,
        title: str,
        content: Optional[str],
        published_at: datetime,
        source: str,
        url: str,
    ):
        self.title = title
        self.content = content or ""
        self.published_at = published_at
        self.source = source
        self.url = url

    def get_full_text(self) -> str:
        """Get combined title + content."""
        return f"{self.title} {self.content}"

    def __repr__(self) -> str:
        return f"NewsArticle({self.source}: {self.title[:50]}...)"


class NewsCollector:
    """
    Multi-source news collector.

    Features:
    - Yahoo Finance (free, unlimited)
    - NewsAPI.org (100/day free tier)
    - RSS feeds (unlimited)
    """

    def __init__(self, newsapi_key: Optional[str] = None):
        """
        Initialize news collector.

        Args:
            newsapi_key: Optional NewsAPI.org API key
        """
        self.newsapi_key = newsapi_key
        self.newsapi_base_url = "https://newsapi.org/v2"

        # Rate limiting
        self.newsapi_calls_today = 0
        self.newsapi_limit = 100  # Free tier limit

    async def fetch_news(
        self,
        ticker: str,
        days: int = 30,
        sources: Optional[List[str]] = None,
    ) -> List[NewsArticle]:
        """
        Fetch news for a ticker from multiple sources.

        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back
            sources: Optional list of sources to use (default: all available)

        Returns:
            List of NewsArticle objects
        """
        all_news = []

        # Default: try all sources
        if sources is None:
            sources = ["yahoo", "newsapi", "rss"]

        # 1. Yahoo Finance (always free, most reliable)
        if "yahoo" in sources:
            yahoo_news = await self._fetch_yahoo_news(ticker, days)
            all_news.extend(yahoo_news)
            logger.info(f"Fetched {len(yahoo_news)} articles from Yahoo Finance")

        # 2. NewsAPI.org (rate limited)
        if "newsapi" in sources and self.newsapi_key:
            if self.newsapi_calls_today < self.newsapi_limit:
                newsapi_news = await self._fetch_newsapi(ticker, days)
                all_news.extend(newsapi_news)
                logger.info(f"Fetched {len(newsapi_news)} articles from NewsAPI")
            else:
                logger.warning("NewsAPI rate limit reached today")

        # 3. RSS feeds (free, unlimited)
        if "rss" in sources:
            rss_news = await self._fetch_rss_feeds(ticker, days)
            all_news.extend(rss_news)
            logger.info(f"Fetched {len(rss_news)} articles from RSS feeds")

        # Remove duplicates by URL
        seen_urls = set()
        unique_news = []
        for article in all_news:
            if article.url not in seen_urls:
                unique_news.append(article)
                seen_urls.add(article.url)

        logger.info(
            f"Total unique articles for {ticker}: {len(unique_news)} "
            f"(from {len(all_news)} total)"
        )

        return unique_news

    async def _fetch_yahoo_news(
        self, ticker: str, days: int
    ) -> List[NewsArticle]:
        """Fetch news from Yahoo Finance (via yfinance)."""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news  # List of news items

            articles = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for item in news:
                # Yahoo Finance news format
                published_timestamp = item.get("providerPublishTime", 0)
                published_at = datetime.fromtimestamp(published_timestamp)

                if published_at < cutoff_date:
                    continue

                article = NewsArticle(
                    title=item.get("title", ""),
                    content=None,  # Yahoo doesn't provide full content
                    published_at=published_at,
                    source="Yahoo Finance",
                    url=item.get("link", ""),
                )
                articles.append(article)

            return articles

        except Exception as e:
            logger.error(f"Error fetching Yahoo news for {ticker}: {e}")
            return []

    async def _fetch_newsapi(
        self, ticker: str, days: int
    ) -> List[NewsArticle]:
        """Fetch news from NewsAPI.org."""
        if not self.newsapi_key:
            return []

        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)

            # NewsAPI endpoint
            url = f"{self.newsapi_base_url}/everything"
            params = {
                "q": ticker,  # Search query
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d"),
                "language": "en",
                "sortBy": "publishedAt",
                "apiKey": self.newsapi_key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(
                            f"NewsAPI error: {response.status} - {await response.text()}"
                        )
                        return []

                    data = await response.json()
                    articles = []

                    for item in data.get("articles", []):
                        published_str = item.get("publishedAt")
                        published_at = datetime.fromisoformat(
                            published_str.replace("Z", "+00:00")
                        )

                        article = NewsArticle(
                            title=item.get("title", ""),
                            content=item.get("description", ""),
                            published_at=published_at,
                            source=item.get("source", {}).get("name", "NewsAPI"),
                            url=item.get("url", ""),
                        )
                        articles.append(article)

                    # Update rate limit counter
                    self.newsapi_calls_today += 1

                    return articles

        except Exception as e:
            logger.error(f"Error fetching NewsAPI for {ticker}: {e}")
            return []

    async def _fetch_rss_feeds(
        self, ticker: str, days: int
    ) -> List[NewsArticle]:
        """
        Fetch news from RSS feeds.

        TODO: Implement RSS parsing (feedparser library).
        For now, return empty list.
        """
        # This would require feedparser library
        # and RSS feed URLs for major financial news sources
        logger.debug(f"RSS feed fetching not yet implemented for {ticker}")
        return []

    def reset_daily_limits(self) -> None:
        """Reset daily rate limits (call this at midnight)."""
        self.newsapi_calls_today = 0
        logger.info("NewsAPI daily limits reset")