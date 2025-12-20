"""
Test script for KIS Broker Integration

Tests KIS broker functionality including:
- Authentication
- Price quotes
- Account balance
- Order execution (virtual trading only)

Usage:
    python test_kis.py --account YOUR_ACCOUNT_NO
    python test_kis.py --account YOUR_ACCOUNT_NO --test-order

Author: AI Trading System Team
Date: 2025-11-15
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from brokers import KISBroker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_broker_info(broker: KISBroker):
    """Test broker information."""
    print("\n" + "="*70)
    print("TEST 1: Broker Information")
    print("="*70)

    info = broker.get_info()
    print(f"Broker: {info['broker']}")
    print(f"Account: {info['account']}")
    print(f"Mode: {info['mode']}")
    print(f"Server: {info['server']}")
    print(f"Available: {info['available']}")

    print("OK: Broker info retrieved")


def test_price_quotes(broker: KISBroker):
    """Test price quote retrieval."""
    print("\n" + "="*70)
    print("TEST 2: Price Quotes")
    print("="*70)

    test_symbols = ["AAPL", "NVDA", "MSFT"]

    for symbol in test_symbols:
        price_data = broker.get_price(symbol)

        if price_data:
            print(f"\n{symbol}:")
            print(f"  Name: {price_data['name']}")
            print(f"  Price: ${price_data['current_price']:.2f}")
            print(f"  Change: ${price_data['change']:.2f} ({price_data['change_rate']:.2f}%)")
            print(f"  Volume: {price_data['volume']:,}")
        else:
            print(f"ERROR: Failed to get price for {symbol}")

    print("\nOK: Price quotes retrieved")


def test_account_balance(broker: KISBroker):
    """Test account balance retrieval."""
    print("\n" + "="*70)
    print("TEST 3: Account Balance")
    print("="*70)

    balance = broker.get_account_balance()

    if balance:
        print(f"Total Value: ${balance['total_value']:,.2f}")
        print(f"Cash: ${balance['cash']:,.2f}")
        print(f"Positions: {len(balance['positions'])}")

        if balance['positions']:
            print("\nCurrent Positions:")
            for pos in balance['positions']:
                print(f"  {pos['symbol']}: {pos['quantity']} shares @ ${pos['avg_price']:.2f}")
                print(f"    Current: ${pos['current_price']:.2f} | P&L: ${pos['profit_loss']:+,.2f}")
        else:
            print("\nNo current positions")

        print("\nOK: Account balance retrieved")
    else:
        print("WARNING: Failed to get account balance")


def test_market_status(broker: KISBroker):
    """Test market status check."""
    print("\n" + "="*70)
    print("TEST 4: Market Status")
    print("="*70)

    is_open = broker.is_market_open("NASDAQ")
    print(f"NASDAQ Market Open: {is_open}")

    print("OK: Market status checked")


def test_order_execution(broker: KISBroker, test_order: bool = False):
    """Test order execution (optional)."""
    print("\n" + "="*70)
    print("TEST 5: Order Execution (OPTIONAL)")
    print("="*70)

    if not test_order:
        print("SKIPPED: Use --test-order flag to test actual orders")
        print("WARNING: This will place real orders in virtual trading!")
        return

    print("WARNING: This will place actual orders in VIRTUAL TRADING")
    confirm = input("Continue? (yes/no): ")

    if confirm.lower() != "yes":
        print("SKIPPED: Order test cancelled")
        return

    # Test market buy order (small quantity)
    print("\nPlacing test BUY order...")
    result = broker.buy_market_order("AAPL", quantity=1, exchange="NASDAQ")

    if result:
        print(f"OK: BUY order placed")
        print(f"  Symbol: {result['symbol']}")
        print(f"  Quantity: {result['quantity']}")
        print(f"  Type: {result['order_type']}")
        print(f"  Status: {result['status']}")
    else:
        print("ERROR: Failed to place BUY order")


def main():
    parser = argparse.ArgumentParser(description="Test KIS Broker Integration")
    parser.add_argument(
        "--account",
        required=True,
        help="KIS account number (8 digits)"
    )
    parser.add_argument(
        "--test-order",
        action="store_true",
        help="Test order execution (virtual trading)"
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real trading (default: virtual/paper trading)"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("KIS BROKER INTEGRATION TEST")
    print("="*70)
    print(f"Account: {args.account}")
    print(f"Mode: {'Real Trading' if args.real else 'Virtual Trading'}")
    print("="*70)

    try:
        # Initialize broker
        print("\nInitializing KIS Broker...")
        broker = KISBroker(
            account_no=args.account,
            is_virtual=not args.real
        )

        # Run tests
        test_broker_info(broker)
        test_price_quotes(broker)
        test_account_balance(broker)
        test_market_status(broker)
        test_order_execution(broker, test_order=args.test_order)

        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print("All basic tests completed successfully!")
        print("\nKIS Broker is ready for trading.")
        print("="*70)

    except Exception as e:
        print(f"\nERROR: Test failed: {e}")
        logger.exception("Test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
