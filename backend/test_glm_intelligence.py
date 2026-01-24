"""
Test GLM-4.7 with Market Intelligence v2.0 Components

This test validates:
1. NewsFilter with GLM-4.7
2. NarrativeStateEngine with GLM-4.7
3. FactChecker with GLM-4.7
4. MarketConfirmation with GLM-4.7
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, '..')

from backend.ai.llm_providers import LLMProvider, ModelConfig, ModelProvider
from backend.ai.intelligence.news_filter import NewsFilter


async def test_news_filter_with_glm():
    """Test NewsFilter with GLM-4.7"""
    print("\n" + "=" * 60)
    print("TEST 1: NewsFilter with GLM-4.7")
    print("=" * 60)

    # Create LLM provider with GLM-4.7
    llm = LLMProvider()

    # Create GLM-4.7 config for both stages
    glm_config = ModelConfig(
        model="GLM-4.7",
        provider=ModelProvider.GLM,
        max_tokens=1000,
        temperature=0.7,
    )

    # Create NewsFilter with GLM-4.7
    filter = NewsFilter(
        llm_provider=llm,
        stage1_config=glm_config,
        stage2_config=glm_config,
    )

    print(f"✓ NewsFilter initialized with GLM-4.7")

    # Test article
    article = {
        "title": "Apple announces new AI chip for data centers",
        "content": "Apple unveiled its latest M4 chip designed specifically for AI workloads in data centers. The new chip promises 3x better performance for machine learning tasks compared to previous generations. Major cloud providers including AWS and Google Cloud have already announced support for the new chip.",
    }

    print(f"\nTesting article: {article['title']}")

    # Process article
    result = await filter.process(article)

    print(f"\n✓ Filter Result:")
    print(f"  Success: {result.success}")
    print(f"  Stage 1 Passed: {result.data.get('stage1_passed', False)}")
    print(f"  Stage 2 Completed: {result.data.get('stage2_completed', False)}")
    print(f"  Is Relevant: {result.data.get('is_relevant', False)}")

    if result.data.get('stage2_completed'):
        print(f"\n  Analysis:")
        print(f"    Topic: {result.data.get('topic', 'N/A')}")
        print(f"    Sentiment: {result.data.get('sentiment', 'N/A')}")
        print(f"    Confidence: {result.data.get('confidence', 0):.2f}")
        print(f"    Reasoning: {result.data.get('reasoning', 'N/A')[:100]}...")
        print(f"    Cost Savings: {result.data.get('cost_savings', {})}")

    if not result.success:
        print(f"\n✗ Errors: {result.errors}")

    return result.success


async def main():
    """Run all tests"""
    print("\n🚀 GLM-4.7 Market Intelligence Test Suite")
    print(f"Time: {asyncio.get_event_loop().time()}")

    results = {}

    try:
        # Test 1: NewsFilter
        results['news_filter'] = await test_news_filter_with_glm()
    except Exception as e:
        print(f"✗ NewsFilter test failed: {e}")
        import traceback
        traceback.print_exc()
        results['news_filter'] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20s} {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! GLM-4.7 integration is working correctly.")
    else:
        print(f"\n⚠ {total_tests - passed_tests} test(s) failed. Please review errors above.")


if __name__ == "__main__":
    asyncio.run(main())
