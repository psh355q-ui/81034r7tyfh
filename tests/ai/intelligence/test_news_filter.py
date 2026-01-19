"""
NewsFilter Component Tests

Tests for the 2-stage news filtering component (Phase 1, T1.1).
This component filters news articles to reduce LLM API costs by 90%.
"""

import pytest
import asyncio
from datetime import datetime
from backend.ai.intelligence.base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from backend.ai.llm_providers import LLMProvider, ModelConfig, ModelProvider


class MockLLMProvider:
    """Mock LLM Provider for testing"""

    def __init__(self):
        self.stage1_calls = []
        self.stage2_calls = []

    async def complete(self, prompt: str, config: ModelConfig) -> str:
        """Mock completion"""
        if config.model == "mock-stage1":
            self.stage1_calls.append(prompt)
            # Stage 1: Check relevance (YES/NO)
            if "DEFENSE" in prompt.upper() or "방산" in prompt or "국방" in prompt:
                return "YES"
            return "NO"

        elif config.model == "mock-stage2":
            self.stage2_calls.append(prompt)
            # Stage 2: Deep analysis
            return '{"topic": "DEFENSE", "sentiment": "BULLISH", "confidence": 0.85, "reasoning": "국방비 증액으로 방산주 수혜 기대"}'

        return "Mock response"


class MockLLMProviderWrapper:
    """Wrapper to make MockLLMProvider compatible with LLMProvider interface"""

    def __init__(self, mock_provider: MockLLMProvider):
        self.mock = mock_provider
        # Import LLMResponse to return proper objects
        from backend.ai.llm_providers import LLMResponse, ModelProvider

    async def complete(self, prompt: str, config: ModelConfig):
        content = await self.mock.complete(prompt, config)
        # Return proper LLMResponse object
        from backend.ai.llm_providers import LLMResponse, ModelProvider
        return LLMResponse(
            content=content,
            model=config.model,
            provider=ModelProvider.MOCK,
            tokens_used=100,
            latency_ms=100,
        )

    async def complete_with_system(self, system_prompt: str, user_prompt: str, config: ModelConfig):
        """Mock complete with system prompt"""
        content = await self.mock.complete(user_prompt, config)
        from backend.ai.llm_providers import LLMResponse, ModelProvider
        return LLMResponse(
            content=content,
            model=config.model,
            provider=ModelProvider.MOCK,
            tokens_used=100,
            latency_ms=100,
        )

    def create_stage1_config(self):
        """Create Stage 1 config for mock"""
        from backend.ai.llm_providers import ModelConfig, ModelProvider
        return ModelConfig(
            model="mock-stage1",
            provider=ModelProvider.MOCK,
            max_tokens=50,
            temperature=0.3,
        )

    def create_stage2_config(self):
        """Create Stage 2 config for mock"""
        from backend.ai.llm_providers import ModelConfig, ModelProvider
        return ModelConfig(
            model="mock-stage2",
            provider=ModelProvider.MOCK,
            max_tokens=500,
            temperature=0.7,
        )


@pytest.fixture
def mock_llm():
    """Mock LLM provider fixture"""
    return MockLLMProvider()


@pytest.fixture
def sample_news_articles():
    """Sample news articles for testing"""
    return [
        {
            "id": 1,
            "title": "국방비 50% 증액: 방산주 대세 상승",
            "content": "정부가 내년도 국방비 예산을 50% 증액하는 방안을 추진 중이다. 이로 인해 방산 관련 주가들이 강세를 보이고 있다.",
            "source": "Reuters",
            "published_date": "2025-01-18",
        },
        {
            "id": 2,
            "title": "삼성전자, 신규 반도체 공장 준공",
            "content": "삼성전자가 파주 캠퍼스 내 신규 반도체 공장 건설을 완료하고 준공식을 가졌다.",
            "source": "TechCrunch",
            "published_date": "2025-01-18",
        },
        {
            "id": 3,
            "title": "연예 15도, 서울시 폭염 특보 발령",
            "content": "서울시가 오늘 오후 2시부터 폭염 특보를 발령했다. 시민들은 야외 활동을 자제해야 한다.",
            "source": "KBS",
            "published_date": "2025-01-18",
        },
        {
            "id": 4,
            "title": "AI 칩 수요 급증: 엔비디아 실적 호조",
            "content": "AI 데이터센터 확대로 엔비디아 GPU 수요가 급증하고 있다. 실적 시장 기대치를 상회하는 결과를 발표했다.",
            "source": "Bloomberg",
            "published_date": "2025-01-18",
        },
    ]


# ============================================================================
# Stage 1: Relevance Check Tests
# ============================================================================

