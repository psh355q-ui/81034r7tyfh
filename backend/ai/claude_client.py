"""
Claude API Client for AI Trading Analysis.

This module provides a robust interface to Claude API with:
- Automatic retries with exponential backoff
- Error handling and logging
- Cost tracking
- Response parsing
- **Prompt Caching support for 90% cost reduction**
"""

import json
import logging
import time
from typing import Optional
from datetime import datetime, timedelta

import anthropic
from anthropic import Anthropic

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Claude API client for trading analysis.

    Features:
    - Conservative temperature (0.3) for consistent trading decisions
    - Automatic retry logic
    - Cost tracking per request
    - Structured response parsing
    - **Prompt Caching support for 90% cost reduction on cached tokens**
    """

    # Constitution System Prompt (will be cached)
    CONSTITUTION_SYSTEM_PROMPT = """You are an expert quantitative trading analyst with a strong focus on risk management and capital preservation.

CORE CONSTITUTION PRINCIPLES:

Article 1: Risk Management First
- Capital preservation is paramount
- Never recommend trades that could result in catastrophic loss (>5% of portfolio)
- Always set appropriate stop-loss levels for BUY recommendations
- Consider portfolio-level risk, not just individual position risk

Article 2: Data-Driven Decisions
- All recommendations must be based on quantitative data
- Technical indicators (RSI, MACD, volume, momentum) are primary signals
- Avoid emotional or speculative reasoning
- If data is insufficient or contradictory, recommend HOLD

Article 3: Conservative Approach
- When in doubt, recommend HOLD
- BUY only if conviction ≥ 70% AND risk is acceptable
- SELL if conviction < 40% OR significant risk detected
- Missing an opportunity is better than incurring a loss

Article 4: Transparency and Explainability
- Always provide clear reasoning (2-3 sentences minimum)
- List specific risk factors identified
- Explain which data points drove the decision
- Never provide vague or generic explanations

Article 5: Defensive Consensus
- Never override risk warnings without strong justification
- If multiple signals conflict, favor the conservative action
- Respect stop-loss and circuit breaker rules absolutely
- When market conditions are uncertain, reduce position sizes

Article 6: Position Sizing Rules
- Use Kelly Criterion with 0.5x safety factor
- Maximum 5% of portfolio in any single position (conservative limit)
- Maximum 10% in any single sector
- Reduce position size if risk_score > 0.6

Article 7: Circuit Breakers
- If portfolio daily drawdown > 2%, STOP all new BUY orders
- If portfolio monthly drawdown > 5%, enter defensive mode (SELL risky positions)
- If single position drops > 10% from entry, force re-evaluation
- If market VIX > 30, reduce all position size recommendations by 50%

