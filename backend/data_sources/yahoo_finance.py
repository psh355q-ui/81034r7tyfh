"""
yahoo_finance.py - Yahoo Finance 데이터 소스

📊 Provides:
    - 배당 정보: annual_dividend, dividend_yield, frequency
    - 섹터 정보: sector classification (GICS)
    - 배당 히스토리: 최근 2년간 배당 지급 내역
    - 배당 증가 연수: consecutive dividend growth years

🔗 External APIs:
    - Yahoo Finance API (via yfinance library)
        - ticker.info: 기업 정보, 현재가, 섹터
        - ticker.dividends: 배당 히스토리 (pandas Series)

🔄 Used By:
    - backend/api/portfolio_router.py: KIS API fallback
    - backend/api/dividend_router.py: 배당 대시보드, aristocrats

📝 Notes:
    - KIS API에 배당 정보가 없을 때 사용
    - TTM (Trailing Twelve Months) 기준 배당 계산
    - 히스토리가 없으면 최근 2년 데이터로 추정
    - get_dividend_growth_streak: 연속 배당 증가 연수 분석
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
        
        
        # Calculate TTM (Trailing Twelve Months) dividend
        one_year_ago = today_tz - timedelta(days=365)
        ttm_divs = dividends[dividends.index >= one_year_ago]
        annual_dividend = float(ttm_divs.sum())
        
        # Fallback: if TTM is 0 but we have recent dividends (last 2 years), use those
        if annual_dividend == 0 and len(recent_divs) > 0:
            logger.info(f"  TTM is $0, using {len(recent_divs)} recent dividends as fallback")
            annual_dividend = float(recent_divs.sum())
            payment_count = len(recent_divs)
        else:
            # Determine frequency from TTM
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


def get_stock_sector(ticker: str) -> str:
    """
    섹터 정보 조회
    
    Data Source: Yahoo Finance ticker.info['sector']
    
    Args:
        ticker: 종목 코드
    
    Returns:
        str: Sector name (e.g., "Technology", "Healthcare")
    """
    try:
        logger.info(f"📊 Fetching sector data from Yahoo Finance: {ticker}")
        stock = yf.Ticker(ticker)
        sector = stock.info.get('sector', 'Unknown')
        logger.info(f"✅ Sector for {ticker}: {sector}")
        return sector
    
    except Exception as e:
        logger.error(f"Failed to get sector for {ticker}: {e}")
        return "Unknown"
    
    return sector


def get_dividend_growth_streak(ticker: str) -> dict:
    """
    배당금 연속 증가 연수 계산
    
    Data Source: Yahoo Finance - ticker.dividends (전체 배당 이력)
    
    Args:
        ticker: 종목 코드
    
    Returns:
        {
            "ticker": str,
            "consecutive_years": int,  # 연속 증가 연수
            "total_years": int,  # 총 배당 지급 연수
            "is_growing": bool,  # 현재 증가 중인지
            "last_dividend": float,  # 최근 배당금
            "growth_rate": float  # 평균 증가율
        }
    """
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends
        
        if dividends.empty:
            return {
                "ticker": ticker,
                "consecutive_years": 0,
                "total_years": 0,
                "is_growing": False,
                "last_dividend": 0.0,
                "growth_rate": 0.0
            }
        
        # 연도별 배당금 합계 계산
        annual_dividends = dividends.resample('Y').sum()
        annual_dividends = annual_dividends[annual_dividends > 0]  # 0보다 큰 값만
        
        if len(annual_dividends) < 2:
            return {
                "ticker": ticker,
                "consecutive_years": 0,
                "total_years": len(annual_dividends),
                "is_growing": False,
                "last_dividend": float(annual_dividends.iloc[-1]) if len(annual_dividends) > 0 else 0.0,
                "growth_rate": 0.0
            }
        
        # 연속 증가 연수 계산
        consecutive_years = 0
        growth_rates = []
        
        for i in range(len(annual_dividends) - 1, 0, -1):  # 최근부터 역순으로
            current = annual_dividends.iloc[i]
            previous = annual_dividends.iloc[i - 1]
            
            if current > previous:
                consecutive_years += 1
                if previous > 0:
                    growth_rate = ((current - previous) / previous) * 100
                    growth_rates.append(growth_rate)
            else:
                break  # 증가가 끊기면 종료
        
        avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0.0
        
        return {
            "ticker": ticker,
            "consecutive_years": consecutive_years,
            "total_years": len(annual_dividends),
            "is_growing": consecutive_years > 0,
            "last_dividend": float(annual_dividends.iloc[-1]),
            "growth_rate": round(avg_growth_rate, 2)
        }
        
    except Exception as e:
        logger.error(f"Failed to get dividend growth streak for {ticker}: {e}")
        return {
            "ticker": ticker,
            "consecutive_years": 0,
            "total_years": 0,
            "is_growing": False,
            "last_dividend": 0.0,
            "growth_rate": 0.0
        }
