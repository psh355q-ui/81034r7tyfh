"""
Chip War Agent for War Room Debate

8번째 War Room 멤버로 반도체 칩 경쟁 분석 (Nvidia vs Google/Meta TPU)을 수행하여
매매 의견을 제시합니다.

Vote Weight: 12%
Focus: TorchTPU vs CUDA moat competition
Data Sources:
- ChipWarSimulator (software ecosystem score, TCO analysis)
- Market disruption scoring

Author: AI Trading System
Date: 2025-12-23
Phase: 24 (ChipWarAgent Integration)
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import asyncio

from backend.ai.economics.chip_war_simulator import ChipWarSimulator

logger = logging.getLogger(__name__)


class ChipWarAgent:
    """칩 전쟁 분석 Agent (War Room 8th member)"""

    def __init__(self):
        self.agent_name = "chip_war"
        self.vote_weight = 0.12  # 12% 투표권
        self.simulator = ChipWarSimulator()

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

        logger.info(f"ChipWarAgent initialized (weight: {self.vote_weight})")

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
            # Run chip war simulation (base scenario)
            report = await asyncio.to_thread(
                self.simulator.generate_chip_war_report,
                scenario="base"
            )

            # Find relevant signal for this ticker
            vote = self._generate_vote_for_ticker(ticker, report)

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
