"""
Test news analyzer directly to see error
"""
from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing NewsDeepAnalyzer import...")
try:
    from backend.data.news_models import get_db, NewsArticle
    print("✅ news_models imported")
    
    from backend.data.news_analyzer import NewsDeepAnalyzer
    print("✅ NewsDeepAnalyzer imported")
    
    db = next(get_db())
    print("✅ DB connection established")
    
    analyzer = NewsDeepAnalyzer(db)
    print(f"✅ Analyzer created successfully!")
    print(f"   Model: {analyzer.model}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
