import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ai.reasoning.deep_reasoning_agent import DeepReasoningAgent
from dotenv import load_dotenv

# Load env for API keys
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_deep_reasoning():
    agent = DeepReasoningAgent()
    
    print("\n" + "="*50)
    print("🧪 Deep Reasoning Agent Verification")
    print("="*50)

    # Test Case 1: High Risk Geopolitics (War) -> Should trigger High GRS
    print("\n[Case 1] High Risk Event: 'Russia invades neighboring country'")
    result1 = await agent.analyze_event(
        event_type="GEOPOLITICS",
        keywords=["invasion", "war", "russia", "border"],
        base_info={"ticker": "SPY", "context": "Market fear increasing"}
    )
    
    print(f"Status: {result1.get('status')}")
    if result1.get('status') == 'SUCCESS':
        cls = result1.get('classification', {})
        vec = cls.get('vectors', {})
        grs = cls.get('grs_score')
        reasoning = cls.get('reasoning')
        
        print(f"Type: {cls.get('type')}")
        print(f"Vectors: {vec}")
        print(f"GRS Score: {grs} ({cls.get('grs_label')})")
        print(f"Reasoning (KR): {reasoning}")
        
    
    # Test Case 2: Venezuela Scenario -> Should trigger Matrix Logic
    print("\n[Case 2] Specific Scenario: 'Venezuela oil sanctions relief'")
    result2 = await agent.analyze_event(
        event_type="GEOPOLITICS",
        keywords=["venezuela", "oil", "sanctions", "relief"],
        base_info={"ticker": "XLE", "context": "Energy sector focus"}
    )
    
    print(f"Status: {result2.get('status')}")
    if result2.get('status') == 'SUCCESS':
        sim = result2.get('simulation', {})
        print(f"Primary Channel: {sim.get('primary_channel')}")
        print(f"Impact Chain: {sim.get('impact_chain')}")
        
    # Test Case 3: Noise -> Should be ignored
    print("\n[Case 3] Noise Event: 'Minor celebrity rumor'")
    result3 = await agent.analyze_event(
        event_type="GEOPOLITICS",
        keywords=["rumor", "celebrity", "gossip"],
        base_info={"ticker": "None", "context": "Noise"}
    )
    print(f"Status: {result3.get('status')}")
    if result3.get('status') == 'IGNORED':
         print(f"Reason: {result3.get('reason')}")

    print("\n" + "="*50)

if __name__ == "__main__":
    try:
        asyncio.run(verify_deep_reasoning())
    except KeyboardInterrupt:
        pass
