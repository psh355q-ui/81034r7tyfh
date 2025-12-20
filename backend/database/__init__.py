"""
Database Module

SQLAlchemy models and repository layer for persistent storage.
"""

from backend.database.models import (
    Base,
    NewsArticle,
    AnalysisResult,
    TradingSignal,
    BacktestRun,
    BacktestTrade,
    SignalPerformance,
    create_all_tables,
    drop_all_tables,
    setup_timescaledb_hypertables
)

from backend.database.repository import (
    NewsRepository,
    AnalysisRepository,
    SignalRepository,
    BacktestRepository,
    PerformanceRepository,
    get_db_session,
    get_sync_session
)

__all__ = [
    # Models
    'Base',
    'NewsArticle',
    'AnalysisResult',
    'TradingSignal',
    'BacktestRun',
    'BacktestTrade',
    'SignalPerformance',
    'create_all_tables',
    'drop_all_tables',
    'setup_timescaledb_hypertables',

    # Repositories
    'NewsRepository',
    'AnalysisRepository',
    'SignalRepository',
    'BacktestRepository',
    'PerformanceRepository',
    'get_db_session',
    'get_sync_session',
]
