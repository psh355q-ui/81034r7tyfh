import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.skills.trading.risk_skill import RiskSkill
# Assuming there is a way to get the global skill registry or just instantiate directly for internal usage.
# For tighter integration, we can instantiate the skill directly if it's used as a library, 
# or go through the registry if we want to simulate agent behavior. 
# Here, direct instantiation is practical for a Manager component.

logger = logging.getLogger(__name__)

class PortfolioManager:
    """
    Portfolio Manager
    
    Orchestrates portfolio health checks, risk analysis, and rebalancing suggestions.
    Leverages `RiskSkill` for core calculations to maintain architecture consistency.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        self.risk_skill = RiskSkill()
        self.initial_capital_history = initial_capital
        
    async def analyze_portfolio(
        self, 
        current_positions: List[Dict[str, Any]], 
        equity_curve: List[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze portfolio health using RiskSkill.
        
        Args:
            current_positions: List of dicts with keys 'ticker', 'quantity', 'current_price', 'entry_price', 'weight', 'value'
            equity_curve: List of total portfolio values over time
            
        Returns:
            Comprehensive analysis report with warnings and suggestions.
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "status": "Healthy",
            "warnings": [],
            "rebalancing_suggestions": [],
            "metrics": {}
        }
        
        # 1. Calculate Portfolio Risk (VaR, etc.)
        risk_metrics = await self.risk_skill.execute(
            "calculate_portfolio_risk",
            positions=current_positions
        )
        
        if risk_metrics["success"]:
            results["metrics"].update(risk_metrics["risk_metrics"])
            if risk_metrics["recommendation"] == "High Risk":
                results["status"] = "Risk Warning"
                results["warnings"].append("Portfolio Risk is High (VaR)")
        
        # 2. Check Concentration Risk
        correlation_metrics = await self.risk_skill.execute(
            "calculate_correlation_risk",
            positions=current_positions
        )
        
        if correlation_metrics["success"]:
            results["metrics"].update(correlation_metrics["concentration_metrics"])
            if correlation_metrics["violations"]:
                results["status"] = "Imbalanced"
                for v in correlation_metrics["violations"]:
                    results["warnings"].append(f"Concentration Violation: {v['ticker']} ({v['weight']:.1f}%)")
                    
                # Generate Rebalancing Suggestions for Violations
                for v in correlation_metrics["violations"]:
                    excess_weight = v['excess']
                    # Simple suggestion: reduce by excess amount
                    results["rebalancing_suggestions"].append({
                        "action": "SELL",
                        "ticker": v["ticker"],
                        "reason": "Concentration Limit Exceeded",
                        "target_weight_reduction": excess_weight
                    })
            
        # 3. Check Drawdown (if history available)
        if equity_curve and len(equity_curve) > 1:
            drawdown_metrics = await self.risk_skill.execute(
                "calculate_max_drawdown",
                equity_curve=equity_curve
            )
            
            if drawdown_metrics["success"]:
                results["metrics"]["max_drawdown_pct"] = drawdown_metrics["max_drawdown_pct"]
                if drawdown_metrics["is_warning"]:
                    results["warnings"].append(f"Max Drawdown Alert: {drawdown_metrics['current_drawdown_pct']:.2f}%")
                    results["status"] = "Critical"

        return results

    async def suggest_rebalancing(self, current_positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate specific rebalancing orders to optimize the portfolio.
        Currently focused on reducing risk.
        """
        analysis = await self.analyze_portfolio(current_positions)
        return analysis.get("rebalancing_suggestions", [])
