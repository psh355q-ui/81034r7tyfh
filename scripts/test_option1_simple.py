"""
Option 1 Integration Test: Phase A-D-E Full Pipeline

Test Scenarios:
1. News Analysis -> Deep Reasoning -> Consensus Voting
2. DCA Evaluation -> Consensus Voting -> Position Update
3. Broker Order Filled -> Position Sync

Created: 2025-12-06
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from datetime import datetime

# Logging setup
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    print("=" * 80)
    print("Option 1 Integration Test: Phase A-D-E Full Pipeline")
    print("=" * 80)

    # Import modules
    try:
        from backend.ai.strategies.deep_reasoning_strategy import DeepReasoningStrategy
        from backend.ai.consensus.consensus_engine import ConsensusEngine
        from backend.ai.strategies.dca_strategy import DCAStrategy
        from backend.data.position_tracker import PositionTracker
        from backend.services.news_event_handler import NewsEventHandler
        from backend.services.broker_position_sync import BrokerPositionSync
        from backend.schemas.base_schema import MarketContext, NewsFeatures, MarketSegment

        print("[OK] All modules imported successfully\n")

    except ImportError as e:
        print(f"[ERROR] Module import failed: {e}")
        return

    # ========================================================================
    # Step 1: Initialize Components
    # ========================================================================

    print("Step 1: Initialize Components")
    print("-" * 80)

    consensus_engine = ConsensusEngine()
    deep_reasoning = DeepReasoningStrategy(consensus_engine=consensus_engine)
    dca_strategy = DCAStrategy()
    position_tracker = PositionTracker()
    news_handler = NewsEventHandler(dca_strategy, position_tracker, consensus_engine)
    broker_sync = BrokerPositionSync(position_tracker, kis_broker=None)

    print("[OK] All components initialized\n")

    # ========================================================================
    # Step 2: News Analysis -> Deep Reasoning -> Consensus
    # ========================================================================

    print("Step 2: News Analysis -> Deep Reasoning -> Consensus")
    print("-" * 80)

    news = "Google announces Gemini 3 trained on TPU v6e with 50% better efficiency"
    print(f"News: {news}\n")

    result = await deep_reasoning.analyze_news(
        news_headline=news,
        use_consensus=True
    )

    print(f"Consensus Enabled: {result['consensus_enabled']}")
    print(f"Original Signals: {len(result['original_signals'])}")

    if result.get('consensus_results'):
        print("\nConsensus Results:")
        for cr in result['consensus_results']:
            status = "APPROVED" if cr['approved'] else "REJECTED"
            print(f"  - {status}: {cr['action']} {cr['ticker']} ({cr['votes']})")

    print(f"\nApproved Signals: {len(result['approved_signals'])}")
    for signal in result['approved_signals']:
        print(f"  - {signal['action']} {signal['ticker']}")

    print(f"\n[OK] News analysis completed ({result['processing_time_ms']:.1f}ms)\n")

    # ========================================================================
    # Step 3: Position Creation -> DCA Event
    # ========================================================================

    print("Step 3: Position Creation -> DCA Event")
    print("-" * 80)

    # Create initial position (or use existing)
    position = position_tracker.get_position("NVDA")

    if position is None:
        position_tracker.create_position(
            ticker="NVDA",
            company_name="NVIDIA",
            initial_price=150.0,
            initial_amount=10000.0
        )
        position = position_tracker.get_position("NVDA")
        print(f"[OK] Position created: NVDA @ ${position.avg_entry_price:.2f}")
    else:
        print(f"[OK] Using existing position: NVDA @ ${position.avg_entry_price:.2f}")

    print(f"     Shares: {position.total_shares:.2f}, Invested: ${position.total_invested:.2f}\n")

    # DCA event (price drop 10%)
    market_context = MarketContext(
        ticker="NVDA",
        company_name="NVIDIA",
        chip_info=[],
        supply_chain=[],
        unit_economics=None,
        news=NewsFeatures(
            headline="NVIDIA faces short-term supply chain challenges",
            segment=MarketSegment.TRAINING,
            tickers_mentioned=["NVDA"],
            sentiment=0.3,
            urgency="medium",
            tone="neutral"
        ),
        risk_factors={},
        market_regime=None
    )

    dca_result = await news_handler.on_news_event(
        ticker="NVDA",
        news_headline="NVIDIA faces short-term supply chain challenges",
        news_body="Temporary delays in H100 production",
        market_context=market_context,
        current_price=135.0  # 10% drop
    )

    print("DCA Evaluation:")
    print(f"  - Has Position: {dca_result['has_position']}")
    print(f"  - DCA Recommended: {dca_result['dca_recommended']}")

    if dca_result.get('dca_decision'):
        print(f"  - Reasoning: {dca_result['dca_decision']['reasoning']}")

    if dca_result.get('consensus_result'):
        cr = dca_result['consensus_result']
        status = "APPROVED" if cr['approved'] else "REJECTED"
        print(f"  - Consensus: {status} ({cr['votes']})")

    if dca_result.get('action_taken'):
        action = dca_result['action_taken']
        print(f"\n[OK] DCA executed: ${action['amount']:.2f} @ ${action['price']:.2f}")

    # Check updated position
    position = position_tracker.get_position("NVDA")
    pnl = position.get_unrealized_pnl(current_price=135.0)

    print(f"\nUpdated Position:")
    print(f"  - Avg Entry: ${position.avg_entry_price:.2f}")
    print(f"  - Total Shares: {position.total_shares:.2f}")
    print(f"  - DCA Count: {position.dca_count}")
    print(f"  - Unrealized P&L: ${pnl['pnl']:.2f} ({pnl['pnl_pct']:.2%})\n")

    # ========================================================================
    # Step 4: Broker Order Filled -> Position Sync
    # ========================================================================

    print("Step 4: Broker Order Filled -> Position Sync")
    print("-" * 80)

    fill_result = await broker_sync.on_order_filled(
        ticker="TSLA",
        company_name="Tesla",
        side="BUY",
        quantity=5,
        avg_price=250.0,
        order_id="KIS20241206001",
        filled_at=datetime.now()
    )

    print(f"Order Filled: {fill_result['order_id']}")
    print(f"  - Action: {fill_result['action']}")
    print(f"  - Position Updated: {fill_result['position_updated']}")

    tsla_position = position_tracker.get_position("TSLA")
    if tsla_position:
        print(f"\n[OK] TSLA Position created: {tsla_position.total_shares} shares @ ${tsla_position.avg_entry_price:.2f}\n")

    # ========================================================================
    # Step 5: Portfolio Summary
    # ========================================================================

    print("Step 5: Portfolio Summary")
    print("-" * 80)

    all_positions = position_tracker.get_all_positions()
    print(f"Total Positions: {len(all_positions)}\n")

    current_prices = {"NVDA": 135.0, "TSLA": 250.0}

    for pos in all_positions:
        current_price = current_prices.get(pos.ticker, pos.avg_entry_price)
        pnl = pos.get_unrealized_pnl(current_price=current_price)

        print(f"[{pos.ticker}]")
        print(f"  Shares: {pos.total_shares:.2f}")
        print(f"  Avg Entry: ${pos.avg_entry_price:.2f}")
        print(f"  Current: ${current_price:.2f}")
        print(f"  DCA Count: {pos.dca_count}")
        print(f"  P&L: ${pnl['pnl']:.2f} ({pnl['pnl_pct']:.2%})\n")

    # ========================================================================
    # Complete
    # ========================================================================

    print("=" * 80)
    print("Integration Test COMPLETED")
    print("=" * 80)

    print("\nIntegrated Features:")
    print("  [OK] Deep Reasoning Strategy -> Consensus")
    print("  [OK] News Event -> DCA Auto Evaluation")
    print("  [OK] Position Tracker <-> Broker Sync")

    print("\nNext Steps:")
    print("  -> Option 2: Auto Trading System")
    print("  -> Option 3: Backtesting & Performance Analysis")
    print("  -> Real environment testing with actual AI clients")


if __name__ == "__main__":
    asyncio.run(main())
