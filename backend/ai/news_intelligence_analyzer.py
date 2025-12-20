"""
News Intelligence Analyzer

AI-powered news analysis with Phase 1 optimizations
- Sentiment: POSITIVE/NEGATIVE/NEUTRAL/CHAOS
- Impact Score: 0-100
- Auto-tagging
- Gemini Flash (fast + cheap)
- Compression + Caching (90% cost reduction)
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging
import json
from sqlalchemy.orm import Session

# Phase 1 optimizations
try:
    from backend.ai.compression import get_compressor
    COMPRESSION_AVAILABLE = True
except ImportError:
    COMPRESSION_AVAILABLE = False
    logging.warning("⚠️  LLMLingua-2 not available")

try:
    from backend.caching import get_cache
    CACHING_AVAILABLE = True
except ImportError:
    CACHING_AVAILABLE = False
    logging.warning("⚠️  Semantic caching not available")

# Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("⚠️  Gemini not available")

from backend.data.news_models import NewsArticle, SessionLocal
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

class NewsSentiment(str, Enum):
    """News sentiment classification"""
    POSITIVE = "POSITIVE"      # Clear bullish
    NEGATIVE = "NEGATIVE"      # Clear bearish
    NEUTRAL = "NEUTRAL"        # Informational
    CHAOS = "CHAOS"            # Conflicting information


class NewsUrgency(str, Enum):
    """News urgency level"""
    IMMEDIATE = "IMMEDIATE"    # Act now
    HOURS = "HOURS"            # Act within hours
    DAYS = "DAYS"              # Monitor, act later


class NewsCategory(str, Enum):
    """News category"""
    EARNINGS = "EARNINGS"
    MACRO = "MACRO"
    GEOPOLITICAL = "GEOPOLITICAL"
    REGULATORY = "REGULATORY"
    PRODUCT = "PRODUCT"
    MERGER = "MERGER"
    PERSONNEL = "PERSONNEL"
    OTHER = "OTHER"


@dataclass
class NewsIntelligence:
    """News analysis result"""
    # Core Analysis
    sentiment: NewsSentiment
    impact_score: int          # 0-100
    confidence: float          # 0.0-1.0
    
    # Details
    related_tickers: List[str]
    keywords: List[str]
    tags: List[str]
    urgency: NewsUrgency
    category: NewsCategory
    reasoning: str
    
    # Meta
    analyzed_at: datetime
    model_used: str
    tokens_used: int
    cost_usd: float
    
    @property
    def sentiment_value(self) -> float:
        """Convert sentiment to numeric value"""
        mapping = {
            NewsSentiment.POSITIVE: 1.0,
            NewsSentiment.NEGATIVE: -1.0,
            NewsSentiment.NEUTRAL: 0.0,
            NewsSentiment.CHAOS: 0.0
        }
        return mapping.get(self.sentiment, 0.0)


# =============================================================================
# News Intelligence Analyzer
# =============================================================================

class NewsIntelligenceAnalyzer:
    """
    AI-powered news intelligence
    
    Phase 1 Integration:
    - LLMLingua-2: 40% token reduction
    - Semantic cache: 40% query elimination
    - Result: ~80% cost savings
    
    Model: Gemini Flash (fast + cheap)
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize analyzer
        
        Args:
            gemini_api_key: Gemini API key (or from env: GEMINI_API_KEY)
        """
        # Gemini setup
        if GEMINI_AVAILABLE:
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("Gemini not available")
        
        # Phase 1 optimizations
        self.compressor = get_compressor() if COMPRESSION_AVAILABLE else None
        self.cache = get_cache(
            distance_threshold=0.1,
            ttl=3600
        ) if CACHING_AVAILABLE else None
        
        logger.info(
            f"✅ News Intelligence Analyzer initialized\n"
            f"  - Gemini: {'✅' if self.model else '❌'}\n"
            f"  - Compression: {'✅' if self.compressor else '❌'}\n"
            f"  - Caching: {'✅' if self.cache else '❌'}"
        )
    
    async def analyze(
        self,
        article: NewsArticle,
        use_compression: bool = True,
        use_cache: bool = True
    ) -> NewsIntelligence:
        """
        Analyze news article
        
        Args:
            article: NewsArticle from DB
            use_compression: Use LLMLingua-2
            use_cache: Use semantic cache
        
        Returns:
            NewsIntelligence with sentiment, impact, tags
        """
        if not self.model:
            raise RuntimeError("Gemini model not available")
        
        # Cache key
        cache_key = f"news_intel:{article.id}:{article.url}"
        
        # Define analysis function
        async def generate_analysis() -> Dict:
            return await self._generate_analysis(article, use_compression)
        
        # Get from cache or generate
        if use_cache and self.cache:
            cached_result = await self.cache.get_or_generate(
                query=cache_key,
                generate_func=generate_analysis
            )
            analysis_data = cached_result['response']
            from_cache = (cached_result['source'] == 'cache')
            
            if from_cache:
                logger.info(f"💾 Cache hit for: {article.title[:50]}")
        else:
            analysis_data = await generate_analysis()
        
        # Convert to NewsIntelligence
        intelligence = NewsIntelligence(
            sentiment=NewsSentiment(analysis_data['sentiment']),
            impact_score=analysis_data['impact_score'],
            confidence=analysis_data['confidence'],
            related_tickers=analysis_data['related_tickers'],
            keywords=analysis_data['keywords'],
            tags=self.auto_tag(analysis_data),
            urgency=NewsUrgency(analysis_data['urgency']),
            category=NewsCategory(analysis_data['category']),
            reasoning=analysis_data['reasoning'],
            analyzed_at=datetime.now(),
            model_used=analysis_data.get('model_used', 'gemini-1.5-flash'),
            tokens_used=analysis_data.get('tokens_used', 0),
            cost_usd=analysis_data.get('cost_usd', 0.0)
        )
        
        return intelligence
    
    async def _generate_analysis(
        self,
        article: NewsArticle,
        use_compression: bool
    ) -> Dict:
        """Generate AI analysis"""
        
        # Prepare content
        content = article.content_text or article.content_summary or article.title
        original_length = len(content)
        
        # Step 1: Compress if available and content is long
        if use_compression and self.compressor and len(content) > 500:
            try:
                compressed = self.compressor.compress_news_article(
                    article_text=content,
                    query="Analyze market impact and sentiment"
                )
                content = compressed['compressed_prompt']
                compression_ratio = compressed['savings']
                
                logger.info(
                    f"📦 Compressed: {compressed['original_tokens']} → "
                    f"{compressed['compressed_tokens']} tokens ({compression_ratio:.1%})"
                )
            except Exception as e:
                logger.warning(f"Compression failed: {e}, using original")
                compression_ratio = 0.0
        else:
            compression_ratio = 0.0
        
        # Step 2: Build prompt
        prompt = self._build_analysis_prompt(article, content)
        
        # Step 3: Call Gemini
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,  # Consistent analysis
                    max_output_tokens=1000
                )
            )
            
            # Extract tokens used
            tokens_used = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens_used = (
                    response.usage_metadata.prompt_token_count +
                    response.usage_metadata.candidates_token_count
                )
            
            # Parse JSON response
            result = json.loads(response.text)
            result['tokens_used'] = tokens_used
            result['cost_usd'] = self._calculate_cost(tokens_used)
            result['model_used'] = 'gemini-1.5-flash'
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nResponse: {response.text}")
            # Return default analysis
            return self._default_analysis(article)
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._default_analysis(article)
    
    def _build_analysis_prompt(self, article: NewsArticle, content: str) -> str:
        """Build analysis prompt"""
        return f"""
