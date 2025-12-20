"""
PDF Renderer - Render reports to PDF format

Features:
- ReportLab-based PDF generation
- Chart embedding using matplotlib
- Table rendering
- Professional formatting
- Logo and branding support

Author: AI Trading System Team
Date: 2025-11-25
"""

import logging
import io
from datetime import datetime
from typing import Optional
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Chart generation
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from backend.reporting.report_templates import (
    DailyReport,
    WeeklyReport,
    MonthlyReport,
    ChartData,
    TableData,
)

logger = logging.getLogger(__name__)


class PDFRenderer:
    """
    Renders reports to PDF using ReportLab.

    Supports:
    - Daily/Weekly/Monthly reports
    - Charts and tables
    - Professional formatting
    """

    def __init__(self):
        """Initialize PDF renderer."""
        self.page_width = letter[0]
        self.page_height = letter[1]
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        logger.info("PDFRenderer initialized")

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=TA_CENTER,
        ))

        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#374151'),
            spaceBefore=20,
            spaceAfter=12,
            borderWidth=1,
            borderColor=colors.HexColor('#e5e7eb'),
            borderPadding=8,
            backColor=colors.HexColor('#f9fafb'),
        ))

        # Metric label style
        self.styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6b7280'),
        ))

        # Metric value style
        self.styles.add(ParagraphStyle(
            name='MetricValue',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#111827'),
            fontName='Helvetica-Bold',
        ))

    def render_daily_report(self, report: DailyReport) -> bytes:
        """
        Render daily report to PDF.

        Args:
            report: DailyReport object

        Returns:
            PDF bytes
        """
        logger.info(f"Rendering daily report PDF for {report.report_date}")

        # Create PDF buffer
        buffer = io.BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Build content
        story = []

        # Title page
        story.extend(self._build_title_page(report))

        # Executive Summary
        if report.executive_summary:
            story.extend(self._build_executive_summary_section(report.executive_summary))

        # Trading Activity
        if report.trading_activity:
            story.extend(self._build_trading_activity_section(report.trading_activity))

        # Portfolio Overview
        if report.portfolio_overview:
            story.extend(self._build_portfolio_overview_section(report.portfolio_overview))

        # Charts
        if report.performance_chart:
            story.append(Spacer(1, 0.2*inch))
            chart_img = self._render_chart(report.performance_chart)
            if chart_img:
                story.append(chart_img)

        if report.pnl_chart:
            story.append(Spacer(1, 0.2*inch))
            chart_img = self._render_chart(report.pnl_chart)
            if chart_img:
                story.append(chart_img)

        # AI Performance
        if report.ai_performance:
            story.extend(self._build_ai_performance_section(report.ai_performance))

        # Risk Metrics
        if report.risk_metrics:
            story.extend(self._build_risk_metrics_section(report.risk_metrics))

        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            self.styles['MetricLabel']
        ))

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"Daily report PDF rendered ({len(pdf_bytes)} bytes)")

        return pdf_bytes

    def _build_title_page(self, report: DailyReport) -> list:
        """Build title page elements."""
        elements = []

        # Title
        title = f"Daily Trading Report"
        elements.append(Paragraph(title, self.styles['CustomTitle']))

        # Date
        date_text = report.report_date.strftime('%B %d, %Y')
        elements.append(Paragraph(date_text, self.styles['CustomHeading']))

        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_executive_summary_section(self, summary) -> list:
        """Build executive summary section."""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))

        # Key metrics table
        data = [
            ["Metric", "Value"],
            ["Portfolio Value", f"${summary.portfolio_value:,.2f}"],
            ["Daily P&L", self._format_pnl(summary.daily_pnl)],
            ["Daily Return", f"{summary.daily_return_pct:.2f}%"],
            ["Total Return", f"{summary.total_return_pct:.2f}%"],
            ["Trades Executed", str(summary.trades_count)],
        ]

        if summary.win_rate:
            data.append(["Win Rate", f"{summary.win_rate*100:.1f}%"])
        if summary.sharpe_ratio:
            data.append(["Sharpe Ratio", f"{summary.sharpe_ratio:.2f}"])

        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))

        # Highlights
        if summary.highlights:
            elements.append(Paragraph("<b>Highlights:</b>", self.styles['Normal']))
            for highlight in summary.highlights:
                elements.append(Paragraph(f"• {highlight}", self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))

        # Risk alerts
        if summary.risk_alerts:
            elements.append(Paragraph("<b>Risk Alerts:</b>", self.styles['Normal']))
            for alert in summary.risk_alerts:
                elements.append(Paragraph(f"• {alert}", self.styles['Normal']))

        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_trading_activity_section(self, activity) -> list:
        """Build trading activity section."""
        elements = []

        elements.append(Paragraph("Trading Activity", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))

        # Activity metrics
        data = [
            ["Metric", "Value"],
            ["Total Trades", str(activity.total_trades)],
            ["Buy Trades", str(activity.buy_trades)],
            ["Sell Trades", str(activity.sell_trades)],
            ["Total Volume", f"${activity.total_volume_usd:,.2f}"],
        ]

        if activity.win_rate:
            data.append(["Win Rate", f"{activity.win_rate*100:.1f}%"])
            data.append(["Wins", str(activity.win_count)])
            data.append(["Losses", str(activity.loss_count)])

        if activity.avg_slippage_bps:
            data.append(["Avg Slippage", f"{activity.avg_slippage_bps:.2f} bps"])

        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(self._get_default_table_style())

        elements.append(table)

        # Top trades table
        if activity.top_trades:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("<b>Top Trades:</b>", self.styles['Normal']))
            elements.append(Spacer(1, 0.05*inch))

            top_trades_table = self._build_table(activity.top_trades)
            elements.append(top_trades_table)

        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_portfolio_overview_section(self, portfolio) -> list:
        """Build portfolio overview section."""
        elements = []

        elements.append(Paragraph("Portfolio Overview", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))

        # Portfolio metrics
        data = [
            ["Metric", "Value"],
            ["Total Value", f"${portfolio.total_value:,.2f}"],
            ["Cash", f"${portfolio.cash:,.2f}"],
            ["Invested", f"${portfolio.invested_value:,.2f}"],
            ["Positions", str(portfolio.positions_count)],
        ]

        if portfolio.cash_pct:
            data.append(["Cash %", f"{portfolio.cash_pct*100:.1f}%"])

        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(self._get_default_table_style())

        elements.append(table)

        # Allocation
        if portfolio.sector_allocation:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("<b>Sector Allocation:</b>", self.styles['Normal']))

            sector_data = [["Sector", "Allocation %"]]
            for sector, pct in sorted(portfolio.sector_allocation.items(), key=lambda x: -x[1]):
                sector_data.append([sector, f"{pct:.1f}%"])

            sector_table = Table(sector_data, colWidths=[3*inch, 3*inch])
            sector_table.setStyle(self._get_default_table_style())
            elements.append(sector_table)

        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_ai_performance_section(self, ai_perf) -> list:
        """Build AI performance section."""
        elements = []

        elements.append(Paragraph("AI Performance", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))

        data = [
            ["Metric", "Value"],
            ["Signals Generated", str(ai_perf.signals_generated)],
            ["AI Cost", f"${ai_perf.ai_cost_usd:.4f}"],
            ["Tokens Used", f"{ai_perf.ai_tokens_used:,}"],
        ]

        if ai_perf.signal_avg_confidence:
            data.append(["Avg Confidence", f"{ai_perf.signal_avg_confidence*100:.1f}%"])
        if ai_perf.signal_accuracy:
            data.append(["Accuracy", f"{ai_perf.signal_accuracy*100:.1f}%"])
        if ai_perf.cost_per_signal:
            data.append(["Cost/Signal", f"${ai_perf.cost_per_signal:.4f}"])

        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(self._get_default_table_style())

        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_risk_metrics_section(self, risk) -> list:
        """Build risk metrics section."""
        elements = []

        elements.append(Paragraph("Risk Metrics", self.styles['CustomHeading']))
        elements.append(Spacer(1, 0.1*inch))

        data = [["Metric", "Value"]]

        if risk.sharpe_ratio:
            data.append(["Sharpe Ratio", f"{risk.sharpe_ratio:.2f}"])
        if risk.sortino_ratio:
            data.append(["Sortino Ratio", f"{risk.sortino_ratio:.2f}"])
        if risk.max_drawdown_pct:
            data.append(["Max Drawdown", f"{risk.max_drawdown_pct:.2f}%"])
        if risk.volatility_30d:
            data.append(["Volatility (30d)", f"{risk.volatility_30d:.2f}%"])
        if risk.var_95:
            data.append(["VaR (95%)", f"${risk.var_95:,.2f}"])

        data.append(["Circuit Breakers", str(risk.circuit_breaker_triggers)])
        data.append(["Kill Switch", "ACTIVE" if risk.kill_switch_active else "Inactive"])

        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(self._get_default_table_style())

        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_table(self, table_data: TableData) -> Table:
        """Build ReportLab table from TableData."""
        data = [table_data.headers] + table_data.rows

        if table_data.footer:
            data.append(table_data.footer)

        col_widths = [self.page_width / len(table_data.headers) - 0.3*inch] * len(table_data.headers)

        table = Table(data, colWidths=col_widths)
        table.setStyle(self._get_default_table_style())

        return table

    def _get_default_table_style(self) -> TableStyle:
        """Get default table style."""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
        ])

    def _render_chart(self, chart_data: ChartData) -> Optional[Image]:
        """
        Render chart using matplotlib and convert to ReportLab Image.

        Args:
            chart_data: ChartData object

        Returns:
            ReportLab Image or None
        """
        try:
            fig, ax = plt.subplots(figsize=(6, 4))

            if chart_data.chart_type == "line":
                for dataset in chart_data.datasets:
                    ax.plot(
                        chart_data.x_labels,
                        dataset['data'],
                        label=dataset.get('label'),
                        color=dataset.get('color', '#3b82f6'),
                    )

            elif chart_data.chart_type == "bar":
                for dataset in chart_data.datasets:
                    colors_list = dataset.get('backgroundColor', '#3b82f6')
                    ax.bar(
                        chart_data.x_labels,
                        dataset['data'],
                        label=dataset.get('label'),
                        color=colors_list,
                    )

            elif chart_data.chart_type == "area":
                for dataset in chart_data.datasets:
                    ax.fill_between(
                        chart_data.x_labels,
                        dataset['data'],
                        label=dataset.get('label'),
                        color=dataset.get('color', '#3b82f6'),
                        alpha=0.3,
                    )

            ax.set_title(chart_data.title, fontsize=12, fontweight='bold')

            if chart_data.x_axis_label:
                ax.set_xlabel(chart_data.x_axis_label)
            if chart_data.y_axis_label:
                ax.set_ylabel(chart_data.y_axis_label)

            ax.grid(True, alpha=0.3)
            ax.legend()

            # Rotate x-axis labels if many
            if len(chart_data.x_labels) > 10:
                plt.xticks(rotation=45, ha='right')

            plt.tight_layout()

            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)

            # Create ReportLab Image
            img = Image(img_buffer, width=5*inch, height=3.5*inch)

            return img

        except Exception as e:
            logger.error(f"Error rendering chart: {e}", exc_info=True)
            return None

    def _format_pnl(self, pnl: Decimal) -> str:
        """Format P&L with color indication."""
        if pnl > 0:
            return f"+${pnl:,.2f}"
        elif pnl < 0:
            return f"-${abs(pnl):,.2f}"
        else:
            return f"${pnl:,.2f}"


# =============================================================================
# Convenience Functions
# =============================================================================

def render_daily_report_pdf(report: DailyReport) -> bytes:
    """
    Render daily report to PDF.

    Args:
        report: DailyReport object

    Returns:
        PDF bytes
    """
    renderer = PDFRenderer()
    return renderer.render_daily_report(report)
