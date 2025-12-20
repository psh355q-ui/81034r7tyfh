"""
Skill Layer 통합 테스트 스크립트

Skill Layer가 올바르게 초기화되고 Semantic Router와 통합되는지 검증

Author: AI Trading System
Date: 2025-12-04
"""

import logging
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_skill_initialization():
    """Skill 초기화 테스트"""
    print("\n" + "=" * 60)
    print("Test 1: Skill Initialization")
    print("=" * 60)

    from backend.skills.skill_initializer import initialize_all_skills

    try:
        registry = initialize_all_skills()
        info = registry.get_registry_info()

        print(f"✓ Total Skills: {info['total_skills']}")
        print(f"✓ Categories: {', '.join(info['categories'].keys())}")
        print("\nRegistered Skills:")
        for skill in info['skills']:
            print(f"  - {skill['name']} ({skill['category']}, {skill['tool_count']} tools)")

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        logger.error("Skill initialization failed", exc_info=True)
        return False


def test_skill_tools():
    """Skill의 도구 정의 테스트"""
    print("\n" + "=" * 60)
    print("Test 2: Skill Tools")
    print("=" * 60)

    from backend.skills.base_skill import get_skill_registry

    try:
        registry = get_skill_registry()

        # NewsSkill 테스트
        news_skill = registry.get_skill("MarketData.News")
        if news_skill:
            tools = news_skill.get_tools()
            print(f"✓ MarketData.News: {len(tools)} tools")
            for tool in tools:
                print(f"  - {tool['function']['name']}: {tool['function']['description'][:50]}...")

        # KISSkill 테스트
        kis_skill = registry.get_skill("Trading.KIS")
        if kis_skill:
            tools = kis_skill.get_tools()
            print(f"\n✓ Trading.KIS: {len(tools)} tools")
            for tool in tools:
                print(f"  - {tool['function']['name']}: {tool['function']['description'][:50]}...")

        # GeminiSkill 테스트
        gemini_skill = registry.get_skill("Intelligence.Gemini")
        if gemini_skill:
            tools = gemini_skill.get_tools()
            print(f"\n✓ Intelligence.Gemini: {len(tools)} tools")
            for tool in tools:
                print(f"  - {tool['function']['name']}: {tool['function']['description'][:50]}...")

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        logger.error("Skill tools test failed", exc_info=True)
        return False


def test_dynamic_tool_loader():
    """DynamicToolLoader 테스트"""
    print("\n" + "=" * 60)
    print("Test 3: Dynamic Tool Loader")
    print("=" * 60)

    from backend.routing.tool_selector import get_tool_loader

    try:
        loader = get_tool_loader()
        registered_skills = loader.get_registered_skills()

        print(f"✓ Registered Skills: {len(registered_skills)}")
        for skill_name in registered_skills:
            print(f"  - {skill_name}")

        # 특정 Tool Group의 도구 로드 테스트
        test_groups = ["MarketData.News", "Intelligence.Gemini"]
        tools = loader.load_tools_for_groups(test_groups)

        print(f"\n✓ Loaded Tools for {test_groups}: {len(tools)} tools")

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        logger.error("DynamicToolLoader test failed", exc_info=True)
        return False


def test_semantic_router_integration():
    """Semantic Router 통합 테스트"""
    print("\n" + "=" * 60)
    print("Test 4: Semantic Router Integration")
    print("=" * 60)

    from backend.routing.skill_router_integration import test_skill_routing

    try:
        results = test_skill_routing()

        if results["all_passed"]:
            print("✓ All routing tests passed")
        else:
            print("✗ Some routing tests failed")
            for result in results["results"]:
                if result["status"] == "fail":
                    print(f"  - Failed: {result['intent']}")

        return results["all_passed"]

    except Exception as e:
        print(f"✗ Failed: {e}")
        logger.error("Semantic Router integration test failed", exc_info=True)
        return False


def test_find_skill_by_tool():
    """도구 이름으로 Skill 찾기 테스트"""
    print("\n" + "=" * 60)
    print("Test 5: Find Skill by Tool Name")
    print("=" * 60)

    from backend.skills.base_skill import get_skill_registry

    try:
        registry = get_skill_registry()

        test_tools = [
            "search_news",
            "get_account_balance",
            "analyze_sentiment"
        ]

        for tool_name in test_tools:
            skill = registry.find_skill_by_tool(tool_name)
            if skill:
                print(f"✓ '{tool_name}' found in: {skill.metadata.name}")
            else:
                print(f"✗ '{tool_name}' not found")

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        logger.error("Find skill by tool test failed", exc_info=True)
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 80)
    print("SKILL LAYER INTEGRATION TEST SUITE")
    print("=" * 80)

    tests = [
        ("Skill Initialization", test_skill_initialization),
        ("Skill Tools", test_skill_tools),
        ("Dynamic Tool Loader", test_dynamic_tool_loader),
        ("Semantic Router Integration", test_semantic_router_integration),
        ("Find Skill by Tool", test_find_skill_by_tool),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}", exc_info=True)
            results.append((test_name, False))

    # 최종 결과
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "=" * 80)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 80)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
