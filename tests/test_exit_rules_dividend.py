"""
Dividend Exit Rules Tests

TDD RED Phase: 배당 중단 감지 및 청산 로직 테스트
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime

# Import will fail initially (RED phase)
from backend.ai.exit_rules import DividendExitRule, ExitRuleEngine


class TestDividendExitRule:
    """Test Dividend Exit Rule - 배당 중단 감지"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.exit_rule = DividendExitRule()
    
    def test_dividend_cut_triggers_exit(self):
        """Test: 배당 삭감 시 청산 트리거 발동"""
        # Arrange
        position = {
            'ticker': 'T',  # AT&T (실제 2022년 배당 삭감)
            'mode': 'dividend',
            'entry_date': '2023-01-01'
        }
        
        dividend_history = {
            'previous': 0.52,  # Q1 dividend
            'current': 0.27    # Q2 dividend (48% cut!)
        }
        
        # Act
        result = self.exit_rule.check_exit(position, dividend_history)
        
        # Assert
        assert result['exit_triggered'] is True, "배당 삭감 시 청산 트리거 발동되어야 함"
        assert result['reason'] == 'dividend_cut', "사유는 'dividend_cut'이어야 함"
        assert result['cut_percentage'] > 40, "40% 이상 삭감 감지되어야 함"
        assert result['action'] == 'force_liquidate', "강제 청산 액션이어야 함"
        assert result['priority'] == 'immediate', "우선순위는 'immediate'여야 함"
    
    def test_dividend_maintained_no_exit(self):
        """Test: 배당 유지 시 청산 트리거 없음"""
        # Arrange
        position = {
            'ticker': 'JNJ',  # Johnson & Johnson
            'mode': 'dividend',
            'entry_date': '2023-01-01'
        }
        
        dividend_history = {
            'previous': 1.13,
            'current': 1.13  # Same dividend
        }
        
        # Act
        result = self.exit_rule.check_exit(position, dividend_history)
        
        # Assert
        assert result['exit_triggered'] is False, "배당 유지 시 청산 트리거 없어야 함"
        assert result['reason'] == 'dividend_maintained', "사유는 'dividend_maintained'여야 함"
        assert result['action'] is None, "청산 액션 없어야 함"
    
    def test_dividend_increase_no_exit(self):
        """Test: 배당 증가 시 청산 트리거 없음"""
        # Arrange
        position = {
            'ticker': 'KO',  # Coca-Cola
            'mode': 'dividend',
            'entry_date': '2023-01-01'
        }
        
        dividend_history = {
            'previous': 0.44,
            'current': 0.46  # 4.5% increase
        }
        
        # Act
        result = self.exit_rule.check_exit(position, dividend_history)
        
        # Assert
        assert result['exit_triggered'] is False, "배당 증가 시 청산 트리거 없어야 함"
        assert result['reason'] == 'dividend_increased', "사유는 'dividend_increased'여야 함"
        assert result['growth_percentage'] > 0, "증가율이 0보다 커야 함"
        assert abs(result['growth_percentage'] - 4.5) < 1, "약 4.5% 증가 감지되어야 함"
    
    def test_small_dividend_decrease_no_exit(self):
        """Test: 소폭 배당 감소(5% 미만) 시 청산 트리거 없음"""
        # Arrange
        position = {
            'ticker': 'PG',  # Procter & Gamble
            'mode': 'dividend',
            'entry_date': '2023-01-01'
        }
        
        dividend_history = {
            'previous': 0.90,
            'current': 0.88  # 2.2% decrease (minor)
        }
        
        # Act
        result = self.exit_rule.check_exit(position, dividend_history)
        
        # Assert
        assert result['exit_triggered'] is False, "소폭 배당 감소 시 청산 트리거 없어야 함"
        # Small decrease might be treated as "maintained" or have specific reason
    
    @patch('backend.ai.exit_rules.yf.Ticker')
    def test_yfinance_integration(self, mock_ticker_class):
        """Test: yfinance API 통합 (Mocked)"""
        # Arrange: Mock yfinance Ticker
        mock_ticker = Mock()
        
        # Simulate dividend history: Q1 0.52 → Q2 0.27 (cut)
        mock_dividends = pd.Series(
            [0.52, 0.27],
            index=pd.to_datetime(['2023-01-15', '2023-04-15'])
        )
        mock_ticker.dividends = mock_dividends
        mock_ticker_class.return_value = mock_ticker
        
        position = {
            'ticker': 'T',
            'mode': 'dividend',
            'entry_date': '2023-01-01'
        }
        
        # Act
        result = self.exit_rule.check_exit_live(position)
        
        # Assert
        assert result['exit_triggered'] is True, "실제 API 통합 시 배당 삭감 감지되어야 함"
        assert result['reason'] == 'dividend_cut'
        mock_ticker_class.assert_called_once_with('T')
    
    @patch('backend.ai.exit_rules.yf.Ticker')
    def test_yfinance_insufficient_data(self, mock_ticker_class):
        """Test: 배당 이력 불충분 시 처리"""
        # Arrange
        mock_ticker = Mock()
        mock_ticker.dividends = pd.Series([])  # Empty history
        mock_ticker_class.return_value = mock_ticker
        
        position = {'ticker': 'NVDA', 'mode': 'dividend'}
        
        # Act
        result = self.exit_rule.check_exit_live(position)
        
        # Assert
        assert result['exit_triggered'] is False
        assert result['reason'] == 'insufficient_dividend_history'
    
    @patch('backend.ai.exit_rules.yf.Ticker')
    def test_yfinance_api_error_handling(self, mock_ticker_class):
        """Test: yfinance API 에러 핸들링"""
        # Arrange
        mock_ticker_class.side_effect = Exception("API Error")
        
        position = {'ticker': 'ERROR', 'mode': 'dividend'}
        
        # Act
        result = self.exit_rule.check_exit_live(position)
        
        # Assert
        assert result['exit_triggered'] is False
        assert result['reason'] == 'api_error'
        assert 'error' in result
    
    def test_non_dividend_mode_ignored(self):
        """Test: dividend 모드가 아닌 경우 규칙 미적용"""
        # Arrange
        position = {
            'ticker': 'NVDA',
            'mode': 'aggressive',  # Not dividend mode
            'entry_date': '2023-01-01'
        }
        
        dividend_history = {
            'previous': 0.04,
            'current': 0.0  # Dividend cut (NVDA doesn't pay dividends anyway)
        }
        
        # Act
        result = self.exit_rule.check_exit(position, dividend_history)
        
        # Assert
        assert result['exit_triggered'] is False, "dividend 모드가 아니면 규칙 미적용"
        assert result['reason'] == 'mode_not_applicable'


