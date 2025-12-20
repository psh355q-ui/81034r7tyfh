"""
Backfill Historical Document Embeddings (Phase 13).

This script embeds historical SEC filings and news articles for RAG retrieval.

Usage:
    # Backfill SEC filings (10 years, top 100 stocks)
    python -m backend.scripts.backfill_embeddings --type sec --years 10 --limit 100

    # Backfill news articles (30 days)
    python -m backend.scripts.backfill_embeddings --type news --days 30 --limit 100

    # Backfill both
    python -m backend.scripts.backfill_embeddings --type all --years 5 --days 30

Cost Estimation:
- SEC filings: 100 stocks × 4 filings/year × 10 years = 4,000 filings × $0.0005 = $2.00
- News articles: 100 stocks × 30 days × 10 articles/day = 30,000 articles × $0.00001 = $0.30
- Total one-time cost: ~$2.30
- Monthly maintenance: ~$0.05 (incremental updates)
"""

import argparse
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os

from backend.core.database import get_db, init_db
from backend.pipelines.sec_embedding_pipeline import SECEmbeddingPipeline
from backend.pipelines.news_embedding_pipeline import NewsEmbeddingPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# Top 100 S&P 500 stocks by market cap
TOP_100_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "UNH", "JNJ",
    "XOM", "V", "PG", "JPM", "MA", "HD", "CVX", "MRK", "ABBV", "PEP",
    "COST", "AVGO", "KO", "LLY", "ADBE", "PFE", "WMT", "MCD", "CSCO", "TMO",
    "BAC", "ABT", "CRM", "ACN", "DHR", "NKE", "NFLX", "TXN", "DIS", "LIN",
    "VZ", "UPS", "PM", "NEE", "ORCL", "MS", "RTX", "HON", "QCOM", "INTU",
    "IBM", "LOW", "BMY", "AMD", "UNP", "AMGN", "COP", "BA", "SPGI", "SCHW",
    "ELV", "GS", "DE", "PLD", "BLK", "AXP", "MDT", "GILD", "TJX", "SYK",
    "ISRG", "REGN", "CI", "ADP", "MMC", "BKNG", "MDLZ", "ADI", "C", "CVS",
    "VRTX", "ZTS", "TMUS", "SO", "MO", "CB", "NOW", "DUK", "SLB", "EOG",
    "ITW", "PGR", "GE", "USB", "BDX", "TGT", "ETN", "CME", "NSC", "WM",
]


async def backfill_sec_filings(
    tickers: List[str], years: int = 10
) -> Dict[str, Any]:
    """
    Backfill SEC filings for given tickers.

    Args:
        tickers: List of stock tickers
        years: Number of years to backfill

    Returns:
        Statistics dict
    """
    logger.info(f"Starting SEC backfill: {len(tickers)} tickers, {years} years")

    async with get_db() as db:
        pipeline = SECEmbeddingPipeline(db)

        stats = await pipeline.backfill_historical(
            tickers=tickers,
            years=years,
            filing_types=["10-Q", "10-K"],
        )

        logger.info(
            f"SEC backfill complete: "
            f"{stats['total_filings']} filings, "
            f"${stats['total_cost_usd']:.2f}"
        )

        return stats


async def backfill_news_articles(
    tickers: List[str], days: int = 30
) -> Dict[str, Any]:
    """
    Backfill news articles for given tickers.

    Args:
        tickers: List of stock tickers
        days: Number of days to backfill

    Returns:
        Statistics dict
    """
    logger.info(f"Starting news backfill: {len(tickers)} tickers, {days} days")

    async with get_db() as db:
        pipeline = NewsEmbeddingPipeline(db)

        stats = await pipeline.embed_batch_tickers_news(
            tickers=tickers, hours=days * 24
        )

        logger.info(
            f"News backfill complete: "
            f"{stats['total_articles_embedded']} articles, "
            f"${stats['total_cost_usd']:.5f}"
        )

        return stats


