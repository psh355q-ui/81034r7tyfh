"""
KIS API HTTP 엔드포인트 테스트

FastAPI 서버가 실행 중이어야 합니다:
    python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
"""
import requests
import json
from datetime import datetime

# Server URL - .env 파일의 APP_HOST 사용
BASE_URL = "http://192.168.50.148:8000"  # localhost 대신 실제 IP 사용
# localhost로 접속하려면 서버를 0.0.0.0으로 시작하세요:
#   python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload


def test_health_check():
    """Test 1: Health Check 엔드포인트"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)

    try:
        response = requests.get(f"{BASE_URL}/kis/health", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"   KIS Available: {data['kis_available']}")
            print(f"   Message: {data['message']}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("\n⚠️  FastAPI 서버가 실행 중인지 확인하세요:")
        print("   uvicorn backend.api.main:app --reload --port 8000")
        return False


def test_auto_trade_dry_run():
    """Test 2: Auto Trade (Dry Run)"""
    print("\n" + "="*70)
    print("TEST 2: Auto Trade (Dry Run)")
    print("="*70)

    payload = {
        "headline": "NVIDIA announces next-gen Blackwell B200 GPU",
        "body": "NVIDIA revealed its breakthrough Blackwell B200 GPU with unprecedented training performance.",
        "url": "https://investing.com/news/nvidia-blackwell",
        "is_virtual": True,
        "dry_run": True
    }

    print(f"\n📰 Request:")
    print(f"   Headline: {payload['headline']}")
    print(f"   Dry Run: {payload['dry_run']}")

    try:
        response = requests.post(
            f"{BASE_URL}/kis/auto-trade",
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            analysis = data['analysis']

            print(f"\n✅ Analysis Complete:")
            print(f"   Segment: {analysis['segment']}")
            print(f"   Final Ticker: {analysis['final_ticker']}")
            print(f"   Action: {analysis['final_action']}")
            print(f"   Confidence: {analysis['final_confidence']:.2%}")
            print(f"   Order Created: {analysis['order_created']}")

            if analysis['order_created']:
                print(f"   Order Side: {analysis['order_side']}")
                print(f"   Quantity: {analysis['order_quantity']}")

            print(f"\n💼 KIS Status:")
            print(f"   Enabled: {data['kis_enabled']}")
            print(f"   Order Executed: {data['kis_order_executed']}")
            print(f"   Mode: {data['mode']}")

            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False

    except Exception as e:
        print(f"❌ Request Error: {e}")
        return False


def test_kis_balance():
    """Test 3: KIS Balance Query"""
    print("\n" + "="*70)
    print("TEST 3: KIS Balance Query")
    print("="*70)

    try:
        response = requests.get(
            f"{BASE_URL}/kis/balance",
            params={"is_virtual": True},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            print(f"✅ Balance Retrieved:")
            print(f"   Broker: {data['broker']}")
            print(f"   Account: {data['account']}")
            print(f"   Mode: {data['mode']}")
            print(f"   Total Value: ${data['total_value']:,.2f}")
            print(f"   Cash: ${data['cash']:,.2f}")
            print(f"   Positions: {len(data['positions'])}")

            if data['positions']:
                print(f"\n   Holdings:")
                for pos in data['positions'][:5]:
                    print(f"      • {pos['symbol']}: {pos['quantity']} shares")

            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False

    except Exception as e:
        print(f"❌ Request Error: {e}")
        return False


def test_kis_price():
    """Test 4: KIS Price Query"""
    print("\n" + "="*70)
    print("TEST 4: KIS Price Query (NVDA)")
    print("="*70)

    try:
        response = requests.get(
            f"{BASE_URL}/kis/price/NVDA",
            params={
                "exchange": "NASDAQ",
                "is_virtual": True
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            print(f"✅ Price Retrieved:")
            print(f"   Symbol: {data['symbol']}")
            print(f"   Name: {data.get('name', 'N/A')}")
            print(f"   Current Price: ${data['current_price']:.2f}")
            print(f"   Change: ${data['change']:.2f} ({data['change_rate']:.2f}%)")
            print(f"   Volume: {data['volume']:,}")

            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False

    except Exception as e:
        print(f"❌ Request Error: {e}")
        return False


def main():
    """Run all API tests"""
    print("\n" + "="*70)
    print("🚀 KIS API HTTP Endpoint Tests")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test 1: Health Check
    health_ok = test_health_check()

    if not health_ok:
        print("\n⚠️  서버 연결 실패 - 테스트 중단")
        return

    # Test 2: Auto Trade
    auto_trade_ok = test_auto_trade_dry_run()

    # Test 3: Balance
    balance_ok = test_kis_balance()

    # Test 4: Price
    price_ok = test_kis_price()

    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    print(f"   Health Check:  {'✅' if health_ok else '❌'}")
    print(f"   Auto Trade:    {'✅' if auto_trade_ok else '❌'}")
    print(f"   Balance Query: {'✅' if balance_ok else '❌'}")
    print(f"   Price Query:   {'✅' if price_ok else '❌'}")
    print("="*70)

    all_passed = health_ok and auto_trade_ok and balance_ok and price_ok

    if all_passed:
        print("\n✅ 모든 API 테스트 통과!")
    else:
        print("\n⚠️  일부 테스트 실패")

    print("\n" + "="*70)
    print("API Endpoints:")
    print("="*70)
    print(f"  Health Check:  GET  {BASE_URL}/kis/health")
    print(f"  Auto Trade:    POST {BASE_URL}/kis/auto-trade")
    print(f"  Balance:       GET  {BASE_URL}/kis/balance")
    print(f"  Price:         GET  {BASE_URL}/kis/price/{{symbol}}")
    print(f"  Manual Order:  POST {BASE_URL}/kis/manual-order")
    print(f"  Swagger UI:    {BASE_URL}/docs")
    print("="*70)


if __name__ == "__main__":
    main()
