"""
NewsFilter Component - 2-Stage Filtering for Cost Optimization

Market Intelligence v2.0 - Phase 1, T1.1

This component implements a 2-stage filtering mechanism to reduce LLM API costs by 90%:
- Stage 1: Lightweight model (gpt-4o-mini) checks relevance (YES/NO)
- Stage 2: Heavy model (claude-sonnet) performs deep analysis (only for relevant news)

Author: AI Trading System Team
Date: 2026-01-18
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ..llm_providers import LLMProvider, ModelConfig, ModelProvider


logger = logging.getLogger(__name__)


class NewsFilter(BaseIntelligence):
    """
    2-Stage News Filter

    Reduces LLM API costs by 90% through:
    1. Stage 1: Quick relevance check with lightweight model (gpt-4o-mini)
    2. Stage 2: Deep analysis with heavy model (claude-sonnet) only for relevant news

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.news_filter import NewsFilter

        llm = get_llm_provider()
        filter = NewsFilter(llm_provider=llm)

        result = await filter.process(article)
        if result.success and result.data["stage1_passed"]:
            # Article is relevant and analyzed
            topic = result.data.get("topic")
            sentiment = result.data.get("sentiment")
    """

    # Stage 1: Relevance check prompts
    STAGE1_SYSTEM_PROMPT = """You are a news relevance classifier for investment analysis.

Your task is to determine if a news article is relevant for investment analysis.

Criteria for RELEVANT (YES):
- Related to stocks, markets, economy, or sectors
- Contains company earnings, financial data, or business news
- Discusses government policies affecting markets
- Covers industry trends or sector movements

Criteria for NOT RELEVANT (NO):
- Weather reports (unless market-impacting)
- Celebrity gossip
- Sports scores (unless business-related)
- General human interest stories

Respond with ONLY: YES or NO"""

    STAGE1_USER_PROMPT_TEMPLATE = """Title: {title}
Content: {content}

Is this news article relevant for investment analysis? Respond with ONLY: YES or NO"""

    # Stage 2: Deep analysis prompts
    STAGE2_SYSTEM_PROMPT = """You are an expert financial analyst specializing in news sentiment and topic extraction.

Analyze the news article and extract:
1. topic: Main investment theme (e.g., "DEFENSE", "AI_TECH", "CONSUMER")
2. sentiment: Market sentiment ("BULLISH", "BEARISH", "NEUTRAL")
3. confidence: Your confidence level (0.0 to 1.0)
4. reasoning: Brief explanation (1-2 sentences)

Respond in JSON format:
{
    "topic": "THEME",
    "sentiment": "BULLISH/BEARISH/NEUTRAL",
    "confidence": 0.85,
    "reasoning": "Brief explanation"
}"""

    STAGE2_USER_PROMPT_TEMPLATE = """Title: {title}
Content: {content}

