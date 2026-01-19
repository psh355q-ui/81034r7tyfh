"""
Intelligence Prompts Module

This module contains prompt templates and persona tuning for
the Market Intelligence v2.0 system.
"""

from .persona_tuned_prompts import (
    PersonaTuning,
    PersonaStyle,
    PromptVersion,
    SOSUMONKEY_PERSONA,
    INSIGHT_GENERATION_PROMPT_V2,
    create_persona_tuning,
)

__all__ = [
    "PersonaTuning",
    "PersonaStyle",
    "PromptVersion",
    "SOSUMONKEY_PERSONA",
    "INSIGHT_GENERATION_PROMPT_V2",
    "create_persona_tuning",
]
