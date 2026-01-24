import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

# Test GLM-4.5
import asyncio
from backend.ai.llm_providers import get_llm_provider, ModelConfig, ModelProvider

async def test_glm_45():
    try:
        llm = get_llm_provider()
        print(f"LLM Provider initialized")
        print(f"Default provider: {llm.default_config.provider.value}")
        print(f"Default model: {llm.default_config.model}")
        
        # Test with GLM-4.5
        config = ModelConfig(model="glm-4.5", provider=ModelProvider.GLM)
        response = await llm.complete("Say 'Hello from GLM-4.5!'", config=config)
        print(f"\n✅ GLM-4.5 Response: {response.content}")
        return True
    except Exception as e:
        print(f"\n❌ GLM-4.5 Error: {e}")
        
        # Try GLM-4-flash
        print("\n\nTrying GLM-4-flash...")
        try:
            config = ModelConfig(model="glm-4-flash", provider=ModelProvider.GLM)
            response = await llm.complete("Say 'Hello from GLM-4-flash!'", config=config)
            print(f"✅ GLM-4-flash Response: {response.content}")
            return True
        except Exception as e2:
            print(f"❌ GLM-4-flash Error: {e2}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_glm_45())
    sys.exit(0 if success else 1)
