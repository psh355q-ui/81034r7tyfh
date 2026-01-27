"""
Exit Rules Engine

자동 청산 규칙 시스템:
1. Dividend Mode: 배당 중단 → 즉시 청산
2. Long-Term Mode: Thesis Violation → 청산 검토
3. Trading Mode: 손절/익절 → 자동 청산
4. Aggressive Mode: Stop-Loss → 자동 청산
"""

import yfinance as yf
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DividendExitRule:
    """
    Dividend Mode Exit Rule
    
    배당 중단 감지 시 즉시 청산
    """
    
    def __init__(self, cut_threshold: float = 0.05):
        """
        초기화
        
        Args:
            cut_threshold: 배당 감소 임계값 (5% 이상 감소 시 cut으로 판단)
        """
        self.cut_threshold = cut_threshold
    
    def check_exit(self, position: Dict, dividend_history: Dict) -> Dict:
        """
        청산 여부 체크 (Manual dividend history input)
        
        Args:
            position: 포지션 정보
                - ticker: 종목 심볼
                - mode: 투자 모드 ('dividend', 'long_term', 'trading', 'aggressive')
                - entry_date: 진입 일자
            dividend_history: 배당 이력
                - previous: 이전 배당금
                - current: 현재 배당금
        
        Returns:
            Dict: 청산 판단 결과
                - exit_triggered: 청산 트리거 여부
                - reason: 사유
                - cut_percentage: 감소율 (감소 시)
                - growth_percentage: 증가율 (증가 시)
                - action: 조치 ('force_liquidate' or None)
                - priority: 우선순위 ('immediate', 'normal', None)
        """
        # Mode 체크
        if position.get('mode') != 'dividend':
            return {
                'exit_triggered': False,
                'reason': 'mode_not_applicable',
                'action': None,
                'priority': None
            }
        
        previous = dividend_history.get('previous', 0)
        current = dividend_history.get('current', 0)
        
        # 배당금 변화 계산
        if previous == 0:
            return {
                'exit_triggered': False,
                'reason': 'no_previous_dividend',
                'action': None
            }
        
        change_percentage = (current - previous) / previous
        
        # 배당 감소 (cut)
        if change_percentage < -self.cut_threshold:
            cut_percentage = abs(change_percentage) * 100
            
            logger.warning(
                f"Dividend CUT detected for {position['ticker']}: "
                f"{previous:.2f} → {current:.2f} ({cut_percentage:.1f}% cut)"
            )
            
            return {
                'exit_triggered': True,
                'reason': 'dividend_cut',
                'cut_percentage': cut_percentage,
                'action': 'force_liquidate',
                'priority': 'immediate',
                'details': {
                    'previous_dividend': previous,
                    'current_dividend': current,
                    'ticker': position['ticker']
                }
            }
        
        # 배당 증가
        elif change_percentage > 0:
            growth_percentage = change_percentage * 100
            
            return {
                'exit_triggered': False,
                'reason': 'dividend_increased',
                'growth_percentage': growth_percentage,
                'action': None,
                'details': {
                    'previous_dividend': previous,
                    'current_dividend': current
                }
            }
        
        # 배당 유지
        else:
            return {
                'exit_triggered': False,
                'reason': 'dividend_maintained',
                'action': None,
                'details': {
                    'dividend': current
                }
            }
    
    def check_exit_live(self, position: Dict) -> Dict:
        """
        실제 yfinance API를 사용한 배당 체크
        
        Args:
            position: 포지션 정보
        
        Returns:
            Dict: 청산 판단 결과
        """
        ticker = position['ticker']
        
        try:
            # yfinance로 배당 이력 가져오기
            stock = yf.Ticker(ticker)
            dividends = stock.dividends
            
            if dividends.empty or len(dividends) < 2:
                return {
                    'exit_triggered': False,
                    'reason': 'insufficient_dividend_history',
                    'action': None
                }
            
            # 최근 2개 배당 비교
            recent_dividends = dividends.tail(2)
            previous = recent_dividends.iloc[0]
            current = recent_dividends.iloc[1]
            
            dividend_history = {
                'previous': previous,
                'current': current
            }
            
            return self.check_exit(position, dividend_history)
            
        except Exception as e:
            logger.error(f"Error fetching dividend data for {ticker}: {str(e)}")
            return {
                'exit_triggered': False,
                'reason': 'api_error',
                'error': str(e),
                'action': None
            }


class LongTermExitRule:
    """
    Long-Term Mode Exit Rule
    
    투자 논리(Thesis) 위반 감지 시 청산 검토
    """
    
    def __init__(self):
        """초기화"""
        # TODO: Import ThesisKeeper when ready
        # from backend.services.thesis_keeper import ThesisKeeper
        # self.thesis_keeper = ThesisKeeper()
        pass
    
    def check_exit(self, position: Dict, current_analysis: Optional[str] = None) -> Dict:
        """
        Long-Term 청산 체크
        
        Args:
            position: 포지션 정보
                - ticker: 종목
                - entry_price: 진입가
                - current_price: 현재가
            current_analysis: 현재 분석 텍스트 (LLM 비교용)
        
        Returns:
            Dict: 청산 판단 결과
        """
        # Mode 체크
        if position.get('mode') != 'long_term':
            return {
                'exit_triggered': False,
                'reason': 'mode_not_applicable',
                'action': None
            }
        
        # TODO: Thesis Keeper 통합
        # thesis = self.thesis_keeper.get_thesis(position['ticker'])
        # if not thesis:
        #     return {'exit_triggered': False, 'reason': 'no_thesis'}
        
        # TODO: LLM-based Thesis Violation Detection
        # violation = self._check_thesis_violation_llm(thesis, current_analysis)
        # if violation['is_violated']:
        #     return {'exit_triggered': True, 'reason': 'thesis_violated'}
        
        # Placeholder: No exit for now
        return {
            'exit_triggered': False,
            'reason': 'thesis_intact',
            'action': None
        }
    
    def _check_thesis_violation_llm(self, thesis_text: str, current_analysis: str) -> Dict:
        """LLM을 사용한 Thesis Violation 감지 (Placeholder)"""
        return {'is_violated': False, 'reason': 'Not implemented'}


