"""
NarrativeStateEngine Tests

Market Intelligence v2.0 - Phase 1, T1.2

Tests for the Fact/Narrative separation engine that tracks market narratives through
their lifecycle: EMERGING → ACCELERATING → CONSENSUS → FATIGUED → REVERSING

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from backend.ai.intelligence.narrative_state_engine import (
    NarrativeStateEngine,
    NarrativePhase,
    NarrativeState,
)
from backend.ai.intelligence.base import IntelligenceResult
from backend.ai.llm_providers import LLMProvider


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Mock LLM provider for testing"""
    class MockLLM:
        # State to track call count for different responses
        _call_count = 0

        async def complete_with_system(self, system_prompt: str, user_prompt: str, config=None):
            from backend.ai.llm_providers import LLMResponse, ModelProvider

            self._call_count += 1

            # Check if this is a shift detection request by examining system prompt
            is_shift_detection = "shift" in system_prompt.lower()

            # Simulate narrative analysis response
            content = """{
    "fact_layer": "Samsung Electronics reported Q4 2024 earnings: KRW 77.2 trillion revenue, operating profit KRW 6.5 trillion. Revenue increased 12% YoY driven by memory chip demand.",
    "narrative_layer": "AI chip boom continues to power Samsung's earnings recovery, with memory prices expected to rise further in 2025 due to generative AI demand.",
    "phase": "ACCELERATING",
    "confidence": 0.85,
    "evidence": ["Revenue beat expectations", "Memory prices rising", "AI demand strong"]
}"""

            if is_shift_detection:
                # Shift detection response based on user prompt content
                prompt_lower = user_prompt.lower()
                if "emerging" in prompt_lower and ("accelerating" in prompt_lower or ("ai chip" in prompt_lower and "300%" in prompt_lower)):
                    content = """{
    "shift_detected": true,
    "from_phase": "EMERGING",
    "to_phase": "ACCELERATING",
    "reasoning": "Major tech companies significantly increasing AI chip orders indicates accelerating momentum.",
    "confidence": 0.85
}"""
                elif "accelerating" in prompt_lower and ("consensus" in prompt_lower or ("fed meeting" in prompt_lower and "confirm" in prompt_lower)):
                    content = """{
    "shift_detected": true,
    "from_phase": "ACCELERATING",
    "to_phase": "CONSENSUS",
    "reasoning": "Fed minutes confirm rate cut plans with full market pricing indicates consensus reached.",
    "confidence": 0.90
}"""
                elif "consensus" in prompt_lower and ("fatigued" in prompt_lower or ("ai stocks" in prompt_lower and "slide" in prompt_lower)):
                    content = """{
    "shift_detected": true,
    "from_phase": "CONSENSUS",
    "to_phase": "FATIGUED",
    "reasoning": "AI stocks declining despite strong earnings with investor fatigue and valuation concerns.",
    "confidence": 0.80
}"""
                elif "fatigued" in prompt_lower and ("reversing" in prompt_lower or ("traditional automakers" in prompt_lower and "overtake" in prompt_lower)):
                    content = """{
    "shift_detected": true,
    "from_phase": "FATIGUED",
    "to_phase": "REVERSING",
    "reasoning": "Traditional automakers gaining market share while EV companies struggle suggests narrative reversal.",
    "confidence": 0.85
}"""
                else:
                    # No shift detected
                    content = """{
    "shift_detected": false,
    "from_phase": "",
    "to_phase": "",
    "reasoning": "Narrative remains consistent with previous assessment.",
    "confidence": 0.70
}"""
            else:
                # Regular narrative analysis response
                # Customize response based on user prompt content
                prompt_lower = user_prompt.lower()

                if "rumor" in prompt_lower or "ar glasses" in prompt_lower:
                    content = """{
    "fact_layer": "Industry sources suggest Apple is developing AR glasses with new display technology.",
    "narrative_layer": "Apple AR glasses could be the next major product category, potentially launching in 2026.",
    "phase": "EMERGING",
    "confidence": 0.75,
    "evidence": ["Industry rumors", "Early development reports"]
}"""
                elif "federal reserve" in prompt_lower or ("fed" in prompt_lower and "rate cut" in prompt_lower) or "unanimously" in prompt_lower:
                    content = """{
    "fact_layer": "Federal Reserve officials have indicated interest rate cuts are likely in 2025 as inflation cools.",
    "narrative_layer": "Fed rate cut narrative has reached full market consensus with expectations fully priced in.",
    "phase": "CONSENSUS",
    "confidence": 0.90,
    "evidence": ["Official Fed statements", "Market pricing"]
}"""
                elif "fatigue" in prompt_lower or "hundreds of ai" in prompt_lower or "ai startup" in prompt_lower:
                    content = """{
    "fact_layer": "Another AI startup announced funding, adding to hundreds of AI companies that have raised capital.",
    "narrative_layer": "AI startup funding frenzy is showing signs of saturation as investors become more selective.",
    "phase": "FATIGUED",
    "confidence": 0.80,
    "evidence": ["Increasing selectivity", "Market saturation signals"]
}"""
                elif "recession fears fade" in prompt_lower or "contrary" in prompt_lower:
                    content = """{
    "fact_layer": "Latest employment report shows unemployment at 3.7% with strong labor market indicators.",
    "narrative_layer": "Recession fears are reversing as economic data shows continued growth rather than contraction.",
    "phase": "REVERSING",
    "confidence": 0.85,
    "evidence": ["Strong jobs data", "GDP growth indicators"]
}"""

            return LLMResponse(
                content=content,
                model="mock-model",
                provider=ModelProvider.MOCK,
                tokens_used=150,
                latency_ms=100,
            )

        def create_stage1_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK, max_tokens=100)

        def create_stage2_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK, max_tokens=2000)

    return MockLLM()