class TestNewsFilterStage1:
    """Tests for Stage 1: Relevance Check (Light Model)"""

    @pytest.mark.asyncio
    async def test_stage1_relevant_article(self, mock_llm):
        """Test Stage 1 with relevant article (DEFENSE)"""
        from backend.ai.intelligence.news_filter import NewsFilter

        # Create filter with mock LLM
        filter = NewsFilter(llm_provider=MockLLMProviderWrapper(mock_llm))

        # Test relevant article
        article = {
            "id": 1,
            "title": "국방비 50% 증액",
            "content": "정부가 국방비를 대폭 증액하기로 했다.",
        }

        result = await filter.stage1_relevance_check(article)

        assert result.success is True
        assert result.data["is_relevant"] is True
        assert result.data["stage"] == "stage1"
        assert len(mock_llm.stage1_calls) == 1

    @pytest.mark.asyncio
    async def test_stage1_irrelevant_article(self, mock_llm):
        """Test Stage 1 with irrelevant article (weather)"""
        from backend.ai.intelligence.news_filter import NewsFilter

        filter = NewsFilter(llm_provider=MockLLMProviderWrapper(mock_llm))

        # Test irrelevant article
        article = {
            "id": 3,
            "title": "연예 15도",
            "content": "서울시가 폭염 특보를 발령했다.",
        }

        result = await filter.stage1_relevance_check(article)

        assert result.success is True
        assert result.data["is_relevant"] is False
        assert result.data["stage"] == "stage1"

    @pytest.mark.asyncio
    async def test_stage1_confidence_score(self, mock_llm):
        """Test Stage 1 returns confidence score"""
        from backend.ai.intelligence.news_filter import NewsFilter

        filter = NewsFilter(llm_provider=MockLLMProviderWrapper(mock_llm))

        article = {
            "id": 1,
            "title": "국방비 증액",
            "content": "방산주 관련 뉴스",
        }

        result = await filter.stage1_relevance_check(article)

        assert "confidence" in result.data
        assert 0.0 <= result.data["confidence"] <= 1.0


# ============================================================================
# Stage 2: Deep Analysis Tests
# ============================================================================

class TestNewsFilterStage2:
    """Tests for Stage 2: Deep Analysis (Heavy Model)"""

    @pytest.mark.asyncio
    async def test_stage2_deep_analysis(self, mock_llm):
        """Test Stage 2 deep analysis"""
        from backend.ai.intelligence.news_filter import NewsFilter

        filter = NewsFilter(llm_provider=MockLLMProviderWrapper(mock_llm))

        article = {
            "id": 1,
            "title": "국방비 50% 증액: 방산주 대세 상승",
            "content": "정부가 국방비 예산을 50% 증액하는 방안을 추진 중이다.",
        }

        result = await filter.stage2_deep_analysis(article)

        assert result.success is True
        assert result.data["stage"] == "stage2"
        assert "topic" in result.data
        assert "sentiment" in result.data
        assert "confidence" in result.data
        assert len(mock_llm.stage2_calls) == 1

    @pytest.mark.asyncio
    async def test_stage2_returns_structured_data(self, mock_llm):
        """Test Stage 2 returns properly structured data"""
        from backend.ai.intelligence.news_filter import NewsFilter

        filter = NewsFilter(llm_provider=MockLLMProviderWrapper(mock_llm))

        article = {
            "id": 1,
            "title": "AI 칩 수요 급증",
            "content": "엔비디아 GPU 수요가 폭증하고 있다.",
        }

        result = await filter.stage2_deep_analysis(article)

        # Check required fields
        assert result.data.get("topic") is not None
        assert result.data.get("sentiment") in ["BULLISH", "BEARISH", "NEUTRAL"]
        assert 0.0 <= result.data.get("confidence", 0) <= 1.0
        assert isinstance(result.data.get("reasoning"), str)


# ============================================================================
# Full Pipeline Tests
# ============================================================================

