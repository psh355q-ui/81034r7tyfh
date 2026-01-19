"""
PersonaTuning Tests

Market Intelligence v2.0 - Phase 3, T3.3

Tests for the Persona Tuning component that creates prompts in the style of
"Sosumonkey" - two-stage conclusion, connecting threads, easy metaphors,
data-driven, opposing viewpoints.

Key Features:
1. SOSUMONKEY_PERSONA prompt template
2. INSIGHT_GENERATION_PROMPT_V2
3. Style validation (LLM response matches Sosumonkey style)
4. Prompt version tracking
5. Connect to prompt_versions table

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from backend.ai.intelligence.prompts.persona_tuned_prompts import (
    PersonaTuning,
    PersonaStyle,
    PromptVersion,
    SOSUMONKEY_PERSONA,
    INSIGHT_GENERATION_PROMPT_V2,
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

            # Return Sosumonkey-style response
            content = """**[요약]**
AI 반도체 테마가 강세입니다. NVDA가 데이터센터 수요 증가로 주가 8% 상승.

**[배경]**
1. 빅테크 기업들이 AI 인프라 투자 확대
2. HBM/AI 칩 수요가 공급보다 수요가 많음
3. 2분기 실적 시즌 전 기대감 형성

**[연결]**
이미 HBM 칩 가격은 1분기 대비 15% 올랐고, SK하이닉스가 생산 늘력 확대 발표했습니다. 이는 NVDA 실적과 직결됩니다.

**[반론]**
하지만 일부에서는 밸류에이션 우려를 제기합니다. P/E 80배는 과하게 높다는 시각입니다.

**[종합]**
단기적으로는 실적 좋을 것이고, 중기적으로는 밸류에이션 조정이 예상됩니다."""

            return LLMResponse(
                content=content,
                model="mock",
                provider=ModelProvider.MOCK,
                tokens_used=150,
                latency_ms=100,
            )

        def create_stage1_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK)

        def create_stage2_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK)

    return MockLLM()


@pytest.fixture
def mock_prompt_repository():
    """Mock prompt version repository"""
    class MockPromptRepository:
        def __init__(self):
            self.versions = []

        async def save_prompt_version(self, version: PromptVersion):
            """Save prompt version"""
            self.versions.append(version)
            return True

        async def get_latest_version(self, persona: str) -> PromptVersion:
            """Get latest prompt version"""
            return PromptVersion(
                version_id=1,
                persona=persona,
                template_content="Test template",
                created_at=datetime.now(),
            )

        async def get_version_history(self, persona: str) -> list:
            """Get version history"""
            return self.versions

    return MockPromptRepository()


@pytest.fixture
def persona_tuning(mock_llm, mock_prompt_repository):
    """Create PersonaTuning instance"""
    return PersonaTuning(
        llm_provider=mock_llm,
        prompt_repository=mock_prompt_repository,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestPersonaTuningBasic:
    """Test basic PersonaTuning functionality"""

    def test_initialization(self, persona_tuning):
        """Test tuner initializes correctly"""
        assert persona_tuning.name == "PersonaTuning"
        assert persona_tuning.phase.value == "P2"
        assert persona_tuning._enabled is True

    @pytest.mark.asyncio
    async def test_generate_insight_with_persona(self, persona_tuning):
        """Test generating insight with persona"""
        insight_data = {
            "topic": "AI Semiconductor Demand",
            "context": {
                "symbols": ["NVDA", "AMD"],
                "sentiment": "BULLISH",
                "key_points": ["Data center demand surge", "AI chip shortage"],
            },
        }

        result = await persona_tuning.generate_insight(insight_data)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "insight" in result.data


# ============================================================================
# Test: Sosumonkey Persona Style
# ============================================================================

class TestSosumonkeyPersona:
    """Test Sosumonkey persona characteristics"""

    def test_sosumonkey_persona_exists(self):
        """Test that SOSUMONKEY_PERSONA is defined"""
        assert SOSUMONKEY_PERSONA is not None
        assert isinstance(SOSUMONKEY_PERSONA, str)

    def test_sosumonkey_has_summary_section(self):
        """Test that Sosumonkey persona includes summary section"""
        assert "[요약]" in SOSUMONKEY_PERSONA or "**요약**" in SOSUMONKEY_PERSONA

    def test_sosumonkey_has_background_section(self):
        """Test that Sosumonkey persona includes background section"""
        assert "[배경]" in SOSUMONKEY_PERSONA or "**배경**" in SOSUMONKEY_PERSONA

    def test_sosumonkey_has_connection_section(self):
        """Test that Sosumonkey persona includes connection section"""
        assert "[연결]" in SOSUMONKEY_PERSONA or "**연결**" in SOSUMONKEY_PERSONA

    def test_sosumonkey_has_counterargument_section(self):
        """Test that Sosumonkey persona includes counterargument section"""
        assert "[반론]" in SOSUMONKEY_PERSONA or "**반론**" in SOSUMONKEY_PERSONA

    def test_sosumonkey_has_conclusion_section(self):
        """Test that Sosumonkey persona includes conclusion section"""
        assert "[종합]" in SOSUMONKEY_PERSONA or "**종합**" in SOSUMONKEY_PERSONA


# ============================================================================
# Test: Insight Generation Prompt V2
# ============================================================================

class TestInsightGenerationPromptV2:
    """Test INSIGHT_GENERATION_PROMPT_V2"""

    def test_prompt_v2_exists(self):
        """Test that INSIGHT_GENERATION_PROMPT_V2 is defined"""
        assert INSIGHT_GENERATION_PROMPT_V2 is not None
        assert isinstance(INSIGHT_GENERATION_PROMPT_V2, str)

    def test_prompt_v2_includes_persona(self):
        """Test that V2 prompt includes Sosumonkey persona"""
        assert "Sosumonkey" in INSIGHT_GENERATION_PROMPT_V2 or "소수몽키" in INSIGHT_GENERATION_PROMPT_V2

    def test_prompt_v2_has_structure(self):
        """Test that V2 prompt has clear structure"""
        # Should have sections for input data, output format
        assert "입력" in INSIGHT_GENERATION_PROMPT_V2 or "input" in INSIGHT_GENERATION_PROMPT_V2.lower()
        assert "출력" in INSIGHT_GENERATION_PROMPT_V2 or "output" in INSIGHT_GENERATION_PROMPT_V2.lower()


# ============================================================================
# Test: Style Validation
# ============================================================================

class TestStyleValidation:
    """Test style validation for LLM responses"""

    @pytest.mark.asyncio
    async def test_validate_summary_section(self, persona_tuning):
        """Test validation of summary section"""
        response = """**[요약]**
