
"""
Test Deep Reasoning Features (Vectors, GRS, Venezuela Matrix)
=============================================================
Directly tests the DeepReasoningAgent's internal logic for:
1. Event Vectors (structural classification)
2. GRS (Geopolitical Risk Score) calculation
3. Venezuela Scenario Matrix injection
"""
import sys
import os
import asyncio
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ai.reasoning.deep_reasoning_agent import DeepReasoningAgent

async def test_features():
    print("🧠 Testing Deep Reasoning Features...\n")
    agent = DeepReasoningAgent()
    
    # Test Case 1: Invasion (High GRS expected)
    print("--- Test Case 1: Invasion (GRS Check) ---")
    result1 = await agent.analyze_event(
        event_type="GEOPOLITICS",
        keywords=["invasion", "war", "tanks"],
        base_info={"ticker": "XLE", "news_count": 5}
    )
    
    print(f"Status: {result1['status']}")
    if result1['status'] == 'SUCCESS':
        cls = result1['classification']
        print(f"Type: {cls.get('type')}")
        print(f"Vectors: {cls.get('vectors')}")
        print(f"GRS Score: {cls.get('grs_score')} ({cls.get('grs_label')})")
        
        # Verify GRS calculation
        v = cls.get('vectors', {})
        calc_grs = (v.get("intensity", 0) * 0.3) + (v.get("scope", 0) * 0.3) + \
                   (v.get("duration", 0) * 0.2) + (v.get("economic", 0) * 0.2)
        print(f"Calculated GRS: {calc_grs:.2f}")
        
    print("\n")
    
    # Test Case 2: Venezuela Logic (Matrix Check)
    print("--- Test Case 2: Venezuela (Matrix Context Check) ---")
    # Note: We can't see the internal prompt easily, but we can check if the result mentions specific sectors
    # implied by the matrix (Energy, XLE, Oil).
    result2 = await agent.analyze_event(
        event_type="GEOPOLITICS",
        keywords=["venezuela", "maduro", "sanctions"],
        base_info={"ticker": "CVX", "news_count": 2}
    )
    
    if result2['status'] == 'SUCCESS':
        sim = result2['simulation']
        print(f"Primary Channel: {sim.get('primary_channel')}")
        print(f"Impact Chain: {sim.get('impact_chain')}")
        # Check if output is influenced by matrix
        print(f"Sector Impacts: {sim.get('sector_impacts')}")

if __name__ == "__main__":
    asyncio.run(test_features())
