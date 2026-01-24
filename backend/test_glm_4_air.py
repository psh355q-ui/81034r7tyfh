import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

import asyncio
from backend.ai.llm_providers import get_llm_provider, ModelConfig, ModelProvider

async def test_glm_4_air():
    try:
        llm = get_llm_provider()
        config = ModelConfig(model="glm-4-air", provider=ModelProvider.GLM)
        print("Testing glm-4-air...")
        response = await llm.complete("Say 'Hello from glm-4-air!'", config=config)
        print(f"✅ glm-4-air Response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ glm-4-air Error: {e}")
        
        # Also test glm-4 (basic model)
        print("\nTrying basic glm-4...")
        try:
            config = ModelConfig(model="glm-4", provider=ModelProvider.GLM)
            response = await llm.complete("Say 'Hello from glm-4!'", config=config)
            print(f"✅ glm-4 Response: {response.content}")
            return True
        except Exception as e2:
            print(f"❌ glm-4 Error: {e2}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_glm_4_air())
    sys.exit(0 if success else 1)
