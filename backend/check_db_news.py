"""
DB에서 직접 뉴스 데이터 확인
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.repository import get_sync_session
from backend.database.models import NewsArticle, NewsAnalysis
from sqlalchemy import func, desc

def check_news_in_db():
    """DB에서 직접 뉴스 데이터 확인"""
    print("=" * 80)
    print("DB 뉴스 데이터 확인 (Ollama 분석 결과)")
    print("=" * 80)
    print()
    
    db = get_sync_session()
    
    try:
        # 1. 전체 통계
        print("[1] 전체 뉴스 통계")
        print("-" * 80)
        total_articles = db.query(NewsArticle).count()
        analyzed_articles = db.query(NewsArticle).join(NewsAnalysis).count()
        
        print(f"총 뉴스 기사: {total_articles}개")
        print(f"분석 완료: {analyzed_articles}개")
        print(f"미분석: {total_articles - analyzed_articles}개")
        
        # Ollama 모델인 기사 확인
        ollama_articles = db.query(NewsAnalysis).filter(
            NewsAnalysis.model_used.like('%llama%')
        ).count()
        print(f"Ollama 분석 기사: {ollama_articles}개")
        
        print()
        
        # 2. 최신 분석 기사 (Ollama)
        print("[2] 최신 Ollama 분석 기사 (상위 5개)")
        print("-" * 80)
        
        latest_analyzed = (
            db.query(NewsArticle, NewsAnalysis)
            .join(NewsAnalysis)
            .filter(NewsAnalysis.model_used.like('%llama%'))
            .order_by(desc(NewsArticle.published_date))
            .limit(5)
            .all()
        )
        
        if latest_analyzed:
            for i, (article, analysis) in enumerate(latest_analyzed, 1):
                print(f"\n[{i}] {article.title[:65]}...")
                print(f"    출처: {article.source}")
                print(f"    날짜: {article.published_date}")
                print(f"    모델: {analysis.model_used}")
                print(f"    감성: {analysis.sentiment_overall} ({analysis.sentiment_score:.2f})")
                print(f"    긴급도: {analysis.urgency}")
                print(f"    단기 영향: {analysis.market_impact_short}")
                print(f"    거래 가능: {analysis.trading_actionable}")
        else:
            print("ℹ️ Ollama로 분석된 기사가 없습니다.")
        
        print()
        
        # 3. 감성별 통계
        print("[3] 감성별 통계 (Ollama 분석)")
        print("-" * 80)
        
        sentiment_stats = (
            db.query(
                NewsAnalysis.sentiment_overall,
                func.count(NewsAnalysis.id).label('count'),
                func.avg(NewsAnalysis.sentiment_score).label('avg_score')
            )
            .filter(NewsAnalysis.model_used.like('%llama%'))
            .group_by(NewsAnalysis.sentiment_overall)
            .all()
        )
        
        if sentiment_stats:
            for sentiment, count, avg_score in sentiment_stats:
                avg_score_val = float(avg_score) if avg_score else 0.0
                print(f"{sentiment:10s}: {count:3d}개 (평균 점수: {avg_score_val:+.2f})")
        else:
            print("ℹ️ 감성 데이터가 없습니다.")
        
        print()
        
        # 4. 최근 24시간 분석 기사
        print("[4] 최근 24시간 분석 기사")
        print("-" * 80)
        
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(days=1)
        
        recent_count = (
            db.query(NewsArticle)
            .join(NewsAnalysis)
            .filter(NewsArticle.published_date >= recent_cutoff)
            .filter(NewsAnalysis.model_used.like('%llama%'))
            .count()
        )
        
        print(f"최근 24시간 Ollama 분석 기사: {recent_count}개")
        
        print()
        print("=" * 80)
        print("✅ DB 확인 완료")
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    check_news_in_db()
