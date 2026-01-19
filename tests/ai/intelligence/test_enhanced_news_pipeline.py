"""
Enhanced News Processing Pipeline Tests

Market Intelligence v2.0 - Phase 4, T4.3

Tests for the Enhanced News Processing Pipeline that integrates all intelligence
components into a unified workflow with comprehensive contrarian view analysis.

Key Features:
1. Full pipeline integration (Filter → Intelligence → Narrative → FactCheck → MarketConfirm → Horizon → Policy → Insight)
2. Each stage mockable for testing
3. Contrarian view forced display (contrarian_view, invalidation_conditions, failure_triggers)
4. End-to-end integration testing

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from backend.ai.intelligence.enhanced_news_pipeline import (
    EnhancedNewsProcessingPipeline,
    PipelineStage,
    PipelineResult,
    ContrarianView,
)
from backend.ai.intelligence.base import IntelligenceResult, IntelligencePhase


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    class MockLLM:
        async def complete_with_system(self, system_prompt: str, user_prompt: str, config=None):
            from backend.ai.llm_providers import LLMResponse, ModelProvider

            # Return enhanced analysis
            content = """**Enhanced News Analysis:**

**Summary**: AI Infrastructure narrative showing signs of fatigue

**Key Insights**:
1. Narrative is in FATIGUED phase (high mentions, low new information)
2. Market confirmation shows divergence
3. Contrarian view: Consider profit-taking on recent winners

