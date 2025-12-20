"""
Claude Prompt Caching Implementation for AI Trading System.

This module implements Claude's Prompt Caching feature to reduce costs by up to 90%
for repeated prompts (e.g., system instructions, tool definitions, constitution rules).

Key Features:
- Cache control for long system prompts
- Tool definition caching
- Constitution rules caching
- Automatic cache refresh (5-minute TTL)

Cost Savings:
- Cached input: $0.30 per MTok (90% discount from $3.00)
- Cached output: $15.00 per MTok (no discount)
- Cache writes: $3.75 per MTok (25% premium for first write)

References:
- https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlock

logger = logging.getLogger(__name__)


class PromptCachingClient:
    """
    Claude client with Prompt Caching support.

    Caches:
    1. System instructions (Constitution rules)
    2. Tool definitions (if using function calling)
    3. Long context (e.g., SEC filings, market data)
    """

    # Constitution principles (cached for all requests)
    CONSTITUTION_SYSTEM_PROMPT = """You are an expert quantitative trading analyst for an institutional-grade AI trading system.

CORE CONSTITUTION PRINCIPLES:

Article 1: Risk Management First
- Capital preservation is paramount
- Never recommend trades that could result in catastrophic loss (>5% of portfolio)
- Always specify stop-loss levels for BUY recommendations
- Position sizing must reflect both conviction AND risk

Article 2: Data-Driven Decisions
- All recommendations must be based on quantitative data
- No emotional trading or speculation
- Market sentiment is informative, not decisive
- Technical indicators must be weighted appropriately

Article 3: Conservative Approach
- When in doubt, recommend HOLD
- It is better to miss opportunities than to incur losses
- BUY only if conviction ≥ 70% and risk is acceptable
- SELL if conviction < 40% or significant risk detected

Article 4: Transparency and Explainability
- Always provide clear reasoning (2-3 sentences minimum)
- List specific risk factors identified
- Explain how conviction score was calculated
- Reference specific data points in reasoning

Article 5: Defensive Consensus
- Never override risk warnings without strong justification
- Respect volatility constraints (>50% volatility → HOLD)
- Respect momentum filters (< -30% momentum → HOLD)
- Respect sector concentration limits

Article 6: Position Sizing Rules
- Kelly Criterion with 0.5x safety factor
- Maximum 10% in single position
- Maximum 30% in single sector
- Scale size with conviction: 70% → 2%, 90% → 5%

Article 7: Circuit Breakers
- Maximum 2% daily portfolio drawdown
- Maximum 5% monthly portfolio drawdown
- Automatic trading halt if limits exceeded

