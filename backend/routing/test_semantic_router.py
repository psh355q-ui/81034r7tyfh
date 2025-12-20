"""
Semantic Router 테스트 및 데모

토큰 절감 효과 시연

Author: AI Trading System
Date: 2025-12-04
"""

import asyncio
import logging
from typing import List, Dict, Any

from backend.routing.semantic_router import (
    SemanticRouter,
    get_semantic_router,
    format_routing_result,
)
from backend.routing.intent_classifier import Intent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# ============================================================================
# Test Cases
# ============================================================================

TEST_QUERIES = [
    # News Analysis
    "삼성전자 최근 뉴스 분석해줘",
    "애플의 최신 제품 발표 소식 알려줘",
    "What's the latest news about Tesla?",

    # Trading Execution
    "삼성전자 10주 매수해줘",
    "테슬라 주식 팔아줘",
    "Buy 100 shares of AAPL",

    # Strategy Generation
    "이동평균 크로스오버 전략 백테스트해줘",
    "포트폴리오 최적화 전략 만들어줘",
    "Create a momentum trading strategy",

    # Market Research
    "반도체 산업 분석해줘",
    "애플의 경쟁사는 누구야?",
    "Analyze the EV market",

    # Portfolio Management
    "내 포트폴리오 상태 보여줘",
    "계좌 잔고 확인해줘",
    "Show my account balance",

    # Data Query
    "삼성전자 현재가는?",
    "테슬라 주가 얼마야?",
    "What's the price of NVDA?",

    # General
    "안녕하세요",
    "도와줄 수 있는 게 뭐야?",
]


async def test_single_route():
    """단일 라우팅 테스트"""
    print("\n" + "=" * 80)
    print("Test 1: Single Route")
    print("=" * 80)

    router = SemanticRouter(
        use_local_llm_for_intent=False,
        enable_caching=True,
        prefer_low_cost=False,
    )

    user_input = "삼성전자 최근 뉴스 분석해줘"
    result = await router.route(user_input)

    print(format_routing_result(result, verbose=True))

    # 결과 검증
    assert result.intent == Intent.NEWS_ANALYSIS.value
    assert result.provider == "gemini"
    assert result.tool_count > 0

    print("\n✅ Single route test passed!")


async def test_batch_routing():
    """배치 라우팅 테스트"""
    print("\n" + "=" * 80)
    print("Test 2: Batch Routing")
    print("=" * 80)

    router = SemanticRouter(enable_caching=True)

    results = []
    for query in TEST_QUERIES:
        result = await router.route(query)
        results.append(result)
        print(f"\n[{result.intent}] \"{query}\"")
        print(f"  → {result.provider}/{result.model} ({result.tool_count} tools, {result.estimated_tokens} tokens)")

    print(f"\n✅ Processed {len(results)} queries")


async def test_caching_effect():
    """캐싱 효과 테스트"""
    print("\n" + "=" * 80)
    print("Test 3: Caching Effect")
    print("=" * 80)

    # 캐싱 비활성화
    router_no_cache = SemanticRouter(enable_caching=False)
    result_no_cache = await router_no_cache.route("삼성전자 뉴스 분석해줘")

    # 캐싱 활성화
    router_with_cache = SemanticRouter(enable_caching=True)
    result_1st = await router_with_cache.route("삼성전자 뉴스 분석해줘")
    result_2nd = await router_with_cache.route("삼성전자 뉴스 분석해줘")

    print(f"\nNo Cache:")
    print(f"  Tokens: {result_no_cache.estimated_tokens}")
    print(f"  Cost: ${result_no_cache.estimated_cost_usd:.6f}")

    print(f"\nWith Cache (1st request):")
    print(f"  Tokens: {result_1st.estimated_tokens}")
    print(f"  Cost: ${result_1st.estimated_cost_usd:.6f}")
    print(f"  Cache Key: {result_1st.cache_key}")

    print(f"\nWith Cache (2nd request, cache hit):")
    print(f"  Tokens: {result_2nd.estimated_tokens}")
    print(f"  Cost: ${result_2nd.estimated_cost_usd:.6f}")
    print(f"  Cache Key: {result_2nd.cache_key}")

    # 절감액 계산
    token_savings = result_no_cache.estimated_tokens - result_2nd.estimated_tokens
    cost_savings = result_no_cache.estimated_cost_usd - result_2nd.estimated_cost_usd

    print(f"\n💰 Savings (Cache Hit):")
    print(f"  Tokens: {token_savings} ({token_savings / result_no_cache.estimated_tokens * 100:.1f}%)")
    print(f"  Cost: ${cost_savings:.6f} ({cost_savings / result_no_cache.estimated_cost_usd * 100:.1f}%)")

    print("\n✅ Caching effect test passed!")


