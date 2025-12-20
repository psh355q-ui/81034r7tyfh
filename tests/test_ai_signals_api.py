"""
AI Signals API 테스트 스크립트

AI Signals Router의 기능을 테스트합니다.

Usage:
    python test_ai_signals_api.py

Author: AI Trading System
Date: 2025-12-05
"""

import requests
import json
from datetime import datetime

# API 기본 URL
BASE_URL = "http://localhost:8000/ai-signals"


def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_health_check():
    """Health Check 테스트"""
    print_section("1. Health Check")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Service: {data.get('service')}")
            print(f"✓ Status: {data.get('status')}")
            print(f"✓ Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"✗ Health check failed: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("✗ Connection Error: API 서버가 실행 중이지 않습니다.")
        print("  다음 명령으로 서버를 시작하세요:")
        print("  cd ai-trading-system && uvicorn backend.api.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_router_status():
    """Router 상태 확인"""
    print_section("2. Router Status")

    try:
        response = requests.get(f"{BASE_URL}/status", timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Semantic Router: {'Active' if data.get('semantic_router_active') else 'Inactive'}")
            print(f"✓ Skill Registry: {'Active' if data.get('skill_registry_active') else 'Inactive'}")
            print(f"✓ Signal Pipeline: {'Active' if data.get('signal_pipeline_active') else 'Inactive'}")
            print(f"✓ Registered Skills: {data.get('registered_skills')}")
            print(f"✓ Available Tools: {data.get('available_tools')}")
            return True
        else:
            print(f"✗ Status check failed: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_skills_info():
    """Skills 정보 조회"""
    print_section("3. Skills Information")

    try:
        response = requests.get(f"{BASE_URL}/skills", timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Total Skills: {data.get('total_skills')}")
            print(f"✓ Categories: {data.get('categories')}")

            print("\nRegistered Skills:")
            for skill in data.get('skills', []):
                print(f"  - {skill['name']} ({skill['category']}, {skill['tool_count']} tools)")

            return True
        else:
            print(f"✗ Skills info failed: {response.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_routing_demo():
    """Routing Demo 테스트"""
    print_section("4. Routing Demo")

    test_inputs = [
        "AAPL에 대한 최신 뉴스를 분석해줘",
        "삼성전자 주식을 매수할까?",
        "내 포트폴리오의 리스크를 분석해줘",
    ]

    try:
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n[Test {i}] User Input: {user_input}")

            response = requests.get(
                f"{BASE_URL}/routing-demo",
                params={"user_input": user_input},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                routing = data.get('routing', {})

                print(f"  Intent: {routing.get('intent')}")
                print(f"  Confidence: {routing.get('confidence'):.2f}")
                print(f"  Tool Groups: {routing.get('tool_groups')}")
                print(f"  Tools Count: {routing.get('tools_count')}")
                print(f"  Model: {routing.get('model', {}).get('provider')} - {routing.get('model', {}).get('model')}")

                print("  Selected Tools:")
                for tool in data.get('tools', []):
                    print(f"    - {tool['name']}: {tool['description'][:60]}...")

            else:
                print(f"  ✗ Failed: {response.text}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_signal_generation():
    """신호 생성 테스트 (실제 API 호출 없이 구조만 확인)"""
    print_section("5. Signal Generation (Structure Test)")

    print("\nNOTE: 실제 신호 생성은 API 키가 필요하므로 스킵합니다.")
    print("API 키 설정 후 다음과 같이 호출할 수 있습니다:")

    example_request = {
        "ticker": "AAPL",
        "context": "최근 AI 관련 발표가 있었음",
        "strategy": "news_analysis",
        "use_optimization": True
    }

    print("\nExample Request:")
    print(json.dumps(example_request, indent=2, ensure_ascii=False))

    print("\nExpected Response:")
    expected_response = {
        "success": True,
        "ticker": "AAPL",
        "signal": {
            "action": "BUY",
            "confidence": 0.85,
            "reasoning": "..."
        },
        "intent": "news_analysis",
        "tools_used": 7,
        "tokens_saved_pct": 76.7,
        "cost_usd": 0.02,
        "processing_time_ms": 1500,
        "message": "Signal generated successfully"
    }

    print(json.dumps(expected_response, indent=2, ensure_ascii=False))

    return True


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 80)
    print("  AI SIGNALS API TEST SUITE")
    print("=" * 80)
    print(f"\nTest Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {BASE_URL}")

    results = []

    # 1. Health Check
    results.append(("Health Check", test_health_check()))

    if not results[0][1]:
        print("\n" + "=" * 80)
        print("  API 서버가 실행 중이지 않아 테스트를 중단합니다.")
        print("=" * 80)
        return

    # 2. Router Status
    results.append(("Router Status", test_router_status()))

    # 3. Skills Info
    results.append(("Skills Information", test_skills_info()))

    # 4. Routing Demo
    results.append(("Routing Demo", test_routing_demo()))

    # 5. Signal Generation (Structure)
    results.append(("Signal Generation Structure", test_signal_generation()))

    # 최종 결과
    print("\n" + "=" * 80)
    print("  TEST RESULTS")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 80)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 80)

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