@pytest.fixture
def engine(mock_llm):
    """Create NarrativeStateEngine instance"""
    return NarrativeStateEngine(llm_provider=mock_llm)


@pytest.fixture
def sample_article():
    """Sample news article for testing"""
    return {
        "title": "Samsung Q4 Earnings Beat Estimates on AI Chip Demand",
        "content": "Samsung Electronics reported better-than-expected quarterly earnings on Friday, driven by strong demand for memory chips used in artificial intelligence applications. The company said operating profit rose to 6.5 trillion won ($4.8 billion) in the October-December period, beating the 5.9 trillion won average of analyst estimates. Revenue increased 12% year-over-year to 77.2 trillion won.",
        "source": "Reuters",
        "published_date": "2025-01-19T10:00:00Z",
        "symbols": ["005930.KS"],
    }


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestNarrativeStateEngineBasic:
    """Test basic NarrativeStateEngine functionality"""

    def test_initialization(self, engine):
        """Test engine initializes correctly"""
        assert engine.name == "NarrativeStateEngine"
        assert engine.phase.value == "P0"
        assert engine._enabled is True

    @pytest.mark.asyncio
    async def test_analyze_news_returns_valid_result(self, engine, sample_article):
        """Test analyze_news returns valid IntelligenceResult"""
        result = await engine.analyze_news(sample_article)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "fact_layer" in result.data
        assert "narrative_layer" in result.data
        assert "phase" in result.data
        assert "confidence" in result.data

    @pytest.mark.asyncio
    async def test_fact_narrative_separation(self, engine, sample_article):
        """Test fact and narrative layers are properly separated"""
        result = await engine.analyze_news(sample_article)

        fact_layer = result.data["fact_layer"]
        narrative_layer = result.data["narrative_layer"]

        # Fact layer should contain concrete data
        assert fact_layer is not None
        assert len(fact_layer) > 0
        assert "77.2 trillion" in fact_layer or "77.2" in fact_layer

        # Narrative layer should contain interpretation
        assert narrative_layer is not None
        assert len(narrative_layer) > 0
        assert any(word in narrative_layer.lower() for word in ["ai", "boom", "recovery"])

    @pytest.mark.asyncio
    async def test_phase_detection(self, engine, sample_article):
        """Test narrative phase is correctly detected"""
        result = await engine.analyze_news(sample_article)

        phase = result.data["phase"]
        assert phase in [p.value for p in NarrativePhase]
        # Default mock returns ACCELERATING
        assert phase == "ACCELERATING"


