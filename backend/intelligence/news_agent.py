"""
NewsAgent

AI Agent for news-based trading opinions
- Participates in AI War Room debates
- Provides evidence from high-impact news
- Impact-weighted sentiment analysis
- Independent opinion alongside Technical/Fundamental/Risk agents
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.data.news_models import NewsArticle, SessionLocal
from backend.ai.news_intelligence_analyzer import (
    NewsIntelligenceAnalyzer,
    NewsIntelligence,
    NewsSentiment
)

logger = logging.getLogger(__name__)


# =============================================================================
# Agent Opinion Structure (matching existing debate system)
# =============================================================================

class AgentOpinion:
    """
    Standardized agent opinion for AI War Room
    
    Matches format expected by debate_engine.py
    """
    
    def __init__(
        self,
        agent_name: str,
        action: str,  # "BUY" | "SELL" | "HOLD"
        conviction: float,  # 0.0-1.0
        reasoning: str,
        evidence: Optional[List] = None
    ):
        self.agent_name = agent_name
        self.action = action
        self.conviction = conviction
        self.reasoning = reasoning
        self.evidence = evidence or []
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'agent_name': self.agent_name,
            'action': self.action,
            'conviction': self.conviction,
            'reasoning': self.reasoning,
            'evidence_count': len(self.evidence),
            'timestamp': self.timestamp.isoformat()
        }


# =============================================================================
# NewsAgent
# =============================================================================

class NewsAgent:
    """
    News-based AI Agent for trading decisions
    
    Role in AI War Room:
    - Provides independent opinion based on recent news
    - Weighs news by impact score
    - Aggregates sentiment from multiple sources
    - Highlights urgent/critical news
    
    Integration:
    - Integrates with existing debate_engine.py
    - Uses NewsIntelligenceAnalyzer for analysis
    - Queries news_articles table for recent news
    """
    
    def __init__(
        self,
        db: Session = None,
        lookback_days: int = 7,
        min_impact_score: int = 50
    ):
        """
        Initialize NewsAgent
        
        Args:
            db: Database session
            lookback_days: How far back to look for news (default 7 days)
            min_impact_score: Minimum impact score to consider (default 50)
        """
        self.db = db or SessionLocal()
        self.name = "NewsAgent"
        self.lookback_days = lookback_days
        self.min_impact_score = min_impact_score
        
        # For future: News intelligence analyzer
        # (Currently assuming news is pre-analyzed)
        self.analyzer = NewsIntelligenceAnalyzer()
        
        logger.info(
            f"✅ NewsAgent initialized\n"
            f"  - Lookback: {lookback_days} days\n"
            f"  - Min impact: {min_impact_score}/100"
        )
    
    async def analyze(
        self,
        ticker: str,
        context: Optional[Dict] = None
    ) -> AgentOpinion:
        """
        Generate news-based trading opinion
        
        Args:
            ticker: Stock ticker symbol
            context: Additional context (optional)
        
        Returns:
            AgentOpinion with action, conviction, reasoning
        """
        # Fetch relevant news
        news_items = self._fetch_recent_news(ticker)
        
        if not news_items:
            return self._no_news_opinion(ticker)
        
        # Calculate impact-weighted sentiment
        weighted_sentiment, total_impact = self._calculate_weighted_sentiment(news_items)
        
        # Determine action and conviction
        action, conviction = self._sentiment_to_action(
            weighted_sentiment,
            total_impact,
            len(news_items)
        )
        
        # Build reasoning with evidence
        reasoning = self._build_reasoning(
            ticker,
            news_items,
            weighted_sentiment,
            total_impact,
            action,
            conviction
        )
        
        logger.info(
            f"📰 NewsAgent opinion for {ticker}:\n"
            f"  Action: {action}\n"
            f"  Conviction: {conviction:.2f}\n"
            f"  News count: {len(news_items)}\n"
            f"  Weighted sentiment: {weighted_sentiment:.2f}"
        )
        
        return AgentOpinion(
            agent_name=self.name,
            action=action,
            conviction=conviction,
            reasoning=reasoning,
            evidence=news_items
        )
    
    def _fetch_recent_news(self, ticker: str) -> List[Dict]:
        """
        Fetch recent high-impact news for ticker
        
        Returns:
            List of news items with intelligence data
        """
        since = datetime.now() - timedelta(days=self.lookback_days)
        
        # Query news articles
        # For now, using keywords field to match ticker
        # Future: Use news_intelligence table with related_tickers
        articles = self.db.query(NewsArticle).filter(
            and_(
                NewsArticle.crawled_at >= since,
                NewsArticle.keywords.contains([ticker])  # SQLite JSON contains
            )
        ).order_by(
            NewsArticle.published_at.desc()
        ).limit(20).all()
        
        # Convert to intelligence format
        # TODO: Replace with actual news_intelligence table lookup
        news_items = []
        for article in articles:
            # Mock intelligence for now
            # In production, this would come from news_intelligence table
            news_items.append({
                'title': article.title,
                'source': article.source,
                'published_at': article.published_at,
                'sentiment': self._infer_sentiment(article.title),
                'impact_score': self._infer_impact(article),
                'url': article.url
            })
        
        # Filter by min impact
        high_impact = [
            n for n in news_items 
            if n['impact_score'] >= self.min_impact_score
        ]
        
        logger.info(
            f"📊 Found {len(articles)} news items, "
            f"{len(high_impact)} high-impact (>={self.min_impact_score})"
        )
        
        return high_impact
    
    def _infer_sentiment(self, title: str) -> float:
        """
        Infer sentiment from title (temporary)
        
        Returns: -1.0 (negative) to +1.0 (positive)
        
        TODO: Replace with actual NewsIntelligence lookup
        """
        title_lower = title.lower()
        
        # Positive keywords
        positive = ['beat', 'surge', 'rally', 'gain', 'approve', 'success', 
                   'record', 'upgrade', 'bullish']
        # Negative keywords
        negative = ['miss', 'fall', 'plunge', 'loss', 'reject', 'downgrade',
                   'bearish', 'warning', 'decline']
        
        pos_count = sum(1 for kw in positive if kw in title_lower)
        neg_count = sum(1 for kw in negative if kw in title_lower)
        
        if pos_count > neg_count:
            return 0.7
        elif neg_count > pos_count:
            return -0.7
        else:
            return 0.0
    
    def _infer_impact(self, article: NewsArticle) -> int:
        """
        Infer impact score (temporary)
        
        Returns: 0-100
        
        TODO: Replace with actual NewsIntelligence lookup
        """
        # Simple heuristic based on source
        major_sources = ['Bloomberg', 'Reuters', 'WSJ', 'CNBC']
        
        if any(src in article.source for src in major_sources):
            return 70
        elif article.source == 'finviz':
            return 60
        else:
            return 50
    
    def _calculate_weighted_sentiment(
        self,
        news_items: List[Dict]
    ) -> tuple[float, float]:
        """
        Calculate impact-weighted average sentiment
        
        Formula: sum(sentiment * impact) / sum(impact)
        
        Returns:
            (weighted_sentiment, total_impact)
        """
        if not news_items:
            return 0.0, 0.0
        
        weights = [item['impact_score'] for item in news_items]
        sentiments = [item['sentiment'] for item in news_items]
        
        weighted_avg = np.average(sentiments, weights=weights)
        total_impact = sum(weights)
        
        return weighted_avg, total_impact
    
    def _sentiment_to_action(
        self,
        weighted_sentiment: float,
        total_impact: float,
        news_count: int
    ) -> tuple[str, float]:
        """
        Convert weighted sentiment to trading action
        
        Args:
            weighted_sentiment: -1.0 to +1.0
            total_impact: Total impact score
            news_count: Number of news items
        
        Returns:
            (action, conviction)
        """
        # Base thresholds
        buy_threshold = 0.3
        sell_threshold = -0.3
        
        # Determine action
        if weighted_sentiment > buy_threshold:
            action = "BUY"
            base_conviction = abs(weighted_sentiment)
        elif weighted_sentiment < sell_threshold:
            action = "SELL"
            base_conviction = abs(weighted_sentiment)
        else:
            action = "HOLD"
            base_conviction = 0.6
        
        # Adjust conviction by impact and volume
        impact_factor = min(total_impact / (news_count * 100), 1.0)
        volume_factor = min(news_count / 5.0, 1.0)
        
        conviction = base_conviction * 0.7 + impact_factor * 0.2 + volume_factor * 0.1
        conviction = min(max(conviction, 0.0), 0.95)  # Cap at 0.95
        
        return action, conviction
    
    def _build_reasoning(
        self,
        ticker: str,
        news_items: List[Dict],
        weighted_sentiment: float,
        total_impact: float,
        action: str,
        conviction: float
    ) -> str:
        """Build human-readable reasoning"""
        
        # Summarize key events
        key_events = []
        for item in sorted(news_items, key=lambda x: x['impact_score'], reverse=True)[:3]:
            sentiment_label = "📈" if item['sentiment'] > 0 else "📉" if item['sentiment'] < 0 else "➡️"
            key_events.append(
                f"{sentiment_label} {item['title'][:60]}... (impact={item['impact_score']})"
            )
        
        # Build reasoning text
        reasoning = f"""
