"""
Momentum Filter
모멘텀 스크리닝 필터 (5일/20일 수익률 기반)
"""

from dataclasses import dataclass
from typing import Optional
import yfinance as yf
import numpy as np


@dataclass
class MomentumFilterResult:
    """모멘텀 필터 결과"""
    ticker: str
    score: float  # 0-100
    return_5d: float  # 5일 수익률 (%)
    return_20d: float  # 20일 수익률 (%)
    rsi_14: float  # 14일 RSI
    momentum_signal: str  # STRONG_UP, UP, NEUTRAL, DOWN, STRONG_DOWN
    passed: bool
    reason: str


class MomentumFilter:
    """
    모멘텀 스크리닝 필터
    
    5일 수익률 + RSI 조합으로 모멘텀 강도 평가
    강한 상승 모멘텀이면 통과
    """
    
    def __init__(
        self,
        min_return_5d: float = 3.0,  # 최소 5일 수익률 3%
        rsi_oversold: float = 30.0,
        rsi_overbought: float = 70.0,
        max_score_return: float = 10.0,  # 10%에서 100점
    ):
        self.min_return_5d = min_return_5d
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.max_score_return = max_score_return
    
    def _calculate_rsi(self, prices, period: int = 14) -> float:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0
    
    async def check(self, ticker: str) -> MomentumFilterResult:
        """
        모멘텀 필터 체크
        
        Args:
            ticker: 종목 티커
            
        Returns:
            MomentumFilterResult: 필터 결과
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2mo")
            
            if len(hist) < 20:
                return MomentumFilterResult(
                    ticker=ticker,
                    score=0,
                    return_5d=0,
                    return_20d=0,
                    rsi_14=50,
                    momentum_signal="NEUTRAL",
                    passed=False,
                    reason="데이터 부족"
                )
            
            current_price = float(hist['Close'].iloc[-1])
            price_5d_ago = float(hist['Close'].iloc[-5])
            price_20d_ago = float(hist['Close'].iloc[-20])
            
            return_5d = (current_price - price_5d_ago) / price_5d_ago * 100
            return_20d = (current_price - price_20d_ago) / price_20d_ago * 100
            
            # RSI 계산
            rsi_14 = self._calculate_rsi(hist['Close'], 14)
            
            # 모멘텀 시그널 결정
            if return_5d >= 7 and rsi_14 > 60:
                momentum_signal = "STRONG_UP"
            elif return_5d >= 3:
                momentum_signal = "UP"
            elif return_5d <= -7 and rsi_14 < 40:
                momentum_signal = "STRONG_DOWN"
            elif return_5d <= -3:
                momentum_signal = "DOWN"
            else:
                momentum_signal = "NEUTRAL"
            
            # 통과 여부 (상승 모멘텀만)
            passed = return_5d >= self.min_return_5d
            
            if not passed:
                score = 0
                reason = f"모멘텀 부족 (5일 {return_5d:+.1f}% < {self.min_return_5d}%)"
            else:
                # 점수 계산
                normalized = return_5d / self.max_score_return
                score = min(100, max(0, normalized * 100))
                reason = f"강한 모멘텀 감지 (5일 {return_5d:+.1f}%, RSI {rsi_14:.0f})"
            
            return MomentumFilterResult(
                ticker=ticker,
                score=score,
                return_5d=return_5d,
                return_20d=return_20d,
                rsi_14=rsi_14,
                momentum_signal=momentum_signal,
                passed=passed,
                reason=reason
            )
            
        except Exception as e:
            return MomentumFilterResult(
                ticker=ticker,
                score=0,
                return_5d=0,
                return_20d=0,
                rsi_14=50,
                momentum_signal="NEUTRAL",
                passed=False,
                reason=f"오류: {str(e)}"
            )
