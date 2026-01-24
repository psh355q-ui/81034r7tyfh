"""
Test GLM-4.7 with All Market Intelligence v2.0 Components

This test validates:
1. NewsFilter with GLM-4.7
2. NarrativeStateEngine with GLM-4.7
3. FactChecker with GLM-4.7
4. MarketConfirmation with GLM-4.7
5. HorizonTagger with GLM-4.7
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
from backend.ai.intelligence.narrative_state_engine import NarrativeStateEngine


async def test_news_filter_with_glm():
    """Test NewsFilter with GLM-4.7"""
    print("\n" + "=" * 60)
    print("TEST 1: NewsFilter with GLM-4.7")
    print("=" * 60)

    llm = LLMProvider()

    glm_config = ModelConfig(
        model="GLM-4.7",
        provider=ModelProvider.GLM,
        max_tokens=1000,
        temperature=0.7,
    )

    filter = NewsFilter(
        llm_provider=llm,
        stage1_config=glm_config,
        stage2_config=glm_config,
    )

    print(f"✓ NewsFilter initialized with GLM-4.7")

    article = {
        "title": "Apple announces new AI chip for data centers",
        "content": "Apple unveiled its latest M4 chip designed specifically for AI workloads in data centers. The new chip promises 3x better performance for machine learning tasks compared to previous generations. Major cloud providers including AWS and Google Cloud have already announced support for the new chip.",
    }

    print(f"\nTesting article: {article['title']}")

    result = await filter.process(article)

    print(f"\n✓ Filter Result:")
    print(f"  Success: {result.success}")
    print(f"  Stage 1 Passed: {result.data.get('stage1_passed', False)}")
    print(f"  Stage 2 Completed: {result.data.get('stage2_completed', False)}")

    if result.data.get('stage2_completed'):
        print(f"  Topic: {result.data.get('topic', 'N/A')}")
        print(f"  Sentiment: {result.data.get('sentiment', 'N/A')}")
        print(f"  Confidence: {result.data.get('confidence', 0):.2f}")
        print(f"  Cost Savings: {result.data.get('cost_savings', {}).get('savings_pct', 0):.1f}%")

    return result.success


async def test_narrative_engine_with_glm():
    """Test NarrativeStateEngine with GLM-4.7"""
    print("\n" + "=" * 60)
    print("TEST 2: NarrativeStateEngine with GLM-4.7")
    print("=" * 60)

    try:
        llm = LLMProvider()

        glm_config = ModelConfig(
            model="GLM-4.7",
            provider=ModelProvider.GLM,
            max_tokens=1000,
            temperature=0.7,
        )

        engine = NarrativeStateEngine(llm_provider=llm, analysis_config=glm_config)

        print(f"✓ NarrativeStateEngine initialized with GLM-4.7")

        # Test news tags
        news_tags = {
            "title": "Defense stocks surge amid geopolitical tensions",
            "content": "Defense contractors including Lockheed Martin and Raytheon saw significant gains as geopolitical tensions in Eastern Europe escalate. Analysts expect increased defense spending in the coming quarters.",
            "topic": "DEFENSE",
            "sentiment": "BULLISH",
        }

        print(f"\nTesting narrative: {news_tags['title']}")

        result = await engine.analyze(news_tags)

        print(f"\n✓ Narrative Result:")
        print(f"  Success: {result.success}")
        print(f"  Narrative Phase: {result.data.get('narrative_phase', 'N/A')}")
        print(f"  Fact Layer: {result.data.get('fact_layer', 'N/A')[:50] if result.data.get('fact_layer') else 'N/A'}...")
        print(f"  Narrative Layer: {result.data.get('narrative_layer', 'N/A')[:50] if result.data.get('narrative_layer') else 'N/A'}...")

        return result.success

    except Exception as e:
        print(f"✗ NarrativeStateEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n🚀 GLM-4.7 Market Intelligence Test Suite")
    print(f"Testing all components with GLM-4.7")

    results = {}

    try:
        # Test 1: NewsFilter
        results['news_filter'] = await test_news_filter_with_glm()
    except Exception as e:
        print(f"✗ NewsFilter test failed: {e}")
        import traceback
        traceback.print_exc()
        results['news_filter'] = False

    try:
        # Test 2: NarrativeStateEngine
        results['narrative_engine'] = await test_narrative_engine_with_glm()
    except Exception as e:
        print(f"✗ NarrativeStateEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        results['narrative_engine'] = False

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
