"""
Meta-Controller V2

3축 리스크 감지 시스템 통합. VIX + Correlation + Drawdown 중 가장 보수적인 판단 채택.
우선순위: Drawdown > Correlation > VIX.
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

from .correlation_shock_detector import CorrelationShockDetector
from .drawdown_recovery import DrawdownRecoveryMode

logger = logging.getLogger(__name__)

class MetaControllerV2:
    """
    3축 리스크 감지 시스템 통합 클래스
    """
    
    def __init__(self):
        """초기화"""
        self.correlation_detector = CorrelationShockDetector()
        self.drawdown_monitor = DrawdownRecoveryMode()
        
        # 우선순위 정의 (높을수록 보수적)
        self.regime_priority = {
            'crisis_drawdown': 100,
            'crisis_correlation': 90,
            'crisis_vix': 80,
            'warning_drawdown': 70,
            'elevated_correlation': 60,
            'elevated_vix': 50,
            'normal': 10,
            'single_position': 5,
            'insufficient_data': 0
        }
    
    def evaluate_market_regime(self, market_data: Dict, portfolio_data: Dict) -> Dict:
        """
        시장 국면을 평가하고 최종 결정을 반환
        
        Args:
            market_data: 시장 데이터 딕셔너리
                - vix: VIX 지수
                - spy_ticker: SPY 티커 (선택적)
            portfolio_data: 포트폴리오 데이터 딕셔너리
                - current_value: 현재 포트폴리오 가치
                - peak_value: 포트폴리오 최고 가치
                - positions: 포지션 정보 리스트
                
        Returns:
            Dict: 시장 국면 평가 결과
                - final_regime: 최종 국면
                - vix_regime: VIX 기반 국면
                - correlation_regime: Correlation 기반 국면
                - drawdown_result: Drawdown 분석 결과
                - forced_mode: 강제 전환 모드 (있는 경우)
                - position_limit_multiplier: 포지션 한정 배수
                - reason: 결정 사유
                - timestamp: 평가 시간
        """
        try:
            # 1. VIX 기반 판단
            vix = market_data.get('vix')
            vix_regime, vix_score = self._evaluate_vix_regime(vix)
            
            # 2. Correlation 기반 판단
            correlation_regime, avg_correlation = self.correlation_detector.detect_correlation_regime(portfolio_data)
            correlation_score = self._get_regime_score(correlation_regime)
            
            # 3. Drawdown 기반 판단
            drawdown_result = self.drawdown_monitor.check_portfolio_drawdown(portfolio_data)
            drawdown_regime = self._convert_drawdown_to_regime(drawdown_result['severity'])
            drawdown_score = self._get_regime_score(drawdown_regime)
            
            # 4. 가장 보수적인 판단 채택
            final_regime, reason = self._combine_regimes(
                vix_regime, correlation_regime, drawdown_regime,
                vix_score, correlation_score, drawdown_score,
                drawdown_result
            )
            
            # 5. 최종 결과 구성
            result = {
                'final_regime': final_regime,
                'vix_regime': vix_regime,
                'correlation_regime': correlation_regime,
                'drawdown_result': drawdown_result,
                'avg_correlation': avg_correlation,
                'forced_mode': drawdown_result.get('forced_mode'),
                'position_limit_multiplier': drawdown_result.get('position_limit_multiplier', 1.0),
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Meta-Controller V2 evaluation: {final_regime}, reason: {reason}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in market regime evaluation: {str(e)}")
            return {
                'final_regime': 'insufficient_data',
                'vix_regime': 'insufficient_data',
                'correlation_regime': 'insufficient_data',
                'drawdown_result': {'severity': 'normal'},
                'avg_correlation': 0.0,
                'forced_mode': None,
                'position_limit_multiplier': 1.0,
                'reason': f'Error in evaluation: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _evaluate_vix_regime(self, vix: Optional[float]) -> Tuple[str, float]:
        """
        VIX 지수 기반 시장 국면 평가
        
        Args:
            vix: VIX 지수
            
        Returns:
            Tuple[str, float]: (국면, 점수)
        """
        if vix is None:
            return 'insufficient_data', 0.0
        
        if vix >= 40:
            return 'crisis_vix', 80.0
        elif vix >= 30:
            return 'elevated_vix', 50.0
        else:
            return 'normal', 10.0
    
    def _convert_drawdown_to_regime(self, severity: str) -> str:
        """
        Drawdown 심각도를 국면으로 변환
        
        Args:
            severity: 드로다운 심각도 ('critical', 'warning', 'normal')
            
        Returns:
            str: 국면
        """
        if severity == 'critical':
            return 'crisis_drawdown'
        elif severity == 'warning':
            return 'warning_drawdown'
        else:
            return 'normal'
    
    def _get_regime_score(self, regime: str) -> float:
        """
        국면에 따른 점수 반환
        
        Args:
            regime: 국면
            
        Returns:
            float: 점수
        """
        return self.regime_priority.get(regime, 0.0)
    
    def _combine_regimes(self, vix_regime: str, correlation_regime: str, drawdown_regime: str,
                      vix_score: float, correlation_score: float, drawdown_score: float,
                      drawdown_result: Dict) -> Tuple[str, str]:
        """
        3개 국면을 조합하여 최종 국면 결정
        
        Args:
            vix_regime: VIX 기반 국면
            correlation_regime: Correlation 기반 국면
            drawdown_regime: Drawdown 기반 국면
            vix_score: VIX 점수
            correlation_score: Correlation 점수
            drawdown_score: Drawdown 점수
            drawdown_result: Drawdown 분석 결과
            
        Returns:
            Tuple[str, str]: (최종 국면, 결정 사유)
        """
        # 점수 비교하여 가장 높은 점수의 국면 선택
        scores = {
            'vix': (vix_regime, vix_score),
            'correlation': (correlation_regime, correlation_score),
            'drawdown': (drawdown_regime, drawdown_score)
        }
        
        # 가장 높은 점수를 가진 국면 찾기
        highest_source = max(scores.keys(), key=lambda k: scores[k][1])
        highest_regime, highest_score = scores[highest_source]
        
        # Drawdown이 critical인 경우 무조건 Drawdown 우선
        if drawdown_result.get('severity') == 'critical':
            return 'crisis_drawdown', f"Critical drawdown ({drawdown_result['drawdown']:.1%}) detected. Forcing dividend mode."
        
        # 점수가 동일한 경우 우선순위에 따라 결정 (Drawdown > Correlation > VIX)
        if highest_score == drawdown_score:
            return drawdown_regime, f"Drawdown-based decision: {drawdown_regime} (severity: {drawdown_result['severity']})"
        elif highest_score == correlation_score:
            return correlation_regime, f"Correlation-based decision: {correlation_regime} (avg_corr: {drawdown_result.get('avg_correlation', 0):.3f})"
        else:
            return vix_regime, f"VIX-based decision: {vix_regime}"
    
    def get_risk_summary(self, market_data: Dict, portfolio_data: Dict) -> Dict:
        """
        리스크 요약 정보 반환
        
        Args:
            market_data: 시장 데이터
            portfolio_data: 포트폴리오 데이터
            
        Returns:
            Dict: 리스크 요약
        """
        evaluation = self.evaluate_market_regime(market_data, portfolio_data)
        
        return {
            'risk_level': self._calculate_risk_level(evaluation),
            'primary_risk_factor': self._identify_primary_risk(evaluation),
            'recommended_actions': self._get_recommended_actions(evaluation),
            'evaluation': evaluation
        }
    
    def _calculate_risk_level(self, evaluation: Dict) -> str:
        """
        평가 결과를 바탕으로 리스크 레벨 계산
        
        Args:
            evaluation: 시장 국면 평가 결과
            
        Returns:
            str: 리스크 레벨 ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        """
        regime = evaluation['final_regime']
        
        if regime in ['crisis_drawdown', 'crisis_correlation', 'crisis_vix']:
            return 'CRITICAL'
        elif regime in ['warning_drawdown', 'elevated_correlation', 'elevated_vix']:
            return 'HIGH'
        else:
            return 'MEDIUM' if regime != 'normal' else 'LOW'
    
    def _identify_primary_risk(self, evaluation: Dict) -> str:
        """
        주요 리스크 요인 식별
        
        Args:
            evaluation: 시장 국면 평가 결과
            
        Returns:
            str: 주요 리스크 요인
        """
        regime = evaluation['final_regime']
        
        if 'drawdown' in regime:
            return 'Portfolio Loss'
        elif 'correlation' in regime:
            return 'Diversification Failure'
        elif 'vix' in regime:
            return 'Market Volatility'
        else:
            return 'Normal Market Conditions'
    
    def _get_recommended_actions(self, evaluation: Dict) -> list:
        """
        평가 결과에 따른 추천 행동 반환
        
        Args:
            evaluation: 시장 국면 평가 결과
            
        Returns:
            list: 추천 행동 리스트
        """
        actions = []
        regime = evaluation['final_regime']
        forced_mode = evaluation.get('forced_mode')
        
        if forced_mode:
            actions.append(f"Force portfolio mode to '{forced_mode}'")
        
        if regime in ['crisis_drawdown', 'crisis_correlation', 'crisis_vix']:
            actions.extend([
                "Reduce position sizes significantly",
                "Consider defensive assets",
                "Increase cash allocation"
            ])
        elif regime in ['warning_drawdown', 'elevated_correlation', 'elevated_vix']:
            actions.extend([
                "Monitor positions closely",
                "Consider partial position reduction"
            ])
        
        if evaluation.get('position_limit_multiplier', 1.0) < 1.0:
            actions.append(f"Apply position limit multiplier of {evaluation['position_limit_multiplier']}")
        
        return actions