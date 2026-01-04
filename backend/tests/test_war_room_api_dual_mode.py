"""
War Room MVP - Dual Mode API 테스트

Date: 2026-01-02
Purpose: Direct mode vs Skill mode 결과 비교 및 성능 측정
"""

import requests
import time
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8001"  # 백엔드 포트 8001


def test_war_room_mvp_api(use_skills: bool = False) -> Dict[str, Any]:
    """
    War Room MVP API 테스트
    
    Args:
        use_skills: True면 Skill mode, False면 Direct mode
    
    Returns:
        테스트 결과
    """
    mode_name = "Skill Mode" if use_skills else "Direct Mode"
    print(f"\n{'='*80}")
    print(f"Testing: {mode_name}")
    print(f"{'='*80}")
    
    # Test request
    test_data = {
        "symbol": "NVDA",
        "action_context": "new_position",
        "market_data": {
            "price_data": {
                "current_price": 500.0,
                "open": 498.0,
                "high": 505.0,
                "low": 495.0,
                "volume": 50000000
            },
            "market_conditions": {
                "is_market_open": True,
                "volatility": 25.0
            }
        },
        "portfolio_state": {
            "total_value": 100000.0,
            "available_cash": 50000.0,
            "total_risk": 0.15,
            "position_count": 3
        }
    }
    
    print(f"\nRequest: POST /api/war-room-mvp/deliberate")
    print(f"Symbol: {test_data['symbol']}")
    print(f"Action Context: {test_data['action_context']}")
    
    # Measure time
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/war-room-mvp/deliberate",
            json=test_data,
            timeout=30
        )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Success!")
            print(f"Status Code: {response.status_code}")
            print(f"Processing Time: {elapsed_time:.2f}s")
            print(f"\nExecution Mode: {result.get('execution_mode', 'N/A')}")
            print(f"Final Decision: {result.get('final_decision', result.get('pm_decision', {}).get('final_decision', 'N/A'))}")
            
            # Extract confidence
            confidence = result.get('confidence', result.get('pm_decision', {}).get('confidence', 0))
            print(f"Confidence: {confidence:.2f}")
            
            # Create summary
            return {
                'success': True,
                'mode': mode_name,
                'execution_mode': result.get('execution_mode'),
                'final_decision': result.get('final_decision', result.get('pm_decision', {}).get('final_decision')),
                'confidence': confidence,
                'processing_time': elapsed_time,
                'full_result': result
            }
        else:
            print(f"\n❌ Failed!")
            print(f"Status Code: {response.status_code}")
            print(f"Error: {response.text}")
            
            return {
                'success': False,
                'mode': mode_name,
                'error': response.text,
                'status_code': response.status_code
            }
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error!")
        print(f"서버가 실행 중이 아닙니다: {BASE_URL}")
        print(f"\n서버 시작 방법:")
        print(f"  1. Direct mode (기본값): python -m uvicorn backend.main:app --reload")
        print(f"  2. Skill mode: WAR_ROOM_MVP_USE_SKILLS=true python -m uvicorn backend.main:app --reload")
        
        return {
            'success': False,
            'mode': mode_name,
            'error': 'Connection refused - Server not running'
        }
    
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        
        return {
            'success': False,
            'mode': mode_name,
            'error': str(e)
        }


