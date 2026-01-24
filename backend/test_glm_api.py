import os
import sys
sys.path.insert(0, '..')

from dotenv import load_dotenv
load_dotenv()

# Check API keys
glm_key = os.getenv("GLM_API_KEY") or os.getenv("ZAI_API_KEY")
print(f"GLM API Key loaded: {bool(glm_key)}")
if glm_key:
    print(f"Key length: {len(glm_key)}")
    print(f"Key prefix: {glm_key[:10]}...")

# Test LLM Provider
import asyncio
from backend.ai.llm_providers import get_llm_provider

async def test_llm():
    try:
        llm = get_llm_provider()
        print(f"\nLLM Provider initialized successfully")
        print(f"Default provider: {llm.default_config.provider}")
        
        # Test simple completion
        response = await llm.complete("Say 'Hello, test successful!'")
        print(f"\nLLM Response: {response.content}")
        return True
    except Exception as e:
        print(f"\n❌ LLM Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm())
    sys.exit(0 if success else 1)
