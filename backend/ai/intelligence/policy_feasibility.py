"""
PolicyFeasibility Component - Policy Realization Probability

Market Intelligence v2.0 - Phase 3, T3.1

This component calculates the probability of policy realization based on
political factors including presidential power, congressional alignment,
historical precedent, and opposition strength.

Key Features:
1. Presidential power assessment
2. Congressional alignment calculation
3. Historical precedent analysis
4. Opposition strength evaluation
5. Policy factor mapping (DEFENSE_BUDGET_INCREASE, TARIFF, TAX_CUT)

Feasibility Formula:
feasibility = presidential_power + congressional_alignment + historical_precedent - opposition_strength

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ..llm_providers import LLMProvider


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class PolicyFactor(Enum):
    """Policy factors for feasibility analysis"""
    DEFENSE_BUDGET_INCREASE = "DEFENSE_BUDGET_INCREASE"  # Defense spending increase
    TARIFF = "TARIFF"  # Trade tariff implementation
    TAX_CUT = "TAX_CUT"  # Tax rate reduction


@dataclass
class FeasibilityScore:
    """
    Feasibility score components

    Attributes:
        feasibility_score: Overall feasibility (0-1)
        presidential_power: Presidential support strength (0-1)
        congressional_alignment: Congressional support level (0-1)
        historical_precedent: Historical precedent strength (0-1)
        opposition_strength: Opposition intensity (0-1)
    """
    feasibility_score: float
    presidential_power: float
    congressional_alignment: float
    historical_precedent: float
    opposition_strength: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "feasibility_score": self.feasibility_score,
            "presidential_power": self.presidential_power,
            "congressional_alignment": self.congressional_alignment,
            "historical_precedent": self.historical_precedent,
            "opposition_strength": self.opposition_strength,
        }


@dataclass
class PolicyAnalysis:
    """
    Result of policy feasibility analysis

    Attributes:
        policy_factor: Policy factor being analyzed
        feasibility_score: Feasibility score components
        reasoning: Explanation of feasibility assessment
        confidence: Confidence in assessment
        analyzed_at: Analysis timestamp
    """
    policy_factor: PolicyFactor
    feasibility_score: FeasibilityScore
    reasoning: str = ""
    confidence: float = 0.7
    analyzed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "policy_factor": self.policy_factor.value,
            "feasibility_score": self.feasibility_score.to_dict(),
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


# ============================================================================
# Main Component
# ============================================================================

class PolicyFeasibility(BaseIntelligence):
    """
    Policy Feasibility Analyzer

    Calculates the probability of policy realization based on political factors.

    Feasibility Formula:
    feasibility = presidential_power + congressional_alignment + historical_precedent - opposition_strength

    Key Features:
    1. Presidential power: Based on approval rating and executive order capability
    2. Congressional alignment: Based on support rate and bipartisanship
    3. Historical precedent: Based on similar past policies
    4. Opposition strength: Based on filibuster risk and public opposition

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.policy_feasibility import PolicyFeasibility, PolicyFactor

        llm = get_llm_provider()
        analyzer = PolicyFeasibility(
            llm_provider=llm,
            congressional_data=congress_client,
        )

        # Analyze defense budget feasibility
        result = await analyzer.analyze({
            "policy_factor": "DEFENSE_BUDGET_INCREASE",
            "description": "Increase defense budget by 15%",
        })

        feasibility = result.data["feasibility_score"]
    """

    # Thresholds
    PRESIDENTIAL_APPROVAL_THRESHOLD = 0.5  # 50% approval threshold
    MAX_FEASIBILITY_SCORE = 1.0  # Maximum normalized score

    def __init__(
        self,
        llm_provider: LLMProvider,
        congressional_data: Optional[Any] = None,
    ):
        """
        Initialize PolicyFeasibility

        Args:
            llm_provider: LLM Provider instance
            congressional_data: Congressional data API client (optional)
        """
        super().__init__(
            name="PolicyFeasibility",
            phase=IntelligencePhase.P2,
        )

        self.llm = llm_provider
        self.congressional_data = congressional_data

        # Statistics
        self._analysis_count = 0
        self._policy_factor_counts = {
            "DEFENSE_BUDGET_INCREASE": 0,
            "TARIFF": 0,
            "TAX_CUT": 0,
        }

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Analyze policy feasibility (main entry point)

        Args:
            data: Policy data with:
                - policy_factor: Policy factor (string or PolicyFactor)
                - description: Policy description
                - presidential_approval: Presidential approval rating (optional)
                - executive_order_possible: Can use executive order (optional)
                - historical_similar_policies: List of similar policies (optional)

        Returns:
            IntelligenceResult: Feasibility analysis result
        """
        try:
            # Parse policy factor
            policy_factor_str = data.get("policy_factor", "")
            try:
                policy_factor = PolicyFactor(policy_factor_str)
            except ValueError:
                # Invalid policy factor
                return self.create_result(
                    success=False,
                    data={"stage": "policy_feasibility"},
                    reasoning=f"Invalid policy factor: {policy_factor_str}",
                )

            # Calculate components
            presidential_power = await self._calculate_presidential_power(data, policy_factor)
            congressional_alignment = await self._calculate_congressional_alignment(policy_factor)
            historical_precedent = await self._calculate_historical_precedent(data, policy_factor)
            opposition_strength = await self._calculate_opposition_strength(policy_factor)

            # Calculate feasibility score
            raw_score = (
                presidential_power
                + congressional_alignment
                + historical_precedent
                - opposition_strength
            )

            # Normalize to 0-1 range
            feasibility_score = max(0.0, min(self.MAX_FEASIBILITY_SCORE, raw_score))

            # Create feasibility score object
            score = FeasibilityScore(
                feasibility_score=feasibility_score,
                presidential_power=presidential_power,
                congressional_alignment=congressional_alignment,
                historical_precedent=historical_precedent,
                opposition_strength=opposition_strength,
            )

            # Generate reasoning with LLM
            reasoning = await self._generate_reasoning(policy_factor, score, data)

            # Calculate confidence
            confidence = self._calculate_confidence(score, data)

            # Build result
            analysis = PolicyAnalysis(
                policy_factor=policy_factor,
                feasibility_score=score,
                reasoning=reasoning,
                confidence=confidence,
            )

            # Update statistics
            self._analysis_count += 1
            self._policy_factor_counts[policy_factor.value] += 1

            return self.create_result(
                success=True,
                data={
                    "stage": "policy_feasibility",
                    "policy_factor": policy_factor.value,
                    **score.to_dict(),
                    "reasoning": reasoning,
                },
                confidence=confidence,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Policy feasibility analysis error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "policy_feasibility"},
            )
            result.add_error(f"Analysis error: {str(e)}")
            return result

    async def _calculate_presidential_power(
        self,
        data: Dict[str, Any],
        policy_factor: PolicyFactor,
    ) -> float:
        """
        Calculate presidential power

        Based on:
        - Presidential approval rating
        - Executive order capability
        """
        try:
            # Get presidential approval (default to 0.5 if not provided)
            approval = data.get("presidential_approval", 0.5)

            # Executive order capability
            executive_order_possible = data.get("executive_order_possible", False)

            # Base power from approval
            power = approval

            # Boost if executive order is possible
            if executive_order_possible:
                power = min(1.0, power + 0.2)

            return power

        except Exception as e:
            logger.error(f"Presidential power calculation error: {e}")
            return 0.5  # Default to neutral

    async def _calculate_congressional_alignment(
        self,
        policy_factor: PolicyFactor,
    ) -> float:
        """
        Calculate congressional alignment

        Based on:
        - Support rate in Congress
        - Bipartisan score
        - Committee approval
        """
        try:
            if self.congressional_data:
                # Get actual congressional data
                alignment_data = await self.congressional_data.get_congressional_alignment(policy_factor)

                # Calculate alignment from support rate and bipartisanship
                support_rate = alignment_data.get("support_rate", 0.5)
                bipartisan_score = alignment_data.get("bipartisan_score", 0.3)

                # Weighted average: 70% support rate, 30% bipartisanship
                alignment = 0.7 * support_rate + 0.3 * bipartisan_score

                # Boost if committee approved
                if alignment_data.get("committee_approval", False):
                    alignment = min(1.0, alignment + 0.1)

                return alignment
            else:
                # Use default values based on policy factor
                defaults = {
                    PolicyFactor.DEFENSE_BUDGET_INCREASE: 0.7,  # High alignment
                    PolicyFactor.TARIFF: 0.4,  # Lower alignment
                    PolicyFactor.TAX_CUT: 0.5,  # Moderate alignment
                }
                return defaults.get(policy_factor, 0.5)

        except Exception as e:
            logger.error(f"Congressional alignment calculation error: {e}")
            return 0.5  # Default to neutral

    async def _calculate_historical_precedent(
        self,
        data: Dict[str, Any],
        policy_factor: PolicyFactor,
    ) -> float:
        """
        Calculate historical precedent

        Based on:
        - Number of similar past policies
        - Success rate of similar policies
        """
        try:
            # Get historical similar policies
            similar_policies = data.get("historical_similar_policies", [])

            if not similar_policies:
                # Use default values based on policy factor
                defaults = {
                    PolicyFactor.DEFENSE_BUDGET_INCREASE: 0.7,  # Strong precedent
                    PolicyFactor.TARIFF: 0.3,  # Weak precedent (Smoot-Hawley)
                    PolicyFactor.TAX_CUT: 0.5,  # Moderate precedent
                }
                return defaults.get(policy_factor, 0.4)

            # Calculate precedent based on number of similar policies
            # More similar policies = stronger precedent
            base_precedent = min(1.0, len(similar_policies) * 0.2)

            return base_precedent

        except Exception as e:
            logger.error(f"Historical precedent calculation error: {e}")
            return 0.4  # Default to moderate

    async def _calculate_opposition_strength(
        self,
        policy_factor: PolicyFactor,
    ) -> float:
        """
        Calculate opposition strength

        Based on:
        - Filibuster risk
        - Public opposition
        - Lobby influence
        """
        try:
            if self.congressional_data:
                # Get actual opposition data
                opposition_data = await self.congressional_data.get_opposition_strength(policy_factor)

                # Calculate opposition from multiple factors
                filibuster_risk = opposition_data.get("filibuster_risk", 0.5)
                public_opposition = opposition_data.get("public_opposition", 0.4)
                lobby_influence = opposition_data.get("lobby_influence", 0.5)

                # Weighted average: 50% filibuster, 30% public, 20% lobby
                opposition = (
                    0.5 * filibuster_risk
                    + 0.3 * public_opposition
                    + 0.2 * lobby_influence
                )

                return opposition
            else:
                # Use default values based on policy factor
                defaults = {
                    PolicyFactor.DEFENSE_BUDGET_INCREASE: 0.2,  # Low opposition
                    PolicyFactor.TARIFF: 0.6,  # High opposition
                    PolicyFactor.TAX_CUT: 0.4,  # Moderate opposition
                }
                return defaults.get(policy_factor, 0.4)

        except Exception as e:
            logger.error(f"Opposition strength calculation error: {e}")
            return 0.4  # Default to moderate

    async def _generate_reasoning(
        self,
        policy_factor: PolicyFactor,
        score: FeasibilityScore,
        data: Dict[str, Any],
    ) -> str:
        """
        Generate human-readable reasoning using LLM
        """
        try:
            description = data.get("description", "")

            system_prompt = """You are a political analyst specializing in US policy feasibility.
Assess the likelihood of policy realization based on political factors."""

            user_prompt = f"""Analyze the feasibility of this policy:

Policy: {policy_factor.value}
Description: {description}

Key Factors:
- Presidential Power: {score.presidential_power:.0%}
- Congressional Alignment: {score.congressional_alignment:.0%}
- Historical Precedent: {score.historical_precedent:.0%}
- Opposition Strength: {score.opposition_strength:.0%}
- Overall Feasibility: {score.feasibility_score:.0%}

Provide a concise explanation of the feasibility assessment (2-3 sentences)."""

            response = await self.llm.complete_with_system(system_prompt, user_prompt)

            return response.content

        except Exception as e:
            logger.error(f"Reasoning generation error: {e}")
            # Fallback reasoning
            return f"Feasibility: {score.feasibility_score:.0%} based on political factors"

    def _calculate_confidence(
        self,
        score: FeasibilityScore,
        data: Dict[str, Any],
    ) -> float:
        """
        Calculate confidence in feasibility assessment

        Higher confidence when:
        - All factors are provided
        - Values are consistent
        - No extreme outliers
        """
        try:
            confidence = 0.7  # Base confidence

            # Boost if all factors are in reasonable range
            if all(0.0 <= v <= 1.0 for v in [
                score.presidential_power,
                score.congressional_alignment,
                score.historical_precedent,
                score.opposition_strength,
            ]):
                confidence = min(1.0, confidence + 0.15)

            # Reduce if feasibility is extreme (very high or very low)
            if score.feasibility_score > 0.9 or score.feasibility_score < 0.1:
                confidence = max(0.4, confidence - 0.1)

            return confidence

        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return 0.6  # Default confidence

    def get_statistics(self) -> Dict[str, Any]:
        """Get policy feasibility statistics"""
        return {
            "total_analyses": self._analysis_count,
            "defense_budget_count": self._policy_factor_counts["DEFENSE_BUDGET_INCREASE"],
            "tariff_count": self._policy_factor_counts["TARIFF"],
            "tax_cut_count": self._policy_factor_counts["TAX_CUT"],
        }


# ============================================================================
# Factory function
# ============================================================================

def create_policy_feasibility(
    llm_provider: Optional[LLMProvider] = None,
    congressional_data: Optional[Any] = None,
) -> PolicyFeasibility:
    """
    Create PolicyFeasibility instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        congressional_data: Congressional data API client

    Returns:
        PolicyFeasibility: Configured analyzer instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return PolicyFeasibility(
        llm_provider=llm_provider,
        congressional_data=congressional_data,
    )
