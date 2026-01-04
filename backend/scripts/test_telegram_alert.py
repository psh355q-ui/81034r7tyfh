"""
Telegram 알림 전송 테스트
"""
import requests
import json
import time

BASE_URL = "http://localhost:8001"

print("=" * 80)
print("Telegram Alert Test - Kill Switch Trigger")
print("=" * 80)

# 1. Kill Switch 트리거 (Telegram 알림 포함)
print("\n1. Kill Switch 활성화 (Telegram 알림 전송)...")
try:
    r = requests.post(
        f"{BASE_URL}/api/kill-switch/activate",
        json={
            "reason": "Telegram Test - Manual Trigger",
            "details": {
                "daily_loss_pct": -3.5,
                "test_mode": True
            }
        },
        timeout=15  # 더 긴 타임아웃 (Telegram 전송 시간 고려)
    )
    
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Kill Switch 트리거 성공!")
        print(f"   Message: {data.get('message')}")
        print(f"   Can Trade: {data.get('status', {}).get('can_trade')}")
        print(f"\n   📱 Telegram 메시지를 확인하세요!")
        print(f"   예상 내용:")
        print(f"   - 제목: 🚨🚨🚨 KILL SWITCH ACTIVATED")
        print(f"   - Reason: manual")
        print(f"   - Daily Loss: -3.50%")
        print(f"   - Threshold: 5.00%")
    else:
        print(f"   ❌ Failed: {r.status_code}")
        print(f"   Response: {r.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. 잠시 대기 (메시지 확인 시간)
print("\n2. 메시지 도착 대기 중...")
for i in range(5, 0, -1):
    print(f"   {i}초 남음...", end="\r")
    time.sleep(1)
print("\n")

# 3. 사용자 확인
print("3. Telegram 앱에서 메시지를 확인해주세요.")
print("   Bot에서 다음과 같은 메시지가 와야 합니다:")
print("   ┌─────────────────────────────────────────┐")
print("   │ 🚨🚨🚨 KILL SWITCH ACTIVATED 🚨🚨🚨 │")
print("   │                                         │")
print("   │ Reason: manual                          │")
print("   │ Daily Loss: -3.50%                      │")
print("   │ Threshold: 5.00%                        │")
print("   │                                         │")
print("   │ ALL TRADING HAS BEEN STOPPED            │")
print("   │                                         │")
print("   │ Manual intervention required...         │")
print("   │ ⏰ 2026-01-03 15:XX:XX                  │")
print("   └─────────────────────────────────────────┘")

# 4. Override 해제
print("\n4. Kill Switch 해제...")
try:
    r = requests.post(
        f"{BASE_URL}/api/kill-switch/deactivate",
        json={"manual_override_code": "OVERRIDE_2026", "reason": "Telegram test complete"},
        timeout=10
    )
    
    if r.status_code == 200:
        print(f"   ✅ Kill Switch 해제 성공")
    else:
        print(f"   ❌ Failed: {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("테스트 완료!")
print("=" * 80)
print("\n📱 Telegram 메시지가 도착했나요?")
print("   - Yes: Telegram 알림 시스템 정상 ✅")
print("   - No: 백엔드 로그 확인 필요 ⚠️")