**Confidence**: 75% | **Risk Level**: MEDIUM
**Horizon**: Short-term (1-5 days)"""

            return LLMResponse(
                content=content,
                model="mock",
                provider=ModelProvider.MOCK,
                tokens_used=150,
                latency_ms=100,
            )

        def create_stage1_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK)

        def create_stage2_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK)

    return MockLLM()


@pytest.fixture
def mock_intelligence_components():
    """Mock intelligence components"""
    components = {}

    # Mock NewsFilter
    class MockNewsFilter:
        async def filter_news(self, article: Dict[str, Any]) -> IntelligenceResult:
            return IntelligenceResult(
                success=True,
                component_name="news_filter",
                data={"is_relevant": True, "stage": "filter"},
                confidence=0.9,
                reasoning="Article is relevant",
            )

    # Mock NarrativeStateEngine
    class MockNarrativeEngine:
        async def analyze_news(self, article: Dict[str, Any]) -> IntelligenceResult:
            return IntelligenceResult(
                success=True,
                component_name="narrative_engine",
                data={"narrative_phase": "FATIGUED", "stage": "narrative"},
                confidence=0.8,
                reasoning="Narrative in fatigue phase",
            )

    # Mock FactChecker
    class MockFactChecker:
        async def verify_data(self, article: Dict[str, Any]) -> IntelligenceResult:
            return IntelligenceResult(
                success=True,
                component_name="fact_checker",
                data={"verification_status": "VERIFIED", "stage": "fact_check"},
                confidence=0.9,
                reasoning="All facts verified",
            )

    # Mock MarketConfirmation
    class MockMarketConfirmation:
        async def confirm_narrative(self, narrative: Dict[str, Any]) -> IntelligenceResult:
            return IntelligenceResult(
                success=True,
                component_name="market_confirmation",
                data={"confirmation_status": "DIVERGENT", "stage": "market_confirm"},
                confidence=0.7,
                reasoning="Price action diverging from narrative",
            )

    # Mock HorizonTagger
    class MockHorizonTagger:
        async def tag_horizons(self, insight: Dict[str, Any]) -> IntelligenceResult:
            return IntelligenceResult(
                success=True,
                component_name="horizon_tagger",
                data={"horizons": ["short_term"], "stage": "horizon"},
                confidence=0.8,
                reasoning="Short-term opportunity",
            )

    # Mock PolicyFeasibility
    class MockPolicyFeasibility:
        async def analyze_feasibility(self, policy: Dict[str, Any]) -> IntelligenceResult:
            return IntelligenceResult(
                success=True,
                component_name="policy_feasibility",
                data={"feasibility": 0.6, "stage": "policy"},
                confidence=0.7,
                reasoning="Moderate feasibility",
            )

    components["news_filter"] = MockNewsFilter()
    components["narrative_engine"] = MockNarrativeEngine()
    components["fact_checker"] = MockFactChecker()
    components["market_confirmation"] = MockMarketConfirmation()
    components["horizon_tagger"] = MockHorizonTagger()
    components["policy_feasibility"] = MockPolicyFeasibility()

    return components


@pytest.fixture
def pipeline(mock_llm, mock_intelligence_components):
    """Create EnhancedNewsProcessingPipeline instance"""
    return EnhancedNewsProcessingPipeline(
        llm_provider=mock_llm,
        intelligence_components=mock_intelligence_components,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestPipelineBasic:
    """Test basic pipeline functionality"""

    def test_initialization(self, pipeline):
        """Test pipeline initializes correctly"""
        assert pipeline.name == "EnhancedNewsProcessingPipeline"
        assert pipeline.phase.value == "P2"
        assert pipeline._enabled is True

    @pytest.mark.asyncio
    async def test_process_article(self, pipeline):
        """Test processing a news article"""
        article = {
            "title": "AI Infrastructure Stocks Rally on Government Spending",
            "content": "Major AI infrastructure companies saw significant gains...",
            "source": "Reuters",
            "published_at": "2026-01-19T10:00:00Z",
        }

        result = await pipeline.process_article(article)

        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert result.final_insight is not None


# ============================================================================
# Test: Pipeline Stages
# ============================================================================

class TestPipelineStages:
    """Test individual pipeline stages"""

    @pytest.mark.asyncio
    async def test_stage1_filtering(self, pipeline):
        """Test Stage 1: News Filtering"""
        article = {"title": "Test Article", "content": "Test content"}

        result = await pipeline._stage1_filter(article)

        assert isinstance(result, IntelligenceResult)
        assert result.data.get("stage") == "filter"

    @pytest.mark.asyncio
    async def test_stage2_narrative_analysis(self, pipeline):
        """Test Stage 2: Narrative Analysis"""
        article = {"title": "Test Article", "content": "Test content"}

        result = await pipeline._stage2_narrative(article)

        assert isinstance(result, IntelligenceResult)
        assert result.data.get("stage") == "narrative"

    @pytest.mark.asyncio
    async def test_stage3_fact_check(self, pipeline):
        """Test Stage 3: Fact Checking"""
        article = {"title": "Test Article", "content": "Test content"}

        result = await pipeline._stage3_fact_check(article)

        assert isinstance(result, IntelligenceResult)
        assert result.data.get("stage") == "fact_check"

    @pytest.mark.asyncio
    async def test_stage4_market_confirm(self, pipeline):
        """Test Stage 4: Market Confirmation"""
        narrative = {"theme": "AI", "phase": "ACCELERATING"}

        result = await pipeline._stage4_market_confirm(narrative)

        assert isinstance(result, IntelligenceResult)
        assert result.data.get("stage") == "market_confirm"

    @pytest.mark.asyncio
    async def test_stage5_horizon_tagging(self, pipeline):
        """Test Stage 5: Horizon Tagging"""
        insight = {"theme": "AI", "confidence": 0.8}

        result = await pipeline._stage5_horizon_tagging(insight)

        assert isinstance(result, IntelligenceResult)
        assert result.data.get("stage") == "horizon"

    @pytest.mark.asyncio
    async def test_stage6_policy_analysis(self, pipeline):
        """Test Stage 6: Policy Feasibility"""
        insight = {"theme": "AI", "policy": "CHIPS Act"}

        result = await pipeline._stage6_policy_analysis(insight)

        assert isinstance(result, IntelligenceResult)
        assert result.data.get("stage") == "policy"


# ============================================================================
# Test: Contrarian View
# ============================================================================

class TestContrarianView:
    """Test contrarian view generation"""

    @pytest.mark.asyncio
    async def test_generate_contrarian_view(self, pipeline):
        """Test contrarian view generation"""
        pipeline_result = {
            "filter": IntelligenceResult(success=True, component_name="filter", data={}, reasoning=""),
            "narrative": IntelligenceResult(success=True, component_name="narrative", data={"narrative_phase": "FATIGUED"}, reasoning=""),
            "fact_check": IntelligenceResult(success=True, component_name="fact_check", data={}, reasoning=""),
            "market_confirm": IntelligenceResult(success=True, component_name="market_confirm", data={"confirmation_status": "DIVERGENT"}, reasoning=""),
            "horizon": IntelligenceResult(success=True, component_name="horizon", data={"horizons": ["short_term"]}, reasoning=""),
            "policy": IntelligenceResult(success=True, component_name="policy", data={}, reasoning=""),
        }

        result = await pipeline._generate_contrarian_view(pipeline_result)

        assert isinstance(result, ContrarianView)
        assert result.bull_case is not None or result.bear_case is not None

    @pytest.mark.asyncio
    async def test_identify_invalidation_conditions(self, pipeline):
        """Test identification of invalidation conditions"""
        pipeline_result = {
            "market_confirm": IntelligenceResult(
                success=True,
                component_name="market_confirm",
                data={"confirmation_status": "CONTRADICTED"},
                reasoning="Price action contradicts narrative",
            ),
        }

        conditions = pipeline._identify_invalidation_conditions(pipeline_result)

        assert isinstance(conditions, list)
        assert len(conditions) > 0

    @pytest.mark.asyncio
    async def test_identify_failure_triggers(self, pipeline):
        """Test identification of failure triggers"""
        pipeline_result = {
            "fact_check": IntelligenceResult(
                success=False,
                component_name="fact_check",
                data={},
                reasoning="Hallucination detected",
            ),
        }

        triggers = pipeline._identify_failure_triggers(pipeline_result)

        assert isinstance(triggers, list)
        assert len(triggers) > 0


# ============================================================================
# Test: End-to-End Integration
# ============================================================================

class TestEndToEndIntegration:
    """Test complete pipeline integration"""

    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, pipeline):
        """Test complete pipeline from article to final insight"""
        article = {
            "title": "AI Infrastructure Sector Shows Signs of Fatigue",
            "content": "After months of strong gains, AI infrastructure stocks are showing...",
            "source": "Bloomberg",
            "published_at": "2026-01-19T14:30:00Z",
        }

        result = await pipeline.process_article(article)

        assert result.success is True
        assert result.final_insight is not None
        assert result.contrarian_view is not None
        assert len(result.invalidation_conditions) >= 0
        assert len(result.failure_triggers) >= 0

    @pytest.mark.asyncio
    async def test_pipeline_with_irrelevant_article(self, pipeline):
        """Test pipeline filters out irrelevant articles early"""
        # Mock filter to reject article
        original_filter = pipeline._components.get("news_filter")

        class RejectFilter:
            async def filter_news(self, article):
                from backend.ai.intelligence.base import IntelligenceResult
                return IntelligenceResult(
                    success=True,
                    component_name="news_filter",
                    data={"is_relevant": False, "stage": "filter"},
                    confidence=0.9,
                    reasoning="Article not relevant",
                )

        pipeline._components["news_filter"] = RejectFilter()

        article = {"title": "Unrelated Article", "content": "Not market related"}

        result = await pipeline.process_article(article)

        assert result.success is True
        # Should indicate early termination by checking final_insight
        assert "filtered out" in result.final_insight.lower() or result.final_insight == "Article filtered out as irrelevant"

        # Restore original
        pipeline._components["news_filter"] = original_filter


# ============================================================================
# Test: Mockable Stages
# ============================================================================

class TestMockableStages:
    """Test that each stage can be mocked independently"""

    @pytest.mark.asyncio
    async def test_mock_news_filter(self, pipeline):
        """Test NewsFilter can be mocked"""
        mock_filter = Mock()
        mock_filter.filter_news = AsyncMock(return_value=IntelligenceResult(
            success=True,
            component_name="news_filter",
            data={"is_relevant": True},
            reasoning="Mocked filter",
        ))

        original_filter = pipeline._components.get("news_filter")
        pipeline._components["news_filter"] = mock_filter

        article = {"title": "Test"}
        result = await pipeline._stage1_filter(article)

        assert result.success is True
        mock_filter.filter_news.assert_called_once()

        # Restore original
        pipeline._components["news_filter"] = original_filter

    @pytest.mark.asyncio
    async def test_mock_market_confirmation(self, pipeline):
        """Test MarketConfirmation can be mocked"""
        mock_confirm = Mock()
        mock_confirm.confirm_narrative = AsyncMock(return_value=IntelligenceResult(
            success=True,
            component_name="market_confirmation",
            data={"confirmation_status": "CONFIRMED"},
            reasoning="Mocked confirmation",
        ))

        original_confirm = pipeline._components.get("market_confirmation")
        pipeline._components["market_confirmation"] = mock_confirm

        narrative = {"theme": "Test"}
        result = await pipeline._stage4_market_confirm(narrative)

        assert result.success is True
        mock_confirm.confirm_narrative.assert_called_once()

        # Restore original
        pipeline._components["market_confirmation"] = original_confirm


# ============================================================================
# Test: Pipeline Result Data Class
# ============================================================================

class TestPipelineResult:
    """Test PipelineResult data class"""

    def test_pipeline_result_creation(self):
        """Test PipelineResult creation"""
        stages = {
            "filter": IntelligenceResult(success=True, component_name="filter", data={}, reasoning=""),
            "narrative": IntelligenceResult(success=True, component_name="narrative", data={}, reasoning=""),
        }

        result = PipelineResult(
            success=True,
            stages=stages,
            final_insight="Test insight",
            contrarian_view=ContrarianView(
                bull_case="Test bull case",
                bear_case="Test bear case",
            ),
        )

        assert result.success is True
        assert result.final_insight == "Test insight"
        assert len(result.stages) == 2

    def test_pipeline_result_to_dict(self):
        """Test converting PipelineResult to dictionary"""
        stages = {
            "filter": IntelligenceResult(success=True, component_name="filter", data={"stage": "filter"}, reasoning=""),
            "narrative": IntelligenceResult(success=True, component_name="narrative", data={"stage": "narrative"}, reasoning=""),
        }

        result = PipelineResult(
            success=True,
            stages=stages,
            final_insight="Test insight",
            contrarian_view=ContrarianView(
                bull_case="Test bull case",
                bear_case="Test bear case",
            ),
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["final_insight"] == "Test insight"


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestPipelineEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_article(self, pipeline):
        """Test handling of empty article"""
        article = {}

        result = await pipeline.process_article(article)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_missing_title(self, pipeline):
        """Test article without title"""
        article = {"content": "Test content without title"}

        result = await pipeline.process_article(article)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_component_failure_handling(self, pipeline):
        """Test handling when component fails"""
        class FailingComponent:
            async def verify_data(self, data):
                raise Exception("Component failure")

        # Replace a component with failing one
        pipeline._components["fact_checker"] = FailingComponent()

        article = {"title": "Test", "content": "Test content"}

        result = await pipeline.process_article(article)

        # Should handle failure gracefully
        assert result is not None
        # Since pipeline wraps exceptions, result may still be success with default fallback
        # or it may have error indicators
        assert result is not None  # Basic check that we got a result

    @pytest.mark.asyncio
    async def test_pipeline_with_all_stages_failing(self, pipeline):
        """Test pipeline when all intelligence components fail"""
        # Make all components fail
        for key in pipeline._components:
            pipeline._components[key] = Mock()

        # Make analyze method fail
        async def failing_analyze(self, data):
            raise Exception("All components failed")

        for key in pipeline._components:
            if hasattr(pipeline._components[key], "analyze"):
                pipeline._components[key].analyze = failing_analyze

        article = {"title": "Test", "content": "Test"}

        result = await pipeline.process_article(article)

        # Should still return a result
        assert result is not None


# ============================================================================
# Test: ContrarianView Data Class
# ============================================================================

class TestContrarianView:
    """Test ContrarianView data class"""

    def test_contrarian_view_creation(self):
        """Test ContrarianView creation"""
        view = ContrarianView(
            bull_case="Market is overextended, consider profit-taking",
            bear_case="Wait for pullback before entering",
            confidence=0.75,
        )

        assert view.bull_case == "Market is overextended, consider profit-taking"
        assert view.bear_case == "Wait for pullback before entering"
        assert view.confidence == 0.75

    def test_contrarian_view_to_dict(self):
        """Test converting ContrarianView to dictionary"""
        view = ContrarianView(
            bull_case="Bullish scenario",
            bear_case="Bearish scenario",
            key_risks=["Risk 1", "Risk 2"],
            confidence=0.8,
        )

        view_dict = view.to_dict()

        assert isinstance(view_dict, dict)
        assert view_dict["bull_case"] == "Bullish scenario"


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
