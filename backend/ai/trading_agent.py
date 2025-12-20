"""
AI Trading Agent with Constitution Rules

Phase 4, Task 7 Integration:
- Non-standard risk pre-check (CRITICAL >= 0.6 → HOLD)
- Non-standard risk post-check (HIGH 0.3-0.6 → reduce position 50%)
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from backend.config.settings import settings
from backend.ai.claude_client import ClaudeClient
from backend.data.feature_store.store import FeatureStore
from backend.models.trading_decision import TradingDecision

logger = logging.getLogger(__name__)


class TradingAgent:
    """
    AI Trading Agent with Constitution Rules enforcement.
    
    Decision Flow:
    1. Feature Store → Get features (cached)
    2. Pre-Checks → Constitution filters (volatility, momentum, risks)
    3. Claude AI → Analysis & reasoning
    4. Post-Checks → Conviction thresholds, position sizing
    5. Final Decision → BUY/SELL/HOLD with conviction
    """
    
    def __init__(self):
        self.settings = settings
        self.claude_client = ClaudeClient()
        self.feature_store = FeatureStore()
        
        # Metrics
        self.metrics = {
            "total_analyses": 0,
            "pre_check_filtered": 0,
            "post_check_adjusted": 0,
            "final_buy": 0,
            "final_sell": 0,
            "final_hold": 0,
        }
        
        logger.info("TradingAgent initialized with Constitution Rules")
        logger.info(f"Max volatility: {self.settings.max_volatility_pct}%")
        logger.info(f"Min momentum: {self.settings.min_momentum_pct}%")
        logger.info(f"Conviction thresholds: BUY {self.settings.conviction_threshold_buy}, SELL {self.settings.conviction_threshold_sell}")
        logger.info(f"Non-standard risk: CRITICAL {self.settings.max_non_standard_risk_critical}, HIGH {self.settings.max_non_standard_risk_high}")
    
    async def analyze(
        self,
        ticker: str,
        market_context: Optional[Dict] = None,
        portfolio_context: Optional[Dict] = None,
    ) -> TradingDecision:
        """
        Analyze a stock and make trading decision.
        
        Args:
            ticker: Stock ticker symbol
            market_context: Market regime info (VIX, sector performance, etc.)
            portfolio_context: Current holdings, cash, etc.
        
        Returns:
            TradingDecision with action, conviction, reasoning
        """
        self.metrics["total_analyses"] += 1
        
        try:
            logger.info(f"=== Analyzing {ticker} ===")
            
            # Step 1: Get features from Feature Store (cached)
            features = await self.feature_store.get_features(
                ticker=ticker,
                as_of_date=datetime.now(),
            )
            
            if not features:
                logger.warning(f"No features available for {ticker}")
                return TradingDecision(
                    ticker=ticker,
                    action="HOLD",
                    conviction=0.0,
                    reasoning="No feature data available",
                    risk_factors=["missing_data"],
                    features_used={},
                )
            
            logger.info(f"Features: {features}")
            
            # Step 2: Constitution Pre-Checks
            pre_check_result = self._apply_pre_checks(ticker, features)
            if pre_check_result:
                self.metrics["pre_check_filtered"] += 1
                self.metrics["final_hold"] += 1
                logger.info(f"Pre-check filtered: {pre_check_result.reasoning}")
                return pre_check_result
            
            logger.info("Pre-checks passed ✓")
            
            # Step 3: Get current price for context
            current_price = features.get("current_price")
            
            # Step 4: Claude AI analysis
            ai_result = await self.claude_client.analyze_stock(
                ticker=ticker,
                features=features,
                market_context=market_context,
                portfolio_context=portfolio_context,
            )
            
            # Step 5: Post-checks (Constitution conviction thresholds)
            decision = self._apply_post_checks(
                ticker=ticker,
                ai_result=ai_result,
                features=features,
                current_price=current_price,
            )
            
            logger.info(f"Final decision for {ticker}: {decision}")
            self._update_metrics(decision.action)
            
            return decision
        
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            # Conservative default: HOLD on error
            decision = TradingDecision(
                ticker=ticker,
                action="HOLD",
                conviction=0.0,
                reasoning=f"Analysis failed: {str(e)}",
                risk_factors=["analysis_error"],
                features_used=features,
            )
            self._update_metrics("HOLD")
            return decision
    
    def _apply_pre_checks(
        self, ticker: str, features: dict
    ) -> Optional[TradingDecision]:
        """
        Apply Constitution pre-checks before AI analysis.
        
        Pre-checks (immediate HOLD):
        1. Missing critical features
        2. Extremely high volatility (> 50%)
        3. Extreme negative momentum (< -30%)
        4. Low management credibility (< 0.3)
        5. High supply chain risk (> 0.6)
        6. CRITICAL non-standard risk (>= 0.6)  ← NEW in Task 7
        
        Returns:
            TradingDecision if pre-check triggers, None otherwise
        """
        # Check for missing critical features
        critical_features = ["ret_5d", "vol_20d"]
        missing = [f for f in critical_features if f not in features or features[f] is None]
        
        if missing:
            return TradingDecision(
                ticker=ticker,
                action="HOLD",
                conviction=0.0,
                reasoning=f"Missing critical features: {missing}",
                risk_factors=["missing_data"],
                features_used=features,
            )
        
        # Check for extreme volatility
        vol_20d = features.get("vol_20d", 0.0)
        if vol_20d and vol_20d > (self.settings.max_volatility_pct / 100.0):
            return TradingDecision(
                ticker=ticker,
                action="HOLD",
                conviction=0.0,
                reasoning=f"Extreme volatility detected: {vol_20d:.1%} > {self.settings.max_volatility_pct}%",
                risk_factors=["extreme_volatility"],
                features_used=features,
            )
        
        # Check for extreme negative momentum
        mom_20d = features.get("mom_20d", 0.0)
        if mom_20d and mom_20d < (self.settings.min_momentum_pct / 100.0):
            return TradingDecision(
                ticker=ticker,
                action="HOLD",
                conviction=0.0,
                reasoning=f"Extreme negative momentum: {mom_20d:.1%} < {self.settings.min_momentum_pct}%",
                risk_factors=["extreme_negative_momentum"],
                features_used=features,
            )
        
        # Check management credibility (AI Factor from Task 2)
        mgmt_credibility = features.get("management_credibility", 0.5)
        if mgmt_credibility < self.settings.min_management_credibility:
            return TradingDecision(
                ticker=ticker,
                action="HOLD",
                conviction=0.0,
                reasoning=f"Low management credibility: {mgmt_credibility:.2f} < {self.settings.min_management_credibility}",
                risk_factors=["low_management_credibility"],
                features_used=features,
            )
        
        # Check supply chain risk
        sc_risk = features.get("supply_chain_risk", 0.5)
        if sc_risk > self.settings.min_supply_chain_risk_threshold:
            return TradingDecision(
                ticker=ticker,
                action="HOLD",
                conviction=0.0,
                reasoning=f"High supply chain risk: {sc_risk:.2f} > {self.settings.min_supply_chain_risk_threshold}",
                risk_factors=["high_supply_chain_risk"],
                features_used=features,
            )
        
        # ==================== NEW: Non-Standard Risk Pre-Check ====================
        # CRITICAL risk (>= 0.6) → Immediate HOLD
        non_standard_risk = features.get("non_standard_risk_score", 0.0)
        
        if non_standard_risk >= self.settings.max_non_standard_risk_critical:
            # Get risk categories for detailed reasoning
            risk_categories = features.get("non_standard_risk_categories", {})
            risk_level = features.get("non_standard_risk_level", "CRITICAL")
            
            high_risk_categories = [
                f"{cat.upper()} ({score:.1%})"
                for cat, score in risk_categories.items()
                if score > 0.3
            ]
            
            return TradingDecision(
                ticker=ticker,
                action="HOLD",
                conviction=0.0,
                reasoning=(
                    f"CRITICAL non-standard risk detected: {non_standard_risk:.2f} >= {self.settings.max_non_standard_risk_critical} | "
                    f"Risk level: {risk_level} | High-risk categories: {', '.join(high_risk_categories) if high_risk_categories else 'Multiple'}"
                ),
                risk_factors=[
                    "critical_non_standard_risk",
                    *[f"risk_{cat}" for cat, score in risk_categories.items() if score > 0.3]
                ],
                features_used=features,
            )
        # ==================== END: Non-Standard Risk Pre-Check ====================
        
        # All pre-checks passed
        return None
    
    def _apply_post_checks(
        self,
        ticker: str,
        ai_result: dict,
        features: dict,
        current_price: Optional[float],
    ) -> TradingDecision:
        """
        Apply Constitution post-checks after AI analysis.
        
        Post-checks:
        1. Conviction threshold enforcement
        2. Position sizing based on risk
        3. Stop-loss validation
        4. Max position size enforcement
        5. HIGH non-standard risk (0.3-0.6) → reduce position 50%  ← NEW in Task 7
        
        Returns:
            Final TradingDecision
        """
        action = ai_result["action"]
        conviction = ai_result["conviction"]
        
        # Constitution Rule: Conviction thresholds
        if action == "BUY" and conviction < self.settings.conviction_threshold_buy:
            logger.info(
                f"BUY conviction too low: {conviction:.2f} < "
                f"{self.settings.conviction_threshold_buy}"
            )
            action = "HOLD"
            ai_result["reasoning"] += " (Lowered to HOLD: conviction below threshold)"
        
        elif action == "SELL" and conviction < self.settings.conviction_threshold_sell:
            logger.info(
                f"SELL conviction too low: {conviction:.2f} < "
                f"{self.settings.conviction_threshold_sell}"
            )
            action = "HOLD"
            ai_result["reasoning"] += " (Changed to HOLD: conviction below threshold)"
        
        # Constitution Rule: Max position size
        position_size = ai_result.get("position_size", 0.0)
        if position_size > self.settings.max_position_size_pct:
            logger.warning(
                f"Position size capped: {position_size:.1f}% → "
                f"{self.settings.max_position_size_pct}%"
            )
            position_size = self.settings.max_position_size_pct
        
        # Constitution Rule: Reduce position for medium management credibility
        if self.settings.management_credibility_position_scaling:
            mgmt_credibility = features.get("management_credibility", 0.5)
            
            if 0.3 <= mgmt_credibility < 0.6:  # Medium credibility
                original_size = position_size
                position_size *= 0.7  # 30% reduction
                logger.info(
                    f"Position size reduced due to medium management credibility "
                    f"({mgmt_credibility:.2f}): {original_size:.1f}% → {position_size:.1f}%"
                )
                ai_result["reasoning"] += (
                    f" | Position reduced 30% due to medium management credibility "
                    f"({mgmt_credibility:.2f})"
                )
            
            elif mgmt_credibility >= 0.8:  # Excellent credibility
                # Bonus: increase conviction by 10%
                conviction = min(conviction * 1.1, 1.0)
                logger.info(
                    f"Conviction boosted due to excellent management credibility "
                    f"({mgmt_credibility:.2f})"
                )
        
        # ==================== NEW: Non-Standard Risk Post-Check ====================
        # HIGH risk (0.3-0.6) → Reduce position by 50%
        non_standard_risk = features.get("non_standard_risk_score", 0.0)
        risk_level = features.get("non_standard_risk_level", "LOW")
        
        if (
            self.settings.non_standard_risk_position_scaling
            and self.settings.max_non_standard_risk_high <= non_standard_risk < self.settings.max_non_standard_risk_critical
        ):
            original_size = position_size
            reduction_factor = 1.0 - (self.settings.high_risk_position_reduction_pct / 100.0)
            position_size *= reduction_factor
            
            risk_categories = features.get("non_standard_risk_categories", {})
            high_risk_categories = [
                cat.upper()
                for cat, score in risk_categories.items()
                if score > 0.3
            ]
            
            logger.info(
                f"Position size reduced due to HIGH non-standard risk "
                f"({non_standard_risk:.2f}): {original_size:.1f}% → {position_size:.1f}% "
                f"(Risk level: {risk_level}, Categories: {', '.join(high_risk_categories)})"
            )
            
            ai_result["reasoning"] += (
                f" | Position reduced {self.settings.high_risk_position_reduction_pct:.0f}% due to "
                f"HIGH non-standard risk ({risk_level}, {non_standard_risk:.2f})"
            )
            
            self.metrics["post_check_adjusted"] += 1
        # ==================== END: Non-Standard Risk Post-Check ====================
        
        # Create final decision
        decision = TradingDecision(
            ticker=ticker,
            action=action,
            conviction=conviction,
            reasoning=ai_result["reasoning"],
            risk_factors=ai_result.get("risk_factors", []),
            target_price=ai_result.get("target_price"),
            stop_loss=ai_result.get("stop_loss"),
            position_size=position_size,
            features_used=features,
        )
        
        return decision
    
    def _update_metrics(self, action: str):
        """Update action metrics"""
        if action == "BUY":
            self.metrics["final_buy"] += 1
        elif action == "SELL":
            self.metrics["final_sell"] += 1
        else:
            self.metrics["final_hold"] += 1
    
    def get_metrics(self) -> Dict:
        """Get agent metrics"""
        return {
            "agent_metrics": self.metrics.copy(),
            "claude_metrics": self.claude_client.get_metrics(),
            "feature_store_metrics": self.feature_store.get_metrics(),
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            "total_analyses": 0,
            "pre_check_filtered": 0,
            "post_check_adjusted": 0,
            "final_buy": 0,
            "final_sell": 0,
            "final_hold": 0,
        }
        self.claude_client.reset_metrics()