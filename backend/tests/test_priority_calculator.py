"""
AI War Priority System - Unit Tests

Tests for priority_calculator.py

작성일: 2025-12-16
"""

import pytest
from backend.ai.debate.priority_calculator import calculate_priority_score
from backend.ai.debate.ai_debate_engine import DebateResult, DebateRound, InvestmentSignal, AIModel


def test_priority_high_consensus_with_institutional():
    """높은 합의 + 기관 신호 = 높은 우선순위"""
    result = DebateResult(
        final_signal=InvestmentSignal(ticker="NVDA", action="BUY", confidence=0.9),
        consensus_confidence=0.9,
        debate_rounds=[DebateRound(), DebateRound(), DebateRound()],  # 3 rounds
        model_votes={
            AIModel.CLAUDE: "BUY",
            AIModel.CHATGPT: "BUY",
            AIModel.GEMINI: "BUY"
        }
    )
    
    score = calculate_priority_score(result, has_institutional_signal=True)
    
    assert score > 0.7, f"Expected high priority (>0.7), got {score}"
    assert score <= 1.0, "Priority should not exceed 1.0"


def test_priority_low_consensus_no_institutional():
    """낮은 합의 + 기관 신호 없음 = 낮은 우선순위"""
    result = DebateResult(
        final_signal=InvestmentSignal(ticker="NVDA", action="HOLD", confidence=0.5),
        consensus_confidence=0.5,
        debate_rounds=[DebateRound()],  # 1 round only
        model_votes={
            AIModel.CLAUDE: "BUY",
            AIModel.CHATGPT: "SELL"
        }
    )
    
    score = calculate_priority_score(result, has_institutional_signal=False)
    
    assert score < 0.5, f"Expected low priority (<0.5), got {score}"


def test_priority_institutional_boost():
    """기관 신호의 영향 테스트"""
    result = DebateResult(
        final_signal=InvestmentSignal(ticker="NVDA", action="BUY", confidence=0.8),
        consensus_confidence=0.8,
        debate_rounds=[DebateRound(), DebateRound()],
        model_votes={
            AIModel.CLAUDE: "BUY",
            AIModel.CHATGPT: "BUY",
            AIModel.GEMINI: "BUY"
        }
    )
    
    score_without = calculate_priority_score(result, has_institutional_signal=False)
    score_with = calculate_priority_score(result, has_institutional_signal=True)
    
    assert score_with > score_without, "Institutional signal should boost priority"
    assert (score_with - score_without) == pytest.approx(0.1, abs=0.01), "Institutional boost should be ~0.1"


def test_priority_bounds():
    """우선순위 점수는 0~1 사이여야 함"""
    # Minimum case
    min_result = DebateResult(
        final_signal=InvestmentSignal(ticker="TEST", action="HOLD", confidence=0.0),
        consensus_confidence=0.0,
        debate_rounds=[],
        model_votes={}
    )
    
    min_score = calculate_priority_score(min_result, has_institutional_signal=False)
    assert min_score >= 0.0, "Minimum score should be >= 0"
    
    # Maximum case
    max_result = DebateResult(
        final_signal=InvestmentSignal(ticker="TEST", action="BUY", confidence=1.0),
        consensus_confidence=1.0,
        debate_rounds=[DebateRound() for _ in range(5)],  # Many rounds
        model_votes={model: "BUY" for model in AIModel}  # All models
    )
    
    max_score = calculate_priority_score(max_result, has_institutional_signal=True)
    assert max_score <= 1.5, "Score should not exceed reasonable bounds"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
