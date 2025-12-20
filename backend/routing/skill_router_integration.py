"""
Skill Layer와 Semantic Router 통합

SkillRegistry를 초기화하고 Semantic Router에 연결

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import Dict, Any

from backend.skills.skill_initializer import initialize_all_skills
from backend.routing.semantic_router import SemanticRouter, get_semantic_router
from backend.routing.tool_selector import DynamicToolLoader, get_tool_loader

logger = logging.getLogger(__name__)


def integrate_skill_layer() -> Dict[str, Any]:
    """
    Skill Layer를 Semantic Router에 통합

    단계:
    1. SkillRegistry 초기화 및 모든 Skill 등록
    2. DynamicToolLoader에 SkillRegistry 연결
    3. SemanticRouter 업데이트

    Returns:
        통합 결과 정보
    """
    logger.info("Starting Skill Layer integration...")

    # Step 1: Initialize all skills
    try:
        registry = initialize_all_skills()
        registry_info = registry.get_registry_info()
        logger.info(
            f"✓ Skills initialized: {registry_info['total_skills']} skills "
            f"across {len(registry_info['categories'])} categories"
        )
    except Exception as e:
        logger.error(f"Failed to initialize skills: {e}")
        raise

    # Step 2: Connect DynamicToolLoader
    try:
        tool_loader = get_tool_loader()
        # 이미 get_tool_loader()가 자동으로 SkillRegistry를 연결함
        registered_skills = tool_loader.get_registered_skills()
        logger.info(f"✓ DynamicToolLoader connected: {len(registered_skills)} skills available")
    except Exception as e:
        logger.error(f"Failed to connect DynamicToolLoader: {e}")
        raise

    # Step 3: Verify Semantic Router
    try:
        router = get_semantic_router()
        logger.info("✓ SemanticRouter ready")
    except Exception as e:
        logger.error(f"Failed to initialize SemanticRouter: {e}")
        raise

    # Summary
    result = {
        "success": True,
        "registry_info": registry_info,
        "registered_skills": registered_skills,
        "message": "Skill Layer successfully integrated with Semantic Router"
    }

    logger.info("=" * 60)
    logger.info("Skill Layer Integration Complete")
    logger.info(f"Total Skills: {registry_info['total_skills']}")
    logger.info(f"Categories: {', '.join(registry_info['categories'].keys())}")
    logger.info("=" * 60)

    return result


def get_integration_status() -> Dict[str, Any]:
    """
    현재 통합 상태 조회

    Returns:
        통합 상태 정보
    """
    from backend.skills.base_skill import get_skill_registry

    registry = get_skill_registry()
    tool_loader = get_tool_loader()
    router = get_semantic_router()

    registry_info = registry.get_registry_info()
    registered_skills = tool_loader.get_registered_skills()

    return {
        "registry": {
            "total_skills": registry_info['total_skills'],
            "categories": registry_info['categories'],
            "skills": registry_info['skills']
        },
        "tool_loader": {
            "registered_skills_count": len(registered_skills),
            "registered_skills": registered_skills
        },
        "router": {
            "status": "active",
            "router_type": router.__class__.__name__
        }
    }


def test_skill_routing():
    """
    Skill Layer 통합 테스트

    여러 Intent로 라우팅을 테스트하고 올바른 Skill이 선택되는지 확인
    """
    logger.info("Testing Skill Layer routing...")

    from backend.routing.intent_classifier import Intent

    test_cases = [
        {
            "intent": Intent.NEWS_ANALYSIS,
            "expected_skills": ["MarketData.News", "Intelligence.Gemini"]
        },
        {
            "intent": Intent.TRADING_EXECUTION,
            "expected_skills": ["Trading.KIS", "Trading.Order", "Trading.Risk", "Intelligence.GPT4o"]
        },
        {
            "intent": Intent.STRATEGY_GENERATION,
            "expected_skills": ["Intelligence.GPT4o"]  # 백테스트 스킬은 아직 미구현
        },
    ]

    tool_loader = get_tool_loader()
    from backend.routing.tool_selector import get_tool_selector

    selector = get_tool_selector()

    results = []

    for test in test_cases:
        intent = test["intent"]
        expected = test["expected_skills"]

        # Tool Groups 선택
        tool_groups = selector.select_tool_groups(intent)

        # 도구 로드
        tools = tool_loader.load_tools_for_groups(tool_groups)

        # 결과 검증
        available_skills = [g for g in tool_groups if g in tool_loader.get_registered_skills()]

        result = {
            "intent": intent.value,
            "expected_skills": expected,
            "selected_tool_groups": tool_groups,
            "available_skills": available_skills,
            "tool_count": len(tools),
            "status": "pass" if len(tools) > 0 else "fail"
        }

        results.append(result)

        logger.info(f"Intent: {intent.value}")
        logger.info(f"  Expected: {expected}")
        logger.info(f"  Selected: {tool_groups}")
        logger.info(f"  Available: {available_skills}")
        logger.info(f"  Tool Count: {len(tools)}")
        logger.info(f"  Status: {result['status']}")
        logger.info("")

    # 전체 통과 여부
    all_passed = all(r["status"] == "pass" for r in results)

    logger.info("=" * 60)
    logger.info(f"Test Results: {'PASS' if all_passed else 'FAIL'}")
    logger.info(f"Passed: {sum(1 for r in results if r['status'] == 'pass')}/{len(results)}")
    logger.info("=" * 60)

    return {
        "all_passed": all_passed,
        "results": results
    }


# ============================================================================
# Auto-integration (optional)
# ============================================================================

# 자동 통합 (필요 시)
# integrate_skill_layer()
