"""
Risk Agent MVP - Skill Handler
Wraps RiskAgentMVP to provide Agent Skills interface.

Date: 2026-01-02
Phase: Skills Migration
"""

from typing import Dict, Any
from backend.ai.mvp.risk_agent_mvp import RiskAgentMVP


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Risk Agent MVP analysis

    Args:
        context: {
            'symbol': str (required),
            'price_data': dict,
            'trader_opinion': dict (optional),
            'market_data': dict (optional),
            'dividend_info': dict (optional),
            'portfolio_context': dict (optional)
        }

    Returns:
        Analysis result from RiskAgentMVP
        {
            'action': 'approve|reject|reduce_size',
            'confidence': 0.0-1.0,
            'reasoning': str,
            'position_size': float,
            'risk_level': str,
            ...
        }
    """
    # Validate required parameters
    symbol = context.get('symbol')
    if not symbol:
        return {
            'error': 'Missing required parameter: symbol',
            'agent': 'risk_mvp',
            'action': 'reject',
            'confidence': 0.0
        }

    # Initialize agent
    agent = RiskAgentMVP()

    # Execute analysis
    result = agent.analyze(
        symbol=symbol,
        price_data=context.get('price_data', {}),
        trader_opinion=context.get('trader_opinion'),
        market_data=context.get('market_data'),
        dividend_info=context.get('dividend_info'),
        portfolio_context=context.get('portfolio_context')
    )

    return result


# Export
__all__ = ['execute', 'RiskAgentMVP']
