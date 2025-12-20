"""
Model Selector

Intent와 Tool Group에 따라 최적 AI 모델 선택

Stage 3 of Semantic Router:
- Intent 기반 모델 선택
- 비용/성능 최적화
- 멀티 모델 라우팅

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from backend.routing.intent_classifier import Intent

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """AI 모델 설정"""
    provider: str  # openai, gemini, claude, local
    model: str  # gpt-4o, gemini-1.5-flash, claude-sonnet-4-5 등
    reason: str  # 선택 이유
    estimated_cost: str  # low, medium, high
    max_tokens: int = 4096  # 최대 출력 토큰
    temperature: float = 0.7  # 온도


class ModelSelector:
    """
    Intent에 최적화된 AI 모델 선택

    각 Intent마다 가장 적합한 모델을 선택하여 비용 최적화

    Usage:
        selector = ModelSelector()
        model_config = selector.select_model(Intent.NEWS_ANALYSIS)
        # ModelConfig(provider='gemini', model='gemini-1.5-flash', ...)
    """

    # Intent별 최적 모델 설정
    MODEL_CONFIGS: Dict[Intent, ModelConfig] = {
        Intent.NEWS_ANALYSIS: ModelConfig(
            provider="gemini",
            model="gemini-1.5-flash",
            reason="뉴스 분석에 특화, 저렴한 비용, 빠른 응답",
            estimated_cost="low",
            max_tokens=2048,
            temperature=0.3,
        ),
        Intent.TRADING_EXECUTION: ModelConfig(
            provider="openai",
            model="gpt-4o-mini",
            reason="빠른 응답 속도, 높은 안정성, 거래 실행에 적합",
            estimated_cost="low",
            max_tokens=1024,
            temperature=0.1,  # 낮은 온도 (일관성 중요)
        ),
        Intent.STRATEGY_GENERATION: ModelConfig(
            provider="openai",
            model="gpt-4o",
            reason="복잡한 전략 생성, 높은 추론 품질, 코드 생성 우수",
            estimated_cost="high",
            max_tokens=4096,
            temperature=0.7,
        ),
        Intent.MARKET_RESEARCH: ModelConfig(
            provider="claude",
            model="claude-sonnet-4-5",
            reason="긴 컨텍스트 (200K), 심층 분석, 종합적 리서치",
            estimated_cost="high",
            max_tokens=4096,
            temperature=0.5,
        ),
        Intent.PORTFOLIO_MANAGEMENT: ModelConfig(
            provider="openai",
            model="gpt-4o-mini",
            reason="빠른 응답, 안정적인 계산, 실시간 조회",
            estimated_cost="low",
            max_tokens=2048,
            temperature=0.3,
        ),
        Intent.DATA_QUERY: ModelConfig(
            provider="local",
            model="llama3.2:3b",
            reason="간단한 쿼리, 완전 무료, 빠른 응답",
            estimated_cost="free",
            max_tokens=512,
            temperature=0.1,
        ),
        Intent.GENERAL_QUERY: ModelConfig(
            provider="openai",
            model="gpt-4o-mini",
            reason="범용 모델, 균형잡힌 성능/비용",
            estimated_cost="medium",
            max_tokens=2048,
            temperature=0.7,
        ),
    }

    # Provider별 API 설정
    PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "supports_function_calling": True,
            "supports_prompt_caching": True,
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com",
            "api_key_env": "GEMINI_API_KEY",
            "supports_function_calling": True,
            "supports_prompt_caching": False,
        },
        "claude": {
            "base_url": "https://api.anthropic.com/v1",
            "api_key_env": "CLAUDE_API_KEY",
            "supports_function_calling": True,
            "supports_prompt_caching": True,
        },
        "local": {
            "base_url": "http://localhost:11434",
            "api_key_env": None,
            "supports_function_calling": False,
            "supports_prompt_caching": False,
        }
    }

    def __init__(self):
        """초기화"""
        logger.info("ModelSelector initialized")

    def select_model(self, intent: Intent) -> ModelConfig:
        """
        Intent에 최적화된 모델 선택

        Args:
            intent: Intent

        Returns:
            ModelConfig
        """
        config = self.MODEL_CONFIGS.get(intent, self.MODEL_CONFIGS[Intent.GENERAL_QUERY])

        logger.debug(
            f"Model selected for {intent.value}: {config.provider}/{config.model} "
            f"(reason: {config.reason})"
        )

        return config

    def select_model_with_fallback(
        self,
        intent: Intent,
        prefer_low_cost: bool = False
    ) -> ModelConfig:
        """
        Fallback 전략이 있는 모델 선택

        Args:
            intent: Intent
            prefer_low_cost: 비용 우선 선택 여부

        Returns:
            ModelConfig
        """
        # 기본 선택
        config = self.select_model(intent)

        # 비용 우선 모드
        if prefer_low_cost and config.estimated_cost == "high":
            # 저비용 대안 선택
            if intent == Intent.STRATEGY_GENERATION:
                # gpt-4o → gpt-4o-mini
                config = ModelConfig(
                    provider="openai",
                    model="gpt-4o-mini",
                    reason="비용 절감 모드: gpt-4o 대신 gpt-4o-mini 사용",
                    estimated_cost="low",
                    max_tokens=4096,
                    temperature=0.7,
                )
            elif intent == Intent.MARKET_RESEARCH:
                # claude → gemini
                config = ModelConfig(
                    provider="gemini",
                    model="gemini-1.5-pro",
                    reason="비용 절감 모드: Claude 대신 Gemini Pro 사용",
                    estimated_cost="medium",
                    max_tokens=4096,
                    temperature=0.5,
                )

            logger.info(f"Fallback to low-cost model: {config.provider}/{config.model}")

        return config

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Provider 설정 조회"""
        return self.PROVIDER_CONFIGS.get(provider, {})

    def estimate_cost(
        self,
        intent: Intent,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """
        예상 비용 계산

        Args:
            intent: Intent
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수

        Returns:
            비용 정보
        """
        config = self.select_model(intent)

        # 모델별 토큰 가격 (2024년 12월 기준, USD per 1M tokens)
        PRICING = {
            ("openai", "gpt-4o"): {"input": 2.50, "output": 10.00},
            ("openai", "gpt-4o-mini"): {"input": 0.15, "output": 0.60},
            ("gemini", "gemini-1.5-flash"): {"input": 0.075, "output": 0.30},
            ("gemini", "gemini-1.5-pro"): {"input": 1.25, "output": 5.00},
            ("claude", "claude-sonnet-4-5"): {"input": 3.00, "output": 15.00},
            ("local", "llama3.2:3b"): {"input": 0.0, "output": 0.0},
        }

        key = (config.provider, config.model)
        prices = PRICING.get(key, {"input": 0.0, "output": 0.0})

        input_cost = (input_tokens / 1_000_000) * prices["input"]
        output_cost = (output_tokens / 1_000_000) * prices["output"]
        total_cost = input_cost + output_cost

        return {
            "provider": config.provider,
            "model": config.model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "estimated_cost_krw": round(total_cost * 1300, 2),  # USD to KRW
        }

    def get_all_models(self) -> Dict[str, ModelConfig]:
        """사용 가능한 모든 모델 정보"""
        return self.MODEL_CONFIGS.copy()

    def get_model_info(self, provider: str, model: str) -> Dict[str, Any]:
        """특정 모델 정보 조회"""
        for intent, config in self.MODEL_CONFIGS.items():
            if config.provider == provider and config.model == model:
                return {
                    "provider": config.provider,
                    "model": config.model,
                    "reason": config.reason,
                    "estimated_cost": config.estimated_cost,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "typical_use_cases": [intent.value],
                }

        return {}


# ============================================================================
# Multi-Model Router (Advanced)
# ============================================================================

class MultiModelRouter:
    """
    복수 모델 라우팅

    복잡한 작업을 여러 모델로 분산 처리
    예: 1차 분석 (Gemini) → 2차 요약 (GPT-4o)
    """

    def __init__(self):
        """초기화"""
        self.model_selector = ModelSelector()
        logger.info("MultiModelRouter initialized")

    def route_pipeline(self, intent: Intent, stages: List[str]) -> List[ModelConfig]:
        """
        파이프라인 단계별 모델 라우팅

        Args:
            intent: Intent
            stages: 단계 목록 (예: ["analysis", "summary", "recommendation"])

        Returns:
            각 단계별 ModelConfig 리스트
        """
        # 단계별 최적 모델 선택 전략
        stage_strategies = {
            "analysis": lambda: self._get_analysis_model(intent),
            "summary": lambda: self._get_summary_model(),
            "recommendation": lambda: self._get_recommendation_model(),
            "execution": lambda: self._get_execution_model(),
        }

        configs = []
        for stage in stages:
            strategy = stage_strategies.get(stage)
            if strategy:
                configs.append(strategy())
            else:
                # 기본값
                configs.append(self.model_selector.select_model(intent))

        logger.info(f"Multi-model pipeline: {[(c.provider, c.model) for c in configs]}")

        return configs

    def _get_analysis_model(self, intent: Intent) -> ModelConfig:
        """분석 단계 모델 (저비용)"""
        if intent == Intent.NEWS_ANALYSIS:
            return self.model_selector.MODEL_CONFIGS[Intent.NEWS_ANALYSIS]
        else:
            return ModelConfig(
                provider="gemini",
                model="gemini-1.5-flash",
                reason="분석 단계: 빠르고 저렴한 모델",
                estimated_cost="low",
            )

    def _get_summary_model(self) -> ModelConfig:
        """요약 단계 모델 (중간 품질)"""
        return ModelConfig(
            provider="openai",
            model="gpt-4o-mini",
            reason="요약 단계: 균형잡힌 품질/비용",
            estimated_cost="low",
        )

    def _get_recommendation_model(self) -> ModelConfig:
        """추천 단계 모델 (고품질)"""
        return ModelConfig(
            provider="openai",
            model="gpt-4o",
            reason="추천 단계: 높은 품질 필요",
            estimated_cost="high",
        )

    def _get_execution_model(self) -> ModelConfig:
        """실행 단계 모델 (안정성 중시)"""
        return self.model_selector.MODEL_CONFIGS[Intent.TRADING_EXECUTION]


# ============================================================================
# Global Instance
# ============================================================================

_global_selector: Optional[ModelSelector] = None


def get_model_selector() -> ModelSelector:
    """전역 Model Selector 인스턴스"""
    global _global_selector

    if _global_selector is None:
        _global_selector = ModelSelector()
        logger.info("Global ModelSelector created")

    return _global_selector
