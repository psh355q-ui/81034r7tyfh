"""
Drawdown Recovery Mode

포트폴리오 손실 기반 자동 방어 모드 전환.
20% 손실에 Dividend 모드 강제 전환, 10% 손실에 포지션 50% 축소.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DrawdownRecoveryMode:
    """
    포트폴리오 손실 기반 자동 방어 모드 전환 클래스
    """
    
    def __init__(self):
        """초기화"""
        self.critical_threshold = 0.20  # 20% 손실 시 critical
        self.warning_threshold = 0.10   # 10% 손실 시 warning
        self.normal_threshold = 0.05    # 5% 손실 시 normal
        
    def check_drawdown(self, current_value: float, peak_value: float) -> Dict:
        """
        포트폴리오 드로다운을 체크하고 방어 모드를 결정
        
        Args:
            current_value: 현재 포트폴리오 가치
            peak_value: 포트폴리오 최고 가치
            
        Returns:
            Dict: 드로다운 분석 결과
                - severity: 'critical', 'warning', 'normal'
                - drawdown: 드로다운 비율 (0.0 ~ 1.0)
                - forced_mode: 강제 전환 모드 (critical 시 'dividend')
                - position_limit_multiplier: 포지션 한정 배수
                - reason: 사유
                - timestamp: 분석 시간
        """
        try:
            # 입력값 검증
            if current_value <= 0 or peak_value <= 0:
                return {
                    'severity': 'normal',
                    'drawdown': 0.0,
                    'forced_mode': None,
                    'position_limit_multiplier': 1.0,
                    'reason': 'Invalid portfolio values',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 드로다운 계산
            drawdown = (peak_value - current_value) / peak_value
            
            # 드로다운 수준에 따른 방어 모드 결정
            if drawdown >= self.critical_threshold:
                return {
                    'severity': 'critical',
                    'drawdown': drawdown,
                    'forced_mode': 'dividend',
                    'position_limit_multiplier': 0.3,
                    'reason': f'Critical drawdown ({drawdown:.1%}) detected. Forcing dividend mode.',
                    'timestamp': datetime.now().isoformat()
                }
            elif drawdown >= self.warning_threshold:
                return {
                    'severity': 'warning',
                    'drawdown': drawdown,
                    'forced_mode': None,
                    'position_limit_multiplier': 0.5,
                    'reason': f'Warning level drawdown ({drawdown:.1%}) detected. Reducing position size.',
                    'timestamp': datetime.now().isoformat()
                }
            elif drawdown >= self.normal_threshold:
                return {
                    'severity': 'normal',
                    'drawdown': drawdown,
                    'forced_mode': None,
                    'position_limit_multiplier': 1.0,
                    'reason': f'Normal drawdown ({drawdown:.1%}) detected. No action required.',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'severity': 'normal',
                    'drawdown': drawdown,
                    'forced_mode': None,
                    'position_limit_multiplier': 1.0,
                    'reason': f'Minimal drawdown ({drawdown:.1%}) detected. No action required.',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in drawdown recovery check: {str(e)}")
            return {
                'severity': 'normal',
                'drawdown': 0.0,
                'forced_mode': None,
                'position_limit_multiplier': 1.0,
                'reason': f'Error in drawdown calculation: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def check_portfolio_drawdown(self, portfolio: Dict) -> Dict:
        """
        포트폴리오 딕셔너리에서 드로다운을 체크
        
        Args:
            portfolio: 포트폴리오 정보 딕셔너리
                - current_value: 현재 포트폴리오 가치
                - peak_value: 포트폴리오 최고 가치
                
        Returns:
            Dict: 드로다운 분석 결과
        """
        try:
            current_value = portfolio.get('current_value', 0)
            peak_value = portfolio.get('peak_value', 0)
            
            return self.check_drawdown(current_value, peak_value)
            
        except Exception as e:
            logger.error(f"Error in portfolio drawdown check: {str(e)}")
            return {
                'severity': 'normal',
                'drawdown': 0.0,
                'forced_mode': None,
                'position_limit_multiplier': 1.0,
                'reason': f'Error in portfolio drawdown check: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }