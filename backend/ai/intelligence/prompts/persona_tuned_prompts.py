"""
Persona-Tuned Prompts Component

Market Intelligence v2.0 - Phase 3, T3.3

This component creates prompts in the style of "Sosumonkey" with
two-stage conclusion, connecting threads, easy metaphors, data-driven
analysis, and opposing viewpoints.

Key Features:
1. SOSUMONKEY_PERSONA prompt template
2. INSIGHT_GENERATION_PROMPT_V2
3. Style validation (LLM response matches Sosumonkey style)
4. Prompt version tracking
5. Connect to prompt_versions table

Sosumonkey Style Characteristics:
- **[요약]**: Two-stage conclusion upfront
- **[배경]**: Background context and data
- **[연결]**: Connecting threads between facts
- **[반론]**: Opposing viewpoints considered
- **[종합]**: Final conclusion with implications

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re

from ..base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ...llm_providers import LLMProvider


logger = logging.getLogger(__name__)


# ============================================================================
# Sosumonkey Persona Template
# ============================================================================

SOSUMONKEY_PERSONA = """You are "Sosumonkey" (소수몽키), a Korean investment analyst known for clear, actionable market insights.

**Your Writing Style:**

1. **[요약]** (Summary): Start with a concise two-line conclusion
   - First line: Main thesis in one sentence
   - Second line: Key supporting fact or number

2. **[배경]** (Background): Provide 3-4 bullet points of context
   - Use data and specific numbers
   - Include recent market events
   - Keep it factual

3. **[연결]** (Connection): Show the logical thread
   - Connect facts to the thesis
   - Use phrases like "이미" (already), "~와 직결됩니다" (directly tied to ~)
   - Show cause-and-effect clearly

4. **[반론]** (Counterargument): Present opposing views
   - Start with "하지만" (however) or "일부에서는" (some argue)
   - Acknowledge valid concerns
   - Present balanced view

5. **[종합]** (Conclusion): Final takeaway with time horizon
   - Short-term vs long-term implications
   - Actionable guidance
   - Risk factors to watch

**Writing Guidelines:**
- Use simple, direct language
- Avoid jargon unless explaining it
- Always include specific numbers
- Keep paragraphs short (2-3 sentences)
- Use Korean format for numbers (e.g., "8% 상승", "15% 오름")
- Bold key numbers and themes
"""

INSIGHT_GENERATION_PROMPT_V2 = f"""{SOSUMONKEY_PERSONA}

**Task**: Generate a market insight following the Sosumonkey style above.

**Input Data**:
- Topic: {{topic}}
- Sentiment: {{sentiment}}
- Symbols: {{symbols}}
- Key Points: {{key_points}}
- Context: {{context}}

**Output Format**:
{SOSUMONKEY_PERSONA}

