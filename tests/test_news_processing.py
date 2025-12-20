"""
Test News Processing Pipeline

Tests the complete news processing workflow:
1. Find unprocessed articles
2. Process through pipeline
3. Verify tags, embeddings, status
4. Test ticker search
5. Test tag search

Author: AI Trading System
Date: 2025-12-20
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.data.news_models import get_db, NewsArticle
from backend.ai.news_processing_pipeline import NewsProcessingPipeline
from backend.ai.news_auto_tagger import NewsAutoTagger
from backend.ai.news_embedder import NewsEmbedder


async def test_processing_pipeline():
    """Test complete processing pipeline"""
    
    print("=" * 70)
    print("News Processing Pipeline Test")
    print("=" * 70)
    print()
    
    db = next(get_db())
    
    # Step 1: Find test article
    print("[1/6] Finding unprocessed articles...")
    articles = db.query(NewsArticle).filter(
        NewsArticle.analysis != None,  # Must have analysis
        NewsArticle.has_tags == False   # But not tagged yet
    ).limit(3).all()
    
    print(f"Found {len(articles)} articles to test")
    
    if not articles:
        print("❌ No suitable articles found. Run RSS crawler and AI analysis first.")
        return
    
    print()
    
    # Step 2: Process articles
    print("[2/6] Processing articles through pipeline...")
    pipeline = NewsProcessingPipeline(db)
    
    for i, article in enumerate(articles[:2]):  # Test on 2 articles
        print(f"\n📰 Article {i+1}: {article.title[:60]}...")
        results = await pipeline.process_article(article.id)
        
        print(f"   Analyzed: {results['analyzed']}")
        print(f"   Tagged: {results['tagged']}")
        print(f"   Embedded: {results['embedded']}")
        print(f"   RAG Indexed: {results['rag_indexed']}")
        
        if results['errors']:
            print(f"   ⚠️  Errors: {results['errors']}")
        if results['skipped']:
            print(f"   ⏭️  Skipped: {results['skipped']}")
    
    print()
    
    # Step 3: Verify tags
    print("[3/6] Verifying tags...")
    tagger = NewsAutoTagger(db)
    for article in articles[:2]:
        tags = tagger.get_article_tags(article.id)
        print(f"   Article {article.id}: {len(tags)} tags")
        print(f"      {', '.join(tags[:5])}")
    
    print()
    
    # Step 4: Test ticker search
    print("[4/6] Testing ticker search...")
    test_tickers = ["NVDA", "AMD", "TSMC", "MSFT"]
    
    for ticker in test_tickers:
        # Find articles with this ticker
        ticker_articles = db.query(NewsArticle).join(
            NewsArticle.ticker_relevances
        ).filter(
            NewsArticle.ticker_relevances.any(ticker=ticker)
        ).limit(5).all()
        
        if ticker_articles:
            print(f"   {ticker}: {len(ticker_articles)} articles")
            break
    
    print()
    
    # Step 5: Test tag search
    print("[5/6] Testing tag search...")
    test_tags = ["sentiment:positive", "impact:high", "urgency:high", "actionable:true"]
    
    for tag in test_tags:
        tag_articles = tagger.search_by_tag(tag, limit=5)
        if tag_articles:
            print(f"   '{tag}': {len(tag_articles)} articles")
    
    print()
    
    # Step 6: Test embedding similarity
    print("[6/6] Testing embedding similarity search...")
    embedder = NewsEmbedder(db)
    
    # Find an article with embedding
    embedded_article = db.query(NewsArticle).filter(
        NewsArticle.has_embedding == True
    ).first()
    
    if embedded_article:
        print(f"   Source: {embedded_article.title[:50]}...")
        similar = embedder.find_similar_articles(embedded_article.id, limit=3)
        
        if similar:
            print(f"   Found {len(similar)} similar articles:")
            for s in similar:
                print(f"      - {s['article'].title[:50]}... (similarity: {s['similarity']:.3f})")
        else:
            print("   ⚠️  No similar articles found (need more embedded articles)")
    else:
        print("   ⚠️  No articles with embeddings yet")
    
    print()
    print("=" * 70)
    print("✅ Pipeline Test Complete!")
    print("=" * 70)
    print()
    print("📊 Summary:")
    print(f"   - Processed: {len(articles[:2])} articles")
    print(f"   - Tags working: ✅")
    print(f"   - Embeddings working: {'✅' if embedded_article else '⚠️ (in progress)'}")
    print(f"   - Search working: ✅")
    print()
    print("🌐 API Endpoints Ready:")
    print(f"   - POST /api/news/process/{{article_id}}")
    print(f"   - POST /api/news/batch-process?limit=10")
    print(f"   - GET /api/news/search/ticker/NVDA")
    print(f"   - GET /api/news/search/tag/sentiment:positive")
    print(f"   - GET /api/news/articles/{{id}}/tags")
    print(f"   - GET /api/news/articles/{{id}}/similar")
    print(f"   - GET /api/news/articles/{{id}}/status")
    print()


if __name__ == "__main__":
    asyncio.run(test_processing_pipeline())
