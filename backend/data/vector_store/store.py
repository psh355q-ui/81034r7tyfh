"""
VectorStore - TimescaleDB + pgvector interface for RAG.

Features:
- Document storage with auto-tagging
- Vector similarity search with tag filtering
- Incremental update tracking
- Cost tracking
- Related ticker discovery
"""

import asyncpg
from typing import List, Dict, Optional, Any
from datetime import datetime
from .embedder import DocumentEmbedder
from .tagger import AutoTagger


class VectorStore:
    """
    TimescaleDB + pgvector interface for RAG with auto-tagging.
    
    Architecture:
    - Vector embeddings: 1536-dim (OpenAI text-embedding-3-small)
    - Storage: TimescaleDB hypertable (partitioned by document_date)
    - Index: IVFFlat for fast cosine similarity search
    - Tags: Multi-dimensional tagging (ticker, sector, topic, entity, geographic)
    
    Usage:
        store = VectorStore(db_pool, embedder, tagger)
        
        # Add document with auto-tagging
        doc_id = await store.add_document(
            ticker="AAPL",
            doc_type="10K",
            content="Risk factors section...",
            metadata={"filing_date": "2024-10-30"},
            document_date=datetime(2024, 10, 30),
            auto_tag=True
        )
        
        # Search with tag filtering
        results = await store.search_similar(
            query="supply chain disruption",
            tags={"sector": ["Technology"], "topic": ["supply_chain"]},
            top_k=10
        )
    """
    
    def __init__(
        self,
        db_pool: asyncpg.Pool,
        embedder: DocumentEmbedder,
        tagger: Optional[AutoTagger] = None
    ):
        """
        Initialize VectorStore.
        
        Args:
            db_pool: AsyncPG connection pool
            embedder: DocumentEmbedder instance
            tagger: AutoTagger instance (optional, required for auto_tag=True)
        """
        self.db = db_pool
        self.embedder = embedder
        self.tagger = tagger
        
        # Stats
        self.total_documents = 0
        self.total_searches = 0
    
    async def add_document(
        self,
        ticker: str,
        doc_type: str,
        content: str,
        metadata: Dict,
        document_date: datetime,
        auto_tag: bool = True
    ) -> int:
        """
        Add document to vector store with automatic tagging.
        
        Args:
            ticker: Stock ticker symbol
            doc_type: Document type ('10K', '10Q', '8K', 'news', 'earnings_call', 'regime')
            content: Document text content
            metadata: Additional metadata (JSONB)
            document_date: Filing/publish date (for incremental updates)
            auto_tag: Whether to generate tags automatically
        
        Returns:
            Document ID (or existing ID if duplicate)
        
        Example:
            >>> doc_id = await store.add_document(
            ...     ticker="AAPL",
            ...     doc_type="10K",
            ...     content="Apple Inc. faces supply chain risks in China...",
            ...     metadata={"filing_date": "2024-10-30", "fiscal_year": 2024},
            ...     document_date=datetime(2024, 10, 30),
            ...     auto_tag=True
            ... )
            >>> doc_id
            123
        """
        # Check for duplicates (by content hash)
        content_hash = DocumentEmbedder.hash_content(content)
        existing = await self.db.fetchval(
            "SELECT id FROM document_embeddings WHERE content_hash = $1",
            content_hash
        )
        
        if existing:
            print(f"  ⏭️  Document already exists (ID: {existing}), skipping")
            return existing
        
        # Generate embedding
        embed_result = await self.embedder.embed_text(content)
        
        # Insert to DB
        doc_id = await self.db.fetchval("""
            INSERT INTO document_embeddings 
                (ticker, doc_type, content, content_hash, embedding, metadata, document_date)
            VALUES ($1, $2, $3, $4, $5::vector, $6, $7)
            RETURNING id
        """, ticker, doc_type, content, content_hash, embed_result.embedding, metadata, document_date)
        
        # Auto-generate tags
        if auto_tag and self.tagger:
            tags = await self.tagger.generate_tags(content, ticker, doc_type)
            await self._add_tags(doc_id, tags)
            print(f"  🏷️  Generated {len(tags)} tags")
        
        # Track cost
        await self._track_cost(1, embed_result.tokens, embed_result.cost)
        
        # Update sync status
        await self._update_sync_status(ticker, doc_type, document_date, embed_result.cost)
        
        self.total_documents += 1
        
        return doc_id
    
    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        ticker: Optional[str] = None,
        doc_type: Optional[str] = None,
        tags: Optional[Dict[str, List[str]]] = None,
        min_similarity: float = 0.7,
        date_range: Optional[tuple[datetime, datetime]] = None
    ) -> List[Dict]:
        """
        Search for similar documents using cosine similarity with tag filtering.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            ticker: Filter by specific ticker (optional)
            doc_type: Filter by document type (optional)
            tags: Filter by tags, e.g. {"sector": ["Technology"], "topic": ["supply_chain"]}
            min_similarity: Minimum cosine similarity threshold (0-1)
            date_range: Filter by document date range (start, end)
        
        Returns:
            List of matching documents with similarity scores and tags
        
        Example:
            >>> results = await store.search_similar(
            ...     query="CEO mentions supply chain issues",
            ...     tags={"sector": ["Technology"], "topic": ["supply_chain"]},
            ...     top_k=5
            ... )
            >>> results[0]
            {
                "id": 123,
                "ticker": "AAPL",
                "doc_type": "10K",
                "content": "Apple faces supply chain risks...",
                "similarity": 0.92,
                "tags": [
                    {"type": "ticker", "value": "AAPL", "confidence": 1.0},
                    {"type": "topic", "value": "supply_chain", "confidence": 0.87}
                ]
            }
        """
        # Generate query embedding
        query_embed = await self.embedder.embed_text(query)
        
        # Build SQL with optional filters
        sql = """
            SELECT 
                de.id,
                de.ticker,
                de.doc_type,
                de.content,
                de.metadata,
                de.document_date,
                de.created_at,
                1 - (de.embedding <=> $1::vector) AS similarity,
                COALESCE(
                    array_agg(
                        json_build_object(
                            'type', dt.tag_type,
                            'value', dt.tag_value,
                            'confidence', dt.confidence
                        )
                    ) FILTER (WHERE dt.id IS NOT NULL),
                    '{}'
                ) as tags
            FROM document_embeddings de
            LEFT JOIN document_tags dt ON de.id = dt.document_id
            WHERE 1=1
        """
        params = [query_embed.embedding]
        param_idx = 2
        
        # Ticker filter
        if ticker:
            sql += f" AND de.ticker = ${param_idx}"
            params.append(ticker)
            param_idx += 1
        
        # Doc type filter
        if doc_type:
            sql += f" AND de.doc_type = ${param_idx}"
            params.append(doc_type)
            param_idx += 1
        
        # Date range filter
        if date_range:
            start_date, end_date = date_range
            sql += f" AND de.document_date BETWEEN ${param_idx} AND ${param_idx + 1}"
            params.extend([start_date, end_date])
            param_idx += 2
        
        # Tag filtering
        if tags:
            for tag_type, tag_values in tags.items():
                sql += f"""
                    AND de.id IN (
                        SELECT document_id FROM document_tags
                        WHERE tag_type = ${param_idx} AND tag_value = ANY(${param_idx + 1})
                    )
                """
                params.extend([tag_type, tag_values])
                param_idx += 2
        
        sql += f"""
            GROUP BY de.id
            ORDER BY de.embedding <=> $1::vector
            LIMIT ${param_idx}
        """
        params.append(top_k * 2)  # Fetch 2x, then filter by similarity
        
        # Execute search
        rows = await self.db.fetch(sql, *params)
        
        # Filter by minimum similarity
        results = []
        for row in rows:
            if row["similarity"] >= min_similarity:
                results.append({
                    "id": row["id"],
                    "ticker": row["ticker"],
                    "doc_type": row["doc_type"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "similarity": float(row["similarity"]),
                    "document_date": row["document_date"],
                    "created_at": row["created_at"],
                    "tags": row["tags"] if row["tags"] else []
                })
        
        # Return top_k after filtering
        results = results[:top_k]
        
        self.total_searches += 1
        
        return results
    
    async def get_incremental_updates_needed(
        self,
        ticker: str,
        doc_type: str
    ) -> Optional[datetime]:
        """
        Check when incremental update is needed for a ticker/doc_type.
        
        Args:
            ticker: Stock ticker
            doc_type: Document type
        
        Returns:
            Last document date if updates needed, None if never synced
        
        Example:
            >>> last_date = await store.get_incremental_updates_needed("AAPL", "10K")
            >>> last_date
            datetime(2024, 10, 30)  # Fetch docs after this date
        """
        sync_status = await self.db.fetchrow("""
            SELECT last_document_date, last_sync_date
            FROM document_sync_status
            WHERE ticker = $1 AND doc_type = $2
        """, ticker, doc_type)
        
        if not sync_status:
            # Never synced - need full backfill
            return None
        
        # Return last document date to fetch only newer documents
        return sync_status["last_document_date"]
    
    async def find_related_tickers(
        self,
        ticker: str,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Find tickers with similar document patterns (sector peers, supply chain).
        
        Uses tag co-occurrence analysis to find related companies.
        
        Args:
            ticker: Stock ticker
            top_k: Number of related tickers to return
        
        Returns:
            List of related tickers with shared tag counts
        
        Example:
            >>> related = await store.find_related_tickers("AAPL", top_k=5)
            >>> related
            [
                {"ticker": "MSFT", "shared_tags": 15, "latest_doc": "2024-11-01"},
                {"ticker": "GOOGL", "shared_tags": 12, "latest_doc": "2024-10-28"},
                ...
            ]
        """
        related = await self.db.fetch("""
            WITH ticker_tags AS (
                SELECT DISTINCT dt.tag_type, dt.tag_value
                FROM document_tags dt
                JOIN document_embeddings de ON dt.document_id = de.id
                WHERE de.ticker = $1
            )
            SELECT 
                de.ticker,
                COUNT(DISTINCT dt.tag_value) as shared_tags,
                array_agg(DISTINCT de.doc_type) as doc_types,
                MAX(de.document_date) as latest_doc
            FROM document_embeddings de
            JOIN document_tags dt ON de.id = dt.document_id
            WHERE (dt.tag_type, dt.tag_value) IN (
                    SELECT tag_type, tag_value FROM ticker_tags
                )
                AND de.ticker != $1
            GROUP BY de.ticker
            ORDER BY shared_tags DESC
            LIMIT $2
        """, ticker, top_k)
        
        return [
            {
                "ticker": row["ticker"],
                "shared_tags": row["shared_tags"],
                "doc_types": row["doc_types"],
                "latest_doc": row["latest_doc"]
            }
            for row in related
        ]
    
    # ===== Phase 15: CEO Speech Analysis Methods =====
    
    async def embed_sec_analysis(
        self,
        analysis: Any  # SECAnalysisResult
    ) -> int:
        """
        SEC 분석 결과 임베딩 (Phase 15 Tier 2)
        
        Args:
            analysis: SECAnalysisResult 객체
            
        Returns:
            Document ID
        """
        # CEO quotes 별도 임베딩
        if hasattr(analysis, 'management_analysis') and analysis.management_analysis:
            for quote in analysis.management_analysis.ceo_quotes:
                await self.add_document(
                    ticker=analysis.ticker,
                    doc_type="ceo_quote",
                    content=quote.text,
                    metadata={
                        "fiscal_period": analysis.fiscal_period,
                        "quote_type": quote.quote_type,
                        "source": "sec_filing",
                        "sentiment": quote.sentiment
                    },
                    document_date=analysis.analysis_date,
                    auto_tag=True
                )
        
        # 전체 분석 임베딩
        summary_text = f"{analysis.executive_summary}\n{' '.join(analysis.key_takeaways)}"
        return await self.add_document(
            ticker=analysis.ticker,
            doc_type="sec_analysis",
            content=summary_text,
            metadata={
                "fiscal_period": analysis.fiscal_period,
                "risk_level": analysis.overall_risk_level.value,
                "filing_type": analysis.filing_type
            },
            document_date=analysis.analysis_date,
            auto_tag=True
        )
    
    async def find_similar_ceo_statements(
        self,
        current_statement: str,
        ticker: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        과거 유사 CEO 발언 검색 (Phase 15 Tier 2)
        
        Args:
            current_statement: 현재 CEO 발언
            ticker: 주식 티커
            top_k: 반환할 결과 수
            
        Returns:
            유사 발언 목록 (similarity, outcome 포함)
        """
        # Vector search
        results = await self.search_similar(
            query=current_statement,
            ticker=ticker,
            doc_type="ceo_quote",
            top_k=top_k,
            min_similarity=0.7
        )
        
        # 결과 추적 추가 (3개월 후 주가 변동)
        matches = []
        for result in results:
            # Outcome tracking (placeholder - 실제로는 주가 데이터 조회 필요)
            outcome = await self._get_outcome(
                ticker=ticker,
                date=result.get("metadata", {}).get("fiscal_period", "")
            )
            
            matches.append({
                "date": result.get("metadata", {}).get("fiscal_period", ""),
                "statement": result["content"],
                "similarity": result["similarity"],
                "outcome": outcome,
                "source": result.get("metadata", {}).get("source", "unknown")
            })
        
        return matches
    
    async def _get_outcome(self, ticker: str, date: str) -> Optional[str]:
        """
        발언 후 주가 변동 조회 (placeholder)
        
        실제 구현 시 Yahoo Finance API로 3개월 후 주가 변동 계산
        """
        # TODO: 실제 주가 데이터 조회 구현
        return None
    
    async def get_ticker_tags(self, ticker: str) -> Dict[str, List[str]]:
        """
        Get all tags for a specific ticker, grouped by type.
        
        Args:
            ticker: Stock ticker
        
        Returns:
            Dictionary of tag_type -> [tag_values]
        
        Example:
            >>> tags = await store.get_ticker_tags("AAPL")
            >>> tags
            {
                "ticker": ["AAPL", "TSLA", "MSFT"],
                "sector": ["Technology"],
                "topic": ["supply_chain", "AI_adoption"],
                "entity": ["Tim Cook", "iPhone 15"],
                "geographic": ["China", "United States"]
            }
        """
        rows = await self.db.fetch("""
            SELECT DISTINCT dt.tag_type, dt.tag_value
            FROM document_tags dt
            JOIN document_embeddings de ON dt.document_id = de.id
            WHERE de.ticker = $1
            ORDER BY dt.tag_type, dt.tag_value
        """, ticker)
        
        tags_by_type = {}
        for row in rows:
            tag_type = row["tag_type"]
            tag_value = row["tag_value"]
            
            if tag_type not in tags_by_type:
                tags_by_type[tag_type] = []
            
            tags_by_type[tag_type].append(tag_value)
        
        return tags_by_type
    
    async def get_cost_stats(
        self,
        days: int = 30
    ) -> Dict:
        """
        Get embedding cost statistics.
        
        Args:
            days: Number of days to look back
        
        Returns:
            Dictionary with cost statistics
        
        Example:
            >>> stats = await store.get_cost_stats(days=7)
            >>> stats
            {
                "total_documents": 1523,
                "total_tokens": 752389,
                "total_cost_usd": 0.0150,
                "daily_avg_cost_usd": 0.0021,
                "period_days": 7
            }
        """
        stats = await self.db.fetchrow(f"""
            SELECT 
                SUM(doc_count) as total_documents,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost_usd
            FROM embedding_costs
            WHERE created_at >= NOW() - INTERVAL '{days} days'
        """)
        
        return {
            "total_documents": stats["total_documents"] or 0,
            "total_tokens": stats["total_tokens"] or 0,
            "total_cost_usd": float(stats["total_cost_usd"] or 0),
            "daily_avg_cost_usd": float(stats["total_cost_usd"] or 0) / days,
            "period_days": days
        }
    
    async def refresh_tag_stats(self):
        """Refresh materialized view for tag statistics."""
        await self.db.execute("REFRESH MATERIALIZED VIEW tag_stats")
        print("✅ Tag statistics refreshed")
    
    # ===== Private Helper Methods =====
    
    async def _add_tags(self, document_id: int, tags: List[Dict]):
        """Add tags to document."""
        for tag in tags:
            try:
                await self.db.execute("""
                    INSERT INTO document_tags (document_id, tag_type, tag_value, confidence)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (document_id, tag_type, tag_value) DO NOTHING
                """, document_id, tag["type"], tag["value"], tag["confidence"])
            except Exception as e:
                print(f"  ⚠️  Failed to add tag {tag}: {e}")
    
    async def _update_sync_status(
        self,
        ticker: str,
        doc_type: str,
        document_date: datetime,
        cost: float
    ):
        """Update incremental sync tracking."""
        await self.db.execute("""
            INSERT INTO document_sync_status 
                (ticker, doc_type, last_sync_date, last_document_date, documents_processed, total_cost_usd)
            VALUES ($1, $2, NOW(), $3, 1, $4)
            ON CONFLICT (ticker, doc_type) DO UPDATE SET
                last_sync_date = NOW(),
                last_document_date = GREATEST(
                    document_sync_status.last_document_date,
                    EXCLUDED.last_document_date
                ),
                documents_processed = document_sync_status.documents_processed + 1,
                total_cost_usd = document_sync_status.total_cost_usd + EXCLUDED.total_cost_usd,
                updated_at = NOW()
        """, ticker, doc_type, document_date, cost)
    
    async def _track_cost(self, doc_count: int, tokens: int, cost: float):
        """Track embedding API costs to database."""
        import uuid
        await self.db.execute("""
            INSERT INTO embedding_costs (batch_id, doc_count, total_tokens, cost_usd)
            VALUES ($1, $2, $3, $4)
        """, uuid.uuid4(), doc_count, tokens, cost)
    
    async def close(self):
        """Close database connection pool."""
        await self.db.close()
        print("✅ VectorStore closed")


# Async context manager support
class VectorStoreContext:
    """Context manager for VectorStore."""
    
    def __init__(
        self,
        db_dsn: str,
        embedder: DocumentEmbedder,
        tagger: Optional[AutoTagger] = None
    ):
        self.db_dsn = db_dsn
        self.embedder = embedder
        self.tagger = tagger
        self.pool = None
        self.store = None
    
    async def __aenter__(self):
        # Create connection pool
        self.pool = await asyncpg.create_pool(
            self.db_dsn,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        # Create store
        self.store = VectorStore(self.pool, self.embedder, self.tagger)
        
        return self.store
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Close pool
        if self.pool:
            await self.pool.close()
        
        print("✅ VectorStore connection pool closed")


if __name__ == "__main__":
    # Example usage
    import asyncio
    import os
    from .embedder import DocumentEmbedder
    from .tagger import AutoTagger
    from anthropic import AsyncAnthropic
    
    async def test():
        # Configuration
        db_dsn = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_trading")
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not openai_key:
            print("❌ Set OPENAI_API_KEY environment variable")
            return
        
        # Initialize components
        embedder = DocumentEmbedder(openai_key)
        
        tagger = None
        if anthropic_key:
            claude = AsyncAnthropic(api_key=anthropic_key)
            tagger = AutoTagger(claude_client=claude, use_ai=True)
        
        # Use context manager
        async with VectorStoreContext(db_dsn, embedder, tagger) as store:
            # Test 1: Add document
            doc_id = await store.add_document(
                ticker="AAPL",
                doc_type="news",
                content="Apple Inc. reports supply chain disruptions affecting iPhone production in China.",
                metadata={"source": "Reuters", "url": "https://example.com"},
                document_date=datetime.now(),
                auto_tag=True
            )
            print(f"\n✅ Added document ID: {doc_id}")
            
            # Test 2: Search similar
            results = await store.search_similar(
                query="supply chain problems",
                tags={"topic": ["supply_chain"]},
                top_k=5
            )
            print(f"\n✅ Found {len(results)} similar documents:")
            for r in results:
                print(f"   - {r['ticker']} ({r['similarity']:.2f}): {r['content'][:100]}...")
            
            # Test 3: Get ticker tags
            tags = await store.get_ticker_tags("AAPL")
            print(f"\n✅ Tags for AAPL:")
            for tag_type, values in tags.items():
                print(f"   {tag_type}: {', '.join(values[:5])}")
            
            # Test 4: Cost stats
            stats = await store.get_cost_stats(days=1)
            print(f"\n📊 Cost Stats (last 24h):")
            print(f"   Documents: {stats['total_documents']}")
            print(f"   Total cost: ${stats['total_cost_usd']:.6f}")
    
    asyncio.run(test())