Generate the insight now:
"""


# ============================================================================
# Data Models
# ============================================================================

class PersonaStyle(Enum):
    """Persona styles for insight generation"""
    SOSUMONKEY = "SOSUMONKEY"  # Korean analyst style
    ANALYST = "ANALYST"  # Traditional analyst style
    TRADER = "TRADER"  # Active trader style


@dataclass
class PromptVersion:
    """
    Version tracking for prompt templates

    Attributes:
        version_id: Unique version identifier
        persona: Persona style
        template_content: Prompt template content
        created_at: Creation timestamp
        changes: Description of changes from previous version
    """
    version_id: int
    persona: str
    template_content: str
    created_at: datetime
    changes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "version_id": self.version_id,
            "persona": self.persona,
            "template_content": self.template_content,
            "created_at": self.created_at.isoformat(),
            "changes": self.changes,
        }


# ============================================================================
# Main Component
# ============================================================================

class PersonaTuning(BaseIntelligence):
    """
    Persona Tuning Component

    Creates prompts in the style of "Sosumonkey" and validates
    that LLM responses match the expected style.

    Key Features:
    1. Persona-based prompt generation
    2. Style validation for LLM responses
    3. Prompt version tracking
    4. Support for multiple persona styles

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.prompts.persona_tuned_prompts import PersonaTuning

        llm = get_llm_provider()
        tuner = PersonaTuning(llm_provider=llm)

        # Generate insight with Sosumonkey style
        result = await tuner.generate_insight({
            "topic": "AI Semiconductor Demand",
            "sentiment": "BULLISH",
            "symbols": ["NVDA", "AMD"],
        })

        # Validate response style
        validation = await tuner.validate_style(result.data["insight"])
    """

    # Style sections to validate
    STYLE_SECTIONS = {
        "summary": ["**[요약]**", "[요약]"],
        "background": ["**[배경]**", "[배경]"],
        "connection": ["**[연결]**", "[연결]"],
        "counterargument": ["**[반론]**", "[반론]"],
        "conclusion": ["**[종합]**", "[종합]"],
    }

    def __init__(
        self,
        llm_provider: LLMProvider,
        prompt_repository: Optional[Any] = None,
    ):
        """
        Initialize PersonaTuning

        Args:
            llm_provider: LLM Provider instance
            prompt_repository: Prompt version repository (optional)
        """
        super().__init__(
            name="PersonaTuning",
            phase=IntelligencePhase.P2,
        )

        self.llm = llm_provider
        self.prompt_repository = prompt_repository

        # Statistics
        self._generation_count = 0
        self._validation_count = 0
        self._version_count = 0

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Generate insight with persona (main entry point)

        Args:
            data: Insight generation data

        Returns:
            IntelligenceResult: Generated insight
        """
        return await self.generate_insight(data)

    async def generate_insight(
        self,
        data: Dict[str, Any],
    ) -> IntelligenceResult:
        """
        Generate insight with persona styling

        Args:
            data: Generation data with:
                - topic: Insight topic
                - sentiment: BULLISH/BEARISH/NEUTRAL
                - symbols: Related symbols (optional)
                - key_points: Key points to cover (optional)
                - context: Additional context (optional)
                - persona: Persona style (default: SOSUMONKEY)

        Returns:
            IntelligenceResult: Generated insight
        """
        try:
            topic = data.get("topic", "")
            sentiment = data.get("sentiment", "NEUTRAL")
            symbols = data.get("symbols", [])
            key_points = data.get("key_points", [])
            context = data.get("context", {})
            persona = data.get("persona", "SOSUMONKEY")

            # Build prompt from template
            prompt = self._build_prompt(
                topic=topic,
                sentiment=sentiment,
                symbols=symbols,
                key_points=key_points,
                context=context,
                persona=persona,
            )

            # Generate insight with LLM
            system_prompt = SOSUMONKEY_PERSONA if persona == "SOSUMONKEY" else ""
            response = await self.llm.complete_with_system(system_prompt, prompt)

            insight = response.content

            # Update statistics
            self._generation_count += 1

            return self.create_result(
                success=True,
                data={
                    "stage": "insight_generation",
                    "insight": insight,
                    "persona": persona,
                    "topic": topic,
                },
                reasoning=f"Generated insight for {topic} using {persona} persona",
            )

        except Exception as e:
            logger.error(f"Insight generation error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "insight_generation"},
            )
            result.add_error(f"Generation error: {str(e)}")
            return result

    async def validate_style(
        self,
        response: str,
        expected_style: str = "SOSUMONKEY",
    ) -> IntelligenceResult:
        """
        Validate that LLM response matches expected style

        Args:
            response: LLM response to validate
            expected_style: Expected persona style

        Returns:
            IntelligenceResult: Validation result with style match score
        """
        try:
            self._validation_count += 1

            # Check for style sections
            section_scores = {}
            for section_name, markers in self.STYLE_SECTIONS.items():
                section_scores[f"has_{section_name}"] = any(
                    marker in response for marker in markers
                )

            # Calculate overall style match
            sections_present = sum(section_scores.values())
            total_sections = len(self.STYLE_SECTIONS)
            style_match = sections_present / total_sections

            return self.create_result(
                success=True,
                data={
                    "stage": "style_validation",
                    "style_match": style_match,
                    "expected_style": expected_style,
                    **section_scores,
                },
                reasoning=f"Style match: {style_match:.1%} ({sections_present}/{total_sections} sections)",
            )

        except Exception as e:
            logger.error(f"Style validation error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "style_validation"},
            )
            result.add_error(f"Validation error: {str(e)}")
            return result

    async def save_prompt_version(
        self,
        version: PromptVersion,
    ) -> IntelligenceResult:
        """
        Save a prompt version

        Args:
            version: Prompt version to save

        Returns:
            IntelligenceResult: Save result
        """
        try:
            if self.prompt_repository:
                saved = await self.prompt_repository.save_prompt_version(version)
                if saved:
                    self._version_count += 1
            else:
                # Mock save
                self._version_count += 1

            return self.create_result(
                success=True,
                data={
                    "stage": "save_version",
                    "version_id": version.version_id,
                    "persona": version.persona,
                },
                reasoning=f"Saved prompt version {version.version_id} for {version.persona}",
            )

        except Exception as e:
            logger.error(f"Save version error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "save_version"},
            )
            result.add_error(f"Save error: {str(e)}")
            return result

    async def get_latest_version(
        self,
        persona: str,
    ) -> IntelligenceResult:
        """
        Get latest prompt version for a persona

        Args:
            persona: Persona style

        Returns:
            IntelligenceResult: Latest version
        """
        try:
            if self.prompt_repository:
                version = await self.prompt_repository.get_latest_version(persona)
            else:
                # Mock version
                version = PromptVersion(
                    version_id=1,
                    persona=persona,
                    template_content=SOSUMONKEY_PERSONA,
                    created_at=datetime.now(),
                )

            return self.create_result(
                success=True,
                data={
                    "stage": "get_version",
                    "version": version.to_dict(),
                },
                reasoning=f"Retrieved version {version.version_id} for {persona}",
            )

        except Exception as e:
            logger.error(f"Get version error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "get_version"},
            )
            result.add_error(f"Get error: {str(e)}")
            return result

    def _build_prompt(
        self,
        topic: str,
        sentiment: str,
        symbols: List[str],
        key_points: List[str],
        context: Dict[str, Any],
        persona: str,
    ) -> str:
        """Build prompt from template"""
        # Format the context
        symbols_str = ", ".join(symbols) if symbols else "N/A"
        key_points_str = "\n".join(f"- {point}" for point in key_points) if key_points else "N/A"
        context_str = "\n".join(f"{k}: {v}" for k, v in context.items()) if context else "N/A"

        # Use V2 prompt template
        prompt = INSIGHT_GENERATION_PROMPT_V2.replace("{{topic}}", topic)
        prompt = prompt.replace("{{sentiment}}", sentiment)
        prompt = prompt.replace("{{symbols}}", symbols_str)
        prompt = prompt.replace("{{key_points}}", key_points_str)
        prompt = prompt.replace("{{context}}", context_str)

        return prompt

    def get_statistics(self) -> Dict[str, Any]:
        """Get persona tuning statistics"""
        return {
            "total_generations": self._generation_count,
            "total_validations": self._validation_count,
            "total_versions": self._version_count,
        }


# ============================================================================
# Factory function
# ============================================================================

def create_persona_tuning(
    llm_provider: Optional[LLMProvider] = None,
    prompt_repository: Optional[Any] = None,
) -> PersonaTuning:
    """
    Create PersonaTuning instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        prompt_repository: Prompt version repository

    Returns:
        PersonaTuning: Configured tuner instance
    """
    if llm_provider is None:
        from ...llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return PersonaTuning(
        llm_provider=llm_provider,
        prompt_repository=prompt_repository,
    )
