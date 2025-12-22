"""
Real-time News Service - Unified Pipeline for Live News Collection

Integrates multiple real-time sources with NLP processing and database storage:
- Finviz Scout (ultra-fast headlines)
- SEC EDGAR 8-K (corporate events)
- (Future) Telegram breaking news

Pipeline:
1. Collect from sources
2. Convert to unified NewsArticle format
3. NLP processing (sentiment + embedding)
4. Database storage with deduplication
5. RAG indexing ready

Author: AI Trading System Team
Date: 2025-12-22
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from backend.data.crawlers.finviz_scout import FinvizScout, FinvizNewsItem
    from backend.data.crawlers.sec_edgar_monitor import SECEdgarMonitor, SECFiling
    from backend.data.crawlers.multi_source_crawler import NewsArticle
    from backend.data.processors.news_processor import NewsProcessor, ProcessedNews
    from backend.database.repository import get_db_session, NewsRepository
    from backend.config.settings import settings
except ImportError as e:
    print(f"Import error: {e}")
    # Mock for standalone testing
    class MockSettings:
        pass
    settings = MockSettings()


logger = logging.getLogger(__name__)


class RealtimeNewsService:
    """
    Real-time news collection service with full NLP pipeline.

    Features:
    - Multi-source collection (Finviz, SEC, Telegram)
    - Automatic sentiment analysis
    - Embedding generation for RAG
    - Database storage with deduplication
    - Impact scoring and tagging
    """

    def __init__(self):
        """Initialize service."""
        self.logger = logging.getLogger(__name__)
        self.settings = settings

        # Initialize collectors
        self.finviz_scout = FinvizScout(min_impact_score=50)
        self.sec_monitor = SECEdgarMonitor()

        # Initialize NLP processor
        self.news_processor = NewsProcessor()

        # Stats tracking
        self.stats = {
            'finviz_collected': 0,
            'sec_collected': 0,
            'processed': 0,
            'saved': 0,
            'errors': 0
        }

    def finviz_to_news_article(self, item: FinvizNewsItem) -> NewsArticle:
        """
        Convert Finviz item to NewsArticle format.

        Args:
            item: FinvizNewsItem from Finviz Scout

        Returns:
            NewsArticle for processing pipeline
        """
        # Generate content from title (Finviz doesn't provide full content)
        content = f"{item.title}\n\nSource: {item.source}"
        if item.tickers:
            content += f"\nTickers: {', '.join(item.tickers)}"

        # Generate tags based on category
        tags = []
        if item.category:
            tags.append(item.category.lower())
        if item.impact_score:
            if item.impact_score >= 80:
                tags.append('high-impact')
            elif item.impact_score >= 60:
                tags.append('medium-impact')
        if item.source:
            tags.append(f'source:{item.source.lower().replace(" ", "-")}')

        return NewsArticle(
            title=item.title,
            content=content,
            url=item.url,
            source=item.source,
            source_category='finviz',
            published_at=item.published_at,
            tickers=item.tickers,
            tags=tags,
            author=None,
            metadata={
                'impact_score': item.impact_score,
                'category': item.category,
                'raw_html': item.raw_html
            }
        )

    def sec_filing_to_news_article(self, filing: SECFiling) -> NewsArticle:
        """
        Convert SEC 8-K filing to NewsArticle format.

        Args:
            filing: SECFiling from SEC EDGAR Monitor

        Returns:
            NewsArticle for processing pipeline
        """
        # Build content from filing data
        content = f"""SEC Form {filing.form_type} Filing

Company: {filing.company_name}
CIK: {filing.cik}
Filing Date: {filing.filing_date.strftime('%Y-%m-%d %H:%M:%S')}

Items Disclosed:
{chr(10).join([f'- Item {item}' for item in filing.items])}

Description:
{filing.description}

Impact Category: {filing.impact_category}
Impact Score: {filing.impact_score}

