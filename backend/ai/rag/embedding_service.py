
import os
import google.generativeai as genai
import logging
from sqlalchemy.orm import Session
from backend.database.vector_db import get_vector_session, engine
from backend.database.vector_models import NewsEmbedding
from backend.database.models import NewsArticle

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY not found in environment variables.")

genai.configure(api_key=GOOGLE_API_KEY)

EMBEDDING_MODEL = "models/text-embedding-004"

class EmbeddingService:
    def __init__(self):
        pass

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate 768-dim vector embedding for the given text using Gemini.
        """
        if not text or len(text.strip()) == 0:
            return []
            
        try:
            # task_type="retrieval_document" optimizes for storing in a DB for search
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document",
                title=None
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    def store_article_embedding(self, article_id: int, title: str, content: str, sector: str = None, tickers: str = None):
        """
        Generate embedding for an article and store it in Vector DB.
        Merges title + content for the embedding input.
        """
        # Prepare text to embed
        # We focus on Title + Content Summary (or full content if short)
        # Deep Reasoning prompt uses Title + Content, so we mimic that.
        combined_text = f"Title: {title}\n\nContent: {content}"
        
        # Truncate if too long (Gemini has limits, though huge, good to be safe)
        # Approx 8000 tokens limit typically for embedding models
        combined_text = combined_text[:20000] 

        embedding_vector = self.generate_embedding(combined_text)
        
        if not embedding_vector:
            logger.warning(f"Skipping storage for article {article_id} due to empty embedding.")
            return

        # Store in DB
        # Use simple session management for now
        with Session(engine) as db:
            # Check if exists
            existing = db.query(NewsEmbedding).filter(NewsEmbedding.article_id == article_id).first()
            
            if existing:
                logger.info(f"Updating embedding for article {article_id}")
                existing.embedding = embedding_vector
                existing.title = title
                existing.sector = sector
                existing.tickers = tickers
            else:
                logger.info(f"Creating new embedding for article {article_id}")
                new_embedding = NewsEmbedding(
                    article_id=article_id,
                    title=title,
                    embedding=embedding_vector,
                    # Optional metadata
                    sector=sector,
                    tickers=tickers
                )
                db.add(new_embedding)
            
            db.commit()
            logger.info(f"Successfully stored embedding for article {article_id}")

# Singleton instance
embedding_service = EmbeddingService()
