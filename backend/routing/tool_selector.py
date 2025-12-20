"""
Tool Group Selector

Intent에 따라 필요한 도구 그룹을 선택하는 모듈

Stage 2 of Semantic Router:
- Intent → Skill Group 매핑
- 동적 도구 로딩 (필요한 것만)
- 토큰 사용량 최소화

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import List, Dict, Any, Set
from backend.routing.intent_classifier import Intent

logger = logging.getLogger(__name__)


class ToolGroup(str):
    """도구 그룹 정의"""

    # Market Data
    NEWS = "MarketData.News"
    SEARCH = "MarketData.Search"
    CALENDAR = "MarketData.Calendar"

    # Fundamental
    SEC = "Fundamental.SEC"
    FINANCIALS = "Fundamental.Financials"
    VALUE_CHAIN = "Fundamental.ValueChain"

    # Technical
    CHART = "Technical.Chart"
    BACKTEST = "Technical.Backtest"
    STATISTICS = "Technical.Statistics"

    # Trading
    KIS_API = "Trading.KIS"
    ORDER = "Trading.Order"
    RISK = "Trading.Risk"

    # Intelligence (AI Models)
    GEMINI = "Intelligence.Gemini"
    GPT4O = "Intelligence.GPT4o"
    CLAUDE = "Intelligence.Claude"
    LOCAL_LLM = "Intelligence.LocalLLM"


class ToolGroupSelector:
    """
    Intent에 따라 필요한 도구 그룹 선택

    Usage:
        selector = ToolGroupSelector()
        tool_groups = selector.select_tool_groups(Intent.NEWS_ANALYSIS)
        # Returns: ["MarketData.News", "Intelligence.Gemini"]
    """

    # Intent → Tool Groups 매핑
    INTENT_TO_TOOL_GROUPS: Dict[Intent, List[str]] = {
        Intent.NEWS_ANALYSIS: [
            ToolGroup.NEWS,
            ToolGroup.GEMINI,  # 뉴스 분석에 특화
        ],
        Intent.TRADING_EXECUTION: [
            ToolGroup.KIS_API,
            ToolGroup.ORDER,
            ToolGroup.RISK,
            ToolGroup.GPT4O,  # 빠른 응답
        ],
        Intent.STRATEGY_GENERATION: [
            ToolGroup.BACKTEST,
            ToolGroup.STATISTICS,
            ToolGroup.CHART,
            ToolGroup.GPT4O,  # 전략 생성에 특화
        ],
        Intent.MARKET_RESEARCH: [
            ToolGroup.SEARCH,
            ToolGroup.SEC,
            ToolGroup.FINANCIALS,
            ToolGroup.VALUE_CHAIN,
            ToolGroup.CLAUDE,  # 긴 컨텍스트, 심층 분석
        ],
        Intent.PORTFOLIO_MANAGEMENT: [
            ToolGroup.ORDER,
            ToolGroup.RISK,
            ToolGroup.STATISTICS,
            ToolGroup.GPT4O,
        ],
        Intent.DATA_QUERY: [
            ToolGroup.SEARCH,
            ToolGroup.CHART,
            ToolGroup.LOCAL_LLM,  # 간단한 쿼리
        ],
        Intent.GENERAL_QUERY: [
            ToolGroup.GPT4O,  # 범용
        ],
    }

    # Tool Group별 도구 정의 (실제로는 Skill에서 가져옴)
    # 여기서는 간단한 예시만 제공
    TOOL_DEFINITIONS: Dict[str, List[Dict[str, Any]]] = {
        ToolGroup.NEWS: [
            {
                "type": "function",
                "function": {
                    "name": "search_news",
                    "description": "Search news articles by keyword",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string", "description": "Search keyword"},
                            "max_results": {"type": "integer", "default": 20}
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_latest_news",
                    "description": "Get latest news articles",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "default": "all"},
                            "limit": {"type": "integer", "default": 10}
                        }
                    }
                }
            }
        ],
        ToolGroup.KIS_API: [
            {
                "type": "function",
                "function": {
                    "name": "get_account_balance",
                    "description": "Get KIS account balance and holdings",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_number": {"type": "string"}
                        },
                        "required": ["account_number"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_order",
                    "description": "Execute buy/sell order through KIS API",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {"type": "string"},
                            "action": {"type": "string", "enum": ["BUY", "SELL"]},
                            "quantity": {"type": "integer"},
                            "price": {"type": "number", "description": "Limit price (optional)"}
                        },
                        "required": ["ticker", "action", "quantity"]
                    }
                }
            }
        ],
        ToolGroup.BACKTEST: [
            {
                "type": "function",
                "function": {
                    "name": "run_backtest",
                    "description": "Run backtest for a trading strategy",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "strategy_code": {"type": "string", "description": "Python strategy code"},
                            "start_date": {"type": "string", "format": "date"},
                            "end_date": {"type": "string", "format": "date"},
                            "initial_capital": {"type": "number", "default": 10000000}
                        },
                        "required": ["strategy_code", "start_date", "end_date"]
                    }
                }
            }
        ],
        # ... 나머지 Tool Groups는 실제 구현 시 추가
    }

    def __init__(self):
        """초기화"""
        logger.info("ToolGroupSelector initialized")

    def select_tool_groups(self, intent: Intent) -> List[str]:
        """
        Intent에 맞는 Tool Groups 선택

        Args:
            intent: 분류된 Intent

        Returns:
            Tool Group 목록 (예: ["MarketData.News", "Intelligence.Gemini"])
        """
        groups = self.INTENT_TO_TOOL_GROUPS.get(intent, [ToolGroup.GPT4O])

        logger.debug(f"Selected tool groups for {intent.value}: {groups}")

        return groups

    def get_tools_for_intent(self, intent: Intent) -> List[Dict[str, Any]]:
        """
        Intent에 필요한 도구 정의 목록 반환

        Args:
            intent: Intent

        Returns:
            도구 정의 목록 (OpenAI Function Calling 형식)
        """
        tool_groups = self.select_tool_groups(intent)
        tools = []

        for group in tool_groups:
            group_tools = self.TOOL_DEFINITIONS.get(group, [])
            tools.extend(group_tools)

        logger.info(
            f"Tools for {intent.value}: {len(tools)} tools from {len(tool_groups)} groups"
        )

        return tools

    def get_tools_for_groups(self, tool_groups: List[str]) -> List[Dict[str, Any]]:
        """
        지정된 Tool Groups의 도구 정의 반환

        Args:
            tool_groups: Tool Group 목록

        Returns:
            도구 정의 목록
        """
        tools = []

        for group in tool_groups:
            group_tools = self.TOOL_DEFINITIONS.get(group, [])
            tools.extend(group_tools)

        return tools

    def estimate_token_usage(self, intent: Intent) -> int:
        """
        Intent에 필요한 도구의 예상 토큰 사용량

        Args:
            intent: Intent

        Returns:
            예상 토큰 수
        """
        tools = self.get_tools_for_intent(intent)

        # 간단한 추정: 도구 1개당 평균 100토큰
        avg_tokens_per_tool = 100
        return len(tools) * avg_tokens_per_tool

    def get_tool_group_info(self, tool_group: str) -> Dict[str, Any]:
        """Tool Group 정보 조회"""
        tools = self.TOOL_DEFINITIONS.get(tool_group, [])

        return {
            "tool_group": tool_group,
            "tool_count": len(tools),
            "tools": [t["function"]["name"] for t in tools if "function" in t],
            "estimated_tokens": len(tools) * 100,
        }

    def get_all_tool_groups(self) -> List[str]:
        """사용 가능한 모든 Tool Groups 목록"""
        return list(self.TOOL_DEFINITIONS.keys())


# ============================================================================
# Dynamic Tool Loader (실제 Skill과 통합)
# ============================================================================

class DynamicToolLoader:
    """
    Skill Layer에서 동적으로 도구 정의를 로드

    SkillRegistry와 통합하여 실제 Skill에서 도구 정의를 가져옵니다.
    """

    def __init__(self):
        """초기화"""
        self._registry = None
        logger.info("DynamicToolLoader initialized")

    def _get_registry(self):
        """SkillRegistry 가져오기 (지연 로딩)"""
        if self._registry is None:
            try:
                from backend.skills.base_skill import get_skill_registry
                self._registry = get_skill_registry()
                logger.info("SkillRegistry loaded into DynamicToolLoader")
            except ImportError as e:
                logger.error(f"Failed to import SkillRegistry: {e}")
                self._registry = None

        return self._registry

    def load_tools_for_groups(self, tool_groups: List[str]) -> List[Dict[str, Any]]:
        """
        Tool Groups에 해당하는 Skill에서 도구 정의 로드

        Args:
            tool_groups: Tool Group 목록

        Returns:
            도구 정의 목록 (OpenAI Function Calling 형식)
        """
        registry = self._get_registry()

        if registry is None:
            logger.warning("SkillRegistry not available, returning empty tools")
            return []

        tools = []

        for group in tool_groups:
            skill = registry.get_skill(group)

            if skill:
                try:
                    skill_tools = skill.get_tools()
                    tools.extend(skill_tools)
                    logger.debug(f"Loaded {len(skill_tools)} tools from {group}")
                except Exception as e:
                    logger.error(f"Error loading tools from {group}: {e}")
            else:
                logger.warning(f"Skill not found: {group}")

        logger.info(f"DynamicToolLoader: Loaded {len(tools)} tools from {len(tool_groups)} groups")

        return tools

    def get_registered_skills(self) -> List[str]:
        """등록된 Skill 목록"""
        registry = self._get_registry()

        if registry is None:
            return []

        return registry.list_skills()

    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        도구 실행 (Skill에서 직접 실행)

        Args:
            tool_name: 실행할 도구 이름
            **kwargs: 도구 파라미터

        Returns:
            실행 결과
        """
        registry = self._get_registry()

        if registry is None:
            raise RuntimeError("SkillRegistry not available")

        # 도구 이름으로 해당 Skill 찾기
        skill = registry.find_skill_by_tool(tool_name)

        if skill is None:
            raise ValueError(f"No skill found for tool: {tool_name}")

        # Skill에서 도구 실행
        return skill.execute(tool_name, **kwargs)


# ============================================================================
# Global Instances
# ============================================================================

_global_selector: ToolGroupSelector | None = None
_global_loader: DynamicToolLoader | None = None


def get_tool_selector() -> ToolGroupSelector:
    """전역 Tool Selector 인스턴스"""
    global _global_selector

    if _global_selector is None:
        _global_selector = ToolGroupSelector()
        logger.info("Global ToolGroupSelector created")

    return _global_selector


def get_tool_loader() -> DynamicToolLoader:
    """전역 Tool Loader 인스턴스"""
    global _global_loader

    if _global_loader is None:
        _global_loader = DynamicToolLoader()
        logger.info("Global DynamicToolLoader created")

    return _global_loader
