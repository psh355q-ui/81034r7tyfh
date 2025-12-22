"""Test War Room with SEC News (with tickers)"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.api.war_room_router import get_war_room_engine


async def main():
    print("🧪 War Room Test with SEC News Data\n")

    # Test with ANEB (has recent SEC filing)
    ticker = "ANEB"

    print("=" * 80)
    print(f"Testing War Room Debate for {ticker}")
    print("=" * 80)

    engine = get_war_room_engine()

    try:
        votes, pm_decision = await engine.run_debate(ticker)

        print("\n" + "=" * 80)
        print("DEBATE RESULTS")
        print("=" * 80)

        # Display votes
        for vote in votes:
            agent = vote['agent'].upper()
            action = vote['action']
            confidence = vote['confidence']

            print(f"\n{agent} Agent:")
            print(f"  Action: {action}")
            print(f"  Confidence: {confidence:.2%}")

            if agent == "NEWS":
                print(f"  News Count: {vote.get('news_count', 0)}")
                print(f"  Emergency Count: {vote.get('emergency_count', 0)}")
                print(f"  Sentiment Score: {vote.get('sentiment_score', 0):.2f}")
                print(f"  Reasoning: {vote.get('reasoning', '')[:150]}")

        # PM Decision
        print("\n" + "=" * 80)
        print("PM DECISION")
        print("=" * 80)
        print(f"  Consensus: {pm_decision['consensus_action']}")
        print(f"  Confidence: {pm_decision['consensus_confidence']:.2%}")

        # Check if NewsAgent found SEC news
        news_vote = next((v for v in votes if v['agent'] == 'news'), None)

        print("\n" + "=" * 80)
        print("SEC NEWS INTEGRATION STATUS")
        print("=" * 80)

        if news_vote:
            news_count = news_vote.get('news_count', 0)

            if news_count > 0:
                print(f"✅ SUCCESS: NewsAgent found {news_count} news articles!")
                print(f"   Sentiment: {news_vote.get('sentiment_score', 0):.2f}")
                print(f"   Action: {news_vote['action']}")
            else:
                print(f"⚠️ WARNING: NewsAgent found 0 news articles")
                print(f"   This means SEC tickers aren't being matched properly")
        else:
            print(f"❌ ERROR: NewsAgent did not participate!")

        print("\n✅ Test complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
