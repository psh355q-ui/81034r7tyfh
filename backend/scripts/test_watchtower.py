
"""
Test Watchtower (Cost Optimization Trigger)
===========================================
Verifies that the NewsAgent correctly detects critical keywords and sets urgency levels 
as defined in watchtower_triggers.py.
"""
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ai.debate.news_agent import NewsAgent

async def test_watchtower():
    print("🏰 Testing The Watchtower Triggers...\n")
    agent = NewsAgent()
    
    test_cases = [
        {
            "name": "Geopolitics Critical",
            "news": [{"title": "Russia launches full-scale invasion", "content": "Troops deployed to border"}],
            "expected_type": "GEOPOLITICS",
            "expected_urgency": "CRITICAL"
        },
        {
            "name": "Chip War High",
            "news": [{"title": "US announces new export control on AI chips", "content": "NVIDIA impacted"}],
            "expected_type": "CHIP_WAR",
            "expected_urgency": "HIGH"
        },
        {
            "name": "Macro Shock High",
            "news": [{"title": "Fed announces emergency rate hike due to inflation", "content": "Market in shock"}],
            "expected_type": "MACRO_SHOCK",
            "expected_urgency": "HIGH"
        },
        {
            "name": "Normal News (Should NOT Trigger)",
            "news": [{"title": "Apple releases new iPhone 16", "content": "Features better camera"}],
            "expected_type": "NONE",
            "expected_urgency": "NONE"
        }
    ]
    
    passed = 0
    for case in test_cases:
        print(f"Testing: {case['name']}...")
        result = agent.detect_critical_events(case['news'])
        
        type_match = result['event_type'] == case['expected_type']
        urgency_match = result['urgency'] == case['expected_urgency']
        detected_match = result['detected'] == (case['expected_type'] != "NONE")
        
        if type_match and urgency_match and detected_match:
            print(f"✅ PASS: Detected {result['event_type']} ({result['urgency']})")
            passed += 1
        else:
            print(f"❌ FAIL: Expected {case['expected_type']}/{case['expected_urgency']}, Got {result['event_type']}/{result['urgency']}")
            print(f"   Keywords found: {result['keywords']}")
            
    print(f"\nResult: {passed}/{len(test_cases)} Passed")

if __name__ == "__main__":
    asyncio.run(test_watchtower())