AI 반도체 테마가 강세입니다."""

        result = await persona_tuning.validate_style(response)

        assert result.success is True
        assert result.data["has_summary"] is True

    @pytest.mark.asyncio
    async def test_validate_connection_section(self, persona_tuning):
        """Test validation of connection section"""
        response = """**[연결]**
NVDA 실적이 좋았고, 이는 AI 칩 수요와 직결됩니다."""

        result = await persona_tuning.validate_style(response)

        assert result.success is True
        assert result.data["has_connection"] is True

    @pytest.mark.asyncio
    async def test_validate_counterargument_section(self, persona_tuning):
        """Test validation of counterargument section"""
        response = """**[반론]**
하지만 일부에서는 밸류에이션 우려를 제기합니다."""

        result = await persona_tuning.validate_style(response)

        assert result.success is True
        assert result.data["has_counterargument"] is True

    @pytest.mark.asyncio
    async def test_validate_complete_sosumonkey_style(self, persona_tuning):
        """Test validation of complete Sosumonkey style"""
        response = """**[요약]**
AI 반도체 테마가 강세입니다.

**[배경]**
데이터센터 수요 증가

**[연결]**
HBM 칩 가격 상승

**[반론]**
밸류에이션 우려

**[종합]**
단기 강세, 중기 조정"""

        result = await persona_tuning.validate_style(response)

        assert result.success is True
        assert result.data["style_match"] >= 0.8

    @pytest.mark.asyncio
    async def test_detect_incomplete_style(self, persona_tuning):
        """Test detection of incomplete Sosumonkey style"""
        response = "AI 반도체 테마가 강세입니다. NVDA가 상승 중입니다."

        result = await persona_tuning.validate_style(response)

        # Should have low style match
        assert result.data["style_match"] <= 0.5


# ============================================================================
# Test: Prompt Version Tracking
# ============================================================================

class TestPromptVersionTracking:
    """Test prompt version tracking"""

    def test_prompt_version_creation(self):
        """Test creating a PromptVersion"""
        version = PromptVersion(
            version_id=1,
            persona="SOSUMONKEY",
            template_content="Test template",
            created_at=datetime.now(),
        )

        assert version.version_id == 1
        assert version.persona == "SOSUMONKEY"

    def test_prompt_version_to_dict(self):
        """Test converting PromptVersion to dictionary"""
        version = PromptVersion(
            version_id=1,
            persona="SOSUMONKEY",
            template_content="Test template",
            created_at=datetime.now(),
        )

        version_dict = version.to_dict()

        assert isinstance(version_dict, dict)
        assert version_dict["persona"] == "SOSUMONKEY"

    @pytest.mark.asyncio
    async def test_save_prompt_version(self, persona_tuning):
        """Test saving a prompt version"""
        version = PromptVersion(
            version_id=1,
            persona="SOSUMONKEY",
            template_content="Updated template",
            created_at=datetime.now(),
        )

        result = await persona_tuning.save_prompt_version(version)

        assert result.success is True
        assert result.data["version_id"] == 1

    @pytest.mark.asyncio
    async def test_get_latest_version(self, persona_tuning):
        """Test getting latest prompt version"""
        result = await persona_tuning.get_latest_version("SOSUMONKEY")

        assert result.success is True
        assert "version" in result.data


# ============================================================================
# Test: Persona Style Enum
# ============================================================================

class TestPersonaStyle:
    """Test PersonaStyle enum"""

    def test_sosumonkey_style(self):
        """Test SOSUMONKEY persona style"""
        style = PersonaStyle.SOSUMONKEY
        assert style.value == "SOSUMONKEY"

    def test_analyst_style(self):
        """Test ANALYST persona style"""
        style = PersonaStyle.ANALYST
        assert style.value == "ANALYST"

    def test_trader_style(self):
        """Test TRADER persona style"""
        style = PersonaStyle.TRADER
        assert style.value == "TRADER"


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestPersonaTuningEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_insight_data(self, persona_tuning):
        """Test handling of empty insight data"""
        insight_data = {}

        result = await persona_tuning.generate_insight(insight_data)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, persona_tuning):
        """Test handling of LLM errors"""
        class ErrorLLM:
            async def complete_with_system(self, system_prompt, user_prompt, config=None):
                raise Exception("LLM Error")

        original_llm = persona_tuning.llm
        persona_tuning.llm = ErrorLLM()

        insight_data = {"topic": "Test"}

        result = await persona_tuning.generate_insight(insight_data)

        # Restore original
        persona_tuning.llm = original_llm

        # Should handle error gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_response_format(self, persona_tuning):
        """Test handling of invalid response format"""
        response = 12345  # Not a string

        result = await persona_tuning.validate_style(response)

        # Should handle gracefully
        assert result is not None


# ============================================================================
# Test: Style Score Calculation
# ============================================================================

class TestStyleScoreCalculation:
    """Test style score calculation"""

    @pytest.mark.asyncio
    async def test_full_score_for_complete_style(self, persona_tuning):
        """Test full score for complete Sosumonkey style"""
        response = """**[요약]**
