"""
Deep Reasoning Module for AI Trading System

Features:
- 3-step Chain of Thought (CoT) reasoning
- Hidden beneficiary detection
- Knowledge graph integration
- Model-agnostic AI client

Author: AI Trading System
Date: 2025-11-27
"""

from .deep_reasoning import DeepReasoningStrategy, DeepReasoningResult, ReasoningStep
from .cot_prompts import PromptTemplate, PromptStyle, get_prompt_template, format_evidence_blocks

__all__ = [
    "DeepReasoningStrategy",
    "DeepReasoningResult",
    "ReasoningStep",
    "PromptTemplate",
    "PromptStyle",
    "get_prompt_template",
    "format_evidence_blocks",
]