These principles are IMMUTABLE and must be followed for every recommendation.
"""

    def __init__(self, api_key: str):
        """
        Initialize Prompt Caching client.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Caching requires Sonnet/Opus
        self.max_tokens = 4096
        self.temperature = 0.3

        # Cache metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_input_tokens = 0
        self.total_cached_tokens = 0
        self.total_output_tokens = 0
        self.cache_creation_tokens = 0

        # Cache TTL tracking
        self.last_cache_refresh = datetime.now()
        self.cache_ttl = timedelta(minutes=5)  # Claude's cache TTL

        logger.info("PromptCachingClient initialized with caching support")

    def _should_refresh_cache(self) -> bool:
        """Check if cache should be refreshed (5-minute TTL)."""
        return datetime.now() - self.last_cache_refresh >= self.cache_ttl

    async def analyze_stock_cached(
        self,
        ticker: str,
        features: dict,
        market_context: Optional[dict] = None,
        portfolio_context: Optional[dict] = None,
    ) -> dict:
        """
        Analyze stock with prompt caching.

        The system prompt (Constitution) is cached, reducing costs for repeated calls.

        Args:
            ticker: Stock ticker symbol
            features: Technical features
            market_context: Optional market data
            portfolio_context: Optional portfolio state

        Returns:
            Trading recommendation with cache usage stats
        """

        # Build user prompt (NOT cached - this changes per request)
        user_prompt = self._build_user_prompt(
            ticker, features, market_context, portfolio_context
        )

        # Make API call with cache control
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=[
                    {
                        "type": "text",
                        "text": self.CONSTITUTION_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},  # Enable caching
                    }
                ],
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Update cache metrics
            usage = response.usage
            self.total_input_tokens += usage.input_tokens
            self.total_output_tokens += usage.output_tokens

            # Track cache performance
            if hasattr(usage, "cache_read_input_tokens") and usage.cache_read_input_tokens:
                self.total_cached_tokens += usage.cache_read_input_tokens
                self.cache_hits += 1
                cache_hit = True
            else:
                self.cache_misses += 1
                cache_hit = False

            if hasattr(usage, "cache_creation_input_tokens") and usage.cache_creation_input_tokens:
                self.cache_creation_tokens += usage.cache_creation_input_tokens

            # Parse response
            result = self._parse_response(response.content[0].text)
            result["ticker"] = ticker
            result["analyzed_at"] = datetime.now().isoformat()

            # Add cache stats
            result["cache_stats"] = {
                "cache_hit": cache_hit,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cached_tokens": getattr(usage, "cache_read_input_tokens", 0),
                "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0),
            }

            logger.info(
                f"Claude analysis for {ticker}: {result['action']} "
                f"(conviction: {result.get('conviction', 0):.2f}) "
                f"[Cache {'HIT' if cache_hit else 'MISS'}]"
            )

            return result

        except Exception as e:
            logger.error(f"Error in cached analysis for {ticker}: {e}")
            raise

    async def analyze_sec_filing_cached(
        self,
        ticker: str,
        filing_text: str,
        filing_type: str = "10-K",
    ) -> dict:
        """
        Analyze SEC filing with multi-level caching.

        Caches:
        1. System prompt (Constitution)
        2. Filing text (if it's long and unchanging)

        Args:
            ticker: Stock ticker
            filing_text: Extracted filing text
            filing_type: Type of filing (10-K, 10-Q, etc.)

        Returns:
            Analysis with risk factors and key insights
        """

        # Build analysis prompt
        filing_prompt = f"""Analyze the following SEC {filing_type} filing for {ticker}.

FILING TEXT:
{filing_text}

TASK:
Extract and analyze the following in JSON format:

```json
{{
    "risk_factors": ["factor1", "factor2", ...],
    "key_insights": ["insight1", "insight2", ...],
    "financial_health": "STRONG" | "MODERATE" | "WEAK",
    "growth_outlook": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
    "competitive_position": "description",
    "management_tone": "OPTIMISTIC" | "CAUTIOUS" | "DEFENSIVE",
    "red_flags": ["flag1", "flag2", ...] or []
}}
```

Focus on:
- Material risks mentioned in Risk Factors section
- MD&A tone and forward-looking statements
- Changes from previous filings
- Regulatory or legal concerns

Return ONLY valid JSON.
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=[
                    {
                        "type": "text",
                        "text": self.CONSTITUTION_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": filing_prompt,
                                "cache_control": {"type": "ephemeral"},  # Cache long filing
                            }
                        ],
                    }
                ],
            )

            # Update metrics
            usage = response.usage
            self.total_input_tokens += usage.input_tokens
            self.total_output_tokens += usage.output_tokens

            if hasattr(usage, "cache_read_input_tokens") and usage.cache_read_input_tokens:
                self.total_cached_tokens += usage.cache_read_input_tokens
                self.cache_hits += 1

            if hasattr(usage, "cache_creation_input_tokens") and usage.cache_creation_input_tokens:
                self.cache_creation_tokens += usage.cache_creation_input_tokens

            # Parse response
            result = self._parse_response(response.content[0].text)
            result["ticker"] = ticker
            result["filing_type"] = filing_type

            logger.info(f"SEC filing analysis for {ticker}: {result.get('financial_health')}")

            return result

        except Exception as e:
            logger.error(f"Error analyzing SEC filing for {ticker}: {e}")
            raise

    def _build_user_prompt(
        self,
        ticker: str,
        features: dict,
        market_context: Optional[dict],
        portfolio_context: Optional[dict],
    ) -> str:
        """Build user prompt (NOT cached)."""
        prompt = f"""Analyze {ticker} and provide a trading recommendation.

