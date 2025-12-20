"""
Semantic Router

3단계 라우팅 시스템 통합

Stage 1: Intent Classification (의도 분류)
Stage 2: Tool Group Selection (도구 그룹 선택)
Stage 3: Model Selection (모델 선택)

토큰 사용량 83% 절감 목표

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from backend.routing.intent_classifier import Intent, IntentClassifier, create_intent_classifier
from backend.routing.tool_selector import ToolGroupSelector, get_tool_selector
from backend.routing.model_selector import ModelSelector, ModelConfig, get_model_selector
from backend.utils.tool_cache import get_tool_cache

logger = logging.getLogger(__name__)


@dataclass
class RoutingResult:
    """라우팅 결과"""

    # Stage 1: Intent
    intent: str
    intent_confidence: float

    # Stage 2: Tools
    selected_tool_groups: List[str]
    tools: List[Dict[str, Any]]
    tool_count: int

    # Stage 3: Model
    provider: str
    model: str
    model_reason: str
    model_config: Dict[str, Any]

    # Caching
    use_cache: bool
    cache_key: Optional[str]

    # Metadata
    estimated_tokens: int
    estimated_cost_usd: float
    routing_time_ms: float

    # Timestamp
    routed_at: str


class SemanticRouter:
    """
    3단계 Semantic Router

    사용자 입력 → Intent 분류 → Tool Groups 선택 → Model 선택 → 실행

    Usage:
        router = SemanticRouter()
        result = await router.route("삼성전자 최근 뉴스 분석해줘")

        # result.intent = "news_analysis"
        # result.model = "gemini-1.5-flash"
        # result.tools = [뉴스 검색 도구들...]
    """

    def __init__(
        self,
        use_local_llm_for_intent: bool = False,
        enable_caching: bool = True,
        prefer_low_cost: bool = False,
    ):
        """
        Args:
            use_local_llm_for_intent: Intent 분류에 Local LLM 사용 여부
            enable_caching: 도구 정의 캐싱 활성화
            prefer_low_cost: 비용 우선 모드 (저비용 모델 선호)
        """
        self.intent_classifier = create_intent_classifier(use_local_llm=use_local_llm_for_intent)
        self.tool_selector = get_tool_selector()
        self.model_selector = get_model_selector()
        self.tool_cache = get_tool_cache() if enable_caching else None

        self.enable_caching = enable_caching
        self.prefer_low_cost = prefer_low_cost

        # 통계
        self.stats = {
            "total_routes": 0,
            "total_tokens_saved": 0,
            "total_cost_saved_usd": 0.0,
            "intent_distribution": {},
            "model_usage": {},
        }

        logger.info(
            f"SemanticRouter initialized (local_llm={use_local_llm_for_intent}, "
            f"caching={enable_caching}, low_cost={prefer_low_cost})"
        )

    async def route(self, user_input: str) -> RoutingResult:
        """
        사용자 입력 라우팅

        Args:
            user_input: 사용자 입력 텍스트

        Returns:
            RoutingResult
        """
        start_time = datetime.now()

        # ================================================================
        # Stage 1: Intent Classification
        # ================================================================
        if hasattr(self.intent_classifier, 'classify'):
            # Async LLM classifier
            if asyncio.iscoroutinefunction(self.intent_classifier.classify):
                intent, confidence = await self.intent_classifier.classify(user_input)
            else:
                intent, confidence = self.intent_classifier.classify(user_input)
        else:
            intent = Intent.GENERAL_QUERY
            confidence = 0.3

        logger.info(f"[Stage 1] Intent: {intent.value} (confidence={confidence:.2f})")

        # ================================================================
        # Stage 2: Tool Group Selection
        # ================================================================
        tool_groups = self.tool_selector.select_tool_groups(intent)
        tools = self.tool_selector.get_tools_for_intent(intent)

        logger.info(f"[Stage 2] Tool Groups: {tool_groups} ({len(tools)} tools)")

        # Tool Caching
        cache_key = None
        if self.enable_caching and tools:
            cache_key = self.tool_cache.cache_tools(tools)
            logger.debug(f"Tools cached: {cache_key}")

        # ================================================================
        # Stage 3: Model Selection
        # ================================================================
        if self.prefer_low_cost:
            model_config = self.model_selector.select_model_with_fallback(
                intent,
                prefer_low_cost=True
            )
        else:
            model_config = self.model_selector.select_model(intent)

        logger.info(
            f"[Stage 3] Model: {model_config.provider}/{model_config.model} "
            f"({model_config.reason})"
        )

        # ================================================================
        # 통계 및 비용 추정
        # ================================================================
        estimated_tokens = self.tool_selector.estimate_token_usage(intent)

        # 캐싱으로 인한 토큰 절감 (첫 요청 제외 90% 절감)
        if self.enable_caching and cache_key:
            cache_hit = self.tool_cache.is_cached(cache_key)
            if cache_hit:
                estimated_tokens = int(estimated_tokens * 0.1)  # 90% 절감

        # 비용 추정 (입력 토큰만, 출력은 요청에 따라 다름)
        cost_info = self.model_selector.estimate_cost(
            intent,
            input_tokens=estimated_tokens,
            output_tokens=500  # 평균 출력
        )

        # 라우팅 시간
        routing_time = (datetime.now() - start_time).total_seconds() * 1000

        # ================================================================
        # 통계 업데이트
        # ================================================================
        self._update_stats(intent, model_config, estimated_tokens, cost_info["total_cost_usd"])

        # ================================================================
        # 결과 반환
        # ================================================================
        result = RoutingResult(
            intent=intent.value,
            intent_confidence=confidence,
            selected_tool_groups=tool_groups,
            tools=tools,
            tool_count=len(tools),
            provider=model_config.provider,
            model=model_config.model,
            model_reason=model_config.reason,
            model_config={
                "max_tokens": model_config.max_tokens,
                "temperature": model_config.temperature,
                "estimated_cost": model_config.estimated_cost,
            },
            use_cache=self.enable_caching,
            cache_key=cache_key,
            estimated_tokens=estimated_tokens,
            estimated_cost_usd=cost_info["total_cost_usd"],
            routing_time_ms=routing_time,
            routed_at=datetime.now().isoformat(),
        )

        logger.info(
            f"Routing complete: {intent.value} → {model_config.model} "
            f"({len(tools)} tools, {estimated_tokens} tokens, {routing_time:.1f}ms)"
        )

        return result

    def route_sync(self, user_input: str) -> RoutingResult:
        """동기 버전 라우팅 (규칙 기반 Intent만 사용)"""
        import asyncio
        return asyncio.run(self.route(user_input))

    def _update_stats(
        self,
        intent: Intent,
        model_config: ModelConfig,
        tokens: int,
        cost: float
    ):
        """통계 업데이트"""
        self.stats["total_routes"] += 1

        # Intent 분포
        intent_key = intent.value
        self.stats["intent_distribution"][intent_key] = \
            self.stats["intent_distribution"].get(intent_key, 0) + 1

        # 모델 사용 통계
        model_key = f"{model_config.provider}/{model_config.model}"
        self.stats["model_usage"][model_key] = \
            self.stats["model_usage"].get(model_key, 0) + 1

        # 토큰/비용 절감 (캐싱 효과)
        # 가정: 캐싱 없이는 3000 토큰 사용
        baseline_tokens = 3000
        if tokens < baseline_tokens:
            self.stats["total_tokens_saved"] += (baseline_tokens - tokens)

    def get_statistics(self) -> Dict[str, Any]:
        """라우팅 통계 조회"""
        return {
            **self.stats,
            "cache_stats": self.tool_cache.get_statistics() if self.tool_cache else {},
        }

    def reset_statistics(self):
        """통계 초기화"""
        self.stats = {
            "total_routes": 0,
            "total_tokens_saved": 0,
            "total_cost_saved_usd": 0.0,
            "intent_distribution": {},
            "model_usage": {},
        }
        logger.info("Statistics reset")


# ============================================================================
# Helper Functions
# ============================================================================

def create_routing_request(user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    라우팅 요청 생성

    Args:
        user_input: 사용자 입력
        context: 추가 컨텍스트 (이전 대화, 사용자 설정 등)

    Returns:
        라우팅 요청 dict
    """
    return {
        "user_input": user_input,
        "context": context or {},
        "timestamp": datetime.now().isoformat(),
    }


