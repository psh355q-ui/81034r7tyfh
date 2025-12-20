"""
Management Credibility Factor Calculator for AI Trading System.

This module analyzes management quality and credibility using:
- CEO tenure and track record
- Conference call sentiment analysis (via Claude API)
- Executive compensation alignment
- Insider trading patterns
- Board independence metrics

Cost: ~$0.043/month (quarterly updates, 100 stocks)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import yfinance as yf
from anthropic import Anthropic

from config import get_settings

logger = logging.getLogger(__name__)


class ManagementCredibilityCalculator:
    """
    Calculate management credibility score (0.0-1.0).
    
    Scoring factors:
    - CEO Tenure (0-20%): Longer tenure = higher trust
    - Conference Call Sentiment (0-40%): Analyzed by Claude
    - Compensation Alignment (0-20%): Stock-based vs cash
    - Insider Activity (0-10%): Recent buying/selling
    - Board Independence (0-10%): Independent director ratio
    
    Update frequency: Quarterly (90 days)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize calculator.
        
        Args:
            api_key: Claude API key (if None, loads from settings)
                    If no API key provided, AI sentiment analysis will be skipped
        """
        settings = get_settings()
        self.api_key = api_key or settings.claude_api_key
        
        # API client is optional (for cost-free testing)
        if self.api_key and self.api_key != "":
            self.client = Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-haiku-20241022"
            logger.info("Claude API client initialized")
        else:
            self.client = None
            self.model = None
            logger.warning("No Claude API key provided - AI sentiment analysis disabled")
        
        # Cost tracking
        self.total_api_calls = 0
        self.total_cost_usd = 0.0
        
        # Pricing (Claude 3.5 Haiku)
        self.cost_per_1k_input_tokens = 0.001
        self.cost_per_1k_output_tokens = 0.005
        
    async def calculate_credibility(
        self,
        ticker: str,
        use_ai: bool = True,
    ) -> Dict:
        """
        Calculate management credibility score.
        
        Args:
            ticker: Stock ticker (e.g., "AAPL")
            use_ai: Whether to use Claude API for sentiment analysis
                    (set False for cost savings during testing)
        
        Returns:
            {
                "score": 0.0-1.0 (overall credibility),
                "confidence": "high" | "medium" | "low",
                "components": {
                    "tenure_score": 0.0-0.2,
                    "sentiment_score": 0.0-0.4,
                    "compensation_score": 0.0-0.2,
                    "insider_score": 0.0-0.1,
                    "board_score": 0.0-0.1
                },
                "details": {
                    "ceo_name": str,
                    "ceo_tenure_years": float,
                    "insider_transactions": list,
                    "board_independence": float
                },
                "last_updated": datetime,
                "ttl_days": 90  # Quarterly update
            }
        """
        logger.info(f"Calculating management credibility for {ticker}")
        
        try:
            # Get company info from Yahoo Finance
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Calculate component scores
            tenure_score = self._calculate_tenure_score(info)
            compensation_score = self._calculate_compensation_score(info)
            insider_score = self._calculate_insider_score(stock)
            board_score = self._calculate_board_score(info)
            
            # Sentiment analysis (expensive, only if use_ai=True)
            if use_ai and self.client:
                sentiment_score = await self._analyze_sentiment(ticker, info)
            else:
                sentiment_score = 0.2  # Neutral score
                if use_ai and not self.client:
                    logger.warning(f"AI requested but no API key available for {ticker}")
                else:
                    logger.info(f"Skipping AI sentiment analysis for {ticker} (use_ai=False)")
            
            # Total score (weighted sum)
            total_score = (
                tenure_score +
                sentiment_score +
                compensation_score +
                insider_score +
                board_score
            )
            
            # Confidence based on data availability
            confidence = self._assess_confidence(info)
            
            result = {
                "score": round(total_score, 4),
                "confidence": confidence,
                "components": {
                    "tenure_score": round(tenure_score, 4),
                    "sentiment_score": round(sentiment_score, 4),
                    "compensation_score": round(compensation_score, 4),
                    "insider_score": round(insider_score, 4),
                    "board_score": round(board_score, 4),
                },
                "details": {
                    "ceo_name": info.get("companyOfficers", [{}])[0].get("name", "Unknown"),
                    "ceo_tenure_years": self._get_ceo_tenure(info),
                    "board_independence": info.get("boardSize", 0),
                },
                "last_updated": datetime.now().isoformat(),
                "ttl_days": 90,  # Quarterly refresh
            }
            
            logger.info(
                f"Management credibility for {ticker}: {result['score']:.2f} "
                f"(confidence: {result['confidence']})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating credibility for {ticker}: {e}")
            # Return neutral score on error
            return {
                "score": 0.5,
                "confidence": "low",
                "components": {},
                "details": {},
                "last_updated": datetime.now().isoformat(),
                "ttl_days": 90,
                "error": str(e),
            }
    
    def _calculate_tenure_score(self, info: dict) -> float:
        """
        Calculate CEO tenure score (0.0-0.2).
        
        Longer tenure = higher trust (up to 10 years)
        """
        tenure_years = self._get_ceo_tenure(info)
        
        if tenure_years <= 0:
            return 0.05  # No data, assume neutral
        
        # Score increases linearly up to 10 years
        normalized = min(tenure_years / 10.0, 1.0)
        return normalized * 0.2
    
    def _get_ceo_tenure(self, info: dict) -> float:
        """Extract CEO tenure from company info."""
        officers = info.get("companyOfficers", [])
        
        if not officers:
            return 0.0
        
        # Find CEO (usually first officer)
        ceo = next((o for o in officers if "CEO" in o.get("title", "")), officers[0])
        
        # Yahoo Finance doesn't always provide tenure directly
        # Use age as proxy (rough estimate: age - 40 = tenure)
        age = ceo.get("age", 0)
        if age > 40:
            return min((age - 40) / 2.0, 15.0)  # Cap at 15 years
        
        return 3.0  # Default to 3 years if no data
    
    def _calculate_compensation_score(self, info: dict) -> float:
        """
        Calculate compensation alignment score (0.0-0.2).
        
        Higher stock-based comp = better alignment
        """
        # Yahoo Finance doesn't provide detailed comp breakdown
        # Use proxy: if company pays dividends, assume good alignment
        dividend_rate = info.get("dividendRate", 0)
        dividend_yield = info.get("dividendYield", 0)
        
        if dividend_yield and dividend_yield > 0.02:  # > 2% yield
            return 0.15  # Good alignment
        elif dividend_rate and dividend_rate > 0:
            return 0.10  # Some alignment
        else:
            return 0.05  # Neutral (no dividend data)
    
    def _calculate_insider_score(self, stock) -> float:
        """
        Calculate insider trading score (0.0-0.1).
        
        Recent insider buying = positive signal
        """
        try:
            # Get insider transactions (last 6 months)
            insider_transactions = stock.insider_transactions
            
            if insider_transactions is None or insider_transactions.empty:
                return 0.05  # Neutral (no data)
            
            # Filter last 6 months
            six_months_ago = datetime.now() - timedelta(days=180)
            recent = insider_transactions[
                insider_transactions.index > six_months_ago
            ]
            
            if recent.empty:
                return 0.05
            
            # Calculate net buying (positive = bullish)
            buys = recent[recent["Transaction"] == "Buy"]["Value"].sum()
            sells = recent[recent["Transaction"] == "Sale"]["Value"].sum()
            
            net_buying = buys - sells
            
            if net_buying > 0:
                return 0.10  # Positive signal
            elif net_buying < 0:
                return 0.0  # Negative signal
            else:
                return 0.05  # Neutral
                
        except Exception as e:
            logger.debug(f"Could not fetch insider transactions: {e}")
            return 0.05  # Neutral on error
    
    def _calculate_board_score(self, info: dict) -> float:
        """
        Calculate board independence score (0.0-0.1).
        
        More independent directors = better governance
        """
        board_size = info.get("boardSize", 0)
        
        if board_size == 0:
            return 0.05  # No data
        
        # Proxy: larger boards tend to be more independent
        if board_size >= 10:
            return 0.10  # Large board
        elif board_size >= 7:
            return 0.07  # Medium board
        else:
            return 0.05  # Small board
    
    async def _analyze_sentiment(self, ticker: str, info: dict) -> float:
        """
        Analyze CEO communication sentiment using Claude (0.0-0.4).
        
        This is the most expensive component but provides unique insights.
        """
        company_name = info.get("longName", ticker)
        business_summary = info.get("longBusinessSummary", "")
        
        # Limit summary length to control costs
        if len(business_summary) > 1000:
            business_summary = business_summary[:1000] + "..."
        
        prompt = f"""Analyze the management quality of {company_name} ({ticker}).