Full Filing: {filing.url}
"""

        # Generate tags
        tags = [
            'sec-filing',
            f'form:{filing.form_type.lower()}',
            filing.impact_category.lower()
        ]

        # Add item-specific tags
        for item in filing.items:
            tags.append(f'item:{item}')

        # Impact level tags
        if filing.impact_score:
            if filing.impact_score >= 80:
                tags.append('high-impact')
            elif filing.impact_score >= 60:
                tags.append('medium-impact')
            else:
                tags.append('low-impact')

        # Add ticker if available
        tickers = [filing.ticker] if filing.ticker else []

        return NewsArticle(
            title=f"{filing.company_name} - SEC Form {filing.form_type} ({filing.impact_category})",
            content=content,
            url=filing.url,
            source='SEC EDGAR',
            source_category='sec',
            published_at=filing.filing_date,
            tickers=tickers,
            tags=tags,
            author='SEC',
            metadata={
                'cik': filing.cik,
                'form_type': filing.form_type,
                'items': filing.items,
                'accession_number': filing.accession_number,
                'impact_score': filing.impact_score,
                'impact_category': filing.impact_category
            }
        )

    async def collect_from_finviz(self, score: bool = True, min_score: float = 50) -> List[NewsArticle]:
        """
        Collect news from Finviz and convert to NewsArticle format.

        Args:
            score: Whether to score headlines with Gemini
            min_score: Minimum impact score

        Returns:
            List of NewsArticle objects
        """
        try:
            self.logger.info("📰 Collecting from Finviz Scout...")

            # Collect from Finviz
            finviz_items = self.finviz_scout.collect(score=score, min_score=min_score)

            self.stats['finviz_collected'] += len(finviz_items)

            # Convert to NewsArticle format
            articles = [self.finviz_to_news_article(item) for item in finviz_items]

            self.logger.info(f"✅ Collected {len(articles)} articles from Finviz")

            return articles

        except Exception as e:
            self.logger.error(f"❌ Finviz collection failed: {e}")
            self.stats['errors'] += 1
            return []

    async def collect_from_sec(self, min_score: float = 60) -> List[NewsArticle]:
        """
        Collect filings from SEC EDGAR and convert to NewsArticle format.

        Args:
            min_score: Minimum impact score

        Returns:
            List of NewsArticle objects
        """
        try:
            self.logger.info("📰 Collecting from SEC EDGAR...")

            # Collect from SEC
            async with self.sec_monitor:
                sec_filings = await self.sec_monitor.collect(min_score=min_score)

            self.stats['sec_collected'] += len(sec_filings)

            # Convert to NewsArticle format
            articles = [self.sec_filing_to_news_article(filing) for filing in sec_filings]

            self.logger.info(f"✅ Collected {len(articles)} filings from SEC")

            return articles

        except Exception as e:
            self.logger.error(f"❌ SEC collection failed: {e}")
            self.stats['errors'] += 1
            return []

    async def collect_all_sources(
        self,
        finviz_enabled: bool = True,
        sec_enabled: bool = True,
        finviz_min_score: float = 50,
        sec_min_score: float = 60
    ) -> List[NewsArticle]:
        """
        Collect from all enabled sources in parallel.

        Args:
            finviz_enabled: Enable Finviz Scout
            sec_enabled: Enable SEC EDGAR
            finviz_min_score: Min score for Finviz
            sec_min_score: Min score for SEC

        Returns:
            Combined list of NewsArticle objects
        """
        self.logger.info("🚀 Starting multi-source collection...")

        tasks = []

        if finviz_enabled:
            tasks.append(self.collect_from_finviz(score=True, min_score=finviz_min_score))

        if sec_enabled:
            tasks.append(self.collect_from_sec(min_score=sec_min_score))

        # Collect in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        all_articles = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Collection error: {result}")
                self.stats['errors'] += 1
            elif isinstance(result, list):
                all_articles.extend(result)

        self.logger.info(f"✅ Collected {len(all_articles)} total articles from all sources")

        return all_articles

    async def process_and_save(self, articles: List[NewsArticle]) -> int:
        """
        Process articles with NLP and save to database.

        Pipeline:
        1. NLP processing (sentiment + embedding)
        2. Database storage with deduplication
        3. RAG indexing ready

        Args:
            articles: List of NewsArticle objects

        Returns:
            Number of articles saved
        """
        if not articles:
            self.logger.warning("⚠️ No articles to process")
            return 0

        try:
            self.logger.info(f"🔄 Processing {len(articles)} articles...")

            # 1. NLP Processing
            processed = await self.news_processor.process_batch(articles, batch_size=10)

            self.stats['processed'] += len(processed)

            self.logger.info(f"✅ Processed {len(processed)} articles with NLP")

            # 2. Database Storage
            saved_count = 0

            async with get_db_session() as session:
                news_repo = NewsRepository(session)

                for proc_news in processed:
                    try:
                        # Convert to DB dict
                        article_dict = proc_news.to_db_dict()

                        # Save to database
                        news_repo.save_processed_article(article_dict)

                        saved_count += 1

                    except Exception as e:
                        self.logger.error(f"❌ Failed to save article: {e}")
                        self.stats['errors'] += 1
                        continue

            self.stats['saved'] += saved_count

            self.logger.info(f"✅ Saved {saved_count} articles to database")

            return saved_count

        except Exception as e:
            self.logger.error(f"❌ Process and save failed: {e}")
            self.stats['errors'] += 1
            return 0

    async def run_collection_cycle(
        self,
        finviz_enabled: bool = True,
        sec_enabled: bool = True,
        finviz_min_score: float = 50,
        sec_min_score: float = 60
    ) -> Dict:
        """
        Run a complete collection cycle.

        1. Collect from all sources
        2. Process with NLP
        3. Save to database
        4. Return stats

        Args:
            finviz_enabled: Enable Finviz
            sec_enabled: Enable SEC
            finviz_min_score: Min score for Finviz
            sec_min_score: Min score for SEC

        Returns:
            Stats dict
        """
        start_time = datetime.now()

        self.logger.info("🚀 Starting real-time news collection cycle...")

        # 1. Collect from sources
        articles = await self.collect_all_sources(
            finviz_enabled=finviz_enabled,
            sec_enabled=sec_enabled,
            finviz_min_score=finviz_min_score,
            sec_min_score=sec_min_score
        )

        # 2. Process and save
        saved_count = await self.process_and_save(articles)

        # Calculate stats
        duration = (datetime.now() - start_time).total_seconds()

        stats = {
            **self.stats,
            'cycle_duration_seconds': duration,
            'articles_per_second': saved_count / duration if duration > 0 else 0
        }

        self.logger.info(f"✅ Collection cycle complete: {saved_count} articles saved in {duration:.1f}s")

        return stats

    async def run_continuous_loop(
        self,
        interval: int = 60,
        duration: int = 3600,
        **kwargs
    ):
        """
        Run continuous collection loop.

        Args:
            interval: Seconds between cycles (default: 60s)
            duration: Total duration in seconds (default: 1 hour)
            **kwargs: Passed to run_collection_cycle
        """
        start_time = datetime.now()
        iteration = 0

        self.logger.info(f"🔄 Starting continuous loop: {interval}s interval, {duration}s duration")

        try:
            while (datetime.now() - start_time).total_seconds() < duration:
                iteration += 1
                self.logger.info(f"\n{'='*60}\n🔄 Iteration {iteration}\n{'='*60}")

                stats = await self.run_collection_cycle(**kwargs)

                self.logger.info(f"📊 Stats: {stats}")

                # Wait for next iteration
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("\n⏹️ Loop stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Loop error: {e}")

        # Final stats
        total_duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🏁 FINAL STATS (after {total_duration:.0f}s)")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Finviz collected: {self.stats['finviz_collected']}")
        self.logger.info(f"SEC collected: {self.stats['sec_collected']}")
        self.logger.info(f"Processed: {self.stats['processed']}")
        self.logger.info(f"Saved: {self.stats['saved']}")
        self.logger.info(f"Errors: {self.stats['errors']}")


# CLI for testing
if __name__ == "__main__":
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    async def main():
        service = RealtimeNewsService()

        if len(sys.argv) > 1 and sys.argv[1] == "loop":
            # Continuous mode
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 3600
            await service.run_continuous_loop(
                interval=interval,
                duration=duration,
                finviz_enabled=True,
                sec_enabled=True,
                finviz_min_score=50,
                sec_min_score=60
            )
        else:
            # Single cycle
            stats = await service.run_collection_cycle(
                finviz_enabled=True,
                sec_enabled=True,
                finviz_min_score=50,
                sec_min_score=60
            )

            print(f"\n{'='*80}")
            print(f"📊 COLLECTION STATS")
            print(f"{'='*80}\n")

            for key, value in stats.items():
                print(f"{key}: {value}")

    asyncio.run(main())
