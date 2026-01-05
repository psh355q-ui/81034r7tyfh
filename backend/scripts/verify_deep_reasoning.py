
"""
Verify Deep Reasoning Agent Integration
Test if AnalystAgentMVP correctly triggers DeepReasoningAgent on critical news.
"""
import asyncio
import os
import sys
from datetime import datetime

# Adjust path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ai.mvp.analyst_agent_mvp import AnalystAgentMVP

async def main():
    print("🚀 Starting Deep Reasoning Verification...")
    
    agent = AnalystAgentMVP()
    
    # Test Data: Critical Geopolitical Event
    fake_news = [
        {
            "title": "Emergency Alert: Country X launches full-scale invasion of Country Y",
            "content": "Military operation underway. Global markets in panic. Oil prices spike.",
            "source": "Breaking News",
            "published_at": datetime.now().isoformat()
        },
        {
            "title": "US announces severe sanctions on aggressor nation",
            "content": "Full economic blockade initiated.",
            "source": "Reuters",
            "published_at": datetime.now().isoformat()
        }
    ]
    
    print("\n📰 Feeding Fake News (Invasion Scenario)...")
    
    # Run Analysis
    try:
        result = await agent.analyze(
            symbol="NVDA",
            news_articles=fake_news,
            price_context={'current_price': 100.0, 'trend': 'downtrend'}
        )
        
        print("\n✅ Analysis Complete!")
        print(f"Action: {result.get('action')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Reasoning: {result.get('reasoning')}")
        
        # Check for keywords in reasoning that indicate Deep Reasoning was used
        reasoning = result.get('reasoning', '')
        if "침공" in reasoning or "전쟁" in reasoning or "지정학" in reasoning:
             print("\n✅ SUCCESS: Deep Reasoning keywords found in output.")
        else:
             print("\n⚠️ WARNING: Deep Reasoning keywords NOT clearly found in output.")
             
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
