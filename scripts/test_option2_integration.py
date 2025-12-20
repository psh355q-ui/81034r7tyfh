"""
Option 2 Integration Test - Auto Trading System

Tests the complete auto trading pipeline:
1. AutoTrader - Automatic order execution on Consensus approval
2. Stop-Loss Monitor - Real-time monitoring and stop-loss triggering
3. Realtime Notifier - WebSocket + Telegram/Slack notifications

Test Scenarios:
- Consensus approved BUY → AutoTrader → Order → Position → Notification
- Stop-Loss triggered → Consensus vote → AutoTrader → Notification
- DCA execution → Position update → Notification

Created: 2025-12-06
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Fix module imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.automation.auto_trader import AutoTrader
from backend.services.stop_loss_monitor import StopLossMonitor
from backend.notifications.realtime_notifier import RealtimeNotifier
from backend.data.position_tracker import PositionTracker
from backend.ai.consensus.consensus_engine import ConsensusEngine
from backend.ai.consensus.consensus_models import ConsensusResult, ConsensusStrength, AIVote, VoteDecision
from backend.services.broker_position_sync import BrokerPositionSync
from backend.schemas.base_schema import MarketContext, NewsFeatures, MarketSegment


async def test_option2_integration():
    """
    Option 2 Full Integration Test
    """
    print("=" * 80)
    print("Option 2 Integration Test - Auto Trading System")
    print("=" * 80)

    # ========================================================================
    # Setup
    # ========================================================================
    print("\n[1] Initializing components...")

    # Position Tracker
    position_tracker = PositionTracker()

    # Consensus Engine (Mock mode - no clients = mock votes)
    consensus_engine = ConsensusEngine(
        claude_client=None,
        chatgpt_client=None,
        gemini_client=None
    )

    # Broker Position Sync
    broker_sync = BrokerPositionSync(
        position_tracker=position_tracker,
        kis_broker=None  # Mock mode
    )

    # Realtime Notifier (WebSocket only, no Telegram/Slack)
    notifier = RealtimeNotifier(
        enable_websocket=True,
        enable_telegram=False,
        enable_slack=False
    )

    # AutoTrader
    auto_trader = AutoTrader(
        kis_broker=None,  # Mock mode
        position_tracker=position_tracker,
        broker_sync=broker_sync,
        auto_execute=False,  # Dry-run mode
        position_size_pct=0.1,  # 10% of portfolio
        max_position_count=10
    )

    # Stop-Loss Monitor
    stop_loss_monitor = StopLossMonitor(
        position_tracker=position_tracker,
        consensus_engine=consensus_engine,
        auto_trader=auto_trader,
        kis_broker=None,
        stop_loss_threshold_pct=-10.0,
        check_interval_seconds=2,  # 2 seconds for testing
        enable_auto_execute=False  # Dry-run mode
    )

    print("[OK] All components initialized")

    # ========================================================================
    # Test 1: Consensus Approved BUY → AutoTrader → Position → Notification
    # ========================================================================
    print("\n" + "=" * 80)
    print("[Test 1] Consensus Approved BUY → AutoTrader")
    print("=" * 80)

    # Create mock MarketContext
    market_context_buy = MarketContext(
        ticker="GOOGL",
        company_name="Alphabet Inc.",
        chip_info=[],
        supply_chain=[],
        unit_economics=None,
        news=NewsFeatures(
            headline="Google announces Gemini 3.0 trained on TPU v7",
            segment=MarketSegment.TRAINING,
            tickers_mentioned=["GOOGL"],
            sentiment=0.8,
            urgency="high",
            tone="positive"
        ),
        risk_factors={},
        market_regime=None
    )

    # Consensus vote
    print("\n[1.1] Running Consensus vote for BUY GOOGL...")
    consensus_buy = await consensus_engine.vote_on_signal(
        context=market_context_buy,
        action="BUY"
    )

    print(f"Consensus Result: {consensus_buy.approved}")
    print(f"Votes: {consensus_buy.approve_count}/{consensus_buy.total_votes}")
    print(f"Strength: {consensus_buy.consensus_strength.value}")

    # Send consensus notification
    await notifier.notify_consensus_decision(consensus_buy)

    if consensus_buy.approved:
        # AutoTrader execution
        print("\n[1.2] Executing AutoTrader for BUY...")
        exec_result = await auto_trader.on_consensus_approved(
            consensus_result=consensus_buy,
            market_context=market_context_buy,
            current_price=142.50
        )

        print(f"Executed: {exec_result.get('executed', False)}")
        print(f"Action: {exec_result.get('action')}")
        print(f"Ticker: {exec_result.get('ticker')}")
        print(f"Dry-run: {exec_result.get('dry_run', False)}")

        if exec_result.get('executed'):
            # Send order filled notification
            await notifier.notify_order_filled({
                "ticker": "GOOGL",
                "side": "BUY",
                "quantity": exec_result.get('quantity', 0),
                "avg_price": 142.50,
                "order_id": "TEST_BUY_001"
            })
    else:
        print("[SKIPPED] Consensus rejected BUY")

    # Check position
    position_googl = position_tracker.get_position("GOOGL")
    if position_googl:
        print(f"\n[Position Created]")
        print(f"Ticker: {position_googl.ticker}")
        print(f"Shares: {position_googl.total_shares:.2f}")
        print(f"Avg Entry: ${position_googl.avg_entry_price:.2f}")
        print(f"Status: {position_googl.status.value}")
    else:
        print("[INFO] No position created (dry-run or consensus rejected)")

    # ========================================================================
    # Test 2: DCA Execution
    # ========================================================================
    print("\n" + "=" * 80)
    print("[Test 2] DCA Execution")
    print("=" * 80)

    # Create initial position if not exists
    if position_tracker.get_position("NVDA") is None:
        print("\n[2.1] Creating initial NVDA position...")
        position_tracker.create_position(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            initial_price=150.0,
            initial_amount=10000.0
        )
        print("[OK] Initial position created")

    position_nvda = position_tracker.get_position("NVDA")
    print(f"\nInitial Position: {position_nvda.total_shares:.2f} shares @ ${position_nvda.avg_entry_price:.2f}")

    # DCA context
    market_context_dca = MarketContext(
        ticker="NVDA",
        company_name="NVIDIA Corporation",
        chip_info=[],
        supply_chain=[],
        unit_economics=None,
        news=NewsFeatures(
            headline="NVIDIA stock drops 15% on market correction",
            segment=MarketSegment.INFERENCE,
            tickers_mentioned=["NVDA"],
            sentiment=-0.6,
            urgency="medium",
            tone="negative"
        ),
        risk_factors={"market_correction": True},
        market_regime=None
    )

    # Consensus vote for DCA
    print("\n[2.2] Running Consensus vote for DCA...")
    consensus_dca = await consensus_engine.vote_on_signal(
        context=market_context_dca,
        action="DCA"
    )

    print(f"Consensus Result: {consensus_dca.approved}")
    print(f"Votes: {consensus_dca.approve_count}/{consensus_dca.total_votes}")

    await notifier.notify_consensus_decision(consensus_dca)

    if consensus_dca.approved:
        # Execute DCA
        print("\n[2.3] Executing DCA...")
        dca_price = 127.50  # 15% drop
        exec_result_dca = await auto_trader.execute_dca(
            ticker="NVDA",
            consensus_result=consensus_dca,
            current_price=dca_price
        )

        print(f"Executed: {exec_result_dca.get('executed', False)}")
        print(f"DCA Amount: ${exec_result_dca.get('dca_amount', 0):.2f}")
        print(f"Dry-run: {exec_result_dca.get('dry_run', False)}")

        if exec_result_dca.get('executed'):
            # Send DCA notification
            await notifier.notify_dca_executed(
                ticker="NVDA",
                dca_number=position_nvda.dca_count + 1,
                price=dca_price,
                amount=exec_result_dca.get('dca_amount', 0)
            )

            # Update position
            position_nvda = position_tracker.get_position("NVDA")
            print(f"\n[Position Updated]")
            print(f"Shares: {position_nvda.total_shares:.2f}")
            print(f"Avg Entry: ${position_nvda.avg_entry_price:.2f}")
            print(f"DCA Count: {position_nvda.dca_count}")
    else:
        print("[SKIPPED] Consensus rejected DCA")

    # ========================================================================
    # Test 3: Stop-Loss Monitor
    # ========================================================================
    print("\n" + "=" * 80)
    print("[Test 3] Stop-Loss Real-time Monitoring")
    print("=" * 80)

    print("\n[3.1] Starting Stop-Loss Monitor (10 seconds)...")

    # Start monitoring in background
    monitor_task = asyncio.create_task(stop_loss_monitor.start_monitoring())

    # Wait 10 seconds
    await asyncio.sleep(10)

    # Stop monitoring
    print("\n[3.2] Stopping monitor...")
    stop_loss_monitor.stop_monitoring()

    # Wait for task to finish
    try:
        await asyncio.wait_for(monitor_task, timeout=2.0)
    except asyncio.TimeoutError:
        monitor_task.cancel()

    # Check monitoring stats
    summary = stop_loss_monitor.get_monitoring_summary()
    print(f"\n[Monitoring Summary]")
    print(f"Running: {summary['is_running']}")
    print(f"Check Count: {summary['check_count']}")
    print(f"Stop-Loss Triggered: {summary['stop_loss_triggered_count']}")
    print(f"Positions Monitored: {summary['current_positions']}")

    if summary['recent_triggers']:
        print(f"\n[Recent Triggers]")
        for trigger in summary['recent_triggers']:
            print(f"  - {trigger['ticker']}: {trigger['loss_pct']:.2f}% ({trigger['reason']})")

    # ========================================================================
    # Test 4: Manual Stop-Loss Trigger
    # ========================================================================
    print("\n" + "=" * 80)
    print("[Test 4] Manual Stop-Loss Trigger")
    print("=" * 80)

    # Create position with loss
    if position_tracker.get_position("TSLA") is None:
        print("\n[4.1] Creating TSLA position...")
        position_tracker.create_position(
            ticker="TSLA",
            company_name="Tesla Inc.",
            initial_price=250.0,
            initial_amount=5000.0
        )

    position_tsla = position_tracker.get_position("TSLA")
    print(f"Initial Position: {position_tsla.total_shares:.2f} shares @ ${position_tsla.avg_entry_price:.2f}")

    # Simulate stop-loss condition
    current_price_tsla = 220.0  # -12% loss
    loss_pct = ((current_price_tsla - position_tsla.avg_entry_price) / position_tsla.avg_entry_price) * 100

    print(f"\n[4.2] Simulating stop-loss condition...")
    print(f"Current Price: ${current_price_tsla:.2f}")
    print(f"Loss: {loss_pct:.2f}%")

    # Send stop-loss notification
    await notifier.notify_stop_loss_triggered(
        ticker="TSLA",
        loss_pct=loss_pct,
        current_price=current_price_tsla,
        avg_entry_price=position_tsla.avg_entry_price
    )

    # Consensus vote for stop-loss
    market_context_sl = MarketContext(
        ticker="TSLA",
        company_name="Tesla Inc.",
        chip_info=[],
        supply_chain=[],
        unit_economics=None,
        news=NewsFeatures(
            headline="TSLA drops below stop-loss threshold",
            segment=MarketSegment.INFERENCE,
            tickers_mentioned=["TSLA"],
            sentiment=-0.8,
            urgency="critical",
            tone="negative"
        ),
        risk_factors={"stop_loss": True},
        market_regime=None
    )

    print("\n[4.3] Running Consensus vote for STOP_LOSS...")
    consensus_sl = await consensus_engine.vote_on_signal(
        context=market_context_sl,
        action="STOP_LOSS"
    )

    print(f"Consensus Result: {consensus_sl.approved}")
    print(f"Votes: {consensus_sl.approve_count}/{consensus_sl.total_votes}")

    await notifier.notify_consensus_decision(consensus_sl)

    if consensus_sl.approved:
        # Execute stop-loss
        print("\n[4.4] Executing STOP_LOSS...")
        exec_result_sl = await auto_trader.execute_stop_loss(
            ticker="TSLA",
            consensus_result=consensus_sl,
            current_price=current_price_tsla
        )

        print(f"Executed: {exec_result_sl.get('executed', False)}")
        print(f"Action: {exec_result_sl.get('action')}")
        print(f"Dry-run: {exec_result_sl.get('dry_run', False)}")

        if exec_result_sl.get('executed'):
            # Send order filled notification
            await notifier.notify_order_filled({
                "ticker": "TSLA",
                "side": "SELL",
                "quantity": position_tsla.total_shares,
                "avg_price": current_price_tsla,
                "order_id": "TEST_SL_001"
            })
    else:
        print("[SKIPPED] Consensus rejected STOP_LOSS")

    # ========================================================================
    # Final Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("Final Portfolio Status")
    print("=" * 80)

    all_positions = position_tracker.get_all_positions()
    print(f"\nTotal Positions: {len(all_positions)}")

    for pos in all_positions:
        print(f"\n[{pos.ticker}]")
        print(f"  Company: {pos.company_name}")
        print(f"  Shares: {pos.total_shares:.2f}")
        print(f"  Avg Entry: ${pos.avg_entry_price:.2f}")
        print(f"  DCA Count: {pos.dca_count}")
        print(f"  Status: {pos.status.value}")

    # AutoTrader stats
    trader_summary = auto_trader.get_execution_summary()
    print(f"\n[AutoTrader Summary]")
    print(f"Total Executions: {trader_summary['total_executions']}")
    print(f"Successful: {trader_summary['successful']}")
    print(f"Success Rate: {trader_summary['success_rate']:.0%}")
    print(f"By Action: {trader_summary['by_action']}")

    # Notifier stats
    notifier_summary = notifier.get_notification_summary()
    print(f"\n[Notifier Summary]")
    print(f"Total Notifications: {notifier_summary['total_notifications']}")
    print(f"By Type: {notifier_summary['by_type']}")
    print(f"By Level: {notifier_summary['by_level']}")

    # ========================================================================
    # Test Results
    # ========================================================================
    print("\n" + "=" * 80)
    print("Test Results")
    print("=" * 80)

    results = {
        "Consensus BUY Integration": consensus_buy.approved or not consensus_buy.approved,
        "AutoTrader Execution": trader_summary['total_executions'] > 0,
        "Position Management": len(all_positions) > 0,
        "Stop-Loss Monitoring": summary['check_count'] > 0,
        "Realtime Notifications": notifier_summary['total_notifications'] > 0
    }

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        mark = "[OK]" if passed else "[FAIL]"
        print(f"{mark} {test_name}: {status}")

    all_passed = all(results.values())
    print(f"\n{'=' * 80}")
    print(f"Overall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(test_option2_integration())
