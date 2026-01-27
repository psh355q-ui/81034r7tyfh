"""
Meta-Controller V2 테스트
"""

import pytest
from unittest.mock import Mock, patch
from backend.ai.meta_controller_v2 import MetaControllerV2


class TestMetaControllerV2:
    """MetaControllerV2 클래스 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.meta_controller = MetaControllerV2()
    
    @patch('backend.ai.meta_controller_v2.CorrelationShockDetector')
    @patch('backend.ai.meta_controller_v2.DrawdownRecoveryMode')
    def test_scenario_1_normal_vix_critical_drawdown(self, mock_drawdown, mock_correlation):
        """Scenario 1: VIX 15 (정상) + Drawdown 20% → forced_mode='dividend'"""
        # Mock 설정
        mock_correlation.return_value.detect_correlation_regime.return_value = ('normal', 0.5)
        mock_drawdown.return_value.check_portfolio_drawdown.return_value = {
            'severity': 'critical',
            'drawdown': 0.2,
            'forced_mode': 'dividend',
            'position_limit_multiplier': 0.3,
            'reason': 'Critical drawdown (20.0%) detected. Forcing dividend mode.',
            'timestamp': '2026-01-27T15:00:00'
        }
        
        market_data = {'vix': 15}
        portfolio_data = {
            'current_value': 80000,
            'peak_value': 100000,
            'positions': [{'symbol': 'AAPL', 'quantity': 100}]
        }
        
        result = self.meta_controller.evaluate_market_regime(market_data, portfolio_data)
        
        assert result['final_regime'] == 'crisis_drawdown'
        assert result['forced_mode'] == 'dividend'
        assert result['position_limit_multiplier'] == 0.3
        assert 'Critical drawdown' in result['reason']
    
    @patch('backend.ai.meta_controller_v2.CorrelationShockDetector')
    @patch('backend.ai.meta_controller_v2.DrawdownRecoveryMode')
    def test_scenario_2_crisis_vix_crisis_correlation(self, mock_drawdown, mock_correlation):
        """Scenario 2: VIX 38 (위기) + Correlation 0.92 → forced_mode='dividend' (둘 다 crisis지만 Drawdown이 우선)"""
        # Mock 설정
        mock_correlation.return_value.detect_correlation_regime.return_value = ('crisis_correlation', 0.92)
        mock_drawdown.return_value.check_portfolio_drawdown.return_value = {
            'severity': 'critical',
            'drawdown': 0.25,
            'forced_mode': 'dividend',
            'position_limit_multiplier': 0.3,
            'reason': 'Critical drawdown (25.0%) detected. Forcing dividend mode.',
            'timestamp': '2026-01-27T15:00:00'
        }
        
        market_data = {'vix': 38}
        portfolio_data = {
            'current_value': 75000,
            'peak_value': 100000,
            'positions': [
                {'symbol': 'NVDA', 'quantity': 10},
                {'symbol': 'AMD', 'quantity': 20}
            ]
        }
        
        result = self.meta_controller.evaluate_market_regime(market_data, portfolio_data)
        
        assert result['final_regime'] == 'crisis_drawdown'  # Drawdown이 우선
        assert result['forced_mode'] == 'dividend'
        assert result['position_limit_multiplier'] == 0.3
        assert 'Critical drawdown' in result['reason']
    
    @patch('backend.ai.meta_controller_v2.CorrelationShockDetector')
    @patch('backend.ai.meta_controller_v2.DrawdownRecoveryMode')
    def test_scenario_3_all_normal(self, mock_drawdown, mock_correlation):
        """Scenario 3: 모두 정상 → final_regime='normal', multiplier=1.0"""
        # Mock 설정
        mock_correlation.return_value.detect_correlation_regime.return_value = ('normal', 0.4)
        mock_drawdown.return_value.check_portfolio_drawdown.return_value = {
            'severity': 'normal',
            'drawdown': 0.02,
            'forced_mode': None,
            'position_limit_multiplier': 1.0,
            'reason': 'Minimal drawdown (2.0%) detected. No action required.',
            'timestamp': '2026-01-27T15:00:00'
        }
        
        market_data = {'vix': 15}
        portfolio_data = {
            'current_value': 98000,
            'peak_value': 100000,
            'positions': [
                {'symbol': 'AAPL', 'quantity': 100},
                {'symbol': 'MSFT', 'quantity': 50}
            ]
        }
        
        result = self.meta_controller.evaluate_market_regime(market_data, portfolio_data)
        
        assert result['final_regime'] == 'normal'
        assert result['forced_mode'] is None
        assert result['position_limit_multiplier'] == 1.0
    
    @patch('backend.ai.meta_controller_v2.CorrelationShockDetector')
    @patch('backend.ai.meta_controller_v2.DrawdownRecoveryMode')
    def test_evaluate_vix_regime(self, mock_drawdown, mock_correlation):
        """VIX 국면 평가 테스트"""
        # Mock 설정 (다른 테스트에 영향 주지 않도록)
        mock_correlation.return_value.detect_correlation_regime.return_value = ('normal', 0.5)
        mock_drawdown.return_value.check_portfolio_drawdown.return_value = {
            'severity': 'normal',
            'drawdown': 0.0,
            'forced_mode': None,
            'position_limit_multiplier': 1.0,
            'reason': 'Test',
            'timestamp': '2026-01-27T15:00:00'
        }
        
        # Crisis VIX
        result1 = self.meta_controller.evaluate_market_regime({'vix': 45}, {})
        assert result1['vix_regime'] == 'crisis_vix'
        
        # Elevated VIX
        result2 = self.meta_controller.evaluate_market_regime({'vix': 35}, {})
        assert result2['vix_regime'] == 'elevated_vix'
        
        # Normal VIX
        result3 = self.meta_controller.evaluate_market_regime({'vix': 20}, {})
        assert result3['vix_regime'] == 'normal'
        
        # None VIX
        result4 = self.meta_controller.evaluate_market_regime({}, {})
        assert result4['vix_regime'] == 'insufficient_data'
    
    @patch('backend.ai.meta_controller_v2.CorrelationShockDetector')
    @patch('backend.ai.meta_controller_v2.DrawdownRecoveryMode')
    def test_warning_drawdown_priority(self, mock_drawdown, mock_correlation):
        """Warning Drawdown이 다른 요인보다 우선하는지 테스트"""
        # Mock 설정
        mock_correlation.return_value.detect_correlation_regime.return_value = ('elevated_correlation', 0.75)
        mock_drawdown.return_value.check_portfolio_drawdown.return_value = {
            'severity': 'warning',
            'drawdown': 0.12,
            'forced_mode': None,
            'position_limit_multiplier': 0.5,
            'reason': 'Warning level drawdown (12.0%) detected. Reducing position size.',
            'timestamp': '2026-01-27T15:00:00'
        }
        
        market_data = {'vix': 35}  # elevated_vix (50점)
        portfolio_data = {
            'current_value': 88000,
            'peak_value': 100000,
            'positions': [{'symbol': 'AAPL', 'quantity': 100}]
        }
        
        result = self.meta_controller.evaluate_market_regime(market_data, portfolio_data)
        
        # warning_drawdown (70점) > elevated_correlation (60점) > elevated_vix (50점)
        assert result['final_regime'] == 'warning_drawdown'
        assert result['position_limit_multiplier'] == 0.5
        assert 'Drawdown-based decision' in result['reason']
    
    def test_get_risk_summary(self):
        """리스크 요약 정보 테스트"""
        # Mock으로 evaluate_market_regime 결과 설정
        with patch.object(self.meta_controller, 'evaluate_market_regime') as mock_evaluate:
            mock_evaluate.return_value = {
                'final_regime': 'crisis_drawdown',
                'vix_regime': 'normal',
                'correlation_regime': 'normal',
                'drawdown_result': {'severity': 'critical'},
                'forced_mode': 'dividend',
                'position_limit_multiplier': 0.3,
                'reason': 'Test'
            }
            
            market_data = {'vix': 15}
            portfolio_data = {
                'current_value': 80000,
                'peak_value': 100000,
                'positions': [{'symbol': 'AAPL', 'quantity': 100}]
            }
            
            summary = self.meta_controller.get_risk_summary(market_data, portfolio_data)
            
            assert summary['risk_level'] == 'CRITICAL'
            assert summary['primary_risk_factor'] == 'Portfolio Loss'
            assert 'Force portfolio mode to' in summary['recommended_actions'][0]
            assert 'Reduce position sizes significantly' in summary['recommended_actions']
    
    def test_calculate_risk_level(self):
        """리스크 레벨 계산 테스트"""
        # Critical
        evaluation1 = {'final_regime': 'crisis_drawdown'}
        assert self.meta_controller._calculate_risk_level(evaluation1) == 'CRITICAL'
        
        evaluation2 = {'final_regime': 'crisis_correlation'}
        assert self.meta_controller._calculate_risk_level(evaluation2) == 'CRITICAL'
        
        evaluation3 = {'final_regime': 'crisis_vix'}
        assert self.meta_controller._calculate_risk_level(evaluation3) == 'CRITICAL'
        
        # High
        evaluation4 = {'final_regime': 'warning_drawdown'}
        assert self.meta_controller._calculate_risk_level(evaluation4) == 'HIGH'
        
        evaluation5 = {'final_regime': 'elevated_correlation'}
        assert self.meta_controller._calculate_risk_level(evaluation5) == 'HIGH'
        
        # Medium
        evaluation6 = {'final_regime': 'single_position'}
        assert self.meta_controller._calculate_risk_level(evaluation6) == 'MEDIUM'
        
        # Low
        evaluation7 = {'final_regime': 'normal'}
        assert self.meta_controller._calculate_risk_level(evaluation7) == 'LOW'
    
    def test_identify_primary_risk(self):
        """주요 리스크 요인 식별 테스트"""
        evaluation1 = {'final_regime': 'crisis_drawdown'}
        assert self.meta_controller._identify_primary_risk(evaluation1) == 'Portfolio Loss'
        
        evaluation2 = {'final_regime': 'crisis_correlation'}
        assert self.meta_controller._identify_primary_risk(evaluation2) == 'Diversification Failure'
        
        evaluation3 = {'final_regime': 'crisis_vix'}
        assert self.meta_controller._identify_primary_risk(evaluation3) == 'Market Volatility'
        
        evaluation4 = {'final_regime': 'normal'}
        assert self.meta_controller._identify_primary_risk(evaluation4) == 'Normal Market Conditions'
    
    def test_get_recommended_actions(self):
        """추천 행동 반환 테스트"""
        # Critical
        evaluation1 = {
            'final_regime': 'crisis_drawdown',
            'forced_mode': 'dividend',
            'position_limit_multiplier': 0.3
        }
        actions1 = self.meta_controller._get_recommended_actions(evaluation1)
        assert "Force portfolio mode to 'dividend'" in actions1
        assert "Reduce position sizes significantly" in actions1
        assert "Apply position limit multiplier of 0.3" in actions1
        
        # Warning
        evaluation2 = {
            'final_regime': 'warning_drawdown',
            'forced_mode': None,
            'position_limit_multiplier': 0.5
        }
        actions2 = self.meta_controller._get_recommended_actions(evaluation2)
        assert "Monitor positions closely" in actions2
        assert "Consider partial position reduction" in actions2
        assert "Apply position limit multiplier of 0.5" in actions2
        
        # Normal
        evaluation3 = {
            'final_regime': 'normal',
            'forced_mode': None,
            'position_limit_multiplier': 1.0
        }
        actions3 = self.meta_controller._get_recommended_actions(evaluation3)
        assert len(actions3) == 0  # 정상 상태에서는 추천 행동 없음
    
    def test_error_handling(self):
        """에러 핸들링 테스트"""
        # None 입력
        result1 = self.meta_controller.evaluate_market_regime(None, None)
        assert result1['final_regime'] == 'insufficient_data'
        assert 'Error in evaluation' in result1['reason']
        
        # 빈 딕셔너리
        result2 = self.meta_controller.evaluate_market_regime({}, {})
        assert result2['final_regime'] == 'insufficient_data'
        assert 'Error in evaluation' in result2['reason']