
import requests
import json
import time

url = 'http://localhost:8001/api/portfolio'
max_retries = 5
print(f"Checking {url}...")

for i in range(max_retries):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"Status Code: {response.status_code}")
            
            positions = data.get('positions', [])
            intc_found = False
            
            if positions:
                print(f"Found {len(positions)} positions:")
                for p in positions:
                    ticker = p.get('ticker', 'UNKNOWN')
                    qty = p.get('quantity', 0)
                    val = p.get('market_value', 0)
                    print(f" - {ticker}: Qty={qty}, Value=${val}")
                    
                    if "INTC" in ticker or "INTL" in ticker:
                        intc_found = True
            else:
                print("No positions found.")
                
            cash = data.get('cash', 0)
            print(f"💰 Cash Balance: ${cash}")

            if intc_found:
                print("\n✅ Verification PASSED: INTC/INTL position found.")
            elif len(positions) > 0:
                 print("\n⚠️ Verification PARTIAL: Positions found but not INTC. (Might be other holdings)")
            else:
                 print("\n❌ Verification FAILED: No positions (should have INTC).")
            
            if cash > 0:
                print(f"✅ Cash Verification SUCCESS: ${cash}")
            else:
                print(f"⚠️ Cash Verification WARNING: Cash is ${cash}")

            # Check Daily P&L
            daily_pnl = data.get('daily_pnl', 0)
            print(f"💰 Daily P&L: ${daily_pnl} (Total Portfolio)")
            
            # Check Position Daily P&L
            if positions:
                p = positions[0]
                dpnl = p.get('daily_pnl', 0)
                dpct = p.get('daily_return_pct', 0)
                print(f"  First Position Daily P&L: ${dpnl} ({dpct}%)")

            break

        else:
            print(f"Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Connection failed: {e}")
        
    print(f"Retrying in 2s... ({i+1}/{max_retries})")
    time.sleep(2)
