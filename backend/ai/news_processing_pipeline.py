"""
News Processing Pipeline

Orchestrates the complete news processing workflow:
1. AI Analysis (sentiment, impact, entities)
2. Auto-Tagging (structured tags)
3. Embedding Generation (vector representation)
4. RAG Indexing (searchable knowledge base)

Each step checks for duplicates to avoid reprocessing.

Author: AI Trading System
Date: 2025-12-20
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.data.news_models import NewsArticle
from backend.ai.news_intelligence_analyzer import NewsIntelligenceAnalyzer
from backend.ai.news_auto_tagger import NewsAutoTagger
from backend.ai.news_embedder import NewsEmbedder
import logging

logger = logging.getLogger(__name__)


class NewsProcessingPipeline:
    """
    Complete news processing pipeline
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.analyzer = NewsIntelligenceAnalyzer(db)
        self.tagger = NewsAutoTagger(db)
        self.embedder = NewsEmbedder(db)
    
    async def process_article(self, article_id: int) -> Dict[str, Any]:
        """
        Process a single article through the complete pipeline
        
        Args:
            article_id: Article ID
            
        Returns:
            Dictionary with processing results
        """
        results = {
            "article_id": article_id,
            "analyzed": False,
            "tagged": False,
            "embedded": False,
            "rag_indexed": False,
            "errors": [],
            "skipped": []
        }
        
        try:
            article = self.db.query(NewsArticle).get(article_id)
            if not article:
                results["errors"].append(f"Article {article_id} not found")
                return results
            
            # Step 1: AI Analysis
            if not article.analysis:
                try:
                    logger.info(f"[1/4] Analyzing article {article_id}...")
                    await self.analyzer.analyze_article(article)
                    results["analyzed"] = True
                    logger.info(f"✅ Analysis complete")
                except Exception as e:
                    error_msg = f"Analysis failed: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
                    return results  # Stop if analysis fails
            else:
                results["skipped"].append("analysis")
                logger.info(f"⏭️  Analysis already exists")
            
            # Step 2: Auto-Tagging
            if not article.has_tags:
                try:
                    logger.info(f"[2/4] Tagging article {article_id}...")
                    if self.tagger.apply_tags(article_id):
                        results["tagged"] = True
                        logger.info(f"✅ Tagging complete")
                    else:
                        results["skipped"].append("tagging")
                except Exception as e:
                    error_msg = f"Tagging failed: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            else:
                results["skipped"].append("tagging")
                logger.info(f"⏭️  Tagging already done")
            
            # Step 3: Embedding Generation
            if not article.has_embedding:
                try:
                    logger.info(f"[3/4] Generating embedding for article {article_id}...")
                    if self.embedder.generate_embedding(article_id):
                        results["embedded"] = True
                        logger.info(f"✅ Embedding complete")
                    else:
                        results["skipped"].append("embedding")
                except Exception as e:
                    error_msg = f"Embedding failed: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            else:
                results["skipped"].append("embedding")
                logger.info(f"⏭️  Embedding already exists")
            
            # Step 4: RAG Indexing (future implementation)
            # TODO: Implement RAG indexing to VectorStore
            results["rag_indexed"] = False
            results["skipped"].append("rag_indexing (not implemented)")
            
            logger.info(f"🎉 Pipeline complete for article {article_id}")
            logger.info(f"Results: {results}")
            
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    async def batch_process(self, limit: int = 10) -> Dict[str, Any]:
        """
        Process multiple unprocessed articles
        
        Args:
            limit: Maximum number of articles to process
            
        Returns:
            Batch processing results
        """
        from sqlalchemy import or_
        
        # Find articles that need processing
        articles = self.db.query(NewsArticle).filter(
            or_(
                NewsArticle.analysis == None,
                NewsArticle.has_tags == False,
                NewsArticle.has_embedding == False,
                NewsArticle.rag_indexed == False
            )
        ).limit(limit).all()
        
        logger.info(f"Found {len(articles)} articles to process (limit: {limit})")
        
        batch_results = {
            "total": len(articles),
            "processed": 0,
            "successes": [],
            "errors": []
        }
        
        for article in articles:
            try:
                result = await self.process_article(article.id)
                batch_results["successes"].append(result)
                batch_results["processed"] += 1
            except Exception as e:
                error_info = {
                    "article_id": article.id,
                    "error": str(e)
                }
                batch_results["errors"].append(error_info)
                logger.error(f"Failed to process article {article.id}: {e}")
        
        logger.info(f"Batch processing complete: {batch_results['processed']}/{batch_results['total']} successful")
        return batch_results
    
    def get_processing_status(self, article_id: int) -> Dict[str, bool]:
        """
        Get processing status for an article
        
        Args:
            article_id: Article ID
            
        Returns:
            Status dictionary
        """
        article = self.db.query(NewsArticle).get(article_id)
        if not article:
            return None
        
        return {
            "has_analysis": article.analysis is not None,
            "has_tags": article.has_tags,
            "has_embedding": article.has_embedding,
            "rag_indexed": article.rag_indexed
        }
