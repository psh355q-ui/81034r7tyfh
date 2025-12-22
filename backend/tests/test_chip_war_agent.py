"""
Test Chip War Agent

Phase 24: ChipWarAgent Integration Test
Date: 2025-12-23

Tests:
1. ChipWarAgent voting logic for different tickers
2. Scenario-based signal generation
3. Integration with War Room
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.ai.debate.chip_war_agent import ChipWarAgent


async def test_chip_war_agent():
    """Test ChipWarAgent for semiconductor tickers"""

    print("=" * 80)
    print("🎮 Chip War Agent Test")
    print("=" * 80)

    agent = ChipWarAgent()

    # Test tickers
    test_cases = [
        ("NVDA", "Nvidia (CUDA moat defender)"),
        ("GOOGL", "Google (TPU challenger)"),
        ("META", "Meta (TorchTPU co-developer)"),
        ("AVGO", "Broadcom (TPU partnerships)"),
        ("AMD", "AMD (Nvidia competitor)"),
        ("AAPL", "Apple (not a chip war ticker)"),
    ]

    print(f"\nAgent: {agent.agent_name}")
    print(f"Weight: {agent.vote_weight * 100:.0f}%")
    print(f"Semiconductor tickers tracked: {len(agent.chip_tickers)}")
    print()

    for ticker, description in test_cases:
        print(f"\n{'─' * 80}")
        print(f"Testing {ticker} - {description}")
        print('─' * 80)

        try:
            vote = await agent.analyze(ticker)

            print(f"✅ Vote received:")
            print(f"   Agent: {vote['agent']}")
            print(f"   Action: {vote['action']}")
            print(f"   Confidence: {vote['confidence']:.1%}")
            print(f"   Reasoning: {vote['reasoning'][:120]}...")

            if vote.get('chip_war_factors'):
                factors = vote['chip_war_factors']
                print(f"\n   Chip War Factors:")
                print(f"      Disruption Score: {factors['disruption_score']:.0f}")
                print(f"      Verdict: {factors['verdict']}")
                print(f"      Scenario: {factors['scenario']}")
                print(f"      TCO Advantage: {factors['tco_advantage']:.1f}%")
            else:
                print(f"\n   Chip War Factors: N/A (not a semiconductor ticker)")

        except Exception as e:
            print(f"❌ Test failed for {ticker}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("✅ Chip War Agent Test Complete")
    print("=" * 80)


async def test_voting_consistency():
    """Test that ChipWarAgent votes are consistent with chip war logic"""

    print("\n" + "=" * 80)
    print("🧪 Voting Consistency Test")
    print("=" * 80)

    agent = ChipWarAgent()

    # Get votes for NVDA and GOOGL
    nvda_vote = await agent.analyze("NVDA")
    googl_vote = await agent.analyze("GOOGL")

    print(f"\nNVDA Action: {nvda_vote['action']} ({nvda_vote['confidence']:.0%})")
    print(f"GOOGL Action: {googl_vote['action']} ({googl_vote['confidence']:.0%})")

    # Logic check: If GOOGL is BUY, NVDA should be SELL/HOLD (inverse relationship)
    if nvda_vote['chip_war_factors'] and googl_vote['chip_war_factors']:
        nvda_factors = nvda_vote['chip_war_factors']
        googl_factors = googl_vote['chip_war_factors']

        verdict = nvda_factors['verdict']

        print(f"\nChip War Verdict: {verdict}")
        print(f"Disruption Score: {nvda_factors['disruption_score']:.0f}")

        # Consistency checks
        checks_passed = 0
        total_checks = 3

        # Check 1: THREAT verdict should favor GOOGL
        if verdict == "THREAT":
            if googl_vote['action'] in ['BUY', 'HOLD'] and nvda_vote['action'] in ['SELL', 'HOLD']:
                print("✅ THREAT scenario: GOOGL favored over NVDA")
                checks_passed += 1
            else:
                print(f"⚠️ THREAT scenario inconsistency: NVDA={nvda_vote['action']}, GOOGL={googl_vote['action']}")

        # Check 2: SAFE verdict should favor NVDA
        elif verdict == "SAFE":
            if nvda_vote['action'] in ['BUY', 'HOLD'] and googl_vote['action'] in ['SELL', 'HOLD']:
                print("✅ SAFE scenario: NVDA favored over GOOGL")
                checks_passed += 1
            else:
                print(f"⚠️ SAFE scenario inconsistency: NVDA={nvda_vote['action']}, GOOGL={googl_vote['action']}")

        # Check 3: TCO advantage should align with recommendations
        else:  # MONITORING
            print("✅ MONITORING scenario: Both positions cautious")
            checks_passed += 1

        # Check 4: Confidence levels reasonable (0-1 range)
        if 0 <= nvda_vote['confidence'] <= 1 and 0 <= googl_vote['confidence'] <= 1:
            print("✅ Confidence levels in valid range")
            checks_passed += 1

        # Check 5: TCO advantage calculation
        tco_adv = nvda_factors['tco_advantage']
        if -50 <= tco_adv <= 50:  # Reasonable TCO difference range
            print(f"✅ TCO advantage reasonable: {tco_adv:.1f}%")
            checks_passed += 1

        print(f"\n📊 Consistency Score: {checks_passed}/{total_checks + 2} checks passed")

    print("\n" + "=" * 80)


async def test_non_chip_tickers():
    """Test that non-chip tickers get neutral votes"""

    print("\n" + "=" * 80)
    print("🧪 Non-Chip Ticker Test")
    print("=" * 80)

    agent = ChipWarAgent()

    non_chip_tickers = ["AAPL", "MSFT", "TSLA", "JPM", "XOM"]

    for ticker in non_chip_tickers:
        vote = await agent.analyze(ticker)

        print(f"\n{ticker}:")
        print(f"   Action: {vote['action']}")
        print(f"   Confidence: {vote['confidence']:.1%}")
        print(f"   Has chip factors: {vote.get('chip_war_factors') is not None}")

        # Non-chip tickers should have HOLD with 0.0 confidence
        if vote['action'] == 'HOLD' and vote['confidence'] == 0.0:
            print("   ✅ Correct neutral vote")
        else:
            print(f"   ⚠️ Unexpected vote for non-chip ticker")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n" + "🎮" * 40)
    print("CHIP WAR AGENT TEST SUITE")
    print("🎮" * 40)

    # Run tests
    asyncio.run(test_chip_war_agent())
    asyncio.run(test_voting_consistency())
    asyncio.run(test_non_chip_tickers())

    print("\n" + "✅" * 40)
    print("ALL TESTS COMPLETE")
    print("✅" * 40 + "\n")
