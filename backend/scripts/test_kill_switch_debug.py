"""
Kill Switch 디버그 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8001"

print("=" * 80)
print("Kill Switch Debug Test")
print("=" * 80)

# 1. 초기 상태
print("\n1. 초기 상태 확인")
r = requests.get(f"{BASE_URL}/api/kill-switch/status", timeout=10)
data = r.json()
print(f"   Status: {data['status']}")
print(f"   Can Trade: {data['can_trade']}")
print(f"   Triggered At: {data.get('triggered_at', 'None')}")

# 2. 수동 트리거
print("\n2. 수동 트리거 (MANUAL)")
r = requests.post(
    f"{BASE_URL}/api/kill-switch/trigger",
    json={"reason": "MANUAL"},
    timeout=10
)
trigger_data = r.json()
print(f"   Response: {json.dumps(trigger_data, indent=2)}")

# 3. 트리거 직후 상태 확인
print("\n3. 트리거 직후 상태 확인")
r = requests.get(f"{BASE_URL}/api/kill-switch/status", timeout=10)
status_after = r.json()
print(f"   Status: {status_after['status']}")
print(f"   Can Trade: {status_after['can_trade']}")
print(f"   Trigger Reason: {status_after.get('trigger_reason', 'None')}")
print(f"   Triggered At: {status_after.get('triggered_at', 'None')}")

# 4. 거래 시도
print("\n4. 거래 시도 (should be BLOCKED)")
r = requests.post(
    f"{BASE_URL}/api/war-room-mvp/shadow/execute",
    json={"symbol": "TEST", "action": "buy", "quantity": 1, "price": 100.0},
    timeout=10
)
print(f"   Status Code: {r.status_code}")
if r.status_code == 403:
    print(f"   ✅ BLOCKED!")
    error = r.json()
    print(f"   Error: {error}")
elif r.status_code == 200:
    print(f"   ❌ NOT BLOCKED!")
    result = r.json()
    print(f"   Result: {result}")
else:
    print(f"   ⚠️  Unexpected: {r.status_code}")
    print(f"   Response: {r.text}")

# 5. Override 해제
print("\n5. Override 해제")
r = requests.post(
    f"{BASE_URL}/api/kill-switch/deactivate",
    json={"override_code": "OVERRIDE_2026"},
    timeout=10
)
print(f"   Status Code: {r.status_code}")
if r.status_code == 200:
    deactivate_data = r.json()
    print(f"   Can Trade: {deactivate_data.get('can_trade')}")

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
