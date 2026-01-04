"""
간단한 War Room MVP API 테스트

서버가 8001 포트에서 실행 중인 상태에서 테스트
"""

import requests
import json

BASE_URL = "http://localhost:8001"

print("\n" + "="*80)
print("War Room MVP API - Quick Test")
print("="*80)

# 1. Health Check
print("\n1. Health Check...")
try:
    r = requests.get(f"{BASE_URL}/api/war-room-mvp/health", timeout=10)
    print(f"✅ Status: {r.status_code}")
    print(f"   {r.json()}")
except Exception as e:
    print(f"❌ Error: {e}")

# 2. Get Info
print("\n2. Get War Room Info...")
try:
    r = requests.get(f"{BASE_URL}/api/war-room-mvp/info", timeout=10)
    if r.status_code == 200:
        info = r.json()
        print(f"✅ Status: {r.status_code}")
        print(f"   Execution Mode: {info.get('execution_mode')}")
        print(f"   War Room Structure: {info.get('war_room_structure')}")
    else:
        print(f"❌ Status: {r.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80)
print("Test Complete!")
print("="*80)
