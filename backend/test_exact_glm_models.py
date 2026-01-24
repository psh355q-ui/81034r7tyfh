import os
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

import asyncio
from backend.ai.llm_providers import get_llm_provider, ModelConfig, ModelProvider

async def test_exact_models():
    """Test with exact model names from Z.AI rate limits page"""
    llm = get_llm_provider()
    
    # Test models in order of Concurrency (highest first)
    models_to_test = [
        ("GLM-4-Plus", 20),
        ("GLM-4-32B-0414-128K", 15),  
        ("GLM-4.5", 10),
        ("GLM-4.6V", 10),
        ("GLM-4.5-Air", 5),
        ("GLM-4.5-AirX", 5),
    ]
    
    for model_name, concurrency in models_to_test:
        try:
            print(f"\n{'='*60}")
            print(f"Testing: {model_name} (Concurrency: {concurrency})")
            print(f"{'='*60}")
            
            config = ModelConfig(model=model_name, provider=ModelProvider.GLM)
            response = await llm.complete("Say 'OK'", config=config)
            
            print(f"✅ SUCCESS! {model_name} is working!")
            print(f"Response: {response.content[:100]}")
            return model_name  # Return first working model
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                if "余额不足" in error_msg or "insufficient" in error_msg.lower():
                    print(f"❌ {model_name} - 429 Rate Limit (quota issue)")
                else:
                    print(f"❌ {model_name} - 429 Too Many Requests")
            elif "400" in error_msg:
                if "模型不存在" in error_msg or "does not exist" in error_msg.lower():
                    print(f"❌ {model_name} - Model does not exist")
                else:
                    print(f"❌ {model_name} - 400 Error: {error_msg[:100]}")
            else:
                print(f"❌ {model_name} - Error: {error_msg[:100]}")
    
    print(f"\n{'='*60}")
    print("❌ ALL MODELS FAILED")
    print(f"{'='*60}")
    return None

if __name__ == "__main__":
    working_model = asyncio.run(test_exact_models())
    if working_model:
        print(f"\n✅ Use this model: {working_model}")
        sys.exit(0)
    else:
        print(f"\n❌ No working models found - GLM MAX may have oversell issues")
        sys.exit(1)