class TradingExitRule:
    """
    Trading Mode Exit Rule
    
    기술적 분석 기반 자동 청산:
    - Stop-Loss: -3%
    - Take-Profit: +7%
    - MACD Dead Cross
    """
    
    def __init__(self, stop_loss_pct: float = 0.03, take_profit_pct: float = 0.07):
        """
        초기화
        
        Args:
            stop_loss_pct: 손절 비율 (기본 3%)
            take_profit_pct: 익절 비율 (기본 7%)
        """
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
    
    def check_exit(self, position: Dict, price_data: Optional[Dict] = None) -> Dict:
        """
        Trading 청산 체크
        
        Args:
            position: 포지션 정보
                - ticker: 종목
                - entry_price: 진입가
                - current_price: 현재가
                - mode: 'trading'
            price_data: 가격 데이터 (MACD 계산용, optional)
        
        Returns:
            Dict: 청산 판단 결과
        """
        # Mode 체크
        if position.get('mode') != 'trading':
            return {
                'exit_triggered': False,
                'reason': 'mode_not_applicable',
                'action': None
            }
        
        entry_price = position.get('entry_price')
        current_price = position.get('current_price')
        
        if not entry_price or not current_price:
            return {
                'exit_triggered': False,
                'reason': 'insufficient_price_data',
                'action': None
            }
        
        # Calculate P&L percentage
        pnl_pct = (current_price - entry_price) / entry_price
        
        # Stop-Loss Check
        if pnl_pct <= -self.stop_loss_pct:
            logger.warning(
                f"Stop-Loss triggered for {position['ticker']}: "
                f"{pnl_pct*100:.1f}% loss"
            )
            return {
                'exit_triggered': True,
                'reason': 'stop_loss',
                'action': 'force_liquidate',
                'priority': 'immediate',
                'details': {
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'pnl_pct': pnl_pct * 100,
                    'threshold': -self.stop_loss_pct * 100
                }
            }
        
        # Take-Profit Check
        if pnl_pct >= self.take_profit_pct:
            logger.info(
                f"Take-Profit triggered for {position['ticker']}: "
                f"{pnl_pct*100:.1f}% profit"
            )
            return {
                'exit_triggered': True,
                'reason': 'take_profit',
                'action': 'liquidate',
                'priority': 'normal',
                'details': {
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'pnl_pct': pnl_pct * 100,
                    'threshold': self.take_profit_pct * 100
                }
            }
        
        # MACD Dead Cross Check (if price_data provided)
        if price_data and 'macd' in price_data:
            macd_signal = self._check_macd_dead_cross(price_data['macd'])
            if macd_signal['dead_cross']:
                return {
                    'exit_triggered': True,
                    'reason': 'macd_dead_cross',
                    'action': 'liquidate',
                    'priority': 'normal',
                    'details': macd_signal
                }
        
        # No exit
        return {
            'exit_triggered': False,
            'reason': 'within_range',
            'action': None,
            'details': {
                'pnl_pct': pnl_pct * 100,
                'stop_loss_threshold': -self.stop_loss_pct * 100,
                'take_profit_threshold': self.take_profit_pct * 100
            }
        }
    
    def _check_macd_dead_cross(self, macd_data: Dict) -> Dict:
        """MACD Dead Cross 감지"""
        macd = macd_data.get('macd')
        signal = macd_data.get('signal')
        prev_macd = macd_data.get('previous_macd')
        prev_signal = macd_data.get('previous_signal')
        
        if prev_macd and prev_signal:
            was_above = prev_macd > prev_signal
            now_below = macd < signal
            if was_above and now_below:
                return {'dead_cross': True, 'macd': macd, 'signal': signal, 'message': 'MACD 데드크로스 발생'}
        
        return {'dead_cross': False, 'macd': macd, 'signal': signal}


class ExitRuleEngine:
    """Exit Rule 통합 엔진"""
    
    def __init__(self):
        self.dividend_rule = DividendExitRule()
        self.longterm_rule = LongTermExitRule()
        self.trading_rule = TradingExitRule()
    
    def check_all_exits(self, position: Dict) -> Dict:
        """모든 Exit Rules 체크"""
        mode = position.get('mode')
        
        if mode == 'dividend':
            return self.dividend_rule.check_exit_live(position)
        elif mode == 'long_term':
            return self.longterm_rule.check_exit(position)
        elif mode == 'trading':
            return self.trading_rule.check_exit(position)
        else:
            return {
                'exit_triggered': False,
                'reason': 'no_applicable_rule',
                'action': None
            }
