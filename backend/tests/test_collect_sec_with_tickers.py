"""Collect SEC data with tickers and save to DB"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.data.realtime_news_service import RealtimeNewsService


async def main():
    print("🚀 Collecting SEC data with ticker mapping...\n")

    service = RealtimeNewsService()

    # Collect from SEC only with ticker mapping enabled
    articles = await service.collect_from_sec(min_score=50)

    print(f"\n✅ Collected {len(articles)} SEC articles")

    # Show first 10 with ticker info
    print("\n" + "=" * 80)
    print("First 10 Articles (with Tickers)")
    print("=" * 80)

    for i, article in enumerate(articles[:10], 1):
        print(f"\n{i}. {article.title}")
        print(f"   Tickers: {article.tickers}")
        print(f"   Published: {article.published_at}")
        print(f"   Tags: {', '.join(article.tags[:5])}")

    # Process and save to database
    print("\n" + "=" * 80)
    print("Processing and saving to database...")
    print("=" * 80)

    saved_count = await service.process_and_save(articles)

    print(f"\n✅ Saved {saved_count}/{len(articles)} articles to database")

    # Show statistics
    stats = service.stats
    print("\n" + "=" * 80)
    print("Collection Statistics")
    print("=" * 80)
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Verify database records
    print("\n" + "=" * 80)
    print("Verifying database records...")
    print("=" * 80)

    from backend.database.repository import get_sync_session
    from backend.database.models import NewsArticle
    from sqlalchemy import text

    db = get_sync_session()
    try:
        # Count SEC articles with tickers
        recent_cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        total_sec = db.query(NewsArticle)\
            .filter(NewsArticle.source_category == 'sec')\
            .filter(NewsArticle.published_date >= recent_cutoff)\
            .count()

        with_tickers = db.execute(
            text("SELECT COUNT(*) FROM news_articles WHERE source_category = 'sec' AND published_date >= :cutoff AND tickers IS NOT NULL AND array_length(tickers, 1) > 0"),
            {"cutoff": recent_cutoff}
        ).scalar()

        print(f"  Today's SEC articles: {total_sec}")
        print(f"  With tickers: {with_tickers} ({with_tickers/total_sec*100 if total_sec > 0 else 0:.1f}%)")

        # Sample tickers
        sample = db.execute(
            text("SELECT DISTINCT unnest(tickers) as ticker FROM news_articles WHERE source_category = 'sec' AND published_date >= :cutoff LIMIT 10"),
            {"cutoff": recent_cutoff}
        ).fetchall()

        print(f"\n  Sample tickers: {', '.join([s[0] for s in sample])}")

    finally:
        db.close()

    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
