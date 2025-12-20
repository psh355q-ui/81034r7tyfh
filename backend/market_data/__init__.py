"""
Market Data Module

Real-time and historical market data fetching

Components:
- price_fetcher: Yahoo Finance + Alpha Vantage integration
- price_scheduler: Periodic portfolio price updates
"""

from .price_fetcher import (
    PriceFetcher,
    get_price_fetcher,
    get_current_price,
    get_multiple_prices,
    get_price_history
)

from .price_scheduler import PriceUpdateScheduler

__all__ = [
    'PriceFetcher',
    'get_price_fetcher',
    'get_current_price',
    'get_multiple_prices',
    'get_price_history',
    'PriceUpdateScheduler'
]
