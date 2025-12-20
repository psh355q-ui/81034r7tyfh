"""
KIS API 간단 테스트
인증 및 기본 기능 확인
"""
import sys
import os
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_kis_client():
    """KIS 클라이언트 직접 테스트"""
    print("\n" + "="*70)
    print("🧪 KIS Client Test")
    print("="*70)

    try:
        # 1. Import test
        print("\n[1/4] Importing kis_client...")
        from backend.trading import kis_client
        print("✅ kis_client imported successfully")

        # 2. Config test
        print("\n[2/4] Loading configuration...")
        config = kis_client.load_config()
        print(f"✅ Config loaded: {len(config)} keys")
        print(f"    - my_app: {config.get('my_app', '')[:20]}...")
        print(f"    - my_acct_stock: {config.get('my_acct_stock', '')}")

        # 3. Authentication test (모의투자)
        print("\n[3/4] Testing authentication (Virtual Trading)...")
        success = kis_client.auth(svr="vps", product="01")

        if success:
            print("✅ Authentication successful!")
            env = kis_client.getTREnv()
            print(f"    - Token: {env.my_token[:30]}...")
            print(f"    - Account: {env.my_acct}")
            print(f"    - URL: {env.my_url}")
        else:
            print("❌ Authentication failed")
            return False

        # 4. Market data test (optional)
        print("\n[4/4] Testing market data (NVDA price)...")
        try:
            # Note: osf functions may not be available yet
            print("⏭️  Market data test skipped (not implemented yet)")
        except Exception as e:
            print(f"⚠️  Market data test error: {e}")

        print("\n" + "="*70)
        print("✅ KIS Client Test PASSED")
        print("="*70)
        return True

    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("    Check if kis_client.py exists and dependencies are installed")
        return False
    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_kis_broker():
    """KIS 브로커 클래스 테스트"""
    print("\n" + "="*70)
    print("🧪 KIS Broker Test")
    print("="*70)

    try:
        # Import broker
        print("\n[1/3] Importing KISBroker...")
        from backend.brokers.kis_broker import KISBroker, KIS_AVAILABLE

        if not KIS_AVAILABLE:
            print("❌ KIS not available")
            return False

        print("✅ KISBroker imported successfully")

        # Initialize broker (모의투자)
        print("\n[2/3] Initializing KISBroker (Virtual Trading)...")
        broker = KISBroker(
            account_no="43349421",  # From .env
            product_code="01",
            is_virtual=True
        )
        print("✅ KISBroker initialized")

        # Get broker info
        print("\n[3/3] Getting broker info...")
        info = broker.get_info()
        print(f"✅ Broker info:")
        print(f"    - Broker: {info['broker']}")
        print(f"    - Account: {info['account']}")
        print(f"    - Mode: {info['mode']}")
        print(f"    - Server: {info['server']}")
        print(f"    - Available: {info['available']}")

        print("\n" + "="*70)
        print("✅ KIS Broker Test PASSED")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test 1: kis_client 직접 테스트
    client_ok = test_kis_client()

    # Test 2: KISBroker 클래스 테스트
    if client_ok:
        broker_ok = test_kis_broker()
    else:
        print("\n⚠️  Skipping broker test (client test failed)")
        broker_ok = False

    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    print(f"KIS Client:  {'✅ PASS' if client_ok else '❌ FAIL'}")
    print(f"KIS Broker:  {'✅ PASS' if broker_ok else '❌ FAIL'}")
    print("="*70)

    sys.exit(0 if (client_ok and broker_ok) else 1)
