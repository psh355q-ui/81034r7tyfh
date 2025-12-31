"""
ChipWarAgent Helper Methods - Self-Learning Functions

Extends ChipWarAgent with self-learning capabilities:
- Scenario mapping
- V2 analysis vote generation
- Learning schedule management

Author: AI Trading System
Date: 2025-12-23
Phase: 24.5 (Self-Learning)
"""

import logging
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ChipWarAgentHelpers:
    """Helper methods for ChipWarAgent self-learning"""

    @staticmethod
    def map_scenario_to_analysis(scenario: Dict, ticker: str) -> str:
        """
        Map future scenario to analysis scenario type

        Args:
            scenario: Future scenario dict from intelligence engine
            ticker: Stock ticker being analyzed

        Returns:
            "best", "base", or "worst" for ChipComparator
        """
        scenario_name = scenario.get("name", "").lower()
        probability = scenario.get("probability", 0.5)

        # High probability scenarios (>60%) become base case
        if probability > 0.60:
            return "base"

        # Analyze impact on ticker
        if ticker == "NVDA":
            # Nvidia perspective
            impact = scenario.get("impact_on_nvidia", "neutral")
            if impact == "positive":
                return "worst"  # Good for Nvidia = worst case for Google
            elif impact == "negative":
                return "best"  # Bad for Nvidia = best case for Google
            else:
                return "base"

        elif ticker in ["GOOGL", "GOOG"]:
            # Google perspective
            impact = scenario.get("impact_on_google", "neutral")
            if impact == "positive":
                return "best"
            elif impact == "negative":
                return "worst"
            else:
                return "base"

        else:
            return "base"

    @staticmethod
    def generate_vote_from_v2_analysis(
        ticker: str,
        comparison: Dict,
        chip_war_factors: Dict
    ) -> Dict[str, Any]:
        """
        Generate vote from V2 ChipComparator analysis

        Args:
            ticker: Stock ticker
            comparison: Result from ChipComparator.compare_comprehensive()
            chip_war_factors: Extracted factors

        Returns:
            Vote dict
        """
        verdict = comparison["analysis"]["verdict"]
        disruption_score = comparison["analysis"]["disruption_score"]
        confidence_base = comparison["analysis"]["confidence"]

        # Adjust confidence based on rumor activity
        active_rumors = chip_war_factors.get("active_rumors", 0)
        scenario_prob = chip_war_factors.get("scenario_probability", 0)

        # More rumors/higher scenario probability = higher confidence
        confidence_boost = min(0.15, (active_rumors * 0.03) + (scenario_prob * 0.10))
        confidence = min(0.95, confidence_base + confidence_boost)

        # Get investment signals for this ticker
        signals = comparison.get("investment_signals", [])
        matching_signal = next((s for s in signals if s["ticker"] == ticker), None)

        if matching_signal:
            action = matching_signal["action"]
            reasoning = matching_signal["reasoning"]

            # Enhance reasoning with rumor/scenario info
            if active_rumors > 0:
                reasoning += f" | {active_rumors} high-credibility rumors active"
            if scenario_prob > 0.30:
                reasoning += f" | Scenario probability: {scenario_prob:.0%}"

        else:
            # No specific signal, derive from verdict
            if ticker == "NVDA":
                action = "SELL" if verdict == "THREAT" else "BUY" if verdict == "SAFE" else "HOLD"
            else:  # GOOGL
                action = "BUY" if verdict == "THREAT" else "SELL" if verdict == "SAFE" else "HOLD"

            reasoning = f"Chip war verdict: {verdict} (disruption: {disruption_score:.0f})"

        return {
            "agent": "chip_war",
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "chip_war_factors": chip_war_factors
        }

    @staticmethod
    async def schedule_learning_check(
        ticker: str,
        vote: Dict,
        delay_hours: int = 24
    ):
        """
        Schedule learning check after market has reacted

        Args:
            ticker: Stock ticker
            vote: ChipWarAgent's vote
            delay_hours: How long to wait before checking (default 24h)
        """
        # Wait for market reaction period
        await asyncio.sleep(delay_hours * 3600)

        try:
            # Import here to avoid circular dependency
            from backend.ai.economics.chip_intelligence_engine import ChipIntelligenceOrchestrator

            orchestrator = ChipIntelligenceOrchestrator()

            # TODO: Fetch actual market reaction from price API
            # For now, log that learning check is needed
            logger.info(
                f"🧠 Learning check scheduled for {ticker} after {delay_hours}h "
                f"(prediction: {vote['action']} {vote['confidence']:.0%})"
            )

            # This would fetch actual price change and call:
            # orchestrator.learning_agent.analyze_debate_result(
            #     ticker=ticker,
            #     chip_war_vote=vote,
            #     final_pm_decision={...},
            #     market_reaction_24h=actual_price_change
            # )

        except Exception as e:
            logger.error(f"Learning check failed for {ticker}: {e}")


# Extend ChipWarAgent with helper methods
def extend_chip_war_agent(agent_class):
    """
    Decorator to extend ChipWarAgent with helper methods
    """
    agent_class._map_scenario_to_analysis = staticmethod(
        ChipWarAgentHelpers.map_scenario_to_analysis
    )
    agent_class._generate_vote_from_v2_analysis = staticmethod(
        ChipWarAgentHelpers.generate_vote_from_v2_analysis
    )
    agent_class._schedule_learning_check = staticmethod(
        ChipWarAgentHelpers.schedule_learning_check
    )

    return agent_class
