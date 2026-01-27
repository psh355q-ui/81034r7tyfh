"""
Correlation Shock Detector

포트폴리오 내부 상관관계 급등 감지 시스템 구현.
VIX가 낮아도 내 포트폴리오 안에서 분산 효과가 소멸하는 순간을 탐지.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CorrelationShockDetector:
    """
    포트폴리오 내 상관관계 급등을 감지하는 클래스
    """
    
    def __init__(self, lookback_days: int = 20):
        """
        초기화
        
        Args:
            lookback_days: 상관관계 계산에 사용할 과거 데이터 일수
        """
        self.lookback_days = lookback_days
        
    def detect_correlation_regime(self, portfolio: Dict) -> Tuple[str, float]:
        """
        포트폴리오 상관관계 국면을 감지
        
        Args:
            portfolio: 포트폴리오 정보 딕셔너리
                - positions: 포지션 정보 리스트 [{'symbol': 'AAPL', 'quantity': 100}, ...]
                - current_value: 현재 포트폴리오 가치
                - peak_value: 포트폴리오 최고 가치
                
        Returns:
            Tuple[str, float]: (상관관계 국면, 평균 상관관계)
                - 국면: 'crisis_correlation', 'elevated_correlation', 'normal', 'single_position', 'insufficient_data'
        """
        try:
            positions = portfolio.get('positions', [])
            
            # 종목이 1개 이하인 경우
            if len(positions) <= 1:
                return 'single_position', 0.0
                
            # 종목 심볼 추출
            symbols = [pos.get('symbol') for pos in positions if pos.get('symbol')]
            
            # 최소 2개 종목 필요
            if len(symbols) < 2:
                return 'insufficient_data', 0.0
                
            # 종목별 수익률 데이터 가져오기
            returns_data = self._fetch_returns_data(symbols)
            
            # 데이터가 충분하지 않은 경우
            if returns_data is None or len(returns_data.columns) < 2:
                return 'insufficient_data', 0.0
                
            # 상관관계 행렬 계산
            correlation_matrix = returns_data.corr()
            
            # 평균 상관관계 계산 (대각선 제외)
            avg_correlation = self._calculate_average_correlation(correlation_matrix)
            
            # 상관관계 국면 판단
            regime = self._determine_correlation_regime(avg_correlation)
            
            logger.info(f"Correlation analysis: avg_corr={avg_correlation:.3f}, regime={regime}")
            
            return regime, avg_correlation
            
        except Exception as e:
            logger.error(f"Error in correlation detection: {str(e)}")
            return 'insufficient_data', 0.0
    
    def _fetch_returns_data(self, symbols: List[str]) -> Optional[pd.DataFrame]:
        """
        종목별 수익률 데이터 가져오기
        
        Args:
            symbols: 종목 심볼 리스트
            
        Returns:
            DataFrame: 종목별 일일 수익률 데이터
        """
        try:
            # 종목별 데이터 가져오기
            tickers = yf.Tickers(symbols)
            
            # 종료일: 오늘
            end_date = datetime.now()
            # 시작일: lookback_days 전
            start_date = end_date - timedelta(days=self.lookback_days + 30)  # 여유 추가
            
            # 종목별 종가 데이터 가져오기
            data = tickers.history(start=start_date, end=end_date)
            
            # 종가 데이터만 추출
            close_prices = data['Close']
            
            # 마지막 lookback_days 데이터만 사용
            if len(close_prices) > self.lookback_days:
                close_prices = close_prices.tail(self.lookback_days)
            
            # 일일 수익률 계산
            returns = close_prices.pct_change().dropna()
            
            # 데이터가 충분한지 확인
            if len(returns) < 5:  # 최소 5일 데이터 필요
                return None
                
            return returns
            
        except Exception as e:
            logger.error(f"Error fetching returns data: {str(e)}")
            return None
    
    def _calculate_average_correlation(self, correlation_matrix: pd.DataFrame) -> float:
        """
        상관관계 행렬의 평균 상관관계 계산 (대각선 제외)
        
        Args:
            correlation_matrix: 상관관계 행렬
            
        Returns:
            float: 평균 상관관계
        """
        try:
            # 대각선(자기 자신과의 상관관계) 제외
            mask = ~np.eye(correlation_matrix.shape[0], dtype=bool)
            
            # 대각선 제외 평균 계산
            avg_corr = correlation_matrix.values[mask].mean()
            
            return float(avg_corr)
            
        except Exception as e:
            logger.error(f"Error calculating average correlation: {str(e)}")
            return 0.0
    
    def _determine_correlation_regime(self, avg_correlation: float) -> str:
        """
        평균 상관관계에 따른 국면 판단
        
        Args:
            avg_correlation: 평균 상관관계
            
        Returns:
            str: 상관관계 국면
        """
        if avg_correlation >= 0.85:
            return 'crisis_correlation'
        elif avg_correlation >= 0.70:
            return 'elevated_correlation'
        else:
            return 'normal'