# ============================================================================
# Test: Narrative Phase Tracking
# ============================================================================

class TestNarrativePhaseTracking:
    """Test narrative phase detection and transitions"""

    @pytest.mark.asyncio
    async def test_emerging_phase_detection(self, engine):
        """Test EMERGING phase detection for new topics"""
        article = {
            "title": "Rumors: Apple developing AR glasses with new display technology",
            "content": "Industry sources suggest Apple is secretly developing augmented reality glasses that could launch as early as 2026. The project is said to use breakthrough display technology.",
            "source": "TechRumor",
            "published_date": "2025-01-19T10:00:00Z",
        }

        # Mock would return EMERGING for this
        result = await engine.analyze_news(article)

        assert result.data["phase"] == "EMERGING"
        assert result.data["confidence"] >= 0.0

    @pytest.mark.asyncio
    async def test_consenus_phase_detection(self, engine):
        """Test CONSENSUS phase detection for widely accepted narratives"""
        article = {
            "title": "Fed Signals Rate Cuts Coming in 2025",
            "content": "Federal Reserve officials have unanimously indicated that interest rate cuts are likely in 2025 as inflation continues to cool toward the 2% target. Markets have fully priced in expected cuts.",
            "source": "Bloomberg",
            "published_date": "2025-01-19T10:00:00Z",
        }

        # Mock would return CONSENSUS
        result = await engine.analyze_news(article)

        assert result.data["phase"] == "CONSENSUS"

    @pytest.mark.asyncio
    async def test_fatigued_phase_detection(self, engine):
        """Test FATIGUED phase detection for overplayed narratives"""
        article = {
            "title": "Yet Another AI Startup Raises Funding at Billion Dollar Valuation",
            "content": "Another AI startup announced funding today, adding to the hundreds of AI companies that have raised capital in the past year. Investors are becoming more selective.",
            "source": "TechNews",
            "published_date": "2025-01-19T10:00:00Z",
        }

        # Mock would return FATIGUED
        result = await engine.analyze_news(article)

        assert result.data["phase"] == "FATIGUED"

    @pytest.mark.asyncio
    async def test_reversing_phase_detection(self, engine):
        """Test REVERSING phase detection when narrative breaks down"""
        article = {
            "title": "Recession Fears Fade as Jobs Data Shows Strong Labor Market",
            "content": "Contrary to recent recession fears, the latest employment report shows the labor market remains robust with unemployment at 3.7%. Economic indicators suggest growth, not contraction.",
            "source": "Financial Times",
            "published_date": "2025-01-19T10:00:00Z",
        }

        # Mock would return REVERSING
        result = await engine.analyze_news(article)

        assert result.data["phase"] == "REVERSING"


# ============================================================================
# Test: Narrative Shift Detection
# ============================================================================

