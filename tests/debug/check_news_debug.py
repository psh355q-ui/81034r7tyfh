
import sys
import os
from sqlalchemy import desc

# Add current directory to path
sys.path.append(os.getcwd())

from backend.database.repository import get_sync_session
from backend.database.models import NewsArticle, AnalysisResult

def check():
    db = get_sync_session()
    try:
        print("=== DB Status Check ===")
        total = db.query(NewsArticle).count()
        print(f"Total Articles: {total}")
        
        sources = db.query(NewsArticle.source).distinct().all()
        print(f"Sources: {[s[0] for s in sources]}")
        
        analyzed_count = db.query(AnalysisResult).count()
        print(f"Analyzed Count: {analyzed_count}")
        
        analyzed_ids = db.query(AnalysisResult.article_id).all()
        analyzed_ids = [r[0] for r in analyzed_ids]
        print(f"Analyzed IDs: {analyzed_ids}")
        
        print("\n=== Exact Server Query Verification ===")
        # 1. 미분석 기사 조회
        analyzed_ids = db.query(AnalysisResult.article_id).all()
        analyzed_ids = [r[0] for r in analyzed_ids]
        print(f"Analyzed IDs count: {len(analyzed_ids)}")
        
        query = db.query(NewsArticle).filter(
            NewsArticle.id.notin_(analyzed_ids),
            NewsArticle.source != "KIS_API"
        ).order_by(desc(NewsArticle.published_date)).limit(10)
        
        articles = query.all()
        print(f"Exact Query Result Count: {len(articles)}")
        
        if articles:
            print(f"First article: {articles[0].title} (ID: {articles[0].id}, Source: {articles[0].source})")
        else:
            print("No articles found with exact query.")
            
            # Debugging why
            print("\n--- Debugging Filters ---")
            # 1. Check total non-KIS
            q1 = db.query(NewsArticle).filter(NewsArticle.source != "KIS_API")
            print(f"Total non-KIS articles: {q1.count()}")
            
            # 2. Check notin
            if analyzed_ids:
                q2 = q1.filter(NewsArticle.id.notin_(analyzed_ids))
                print(f"Non-KIS unanalyzed: {q2.count()}")
            
            # 3. Check order by
            q3 = q2.order_by(desc(NewsArticle.published_date))
            results = q3.limit(5).all()
            print(f"Top 5 unanalyzed dates: {[a.published_date for a in results]}")

            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check()
