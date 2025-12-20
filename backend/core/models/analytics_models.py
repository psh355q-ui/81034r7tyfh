"""
Analytics Models - Historical analytics data storage

Stores aggregated metrics from Prometheus for historical analysis and reporting.

Features:
- Daily analytics aggregation
- Trade execution tracking
- Portfolio snapshots
- Signal performance validation
- Attribution data

Author: AI Trading System Team
Date: 2025-11-25
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, Boolean, JSON, BigInteger, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date
from backend.core.database import Base


class DailyAnalytics(Base):
    """
    Daily aggregated analytics from Prometheus metrics.

    Stores end-of-day snapshots for performance tracking and reporting.
    """
    __tablename__ = 'daily_analytics'

    # Primary key
    date = Column(Date, primary_key=True, index=True)

    # Portfolio metrics
    portfolio_value_eod = Column(Numeric(15, 2), nullable=False, comment="End-of-day portfolio value")
    daily_pnl = Column(Numeric(15, 2), nullable=False, comment="Daily profit/loss")
    daily_return_pct = Column(Numeric(10, 6), comment="Daily return percentage")
    cumulative_pnl = Column(Numeric(15, 2), comment="Cumulative PnL since inception")

    # Trading activity
    total_trades = Column(Integer, default=0, comment="Number of trades executed")
    buy_trades = Column(Integer, default=0)
    sell_trades = Column(Integer, default=0)
    total_volume_usd = Column(Numeric(15, 2), comment="Total trading volume")

    # Performance metrics
    win_count = Column(Integer, default=0, comment="Winning trades")
    loss_count = Column(Integer, default=0, comment="Losing trades")
    win_rate = Column(Numeric(5, 4), comment="Win rate (0-1)")
    avg_win_pct = Column(Numeric(10, 6), comment="Average winning trade %")
    avg_loss_pct = Column(Numeric(10, 6), comment="Average losing trade %")

    # Risk metrics
    sharpe_ratio = Column(Numeric(10, 4), comment="Sharpe ratio")
    sortino_ratio = Column(Numeric(10, 4), comment="Sortino ratio")
    max_drawdown_pct = Column(Numeric(10, 6), comment="Maximum drawdown %")
    volatility_30d = Column(Numeric(10, 6), comment="30-day volatility")
    var_95 = Column(Numeric(15, 2), comment="Value at Risk (95% confidence)")

    # AI metrics
    ai_cost_usd = Column(Numeric(10, 4), nullable=False, default=0, comment="Daily AI API costs")
    ai_tokens_used = Column(BigInteger, default=0, comment="Total tokens consumed")
    signals_generated = Column(Integer, default=0, comment="AI signals generated")
    signal_avg_confidence = Column(Numeric(5, 4), comment="Average signal confidence")
    signal_accuracy = Column(Numeric(5, 4), comment="Signal accuracy (if resolved)")

    # Execution quality
    avg_slippage_bps = Column(Numeric(8, 2), comment="Average slippage in basis points")
    avg_execution_time_ms = Column(Numeric(10, 2), comment="Average execution time in ms")

    # Position metrics
    positions_count = Column(Integer, default=0, comment="Number of open positions")
    avg_position_size_usd = Column(Numeric(15, 2), comment="Average position size")
    max_position_size_usd = Column(Numeric(15, 2), comment="Largest position size")

    # Risk management
    circuit_breaker_triggers = Column(Integer, default=0, comment="Circuit breaker activations")
    kill_switch_active = Column(Boolean, default=False, comment="Kill switch status")
    alerts_triggered = Column(Integer, default=0, comment="Total alerts triggered")

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(String, comment="Optional notes for the day")

    # Indexes
    __table_args__ = (
        Index('idx_daily_analytics_date', 'date'),
        Index('idx_daily_analytics_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<DailyAnalytics(date={self.date}, portfolio_value={self.portfolio_value_eod}, pnl={self.daily_pnl})>"


class TradeExecution(Base):
    """
    Individual trade execution records for detailed analysis.

    Tracks every trade execution with full details for performance attribution.
    """
    __tablename__ = 'trade_executions'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Trade identification
    trade_id = Column(String, unique=True, nullable=False, index=True, comment="Unique trade identifier")
    ticker = Column(String(10), nullable=False, index=True, comment="Stock ticker")
    action = Column(String(10), nullable=False, comment="BUY/SELL")

    # Timing
    signal_timestamp = Column(DateTime, nullable=False, comment="When signal was generated")
    execution_timestamp = Column(DateTime, nullable=False, index=True, comment="When trade was executed")
    exit_timestamp = Column(DateTime, comment="When position was closed")

    # Prices
    signal_price = Column(Numeric(10, 2), comment="Price when signal generated")
    entry_price = Column(Numeric(10, 2), nullable=False, comment="Actual entry price")
    exit_price = Column(Numeric(10, 2), comment="Actual exit price")
    target_price = Column(Numeric(10, 2), comment="AI target price")
    stop_loss_price = Column(Numeric(10, 2), comment="Stop loss price")

    # Position sizing
    shares = Column(Integer, nullable=False, comment="Number of shares")
    position_size_usd = Column(Numeric(15, 2), nullable=False, comment="Position size in USD")
    portfolio_pct = Column(Numeric(5, 4), comment="% of portfolio")

    # Performance
    pnl_usd = Column(Numeric(15, 2), comment="Profit/Loss in USD")
    pnl_pct = Column(Numeric(10, 6), comment="Profit/Loss percentage")
    is_win = Column(Boolean, comment="True if profitable")
    hold_duration_hours = Column(Numeric(10, 2), comment="How long position was held")

    # Execution quality
    slippage_bps = Column(Numeric(8, 2), comment="Slippage in basis points")
    execution_time_ms = Column(Numeric(10, 2), comment="Time to execute in ms")
    commission_usd = Column(Numeric(10, 4), default=0, comment="Trading commission")

    # AI attribution
    ai_source = Column(String(50), comment="claude/gemini/chatgpt/ensemble")
    signal_confidence = Column(Numeric(5, 4), comment="AI confidence (0-1)")
    signal_reason = Column(String, comment="AI reasoning for signal")
    rag_documents_used = Column(Integer, default=0, comment="RAG documents consulted")

    # Strategy attribution
    strategy_name = Column(String(100), comment="Strategy that generated signal")
    market_regime = Column(String(20), comment="bull/bear/sideways/volatile")
    sector = Column(String(50), comment="Stock sector")

    # Risk metrics
    risk_score = Column(Numeric(5, 4), comment="Risk score at entry (0-1)")
    position_risk_pct = Column(Numeric(5, 4), comment="Risk as % of portfolio")

    # Status
    status = Column(String(20), nullable=False, default='OPEN', comment="OPEN/CLOSED/CANCELLED")
    exit_reason = Column(String(100), comment="Why position was closed")

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    trade_metadata = Column(JSONB, comment="Additional trade metadata")

    # Indexes
    __table_args__ = (
        Index('idx_trade_ticker', 'ticker'),
        Index('idx_trade_execution_timestamp', 'execution_timestamp'),
        Index('idx_trade_status', 'status'),
        Index('idx_trade_ai_source', 'ai_source'),
        Index('idx_trade_strategy', 'strategy_name'),
        Index('idx_trade_market_regime', 'market_regime'),
    )

    def __repr__(self):
        return f"<TradeExecution(id={self.trade_id}, ticker={self.ticker}, action={self.action}, pnl={self.pnl_usd})>"


class PortfolioSnapshot(Base):
    """
    Daily portfolio snapshots for historical analysis.

    Captures complete portfolio state including all positions and allocations.
    """
    __tablename__ = 'portfolio_snapshots'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False, index=True, comment="Date of snapshot")
    snapshot_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Exact time of snapshot")

    # Portfolio totals
    total_value = Column(Numeric(15, 2), nullable=False, comment="Total portfolio value")
    cash = Column(Numeric(15, 2), nullable=False, comment="Cash balance")
    invested_value = Column(Numeric(15, 2), nullable=False, comment="Value in positions")

    # Position details (JSONB for flexibility)
    positions = Column(JSONB, nullable=False, comment="Array of position objects")
    # positions structure:
    # [
    #   {
    #     "ticker": "AAPL",
    #     "shares": 100,
    #     "entry_price": 150.0,
    #     "current_price": 155.0,
    #     "value": 15500.0,
    #     "pnl": 500.0,
    #     "pnl_pct": 3.33,
    #     "portfolio_pct": 15.5,
    #     "sector": "Technology",
    #     "days_held": 5
    #   }
    # ]

    # Allocation breakdown
    sector_allocation = Column(JSONB, comment="Allocation by sector")
    # {"Technology": 45.2, "Healthcare": 30.1, "Finance": 24.7}

    strategy_allocation = Column(JSONB, comment="Allocation by strategy")
    # {"Bull Momentum": 60.0, "Range Trading": 40.0}

    # Risk metrics
    positions_count = Column(Integer, nullable=False, comment="Number of positions")
    avg_position_size = Column(Numeric(15, 2), comment="Average position size")
    largest_position_pct = Column(Numeric(5, 4), comment="Largest position as % of portfolio")
    cash_pct = Column(Numeric(5, 4), comment="Cash as % of portfolio")

    # Performance since inception
    total_pnl = Column(Numeric(15, 2), comment="Total unrealized + realized PnL")
    total_return_pct = Column(Numeric(10, 6), comment="Total return %")

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(String, comment="Optional snapshot notes")

    # Indexes
    __table_args__ = (
        Index('idx_portfolio_snapshot_date', 'snapshot_date'),
        Index('idx_portfolio_snapshot_timestamp', 'snapshot_timestamp'),
    )

    def __repr__(self):
        return f"<PortfolioSnapshot(date={self.snapshot_date}, value={self.total_value}, positions={self.positions_count})>"


class SignalPerformance(Base):
    """
    AI signal performance tracking for validation and optimization.

    Links to analysis_validator.py for accuracy tracking.
    """
    __tablename__ = 'signal_performance'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String, unique=True, nullable=False, index=True, comment="Unique signal identifier")

    # Signal details
    ticker = Column(String(10), nullable=False, index=True)
    signal = Column(String(10), nullable=False, comment="BUY/SELL/HOLD")
    confidence = Column(Numeric(5, 4), nullable=False, comment="AI confidence (0-1)")

    # AI source
    source = Column(String(50), nullable=False, index=True, comment="claude/gemini/chatgpt/ensemble")
    model_version = Column(String(50), comment="Model version used")

    # Context
    generated_at = Column(DateTime, nullable=False, index=True, comment="When signal was generated")
    market_regime = Column(String(20), comment="Market regime at signal time")

    # Prices
    signal_price = Column(Numeric(10, 2), nullable=False, comment="Price when signal generated")
    target_price = Column(Numeric(10, 2), comment="AI target price")
    stop_loss = Column(Numeric(10, 2), comment="Suggested stop loss")

    # Resolution
    time_horizon_days = Column(Integer, default=5, comment="Expected time to target")
    resolution_date = Column(Date, comment="When signal was resolved")
    actual_price = Column(Numeric(10, 2), comment="Actual price at resolution")

    # Outcome
    outcome = Column(String(20), comment="WIN/LOSS/NEUTRAL/PENDING")
    return_pct = Column(Numeric(10, 6), comment="Actual return %")
    target_hit = Column(Boolean, comment="Did price reach target?")
    stop_loss_hit = Column(Boolean, comment="Did price hit stop loss?")

    # RAG context
    rag_documents_used = Column(Integer, default=0, comment="Number of RAG documents used")
    rag_relevance_score = Column(Numeric(5, 4), comment="RAG relevance score (0-1)")
    rag_document_ids = Column(JSONB, comment="List of document IDs used")

    # Validation metrics
    confidence_calibration_error = Column(Numeric(10, 6), comment="Confidence vs actual accuracy")

    # Status
    status = Column(String(20), nullable=False, default='PENDING', comment="PENDING/RESOLVED/EXPIRED")

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    signal_metadata = Column(JSONB, comment="Additional signal metadata")

    # Indexes
    __table_args__ = (
        Index('idx_signal_ticker', 'ticker'),
        Index('idx_signal_source', 'source'),
        Index('idx_signal_generated_at', 'generated_at'),
        Index('idx_signal_status', 'status'),
        Index('idx_signal_outcome', 'outcome'),
        Index('idx_signal_market_regime', 'market_regime'),
    )

    def __repr__(self):
        return f"<SignalPerformance(id={self.signal_id}, ticker={self.ticker}, signal={self.signal}, outcome={self.outcome})>"


class WeeklyAnalytics(Base):
    """
    Weekly aggregated analytics for weekly reports.

    Aggregates daily analytics into weekly summaries.
    """
    __tablename__ = 'weekly_analytics'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    week_number = Column(Integer, nullable=False, index=True, comment="ISO week number (1-53)")
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)

    # Portfolio metrics
    portfolio_value_start = Column(Numeric(15, 2), nullable=False)
    portfolio_value_end = Column(Numeric(15, 2), nullable=False)
    weekly_pnl = Column(Numeric(15, 2), nullable=False)
    weekly_return_pct = Column(Numeric(10, 6))

    # Trading activity
    total_trades = Column(Integer, default=0)
    total_volume_usd = Column(Numeric(15, 2))
    avg_daily_trades = Column(Numeric(8, 2))

    # Performance
    win_count = Column(Integer, default=0)
    loss_count = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 4))
    sharpe_ratio = Column(Numeric(10, 4))
    max_drawdown_pct = Column(Numeric(10, 6))

    # AI costs
    total_ai_cost_usd = Column(Numeric(10, 4), nullable=False, default=0)
    avg_daily_ai_cost = Column(Numeric(10, 4))

    # Best/Worst days
    best_day_date = Column(Date)
    best_day_return_pct = Column(Numeric(10, 6))
    worst_day_date = Column(Date)
    worst_day_return_pct = Column(Numeric(10, 6))

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_weekly_analytics_year_week', 'year', 'week_number', unique=True),
        Index('idx_weekly_analytics_start_date', 'week_start_date'),
    )

    def __repr__(self):
        return f"<WeeklyAnalytics(year={self.year}, week={self.week_number}, pnl={self.weekly_pnl})>"


class MonthlyAnalytics(Base):
    """
    Monthly aggregated analytics for monthly reports.

    Aggregates daily/weekly analytics into monthly summaries.
    """
    __tablename__ = 'monthly_analytics'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True, comment="Month number (1-12)")

    # Portfolio metrics
    portfolio_value_start = Column(Numeric(15, 2), nullable=False)
    portfolio_value_end = Column(Numeric(15, 2), nullable=False)
    monthly_pnl = Column(Numeric(15, 2), nullable=False)
    monthly_return_pct = Column(Numeric(10, 6))

    # Trading activity
    total_trades = Column(Integer, default=0)
    total_volume_usd = Column(Numeric(15, 2))
    trading_days = Column(Integer, comment="Number of trading days")

    # Performance
    win_count = Column(Integer, default=0)
    loss_count = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 4))
    sharpe_ratio = Column(Numeric(10, 4))
    sortino_ratio = Column(Numeric(10, 4))
    max_drawdown_pct = Column(Numeric(10, 6))

    # AI costs
    total_ai_cost_usd = Column(Numeric(10, 4), nullable=False, default=0)
    avg_daily_ai_cost = Column(Numeric(10, 4))
    total_tokens_used = Column(BigInteger)

    # Best/Worst performance
    best_week_return_pct = Column(Numeric(10, 6))
    worst_week_return_pct = Column(Numeric(10, 6))

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(String, comment="Monthly commentary")

    # Indexes
    __table_args__ = (
        Index('idx_monthly_analytics_year_month', 'year', 'month', unique=True),
    )

    def __repr__(self):
        return f"<MonthlyAnalytics(year={self.year}, month={self.month}, pnl={self.monthly_pnl})>"