class TestNarrativeShiftDetection:
    """Test narrative shift detection capabilities"""

    @pytest.mark.asyncio
    async def test_detect_narrative_shift_emerging_to_accelerating(self, mock_llm):
        """Test detecting shift from EMERGING to ACCELERATING"""
        engine = NarrativeStateEngine(llm_provider=mock_llm)

        previous_state = NarrativeState(
            topic="AI Semiconductor Boom",
            fact_layer="Initial reports of AI chip demand increase",
            narrative_layer="Early signs of AI-driven semiconductor cycle",
            phase=NarrativePhase.EMERGING,
            confidence=0.6,
            evidence_count=5,
            last_updated=datetime.now() - timedelta(days=7),
        )

        new_article = {
            "title": "Major Tech Companies Increase AI Chip Orders by 300%",
            "content": "Amazon, Google, and Microsoft have all significantly increased their orders for AI chips in Q4, signaling accelerating demand for datacenter AI infrastructure.",
            "source": "WSJ",
            "published_date": "2025-01-19T10:00:00Z",
        }

        shift_detected = await engine.detect_narrative_shift(previous_state, new_article)

        assert shift_detected  # Truthy check (not is True)
        assert shift_detected["from_phase"] == "EMERGING"
        assert shift_detected["to_phase"] == "ACCELERATING"

    @pytest.mark.asyncio
    async def test_detect_narrative_shift_accelerating_to_consensus(self, mock_llm):
        """Test detecting shift from ACCELERATING to CONSENSUS"""
        engine = NarrativeStateEngine(llm_provider=mock_llm)

        previous_state = NarrativeState(
            topic="Fed Rate Cuts",
            fact_layer="Fed officials signal rate cuts possible in 2025",
            narrative_layer="Market expectations building for rate cuts",
            phase=NarrativePhase.ACCELERATING,
            confidence=0.75,
            evidence_count=15,
            last_updated=datetime.now() - timedelta(days=3),
        )

        new_article = {
            "title": "Fed Meeting Minutes Confirm Rate Cut Plans, Markets Rally",
            "content": "The Federal Reserve's latest meeting minutes confirm that rate cuts are planned for 2025. All major market indices rallied on the news, with rate cut expectations now fully priced in.",
            "source": "Reuters",
            "published_date": "2025-01-19T10:00:00Z",
        }

        shift_detected = await engine.detect_narrative_shift(previous_state, new_article)

        assert shift_detected  # Truthy check (not is True)
        assert shift_detected["from_phase"] == "ACCELERATING"
        assert shift_detected["to_phase"] == "CONSENSUS"

    @pytest.mark.asyncio
    async def test_detect_narrative_shift_consensus_to_fatigued(self, mock_llm):
        """Test detecting shift from CONSENSUS to FATIGUED"""
        engine = NarrativeStateEngine(llm_provider=mock_llm)

        previous_state = NarrativeState(
            topic="AI Trade",
            fact_layer="AI companies reporting strong earnings",
            narrative_layer="AI boom driving market gains",
            phase=NarrativePhase.CONSENSUS,
            confidence=0.9,
            evidence_count=50,
            last_updated=datetime.now() - timedelta(days=14),
        )

        new_article = {
            "title": "AI Stocks Slide Despite Strong Earnings, Investors Cite 'AI Fatigue'",
            "content": "Even with strong earnings reports, AI-related stocks are declining. Investors mention 'AI fatigue' and say the narrative is overplayed. Valuation concerns are mounting.",
            "source": "CNBC",
            "published_date": "2025-01-19T10:00:00Z",
        }

        shift_detected = await engine.detect_narrative_shift(previous_state, new_article)

        assert shift_detected  # Truthy check (not is True)
        assert shift_detected["from_phase"] == "CONSENSUS"
        assert shift_detected["to_phase"] == "FATIGUED"

    @pytest.mark.asyncio
    async def test_detect_narrative_shift_fatigued_to_reversing(self, mock_llm):
        """Test detecting shift from FATIGUED to REVERSING"""
        engine = NarrativeStateEngine(llm_provider=mock_llm)

        previous_state = NarrativeState(
            topic="EV Stocks",
            fact_layer="EV sales growth slowing",
            narrative_layer="EV boom narrative losing momentum",
            phase=NarrativePhase.FATIGUED,
            confidence=0.5,
            evidence_count=30,
            last_updated=datetime.now() - timedelta(days=10),
        )

        new_article = {
            "title": "Traditional Automakers Overtake EV Companies in Market Share",
            "content": "In a surprising reversal, traditional automakers with hybrid offerings are gaining market share while pure-play EV companies struggle. The electric vehicle transition is taking longer than expected.",
            "source": "Bloomberg",
            "published_date": "2025-01-19T10:00:00Z",
        }

        shift_detected = await engine.detect_narrative_shift(previous_state, new_article)

        assert shift_detected  # Truthy check (not is True)
        assert shift_detected["from_phase"] == "FATIGUED"
        assert shift_detected["to_phase"] == "REVERSING"

    @pytest.mark.asyncio
    async def test_no_shift_detected(self, mock_llm):
        """Test when no narrative shift is detected"""
        engine = NarrativeStateEngine(llm_provider=mock_llm)

        previous_state = NarrativeState(
            topic="Fed Rate Cuts",
            fact_layer="Fed signals rate cuts likely",
            narrative_layer="Market expects rate cuts in 2025",
            phase=NarrativePhase.CONSENSUS,
            confidence=0.85,
            evidence_count=25,
            last_updated=datetime.now() - timedelta(days=1),
        )

        new_article = {
            "title": "Fed Chair Reaffirms Rate Cut Stance",
            "content": "Federal Reserve Chair Jerome Powell reaffirmed that rate cuts are likely in 2025 if inflation continues to cool. The message is consistent with previous communications.",
            "source": "Reuters",
            "published_date": "2025-01-19T10:00:00Z",
        }

        shift_detected = await engine.detect_narrative_shift(previous_state, new_article)

        # Should return None or False when no shift
        assert shift_detected is False or shift_detected is None


