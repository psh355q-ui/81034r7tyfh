"""
Analyst Agent MVP - Skill Handler
Wraps AnalystAgentMVP to provide Agent Skills interface.

Date: 2026-01-02
Phase: Skills Migration
"""

from typing import Dict, Any, List, Optional
from backend.ai.mvp.analyst_agent_mvp import AnalystAgentMVP


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Analyst Agent MVP analysis

    Args:
        context: {
            'symbol': str (required),
            'news_articles': List[dict] (optional),
            'macro_indicators': dict (optional),
            'institutional_data': dict (optional),
            'chipwar_events': List[dict] (optional),
            'price_context': dict (optional)
        }

    Returns:
        Analysis result from AnalystAgentMVP
        {
            'action': 'support|oppose|neutral',
            'confidence': 0.0-1.0,
            'reasoning': str,
            'information_score': float,
            'key_catalysts': List[str],
            'red_flags': List[str],
            ...
        }
    """
    # Validate required parameters
    symbol = context.get('symbol')
    if not symbol:
        return {
            'error': 'Missing required parameter: symbol',
            'agent': 'analyst_mvp',
            'action': 'neutral',
            'confidence': 0.0
        }

    # Initialize agent
    agent = AnalystAgentMVP()

    # Execute analysis
    result = agent.analyze(
        symbol=symbol,
        news_articles=context.get('news_articles'),
        macro_indicators=context.get('macro_indicators'),
        institutional_data=context.get('institutional_data'),
        chipwar_events=context.get('chipwar_events'),
        price_context=context.get('price_context')
    )

    return result


# Export
__all__ = ['execute', 'AnalystAgentMVP']
