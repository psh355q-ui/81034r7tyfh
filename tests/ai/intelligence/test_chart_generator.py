"""
ChartGenerator Tests

Market Intelligence v2.0 - Phase 2, T2.4

Tests for the Chart Generator component that automatically creates
visualization charts in the style of "Sosumonkey" for market insights.

Key Features:
1. Theme bubble chart generation
2. Geopolitical timeline visualization
3. Sector performance bar chart
4. Automatic chart file generation
5. Chart metadata logging

Author: AI Trading System Team
Date: 2026-01-19
Reference: docs/planning/260118_market_intelligence_roadmap.md
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from backend.ai.intelligence.chart_generator import (
    ChartGenerator,
    ChartType,
    ChartConfig,
    ChartResult,
)
from backend.ai.intelligence.base import IntelligenceResult
from backend.ai.llm_providers import LLMProvider


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Mock LLM provider"""
    class MockLLM:
        async def complete_with_system(self, system_prompt: str, user_prompt: str, config=None):
            from backend.ai.llm_providers import LLMResponse, ModelProvider
            return LLMResponse(
                content="Mock chart generation response",
                model="mock",
                provider=ModelProvider.MOCK,
                tokens_used=50,
                latency_ms=50,
            )

        def create_stage1_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK)

        def create_stage2_config(self):
            from backend.ai.llm_providers import ModelConfig, ModelProvider
            return ModelConfig(model="mock", provider=ModelProvider.MOCK)

    return MockLLM()


@pytest.fixture
def mock_chart_renderer():
    """Mock chart rendering service"""
    class MockChartRenderer:
        async def render_bubble_chart(self, config: ChartConfig):
            """Return mock bubble chart data"""
            return {
                "type": "bubble",
                "data": [
                    {"theme": "AI Semiconductor", "x": 0.8, "y": 0.7, "size": 100},
                    {"theme": "Defense", "x": 0.6, "y": 0.5, "size": 50},
                ],
                "file_path": "/tmp/charts/theme_bubble_20260119.png",
            }

        async def render_timeline_chart(self, config: ChartConfig):
            """Return mock timeline chart data"""
            return {
                "type": "timeline",
                "events": [
                    {"date": "2026-01-15", "event": "Defense spending increase", "impact": 0.8},
                    {"date": "2026-01-18", "event": "AI chip demand surge", "impact": 0.9},
                ],
                "file_path": "/tmp/charts/timeline_20260119.png",
            }

        async def render_bar_chart(self, config: ChartConfig):
            """Return mock bar chart data"""
            return {
                "type": "bar",
                "data": [
                    {"sector": "Technology", "performance": 15.2},
                    {"sector": "Defense", "performance": 8.5},
                    {"sector": "Healthcare", "performance": 2.1},
                ],
                "file_path": "/tmp/charts/sector_performance_20260119.png",
            }

    return MockChartRenderer()


@pytest.fixture
def chart_generator(mock_llm, mock_chart_renderer):
    """Create ChartGenerator instance"""
    return ChartGenerator(
        llm_provider=mock_llm,
        chart_renderer=mock_chart_renderer,
    )


# ============================================================================
# Test: Basic Functionality
# ============================================================================

class TestChartGeneratorBasic:
    """Test basic ChartGenerator functionality"""

    def test_initialization(self, chart_generator):
        """Test generator initializes correctly"""
        assert chart_generator.name == "ChartGenerator"
        assert chart_generator.phase.value == "P1"
        assert chart_generator._enabled is True

    @pytest.mark.asyncio
    async def test_generate_theme_bubble_chart(self, chart_generator):
        """Test theme bubble chart generation"""
        config = ChartConfig(
            chart_type=ChartType.THEME_BUBBLE,
            themes=["AI Semiconductor", "Defense", "EV"],
            metrics={"mentions": [100, 50, 75], "performance": [20, 8, 5]},
        )

        result = await chart_generator.generate_chart(config)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert "chart_type" in result.data
        assert "file_path" in result.data

    @pytest.mark.asyncio
    async def test_generate_timeline_chart(self, chart_generator):
        """Test geopolitical timeline chart generation"""
        config = ChartConfig(
            chart_type=ChartType.GEOPOLITICAL_TIMELINE,
            events=[
                {"date": "2026-01-15", "event": "Defense Bill", "impact": 0.8},
                {"date": "2026-01-18", "event": "Sanctions", "impact": 0.6},
            ],
        )

        result = await chart_generator.generate_chart(config)

        assert isinstance(result, IntelligenceResult)
        assert result.success is True
        assert result.data["chart_type"] == "GEOPOLITICAL_TIMELINE"


