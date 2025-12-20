"""
Non-Standard Risk Calculator - Dual Mode (A/B Testing)

Supports two modes:
- V1: Rule-based (Phase 4 original, $0 cost)
- V2: Gemini-based (Phase 5 new, $0.0003 cost)

Purpose: Compare accuracy and decide which to use in production

Phase: 5 (Strategy Ensemble)
Task: 2 (Risk Migration)
"""

import logging
import sys
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RiskMode(Enum):
    """Risk calculation mode"""
    RULE_BASED = "rule_based"  # V1: Original (Phase 4)
    GEMINI = "gemini"           # V2: New (Phase 5)
    DUAL = "dual"               # A/B testing mode


class NonStandardRiskCalculator:
    """
    Non-standard risk calculator with dual mode support.
    
    Modes:
    1. RULE_BASED: Original keyword matching (free)
    2. GEMINI: AI-powered semantic analysis ($0.0003/stock)
    3. DUAL: Run both in parallel for A/B testing
    
    A/B Testing Flow:
    1. Run both V1 and V2 in parallel
    2. Log results for comparison
    3. Use V1 result (conservative, keep existing behavior)
    4. After 1 week, analyze metrics and decide
    """
    
    def __init__(self, mode: RiskMode = RiskMode.DUAL):
        """
        Initialize calculator.
        
        Args:
            mode: Calculation mode (RULE_BASED, GEMINI, or DUAL)
        """
        self.mode = mode
        
        # Lazy import Gemini (only if needed)
        self.gemini_client = None
        if mode in [RiskMode.GEMINI, RiskMode.DUAL]:
            try:
                from ai.gemini_client import GeminiClient
                self.gemini_client = GeminiClient()
                logger.info("Gemini client initialized for risk screening")
            except ImportError:
                logger.warning("Gemini client not available, falling back to rule-based")
                self.mode = RiskMode.RULE_BASED
        
        # A/B testing metrics
        self.ab_metrics = {
            "total_comparisons": 0,
            "agreement_count": 0,  # Both agree on risk level
            "v1_higher": 0,        # V1 scores higher than V2
            "v2_higher": 0,        # V2 scores higher than V1
            "avg_difference": 0.0, # Average score difference
        }
        
        logger.info(f"NonStandardRiskCalculator initialized in {mode.value} mode")
    
    async def calculate(
        self,
        ticker: str,
        news_headlines: List[str],
        recent_events: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Calculate non-standard risk score.
        
        Returns:
            {
                "ticker": str,
                "risk_score": float (0.0-1.0),
                "risk_level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
                "categories": {...},
                "reasoning": str,
                "mode": str,
                "v1_result": Dict (if DUAL mode),
                "v2_result": Dict (if DUAL mode),
                "agreement": bool (if DUAL mode),
            }
        """
        if self.mode == RiskMode.RULE_BASED:
            return self._calculate_v1(ticker, news_headlines)
        
        elif self.mode == RiskMode.GEMINI:
            return await self._calculate_v2(ticker, news_headlines, recent_events)
        
        elif self.mode == RiskMode.DUAL:
            return await self._calculate_dual(ticker, news_headlines, recent_events)
    
    def _calculate_v1(self, ticker: str, news_headlines: List[str]) -> Dict:
        """
        V1: Rule-based calculation (Phase 4 original).
        
        Method: Keyword matching for 6 risk categories
        Cost: $0
        Speed: < 1ms
        
        Returns: Risk dict with rule-based results
        """
        categories = {
            "legal": self._calculate_legal_risk(news_headlines),
            "regulatory": self._calculate_regulatory_risk(news_headlines),
            "operational": self._calculate_operational_risk(news_headlines),
            "labor": self._calculate_labor_risk(news_headlines),
            "governance": self._calculate_governance_risk(news_headlines),
            "reputation": self._calculate_reputation_risk(news_headlines),
        }
        
        # Weighted average (from Phase 4 Task 1)
        weights = {
            "legal": 0.15,
            "regulatory": 0.25,
            "operational": 0.20,
            "labor": 0.10,
            "governance": 0.25,
            "reputation": 0.05,
        }
        
        risk_score = sum(categories[cat] * weights[cat] for cat in categories)
        
        # Determine risk level
        if risk_score < 0.1:
            risk_level = "LOW"
        elif risk_score < 0.3:
            risk_level = "MODERATE"
        elif risk_score < 0.6:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
        
        return {
            "ticker": ticker,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "categories": categories,
            "reasoning": f"Rule-based analysis: {len(news_headlines)} headlines analyzed",
            "mode": "rule_based",
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _calculate_v2(
        self,
        ticker: str,
        news_headlines: List[str],
        recent_events: Optional[List[Dict]],
    ) -> Dict:
        """
        V2: Gemini-based calculation (Phase 5 new).
        
        Method: Semantic analysis with Gemini 1.5 Flash
        Cost: $0.0003
        Speed: ~500ms
        
        Returns: Risk dict with Gemini results
        """
        if not self.gemini_client:
            logger.warning("Gemini client not available, falling back to V1")
            return self._calculate_v1(ticker, news_headlines)
        
        result = await self.gemini_client.screen_risk(
            ticker=ticker,
            news_headlines=news_headlines,
            recent_events=recent_events or []
        )
        
        # Add mode info
        result["mode"] = "gemini"
        
        return result
    
    async def _calculate_dual(
        self,
        ticker: str,
        news_headlines: List[str],
        recent_events: Optional[List[Dict]],
    ) -> Dict:
        """
        DUAL: Run both V1 and V2, compare results.
        
        A/B Testing Mode:
        1. Calculate V1 (rule-based)
        2. Calculate V2 (Gemini)
        3. Log comparison metrics
        4. Return V1 result (conservative, keep existing behavior)
        
        Returns: V1 result with V2 comparison data attached
        """
        # Calculate V1
        v1_result = self._calculate_v1(ticker, news_headlines)
        
        # Calculate V2
        v2_result = await self._calculate_v2(ticker, news_headlines, recent_events)
        
        # Compare results
        v1_score = v1_result["risk_score"]
        v2_score = v2_result["risk_score"]
        v1_level = v1_result["risk_level"]
        v2_level = v2_result["risk_level"]
        
        agreement = v1_level == v2_level
        difference = abs(v1_score - v2_score)
        
        # Update A/B metrics
        self.ab_metrics["total_comparisons"] += 1
        if agreement:
            self.ab_metrics["agreement_count"] += 1
        if v1_score > v2_score:
            self.ab_metrics["v1_higher"] += 1
        elif v2_score > v1_score:
            self.ab_metrics["v2_higher"] += 1
        
        # Update average difference
        total = self.ab_metrics["total_comparisons"]
        self.ab_metrics["avg_difference"] = (
            (self.ab_metrics["avg_difference"] * (total - 1) + difference) / total
        )
        
        # Log comparison
        logger.info(
            f"A/B Test {ticker}: "
            f"V1={v1_level}({v1_score:.2f}) vs V2={v2_level}({v2_score:.2f}) | "
            f"Agreement: {agreement}, Diff: {difference:.2f}"
        )
        
        # Return V1 result with comparison data
        return {
            **v1_result,
            "mode": "dual",
            "v1_result": v1_result,
            "v2_result": v2_result,
            "agreement": agreement,
            "score_difference": difference,
            "v2_reasoning": v2_result.get("reasoning", ""),
        }
    
    # ==================== V1: Rule-based Category Calculators ====================
    
    def _calculate_legal_risk(self, news: List[str]) -> float:
        """Legal risk: lawsuits, investigations, settlements"""
        keywords = {
            "critical": ["class action", "criminal charges", "indictment", "convicted"],
            "high": ["lawsuit", "litigation", "sued", "legal action", "settlement"],
            "moderate": ["investigation", "probe", "inquiry", "subpoena"],
        }
        return self._keyword_score(news, keywords)
    
    def _calculate_regulatory_risk(self, news: List[str]) -> float:
        """Regulatory risk: FDA, SEC, FTC actions"""
        keywords = {
            "critical": ["license suspended", "banned", "emergency order"],
            "high": ["fda rejection", "sec charges", "ftc action", "violation"],
            "moderate": ["warning letter", "inspection", "review", "compliance"],
        }
        return self._keyword_score(news, keywords)
    
    def _calculate_operational_risk(self, news: List[str]) -> float:
        """Operational risk: recalls, outages, quality issues"""
        keywords = {
            "critical": ["massive recall", "catastrophic failure", "emergency shutdown"],
            "high": ["recall", "defect", "malfunction", "outage", "breach"],
            "moderate": ["quality issue", "delay", "disruption", "problem"],
        }
        return self._keyword_score(news, keywords)
    
    def _calculate_labor_risk(self, news: List[str]) -> float:
        """Labor risk: strikes, unionization, workforce issues"""
        keywords = {
            "critical": ["strike", "walkout", "labor action"],
            "high": ["union", "organize", "protest", "workplace"],
            "moderate": ["dispute", "negotiation", "complaint"],
        }
        return self._keyword_score(news, keywords)
    
    def _calculate_governance_risk(self, news: List[str]) -> float:
        """Governance risk: executive changes, scandals"""
        keywords = {
            "critical": ["ceo fired", "cfo arrested", "scandal", "fraud"],
            "high": ["ceo resigns", "cfo departs", "executive leaves", "board conflict"],
            "moderate": ["management change", "resignation", "departure"],
        }
        return self._keyword_score(news, keywords)
    
    def _calculate_reputation_risk(self, news: List[str]) -> float:
        """Reputation risk: PR disasters, boycotts"""
        keywords = {
            "critical": ["boycott", "pr disaster", "massive backlash"],
            "high": ["controversy", "backlash", "outrage", "criticism"],
            "moderate": ["concern", "question", "doubt"],
        }
        return self._keyword_score(news, keywords)
    
    def _keyword_score(self, news: List[str], keywords: Dict[str, List[str]]) -> float:
        """
        Calculate score based on keyword matches.
        
        Scoring:
        - Critical keyword: 1.0
        - High keyword: 0.6
        - Moderate keyword: 0.3
        
        Returns: 0.0-1.0
        """
        if not news:
            return 0.0
        
        news_lower = [n.lower() for n in news]
        score = 0.0
        
        for headline in news_lower:
            # Critical keywords
            if any(kw in headline for kw in keywords.get("critical", [])):
                score = max(score, 1.0)
            # High keywords
            elif any(kw in headline for kw in keywords.get("high", [])):
                score = max(score, 0.6)
            # Moderate keywords
            elif any(kw in headline for kw in keywords.get("moderate", [])):
                score = max(score, 0.3)
        
        return min(score, 1.0)
    
    # ==================== A/B Testing Metrics ====================
    
    def get_ab_metrics(self) -> Dict:
        """
        Get A/B testing metrics.
        
        Returns:
            {
                "total_comparisons": int,
                "agreement_rate": float (0-1),
                "v1_higher_rate": float,
                "v2_higher_rate": float,
                "avg_difference": float,
                "recommendation": str
            }
        """
        total = self.ab_metrics["total_comparisons"]
        
        if total == 0:
            return {
                **self.ab_metrics,
                "agreement_rate": 0.0,
                "v1_higher_rate": 0.0,
                "v2_higher_rate": 0.0,
                "recommendation": "No data yet"
            }
        
        agreement_rate = self.ab_metrics["agreement_count"] / total
        v1_higher_rate = self.ab_metrics["v1_higher"] / total
        v2_higher_rate = self.ab_metrics["v2_higher"] / total
        
        # Decision logic
        if agreement_rate > 0.8:
            recommendation = "High agreement - both methods work well"
        elif v2_higher_rate > 0.6 and self.ab_metrics["avg_difference"] > 0.2:
            recommendation = "V2 (Gemini) detects more risks - consider switching"
        elif v1_higher_rate > 0.6 and self.ab_metrics["avg_difference"] > 0.2:
            recommendation = "V1 (Rule-based) more conservative - keep current"
        else:
            recommendation = "Need more data to decide"
        
        return {
            **self.ab_metrics,
            "agreement_rate": agreement_rate,
            "v1_higher_rate": v1_higher_rate,
            "v2_higher_rate": v2_higher_rate,
            "recommendation": recommendation,
        }
    
    def reset_ab_metrics(self):
        """Reset A/B testing metrics"""
        self.ab_metrics = {
            "total_comparisons": 0,
            "agreement_count": 0,
            "v1_higher": 0,
            "v2_higher": 0,
            "avg_difference": 0.0,
        }


# Example usage
if __name__ == "__main__":
    import asyncio

# Handle UTF-8 encoding on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    
    async def test_dual_mode():
        """Test dual mode A/B testing"""
        
        # Initialize calculator in DUAL mode
        calculator = NonStandardRiskCalculator(mode=RiskMode.DUAL)
        
        # Test data
        test_cases = [
            {
                "ticker": "AAPL",
                "news": [
                    "Apple reports strong Q4 earnings",
                    "iPhone 16 sales exceed expectations",
                ],
            },
            {
                "ticker": "TSLA",
                "news": [
                    "Tesla recalls 2 million vehicles",
                    "Elon Musk faces SEC investigation",
                    "NHTSA opens Autopilot probe",
                ],
            },
            {
                "ticker": "BA",
                "news": [
                    "Boeing 737 Max grounded again",
                    "FAA emergency order issued",
                    "Class action lawsuit filed",
                ],
            },
        ]
        
        print("\n" + "="*60)
        print("A/B Testing: Rule-based (V1) vs Gemini (V2)")
        print("="*60 + "\n")
        
        for case in test_cases:
            result = await calculator.calculate(
                ticker=case["ticker"],
                news_headlines=case["news"],
            )
            
            print(f"Ticker: {result['ticker']}")
            print(f"V1 (Rule): {result['v1_result']['risk_level']} ({result['v1_result']['risk_score']:.2f})")
            print(f"V2 (Gemini): {result['v2_result']['risk_level']} ({result['v2_result']['risk_score']:.2f})")
            print(f"Agreement: {'✅' if result['agreement'] else '❌'}")
            print(f"Difference: {result['score_difference']:.2f}")
            print()
        
        # Show A/B metrics
        metrics = calculator.get_ab_metrics()
        print("="*60)
        print("A/B Testing Metrics")
        print("="*60)
        print(f"Total comparisons: {metrics['total_comparisons']}")
        print(f"Agreement rate: {metrics['agreement_rate']:.1%}")
        print(f"V1 higher rate: {metrics['v1_higher_rate']:.1%}")
        print(f"V2 higher rate: {metrics['v2_higher_rate']:.1%}")
        print(f"Avg difference: {metrics['avg_difference']:.2f}")
        print(f"\n📊 Recommendation: {metrics['recommendation']}")
        print("="*60 + "\n")
    
