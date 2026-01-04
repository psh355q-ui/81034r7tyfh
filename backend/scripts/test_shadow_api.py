"""
Shadow Trading API 상세 테스트
"""
import requests
import json

url = "http://localhost:8001/api/war-room-mvp/shadow/status"

print("📡 Calling Shadow Trading API...")
print(f"   URL: {url}\n")

try:
    response = requests.get(url, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n📊 Full Response:")
        print(json.dumps(data, indent=2))
        
        # Info 분석
        if 'info' in data:
            info = data['info']
            print("\n📋 Info Section:")
            print(f"  Session Status: {info.get('status')}")
            print(f"  Start Date: {info.get('start_date')}")
            print(f"  Initial Capital: ${info.get('initial_capital', 0):,.2f}")
            print(f"  Current Capital: ${info.get('current_capital', 0):,.2f}")
            print(f"  Available Cash: ${info.get('available_cash', 0):,.2f}")
            print(f"  Open Positions Count: {info.get('open_positions_count', 0)}")
            print(f"  Closed Trades Count: {info.get('closed_trades_count', 0)}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)

except requests.exceptions.Timeout:
    print("\n❌ Request timed out!")
except Exception as e:
    print(f"\n❌ Error: {e}")
