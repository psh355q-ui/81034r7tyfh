import pytest
from backend.ai.reasoning.models import ReasoningStep, MarketThesis

@pytest.mark.unit
def test_reasoning_step_creation():
    """Test ReasoningStep model creation."""
    step = ReasoningStep(
        step_number=1,
        premise="Test premise",
        inference="Test inference",
        conclusion="Test conclusion",
        confidence=0.8
    )
    assert step.step_number == 1
    assert step.confidence == 0.8

@pytest.mark.unit
def test_market_thesis_creation():
    """Test MarketThesis model creation."""
    thesis = MarketThesis(
        ticker="NVDA",
        direction="BULLISH",
        time_horizon="SWING",
        summary="Test summary",
        bull_case="Bull case",
        bear_case="Bear case",
        reasoning_trace=[],
        key_risks=["Risk 1"],
        catalysts=["Catalyst 1"],
        final_confidence_score=0.85
    )
    assert thesis.ticker == "NVDA"
    assert thesis.direction == "BULLISH"
    assert thesis.final_confidence_score == 0.85
