"""
Drawdown Recovery Mode 테스트
"""

import pytest
from datetime import datetime
from backend.ai.drawdown_recovery import DrawdownRecoveryMode


class TestDrawdownRecoveryMode:
    """DrawdownRecoveryMode 클래스 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.recovery_mode = DrawdownRecoveryMode()
    
    def test_critical_drawdown(self):
        """20% 손실 → severity='critical', forced_mode='dividend'"""
        result = self.recovery_mode.check_drawdown(current_value=80000, peak_value=100000)
        
        assert result['severity'] == 'critical'
        assert result['drawdown'] == 0.2
        assert result['forced_mode'] == 'dividend'
        assert result['position_limit_multiplier'] == 0.3
        assert 'Critical drawdown' in result['reason']
        assert 'timestamp' in result
    
    def test_warning_drawdown(self):
        """10% 손실 → severity='warning', multiplier=0.5"""
        result = self.recovery_mode.check_drawdown(current_value=90000, peak_value=100000)
        
        assert result['severity'] == 'warning'
        assert result['drawdown'] == 0.1
        assert result['forced_mode'] is None
        assert result['position_limit_multiplier'] == 0.5
        assert 'Warning level drawdown' in result['reason']
    
    def test_normal_drawdown(self):
        """5% 손실 → severity='normal', multiplier=1.0"""
        result = self.recovery_mode.check_drawdown(current_value=95000, peak_value=100000)
        
        assert result['severity'] == 'normal'
        assert result['drawdown'] == 0.05
        assert result['forced_mode'] is None
        assert result['position_limit_multiplier'] == 1.0
        assert 'Normal drawdown' in result['reason']
    
    def test_minimal_drawdown(self):
        """1% 손실 → severity='normal', multiplier=1.0"""
        result = self.recovery_mode.check_drawdown(current_value=99000, peak_value=100000)
        
        assert result['severity'] == 'normal'
        assert result['drawdown'] == 0.01
        assert result['forced_mode'] is None
        assert result['position_limit_multiplier'] == 1.0
        assert 'Minimal drawdown' in result['reason']
    
    def test_no_drawdown(self):
        """드로다운 없음 → severity='normal', drawdown=0.0"""
        result = self.recovery_mode.check_drawdown(current_value=100000, peak_value=100000)
        
        assert result['severity'] == 'normal'
        assert result['drawdown'] == 0.0
        assert result['forced_mode'] is None
        assert result['position_limit_multiplier'] == 1.0
    
    def test_profit_situation(self):
        """이익 상태 → severity='normal', drawdown=0.0"""
        result = self.recovery_mode.check_drawdown(current_value=110000, peak_value=100000)
        
        assert result['severity'] == 'normal'
        assert result['drawdown'] == 0.0  # 이익 상태에서는 드로다운 0으로 처리
        assert result['forced_mode'] is None
        assert result['position_limit_multiplier'] == 1.0
    
    def test_invalid_values(self):
        """잘못된 값 입력 → severity='normal', drawdown=0.0"""
        # 0 또는 음수 값
        result1 = self.recovery_mode.check_drawdown(current_value=0, peak_value=100000)
        assert result1['severity'] == 'normal'
        assert result1['drawdown'] == 0.0
        assert 'Invalid portfolio values' in result1['reason']
        
        result2 = self.recovery_mode.check_drawdown(current_value=80000, peak_value=0)
        assert result2['severity'] == 'normal'
        assert result2['drawdown'] == 0.0
        assert 'Invalid portfolio values' in result2['reason']
        
        result3 = self.recovery_mode.check_drawdown(current_value=-1000, peak_value=100000)
        assert result3['severity'] == 'normal'
        assert result3['drawdown'] == 0.0
        assert 'Invalid portfolio values' in result3['reason']
    
    def test_extreme_drawdown(self):
        """극단적인 드로다운 (50% 손실) → severity='critical'"""
        result = self.recovery_mode.check_drawdown(current_value=50000, peak_value=100000)
        
        assert result['severity'] == 'critical'
        assert result['drawdown'] == 0.5
        assert result['forced_mode'] == 'dividend'
        assert result['position_limit_multiplier'] == 0.3
    
    def test_portfolio_dict_input(self):
        """포트폴리오 딕셔너리 입력 테스트"""
        portfolio = {
            'current_value': 80000,
            'peak_value': 100000
        }
        
        result = self.recovery_mode.check_portfolio_drawdown(portfolio)
        
        assert result['severity'] == 'critical'
        assert result['drawdown'] == 0.2
        assert result['forced_mode'] == 'dividend'
        assert result['position_limit_multiplier'] == 0.3
    
    def test_portfolio_dict_missing_values(self):
        """포트폴리오 딕셔너리에 값이 없는 경우"""
        portfolio = {}  # 빈 딕셔너리
        
        result = self.recovery_mode.check_portfolio_drawdown(portfolio)
        
        assert result['severity'] == 'normal'
        assert result['drawdown'] == 0.0
        assert result['forced_mode'] is None
        assert result['position_limit_multiplier'] == 1.0
    
    def test_portfolio_dict_partial_values(self):
        """포트폴리오 딕셔너리에 일부 값만 있는 경우"""
        portfolio = {
            'current_value': 90000
            # peak_value 없음
        }
        
        result = self.recovery_mode.check_portfolio_drawdown(portfolio)
        
        assert result['severity'] == 'normal'
        assert result['drawdown'] == 0.0
        assert result['forced_mode'] is None
        assert result['position_limit_multiplier'] == 1.0
    
    def test_timestamp_format(self):
        """타임스탬프 형식 확인"""
        result = self.recovery_mode.check_drawdown(current_value=80000, peak_value=100000)
        
        # ISO 8601 형식인지 확인 (YYYY-MM-DDTHH:MM:SS)
        timestamp = result['timestamp']
        assert isinstance(timestamp, str)
        assert 'T' in timestamp
        # datetime 객체로 파싱 가능한지 확인
        datetime.fromisoformat(timestamp)
    
    def test_boundary_values(self):
        """경계값 테스트"""
        # 정확히 20% 드로다운
        result1 = self.recovery_mode.check_drawdown(current_value=80000, peak_value=100000)
        assert result1['severity'] == 'critical'
        
        # 정확히 10% 드로다운
        result2 = self.recovery_mode.check_drawdown(current_value=90000, peak_value=100000)
        assert result2['severity'] == 'warning'
        
        # 정확히 5% 드로다운
        result3 = self.recovery_mode.check_drawdown(current_value=95000, peak_value=100000)
        assert result3['severity'] == 'normal'
        
        # 19.9% 드로다운 (critical 아님)
        result4 = self.recovery_mode.check_drawdown(current_value=80100, peak_value=100000)
        assert result4['severity'] == 'warning'
        
        # 9.9% 드로다운 (warning 아님)
        result5 = self.recovery_mode.check_drawdown(current_value=90100, peak_value=100000)
        assert result5['severity'] == 'normal'