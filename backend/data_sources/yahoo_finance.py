"""
Yahoo Finance Data Source for Dividend Information
Provides fallback dividend data when KIS API doesn't have the information
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)


def get_dividend_info(symbol: str) -> Dict:
    """
    Fetch dividend information from Yahoo Finance
    
    Args:
        symbol: Stock ticker symbol (e.g., "INTC", "AAPL")
        
    Returns:
        Dict: {
            "annual_dividend": float,     # Annual dividend amount
            "dividend_yield": float,      # Dividend yield percentage
            "frequency": str,             # Q, M, S, or A
            "next_ex_date": str,          # Next ex-dividend date (YYYYMMDD)
            "payment_count": int,         # Number of payments per year
            "history": List[Dict]         # Recent dividend history
        }
    """
    try:
        logger.info(f"📊 Fetching dividend data from Yahoo Finance: {symbol}")
        
        # Create ticker object
        ticker = yf.Ticker(symbol)
        
        # Get dividend history (last 2 years)
        import pandas as pd
        today = datetime.now()
        dividends = ticker.dividends
        
        if dividends.empty:
            logger.warning(f"No dividend data found for {symbol} on Yahoo Finance")
            return _get_default_dividend_info()
        
        # Make today timezone-aware to match dividends.index
        if dividends.index.tz is not None:
            # dividends.index is timezone-aware, convert today
            today_tz = pd.Timestamp(today).tz_localize(dividends.index.tz)
        else:
            # dividends.index is naive
            today_tz = pd.Timestamp(today)
        
        start_date = today_tz - timedelta(days=730)
        
        # Filter to last 2 years
        recent_divs = dividends[dividends.index >= start_date]
        
        if recent_divs.empty:
            logger.warning(f"No recent dividend data for {symbol}")
            return _get_default_dividend_info()
        
        # Calculate TTM (Trailing Twelve Months) dividend
        one_year_ago = today_tz - timedelta(days=365)
        ttm_divs = dividends[dividends.index >= one_year_ago]
        annual_dividend = float(ttm_divs.sum())
        
        # DEBUG: Log dividend data
        logger.info(f"  Total dividends in dataset: {len(dividends)}")
        logger.info(f"  Recent dividends (last 2 years): {len(recent_divs)}")
        logger.info(f"  TTM dividends (last 365 days): {len(ttm_divs)}")
        if len(ttm_divs) > 0:
            logger.info(f"  TTM dividend dates: {[d.strftime('%Y-%m-%d') for d in ttm_divs.index[-5:]]}")
            logger.info(f"  TTM dividend amounts: {ttm_divs.values[-5:].tolist()}")
        logger.info(f"  TTM sum: ${annual_dividend:.4f}")
        
        # Determine frequency
        payment_count = len(ttm_divs)
        if payment_count >= 12:
            frequency = "M"  # Monthly
        elif payment_count >= 4:
            frequency = "Q"  # Quarterly
        elif payment_count >= 2:
            frequency = "S"  # Semi-annual
        else:
            frequency = "A"  # Annual
        
        # Get ticker info for current price and yield
        info = ticker.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        
        # Calculate yield
        dividend_yield = (annual_dividend / current_price * 100) if current_price > 0 else 0.0
        
        # Find next ex-dividend date
        # Yahoo Finance doesn't provide future dates, so we estimate based on history
        next_ex_date = _estimate_next_ex_date(dividends, frequency)
        
        # Build history
        history = []
        for date, amount in recent_divs.items():
            history.append({
                'date': date.strftime('%Y%m%d'),
                'amount': float(amount)
            })
        
        result = {
            "annual_dividend": round(annual_dividend, 4),
            "dividend_yield": round(dividend_yield, 2),
            "frequency": frequency,
            "next_ex_date": next_ex_date,
            "payment_count": payment_count,
            "history": history[-10:]  # Last 10 payments
        }
        
        logger.info(f"✅ Yahoo Finance data for {symbol}: ${annual_dividend:.2f}/year, {dividend_yield:.2f}% yield, {frequency} frequency")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
        return _get_default_dividend_info()


def _estimate_next_ex_date(dividends, frequency: str) -> str:
    """
    Estimate next ex-dividend date based on historical pattern
    
    Args:
        dividends: pandas Series of dividend payments
        frequency: Q, M, S, or A
        
    Returns:
        str: Estimated next ex-date in YYYYMMDD format, or empty string
    """
    try:
        if len(dividends) < 2:
            return ""
        
        # Get the last two dividend dates
        last_dates = dividends.index[-2:]
        last_date = dividends.index[-1]
        
        # Calculate average interval
        if len(last_dates) >= 2:
            interval_days = (last_dates[-1] - last_dates[-2]).days
        else:
            # Estimate based on frequency
            freq_map = {"M": 30, "Q": 90, "S": 180, "A": 365}
            interval_days = freq_map.get(frequency, 90)
        
        # Estimate next date
        next_date = last_date + timedelta(days=interval_days)
        
        # Only return if it's in the future
        # Make comparison timezone-aware if needed
        import pandas as pd
        if hasattr(next_date, 'tz') and next_date.tz is not None:
            now_tz = pd.Timestamp.now(tz=next_date.tz)
        else:
            now_tz = pd.Timestamp.now()
        
        if next_date > now_tz:
            return next_date.strftime('%Y%m%d')
        
        return ""
        
    except Exception as e:
        logger.error(f"Error estimating next ex-date: {e}")
        return ""


def _get_default_dividend_info() -> Dict:
    """Return default empty dividend info"""
    return {
        "annual_dividend": 0.0,
        "dividend_yield": 0.0,
        "frequency": "Q",
        "next_ex_date": "",
        "payment_count": 0,
        "history": []
    }
