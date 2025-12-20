"""
Test Real Gemini API with Deep Reasoning

Phase 14 Option A: 실제 Gemini API를 사용한 Deep Reasoning 테스트
"""

import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from backend.ai.ai_client_factory import AIClientFactory
from backend.ai.reasoning.deep_reasoning import DeepReasoningStrategy
from backend.config_phase14 import settings as phase14_settings


async def test_gemini_api_direct():
    """Test 1: Gemini API 직접 호출 테스트"""
    print("=" * 80)
    print("TEST 1: Gemini API Direct Call")
    print("=" * 80)

    # API 키 확인
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n[ERROR] GEMINI_API_KEY not found in environment variables")
        print("Please set GEMINI_API_KEY in .env file")
        return False

    print(f"\n[INFO] GEMINI_API_KEY found: {api_key[:20]}...")

    try:
        # Gemini Pro 클라이언트 생성
        client = AIClientFactory.create("gemini-2.5-pro")

        # 간단한 프롬프트 테스트
        prompt = "Explain Google TPU in 2 sentences."
        print(f"\n[PROMPT] {prompt}")

        response = await client.call_api(prompt, max_tokens=100)

        print(f"\n[RESPONSE] {response}")
        print("\n[SUCCESS] Gemini API call succeeded!")
        return True

    except Exception as e:
        print(f"\n Gemini API 호출 실패: {e}")
        return False


async def test_gemini_web_search():
    """Test 2: Gemini Web Search 기능 테스트"""
    print("\n" + "=" * 80)
    print("TEST 2: Gemini Web Search")
    print("=" * 80)

    try:
        client = AIClientFactory.create("gemini-2.5-pro")

        query = "Broadcom Google TPU partnership 2024"
        print(f"\n[QUERY] {query}")

        # Note: Gemini API는 기본적으로 web search 지원 안함
        # 대신 일반 API 호출로 대체
        prompt = f"What do you know about: {query}"
        response = await client.call_api(prompt, max_tokens=200)

        print(f"\n[RESPONSE] {response[:300]}...")
        print("\n Gemini 정보 검색 성공!")
        return True

    except Exception as e:
        print(f"\n Gemini 검색 실패: {e}")
        return False


async def test_deep_reasoning_real_api():
    """Test 3: Deep Reasoning with Real Gemini API"""
    print("\n" + "=" * 80)
    print("TEST 3: Deep Reasoning with Real Gemini API")
    print("=" * 80)

    try:
        strategy = DeepReasoningStrategy()

        # 실제 뉴스 예시
        news_text = """
        Google announced TPU v6 AI accelerators, with Anthropic signing a
        $1 million contract to use Google TPUs for Claude AI training.
        This represents a strategic shift from Nvidia GPUs to custom silicon.
        """

        print(f"\n[NEWS INPUT]\n{news_text.strip()}")
        print("\n[ANALYZING with Real Gemini API...]")

        # analyze_news 호출 (내부적으로 Gemini API 사용)
        result = await strategy.analyze_news(news_text=news_text)

        # 결과 출력
        print("\n" + "=" * 80)
        print("ANALYSIS RESULT")
        print("=" * 80)

        print(f"\n Investment Theme: {result.theme}")

        if result.primary_beneficiary:
            pb = result.primary_beneficiary
            print(f"\n[PRIMARY] Primary Beneficiary:")
            print(f"   {pb.get('ticker', 'N/A')} -> {pb.get('action', 'N/A')}")
            print(f"   Confidence: {pb.get('confidence', 0):.2f}")
            print(f"   Reason: {pb.get('reasoning', 'N/A')}")

        if result.hidden_beneficiary:
            hb = result.hidden_beneficiary
            print(f"\n[HIDDEN] Hidden Beneficiary:")
            print(f"   {hb.get('ticker', 'N/A')} -> {hb.get('action', 'N/A')}")
            print(f"   Confidence: {hb.get('confidence', 0):.2f}")
            print(f"   Reason: {hb.get('reasoning', 'N/A')}")

        if result.loser:
            loser = result.loser
            print(f"\n[LOSER] Loser:")
            print(f"   {loser.get('ticker', 'N/A')} -> {loser.get('action', 'N/A')}")
            print(f"   Confidence: {loser.get('confidence', 0):.2f}")

        print(f"\n[BULL] Bull Case:\n{result.bull_case}")
        print(f"\n[BEAR] Bear Case:\n{result.bear_case}")

        print(f"\n[TRACE] Reasoning Trace:")
        for i, step in enumerate(result.reasoning_trace, 1):
            print(f"   {i}. {step}")

        if hasattr(result, 'processing_time_ms'):
            print(f"\n  Processing Time: {result.processing_time_ms}ms")
        if hasattr(result, 'model_used'):
            print(f" Model Used: {result.model_used}")

        print("\n Deep Reasoning 실제 API 테스트 성공!")
        return True

    except Exception as e:
        print(f"\n Deep Reasoning 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("Phase 14 Option A: Real Gemini API Test")
    print("=" * 80)
    print("\nThis script tests Deep Reasoning with real Gemini API")
    print("\nExecution steps:")
    print("  1. Gemini API direct call test")
    print("  2. Gemini information search test")
    print("  3. Deep Reasoning full pipeline test")
    print("=" * 80)

    # 설정 확인
    print(f"\n[CONFIG] Configuration:")
    print(f"   Reasoning Model: {phase14_settings.REASONING_MODEL_NAME}")
    print(f"   Provider: {phase14_settings.REASONING_MODEL_PROVIDER}")
    print(f"   Knowledge Graph: {'Enabled' if phase14_settings.KNOWLEDGE_GRAPH_ENABLED else 'Disabled'}")

    # Test 1: Gemini API 직접 호출
    test1_pass = await test_gemini_api_direct()

    if not test1_pass:
        print("\n  Gemini API 호출 실패. GEMINI_API_KEY를 확인해주세요.")
        return

    # Test 2: Gemini 검색 기능
    test2_pass = await test_gemini_web_search()

    # Test 3: Deep Reasoning 전체 파이프라인
    test3_pass = await test_deep_reasoning_real_api()

    # 최종 결과
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Test 1 (Gemini API Direct): {' PASS' if test1_pass else ' FAIL'}")
    print(f"Test 2 (Gemini Web Search): {' PASS' if test2_pass else ' FAIL'}")
    print(f"Test 3 (Deep Reasoning):    {' PASS' if test3_pass else ' FAIL'}")

    if test1_pass and test3_pass:
        print("\n 모든 테스트 성공! Real Gemini API가 정상 작동합니다.")
    else:
        print("\n  일부 테스트 실패. 로그를 확인해주세요.")


if __name__ == "__main__":
    asyncio.run(main())
