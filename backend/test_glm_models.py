import os
import sys
sys.path.insert(0, '..')

from dotenv import load_dotenv
load_dotenv()

import asyncio
from backend.ai.llm_providers import get_llm_provider, ModelConfig, ModelProvider

async def test_models():
    """Test various GLM model names to find which ones work"""
    llm = get_llm_provider()
    
    # Common GLM model names to try
    models_to_test = [
        "glm-4-plus",
        "glm-4-flash", 
        "glm-4",
        "glm-4-air",
        "glm-4-airx",
        "glm-4-0520",
        "glm-4v"
    ]
    
    working_models = []
    
    for model_name in models_to_test:
        try:
            print(f"\nTesting {model_name}...")
            config = ModelConfig(model=model_name, provider=ModelProvider.GLM)
            response = await llm.complete("Say 'OK'", config=config)
            print(f"✅ {model_name} works! Response: {response.content[:50]}")
            working_models.append(model_name)
        except Exception as e:
            error_msg = str(e)
            if "模型不存在" in error_msg or "does not exist" in error_msg:
                print(f"❌ {model_name} - Model does not exist")
            elif "余额不足" in error_msg or "insufficient_quota" in error_msg:
                print(f"⚠️ {model_name} - Exists but quota exhausted")
                working_models.append(f"{model_name} (quota issue)")
            else:
                print(f"❌ {model_name} - Error: {error_msg[:100]}")
    
    print(f"\n\n=== Summary ===")
    print(f"Working models: {working_models}")
    return working_models

if __name__ == "__main__":
    result = asyncio.run(test_models())
