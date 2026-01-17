"""
Debug script to see actual response_text passed to parsing functions
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from backend.ai.glm_client import GLMClient


async def debug_response_content():
    """Check what content/reasoning_content GLM returns"""
    print("\n" + "=" * 60)
    print("DEBUG: GLM Response Content Structure")
    print("=" * 60)

    client = GLMClient()

    # Test prompt
    prompt = """Analyze risk for AAPL and respond in JSON format with these fields:
    - risk_level (low/medium/high/extreme)
    - confidence (0.0-1.0)
    - reasoning (brief explanation)"""

    response = await client.chat(
        messages=[
            {"role": "system", "content": "You are a risk analyst. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.3
    )

    print("\n" + "-" * 60)
    print("RAW RESPONSE:")
    print("-" * 60)
    import json
    print(json.dumps(response, indent=2, ensure_ascii=False)[:3000])

    print("\n" + "-" * 60)
    print("MESSAGE DETAILS:")
    print("-" * 60)
    message = response["choices"][0]["message"]

    print(f"Has 'content': {('content' in message)}")
    print(f"Has 'reasoning_content': {('reasoning_content' in message)}")

    content = message.get("content", "")
    reasoning_content = message.get("reasoning_content", "")

    print(f"\nContent length: {len(content)}")
    print(f"Reasoning content length: {len(reasoning_content)}")

    if content:
        print(f"\n--- CONTENT (first 500 chars) ---\n{content[:500]}")
    if reasoning_content:
        print(f"\n--- REASONING_CONTENT (first 500 chars) ---\n{reasoning_content[:500]}")

    # Test which one contains JSON
    import re
    combined = content or reasoning_content
    json_match = re.search(r'\{.*\}', combined, re.DOTALL)
    if json_match:
        print(f"\n--- FOUND JSON (first 300 chars) ---\n{json_match.group(0)[:300]}")
    else:
        print("\n--- NO JSON FOUND ---")

    await client.close()


async def main():
    await debug_response_content()


if __name__ == "__main__":
    asyncio.run(main())
