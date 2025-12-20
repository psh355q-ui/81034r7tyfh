"""
DocumentEmbedder - OpenAI Embedding API wrapper with cost tracking.

Supports:
- Single text embedding
- Batch embedding with rate limiting
- Cost calculation
- Content hashing for deduplication
"""

from openai import AsyncOpenAI
from typing import List, Dict, Optional
import hashlib
import asyncio
from datetime import datetime


class EmbeddingResult:
    """Result of an embedding operation."""
    
    def __init__(self, embedding: List[float], tokens: int, cost: float):
        self.embedding = embedding
        self.tokens = tokens
        self.cost = cost
        self.timestamp = datetime.utcnow()


class DocumentEmbedder:
    """
    OpenAI Embedding API wrapper with cost tracking.
    
    Features:
    - Async API calls
    - Batch processing with rate limiting
    - Cost calculation ($0.02 per 1M tokens)
    - Content hashing for deduplication
    
    Usage:
        embedder = DocumentEmbedder(api_key="sk-...")
        result = await embedder.embed_text("Sample text")
        print(f"Embedding: {result.embedding[:5]}...")
        print(f"Cost: ${result.cost:.6f}")
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        cost_per_million_tokens: float = 0.02
    ):
        """
        Initialize DocumentEmbedder.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model name (default: text-embedding-3-small)
            cost_per_million_tokens: Cost per 1M tokens (default: $0.02)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.cost_per_million = cost_per_million_tokens
        
        # Rate limiting (OpenAI tier 1: 3,000 RPM)
        self.max_requests_per_minute = 3000
        self.request_interval = 60.0 / self.max_requests_per_minute  # ~0.02s
        
        # Stats
        self.total_tokens = 0
        self.total_cost = 0.0
        self.total_requests = 0
    
    async def embed_text(self, text: str) -> EmbeddingResult:
        """
        Embed single text string.
        
        Args:
            text: Text to embed
        
        Returns:
            EmbeddingResult with embedding vector, tokens, and cost
        
        Example:
            >>> result = await embedder.embed_text("Apple reports Q3 earnings")
            >>> len(result.embedding)
            1536
            >>> result.cost
            0.000026
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            tokens = response.usage.total_tokens
            cost = (tokens / 1_000_000) * self.cost_per_million
            
            # Update stats
            self.total_tokens += tokens
            self.total_cost += cost
            self.total_requests += 1
            
            return EmbeddingResult(
                embedding=embedding,
                tokens=tokens,
                cost=cost
            )
        
        except Exception as e:
            raise RuntimeError(f"Embedding API error: {e}")
    
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> List[EmbeddingResult]:
        """
        Embed batch of texts with rate limiting.
        
        OpenAI rate limits:
        - Tier 1: 3,000 RPM (requests per minute)
        - We batch 100 texts per request to stay under limit
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call (max 100)
            show_progress: Print progress updates
        
        Returns:
            List of EmbeddingResult objects
        
        Example:
            >>> texts = ["Text 1", "Text 2", ..., "Text 1000"]
            >>> results = await embedder.embed_batch(texts)
            >>> sum(r.cost for r in results)
            0.052
        """
        results = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            if show_progress:
                print(f"  Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)...")
            
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    encoding_format="float"
                )
                
                # Process each embedding in response
                for j, data in enumerate(response.data):
                    # Estimate tokens per text (rough approximation)
                    text_tokens = response.usage.total_tokens // len(batch)
                    cost = (text_tokens / 1_000_000) * self.cost_per_million
                    
                    results.append(EmbeddingResult(
                        embedding=data.embedding,
                        tokens=text_tokens,
                        cost=cost
                    ))
                
                # Update stats
                self.total_tokens += response.usage.total_tokens
                self.total_cost += (response.usage.total_tokens / 1_000_000) * self.cost_per_million
                self.total_requests += 1
                
                # Rate limiting: wait between batches
                if i + batch_size < len(texts):
                    await asyncio.sleep(self.request_interval * len(batch))
            
            except Exception as e:
                print(f"  ✗ Error in batch {batch_num}: {e}")
                # Add None for failed embeddings
                results.extend([None] * len(batch))
                continue
        
        if show_progress:
            print(f"  ✓ Completed {len(texts)} embeddings (${self.total_cost:.4f})")
        
        return results
    
    @staticmethod
    def hash_content(text: str) -> str:
        """
        Generate SHA256 hash for deduplication.
        
        Args:
            text: Text to hash
        
        Returns:
            64-character hex string
        
        Example:
            >>> DocumentEmbedder.hash_content("Hello world")
            '64ec88ca00b268e5ba1a35678a1b5316d212f4f366b2477232534a8aeca37f3c'
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def get_stats(self) -> Dict:
        """
        Get embedding statistics.
        
        Returns:
            Dictionary with total_tokens, total_cost, total_requests, avg_cost_per_request
        """
        return {
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "total_requests": self.total_requests,
            "avg_cost_per_request": round(
                self.total_cost / max(self.total_requests, 1), 6
            ),
            "model": self.model
        }
    
    async def test_connection(self) -> bool:
        """
        Test OpenAI API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            result = await self.embed_text("test")
            return len(result.embedding) == 1536
        except Exception as e:
            print(f"❌ OpenAI API connection failed: {e}")
            return False


# Async context manager support
class DocumentEmbedderContext:
    """Context manager for DocumentEmbedder."""
    
    def __init__(self, api_key: str, **kwargs):
        self.embedder = DocumentEmbedder(api_key, **kwargs)
    
    async def __aenter__(self):
        # Test connection on enter
        if not await self.embedder.test_connection():
            raise RuntimeError("Failed to connect to OpenAI API")
        return self.embedder
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Print stats on exit
        stats = self.embedder.get_stats()
        print(f"\n📊 Embedding Session Stats:")
        print(f"   Total Tokens: {stats['total_tokens']:,}")
        print(f"   Total Cost: ${stats['total_cost_usd']:.6f}")
        print(f"   Total Requests: {stats['total_requests']}")
        print(f"   Avg Cost/Request: ${stats['avg_cost_per_request']:.6f}")


if __name__ == "__main__":
    # Example usage
    import os
    
    async def test():
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ Set OPENAI_API_KEY environment variable")
            return
        
        async with DocumentEmbedderContext(api_key) as embedder:
            # Test single embedding
            result = await embedder.embed_text("Apple reports strong Q3 earnings")
            print(f"\n✅ Single embedding:")
            print(f"   Dimensions: {len(result.embedding)}")
            print(f"   Tokens: {result.tokens}")
            print(f"   Cost: ${result.cost:.6f}")
            
            # Test batch embedding
            texts = [
                "Tesla stock rises on delivery numbers",
                "Microsoft announces new AI features",
                "Google reports search revenue growth"
            ]
            results = await embedder.embed_batch(texts)
            print(f"\n✅ Batch embedding:")
            print(f"   Embeddings: {len(results)}")
            print(f"   Total cost: ${sum(r.cost for r in results):.6f}")
    
    asyncio.run(test())
