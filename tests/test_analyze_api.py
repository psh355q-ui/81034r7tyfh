import requests
import json

# Test analyze endpoint
print("Testing /api/news/analyze endpoint...")
response = requests.post("http://localhost:8001/api/news/analyze?max_count=1")

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Check DB after
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.data.news_models import get_db, NewsArticle

db = next(get_db())
analyzed = [a for a in db.query(NewsArticle).all() if a.analysis]
print(f"\nAnalyzed articles in DB: {len(analyzed)}")
