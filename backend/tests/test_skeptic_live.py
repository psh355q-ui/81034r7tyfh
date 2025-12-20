"""
Skeptic Agent 실전 테스트

합의 의견에 대한 도전 테스트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_skeptic_agent():
    """Skeptic Agent 테스트"""
    
    print("="*60)
    print("😈 Skeptic Agent (악마의 변호인) 테스트")
    print("="*60)
    print()
    
    try:
        from backend.ai.debate.skeptic_agent import get_skeptic_agent, SkepticMode
        
        skeptic = get_skeptic_agent(mode=SkepticMode.MODERATE)
        print("✅ Skeptic Agent 초기화 완료")
        print()
        
        # 테스트 시나리오: 낙관적 합의에 도전
        consensus_view = "NVDA 매수 추천 (85% confidence)"
        reasoning = """
        NVIDIA는 AI 붐으로 계속 성장할 전망입니다.
        - 데이터센터 수요 급증
        - GPU 시장 독점적 지위
        - 신제품 발표 호조
        """
        
        print("📋 합의 의견:")
        print(f"   {consensus_view}")
        print()
        print("💭 논리:")
        print(reasoning.strip())
        print()
        print("🔄 Skeptic 분석 중...")
        print()
        
        # Skeptic 도전
        challenge = await skeptic.challenge(
            consensus_view=consensus_view,
            reasoning=reasoning,
            confidence=0.85,
            market_data={"ticker": "NVDA", "price": 500}
        )
        
        print("="*60)
        print("😈 Skeptic의 도전")
        print("="*60)
        print()
        
        if challenge.challenges:
            print("🎯 반대 논리:")
            for i, c in enumerate(challenge.challenges, 1):
                print(f"   {i}. {c}")
            print()
        
        if challenge.hidden_risks:
            print("🔍 숨겨진 리스크:")
            for i, risk in enumerate(challenge.hidden_risks, 1):
                print(f"   {i}. {risk}")
            print()
        
        if challenge.alternative_view:
            print(f"💡 대안적 관점:")
            print(f"   {challenge.alternative_view}")
            print()
        
        print(f"⚖️  최종 평가: {challenge.final_verdict}")
        print()
        
        print("="*60)
        print("✅ Skeptic Agent 테스트 성공!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_skeptic_agent())
    sys.exit(0 if success else 1)
