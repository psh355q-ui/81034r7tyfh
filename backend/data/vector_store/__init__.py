"""
Vector Store Module - RAG Foundation for AI Trading System.

Components:
- DocumentEmbedder: OpenAI Embedding API wrapper
- TextChunker: Document chunking strategies
- AutoTagger: AI-powered automatic tagging
- VectorStore: TimescaleDB + pgvector interface

Usage:
    from data.vector_store import VectorStore, DocumentEmbedder, AutoTagger
    
    # Initialize components
    embedder = DocumentEmbedder(api_key="sk-...")
    tagger = AutoTagger(claude_client, use_ai=True)
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

from .embedder import DocumentEmbedder, EmbeddingResult, DocumentEmbedderContext
from .chunker import TextChunker
from .tagger import AutoTagger
from .store import VectorStore, VectorStoreContext

__all__ = [
    "DocumentEmbedder",
    "EmbeddingResult",
    "DocumentEmbedderContext",
    "TextChunker",
    "AutoTagger",
    "VectorStore",
    "VectorStoreContext",
]

__version__ = "1.0.0"
