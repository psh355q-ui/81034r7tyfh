"""
Position Aging Tracker

포지션 보유 기간 리스크 관리 시스템
Strategy Mode별 다른 임계값 적용:
- Trading: 5일(Warn) / 7일(Critical) - 단기 자금 회전 중시
- Long-Term: 90일(Warn) / 180일(Critical) - Thesis 중간 점검
- Dividend: 180일(Warn) / 365일(Critical) - 장기 보유 권장이나 점검 필요
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class PositionAgingTracker:
    """
    Position Aging Tracker
    
    포지션 보유 기간을 모니터링하고 리스크 수준을 평가
    """
    
    def __init__(self):
        """초기화 및 임계값 설정"""
        self.thresholds = {
            'trading': {
                'warning': 5,
                'critical': 7,
                'action_critical': 'recommend_exit',
                'action_warning': 'stale_warning'
            },
            'long_term': {
                'warning': 90,
                'critical': 180,
                'action_critical': 'forced_thesis_review',
                'action_warning': 'thesis_review'
            },
            'dividend': {
                'warning': 180,
                'critical': 365,
                'action_critical': 'deep_dive_analysis',
                'action_warning': 'business_check'
            },
            'aggressive': {
                'warning': 1,
                'critical': 3,
                'action_critical': 'force_exit',
                'action_warning': 'monitor_closely'
            }
        }
        
    def check_aging(self, position: Dict) -> Dict:
        """
        포지션 Aging 체크
        
        Args:
            position: 포지션 정보 (must include 'entry_date' in 'YYYY-MM-DD' or datetime object)
            
        Returns:
            Dict: Aging 상태 및 조치 권고
        """
        ticker = position.get('ticker')
        mode = position.get('mode', 'long_term')  # Default to long_term
        entry_date_raw = position.get('entry_date')
        
        if not entry_date_raw:
            return {
                'stale': False,
                'level': 'error',
                'error': 'no_entry_date',
                'message': '진입일 정보 없음'
            }
            
        # Parse entry_date
        try:
            if isinstance(entry_date_raw, str):
                entry_date = datetime.strptime(entry_date_raw, "%Y-%m-%d")
            elif isinstance(entry_date_raw, datetime):
                entry_date = entry_date_raw
            else:
                raise ValueError("Invalid date format")
        except Exception as e:
            logger.error(f"Date parsing error for {ticker}: {e}")
            return {
                'stale': False,
                'level': 'error',
                'error': 'date_parse_error',
                'message': f'날짜 형식 오류: {entry_date_raw}'
            }
            
        # days_held 계산 (시간 정보 제거하여 날짜 차이만 계산)
        entry_date_date = entry_date.date() if isinstance(entry_date, datetime) else entry_date
        current_date_date = datetime.now().date()
        days_held = (current_date_date - entry_date_date).days
        
        # Mode별 임계값 적용
        threshold = self.thresholds.get(mode, self.thresholds['long_term'])
        
        # Check Critical Threshold
        if days_held > threshold['critical']:
            return {
                'stale': True,
                'level': 'critical',
                'days_held': days_held,
                'action': threshold['action_critical'],
                'message': f"보유 기간 {days_held}일 - Critical 임계값({threshold['critical']}일) 초과"
            }
            
        # Check Warning Threshold
        elif days_held > threshold['warning']:
            return {
                'stale': True,
                'level': 'warning',
                'days_held': days_held,
                'action': threshold['action_warning'],
                'message': f"보유 기간 {days_held}일 - Warning 임계값({threshold['warning']}일) 초과"
            }
            
        # Normal State
        else:
            return {
                'stale': False,
                'level': 'normal',
                'days_held': days_held,
                'action': None,
                'message': f"보유 기간 {days_held}일 (정상)"
            }