RESPONSE FORMAT:
Always return valid JSON in this exact format:
{
    "action": "BUY" | "SELL" | "HOLD",
    "conviction": 0.0-1.0,
    "reasoning": "Brief explanation (2-3 sentences)",
    "risk_factors": ["factor1", "factor2", ...],
    "target_price": null or number,
    "stop_loss": null or number,
    "position_size": 0.0-5.0
}"""

    def __init__(self, api_key: Optional[str] = None, enable_caching: bool = True):
        """
        Initialize Claude client.

        Args:
            api_key: Claude API key (if None, loads from settings)
            enable_caching: Enable prompt caching for cost reduction (default: True)
        """
        self.api_key = api_key or settings.anthropic_api_key

        if not self.api_key or self.api_key == "":
            raise ValueError(
                "Claude API key not found. Set CLAUDE_API_KEY in .env file."
            )

        self.client = Anthropic(api_key=self.api_key)

        # Configuration
        self.model = "claude-3-5-haiku-20241022"  # Cost-efficient model
        self.max_tokens = settings.ai_max_tokens
        self.temperature = settings.ai_temperature
        self.timeout = settings.ai_request_timeout
        self.max_retries = settings.ai_max_retries
        self.enable_caching = enable_caching

        # Metrics
        self.total_requests = 0
        self.total_tokens_input = 0
        self.total_tokens_output = 0
        self.total_cost_usd = 0.0

        # Cache metrics
        self.total_cached_tokens = 0
        self.total_cache_creation_tokens = 0
        self.total_cache_read_tokens = 0
        self.cache_last_updated = datetime.now()

        logger.info(
            f"ClaudeClient initialized with model {self.model} "
            f"(caching: {'enabled' if enable_caching else 'disabled'})"
        )

    async def analyze_stock(
        self,
        ticker: str,
        features: dict,
        market_context: Optional[dict] = None,
        portfolio_context: Optional[dict] = None,
    ) -> dict:
        """
        Analyze a stock and provide trading recommendation.

        Args:
            ticker: Stock ticker symbol
            features: Dict of computed features (from Feature Store)
            market_context: Optional market conditions (VIX, sector performance, etc.)
            portfolio_context: Optional current portfolio state

        Returns:
            Dict with:
                - action: "BUY" | "SELL" | "HOLD"
                - conviction: 0.0-1.0 (confidence level)
                - reasoning: str (explanation)
                - risk_factors: list[str]
                - target_price: Optional[float]
                - stop_loss: Optional[float]
                - position_size: Optional[float] (% of portfolio)
        """
        prompt = self._build_analysis_prompt(
            ticker, features, market_context, portfolio_context
        )

        response_text = await self._call_api(prompt)

        # Parse structured response
        result = self._parse_trading_response(response_text)
        result["ticker"] = ticker
        result["analyzed_at"] = time.time()

        logger.info(
            f"Claude analysis for {ticker}: {result['action']} "
            f"(conviction: {result['conviction']:.2f})"
        )

        return result

    async def evaluate_risk(
        self,
        ticker: str,
        features: dict,
        news: Optional[list[str]] = None,
    ) -> dict:
        """
        Evaluate risk factors for a stock.

        Args:
            ticker: Stock ticker symbol
            features: Dict of computed features
            news: Optional list of recent news headlines

        Returns:
            Dict with:
                - risk_score: 0.0-1.0 (higher = more risky)
                - risk_factors: list[str]
                - max_position_size: float (% of portfolio)
                - requires_human_review: bool
        """
        prompt = self._build_risk_prompt(ticker, features, news)

        response_text = await self._call_api(prompt)
        result = self._parse_risk_response(response_text)

        logger.info(f"Risk evaluation for {ticker}: {result['risk_score']:.2f}")

        return result

    def _build_analysis_prompt(
        self,
        ticker: str,
        features: dict,
        market_context: Optional[dict],
        portfolio_context: Optional[dict],
    ) -> str:
        """Build analysis prompt for Claude."""
        prompt = f"""You are an expert quantitative trading analyst. Analyze {ticker} and provide a trading recommendation.

CONSTITUTION PRINCIPLES:
1. Risk Management First - Always prioritize capital preservation
2. Data-Driven Decisions - No emotional trading
3. Conservative Approach - When in doubt, don't trade

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
TASK:
Provide a trading recommendation in the following JSON format:

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

GUIDELINES:
- BUY only if conviction > 0.7 and risk is acceptable
- SELL if conviction < 0.4 or significant risk detected
- HOLD otherwise
- Always specify stop_loss if recommending BUY
- Position size should reflect conviction and risk (lower risk = larger size)
- Be conservative - it's okay to miss opportunities to avoid losses

Return ONLY valid JSON, no additional text.
"""

        return prompt

    def _build_risk_prompt(
        self,
        ticker: str,
        features: dict,
        news: Optional[list[str]],
    ) -> str:
        """Build risk evaluation prompt."""
        prompt = f"""You are a risk management specialist. Evaluate the risk of trading {ticker}.

STOCK DATA:
Ticker: {ticker}

Features:
{json.dumps(features, indent=2)}
"""

        if news:
            prompt += f"""
Recent News:
{chr(10).join(f"- {headline}" for headline in news[:10])}
"""

        prompt += """
TASK:
Evaluate the risk and provide assessment in JSON format:

```json
{
    "risk_score": 0.0-1.0,
    "risk_factors": ["factor1", "factor2", ...],
    "max_position_size": 0.0-5.0,
    "requires_human_review": true/false
}
```

RISK FACTORS TO CONSIDER:
- High volatility (vol_20d > 0.3)
- Negative momentum
- Recent negative news
- Unusual price movements
- Sector-specific risks

