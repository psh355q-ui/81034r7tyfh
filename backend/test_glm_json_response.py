"""
Test GLM-4.7 JSON Response

This test validates GLM-4.7 can respond in valid JSON format.
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


async def test_glm_json_response():
    """Test GLM-4.7 JSON response"""
    print("\n" + "=" * 60)
    print("TEST: GLM-4.7 JSON Response")
    print("=" * 60)

    try:
        llm = LLMProvider()

        glm_config = ModelConfig(
            model="GLM-4.7",
            provider=ModelProvider.GLM,
            max_tokens=1000,
            temperature=0.7,
        )

        # Test JSON response
        prompt = """Respond in JSON format with the following structure:
{
    "fact_layer": "Concrete facts...",
    "narrative_layer": "Market interpretation...",
    "phase": "EMERGING",
    "confidence": 0.85,
    "evidence": ["evidence1", "evidence2", "evidence3"]
}

IMPORTANT: The phase field must be one of: EMERGING, ACCELERATING, CONSENSUS, FATIGUED, REVERSING"""

        response = await llm.complete_with_system(
            system_prompt="You are a JSON API. Respond ONLY with valid JSON, no additional text.",
            user_prompt=prompt,
            config=glm_config,
        )

        print(f"\n✓ Response:")
        print(f"    {response.content[:200]}...")

        # Try to parse JSON
        import json
        try:
            parsed = json.loads(response.content)
            print(f"\n✓ JSON Parsed Successfully:")
            print(f"    phase: {parsed.get('phase', 'N/A')}")
            print(f"    confidence: {parsed.get('confidence', 'N/A')}")
            return True
        except json.JSONDecodeError as e:
            print(f"\n✗ JSON Parse Failed:")
            print(f"    Error: {e}")
            print(f"    Response: {response.content[:500]}...")
            return False

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run test"""
    print("\n🚀 GLM-4.7 JSON Response Test")
    print(f"Testing GLM-4.7 JSON format response")

    success = await test_glm_json_response()

    print("\n" + "=" * 60)
    if success:
        print("✓ Test PASSED - GLM-4.7 responds in valid JSON format!")
    else:
        print("✗ Test FAILED - GLM-4.7 does not respond in valid JSON format")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