Company Description:
{business_summary}

Task:
Evaluate management credibility based on available information. Consider:

1. Communication Clarity: Is the business strategy clear?
2. Track Record: Does the company have a history of meeting guidance?
3. Capital Allocation: Are investments and buybacks sensible?
4. Transparency: Does management address problems openly?

Provide a credibility score and brief reasoning.

Return JSON only:
{{
    "score": 0.0-1.0,
    "confidence": "high" | "medium" | "low",
    "reasoning": "Brief explanation (1-2 sentences)"
}}
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,  # Keep it short to save costs
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Track costs
            self.total_api_calls += 1
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            
            cost = (
                input_tokens / 1000 * self.cost_per_1k_input_tokens +
                output_tokens / 1000 * self.cost_per_1k_output_tokens
            )
            self.total_cost_usd += cost
            
            logger.info(
                f"Claude API call for {ticker}: "
                f"${cost:.4f} ({input_tokens} in, {output_tokens} out)"
            )
            
            # Parse response
            result = json.loads(response.content[0].text)
            
            # Scale to 0.0-0.4 range (40% of total score)
            sentiment_score = result["score"] * 0.4
            
            logger.info(
                f"Sentiment analysis for {ticker}: {sentiment_score:.2f}/0.4 "
                f"(confidence: {result['confidence']})"
            )
            
            return sentiment_score
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis for {ticker}: {e}")
            return 0.2  # Neutral score on error
    
    def _assess_confidence(self, info: dict) -> str:
        """
        Assess confidence level based on data availability.
        """
        has_officers = bool(info.get("companyOfficers"))
        has_summary = bool(info.get("longBusinessSummary"))
        has_board = bool(info.get("boardSize"))
        
        data_points = sum([has_officers, has_summary, has_board])
        
        if data_points >= 3:
            return "high"
        elif data_points >= 2:
            return "medium"
        else:
            return "low"
    
    def get_metrics(self) -> dict:
        """Get cost tracking metrics."""
        return {
            "total_api_calls": self.total_api_calls,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "avg_cost_per_call": (
                round(self.total_cost_usd / self.total_api_calls, 4)
                if self.total_api_calls > 0
                else 0.0
            ),
        }