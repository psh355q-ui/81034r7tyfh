"""
News Auto-Tagging Module

Converts AI analysis results into structured tags for better organization and searchability.

Tag Categories:
- sentiment: positive, negative, neutral, mixed
- impact: high, medium, low
- urgency: critical, high, medium, low
- ticker: NVDA, AMD, TSMC, etc.
- keyword: AI, GPU, earnings, etc.
- actionable: true/false

Author: AI Trading System
Date: 2025-12-20
"""

from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from backend.data.news_models import NewsArticle, NewsAnalysis, NewsTickerRelevance, Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
import logging

logger = logging.getLogger(__name__)


# New model for tags
class ArticleTag(Base):
    """Article tags for organization"""
    __tablename__ = "article_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False, index=True)
    tag = Column(String(128), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NewsAutoTagger:
    """
    Automatically generate structured tags from news analysis
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_tags(self, article: NewsArticle, analysis: NewsAnalysis) -> List[str]:
        """
        Generate tags from analysis results
        
        Args:
            article: NewsArticle instance
            analysis: NewsAnalysis instance
            
        Returns:
            List of tag strings
        """
        tags = []
        
        # 1. Sentiment tag
        if analysis.sentiment_overall:
            tags.append(f"sentiment:{analysis.sentiment_overall.lower()}")
        
        # 2. Impact tag
        if analysis.impact_magnitude is not None:
            if analysis.impact_magnitude > 0.7:
                tags.append("impact:high")
            elif analysis.impact_magnitude > 0.4:
                tags.append("impact:medium")
            else:
                tags.append("impact:low")
        
        # 3. Urgency tag
        if analysis.urgency:
            tags.append(f"urgency:{analysis.urgency.lower()}")
        
        # 4. Ticker tags (only high relevance)
        ticker_relevances = self.db.query(NewsTickerRelevance).filter(
            NewsTickerRelevance.article_id == article.id
        ).all()
        
        for ticker_rel in ticker_relevances:
            if ticker_rel.relevance > 0.5:
                tags.append(f"ticker:{ticker_rel.ticker}")
        
        # 5. Keyword tags (top 5)
        if analysis.keywords:
            for kw in analysis.keywords[:5]:
                tags.append(f"keyword:{kw.lower()}")
        
        # 6. Actionable tag
        if analysis.trading_actionable:
            tags.append("actionable:true")
        
        # 7. Market impact tags
        if analysis.market_impact_short:
            tags.append(f"short-impact:{analysis.market_impact_short.lower()}")
        if analysis.market_impact_long:
            tags.append(f"long-impact:{analysis.market_impact_long.lower()}")
        
        return list(set(tags))  # Remove duplicates
    
    def apply_tags(self, article_id: int) -> bool:
        """
        Apply tags to an article and set has_tags flag
        
        Args:
            article_id: Article ID
            
        Returns:
            True if tags were applied, False if already tagged or no analysis
        """
        try:
            article = self.db.query(NewsArticle).get(article_id)
            if not article:
                logger.error(f"Article {article_id} not found")
                return False
            
            # Skip if already tagged
            if article.has_tags:
                logger.info(f"Article {article_id} already tagged")
                return False
            
            # Need analysis first
            analysis = article.analysis
            if not analysis:
                logger.warning(f"Article {article_id} has no analysis yet")
                return False
            
            # Generate tags
            tags = self.generate_tags(article, analysis)
            logger.info(f"Generated {len(tags)} tags for article {article_id}")
            
            # Save tags to database
            for tag_name in tags:
                tag = ArticleTag(
                    article_id=article_id,
                    tag=tag_name
                )
                self.db.add(tag)
            
            # Set has_tags flag
            article.has_tags = True
            self.db.commit()
            
            logger.info(f"✅ Tagged article {article_id}: {tags}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to tag article {article_id}: {e}")
            self.db.rollback()
            return False
    
    def get_article_tags(self, article_id: int) -> List[str]:
        """Get all tags for an article"""
        tags = self.db.query(ArticleTag).filter(
            ArticleTag.article_id == article_id
        ).all()
        return [tag.tag for tag in tags]
    
    def search_by_tag(self, tag: str, limit: int = 20) -> List[NewsArticle]:
        """Search articles by tag"""
        article_ids = self.db.query(ArticleTag.article_id).filter(
            ArticleTag.tag == tag
        ).distinct().limit(limit).all()
        
        article_ids = [aid[0] for aid in article_ids]
        
        articles = self.db.query(NewsArticle).filter(
            NewsArticle.id.in_(article_ids)
        ).all()
        
        return articles
