"""
News Article Embedding Pipeline (Phase 13).

Incrementally embeds news articles for RAG retrieval.

Features:
1. RSS feed + NewsAPI integration
2. Real-time embedding (3-minute polling)
3. Deduplication (URL hash)
4. Multi-source aggregation

Workflow:
1. Poll RSS feeds (Google News, Yahoo Finance, Reuters)
2. Fetch full article content
3. Generate embeddings
4. Store with metadata (source, sentiment, urgency)

Cost:
- News article (~500 tokens): $0.00001
- 100 articles/day × 30 days = 3,000 articles/month
- Monthly cost: ~$0.03
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import aiohttp
import feedparser
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.embedding_engine import EmbeddingEngine
from backend.core.models.embedding_models import (
    DocumentEmbedding,
    EmbeddingCache,
)

logger = logging.getLogger(__name__)


class NewsEmbeddingPipeline:
    """
    News article embedding pipeline with real-time updates.

    Usage:
        pipeline = NewsEmbeddingPipeline(db_session)

        # Embed news for a ticker
        stats = await pipeline.embed_ticker_news("AAPL", hours=24)

        # Embed news from RSS feeds
        stats = await pipeline.embed_from_rss(
            feeds=["google_finance", "yahoo_finance"],
            tickers=["AAPL", "MSFT"]
        )
    """

    # RSS Feed URLs
    RSS_FEEDS = {
        "google_finance": "https://news.google.com/rss/search?q={ticker}+stock",
        "yahoo_finance": "https://finance.yahoo.com/rss/headline?s={ticker}",
        "reuters_business": "https://www.reuterstv.com/business/feed/",
        "cnbc_top": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    }

    def __init__(self, db_session: AsyncSession, openai_api_key: Optional[str] = None):
        """
        Initialize news embedding pipeline.

        Args:
            db_session: SQLAlchemy async session
            openai_api_key: OpenAI API key
        """
        self.db = db_session
        self.embedding_engine = EmbeddingEngine(db_session, openai_api_key)

        logger.info("NewsEmbeddingPipeline initialized")

    def _compute_url_hash(self, url: str) -> str:
        """
        Compute hash of URL for deduplication.

        Args:
            url: Article URL

        Returns:
            SHA-256 hash
        """
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    async def _check_article_exists(self, url_hash: str) -> bool:
        """
        Check if article has already been embedded.

        Args:
            url_hash: URL hash

        Returns:
            True if exists, False otherwise
        """
        result = await self.db.execute(
            select(EmbeddingCache).where(EmbeddingCache.content_hash == url_hash)
        )
        return result.scalar_one_or_none() is not None

    async def _fetch_rss_articles(
        self, feed_url: str, max_articles: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from RSS feed.

        Args:
            feed_url: RSS feed URL
            max_articles: Max articles to fetch

        Returns:
            List of article dicts
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    content = await response.text()

            # Parse RSS
            feed = feedparser.parse(content)

            articles = []

            for entry in feed.entries[:max_articles]:
                article = {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published": entry.get("published_parsed"),
                    "summary": entry.get("summary", ""),
                    "source": feed.feed.get("title", "Unknown"),
                }

                # Convert published time
                if article["published"]:
                    article["published_date"] = datetime(
                        *article["published"][:6]
                    )
                else:
                    article["published_date"] = datetime.now()

                articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from {feed_url}")

            return articles

        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}", exc_info=True)
            return []

    def _extract_ticker_from_text(self, text: str, tickers: List[str]) -> Optional[str]:
        """
        Extract ticker from article text.

        Args:
            text: Article text
            tickers: List of candidate tickers

        Returns:
            Ticker if found, None otherwise
        """
        text_upper = text.upper()

        for ticker in tickers:
            if ticker.upper() in text_upper:
                return ticker

        return None

    async def embed_ticker_news(
        self,
        ticker: str,
        hours: int = 24,
        sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Embed news articles for a ticker.

        Args:
            ticker: Stock ticker
            hours: Look back hours
            sources: RSS feed sources (default: all)

        Returns:
            Statistics dict
        """
        if not sources:
            sources = list(self.RSS_FEEDS.keys())

        stats = {
            "ticker": ticker,
            "articles_fetched": 0,
            "articles_embedded": 0,
            "duplicates": 0,
            "total_cost_usd": 0.0,
        }

        # 1. Fetch articles from RSS feeds
        all_articles = []

        for source in sources:
            if source not in self.RSS_FEEDS:
                continue

            feed_url = self.RSS_FEEDS[source].format(ticker=ticker)
            articles = await self._fetch_rss_articles(feed_url)

            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_articles = [
                a for a in articles if a["published_date"] >= cutoff_time
            ]

            all_articles.extend(recent_articles)

        stats["articles_fetched"] = len(all_articles)

        logger.info(
            f"{ticker}: Fetched {len(all_articles)} articles from {len(sources)} sources"
        )

        # 2. Embed each article
        for article in all_articles:
            try:
                # Check for duplicates
                url_hash = self._compute_url_hash(article["url"])

                if await self._check_article_exists(url_hash):
                    stats["duplicates"] += 1
                    continue

                # Prepare content
                content = f"{article['title']}\n\n{article['summary']}"

                # Generate embedding
                embedding_ids = await self.embedding_engine.embed_document(
                    document_type="news_article",
                    document_id=hash(article["url"])
                    % 2147483647,  # Convert to int32 range
                    ticker=ticker,
                    title=article["title"],
                    content=content,
                    source_date=article["published_date"],
                    metadata={
                        "url": article["url"],
                        "source": article["source"],
                        "summary": article["summary"],
                    },
                )

                # Save URL hash to cache
                for emb_id in embedding_ids:
                    await self.embedding_engine._save_cache(url_hash, emb_id)

                # Update stats
                stats["articles_embedded"] += 1

                # Get cost
                result = await self.db.execute(
                    select(DocumentEmbedding).where(
                        DocumentEmbedding.id.in_(embedding_ids)
                    )
                )
                embeddings = result.scalars().all()

                for emb in embeddings:
                    stats["total_cost_usd"] += emb.embedding_cost_usd

                logger.info(
                    f"{ticker}: Embedded news article: {article['title'][:50]}..."
                )

            except Exception as e:
                logger.error(
                    f"Error embedding article {article['url']}: {e}", exc_info=True
                )
                continue

        logger.info(
            f"{ticker}: News embedding complete - "
            f"{stats['articles_embedded']} embedded, "
            f"{stats['duplicates']} duplicates, "
            f"${stats['total_cost_usd']:.5f}"
        )

        return stats

    async def embed_batch_tickers_news(
        self, tickers: List[str], hours: int = 24
    ) -> Dict[str, Any]:
        """
        Embed news for multiple tickers.

        Args:
            tickers: List of stock tickers
            hours: Look back hours

        Returns:
            Aggregate statistics
        """
        total_stats = {
            "tickers_processed": 0,
            "total_articles_fetched": 0,
            "total_articles_embedded": 0,
            "total_duplicates": 0,
            "total_cost_usd": 0.0,
            "by_ticker": {},
        }

        for ticker in tickers:
            try:
                stats = await self.embed_ticker_news(ticker=ticker, hours=hours)

                # Aggregate
                total_stats["tickers_processed"] += 1
                total_stats["total_articles_fetched"] += stats["articles_fetched"]
                total_stats["total_articles_embedded"] += stats["articles_embedded"]
                total_stats["total_duplicates"] += stats["duplicates"]
                total_stats["total_cost_usd"] += stats["total_cost_usd"]
                total_stats["by_ticker"][ticker] = stats

                logger.info(
                    f"News batch progress: {total_stats['tickers_processed']}/{len(tickers)} tickers"
                )

            except Exception as e:
                logger.error(f"Error processing ticker {ticker}: {e}", exc_info=True)
                continue

        logger.info(
            f"News batch complete: "
            f"{total_stats['tickers_processed']} tickers, "
            f"{total_stats['total_articles_embedded']} articles, "
            f"${total_stats['total_cost_usd']:.5f}"
        )

        return total_stats

    async def embed_from_general_feeds(
        self, feeds: List[str], tickers: List[str], hours: int = 24
    ) -> Dict[str, Any]:
        """
        Embed articles from general news feeds (CNBC, Reuters, etc.).

        Filters articles by ticker mentions.

        Args:
            feeds: List of feed names
            tickers: List of tickers to filter for
            hours: Look back hours

        Returns:
            Statistics dict
        """
        stats = {
            "feeds_processed": 0,
            "articles_fetched": 0,
            "articles_embedded": 0,
            "total_cost_usd": 0.0,
        }

        for feed in feeds:
            if feed not in self.RSS_FEEDS:
                continue

            # Fetch articles
            feed_url = self.RSS_FEEDS[feed]

            # If feed URL has {ticker} placeholder, skip
            if "{ticker}" in feed_url:
                continue

            articles = await self._fetch_rss_articles(feed_url)

            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_articles = [
                a for a in articles if a["published_date"] >= cutoff_time
            ]

            stats["articles_fetched"] += len(recent_articles)

            # Filter by ticker mentions
            for article in recent_articles:
                # Extract ticker from title/summary
                text = f"{article['title']} {article['summary']}"
                ticker = self._extract_ticker_from_text(text, tickers)

                if not ticker:
                    continue

                # Embed article
                try:
                    url_hash = self._compute_url_hash(article["url"])

                    if await self._check_article_exists(url_hash):
                        continue

                    content = f"{article['title']}\n\n{article['summary']}"

                    embedding_ids = await self.embedding_engine.embed_document(
                        document_type="news_article",
                        document_id=hash(article["url"]) % 2147483647,
                        ticker=ticker,
                        title=article["title"],
                        content=content,
                        source_date=article["published_date"],
                        metadata={
                            "url": article["url"],
                            "source": article["source"],
                            "feed": feed,
                        },
                    )

                    for emb_id in embedding_ids:
                        await self.embedding_engine._save_cache(url_hash, emb_id)

                    stats["articles_embedded"] += 1

                    # Get cost
                    result = await self.db.execute(
                        select(DocumentEmbedding).where(
                            DocumentEmbedding.id.in_(embedding_ids)
                        )
                    )
                    embeddings = result.scalars().all()

                    for emb in embeddings:
                        stats["total_cost_usd"] += emb.embedding_cost_usd

                except Exception as e:
                    logger.error(
                        f"Error embedding article {article['url']}: {e}", exc_info=True
                    )
                    continue

            stats["feeds_processed"] += 1

        logger.info(
            f"General feed embedding complete: "
            f"{stats['feeds_processed']} feeds, "
            f"{stats['articles_embedded']} articles, "
            f"${stats['total_cost_usd']:.5f}"
        )

        return stats


# Example usage
if __name__ == "__main__":
    import asyncio
    from backend.core.database import get_db

    async def demo():
        async with get_db() as db:
            pipeline = NewsEmbeddingPipeline(db)

            # Embed AAPL news from last 24 hours
            stats = await pipeline.embed_ticker_news("AAPL", hours=24)
            print(f"AAPL news stats: {stats}")

            # Batch embed multiple tickers
            tickers = ["AAPL", "MSFT", "GOOGL"]
            batch_stats = await pipeline.embed_batch_tickers_news(tickers, hours=24)
            print(f"Batch stats: {batch_stats}")

    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo())
