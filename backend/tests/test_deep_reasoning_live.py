"""
Deep Reasoning 실전 테스트

실제 뉴스로 Deep Reasoning Engine 테스트
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

async def test_deep_reasoning():
    """Deep Reasoning 엔진 테스트"""
    
    print("="*60)
    print("🧠 Deep Reasoning Engine 테스트")
    print("="*60)
    print()
    
    try:
        from ai.reasoning.engine import DeepReasoningEngine
        
        engine = DeepReasoningEngine()
        print("✅ Deep Reasoning Engine 초기화 완료")
        print()
        
        # 테스트 뉴스
        test_news = """
        연준(Fed)이 기준 금리를 4.75%로 유지했습니다.
        제롬 파월 의장은 기자회견에서 인플레이션 둔화세가 확인되고 있다고 밝혔으나,
        금리 인하는 여전히 신중하게 접근할 것이라고 강조했습니다.
        시장 전문가들은 이를 '비둘기파적 신호'로 해석하고 있으며,
        S&P 500 지수는 발표 후 1.2% 상승했습니다.
        """
        
        print("📰 테스트 뉴스:")
        print(test_news.strip())
        print()
        print("🔄 분석 중...")
        print()
        
        # 분석 실행
        result = await engine.analyze(
            news_text=test_news,
            ticker="SPY"
        )
        
        print("="*60)
        print("📊 분석 결과")
        print("="*60)
        print()
        
        print(f"📌 핵심 논제 (Thesis):")
        print(f"   {result.thesis}")
        print()
        
        print(f"🔑 주요 동인 (Key Drivers):")
        for i, driver in enumerate(result.key_drivers, 1):
            print(f"   {i}. {driver}")
        print()
        
        print(f"📈 가격 방향 (Direction): {result.direction}")
        print(f"💪 신뢰도 (Confidence): {result.confidence:.0%}")
        print()
        
        if result.risk_factors:
            print(f"⚠️  리스크 요인:")
            for i, risk in enumerate(result.risk_factors, 1):
                print(f"   {i}. {risk}")
            print()
        
        print("="*60)
        print("✅ Deep Reasoning 테스트 성공!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_deep_reasoning())
    sys.exit(0 if success else 1)
