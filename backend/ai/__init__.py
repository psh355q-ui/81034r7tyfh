"""
AI Module

This module contains AI clients and trading agents.

Multi-AI System:
- Claude Haiku: Investment analysis and trading decisions
- Google Gemini: Risk screening and filtering
- ChatGPT-4o mini: Market regime detection
"""

from .claude_client import ClaudeClient
from .gemini_client import GeminiClient
from .chatgpt_client import ChatGPTClient
from .trading_agent import TradingAgent
from .failover_manager import FailoverManager, failover_manager

__all__ = [
    "ClaudeClient",
    "GeminiClient",
    "ChatGPTClient",
    "TradingAgent",
    "FailoverManager",
    "failover_manager",
]
