"""
News Processing Pipeline for Historical Data Seeding.

Features:
- Sentiment Analysis (Ollama llama3.2:3b - 로컬 LLM)
- Named Entity Recognition (Ticker extraction)
- Text Embedding Generation (sentence-transformers - 로컬)
- Batch processing with progress tracking

Author: AI Trading System Team
Date: 2025-12-21
Updated: 2026-01-09 (Ollama integration)
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import os

try:
    from backend.config.settings import settings
    from backend.data.crawlers.multi_source_crawler import NewsArticle
    from backend.ai.llm import get_ollama_client, get_embedding_service
except ImportError:
    class MockSettings:
        use_local_llm = True
    settings = MockSettings()

    @dataclass
    class NewsArticle:
        title: str
        content: str
        url: str
        source: str
        source_category: str
        published_at: datetime
        tickers: List[str]
        tags: List[str]
        author: Optional[str] = None
        metadata: Optional[Dict] = None


logger = logging.getLogger(__name__)


@dataclass
class ProcessedNews:
    """Processed news article with NLP enhancements."""
    article: NewsArticle
    sentiment_score: float  # -1.0 (negative) to 1.0 (positive)
    sentiment_label: str    # "positive", "negative", "neutral"
    embedding: List[float]  # 1536-dim vector
    embedding_model: str
    processed_at: datetime
    processing_errors: List[str]

    def to_db_dict(self) -> Dict:
        """Convert to database-ready dict."""
        base = self.article.to_dict() if hasattr(self.article, 'to_dict') else {}
        return {
            **base,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "embedding": self.embedding,
            "embedding_model": self.embedding_model,
            "processed_at": self.processed_at
        }


class NewsProcessor:
    """
    News processing pipeline with NLP capabilities.

    Pipeline:
    1. Sentiment Analysis (Gemini)
    2. Embedding Generation (OpenAI)
    3. Batch processing with rate limiting
    """

    def __init__(self):
        """Initialize processors with local LLM."""
        self.logger = logging.getLogger(__name__)

        # Check if USE_LOCAL_LLM is enabled
        use_local = os.getenv('USE_LOCAL_LLM', 'true').lower() == 'true'
        
        if use_local:
            self.logger.info("🔧 Using local LLM (Ollama) and local embeddings")
            
            # Initialize Ollama client
            try:
                self.ollama_client = get_ollama_client()
                if not self.ollama_client.check_health():
                    self.logger.warning("⚠️ Ollama server not responding. Make sure Ollama is running.")
            except Exception as e:
                self.logger.error(f"Failed to initialize Ollama: {e}")
                self.ollama_client = None
            
            # Initialize local embedding service
            try:
                self.embedding_service = get_embedding_service()
                self.embedding_dimension = 384  # all-MiniLM-L6-v2
                self.logger.info(f"✅ Local embedding service ready ({self.embedding_dimension}D)")
            except Exception as e:
                self.logger.error(f"Failed to initialize local embeddings: {e}")
                self.embedding_service = None
        else:
            self.logger.warning("Local LLM disabled. Please set USE_LOCAL_LLM=true")
            self.ollama_client = None
            self.embedding_service = None
            self.embedding_dimension = 384

    async def process_batch(
        self,
        articles: List[NewsArticle],
        batch_size: int = 10
    ) -> List[ProcessedNews]:
        """
        Process a batch of news articles.

        Args:
            articles: List of NewsArticle objects
            batch_size: Number of articles to process concurrently

        Returns:
            List of ProcessedNews objects
        """
        self.logger.info(f"Processing {len(articles)} articles in batches of {batch_size}")

        processed = []

        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]

            tasks = [self.process_article(article) for article in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Processing error: {result}")
                elif result:
                    processed.append(result)

            self.logger.info(f"Processed {len(processed)}/{len(articles)} articles")

            # Rate limiting between batches
            await asyncio.sleep(4)  # 15 req/min = 4s between batches

        return processed

    async def process_article(self, article: NewsArticle) -> Optional[ProcessedNews]:
        """
        Process a single article through the full pipeline.

        Args:
            article: NewsArticle object

        Returns:
            ProcessedNews object or None if processing fails
        """
        errors = []

        try:
            # 1. Content Analysis (Sentiment + NER)
            analysis_result = await self.analyze_content(
                article.title, article.content
            )
            
            sentiment_score = analysis_result["score"]
            sentiment_label = analysis_result["label"]
            
            # Update article with extracted data
            article.tickers = analysis_result["tickers"]
            article.tags = analysis_result["tags"]

            # 2. Generate Embedding
            embedding = await self.generate_embedding(
                f"{article.title}. {article.content}"
            )

            if embedding is None:
                errors.append("Embedding generation failed")
                embedding = [0.0] * 1536  # Fallback empty embedding

            return ProcessedNews(
                article=article,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                embedding=embedding,
                embedding_model="all-MiniLM-L6-v2",  # 로컬 모델
                processed_at=datetime.now(),
                processing_errors=errors
            )

        except Exception as e:
            self.logger.error(f"Article processing failed: {e}")
            errors.append(str(e))
            return None

    async def analyze_content(
        self,
        title: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Analyze content using Ollama for Sentiment, Tickers, and Tags.

        Args:
            title: Article title
            content: Article content

        Returns:
            Dict with keys: score, label, tickers, tags
        """
        default_result = {
            "score": 0.0,
            "label": "neutral",
            "tickers": [],
            "tags": []
        }

        if not self.ollama_client:
            self.logger.warning("Ollama client not available, using default result")
            return default_result

        try:
            # Ollama를 사용한 분석
            analysis = self.ollama_client.analyze_news_sentiment(title, content)
            
            # Ollama 응답을 우리 형식으로 변환
            score = analysis.get('sentiment_score', 0.0)
            label = analysis.get('sentiment_overall', 'neutral')
            tickers = analysis.get('affected_tickers', [])
            tags = self.extract_topics(f"{title} {content}")
            
            # 감성 점수/라벨 검증
            score = max(-1.0, min(1.0, score))
            if label not in ["positive", "negative", "neutral"]:
                label = "neutral"
            
            return {
                "score": score,
                "label": label,
                "tickers": tickers,
                "tags": tags
            }

        except Exception as e:
            self.logger.error(f"Content analysis failed: {e}")
            return default_result

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate text embedding using local sentence-transformers.

        Args:
            text: Text to embed (title + content)

        Returns:
            384-dimensional embedding vector or None if failed
        """
        if not self.embedding_service:
            self.logger.warning("Embedding service not available")
            return None

        try:
            # Truncate text to 5000 chars (로컬 모델 한계 고려)
            text = text[:5000]

            # 동기 함수를 비동기로 실행
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.embedding_service.get_embedding,
                text
            )
            
            return embedding

        except Exception as e:
            self.logger.error(f"Local embedding generation failed: {e}")
            return None

    def extract_topics(self, text: str) -> List[str]:
        """
        Extract key topics/tags from text (simple keyword-based).

        Args:
            text: Text to analyze

        Returns:
            List of topic tags
        """
        topics = set()

        # Financial keywords
        keywords_map = {
            "earnings": ["earnings", "eps", "revenue", "profit"],
            "merger": ["merger", "acquisition", "m&a", "buyout"],
            "ipo": ["ipo", "initial public offering"],
            "dividend": ["dividend", "payout"],
            "bankruptcy": ["bankruptcy", "chapter 11"],
            "regulation": ["sec", "regulation", "compliance", "fine"],
            "lawsuit": ["lawsuit", "litigation", "settlement"],
            "product": ["product", "launch", "release"],
            "ceo": ["ceo", "chief executive", "management"],
            "layoff": ["layoff", "job cut", "restructuring"]
        }

        text_lower = text.lower()

        for topic, keywords in keywords_map.items():
            if any(kw in text_lower for kw in keywords):
                topics.add(topic)

        return list(topics)


# Standalone test
if __name__ == "__main__":
    import sys
    from datetime import timedelta

    async def test_processor():
        """Test the news processor."""
        print("=" * 80)
        print("News Processing Pipeline Test")
        print("=" * 80)
        print()

        # Create mock article
        mock_article = NewsArticle(
            title="Apple Reports Record Q4 Earnings, Stock Surges",
            content="Apple Inc. reported record earnings for Q4 2024, beating analyst expectations. The company's revenue increased 12% year-over-year to $95 billion, driven by strong iPhone sales and services growth.",
            url="https://example.com/article",
            source="Mock News",
            source_category="financial",
            published_at=datetime.now(),
            tickers=["AAPL"],
            tags=["earnings"],
            author="Test Author"
        )

        processor = NewsProcessor()

        print("Processing single article...")
        result = await processor.process_article(mock_article)

        if result:
            print(f"\n✅ Processing successful!")
            print(f"   Sentiment: {result.sentiment_label} ({result.sentiment_score:.2f})")
            print(f"   Embedding dim: {len(result.embedding)}")
            print(f"   Embedding model: {result.embedding_model}")
            print(f"   Processed at: {result.processed_at}")

            if result.processing_errors:
                print(f"   Errors: {result.processing_errors}")
        else:
            print("❌ Processing failed")

        print("\n" + "=" * 80)
        print("Test completed!")
        print("=" * 80)

    asyncio.run(test_processor())