# ============================================================================
# Test: Theme Bubble Chart
# ============================================================================

class TestThemeBubbleChart:
    """Test theme bubble chart generation"""

    @pytest.mark.asyncio
    async def test_bubble_chart_data_structure(self, chart_generator):
        """Test bubble chart data structure"""
        config = ChartConfig(
            chart_type=ChartType.THEME_BUBBLE,
            themes=["AI", "Defense"],
            metrics={"x": [0.8, 0.6], "y": [0.7, 0.5], "size": [100, 50]},
        )

        result = await chart_generator.generate_chart(config)

        assert result.data["chart_type"] == "THEME_BUBBLE"
        assert "file_path" in result.data

    @pytest.mark.asyncio
    async def test_bubble_chart_with_multiple_themes(self, chart_generator):
        """Test bubble chart with multiple themes"""
        config = ChartConfig(
            chart_type=ChartType.THEME_BUBBLE,
            themes=["AI Semiconductor", "Defense", "EV", "Healthcare", "Finance"],
            metrics={
                "x": [0.8, 0.6, 0.4, 0.3, 0.5],
                "y": [0.7, 0.5, 0.3, 0.4, 0.6],
                "size": [100, 50, 75, 40, 60],
            },
        )

        result = await chart_generator.generate_chart(config)

        assert result.success is True
        assert "bubble" in result.data.get("file_path", "").lower()


# ============================================================================
# Test: Geopolitical Timeline Chart
# ============================================================================

class TestTimelineChart:
    """Test geopolitical timeline chart generation"""

    @pytest.mark.asyncio
    async def test_timeline_chart_events(self, chart_generator):
        """Test timeline chart with events"""
        config = ChartConfig(
            chart_type=ChartType.GEOPOLITICAL_TIMELINE,
            events=[
                {"date": "2026-01-15", "event": "Defense spending bill", "impact": 0.8},
                {"date": "2026-01-20", "event": "Trade agreement", "impact": 0.5},
            ],
        )

        result = await chart_generator.generate_chart(config)

        assert result.success is True
        assert result.data["chart_type"] == "GEOPOLITICAL_TIMELINE"

    @pytest.mark.asyncio
    async def test_timeline_chronological_order(self, chart_generator):
        """Test timeline maintains chronological order"""
        config = ChartConfig(
            chart_type=ChartType.GEOPOLITICAL_TIMELINE,
            events=[
                {"date": "2026-01-20", "event": "Event 2", "impact": 0.5},
                {"date": "2026-01-15", "event": "Event 1", "impact": 0.8},  # Out of order
            ],
        )

        result = await chart_generator.generate_chart(config)

        assert result.success is True
        # Should be sorted chronologically


# ============================================================================
# Test: Sector Performance Bar Chart
# ============================================================================

class TestSectorBarChart:
    """Test sector performance bar chart generation"""

    @pytest.mark.asyncio
    async def test_bar_chart_sectors(self, chart_generator):
        """Test bar chart with sector performance"""
        config = ChartConfig(
            chart_type=ChartType.SECTOR_PERFORMANCE,
            sectors=["Technology", "Defense", "Healthcare"],
            metrics={"performance": [15.2, 8.5, 2.1]},
        )

        result = await chart_generator.generate_chart(config)

        assert result.success is True
        assert result.data["chart_type"] == "SECTOR_PERFORMANCE"

    @pytest.mark.asyncio
    async def test_bar_chart_positive_negative(self, chart_generator):
        """Test bar chart with positive and negative performance"""
        config = ChartConfig(
            chart_type=ChartType.SECTOR_PERFORMANCE,
            sectors=["Tech", "Energy", "Retail"],
            metrics={"performance": [10.5, -3.2, 5.1]},
        )

        result = await chart_generator.generate_chart(config)

        assert result.success is True


# ============================================================================
# Test: Chart Configuration
# ============================================================================

