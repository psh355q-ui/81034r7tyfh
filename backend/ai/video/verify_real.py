
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from backend.ai.video.video_analyzer import VideoAnalyzer

# Load environment variables
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def verify():
    print("=== Real Video Analysis Verification ===")
    
    # Check OpenAI Key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        return

    url = "https://www.youtube.com/watch?v=7dROvom5hVY"
    analyzer = VideoAnalyzer()
    
    print(f"Analyzing: {url} (First 3 minutes for verification)")
    print("This may take a moment (Downloading -> Transcribing -> Analyzing)...")
    
    try:
        # Download first 3 minutes (0-180s) to speed up verification
        result = await analyzer.analyze_youtube(url, download_sections=[(0, 180)])
        
        print("\n✅ Analysis Successful!")
        print(f"Title: {result.title}")
        print(f"Duration: {result.duration_seconds}s")
        
        print("\n--- 🔊 Audio Analysis (Tone/Energy) ---")
        metrics = result.tone_metrics
        if metrics:
            print(f"Interpretation: {metrics.get('interpretation')}")
            print(f"Energy Mean: {metrics.get('energy_mean'):.4f}")
            print(f"Tone Brightness (Centroid): {metrics.get('tone_brightness'):.1f}")
            print(f"High Energy Ratio: {metrics.get('high_energy_ratio'):.2%}")
        else:
            print("No audio metrics available.")

        print("\n--- 📝 Text Sentiment Timeline (Top 3 Pos/Neg) ---")
        timeline = result.sentiment_timeline
        if timeline:
            top_pos = sorted(timeline, key=lambda x: x['sentiment_score'], reverse=True)[:3]
            top_neg = sorted(timeline, key=lambda x: x['sentiment_score'])[:3]
            
            print("Top Positive:")
            for p in top_pos:
                print(f"  [+{p['sentiment_score']:.2f}] {p['text']}")
            
            print("\nTop Negative:")
            for n in top_neg:
                print(f"  [{n['sentiment_score']:.2f}] {n['text']}")
        else:
            print("No sentiment data available.")

        print("\n--- 🧠 Market Intelligence (Wall Street Editor) ---")
        intelligence = result.intelligence_data
        if intelligence:
            for item in intelligence:
                print(f"[{item.get('category', 'General')}] Impact: {item.get('impact_score', 'N/A')}")
                print(f"  Fact: {item.get('fact')}")
                print(f"  Entities: {item.get('entity')}")
                print(f"  Related Sectors: {item.get('related_sectors')}")
                print(f"  Mapped Tickers: {item.get('related_tickers')}")
                print("-" * 30)
        else:
            print("No significant intelligence extracted (or parsing failed).")

        print("\n--- 🤖 AI Synthesis ---")
        print(result.summary[:500] + "..." if len(result.summary) > 500 else result.summary)
            
    except Exception as e:
        print(f"\n❌ Analysis Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify())
