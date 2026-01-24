import os
import sys
sys.path.insert(0, '..')

from dotenv import load_dotenv
load_dotenv()

from backend.ai.glm_client import GLMClient
from backend.ai.llm_providers import LLMProvider

print("=" * 60)
print("GLM Configuration Check")
print("=" * 60)

# Check environment variables
print("\n[Environment Variables]")
print(f"GLM_API_KEY: {os.getenv('GLM_API_KEY', 'NOT SET')[:10]}...")
print(f"ZAI_API_KEY: {os.getenv('ZAI_API_KEY', 'NOT SET')[:10]}...")
print(f"ZAI_API_URL: {os.getenv('ZAI_API_URL', 'NOT SET')}")

# Check backend.ai.glm_client
print("\n[backend.ai.glm_client]")
try:
    client = GLMClient()
    print(f"✓ GLMClient initialized")
    print(f"  API URL: {client.api_url}")
    print(f"  Model: {client.model}")
    print(f"  API Key: {client.api_key[:10]}...")
    import asyncio
    asyncio.run(client.close())
except Exception as e:
    print(f"✗ GLMClient error: {e}")

# Check backend.ai.llm_providers
print("\n[backend.ai.llm_providers]")
try:
    provider = LLMProvider()
    print(f"✓ LLMProvider initialized")
    print(f"  Default provider: {provider.default_config.provider}")
    print(f"  Default model: {provider.default_config.model}")
    print(f"  GLM Key: {provider._glm_key[:10] if provider._glm_key else 'NOT SET'}...")
except Exception as e:
    print(f"✗ LLMProvider error: {e}")

print("\n" + "=" * 60)
