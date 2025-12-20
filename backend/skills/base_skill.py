"""
Base Skill Class

모든 Skill의 기본 인터페이스 정의

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SkillCategory(str, Enum):
    """Skill 카테고리"""
    MARKET_DATA = "market_data"
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    TRADING = "trading"
    INTELLIGENCE = "intelligence"


class CostTier(str, Enum):
    """비용 등급"""
    FREE = "free"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class SkillMetadata:
    """Skill 메타데이터"""
    name: str  # 예: "MarketData.News"
    category: SkillCategory
    description: str
    keywords: List[str] = field(default_factory=list)
    cost_tier: CostTier = CostTier.MEDIUM
    requires_api_key: bool = False
    rate_limit_per_min: Optional[int] = None


class BaseSkill(ABC):
    """
    모든 Skill의 기본 클래스

    각 Skill은:
    1. 도구 정의 제공 (OpenAI Function Calling 형식)
    2. 도구 실행 기능
    3. 메타데이터 제공 (라우팅용)

    Usage:
        class MySkill(BaseSkill):
            def __init__(self):
                super().__init__(
                    name="MyGroup.MySkill",
                    category=SkillCategory.MARKET_DATA,
                    description="My skill description"
                )

            def get_tools(self) -> List[Dict]:
                return [...]

            async def execute(self, tool_name: str, **kwargs):
                # 도구 실행 로직
                pass
    """

    def __init__(
        self,
        name: str,
        category: SkillCategory,
        description: str,
        keywords: Optional[List[str]] = None,
        cost_tier: CostTier = CostTier.MEDIUM,
        requires_api_key: bool = False,
        rate_limit_per_min: Optional[int] = None,
    ):
        """
        Args:
            name: Skill 이름 (예: "MarketData.News")
            category: Skill 카테고리
            description: Skill 설명
            keywords: 라우팅용 키워드
            cost_tier: 비용 등급
            requires_api_key: API 키 필요 여부
            rate_limit_per_min: 분당 호출 제한
        """
        self.metadata = SkillMetadata(
            name=name,
            category=category,
            description=description,
            keywords=keywords or [],
            cost_tier=cost_tier,
            requires_api_key=requires_api_key,
            rate_limit_per_min=rate_limit_per_min,
        )

        # 통계
        self.stats = {
            "total_calls": 0,
            "total_errors": 0,
            "total_cost_usd": 0.0,
        }

        logger.info(f"Skill initialized: {self.metadata.name}")

    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        이 Skill이 제공하는 도구 목록 반환

        Returns:
            OpenAI Function Calling 형식의 도구 정의 리스트
            [
                {
                    "type": "function",
                    "function": {
                        "name": "tool_name",
                        "description": "Tool description",
                        "parameters": {...}
                    }
                }
            ]
        """
        pass

    @abstractmethod
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """
        도구 실행

        Args:
            tool_name: 실행할 도구 이름
            **kwargs: 도구 파라미터

        Returns:
            실행 결과

        Raises:
            ValueError: 알 수 없는 도구
            Exception: 실행 오류
        """
        pass

    def get_metadata(self) -> SkillMetadata:
        """Skill 메타데이터 반환"""
        return self.metadata

    def get_statistics(self) -> Dict[str, Any]:
        """Skill 통계 조회"""
        return {
            **self.stats,
            "avg_cost_per_call": (
                self.stats["total_cost_usd"] / self.stats["total_calls"]
                if self.stats["total_calls"] > 0 else 0
            ),
            "error_rate": (
                self.stats["total_errors"] / self.stats["total_calls"]
                if self.stats["total_calls"] > 0 else 0
            ),
        }

    def _track_call(self, success: bool = True, cost_usd: float = 0.0):
        """호출 추적"""
        self.stats["total_calls"] += 1
        if not success:
            self.stats["total_errors"] += 1
        self.stats["total_cost_usd"] += cost_usd

    def _get_keywords(self) -> List[str]:
        """라우팅용 키워드 반환 (하위 호환)"""
        return self.metadata.keywords

    def _estimate_cost(self) -> str:
        """예상 비용 등급 반환 (하위 호환)"""
        return self.metadata.cost_tier.value


# ============================================================================
# Skill Registry
# ============================================================================

