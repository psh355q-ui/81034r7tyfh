"""
Test Enhanced News Processing Pipeline with GLM-4.7

This test validates complete pipeline with all components initialized.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, '..')

from backend.api.intelligence_router import get_enhanced_pipeline


async def test_enhanced_pipeline():
    """Test Enhanced News Processing Pipeline with GLM-4.7"""
    print("\n" + "=" * 60)
    print("TEST: Enhanced News Processing Pipeline with GLM-4.7")
    print("=" * 60)

    try:
        # Get enhanced pipeline (singleton)
        pipeline = get_enhanced_pipeline()

        print(f"✓ EnhancedNewsProcessingPipeline initialized")
        print(f"  Name: {pipeline.name}")
        print(f"  Phase: {pipeline.phase}")

        # Test article
        article = {
            "title": "AI Infrastructure Stocks Rally on Government Spending",
            "content": "AI infrastructure stocks surged today following reports of increased government spending on AI research and development. Major tech companies including NVIDIA, AMD, and Intel saw significant gains as investors anticipate new contracts for AI chip manufacturing and data center infrastructure.",
        }

        print(f"\nTesting article: {article['title']}")

        # Process article
        result = await pipeline.process_article(article)

        print(f"\n✓ Pipeline Result:")
        print(f"  Success: {result.success}")
        print(f"  Processing Time: {result.processing_time_ms}ms")

        if result.success:
            print(f"\n  Final Insight:")
            print(f"    {result.final_insight[:200]}...")

            if result.contrarian_view:
                print(f"\n  Contrarian View:")
                print(f"    Bull Case: {result.contrarian_view.bull_case or 'N/A'}")
                print(f"    Bear Case: {result.contrarian_view.bear_case or 'N/A'}")
                print(f"    Key Risks: {len(result.contrarian_view.key_risks)} risks identified")

            if result.invalidation_conditions:
                print(f"\n  Invalidation Conditions:")
                for condition in result.invalidation_conditions:
                    print(f"    - {condition}")

            if result.failure_triggers:
                print(f"\n  Failure Triggers:")
                for trigger in result.failure_triggers:
                    print(f"    - {trigger}")

            # Show stage results
            print(f"\n  Stage Results:")
            for stage_name, stage_result in result.stages.items():
                print(f"    {stage_name}: {'✓' if stage_result.success else '✗'}")
                if stage_result.success and stage_name in ["narrative", "market_confirm"]:
                    print(f"      Data: {stage_result.data}")

        else:
            print(f"\n  Errors: {result.stages}")

        return result.success

    except Exception as e:
        print(f"✗ Enhanced Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run test"""
    print("\n🚀 Enhanced News Processing Pipeline Test")
    print(f"Testing complete pipeline with GLM-4.7")

    success = await test_enhanced_pipeline()

    print("\n" + "=" * 60)
    if success:
        print("✓ Test PASSED - Enhanced News Pipeline is working correctly!")
    else:
        print("✗ Test FAILED - Please review errors above")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
