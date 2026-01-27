"""
Correlation Shock Detector 테스트
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from backend.ai.correlation_shock_detector import CorrelationShockDetector


class TestCorrelationShockDetector:
    """CorrelationShockDetector 클래스 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.detector = CorrelationShockDetector(lookback_days=20)
    
    def test_single_position(self):
        """종목 1개 포트폴리오는 'single_position' 반환"""
        portfolio = {
            'positions': [{'symbol': 'AAPL', 'quantity': 100}],
            'current_value': 15000,
            'peak_value': 20000
        }
        
        regime, avg_corr = self.detector.detect_correlation_regime(portfolio)
        
        assert regime == 'single_position'
        assert avg_corr == 0.0
    
    def test_insufficient_data(self):
        """종목 0개 포트폴리오는 'insufficient_data' 반환"""
        portfolio = {
            'positions': [],
            'current_value': 0,
            'peak_value': 0
        }
        
        regime, avg_corr = self.detector.detect_correlation_regime(portfolio)
        
        assert regime == 'insufficient_data'
        assert avg_corr == 0.0
    
    @patch('backend.ai.correlation_shock_detector.yf.Tickers')
    def test_crisis_correlation_detection(self, mock_tickers):
        """상관관계 0.85+ 탐지 시 'crisis_correlation' 반환"""
        # Mock 데이터 설정
        mock_data = Mock()
        # 높은 상관관계를 가진 데이터 생성
        dates = pd.date_range('2023-01-01', periods=20)
        # 모든 종목이 동일한 움직임을 보이도록 설정
        price_data = pd.DataFrame({
            'Close': {
                'NVDA': np.linspace(100, 150, 20),
                'AMD': np.linspace(50, 75, 20),
                'TSM': np.linspace(80, 120, 20),
                'AVGO': np.linspace(300, 450, 20)
            }
        }, index=dates)
        
        mock_tickers.return_value.history.return_value = price_data
        
        portfolio = {
            'positions': [
                {'symbol': 'NVDA', 'quantity': 10},
                {'symbol': 'AMD', 'quantity': 20},
                {'symbol': 'TSM', 'quantity': 15},
                {'symbol': 'AVGO', 'quantity': 5}
            ],
            'current_value': 100000,
            'peak_value': 120000
        }
        
        regime, avg_corr = self.detector.detect_correlation_regime(portfolio)
        
        assert regime == 'crisis_correlation'
        assert avg_corr >= 0.85
    
    @patch('backend.ai.correlation_shock_detector.yf.Tickers')
    def test_elevated_correlation_detection(self, mock_tickers):
        """상관관계 0.70-0.84 탐지 시 'elevated_correlation' 반환"""
        # Mock 데이터 설정
        mock_data = Mock()
        # 중간 상관관계를 가진 데이터 생성
        dates = pd.date_range('2023-01-01', periods=20)
        np.random.seed(42)  # 재현성을 위한 시드 설정
        
        # 기본 추세 + 약간의 노이즈
        base_trend = np.linspace(100, 120, 20)
        price_data = pd.DataFrame({
            'Close': {
                'NVDA': base_trend + np.random.normal(0, 2, 20),
                'AMD': base_trend * 0.8 + np.random.normal(0, 3, 20),
                'TSM': base_trend * 1.2 + np.random.normal(0, 4, 20),
                'AVGO': base_trend * 3 + np.random.normal(0, 8, 20)
            }
        }, index=dates)
        
        mock_tickers.return_value.history.return_value = price_data
        
        portfolio = {
            'positions': [
                {'symbol': 'NVDA', 'quantity': 10},
                {'symbol': 'AMD', 'quantity': 20},
                {'symbol': 'TSM', 'quantity': 15},
                {'symbol': 'AVGO', 'quantity': 5}
            ],
            'current_value': 100000,
            'peak_value': 120000
        }
        
        regime, avg_corr = self.detector.detect_correlation_regime(portfolio)
        
        assert regime == 'elevated_correlation'
        assert 0.70 <= avg_corr < 0.85
    
    @patch('backend.ai.correlation_shock_detector.yf.Tickers')
    def test_normal_correlation_detection(self, mock_tickers):
        """상관관계 0.70 미만 탐지 시 'normal' 반환"""
        # Mock 데이터 설정
        mock_data = Mock()
        # 낮은 상관관계를 가진 데이터 생성
        dates = pd.date_range('2023-01-01', periods=20)
        np.random.seed(42)  # 재현성을 위한 시드 설정
        
        # 독립적인 움직임을 보이는 데이터
        price_data = pd.DataFrame({
            'Close': {
                'NVDA': np.random.normal(100, 10, 20),
                'AMD': np.random.normal(50, 8, 20),
                'TSM': np.random.normal(80, 12, 20),
                'AVGO': np.random.normal(300, 30, 20)
            }
        }, index=dates)
        
        mock_tickers.return_value.history.return_value = price_data
        
        portfolio = {
            'positions': [
                {'symbol': 'NVDA', 'quantity': 10},
                {'symbol': 'AMD', 'quantity': 20},
                {'symbol': 'TSM', 'quantity': 15},
                {'symbol': 'AVGO', 'quantity': 5}
            ],
            'current_value': 100000,
            'peak_value': 120000
        }
        
        regime, avg_corr = self.detector.detect_correlation_regime(portfolio)
        
        assert regime == 'normal'
        assert avg_corr < 0.70
    
    def test_calculate_average_correlation(self):
        """평균 상관관계 계산 테스트"""
        # 테스트용 상관관계 행렬
        corr_matrix = pd.DataFrame({
            'NVDA': {'NVDA': 1.0, 'AMD': 0.8, 'TSM': 0.7, 'AVGO': 0.9},
            'AMD': {'NVDA': 0.8, 'AMD': 1.0, 'TSM': 0.6, 'AVGO': 0.7},
            'TSM': {'NVDA': 0.7, 'AMD': 0.6, 'TSM': 1.0, 'AVGO': 0.8},
            'AVGO': {'NVDA': 0.9, 'AMD': 0.7, 'TSM': 0.8, 'AVGO': 1.0}
        })
        
        avg_corr = self.detector._calculate_average_correlation(corr_matrix)
        
        # 대각선 제외 평균: (0.8+0.7+0.9+0.6+0.7+0.8+0.7+0.6+0.8+0.7+0.8+0.8) / 12
        expected = (0.8+0.7+0.9+0.6+0.7+0.8+0.7+0.6+0.8+0.7+0.8+0.8) / 12
        
        assert abs(avg_corr - expected) < 0.001
    
    def test_determine_correlation_regime(self):
        """상관관계 국면 판단 테스트"""
        assert self.detector._determine_correlation_regime(0.9) == 'crisis_correlation'
        assert self.detector._determine_correlation_regime(0.85) == 'crisis_correlation'
        assert self.detector._determine_correlation_regime(0.8) == 'elevated_correlation'
        assert self.detector._determine_correlation_regime(0.7) == 'elevated_correlation'
        assert self.detector._determine_correlation_regime(0.69) == 'normal'
        assert self.detector._determine_correlation_regime(0.5) == 'normal'
    
    @patch('backend.ai.correlation_shock_detector.yf.Tickers')
    def test_fetch_returns_data_error_handling(self, mock_tickers):
        """데이터 가져오기 에러 핸들링 테스트"""
        # API 호출 예외 발생
        mock_tickers.side_effect = Exception("API Error")
        
        returns = self.detector._fetch_returns_data(['AAPL', 'MSFT'])
        
        assert returns is None
    
    def test_detect_correlation_regime_error_handling(self):
        """상관관계 감지 에러 핸들링 테스트"""
        # 잘못된 포트폴리오 데이터
        portfolio = None
        
        regime, avg_corr = self.detector.detect_correlation_regime(portfolio)
        
        assert regime == 'insufficient_data'
        assert avg_corr == 0.0