class SkillRegistry:
    """
    전역 Skill 레지스트리

    모든 Skill을 등록하고 관리

    Usage:
        registry = SkillRegistry()
        registry.register(my_skill)

        # 카테고리별 조회
        market_skills = registry.get_skills_by_category(SkillCategory.MARKET_DATA)

        # 이름으로 조회
        news_skill = registry.get_skill("MarketData.News")
    """

    def __init__(self):
        """초기화"""
        self._skills: Dict[str, BaseSkill] = {}
        logger.info("SkillRegistry initialized")

    def register(self, skill: BaseSkill):
        """
        Skill 등록

        Args:
            skill: BaseSkill 인스턴스
        """
        name = skill.metadata.name
        if name in self._skills:
            logger.warning(f"Skill already registered, overwriting: {name}")

        self._skills[name] = skill
        logger.info(f"Skill registered: {name}")

    def unregister(self, skill_name: str) -> bool:
        """
        Skill 등록 해제

        Args:
            skill_name: Skill 이름

        Returns:
            성공 여부
        """
        if skill_name in self._skills:
            del self._skills[skill_name]
            logger.info(f"Skill unregistered: {skill_name}")
            return True
        return False

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """
        이름으로 Skill 조회

        Args:
            skill_name: Skill 이름

        Returns:
            BaseSkill 인스턴스 또는 None
        """
        return self._skills.get(skill_name)

    def get_skills_by_category(self, category: SkillCategory) -> List[BaseSkill]:
        """
        카테고리별 Skill 조회

        Args:
            category: Skill 카테고리

        Returns:
            해당 카테고리의 Skill 리스트
        """
        return [
            skill for skill in self._skills.values()
            if skill.metadata.category == category
        ]

    def get_all_skills(self) -> List[BaseSkill]:
        """모든 Skill 조회"""
        return list(self._skills.values())

    def get_all_skill_names(self) -> List[str]:
        """등록된 모든 Skill 이름 조회"""
        return list(self._skills.keys())

    def search_skills(self, keyword: str) -> List[BaseSkill]:
        """
        키워드로 Skill 검색

        Args:
            keyword: 검색 키워드

        Returns:
            매칭되는 Skill 리스트
        """
        keyword_lower = keyword.lower()
        results = []

        for skill in self._skills.values():
            # 이름, 설명, 키워드에서 검색
            if (
                keyword_lower in skill.metadata.name.lower() or
                keyword_lower in skill.metadata.description.lower() or
                any(keyword_lower in kw.lower() for kw in skill.metadata.keywords)
            ):
                results.append(skill)

        return results

    def get_tools_for_skills(self, skill_names: List[str]) -> List[Dict[str, Any]]:
        """
        여러 Skill의 도구 정의를 병합

        Args:
            skill_names: Skill 이름 리스트

        Returns:
            병합된 도구 정의 리스트
        """
        tools = []

        for skill_name in skill_names:
            skill = self.get_skill(skill_name)
            if skill:
                try:
                    skill_tools = skill.get_tools()
                    tools.extend(skill_tools)
                except Exception as e:
                    logger.error(f"Error getting tools from {skill_name}: {e}")

        return tools

    def find_skill_by_tool(self, tool_name: str) -> Optional[BaseSkill]:
        """
        도구 이름으로 해당 Skill 찾기

        Args:
            tool_name: 도구 이름 (예: "search_news")

        Returns:
            해당 도구를 제공하는 Skill 또는 None
        """
        for skill in self._skills.values():
            try:
                tools = skill.get_tools()
                for tool in tools:
                    if tool.get("function", {}).get("name") == tool_name:
                        return skill
            except Exception as e:
                logger.error(f"Error checking tools for {skill.metadata.name}: {e}")

        return None

    def list_skills(self) -> List[str]:
        """등록된 모든 Skill 이름 목록 (get_all_skill_names의 별칭)"""
        return self.get_all_skill_names()

    def get_registry_info(self) -> Dict[str, Any]:
        """레지스트리 정보 조회"""
        category_counts = {}
        for category in SkillCategory:
            count = len(self.get_skills_by_category(category))
            if count > 0:
                category_counts[category.value] = count

        return {
            "total_skills": len(self._skills),
            "categories": category_counts,
            "skills": [
                {
                    "name": skill.metadata.name,
                    "category": skill.metadata.category.value,
                    "cost_tier": skill.metadata.cost_tier.value,
                    "tool_count": len(skill.get_tools()),
                }
                for skill in self._skills.values()
            ],
        }


# ============================================================================
# Global Registry Instance
# ============================================================================

_global_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """전역 Skill Registry 인스턴스"""
    global _global_registry

    if _global_registry is None:
        _global_registry = SkillRegistry()
        logger.info("Global SkillRegistry created")

    return _global_registry


def register_skill(skill: BaseSkill):
    """전역 레지스트리에 Skill 등록 (편의 함수)"""
    registry = get_skill_registry()
    registry.register(skill)
