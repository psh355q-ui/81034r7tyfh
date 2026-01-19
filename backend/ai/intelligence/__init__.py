"""
Market Intelligence v2.0 Module

AI 트레이딩 시스템을 위한 지능형 시장 분석 모듈입니다.
뉴스에서 팩트와 내러티브를 분리하고, 시장 가격과 교차 검증합니다.

Components (11개):
    P0 (핵심):
        - NewsFilter: 2단계 필터링 (비용 최적화)
        - NarrativeStateEngine: 팩트 vs 내러티브 분리
        - FactChecker: 수치 검증 (Hallucination 방지)
        - MarketConfirmation: 가격 교차 검증

    P1 (고급):
        - NarrativeFatigue: 테마 과열 탐지
        - ContrarySignal: 쏠림 경고
        - HorizonTagger: 시간축 분리
        - ChartGenerator: 시각화 자동화

    P2 (학습):
        - PolicyFeasibility: 정책 실현 확률
        - InsightPostMortem: 사후 분석 및 학습
        - PersonaTuning: 소수몽키 톤앤매너

Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

from .base import BaseIntelligence, IntelligenceResult

__all__ = [
    "BaseIntelligence",
    "IntelligenceResult",
]

# P0 Components (will be added in Phase 1)
# from .news_filter import NewsFilter
# from .narrative_state_engine import NarrativeStateEngine
# from .fact_checker import FactChecker
# from .market_confirmation import MarketConfirmationEngine

# P1 Components (will be added in Phase 2)
# from .narrative_fatigue import NarrativeFatigueDetector
# from .contrary_signal import ContrarySignalDetector
# from .horizon_tagger import HorizonTagger
# from .chart_generator import ChartGenerator

# P2 Components (will be added in Phase 3)
# from .policy_feasibility import PolicyFeasibilityAnalyzer
# from .insight_postmortem import InsightPostMortemEngine
# from .prompts.persona_tuned_prompts import SOSUMONKEY_PERSONA