def format_routing_result(result: RoutingResult, verbose: bool = False) -> str:
    """
    라우팅 결과 포맷팅 (로깅/디버깅용)

    Args:
        result: RoutingResult
        verbose: 상세 정보 포함 여부

    Returns:
        포맷팅된 문자열
    """
    lines = [
        "=" * 60,
        "Semantic Router Result",
        "=" * 60,
        f"Intent: {result.intent} (confidence: {result.intent_confidence:.2f})",
        f"Model: {result.provider}/{result.model}",
        f"Reason: {result.model_reason}",
        f"Tool Groups: {', '.join(result.selected_tool_groups)}",
        f"Tool Count: {result.tool_count}",
        f"Estimated Tokens: {result.estimated_tokens}",
        f"Estimated Cost: ${result.estimated_cost_usd:.6f}",
        f"Routing Time: {result.routing_time_ms:.1f}ms",
    ]

    if verbose:
        lines.extend([
            "-" * 60,
            "Tools:",
        ])
        for tool in result.tools:
            if "function" in tool:
                func = tool["function"]
                lines.append(f"  - {func.get('name', 'unknown')}: {func.get('description', '')[:50]}")

        lines.extend([
            "-" * 60,
            f"Cache: {'Enabled' if result.use_cache else 'Disabled'}",
            f"Cache Key: {result.cache_key or 'N/A'}",
            f"Routed At: {result.routed_at}",
        ])

    lines.append("=" * 60)

    return "\n".join(lines)


# ============================================================================
# Global Instance
# ============================================================================

_global_router: Optional[SemanticRouter] = None


def get_semantic_router(
    use_local_llm: bool = False,
    enable_caching: bool = True,
    prefer_low_cost: bool = False,
) -> SemanticRouter:
    """
    전역 Semantic Router 인스턴스

    Args:
        use_local_llm: Local LLM 사용
        enable_caching: 캐싱 활성화
        prefer_low_cost: 저비용 모드

    Returns:
        SemanticRouter 인스턴스
    """
    global _global_router

    if _global_router is None:
        _global_router = SemanticRouter(
            use_local_llm_for_intent=use_local_llm,
            enable_caching=enable_caching,
            prefer_low_cost=prefer_low_cost,
        )
        logger.info("Global SemanticRouter created")

    return _global_router


# Import for async check
import asyncio
