"""
Gemini 1.5 Flash API Client for Non-Standard Risk Screening

Purpose: Fast, cheap risk screening before expensive Claude analysis
Cost: $0.0003 per stock (~$0.90/month for 100 stocks/day)
Speed: < 0.5s per stock
Role: Filter 100 stocks → 50 stocks (remove high-risk stocks)

Phase: 5 (Strategy Ensemble)
Task: 1 (Gemini Integration)
"""

import json
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("google-generativeai not installed. Install with: pip install google-generativeai")

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Gemini 1.5 Flash client for non-standard risk screening.
    
    Use Cases:
    1. Analyze news headlines for risk signals
    2. Screen legal/regulatory/management events
    3. Fast pre-filter before Claude analysis
    
    Risk Categories:
    - Legal: Lawsuits, investigations, settlements
    - Regulatory: FDA/SEC/FTC actions, compliance issues
    - Management: CEO/CFO changes, scandals, resignations
    - Operational: Product recalls, service outages, supply chain
    - Social: Extreme negative sentiment, boycotts
    
    Output:
    - risk_score: 0.0 (safe) to 1.0 (critical)
    - risk_level: LOW | MODERATE | HIGH | CRITICAL
    - categories: Breakdown by risk type
    """
    
    def __init__(self):
        """
        Initialize Gemini client.
        
        Requires:
            GEMINI_API_KEY environment variable
        
        Model:
            gemini-1.5-flash (fastest, cheapest)
        """
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-generativeai not installed. "
                "Install with: pip install google-generativeai"
            )
        
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=self.api_key)
        
        # Get model from environment, default to gemini-2.5-flash
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.model = genai.GenerativeModel(model_name)
        
        # Cost tracking
        self.metrics = {
            "total_requests": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
            "cache_hits": 0,
        }
        
        # Pricing (as of 2024-11)
        self.cost_per_request = 0.0003  # $0.0003 per analysis
        
        logger.info(f"GeminiClient initialized with model: {model_name}")
    
    async def screen_risk(
        self,
        ticker: str,
        news_headlines: List[str],
        recent_events: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Screen non-standard risk for a stock.
        
        Args:
            ticker: Stock ticker symbol
            news_headlines: List of recent news headlines (max 10)
            recent_events: Optional list of recent events
                           Format: [{"type": str, "description": str, "date": str}, ...]
        
        Returns:
            {
                "ticker": str,
                "risk_score": float (0.0-1.0),
                "risk_level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
                "categories": {
                    "legal": float (0.0-1.0),
                    "regulatory": float (0.0-1.0),
                    "management": float (0.0-1.0),
                    "operational": float (0.0-1.0),
                    "social": float (0.0-1.0)
                },
                "reasoning": str,
                "timestamp": str
            }
        
        Risk Levels:
        - LOW (0.0-0.3): Safe for trading
        - MODERATE (0.3-0.6): Monitor closely
        - HIGH (0.6-0.8): Reduce position size
        - CRITICAL (0.8-1.0): Avoid trading
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Screening risk for {ticker} with Gemini Flash")
            
            # Build prompt
            prompt = self._build_prompt(ticker, news_headlines, recent_events)
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            
            # Parse response
            result = self._parse_response(response.text, ticker)
            
            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update metrics
            self.metrics["total_requests"] += 1
            self.metrics["total_cost_usd"] += self.cost_per_request
            self.metrics["avg_latency_ms"] = (
                (self.metrics["avg_latency_ms"] * (self.metrics["total_requests"] - 1) + latency_ms)
                / self.metrics["total_requests"]
            )
            
            logger.info(
                f"Gemini screening for {ticker}: "
                f"risk_level={result['risk_level']}, "
                f"score={result['risk_score']:.2f}, "
                f"latency={latency_ms:.0f}ms, "
                f"cost=${self.cost_per_request:.4f}"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error screening {ticker} with Gemini: {e}")
            
            # Return conservative default on error
            return {
                "ticker": ticker,
                "risk_score": 0.5,  # Medium risk
                "risk_level": "MODERATE",
                "categories": {
                    "legal": 0.5,
                    "regulatory": 0.5,
                    "management": 0.5,
                    "operational": 0.5,
                    "social": 0.5,
                },
                "reasoning": f"Error during analysis: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }
    
    def _build_prompt(
        self,
        ticker: str,
        news_headlines: List[str],
        recent_events: Optional[List[Dict]] = None,
    ) -> str:
        """
        Build Gemini prompt for risk screening.
        
        Prompt Engineering:
        - Clear role definition (risk analyst)
        - Specific categories to check
        - JSON output format requirement
        - Examples for calibration
        """
        # Limit news to top 10 most recent
        headlines = news_headlines[:10] if news_headlines else []
        
        # Format events
        events = recent_events or []
        events_text = ""
        if events:
            events_text = "\n".join(
                f"- {e['type']}: {e['description']} ({e.get('date', 'recent')})"
                for e in events[:5]
            )
        else:
            events_text = "No recent events provided"
        
        prompt = f"""You are a risk analyst screening stocks for non-standard risks.