Analyze this financial news and provide structured intelligence:

TITLE: {article.title}
SOURCE: {article.source}
PUBLISHED: {article.published_at}
CONTENT: {content}

Provide JSON response with this exact structure:
{{
  "sentiment": "POSITIVE|NEGATIVE|NEUTRAL|CHAOS",
  "impact_score": 0-100,
  "confidence": 0.0-1.0,
  "related_tickers": ["TICKER1", "TICKER2"],
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "urgency": "IMMEDIATE|HOURS|DAYS",
  "category": "EARNINGS|MACRO|GEOPOLITICAL|REGULATORY|PRODUCT|MERGER|PERSONNEL|OTHER",
  "reasoning": "Brief explanation (50 words max)"
}}

SCORING GUIDE:

Impact Score (how much this affects markets):
- 0-20: Noise (routine news, ignore)
- 21-50: General news (reference only)
- 51-80: Important (requires analysis)
- 81-100: Critical (immediate action needed)

Sentiment:
- POSITIVE: Clear bullish signal
- NEGATIVE: Clear bearish signal
- NEUTRAL: Factual information, no clear direction
- CHAOS: Conflicting or confusing information

Urgency:
- IMMEDIATE: Act within minutes
- HOURS: Act within hours
- DAYS: Monitor, decision in days

Category: Choose the most relevant category

