"""
Direct test with full error output
"""
# Load .env FIRST
from dotenv import load_dotenv
load_dotenv()

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Check API key is loaded
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"API Key length: {len(api_key)}")
    print(f"API Key prefix: {api_key[:10]}...")

from backend.data.news_models import get_db, NewsArticle
from backend.data.news_analyzer import NewsDeepAnalyzer

db = next(get_db())

# Get first article
article = db.query(NewsArticle).first()
print(f"\nTesting article: {article.title[:80]}")
print(f"Content text length: {len(article.content_text) if article.content_text else 0}")
print(f"Content summary length: {len(article.content_summary) if article.content_summary else 0}")

# Try to analyze with FULL error output
try:
    print("\n" + "="*60)
    print("Creating analyzer...")
    analyzer = NewsDeepAnalyzer(db)
    print("Analyzer created successfully!")
    
    print("\nAttempting analysis...")
    result = analyzer.analyze_article(article)
    
    if result:
        print(f"\n✅ SUCCESS!")
        print(f"Sentiment: {result.sentiment_overall}")
        print(f"Score: {result.sentiment_score}")
        
        # Check DB
        db.refresh(article)
        if article.analysis:
            print(f"✅ Saved to DB!")
        else:
            print(f"❌ NOT saved to DB!")
    else:
        print(f"\n⚠️ Analysis returned None (article skipped)")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"\nError type: {type(e).__name__}")
    print(f"\nFull traceback:")
    import traceback
    traceback.print_exc()

db.close()
