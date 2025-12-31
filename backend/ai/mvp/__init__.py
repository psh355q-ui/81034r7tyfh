"""
MVP Agents Module

Phase: MVP Consolidation
Date: 2025-12-31

MVP Agent Structure:
    - Trader Agent MVP (35% weight) - Attack
    - Risk Agent MVP (35% weight) - Defense + Position Sizing
    - Analyst Agent MVP (30% weight) - Information (News + Macro + Institutional + ChipWar)
    - PM Agent MVP - Final Decision (Hard Rules + Silence Policy)
    - War Room MVP - 3+1 Voting System

Improvement vs Legacy:
    - Agent count: 9 → 4 (67% reduction)
    - Expected cost reduction: ~67%
    - Expected speed improvement: ~67%
"""

from .trader_agent_mvp import TraderAgentMVP
from .risk_agent_mvp import RiskAgentMVP
from .analyst_agent_mvp import AnalystAgentMVP
from .pm_agent_mvp import PMAgentMVP
from .war_room_mvp import WarRoomMVP

__all__ = [
    'TraderAgentMVP',
    'RiskAgentMVP',
    'AnalystAgentMVP',
    'PMAgentMVP',
    'WarRoomMVP'
]

__version__ = '1.0.0'
__author__ = 'AI Trading System Team'
__description__ = 'MVP Consolidated Agents (3+1 Voting System)'