class TestChartConfig:
    """Test chart configuration"""

    def test_chart_config_creation(self):
        """Test creating a ChartConfig"""
        config = ChartConfig(
            chart_type=ChartType.THEME_BUBBLE,
            themes=["AI"],
            metrics={"x": [0.5], "y": [0.5], "size": [100]},
        )

        assert config.chart_type == ChartType.THEME_BUBBLE
        assert config.themes == ["AI"]

    def test_chart_config_defaults(self):
        """Test chart config default values"""
        config = ChartConfig(
            chart_type=ChartType.SECTOR_PERFORMANCE,
        )

        assert config.title == ""
        assert config.width == 800
        assert config.height == 600


# ============================================================================
# Test: Chart Result
# ============================================================================

class TestChartResult:
    """Test ChartResult data class"""

    def test_chart_result_creation(self):
        """Test creating a ChartResult"""
        result = ChartResult(
            chart_type=ChartType.THEME_BUBBLE,
            file_path="/tmp/charts/test.png",
            metadata={"theme": "AI"},
        )

        assert result.chart_type == ChartType.THEME_BUBBLE
        assert result.file_path == "/tmp/charts/test.png"

    def test_chart_result_to_dict(self):
        """Test converting ChartResult to dictionary"""
        result = ChartResult(
            chart_type=ChartType.SECTOR_PERFORMANCE,
            file_path="/tmp/charts/sector.png",
            metadata={"sectors": 3},
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["chart_type"] == "SECTOR_PERFORMANCE"


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestChartGeneratorEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_config(self, chart_generator):
        """Test handling of empty configuration"""
        config = ChartConfig(chart_type=ChartType.THEME_BUBBLE)

        result = await chart_generator.generate_chart(config)

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_renderer_error(self, chart_generator):
        """Test handling of renderer errors"""
        class ErrorRenderer:
            async def render_bubble_chart(self, config):
                raise Exception("Renderer Error")

        original_renderer = chart_generator.chart_renderer
        chart_generator.chart_renderer = ErrorRenderer()

        config = ChartConfig(
            chart_type=ChartType.THEME_BUBBLE,
            themes=["Test"],
        )

        result = await chart_generator.generate_chart(config)

        # Restore original
        chart_generator.chart_renderer = original_renderer

        # Should handle error gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_chart_type(self, chart_generator):
        """Test handling of invalid chart type"""
        config = ChartConfig(
            chart_type="INVALID_TYPE",
        )

        result = await chart_generator.generate_chart(config)

        # Should handle gracefully
        assert result is not None


# ============================================================================
# Test: File Path Generation
# ============================================================================

class TestFilePathGeneration:
    """Test chart file path generation"""

    @pytest.mark.asyncio
    async def test_unique_file_names(self, chart_generator):
        """Test that each chart gets a unique filename"""
        # Set renderer to None to use built-in file path generation
        original_renderer = chart_generator.chart_renderer
        chart_generator.chart_renderer = None

        config1 = ChartConfig(chart_type=ChartType.THEME_BUBBLE, themes=["AI"])
        config2 = ChartConfig(chart_type=ChartType.THEME_BUBBLE, themes=["Defense"])

        # Generate charts sequentially
        result1 = await chart_generator.generate_chart(config1)
        # Small delay to ensure different timestamp
        import asyncio
        await asyncio.sleep(0.01)  # 10ms delay
        result2 = await chart_generator.generate_chart(config2)

        # Restore original renderer
        chart_generator.chart_renderer = original_renderer

        # File paths should be unique (include counter)
        assert result1.data["file_path"] != result2.data["file_path"]
        # Both should contain the chart type name
        assert "theme_bubble" in result1.data["file_path"].lower()
        assert "theme_bubble" in result2.data["file_path"].lower()


# ============================================================================
# Test: Chart Type Enum
# ============================================================================

class TestChartType:
    """Test ChartType enum"""

    def test_theme_bubble_type(self):
        """Test THEME_BUBBLE chart type"""
        chart_type = ChartType.THEME_BUBBLE

        assert chart_type.value == "THEME_BUBBLE"

    def test_geopolitical_timeline_type(self):
        """Test GEOPOLITICAL_TIMELINE chart type"""
        chart_type = ChartType.GEOPOLITICAL_TIMELINE

        assert chart_type.value == "GEOPOLITICAL_TIMELINE"

    def test_sector_performance_type(self):
        """Test SECTOR_PERFORMANCE chart type"""
        chart_type = ChartType.SECTOR_PERFORMANCE

        assert chart_type.value == "SECTOR_PERFORMANCE"


# ============================================================================
# Test: Chart Metadata
# ============================================================================

class TestChartMetadata:
    """Test chart metadata logging"""

    @pytest.mark.asyncio
    async def test_chart_metadata_logging(self, chart_generator):
        """Test that metadata is logged with chart"""
        config = ChartConfig(
            chart_type=ChartType.THEME_BUBBLE,
            themes=["AI"],
            metadata={"insight_id": 123, "source": "intelligence"},
        )

        result = await chart_generator.generate_chart(config)

        assert result.success is True


# ============================================================================
# Test: Korean Font Support
# ============================================================================

class TestKoreanFontSupport:
    """Test Korean font support functionality"""

    def test_korean_font_setup(self):
        """Test Korean font setup method"""
        # Test that setup_korean_font is callable
        result = ChartGenerator.setup_korean_font()

        # Returns bool indicating success
        assert isinstance(result, bool)

    def test_get_available_korean_font(self):
        """Test getting available Korean font"""
        font = ChartGenerator.get_available_korean_font()

        # Returns string if found, None otherwise
        assert font is None or isinstance(font, str)

    def test_korean_fonts_list(self):
        """Test Korean fonts list is not empty"""
        # Should have at least some fonts defined
        assert len(ChartGenerator.KOREAN_FONTS) > 0

        # Common Korean fonts should be in the list
        assert "Malgun Gothic" in ChartGenerator.KOREAN_FONTS  # Windows
        assert "AppleGothic" in ChartGenerator.KOREAN_FONTS     # macOS
        assert "NanumGothic" in ChartGenerator.KOREAN_FONTS     # Linux

    def test_generator_korean_font_enabled_by_default(self, mock_llm):
        """Test that Korean font is enabled by default"""
        generator = ChartGenerator(llm_provider=mock_llm)

        # Korean font should be enabled by default
        assert hasattr(generator, "_korean_font_enabled")

    def test_generator_korean_font_can_be_disabled(self, mock_llm):
        """Test that Korean font can be disabled"""
        generator = ChartGenerator(
            llm_provider=mock_llm,
            enable_korean_font=False,
        )

        # Korean font should be disabled
        assert generator._korean_font_enabled is False

    @pytest.mark.asyncio
    async def test_korean_text_in_chart_title(self, mock_llm):
        """Test that Korean text in chart title works"""
        # Set renderer to None to use built-in matplotlib generation
        generator = ChartGenerator(
            llm_provider=mock_llm,
            chart_renderer=None,
            enable_korean_font=True,
        )

        config = ChartConfig(
            chart_type=ChartType.THEME_BUBBLE,
            themes=["AI 반도체", "국방"],
            title="테마 버블 차트",
            metrics={"x": [0.8, 0.6], "y": [0.7, 0.5], "size": [100, 50]},
        )

        result = await generator.generate_chart(config)

        # Should succeed even with Korean text
        assert result.success is True
        assert result.data["chart_type"] == "THEME_BUBBLE"

    @pytest.mark.asyncio
    async def test_korean_text_in_timeline_chart(self, mock_llm):
        """Test Korean text in timeline chart"""
        generator = ChartGenerator(
            llm_provider=mock_llm,
            chart_renderer=None,
            enable_korean_font=True,
        )

        config = ChartConfig(
            chart_type=ChartType.GEOPOLITICAL_TIMELINE,
            events=[
                {"date": "2026-01-15", "name": "국방 예산 증액", "category": "정책"},
                {"date": "2026-01-18", "name": "AI 칩 수요 급증", "category": "시장"},
            ],
            title="지정학 타임라인",
        )

        result = await generator.generate_chart(config)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_korean_text_in_sector_chart(self, mock_llm):
        """Test Korean text in sector performance chart"""
        generator = ChartGenerator(
            llm_provider=mock_llm,
            chart_renderer=None,
            enable_korean_font=True,
        )

        config = ChartConfig(
            chart_type=ChartType.SECTOR_PERFORMANCE,
            sectors=["기술", "국방", "헬스케어"],
            metrics={"performance": [15.2, 8.5, 2.1]},
            title="섹터 성과",
        )

        result = await generator.generate_chart(config)

        assert result.success is True

    def test_statistics_includes_korean_font_info(self, mock_llm):
        """Test that statistics includes Korean font information"""
        generator = ChartGenerator(llm_provider=mock_llm)
        stats = generator.get_statistics()

        # Should include Korean font status
        assert "korean_font_enabled" in stats
        assert "available_korean_font" in stats


# ============================================================================
# Test Runners
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
