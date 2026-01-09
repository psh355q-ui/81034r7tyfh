"""
통합 뉴스 시스템 성능 모니터링 스크립트

UnifiedNewsProcessor의 성능을 측정:
- 중복 제거율
- 처리 속도
- 분석률
- DB 저장 효율
"""
import sys
import time
sys.path.insert(0, 'd:/code/ai-trading-system')

from backend.database.repository import get_sync_session
from backend.database.models import NewsArticle, NewsAnalysis

def monitor_performance():
    """성능 통계 수집"""
    print("=" * 80)
    print("통합 뉴스 시스템 성능 모니터링")
    print("=" * 80)
    print()
    
    db = get_sync_session()
    
    try:
        # 1. 전체 통계
        print("[1] 전체 통계")
        print("-" * 80)
        total_articles = db.query(NewsArticle).count()
        analyzed_articles = db.query(NewsAnalysis).count()
        
        print(f"총 기사: {total_articles}")
        print(f"분석 완료: {analyzed_articles}")
        print(f"분석률: {(analyzed_articles/total_articles*100) if total_articles > 0 else 0:.1f}%")
        print()
        
        # 2. 중복 제거 효과
        print("[2] 중복 제거 효과")
        print("-" * 80)
        
        # Content hash 사용률
        with_hash = db.query(NewsArticle).filter(
            NewsArticle.content_hash.isnot(None)
        ).count()
        
        print(f"Content Hash 있는 기사: {with_hash}/{total_articles} ({with_hash/total_articles*100 if total_articles > 0 else 0:.1f}%)")
        
        # 중복 hash 찾기 (간단한 방법)
        from sqlalchemy import func
        duplicate_hashes = db.query(
            NewsArticle.content_hash,
            func.count(NewsArticle.id).label('count')
        ).filter(
            NewsArticle.content_hash.isnot(None)
        ).group_by(
            NewsArticle.content_hash
        ).having(
            func.count(NewsArticle.id) > 1
        ).count()
        
        print(f"중복 Hash 발견: {duplicate_hashes}개")
        print()
        
        # 3. 최근 활동
        print("[3] 최근 활동 (24시간)")
        print("-" * 80)
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        recent_articles = db.query(NewsArticle).filter(
            NewsArticle.crawled_at >= cutoff
        ).count()
        
        recent_analyzed = db.query(NewsAnalysis).join(
            NewsArticle
        ).filter(
            NewsArticle.crawled_at >= cutoff
        ).count()
        
        print(f"최근 수집: {recent_articles}개")
        print(f"최근 분석: {recent_analyzed}개")
        print()
        
        # 4. 감성 분포
        print("[4] 감성 분포")
        print("-" * 80)
        
        positive = db.query(NewsAnalysis).filter(
            NewsAnalysis.sentiment_overall == "positive"
        ).count()
        negative = db.query(NewsAnalysis).filter(
            NewsAnalysis.sentiment_overall == "negative"
        ).count()
        neutral = db.query(NewsAnalysis).filter(
            NewsAnalysis.sentiment_overall == "neutral"
        ).count()
        
        if analyzed_articles > 0:
            print(f"긍정: {positive} ({positive/analyzed_articles*100:.1f}%)")
            print(f"부정: {negative} ({negative/analyzed_articles*100:.1f}%)")
            print(f"중립: {neutral} ({neutral/analyzed_articles*100:.1f}%)")
        else:
            print("분석된 기사 없음")
        print()
        
        # 5. 출처별 통계
        print("[5] 주요 출처")
        print("-" * 80)
        
        top_sources = db.query(
            NewsArticle.source,
            func.count(NewsArticle.id).label('count')
        ).group_by(
            NewsArticle.source
        ).order_by(
            func.count(NewsArticle.id).desc()
        ).limit(5).all()
        
        for source, count in top_sources:
            print(f"  {source or 'Unknown'}: {count}개")
        print()
        
        print("=" * 80)
        print("✅ 모니터링 완료!")
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    monitor_performance()
