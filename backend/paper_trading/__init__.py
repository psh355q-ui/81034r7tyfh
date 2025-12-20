"""
Paper Trading Module

Real-time trading simulation with live market data.

Components:
- MarketDataFetcher: Real-time market data from Yahoo Finance
- LivePortfolio: Portfolio tracking with P&L
- PaperTradingEngine: Main trading simulation engine

Author: AI Trading System Team
Date: 2025-11-15
"""

from .market_data_fetcher import MarketDataFetcher, MarketQuote
from .live_portfolio import LivePortfolio, Position, Order, Trade, OrderStatus
from .paper_trading_engine import PaperTradingEngine, PaperTradingConfig

__all__ = [
    # Market Data
    "MarketDataFetcher",
    "MarketQuote",
    # Portfolio
    "LivePortfolio",
    "Position",
    "Order",
    "Trade",
    "OrderStatus",
    # Engine
    "PaperTradingEngine",
    "PaperTradingConfig",
]

__version__ = "1.0.0"
__author__ = "AI Trading System Team"