Analyze {ticker} for the following risk categories:

**Recent News Headlines:**
{chr(10).join(f"- {h}" for h in headlines) if headlines else "No recent news provided"}

**Recent Events:**
{events_text}

**Risk Categories to Evaluate:**

1. **Legal Risk** (0.0-1.0)
   - Lawsuits (class action, patent, antitrust)
   - Legal investigations
   - Settlements or fines

2. **Regulatory Risk** (0.0-1.0)
   - FDA/SEC/FTC/DOJ actions
   - Compliance violations
   - License suspensions or warnings

3. **Management Risk** (0.0-1.0)
   - CEO/CFO sudden departures
   - Executive scandals or misconduct
   - Board conflicts or proxy fights

4. **Operational Risk** (0.0-1.0)
   - Product recalls or safety issues
   - Service outages or quality problems
   - Supply chain major disruptions

5. **Social Risk** (0.0-1.0)
   - Extreme negative sentiment crashes
   - Consumer boycotts
   - Major PR disasters

**Scoring Guide:**
- 0.0-0.2: No significant risk
- 0.2-0.4: Minor concerns
- 0.4-0.6: Moderate risk
- 0.6-0.8: High risk
- 0.8-1.0: Critical risk

**Overall Risk Level:**
- LOW (0.0-0.3): Safe for normal trading
- MODERATE (0.3-0.6): Monitor closely, proceed with caution
- HIGH (0.6-0.8): Reduce position size significantly
- CRITICAL (0.8-1.0): Avoid trading

Respond with ONLY a valid JSON object (no markdown, no explanation):

