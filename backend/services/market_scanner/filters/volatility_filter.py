"""
Volatility Filter
변동성 돌파를 감지하는 필터 (ATR 기반)
"""

from dataclasses import dataclass
from typing import Optional
import yfinance as yf
import numpy as np
import pandas as pd


@dataclass
class VolatilityFilterResult:
    """변동성 필터 결과"""
    ticker: str
    score: float  # 0-100
    atr_14: float  # 14일 ATR
    atr_ratio: float  # ATR / 현재가 비율
    price_change_pct: float  # 오늘 가격 변동률
    breakout_detected: bool  # ATR 돌파 감지
    passed: bool
    reason: str


class VolatilityFilter:
    """
    변동성 돌파 필터 (ATR 기반)
    
    오늘의 가격 변동이 ATR의 1.5배 이상이면 통과
    점수는 돌파 강도에 따라 0-100점 부여
    """
    
    def __init__(
        self,
        atr_period: int = 14,
        min_breakout_ratio: float = 1.5,  # ATR의 1.5배
        max_score_ratio: float = 3.0,  # ATR의 3배에서 100점
        min_atr_percent: float = 0.02,  # 최소 ATR 2% (유동성 확인)
    ):
        self.atr_period = atr_period
        self.min_breakout_ratio = min_breakout_ratio
        self.max_score_ratio = max_score_ratio
        self.min_atr_percent = min_atr_percent
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """ATR (Average True Range) 계산"""
        high = df['High']
        low = df['Low']
        close = df['Close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    async def check(self, ticker: str) -> VolatilityFilterResult:
        """
        변동성 필터 체크
        
        Args:
            ticker: 종목 티커
            
        Returns:
            VolatilityFilterResult: 필터 결과
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            
            if len(hist) < self.atr_period + 1:
                return VolatilityFilterResult(
                    ticker=ticker,
                    score=0,
                    atr_14=0,
                    atr_ratio=0,
                    price_change_pct=0,
                    breakout_detected=False,
                    passed=False,
                    reason="데이터 부족"
                )
            
            # ATR 계산
            atr_series = self._calculate_atr(hist, self.atr_period)
            atr_14 = float(atr_series.iloc[-1])
            
            current_price = float(hist['Close'].iloc[-1])
            atr_ratio = atr_14 / current_price if current_price > 0 else 0
            
            # 오늘 가격 변동
            today_high = float(hist['High'].iloc[-1])
            today_low = float(hist['Low'].iloc[-1])
            today_range = today_high - today_low
            
            prev_close = float(hist['Close'].iloc[-2])
            price_change_pct = (current_price - prev_close) / prev_close * 100 if prev_close > 0 else 0
            
            # ATR 돌파 비율
            breakout_ratio = today_range / atr_14 if atr_14 > 0 else 0
            
            # 최소 변동성 체크
            if atr_ratio < self.min_atr_percent:
                return VolatilityFilterResult(
                    ticker=ticker,
                    score=0,
                    atr_14=atr_14,
                    atr_ratio=atr_ratio,
                    price_change_pct=price_change_pct,
                    breakout_detected=False,
                    passed=False,
                    reason=f"변동성 부족 (ATR {atr_ratio:.1%} < {self.min_atr_percent:.1%})"
                )
            
            # 돌파 감지
            breakout_detected = breakout_ratio >= self.min_breakout_ratio
            
            if not breakout_detected:
                score = 0
                passed = False
                reason = f"변동성 돌파 없음 ({breakout_ratio:.1f}x ATR)"
            else:
                # 점수 계산
                normalized = (breakout_ratio - self.min_breakout_ratio) / (self.max_score_ratio - self.min_breakout_ratio)
                score = min(100, max(0, normalized * 100))
                passed = True
                reason = f"변동성 돌파 감지 ({breakout_ratio:.1f}x ATR, {price_change_pct:+.1f}%)"
            
            return VolatilityFilterResult(
                ticker=ticker,
                score=score,
                atr_14=atr_14,
                atr_ratio=atr_ratio,
                price_change_pct=price_change_pct,
                breakout_detected=breakout_detected,
                passed=passed,
                reason=reason
            )
            
        except Exception as e:
            return VolatilityFilterResult(
                ticker=ticker,
                score=0,
                atr_14=0,
                atr_ratio=0,
                price_change_pct=0,
                breakout_detected=False,
                passed=False,
                reason=f"오류: {str(e)}"
            )
