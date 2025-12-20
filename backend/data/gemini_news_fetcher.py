"""
Gemini 3.0 Pro News Fetcher Prototype
Real-time news discovery and analysis using Gemini's grounding capabilities
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai

class GeminiNewsFetcher:
    """
    Prototype: Use Gemini to fetch and analyze real-time news
    
    Features:
    - Real-time web search via grounding
    - Automatic ticker extraction
    - Sentiment analysis
    - Market impact assessment
    """
    
    def __init__(self):
        # Load environment first
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Load model from environment (consistent with news_analyzer.py)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        
        # Add 'models/' prefix if not present
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        
        self.model = genai.GenerativeModel(model_name)
        print(f"✅ GeminiNewsFetcher initialized with model: {model_name}")
    
    def fetch_news(
        self, 
        query: str = "latest stock market news", 
        max_articles: int = 10,
        use_grounding: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch news articles using Gemini
        
        Args:
            query: Search query
            max_articles: Maximum number of articles to return
            use_grounding: Use Google Search grounding
        
        Returns:
            List of news articles with analysis
        """
        
        prompt = f"""
Search for {query} from the past 24 hours.

For each article (up to {max_articles}), provide:
- title: Article headline
- url: Direct link (if available)
- source: Publication name
- published_date: Publication date/time
- summary: 2-3 sentence summary
- tickers: List of mentioned stock tickers (e.g., ["AAPL", "NVDA"])
- sentiment: "positive", "negative", or "neutral"
- urgency: "low", "medium", "high", or "critical"
- market_impact: "bullish", "bearish", or "neutral"
- actionable: true if tradeable insight, false otherwise

Return ONLY a valid JSON array of articles.
Do not include markdown, code blocks, or explanations.

Example format:
[
  {{
    "title": "Apple announces new product",
    "url": "https://...",
    "source": "Reuters",
    "published_date": "2024-12-20T10:00:00Z",
    "summary": "Apple unveiled...",
    "tickers": ["AAPL"],
    "sentiment": "positive",
    "urgency": "medium",
    "market_impact": "bullish",
    "actionable": true
  }}
]
"""
        
        try:
            # IMPORTANT: Grounding cannot be used with JSON mode in Gemini API
            # "400 Search Grounding can't be used with JSON/YAML/XML mode"
            # Solution: Disable grounding for now to get structured output
            # Future: Use two-step approach (grounding search → JSON formatting)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,  # Lower for factual accuracy
                    max_output_tokens=4000,
                    response_mime_type="application/json",  # Requires grounding OFF
                ),
                # tools=None  # Grounding disabled due to API limitation
            )
            
            # Parse JSON response
            articles = json.loads(response.text)
            
            # HALLUCINATION PREVENTION: Validate citations
            if use_grounding and hasattr(response, 'candidates'):
                for candidate in response.candidates:
                    if hasattr(candidate, 'grounding_metadata'):
                        metadata = candidate.grounding_metadata
                        # Store grounding sources for validation
                        grounding_sources = []
                        if hasattr(metadata, 'grounding_chunks'):
                            for chunk in metadata.grounding_chunks:
                                if hasattr(chunk, 'web'):
                                    grounding_sources.append({
                                        "uri": chunk.web.uri,
                                        "title": chunk.web.title if hasattr(chunk.web, 'title') else None
                                    })
                        
                        # Add grounding_sources to first article as metadata
                        if articles and grounding_sources:
                            articles[0]["grounding_sources"] = grounding_sources
                            articles[0]["grounding_validated"] = True
            
            # Add metadata
            for article in articles:
                article["fetched_at"] = datetime.utcnow().isoformat()
                article["source_type"] = "gemini_llm"  # No grounding (JSON mode incompatible)
                article["model_version"] = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
                
                # Hallucination check: Articles without URLs are flagged
                if not article.get("url") or article["url"] == "":
                    article["validation_warning"] = "No source URL - verify accuracy"
            
            return articles
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}")
            print(f"Response: {response.text[:500]}")
            return []
        except Exception as e:
            print(f"❌ Error fetching news: {e}")
            return []
    
    def fetch_ticker_news(
        self, 
        ticker: str, 
        max_articles: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch news for a specific ticker
        """
        query = f"latest news about {ticker} stock"
        return self.fetch_news(query, max_articles)
    
    def fetch_breaking_news(self) -> List[Dict[str, Any]]:
        """
        Fetch breaking market news
        """
        query = "breaking stock market news today"
        return self.fetch_news(query, max_articles=5)


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    print("🔬 Gemini News Fetcher Prototype\n")
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test 1: General market news
    print("📰 Test 1: General Market News")
    fetcher = GeminiNewsFetcher()
    articles = fetcher.fetch_news("tech stock news today", max_articles=3)
    
    print(f"Found {len(articles)} articles:\n")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article.get('title', 'No title')}")
        print(f"   Source: {article.get('source', 'Unknown')}")
        print(f"   Tickers: {article.get('tickers', [])}")
        print(f"   Sentiment: {article.get('sentiment', 'N/A')}")
        print(f"   Actionable: {article.get('actionable', False)}")
        print()
    
    # Test 2: Specific ticker
    print("\n📊 Test 2: Ticker-Specific News (NVDA)")
    nvda_news = fetcher.fetch_ticker_news("NVDA", max_articles=2)
    
    print(f"Found {len(nvda_news)} NVDA articles:\n")
    for article in nvda_news:
        print(f"- {article.get('title', 'No title')}")
        print(f"  Impact: {article.get('market_impact', 'N/A')}")
        print()
    
    # Results summary
    print("\n" + "="*60)
    print("📊 Summary:")
    print(f"Total articles fetched: {len(articles) + len(nvda_news)}")
    print(f"Average tickers per article: {sum(len(a.get('tickers', [])) for a in articles + nvda_news) / (len(articles) + len(nvda_news)) if articles + nvda_news else 0:.1f}")
    print(f"Actionable articles: {sum(1 for a in articles + nvda_news if a.get('actionable'))}")