STOCK DATA:
Ticker: {ticker}

Technical Features:
{json.dumps(features, indent=2)}
"""

        if market_context:
            prompt += f"""
Market Context:
{json.dumps(market_context, indent=2)}
"""

        if portfolio_context:
            prompt += f"""
Current Portfolio:
{json.dumps(portfolio_context, indent=2)}
"""

        prompt += """
Provide a trading recommendation in JSON format:

```json
{
    "action": "BUY" | "SELL" | "HOLD",
    "conviction": 0.0-1.0,
    "reasoning": "Brief explanation (2-3 sentences)",
    "risk_factors": ["factor1", "factor2", ...],
    "target_price": null or number,
    "stop_loss": null or number,
    "position_size": 0.0-5.0 (% of portfolio, max 5%)
}
```

Remember:
- BUY only if conviction ≥ 0.7 and risk is acceptable
- SELL if conviction < 0.4 or significant risk detected
- HOLD otherwise
- Always specify stop_loss for BUY
- Position size reflects conviction AND risk

Return ONLY valid JSON.
"""
        return prompt

    def _parse_response(self, text: str) -> dict:
        """Parse Claude's JSON response."""
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                json_text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                json_text = text[start:end].strip()
            else:
                json_text = text.strip()

            return json.loads(json_text)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}\nResponse: {text}")
            # Return default HOLD response
            return {
                "action": "HOLD",
                "conviction": 0.5,
                "reasoning": "Failed to parse AI response",
                "risk_factors": ["Response parsing error"],
                "target_price": None,
                "stop_loss": None,
                "position_size": 0.0,
            }

    def get_cache_stats(self) -> dict:
        """
        Get cache performance statistics.

        Returns:
            Dict with cache metrics and cost savings
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0.0

        # Cost calculation (per Million tokens)
        # Without caching: $3.00/MTok input
        # With caching: $0.30/MTok cached read, $3.75/MTok cache write
        cost_without_caching = (self.total_input_tokens / 1_000_000) * 3.00
        cost_with_caching = (
            (self.total_input_tokens - self.total_cached_tokens) / 1_000_000
        ) * 3.00 + (self.total_cached_tokens / 1_000_000) * 0.30 + (
            self.cache_creation_tokens / 1_000_000
        ) * 3.75

        savings = cost_without_caching - cost_with_caching
        savings_percent = (savings / cost_without_caching * 100) if cost_without_caching > 0 else 0.0

        return {
            "total_requests": total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.1%}",
            "total_input_tokens": self.total_input_tokens,
            "total_cached_tokens": self.total_cached_tokens,
            "total_output_tokens": self.total_output_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cost_without_caching_usd": f"${cost_without_caching:.4f}",
            "cost_with_caching_usd": f"${cost_with_caching:.4f}",
            "savings_usd": f"${savings:.4f}",
            "savings_percent": f"{savings_percent:.1f}%",
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    import os

    async def test_caching():
        """Test prompt caching with example data."""
        client = PromptCachingClient(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Example features
        features = {
            "price": 150.25,
            "volume": 5000000,
            "rsi": 65.5,
            "macd": 2.1,
            "volatility": 0.25,
            "momentum": 0.05,
        }

        # First call - cache MISS
        print("First call (cache MISS expected)...")
        result1 = await client.analyze_stock_cached("AAPL", features)
        print(f"Result: {result1['action']}, Cache: {result1['cache_stats']}")

        # Second call - cache HIT (within 5 min)
        print("\nSecond call (cache HIT expected)...")
        result2 = await client.analyze_stock_cached("AAPL", features)
        print(f"Result: {result2['action']}, Cache: {result2['cache_stats']}")

        # Stats
        print("\n" + "=" * 50)
        stats = client.get_cache_stats()
        print("Cache Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    asyncio.run(test_caching())