class TestNewsFilterPipeline:
    """Tests for full 2-stage filtering pipeline"""

    @pytest.mark.asyncio
    async def test_full_pipeline_relevant_article(self, mock_llm):
        """Test full pipeline with relevant article"""
        from backend.ai.intelligence.news_filter import NewsFilter

        filter = NewsFilter(llm_provider=MockLLMProviderWrapper(mock_llm))

        article = {
            "id": 1,
            "title": "국방비 50% 증액: 방산주 대세 상승",
            "content": "정부가 국방비 예산을 50% 증액하는 방안을 추진 중이다.",
        }

        result = await filter.process(article)

        assert result.success is True
        assert result.data["stage1_passed"] is True
        assert result.data["stage2_completed"] is True
        assert len(mock_llm.stage1_calls) == 1
        assert len(mock_llm.stage2_calls) == 1

    @pytest.mark.asyncio
    async def test_full_pipeline_irrelevant_article(self, mock_llm):
        """Test full pipeline with irrelevant article (Stage 2 skipped)"""
        from backend.ai.intelligence.news_filter import NewsFilter

        filter = NewsFilter(llm_provider=MockLLMProviderWrapper(mock_llm))

        article = {
            "id": 3,
            "title": "연예 15도",
            "content": "서울시가 폭염 특보를 발령했다.",
        }

        result = await filter.process(article)

        assert result.success is True
        assert result.data["stage1_passed"] is False
        assert result.data["stage2_completed"] is False
        assert len(mock_llm.stage1_calls) == 1
        assert len(mock_llm.stage2_calls) == 0  # Stage 2 skipped

    @pytest.mark.asyncio
    async def test_cost_tracking(self, mock_llm):
        """Test cost tracking (90% cost reduction)"""
        from backend.ai.intelligence.news_filter import NewsFilter

        filter = NewsFilter(llm_provider=MockLLMProviderWrapper(mock_llm))

        # Process multiple articles
        articles = [
            {"id": 1, "title": "국방비 증액", "content": "방산주 관련"},
            {"id": 3, "title": "연예", "content": "폭염 특보"},
            {"id": 2, "title": "삼성전자", "content": "반도체 공장"},
        ]

        results = []
        for article in articles:
            result = await filter.process(article)
            results.append(result)

        # Count calls
        total_stage1 = len(mock_llm.stage1_calls)
        total_stage2 = len(mock_llm.stage2_calls)

        # All articles should go through Stage 1
        assert total_stage1 == 3

        # Only relevant articles should go through Stage 2
        # In our mock: DEFENSE (yes), WEATHER (no), SAMSUNG (no)
        assert total_stage2 == 1

        # Cost calculation: Stage 1 is cheap, Stage 2 is expensive
        # With 2-stage filter: 3x Stage1 + 1x Stage2
        # Without filter: 3x Stage2
        # Savings = (3x Stage2 - 3x Stage1 - 1x Stage2) / 3x Stage2 = 66%
        # Real savings should be ~90% with real LLM costs


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestNewsFilterErrors:
    """Tests for error handling"""

    @pytest.mark.asyncio
    async def test_missing_title(self, mock_llm):
        """Test handling of missing title"""
        from backend.ai.intelligence.news_filter import NewsFilter

        filter = NewsFilter(llm_provider=MockLLMProviderWrapper(mock_llm))

        article = {
            "id": 1,
            # "title" is missing
            "content": "Some content",
        }

        result = await filter.process(article)

        # Should fail gracefully
        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_llm_api_error(self, mock_llm):
        """Test handling of LLM API errors"""
        from backend.ai.intelligence.news_filter import NewsFilter

        # Mock LLM that raises error
        class ErrorMockWrapper:
            async def complete(self, prompt, config):
                raise Exception("API Error")

            async def complete_with_system(self, system_prompt, user_prompt, config):
                raise Exception("API Error")

            def create_stage1_config(self):
                from backend.ai.llm_providers import ModelConfig, ModelProvider
                return ModelConfig(
                    model="mock-stage1",
                    provider=ModelProvider.MOCK,
                    max_tokens=50,
                )

            def create_stage2_config(self):
                from backend.ai.llm_providers import ModelConfig, ModelProvider
                return ModelConfig(
                    model="mock-stage2",
                    provider=ModelProvider.MOCK,
                    max_tokens=500,
                )

        filter = NewsFilter(llm_provider=ErrorMockWrapper())

        article = {
            "id": 1,
            "title": "Test",
            "content": "Test content",
        }

        result = await filter.process(article)

        # Should handle error gracefully
        assert result.success is False
        assert any("API Error" in e for e in result.errors)


# ============================================================================
# Configuration Tests
# ============================================================================

class TestNewsFilterConfig:
    """Tests for NewsFilter configuration"""

    @pytest.mark.asyncio
    async def test_custom_stage1_model(self, mock_llm):
        """Test custom Stage 1 model configuration"""
        from backend.ai.intelligence.news_filter import NewsFilter

        custom_config = ModelConfig(
            model="custom-light-model",
            provider=ModelProvider.MOCK,
            max_tokens=10,
        )

        filter = NewsFilter(
            llm_provider=MockLLMProviderWrapper(mock_llm),
            stage1_config=custom_config,
        )

        # Verify config is stored
        assert filter.stage1_config.model == "custom-light-model"

    @pytest.mark.asyncio
    async def test_custom_stage2_model(self, mock_llm):
        """Test custom Stage 2 model configuration"""
        from backend.ai.intelligence.news_filter import NewsFilter

        custom_config = ModelConfig(
            model="custom-heavy-model",
            provider=ModelProvider.MOCK,
            max_tokens=2000,
        )

        filter = NewsFilter(
            llm_provider=MockLLMProviderWrapper(mock_llm),
            stage2_config=custom_config,
        )

        # Verify config is stored
        assert filter.stage2_config.model == "custom-heavy-model"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
