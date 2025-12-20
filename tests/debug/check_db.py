import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.data.news_models import get_db, NewsArticle

db = next(get_db())

# Check articles
articles = db.query(NewsArticle).all()
print(f"Total articles: {len(articles)}")

# Check analyzed
analyzed = [a for a in articles if a.analysis]
print(f"Analyzed articles: {len(analyzed)}")

if analyzed:
    print("\nAnalyzed articles:")
    for a in analyzed[:5]:
        print(f"  - ID {a.id}: {a.title[:60]}...")
        print(f"    has_tags: {a.has_tags}")
        print(f"    has_embedding: {a.has_embedding}")
else:
    print("\n❌ No analyzed articles found")
    print("Run AI analysis from http://localhost:3002/news first")