Only return JSON, no other text.
"""
    
    def _default_analysis(self, article: NewsArticle) -> Dict:
        """Fallback analysis when AI fails"""
        return {
            'sentiment': 'NEUTRAL',
            'impact_score': 30,
            'confidence': 0.5,
            'related_tickers': article.keywords or [],
            'keywords': article.keywords or [],
            'urgency': 'DAYS',
            'category': 'OTHER',
            'reasoning': 'AI analysis unavailable, default values used',
            'tokens_used': 0,
            'cost_usd': 0.0,
            'model_used': 'fallback'
        }
    
    def _calculate_cost(self, tokens: int) -> float:
        """
        Calculate Gemini Flash cost
        
        Pricing: $0.075 per 1M input tokens, $0.30 per 1M output tokens
        Estimate: 80% input, 20% output
        """
        input_tokens = int(tokens * 0.8)
        output_tokens = int(tokens * 0.2)
        
        input_cost = (input_tokens / 1_000_000) * 0.075
        output_cost = (output_tokens / 1_000_000) * 0.30
        
        return input_cost + output_cost
    
    def auto_tag(self, analysis: Dict) -> List[str]:
        """
        Auto-tag news based on analysis
        
        Tags used for filtering and RAG metadata
        """
        tags = []
        
        # Event type tags
        category = analysis.get('category', '').lower()
        if category:
            tags.append(category)
        
        # Impact tags
        impact = analysis.get('impact_score', 0)
        if impact >= 80:
            tags.append('critical')
        elif impact >= 50:
            tags.append('important')
        else:
            tags.append('low_impact')
        
        # Sentiment tags
        sentiment = analysis.get('sentiment', '').lower()
        if sentiment:
            tags.append(f"sent_{sentiment}")
        
        # Urgency tags
        urgency = analysis.get('urgency', '').lower()
        if urgency:
            tags.append(f"urgency_{urgency}")
        
        # Keyword-based tags
        keywords = analysis.get('keywords', [])
        for kw in keywords[:5]:  # Top 5 keywords
            clean_kw = kw.lower().replace(' ', '_')
            tags.append(clean_kw)
        
        return tags


# =============================================================================
# Utility Functions
# =============================================================================

async def analyze_article(article_id: int, db: Session = None) -> Optional[NewsIntelligence]:
    """Analyze single article by ID"""
    db = db or SessionLocal()
    
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        logger.error(f"Article {article_id} not found")
        return None
    
    analyzer = NewsIntelligenceAnalyzer()
    intelligence = await analyzer.analyze(article)
    
    logger.info(
        f"✅ Analysis complete:\n"
        f"  Sentiment: {intelligence.sentiment.value}\n"
        f"  Impact: {intelligence.impact_score}/100\n"
        f"  Urgency: {intelligence.urgency.value}\n"
        f"  Cost: ${intelligence.cost_usd:.4f}"
    )
    
    return intelligence


# =============================================================================
# Test/Demo
# =============================================================================

async def test_analyzer():
    """Test news intelligence analyzer"""
    print("🧪 Testing News Intelligence Analyzer\n")
    
    db = SessionLocal()
    
    # Get recent news
    recent = db.query(NewsArticle).order_by(
        NewsArticle.crawled_at.desc()
    ).limit(3).all()
    
    if not recent:
        print("❌ No news articles found in DB")
        print("Run Finviz collector first!")
        return
    
    analyzer = NewsIntelligenceAnalyzer()
    
    for article in recent:
        print(f"\n{'='*60}")
        print(f"Title: {article.title}")
        print(f"Source: {article.source}")
        print(f"{'='*60}")
        
        intelligence = await analyzer.analyze(article)
        
        print(f"\n📊 Analysis:")
        print(f"  Sentiment: {intelligence.sentiment.value}")
        print(f"  Impact Score: {intelligence.impact_score}/100")
        print(f"  Confidence: {intelligence.confidence:.2f}")
        print(f"  Urgency: {intelligence.urgency.value}")
        print(f"  Category: {intelligence.category.value}")
        print(f"  Tickers: {', '.join(intelligence.related_tickers)}")
        print(f"  Keywords: {', '.join(intelligence.keywords[:5])}")
        print(f"  Tags: {', '.join(intelligence.tags[:5])}")
        print(f"\n  Reasoning: {intelligence.reasoning}")
        print(f"\n  💰 Cost: ${intelligence.cost_usd:.4f} ({intelligence.tokens_used} tokens)")
    
    db.close()


if __name__ == "__main__":
    asyncio.run(test_analyzer())
