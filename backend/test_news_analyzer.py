"""
News Poller + Ollama 테스트 스크립트
"""
import asyncio
import sys
import os

# 프로젝트 루트를 Python 패스에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.repository import get_sync_session
from backend.database.models import NewsArticle
from backend.data.news_analyzer import NewsDeepAnalyzer


def test_news_analyzer_ollama():
    """NewsDeepAnalyzer + Ollama 테스트"""
    print("=" * 80)
    print("NewsDeepAnalyzer + Ollama Integration Test")
    print("=" * 80)
    print()
    
    db = get_sync_session()
    
    try:
        # 1. NewsDeepAnalyzer 초기화
        print("[테스트 1] NewsDeepAnalyzer 초기화")
        try:
            analyzer = NewsDeepAnalyzer(db)
            print(f"✅ NewsDeepAnalyzer 초기화 완료")
            print(f"   Ollama Model: {analyzer.ollama_client.model}")
        except Exception as e:
            print(f"❌ NewsDeepAnalyzer 초기화 실패: {e}")
            return
        
        print()
        
        # 2. 미분석 뉴스 조회
        print("[테스트 2] 미분석 뉴스 조회")
        unanalyzed = (
            db.query(NewsArticle)
            .outerjoin(NewsArticle.analysis)
            .filter(NewsArticle.analysis == None)
            .order_by(NewsArticle.published_date.desc())
            .limit(3)
            .all()
        )
        
        print(f"✅ 미분석 뉴스: {len(unanalyzed)}개")
        
        if not unanalyzed:
            print("ℹ️ 미분석 뉴스가 없습니다. 테스트 기사를 생성합니다.")
            
            # 테스트 기사 생성
            from datetime import datetime
            test_article = NewsArticle(
                title="Tesla Stock Surges as Q4 Deliveries Beat Expectations",
                content="Tesla Inc. announced record Q4 deliveries exceeding analyst expectations. The electric vehicle maker delivered 500,000 vehicles in Q4 2024, up 30% year-over-year. Stock price surged 8% in after-hours trading.",
                summary="Tesla Q4 deliveries beat expectations, stock surges 8%",
                source="MarketWatch",
                url="https://example.com/test",
                published_date=datetime.utcnow(),
                keywords=["Tesla", "TSLA", "earnings", "deliveries"]
            )
            db.add(test_article)
            db.commit()
            db.refresh(test_article)
            
            unanalyzed = [test_article]
            print(f"✅ 테스트 기사 생성: {test_article.title}")
        
        print()
        
        # 3. Ollama 분석 테스트
        print("[테스트 3] Ollama 뉴스 분석")
        for i, article in enumerate(unanalyzed[:2], 1):  # 최대 2개만 테스트
            print(f"\n--- 기사 {i} ---")
            print(f"제목: {article.title[:60]}...")
            
            try:
                analysis = analyzer.analyze_article(article)
                
                if analysis:
                    print(f"✅ 분석 완료")
                    print(f"   감성: {analysis.sentiment_overall}")
                    print(f"   점수: {analysis.sentiment_score:.2f}")
                    print(f"   긴급도: {analysis.urgency}")
                    print(f"   단기 영향: {analysis.market_impact_short}")
                    print(f"   장기 영향: {analysis.market_impact_long}")
                    print(f"   거래 가능: {analysis.trading_actionable}")
                else:
                    print(f"⚠️ 분석 결과 없음")
                    
            except Exception as e:
                print(f"❌ 분석 실패: {e}")
                import traceback
                traceback.print_exc()
        
        print()
        print("=" * 80)
        print("테스트 완료!")
        print("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    test_news_analyzer_ollama()
