"""
뉴스 데이터 확인 스크립트
"""
import httpx
import json

def check_news_data():
    """뉴스 데이터 및 통계 확인"""
    print("=" * 80)
    print("뉴스 데이터 확인 (Ollama 분석 결과)")
    print("=" * 80)
    print()
    
    try:
        # 1. 뉴스 통계
        print("[1] 뉴스 통계")
        print("-" * 80)
        stats_response = httpx.get("http://localhost:8001/api/news/stats", timeout=10.0)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print(f"❌ 통계 조회 실패: HTTP {stats_response.status_code}")
        
        print("\n")
        
        # 2. 최신 뉴스 (Ollama 분석 결과)
        print("[2] 최신 뉴스 기사 (Ollama 분석 결과)")
        print("-" * 80)
        articles_response = httpx.get(
            "http://localhost:8001/api/news/articles?limit=5",
            timeout=10.0
        )
        
        if articles_response.status_code == 200:
            data = articles_response.json()
            articles = data.get("articles", [])
            
            if articles:
                for i, article in enumerate(articles[:3], 1):
                    print(f"\n[기사 {i}]")
                    print(f"제목: {article.get('title', 'N/A')[:70]}...")
                    print(f"출처: {article.get('source', 'N/A')}")
                    print(f"감성: {article.get('sentiment_label', 'N/A')}")
                    print(f"감성 점수: {article.get('sentiment_score', 0):.2f}")
                    print(f"모델: {article.get('model_used', 'N/A')}")
                    print(f"거래 가능: {article.get('trading_actionable', False)}")
            else:
                print("ℹ️ 뉴스 기사가 없습니다.")
        else:
            print(f"❌ 기사 조회 실패: HTTP {articles_response.status_code}")
        
        print("\n")
        
        # 3. Positive 감성 뉴스
        print("[3] Positive 감성 뉴스")
        print("-" * 80)
        positive_response = httpx.get(
            "http://localhost:8001/api/news/articles?sentiment=positive&limit=3",
            timeout=10.0
        )
        
        if positive_response.status_code == 200:
            data = positive_response.json()
            articles = data.get("articles", [])
            
            if articles:
                for i, article in enumerate(articles, 1):
                    print(f"\n{i}. {article.get('title', 'N/A')[:60]}...")
                    print(f"   점수: {article.get('sentiment_score', 0):.2f} | 출처: {article.get('source', 'N/A')}")
            else:
                print("ℹ️ Positive 뉴스가 없습니다.")
        
        print("\n")
        print("=" * 80)
        print("✅ 뉴스 데이터 확인 완료")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_news_data()
