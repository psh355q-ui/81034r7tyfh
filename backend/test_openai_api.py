import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

# Check API keys
openai_key = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key loaded: {bool(openai_key)}")
if openai_key:
    print(f"Key prefix: {openai_key[:15]}...")

# Test OpenAI Provider
import asyncio
from backend.ai.llm_providers import get_llm_provider

async def test_openai():
    try:
        llm = get_llm_provider()
        print(f"\nLLM Provider initialized")
        print(f"Default provider: {llm.default_config.provider.value}")
        print(f"Default model: {llm.default_config.model}")
        
        # Test simple completion
        response = await llm.complete("Say 'Hello from OpenAI!'")
        print(f"\nOpenAI Response: {response.content}")
        return True
    except Exception as e:
        print(f"\n❌ OpenAI Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai())
    sys.exit(0 if success else 1)
