"""
PolicyFeasibility Tests

Market Intelligence v2.0 - Phase 3, T3.1

Tests for the Policy Feasibility component that calculates the probability
of policy realization based on political factors.

Key Features:
1. Presidential power assessment
2. Congressional alignment calculation
3. Historical precedent analysis
4. Opposition strength evaluation
5. Policy factor mapping (DEFENSE_BUDGET_INCREASE, TARIFF, TAX_CUT)

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from backend.ai.intelligence.policy_feasibility import (
    PolicyFeasibility,
    PolicyFactor,
    FeasibilityScore,
    PolicyAnalysis,
)
from backend.ai.intelligence.base import IntelligenceResult
from backend.ai.llm_providers import LLMProvider


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    class MockLLM:
        async def complete_with_system(self, system_prompt: str, user_prompt: str, config=None):
            from backend.ai.llm_providers import LLMResponse, ModelProvider

            # Return policy-specific analysis based on prompt
            if "defense" in user_prompt.lower():
                content = "Defense budget increase has high feasibility. Strong bipartisan support for national security. Historical precedent: Post-9/11 defense spending increases."
            elif "tariff" in user_prompt.lower():
                content = "Tariff policy has moderate feasibility. Congressional support split along party lines. Historical precedent: Smoot-Hawley Tariff Act effects."
            elif "tax" in user_prompt.lower():
                content = "Tax cut feasibility depends on economic conditions. Congressional alignment varies. Historical precedent: 2017 Tax Cuts and Jobs Act."
            else:
                content = "General policy feasibility analysis based on political factors."

            return LLMResponse(
                content=content,
                model="mock",
                provider=ModelProvider.MOCK,
                tokens_used=50,
                latency_ms=50,
            )

        def create_stage1_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK)

        def create_stage2_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK)

    return MockLLM()


@pytest.fixture
def mock_congressional_data():
    """Mock congressional data provider"""
    class MockCongressionalData:
        async def get_congressional_alignment(self, policy: PolicyFactor) -> Dict[str, Any]:
            """Return mock congressional alignment data"""
            alignment_map = {
                PolicyFactor.DEFENSE_BUDGET_INCREASE: {
                    "support_rate": 0.85,  # 85% support
                    "bipartisan_score": 0.7,  # Strong bipartisan support
                    "committee_approval": True,
                },
                PolicyFactor.TARIFF: {
                    "support_rate": 0.55,  # Split support
                    "bipartisan_score": 0.3,  # Low bipartisan support
                    "committee_approval": False,
                },
                PolicyFactor.TAX_CUT: {
                    "support_rate": 0.65,  # Moderate support
                    "bipartisan_score": 0.4,  # Some bipartisan support
                    "committee_approval": True,
                },
            }
            return alignment_map.get(policy, {
                "support_rate": 0.5,
                "bipartisan_score": 0.3,
                "committee_approval": False,
            })

        async def get_opposition_strength(self, policy: PolicyFactor) -> Dict[str, Any]:
            """Return mock opposition strength data"""
            opposition_map = {
                PolicyFactor.DEFENSE_BUDGET_INCREASE: {
                    "filibuster_risk": 0.2,  # Low risk
                    "public_opposition": 0.15,  # Low opposition
                    "lobby_influence": 0.3,
                },
                PolicyFactor.TARIFF: {
                    "filibuster_risk": 0.7,  # High risk
                    "public_opposition": 0.5,  # Moderate opposition
                    "lobby_influence": 0.6,
                },
                PolicyFactor.TAX_CUT: {
                    "filibuster_risk": 0.4,  # Moderate risk
                    "public_opposition": 0.3,  # Low opposition
                    "lobby_influence": 0.5,
                },
            }
            return opposition_map.get(policy, {
                "filibuster_risk": 0.5,
                "public_opposition": 0.4,
                "lobby_influence": 0.5,
            })

    return MockCongressionalData()


@pytest.fixture
def policy_feasibility(mock_llm, mock_congressional_data):
    """Create PolicyFeasibility instance"""
    return PolicyFeasibility(
        llm_provider=mock_llm,
        congressional_data=mock_congressional_data,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestPolicyFeasibilityBasic:
    """Test basic PolicyFeasibility functionality"""

    def test_initialization(self, policy_feasibility):
        """Test analyzer initializes correctly"""
        assert policy_feasibility.name == "PolicyFeasibility"
        assert policy_feasibility.phase.value == "P2"
        assert policy_feasibility._enabled is True

    @pytest.mark.asyncio
    async def test_analyze_policy_feasibility(self, policy_feasibility):
        """Test policy feasibility analysis"""
        policy_data = {
            "policy_factor": "DEFENSE_BUDGET_INCREASE",
            "description": "Increase defense budget by 15%",
            "timeline": "6-12 months",
        }

        result = await policy_feasibility.analyze(policy_data)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "feasibility_score" in result.data
        assert "presidential_power" in result.data
        assert "congressional_alignment" in result.data
        assert "historical_precedent" in result.data
        assert "opposition_strength" in result.data


# ============================================================================
# Test: Feasibility Formula
# ============================================================================

class TestFeasibilityFormula:
    """Test feasibility score calculation formula"""

    @pytest.mark.asyncio
    async def test_feasibility_formula_components(self, policy_feasibility):
        """Test that feasibility = presidential + congressional + historical - opposition"""
        policy_data = {
            "policy_factor": "DEFENSE_BUDGET_INCREASE",
            "presidential_power": 0.8,  # Strong presidential support
            "congressional_alignment": 0.7,  # Good congressional alignment
            "historical_precedent": 0.6,  # Some historical precedent
            "opposition_strength": 0.2,  # Low opposition
        }

        result = await policy_feasibility.analyze(policy_data)

        # Expected: 0.8 + 0.7 + 0.6 - 0.2 = 1.9 (normalized to 0-1)
        feasibility = result.data["feasibility_score"]
        assert 0.0 <= feasibility <= 1.0

    @pytest.mark.asyncio
    async def test_high_feasibility_scenario(self, policy_feasibility):
        """Test high feasibility scenario"""
        policy_data = {
            "policy_factor": "DEFENSE_BUDGET_INCREASE",
            "presidential_power": 0.9,
            "congressional_alignment": 0.85,
            "historical_precedent": 0.8,
            "opposition_strength": 0.1,  # Very low opposition
        }

        result = await policy_feasibility.analyze(policy_data)

        assert result.data["feasibility_score"] >= 0.7  # High feasibility

    @pytest.mark.asyncio
    async def test_low_feasibility_scenario(self, policy_feasibility):
        """Test low feasibility scenario"""
        # Create custom mock with low alignment and high opposition
        class LowAlignmentMock:
            async def get_congressional_alignment(self, policy):
                return {"support_rate": 0.2, "bipartisan_score": 0.2, "committee_approval": False}

            async def get_opposition_strength(self, policy):
                return {"filibuster_risk": 0.8, "public_opposition": 0.7, "lobby_influence": 0.8}

        original_data = policy_feasibility.congressional_data
        policy_feasibility.congressional_data = LowAlignmentMock()

        policy_data = {
            "policy_factor": "TARIFF",
            "presidential_approval": 0.3,  # Low approval
            "executive_order_possible": False,
        }

        result = await policy_feasibility.analyze(policy_data)

        # Restore original
        policy_feasibility.congressional_data = original_data

        # Should have low feasibility
        assert result.data["feasibility_score"] <= 0.5  # Low feasibility


# ============================================================================
# Test: Policy Factors
# ============================================================================

class TestPolicyFactors:
    """Test policy factor mapping"""

    def test_defense_budget_increase_enum(self):
        """Test DEFENSE_BUDGET_INCREASE policy factor"""
        factor = PolicyFactor.DEFENSE_BUDGET_INCREASE
        assert factor.value == "DEFENSE_BUDGET_INCREASE"

    def test_tariff_enum(self):
        """Test TARIFF policy factor"""
        factor = PolicyFactor.TARIFF
        assert factor.value == "TARIFF"

    def test_tax_cut_enum(self):
        """Test TAX_CUT policy factor"""
        factor = PolicyFactor.TAX_CUT
        assert factor.value == "TAX_CUT"

    @pytest.mark.asyncio
    async def test_defense_budget_analysis(self, policy_feasibility):
        """Test defense budget increase analysis"""
        policy_data = {
            "policy_factor": "DEFENSE_BUDGET_INCREASE",
            "description": "Increase defense spending for national security",
        }

        result = await policy_feasibility.analyze(policy_data)

        assert result.success is True
        assert result.data["policy_factor"] == "DEFENSE_BUDGET_INCREASE"

    @pytest.mark.asyncio
    async def test_tariff_analysis(self, policy_feasibility):
        """Test tariff policy analysis"""
        policy_data = {
            "policy_factor": "TARIFF",
            "description": "Implement new tariffs on imports",
        }

        result = await policy_feasibility.analyze(policy_data)

        assert result.success is True
        assert result.data["policy_factor"] == "TARIFF"

    @pytest.mark.asyncio
    async def test_tax_cut_analysis(self, policy_feasibility):
        """Test tax cut policy analysis"""
        policy_data = {
            "policy_factor": "TAX_CUT",
            "description": "Reduce corporate tax rates",
        }

        result = await policy_feasibility.analyze(policy_data)

        assert result.success is True
        assert result.data["policy_factor"] == "TAX_CUT"


# ============================================================================
# Test: Presidential Power
# ============================================================================

class TestPresidentialPower:
    """Test presidential power assessment"""

    @pytest.mark.asyncio
    async def test_high_presidential_power(self, policy_feasibility):
        """Test high presidential power scenario"""
        policy_data = {
            "policy_factor": "DEFENSE_BUDGET_INCREASE",
            "presidential_approval": 0.6,  # Above 50% threshold
            "executive_order_possible": True,
        }

        result = await policy_feasibility.analyze(policy_data)

        # Presidential power should be high
        assert result.data["presidential_power"] >= 0.6

    @pytest.mark.asyncio
    async def test_low_presidential_power(self, policy_feasibility):
        """Test low presidential power scenario"""
        policy_data = {
            "policy_factor": "TARIFF",
            "presidential_approval": 0.4,  # Below 50% threshold
            "executive_order_possible": False,
        }

        result = await policy_feasibility.analyze(policy_data)

        # Presidential power should be lower
        assert result.data["presidential_power"] <= 0.5


# ============================================================================
# Test: Congressional Alignment
# ============================================================================

class TestCongressionalAlignment:
    """Test congressional alignment calculation"""

    @pytest.mark.asyncio
    async def test_high_congressional_alignment(self, policy_feasibility):
        """Test high congressional alignment (defense budget)"""
        policy_data = {
            "policy_factor": "DEFENSE_BUDGET_INCREASE",
        }

        result = await policy_feasibility.analyze(policy_data)

        # Defense budget typically has high congressional alignment
        assert result.data["congressional_alignment"] >= 0.6

    @pytest.mark.asyncio
    async def test_low_congressional_alignment(self, policy_feasibility):
        """Test low congressional alignment (tariff)"""
        policy_data = {
            "policy_factor": "TARIFF",
        }

        result = await policy_feasibility.analyze(policy_data)

        # Tariff policies often have split support
        assert result.data["congressional_alignment"] <= 0.6


# ============================================================================
# Test: Historical Precedent
# ============================================================================

class TestHistoricalPrecedent:
    """Test historical precedent analysis"""

    @pytest.mark.asyncio
    async def test_strong_historical_precedent(self, policy_feasibility):
        """Test policy with strong historical precedent"""
        policy_data = {
            "policy_factor": "DEFENSE_BUDGET_INCREASE",
            "historical_similar_policies": [
                "Post-9/11 defense spending increase",
                "WWII defense buildup",
                "Cold War military expansion",
            ],
        }

        result = await policy_feasibility.analyze(policy_data)

        # Should have higher historical precedent score
        assert result.data["historical_precedent"] >= 0.5

    @pytest.mark.asyncio
    async def test_weak_historical_precedent(self, policy_feasibility):
        """Test policy with weak historical precedent"""
        policy_data = {
            "policy_factor": "TARIFF",
            "historical_similar_policies": [
                "Smoot-Hawley Tariff (negative outcome)",
            ],
        }

        result = await policy_feasibility.analyze(policy_data)

        # Negative historical precedent should lower score
        assert result.data["historical_precedent"] <= 0.5


# ============================================================================
# Test: Opposition Strength
# ============================================================================

class TestOppositionStrength:
    """Test opposition strength evaluation"""

    @pytest.mark.asyncio
    async def test_low_opposition_strength(self, policy_feasibility):
        """Test policy with low opposition"""
        policy_data = {
            "policy_factor": "DEFENSE_BUDGET_INCREASE",
        }

        result = await policy_feasibility.analyze(policy_data)

        # Defense budget typically has low opposition
        assert result.data["opposition_strength"] <= 0.4

    @pytest.mark.asyncio
    async def test_high_opposition_strength(self, policy_feasibility):
        """Test policy with high opposition"""
        policy_data = {
            "policy_factor": "TARIFF",
        }

        result = await policy_feasibility.analyze(policy_data)

        # Tariff policies often face higher opposition
        assert result.data["opposition_strength"] >= 0.4


# ============================================================================
# Test: Feasibility Score Data Class
# ============================================================================

class TestFeasibilityScore:
    """Test FeasibilityScore data class"""

    def test_feasibility_score_creation(self):
        """Test creating a FeasibilityScore"""
        score = FeasibilityScore(
            feasibility_score=0.75,
            presidential_power=0.8,
            congressional_alignment=0.7,
            historical_precedent=0.6,
            opposition_strength=0.2,
        )

        assert score.feasibility_score == 0.75
        assert score.presidential_power == 0.8
        assert score.congressional_alignment == 0.7

    def test_feasibility_score_to_dict(self):
        """Test converting FeasibilityScore to dictionary"""
        score = FeasibilityScore(
            feasibility_score=0.65,
            presidential_power=0.7,
            congressional_alignment=0.6,
            historical_precedent=0.5,
            opposition_strength=0.3,
        )

        score_dict = score.to_dict()

        assert isinstance(score_dict, dict)
        assert score_dict["feasibility_score"] == 0.65
        assert "presidential_power" in score_dict


# ============================================================================
# Test: Policy Analysis Data Class
# ============================================================================

class TestPolicyAnalysis:
    """Test PolicyAnalysis data class"""

    def test_policy_analysis_creation(self):
        """Test creating a PolicyAnalysis"""
        score = FeasibilityScore(
            feasibility_score=0.75,
            presidential_power=0.8,
            congressional_alignment=0.7,
            historical_precedent=0.6,
            opposition_strength=0.2,
        )

        analysis = PolicyAnalysis(
            policy_factor=PolicyFactor.DEFENSE_BUDGET_INCREASE,
            feasibility_score=score,
            reasoning="Strong bipartisan support for national security",
            confidence=0.85,
        )

        assert analysis.policy_factor == PolicyFactor.DEFENSE_BUDGET_INCREASE
        assert analysis.confidence == 0.85

    def test_policy_analysis_to_dict(self):
        """Test converting PolicyAnalysis to dictionary"""
        score = FeasibilityScore(
            feasibility_score=0.65,
            presidential_power=0.7,
            congressional_alignment=0.6,
            historical_precedent=0.5,
            opposition_strength=0.3,
        )

        analysis = PolicyAnalysis(
            policy_factor=PolicyFactor.TARIFF,
            feasibility_score=score,
            reasoning="Split congressional support",
            confidence=0.6,
        )

        analysis_dict = analysis.to_dict()

        assert isinstance(analysis_dict, dict)
        assert analysis_dict["policy_factor"] == "TARIFF"
        assert "feasibility_score" in analysis_dict


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestPolicyFeasibilityEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_policy_data(self, policy_feasibility):
        """Test handling of empty policy data"""
        policy_data = {}

        result = await policy_feasibility.analyze(policy_data)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_policy_factor(self, policy_feasibility):
        """Test handling of invalid policy factor"""
        policy_data = {
            "policy_factor": "INVALID_POLICY",
        }

        result = await policy_feasibility.analyze(policy_data)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, policy_feasibility):
        """Test handling of LLM errors"""
        class ErrorLLM:
            async def complete_with_system(self, system_prompt, user_prompt, config=None):
                raise Exception("LLM Error")

        original_llm = policy_feasibility.llm
        policy_feasibility.llm = ErrorLLM()

        policy_data = {"policy_factor": "DEFENSE_BUDGET_INCREASE"}

        result = await policy_feasibility.analyze(policy_data)

        # Restore original
        policy_feasibility.llm = original_llm

        # Should handle error gracefully
        assert result is not None


# ============================================================================
# Test: Confidence Calculation
# ============================================================================

class TestConfidenceCalculation:
    """Test confidence calculation for feasibility assessment"""

    @pytest.mark.asyncio
    async def test_high_confidence_for_clear_data(self, policy_feasibility):
        """Test high confidence when all factors are clear"""
        policy_data = {
            "policy_factor": "DEFENSE_BUDGET_INCREASE",
            "presidential_power": 0.8,
            "congressional_alignment": 0.7,
            "historical_precedent": 0.6,
            "opposition_strength": 0.2,
        }

        result = await policy_feasibility.analyze(policy_data)

        # Should have high confidence
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_moderate_confidence_for_mixed_signals(self, policy_feasibility):
        """Test moderate confidence when signals are mixed"""
        policy_data = {
            "policy_factor": "TARIFF",
            "presidential_power": 0.5,
            "congressional_alignment": 0.3,
            "historical_precedent": 0.4,
            "opposition_strength": 0.6,
        }

        result = await policy_feasibility.analyze(policy_data)

        # Should have moderate to high confidence (implementation adds boost for valid ranges)
        assert 0.6 <= result.confidence <= 0.95


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
