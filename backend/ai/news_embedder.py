"""
News Embedding Generator

Generates vector embeddings for news articles using sentence-transformers.
Uses free, offline model for cost-effective embedding generation.

Model: all-MiniLM-L6-v2 (384 dimensions, ~120KB)
Performance: Fast, accurate for semantic similarity

Author: AI Trading System
Date: 2025-12-20
"""

from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON
from backend.data.news_models import NewsArticle, Base
import logging
import json

logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not installed. Run: pip install sentence-transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = False


# New model for embeddings
class ArticleEmbedding(Base):
    """Article vector embeddings"""
    __tablename__ = "article_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), unique=True, nullable=False, index=True)
    embedding = Column(JSON, nullable=False)  # Store as JSON array
    model_name = Column(String(64), nullable=False)
    dimensions = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class NewsEmbedder:
    """
    Generate vector embeddings for news articles
    """
    
    MODEL_NAME = "all-MiniLM-L6-v2"
    DIMENSIONS = 384
    
    def __init__(self, db: Session):
        self.db = db
        self.model = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading embedding model: {self.MODEL_NAME}")
                self.model = SentenceTransformer(self.MODEL_NAME)
                logger.info("✅ Embedding model loaded")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
        else:
            logger.warning("Sentence transformers not available. Embedding disabled.")
    
    def create_embedding_text(self, article: NewsArticle) -> str:
        """
        Create text for embedding from article
        
        Combines: title + summary + top keywords
        
        Args:
            article: NewsArticle instance
            
        Returns:
            Combined text string
        """
        parts = [article.title]
        
        # Add content summary
        if article.content_summary:
            parts.append(article.content_summary)
        elif article.content_text:
            # Use first 500 chars if no summary
            parts.append(article.content_text[:500])
        
        # Add top keywords from analysis
        if article.analysis and article.analysis.keywords:
            keywords = " ".join(article.analysis.keywords[:10])
            parts.append(keywords)
        
        return " ".join(parts)
    
    def generate_embedding(self, article_id: int) -> bool:
        """
        Generate and save embedding for an article
        
        Args:
            article_id: Article ID
            
        Returns:
            True if embedding was generated, False otherwise
        """
        if not self.model:
            logger.error("Embedding model not available")
            return False
        
        try:
            article = self.db.query(NewsArticle).get(article_id)
            if not article:
                logger.error(f"Article {article_id} not found")
                return False
            
            # Skip if already has embedding
            if article.has_embedding:
                logger.info(f"Article {article_id} already has embedding")
                return False
            
            # Create embedding text
            text = self.create_embedding_text(article)
            logger.info(f"Generating embedding for article {article_id} ({len(text)} chars)")
            
            # Generate embedding
            embedding_vector = self.model.encode(text, convert_to_numpy=True)
            
            # Convert to list for JSON storage
            embedding_list = embedding_vector.tolist()
            
            # Save to database
            embedding_record = ArticleEmbedding(
                article_id=article_id,
                embedding=embedding_list,
                model_name=self.MODEL_NAME,
                dimensions=self.DIMENSIONS
            )
            self.db.add(embedding_record)
            
            # Set has_embedding flag
            article.has_embedding = True
            self.db.commit()
            
            logger.info(f"✅ Generated {self.DIMENSIONS}-D embedding for article {article_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for article {article_id}: {e}")
            self.db.rollback()
            return False
    
    def get_embedding(self, article_id: int) -> List[float]:
        """Get embedding vector for an article"""
        embedding_record = self.db.query(ArticleEmbedding).filter(
            ArticleEmbedding.article_id == article_id
        ).first()
        
        if embedding_record:
            return embedding_record.embedding
        return None
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        import numpy as np
        
        e1 = np.array(embedding1)
        e2 = np.array(embedding2)
        
        # Cosine similarity
        similarity = np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2))
        return float(similarity)
    
    def find_similar_articles(self, article_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar articles based on embedding similarity
        
        Args:
            article_id: Source article ID
            limit: Maximum number of results
            
        Returns:
            List of similar articles with similarity scores
        """
        # Get source embedding
        source_embedding = self.get_embedding(article_id)
        if not source_embedding:
            return []
        
        # Get all other embeddings
        all_embeddings = self.db.query(ArticleEmbedding).filter(
            ArticleEmbedding.article_id != article_id
        ).all()
        
        # Compute similarities
        similarities = []
        for emb_record in all_embeddings:
            similarity = self.compute_similarity(source_embedding, emb_record.embedding)
            similarities.append({
                "article_id": emb_record.article_id,
                "similarity": similarity
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Get article details for top results
        results = []
        for sim in similarities[:limit]:
            article = self.db.query(NewsArticle).get(sim["article_id"])
            if article:
                results.append({
                    "article": article,
                    "similarity": sim["similarity"]
                })
        
        return results