class TestExitRuleEngine:
    """Test Exit Rule Engine - 통합 엔진"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.engine = ExitRuleEngine()
    
    @patch('backend.ai.exit_rules.yf.Ticker')
    def test_check_all_exits_dividend_mode(self, mock_ticker_class):
        """Test: dividend 모드 종합 체크"""
        # Arrange
        mock_ticker = Mock()
        mock_dividends = pd.Series([0.52, 0.27], index=pd.to_datetime(['2023-01-15', '2023-04-15']))
        mock_ticker.dividends = mock_dividends
        mock_ticker_class.return_value = mock_ticker
        
        position = {'ticker': 'T', 'mode': 'dividend'}
        
        # Act
        result = self.engine.check_all_exits(position)
        
        # Assert
        assert result['exit_triggered'] is True
        assert result['reason'] == 'dividend_cut'
    
    def test_check_all_exits_longterm_mode_not_implemented(self):
        """Test: long_term 모드는 아직 미구현"""
        position = {'ticker': 'AAPL', 'mode': 'long_term'}
        
        result = self.engine.check_all_exits(position)
        
        assert result['exit_triggered'] is False
        assert result['reason'] == 'no_applicable_rule'


if __name__ == '__main__':
    """직접 실행 시 테스트 수행"""
    pytest.main([__file__, '-v', '--tb=short'])