{{
  "risk_score": 0.0-1.0,
  "risk_level": "LOW"|"MODERATE"|"HIGH"|"CRITICAL",
  "categories": {{
    "legal": 0.0-1.0,
    "regulatory": 0.0-1.0,
    "management": 0.0-1.0,
    "operational": 0.0-1.0,
    "social": 0.0-1.0
  }},
  "reasoning": "Brief explanation (1-2 sentences max)"
}}
"""
        
        return prompt
    
    def _parse_response(self, response_text: str, ticker: str) -> Dict:
        """
        Parse Gemini response into structured format.
        
        Handles:
        - Markdown code blocks (```json)
        - Extra whitespace
        - Missing fields (use defaults)
        """
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            # Parse JSON
            data = json.loads(text)
            
            # Validate required fields
            risk_score = data.get("risk_score", 0.5)
            risk_level = data.get("risk_level", "MODERATE")
            categories = data.get("categories", {})
            reasoning = data.get("reasoning", "No reasoning provided")
            
            # Ensure all categories present
            default_categories = {
                "legal": 0.0,
                "regulatory": 0.0,
                "management": 0.0,
                "operational": 0.0,
                "social": 0.0,
            }
            default_categories.update(categories)
            
            # Validate risk_level
            if risk_level not in ["LOW", "MODERATE", "HIGH", "CRITICAL"]:
                # Infer from risk_score
                if risk_score < 0.3:
                    risk_level = "LOW"
                elif risk_score < 0.6:
                    risk_level = "MODERATE"
                elif risk_score < 0.8:
                    risk_level = "HIGH"
                else:
                    risk_level = "CRITICAL"
            
            return {
                "ticker": ticker,
                "risk_score": float(risk_score),
                "risk_level": risk_level,
                "categories": default_categories,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat(),
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            logger.debug(f"Response text: {response_text}")
            
            # Return conservative default
            return {
                "ticker": ticker,
                "risk_score": 0.5,
                "risk_level": "MODERATE",
                "categories": {
                    "legal": 0.5,
                    "regulatory": 0.5,
                    "management": 0.5,
                    "operational": 0.5,
                    "social": 0.5,
                },
                "reasoning": "Failed to parse Gemini response",
                "timestamp": datetime.now().isoformat(),
            }
    
    def get_metrics(self) -> Dict:
        """
        Get Gemini client metrics.
        
        Returns:
            {
                "total_requests": int,
                "total_cost_usd": float,
                "avg_latency_ms": float,
                "cache_hits": int,
                "cost_per_request": float,
                "monthly_cost_projection": float  # Based on current usage
            }
        """
        return {
            **self.metrics,
            "cost_per_request": self.cost_per_request,
            "monthly_cost_projection": self.metrics["total_cost_usd"] * 30  # Rough estimate
        }
    
    def reset_metrics(self):
        """Reset cost tracking metrics"""
        self.metrics = {
            "total_requests": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0.0,
            "cache_hits": 0,
        }

    async def diagnose_rss_feed_error(
        self,
        feed_url: str,
        feed_name: str,
        error_message: str,
    ) -> Dict:
        """
        Analyze RSS feed error and suggest fixes.

        Args:
            feed_url: The RSS feed URL that failed
            feed_name: Name of the feed (e.g., "Bloomberg")
            error_message: The error message received

        Returns:
            {
                "feed_url": str,
                "feed_name": str,
                "diagnosis": str,
                "likely_cause": str,
                "suggested_fix": str,
                "alternative_urls": List[str],
                "should_disable": bool,
                "timestamp": str
            }
        """
        start_time = datetime.now()

        try:
            logger.info(f"Diagnosing RSS feed error for {feed_name}: {feed_url}")

            # Build prompt for RSS error diagnosis
            prompt = self._build_rss_diagnosis_prompt(feed_url, feed_name, error_message)

            # Call Gemini API
            response = self.model.generate_content(prompt)

            # Parse response
            result = self._parse_rss_diagnosis_response(response.text, feed_url, feed_name)

            # Calculate latency
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Update metrics
            self.metrics["total_requests"] += 1
            self.metrics["total_cost_usd"] += self.cost_per_request
            self.metrics["avg_latency_ms"] = (
                (self.metrics["avg_latency_ms"] * (self.metrics["total_requests"] - 1) + latency_ms)
                / self.metrics["total_requests"]
            )

            logger.info(
                f"Gemini RSS diagnosis for {feed_name}: "
                f"cause={result['likely_cause']}, "
                f"latency={latency_ms:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Error diagnosing RSS feed {feed_name} with Gemini: {e}")

            return {
                "feed_url": feed_url,
                "feed_name": feed_name,
                "diagnosis": f"Failed to analyze: {str(e)}",
                "likely_cause": "Unknown",
                "suggested_fix": "Unable to provide suggestions due to analysis error",
                "alternative_urls": [],
                "should_disable": False,
                "timestamp": datetime.now().isoformat(),
            }

    def _build_rss_diagnosis_prompt(
        self,
        feed_url: str,
        feed_name: str,
        error_message: str,
    ) -> str:
        """
        Build Gemini prompt for RSS feed error diagnosis.
        """
        prompt = f"""You are an expert RSS feed troubleshooter and web scraping specialist.

Analyze this RSS feed error and provide actionable fix suggestions:

**Feed Information:**
- Feed Name: {feed_name}
- Feed URL: {feed_url}
- Error Message: {error_message}

**Your Task:**
1. Diagnose the likely cause of the error
2. Suggest specific fixes (e.g., URL corrections, format changes)
3. Provide alternative RSS feed URLs if available
4. Determine if the feed should be temporarily disabled

**Common RSS Feed Issues:**
- Invalid or moved URLs (404, 301 redirects)
- Authentication/access requirements
- Rate limiting or bot detection
- Malformed XML/RSS format
- SSL/TLS certificate issues
- Network connectivity problems
- Feed service permanently discontinued

**For {feed_name}, consider:**
- Official website structure changes
- Known RSS feed endpoints for this publisher
- Alternative feed URLs (e.g., different sections, APIs)

Respond with ONLY a valid JSON object (no markdown, no explanation):

{{
  "diagnosis": "Brief technical diagnosis of what went wrong",
  "likely_cause": "MOVED_URL"|"AUTHENTICATION"|"RATE_LIMIT"|"MALFORMED"|"SSL_ERROR"|"NETWORK_ERROR"|"DISCONTINUED"|"UNKNOWN",
  "suggested_fix": "Specific actionable fix (e.g., 'Update URL to https://...' or 'Add authentication headers' or 'Reduce crawl frequency')",
  "alternative_urls": ["https://alternative1.com/rss", "https://alternative2.com/feed"],
  "should_disable": true|false
}}

**Guidelines:**
- For MOVED_URL: Suggest the correct new URL
- For AUTHENTICATION: Explain auth requirements
- For RATE_LIMIT: Suggest reducing frequency
- For DISCONTINUED: Recommend disabling feed
- Provide 1-3 alternative URLs if you know them for this publisher
- Set should_disable=true only if feed is permanently unavailable
"""

        return prompt

    def _parse_rss_diagnosis_response(self, response_text: str, feed_url: str, feed_name: str) -> Dict:
        """
        Parse Gemini RSS diagnosis response into structured format.
        """
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Parse JSON
            data = json.loads(text)

            # Validate required fields
            diagnosis = data.get("diagnosis", "Unable to diagnose")
            likely_cause = data.get("likely_cause", "UNKNOWN")
            suggested_fix = data.get("suggested_fix", "No suggestions available")
            alternative_urls = data.get("alternative_urls", [])
            should_disable = data.get("should_disable", False)

            # Ensure alternative_urls is a list
            if not isinstance(alternative_urls, list):
                alternative_urls = []

            return {
                "feed_url": feed_url,
                "feed_name": feed_name,
                "diagnosis": diagnosis,
                "likely_cause": likely_cause,
                "suggested_fix": suggested_fix,
                "alternative_urls": alternative_urls,
                "should_disable": bool(should_disable),
                "timestamp": datetime.now().isoformat(),
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini RSS diagnosis response: {e}")
            logger.debug(f"Response text: {response_text}")

            # Return basic error info
            return {
                "feed_url": feed_url,
                "feed_name": feed_name,
                "diagnosis": "Failed to parse AI response",
                "likely_cause": "UNKNOWN",
                "suggested_fix": "Unable to provide suggestions",
                "alternative_urls": [],
                "should_disable": False,
                "timestamp": datetime.now().isoformat(),
            }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_gemini_client():
        """Test Gemini client with sample data"""
        
        # Initialize client
        client = GeminiClient()
        
        # Sample data
        ticker = "TSLA"
        news = [
            "Tesla recalls 2 million vehicles over Autopilot safety concerns",
            "Elon Musk faces SEC investigation over Twitter acquisition",
            "Tesla factory workers report safety violations",
            "Tesla stock drops 15% on weak earnings guidance",
        ]
        events = [
            {
                "type": "REGULATORY",
                "description": "NHTSA opens investigation into Autopilot crashes",
                "date": "2024-11-01"
            },
            {
                "type": "LEGAL",
                "description": "Class action lawsuit filed over range estimates",
                "date": "2024-10-25"
            }
        ]
        
        # Screen risk
        result = await client.screen_risk(ticker, news, events)
        
        print("\n" + "="*60)
        print(f"Gemini Risk Screening: {ticker}")
        print("="*60)
        print(f"Risk Score: {result['risk_score']:.2f}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"\nCategories:")
        for cat, score in result['categories'].items():
            print(f"  - {cat.upper()}: {score:.2f}")
        print(f"\nReasoning: {result['reasoning']}")
        print(f"\nMetrics:")
        metrics = client.get_metrics()
        print(f"  - Total requests: {metrics['total_requests']}")
        print(f"  - Total cost: ${metrics['total_cost_usd']:.4f}")
        print(f"  - Avg latency: {metrics['avg_latency_ms']:.0f}ms")
        print("="*60 + "\n")
    
    # Run test
    asyncio.run(test_gemini_client())