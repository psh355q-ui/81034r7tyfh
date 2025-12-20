#!/usr/bin/env python3
"""
Test script for Telegram Notification System

This script tests all notification features:
1. Connection test
2. Trade signals (BUY/SELL/HOLD)
3. Risk alerts
4. Execution reports
5. Daily/Weekly reports
6. System alerts

Usage:
    python test_telegram.py --token YOUR_BOT_TOKEN --chat YOUR_CHAT_ID

Author: AI Trading System
Date: 2025-11-15
"""

import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from notifications.telegram_notifier import TelegramNotifier, AlertType
    from notifications.notification_manager import NotificationManager
except ImportError:
    from telegram_notifier import TelegramNotifier, AlertType
    from notification_manager import NotificationManager

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using environment variables only.")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_connection(notifier: TelegramNotifier):
    """Test basic connection"""
    print("\n" + "="*50)
    print("1. Testing Connection")
    print("="*50)
    
    success = await notifier.test_connection()
    if success:
        print("OK: Connection test PASSED")
    else:
        print("ERROR: Connection test FAILED")
    
    return success


async def test_trade_signals(notifier: TelegramNotifier):
    """Test trade signal notifications"""
    print("\n" + "="*50)
    print("2. Testing Trade Signals")
    print("="*50)
    
    # BUY Signal
    print("Sending BUY signal...")
    await notifier.send_trade_signal(
        ticker="NVDA",
        action="BUY",
        conviction=0.85,
        reasoning="Strong AI/ML tailwinds. Data center revenue growing 150% YoY. "
                  "Multiple expansion justified by dominant market position in GPU computing. "
                  "Next earnings catalyst expected to beat estimates.",
        target_price=145.00,
        stop_loss=118.00,
        position_size=4.5,
        current_price=125.50,
    )
    print("OK: BUY signal sent")
    
    await asyncio.sleep(2)
    
    # SELL Signal
    print("Sending SELL signal...")
    await notifier.send_trade_signal(
        ticker="TSLA",
        action="SELL",
        conviction=0.72,
        reasoning="Valuation concerns amid slowing EV demand. Competition intensifying from "
                  "Chinese EV makers. Margin compression likely to continue. Recent price "
                  "rally provides exit opportunity.",
        target_price=None,
        stop_loss=None,
        position_size=None,
        current_price=245.80,
    )
    print("OK: SELL signal sent")
    
    await asyncio.sleep(2)
    
    # HOLD Signal (usually silent)
    print("Sending HOLD signal...")
    await notifier.send_trade_signal(
        ticker="AAPL",
        action="HOLD",
        conviction=0.55,
        reasoning="Fair valuation. No significant catalysts near-term. Maintain position.",
        current_price=175.20,
    )
    print("OK: HOLD signal sent")


async def test_risk_alerts(notifier: TelegramNotifier):
    """Test risk alert notifications"""
    print("\n" + "="*50)
    print("3. Testing Risk Alerts")
    print("="*50)
    
    # CRITICAL Risk
    print("Sending CRITICAL risk alert...")
    await notifier.send_risk_alert(
        ticker="COIN",
        risk_type="NON_STANDARD",
        risk_score=0.75,
        risk_factors=[
            "SEC lawsuit pending",
            "Regulatory uncertainty",
            "Insider selling detected",
            "Credit downgrade warning",
            "High executive turnover",
        ],
        action_taken="Stock BLOCKED from trading. Position filtered by pre-check.",
    )
    print("OK: CRITICAL risk alert sent")
    
    await asyncio.sleep(2)
    
    # HIGH Risk
    print("Sending HIGH risk alert...")
    await notifier.send_risk_alert(
        ticker="BA",
        risk_type="SUPPLY_CHAIN",
        risk_score=0.45,
        risk_factors=[
            "Major supplier delays",
            "Quality control issues",
            "Production bottlenecks",
        ],
        action_taken="Position size reduced by 50% (from 5% to 2.5%)",
    )
    print("OK: HIGH risk alert sent")


async def test_execution_reports(notifier: TelegramNotifier):
    """Test order execution notifications"""
    print("\n" + "="*50)
    print("4. Testing Execution Reports")
    print("="*50)
    
    # BUY execution
    print("Sending BUY execution report...")
    await notifier.send_execution_report(
        ticker="MSFT",
        side="BUY",
        quantity=25,
        avg_price=415.32,
        total_value=10383.00,
        algorithm="VWAP",
        slippage_bps=1.2,
        commission=2.50,
    )
    print("OK: BUY execution report sent")
    
    await asyncio.sleep(2)
    
    # SELL execution
    print("Sending SELL execution report...")
    await notifier.send_execution_report(
        ticker="META",
        side="SELL",
        quantity=15,
        avg_price=575.80,
        total_value=8637.00,
        algorithm="TWAP",
        slippage_bps=0.8,
        commission=1.75,
    )
    print("OK: SELL execution report sent")


