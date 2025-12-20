"""
ChatGPT Client for Market Regime Detection

Purpose: Detect market regime (BULL/SIDEWAYS/RISK_OFF/CRASH) to adjust strategy
Cost: $0.03/day (1 call/day with caching)
Role: Strategic layer - determines overall market positioning

Phase: 5 (Strategy Ensemble)
Task: 4 (ChatGPT Integration)
Author: AI Trading System Team
Date: 2025-11-14
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import os

try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai not installed. Install with: pip install openai")

logger = logging.getLogger(__name__)


# ============================================================================
# Market Regime Definitions
# ============================================================================

MARKET_REGIMES = {
    "BULL": {
        "description": "Strong uptrend, risk-on environment",
        "characteristics": [
            "SPY > 50-day MA and > 200-day MA",
            "VIX < 20",
            "Positive earnings surprises",
            "Low credit spreads",
            "Strong economic indicators"
        ],
        "sector_weights": {
            "Technology": 1.5,
            "Consumer Discretionary": 1.3,
            "Industrials": 1.2,
            "Financials": 1.1,
            "Communication Services": 1.1,
            "Materials": 1.0,
            "Healthcare": 0.9,
            "Real Estate": 0.8,
            "Consumer Staples": 0.7,
            "Utilities": 0.6,
            "Energy": 0.9,
        }
    },
    "SIDEWAYS": {
        "description": "Range-bound market, neutral environment",
        "characteristics": [
            "SPY oscillating around 50-day MA",
            "VIX 15-25 range",
            "Mixed earnings results",
            "Stable credit spreads",
            "Neutral economic indicators"
        ],
        "sector_weights": {
            "Technology": 1.0,
            "Consumer Discretionary": 1.0,
            "Industrials": 1.0,
            "Financials": 1.1,
            "Communication Services": 1.0,
            "Materials": 1.0,
            "Healthcare": 1.1,
            "Real Estate": 1.0,
            "Consumer Staples": 1.1,
            "Utilities": 1.0,
            "Energy": 1.0,
        }
    },
    "RISK_OFF": {
        "description": "Defensive positioning, elevated uncertainty",
        "characteristics": [
            "SPY < 50-day MA but > 200-day MA",
            "VIX 20-30",
            "Negative earnings surprises",
            "Widening credit spreads",
            "Weak economic indicators"
        ],
        "sector_weights": {
            "Technology": 0.7,
            "Consumer Discretionary": 0.6,
            "Industrials": 0.7,
            "Financials": 0.8,
            "Communication Services": 0.8,
            "Materials": 0.7,
            "Healthcare": 1.3,
            "Real Estate": 0.8,
            "Consumer Staples": 1.4,
            "Utilities": 1.5,
            "Energy": 0.8,
        }
    },
    "CRASH": {
        "description": "Market panic, extreme risk-off",
        "characteristics": [
            "SPY < 200-day MA with high volatility",
            "VIX > 30",
            "Market-wide selloff",
            "Extremely wide credit spreads",
            "Recession indicators"
        ],
        "sector_weights": {
            "Technology": 0.3,
            "Consumer Discretionary": 0.3,
            "Industrials": 0.4,
            "Financials": 0.5,
            "Communication Services": 0.4,
            "Materials": 0.4,
            "Healthcare": 1.2,
            "Real Estate": 0.5,
            "Consumer Staples": 1.5,
            "Utilities": 1.6,
            "Energy": 0.5,
        }
    }
}


# ============================================================================
# ChatGPT Client
# ============================================================================

class ChatGPTClient:
    """
    ChatGPT-4 client for market regime detection.
    
    Use Cases:
    1. Daily market regime classification
    2. Sector weight adjustments
    3. Strategic positioning guidance
    
    Cost Model:
    - GPT-4 Turbo: ~$0.03 per call (with ~2000 tokens)
    - Daily caching: $0.03/day = $0.90/month
    - Called once at market open
    
    Output:
    - regime: BULL | SIDEWAYS | RISK_OFF | CRASH
    - confidence: 0.0-1.0
    - sector_weights: Dict[str, float]
    - reasoning: str
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize ChatGPT client.
        
        Args:
            redis_client: Optional Redis client for caching
        
        Requires:
            OPENAI_API_KEY environment variable
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai not installed. "
                "Install with: pip install openai"
            )
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        self.redis = redis_client
        
        # Model selection: GPT-4 Turbo for cost efficiency
        self.model = "gpt-4-turbo-preview"
        
        # Metrics tracking
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
            "last_regime": None,
            "last_updated": None,
        }
        
        # Cache settings
        self.cache_ttl = 86400  # 24 hours
        self.cache_key = "market_regime:current"
        
        logger.info("ChatGPT client initialized with model: %s", self.model)
    
    async def detect_regime(
        self,
        market_data: Dict[str, Any],
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Detect current market regime using ChatGPT.
        
        Args:
            market_data: Dict containing:
                - spy_price: Current SPY price
                - spy_50ma: 50-day moving average
                - spy_200ma: 200-day moving average
                - vix: Current VIX level
                - vix_percentile: VIX percentile (0-100)
                - recent_returns: Dict of recent SPY returns
                    - 1d, 5d, 20d, 60d
                - credit_spreads: Dict of credit spread data
                    - investment_grade_spread
                    - high_yield_spread
                - economic_indicators: Dict of economic data
                    - unemployment_rate
                    - gdp_growth
                    - inflation_rate
                    - consumer_sentiment
                - earnings_season: Dict of earnings data
                    - beat_rate: % of companies beating estimates
                    - avg_surprise: Average earnings surprise %
            
            force_refresh: Skip cache and get fresh analysis
        
        Returns:
            Dict containing:
                - regime: BULL | SIDEWAYS | RISK_OFF | CRASH
                - confidence: 0.0-1.0
                - reasoning: str explaining the classification
                - sector_weights: Dict[str, float]
                - timestamp: ISO format timestamp
                - cost_usd: API call cost
        """
        import time
        start_time = time.time()
        
        # Check cache first (unless force refresh)
        if not force_refresh and self.redis:
            cached = await self._get_cached_regime()
            if cached:
                self.metrics["cache_hits"] += 1
                logger.info("Using cached market regime: %s", cached["regime"])
                return cached
        
        # Build prompt
        prompt = self._build_regime_detection_prompt(market_data)
        
        # Call ChatGPT
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Low temperature for consistent classification
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = self._parse_regime_response(response)
            
            # Calculate cost (approximate)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)
            result["cost_usd"] = cost
            result["timestamp"] = datetime.utcnow().isoformat()
            
            # Update metrics
            latency_ms = (time.time() - start_time) * 1000
            self._update_metrics(result, latency_ms, cost)
            
            # Cache result
            if self.redis:
                await self._cache_regime(result)
            
            logger.info(
                "Detected market regime: %s (confidence: %.2f, cost: $%.4f)",
                result["regime"],
                result["confidence"],
                cost
            )
            
            return result
            
        except Exception as e:
            logger.error("ChatGPT API error: %s", str(e))
            return self._get_fallback_regime(market_data)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for market regime detection."""
        return """You are an expert quantitative analyst specializing in market regime detection.

Your task is to classify the current market regime into one of four categories:
1. BULL - Strong uptrend, risk-on environment
2. SIDEWAYS - Range-bound, neutral environment
3. RISK_OFF - Defensive positioning, elevated uncertainty
4. CRASH - Market panic, extreme risk-off

You must respond with a JSON object containing:
{
    "regime": "BULL" | "SIDEWAYS" | "RISK_OFF" | "CRASH",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of your classification",
    "key_factors": ["factor1", "factor2", "factor3"],
    "risk_level": "LOW" | "MODERATE" | "HIGH" | "EXTREME"
}

Base your analysis on:
- Technical indicators (SPY vs moving averages)
- Volatility levels (VIX)
- Credit market conditions
- Economic fundamentals
- Earnings season performance

Be decisive and consistent. Avoid hedging unless genuinely uncertain."""

    def _build_regime_detection_prompt(self, market_data: Dict[str, Any]) -> str:
        """Build prompt for regime detection."""
        spy_price = market_data.get("spy_price", 0)
        spy_50ma = market_data.get("spy_50ma", 0)
        spy_200ma = market_data.get("spy_200ma", 0)
        vix = market_data.get("vix", 20)
        vix_percentile = market_data.get("vix_percentile", 50)
        
        recent_returns = market_data.get("recent_returns", {})
        credit_spreads = market_data.get("credit_spreads", {})
        economic = market_data.get("economic_indicators", {})
        earnings = market_data.get("earnings_season", {})
        
        # Calculate technical signals
        above_50ma = "Yes" if spy_price > spy_50ma else "No"
        above_200ma = "Yes" if spy_price > spy_200ma else "No"
        ma_trend = "Bullish" if spy_50ma > spy_200ma else "Bearish"
        
        prompt = f"""Analyze the current market conditions and classify the market regime.

TECHNICAL INDICATORS:
- SPY Price: ${spy_price:.2f}
- 50-day MA: ${spy_50ma:.2f} (Above: {above_50ma})
- 200-day MA: ${spy_200ma:.2f} (Above: {above_200ma})
- MA Trend: {ma_trend}

VOLATILITY:
- VIX Level: {vix:.2f}
- VIX Percentile (1-year): {vix_percentile:.1f}%

RECENT PERFORMANCE:
- 1-day return: {recent_returns.get('1d', 0):.2f}%
- 5-day return: {recent_returns.get('5d', 0):.2f}%
- 20-day return: {recent_returns.get('20d', 0):.2f}%
- 60-day return: {recent_returns.get('60d', 0):.2f}%

CREDIT MARKETS:
- Investment Grade Spread: {credit_spreads.get('investment_grade_spread', 1.5):.2f}%
- High Yield Spread: {credit_spreads.get('high_yield_spread', 4.0):.2f}%

ECONOMIC INDICATORS:
- Unemployment Rate: {economic.get('unemployment_rate', 4.0):.1f}%
- GDP Growth (YoY): {economic.get('gdp_growth', 2.5):.1f}%
- Inflation Rate: {economic.get('inflation_rate', 3.0):.1f}%
- Consumer Sentiment: {economic.get('consumer_sentiment', 70):.1f}

EARNINGS SEASON:
- Beat Rate: {earnings.get('beat_rate', 65):.1f}%
- Average Surprise: {earnings.get('avg_surprise', 3.0):.1f}%

Classify the current market regime (BULL/SIDEWAYS/RISK_OFF/CRASH) and provide your reasoning."""

        return prompt
    
    def _parse_regime_response(self, response) -> Dict[str, Any]:
        """Parse ChatGPT response into structured regime data."""
        try:
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            # Validate regime
            regime = parsed.get("regime", "SIDEWAYS").upper()
            if regime not in MARKET_REGIMES:
                logger.warning("Invalid regime '%s', defaulting to SIDEWAYS", regime)
                regime = "SIDEWAYS"
            
            # Validate confidence
            confidence = float(parsed.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))
            
            # Get sector weights for the detected regime
            sector_weights = MARKET_REGIMES[regime]["sector_weights"]
            
            return {
                "regime": regime,
                "confidence": confidence,
                "reasoning": parsed.get("reasoning", "No reasoning provided"),
                "key_factors": parsed.get("key_factors", []),
                "risk_level": parsed.get("risk_level", "MODERATE"),
                "sector_weights": sector_weights,
            }
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse ChatGPT response: %s", str(e))
            return {
                "regime": "SIDEWAYS",
                "confidence": 0.3,
                "reasoning": "Parse error - defaulting to neutral",
                "key_factors": [],
                "risk_level": "MODERATE",
                "sector_weights": MARKET_REGIMES["SIDEWAYS"]["sector_weights"],
            }
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate API call cost based on token usage.
        
        GPT-4 Turbo pricing (as of 2024):
        - Input: $0.01 per 1K tokens
        - Output: $0.03 per 1K tokens
        """
        input_cost = (input_tokens / 1000) * 0.01
        output_cost = (output_tokens / 1000) * 0.03
        return input_cost + output_cost
    
    def _update_metrics(
        self,
        result: Dict[str, Any],
        latency_ms: float,
        cost: float
    ):
        """Update internal metrics."""
        self.metrics["total_requests"] += 1
        self.metrics["total_cost_usd"] += cost
        self.metrics["last_regime"] = result["regime"]
        self.metrics["last_updated"] = datetime.utcnow().isoformat()
        
        # Running average of latency
        n = self.metrics["total_requests"]
        old_avg = self.metrics["avg_latency_ms"]
        self.metrics["avg_latency_ms"] = old_avg + (latency_ms - old_avg) / n
    
    async def _get_cached_regime(self) -> Optional[Dict[str, Any]]:
        """Get cached regime from Redis."""
        if not self.redis:
            return None
        
        try:
            cached = await self.redis.get(self.cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning("Cache read error: %s", str(e))
        
        return None
    
    async def _cache_regime(self, regime_data: Dict[str, Any]):
        """Cache regime data in Redis."""
        if not self.redis:
            return
        
        try:
            await self.redis.setex(
                self.cache_key,
                self.cache_ttl,
                json.dumps(regime_data)
            )
            logger.debug("Cached market regime for %d seconds", self.cache_ttl)
        except Exception as e:
            logger.warning("Cache write error: %s", str(e))
    
    def _get_fallback_regime(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get fallback regime using rule-based logic when API fails.
        """
        vix = market_data.get("vix", 20)
        spy_price = market_data.get("spy_price", 0)
        spy_50ma = market_data.get("spy_50ma", 0)
        spy_200ma = market_data.get("spy_200ma", 0)
        
        # Simple rule-based classification
        if vix > 30:
            regime = "CRASH"
            confidence = 0.7
        elif vix > 25 or spy_price < spy_200ma:
            regime = "RISK_OFF"
            confidence = 0.6
        elif spy_price > spy_50ma and spy_price > spy_200ma and vix < 20:
            regime = "BULL"
            confidence = 0.7
        else:
            regime = "SIDEWAYS"
            confidence = 0.5
        
        return {
            "regime": regime,
            "confidence": confidence,
            "reasoning": "Fallback rule-based classification (API unavailable)",
            "key_factors": ["VIX level", "SPY vs moving averages"],
            "risk_level": "HIGH" if regime in ["CRASH", "RISK_OFF"] else "MODERATE",
            "sector_weights": MARKET_REGIMES[regime]["sector_weights"],
            "timestamp": datetime.utcnow().isoformat(),
            "cost_usd": 0.0,  # No API call
            "fallback": True,
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def get_sector_weight(self, regime: str, sector: str) -> float:
        """
        Get sector weight for a given regime.
        
        Args:
            regime: BULL | SIDEWAYS | RISK_OFF | CRASH
            sector: Sector name (e.g., "Technology")
        
        Returns:
            Weight multiplier (default 1.0)
        """
        if regime not in MARKET_REGIMES:
            return 1.0
        
        weights = MARKET_REGIMES[regime]["sector_weights"]
        return weights.get(sector, 1.0)
    
    def adjust_position_size(
        self,
        base_size: float,
        regime: str,
        sector: str
    ) -> float:
        """
        Adjust position size based on regime and sector.
        
        Args:
            base_size: Original position size
            regime: Current market regime
            sector: Stock's sector
        
        Returns:
            Adjusted position size
        """
        weight = self.get_sector_weight(regime, sector)
        return base_size * weight


# ============================================================================
# Regime-Based Screener
# ============================================================================

class RegimeBasedScreener:
    """
    Screen stocks based on current market regime.
    
    Use Case:
    - Filter candidates based on regime-appropriate sectors
    - Adjust portfolio weights dynamically
    - Reduce exposure during RISK_OFF/CRASH
    """
    
    def __init__(self, chatgpt_client: ChatGPTClient):
        self.client = chatgpt_client
    
    async def filter_by_regime(
        self,
        candidates: List[Dict[str, Any]],
        regime: str,
        min_weight: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Filter candidates based on regime-appropriate sectors.
        
        Args:
            candidates: List of stock dicts with 'ticker' and 'sector' keys
            regime: Current market regime
            min_weight: Minimum sector weight to include (default 0.8)
        
        Returns:
            Filtered list of candidates with weights
        """
        if regime not in MARKET_REGIMES:
            logger.warning("Unknown regime '%s', using all candidates", regime)
            return candidates
        
        sector_weights = MARKET_REGIMES[regime]["sector_weights"]
        filtered = []
        
        for candidate in candidates:
            sector = candidate.get("sector", "Unknown")
            weight = sector_weights.get(sector, 1.0)
            
            if weight >= min_weight:
                candidate["regime_weight"] = weight
                filtered.append(candidate)
            else:
                logger.debug(
                    "Excluded %s (sector: %s, weight: %.2f)",
                    candidate.get("ticker"),
                    sector,
                    weight
                )
        
        # Sort by regime weight
        filtered.sort(key=lambda x: x.get("regime_weight", 1.0), reverse=True)
        
        logger.info(
            "Regime filter: %d -> %d candidates (regime: %s)",
            len(candidates),
            len(filtered),
            regime
        )
        
        return filtered
    
    def get_regime_strategy(self, regime: str) -> Dict[str, Any]:
        """
        Get strategy recommendations for current regime.
        
        Returns:
            Dict with strategy parameters
        """
        strategies = {
            "BULL": {
                "position_size_multiplier": 1.2,
                "max_positions": 20,
                "stop_loss_pct": 0.10,  # 10% stop loss
                "take_profit_pct": 0.25,  # 25% take profit
                "focus": "Momentum and growth",
                "avoid": "Defensive sectors",
            },
            "SIDEWAYS": {
                "position_size_multiplier": 1.0,
                "max_positions": 15,
                "stop_loss_pct": 0.08,  # 8% stop loss
                "take_profit_pct": 0.15,  # 15% take profit
                "focus": "Mean reversion and quality",
                "avoid": "High beta stocks",
            },
            "RISK_OFF": {
                "position_size_multiplier": 0.7,
                "max_positions": 10,
                "stop_loss_pct": 0.06,  # 6% stop loss
                "take_profit_pct": 0.10,  # 10% take profit
                "focus": "Defensive and low volatility",
                "avoid": "Cyclicals and high growth",
            },
            "CRASH": {
                "position_size_multiplier": 0.3,
                "max_positions": 5,
                "stop_loss_pct": 0.05,  # 5% stop loss
                "take_profit_pct": 0.08,  # 8% take profit
                "focus": "Cash and extreme quality only",
                "avoid": "All risk assets",
            },
        }
        
        return strategies.get(regime, strategies["SIDEWAYS"])


# ============================================================================
# Market Data Fetcher
# ============================================================================

class MarketDataFetcher:
    """
    Fetch market data required for regime detection.
    """
    
    def __init__(self):
        """Initialize fetcher."""
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            raise ImportError("yfinance not installed. Install with: pip install yfinance")
    
    async def get_market_data(self) -> Dict[str, Any]:
        """
        Fetch current market data for regime detection.
        
        Returns:
            Dict with all required market indicators
        """
        import asyncio
        
        # Fetch SPY and VIX data
        spy = self.yf.Ticker("SPY")
        vix = self.yf.Ticker("^VIX")
        
        # Get historical data for moving averages
        spy_hist = spy.history(period="1y")
        vix_hist = vix.history(period="1y")
        
        if spy_hist.empty or vix_hist.empty:
            raise ValueError("Failed to fetch market data")
        
        # Current prices
        spy_price = float(spy_hist["Close"].iloc[-1])
        vix_current = float(vix_hist["Close"].iloc[-1])
        
        # Moving averages
        spy_50ma = float(spy_hist["Close"].tail(50).mean())
        spy_200ma = float(spy_hist["Close"].tail(200).mean())
        
        # VIX percentile
        vix_percentile = (
            (vix_hist["Close"] < vix_current).sum() / len(vix_hist) * 100
        )
        
        # Recent returns
        recent_returns = {
            "1d": self._calculate_return(spy_hist, 1),
            "5d": self._calculate_return(spy_hist, 5),
            "20d": self._calculate_return(spy_hist, 20),
            "60d": self._calculate_return(spy_hist, 60),
        }
        
        # Placeholder for credit spreads and economic indicators
        # In production, these would come from FRED API or similar
        credit_spreads = {
            "investment_grade_spread": 1.50,  # Placeholder
            "high_yield_spread": 4.00,  # Placeholder
        }
        
        economic_indicators = {
            "unemployment_rate": 4.1,  # Placeholder
            "gdp_growth": 2.5,  # Placeholder
            "inflation_rate": 3.2,  # Placeholder
            "consumer_sentiment": 72.0,  # Placeholder
        }
        
        earnings_season = {
            "beat_rate": 68.0,  # Placeholder
            "avg_surprise": 4.2,  # Placeholder
        }
        
        return {
            "spy_price": spy_price,
            "spy_50ma": spy_50ma,
            "spy_200ma": spy_200ma,
            "vix": vix_current,
            "vix_percentile": vix_percentile,
            "recent_returns": recent_returns,
            "credit_spreads": credit_spreads,
            "economic_indicators": economic_indicators,
            "earnings_season": earnings_season,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _calculate_return(self, hist, days: int) -> float:
        """Calculate percentage return over given days."""
        if len(hist) < days + 1:
            return 0.0
        
        current = hist["Close"].iloc[-1]
        past = hist["Close"].iloc[-days - 1]
        return ((current / past) - 1) * 100


if __name__ == "__main__":
    # Test code
    print("ChatGPT Client for Market Regime Detection")
    print("=" * 50)
    print("Model: GPT-4 Turbo")
    print("Cost: ~$0.03/call = $0.90/month")
    print("Caching: 24 hours")
    print("\nRegimes:")
    for regime, data in MARKET_REGIMES.items():
        print(f"  {regime}: {data['description']}")
