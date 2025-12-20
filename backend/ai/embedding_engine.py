"""
Document Embedding Engine for RAG Foundation (Phase 13).

Features:
1. OpenAI text-embedding-3-small (1536 dims, $0.02/1M tokens)
2. Automatic chunking for long documents (8000 token limit)
3. Content-based caching (SHA-256 hash)
4. Incremental embedding (only new documents)
5. Cost tracking per document type

Cost Estimation:
- SEC filing (10-K): ~50,000 tokens → $0.001
- News article: ~500 tokens → $0.00001
- 10,000 documents: ~$0.40 (one-time)
- Monthly update (100 docs): ~$0.003
"""

import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import tiktoken
from openai import AsyncOpenAI
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models.embedding_models import (
    DocumentEmbedding,
    EmbeddingCache,
    EmbeddingSyncStatus,
)

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """
    Document embedding engine with cost-efficient caching.

    Usage:
        engine = EmbeddingEngine(db_session)

        # Embed single document
        embedding_id = await engine.embed_document(
            document_type="sec_filing",
            document_id=123,
            ticker="AAPL",
            title="AAPL 10-Q Q3 2024",
            content="Apple Inc. reported...",
            source_date=datetime(2024, 8, 3)
        )

        # Embed batch of documents
        stats = await engine.embed_batch(
            documents=[
                {"document_type": "news_article", ...},
                {"document_type": "news_article", ...}
            ]
        )
    """

    # OpenAI Embedding Model
    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536
    MAX_TOKENS = 8000  # OpenAI limit: 8191 tokens
    COST_PER_MILLION_TOKENS = 0.02  # $0.02 per 1M tokens

    def __init__(self, db_session: AsyncSession, openai_api_key: Optional[str] = None):
        """
        Initialize embedding engine.

        Args:
            db_session: SQLAlchemy async session
            openai_api_key: OpenAI API key (uses env var if None)
        """
        self.db = db_session
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")

        logger.info(f"EmbeddingEngine initialized (model={self.MODEL})")

    def _compute_content_hash(self, content: str) -> str:
        """
        Compute SHA-256 hash of content for caching.

        Args:
            content: Document content

        Returns:
            Hex digest of SHA-256 hash
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Input text

        Returns:
            Token count
        """
        return len(self.tokenizer.encode(text))

    def _chunk_content(
        self, content: str, max_tokens: int = MAX_TOKENS
    ) -> List[str]:
        """
        Split long content into chunks.

        Args:
            content: Document content
            max_tokens: Max tokens per chunk

        Returns:
            List of content chunks
        """
        tokens = self.tokenizer.encode(content)
        total_tokens = len(tokens)

        if total_tokens <= max_tokens:
            return [content]

        # Split into chunks
        chunks = []
        chunk_size = max_tokens - 100  # Buffer for safety

        for i in range(0, total_tokens, chunk_size):
            chunk_tokens = tokens[i : i + chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)

        logger.info(
            f"Split content into {len(chunks)} chunks ({total_tokens} tokens)"
        )
        return chunks

    async def _check_cache(self, content_hash: str) -> Optional[int]:
        """
        Check if embedding already exists in cache.

        Args:
            content_hash: SHA-256 hash of content

        Returns:
            Embedding ID if cached, None otherwise
        """
        result = await self.db.execute(
            select(EmbeddingCache).where(EmbeddingCache.content_hash == content_hash)
        )
        cache_entry = result.scalar_one_or_none()

        if cache_entry:
            logger.debug(f"Cache HIT: {content_hash[:16]}...")
            return cache_entry.embedding_id

        return None

    async def _save_cache(self, content_hash: str, embedding_id: int):
        """
        Save embedding to cache.

        Args:
            content_hash: SHA-256 hash of content
            embedding_id: Document embedding ID
        """
        cache_entry = EmbeddingCache(
            content_hash=content_hash, embedding_id=embedding_id
        )
        self.db.add(cache_entry)
        await self.db.flush()

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI API.

        Args:
            text: Input text

        Returns:
            Embedding vector (1536 dimensions)
        """
        response = await self.client.embeddings.create(
            model=self.MODEL, input=text, encoding_format="float"
        )

        embedding = response.data[0].embedding
        return embedding

    async def embed_document(
        self,
        document_type: str,
        document_id: int,
        ticker: str,
        title: str,
        content: str,
        source_date: datetime,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[int]:
        """
        Embed a single document with automatic chunking.

        Args:
            document_type: Type of document ('sec_filing', 'news_article', etc.)
            document_id: Reference to source document ID
            ticker: Primary ticker (AAPL, MSFT)
            title: Document title
            content: Full document content
            source_date: Original document date
            metadata: Additional metadata

        Returns:
            List of embedding IDs (one per chunk)
        """
        # 1. Compute content hash
        content_hash = self._compute_content_hash(content)

        # 2. Check cache
        cached_id = await self._check_cache(content_hash)
        if cached_id:
            logger.info(
                f"Using cached embedding for {document_type} {document_id} ({ticker})"
            )
            return [cached_id]

        # 3. Chunk content
        chunks = self._chunk_content(content)
        total_chunks = len(chunks)

        # 4. Embed each chunk
        embedding_ids = []

        for chunk_index, chunk_text in enumerate(chunks):
            # Generate embedding
            embedding_vector = await self._generate_embedding(chunk_text)

            # Count tokens
            token_count = self._count_tokens(chunk_text)
            embedding_cost = (
                token_count / 1_000_000
            ) * self.COST_PER_MILLION_TOKENS

            # Create preview
            content_preview = chunk_text[:500]

            # Save to DB
            doc_embedding = DocumentEmbedding(
                document_type=document_type,
                document_id=document_id,
                ticker=ticker,
                title=title,
                content_preview=content_preview,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                embedding=embedding_vector,
                embedding_model=self.MODEL,
                embedding_cost_usd=embedding_cost,
                token_count=token_count,
                source_date=source_date,
                metadata=metadata or {},
            )

            self.db.add(doc_embedding)
            await self.db.flush()  # Generate ID

            embedding_ids.append(doc_embedding.id)

            logger.info(
                f"Embedded {document_type} {document_id} ({ticker}) "
                f"chunk {chunk_index + 1}/{total_chunks} "
                f"(tokens={token_count}, cost=${embedding_cost:.6f})"
            )

        # 5. Save to cache (only for single-chunk documents)
        if total_chunks == 1:
            await self._save_cache(content_hash, embedding_ids[0])

        await self.db.commit()

        return embedding_ids

    async def embed_batch(
        self, documents: List[Dict[str, Any]], batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Embed multiple documents in batches.

        Args:
            documents: List of document dicts with keys:
                - document_type, document_id, ticker, title, content, source_date
            batch_size: Process in batches (rate limiting)

        Returns:
            Statistics dict with embedding counts and costs
        """
        stats = {
            "total_documents": len(documents),
            "embedded": 0,
            "cached": 0,
            "total_cost_usd": 0.0,
            "total_tokens": 0,
        }

        for i, doc in enumerate(documents):
            try:
                # Check cache first
                content_hash = self._compute_content_hash(doc["content"])
                cached_id = await self._check_cache(content_hash)

                if cached_id:
                    stats["cached"] += 1
                    continue

                # Embed document
                embedding_ids = await self.embed_document(
                    document_type=doc["document_type"],
                    document_id=doc["document_id"],
                    ticker=doc["ticker"],
                    title=doc["title"],
                    content=doc["content"],
                    source_date=doc["source_date"],
                    metadata=doc.get("metadata"),
                )

                # Update stats
                stats["embedded"] += 1

                # Get cost from DB
                result = await self.db.execute(
                    select(DocumentEmbedding).where(
                        DocumentEmbedding.id.in_(embedding_ids)
                    )
                )
                embeddings = result.scalars().all()

                for emb in embeddings:
                    stats["total_cost_usd"] += emb.embedding_cost_usd
                    stats["total_tokens"] += emb.token_count

                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(
                        f"Progress: {i + 1}/{len(documents)} documents embedded"
                    )

            except Exception as e:
                logger.error(
                    f"Error embedding document {doc.get('document_id')}: {e}",
                    exc_info=True,
                )
                continue

        logger.info(
            f"Batch embedding complete: "
            f"{stats['embedded']} embedded, "
            f"{stats['cached']} cached, "
            f"${stats['total_cost_usd']:.4f}"
        )

        return stats

    async def update_sync_status(
        self,
        document_type: str,
        ticker: Optional[str],
        documents_embedded: int,
        total_cost_usd: float,
        last_document_id: int,
    ):
        """
        Update embedding sync status for incremental updates.

        Args:
            document_type: Type of document
            ticker: Ticker (None = all)
            documents_embedded: Number of documents processed
            total_cost_usd: Total embedding cost
            last_document_id: Last processed document ID
        """
        # Check if sync status exists
        result = await self.db.execute(
            select(EmbeddingSyncStatus).where(
                and_(
                    EmbeddingSyncStatus.document_type == document_type,
                    EmbeddingSyncStatus.ticker == ticker,
                )
            )
        )
        sync_status = result.scalar_one_or_none()

        if sync_status:
            # Update existing
            sync_status.last_sync_date = datetime.now()
            sync_status.last_document_id = last_document_id
            sync_status.documents_embedded += documents_embedded
            sync_status.total_cost_usd += total_cost_usd
            sync_status.updated_at = datetime.now()
        else:
            # Create new
            sync_status = EmbeddingSyncStatus(
                document_type=document_type,
                ticker=ticker,
                last_sync_date=datetime.now(),
                last_document_id=last_document_id,
                documents_embedded=documents_embedded,
                total_cost_usd=total_cost_usd,
            )
            self.db.add(sync_status)

        await self.db.commit()

        logger.info(
            f"Sync status updated: {document_type} {ticker or 'ALL'} "
            f"(embedded={documents_embedded}, cost=${total_cost_usd:.4f})"
        )


# Example usage
if __name__ == "__main__":
    import asyncio
    from backend.core.database import get_db

    async def demo():
        async with get_db() as db:
            engine = EmbeddingEngine(db)

            # Embed a sample document
            embedding_ids = await engine.embed_document(
                document_type="news_article",
                document_id=1,
                ticker="AAPL",
                title="Apple reports record Q3 earnings",
                content="Apple Inc. reported record third-quarter earnings...",
                source_date=datetime(2024, 8, 3),
            )

            print(f"Created embeddings: {embedding_ids}")

    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo())
