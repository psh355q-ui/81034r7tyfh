"""
Timezone Manager - PHASE4

Python `zoneinfo`를 사용한 자동 DST 관리

Features:
- 서머타임 규칙 (하절기/동절기)
- 한국 시차 자동 계산
- 스케줄 자동 전환
- DST 자동 감지

Usage:
    from backend.utils.timezone_manager import TimezoneManager
    
    tz_manager = TimezoneManager()
    schedule = tz_manager.get_schedule("market_open")
"""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class TimezoneManager:
    """
    Timezone Manager - 서머타임 자동 관리
    
    주요 기능:
    - 서머타임 규칙 (하절기/동절기)
    - 한국 시차 자동 계산
    - 스케줄 자동 전환
    - DST 자동 감지
    """
    
    # 시간대 설정
    TZ_EST = ZoneInfo("America/New_York")
    TZ_KST = ZoneInfo("Asia/Seoul")
    
    # 스케줄 정의
    SCHEDULES = {
        "daylight": {
            # 미국 시장 시간 (하절기: UTC-4)
            "market_open": "09:30",
            "market_close": "16:00",
            "economic_calendar_load": "00:05",
            "premarket_briefing": "22:30",
            "market_checkpoint_1": "01:00",
            "market_checkpoint_2": "03:00",
            "market_close_briefing": "06:10"
        },
        "standard": {
            # 미국 시장 시간 (동절기: UTC-5)
            "market_open": "09:30",
            "market_close": "16:00",
            "economic_calendar_load": "00:05",
            "premarket_briefing": "23:00",
            "market_checkpoint_1": "01:00",
            "market_checkpoint_2": "03:00",
            "market_close_briefing": "07:10"
        }
    }
    
    # 서머타임 규칙
    DST_START_MONTH = 3  # 3월
    DST_START_WEEKDAY = 2  # 2째 일요일 (0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일)
    DST_END_MONTH = 11  # 11월
    DST_END_WEEKDAY = 1  # 1째 일요일
    
    def __init__(self):
        """Timezone Manager 초기화"""
        self.current_regime = None  # 'daylight' or 'standard'
        self.timezone_offset_hours = None  # 한국 시차
        
        # 현재 시차 확인
        self._detect_current_regime()
        
        logger.info(f"TimezoneManager initialized: regime={self.current_regime}, "
                   f"offset={self.timezone_offset_hours}h")
    
    def _detect_current_regime(self):
        """
        현재 DST 규칙 감지
        
        Returns:
            'daylight' or 'standard'
        """
        now = datetime.now(self.TZ_EST)
        
        # DST 확인
        if now.dst() != timedelta(0):
            self.current_regime = 'daylight'
            self.timezone_offset_hours = 13  # 하절기: UTC-4, 한국 UTC+9 = 13시간
        else:
            self.current_regime = 'standard'
            self.timezone_offset_hours = 14  # 동절기: UTC-5, 한국 UTC+9 = 14시간
        
        logger.info(f"Detected DST regime: {self.current_regime} "
                   f"(offset={self.timezone_offset_hours}h)")
    
    def is_daylight_time(self) -> bool:
        """
        하절기 여부 확인
        
        Returns:
            True if daylight time, False otherwise
        """
        return self.current_regime == 'daylight'
    
    def get_timezone_offset_hours(self) -> int:
        """
        한국 시차 반환 (시간)
        
        Returns:
            시차 (시간)
        """
        return self.timezone_offset_hours
    
    def get_schedule(self, name: str) -> str:
        """
        현재 시간대에 맞는 스케줄 반환
        
        Args:
            name: 스케줄 이름 (예: "market_open")
            
        Returns:
            스케줄 시간 (HH:MM)
        """
        # 현재 규칙 확인
        if self.current_regime == 'daylight':
            schedule = self.SCHEDULES["daylight"].get(name)
        else:
            schedule = self.SCHEDULES["standard"].get(name)
        
        if not schedule:
            logger.warning(f"Schedule not found: {name}")
            return "00:00"
        
        logger.debug(f"Schedule[{name}]: {schedule} (regime={self.current_regime})")
        return schedule
    
    def get_market_open_time(self) -> str:
        """
        미국 시장 개장 시간 반환
        
        Returns:
            시장 개장 시간 (HH:MM KST)
        """
        return self.get_schedule("market_open")
    
    def get_market_close_time(self) -> str:
        """
        미국 시장 폐장 시간 반환
        
        Returns:
            시장 폐장 시간 (HH:MM KST)
        """
        return self.get_schedule("market_close")
    
    def get_pre_market_briefing_time(self) -> str:
        """
        프리마켓 브리핑 시간 반환
        
        Returns:
            프리마켓 브리핑 시간 (HH:MM KST)
        """
        return self.get_schedule("premarket_briefing")
    
    def get_market_close_briefing_time(self) -> str:
        """
        마켓 클로즈 브리핑 시간 반환
        
        Returns:
            마켓 클로즈 브리핑 시간 (HH:MM KST)
        """
        return self.get_schedule("market_close_briefing")
    
    def get_checkpoint_times(self) -> list:
        """
        체크포인트 시간 목록 반환
        
        Returns:
            체크포인트 시간 목록
        """
        return [
            self.get_schedule("market_checkpoint_1"),
            self.get_schedule("market_checkpoint_2")
        ]
    
    def get_economic_calendar_load_time(self) -> str:
        """
        경제 캘린더 로드 시간 반환
        
        Returns:
            경제 캘린더 로드 시간 (HH:MM KST)
        """
        return self.get_schedule("economic_calendar_load")
    
    def convert_est_to_kst(self, est_time: datetime) -> datetime:
        """
        EST 시간을 KST 시간으로 변환
        
        Args:
            est_time: EST 시간
            
        Returns:
            KST 시간
        """
        # EST 시간에 시차 더하기
        kst_time = est_time + timedelta(hours=self.timezone_offset_hours)
        
        logger.debug(f"EST {est_time} -> KST {kst_time} "
                   f"(offset={self.timezone_offset_hours}h)")
        return kst_time
    
    def convert_kst_to_est(self, kst_time: datetime) -> datetime:
        """
        KST 시간을 EST 시간으로 변환
        
        Args:
            kst_time: KST 시간
            
        Returns:
            EST 시간
        """
        # KST 시간에서 시차 빼기
        est_time = kst_time - timedelta(hours=self.timezone_offset_hours)
        
        logger.debug(f"KST {kst_time} -> EST {est_time} "
                   f"(offset={self.timezone_offset_hours}h)")
        return est_time
    
    def get_dst_transition_dates(self, year: int) -> tuple:
        """
        지정된 연도의 DST 전환 날짜 계산
        
        Args:
            year: 연도
            
        Returns:
            (dst_start_date, dst_end_date)
        """
        # DST 시작 날짜 (3월 2째 일요일)
        dst_start_date = self._find_nth_weekday(year, self.DST_START_MONTH, self.DST_START_WEEKDAY)
        
        # DST 종료 날짜 (11월 1째 일요일)
        dst_end_date = self._find_nth_weekday(year, self.DST_END_MONTH, self.DST_END_WEEKDAY)
        
        logger.info(f"DST transition dates for {year}: "
                   f"Start={dst_start_date}, End={dst_end_date}")
        
        return (dst_start_date, dst_end_date)
    
    def _find_nth_weekday(self, year: int, month: int, weekday: int) -> datetime:
        """
        지정된 연도/월의 N번째 요일 찾기
        
        Args:
            year: 연도
            month: 월
            weekday: 요일 (0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일)
            
        Returns:
            해당 날짜
        """
        # 해당 월의 1일 찾기
        date = datetime(year, month, 1)
        
        # 첫 번째 요일 찾기
        days_until_weekday = (weekday - date.weekday()) % 7
        if days_until_weekday < 0:
            days_until_weekday += 7
        
        target_date = date + timedelta(days=days_until_weekday)
        
        return target_date
    
    def update_regime(self):
        """
        현재 DST 규칙 업데이트 (수동 호출)
        """
        old_regime = self.current_regime
        self._detect_current_regime()
        
        if old_regime != self.current_regime:
            logger.info(f"DST regime changed: {old_regime} -> {self.current_regime}")
        else:
            logger.debug(f"DST regime unchanged: {self.current_regime}")