Based on {len(news_items)} high-impact news items from past {self.lookback_days} days:

Weighted Sentiment: {weighted_sentiment:+.2f} (-1.0 to +1.0)
Total Impact: {total_impact:.0f}
Average Impact: {total_impact/len(news_items):.0f}

Key Events:
{chr(10).join(f'  {e}' for e in key_events)}

Interpretation:
The news suggests {action} with {conviction:.0%} conviction.
{'Strong positive momentum' if weighted_sentiment > 0.5 else 
 'Strong negative momentum' if weighted_sentiment < -0.5 else
 'Mixed signals, neutral stance recommended'}.
""".strip()
        
        return reasoning
    
    def _no_news_opinion(self, ticker: str) -> AgentOpinion:
        """Opinion when no significant news found"""
        return AgentOpinion(
            agent_name=self.name,
            action="HOLD",
            conviction=0.5,
            reasoning=f"No significant news found for {ticker} in past {self.lookback_days} days "
                     f"(min impact score: {self.min_impact_score}). "
                     f"Recommending HOLD until more information available."
        )


# =============================================================================
# Integration Helper
# =============================================================================

async def get_news_opinion(
    ticker: str,
    db: Session = None,
    lookback_days: int = 7,
    min_impact: int = 50
) -> AgentOpinion:
    """
    Quick helper to get NewsAgent opinion
    
    Usage in debate_engine.py:
        from backend.intelligence.news_agent import get_news_opinion
        
        news_opinion = await get_news_opinion(ticker, db)
    """
    agent = NewsAgent(db=db, lookback_days=lookback_days, min_impact_score=min_impact)
    return await agent.analyze(ticker)


# =============================================================================
# Test/Demo
# =============================================================================

async def test_news_agent():
    """Test NewsAgent"""
    print("🧪 Testing NewsAgent\n")
    
    db = SessionLocal()
    agent = NewsAgent(db=db)
    
    # Test with sample tickers
    test_tickers = ['AAPL', 'TSLA', 'NVDA']
    
    for ticker in test_tickers:
        print(f"\n{'='*60}")
        print(f"Testing: {ticker}")
        print(f"{'='*60}")
        
        opinion = await agent.analyze(ticker)
        
        print(f"\n📊 NewsAgent Opinion:")
        print(f"  Action: {opinion.action}")
        print(f"  Conviction: {opinion.conviction:.2%}")
        print(f"  Evidence: {len(opinion.evidence)} news items")
        print(f"\n  Reasoning:")
        for line in opinion.reasoning.split('\n'):
            print(f"    {line}")
    
    db.close()


if __name__ == "__main__":
    asyncio.run(test_news_agent())