async def test_portfolio_reports(notifier: TelegramNotifier):
    """Test portfolio report notifications"""
    print("\n" + "="*50)
    print("5. Testing Portfolio Reports")
    print("="*50)
    
    # Daily report
    print("Sending daily portfolio report...")
    await notifier.send_daily_report(
        portfolio_value=105_750.00,
        daily_pnl=1_250.50,
        daily_pnl_pct=1.20,
        total_return_pct=5.75,
        positions=[
            {"ticker": "NVDA", "value": 25000, "pnl_pct": 12.5},
            {"ticker": "MSFT", "value": 20000, "pnl_pct": 3.2},
            {"ticker": "AAPL", "value": 18000, "pnl_pct": -1.5},
            {"ticker": "GOOGL", "value": 15000, "pnl_pct": 5.8},
            {"ticker": "AMZN", "value": 12000, "pnl_pct": 2.1},
        ],
        cash=15750.00,
        trades_today=3,
    )
    print("OK: Daily report sent")
    
    await asyncio.sleep(2)
    
    # Weekly report
    print("Sending weekly performance report...")
    await notifier.send_weekly_report(
        start_value=100_000.00,
        end_value=105_750.00,
        weekly_return_pct=5.75,
        sharpe_ratio=2.35,
        max_drawdown_pct=2.1,
        win_rate=68.5,
        total_trades=12,
        best_trade={"ticker": "NVDA", "return_pct": 8.5},
        worst_trade={"ticker": "TSLA", "return_pct": -3.2},
    )
    print("OK: Weekly report sent")


async def test_system_alerts(notifier: TelegramNotifier):
    """Test system alert notifications"""
    print("\n" + "="*50)
    print("6. Testing System Alerts")
    print("="*50)
    
    # Startup message
    print("Sending system startup message...")
    await notifier.send_startup_message(
        version="1.0.0",
        mode="Paper Trading",
    )
    print("OK: Startup message sent")
    
    await asyncio.sleep(2)
    
    # System alert
    print("Sending system alert...")
    await notifier.send_system_alert(
        alert_type=AlertType.HIGH,
        title="Redis Connection Lost",
        message="Feature Store cache layer disconnected.\n"
                "System is running in degraded mode with TimescaleDB only.",
        action_required="Check Redis container status: docker ps",
    )
    print("OK: System alert sent")
    
    await asyncio.sleep(2)
    
    # Kill switch
    print("Sending KILL SWITCH alert...")
    await notifier.send_kill_switch_alert(
        reason="Daily loss limit exceeded",
        daily_loss_pct=-2.5,
        threshold_pct=-2.0,
    )
    print("OK: Kill switch alert sent")


async def test_manager_integration(manager: NotificationManager):
    """Test NotificationManager integration"""
    print("\n" + "="*50)
    print("7. Testing NotificationManager Integration")
    print("="*50)
    
    # Simulate a trading decision object
    class MockDecision:
        def __init__(self):
            self.ticker = "GOOGL"
            self.action = "BUY"
            self.conviction = 0.78
            self.reasoning = "Cloud growth accelerating. AI integration showing results. " \
                            "Attractive valuation vs peers. Strong balance sheet."
            self.target_price = 185.00
            self.stop_loss = 155.00
            self.position_size = 3.5
    
    decision = MockDecision()
    
    print("Testing on_trading_decision...")
    await manager.on_trading_decision(decision, current_price=168.45)
    print("OK: Trading decision notification sent")
    
    await asyncio.sleep(2)
    
    # Test risk detection
    print("Testing on_risk_detected...")
    await manager.on_risk_detected(
        ticker="INTC",
        risk_type="OPERATIONAL",
        risk_score=0.55,
        risk_factors=[
            "Factory delays in new process node",
            "Market share loss to AMD/ARM",
            "High CapEx requirements",
        ],
        action_taken="Position size reduced to 2.5%",
    )
    print("OK: Risk detection notification sent")