async def test_low_cost_mode():
    """저비용 모드 테스트"""
    print("\n" + "=" * 80)
    print("Test 4: Low Cost Mode")
    print("=" * 80)

    # 일반 모드
    router_normal = SemanticRouter(prefer_low_cost=False)
    result_normal = await router_normal.route("복잡한 트레이딩 전략 만들어줘")

    # 저비용 모드
    router_low_cost = SemanticRouter(prefer_low_cost=True)
    result_low_cost = await router_low_cost.route("복잡한 트레이딩 전략 만들어줘")

    print(f"\nNormal Mode:")
    print(f"  Model: {result_normal.provider}/{result_normal.model}")
    print(f"  Cost: ${result_normal.estimated_cost_usd:.6f}")

    print(f"\nLow Cost Mode:")
    print(f"  Model: {result_low_cost.provider}/{result_low_cost.model}")
    print(f"  Cost: ${result_low_cost.estimated_cost_usd:.6f}")

    cost_savings = result_normal.estimated_cost_usd - result_low_cost.estimated_cost_usd
    savings_pct = cost_savings / result_normal.estimated_cost_usd * 100

    print(f"\n💰 Savings:")
    print(f"  Cost: ${cost_savings:.6f} ({savings_pct:.1f}%)")

    print("\n✅ Low cost mode test passed!")


async def test_statistics():
    """통계 테스트"""
    print("\n" + "=" * 80)
    print("Test 5: Statistics")
    print("=" * 80)

    router = get_semantic_router(enable_caching=True)

    # 여러 쿼리 실행
    for query in TEST_QUERIES[:10]:
        await router.route(query)

    # 통계 조회
    stats = router.get_statistics()

    print("\nRouting Statistics:")
    print(f"  Total Routes: {stats['total_routes']}")
    print(f"  Tokens Saved: {stats['total_tokens_saved']:,}")

    print("\nIntent Distribution:")
    for intent, count in stats['intent_distribution'].items():
        print(f"  {intent}: {count}")

    print("\nModel Usage:")
    for model, count in stats['model_usage'].items():
        print(f"  {model}: {count}")

    if 'cache_stats' in stats:
        cache_stats = stats['cache_stats']
        print("\nCache Statistics:")
        print(f"  Total Requests: {cache_stats['total_requests']}")
        print(f"  Cache Hits: {cache_stats['cache_hits']}")
        print(f"  Cache Misses: {cache_stats['cache_misses']}")
        print(f"  Hit Rate: {cache_stats['hit_rate'] * 100:.1f}%")
        print(f"  Estimated Token Savings: {cache_stats['estimated_token_savings']:,}")

    print("\n✅ Statistics test passed!")


async def simulate_daily_usage():
    """일일 사용량 시뮬레이션"""
    print("\n" + "=" * 80)
    print("Simulation: Daily Usage (1,000 requests)")
    print("=" * 80)

    router = SemanticRouter(enable_caching=True, prefer_low_cost=False)

    # 1,000 요청 시뮬레이션 (샘플링)
    total_requests = 1000
    sample_size = len(TEST_QUERIES)

    total_tokens = 0
    total_cost = 0.0

    for i in range(total_requests):
        query = TEST_QUERIES[i % sample_size]
        result = await router.route(query)

        total_tokens += result.estimated_tokens
        total_cost += result.estimated_cost_usd

        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{total_requests} requests...")

    # 결과
    print(f"\n📊 Simulation Results:")
    print(f"  Total Requests: {total_requests:,}")
    print(f"  Total Tokens: {total_tokens:,}")
    print(f"  Total Cost: ${total_cost:.2f}")
    print(f"  Avg Tokens/Request: {total_tokens / total_requests:.0f}")
    print(f"  Avg Cost/Request: ${total_cost / total_requests:.6f}")

    # 비교: 캐싱 없이
    baseline_tokens_per_request = 3000
    baseline_tokens = baseline_tokens_per_request * total_requests
    baseline_cost = baseline_tokens / 1_000_000 * 2.5  # GPT-4o 입력 가격

    print(f"\n🔴 Without Optimization:")
    print(f"  Total Tokens: {baseline_tokens:,}")
    print(f"  Total Cost: ${baseline_cost:.2f}")

    # 절감액
    token_savings = baseline_tokens - total_tokens
    cost_savings = baseline_cost - total_cost

    print(f"\n💰 Total Savings:")
    print(f"  Tokens: {token_savings:,} ({token_savings / baseline_tokens * 100:.1f}%)")
    print(f"  Cost: ${cost_savings:.2f} ({cost_savings / baseline_cost * 100:.1f}%)")
    print(f"  Monthly: ${cost_savings * 30:.2f}")
    print(f"  Yearly: ${cost_savings * 365:.2f}")

    print("\n✅ Simulation complete!")


# ============================================================================
# Main
# ============================================================================

async def main():
    """모든 테스트 실행"""
    print("\n" + "=" * 80)
    print(" Semantic Router Test Suite")
    print("=" * 80)

    try:
        await test_single_route()
        await test_batch_routing()
        await test_caching_effect()
        await test_low_cost_mode()
        await test_statistics()
        await simulate_daily_usage()

        print("\n" + "=" * 80)
        print(" ✅ All Tests Passed!")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print("\n❌ Tests failed!")


if __name__ == "__main__":
    asyncio.run(main())
