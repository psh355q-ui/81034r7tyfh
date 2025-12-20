# RAG Foundation - Technical Implementation Plan

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Data Sources (Historical)                  │
│   SEC EDGAR (10-K/10-Q) │ News Archive │ FRED Economic Data  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 Document Processing Layer                    │
│   Chunker → OpenAI Embeddings API → Metadata Extraction     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Vector Store (TimescaleDB + pgvector)           │
│   - document_embeddings table (1536-dim vectors)             │
│   - IVFFlat index for cosine similarity search               │
│   - Redis cache (7-day TTL for searches)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    RAG-Enhanced AI Strategies                │
│   Risk Analysis │ Market Regime │ SEC Pattern Detection     │
└─────────────────────────────────────────────────────────────┘
```

## 2. Database Schema Design

### 2.1 TimescaleDB Tables

```sql
-- Main vector storage table
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    doc_type VARCHAR(50) NOT NULL,  -- '10K', '10Q', 'news', 'earnings_call', 'regime'
    content TEXT NOT NULL,
    content_hash VARCHAR(64) UNIQUE,  -- SHA256 for deduplication
    embedding VECTOR(1536) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    document_date TIMESTAMPTZ NOT NULL,  -- Filing/publish date for incremental updates
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Index for fast lookups
    CONSTRAINT valid_doc_type CHECK (doc_type IN ('10K', '10Q', '8K', 'news', 'earnings_call', 'regime'))
);

-- Hypertable for time-series optimization (use document_date, not created_at)
SELECT create_hypertable('document_embeddings', 'document_date',
    chunk_time_interval => INTERVAL '3 months'
);

-- Vector similarity index (IVFFlat algorithm)
CREATE INDEX ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Tune based on data size

-- Lookup indexes
CREATE INDEX idx_doc_ticker_type ON document_embeddings(ticker, doc_type);
CREATE INDEX idx_doc_hash ON document_embeddings(content_hash);
CREATE INDEX idx_doc_date ON document_embeddings(document_date DESC);
CREATE INDEX idx_doc_created ON document_embeddings(created_at DESC);

-- Auto-generated tags table
CREATE TABLE document_tags (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES document_embeddings(id) ON DELETE CASCADE,
    tag_type VARCHAR(50) NOT NULL,  -- 'ticker', 'sector', 'topic', 'entity'
    tag_value VARCHAR(200) NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 1.0,  -- AI confidence score (0-1)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(document_id, tag_type, tag_value),
    CONSTRAINT valid_tag_type CHECK (tag_type IN ('ticker', 'sector', 'topic', 'entity', 'geographic'))
);

-- Indexes for tag-based search
CREATE INDEX idx_tag_type_value ON document_tags(tag_type, tag_value);
CREATE INDEX idx_tag_document ON document_tags(document_id);

-- Materialized view for tag statistics
CREATE MATERIALIZED VIEW tag_stats AS
SELECT 
    tag_type,
    tag_value,
    COUNT(DISTINCT document_id) as doc_count,
    AVG(confidence) as avg_confidence,
    MAX(de.created_at) as last_seen
FROM document_tags dt
JOIN document_embeddings de ON dt.document_id = de.id
GROUP BY tag_type, tag_value;

CREATE INDEX idx_tag_stats_lookup ON tag_stats(tag_type, tag_value);

-- Incremental update tracking table
CREATE TABLE document_sync_status (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    doc_type VARCHAR(50) NOT NULL,
    last_sync_date TIMESTAMPTZ NOT NULL,
    last_document_date TIMESTAMPTZ NOT NULL,  -- Latest document date processed
    documents_processed INTEGER NOT NULL DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(ticker, doc_type)
);

-- Index for incremental updates
CREATE INDEX idx_sync_status_lookup ON document_sync_status(ticker, doc_type);

