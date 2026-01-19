"""
ChartGenerator Component - Automatic Visualization

Market Intelligence v2.0 - Phase 2, T2.4

This component automatically creates visualization charts in the style of
"Sosumonkey" for market insights, including theme bubbles, timelines,
and sector performance charts.

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

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from .base import BaseIntelligence, IntelligenceResult, IntelligencePhase
from ..llm_providers import LLMProvider


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ChartType(Enum):
    """Chart types for visualization"""
    THEME_BUBBLE = "THEME_BUBBLE"              # Theme bubble chart
    GEOPOLITICAL_TIMELINE = "GEOPOLITICAL_TIMELINE"  # Event timeline
    SECTOR_PERFORMANCE = "SECTOR_PERFORMANCE"  # Sector bar chart


@dataclass
class ChartConfig:
    """
    Configuration for chart generation

    Attributes:
        chart_type: Type of chart to generate
        themes: List of themes (for bubble chart)
        sectors: List of sectors (for bar chart)
        events: List of events (for timeline)
        metrics: Chart-specific metrics
        title: Chart title
        width: Chart width in pixels
        height: Chart height in pixels
        metadata: Additional metadata
    """
    chart_type: ChartType
    themes: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    events: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None
    title: str = ""
    width: int = 800
    height: int = 600
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartResult:
    """
    Result of chart generation

    Attributes:
        chart_type: Type of chart generated
        file_path: Path to generated chart file
        metadata: Chart metadata
        created_at: Generation timestamp
    """
    chart_type: ChartType
    file_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "chart_type": self.chart_type.value,
            "file_path": self.file_path,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================================
# Main Component
# ============================================================================

class ChartGenerator(BaseIntelligence):
    """
    Chart Generator

    Automatically creates visualization charts for market insights
    in the style of "Sosumonkey".

    Key Features:
    1. Theme bubble charts showing theme relationships
    2. Geopolitical timeline charts showing event sequences
    3. Sector performance bar charts
    4. Automatic file generation with timestamps
    5. Chart metadata logging

    Usage:
        from backend.ai.llm_providers import get_llm_provider
        from backend.ai.intelligence.chart_generator import ChartGenerator, ChartConfig, ChartType

        llm = get_llm_provider()
        generator = ChartGenerator(
            llm_provider=llm,
            chart_renderer=renderer,
        )

        # Generate theme bubble chart
        config = ChartConfig(
            chart_type=ChartType.THEME_BUBBLE,
            themes=["AI Semiconductor", "Defense"],
            metrics={"x": [0.8, 0.6], "y": [0.7, 0.5], "size": [100, 50]},
        )

        result = await generator.generate_chart(config)
        chart_path = result.data["file_path"]
    """

    # Default chart output directory
    DEFAULT_CHART_DIR = "tmp/charts"

    # Korean font configuration
    # Common Korean fonts: Malgun Gothic (Windows), AppleGothic (Mac), NanumGothic (Linux)
    KOREAN_FONTS = [
        "Malgun Gothic",      # Windows
        "AppleGothic",        # macOS
        "NanumGothic",        # Linux
        "NanumGothicCoding",  # Linux (coding)
        "Dotum",              # Windows (fallback)
        "Batang",             # Windows (fallback)
    ]

    @classmethod
    def setup_korean_font(cls) -> bool:
        """
        Setup Korean font for matplotlib

        Returns:
            bool: True if Korean font was successfully configured
        """
        try:
            # Try each Korean font in order
            for font_name in cls.KOREAN_FONTS:
                try:
                    # Check if font is available
                    font_list = [f.name for f in fm.fontManager.ttflist]
                    if font_name in font_list:
                        plt.rcParams['font.family'] = font_name
                        plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display
                        logger.info(f"Korean font configured: {font_name}")
                        return True
                except Exception as e:
                    logger.debug(f"Font {font_name} not available: {e}")
                    continue

            # If no Korean font found, log warning
            logger.warning("No Korean font found. Charts may not display Korean text correctly.")
            logger.info(f"Available fonts: {len([f.name for f in fm.fontManager.ttflist])} fonts")
            return False

        except Exception as e:
            logger.error(f"Error setting up Korean font: {e}")
            return False

    @classmethod
    def get_available_korean_font(cls) -> Optional[str]:
        """
        Get first available Korean font name

        Returns:
            Optional[str]: Font name if found, None otherwise
        """
        font_list = [f.name for f in fm.fontManager.ttflist]
        for font_name in cls.KOREAN_FONTS:
            if font_name in font_list:
                return font_name
        return None

    def __init__(
        self,
        llm_provider: LLMProvider,
        chart_renderer: Optional[Any] = None,
        chart_dir: Optional[str] = None,
        enable_korean_font: bool = True,
    ):
        """
        Initialize ChartGenerator

        Args:
            llm_provider: LLM Provider instance
            chart_renderer: Chart rendering service
            chart_dir: Directory for chart output
            enable_korean_font: Whether to setup Korean font automatically
        """
        super().__init__(
            name="ChartGenerator",
            phase=IntelligencePhase.P1,
        )

        self.llm = llm_provider
        self.chart_renderer = chart_renderer
        self.chart_dir = chart_dir or self.DEFAULT_CHART_DIR
        self._korean_font_enabled = False

        # Ensure chart directory exists
        Path(self.chart_dir).mkdir(parents=True, exist_ok=True)

        # Setup Korean font if enabled
        if enable_korean_font:
            self._korean_font_enabled = self.setup_korean_font()

        # Statistics
        self._charts_generated = 0
        self._chart_type_counts = {
            "THEME_BUBBLE": 0,
            "GEOPOLITICAL_TIMELINE": 0,
            "SECTOR_PERFORMANCE": 0,
        }
        self._chart_counter = 0  # Counter for unique filenames

    async def analyze(self, data: Dict[str, Any]) -> IntelligenceResult:
        """
        Generate chart (main entry point)

        Args:
            data: Chart configuration

        Returns:
            IntelligenceResult: Chart generation result
        """
        config = ChartConfig(**data) if isinstance(data, dict) else data
        return await self.generate_chart(config)

    async def generate_chart(
        self,
        config: ChartConfig,
    ) -> IntelligenceResult:
        """
        Generate chart based on configuration

        Args:
            config: Chart configuration

        Returns:
            IntelligenceResult: Chart generation result with file path
        """
        try:
            # Route to appropriate chart generator
            if config.chart_type == ChartType.THEME_BUBBLE:
                chart_result = await self._generate_theme_bubble(config)
            elif config.chart_type == ChartType.GEOPOLITICAL_TIMELINE:
                chart_result = await self._generate_timeline(config)
            elif config.chart_type == ChartType.SECTOR_PERFORMANCE:
                chart_result = await self._generate_sector_bar(config)
            else:
                # Unknown chart type
                chart_result = ChartResult(
                    chart_type=config.chart_type,
                    file_path="",
                    metadata={"error": f"Unknown chart type: {config.chart_type}"},
                )

            # Update statistics
            self._charts_generated += 1
            self._chart_type_counts[config.chart_type.value] += 1

            # Build reasoning
            reasoning = f"Generated {config.chart_type.value} chart: {chart_result.file_path}"

            return self.create_result(
                success=True,
                data={
                    "stage": "chart_generation",
                    "chart_type": chart_result.chart_type.value,
                    "file_path": chart_result.file_path,
                    "metadata": chart_result.metadata,
                },
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            result = self.create_result(
                success=False,
                data={"stage": "chart_generation"},
            )
            result.add_error(f"Generation error: {str(e)}")
            return result

    async def _generate_theme_bubble(self, config: ChartConfig) -> ChartResult:
        """
        Generate theme bubble chart

        Args:
            config: Chart configuration

        Returns:
            ChartResult: Bubble chart result
        """
        try:
            # Ensure Korean font is set for this chart
            if self._korean_font_enabled:
                self.setup_korean_font()

            if self.chart_renderer:
                # Use actual renderer
                render_result = await self.chart_renderer.render_bubble_chart(config)
                file_path = render_result.get("file_path", "")
            else:
                # Generate actual chart with matplotlib
                self._chart_counter += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = str(Path(self.chart_dir) / f"theme_bubble_{self._chart_counter}_{timestamp}.png")

                # Create bubble chart
                fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))

                themes = config.themes or []
                metrics = config.metrics or {}

                x_values = metrics.get("x", [0.5] * len(themes))
                y_values = metrics.get("y", [0.5] * len(themes))
                sizes = metrics.get("size", [100] * len(themes))
                colors = metrics.get("colors", None)

                # Create bubble chart
                scatter = ax.scatter(
                    x_values,
                    y_values,
                    s=sizes,
                    alpha=0.6,
                    c=colors if colors else range(len(themes)),
                    cmap='viridis',
                    edgecolors='black',
                    linewidth=1.5,
                )

                # Add theme labels
                for i, theme in enumerate(themes):
                    ax.annotate(
                        theme,
                        (x_values[i], y_values[i]),
                        fontsize=10,
                        ha='center',
                        va='center',
                        weight='bold',
                    )

                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_title(config.title or "테마 버블 차트", fontsize=14, weight='bold')
                ax.set_xlabel("X축", fontsize=12)
                ax.set_ylabel("Y축", fontsize=12)
                ax.grid(True, alpha=0.3)

                plt.tight_layout()
                plt.savefig(file_path, dpi=100, bbox_inches='tight')
                plt.close()

            return ChartResult(
                chart_type=ChartType.THEME_BUBBLE,
                file_path=file_path,
                metadata={
                    "themes": config.themes or [],
                    "metrics": config.metrics or {},
                    "korean_font_enabled": self._korean_font_enabled,
                },
            )

        except Exception as e:
            logger.error(f"Bubble chart generation error: {e}")
            return ChartResult(
                chart_type=ChartType.THEME_BUBBLE,
                file_path="",
                metadata={"error": str(e)},
            )

    async def _generate_timeline(self, config: ChartConfig) -> ChartResult:
        """
        Generate geopolitical timeline chart

        Args:
            config: Chart configuration

        Returns:
            ChartResult: Timeline chart result
        """
        try:
            # Ensure Korean font is set for this chart
            if self._korean_font_enabled:
                self.setup_korean_font()

            # Sort events chronologically
            events = config.events or []
            if events:
                events = sorted(events, key=lambda e: e.get("date", ""))

            if self.chart_renderer:
                render_result = await self.chart_renderer.render_timeline_chart(config)
                file_path = render_result.get("file_path", "")
            else:
                # Generate actual chart with matplotlib
                self._chart_counter += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = str(Path(self.chart_dir) / f"timeline_{self._chart_counter}_{timestamp}.png")

                # Create timeline chart
                fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))

                if events:
                    # Plot events on timeline
                    y_positions = range(len(events))
                    event_names = [e.get("name", f"Event {i+1}") for i, e in enumerate(events)]
                    event_dates = [e.get("date", "") for e in events]

                    ax.barh(y_positions, [1] * len(events), height=0.5, alpha=0.3, color='skyblue')

                    for i, (name, date) in enumerate(zip(event_names, event_dates)):
                        ax.text(0.5, i, f"{name}\n({date})", ha='center', va='center',
                               fontsize=9, weight='bold')

                ax.set_yticks(y_positions if events else [])
                ax.set_yticklabels([] if not events else [e.get("category", "이벤트") for e in events])
                ax.set_xlim(0, 1)
                ax.set_title(config.title or "지정학 타임라인", fontsize=14, weight='bold')
                ax.set_xlabel("", fontsize=12)
                ax.grid(True, axis='x', alpha=0.3)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_visible(False)

                plt.tight_layout()
                plt.savefig(file_path, dpi=100, bbox_inches='tight')
                plt.close()

            return ChartResult(
                chart_type=ChartType.GEOPOLITICAL_TIMELINE,
                file_path=file_path,
                metadata={
                    "events": events,
                    "event_count": len(events),
                    "korean_font_enabled": self._korean_font_enabled,
                },
            )

        except Exception as e:
            logger.error(f"Timeline chart generation error: {e}")
            return ChartResult(
                chart_type=ChartType.GEOPOLITICAL_TIMELINE,
                file_path="",
                metadata={"error": str(e)},
            )

    async def _generate_sector_bar(self, config: ChartConfig) -> ChartResult:
        """
        Generate sector performance bar chart

        Args:
            config: Chart configuration

        Returns:
            ChartResult: Bar chart result
        """
        try:
            # Ensure Korean font is set for this chart
            if self._korean_font_enabled:
                self.setup_korean_font()

            if self.chart_renderer:
                render_result = await self.chart_renderer.render_bar_chart(config)
                file_path = render_result.get("file_path", "")
            else:
                # Generate actual chart with matplotlib
                self._chart_counter += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = str(Path(self.chart_dir) / f"sector_performance_{self._chart_counter}_{timestamp}.png")

                # Create bar chart
                fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))

                sectors = config.sectors or []
                performance = config.metrics.get("performance", []) if config.metrics else []

                if sectors and performance:
                    # Color bars based on positive/negative performance
                    colors = ['green' if p >= 0 else 'red' for p in performance]

                    bars = ax.bar(sectors, performance, color=colors, alpha=0.7, edgecolor='black')

                    # Add value labels on bars
                    for bar, value in zip(bars, performance):
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width() / 2., height,
                               f'{value:.1f}%', ha='center', va='bottom' if value >= 0 else 'top',
                               fontsize=9, weight='bold')

                    # Add horizontal line at y=0
                    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)

                ax.set_title(config.title or "섹터 성과", fontsize=14, weight='bold')
                ax.set_xlabel("섹터", fontsize=12)
                ax.set_ylabel("성과 (%)", fontsize=12)
                ax.grid(True, axis='y', alpha=0.3)

                # Rotate x-axis labels if there are many sectors
                if len(sectors) > 5:
                    plt.xticks(rotation=45, ha='right')

                plt.tight_layout()
                plt.savefig(file_path, dpi=100, bbox_inches='tight')
                plt.close()

            return ChartResult(
                chart_type=ChartType.SECTOR_PERFORMANCE,
                file_path=file_path,
                metadata={
                    "sectors": config.sectors or [],
                    "performance": config.metrics.get("performance", []) if config.metrics else [],
                    "korean_font_enabled": self._korean_font_enabled,
                },
            )

        except Exception as e:
            logger.error(f"Bar chart generation error: {e}")
            return ChartResult(
                chart_type=ChartType.SECTOR_PERFORMANCE,
                file_path="",
                metadata={"error": str(e)},
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get chart generation statistics"""
        return {
            "total_charts": self._charts_generated,
            "theme_bubble_count": self._chart_type_counts["THEME_BUBBLE"],
            "timeline_count": self._chart_type_counts["GEOPOLITICAL_TIMELINE"],
            "sector_performance_count": self._chart_type_counts["SECTOR_PERFORMANCE"],
            "korean_font_enabled": self._korean_font_enabled,
            "available_korean_font": self.get_available_korean_font(),
        }


# ============================================================================
# Factory function
# ============================================================================

def create_chart_generator(
    llm_provider: Optional[LLMProvider] = None,
    chart_renderer: Optional[Any] = None,
    chart_dir: Optional[str] = None,
    enable_korean_font: bool = True,
) -> ChartGenerator:
    """
    Create ChartGenerator instance

    Args:
        llm_provider: LLM Provider (uses default if None)
        chart_renderer: Chart rendering service
        chart_dir: Directory for chart output
        enable_korean_font: Whether to enable Korean font support

    Returns:
        ChartGenerator: Configured generator instance
    """
    if llm_provider is None:
        from ..llm_providers import get_llm_provider
        llm_provider = get_llm_provider()

    return ChartGenerator(
        llm_provider=llm_provider,
        chart_renderer=chart_renderer,
        chart_dir=chart_dir,
        enable_korean_font=enable_korean_font,
    )
