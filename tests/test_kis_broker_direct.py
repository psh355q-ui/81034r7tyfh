
import sys
import os
import asyncio
import logging

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env
from dotenv import load_dotenv
load_dotenv()

print(f"DEBUG: KIS_APP_KEY from env: {os.environ.get('KIS_APP_KEY', 'NOT_FOUND')[:5]}...")

# Add path
sys.path.append(os.getcwd())

from backend.brokers.kis_broker import KISBroker
from backend.trading import kis_client as kc

def test_broker():
    print("Initializing KISBroker...")
    try:
        # Correctly pass is_virtual=False argument
        broker = KISBroker("43349421-01", is_virtual=False) 
        print(f"Broker initialized. Virtual: {broker.is_virtual}, Server: {broker.svr}")
        
        print("Calling get_account_balance...")
        balance = broker.get_account_balance()
        print("Balance Result:")
        import pprint
        pprint.pprint(balance)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_broker()