-- Embedding cost tracking
CREATE TABLE embedding_costs (
    id SERIAL PRIMARY KEY,
    batch_id UUID NOT NULL,
    doc_count INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('embedding_costs', 'created_at',
    chunk_time_interval => INTERVAL '1 month'
);
```

### 2.2 Redis Cache Schema

```
# Vector search results cache
vsearch:{query_hash}:{top_k} = {
    "results": [...],
    "timestamp": "2025-11-22T10:00:00Z"
}
TTL: 604800 seconds (7 days)

# Embedding cache (avoid re-embedding same text)
embed:{content_hash} = {
    "embedding": [0.123, ...],
    "model": "text-embedding-3-small"
}
TTL: 2592000 seconds (30 days)
```

## 3. Module Design

### 3.1 Directory Structure

```
backend/
├── data/
│   └── vector_store/
│       ├── __init__.py
│       ├── embedder.py          # OpenAI Embedding API wrapper
│       ├── store.py             # Vector store interface
│       ├── chunker.py           # Text chunking logic
│       └── cost_tracker.py      # Cost monitoring
│
├── ai/
│   └── rag/
│       ├── __init__.py
│       ├── retriever.py         # RAG retrieval logic
│       └── augmentor.py         # Context augmentation
│
└── scripts/
    └── backfill/
        ├── embed_sec_filings.py # Historical SEC data ingestion
        └── embed_news.py        # Historical news ingestion
```

### 3.2 Core Classes

#### A. DocumentEmbedder

```python
# backend/data/vector_store/embedder.py

from openai import AsyncOpenAI
from typing import List, Dict
import hashlib

class DocumentEmbedder:
    """OpenAI Embedding API wrapper with cost tracking."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.cost_per_million = 0.02  # $0.02 per 1M tokens
    
    async def embed_text(self, text: str) -> Dict:
        """
        Embed single text string.
        
        Returns:
            {
                "embedding": List[float],  # 1536-dim vector
                "tokens": int,
                "cost": float
            }
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        embedding = response.data[0].embedding
        tokens = response.usage.total_tokens
        cost = (tokens / 1_000_000) * self.cost_per_million
        
        return {
            "embedding": embedding,
            "tokens": tokens,
            "cost": cost
        }
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[Dict]:
        """
        Embed batch of texts with rate limiting.
        
        OpenAI rate limit: 3,000 RPM for tier 1
        So we batch 100 at a time with delays.
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            
            for j, data in enumerate(response.data):
                results.append({
                    "text": batch[j],
                    "embedding": data.embedding,
                    "tokens": len(batch[j].split()) * 1.3,  # rough estimate
                    "cost": (len(batch[j].split()) * 1.3 / 1_000_000) * self.cost_per_million
                })
            
            # Rate limiting: 100 embeddings per 2 seconds
            await asyncio.sleep(2)
        
        return results
    
    @staticmethod
    def hash_content(text: str) -> str:
        """Generate SHA256 hash for deduplication."""
        return hashlib.sha256(text.encode()).hexdigest()
```

#### B. VectorStore

```python
# backend/data/vector_store/store.py

import asyncpg
from typing import List, Dict, Optional
from .embedder import DocumentEmbedder

class VectorStore:
    """TimescaleDB + pgvector interface for RAG with auto-tagging."""
    
    def __init__(self, db_pool: asyncpg.Pool, embedder: DocumentEmbedder, tagger: AutoTagger):
        self.db = db_pool
        self.embedder = embedder
        self.tagger = tagger
    
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
            doc_type: Document type (10K, 10Q, news, etc.)
            content: Document text content
            metadata: Additional metadata (JSONB)
            document_date: Filing/publish date (for incremental updates)
            auto_tag: Whether to generate tags automatically
        
        Returns: document ID
        """
        # Check for duplicates
        content_hash = DocumentEmbedder.hash_content(content)
        existing = await self.db.fetchval(
            "SELECT id FROM document_embeddings WHERE content_hash = $1",
            content_hash
        )
        
        if existing:
            return existing
        
        # Generate embedding
        embed_result = await self.embedder.embed_text(content)
        
        # Insert to DB
        doc_id = await self.db.fetchval("""
            INSERT INTO document_embeddings 
                (ticker, doc_type, content, content_hash, embedding, metadata, document_date)
            VALUES ($1, $2, $3, $4, $5::vector, $6, $7)
            RETURNING id
        """, ticker, doc_type, content, content_hash, embed_result["embedding"], metadata, document_date)
        
        # Auto-generate tags
        if auto_tag:
            tags = await self.tagger.generate_tags(content, ticker, doc_type)
            await self._add_tags(doc_id, tags)
        
        # Track cost
        await self._track_cost(1, embed_result["tokens"], embed_result["cost"])
        
        # Update sync status
        await self._update_sync_status(ticker, doc_type, document_date, embed_result["cost"])
        
        return doc_id
    
    async def search_similar(
        self,
        query: str,
        top_k: int = 5,
        ticker: Optional[str] = None,
        doc_type: Optional[str] = None,
        tags: Optional[Dict[str, List[str]]] = None,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        Search for similar documents using cosine similarity with tag filtering.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            ticker: Filter by specific ticker (optional)
            doc_type: Filter by document type (optional)
            tags: Filter by tags, e.g. {"sector": ["Technology"], "topic": ["AI"]}
            min_similarity: Minimum cosine similarity threshold
        
        Returns:
            List of matching documents with similarity scores and tags
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
                array_agg(
                    json_build_object(
                        'type', dt.tag_type,
                        'value', dt.tag_value,
                        'confidence', dt.confidence
                    )
                ) FILTER (WHERE dt.id IS NOT NULL) as tags
            FROM document_embeddings de
            LEFT JOIN document_tags dt ON de.id = dt.document_id
            WHERE 1=1
        """
        params = [query_embed["embedding"]]
        param_idx = 2
        
        if ticker:
            sql += f" AND de.ticker = ${param_idx}"
            params.append(ticker)
            param_idx += 1
        
        if doc_type:
            sql += f" AND de.doc_type = ${param_idx}"
            params.append(doc_type)
            param_idx += 1
        
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
        params.append(top_k)
        
        # Execute search
        rows = await self.db.fetch(sql, *params)
        
        # Filter by minimum similarity
        results = [
            {
                "id": row["id"],
                "ticker": row["ticker"],
                "doc_type": row["doc_type"],
                "content": row["content"],
                "metadata": row["metadata"],
                "similarity": row["similarity"],
                "document_date": row["document_date"],
                "created_at": row["created_at"],
                "tags": row["tags"] or []
            }
            for row in rows
            if row["similarity"] >= min_similarity
        ]
        
        return results
    
    async def get_incremental_updates_needed(self, ticker: str, doc_type: str) -> Optional[datetime]:
        """
        Check when incremental update is needed for a ticker/doc_type.
        
        Returns:
            Last document date if updates needed, None if up-to-date
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
    
    async def find_related_tickers(self, ticker: str, top_k: int = 10) -> List[Dict]:
        """
        Find tickers with similar document patterns (sector peers, supply chain).
        
        Uses tag co-occurrence analysis.
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
            WHERE (dt.tag_type, dt.tag_value) IN (SELECT tag_type, tag_value FROM ticker_tags)
                AND de.ticker != $1
            GROUP BY de.ticker
            ORDER BY shared_tags DESC
            LIMIT $2
        """, ticker, top_k)
        
        return [dict(r) for r in related]
    
    async def _add_tags(self, document_id: int, tags: List[Dict]):
        """Add tags to document."""
        for tag in tags:
            await self.db.execute("""
                INSERT INTO document_tags (document_id, tag_type, tag_value, confidence)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (document_id, tag_type, tag_value) DO NOTHING
            """, document_id, tag["type"], tag["value"], tag["confidence"])
    
    async def _update_sync_status(self, ticker: str, doc_type: str, document_date: datetime, cost: float):
        """Update incremental sync tracking."""
        await self.db.execute("""
            INSERT INTO document_sync_status 
                (ticker, doc_type, last_sync_date, last_document_date, documents_processed, total_cost_usd)
            VALUES ($1, $2, NOW(), $3, 1, $4)
            ON CONFLICT (ticker, doc_type) DO UPDATE SET
                last_sync_date = NOW(),
                last_document_date = GREATEST(document_sync_status.last_document_date, EXCLUDED.last_document_date),
                documents_processed = document_sync_status.documents_processed + 1,
                total_cost_usd = document_sync_status.total_cost_usd + EXCLUDED.total_cost_usd,
                updated_at = NOW()
        """, ticker, doc_type, document_date, cost)
    
    async def _track_cost(self, doc_count: int, tokens: int, cost: float):
        """Track embedding API costs to database."""
        await self.db.execute("""
            INSERT INTO embedding_costs (batch_id, doc_count, total_tokens, cost_usd)
            VALUES (gen_random_uuid(), $1, $2, $3)
        """, doc_count, tokens, cost)
```

#### C. TextChunker

```python
# backend/data/vector_store/chunker.py

from typing import List
import re

class TextChunker:
    """Split long documents into chunks for embedding."""
    
    @staticmethod
    def chunk_by_tokens(
        text: str,
        chunk_size: int = 4000,
        overlap: int = 200
    ) -> List[str]:
        """
        Split text into overlapping chunks by token count.
        
        OpenAI embedding models support up to 8191 tokens,
        but we use 4000 for better semantic coherence.
        """
        # Rough tokenization (1 token ≈ 0.75 words)
        words = text.split()
        tokens_per_word = 1.3
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(words):
            # Calculate end index
            end_idx = start_idx + int(chunk_size / tokens_per_word)
            chunk_words = words[start_idx:end_idx]
            
            chunks.append(" ".join(chunk_words))
            
            # Move start with overlap
            start_idx = end_idx - int(overlap / tokens_per_word)
        
        return chunks
    
    @staticmethod
    def chunk_by_sections(text: str, section_headers: List[str]) -> List[Dict]:
        """
        Split SEC filing by sections (e.g., "Risk Factors", "MD&A").
        
        Returns:
            [
                {"section": "Risk Factors", "content": "..."},
                {"section": "MD&A", "content": "..."},
                ...
            ]
        """
        chunks = []
        
        for i, header in enumerate(section_headers):
            # Find section start
            pattern = re.compile(rf"(?i)^{header}", re.MULTILINE)
            match = pattern.search(text)
            
            if not match:
                continue
            
            start_idx = match.start()
            
            # Find next section (or end of document)
            if i + 1 < len(section_headers):
                next_pattern = re.compile(rf"(?i)^{section_headers[i+1]}", re.MULTILINE)
                next_match = next_pattern.search(text, start_idx + 1)
                end_idx = next_match.start() if next_match else len(text)
            else:
                end_idx = len(text)
            
            content = text[start_idx:end_idx].strip()
            
            chunks.append({
                "section": header,
                "content": content
            })
        
        return chunks
```

#### D. AutoTagger

```python
# backend/data/vector_store/tagger.py

from typing import List, Dict, Optional
import re
from anthropic import AsyncAnthropic

class AutoTagger:
    """
    Automatic tag generation for documents using Claude API.
    
    Generates multi-dimensional tags:
    - Ticker tags: Stock symbols mentioned
    - Sector tags: Industry sectors (Technology, Healthcare, etc.)
    - Topic tags: Key themes (supply_chain, regulatory_risk, AI_adoption)
    - Entity tags: Named entities (CEO names, products, geographic regions)
    """
    
    # Predefined sector taxonomy
    SECTORS = [
        "Technology", "Healthcare", "Financials", "Consumer Discretionary",
        "Communication Services", "Industrials", "Consumer Staples",
        "Energy", "Utilities", "Real Estate", "Materials"
    ]
    
    # Predefined topic taxonomy
    TOPICS = [
        "supply_chain", "regulatory_risk", "legal_risk", "labor_dispute",
        "AI_adoption", "cybersecurity", "ESG", "M&A", "earnings_miss",
        "product_launch", "leadership_change", "market_expansion"
    ]
    
    def __init__(self, claude_client: AsyncAnthropic, use_ai: bool = True):
        self.claude = claude_client
        self.use_ai = use_ai
    
    async def generate_tags(
        self,
        content: str,
        primary_ticker: str,
        doc_type: str
    ) -> List[Dict]:
        """
        Generate comprehensive tags for a document.
        
        Returns:
            [
                {"type": "ticker", "value": "AAPL", "confidence": 1.0},
                {"type": "sector", "value": "Technology", "confidence": 0.95},
                {"type": "topic", "value": "supply_chain", "confidence": 0.87},
                {"type": "entity", "value": "Tim Cook", "confidence": 0.92},
                ...
            ]
        """
        tags = []
        
        # 1. Ticker tags (rule-based + AI)
        ticker_tags = await self._extract_ticker_tags(content, primary_ticker)
        tags.extend(ticker_tags)
        
        # 2. Sector tags (AI-based if enabled, else rule-based)
        sector_tags = await self._extract_sector_tags(content, primary_ticker)
        tags.extend(sector_tags)
        
        # 3. Topic tags (hybrid: rule-based + AI validation)
        topic_tags = await self._extract_topic_tags(content)
        tags.extend(topic_tags)
        
        # 4. Entity tags (AI-based for NER)
        if self.use_ai:
            entity_tags = await self._extract_entity_tags(content)
            tags.extend(entity_tags)
        
        return tags
    
    async def _extract_ticker_tags(self, content: str, primary_ticker: str) -> List[Dict]:
        """Extract stock ticker mentions."""
        tags = [{"type": "ticker", "value": primary_ticker, "confidence": 1.0}]
        
        # Regex for ticker symbols (1-5 uppercase letters)
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        mentioned_tickers = set(re.findall(ticker_pattern, content))
        
        # Filter out common false positives
        exclude_words = {"CEO", "CFO", "SEC", "FDA", "USA", "NYSE", "NASDAQ", "ETF"}
        mentioned_tickers = mentioned_tickers - exclude_words - {primary_ticker}
        
        for ticker in mentioned_tickers:
            tags.append({"type": "ticker", "value": ticker, "confidence": 0.7})
        
        return tags
    
    async def _extract_sector_tags(self, content: str, ticker: str) -> List[Dict]:
        """Extract sector tags."""
        if not self.use_ai:
            # Rule-based fallback
            for sector in self.SECTORS:
                if sector.lower() in content.lower():
                    return [{"type": "sector", "value": sector, "confidence": 0.8}]
            return []
        
        # AI-based sector classification
        prompt = f"""Classify the following document into ONE primary sector from this list:
{', '.join(self.SECTORS)}

Document excerpt:
{content[:2000]}

Respond with ONLY the sector name, nothing else."""

        response = await self.claude.messages.create(
            model="claude-haiku-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        
        sector = response.content[0].text.strip()
        
        if sector in self.SECTORS:
            return [{"type": "sector", "value": sector, "confidence": 0.95}]
        
        return []
    
    async def _extract_topic_tags(self, content: str) -> List[Dict]:
        """Extract topic tags using keyword matching + AI validation."""
        tags = []
        
        # Rule-based keyword matching
        topic_keywords = {
            "supply_chain": ["supply chain", "supplier", "logistics", "shortage", "inventory"],
            "regulatory_risk": ["regulation", "compliance", "FDA", "SEC", "antitrust"],
            "legal_risk": ["lawsuit", "litigation", "settlement", "penalty", "investigation"],
            "labor_dispute": ["strike", "union", "labor", "workforce", "employee relations"],
            "AI_adoption": ["artificial intelligence", "machine learning", "AI", "automation"],
            "cybersecurity": ["cyber", "data breach", "hack", "security incident"],
            "ESG": ["environmental", "sustainability", "carbon", "ESG", "climate"],
            "M&A": ["merger", "acquisition", "takeover", "buyout"],
            "earnings_miss": ["earnings miss", "revenue below", "guidance cut"],
            "product_launch": ["new product", "launch", "release", "unveil"],
            "leadership_change": ["CEO", "resignation", "appointed", "successor"],
            "market_expansion": ["expansion", "new market", "international", "geographic"]
        }
        
        content_lower = content.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append({"type": "topic", "value": topic, "confidence": 0.85})
        
        return tags
    
    async def _extract_entity_tags(self, content: str) -> List[Dict]:
        """Extract named entities using Claude API."""
        if not self.use_ai:
            return []
        
        prompt = f"""Extract important named entities from this document.
Focus on:
- Executive names (CEO, CFO, etc.)
- Product names
- Geographic regions
- Company names

Document excerpt:
{content[:2000]}

Respond with ONLY a comma-separated list of entities, nothing else.
Example: Tim Cook, iPhone 15, China, Apple Inc."""

        response = await self.claude.messages.create(
            model="claude-haiku-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        entities_text = response.content[0].text.strip()
        entities = [e.strip() for e in entities_text.split(",") if e.strip()]
        
        tags = []
        for entity in entities[:10]:  # Limit to top 10
            tags.append({"type": "entity", "value": entity, "confidence": 0.9})
        
        return tags
```

#### C. TextChunker

```python
# backend/data/vector_store/chunker.py

from typing import List
import re

class TextChunker:
    """Split long documents into chunks for embedding."""
    
    @staticmethod
    def chunk_by_tokens(
        text: str,
        chunk_size: int = 4000,
        overlap: int = 200
    ) -> List[str]:
        """
        Split text into overlapping chunks by token count.
        
        OpenAI embedding models support up to 8191 tokens,
        but we use 4000 for better semantic coherence.
        """
        # Rough tokenization (1 token ≈ 0.75 words)
        words = text.split()
        tokens_per_word = 1.3
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(words):
            # Calculate end index
            end_idx = start_idx + int(chunk_size / tokens_per_word)
            chunk_words = words[start_idx:end_idx]
            
            chunks.append(" ".join(chunk_words))
            
            # Move start with overlap
            start_idx = end_idx - int(overlap / tokens_per_word)
        
        return chunks
    
    @staticmethod
    def chunk_by_sections(text: str, section_headers: List[str]) -> List[Dict]:
        """
        Split SEC filing by sections (e.g., "Risk Factors", "MD&A").
        
        Returns:
            [
                {"section": "Risk Factors", "content": "..."},
                {"section": "MD&A", "content": "..."},
                ...
            ]
        """
        chunks = []
        
        for i, header in enumerate(section_headers):
            # Find section start
            pattern = re.compile(rf"(?i)^{header}", re.MULTILINE)
            match = pattern.search(text)
            
            if not match:
                continue
            
            start_idx = match.start()
            
            # Find next section (or end of document)
            if i + 1 < len(section_headers):
                next_pattern = re.compile(rf"(?i)^{section_headers[i+1]}", re.MULTILINE)
                next_match = next_pattern.search(text, start_idx + 1)
                end_idx = next_match.start() if next_match else len(text)
            else:
                end_idx = len(text)
            
            content = text[start_idx:end_idx].strip()
            
            chunks.append({
                "section": header,
                "content": content
            })
        
        return chunks
```

## 4. Integration Points

### 4.1 Risk Factor Integration

```python
# Modify: backend/data/features/non_standard_risk.py

class NonStandardRiskFactor:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        # ... existing code ...
    
    async def calculate(self, ticker: str, as_of_date: date) -> Dict:
        # ... existing keyword-based analysis ...
        
        # NEW: Add RAG-based analysis
        news_text = await self._get_recent_news(ticker)
        
        # Search for similar past risk events
        similar_events = await self.vector_store.search_similar(
            query=news_text,
            ticker=ticker,
            doc_type="news",
            top_k=5,
            min_similarity=0.85
        )
        
        # Calculate impact score based on historical outcomes
        historical_impact = self._analyze_historical_impact(similar_events)
        
        # Combine rule-based + RAG scores
        final_score = 0.5 * rule_based_score + 0.5 * historical_impact
        
        return {
            "score": final_score,
            "similar_events": similar_events[:3],  # Top 3 for explainability
            # ... existing fields ...
        }
```

### 4.2 Market Regime Integration

```python
# Modify: backend/ai/strategies/chatgpt_strategy.py

class ChatGPTStrategy:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        # ... existing code ...
    
    async def detect_regime(self) -> str:
        # ... existing logic ...
        
        # NEW: Compare with historical regimes
        current_conditions = f"VIX: {vix}, Fed Rate: {fed_rate}, CPI: {cpi}"
        
        similar_regimes = await self.vector_store.search_similar(
            query=current_conditions,
            doc_type="regime",
            top_k=3
        )
        
        # Extract regime types from metadata
        historical_regimes = [r["metadata"]["regime_type"] for r in similar_regimes]
        
        # Weight by similarity
        regime_votes = {}
        for i, regime in enumerate(historical_regimes):
            weight = similar_regimes[i]["similarity"]
            regime_votes[regime] = regime_votes.get(regime, 0) + weight
        
        # Return most likely regime
        predicted_regime = max(regime_votes, key=regime_votes.get)
        
        return predicted_regime
```

## 5. Data Ingestion Pipeline

### 5.1 SEC Filing Backfill Script with Incremental Updates

```python
# backend/scripts/backfill/embed_sec_filings.py

import asyncio
from datetime import datetime, timedelta
from backend.data.vector_store import VectorStore, DocumentEmbedder, TextChunker, AutoTagger
from backend.data.sec import SECEdgarAPI  # Existing module from Phase 15

async def backfill_sec_filings(
    tickers: List[str],
    years: int = 10,
    doc_types: List[str] = ["10-K", "10-Q"],
    incremental: bool = True
):
    """
    Download and embed historical SEC filings with incremental updates.
    
    Incremental mode:
    - Checks document_sync_status table for last processed document date
    - Only downloads NEW filings since last sync
    - Dramatically reduces API costs after initial backfill
    
    Estimated time (initial backfill):
    - 500 tickers × 10 years × 5 docs/year = 25,000 docs
    - At 100 docs/hour = 250 hours = 10 days
    
    Estimated cost (initial backfill):
    - 25,000 docs × 500 tokens/doc × $0.02/1M = $0.25
    
    Daily incremental cost:
    - ~10 new filings/day × 500 tokens × $0.02/1M = $0.0001/day = $0.003/month
    """
    sec_api = SECEdgarAPI()
    embedder = DocumentEmbedder(api_key=settings.OPENAI_API_KEY)
    
    # AI-powered auto-tagger (optional, uses Claude Haiku)
    claude_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    tagger = AutoTagger(claude_client, use_ai=True)
    
    vector_store = VectorStore(db_pool, embedder, tagger)
    chunker = TextChunker()
    
    total_cost = 0.0
    total_docs_processed = 0
    total_docs_skipped = 0
    
    for ticker in tickers:
        print(f"\n📊 Processing {ticker}...")
        
        for doc_type in doc_types:
            # Check if incremental update is needed
            if incremental:
                last_doc_date = await vector_store.get_incremental_updates_needed(ticker, doc_type)
                
                if last_doc_date:
                    print(f"  ⚡ Incremental mode: fetching {doc_type} after {last_doc_date.date()}")
                    start_date = last_doc_date + timedelta(days=1)
                else:
                    print(f"  🔄 Full backfill: fetching {doc_type} for {years} years")
                    start_date = datetime.now() - timedelta(days=years * 365)
            else:
                start_date = datetime.now() - timedelta(days=years * 365)
            
            # Get filings from SEC EDGAR
            filings = await sec_api.get_company_filings(
                ticker=ticker,
                form_types=[doc_type],
                start_date=start_date
            )
            
            print(f"  📄 Found {len(filings)} new {doc_type} filings")
            
            if not filings:
                print(f"  ✅ {ticker} {doc_type} is up-to-date")
                continue
            
            for filing in filings:
                try:
                    # Download full text
                    content = await sec_api.download_filing(filing["url"])
                    
                    # Extract key sections
                    sections = chunker.chunk_by_sections(content, [
                        "Risk Factors",
                        "Management's Discussion and Analysis",
                        "Business Overview",
                        "Financial Statements"
                    ])
                    
                    # Embed each section
                    for section in sections:
                        metadata = {
                            "filing_date": filing["filing_date"],
                            "form_type": filing["form_type"],
                            "section": section["section"],
                            "url": filing["url"],
                            "fiscal_year": filing.get("fiscal_year"),
                            "fiscal_quarter": filing.get("fiscal_quarter")
                        }
                        
                        # Add document with auto-tagging
                        doc_id = await vector_store.add_document(
                            ticker=ticker,
                            doc_type=filing["form_type"],
                            content=section["content"],
                            metadata=metadata,
                            document_date=filing["filing_date"],
                            auto_tag=True  # Generate tags automatically
                        )
                        
                        total_docs_processed += 1
                        
                        # Estimate cost (rough)
                        tokens = len(section["content"].split()) * 1.3
                        cost = (tokens / 1_000_000) * 0.02
                        total_cost += cost
                        
                        print(f"    ✓ {ticker} {filing['form_type']} - {section['section']} (${cost:.4f})")
                    
                    # Rate limiting (SEC allows 10 requests/second)
                    await asyncio.sleep(0.1)
                
                except Exception as e:
                    print(f"    ✗ Error processing {ticker} {filing['form_type']}: {e}")
                    continue
        
        # Show related tickers discovered through tagging
        related = await vector_store.find_related_tickers(ticker, top_k=5)
        if related:
            print(f"  🔗 Related tickers: {', '.join([r['ticker'] for r in related])}")
    
    print(f"\n✅ Backfill complete!")
    print(f"   📊 Documents processed: {total_docs_processed}")
    print(f"   ⏭️  Documents skipped (already exists): {total_docs_skipped}")
    print(f"   💰 Total cost: ${total_cost:.2f}")
    print(f"   📈 Average cost per doc: ${total_cost / max(total_docs_processed, 1):.4f}")

async def daily_incremental_update():
    """
    Run daily to fetch only NEW SEC filings.
    
    This is the key to cost optimization:
    - Initial backfill: $0.25 (one-time)
    - Daily updates: $0.0001/day = $0.003/month
    
    Schedule with cron:
    0 2 * * * cd /app && python -m backend.scripts.backfill.embed_sec_filings --incremental
    """
    print(f"🌅 Starting daily incremental update at {datetime.now()}")
    
    # Get all tickers being tracked
    tickers = await db.fetch("""
        SELECT DISTINCT ticker 
        FROM document_sync_status
        ORDER BY ticker
    """)
    
    ticker_list = [row["ticker"] for row in tickers]
    
    await backfill_sec_filings(
        tickers=ticker_list,
        years=1,  # Only look back 1 year max
        doc_types=["10-K", "10-Q", "8-K"],
        incremental=True  # Key: only fetch NEW documents
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Embed SEC filings with incremental updates")
    parser.add_argument("--incremental", action="store_true", help="Only fetch new documents")
    parser.add_argument("--tickers", nargs="+", help="Specific tickers to process")
    parser.add_argument("--years", type=int, default=10, help="Years of history to backfill")
    
    args = parser.parse_args()
    
    if args.tickers:
        ticker_list = args.tickers
    else:
        # Load S&P 500 top 100 by market cap
        import pandas as pd
        sp500 = pd.read_csv("data/sp500_constituents.csv")
        ticker_list = sp500.nlargest(100, "market_cap")["ticker"].tolist()
    
    asyncio.run(backfill_sec_filings(
        tickers=ticker_list,
        years=args.years,
        doc_types=["10-K", "10-Q"],
        incremental=args.incremental
    ))
```

## 6. Cost Optimization Strategies

### Strategy 1: Aggressive Caching
```python
# Cache embeddings to avoid re-computing
# 30-day TTL for embeddings (documents don't change)
# 7-day TTL for search results
```

### Strategy 2: Batch Processing
```python
# Embed 100 documents at once
# Total S&P 500: 500 tickers × 5 years × 8 docs/year = 20,000 docs
# Cost: 20,000 × 500 tokens × $0.02 / 1M = $0.20 (one-time)
```

### Strategy 3: Incremental Updates
```python
# Only embed NEW filings (daily check)
# ~500 new filings per day across S&P 500
# Daily cost: 500 × 500 tokens × $0.02 / 1M = $0.005/day = $0.15/month
```

### Strategy 4: Selective Embedding
```python
# Don't embed entire documents - only key sections
# 10-K full: 50,000 tokens → $1.00
# 10-K sections: 5,000 tokens → $0.10 (90% savings)
```

## 7. Testing Strategy

### Unit Tests
```python
# tests/test_vector_store.py

@pytest.mark.asyncio
async def test_embedding_api():
    embedder = DocumentEmbedder(api_key=settings.OPENAI_API_KEY)
    result = await embedder.embed_text("Tesla Q3 earnings miss")
    
    assert len(result["embedding"]) == 1536
    assert result["tokens"] > 0
    assert result["cost"] < 0.001  # < $0.001 per request

@pytest.mark.asyncio
async def test_vector_search():
    # Insert test document
    await vector_store.add_document(
        ticker="TSLA",
        doc_type="10-K",
        content="Risk Factors: Supply chain disruptions...",
        metadata={"year": 2023}
    )
    
    # Search
    results = await vector_store.search_similar(
        query="supply chain problems",
        top_k=5
    )
    
    assert len(results) > 0
    assert results[0]["ticker"] == "TSLA"
    assert results[0]["similarity"] > 0.8

@pytest.mark.asyncio
async def test_cost_tracking():
    # Embed 100 documents
    for i in range(100):
        await vector_store.add_document(
            ticker="TEST",
            doc_type="news",
            content=f"Test document {i}",
            metadata={}
        )
    
    # Check total cost
    total_cost = await db.fetchval(
        "SELECT SUM(cost_usd) FROM embedding_costs WHERE created_at > NOW() - INTERVAL '1 hour'"
    )
    
    assert total_cost < 0.1  # Should be well under $0.10
```

### Integration Tests
```python
# tests/test_rag_integration.py

@pytest.mark.asyncio
async def test_risk_factor_with_rag():
    risk_factor = NonStandardRiskFactor(vector_store)
    
    result = await risk_factor.calculate("AAPL", date.today())
    
    assert "similar_events" in result
    assert len(result["similar_events"]) <= 3
    assert result["score"] >= 0 and result["score"] <= 1
```

## 8. Deployment Plan

### Week 1: Infrastructure
- [ ] Day 1-2: Install pgvector on TimescaleDB
- [ ] Day 3-4: Create tables and indexes
- [ ] Day 5: Implement DocumentEmbedder + VectorStore
- [ ] Day 6-7: Write unit tests

### Week 2: Data Ingestion
- [ ] Day 8-9: Implement SEC backfill script
- [ ] Day 10-11: Run backfill for 10 sample tickers
- [ ] Day 12-13: Integrate with existing modules
- [ ] Day 14: Performance testing and optimization

## 9. Success Metrics

### Technical Metrics
- [ ] pgvector index created successfully
- [ ] Vector search p95 latency < 100ms
- [ ] Embedding API success rate > 99%
- [ ] Daily cost < $0.10

### Business Metrics
- [ ] False positive reduction: 30% → 10%
- [ ] AI conviction improvement: +15%p
- [ ] Risk detection speed: 3 days → 1 day

---

**Created**: 2025-11-22
**Phase**: 7.5 (RAG Foundation)
**Next**: Generate tasks.md for implementation
