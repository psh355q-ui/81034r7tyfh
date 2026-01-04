"""
War Room MVP Orchestrator - Skill Handler
Coordinates 3+1 agent deliberation with legacy system integration.

Date: 2026-01-02
Phase: Skills Migration
"""

from typing import Dict, Any, Optional
from backend.ai.mvp.war_room_mvp import WarRoomMVP

# Singleton instance
_war_room_instance = None


def get_war_room() -> WarRoomMVP:
    """Get or create War Room MVP singleton"""
    global _war_room_instance
    if _war_room_instance is None:
        _war_room_instance = WarRoomMVP()
    return _war_room_instance


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute War Room MVP deliberation

    Args:
        context: {
            'symbol': str (required),
            'action_context': str (optional, default='new_position'),
            'market_data': dict (required),
            'portfolio_state': dict (required),
            'additional_data': dict (optional)
        }

    Returns:
        Full deliberation result with final_decision, agent_opinions, etc.
        {
            'source': 'war_room_mvp',
            'symbol': str,
            'execution_mode': 'fast_track|deep_dive',
            'agent_opinions': {...},
            'pm_decision': {...},
            'final_decision': 'approve|reject|reduce_size|silence',
            'approved_params': {...},
            'processing_time_ms': int
        }
    """
    # Validate required parameters
    symbol = context.get('symbol')
    market_data = context.get('market_data')
    portfolio_state = context.get('portfolio_state')

    if not symbol:
        return {
            'error': 'Missing required parameter: symbol',
            'final_decision': 'reject'
        }

    if not market_data:
        return {
            'error': 'Missing required parameter: market_data',
            'final_decision': 'reject'
        }

    if not portfolio_state:
        return {
            'error': 'Missing required parameter: portfolio_state',
            'final_decision': 'reject'
        }

    # Get singleton instance
    war_room = get_war_room()

    # Execute deliberation (기존 WarRoomMVP.deliberate() 호출)
    result = await war_room.deliberate(
        symbol=symbol,
        action_context=context.get('action_context', 'new_position'),
        market_data=market_data,
        portfolio_state=portfolio_state,
        additional_data=context.get('additional_data')
    )

    return result


def invoke_legacy_war_room(symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    **NEW FUNCTION - 사용자 요구사항**

    MVP가 Legacy 8-Agent War Room을 호출할 수 있도록 지원

    사용 시나리오:
    - MVP 결과와 Legacy 결과 비교 (validation)
    - 중요한 결정에 대한 2차 검증
    - A/B testing

    Args:
        symbol: 종목 심볼
        context: 추가 컨텍스트 데이터 (market_data, portfolio_state 등)

    Returns:
        Legacy War Room debate 결과
        {
            'source': 'legacy_8_agent_war_room',
            'symbol': str,
            'votes': [...],
            'consensus': {...},
            'note': str
        }
    """
    # TODO: Legacy 8-Agent War Room 호출 구현
    # backend/ai/debate/ 폴더의 8개 agent를 순차 실행
    # 현재는 placeholder 반환

    return {
        'source': 'legacy_8_agent_war_room',
        'symbol': symbol,
        'note': 'Legacy system integration point - implementation pending',
        'status': 'placeholder',
        'context_received': list(context.keys())
    }


def get_info() -> Dict[str, Any]:
    """Get War Room MVP information"""
    war_room = get_war_room()
    return war_room.get_war_room_info()


def get_history(limit: int = 20) -> Dict[str, Any]:
    """
    Get decision history from War Room MVP

    Args:
        limit: Number of recent decisions to retrieve

    Returns:
        {
            'decisions': List[Dict],
            'total_count': int
        }
    """
    war_room = get_war_room()
    
    # WarRoomMVP에 decision_history 속성이 있는지 확인
    if hasattr(war_room, 'decision_history'):
        history = war_room.decision_history[-limit:]
        return {
            'decisions': history,
            'total_count': len(war_room.decision_history)
        }
    else:
        return {
            'decisions': [],
            'total_count': 0,
            'note': 'Decision history not available in current WarRoomMVP implementation'
        }


# Export all public functions
__all__ = ['execute', 'get_war_room', 'invoke_legacy_war_room', 'get_info', 'get_history']
