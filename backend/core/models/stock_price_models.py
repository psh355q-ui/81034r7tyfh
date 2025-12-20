"""
SQLAlchemy models for stock price incremental storage.

Models:
1. StockPrice: TimescaleDB hypertable for OHLCV data
2. PriceSyncStatus: Tracks incremental update state per ticker
"""

from sqlalchemy import Column, String, BigInteger, Date, TIMESTAMP, Integer, DECIMAL
from sqlalchemy.sql import func
from backend.core.database import Base


class StockPrice(Base):
    """
    Stock price OHLCV data (TimescaleDB hypertable).

    This table is converted to a TimescaleDB hypertable for efficient
    time-series queries.

    Indexes:
    - Primary: (time, ticker)
    - Secondary: (ticker, time) for fast ticker-based queries

    Partitioning:
    - Partitioned by time (automatic via TimescaleDB)
    - Chunks: 7 days per chunk (configurable)
    """
    __tablename__ = "stock_prices"

    time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    ticker = Column(String(20), primary_key=True, nullable=False, index=True)
    open = Column(DECIMAL(12, 4))
    high = Column(DECIMAL(12, 4))
    low = Column(DECIMAL(12, 4))
    close = Column(DECIMAL(12, 4))
    volume = Column(BigInteger)
    adjusted_close = Column(DECIMAL(12, 4))

    def __repr__(self):
        return f"<StockPrice(ticker={self.ticker}, time={self.time}, close={self.close})>"


class PriceSyncStatus(Base):
    """
    Tracks incremental update state for each ticker.

    Used to determine:
    - When was last sync?
    - What's the latest price date in DB?
    - How many rows do we have?

    This enables incremental updates: only download data since last_price_date + 1.
    """
    __tablename__ = "price_sync_status"

    ticker = Column(String(20), primary_key=True)
    last_sync_date = Column(Date, nullable=False)  # Last time we ran update
    last_price_date = Column(Date, nullable=False)  # Latest price date in DB
    total_rows = Column(Integer, default=0)
    first_sync_date = Column(Date)  # Initial backfill date
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self):
        return (
            f"<PriceSyncStatus(ticker={self.ticker}, "
            f"last_price_date={self.last_price_date}, "
            f"total_rows={self.total_rows})>"
        )
