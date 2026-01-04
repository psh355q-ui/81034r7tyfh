"""
Kill Switch 간단 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8001"

print("1. Kill Switch 상태 확인...")
try:
    r = requests.get(f"{BASE_URL}/api/kill-switch/status", timeout=10)
    data = r.json()
    print(f"   Status: {data['status']}")
    print(f"   Enabled: {data['enabled']}")
    print(f"   Can Trade: {data['can_trade']}\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")
    exit(1)

print("2. 수동 트리거 테스트...")
try:
    r = requests.post(
        f"{BASE_URL}/api/kill-switch/activate",
        json={"reason": "MANUAL TEST", "details": {}},
        timeout=10
    )
    data = r.json()
    print(f"   ✅ Triggered!")
    print(f"   Reason: {data.get('message')}")
    print(f"   Can Trade: {data.get('status', {}).get('can_trade')}\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

print("3. 거래 차단 테스트...")
try:
    r = requests.post(
        f"{BASE_URL}/api/war-room-mvp/shadow/execute",
        json={"symbol": "AAPL", "action": "buy", "quantity": 10, "price": 150.0},
        timeout=10
    )
    if r.status_code == 403:
        print(f"   ✅ Trade blocked! (403)")
        error = r.json()
        print(f"   Reason: {error.get('detail', {}).get('reason')}\n")
    else:
        print(f"   ❌ NOT blocked! Status: {r.status_code}\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

print("4. Override 해제...")
try:
    r = requests.post(
        f"{BASE_URL}/api/kill-switch/deactivate",
        json={"manual_override_code": "OVERRIDE_2026", "reason": "Test complete"},
        timeout=10
    )
    data = r.json()
    print(f"   ✅ Deactivated!")
    print(f"   Can Trade: {data.get('status', {}).get('can_trade')}\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

print("5. 최종 상태 확인...")
try:
    r = requests.get(f"{BASE_URL}/api/kill-switch/status", timeout=10)
    data = r.json()
    print(f"   Status: {data['status']}")
    print(f"   Can Trade: {data['can_trade']}")
    print(f"\n✅ 모든 테스트 완료!")
except Exception as e:
    print(f"   ❌ Error: {e}")
