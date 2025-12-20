"""
KIS API 심화 테스트
실제 API 호출 테스트 (시세 조회, 잔고 조회 등)
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


def test_oversea_price():
    """해외주식 시세 조회 테스트"""
    print("\n" + "="*70)
    print("🧪 Test: Oversea Stock Price Query")
    print("="*70)

    try:
        from backend.brokers.kis_broker import KISBroker

        broker = KISBroker(
            account_no="43349421",
            product_code="01",
            is_virtual=True
        )

        print("\n[1/2] Getting NVDA price...")
        price_data = broker.get_price("NVDA", "NASDAQ")

        if price_data:
            print("✅ Price data retrieved:")
            print(f"    - Symbol: {price_data['symbol']}")
            print(f"    - Name: {price_data['name']}")
            print(f"    - Current: ${price_data['current_price']:.2f}")
            print(f"    - Open: ${price_data['open_price']:.2f}")
            print(f"    - High: ${price_data['high_price']:.2f}")
            print(f"    - Low: ${price_data['low_price']:.2f}")
            print(f"    - Change: ${price_data['change']:.2f} ({price_data['change_rate']:.2f}%)")
            print(f"    - Volume: {price_data['volume']:,}")
        else:
            print("⚠️  No price data available (market may be closed)")

        print("\n[2/2] Getting AAPL price...")
        price_data = broker.get_price("AAPL", "NASDAQ")

        if price_data:
            print("✅ Price data retrieved:")
            print(f"    - Symbol: {price_data['symbol']}")
            print(f"    - Current: ${price_data['current_price']:.2f}")
        else:
            print("⚠️  No price data available")

        print("\n" + "="*70)
        print("✅ Oversea Price Test COMPLETED")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_oversea_balance():
    """해외주식 계좌 잔고 조회 테스트"""
    print("\n" + "="*70)
    print("🧪 Test: Oversea Account Balance")
    print("="*70)

    try:
        from backend.brokers.kis_broker import KISBroker

        broker = KISBroker(
            account_no="43349421",
            product_code="01",
            is_virtual=True
        )

        print("\n[1/1] Getting account balance...")
        balance = broker.get_account_balance()

        if balance:
            print("✅ Balance retrieved:")
            print(f"    - Total Value: ${balance['total_value']:,.2f}")
            print(f"    - Cash: ${balance['cash']:,.2f}")
            print(f"    - Positions: {len(balance['positions'])}")

            if balance['positions']:
                print("\n    📊 Positions:")
                for pos in balance['positions'][:5]:  # Show first 5
                    print(f"        • {pos['symbol']}: {pos['quantity']} shares")
                    print(f"          Avg: ${pos['avg_price']:.2f}, Current: ${pos['current_price']:.2f}")
                    print(f"          P/L: ${pos['profit_loss']:.2f} ({pos['profit_loss_rate']:.2f}%)")
            else:
                print("    ℹ️  No positions")
        else:
            print("⚠️  No balance data available")

        print("\n" + "="*70)
        print("✅ Balance Test COMPLETED")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_status():
    """시장 상태 확인 테스트"""
    print("\n" + "="*70)
    print("🧪 Test: Market Status Check")
    print("="*70)

    try:
        from backend.brokers.kis_broker import KISBroker

        broker = KISBroker(
            account_no="43349421",
            product_code="01",
            is_virtual=True
        )

        print("\n[1/1] Checking if market is open...")
        is_open = broker.is_market_open("NASDAQ")

        if is_open:
            print("✅ NASDAQ market is OPEN")
        else:
            print("⚠️  NASDAQ market is CLOSED")

        print("\n" + "="*70)
        print("✅ Market Status Test COMPLETED")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 KIS Advanced API Tests")
    print("="*70)
    print("\nThis will make REAL API calls to KIS Open API")
    print("(Virtual Trading Mode)")
    print("="*70)

    # Test 1: Price query
    price_ok = test_oversea_price()

    # Test 2: Balance query
    balance_ok = test_oversea_balance()

    # Test 3: Market status
    market_ok = test_market_status()

    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    print(f"Price Query:     {'✅ PASS' if price_ok else '❌ FAIL'}")
    print(f"Balance Query:   {'✅ PASS' if balance_ok else '❌ FAIL'}")
    print(f"Market Status:   {'✅ PASS' if market_ok else '❌ FAIL'}")
    print("="*70)

    sys.exit(0 if (price_ok and balance_ok and market_ok) else 1)
