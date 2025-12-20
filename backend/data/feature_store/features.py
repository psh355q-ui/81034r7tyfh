"""
Feature Definitions and Calculation Logic.

This module defines all features used in the trading system and provides
calculation functions for each feature.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import yfinance as yf
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# FEATURE DEFINITIONS
# =============================================================================

FEATURE_DEFINITIONS = {
    # =========================================================================
    # Technical Features (기존)
    # =========================================================================
    "ret_5d": {
        "description": "5일 수익률 (%)",
        "category": "technical",
        "data_sources": ["yahoo_finance"],
        "update_frequency": "daily",
        "cache_ttl": 300,  # 5분
    },
    
    "ret_20d": {
        "description": "20일 수익률 (%)",
        "category": "technical",
        "data_sources": ["yahoo_finance"],
        "update_frequency": "daily",
        "cache_ttl": 300,
    },
    
    "vol_20d": {
        "description": "20일 변동성 (표준편차)",
        "category": "technical",
        "data_sources": ["yahoo_finance"],
        "update_frequency": "daily",
        "cache_ttl": 300,
    },
    
    "mom_20d": {
        "description": "20일 모멘텀 (가격 변화율)",
        "category": "technical",
        "data_sources": ["yahoo_finance"],
        "update_frequency": "daily",
        "cache_ttl": 300,
    },
    
    # =========================================================================
    # AI Factors (신규) ✨
    # =========================================================================
    "non_standard_risk": {
        "description": "뉴스 기반 비정형 위험 점수 (0-1)",
        "category": "ai_factor",
        "data_sources": ["yahoo_news", "newsapi"],
        "update_frequency": "hourly",  # 1시간마다 업데이트
        "cache_ttl": 3600,  # 1시간 캐시
        "note": "Rule-based keyword analysis, no AI cost",
    },
    
    # =========================================================================
    # Fundamental Features (예정)
    # =========================================================================
    "pe_ratio": {
        "description": "Price-to-Earnings Ratio",
        "category": "fundamental",
        "data_sources": ["yahoo_finance"],
        "update_frequency": "daily",
        "cache_ttl": 86400,  # 24시간
    },
    
    "market_cap": {
        "description": "시가총액 (USD)",
        "category": "fundamental",
        "data_sources": ["yahoo_finance"],
        "update_frequency": "daily",
        "cache_ttl": 86400,
    },
}


# =============================================================================
# FEATURE CALCULATION FUNCTIONS
# =============================================================================

async def calculate_feature(
    ticker: str,
    feature_name: str,
    as_of_date: datetime,
) -> Optional[float]:
    """
    Calculate a single feature value.
    
    Args:
        ticker: Stock ticker symbol
        feature_name: Name of feature to calculate
        as_of_date: Date to calculate feature for
        
    Returns:
        Feature value or None if calculation fails
        
    Raises:
        ValueError: If feature_name is unknown
    """
    if feature_name not in FEATURE_DEFINITIONS:
        raise ValueError(f"Unknown feature: {feature_name}")
    
    try:
        # Technical features
        if feature_name == "ret_5d":
            return await calculate_ret_5d(ticker, as_of_date)
        elif feature_name == "ret_20d":
            return await calculate_ret_20d(ticker, as_of_date)
        elif feature_name == "vol_20d":
            return await calculate_vol_20d(ticker, as_of_date)
        elif feature_name == "mom_20d":
            return await calculate_mom_20d(ticker, as_of_date)
        
        # AI Factors ✨
        elif feature_name == "non_standard_risk":
            from .ai_factors import calculate_non_standard_risk_feature
            return await calculate_non_standard_risk_feature(ticker, as_of_date)
        
        # Fundamental features
        elif feature_name == "pe_ratio":
            return await calculate_pe_ratio(ticker, as_of_date)
        elif feature_name == "market_cap":
            return await calculate_market_cap(ticker, as_of_date)
        
        else:
            raise ValueError(f"Feature calculation not implemented: {feature_name}")
            
    except Exception as e:
        logger.error(f"Error calculating {feature_name} for {ticker}: {e}")
        return None


# =============================================================================
# Technical Feature Calculations
# =============================================================================

async def calculate_ret_5d(ticker: str, as_of_date: datetime) -> Optional[float]:
    """Calculate 5-day return."""
    try:
        # Fetch data
        end_date = as_of_date
        start_date = as_of_date - timedelta(days=10)  # Buffer for weekends
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if len(df) < 2:
            return None
        
        # Calculate return
        prices = df['Close'].values
        ret = (prices[-1] / prices[0] - 1.0) if len(prices) >= 5 else None
        
        return float(ret) if ret is not None else None
        
    except Exception as e:
        logger.error(f"Error calculating ret_5d for {ticker}: {e}")
        return None


async def calculate_ret_20d(ticker: str, as_of_date: datetime) -> Optional[float]:
    """Calculate 20-day return."""
    try:
        end_date = as_of_date
        start_date = as_of_date - timedelta(days=30)  # Buffer
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if len(df) < 2:
            return None
        
        prices = df['Close'].values
        ret = (prices[-1] / prices[0] - 1.0) if len(prices) >= 20 else None
        
        return float(ret) if ret is not None else None
        
    except Exception as e:
        logger.error(f"Error calculating ret_20d for {ticker}: {e}")
        return None


async def calculate_vol_20d(ticker: str, as_of_date: datetime) -> Optional[float]:
    """Calculate 20-day volatility (annualized standard deviation)."""
    try:
        end_date = as_of_date
        start_date = as_of_date - timedelta(days=30)
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if len(df) < 2:
            return None
        
        # Calculate daily returns
        returns = df['Close'].pct_change().dropna()
        
        if len(returns) < 20:
            return None
        
        # Annualized volatility
        vol = returns.std() * np.sqrt(252)  # 252 trading days
        
        return float(vol)
        
    except Exception as e:
        logger.error(f"Error calculating vol_20d for {ticker}: {e}")
        return None


async def calculate_mom_20d(ticker: str, as_of_date: datetime) -> Optional[float]:
    """Calculate 20-day momentum (rate of change)."""
    try:
        end_date = as_of_date
        start_date = as_of_date - timedelta(days=30)
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if len(df) < 2:
            return None
        
        prices = df['Close'].values
        
        if len(prices) < 20:
            return None
        
        # Momentum = (Current Price - Price 20 days ago) / Price 20 days ago
        mom = (prices[-1] / prices[0] - 1.0)
        
        return float(mom)
        
    except Exception as e:
        logger.error(f"Error calculating mom_20d for {ticker}: {e}")
        return None


# =============================================================================
# Fundamental Feature Calculations
# =============================================================================

async def calculate_pe_ratio(ticker: str, as_of_date: datetime) -> Optional[float]:
    """Calculate P/E ratio."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        pe_ratio = info.get('trailingPE', None)
        
        return float(pe_ratio) if pe_ratio is not None else None
        
    except Exception as e:
        logger.error(f"Error calculating PE ratio for {ticker}: {e}")
        return None


