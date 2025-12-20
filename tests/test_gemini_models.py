"""
Test available Gemini models with current API key
"""
from dotenv import load_dotenv
load_dotenv()

import os
import google.generativeai as genai

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key: {api_key[:10]}... (length: {len(api_key)})")

# Configure
genai.configure(api_key=api_key)

# List available models
print("\n" + "="*60)
print("Available Gemini Models:")
print("="*60)

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"\n✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description[:100]}..." if len(model.description) > 100 else f"   Description: {model.description}")
            
except Exception as e:
    print(f"❌ Error listing models: {e}")
    import traceback
    traceback.print_exc()

# Try different model names
print("\n" + "="*60)
print("Testing model names:")
print("="*60)

model_names = [
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-flash", 
    "gemini-1.5-pro",
    "gemini-pro",
    "models/gemini-1.5-flash",
    "models/gemini-2.0-flash-exp",
]

for model_name in model_names:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'OK' if you can read this")
        print(f"✅ {model_name}: {response.text[:50]}")
    except Exception as e:
        print(f"❌ {model_name}: {str(e)[:80]}")
