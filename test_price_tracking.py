#!/usr/bin/env python
"""
Test Price Tracking Verifier

뉴스 해석 후 가격 추적 테스트
"""
import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env', override=True)

print("="*80)
print(f"Price Tracking Verifier Test - {datetime.now().strftime('%H:%M:%S')}")
print("="*80)
print()

# Step 1: Check existing news interpretations
print("[1/3] Checking Existing News Interpretations...")
print("-"*80)

from backend.database.repository import get_sync_session
from backend.database.models import NewsInterpretation, NewsMarketReaction

session = get_sync_session()

interpretations = session.query(NewsInterpretation).all()
print(f"✅ Found {len(interpretations)} news interpretations")

for i, interp in enumerate(interpretations[:5], 1):
    print(f"{i}. {interp.ticker}: {interp.headline_bias} ({interp.confidence}% confidence)")
    print(f"   Interpreted at: {interp.interpreted_at}")

    # Check if market reaction exists
    reaction = session.query(NewsMarketReaction).filter(
        NewsMarketReaction.interpretation_id == interp.id
    ).first()

    if reaction:
        print(f"   Reaction: 1h=${reaction.price_1h_after or 'N/A'}, "
              f"1d=${reaction.price_1d_after or 'N/A'}, "
              f"3d=${reaction.price_3d_after or 'N/A'}")
    else:
        print(f"   Reaction: Not yet created")

session.close()
print()

# Step 2: Run Price Tracking
print("[2/3] Running Price Tracking Verifier...")
print("-"*80)

from backend.automation.price_tracking_verifier import PriceTrackingVerifier

async def run_tracking():
    verifier = PriceTrackingVerifier()

    # Verify all horizons
    results = await verifier.verify_all_horizons()

    return results

# Run async
results = asyncio.run(run_tracking())

print()
print("Results:")
for horizon, result in results.items():
    print(f"  {horizon}: {result['correct_count']}/{result['verified_count']} correct "
          f"({result['accuracy']*100:.1f}%)")

print()

# Step 3: Check Updated Reactions
print("[3/3] Verifying Updated Market Reactions...")
print("-"*80)

session = get_sync_session()

reactions = session.query(NewsMarketReaction).all()
print(f"Total reactions: {len(reactions)}")

for reaction in reactions[:5]:
    print(f"\n{reaction.ticker}:")
    print(f"  1h: ${reaction.price_1h_after or 'N/A'}")
    print(f"  1d: ${reaction.price_1d_after or 'N/A'}")
    print(f"  3d: ${reaction.price_3d_after or 'N/A'}")
    if reaction.interpretation_correct is not None:
        print(f"  Correct: {reaction.interpretation_correct}")

session.close()

print()
print("="*80)
print("Price Tracking Test Complete")
print("="*80)