async def calculate_market_cap(ticker: str, as_of_date: datetime) -> Optional[float]:
    """Calculate market capitalization."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        market_cap = info.get('marketCap', None)
        
        return float(market_cap) if market_cap is not None else None
        
    except Exception as e:
        logger.error(f"Error calculating market cap for {ticker}: {e}")
        return None


# =============================================================================
# Feature Metadata
# =============================================================================

def get_feature_info(feature_name: str) -> Optional[Dict]:
    """Get metadata for a feature."""
    return FEATURE_DEFINITIONS.get(feature_name)


def get_all_features() -> List[str]:
    """Get list of all available features."""
    return list(FEATURE_DEFINITIONS.keys())


def get_features_by_category(category: str) -> List[str]:
    """Get features by category."""
    return [
        name for name, info in FEATURE_DEFINITIONS.items()
        if info['category'] == category
    ]


# =============================================================================
# Feature Validation
# =============================================================================

def validate_feature_value(feature_name: str, value: float) -> bool:
    """
    Validate if a feature value is reasonable.
    
    Args:
        feature_name: Name of feature
        value: Feature value to validate
        
    Returns:
        True if value is reasonable, False otherwise
    """
    if value is None:
        return False
    
    # Basic sanity checks
    if not np.isfinite(value):
        return False
    
    # Feature-specific validation
    if feature_name == "vol_20d":
        # Volatility should be between 0 and 3 (300%)
        return 0 <= value <= 3.0
    
    elif feature_name in ["ret_5d", "ret_20d", "mom_20d"]:
        # Returns should be between -0.9 and 10 (-90% to 1000%)
        return -0.9 <= value <= 10.0
    
    elif feature_name == "non_standard_risk":
        # Risk score should be between 0 and 1
        return 0 <= value <= 1.0
    
    elif feature_name == "pe_ratio":
        # P/E ratio should be positive and reasonable
        return 0 < value < 1000
    
    elif feature_name == "market_cap":
        # Market cap should be positive
        return value > 0
    
    return True


# =============================================================================
# Feature Dependencies
# =============================================================================

FEATURE_DEPENDENCIES = {
    "non_standard_risk": [],  # No dependencies
    "ret_5d": [],
    "ret_20d": [],
    "vol_20d": [],
    "mom_20d": [],
    "pe_ratio": [],
    "market_cap": [],
}


def get_feature_dependencies(feature_name: str) -> List[str]:
    """Get list of features that must be calculated first."""
    return FEATURE_DEPENDENCIES.get(feature_name, [])


# =============================================================================
# Compatibility Functions (for existing store.py)
# =============================================================================

def get_feature_calculator(feature_name: str):
    """
    Get calculator function for a feature (compatibility wrapper).
    
    Args:
        feature_name: Name of feature
        
    Returns:
        Async function that calculates the feature
    """
    async def calculator(ticker: str, as_of_date: datetime) -> Optional[float]:
        return await calculate_feature(ticker, feature_name, as_of_date)
    
    return calculator


def list_available_features() -> List[str]:
    """
    List all available features (compatibility wrapper).
    
    Returns:
        List of feature names
    """
    return get_all_features()