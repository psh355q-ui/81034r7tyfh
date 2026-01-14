
import os
import sys
import logging
from pprint import pprint

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

# Load .env explicitly
load_dotenv()

def verify_real_account():
    print("="*60)
    print("🔍 KIS Real Account Verification")
    print("="*60)

    # 1. Check Environment Variables
    kis_virtual = os.getenv("KIS_IS_VIRTUAL")
    kis_account = os.getenv("KIS_ACCOUNT_NUMBER")
    kis_app_key = os.getenv("KIS_APP_KEY")
    
    print(f"1. Environment Config:")
    print(f"   - KIS_IS_VIRTUAL (raw): {repr(kis_virtual)}")
    print(f"   - KIS_ACCOUNT_NUMBER: {kis_account[:4]}****" if kis_account else "   - KIS_ACCOUNT_NUMBER: NOT SET")
    print(f"   - KIS_APP_KEY: {'*' * 10}" if kis_app_key else "   - KIS_APP_KEY: NOT SET")
    sys.stdout.flush()

    if str(kis_virtual).lower() != 'false':
        print("\n⚠️  WARNING: KIS_IS_VIRTUAL is not 'false'. API will default to VIRTUAL server.")
    else:
        print("\n✅ KIS_IS_VIRTUAL is 'false'. Connecting to REAL server.")
    sys.stdout.flush()
    
    if not kis_account or not kis_app_key:
        print("\n❌ ERROR: Missing KIS credentials in .env")
        return

    # 2. Initialize Broker
    print("\n2. Initializing KIS Broker...")
    try:
        from backend.brokers.kis_broker import KISBroker, get_kis_broker
        
        # Force reload from env by using factory
        broker = get_kis_broker()
        
        if not broker:
            print("❌ Failed to create KISBroker instance.")
            return

        print(f"   ✅ Broker Initialized. Mode: {'Virtual' if broker.is_virtual else 'REAL'}")
        
    except Exception as e:
        print(f"❌ Broker Initialization Failed: {e}")
        return

    # 3. Fetch Balance (Multi-Exchange Check)
    print("\n3. Fetching Account Balance (NASD/NYSE/AMEX)...")
    try:
        balance = broker.get_account_balance()
        
        if not balance:
            print("❌ Failed to fetch balance (result is empty or None).")
            return

        total_value = balance.get('total_value', 0)
        cash = balance.get('cash', 0)
        positions = balance.get('positions', [])
        
        print(f"   ✅ Balance Fetch Successful")
        print(f"   - Total Value: ${total_value:,.2f}")
        print(f"   - Cash: ${cash:,.2f}")
        print(f"   - Position Count: {len(positions)}")
        
        if positions:
            print("\n   [Holdings]")
            for p in positions:
                print(f"   - {p['symbol']}: {p['quantity']} shares @ ${p['current_price']:.2f} (Val: ${p['market_value']:.2f})")
        else:
            print("\n   [Holdings]")
            print("   - No positions found.")

    except Exception as e:
        print(f"❌ Balance Fetch Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_real_account()