def check_server_status():
    """서버 상태 확인"""
    print(f"\n{'='*80}")
    print(f"Checking Server Status")
    print(f"{'='*80}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/war-room-mvp/health", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Server is running!")
            print(f"Status: {result.get('status')}")
            print(f"War Room Active: {result.get('war_room_active')}")
            print(f"Shadow Trading Active: {result.get('shadow_trading_active')}")
            return True
        else:
            print(f"\n⚠️ Server responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Server is not running at {BASE_URL}")
        print(f"\n서버 시작 필요:")
        print(f"  cd d:\\code\\ai-trading-system")
        print(f"  python -m uvicorn backend.main:app --reload")
        return False


def get_war_room_info():
    """War Room 정보 조회"""
    print(f"\n{'='*80}")
    print(f"Getting War Room Info")
    print(f"{'='*80}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/war-room-mvp/info", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Info retrieved!")
            print(f"Execution Mode: {result.get('execution_mode', 'N/A')}")
            print(f"War Room Structure: {result.get('war_room_structure', 'N/A')}")
            
            if 'agents' in result:
                print(f"\nAgents:")
                for agent, info in result.get('agents', {}).items():
                    print(f"  - {agent}: {info.get('role', 'N/A')}")
            
            return result
        else:
            print(f"\n❌ Failed to get info: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def compare_modes(direct_result: Dict, skill_result: Dict):
    """두 모드의 결과 비교"""
    print(f"\n{'='*80}")
    print(f"Comparing Direct Mode vs Skill Mode")
    print(f"{'='*80}")
    
    if not direct_result.get('success') or not skill_result.get('success'):
        print("\n⚠️ Cannot compare - one or both tests failed")
        return
    
    # Compare final decisions
    print(f"\n📊 Final Decision:")
    print(f"  Direct: {direct_result.get('final_decision')}")
    print(f"  Skill:  {skill_result.get('final_decision')}")
    
    decisions_match = direct_result.get('final_decision') == skill_result.get('final_decision')
    print(f"  Match: {'✅ Yes' if decisions_match else '❌ No'}")
    
    # Compare confidence
    print(f"\n📊 Confidence:")
    direct_conf = direct_result.get('confidence', 0)
    skill_conf = skill_result.get('confidence', 0)
    print(f"  Direct: {direct_conf:.4f}")
    print(f"  Skill:  {skill_conf:.4f}")
    print(f"  Delta:  {abs(direct_conf - skill_conf):.4f}")
    
    # Compare processing time
    print(f"\n⏱️ Processing Time:")
    direct_time = direct_result.get('processing_time', 0)
    skill_time = skill_result.get('processing_time', 0)
    print(f"  Direct: {direct_time:.2f}s")
    print(f"  Skill:  {skill_time:.2f}s")
    print(f"  Delta:  {abs(direct_time - skill_time):.2f}s")
    
    if skill_time > 0:
        overhead = ((skill_time - direct_time) / direct_time) * 100
        print(f"  Overhead: {overhead:.1f}%")
    
    # Summary
    print(f"\n📋 Summary:")
    if decisions_match and abs(direct_conf - skill_conf) < 0.01:
        print(f"  ✅ Results are equivalent!")
    elif decisions_match:
        print(f"  ⚠️ Same decision, but confidence differs")
    else:
        print(f"  ❌ Different decisions - needs investigation")


def main():
    """메인 테스트 실행"""
    print(f"\n{'='*80}")
    print(f"War Room MVP - Dual Mode API Test")
    print(f"{'='*80}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Check server status
    if not check_server_status():
        print(f"\n⚠️ Please start the server first, then run this test again.")
        return
    
    # 2. Get current mode info
    info = get_war_room_info()
    current_mode = info.get('execution_mode', 'unknown') if info else 'unknown'
    print(f"\nCurrent Mode: {current_mode}")
    
    # 3. Run test with current mode
    print(f"\n{'='*80}")
    print(f"Running test with current server configuration...")
    print(f"{'='*80}")
    
    current_result = test_war_room_mvp_api(use_skills=False)  # Will detect actual mode from response
    
    # 4. Show results
    if current_result.get('success'):
        print(f"\n✅ Test completed successfully!")
        print(f"\nTo test the other mode:")
        print(f"  1. Stop the server (Ctrl+C)")
        
        if current_mode == 'direct_class':
            print(f"  2. Set environment: set WAR_ROOM_MVP_USE_SKILLS=true (Windows)")
            print(f"     Or: export WAR_ROOM_MVP_USE_SKILLS=true (Linux/Mac)")
        else:
            print(f"  2. Unset environment: set WAR_ROOM_MVP_USE_SKILLS=false")
        
        print(f"  3. Restart server: python -m uvicorn backend.main:app --reload")
        print(f"  4. Run this test again")
    else:
        print(f"\n❌ Test failed")
    
    print(f"\n{'='*80}")


if __name__ == '__main__':
    main()