# ============================================
# Demo & Testing
# ============================================

def demo():
    """Timezone Manager 데모"""
    print("=" * 80)
    print("PHASE4: Timezone Manager Demo")
    print("=" * 80)
    
    tz_manager = TimezoneManager()
    
    # 현재 규칙 확인
    print(f"\nCurrent DST Regime: {tz_manager.current_regime}")
    print(f"Timezone Offset: {tz_manager.timezone_offset_hours} hours")
    print(f"Is Daylight Time: {tz_manager.is_daylight_time()}")
    
    # 스케줄 확인
    print(f"\nMarket Open: {tz_manager.get_market_open_time()}")
    print(f"Market Close: {tz_manager.get_market_close_time()}")
    print(f"Pre-market Briefing: {tz_manager.get_pre_market_briefing_time()}")
    print(f"Market Close Briefing: {tz_manager.get_market_close_briefing_time()}")
    print(f"Checkpoints: {tz_manager.get_checkpoint_times()}")
    print(f"Economic Calendar Load: {tz_manager.get_economic_calendar_load_time()}")
    
    # DST 전환 날짜 확인
    dst_start, dst_end = tz_manager.get_dst_transition_dates(2026)
    print(f"\nDST 2026:")
    print(f"  Start: {dst_start.strftime('%Y-%m-%d')}")
    print(f"  End: {dst_end.strftime('%Y-%m-%d')}")
    
    # 시간 변환 테스트
    est_time = datetime(2026, 3, 8, 30, 0, tzinfo=tz_manager.TZ_EST)
    kst_time = tz_manager.convert_est_to_kst(est_time)
    print(f"\nTime Conversion:")
    print(f"  EST: {est_time}")
    print(f"  KST: {kst_time}")
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    demo()
