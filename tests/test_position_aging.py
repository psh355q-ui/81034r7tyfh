"""
Position Aging Tracker Tests

TDD RED Phase: 포지션 보유 기간 리스크 관리 테스트
"""

import pytest
from datetime import datetime, timedelta
from backend.ai.position_aging import PositionAgingTracker

class TestPositionAgingTracker:
    """Test Position Aging Tracker - 보유 기간 기반 리스크 관리"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.tracker = PositionAgingTracker()
    
    def test_trading_position_healthy(self):
        """Test: Trading 포지션 3일 보유 (정상)"""
        entry_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        position = {
            'ticker': 'TSLA',
            'mode': 'trading',
            'entry_date': entry_date
        }
        
        result = self.tracker.check_aging(position)
        
        assert result['stale'] is False
        assert result['level'] == 'normal'
        assert result['days_held'] == 3
    
    def test_trading_position_warning(self):
        """Test: Trading 포지션 6일 보유 (경고)"""
        # Threshold: Warning > 5 days
        entry_date = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
        position = {
            'ticker': 'TSLA',
            'mode': 'trading',
            'entry_date': entry_date
        }
        
        result = self.tracker.check_aging(position)
        
        assert result['stale'] is True
        assert result['level'] == 'warning'
        assert str(result['days_held']) in result['message']
        assert "초과" in result['message']
    
    def test_trading_position_critical(self):
        """Test: Trading 포지션 8일 보유 (위험 - 청산 권고)"""
        # Threshold: Critical > 7 days
        entry_date = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
        position = {
            'ticker': 'NVDA',
            'mode': 'trading',
            'entry_date': entry_date
        }
        
        result = self.tracker.check_aging(position)
        
        assert result['stale'] is True
        assert result['level'] == 'critical'
        assert result['action'] == 'recommend_exit'
    
    def test_longterm_position_warning(self):
        """Test: Long-Term 포지션 100일 보유 (Thesis 점검 필요)"""
        # Threshold: Warning > 90 days
        entry_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        position = {
            'ticker': 'AAPL',
            'mode': 'long_term',
            'entry_date': entry_date
        }
        
        result = self.tracker.check_aging(position)
        
        assert result['stale'] is True
        assert result['level'] == 'warning'
        assert result['action'] == 'thesis_review'
    
    def test_dividend_position_healthy(self):
        """Test: Dividend 포지션 100일 보유 (정상)"""
        # Threshold: Warning > 180 days
        entry_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        position = {
            'ticker': 'O',
            'mode': 'dividend',
            'entry_date': entry_date
        }
        
        result = self.tracker.check_aging(position)
        
        assert result['stale'] is False
        assert result['level'] == 'normal'
    
    def test_invalid_date_handling(self):
        """Test: 잘못된 날짜 형식 처리"""
        position = {
            'ticker': 'ERROR',
            'mode': 'trading',
            'entry_date': 'invalid-date'
        }
        
        result = self.tracker.check_aging(position)
        
        assert result['stale'] is False
        assert result['error'] is not None
    
    def test_unknown_mode_defaults(self):
        """Test: 알 수 없는 모드는 기본값(Long-Term) 적용 혹은 무시"""
        entry_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        position = {
            'ticker': 'UNKNOWN',
            'mode': 'custom_mode',
            'entry_date': entry_date
        }
        
        result = self.tracker.check_aging(position)
        
        # Should probably treat as normal or ignore
        assert result['level'] == 'normal'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
