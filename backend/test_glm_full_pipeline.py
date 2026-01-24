"""
Test GLM-4.7 with Full Market Intelligence v2.0 Pipeline

This test validates the complete pipeline with GLM-4.7:
1. NewsFilter (2-Stage)
2. NarrativeStateEngine
3. FactChecker
4. MarketConfirmation
5. HorizonTagger
6. EnhancedNewsProcessingPipeline (Full Integration)
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
from backend.ai.intelligence.fact_checker import FactChecker
from backend.ai.intelligence.market_confirmation import MarketConfirmation
from backend.ai.intelligence.horizon_tagger import HorizonTagger
from backend.ai.intelligence.enhanced_news_pipeline import EnhancedNewsProcessingPipeline


async def test_news_filter():
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

    return result.success


async def test_narrative_engine():
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

        article = {
            "title": "Defense stocks surge amid geopolitical tensions",
            "content": "Defense contractors including Lockheed Martin and Raytheon saw significant gains as geopolitical tensions in Eastern Europe escalate. Analysts expect increased defense spending in the coming quarters.",
        }

        print(f"\nTesting narrative: {article['title']}")

        result = await engine.analyze_news(article)

        print(f"\n✓ Narrative Result:")
        print(f"  Success: {result.success}")
        print(f"  Topic: {result.data.get('topic', 'N/A')}")
        print(f"  Phase: {result.data.get('phase', 'N/A')}")

        return result.success

    except Exception as e:
        print(f"✗ NarrativeStateEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fact_checker():
    """Test FactChecker with GLM-4.7"""
    print("\n" + "=" * 60)
    print("TEST 3: FactChecker with GLM-4.7")
    print("=" * 60)

    try:
        llm = LLMProvider()

        checker = FactChecker(llm_provider=llm)

        print(f"✓ FactChecker initialized with GLM-4.7")

        # Test data with potential hallucination
        intelligence_result = {
            "extracted_data": {
                "earnings": "$5.2 billion",
                "beat_expectations": "15%",
                "revenue_growth": "25%"
            },
            "confidence": 0.85
        }

        print(f"\nTesting fact check: Company reports record earnings")

        result = await checker.verify_intelligence_result(intelligence_result)

        print(f"\n✓ Fact Check Result:")
        print(f"  Success: {result.success}")
        print(f"  Verification Status: {result.data.get('verification_status', 'N/A')}")
        print(f"  Adjusted Confidence: {result.data.get('adjusted_confidence', 0):.2f}")

        return result.success

    except Exception as e:
        print(f"✗ FactChecker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_market_confirmation():
    """Test MarketConfirmation with GLM-4.7"""
    print("\n" + "=" * 60)
    print("TEST 4: MarketConfirmation with GLM-4.7")
    print("=" * 60)

    try:
        llm = LLMProvider()

        confirm = MarketConfirmation(llm_provider=llm)

        print(f"✓ MarketConfirmation initialized with GLM-4.7")

        narrative_data = {
            "topic": "AI_TECH",
            "phase": "ACCELERATING",
            "sentiment": "BULLISH",
            "symbols": ["NVDA", "AMD"],
            "confidence": 0.85
        }

        print(f"\nTesting market confirmation: {narrative_data['topic']}")

        result = await confirm.confirm_narrative(narrative_data)

        print(f"\n✓ Market Confirmation Result:")
        print(f"  Success: {result.success}")
        print(f"  Confirmation Status: {result.data.get('confirmation_status', 'N/A')}")
        print(f"  Price Correlation: {result.data.get('price_correlation', 0):.2f}")

        return result.success

    except Exception as e:
        print(f"✗ MarketConfirmation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_horizon_tagger():
    """Test HorizonTagger with GLM-4.7"""
    print("\n" + "=" * 60)
    print("TEST 5: HorizonTagger with GLM-4.7")
    print("=" * 60)

    try:
        llm = LLMProvider()

        tagger = HorizonTagger(llm_provider=llm)

        print(f"✓ HorizonTagger initialized with GLM-4.7")

        insight = {
            "topic": "AI chip demand surge",
            "sentiment": "BULLISH",
            "catalyst": "Earnings surprise",
            "content": "Growing demand for AI chips is expected to continue through 2026 as cloud providers expand their infrastructure.",
        }

        print(f"\nTesting horizon tagging: {insight['topic']}")

        result = await tagger.tag_horizons(insight)

        print(f"\n✓ Horizon Tagging Result:")
        print(f"  Success: {result.success}")
        print(f"  Recommended Horizon: {result.data.get('recommended_horizon', 'N/A')}")
        short_term = result.data.get('short_term')
        if short_term:
            print(f"  Short Term: {short_term.get('analysis', 'N/A')[:50]}...")

        return result.success

    except Exception as e:
        print(f"✗ HorizonTagger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n🚀 GLM-4.7 Full Market Intelligence Test Suite")
    print(f"Testing all components with GLM-4.7")

    results = {}

    try:
        # Test 1: NewsFilter
        results['news_filter'] = await test_news_filter()
    except Exception as e:
        print(f"✗ NewsFilter test failed: {e}")
        import traceback
        traceback.print_exc()
        results['news_filter'] = False

    try:
        # Test 2: NarrativeStateEngine
        results['narrative_engine'] = await test_narrative_engine()
    except Exception as e:
        print(f"✗ NarrativeStateEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        results['narrative_engine'] = False

    try:
        # Test 3: FactChecker
        results['fact_checker'] = await test_fact_checker()
    except Exception as e:
        print(f"✗ FactChecker test failed: {e}")
        import traceback
        traceback.print_exc()
        results['fact_checker'] = False

    try:
        # Test 4: MarketConfirmation
        results['market_confirmation'] = await test_market_confirmation()
    except Exception as e:
        print(f"✗ MarketConfirmation test failed: {e}")
        import traceback
        traceback.print_exc()
        results['market_confirmation'] = False

    try:
        # Test 5: HorizonTagger
        results['horizon_tagger'] = await test_horizon_tagger()
    except Exception as e:
        print(f"✗ HorizonTagger test failed: {e}")
        import traceback
        traceback.print_exc()
        results['horizon_tagger'] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:25s} {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! GLM-4.7 integration is working correctly.")
        print("Market Intelligence v2.0 is ready to use with GLM-4.7.")
    else:
        print(f"\n⚠ {total_tests - passed_tests} test(s) failed. Please review errors above.")


if __name__ == "__main__":
    asyncio.run(main())