Summary

**[배경]**
Background

**[연결]**
Connection

**[반론]**
Counterargument

**[종합]**
Conclusion"""

        result = await persona_tuning.validate_style(response)

        assert result.data["style_match"] >= 0.9

    @pytest.mark.asyncio
    async def test_partial_score_for_partial_style(self, persona_tuning):
        """Test partial score for partial Sosumonkey style"""
        response = """**[요약]**
Summary

**[배경]**
Background"""

        result = await persona_tuning.validate_style(response)

        # Should have partial score (2 out of 5 sections)
        assert 0.3 <= result.data["style_match"] <= 0.6


# ============================================================================
# Test: Insight Generation
# ============================================================================

class TestInsightGeneration:
    """Test insight generation with different personas"""

    @pytest.mark.asyncio
    async def test_generate_with_sosumonkey_persona(self, persona_tuning):
        """Test generating insight with Sosumonkey persona"""
        insight_data = {
            "topic": "Defense Budget Increase",
            "persona": "SOSUMONKEY",
        }

        result = await persona_tuning.generate_insight(insight_data)

        assert result.success is True
        assert "insight" in result.data

    @pytest.mark.asyncio
    async def test_generate_with_custom_context(self, persona_tuning):
        """Test generating insight with custom context"""
        insight_data = {
            "topic": "Tariff Policy",
            "context": {
                "sentiment": "BULLISH",
                "symbols": ["LMT", "RTX"],
                "key_points": ["Defense spending increase", "Geopolitical tensions"],
            },
        }

        result = await persona_tuning.generate_insight(insight_data)

        assert result.success is True


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
