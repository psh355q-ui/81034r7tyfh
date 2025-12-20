"""
Skill Initializer

모든 Skill을 초기화하고 Registry에 등록

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import Optional

from backend.skills.base_skill import get_skill_registry, SkillRegistry

logger = logging.getLogger(__name__)


def initialize_all_skills() -> SkillRegistry:
    """
    모든 Skill 초기화 및 등록

    Returns:
        SkillRegistry 인스턴스
    """
    registry = get_skill_registry()

    logger.info("Initializing all skills...")

    # Market Data Skills
    try:
        from backend.skills.market_data import NewsSkill
        registry.register(NewsSkill())
        logger.info("✓ NewsSkill registered")
    except Exception as e:
        logger.error(f"Failed to register NewsSkill: {e}")

    # Trading Skills
    try:
        from backend.skills.trading import KISSkill, OrderSkill, RiskSkill
        registry.register(KISSkill(use_paper_trading=True))  # 기본값: 모의투자
        logger.info("✓ KISSkill registered")
        registry.register(OrderSkill())
        logger.info("✓ OrderSkill registered")
        registry.register(RiskSkill())
        logger.info("✓ RiskSkill registered")
    except Exception as e:
        logger.error(f"Failed to register Trading Skills: {e}")

    # Intelligence Skills
    try:
        from backend.skills.intelligence import GeminiSkill, ClaudeSkill, GPT4oSkill
        registry.register(GeminiSkill())
        logger.info("✓ GeminiSkill registered")
        registry.register(ClaudeSkill())
        logger.info("✓ ClaudeSkill registered")
        registry.register(GPT4oSkill())
        logger.info("✓ GPT4oSkill registered")
    except Exception as e:
        logger.error(f"Failed to register Intelligence Skills: {e}")

    # Technical Skills
    try:
        from backend.skills.technical import BacktestSkill
        registry.register(BacktestSkill())
        logger.info("✓ BacktestSkill registered")
    except Exception as e:
        logger.error(f"Failed to register Technical Skills: {e}")

    # TODO: 추가 Skill 등록
    # - SearchSkill, CalendarSkill (MarketData)
    # - SECSkill, FinancialsSkill, ValueChainSkill (Fundamental)
    # - ChartSkill, StatisticsSkill (Technical)
    # - LocalLLMSkill (Intelligence)

    info = registry.get_registry_info()
    logger.info(
        f"Skill initialization complete: {info['total_skills']} skills registered "
        f"across {len(info['categories'])} categories"
    )

    return registry


def initialize_minimal_skills() -> SkillRegistry:
    """
    최소한의 Skill만 초기화 (테스트용)

    Returns:
        SkillRegistry 인스턴스
    """
    registry = get_skill_registry()

    logger.info("Initializing minimal skills...")

    # 필수 Skill만 등록
    try:
        from backend.skills.market_data import NewsSkill
        from backend.skills.intelligence import GeminiSkill

        registry.register(NewsSkill())
        registry.register(GeminiSkill())

        logger.info("Minimal skills initialized: News + Gemini")
    except Exception as e:
        logger.error(f"Failed to initialize minimal skills: {e}")

    return registry


# ============================================================================
# Auto-initialization on import
# ============================================================================

# 자동 초기화 (필요 시)
# initialize_all_skills()
