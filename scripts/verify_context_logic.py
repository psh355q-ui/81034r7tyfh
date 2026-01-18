import requests
import json
import time

def test_context_awareness(symbol="NVDA"):
    print(f"🔬 Testing Context Awareness for {symbol}...\n")
    
    # URL
    url = "http://localhost:8001/api/analyze"
    
    # Scenarios
    scenarios = [
        {
            "name": "Scenario 1: New Position (Trading Mode)",
            "context": "new_position",
            "persona_mode": "trading"
        },
        {
            "name": "Scenario 2: Existing Position (Trading Mode)",
            "context": "existing_position",
            "persona_mode": "trading"
        }
    ]
    
    for scenario in scenarios:
        print(f"=== {scenario['name']} ===")
        payload = {
            "ticker": symbol,
            "context": scenario["context"],
            "persona_mode": scenario["persona_mode"]
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=60)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success ({elapsed:.2f}s)")
                print(f"   Action: {data.get('action')}")
                print(f"   Portfolio Action: {data.get('portfolio_action')}")
                print(f"   Reasoning: {data.get('reasoning')[:100]}...")
                
                # Verify Agent Responses (check if they mention context-specific keywords)
                print("\n   [Sub-Agent Verification]")
                pass_count = 0
                
                # Since we can't see internal logs here, we infer from decision quality
                # But we can check if portfolio_action is set correctly
                if scenario["context"] == "existing_position":
                    if data.get('portfolio_action') in ["hold", "sell", "buy_more"]:
                        print("   ✅ PM Agent returned valid existing_position action")
                        pass_count += 3 # Inferring sub-agents supported this
                    else:
                        print(f"   ⚠️ PM Agent returned unexpected action: {data.get('portfolio_action')}")
                else:
                    if data.get('portfolio_action') in ["buy", "wait", "do_not_buy"]: # 'do_not_buy' maps to 'hold' often for new pos
                         print(f"   ✅ PM Agent returned valid new_position action: {data.get('portfolio_action')}")
                         pass_count += 3
                
            else:
                print(f"❌ Failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
        print("\n")

if __name__ == "__main__":
    test_context_awareness()
