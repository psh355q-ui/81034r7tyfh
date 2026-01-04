import requests
import json

print("=" * 60)
print("War Room API 테스트 (NVDA)")
print("=" * 60)

try:
    response = requests.post(
        'http://localhost:8001/api/war-room-mvp/deliberate',
        json={
            'symbol': 'NVDA',
            'action_context': 'new_position'
        },
        timeout=60
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ War Room 정상 실행")
        print(f"\n최종 결정: {result.get('final_decision')}")
        print(f"전체 신뢰도: {result.get('overall_confidence')}")
        print(f"\nAgent 투표:")
        for agent in result.get('agent_votes', []):
            print(f"  - {agent.get('agent')}: {agent.get('action')} (confidence: {agent.get('confidence')})")
    else:
        print(f"❌ 오류 발생")
        print(response.text[:500])
        
except Exception as e:
    print(f"❌ 예외 발생: {e}")
