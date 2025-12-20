"""
Quick Setup Guide - Phase 20 Week 3-4

Step-by-step instructions to enable news processing features
"""

# ==============================================================================
# Step 1: Install Dependencies (1분)
# ==============================================================================

# In your activated venv:
pip install sentence-transformers

# This will download ~120MB model on first use


# ==============================================================================
# Step 2: Register New Router in main.py (1분)
# ==============================================================================

# 1. Open: backend/main.py
# 2. Find line 63-67 (news_router import section):

try:
    from backend.api.news_router import router as news_router
    NEWS_AVAILABLE = True
except ImportError as e:
    NEWS_AVAILABLE = False
    logger.warning(f"News router not available: {e}")

# 3. Replace with:

try:
    from backend.api.news_router import router as news_router
    from backend.api.news_processing_router import router as news_processing_router
    NEWS_AVAILABLE = True
except ImportError as e:
    NEWS_AVAILABLE = False
    logger.warning(f"News router not available: {e}")

# 4. Find line 284-286 (news_router registration):

if NEWS_AVAILABLE:
    app.include_router(news_router, prefix="/api")
    logger.info("News router registered")

# 5. Replace with:

if NEWS_AVAILABLE:
    app.include_router(news_router, prefix="/api")
    app.include_router(news_processing_router, prefix="/api")
    logger.info("News routers registered")


# ==============================================================================
# Step 3: Prepare Test Data (3-5분)
# ==============================================================================

# Test requires articles with AI analysis. Two options:

# Option A: Use existing data (if available)
# - Check if you have articles at: http://localhost:3002/news
# - If yes, click "AI 분석" button to analyze some articles

# Option B: Quick test setup
python -c "
from backend.data.news_models import get_db, NewsArticle
db = next(get_db())
articles = db.query(NewsArticle).limit(5).all()
print(f'Found {len(articles)} articles in database')
for a in articles:
    print(f'  - {a.id}: {a.title[:50]}... (analyzed: {a.analysis is not None})')
"


# ==============================================================================
# Step 4: Run Test (1분)
# ==============================================================================

python test_news_processing.py

# Expected output:
# - Processing 2 articles
# - Generating tags
# - Creating embeddings
# - Testing ticker search
# - Testing tag search
# - Testing similar articles


# ==============================================================================
# Step 5: Verify API Endpoints (1분)
# ==============================================================================

# Start backend server
python -m uvicorn backend.main:app --reload --port 3001

# Test endpoints:
# 1. Process article:
#    POST http://localhost:3001/api/news/process/1

# 2. Batch process:
#    POST http://localhost:3001/api/news/batch-process?limit=5

# 3. Ticker search:
#    GET http://localhost:3001/api/news/search/ticker/NVDA

# 4. Tag search:
#    GET http://localhost:3001/api/news/search/tag/sentiment:positive


# ==============================================================================
# Troubleshooting
# ==============================================================================

# Issue: "sentence-transformers not installed"
# Solution: pip install sentence-transformers

# Issue: "No suitable articles found"
# Solution: 
#   1. Go to http://localhost:3002/news
#   2. Click "RSS 크롤링" to get articles
#   3. Click "AI 분석" to analyze them
#   4. Re-run test

# Issue: "news_processing_router not found"
# Solution: Check main.py edits in Step 2

# Issue: Router import error
# Solution: Check backend/api/news_processing_router.py exists
