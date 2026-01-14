"""
Volume Filter
거래량 급등을 감지하는 필터
"""

from dataclasses import dataclass
from typing import Optional
import yfinance as yf
import numpy as np


@dataclass
class VolumeFilterResult:
    """거래량 필터 결과"""
    ticker: str
    score: float  # 0-100
    current_volume: int
    avg_volume_20d: float
    volume_ratio: float  # current / avg
    passed: bool
    reason: str


class VolumeFilter:
    """
    거래량 급등 필터
    
    어제 거래량이 20일 평균의 200% 이상이면 통과
    점수는 비율에 따라 0-100점 부여
    """
    
    def __init__(
        self,
        min_ratio: float = 2.0,  # 최소 200%
        max_score_ratio: float = 5.0,  # 500%에서 100점
        min_volume: int = 500_000,  # 최소 일평균 거래량
    ):
        self.min_ratio = min_ratio
        self.max_score_ratio = max_score_ratio
        self.min_volume = min_volume
    
    async def check(self, ticker: str) -> VolumeFilterResult:
        """
        거래량 필터 체크
        
        Args:
            ticker: 종목 티커
            
        Returns:
            VolumeFilterResult: 필터 결과
        """
        try:
            # yfinance 로깅 레벨 조정 (불필요한 에러 로그 방지)
            import logging
            logging.getLogger('yfinance').setLevel(logging.CRITICAL)
            
            # Yahoo Finance에서 데이터 가져오기
            stock = yf.Ticker(ticker)
            
            # Period를 1달로 설정
            hist = stock.history(period="1mo")
            
            if hist.empty or len(hist) < 20:
                return VolumeFilterResult(
                    ticker=ticker,
                    score=0,
                    current_volume=0,
                    avg_volume_20d=0,
                    volume_ratio=0,
                    passed=False,
                    reason="데이터 부족/상장폐지 가능성"
                )
            
            current_volume = int(hist['Volume'].iloc[-1])
            avg_volume_20d = float(hist['Volume'].tail(20).mean())
            
            # 최소 거래량 체크
            if avg_volume_20d < self.min_volume:
                return VolumeFilterResult(
                    ticker=ticker,
                    score=0,
                    current_volume=current_volume,
                    avg_volume_20d=avg_volume_20d,
                    volume_ratio=0,
                    passed=False,
                    reason=f"평균 거래량 부족 ({avg_volume_20d:,.0f} < {self.min_volume:,})"
                )
            
            volume_ratio = current_volume / avg_volume_20d if avg_volume_20d > 0 else 0
            
            # 점수 계산 (min_ratio ~ max_score_ratio 사이에서 0~100)
            if volume_ratio < self.min_ratio:
                score = 0
                passed = False
                reason = f"거래량 비율 부족 ({volume_ratio:.1f}x < {self.min_ratio}x)"
            else:
                # 선형 보간으로 점수 계산
                normalized = (volume_ratio - self.min_ratio) / (self.max_score_ratio - self.min_ratio)
                score = min(100, max(0, normalized * 100))
                passed = True
                reason = f"거래량 급등 감지 ({volume_ratio:.1f}x)"
            
            return VolumeFilterResult(
                ticker=ticker,
                score=score,
                current_volume=current_volume,
                avg_volume_20d=avg_volume_20d,
                volume_ratio=volume_ratio,
                passed=passed,
                reason=reason
            )
            
        except Exception as e:
            return VolumeFilterResult(
                ticker=ticker,
                score=0,
                current_volume=0,
                avg_volume_20d=0,
                volume_ratio=0,
                passed=False,
                reason=f"오류: {str(e)}"
            )
