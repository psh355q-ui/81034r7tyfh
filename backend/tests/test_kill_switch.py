"""
Kill Switch 테스트 스크립트

Kill Switch 기능 검증:
1. 상태 조회
2. 트리거 조건 체크
3. 수동 활성화/비활성화
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_status():
    """상태 조회"""
    print("\n" + "="*80)
    print("1️⃣  Kill Switch Status")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/api/kill-switch/status")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_check_triggers():
    """트리거 조건 체크"""
    print("\n" + "="*80)
    print("2️⃣  Check Triggers (Normal State)")
    print("="*80)
    
    # Normal state
    trading_state = {
        "current_capital": 100000,
        "initial_capital": 100000,
        "daily_pnl": -1000,  # 1% loss
        "daily_trades": 5,
        "open_positions": [
            {"symbol": "NVDA", "quantity": 100, "current_price": 900}
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/kill-switch/check",
        json={"trading_state": trading_state}
    )
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_trigger_daily_loss():
    """Daily Loss 트리거"""
    print("\n" + "="*80)
    print("3️⃣  Trigger: Daily Loss (5%)")
    print("="*80)
    
    # 5% daily loss
    trading_state = {
        "current_capital": 100000,
        "initial_capital": 100000,
        "daily_pnl": -5500,  # 5.5% loss
        "daily_trades": 10,
        "open_positions": []
    }
    
    response = requests.post(
        f"{BASE_URL}/api/kill-switch/check",
        json={"trading_state": trading_state}
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    
    if result.get("should_trigger"):
        print("\n🚨 KILL SWITCH TRIGGERED!")

def test_manual_activate():
    """수동 활성화"""
    print("\n" + "="*80)
    print("4️⃣  Manual Activation")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/kill-switch/activate",
        json={
            "reason": "Manual test activation",
            "details": {"test": True}
        }
    )
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_deactivate():
    """비활성화"""
    print("\n" + "="*80)
    print("5️⃣  Deactivation (Requires Override Code)")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/kill-switch/deactivate",
        json={
            "manual_override_code": "OVERRIDE_2026",
            "reason": "Test completed"
        }
    )
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def main():
    print("\n🧪 Kill Switch Test Suite")
    print("   Backend: http://localhost:8001")
    
    try:
        # Test 1: Status
        test_status()
        
        # Test 2: Normal check
        test_check_triggers()
        
        # Test 3: Daily loss trigger
        # test_trigger_daily_loss()  # 주석: 실제 트리거는 주의
        
        # Test 4: Manual activation
        # test_manual_activate()  # 주석: 실제 활성화는 주의
        
        # Test 5: Deactivation
        # test_deactivate()  # 주석: 활성화 후에만
        
        print("\n" + "="*80)
        print("✅ Basic tests completed!")
        print("="*80)
        print("\n주의: 주석 처리된 테스트는 Kill Switch를 실제로 활성화합니다.")
        print("      실거래 중에는 절대 테스트하지 마세요!\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend")
        print("💡 Make sure backend is running: python backend/main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
