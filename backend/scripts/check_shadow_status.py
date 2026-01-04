"""
Shadow Trading 상태 확인 (API 호출)
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def check_shadow_status():
    """Shadow Trading API 상태 확인"""
    print("\n🔍 Shadow Trading Status Check")
    print(f"   Backend: {BASE_URL}\n")
    
    try:
        # Shadow Trading 상태 API 호출
        response = requests.get(f"{BASE_URL}/api/war-room-mvp/shadow/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Info 섹션
            info = data.get('info', {})
            print("📊 Session Info:")
            print(f"  Session ID: {info.get('session_id', 'N/A')}")
            print(f"  Status: {info.get('status', 'N/A')}")
            print(f"  Start Date: {info.get('start_date', 'N/A')}")
            print(f"  Days Active: {info.get('days_active', 0)}")
            
            # Capital
            capital = info.get('capital', {})
            print(f"\n💰 Capital:")
            print(f"  Initial: ${capital.get('initial', 0):,.2f}")
            print(f"  Current: ${capital.get('current', 0):,.2f}")
            print(f"  Available: ${capital.get('available_cash', 0):,.2f}")
            print(f"  Invested: ${capital.get('invested', 0):,.2f}")
            
            # Positions
            positions = info.get('open_positions', [])
            print(f"\n💼 Open Positions: {len(positions)}")
            for pos in positions:
                print(f"  {pos['symbol']}: {pos['quantity']} shares @ ${pos['entry_price']:.2f}")
                print(f"    Stop Loss: ${pos.get('stop_loss_price', 0):.2f}")
                print(f"    Entry Date: {pos.get('entry_date', 'N/A')}")
            
            # Performance
            perf = data.get('performance', {})
            print(f"\n📈 Performance:")
            print(f"  Total Trades: {perf.get('total_trades', 0)}")
            print(f"  Win Rate: {perf.get('win_rate', 0)*100:.1f}%")
            print(f"  Profit Factor: {perf.get('profit_factor', 0):.2f}")
            print(f"  Total P&L: ${perf.get('total_pnl', 0):,.2f}")
            
            return data
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend")
        print(f"💡 Make sure backend is running on port 8001")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    check_shadow_status()
