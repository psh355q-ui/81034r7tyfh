"""
Ollama 통합 테스트 스크립트
"""
import asyncio
import sys
import os

# 프로젝트 루트를 Python 패스에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai.llm import get_ollama_client, get_embedding_service
from backend.data.processors.news_processor import NewsProcessor


async def test_ollama_integration():
    """Ollama 통합 테스트"""
    print("=" * 80)
    print("Ollama 통합 테스트")
    print("=" * 80)
    print()
    
    # 1. Ollama 클라이언트 테스트
    print("[테스트 1] Ollama 클라이언트 초기화")
    try:
        ollama = get_ollama_client()
        print(f"✅ Ollama 클라이언트 생성 완료")
        print(f"   Base URL: {ollama.base_url}")
        print(f"   Model: {ollama.model}")
        
        # 헬스 체크
        if ollama.check_health():
            print(f"✅ Ollama 서버 정상 작동")
        else:
            print(f"⚠️ Ollama 서버 응답 없음. Ollama가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ Ollama 클라이언트 초기화 실패: {e}")
        return
    
    print()
    
    # 2. 로컬 임베딩 서비스 테스트
    print("[테스트 2] 로컬 임베딩 서비스 초기화")
    try:
        embedding_service = get_embedding_service()
        print(f"✅ 임베딩 서비스 생성 완료")
        print(f"   Dimension: {embedding_service.dimension}")
        
        # 간단한 임베딩 테스트
        test_text = "Apple stock rises 5% on strong earnings"
        embedding = embedding_service.get_embedding(test_text)
        print(f"✅ 임베딩 생성 테스트 성공")
        print(f"   텍스트: {test_text}")
        print(f"   벡터 길이: {len(embedding)}")
        print(f"   첫 5개 값: {embedding[:5]}")
    except Exception as e:
        print(f"❌ 임베딩 서비스 초기화 실패: {e}")
        return
    
    print()
    
    # 3. 뉴스 감성 분석 테스트
    print("[테스트 3] Ollama 뉴스 감성 분석")
    try:
        title = "Apple Reports Record Q4 Earnings, Stock Surges"
        content = "Apple Inc. reported record earnings for Q4 2024, beating analyst expectations. Revenue increased 12% year-over-year."
        
        result = ollama.analyze_news_sentiment(title, content)
        print(f"✅ 감성 분석 완료")
        print(f"   감성: {result['sentiment_overall']}")
        print(f"   점수: {result['sentiment_score']:.2f}")
        print(f"   신뢰도: {result['confidence']:.2f}")
        print(f"   거래 가능: {result['trading_actionable']}")
        if result.get('key_points'):
            print(f"   핵심 포인트: {result['key_points']}")
        if result.get('affected_tickers'):
            print(f"   관련 티커: {result['affected_tickers']}")
    except Exception as e:
        print(f"❌ 감성 분석 실패: {e}")
    
    print()
    
    # 4. NewsProcessor 통합 테스트
    print("[테스트 4] NewsProcessor 통합 테스트")
    try:
        processor = NewsProcessor()
        print(f"✅ NewsProcessor 초기화 완료")
        
        # 간단한 분석 테스트
        analysis = await processor.analyze_content(
            title="Tesla Stock Drops on Production Concerns",
            content="Tesla shares fell 3% today amid concerns about production delays."
        )
        
        print(f"✅ 콘텐츠 분석 완료")
        print(f"   감성: {analysis['label']}")
        print(f"   점수: {analysis['score']:.2f}")
        print(f"   티커: {analysis.get('tickers', [])}")
        print(f"   태그: {analysis.get('tags', [])}")
        
    except Exception as e:
        print(f"❌ NewsProcessor 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_ollama_integration())
