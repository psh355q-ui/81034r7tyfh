"""
Report Templates - Data structures for reports

Defines the structure and sections for each report type:
- Daily Report
- Weekly Report
- Monthly Report
- Custom Report

Author: AI Trading System Team
Date: 2025-11-25
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import date, datetime
from decimal import Decimal


@dataclass
class ChartData:
    """Chart data for visualization."""
    chart_type: str  # line, bar, pie, area
    title: str
    x_labels: List[str]
    datasets: List[Dict]  # [{"label": "PnL", "data": [...], "color": "#..."}]
    y_axis_label: Optional[str] = None
    x_axis_label: Optional[str] = None


@dataclass
class TableData:
    """Table data for tabular display."""
    title: str
    headers: List[str]
    rows: List[List]  # List of rows, each row is a list of values
    footer: Optional[List[str]] = None


@dataclass
class MetricCard:
    """Single metric card for dashboard-style display."""
    label: str
    value: str
    change: Optional[str] = None  # "+5.2%"
    change_type: Optional[str] = None  # "positive", "negative", "neutral"
    icon: Optional[str] = None


@dataclass
class ExecutiveSummary:
    """Executive summary section."""
    portfolio_value: Decimal
    daily_pnl: Decimal
    daily_return_pct: Decimal
    total_return_pct: Decimal
    win_rate: Optional[Decimal]
    sharpe_ratio: Optional[Decimal]
    positions_count: int
    trades_count: int
    ai_cost_usd: Decimal

    # Highlights (bullet points)
    highlights: List[str] = field(default_factory=list)

    # Risk alerts
    risk_alerts: List[str] = field(default_factory=list)


@dataclass
class TradingActivity:
    """Trading activity section."""
    total_trades: int
    buy_trades: int
    sell_trades: int
    total_volume_usd: Decimal
    avg_position_size_usd: Optional[Decimal]

    # Win/Loss breakdown
    win_count: int
    loss_count: int
    win_rate: Optional[Decimal]
    avg_win_pct: Optional[Decimal]
    avg_loss_pct: Optional[Decimal]

    # Execution quality
    avg_slippage_bps: Optional[Decimal]
    avg_execution_time_ms: Optional[Decimal]

    # Top trades (table)
    top_trades: Optional[TableData] = None


@dataclass
class PortfolioOverview:
    """Portfolio overview section."""
    total_value: Decimal
    cash: Decimal
    invested_value: Decimal
    positions_count: int

    # Allocation (pie charts)
    sector_allocation: Dict[str, float]  # {"Technology": 45.2, ...}
    strategy_allocation: Dict[str, float]  # {"Bull Momentum": 60.0, ...}

    # Top positions (table)
    top_positions: Optional[TableData] = None

    # Risk metrics
    largest_position_pct: Optional[Decimal] = None
    cash_pct: Optional[Decimal] = None


@dataclass
class AIPerformance:
    """AI performance section."""
    signals_generated: int
    signal_avg_confidence: Optional[Decimal]
    signal_accuracy: Optional[Decimal]

    # Cost breakdown
    ai_cost_usd: Decimal
    ai_tokens_used: int
    cost_per_signal: Optional[Decimal] = None

    # Source comparison (chart)
    source_comparison: Optional[ChartData] = None

    # RAG impact
    rag_impact_summary: Optional[str] = None


@dataclass
class RiskMetrics:
    """Risk metrics section."""
    sharpe_ratio: Optional[Decimal]
    sortino_ratio: Optional[Decimal]
    max_drawdown_pct: Optional[Decimal]
    volatility_30d: Optional[Decimal]
    var_95: Optional[Decimal]

    # Circuit breaker status
    circuit_breaker_triggers: int = 0
    kill_switch_active: bool = False
    alerts_triggered: int = 0

    # Risk chart (drawdown over time)
    drawdown_chart: Optional[ChartData] = None


@dataclass
class PerformanceAttribution:
    """Performance attribution section."""
    # By strategy
    strategy_returns: Dict[str, Decimal]  # {"Bull Momentum": 2.5, ...}

    # By sector
    sector_returns: Dict[str, Decimal]  # {"Technology": 3.2, ...}

    # By AI source
    ai_source_returns: Dict[str, Decimal]  # {"claude": 2.8, ...}

    # Attribution chart
    attribution_chart: Optional[ChartData] = None


@dataclass
class DailyReport:
    """
    Complete daily report structure.

    Sections:
    1. Executive Summary
    2. Trading Activity
    3. Portfolio Overview
    4. AI Performance
    5. Risk Metrics
    """
    report_id: str
    report_type: str = "daily"
    report_date: date = None
    generated_at: datetime = None

    # Sections
    executive_summary: Optional[ExecutiveSummary] = None
    trading_activity: Optional[TradingActivity] = None
    portfolio_overview: Optional[PortfolioOverview] = None
    ai_performance: Optional[AIPerformance] = None
    risk_metrics: Optional[RiskMetrics] = None

    # Charts
    performance_chart: Optional[ChartData] = None  # Portfolio value over time
    pnl_chart: Optional[ChartData] = None  # Daily PnL
    
    # Narrative Analysis (LLM Generated)
    narrative_analysis: Optional[str] = None

    # Metadata
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "executive_summary": self._summary_to_dict() if self.executive_summary else None,
            "trading_activity": self._trading_to_dict() if self.trading_activity else None,
            "portfolio_overview": self._portfolio_to_dict() if self.portfolio_overview else None,
            "ai_performance": self._ai_to_dict() if self.ai_performance else None,
            "risk_metrics": self._risk_to_dict() if self.risk_metrics else None,
            "performance_chart": self._chart_to_dict(self.performance_chart) if self.performance_chart else None,
            "pnl_chart": self._chart_to_dict(self.pnl_chart) if self.pnl_chart else None,
            "notes": self.notes,
        }

    def _summary_to_dict(self) -> Dict:
        es = self.executive_summary
        return {
            "portfolio_value": float(es.portfolio_value),
            "daily_pnl": float(es.daily_pnl),
            "daily_return_pct": float(es.daily_return_pct),
            "total_return_pct": float(es.total_return_pct),
            "win_rate": float(es.win_rate) if es.win_rate else None,
            "sharpe_ratio": float(es.sharpe_ratio) if es.sharpe_ratio else None,
            "positions_count": es.positions_count,
            "trades_count": es.trades_count,
            "ai_cost_usd": float(es.ai_cost_usd),
            "highlights": es.highlights,
            "risk_alerts": es.risk_alerts,
        }

    def _trading_to_dict(self) -> Dict:
        ta = self.trading_activity
        return {
            "total_trades": ta.total_trades,
            "buy_trades": ta.buy_trades,
            "sell_trades": ta.sell_trades,
            "total_volume_usd": float(ta.total_volume_usd),
            "avg_position_size_usd": float(ta.avg_position_size_usd) if ta.avg_position_size_usd else None,
            "win_count": ta.win_count,
            "loss_count": ta.loss_count,
            "win_rate": float(ta.win_rate) if ta.win_rate else None,
            "avg_win_pct": float(ta.avg_win_pct) if ta.avg_win_pct else None,
            "avg_loss_pct": float(ta.avg_loss_pct) if ta.avg_loss_pct else None,
            "avg_slippage_bps": float(ta.avg_slippage_bps) if ta.avg_slippage_bps else None,
            "avg_execution_time_ms": float(ta.avg_execution_time_ms) if ta.avg_execution_time_ms else None,
            "top_trades": self._table_to_dict(ta.top_trades) if ta.top_trades else None,
        }

    def _portfolio_to_dict(self) -> Dict:
        po = self.portfolio_overview
        return {
            "total_value": float(po.total_value),
            "cash": float(po.cash),
            "invested_value": float(po.invested_value),
            "positions_count": po.positions_count,
            "sector_allocation": po.sector_allocation,
            "strategy_allocation": po.strategy_allocation,
            "top_positions": self._table_to_dict(po.top_positions) if po.top_positions else None,
            "largest_position_pct": float(po.largest_position_pct) if po.largest_position_pct else None,
            "cash_pct": float(po.cash_pct) if po.cash_pct else None,
        }

    def _ai_to_dict(self) -> Dict:
        ai = self.ai_performance
        return {
            "signals_generated": ai.signals_generated,
            "signal_avg_confidence": float(ai.signal_avg_confidence) if ai.signal_avg_confidence else None,
            "signal_accuracy": float(ai.signal_accuracy) if ai.signal_accuracy else None,
            "ai_cost_usd": float(ai.ai_cost_usd),
            "ai_tokens_used": ai.ai_tokens_used,
            "cost_per_signal": float(ai.cost_per_signal) if ai.cost_per_signal else None,
            "source_comparison": self._chart_to_dict(ai.source_comparison) if ai.source_comparison else None,
            "rag_impact_summary": ai.rag_impact_summary,
        }

    def _risk_to_dict(self) -> Dict:
        rm = self.risk_metrics
        return {
            "sharpe_ratio": float(rm.sharpe_ratio) if rm.sharpe_ratio else None,
            "sortino_ratio": float(rm.sortino_ratio) if rm.sortino_ratio else None,
            "max_drawdown_pct": float(rm.max_drawdown_pct) if rm.max_drawdown_pct else None,
            "volatility_30d": float(rm.volatility_30d) if rm.volatility_30d else None,
            "var_95": float(rm.var_95) if rm.var_95 else None,
            "circuit_breaker_triggers": rm.circuit_breaker_triggers,
            "kill_switch_active": rm.kill_switch_active,
            "alerts_triggered": rm.alerts_triggered,
            "drawdown_chart": self._chart_to_dict(rm.drawdown_chart) if rm.drawdown_chart else None,
        }

    def _chart_to_dict(self, chart: Optional[ChartData]) -> Optional[Dict]:
        if not chart:
            return None
        return {
            "chart_type": chart.chart_type,
            "title": chart.title,
            "x_labels": chart.x_labels,
            "datasets": chart.datasets,
            "y_axis_label": chart.y_axis_label,
            "x_axis_label": chart.x_axis_label,
        }

    def _table_to_dict(self, table: Optional[TableData]) -> Optional[Dict]:
        if not table:
            return None
        return {
            "title": table.title,
            "headers": table.headers,
            "rows": table.rows,
            "footer": table.footer,
        }


@dataclass
class WeeklyReport:
    """
    Weekly report structure.

    Similar to daily but with weekly aggregation and trends.
    """
    report_id: str
    report_type: str = "weekly"
    year: int = None
    week_number: int = None
    week_start_date: date = None
    week_end_date: date = None
    generated_at: datetime = None

    # Weekly summary
    portfolio_value_start: Optional[Decimal] = None
    portfolio_value_end: Optional[Decimal] = None
    weekly_pnl: Optional[Decimal] = None
    weekly_return_pct: Optional[Decimal] = None

    # Trading activity
    total_trades: int = 0
    win_rate: Optional[Decimal] = None

    # Charts
    daily_pnl_chart: Optional[ChartData] = None
    daily_trades_chart: Optional[ChartData] = None

    # Best/Worst days
    best_day_date: Optional[date] = None
    best_day_return_pct: Optional[Decimal] = None
    worst_day_date: Optional[date] = None
    worst_day_return_pct: Optional[Decimal] = None

    # Notes
    notes: Optional[str] = None


@dataclass
class MonthlyReport:
    """
    Monthly report structure.

    Comprehensive monthly summary with trends and attribution.
    """
    report_id: str
    report_type: str = "monthly"
    year: int = None
    month: int = None
    generated_at: datetime = None

    # Monthly summary
    portfolio_value_start: Optional[Decimal] = None
    portfolio_value_end: Optional[Decimal] = None
    monthly_pnl: Optional[Decimal] = None
    monthly_return_pct: Optional[Decimal] = None

    # Trading activity
    total_trades: int = 0
    trading_days: int = 0
    win_rate: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None

    # AI costs
    total_ai_cost_usd: Optional[Decimal] = None
    total_tokens_used: int = 0

    # Performance attribution
    attribution: Optional[PerformanceAttribution] = None

    # Charts
    weekly_performance_chart: Optional[ChartData] = None
    sector_returns_chart: Optional[ChartData] = None

    # Notes
    notes: Optional[str] = None


# =============================================================================
# Report Builder Helpers
# =============================================================================

def create_metric_cards(data: Dict) -> List[MetricCard]:
    """Create metric cards from data dictionary."""
    cards = []

    if "portfolio_value" in data:
        cards.append(MetricCard(
            label="Portfolio Value",
            value=f"${data['portfolio_value']:,.2f}",
            icon="💼"
        ))

    if "daily_pnl" in data:
        pnl = data['daily_pnl']
        cards.append(MetricCard(
            label="Daily P&L",
            value=f"${pnl:,.2f}",
            change=f"{data.get('daily_return_pct', 0):.2f}%",
            change_type="positive" if pnl > 0 else "negative" if pnl < 0 else "neutral",
            icon="📊"
        ))

    if "win_rate" in data and data['win_rate']:
        cards.append(MetricCard(
            label="Win Rate",
            value=f"{data['win_rate']*100:.1f}%",
            icon="🎯"
        ))

    if "sharpe_ratio" in data and data['sharpe_ratio']:
        cards.append(MetricCard(
            label="Sharpe Ratio",
            value=f"{data['sharpe_ratio']:.2f}",
            icon="📈"
        ))

    return cards


def format_currency(value: Decimal) -> str:
    """Format decimal as currency string."""
    return f"${value:,.2f}"


def format_percentage(value: Decimal, decimals: int = 2) -> str:
    """Format decimal as percentage string."""
    return f"{value:.{decimals}f}%"


def generate_report_id(report_type: str, target_date: date) -> str:
    """Generate unique report ID."""
    return f"{report_type}_{target_date.isoformat()}_{datetime.utcnow().strftime('%H%M%S')}"
