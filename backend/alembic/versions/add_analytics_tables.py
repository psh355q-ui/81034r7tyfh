"""
Add analytics tables for Phase 15 - Advanced Analytics & Reporting.

Revision ID: analytics_001
Revises: rag_embedding_001
Create Date: 2025-11-25

Tables:
1. daily_analytics: Daily aggregated metrics
2. trade_executions: Individual trade records
3. portfolio_snapshots: Daily portfolio snapshots
4. signal_performance: AI signal tracking
5. weekly_analytics: Weekly aggregated metrics
6. monthly_analytics: Monthly aggregated metrics
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "analytics_001"
down_revision = "rag_embedding_001"
branch_labels = None
depends_on = None


def upgrade():
    """Create analytics tables."""

    # 1. Daily Analytics Table
    op.create_table(
        "daily_analytics",
        sa.Column("date", sa.Date, primary_key=True),
        # Portfolio metrics
        sa.Column("portfolio_value_eod", sa.Numeric(15, 2), nullable=False),
        sa.Column("daily_pnl", sa.Numeric(15, 2), nullable=False),
        sa.Column("daily_return_pct", sa.Numeric(10, 6)),
        sa.Column("cumulative_pnl", sa.Numeric(15, 2)),
        # Trading activity
        sa.Column("total_trades", sa.Integer, default=0),
        sa.Column("buy_trades", sa.Integer, default=0),
        sa.Column("sell_trades", sa.Integer, default=0),
        sa.Column("total_volume_usd", sa.Numeric(15, 2)),
        # Performance metrics
        sa.Column("win_count", sa.Integer, default=0),
        sa.Column("loss_count", sa.Integer, default=0),
        sa.Column("win_rate", sa.Numeric(5, 4)),
        sa.Column("avg_win_pct", sa.Numeric(10, 6)),
        sa.Column("avg_loss_pct", sa.Numeric(10, 6)),
        # Risk metrics
        sa.Column("sharpe_ratio", sa.Numeric(10, 4)),
        sa.Column("sortino_ratio", sa.Numeric(10, 4)),
        sa.Column("max_drawdown_pct", sa.Numeric(10, 6)),
        sa.Column("volatility_30d", sa.Numeric(10, 6)),
        sa.Column("var_95", sa.Numeric(15, 2)),
        # AI metrics
        sa.Column("ai_cost_usd", sa.Numeric(10, 4), nullable=False, default=0),
        sa.Column("ai_tokens_used", sa.BigInteger, default=0),
        sa.Column("signals_generated", sa.Integer, default=0),
        sa.Column("signal_avg_confidence", sa.Numeric(5, 4)),
        sa.Column("signal_accuracy", sa.Numeric(5, 4)),
        # Execution quality
        sa.Column("avg_slippage_bps", sa.Numeric(8, 2)),
        sa.Column("avg_execution_time_ms", sa.Numeric(10, 2)),
        # Position metrics
        sa.Column("positions_count", sa.Integer, default=0),
        sa.Column("avg_position_size_usd", sa.Numeric(15, 2)),
        sa.Column("max_position_size_usd", sa.Numeric(15, 2)),
        # Risk management
        sa.Column("circuit_breaker_triggers", sa.Integer, default=0),
        sa.Column("kill_switch_active", sa.Boolean, default=False),
        sa.Column("alerts_triggered", sa.Integer, default=0),
        # Metadata
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("notes", sa.String),
    )

    # Indexes for daily_analytics
    op.create_index("idx_daily_analytics_date", "daily_analytics", ["date"])
    op.create_index("idx_daily_analytics_created_at", "daily_analytics", ["created_at"])

    # 2. Trade Executions Table
    op.create_table(
        "trade_executions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        # Trade identification
        sa.Column("trade_id", sa.String, unique=True, nullable=False),
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column("action", sa.String(10), nullable=False),
        # Timing
        sa.Column("signal_timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("execution_timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("exit_timestamp", sa.TIMESTAMP(timezone=True)),
        # Prices
        sa.Column("signal_price", sa.Numeric(10, 2)),
        sa.Column("entry_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("exit_price", sa.Numeric(10, 2)),
        sa.Column("target_price", sa.Numeric(10, 2)),
        sa.Column("stop_loss_price", sa.Numeric(10, 2)),
        # Position sizing
        sa.Column("shares", sa.Integer, nullable=False),
        sa.Column("position_size_usd", sa.Numeric(15, 2), nullable=False),
        sa.Column("portfolio_pct", sa.Numeric(5, 4)),
        # Performance
        sa.Column("pnl_usd", sa.Numeric(15, 2)),
        sa.Column("pnl_pct", sa.Numeric(10, 6)),
        sa.Column("is_win", sa.Boolean),
        sa.Column("hold_duration_hours", sa.Numeric(10, 2)),
        # Execution quality
        sa.Column("slippage_bps", sa.Numeric(8, 2)),
        sa.Column("execution_time_ms", sa.Numeric(10, 2)),
        sa.Column("commission_usd", sa.Numeric(10, 4), default=0),
        # AI attribution
        sa.Column("ai_source", sa.String(50)),
        sa.Column("signal_confidence", sa.Numeric(5, 4)),
        sa.Column("signal_reason", sa.String),
        sa.Column("rag_documents_used", sa.Integer, default=0),
        # Strategy attribution
        sa.Column("strategy_name", sa.String(100)),
        sa.Column("market_regime", sa.String(20)),
        sa.Column("sector", sa.String(50)),
        # Risk metrics
        sa.Column("risk_score", sa.Numeric(5, 4)),
        sa.Column("position_risk_pct", sa.Numeric(5, 4)),
        # Status
        sa.Column("status", sa.String(20), nullable=False, default="OPEN"),
        sa.Column("exit_reason", sa.String(100)),
        # Metadata
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("metadata", postgresql.JSONB),
    )

    # Indexes for trade_executions
    op.create_index("idx_trade_ticker", "trade_executions", ["ticker"])
    op.create_index("idx_trade_execution_timestamp", "trade_executions", ["execution_timestamp"])
    op.create_index("idx_trade_status", "trade_executions", ["status"])
    op.create_index("idx_trade_ai_source", "trade_executions", ["ai_source"])
    op.create_index("idx_trade_strategy", "trade_executions", ["strategy_name"])
    op.create_index("idx_trade_market_regime", "trade_executions", ["market_regime"])
    op.create_index("idx_trade_trade_id", "trade_executions", ["trade_id"])

    # 3. Portfolio Snapshots Table
    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("snapshot_timestamp", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        # Portfolio totals
        sa.Column("total_value", sa.Numeric(15, 2), nullable=False),
        sa.Column("cash", sa.Numeric(15, 2), nullable=False),
        sa.Column("invested_value", sa.Numeric(15, 2), nullable=False),
        # Position details
        sa.Column("positions", postgresql.JSONB, nullable=False),
        sa.Column("sector_allocation", postgresql.JSONB),
        sa.Column("strategy_allocation", postgresql.JSONB),
        # Risk metrics
        sa.Column("positions_count", sa.Integer, nullable=False),
        sa.Column("avg_position_size", sa.Numeric(15, 2)),
        sa.Column("largest_position_pct", sa.Numeric(5, 4)),
        sa.Column("cash_pct", sa.Numeric(5, 4)),
        # Performance
        sa.Column("total_pnl", sa.Numeric(15, 2)),
        sa.Column("total_return_pct", sa.Numeric(10, 6)),
        # Metadata
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("notes", sa.String),
    )

    # Indexes for portfolio_snapshots
    op.create_index("idx_portfolio_snapshot_date", "portfolio_snapshots", ["snapshot_date"])
    op.create_index("idx_portfolio_snapshot_timestamp", "portfolio_snapshots", ["snapshot_timestamp"])

    # 4. Signal Performance Table
    op.create_table(
        "signal_performance",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("signal_id", sa.String, unique=True, nullable=False),
        # Signal details
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column("signal", sa.String(10), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        # AI source
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("model_version", sa.String(50)),
        # Context
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("market_regime", sa.String(20)),
        # Prices
        sa.Column("signal_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("target_price", sa.Numeric(10, 2)),
        sa.Column("stop_loss", sa.Numeric(10, 2)),
        # Resolution
        sa.Column("time_horizon_days", sa.Integer, default=5),
        sa.Column("resolution_date", sa.Date),
        sa.Column("actual_price", sa.Numeric(10, 2)),
        # Outcome
        sa.Column("outcome", sa.String(20)),
        sa.Column("return_pct", sa.Numeric(10, 6)),
        sa.Column("target_hit", sa.Boolean),
        sa.Column("stop_loss_hit", sa.Boolean),
        # RAG context
        sa.Column("rag_documents_used", sa.Integer, default=0),
        sa.Column("rag_relevance_score", sa.Numeric(5, 4)),
        sa.Column("rag_document_ids", postgresql.JSONB),
        # Validation metrics
        sa.Column("confidence_calibration_error", sa.Numeric(10, 6)),
        # Status
        sa.Column("status", sa.String(20), nullable=False, default="PENDING"),
        # Metadata
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("metadata", postgresql.JSONB),
    )

    # Indexes for signal_performance
    op.create_index("idx_signal_ticker", "signal_performance", ["ticker"])
    op.create_index("idx_signal_source", "signal_performance", ["source"])
    op.create_index("idx_signal_generated_at", "signal_performance", ["generated_at"])
    op.create_index("idx_signal_status", "signal_performance", ["status"])
    op.create_index("idx_signal_outcome", "signal_performance", ["outcome"])
    op.create_index("idx_signal_market_regime", "signal_performance", ["market_regime"])
    op.create_index("idx_signal_signal_id", "signal_performance", ["signal_id"])

    # 5. Weekly Analytics Table
    op.create_table(
        "weekly_analytics",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("week_number", sa.Integer, nullable=False),
        sa.Column("week_start_date", sa.Date, nullable=False),
        sa.Column("week_end_date", sa.Date, nullable=False),
        # Portfolio metrics
        sa.Column("portfolio_value_start", sa.Numeric(15, 2), nullable=False),
        sa.Column("portfolio_value_end", sa.Numeric(15, 2), nullable=False),
        sa.Column("weekly_pnl", sa.Numeric(15, 2), nullable=False),
        sa.Column("weekly_return_pct", sa.Numeric(10, 6)),
        # Trading activity
        sa.Column("total_trades", sa.Integer, default=0),
        sa.Column("total_volume_usd", sa.Numeric(15, 2)),
        sa.Column("avg_daily_trades", sa.Numeric(8, 2)),
        # Performance
        sa.Column("win_count", sa.Integer, default=0),
        sa.Column("loss_count", sa.Integer, default=0),
        sa.Column("win_rate", sa.Numeric(5, 4)),
        sa.Column("sharpe_ratio", sa.Numeric(10, 4)),
        sa.Column("max_drawdown_pct", sa.Numeric(10, 6)),
        # AI costs
        sa.Column("total_ai_cost_usd", sa.Numeric(10, 4), nullable=False, default=0),
        sa.Column("avg_daily_ai_cost", sa.Numeric(10, 4)),
        # Best/Worst days
        sa.Column("best_day_date", sa.Date),
        sa.Column("best_day_return_pct", sa.Numeric(10, 6)),
        sa.Column("worst_day_date", sa.Date),
        sa.Column("worst_day_return_pct", sa.Numeric(10, 6)),
        # Metadata
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for weekly_analytics
    op.create_index(
        "idx_weekly_analytics_year_week",
        "weekly_analytics",
        ["year", "week_number"],
        unique=True,
    )
    op.create_index("idx_weekly_analytics_start_date", "weekly_analytics", ["week_start_date"])

    # 6. Monthly Analytics Table
    op.create_table(
        "monthly_analytics",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.Integer, nullable=False),
        # Portfolio metrics
        sa.Column("portfolio_value_start", sa.Numeric(15, 2), nullable=False),
        sa.Column("portfolio_value_end", sa.Numeric(15, 2), nullable=False),
        sa.Column("monthly_pnl", sa.Numeric(15, 2), nullable=False),
        sa.Column("monthly_return_pct", sa.Numeric(10, 6)),
        # Trading activity
        sa.Column("total_trades", sa.Integer, default=0),
        sa.Column("total_volume_usd", sa.Numeric(15, 2)),
        sa.Column("trading_days", sa.Integer),
        # Performance
        sa.Column("win_count", sa.Integer, default=0),
        sa.Column("loss_count", sa.Integer, default=0),
        sa.Column("win_rate", sa.Numeric(5, 4)),
        sa.Column("sharpe_ratio", sa.Numeric(10, 4)),
        sa.Column("sortino_ratio", sa.Numeric(10, 4)),
        sa.Column("max_drawdown_pct", sa.Numeric(10, 6)),
        # AI costs
        sa.Column("total_ai_cost_usd", sa.Numeric(10, 4), nullable=False, default=0),
        sa.Column("avg_daily_ai_cost", sa.Numeric(10, 4)),
        sa.Column("total_tokens_used", sa.BigInteger),
        # Best/Worst performance
        sa.Column("best_week_return_pct", sa.Numeric(10, 6)),
        sa.Column("worst_week_return_pct", sa.Numeric(10, 6)),
        # Metadata
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("notes", sa.String),
    )

    # Indexes for monthly_analytics
    op.create_index(
        "idx_monthly_analytics_year_month",
        "monthly_analytics",
        ["year", "month"],
        unique=True,
    )

    # 7. Create materialized view for quick dashboard stats
    op.execute("""
        CREATE MATERIALIZED VIEW analytics_summary AS
        SELECT
            MAX(date) as latest_date,
            COUNT(*) as total_days,
            SUM(total_trades) as all_time_trades,
            AVG(win_rate) as avg_win_rate,
            AVG(sharpe_ratio) as avg_sharpe_ratio,
            SUM(ai_cost_usd) as total_ai_cost,
            MAX(portfolio_value_eod) as peak_portfolio_value,
            MIN(max_drawdown_pct) as worst_drawdown
        FROM daily_analytics;
    """)

    # 8. Create function to auto-update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Apply trigger to tables with updated_at
    for table in ["daily_analytics", "trade_executions", "signal_performance"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade():
    """Remove analytics tables."""

    # Drop triggers
    for table in ["daily_analytics", "trade_executions", "signal_performance"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics_summary;")

    # Drop tables
    op.drop_table("monthly_analytics")
    op.drop_table("weekly_analytics")
    op.drop_table("signal_performance")
    op.drop_table("portfolio_snapshots")
    op.drop_table("trade_executions")
    op.drop_table("daily_analytics")
