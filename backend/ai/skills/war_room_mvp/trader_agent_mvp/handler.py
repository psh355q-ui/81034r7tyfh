"""
Trader Agent MVP - Skill Handler
Wraps TraderAgentMVP to provide Agent Skills interface.

Date: 2026-01-02
Phase: Skills Migration
"""

from typing import Dict, Any
from backend.ai.mvp.trader_agent_mvp import TraderAgentMVP


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Trader Agent MVP analysis

    Args:
        context: {
            'symbol': str (required),
            'price_data': dict,
            'technical_data': dict (optional),
            'chipwar_events': list (optional),
            'market_context': dict (optional)
        }

    Returns:
        Analysis result from TraderAgentMVP
        {
            'action': 'buy|sell|hold|pass',
            'confidence': 0.0-1.0,
            'reasoning': str,
            'opportunity_score': float,
            ...
        }
    """
    # Validate required parameters
    symbol = context.get('symbol')
    if not symbol:
        return {
            'error': 'Missing required parameter: symbol',
            'agent': 'trader_mvp',
            'action': 'pass',
            'confidence': 0.0
        }

    # Initialize agent (기존 MVP 클래스 그대로 사용)
    agent = TraderAgentMVP()

    # Execute analysis (기존 analyze() 메서드 호출)
    result = agent.analyze(
        symbol=symbol,
        price_data=context.get('price_data', {}),
        technical_data=context.get('technical_data'),
        chipwar_events=context.get('chipwar_events'),
        market_context=context.get('market_context')
    )

    return result


# 직접 import도 가능하도록 export
__all__ = ['execute', 'TraderAgentMVP']
