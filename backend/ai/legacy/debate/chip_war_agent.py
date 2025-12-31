"""
Chip War Agent for War Room Debate (Self-Learning Edition)

8번째 War Room 멤버로 반도체 칩 경쟁 분석 (Nvidia vs Google/Meta TPU)을 수행하여
매매 의견을 제시합니다.

Vote Weight: 12%
Focus: TorchTPU vs CUDA moat competition
Data Sources:
- ChipWarSimulator V2 (multi-generation roadmap)
- ChipIntelligenceEngine (self-learning, rumors, scenarios)
- Market disruption scoring

Self-Learning Features:
- Automatically updates chip specs from intelligence engine
- Incorporates market rumors (high credibility only)
- Uses future scenarios for prediction
- Learns from past debate accuracy

Author: AI Trading System
Date: 2025-12-23
Phase: 24.5 (Self-Learning Integration)
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import asyncio

from backend.ai.economics.chip_war_simulator import ChipWarSimulator
from backend.ai.economics.chip_war_simulator_v2 import ChipComparator
from backend.ai.economics.chip_intelligence_engine import (
    ChipIntelligenceOrchestrator,
    ConfidenceLevel
)
from backend.ai.debate.chip_war_agent_helpers import ChipWarAgentHelpers

logger = logging.getLogger(__name__)


class ChipWarAgent:
    """칩 전쟁 분석 Agent (War Room 8th member) - Self-Learning Edition"""

    def __init__(self, enable_self_learning: bool = True):
        self.agent_name = "chip_war"
        self.vote_weight = 0.12  # 12% 투표권

        # V1 Simulator (backward compatibility)
        self.simulator = ChipWarSimulator()

        # V2 Enhanced Comparator (multi-generation)
        self.comparator = ChipComparator()

        # Self-learning intelligence engine
        self.enable_self_learning = enable_self_learning
        if enable_self_learning:
            self.intelligence = ChipIntelligenceOrchestrator()
            logger.info("🧠 ChipWarAgent: Self-learning enabled")
        else:
            self.intelligence = None

        # Semiconductor-related tickers
        self.chip_tickers = {
            "NVDA": "nvidia",
            "GOOGL": "google",
            "GOOG": "google",
            "AVGO": "broadcom",  # TPU partnerships
            "META": "meta",      # TorchTPU co-developer
            "AMD": "amd",
            "INTC": "intel",
            "TSM": "tsmc",       # Manufacturer
            "ASML": "asml",      # Equipment
            "ARM": "arm",        # Architecture
        }

        logger.info(f"ChipWarAgent initialized (weight: {self.vote_weight}, self-learning: {enable_self_learning})")

    async def analyze(self, ticker: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        칩 전쟁 분석 후 투표 결정

        Args:
            ticker: 분석할 티커 (예: NVDA, GOOGL)
            context: 추가 컨텍스트 (선택)

        Returns:
            {
                "agent": "chip_war",
                "action": "BUY/SELL/HOLD",
                "confidence": 0.0-1.0,
                "reasoning": "...",
                "chip_war_factors": {
                    "disruption_score": float,
                    "verdict": str,
                    "scenario": str,
                    "nvidia_tco": float,
                    "google_tco": float,
                }
            }
        """
        ticker = ticker.upper()

        # Only vote on semiconductor-related tickers
        if ticker not in self.chip_tickers:
            logger.debug(f"ChipWarAgent: {ticker} not a semiconductor ticker, voting HOLD")
            return {
                "agent": self.agent_name,
                "action": "HOLD",
                "confidence": 0.0,
                "reasoning": f"{ticker} is not a semiconductor ticker (chip war analysis skipped)",
                "chip_war_factors": None
            }

        logger.info(f"🎮 ChipWarAgent analyzing {ticker} (chip war impact)")

        try:
            # === SELF-LEARNING ENHANCEMENT ===
            # 1. Check for high-credibility rumors
            active_rumors = []
            selected_scenario = "base"
            scenarios = []  # Initialize scenarios outside the if block

            if self.enable_self_learning and self.intelligence:
                # Get high-credibility rumors (>80%)
                high_cred_rumors = self.intelligence.rumor_tracker.get_high_credibility_rumors(0.8)

                if high_cred_rumors:
                    logger.info(f"🔍 Found {len(high_cred_rumors)} high-credibility rumors")
                    active_rumors = high_cred_rumors

                # Get active scenarios (>30% probability)
                scenarios = self.intelligence.db.get_scenarios(min_probability=0.30)

                if scenarios:
                    # Select highest probability scenario
                    top_scenario = max(scenarios, key=lambda s: s["probability"])
                    selected_scenario = self._map_scenario_to_analysis(top_scenario, ticker)
                    logger.info(f"🎯 Using scenario: {top_scenario['name']} ({top_scenario['probability']:.0%} prob)")

            # === RUN ANALYSIS ===
            # Use V2 Comparator for enhanced analysis
            if ticker in ["NVDA", "GOOGL", "GOOG"]:
                # Compare latest generation chips
                comparison = await asyncio.to_thread(
                    self.comparator.compare_comprehensive,
                    nvidia_key="NV_Rubin",  # 2026 flagship
                    google_key="Google_Ironwood_v7",  # 2025-2026
                    scenario=selected_scenario
                )

                # Extract chip war factors
                chip_war_factors = {
                    "disruption_score": comparison["analysis"]["disruption_score"],
                    "verdict": comparison["analysis"]["verdict"],
                    "scenario": selected_scenario,
                    "nvidia_tco": comparison["nvidia"]["tco_3yr"],
                    "google_tco": comparison["google"]["tco_3yr"],
                    "tco_advantage": comparison["analysis"]["economic_advantage_pct"],
                    "active_rumors": len(active_rumors),
                    "scenario_probability": max([s["probability"] for s in scenarios], default=0) if scenarios else 0
                }

                # Generate vote using V2 investment signals
                vote = self._generate_vote_from_v2_analysis(ticker, comparison, chip_war_factors)

            else:
                # Fallback to V1 simulator for other tickers
                report = await asyncio.to_thread(
                    self.simulator.generate_chip_war_report,
                    scenario=selected_scenario
                )

                vote = self._generate_vote_for_ticker(ticker, report)

            # === POST-ANALYSIS LEARNING (Async) ===
            if self.enable_self_learning and self.intelligence:
                # Store this prediction for future learning
                # (Will be evaluated after market reaction is known)
                asyncio.create_task(self._schedule_learning_check(ticker, vote))

            logger.info(f"🎮 ChipWarAgent vote for {ticker}: {vote['action']} "
                       f"({vote['confidence']:.0%}) - {vote['reasoning'][:50]}...")

            return vote

        except Exception as e:
            logger.error(f"❌ ChipWarAgent analysis failed for {ticker}: {e}", exc_info=True)
            # Return neutral vote on error
            return {
                "agent": self.agent_name,
                "action": "HOLD",
                "confidence": 0.3,
                "reasoning": f"Chip war analysis failed: {str(e)}",
                "chip_war_factors": None
            }

    def _generate_vote_for_ticker(
        self,
        ticker: str,
        report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate voting decision for specific ticker based on chip war report

        Logic:
        - NVDA: Inverse of threat level (THREAT → REDUCE, SAFE → BUY)
        - GOOGL/META: Aligned with threat level (THREAT → BUY, SAFE → REDUCE)
        - AVGO: Aligned with Google (TPU partnerships)
        - AMD/INTC: Neutral (benefit from market uncertainty)
        """
        verdict = report["verdict"]
        disruption_score = report["disruption_score"]
        scenario_name = report["scenario_name"]

        # Extract TCO data
        nvidia_chip = next(
            (c for c in report["chip_comparison"] if c["manufacturer"] == "Nvidia"),
            None
        )
        google_chip = next(
            (c for c in report["chip_comparison"] if c["manufacturer"] == "Google"),
            None
        )

        nvidia_tco = nvidia_chip["tco"] if nvidia_chip else 0
        google_tco = google_chip["tco"] if google_chip else 0

        # Chip war factors for all votes
        chip_war_factors = {
            "disruption_score": disruption_score,
            "verdict": verdict,
            "scenario": scenario_name,
            "nvidia_tco": nvidia_tco,
            "google_tco": google_tco,
            "tco_advantage": ((nvidia_tco - google_tco) / nvidia_tco * 100) if nvidia_tco > 0 else 0
        }

        # Generate vote based on ticker
        if ticker == "NVDA":
            return self._vote_for_nvidia(verdict, disruption_score, chip_war_factors)

        elif ticker in ["GOOGL", "GOOG"]:
            return self._vote_for_google(verdict, disruption_score, chip_war_factors)

        elif ticker == "META":
            return self._vote_for_meta(verdict, disruption_score, chip_war_factors)

        elif ticker == "AVGO":
            return self._vote_for_broadcom(verdict, disruption_score, chip_war_factors)

        elif ticker in ["AMD", "INTC"]:
            return self._vote_for_other_chips(ticker, verdict, disruption_score, chip_war_factors)

        else:
            # TSM, ASML, ARM - indirect beneficiaries
            return self._vote_for_infrastructure(ticker, verdict, disruption_score, chip_war_factors)

    def _vote_for_nvidia(
        self,
        verdict: str,
        disruption_score: float,
        factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Vote for NVDA based on chip war threat level

        THREAT → REDUCE (moat under attack)
        MONITORING → HOLD (watch closely)
        SAFE → BUY (moat intact)
        """
        if verdict == "THREAT":
            return {
                "agent": self.agent_name,
                "action": "SELL",
                "confidence": min(0.75, (disruption_score - 100) / 100),  # Higher disruption = higher confidence
                "reasoning": (
                    f"⚠️ Nvidia's CUDA moat under THREAT (disruption: {disruption_score:.0f}). "
                    f"TorchTPU showing strong market disruption potential. "
                    f"Google TPU TCO advantage: {factors['tco_advantage']:.1f}%. "
                    f"Recommend REDUCING Nvidia exposure."
                ),
                "chip_war_factors": factors
            }

        elif verdict == "MONITORING":
            return {
                "agent": self.agent_name,
                "action": "HOLD",
                "confidence": 0.60,
                "reasoning": (
                    f"⚡ Nvidia's CUDA moat needs MONITORING (disruption: {disruption_score:.0f}). "
                    f"TorchTPU progress uncertain, maintain current position. "
                    f"Watch for Meta adoption announcements."
                ),
                "chip_war_factors": factors
            }

        else:  # SAFE
            return {
                "agent": self.agent_name,
                "action": "BUY",
                "confidence": min(0.85, 1.0 - (disruption_score / 200)),
                "reasoning": (
                    f"✅ Nvidia's CUDA moat remains SAFE (disruption: {disruption_score:.0f}). "
                    f"TorchTPU not gaining traction, ecosystem advantage intact. "
                    f"CUDA dominance continues in training market."
                ),
                "chip_war_factors": factors
            }

    def _vote_for_google(
        self,
        verdict: str,
        disruption_score: float,
        factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Vote for GOOGL based on chip war threat level

        THREAT → BUY (TPU gaining momentum)
        MONITORING → HOLD (uncertain outcome)
        SAFE → REDUCE (TPU not competitive)
        """
        if verdict == "THREAT":
            return {
                "agent": self.agent_name,
                "action": "BUY",
                "confidence": min(0.80, (disruption_score - 100) / 120),
                "reasoning": (
                    f"🚀 Google TPU showing STRONG disruption (score: {disruption_score:.0f}). "
                    f"TorchTPU reducing migration friction, TCO advantage: {factors['tco_advantage']:.1f}%. "
                    f"Positioned to capture inference market share from Nvidia. "
                    f"Recommend LONG Google."
                ),
                "chip_war_factors": factors
            }

        elif verdict == "MONITORING":
            return {
                "agent": self.agent_name,
                "action": "HOLD",
                "confidence": 0.55,
                "reasoning": (
                    f"⚡ Google TPU showing moderate potential (disruption: {disruption_score:.0f}). "
                    f"TorchTPU adoption uncertain, wait for Meta confirmation. "
                    f"Cloud AI revenue stable, maintain position."
                ),
                "chip_war_factors": factors
            }

        else:  # SAFE (low disruption = Google losing)
            return {
                "agent": self.agent_name,
                "action": "SELL",
                "confidence": 0.65,
                "reasoning": (
                    f"⚠️ Google TPU failing to disrupt (score: {disruption_score:.0f}). "
                    f"TorchTPU not gaining traction, CUDA moat intact. "
                    f"Cloud AI growth limited by chip competitiveness. "
                    f"Consider REDUCING Google exposure in favor of Nvidia."
                ),
                "chip_war_factors": factors
            }

    def _vote_for_meta(
        self,
        verdict: str,
        disruption_score: float,
        factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Vote for META based on TorchTPU success

        Meta is co-developer of TorchTPU (with Google)
        Success → Reduced datacenter costs → BUY
        Failure → Continued Nvidia dependency → HOLD
        """
        if verdict == "THREAT":
            return {
                "agent": self.agent_name,
                "action": "BUY",
                "confidence": 0.65,
                "reasoning": (
                    f"✅ Meta's TorchTPU initiative succeeding (disruption: {disruption_score:.0f}). "
                    f"Native PyTorch on TPU reduces infrastructure costs. "
                    f"TCO savings: {factors['tco_advantage']:.1f}% vs Nvidia. "
                    f"Positive for Meta's AI capex efficiency."
                ),
                "chip_war_factors": factors
            }

        elif verdict == "MONITORING":
            return {
                "agent": self.agent_name,
                "action": "HOLD",
                "confidence": 0.50,
                "reasoning": (
                    f"⚡ Meta's TorchTPU outcome uncertain (disruption: {disruption_score:.0f}). "
                    f"Watch for official announcements on TPU adoption. "
                    f"AI infrastructure costs remain elevated."
                ),
                "chip_war_factors": factors
            }

        else:  # SAFE (TorchTPU failing)
            return {
                "agent": self.agent_name,
                "action": "HOLD",
                "confidence": 0.40,
                "reasoning": (
                    f"⚠️ Meta's TorchTPU not materializing (disruption: {disruption_score:.0f}). "
                    f"Continued reliance on expensive Nvidia infrastructure. "
                    f"AI capex concerns persist, neutral position."
                ),
                "chip_war_factors": factors
            }

    def _vote_for_broadcom(
        self,
        verdict: str,
        disruption_score: float,
        factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Vote for AVGO (Broadcom)

        Broadcom benefits from TPU custom chip partnerships with Google
        THREAT → BUY (more TPU orders)
        SAFE → HOLD (status quo)
        """
        if verdict == "THREAT":
            return {
                "agent": self.agent_name,
                "action": "BUY",
                "confidence": 0.70,
                "reasoning": (
                    f"🔧 Broadcom positioned for TPU growth (disruption: {disruption_score:.0f}). "
                    f"Google TPU custom chip partnerships expanding. "
                    f"Diversified beneficiary of chip war competition."
                ),
                "chip_war_factors": factors
            }

        else:
            return {
                "agent": self.agent_name,
                "action": "HOLD",
                "confidence": 0.50,
                "reasoning": (
                    f"⚡ Broadcom chip war exposure neutral (disruption: {disruption_score:.0f}). "
                    f"Diversified revenue streams, maintain position."
                ),
                "chip_war_factors": factors
            }

    def _vote_for_other_chips(
        self,
        ticker: str,
        verdict: str,
        disruption_score: float,
        factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Vote for AMD/INTC

        Benefit from market uncertainty and Nvidia pricing pressure
        THREAT → BUY (Nvidia competition helps AMD/INTC)
        SAFE → HOLD (Nvidia dominance limits AMD/INTC)
        """
        if verdict == "THREAT":
            return {
                "agent": self.agent_name,
                "action": "BUY",
                "confidence": 0.60,
                "reasoning": (
                    f"📈 {ticker} benefits from chip war competition (disruption: {disruption_score:.0f}). "
                    f"Nvidia pricing pressure creates opportunities for alternatives. "
                    f"Market share gains possible in fragmented landscape."
                ),
                "chip_war_factors": factors
            }

        else:
            return {
                "agent": self.agent_name,
                "action": "HOLD",
                "confidence": 0.45,
                "reasoning": (
                    f"⚡ {ticker} chip war impact neutral (disruption: {disruption_score:.0f}). "
                    f"Nvidia dominance intact, limited near-term opportunities."
                ),
                "chip_war_factors": factors
            }

    def _vote_for_infrastructure(
        self,
        ticker: str,
        verdict: str,
        disruption_score: float,
        factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Vote for TSM/ASML/ARM

        Infrastructure providers benefit from increased chip R&D regardless of winner
        All scenarios → HOLD/BUY (rising tide lifts all boats)
        """
        if verdict == "THREAT":
            confidence = 0.65
            action = "BUY"
            reasoning_detail = "Chip war driving increased R&D spending across industry"
        else:
            confidence = 0.55
            action = "HOLD"
            reasoning_detail = "Stable demand from Nvidia dominance"

        return {
            "agent": self.agent_name,
            "action": action,
            "confidence": confidence,
            "reasoning": (
                f"🏗️ {ticker} infrastructure play (disruption: {disruption_score:.0f}). "
                f"{reasoning_detail}. "
                f"Long-term beneficiary of AI chip growth."
            ),
            "chip_war_factors": factors
        }
    # === HELPER METHODS FROM ChipWarAgentHelpers ===
    def _map_scenario_to_analysis(self, scenario: Dict, ticker: str) -> str:
        return ChipWarAgentHelpers.map_scenario_to_analysis(scenario, ticker)
    
    def _generate_vote_from_v2_analysis(self, ticker: str, comparison: Dict, chip_war_factors: Dict) -> Dict[str, Any]:
        return ChipWarAgentHelpers.generate_vote_from_v2_analysis(ticker, comparison, chip_war_factors)
    
    async def _schedule_learning_check(self, ticker: str, vote: Dict):
        await ChipWarAgentHelpers.schedule_learning_check(ticker, vote)
