"""
PM Agent MVP - Skill Handler
Wraps PMAgentMVP to provide Agent Skills interface.

Date: 2026-01-02
Phase: Skills Migration
"""

from typing import Dict, Any, Optional
from backend.ai.mvp.pm_agent_mvp import PMAgentMVP


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute PM Agent MVP final decision

    Args:
        context: {
            'symbol': str (required),
            'trader_opinion': dict (required),
            'risk_opinion': dict (required),
            'analyst_opinion': dict (required),
            'portfolio_state': dict (required),
            'correlation_data': dict (optional)
        }

    Returns:
        Final decision from PMAgentMVP
        {
            'final_decision': 'approve|reject|reduce_size|silence',
            'confidence': 0.0-1.0,
            'reasoning': str,
            'hard_rules_passed': bool,
            'recommended_action': str,
            ...
        }
    """
    # Validate required parameters
    symbol = context.get('symbol')
    trader_opinion = context.get('trader_opinion')
    risk_opinion = context.get('risk_opinion')
    analyst_opinion = context.get('analyst_opinion')
    portfolio_state = context.get('portfolio_state')

    if not all([symbol, trader_opinion, risk_opinion, analyst_opinion, portfolio_state]):
        return {
            'error': 'Missing required parameters (symbol, trader_opinion, risk_opinion, analyst_opinion, portfolio_state)',
            'agent': 'pm_mvp',
            'final_decision': 'reject',
            'confidence': 0.0
        }

    # Initialize agent
    agent = PMAgentMVP()

    # Execute final decision
    result = agent.make_final_decision(
        symbol=symbol,
        trader_opinion=trader_opinion,
        risk_opinion=risk_opinion,
        analyst_opinion=analyst_opinion,
        portfolio_state=portfolio_state,
        correlation_data=context.get('correlation_data')
    )

    return result


# Export
__all__ = ['execute', 'PMAgentMVP']