async def backfill_all(
    tickers: List[str], years: int = 10, days: int = 30
) -> Dict[str, Any]:
    """
    Backfill both SEC filings and news articles.

    Args:
        tickers: List of stock tickers
        years: SEC filing years
        days: News article days

    Returns:
        Combined statistics
    """
    logger.info(
        f"Starting full backfill: {len(tickers)} tickers, "
        f"{years} years SEC, {days} days news"
    )

    # 1. Initialize database
    await init_db()

    # 2. Backfill SEC filings
    sec_stats = await backfill_sec_filings(tickers, years)

    # 3. Backfill news articles
    news_stats = await backfill_news_articles(tickers, days)

    # 4. Combine stats
    total_stats = {
        "sec_filings": sec_stats["total_filings"],
        "sec_cost_usd": sec_stats["total_cost_usd"],
        "news_articles": news_stats["total_articles_embedded"],
        "news_cost_usd": news_stats["total_cost_usd"],
        "total_documents": sec_stats["total_filings"]
        + news_stats["total_articles_embedded"],
        "total_cost_usd": sec_stats["total_cost_usd"] + news_stats["total_cost_usd"],
        "tickers": len(tickers),
    }

    logger.info(
        f"\n{'='*60}\n"
        f"BACKFILL COMPLETE\n"
        f"{'='*60}\n"
        f"Tickers: {total_stats['tickers']}\n"
        f"SEC Filings: {total_stats['sec_filings']:,} (${total_stats['sec_cost_usd']:.2f})\n"
        f"News Articles: {total_stats['news_articles']:,} (${total_stats['news_cost_usd']:.5f})\n"
        f"Total Documents: {total_stats['total_documents']:,}\n"
        f"Total Cost: ${total_stats['total_cost_usd']:.2f}\n"
        f"{'='*60}"
    )

    return total_stats


async def verify_embeddings() -> Dict[str, Any]:
    """
    Verify embedding quality and count.

    Returns:
        Verification statistics
    """
    logger.info("Verifying embeddings...")

    async with get_db() as db:
        from sqlalchemy import select, func
        from backend.core.models.embedding_models import DocumentEmbedding

        # Count by document type
        result = await db.execute(
            select(
                DocumentEmbedding.document_type,
                func.count(DocumentEmbedding.id).label("count"),
                func.sum(DocumentEmbedding.embedding_cost_usd).label("total_cost"),
            ).group_by(DocumentEmbedding.document_type)
        )

        stats = {}
        for row in result:
            stats[row.document_type] = {
                "count": row.count,
                "cost": float(row.total_cost or 0),
            }

        # Count by ticker (top 10)
        result = await db.execute(
            select(
                DocumentEmbedding.ticker,
                func.count(DocumentEmbedding.id).label("count"),
            )
            .group_by(DocumentEmbedding.ticker)
            .order_by(func.count(DocumentEmbedding.id).desc())
            .limit(10)
        )

        top_tickers = [(row.ticker, row.count) for row in result]

        logger.info(
            f"\nEmbedding Statistics:\n"
            f"By Type: {stats}\n"
            f"Top 10 Tickers: {top_tickers}"
        )

        return {"by_type": stats, "top_tickers": top_tickers}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill historical document embeddings for RAG"
    )

    parser.add_argument(
        "--type",
        choices=["sec", "news", "all"],
        default="all",
        help="Type of documents to backfill",
    )

    parser.add_argument(
        "--years", type=int, default=10, help="Years of SEC filings to backfill"
    )

    parser.add_argument(
        "--days", type=int, default=30, help="Days of news articles to backfill"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of tickers to process (top N by market cap)",
    )

    parser.add_argument(
        "--tickers",
        nargs="+",
        help="Specific tickers to process (overrides --limit)",
    )

    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing embeddings (no backfill)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print plan without executing",
    )

    args = parser.parse_args()

    # Select tickers
    if args.tickers:
        tickers = args.tickers
    else:
        tickers = TOP_100_TICKERS[: args.limit]

    # Verify only
    if args.verify_only:
        asyncio.run(verify_embeddings())
        return

    # Dry run
    if args.dry_run:
        logger.info(
            f"\nDRY RUN - Backfill Plan:\n"
            f"{'='*60}\n"
            f"Type: {args.type}\n"
            f"Tickers: {len(tickers)} ({', '.join(tickers[:10])}...)\n"
            f"SEC Years: {args.years}\n"
            f"News Days: {args.days}\n"
            f"\nEstimated Cost:\n"
            f"  SEC: {len(tickers) * 4 * args.years} filings × $0.0005 = ${len(tickers) * 4 * args.years * 0.0005:.2f}\n"
            f"  News: {len(tickers) * args.days * 10} articles × $0.00001 = ${len(tickers) * args.days * 10 * 0.00001:.5f}\n"
            f"{'='*60}\n"
        )
        return

    # Execute backfill
    if args.type == "sec":
        asyncio.run(backfill_sec_filings(tickers, args.years))
    elif args.type == "news":
        asyncio.run(backfill_news_articles(tickers, args.days))
    else:  # all
        asyncio.run(backfill_all(tickers, args.years, args.days))

    # Verify
    asyncio.run(verify_embeddings())


if __name__ == "__main__":
    main()
