"""
SEC Filing Embedding Pipeline (Phase 13).

Incrementally embeds SEC filings for RAG retrieval.

Features:
1. Incremental embedding (only new filings)
2. Multi-ticker batch processing
3. Cost tracking and reporting
4. Resume capability (checkpoint-based)

Workflow:
1. Find new SEC filings (not yet embedded)
2. Extract key sections (MD&A, Risk Factors, Financial Statements)
3. Generate embeddings with chunking
4. Update sync status

Cost:
- 10-Q filing (~20,000 tokens): $0.0004
- 10-K filing (~50,000 tokens): $0.001
- 100 stocks × 4 filings/year × 10 years = 4,000 filings
- Total one-time cost: ~$2.50
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, not_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.embedding_engine import EmbeddingEngine
from backend.core.models.embedding_models import (
    DocumentEmbedding,
    EmbeddingSyncStatus,
)

# Mock SEC filing model (replace with actual import)
# from backend.core.models.sec_models import SECFiling

logger = logging.getLogger(__name__)


class SECEmbeddingPipeline:
    """
    SEC filing embedding pipeline with incremental updates.

    Usage:
        pipeline = SECEmbeddingPipeline(db_session)

        # Embed all new filings for a ticker
        stats = await pipeline.embed_ticker_filings("AAPL")

        # Embed all new filings for multiple tickers
        stats = await pipeline.embed_batch_tickers(["AAPL", "MSFT", "GOOGL"])

        # Backfill historical filings
        stats = await pipeline.backfill_historical(
            tickers=["AAPL"],
            years=10
        )
    """

    def __init__(self, db_session: AsyncSession, openai_api_key: Optional[str] = None):
        """
        Initialize SEC embedding pipeline.

        Args:
            db_session: SQLAlchemy async session
            openai_api_key: OpenAI API key
        """
        self.db = db_session
        self.embedding_engine = EmbeddingEngine(db_session, openai_api_key)

        logger.info("SECEmbeddingPipeline initialized")

    def _extract_key_sections(self, filing_content: str) -> str:
        """
        Extract key sections from SEC filing for embedding.

        Prioritizes:
        1. Management Discussion & Analysis (MD&A)
        2. Risk Factors
        3. Financial Highlights
        4. Recent Developments

        Args:
            filing_content: Full SEC filing text

        Returns:
            Extracted key sections (concatenated)
        """
        # Simple heuristic extraction (can be improved with NLP)
        sections = []

        # Look for common section headers
        markers = [
            "MANAGEMENT'S DISCUSSION AND ANALYSIS",
            "MD&A",
            "RISK FACTORS",
            "RESULTS OF OPERATIONS",
            "FINANCIAL CONDITION",
            "LIQUIDITY AND CAPITAL RESOURCES",
            "BUSINESS OVERVIEW",
        ]

        content_lower = filing_content.lower()

        for marker in markers:
            marker_lower = marker.lower()
            if marker_lower in content_lower:
                # Find section start
                start_idx = content_lower.index(marker_lower)

                # Extract next 5000 characters
                section_text = filing_content[start_idx : start_idx + 5000]
                sections.append(section_text)

        # If no sections found, use first 10,000 characters
        if not sections:
            sections.append(filing_content[:10000])

        extracted = "\n\n".join(sections)

        logger.debug(f"Extracted {len(extracted)} chars from filing")

        return extracted

    async def _get_unembedded_filings(
        self, ticker: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get SEC filings that haven't been embedded yet.

        Args:
            ticker: Filter by ticker (None = all)
            limit: Max filings to return

        Returns:
            List of filing dicts
        """
        # Mock implementation - replace with actual SECFiling query
        # This assumes there's a sec_filings table

        # For now, return empty list (will be replaced)
        # TODO: Implement actual query when sec_filings model is available

        logger.warning(
            "Using mock implementation - replace with actual SECFiling query"
        )

        return []

        # Actual implementation would be:
        # from backend.data.sec_file_storage import SECFileStorage
        # storage = SECFileStorage(self.db)
        # filings = await storage.list_filings(ticker=ticker, limit=limit)
        # ... filter out already embedded ...

    async def embed_ticker_filings(
        self, ticker: str, filing_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Embed all new filings for a ticker.

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            filing_types: Filter by filing types (e.g., ["10-Q", "10-K"])

        Returns:
            Statistics dict
        """
        stats = {
            "ticker": ticker,
            "filings_processed": 0,
            "embeddings_created": 0,
            "total_cost_usd": 0.0,
            "errors": 0,
        }

        # 1. Get unembedded filings
        unembedded_filings = await self._get_unembedded_filings(ticker=ticker)

        if filing_types:
            unembedded_filings = [
                f for f in unembedded_filings if f["filing_type"] in filing_types
            ]

        logger.info(
            f"{ticker}: Found {len(unembedded_filings)} new filings to embed"
        )

        # 2. Process each filing
        for filing in unembedded_filings:
            try:
                # Extract key sections
                key_content = self._extract_key_sections(filing["content"])

                # Generate embedding
                embedding_ids = await self.embedding_engine.embed_document(
                    document_type="sec_filing",
                    document_id=filing["id"],
                    ticker=ticker,
                    title=f"{ticker} {filing['filing_type']} {filing['filing_date'].strftime('%Y-%m-%d')}",
                    content=key_content,
                    source_date=filing["filing_date"],
                    metadata={
                        "filing_type": filing["filing_type"],
                        "accession_number": filing["accession_number"],
                        "fiscal_year": filing["filing_date"].year,
                        "fiscal_quarter": (filing["filing_date"].month - 1) // 3 + 1,
                    },
                )

                # Update stats
                stats["filings_processed"] += 1
                stats["embeddings_created"] += len(embedding_ids)

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
                    f"{ticker}: Embedded {filing['filing_type']} "
                    f"({filing['filing_date']}) - "
                    f"{len(embedding_ids)} chunks"
                )

            except Exception as e:
                logger.error(
                    f"Error embedding {ticker} {filing['filing_type']}: {e}",
                    exc_info=True,
                )
                stats["errors"] += 1
                continue

        # 3. Update sync status
        if stats["filings_processed"] > 0:
            last_filing_id = unembedded_filings[-1]["id"]

            await self.embedding_engine.update_sync_status(
                document_type="sec_filing",
                ticker=ticker,
                documents_embedded=stats["filings_processed"],
                total_cost_usd=stats["total_cost_usd"],
                last_document_id=last_filing_id,
            )

        logger.info(
            f"{ticker}: Embedding complete - "
            f"{stats['filings_processed']} filings, "
            f"{stats['embeddings_created']} chunks, "
            f"${stats['total_cost_usd']:.4f}"
        )

        return stats

    async def embed_batch_tickers(
        self, tickers: List[str], filing_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Embed filings for multiple tickers.

        Args:
            tickers: List of stock tickers
            filing_types: Filter by filing types

        Returns:
            Aggregate statistics dict
        """
        total_stats = {
            "tickers_processed": 0,
            "total_filings": 0,
            "total_embeddings": 0,
            "total_cost_usd": 0.0,
            "total_errors": 0,
            "by_ticker": {},
        }

        for ticker in tickers:
            try:
                stats = await self.embed_ticker_filings(
                    ticker=ticker, filing_types=filing_types
                )

                # Aggregate
                total_stats["tickers_processed"] += 1
                total_stats["total_filings"] += stats["filings_processed"]
                total_stats["total_embeddings"] += stats["embeddings_created"]
                total_stats["total_cost_usd"] += stats["total_cost_usd"]
                total_stats["total_errors"] += stats["errors"]
                total_stats["by_ticker"][ticker] = stats

                # Log progress
                logger.info(
                    f"Batch progress: {total_stats['tickers_processed']}/{len(tickers)} tickers, "
                    f"${total_stats['total_cost_usd']:.4f}"
                )

            except Exception as e:
                logger.error(f"Error processing ticker {ticker}: {e}", exc_info=True)
                total_stats["total_errors"] += 1
                continue

        logger.info(
            f"Batch embedding complete: "
            f"{total_stats['tickers_processed']} tickers, "
            f"{total_stats['total_filings']} filings, "
            f"${total_stats['total_cost_usd']:.4f}"
        )

        return total_stats

    async def backfill_historical(
        self,
        tickers: List[str],
        years: int = 10,
        filing_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Backfill historical SEC filings.

        Args:
            tickers: List of stock tickers
            years: Number of years to backfill
            filing_types: Filter by filing types (default: ["10-Q", "10-K"])

        Returns:
            Statistics dict
        """
        if not filing_types:
            filing_types = ["10-Q", "10-K"]

        logger.info(
            f"Starting historical backfill: "
            f"{len(tickers)} tickers, "
            f"{years} years, "
            f"{filing_types}"
        )

        # Use batch embedding
        stats = await self.embed_batch_tickers(
            tickers=tickers, filing_types=filing_types
        )

        logger.info(
            f"Historical backfill complete: "
            f"{stats['total_filings']} filings embedded, "
            f"${stats['total_cost_usd']:.2f}"
        )

        return stats


# Example usage
if __name__ == "__main__":
    import asyncio
    from backend.core.database import get_db

    async def demo():
        async with get_db() as db:
            pipeline = SECEmbeddingPipeline(db)

            # Embed AAPL filings
            stats = await pipeline.embed_ticker_filings("AAPL")
            print(f"AAPL embedding stats: {stats}")

            # Batch embed top tech stocks
            tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
            batch_stats = await pipeline.embed_batch_tickers(tickers)
            print(f"Batch stats: {batch_stats}")

    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo())