async def run_all_tests(bot_token: str, chat_id: str):
    """Run all notification tests"""
    print("\n" + "="*50)
    print("AI Trading System - Telegram Notification Tests")
    print("="*50)
    print(f"Bot Token: {bot_token[:10]}...")
    print(f"Chat ID: {chat_id}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create notifier
    notifier = TelegramNotifier(bot_token, chat_id)
    manager = NotificationManager(bot_token, chat_id)
    
    # Run tests
    try:
        # Test 1: Connection
        if not await test_connection(notifier):
            print("\nERROR: Connection failed. Please check your bot token and chat ID.")
            return
        
        # Test 2: Trade signals
        await test_trade_signals(notifier)
        
        # Test 3: Risk alerts
        await test_risk_alerts(notifier)
        
        # Test 4: Execution reports
        await test_execution_reports(notifier)
        
        # Test 5: Portfolio reports
        await test_portfolio_reports(notifier)
        
        # Test 6: System alerts
        await test_system_alerts(notifier)
        
        # Test 7: Manager integration
        await test_manager_integration(manager)
        
        # Summary
        print("\n" + "="*50)
        print("Test Summary")
        print("="*50)
        stats = notifier.get_stats()
        print(f"Total messages sent: {stats['total_sent']}")
        print(f"Failed messages: {stats['failed']}")
        print(f"Rate limited: {stats['rate_limited']}")
        print("\nOK: All tests completed successfully!")
        print("\nCheck your Telegram chat for the notifications.")
        
    except Exception as e:
        print(f"\nERROR: Test failed with error: {e}")
        raise


async def interactive_test(bot_token: str, chat_id: str):
    """Interactive test mode"""
    print("\n" + "="*50)
    print("Interactive Telegram Test Mode")
    print("="*50)
    
    notifier = TelegramNotifier(bot_token, chat_id)
    
    while True:
        print("\nOptions:")
        print("1. Send custom message")
        print("2. Send BUY signal")
        print("3. Send SELL signal")
        print("4. Send risk alert")
        print("5. Send daily report")
        print("6. Send system alert")
        print("7. View stats")
        print("0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "0":
            print("Goodbye!")
            break
        
        elif choice == "1":
            msg = input("Enter message: ")
            await notifier.send_message(f"📝 <b>Custom Message</b>\n\n{msg}")
            print("OK: Sent!")
        
        elif choice == "2":
            ticker = input("Ticker: ").upper()
            await notifier.send_trade_signal(
                ticker=ticker,
                action="BUY",
                conviction=0.8,
                reasoning="Test BUY signal",
                current_price=100.00,
            )
            print("OK: BUY signal sent!")
        
        elif choice == "3":
            ticker = input("Ticker: ").upper()
            await notifier.send_trade_signal(
                ticker=ticker,
                action="SELL",
                conviction=0.75,
                reasoning="Test SELL signal",
                current_price=100.00,
            )
            print("OK: SELL signal sent!")
        
        elif choice == "4":
            ticker = input("Ticker: ").upper()
            await notifier.send_risk_alert(
                ticker=ticker,
                risk_type="TEST",
                risk_score=0.65,
                risk_factors=["Test risk factor"],
                action_taken="Test action",
            )
            print("OK: Risk alert sent!")
        
        elif choice == "5":
            await notifier.send_daily_report(
                portfolio_value=100000,
                daily_pnl=500,
                daily_pnl_pct=0.5,
                total_return_pct=2.0,
                positions=[],
                cash=50000,
                trades_today=0,
            )
            print("OK: Daily report sent!")
        
        elif choice == "6":
            msg = input("Alert message: ")
            await notifier.send_system_alert(
                alert_type=AlertType.MEDIUM,
                title="Test Alert",
                message=msg,
            )
            print("OK: System alert sent!")
        
        elif choice == "7":
            stats = notifier.get_stats()
            print(f"\nStatistics:")
            print(f"  Total sent: {stats['total_sent']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Rate limited: {stats['rate_limited']}")
        
        else:
            print("Invalid option")


def main():
    parser = argparse.ArgumentParser(description="Test Telegram notifications")
    parser.add_argument("--token", help="Telegram Bot Token (or set TELEGRAM_BOT_TOKEN env var)")
    parser.add_argument("--chat", help="Telegram Chat ID (or set TELEGRAM_CHAT_ID env var)")
    parser.add_argument("--mode", choices=["full", "interactive"], default="full",
                       help="Test mode: full (run all tests) or interactive")

    args = parser.parse_args()

    # Get token and chat_id from args or environment
    token = args.token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = args.chat or os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        print("ERROR: Telegram Bot Token not provided")
        print("   Use --token argument or set TELEGRAM_BOT_TOKEN environment variable")
        sys.exit(1)

    if not chat_id:
        print("ERROR: Telegram Chat ID not provided")
        print("   Use --chat argument or set TELEGRAM_CHAT_ID environment variable")
        sys.exit(1)

    print(f"Using Bot Token: {token[:10]}...")
    print(f"Using Chat ID: {chat_id}")
    print()

    if args.mode == "full":
        asyncio.run(run_all_tests(token, chat_id))
    else:
        asyncio.run(interactive_test(token, chat_id))


if __name__ == "__main__":
    main()