Return ONLY valid JSON.
"""

        return prompt

    async def _call_api(self, prompt: str, use_caching: bool = True) -> str:
        """
        Call Claude API with retry logic and optional prompt caching.

        Args:
            prompt: The prompt to send
            use_caching: Whether to use prompt caching (default: True)

        Returns:
            Response text from Claude

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                # Ensure prompt is properly encoded
                prompt = str(prompt).encode('utf-8', errors='replace').decode('utf-8')

                # Build messages
                if self.enable_caching and use_caching:
                    # Use system prompt with caching
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        system=[
                            {
                                "type": "text",
                                "text": self.CONSTITUTION_SYSTEM_PROMPT,
                                "cache_control": {"type": "ephemeral"}
                            }
                        ],
                        messages=[{"role": "user", "content": prompt}],
                    )
                else:
                    # Standard call without caching
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        messages=[{"role": "user", "content": prompt}],
                    )

                latency_ms = (time.time() - start_time) * 1000

                # Extract response text
                response_text = response.content[0].text

                # Update metrics
                self.total_requests += 1
                self.total_tokens_input += response.usage.input_tokens
                self.total_tokens_output += response.usage.output_tokens

                # Update cache metrics if available
                if hasattr(response.usage, 'cache_creation_input_tokens'):
                    self.total_cache_creation_tokens += response.usage.cache_creation_input_tokens
                if hasattr(response.usage, 'cache_read_input_tokens'):
                    self.total_cache_read_tokens += response.usage.cache_read_input_tokens
                    self.total_cached_tokens += response.usage.cache_read_input_tokens
                    if response.usage.cache_read_input_tokens > 0:
                        self.cache_last_updated = datetime.now()

                # Calculate cost (Claude 3.5 Haiku pricing)
                # Input: $0.80 per million tokens
                # Output: $4.00 per million tokens
                # Cache creation: $1.00 per million tokens (25% premium)
                # Cache read: $0.08 per million tokens (90% discount)
                input_cost = response.usage.input_tokens * 0.80 / 1_000_000
                output_cost = response.usage.output_tokens * 4.00 / 1_000_000

                cache_creation_cost = 0.0
                cache_read_cost = 0.0
                if hasattr(response.usage, 'cache_creation_input_tokens'):
                    cache_creation_cost = response.usage.cache_creation_input_tokens * 1.00 / 1_000_000
                if hasattr(response.usage, 'cache_read_input_tokens'):
                    cache_read_cost = response.usage.cache_read_input_tokens * 0.08 / 1_000_000

                cost = input_cost + output_cost + cache_creation_cost + cache_read_cost
                self.total_cost_usd += cost

                # Log with cache info if available
                cache_info = ""
                if hasattr(response.usage, 'cache_read_input_tokens') and response.usage.cache_read_input_tokens > 0:
                    cache_info = f", cached: {response.usage.cache_read_input_tokens}"

                logger.info(
                    f"Claude API call successful: "
                    f"{response.usage.input_tokens} in, "
                    f"{response.usage.output_tokens} out{cache_info}, "
                    f"${cost:.4f}, {latency_ms:.0f}ms"
                )

                return response_text

            except anthropic.RateLimitError as e:
                wait_time = 2**attempt  # Exponential backoff
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}/{self.max_retries}), "
                    f"waiting {wait_time}s"
                )
                time.sleep(wait_time)

            except anthropic.APIError as e:
                logger.error(f"Claude API error (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise

            except Exception as e:
                logger.error(
                    f"Unexpected error (attempt {attempt + 1}): {e}",
                    exc_info=True
                )
                if attempt == self.max_retries - 1:
                    raise

        raise Exception(f"Failed after {self.max_retries} retries")

    def _parse_trading_response(self, response_text: str) -> dict:
        """
        Parse Claude's trading recommendation response.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed dict with trading recommendation
        """
        try:
            # Extract JSON from markdown code block if present
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            else:
                json_text = response_text.strip()

            result = json.loads(json_text)

            # Validate required fields
            required_fields = ["action", "conviction", "reasoning"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # Normalize action
            result["action"] = result["action"].upper()
            if result["action"] not in ["BUY", "SELL", "HOLD"]:
                logger.warning(f"Invalid action: {result['action']}, defaulting to HOLD")
                result["action"] = "HOLD"

            # Ensure conviction is in range
            result["conviction"] = max(0.0, min(1.0, float(result["conviction"])))

            # Set defaults for optional fields
            result.setdefault("risk_factors", [])
            result.setdefault("target_price", None)
            result.setdefault("stop_loss", None)
            result.setdefault("position_size", 0.0)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            # Return conservative default
            return {
                "action": "HOLD",
                "conviction": 0.0,
                "reasoning": "Failed to parse AI response",
                "risk_factors": ["parsing_error"],
                "target_price": None,
                "stop_loss": None,
                "position_size": 0.0,
            }

    def _parse_risk_response(self, response_text: str) -> dict:
        """Parse Claude's risk evaluation response."""
        try:
            # Extract JSON (same as trading response)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            else:
                json_text = response_text.strip()

            result = json.loads(json_text)

            # Validate and normalize
            result["risk_score"] = max(0.0, min(1.0, float(result.get("risk_score", 0.5))))
            result.setdefault("risk_factors", [])
            result.setdefault("max_position_size", 3.0)
            result.setdefault("requires_human_review", False)

            return result

        except Exception as e:
            logger.error(f"Failed to parse risk response: {e}")
            # Conservative default: high risk
            return {
                "risk_score": 0.8,
                "risk_factors": ["parsing_error"],
                "max_position_size": 1.0,
                "requires_human_review": True,
            }

    def get_metrics(self) -> dict:
        """Get API usage metrics including cache statistics."""
        # Calculate cost without caching (for comparison)
        cost_without_caching = 0.0
        if self.total_tokens_input > 0:
            cost_without_caching = (
                self.total_tokens_input * 0.80 / 1_000_000 +
                self.total_tokens_output * 4.00 / 1_000_000
            )

        # Calculate savings from caching
        savings_usd = cost_without_caching - self.total_cost_usd
        savings_percentage = (
            (savings_usd / cost_without_caching * 100)
            if cost_without_caching > 0
            else 0.0
        )

        # Check if cache is still valid (5 minutes TTL)
        cache_valid = (
            (datetime.now() - self.cache_last_updated).total_seconds() < 300
            if self.cache_last_updated
            else False
        )

        return {
            "total_requests": self.total_requests,
            "total_tokens_input": self.total_tokens_input,
            "total_tokens_output": self.total_tokens_output,
            "total_cost_usd": self.total_cost_usd,
            "avg_cost_per_request": (
                self.total_cost_usd / self.total_requests
                if self.total_requests > 0
                else 0.0
            ),
            # Cache metrics
            "caching_enabled": self.enable_caching,
            "cache_creation_tokens": self.total_cache_creation_tokens,
            "cache_read_tokens": self.total_cache_read_tokens,
            "total_cached_tokens": self.total_cached_tokens,
            "cache_hit_rate": (
                self.total_cache_read_tokens / self.total_tokens_input * 100
                if self.total_tokens_input > 0
                else 0.0
            ),
            "cache_last_updated": self.cache_last_updated.isoformat() if self.cache_last_updated else None,
            "cache_is_valid": cache_valid,
            # Cost savings
            "cost_without_caching_usd": cost_without_caching,
            "savings_usd": savings_usd,
            "savings_percentage": savings_percentage,
        }


class MockClaudeClient:
    """
    Mock Claude client for testing without API key.

    Returns dummy responses for all methods.
    """

    def __init__(self):
        """Initialize mock client."""
        self.model = "claude-3-5-haiku-20241022"
        self.total_requests = 0
        self.total_tokens_input = 0
        self.total_tokens_output = 0
        self.total_cost_usd = 0.0
        logger.info("MockClaudeClient initialized (no API calls will be made)")

    async def analyze_stock(
        self,
        ticker: str,
        features: dict,
        market_context: Optional[dict] = None,
        portfolio_context: Optional[dict] = None,
    ) -> dict:
        """Return mock trading recommendation."""
        self.total_requests += 1
        self.total_tokens_input += 1000
        self.total_tokens_output += 200
        self.total_cost_usd += 0.001

        # Generate deterministic mock response based on ticker
        conviction = 0.5 + (hash(ticker) % 30) / 100  # 0.5-0.8

        return {
            "ticker": ticker,
            "action": "HOLD",
            "conviction": conviction,
            "reasoning": f"Mock analysis for {ticker} (testing mode)",
            "risk_factors": ["mock_testing"],
            "target_price": None,
            "stop_loss": None,
            "position_size": 2.0,
            "analyzed_at": time.time(),
        }

    async def evaluate_risk(
        self,
        ticker: str,
        features: dict,
        news: Optional[list[str]] = None,
    ) -> dict:
        """Return mock risk evaluation."""
        self.total_requests += 1
        self.total_tokens_input += 500
        self.total_tokens_output += 100
        self.total_cost_usd += 0.0005

        return {
            "risk_score": 0.5,
            "risk_factors": ["mock_testing"],
            "max_position_size": 3.0,
            "requires_human_review": False,
        }

    def get_metrics(self) -> dict:
        """Get mock metrics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens_input": self.total_tokens_input,
            "total_tokens_output": self.total_tokens_output,
            "total_cost_usd": self.total_cost_usd,
            "avg_cost_per_request": (
                self.total_cost_usd / self.total_requests
                if self.total_requests > 0
                else 0.0
            ),
        }