# ============================================================================
# Test: Repository Pattern Integration
# ============================================================================

class TestRepositoryIntegration:
    """Test integration with repository pattern for narrative_states table"""

    @pytest.mark.asyncio
    async def test_save_narrative_state(self, engine, sample_article):
        """Test saving narrative state to database"""
        result = await engine.analyze_news(sample_article)

        # Should have narrative_state in result
        assert "narrative_state" in result.data or result.data.get("saved") is True

    @pytest.mark.asyncio
    async def test_load_existing_narrative_state(self, engine, sample_article):
        """Test loading existing narrative state for shift detection"""
        # First analysis creates state
        result1 = await engine.analyze_news(sample_article)

        # Check that narrative state was created
        assert result1.success is True
        assert "narrative_state" in result1.metadata

        # Verify narrative state structure
        narrative_state = result1.metadata["narrative_state"]
        assert narrative_state["topic"] == "AI Semiconductor Boom"
        assert narrative_state["phase"] == "ACCELERATING"
        assert "fact_layer" in narrative_state
        assert "narrative_layer" in narrative_state


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestNarrativeStateEngineEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, engine):
        """Test handling of missing required fields"""
        invalid_article = {
            "title": "Test Article",
            # Missing "content" field
        }

        result = await engine.analyze_news(invalid_article)

        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_empty_article(self, engine):
        """Test handling of empty article"""
        empty_article = {
            "title": "",
            "content": "",
        }

        result = await engine.analyze_news(empty_article)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_llm_api_error(self, engine):
        """Test handling of LLM API errors"""
        # Override mock to raise error
        async def failing_complete(system_prompt, user_prompt, config=None):
            raise Exception("API Error: Rate limit exceeded")

        engine.llm.complete_with_system = failing_complete

        article = {
            "title": "Test",
            "content": "Test content",
        }

        result = await engine.analyze_news(article)

        assert result.success is False
        assert any("API Error" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_malformed_llm_response(self, engine):
        """Test handling of malformed LLM response"""
        # Override mock to return invalid JSON
        async def malformed_complete(system_prompt, user_prompt, config=None):
            from backend.ai.llm_providers import LLMResponse, ModelProvider
            return LLMResponse(
                content="This is not valid JSON {{broken",
                model="mock",
                provider=ModelProvider.MOCK,
                tokens_used=50,
                latency_ms=50,
            )

        engine.llm.complete_with_system = malformed_complete

        article = {
            "title": "Test",
            "content": "Test content",
        }

        result = await engine.analyze_news(article)

        # Should use fallback parsing
        assert result is not None
        # Fallback should still provide basic structure
        assert "fact_layer" in result.data or "error" in result.data


# ============================================================================
# Test: Confidence and Evidence
# ============================================================================

class TestConfidenceAndEvidence:
    """Test confidence scoring and evidence tracking"""

    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self, engine, sample_article):
        """Test confidence score is properly calculated"""
        result = await engine.analyze_news(sample_article)

        confidence = result.data.get("confidence", 0.0)

        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.5  # Mock returns 0.85

    @pytest.mark.asyncio
    async def test_evidence_extraction(self, engine, sample_article):
        """Test evidence points are extracted"""
        result = await engine.analyze_news(sample_article)

        evidence = result.data.get("evidence", [])

        assert isinstance(evidence, list)
        assert len(evidence) > 0


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
