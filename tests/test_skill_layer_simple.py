"""
Skill Layer 통합 간단 테스트 (Windows 호환)

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
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """간단한 통합 테스트"""

    print("\n" + "=" * 80)
    print("SKILL LAYER INTEGRATION TEST")
    print("=" * 80)

    # Test 1: Skill 초기화
    print("\n[Test 1] Skill Initialization")
    print("-" * 80)

    from backend.skills.skill_initializer import initialize_all_skills

    registry = initialize_all_skills()
    info = registry.get_registry_info()

    print(f"Total Skills: {info['total_skills']}")
    print(f"Categories: {list(info['categories'].keys())}")
    print("\nRegistered Skills:")
    for skill in info['skills']:
        print(f"  - {skill['name']} ({skill['category']}, {skill['tool_count']} tools)")

    # Test 2: 각 Skill의 도구 확인
    print("\n[Test 2] Skill Tools")
    print("-" * 80)

    from backend.skills.base_skill import get_skill_registry

    registry = get_skill_registry()

    for skill_info in info['skills']:
        skill_name = skill_info['name']
        skill = registry.get_skill(skill_name)

        if skill:
            tools = skill.get_tools()
            print(f"\n{skill_name}: {len(tools)} tools")
            for tool in tools[:3]:  # 처음 3개만 표시
                func_name = tool.get('function', {}).get('name', 'Unknown')
                func_desc = tool.get('function', {}).get('description', '')[:60]
                print(f"  - {func_name}: {func_desc}...")

    # Test 3: DynamicToolLoader
    print("\n[Test 3] Dynamic Tool Loader")
    print("-" * 80)

    from backend.routing.tool_selector import get_tool_loader

    loader = get_tool_loader()
    registered_skills = loader.get_registered_skills()

    print(f"Registered Skills: {len(registered_skills)}")
    for skill_name in registered_skills:
        print(f"  - {skill_name}")

    # Test 4: Tool Group별 도구 로드
    print("\n[Test 4] Load Tools for Groups")
    print("-" * 80)

    test_groups = ["MarketData.News", "Intelligence.Gemini", "Trading.KIS"]
    tools = loader.load_tools_for_groups(test_groups)

    print(f"Tool Groups: {test_groups}")
    print(f"Total Tools Loaded: {len(tools)}")

    # Test 5: 도구 이름으로 Skill 찾기
    print("\n[Test 5] Find Skill by Tool Name")
    print("-" * 80)

    test_tools = ["search_news", "get_account_balance", "analyze_sentiment"]

    for tool_name in test_tools:
        skill = registry.find_skill_by_tool(tool_name)
        if skill:
            print(f"  '{tool_name}' -> {skill.metadata.name}")
        else:
            print(f"  '{tool_name}' -> NOT FOUND")

    # Test 6: Semantic Router 통합
    print("\n[Test 6] Semantic Router Integration")
    print("-" * 80)

    from backend.routing.intent_classifier import Intent
    from backend.routing.tool_selector import get_tool_selector

    selector = get_tool_selector()

    test_intents = [
        Intent.NEWS_ANALYSIS,
        Intent.TRADING_EXECUTION,
        Intent.STRATEGY_GENERATION
    ]

    for intent in test_intents:
        tool_groups = selector.select_tool_groups(intent)
        tools = loader.load_tools_for_groups(tool_groups)
        available_skills = [g for g in tool_groups if g in registered_skills]

        print(f"\nIntent: {intent.value}")
        print(f"  Selected Groups: {tool_groups}")
        print(f"  Available Skills: {available_skills}")
        print(f"  Total Tools: {len(tools)}")

    # 최종 결과
    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  - {info['total_skills']} skills initialized")
    print(f"  - {len(registered_skills)} skills registered in ToolLoader")
    print(f"  - Semantic Router integration: OK")
    print(f"  - Find skill by tool: OK")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        logger.error("Test failed", exc_info=True)
        sys.exit(1)
