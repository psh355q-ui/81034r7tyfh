"""
뉴스 중복 제거 테스트 스크립트
"""
import sys
sys.path.insert(0, 'd:/code/ai-trading-system')

from backend.database.repository import get_sync_session
from backend.database.models import NewsArticle
from backend.data.rss_crawler import generate_content_hash

def test_deduplication():
    """중복 제거 테스트"""
    print("=" * 80)
    print("뉴스 중복 제거 테스트")
    print("=" * 80)
    print()
    
    db = get_sync_session()
    
    try:
        # 1. Content hash 함수 테스트
        print("[1] Content Hash 생성 테스트")
        title1 = "Tesla Stock Surges on Strong Q4 Earnings"
        content1 = "Tesla Inc. reported record earnings..."
        
        hash1 = generate_content_hash(title1, content1)
        hash2 = generate_content_hash(title1, content1)  # 동일
        hash3 = generate_content_hash(title1 + " Updated", content1)  # 다름
        
        print(f"Hash 1: {hash1[:16]}...")
        print(f"Hash 2: {hash2[:16]}...")  
        print(f"Same?:  {hash1 == hash2}")
        print(f"Hash 3: {hash3[:16]}...")
        print(f"Different?: {hash1 != hash3}")
        print()
        
        # 2. DB에서 content_hash로 검색 테스트
        print("[2] DB Content Hash 검색 테스트")
        articles_with_hash = db.query(NewsArticle).filter(
            NewsArticle.content_hash.isnot(None)
        ).limit(5).all()
        
        print(f"content_hash가 있는 기사: {len(articles_with_hash)}개")
        for article in articles_with_hash:
            print(f"  - {article.title[:50]}...")
            print(f"    Hash: {article.content_hash[:16]}...")
        print()
        
        # 3. 중복 감지 테스트
        print("[3] 중복 감지 테스트")
        # 동일한 content_hash를 가진 기사 찾기
        hash_counts = {}
        all_articles = db.query(NewsArticle).filter(
            NewsArticle.content_hash.isnot(None)
        ).all()
        
        for article in all_articles:
            h = article.content_hash
            if h in hash_counts:
                hash_counts[h].append(article)
            else:
                hash_counts[h] = [article]
        
        duplicates = {h: articles for h, articles in hash_counts.items() if len(articles) > 1}
        
        if duplicates:
            print(f"발견된 중복 세트: {len(duplicates)}개")
            for hash_val, articles in list(duplicates.items())[:3]:
                print(f"\n  Hash: {hash_val[:16]}...")
                for article in articles:
                    print(f"    - ID: {article.id}, URL: {article.url[:50]}...")
        else:
            print("중복 기사 없음 (모두 고유)")
        
        print()
        print("=" * 80)
        print("✅ 테스트 완료!")
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    test_deduplication()
