"""
Test War Room logging by calling the API

Generates war-room logs to test the logging infrastructure
"""

import requests

BASE_URL = "http://localhost:8001"

print("=" * 70)
print("War Room Logging Test")
print("=" * 70)

# Test War Room debate
print("\n🏛️ Calling War Room debate...")

try:
    response = requests.post(
        f"{BASE_URL}/api/war-room/debate",
        json={"ticker": "AAPL"},
        timeout=60
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"   ✅ Success!")
        print(f"   Session ID: {data.get('session_id')}")
        print(f"   Consensus: {data.get('consensus', {}).get('action')} ({data.get('consensus', {}).get('confidence', 0):.0%})")
        print(f"   Votes: {len(data.get('votes', []))} agents")
    else:
        print(f"   ⚠️ Error: {response.status_code}")
        print(f"   {response.text[:200]}")

except requests.exceptions.Timeout:
    print(f"   ⚠️ Timeout (this is expected - War Room takes time)")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("Check logs at:")
print("backend/ai/skills/logs/war-room/war-room-debate/")
print("=" * 70)