Extract the investment information from this news article."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        stage1_config: Optional[ModelConfig] = None,
        stage2_config: Optional[ModelConfig] = None,
    ):
        """
        Initialize NewsFilter

        Args:
            llm_provider: LLM Provider instance
            stage1_config: Custom Stage 1 config (optional)
            stage2_config: Custom Stage 2 config (optional)
        """
        super().__init__(
            name="NewsFilter",
            phase=IntelligencePhase.P0,
        )

        self.llm = llm_provider
        self.stage1_config = stage1_config or llm_provider.create_stage1_config()
        self.stage2_config = stage2_config or llm_provider.create_stage2_config()

        # Cost tracking
        self._stage1_calls = 0
        self._stage2_calls = 0

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Analyze news article (main entry point)

        Args:
            data: Article data with 'title' and 'content'

        Returns:
            IntelligenceResult: Analysis result
        """
        return await self.process(data)

    async def process(self, article: Dict[str, Any]) -> IntelligenceResult:
        """
        Process article through 2-stage filter

        Args:
            article: Article data

        Returns:
            IntelligenceResult: Processing result with:
                - stage1_passed: Boolean
                - stage2_completed: Boolean
                - topic: Extracted theme (if stage2 completed)
                - sentiment: Market sentiment (if stage2 completed)
                - confidence: Confidence score (if stage2 completed)
                - reasoning: Explanation (if stage2 completed)
                - cost_savings: Estimated cost reduction
        """
        # Validate input
        try:
            self.validate_input(article, ["title", "content"])
        except ValueError as e:
            result = self.create_result(
                success=False,
                data={"stage": "news_filter"},
            )
            result.add_error(f"Input validation failed: {str(e)}")
            return result

        # Stage 1: Relevance check
        stage1_result = await self.stage1_relevance_check(article)
        if not stage1_result.success:
            return stage1_result

        # If not relevant, return early (cost saving!)
        if not stage1_result.data["is_relevant"]:
            return self.create_result(
                success=True,
                data={
                    "stage": "news_filter",
                    "stage1_passed": False,
                    "stage2_completed": False,
                    "is_relevant": False,
                    "reasoning": "Article not relevant for investment analysis",
                    "cost_savings": self._calculate_cost_savings(),
                },
                confidence=1.0,
                reasoning="Article filtered out in Stage 1",
            )

        # Stage 2: Deep analysis
        stage2_result = await self.stage2_deep_analysis(article)
        if not stage2_result.success:
            return stage2_result

        # Merge results
        return self.create_result(
            success=True,
            data={
                "stage": "news_filter",
                "stage1_passed": True,
                "stage2_completed": True,
                "is_relevant": True,
                **stage2_result.data,
                "cost_savings": self._calculate_cost_savings(),
            },
            confidence=stage2_result.confidence,
            reasoning=stage2_result.reasoning,
            metadata={
                "stage1_confidence": stage1_result.data.get("confidence", 0),
                "stage1_latency_ms": stage1_result.metadata.get("latency_ms", 0),
                "stage2_latency_ms": stage2_result.metadata.get("latency_ms", 0),
            },
        )

    async def stage1_relevance_check(self, article: Dict[str, Any]) -> IntelligenceResult:
        """
        Stage 1: Quick relevance check

        Args:
            article: Article data

        Returns:
            IntelligenceResult: Relevance check result
        """
        start_time = datetime.now()

        try:
            # Build prompt
            prompt = self.STAGE1_USER_PROMPT_TEMPLATE.format(
                title=article["title"],
                content=article["content"][:500],  # Limit content for speed
            )

            # Call LLM
            response = await self.llm.complete_with_system(
                system_prompt=self.STAGE1_SYSTEM_PROMPT,
                user_prompt=prompt,
                config=self.stage1_config,
            )

            self._stage1_calls += 1

            # Parse response
            content = response.content.strip().upper()
            is_relevant = content == "YES"

            latency = (datetime.now() - start_time).total_seconds() * 1000

            return self.create_result(
                success=True,
                data={
                    "stage": "stage1",
                    "is_relevant": is_relevant,
                    "raw_response": content,
                    "confidence": 1.0,  # Binary decision
                },
                confidence=1.0,
                reasoning=f"Stage 1 relevance check: {'RELEVANT' if is_relevant else 'NOT RELEVANT'}",
                metadata={
                    "latency_ms": int(latency),
                    "tokens_used": response.tokens_used,
                },
            )

        except Exception as e:
            logger.error(f"Stage 1 error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "stage1"},
            )
            result.add_error(f"Stage 1 error: {str(e)}")
            return result

    async def stage2_deep_analysis(self, article: Dict[str, Any]) -> IntelligenceResult:
        """
        Stage 2: Deep analysis

        Args:
            article: Article data

        Returns:
            IntelligenceResult: Deep analysis result
        """
        start_time = datetime.now()

        try:
            # Build prompt
            prompt = self.STAGE2_USER_PROMPT_TEMPLATE.format(
                title=article["title"],
                content=article["content"],
            )

            # Call LLM
            response = await self.llm.complete_with_system(
                system_prompt=self.STAGE2_SYSTEM_PROMPT,
                user_prompt=prompt,
                config=self.stage2_config,
            )

            self._stage2_calls += 1

            # Parse JSON response
            import json
            try:
                parsed = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback: extract key information from text
                parsed = self._parse_fallback(response.content)

            latency = (datetime.now() - start_time).total_seconds() * 1000

            return self.create_result(
                success=True,
                data={
                    "stage": "stage2",
                    **parsed,
                },
                confidence=parsed.get("confidence", 0.7),
                reasoning=parsed.get("reasoning", ""),
                metadata={
                    "latency_ms": int(latency),
                    "tokens_used": response.tokens_used,
                },
            )

        except Exception as e:
            logger.error(f"Stage 2 error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "stage2"},
            )
            result.add_error(f"Stage 2 error: {str(e)}")
            return result

    def _parse_fallback(self, text: str) -> Dict[str, Any]:
        """
        Fallback parser when JSON parsing fails

        Args:
            text: LLM response text

        Returns:
            Dict: Parsed data
        """
        # Simple keyword extraction
        topic = "GENERAL"
        if "방산" in text or "국방" in text or "defense" in text.lower():
            topic = "DEFENSE"
        elif "AI" in text.upper() or "반도체" in text or "chip" in text.lower():
            topic = "AI_TECH"
        elif "삼성" in text or "samsung" in text.lower():
            topic = "CONSUMER"

        sentiment = "NEUTRAL"
        if "상승" in text or "급등" in text or "positive" in text.lower():
            sentiment = "BULLISH"
        elif "하락" in text or "급락" in text or "negative" in text.lower():
            sentiment = "BEARISH"

        return {
            "topic": topic,
            "sentiment": sentiment,
            "confidence": 0.5,
            "reasoning": text[:200],
        }

    def _calculate_cost_savings(self) -> Dict[str, Any]:
        """
        Calculate cost savings from 2-stage filtering

        Returns:
            Dict: Cost savings metrics
        """
        # Cost assumptions (per 1M tokens)
        STAGE1_COST_PER_1M = 0.15  # gpt-4o-mini: $0.15/1M tokens
        STAGE2_COST_PER_1M = 3.0   # claude-sonnet: $3/1M tokens

        # Estimate tokens per call
        STAGE1_TOKENS = 200
        STAGE2_TOKENS = 2000

        # Calculate costs
        stage1_cost = self._stage1_calls * STAGE1_TOKENS * STAGE1_COST_PER_1M / 1_000_000
        stage2_cost = self._stage2_calls * STAGE2_TOKENS * STAGE2_COST_PER_1M / 1_000_000
        total_cost = stage1_cost + stage2_cost

        # Cost without filtering (all Stage 2)
        total_calls = self._stage1_calls + self._stage2_calls
        no_filter_cost = total_calls * STAGE2_TOKENS * STAGE2_COST_PER_1M / 1_000_000

        # Savings
        savings = no_filter_cost - total_cost
        savings_pct = (savings / no_filter_cost * 100) if no_filter_cost > 0 else 0

        return {
            "stage1_calls": self._stage1_calls,
            "stage2_calls": self._stage2_calls,
            "total_cost_usd": round(total_cost, 4),
            "no_filter_cost_usd": round(no_filter_cost, 4),
            "savings_usd": round(savings, 4),
            "savings_pct": round(savings_pct, 1),
        }

    def get_cost_report(self) -> str:
        """
        Get cost savings report

        Returns:
            str: Cost savings report
        """
        metrics = self._calculate_cost_savings()
        return (
            f"NewsFilter Cost Report:\n"
            f"  Stage 1 calls: {metrics['stage1_calls']}\n"
            f"  Stage 2 calls: {metrics['stage2_calls']}\n"
            f"  Total cost: ${metrics['total_cost_usd']}\n"
            f"  Without filter: ${metrics['no_filter_cost_usd']}\n"
            f"  Savings: ${metrics['savings_usd']} ({metrics['savings_pct']}%)"
        )


# Factory function for convenience
def create_news_filter(
    llm_provider: Optional[LLMProvider] = None,
) -> NewsFilter:
    """
    Create NewsFilter instance

    Args:
        llm_provider: LLM Provider (uses default if None)

    Returns:
        NewsFilter: Configured filter instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return NewsFilter(llm_provider=llm_provider)
