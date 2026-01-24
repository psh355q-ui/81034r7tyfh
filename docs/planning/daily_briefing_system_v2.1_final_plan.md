# Daily Briefing System v2.1 - 최종 통합 개발 계획서

**작성일**: 2026-01-22  
**버전**: v2.1 Final  
**검토**: Claude Code + ChatGPT + Gemini + Claude Opus 통합 검토  
**시스템**: Antigravity AI Trading System  

---

## 📋 목차

1. [시스템 개요](#1-시스템-개요)
2. [24시간 운영 타임라인](#2-24시간-운영-타임라인)
3. [서머타임 적용 스케줄러](#3-서머타임-적용-스케줄러)
4. [핵심 아키텍처](#4-핵심-아키텍처)
5. [구현 Phase 순서](#5-구현-phase-순서)
6. [Phase별 상세 작업](#6-phase별-상세-작업)
7. [브리핑 프롬프트 전문](#7-브리핑-프롬프트-전문)
8. [텔레그램 알림 시스템](#8-텔레그램-알림-시스템)
9. [KIS API 포트폴리오 연동](#9-kis-api-포트폴리오-연동)
10. [주간 리포트 시스템](#10-주간-리포트-시스템)
11. [검증 체크리스트](#11-검증-체크리스트)
12. [완료 기준](#12-완료-기준)

---

## 1. 시스템 개요

### 1.1 목표

| 목표 | 설명 |
|------|------|
| **비용 절감** | 캐싱 전략으로 LLM API 호출 70% 절감 |
| **24시간 운영** | RSS 크롤링 + Ollama 전처리 상시 가동 |
| **5단계 브리핑** | 프리마켓 → 장중 체크 → 마감 → 국내 → 주간 |
| **실시간 알림** | 텔레그램 봇으로 속보/브리핑 푸시 |
| **포트폴리오 연동** | KIS API 기반 보유종목 맞춤 분석 |
| **자동 개선** | 주간 시스템 분석으로 지속적 개선 |

### 1.2 브리핑 체계 (5단계)

```
┌─────────────────────────────────────────────────────────────┐
│                    📅 일간 브리핑 (평일)                      │
├─────────────────────────────────────────────────────────────┤
│  23:00  🌙 프리마켓 브리핑      - 미국장 시작 전 뉴스 정리    │
│  01:00  📍 장중 체크포인트 #1   - 장 시작 30분 후 점검       │
│  03:00  📍 장중 체크포인트 #2   - 장 중간 점검              │
│  07:10  🇺🇸 미국장 마감 브리핑   - 장 마감 분석              │
│  08:00  🇰🇷 국내장 오픈 브리핑   - 한국 시장 연결            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    📅 주간 브리핑 (주말)                      │
├─────────────────────────────────────────────────────────────┤
│  토 07:10  🇺🇸 금요일 마감 브리핑  - 주간 마지막 장 분석      │
│  토 14:00  📊 주간 리뷰          - 한 주 성과 분석           │
│  일 22:00  🔮 주간 전망 리포트    - 다음 주 전망 + 시스템 분석 │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 핵심 설계 원칙

| 원칙 | 설명 |
|------|------|
| **역할 분리** | Ollama = 전처리, Gemini/Claude = 브리핑 + 심층 검토 |
| **API 심층 검토** | 전문가 코멘트, 경제 캘린더를 API 웹 검색으로 수집 |
| **서머타임 자동화** | 미국 DST 자동 감지 및 스케줄 조정 |
| **포트폴리오 기반** | KIS API 연동으로 보유종목 맞춤 분석 |
| **자동 개선 루프** | 주간 시스템 분석 → 개선점 도출 → 반영 |

---

## 2. 24시간 운영 타임라인

### 2.1 평일 타임라인 (한국 시간 기준)

```
═══════════════════════════════════════════════════════════════
                    📅 평일 24시간 운영
═══════════════════════════════════════════════════════════════

     [상시 가동]
     ┌─────────────────────────────────────────────────────┐
     │  🔄 RSS 크롤링: 10분 간격                            │
     │  🤖 Ollama 전처리: 5분 간격                          │
     │  📡 텔레그램 속보 알림: 실시간                        │
     └─────────────────────────────────────────────────────┘

06:00 ═══════════ 🔔 미국장 마감 (동절기) ═══════════
      │
07:10 ├─── 🇺🇸 미국장 마감 브리핑 생성
      │         └─ 📲 텔레그램 전송
      │
08:00 ├─── 🇰🇷 국내장 오픈 브리핑 생성
      │         └─ 📲 텔레그램 전송
      │
09:00 ═══════════ 🔔 국내장 시작 ═══════════
      │
      │    [국내장 진행 중]
      │
15:30 ═══════════ 🔔 국내장 마감 ═══════════
      │
      │    [휴식 시간 - 저녁]
      │
22:00 ├─── 🔄 Ollama 전처리 강화 (장전 뉴스 집중)
      │
23:00 ├─── 🌙 프리마켓 브리핑 생성
      │         └─ 📲 텔레그램 전송
      │
00:30 ═══════════ 🔔 미국장 시작 (동절기) ═══════════
      │
01:00 ├─── 📍 장중 체크포인트 #1
      │         └─ 📲 텔레그램 전송 (주요 변동 시)
      │
03:00 ├─── 📍 장중 체크포인트 #2
      │         └─ 📲 텔레그램 전송 (주요 변동 시)
      │
06:00 ═══════════ 🔔 미국장 마감 (동절기) ═══════════
                       (반복)
```

### 2.2 주말 타임라인

```
═══════════════════════════════════════════════════════════════
                    📅 주말 운영
═══════════════════════════════════════════════════════════════

[토요일]
06:00 ═══════════ 🔔 금요일 미국장 마감 ═══════════
      │
07:10 ├─── 🇺🇸 금요일 마감 브리핑 생성 (주간 마지막)
      │         └─ 📲 텔레그램 전송
      │
08:00 ├─── 🇰🇷 토요일 국내 브리핑 (선택적)
      │
14:00 ├─── 📊 주간 리뷰 리포트 생성
      │         ├─ 한 주 시장 요약
      │         ├─ 섹터별 성과 분석
      │         ├─ 포트폴리오 성과 분석 (KIS API)
      │         └─ 📲 텔레그램 전송

[일요일]
      │    [휴식 - 뉴스 모니터링만]
      │
22:00 ├─── 🔮 주간 전망 리포트 생성
      │         ├─ 다음 주 주요 일정
      │         ├─ 다음 주 전망 및 전략
      │         ├─ 이번 주 전체 리뷰
      │         ├─ 🤖 AI 시스템 분석
      │         │    ├─ 잘한 점
      │         │    ├─ 잘못한 점
      │         │    ├─ 개선 필요 사항
      │         │    └─ 시스템 수정 제안
      │         └─ 📲 텔레그램 전송
      │
23:00 ├─── 🌙 월요일 프리마켓 브리핑 (다음 주 시작)
```

---

## 3. 서머타임 적용 스케줄러

### 3.1 미국 서머타임 규칙

```python
"""
미국 서머타임 (Daylight Saving Time)
- 시작: 3월 두 번째 일요일 02:00 → 03:00 (1시간 앞으로)
- 종료: 11월 첫 번째 일요일 02:00 → 01:00 (1시간 뒤로)

한국-미국 시차:
- 서머타임 적용 시 (3월~11월): 한국이 13시간 앞섬
- 서머타임 미적용 시 (11월~3월): 한국이 14시간 앞섬
"""

US_MARKET_HOURS = {
    "standard": {  # 동절기 (11월~3월)
        "market_open": "00:30",   # KST (EST 09:30)
        "market_close": "06:00",  # KST (EST 16:00)
        "premarket_start": "18:00",  # KST (EST 04:00)
        "afterhours_end": "10:00",   # KST (EST 20:00)
    },
    "daylight": {  # 서머타임 (3월~11월)
        "market_open": "23:30",   # KST (EDT 09:30) - 전날
        "market_close": "05:00",  # KST (EDT 16:00)
        "premarket_start": "17:00",  # KST (EDT 04:00)
        "afterhours_end": "09:00",   # KST (EDT 20:00)
    }
}
```

### 3.2 서머타임 자동 감지 모듈

**파일**: `backend/utils/timezone_manager.py`

```python
"""
Timezone Manager for US Market Hours

미국 서머타임 자동 감지 및 스케줄 조정
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Literal
import logging

logger = logging.getLogger(__name__)


class USMarketTimezoneManager:
    """미국 시장 시간대 관리자"""
    
    # 시간대 정의
    TZ_KST = ZoneInfo("Asia/Seoul")
    TZ_EST = ZoneInfo("America/New_York")
    
    # 스케줄 정의 (KST 기준)
    SCHEDULES = {
        "standard": {  # 동절기 (EST)
            "premarket_briefing": "23:00",
            "checkpoint_1": "01:00",
            "checkpoint_2": "03:00",
            "us_close_briefing": "07:10",
            "kr_open_briefing": "08:00",
            "market_open": "00:30",
            "market_close": "06:00",
        },
        "daylight": {  # 서머타임 (EDT)
            "premarket_briefing": "22:00",  # 1시간 앞당김
            "checkpoint_1": "00:00",
            "checkpoint_2": "02:00",
            "us_close_briefing": "06:10",
            "kr_open_briefing": "08:00",  # 국내장은 변동 없음
            "market_open": "23:30",  # 전날
            "market_close": "05:00",
        }
    }
    
    # 주간 리포트 스케줄 (서머타임 무관)
    WEEKLY_SCHEDULES = {
        "saturday_review": "14:00",      # 토요일 주간 리뷰
        "sunday_outlook": "22:00",       # 일요일 주간 전망
    }
    
    def __init__(self):
        self._cached_dst_status = None
        self._cache_date = None
    
    def is_daylight_saving(self, check_date: datetime = None) -> bool:
        """
        현재 미국이 서머타임인지 확인
        
        Returns:
            True if DST is active, False otherwise
        """
        if check_date is None:
            check_date = datetime.now(self.TZ_EST)
        elif check_date.tzinfo is None:
            check_date = check_date.replace(tzinfo=self.TZ_EST)
        
        # 캐시 확인 (같은 날이면 재계산 불필요)
        today = check_date.date()
        if self._cache_date == today and self._cached_dst_status is not None:
            return self._cached_dst_status
        
        # DST 확인: EST와 EDT의 UTC offset 차이로 판단
        # EST = UTC-5, EDT = UTC-4
        utc_offset = check_date.utcoffset()
        is_dst = utc_offset == timedelta(hours=-4)
        
        # 캐시 저장
        self._cached_dst_status = is_dst
        self._cache_date = today
        
        logger.info(f"🕐 DST Status: {'Daylight Saving (EDT)' if is_dst else 'Standard (EST)'}")
        return is_dst
    
    def get_schedule(self, schedule_name: str) -> str:
        """
        현재 시간대에 맞는 스케줄 반환
        
        Args:
            schedule_name: 스케줄 이름 (예: 'premarket_briefing')
            
        Returns:
            KST 기준 시간 문자열 (예: '23:00')
        """
        # 주간 스케줄은 서머타임 무관
        if schedule_name in self.WEEKLY_SCHEDULES:
            return self.WEEKLY_SCHEDULES[schedule_name]
        
        # 일간 스케줄은 서머타임 적용
        period = "daylight" if self.is_daylight_saving() else "standard"
        return self.SCHEDULES[period].get(schedule_name)
    
    def get_all_schedules(self) -> Dict[str, str]:
        """현재 시간대 기준 모든 스케줄 반환"""
        period = "daylight" if self.is_daylight_saving() else "standard"
        schedules = self.SCHEDULES[period].copy()
        schedules.update(self.WEEKLY_SCHEDULES)
        return schedules
    
    def get_next_dst_change(self) -> Dict:
        """다음 서머타임 변경 일자 반환"""
        now = datetime.now(self.TZ_EST)
        year = now.year
        
        # 3월 두 번째 일요일 (서머타임 시작)
        march_first = datetime(year, 3, 1, tzinfo=self.TZ_EST)
        days_until_sunday = (6 - march_first.weekday()) % 7
        dst_start = march_first + timedelta(days=days_until_sunday + 7)
        
        # 11월 첫 번째 일요일 (서머타임 종료)
        nov_first = datetime(year, 11, 1, tzinfo=self.TZ_EST)
        days_until_sunday = (6 - nov_first.weekday()) % 7
        dst_end = nov_first + timedelta(days=days_until_sunday)
        
        # 다음 변경 일자 결정
        if now < dst_start:
            return {"date": dst_start, "type": "DST_START", "description": "서머타임 시작"}
        elif now < dst_end:
            return {"date": dst_end, "type": "DST_END", "description": "서머타임 종료"}
        else:
            # 내년 서머타임 시작
            next_year_march = datetime(year + 1, 3, 1, tzinfo=self.TZ_EST)
            days_until_sunday = (6 - next_year_march.weekday()) % 7
            next_dst_start = next_year_march + timedelta(days=days_until_sunday + 7)
            return {"date": next_dst_start, "type": "DST_START", "description": "서머타임 시작"}


# 싱글톤 인스턴스
_timezone_manager = None

def get_timezone_manager() -> USMarketTimezoneManager:
    global _timezone_manager
    if _timezone_manager is None:
        _timezone_manager = USMarketTimezoneManager()
    return _timezone_manager
```

### 3.3 동적 스케줄러

**파일**: `backend/automation/dynamic_scheduler.py`

```python
"""
Dynamic Scheduler with DST Support

서머타임 자동 적용 스케줄러
"""

import asyncio
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from backend.utils.timezone_manager import get_timezone_manager

logger = logging.getLogger(__name__)


class DynamicBriefingScheduler:
    """서머타임 자동 적용 브리핑 스케줄러"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
        self.tz_manager = get_timezone_manager()
        self._jobs = {}
    
    def setup_schedules(self):
        """모든 스케줄 설정"""
        schedules = self.tz_manager.get_all_schedules()
        is_dst = self.tz_manager.is_daylight_saving()
        
        logger.info(f"📅 Setting up schedules (DST: {is_dst})")
        
        # 일간 브리핑 스케줄
        self._add_job(
            "premarket_briefing",
            self._generate_premarket_briefing,
            schedules["premarket_briefing"],
            "mon-fri"
        )
        
        self._add_job(
            "checkpoint_1",
            self._generate_checkpoint,
            schedules["checkpoint_1"],
            "tue-sat",  # 미국 월~금 장중 = 한국 화~토
            kwargs={"checkpoint_num": 1}
        )
        
        self._add_job(
            "checkpoint_2",
            self._generate_checkpoint,
            schedules["checkpoint_2"],
            "tue-sat",
            kwargs={"checkpoint_num": 2}
        )
        
        self._add_job(
            "us_close_briefing",
            self._generate_us_briefing,
            schedules["us_close_briefing"],
            "tue-sat"
        )
        
        self._add_job(
            "kr_open_briefing",
            self._generate_kr_briefing,
            schedules["kr_open_briefing"],
            "mon-fri"
        )
        
        # 주간 리포트 스케줄
        self._add_job(
            "weekly_review",
            self._generate_weekly_review,
            schedules["saturday_review"],
            "sat"
        )
        
        self._add_job(
            "weekly_outlook",
            self._generate_weekly_outlook,
            schedules["sunday_outlook"],
            "sun"
        )
        
        # 서머타임 변경 체크 (매일 자정)
        self._add_job(
            "dst_check",
            self._check_dst_change,
            "00:00",
            "mon-sun"
        )
        
        logger.info(f"✅ Scheduled {len(self._jobs)} jobs")
    
    def _add_job(self, name: str, func, time_str: str, days: str, kwargs=None):
        """작업 추가"""
        hour, minute = map(int, time_str.split(":"))
        
        trigger = CronTrigger(
            day_of_week=days,
            hour=hour,
            minute=minute,
            timezone="Asia/Seoul"
        )
        
        job = self.scheduler.add_job(
            func,
            trigger,
            id=name,
            kwargs=kwargs or {},
            replace_existing=True
        )
        
        self._jobs[name] = job
        logger.info(f"  📌 {name}: {time_str} ({days})")
    
    async def _check_dst_change(self):
        """서머타임 변경 확인 및 스케줄 재설정"""
        next_change = self.tz_manager.get_next_dst_change()
        today = datetime.now().date()
        
        if next_change["date"].date() == today:
            logger.warning(f"🕐 DST Change Today: {next_change['description']}")
            # 캐시 무효화
            self.tz_manager._cached_dst_status = None
            # 스케줄 재설정
            self.setup_schedules()
    
    async def _generate_premarket_briefing(self):
        """프리마켓 브리핑 생성"""
        from backend.ai.reporters.enhanced_daily_reporter import EnhancedDailyReporter
        reporter = EnhancedDailyReporter()
        await reporter.generate_premarket_briefing()
    
    async def _generate_checkpoint(self, checkpoint_num: int):
        """장중 체크포인트 생성"""
        from backend.ai.reporters.enhanced_daily_reporter import EnhancedDailyReporter
        reporter = EnhancedDailyReporter()
        await reporter.generate_checkpoint(checkpoint_num)
    
    async def _generate_us_briefing(self):
        """미국장 마감 브리핑 생성"""
        from backend.ai.reporters.enhanced_daily_reporter import EnhancedDailyReporter
        reporter = EnhancedDailyReporter()
        await reporter.generate_us_briefing()
    
    async def _generate_kr_briefing(self):
        """국내장 오픈 브리핑 생성"""
        from backend.ai.reporters.korean_market_briefing_reporter import KoreanMarketBriefingReporter
        reporter = KoreanMarketBriefingReporter()
        await reporter.generate_kr_briefing()
    
    async def _generate_weekly_review(self):
        """주간 리뷰 생성"""
        from backend.ai.reporters.weekly_reporter import WeeklyReporter
        reporter = WeeklyReporter()
        await reporter.generate_weekly_review()
    
    async def _generate_weekly_outlook(self):
        """주간 전망 + 시스템 분석 생성"""
        from backend.ai.reporters.weekly_reporter import WeeklyReporter
        reporter = WeeklyReporter()
        await reporter.generate_weekly_outlook_with_system_analysis()
    
    def start(self):
        """스케줄러 시작"""
        self.setup_schedules()
        self.scheduler.start()
        logger.info("🚀 Dynamic Scheduler Started")
    
    def stop(self):
        """스케줄러 중지"""
        self.scheduler.shutdown()
        logger.info("🛑 Dynamic Scheduler Stopped")
```

### 3.4 스케줄 요약 테이블

| 브리핑 | 동절기 (EST) | 서머타임 (EDT) | 요일 |
|--------|-------------|---------------|------|
| 🌙 프리마켓 | 23:00 | 22:00 | 월~금 |
| 📍 체크포인트 #1 | 01:00 | 00:00 | 화~토 |
| 📍 체크포인트 #2 | 03:00 | 02:00 | 화~토 |
| 🇺🇸 미국 마감 | 07:10 | 06:10 | 화~토 |
| 🇰🇷 국내 오픈 | 08:00 | 08:00 | 월~금 |
| 📊 주간 리뷰 | 14:00 | 14:00 | 토 |
| 🔮 주간 전망 | 22:00 | 22:00 | 일 |

---

## 4. 핵심 아키텍처

### 4.1 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI Trading System                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐           │
│   │ RSS Crawler  │────▶│   Ollama     │────▶│  PostgreSQL  │           │
│   │ (10분 간격)   │     │ 전처리(5분)  │     │     DB       │           │
│   └──────────────┘     └──────────────┘     └──────┬───────┘           │
│                                                      │                   │
│   ┌──────────────────────────────────────────────────┼──────────────┐   │
│   │                    Briefing Engine               │              │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌────────────▼───────────┐  │   │
│   │  │ 프리마켓    │  │ 장중 체크   │  │   Gemini/Claude API    │  │   │
│   │  │ 브리핑      │  │ 포인트      │  │   (웹 검색 + 심층검토)   │  │   │
│   │  └─────────────┘  └─────────────┘  └────────────────────────┘  │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────┐  │   │
│   │  │ 미국 마감   │  │ 국내 오픈   │  │     주간 리포트        │  │   │
│   │  │ 브리핑      │  │ 브리핑      │  │  (리뷰 + 전망 + 분석)   │  │   │
│   │  └─────────────┘  └─────────────┘  └────────────────────────┘  │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│   ┌────────────────────────────────┼────────────────────────────────┐   │
│   │              Integration Layer │                                │   │
│   │  ┌─────────────┐  ┌───────────▼─┐  ┌─────────────────────────┐ │   │
│   │  │  KIS API    │  │  Telegram   │  │   Cache Manager         │ │   │
│   │  │ 포트폴리오  │  │    Bot      │  │   (중요도 기반 캐싱)     │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 캐싱 전략 (5단계)

| 점수 범위 | 액션 | 설명 |
|-----------|------|------|
| **0-10점** | CACHE_HIT | 변경 없음, 이전 브리핑 재사용 |
| **10-25점** | UPDATE_METRICS | 지수/가격 숫자만 갱신 |
| **25-60점** | PARTIAL_REGEN | 변경된 섹션만 재생성 |
| **60-80점** | FULL_REGEN | 전체 브리핑 재생성 |
| **80점 이상** | URGENT_REGEN | 즉시 재생성 + 알림 |

---

## 5. 구현 Phase 순서

```
═══════════════════════════════════════════════════════════════
                    구현 Phase 순서 (총 10단계)
═══════════════════════════════════════════════════════════════

Phase 1: DB 마이그레이션 (선행 필수)
  └─> models.py 수정 → 마이그레이션 → DB 적용

Phase 2: Ollama 전처리 시스템
  └─> ollama_rss_preprocessor.py 생성

Phase 3: 캐싱 시스템
  └─> daily_briefing_cache_manager.py 생성

Phase 4: 서머타임 스케줄러
  └─> timezone_manager.py 생성
  └─> dynamic_scheduler.py 생성

Phase 5: 미국장 브리핑 (마감 + 프리마켓 + 체크포인트)
  └─> enhanced_daily_reporter.py 수정
  └─> 심층 검토 프롬프트 적용

Phase 6: 국내장 브리핑
  └─> korean_market_briefing_reporter.py 생성

Phase 7: KIS API 포트폴리오 연동
  └─> portfolio_analyzer.py 생성
  └─> 보유종목 기반 맞춤 분석

Phase 8: 텔레그램 알림 시스템
  └─> telegram_bot.py 생성
  └─> 속보 알림 + 브리핑 전송

Phase 9: 주간 리포트 시스템
  └─> weekly_reporter.py 생성
  └─> 주간 리뷰 + 전망 + 시스템 분석

Phase 10: API & 통합 테스트
  └─> reports_router.py 수정
  └─> 전체 시스템 통합 테스트
```

---

## 6. Phase별 상세 작업

### Phase 1: DB 마이그레이션

**(v2.0 계획서와 동일 - 생략)**

### Phase 2: Ollama 전처리

**(v2.0 계획서와 동일 - 생략)**

### Phase 3: 캐싱 시스템

**(v2.0 계획서와 동일 - 생략)**

### Phase 4: 서머타임 스케줄러

**파일 목록**:
- `backend/utils/timezone_manager.py` (위 3.2 섹션 참조)
- `backend/automation/dynamic_scheduler.py` (위 3.3 섹션 참조)

### Phase 5: 미국장 브리핑

**파일**: `backend/ai/reporters/enhanced_daily_reporter.py`

장중 체크포인트 기능 추가:

```python
class EnhancedDailyReporter:
    
    async def generate_checkpoint(self, checkpoint_num: int) -> str:
        """
        장중 체크포인트 생성
        
        Args:
            checkpoint_num: 1 (장 시작 30분 후) 또는 2 (장 중간)
        """
        # 현재 시장 상태 조회
        market_data = await self._fetch_realtime_market_data()
        
        # 급변 감지
        significant_changes = self._detect_significant_changes(market_data)
        
        if not significant_changes:
            logger.info(f"📍 Checkpoint #{checkpoint_num}: No significant changes")
            return None  # 알림 불필요
        
        # 체크포인트 브리핑 생성
        prompt = CHECKPOINT_PROMPT.format(
            checkpoint_num=checkpoint_num,
            market_data=market_data,
            changes=significant_changes
        )
        
        briefing = await self.llm_client.generate_with_search(prompt)
        
        # 텔레그램 전송
        await self.telegram_bot.send_checkpoint(briefing)
        
        return briefing
    
    def _detect_significant_changes(self, market_data: Dict) -> List[Dict]:
        """
        유의미한 변동 감지
        
        기준:
        - 지수 ±1% 이상 변동
        - VIX ±10% 이상 변동
        - 주요 종목 ±3% 이상 변동
        """
        changes = []
        
        # S&P 500
        if abs(market_data.get('sp500_change_pct', 0)) >= 1.0:
            changes.append({
                'type': 'INDEX',
                'name': 'S&P 500',
                'change': market_data['sp500_change_pct']
            })
        
        # VIX
        if abs(market_data.get('vix_change_pct', 0)) >= 10.0:
            changes.append({
                'type': 'VOLATILITY',
                'name': 'VIX',
                'change': market_data['vix_change_pct']
            })
        
        # 주요 종목
        for ticker, change in market_data.get('major_stocks', {}).items():
            if abs(change) >= 3.0:
                changes.append({
                    'type': 'STOCK',
                    'name': ticker,
                    'change': change
                })
        
        return changes
```

---

## 7. 브리핑 프롬프트 전문

### 7.1 프리마켓 브리핑 (23:00)

```python
PREMARKET_BRIEFING_PROMPT = """
당신은 월가 트레이더를 위한 프리마켓 애널리스트입니다.
미국장 시작 전, 오늘 밤 주목해야 할 내용을 빠르게 정리하세요.

═══════════════════════════════════════════════════════════════
[입력: Ollama 전처리 RSS (최근 6시간)]
{preprocessed_rss_data}

[입력: 보유 포트폴리오 (KIS API)]
{portfolio_data}
═══════════════════════════════════════════════════════════════

### 🔍 심층 검토 지침 (API 웹 검색)

1. **속보 및 핫이슈**
   - 검색: "breaking news stocks", "market moving news"
   - 장 시작 전 가장 중요한 뉴스 3개 선정

2. **프리마켓 동향**
   - 검색: "premarket movers", "futures now"
   - S&P/나스닥 선물, 주요 종목 프리마켓

3. **오늘 밤 일정**
   - 실적 발표 (After Hours, Before Open)
   - 경제 지표 발표

4. **포트폴리오 관련 뉴스** (있는 경우)
   - 보유 종목 관련 뉴스 체크
   - 영향 분석

═══════════════════════════════════════════════════════════════

### 📋 출력 형식

## 🌙 Pre-Market Briefing ({current_date})
> [오늘 밤 시장 핵심 한 문장]

## 🔴 Tonight's Hot Issues (Top 3)

### 1. [이슈명]
- **내용**: 1-2문장
- **영향 종목**: OOO (프리마켓 +X%)
- **대응**: 장 시작 시 주목할 포인트

### 2. [이슈명]
(동일 형식)

### 3. [이슈명]
(동일 형식)

## 📊 Pre-Market Snapshot
| 항목 | 현재 | 변동 |
|------|------|------|
| S&P 500 선물 | | |
| 나스닥 선물 | | |
| VIX | | |
| WTI 원유 | | |
| 비트코인 | | |

## 🏭 Sector Watch
| 섹터 | 핵심 뉴스 | 주목 종목 |
|------|-----------|-----------|
| 반도체 | | |
| AI/빅테크 | | |
| 에너지 | | |

## 💼 Portfolio Alert (보유종목 관련)
{portfolio_alerts}

## 📅 Tonight's Calendar
- [시간] [이벤트]
- [시간] 실적발표: OOO

## 🎯 Trading Setup
> 오늘 밤 주목할 시나리오
> - 시나리오 A: OOO 발생 시 → 대응
> - 시나리오 B: OOO 발생 시 → 대응
"""
```

### 7.2 장중 체크포인트

```python
CHECKPOINT_PROMPT = """
📍 장중 체크포인트 #{checkpoint_num}

═══════════════════════════════════════════════════════════════
[현재 시장 상황]
{market_data}

[감지된 변동]
{changes}
═══════════════════════════════════════════════════════════════

### 📋 출력 형식 (간결하게)

## 📍 Checkpoint #{checkpoint_num} ({current_time} KST)

**시장 현황**
- S&P 500: {sp500} ({sp500_change})
- NASDAQ: {nasdaq} ({nasdaq_change})
- VIX: {vix}

**주요 변동**
{significant_changes_summary}

**원인 분석**
{cause_analysis}

**대응 포인트**
{action_points}
"""
```

### 7.3 미국장 마감 브리핑 (07:10)

**(v2.0 계획서의 US_BRIEFING_PROMPT와 동일)**

### 7.4 국내장 오픈 브리핑 (08:00)

**(v2.0 계획서의 KR_BRIEFING_PROMPT와 동일)**

---

## 8. 텔레그램 알림 시스템

### 8.1 시스템 개요

```
┌─────────────────────────────────────────────────────────────┐
│                  Telegram Bot System                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   [알림 유형]                                                │
│   ├── 📢 정기 브리핑 (5종)                                   │
│   │    ├── 프리마켓 브리핑                                   │
│   │    ├── 장중 체크포인트 (변동 시에만)                     │
│   │    ├── 미국장 마감 브리핑                                │
│   │    ├── 국내장 오픈 브리핑                                │
│   │    └── 주간 리포트                                      │
│   │                                                          │
│   ├── 🚨 속보 알림 (실시간)                                  │
│   │    ├── HIGH 중요도 뉴스                                  │
│   │    ├── 보유종목 급등락 (±5%)                            │
│   │    └── VIX 급등 (±15%)                                  │
│   │                                                          │
│   └── 💬 명령어 응답                                         │
│        ├── /status - 시장 현황                               │
│        ├── /portfolio - 포트폴리오 현황                      │
│        ├── /schedule - 오늘 일정                             │
│        └── /help - 도움말                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 텔레그램 봇 구현

**파일**: `backend/notifications/telegram_bot.py`

```python
"""
Telegram Bot for AI Trading System

브리핑 전송 + 속보 알림 + 명령어 응답
"""

import asyncio
import logging
from typing import Optional, List
from datetime import datetime

from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


class TradingTelegramBot:
    """AI 트레이딩 시스템 텔레그램 봇"""
    
    def __init__(self, token: str, chat_id: str):
        """
        Args:
            token: 텔레그램 봇 토큰 (@BotFather에서 발급)
            chat_id: 메시지를 보낼 채팅/채널 ID
        """
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(token=token)
        self.app = None
    
    async def initialize(self):
        """봇 초기화 및 명령어 핸들러 등록"""
        self.app = Application.builder().token(self.token).build()
        
        # 명령어 핸들러 등록
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("portfolio", self._cmd_portfolio))
        self.app.add_handler(CommandHandler("schedule", self._cmd_schedule))
        
        logger.info("✅ Telegram Bot initialized")
    
    # ═══════════════════════════════════════════════════════════
    # 브리핑 전송 메서드
    # ═══════════════════════════════════════════════════════════
    
    async def send_premarket_briefing(self, briefing: str):
        """프리마켓 브리핑 전송"""
        header = "🌙 *Pre-Market Briefing*\n\n"
        await self._send_long_message(header + briefing)
    
    async def send_checkpoint(self, briefing: str):
        """장중 체크포인트 전송"""
        header = "📍 *Market Checkpoint*\n\n"
        await self._send_long_message(header + briefing)
    
    async def send_us_briefing(self, briefing: str):
        """미국장 마감 브리핑 전송"""
        header = "🇺🇸 *US Market Close Briefing*\n\n"
        await self._send_long_message(header + briefing)
    
    async def send_kr_briefing(self, briefing: str):
        """국내장 오픈 브리핑 전송"""
        header = "🇰🇷 *Korea Market Open Briefing*\n\n"
        await self._send_long_message(header + briefing)
    
    async def send_weekly_report(self, report: str, report_type: str):
        """주간 리포트 전송"""
        if report_type == "review":
            header = "📊 *Weekly Review*\n\n"
        else:
            header = "🔮 *Weekly Outlook*\n\n"
        await self._send_long_message(header + report)
    
    # ═══════════════════════════════════════════════════════════
    # 속보 알림 메서드
    # ═══════════════════════════════════════════════════════════
    
    async def send_breaking_news(self, news: dict):
        """속보 알림 전송"""
        message = f"""
🚨 *BREAKING NEWS*

*{news['title']}*

{news['summary']}

📊 영향도: {news['market_relevance']}
🏭 섹터: {', '.join(news.get('sectors_affected', []))}
🕐 {news['published_date']}
"""
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def send_portfolio_alert(self, alert: dict):
        """포트폴리오 알림 (급등락)"""
        emoji = "🔥" if alert['change'] > 0 else "⚠️"
        direction = "급등" if alert['change'] > 0 else "급락"
        
        message = f"""
{emoji} *Portfolio Alert - {direction}*

종목: *{alert['ticker']}* ({alert['name']})
변동: *{alert['change']:+.2f}%*
현재가: {alert['current_price']}

원인: {alert.get('reason', '분석 중...')}
"""
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def send_vix_alert(self, vix_data: dict):
        """VIX 급등 알림"""
        message = f"""
🔴 *VIX Alert*

현재 VIX: *{vix_data['current']:.2f}*
변동: *{vix_data['change']:+.2f}%*

시장 공포 지수가 급등했습니다. 
변동성 확대에 주의하세요.
"""
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    # ═══════════════════════════════════════════════════════════
    # 명령어 핸들러
    # ═══════════════════════════════════════════════════════════
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """시작 명령어"""
        await update.message.reply_text(
            "🤖 *AI Trading Bot*에 오신 것을 환영합니다!\n\n"
            "/help 명령어로 사용법을 확인하세요.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말"""
        help_text = """
🤖 *AI Trading Bot 명령어*

/status - 현재 시장 현황
/portfolio - 포트폴리오 현황
/schedule - 오늘 브리핑/경제 일정
/help - 이 도움말

📢 *자동 알림*
• 프리마켓 브리핑 (23:00)
• 장중 체크포인트 (변동 시)
• 미국장 마감 브리핑 (07:10)
• 국내장 오픈 브리핑 (08:00)
• 속보 알림 (실시간)
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """시장 현황"""
        # 실시간 시장 데이터 조회
        from backend.services.market_data_service import MarketDataService
        service = MarketDataService()
        data = await service.get_current_status()
        
        status_text = f"""
📊 *Market Status*

*US Futures*
• S&P 500: {data['sp500_futures']} ({data['sp500_change']})
• NASDAQ: {data['nasdaq_futures']} ({data['nasdaq_change']})

*Indicators*
• VIX: {data['vix']}
• DXY: {data['dxy']}
• 10Y Treasury: {data['treasury_10y']}

*Crypto*
• BTC: ${data['btc']:,.0f}

🕐 Updated: {data['timestamp']}
"""
        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _cmd_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """포트폴리오 현황"""
        from backend.services.portfolio_service import PortfolioService
        service = PortfolioService()
        portfolio = await service.get_portfolio_summary()
        
        text = f"""
💼 *Portfolio Summary*

*총 평가금액*: {portfolio['total_value']:,.0f}원
*총 손익*: {portfolio['total_pnl']:+,.0f}원 ({portfolio['total_pnl_pct']:+.2f}%)

*종목별 현황*
"""
        for stock in portfolio['holdings'][:5]:
            emoji = "🟢" if stock['pnl_pct'] > 0 else "🔴"
            text += f"{emoji} {stock['name']}: {stock['pnl_pct']:+.2f}%\n"
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def _cmd_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """오늘 일정"""
        from backend.utils.timezone_manager import get_timezone_manager
        tz = get_timezone_manager()
        schedules = tz.get_all_schedules()
        is_dst = tz.is_daylight_saving()
        
        text = f"""
📅 *Today's Schedule*
*(DST: {'적용중' if is_dst else '미적용'})*

*브리핑 일정*
• 프리마켓: {schedules['premarket_briefing']}
• 체크포인트 #1: {schedules['checkpoint_1']}
• 체크포인트 #2: {schedules['checkpoint_2']}
• 미국 마감: {schedules['us_close_briefing']}
• 국내 오픈: {schedules['kr_open_briefing']}

*시장 시간*
• 미국장 시작: {schedules['market_open']}
• 미국장 마감: {schedules['market_close']}
"""
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    # ═══════════════════════════════════════════════════════════
    # 유틸리티
    # ═══════════════════════════════════════════════════════════
    
    async def _send_long_message(self, text: str, max_length: int = 4000):
        """긴 메시지 분할 전송 (텔레그램 4096자 제한)"""
        if len(text) <= max_length:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # 분할 전송
            parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
            for i, part in enumerate(parts):
                if i > 0:
                    part = f"(계속 {i+1}/{len(parts)})\n\n" + part
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=part,
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(0.5)  # Rate limit 방지


# 싱글톤 인스턴스
_telegram_bot = None

def get_telegram_bot() -> TradingTelegramBot:
    global _telegram_bot
    if _telegram_bot is None:
        from backend.core.config import settings
        _telegram_bot = TradingTelegramBot(
            token=settings.TELEGRAM_BOT_TOKEN,
            chat_id=settings.TELEGRAM_CHAT_ID
        )
    return _telegram_bot
```

### 8.3 텔레그램 봇 설정

**.env 추가**:
```env
# Telegram Bot Settings
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_or_channel_id
TELEGRAM_ENABLE_ALERTS=true
TELEGRAM_BREAKING_NEWS_THRESHOLD=HIGH
```

### 8.4 속보 감지 서비스

**파일**: `backend/services/breaking_news_detector.py`

```python
"""
Breaking News Detector

실시간 속보 감지 및 텔레그램 알림
"""

class BreakingNewsDetector:
    """속보 감지기"""
    
    # 속보 감지 조건
    BREAKING_KEYWORDS = [
        'breaking', 'just in', 'urgent', 'flash',
        '속보', '긴급', '단독', 'exclusive'
    ]
    
    MAJOR_TICKERS = [
        'NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA',
        'AMD', 'INTC', 'AVGO', 'ASML'
    ]
    
    async def check_for_breaking_news(self, article: dict) -> bool:
        """속보 여부 확인"""
        # 조건 1: HIGH 중요도
        if article.get('market_relevance') != 'HIGH':
            return False
        
        # 조건 2: 속보 키워드 포함
        title_lower = article.get('title', '').lower()
        has_breaking_keyword = any(kw in title_lower for kw in self.BREAKING_KEYWORDS)
        
        # 조건 3: 주요 종목 언급
        mentions_major_ticker = any(ticker.lower() in title_lower for ticker in self.MAJOR_TICKERS)
        
        return has_breaking_keyword or (article.get('market_relevance') == 'HIGH' and mentions_major_ticker)
    
    async def process_and_alert(self, article: dict):
        """속보 처리 및 알림"""
        if await self.check_for_breaking_news(article):
            bot = get_telegram_bot()
            await bot.send_breaking_news(article)
```

---

## 9. KIS API 포트폴리오 연동

### 9.1 포트폴리오 분석기

**파일**: `backend/services/portfolio_analyzer.py`

```python
"""
Portfolio Analyzer with KIS API

KIS API 연동 포트폴리오 분석
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from backend.api.kis.kis_client import KISClient

logger = logging.getLogger(__name__)


class PortfolioAnalyzer:
    """KIS API 기반 포트폴리오 분석기"""
    
    def __init__(self):
        self.kis_client = KISClient()
    
    async def get_portfolio_summary(self) -> Dict:
        """포트폴리오 요약 조회"""
        # KIS API로 보유종목 조회
        holdings = await self.kis_client.get_stock_balance()
        
        total_value = sum(h['eval_amount'] for h in holdings)
        total_pnl = sum(h['pnl_amount'] for h in holdings)
        total_pnl_pct = (total_pnl / (total_value - total_pnl)) * 100 if total_value > total_pnl else 0
        
        return {
            'total_value': total_value,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'holdings': holdings,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_holdings_for_briefing(self) -> List[Dict]:
        """브리핑용 보유종목 정보"""
        holdings = await self.kis_client.get_stock_balance()
        
        return [
            {
                'ticker': h['ticker'],
                'name': h['name'],
                'quantity': h['quantity'],
                'avg_price': h['avg_price'],
                'current_price': h['current_price'],
                'pnl_pct': h['pnl_pct'],
                'market': h.get('market', 'KR')  # KR or US
            }
            for h in holdings
        ]
    
    async def check_portfolio_alerts(self) -> List[Dict]:
        """포트폴리오 알림 체크 (급등락)"""
        holdings = await self.kis_client.get_stock_balance()
        alerts = []
        
        for h in holdings:
            # 일일 변동률 ±5% 이상
            daily_change = h.get('daily_change_pct', 0)
            if abs(daily_change) >= 5.0:
                alerts.append({
                    'ticker': h['ticker'],
                    'name': h['name'],
                    'change': daily_change,
                    'current_price': h['current_price'],
                    'reason': await self._find_change_reason(h['ticker'])
                })
        
        return alerts
    
    async def _find_change_reason(self, ticker: str) -> str:
        """급등락 원인 검색"""
        # API 웹 검색으로 원인 파악
        from backend.ai.llm.llm_client import get_llm_client
        client = get_llm_client()
        
        prompt = f"Find the reason for {ticker}'s significant price movement today in one sentence."
        reason = await client.generate_with_search(prompt)
        
        return reason or "원인 분석 중..."
    
    async def generate_portfolio_section(self) -> str:
        """브리핑용 포트폴리오 섹션 생성"""
        holdings = await self.get_holdings_for_briefing()
        alerts = await self.check_portfolio_alerts()
        
        if not holdings:
            return "보유종목 없음"
        
        section = "## 💼 Portfolio Watch\n\n"
        
        # 보유종목 현황
        section += "| 종목 | 수익률 | 현재가 |\n"
        section += "|------|--------|--------|\n"
        
        for h in holdings[:5]:  # 상위 5개
            emoji = "🟢" if h['pnl_pct'] > 0 else "🔴"
            section += f"| {emoji} {h['name']} | {h['pnl_pct']:+.2f}% | {h['current_price']:,} |\n"
        
        # 알림
        if alerts:
            section += "\n### ⚠️ Portfolio Alerts\n"
            for alert in alerts:
                direction = "급등" if alert['change'] > 0 else "급락"
                section += f"- **{alert['name']}** {direction}: {alert['change']:+.2f}% - {alert['reason']}\n"
        
        return section


# 싱글톤
_portfolio_analyzer = None

def get_portfolio_analyzer() -> PortfolioAnalyzer:
    global _portfolio_analyzer
    if _portfolio_analyzer is None:
        _portfolio_analyzer = PortfolioAnalyzer()
    return _portfolio_analyzer
```

### 9.2 브리핑에 포트폴리오 연동

```python
# enhanced_daily_reporter.py 수정

async def generate_premarket_briefing(self):
    """프리마켓 브리핑 (포트폴리오 포함)"""
    
    # 1. Ollama 전처리 RSS 조회
    preprocessed_rss = await self._get_preprocessed_rss()
    
    # 2. 포트폴리오 정보 조회 (KIS API)
    portfolio_analyzer = get_portfolio_analyzer()
    portfolio_data = await portfolio_analyzer.get_holdings_for_briefing()
    portfolio_section = await portfolio_analyzer.generate_portfolio_section()
    
    # 3. 프롬프트 생성
    prompt = PREMARKET_BRIEFING_PROMPT.format(
        preprocessed_rss_data=json.dumps(preprocessed_rss, ensure_ascii=False),
        portfolio_data=json.dumps(portfolio_data, ensure_ascii=False),
        portfolio_alerts=portfolio_section
    )
    
    # 4. 브리핑 생성
    briefing = await self.llm_client.generate_with_search(prompt)
    
    # 5. 텔레그램 전송
    await self.telegram_bot.send_premarket_briefing(briefing)
    
    return briefing
```

---

## 10. 주간 리포트 시스템

### 10.1 주간 리포트 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    주간 리포트 시스템                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [토요일 14:00] 📊 주간 리뷰                                 │
│  ├── 한 주 시장 요약                                        │
│  ├── 섹터별 성과 분석                                       │
│  ├── 주요 이슈 정리                                         │
│  ├── 포트폴리오 주간 성과 (KIS API)                         │
│  └── 브리핑 정확도 분석                                     │
│                                                              │
│  [일요일 22:00] 🔮 주간 전망                                 │
│  ├── 다음 주 주요 일정                                      │
│  ├── 다음 주 전망 및 전략                                   │
│  ├── 이번 주 전체 리뷰                                      │
│  └── 🤖 AI 시스템 분석                                      │
│       ├── 잘한 점 (Strengths)                               │
│       ├── 잘못한 점 (Weaknesses)                            │
│       ├── 개선 필요 사항 (Improvements)                     │
│       └── 시스템 수정 제안 (Recommendations)                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 주간 리포터

**파일**: `backend/ai/reporters/weekly_reporter.py`

```python
"""
Weekly Reporter

주간 리뷰 + 전망 + AI 시스템 분석
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from backend.database.connection import DatabaseSession
from backend.ai.llm.llm_client import get_llm_client
from backend.services.portfolio_analyzer import get_portfolio_analyzer
from backend.notifications.telegram_bot import get_telegram_bot

logger = logging.getLogger(__name__)


class WeeklyReporter:
    """주간 리포트 생성기"""
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.portfolio_analyzer = get_portfolio_analyzer()
        self.telegram_bot = get_telegram_bot()
    
    # ═══════════════════════════════════════════════════════════
    # 토요일: 주간 리뷰
    # ═══════════════════════════════════════════════════════════
    
    async def generate_weekly_review(self) -> str:
        """
        주간 리뷰 생성 (토요일 14:00)
        """
        logger.info("📊 Generating Weekly Review...")
        
        # 1. 이번 주 브리핑 데이터 수집
        weekly_briefings = await self._get_weekly_briefings()
        
        # 2. 포트폴리오 주간 성과
        portfolio_performance = await self._get_portfolio_weekly_performance()
        
        # 3. 주간 시장 데이터
        market_data = await self._get_weekly_market_data()
        
        # 4. 프롬프트 생성 및 리포트 생성
        prompt = WEEKLY_REVIEW_PROMPT.format(
            weekly_briefings=json.dumps(weekly_briefings, ensure_ascii=False),
            portfolio_performance=json.dumps(portfolio_performance, ensure_ascii=False),
            market_data=json.dumps(market_data, ensure_ascii=False),
            week_start=self._get_week_start().strftime('%Y-%m-%d'),
            week_end=datetime.now().strftime('%Y-%m-%d')
        )
        
        review = await self.llm_client.generate_with_search(prompt)
        
        # 5. 텔레그램 전송
        await self.telegram_bot.send_weekly_report(review, "review")
        
        # 6. DB 저장
        await self._save_weekly_report(review, "review")
        
        logger.info("✅ Weekly Review generated and sent")
        return review
    
    # ═══════════════════════════════════════════════════════════
    # 일요일: 주간 전망 + 시스템 분석
    # ═══════════════════════════════════════════════════════════
    
    async def generate_weekly_outlook_with_system_analysis(self) -> str:
        """
        주간 전망 + AI 시스템 분석 (일요일 22:00)
        """
        logger.info("🔮 Generating Weekly Outlook with System Analysis...")
        
        # 1. 다음 주 일정 조회
        next_week_calendar = await self._get_next_week_calendar()
        
        # 2. 이번 주 전체 리뷰 데이터
        weekly_summary = await self._get_weekly_summary()
        
        # 3. AI 시스템 성과 분석 데이터
        system_metrics = await self._get_system_metrics()
        
        # 4. 브리핑 정확도 분석
        accuracy_analysis = await self._analyze_briefing_accuracy()
        
        # 5. 프롬프트 생성
        prompt = WEEKLY_OUTLOOK_PROMPT.format(
            next_week_calendar=json.dumps(next_week_calendar, ensure_ascii=False),
            weekly_summary=json.dumps(weekly_summary, ensure_ascii=False),
            system_metrics=json.dumps(system_metrics, ensure_ascii=False),
            accuracy_analysis=json.dumps(accuracy_analysis, ensure_ascii=False)
        )
        
        outlook = await self.llm_client.generate_with_search(prompt)
        
        # 6. 텔레그램 전송
        await self.telegram_bot.send_weekly_report(outlook, "outlook")
        
        # 7. DB 저장
        await self._save_weekly_report(outlook, "outlook")
        
        # 8. 시스템 개선 사항 추출 및 이슈 생성
        improvements = await self._extract_system_improvements(outlook)
        if improvements:
            await self._create_improvement_issues(improvements)
        
        logger.info("✅ Weekly Outlook generated and sent")
        return outlook
    
    # ═══════════════════════════════════════════════════════════
    # 데이터 수집 메서드
    # ═══════════════════════════════════════════════════════════
    
    async def _get_weekly_briefings(self) -> List[Dict]:
        """이번 주 브리핑 조회"""
        week_start = self._get_week_start()
        
        async with DatabaseSession() as session:
            # 이번 주 생성된 브리핑 조회
            briefings = await session.execute(
                """
                SELECT type, content, created_at, metrics
                FROM daily_briefings
                WHERE created_at >= :week_start
                ORDER BY created_at
                """,
                {"week_start": week_start}
            )
            return [dict(b) for b in briefings.fetchall()]
    
    async def _get_portfolio_weekly_performance(self) -> Dict:
        """포트폴리오 주간 성과"""
        # KIS API로 주간 성과 조회
        return await self.portfolio_analyzer.get_weekly_performance()
    
    async def _get_weekly_market_data(self) -> Dict:
        """주간 시장 데이터"""
        # 웹 검색으로 주간 시장 요약
        prompt = "Summarize this week's US stock market performance including S&P500, NASDAQ, major sectors"
        return await self.llm_client.generate_with_search(prompt)
    
    async def _get_system_metrics(self) -> Dict:
        """AI 시스템 성과 메트릭"""
        week_start = self._get_week_start()
        
        async with DatabaseSession() as session:
            # 브리핑 생성 통계
            stats = await session.execute(
                """
                SELECT 
                    COUNT(*) as total_briefings,
                    AVG(generation_time) as avg_generation_time,
                    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits,
                    SUM(api_cost) as total_api_cost
                FROM daily_briefings
                WHERE created_at >= :week_start
                """,
                {"week_start": week_start}
            )
            
            return dict(stats.fetchone())
    
    async def _analyze_briefing_accuracy(self) -> Dict:
        """브리핑 정확도 분석"""
        # 예측 vs 실제 비교
        # - 프리마켓 브리핑에서 예측한 방향 vs 실제 장 마감 결과
        # - 추천 종목 성과
        
        week_start = self._get_week_start()
        
        # 분석 로직 구현
        accuracy_data = {
            "market_direction_accuracy": 0.0,  # 시장 방향 예측 정확도
            "sector_prediction_accuracy": 0.0,  # 섹터 예측 정확도
            "stock_pick_performance": [],  # 종목 추천 성과
            "false_positives": [],  # 잘못된 경고
            "missed_events": []  # 놓친 이벤트
        }
        
        # TODO: 상세 분석 로직 구현
        
        return accuracy_data
    
    async def _get_next_week_calendar(self) -> List[Dict]:
        """다음 주 경제 일정"""
        prompt = """
        Search for next week's major US economic calendar events including:
        - FOMC meetings
        - GDP, PCE, CPI releases
        - Employment data
        - Major earnings reports
        
        Return as a list with date, time, event name, and importance.
        """
        return await self.llm_client.generate_with_search(prompt)
    
    async def _extract_system_improvements(self, outlook: str) -> List[Dict]:
        """시스템 개선 사항 추출"""
        prompt = f"""
        다음 주간 리포트에서 AI 시스템 개선 사항을 추출하세요:
        
        {outlook}
        
        JSON 형식으로 반환:
        [
            {{
                "category": "accuracy|performance|feature|bug",
                "priority": "high|medium|low",
                "title": "개선 제목",
                "description": "상세 설명",
                "suggested_action": "제안 액션"
            }}
        ]
        """
        
        result = await self.llm_client.generate(prompt)
        try:
            return json.loads(result)
        except:
            return []
    
    async def _create_improvement_issues(self, improvements: List[Dict]):
        """개선 사항을 이슈로 생성 (로그 기록)"""
        for imp in improvements:
            logger.info(f"📌 System Improvement [{imp['priority']}]: {imp['title']}")
            # TODO: GitHub Issue 생성 또는 내부 이슈 트래커 연동
    
    def _get_week_start(self) -> datetime:
        """이번 주 월요일"""
        today = datetime.now()
        return today - timedelta(days=today.weekday())
    
    async def _save_weekly_report(self, report: str, report_type: str):
        """주간 리포트 DB 저장"""
        async with DatabaseSession() as session:
            await session.execute(
                """
                INSERT INTO weekly_reports (type, content, created_at)
                VALUES (:type, :content, :created_at)
                """,
                {
                    "type": report_type,
                    "content": report,
                    "created_at": datetime.now()
                }
            )
            await session.commit()
```

### 10.3 주간 리뷰 프롬프트 (토요일)

```python
WEEKLY_REVIEW_PROMPT = """
📊 주간 리뷰 리포트 생성

═══════════════════════════════════════════════════════════════
[기간]: {week_start} ~ {week_end}

[이번 주 브리핑 데이터]
{weekly_briefings}

[포트폴리오 주간 성과]
{portfolio_performance}

[주간 시장 데이터]
{market_data}
═══════════════════════════════════════════════════════════════

### 📋 출력 형식

## 📊 Weekly Review ({week_start} ~ {week_end})

### 🌍 한 주 시장 요약
> 이번 주 시장의 핵심 흐름 3문장

### 📈 주간 지수 성과
| 지수 | 주간 변동 | 주요 원인 |
|------|----------|-----------|
| S&P 500 | | |
| NASDAQ | | |
| 코스피 | | |

### 🏭 섹터별 성과
| 순위 | 섹터 | 주간 수익률 | 주요 이슈 |
|------|------|------------|-----------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

### 🔥 이번 주 핵심 이슈 (Top 5)
1. [이슈명] - 영향 및 의미
2. ...

### 💼 포트폴리오 주간 성과
- 총 수익률: X%
- 최고 성과 종목: OOO (+X%)
- 최저 성과 종목: OOO (-X%)

### 📊 브리핑 리뷰
- 이번 주 브리핑 횟수: X회
- 주요 예측 적중 사례: ...
- 개선이 필요한 부분: ...

### 💡 Key Takeaways
> 이번 주에서 배운 점 3가지
"""
```

### 10.4 주간 전망 + 시스템 분석 프롬프트 (일요일)

```python
WEEKLY_OUTLOOK_PROMPT = """
🔮 주간 전망 + AI 시스템 분석 리포트

═══════════════════════════════════════════════════════════════
[다음 주 경제 일정]
{next_week_calendar}

[이번 주 요약]
{weekly_summary}

[AI 시스템 메트릭]
{system_metrics}

[브리핑 정확도 분석]
{accuracy_analysis}
═══════════════════════════════════════════════════════════════

### 📋 출력 형식

## 🔮 Weekly Outlook & System Analysis

### 📅 다음 주 주요 일정
| 날짜 | 시간 | 이벤트 | 중요도 | 예상 영향 |
|------|------|--------|--------|----------|
| | | | | |

### 🔭 다음 주 전망

#### 시장 전망
> 다음 주 시장 예상 방향 및 근거

#### 섹터별 전망
| 섹터 | 전망 | 주목 포인트 |
|------|------|-------------|
| | | |

#### 주목할 종목
- [종목명]: 이유
- ...

### 📊 이번 주 전체 리뷰
> 한 주 전체를 관통하는 핵심 테마 및 교훈

═══════════════════════════════════════════════════════════════
## 🤖 AI Trading System Analysis
═══════════════════════════════════════════════════════════════

### ✅ 잘한 점 (Strengths)
1. [구체적 사례와 함께]
2. ...
3. ...

### ❌ 잘못한 점 (Weaknesses)
1. [구체적 사례와 함께]
   - 원인 분석:
   - 영향:
2. ...

### 🔧 개선 필요 사항 (Improvements Needed)
| 우선순위 | 항목 | 현재 상태 | 목표 상태 | 제안 액션 |
|----------|------|----------|----------|-----------|
| 🔴 높음 | | | | |
| 🟡 중간 | | | | |
| 🟢 낮음 | | | | |

### 💡 시스템 수정 제안 (Recommendations)

#### 즉시 적용 (이번 주)
- [ ] [구체적 수정 사항]
- [ ] ...

#### 단기 개선 (2주 내)
- [ ] [구체적 수정 사항]
- [ ] ...

#### 장기 개선 (1개월 내)
- [ ] [구체적 수정 사항]
- [ ] ...

### 📈 성과 메트릭
| 메트릭 | 이번 주 | 지난 주 | 변화 |
|--------|---------|---------|------|
| 브리핑 생성 수 | | | |
| 평균 생성 시간 | | | |
| 캐시 적중률 | | | |
| API 비용 | | | |
| 예측 정확도 | | | |

### 🎯 다음 주 목표
1. [구체적 목표]
2. [구체적 목표]
3. [구체적 목표]
"""
```

---

## 11. 검증 체크리스트

### Phase 1-3 검증 (기존)
**(v2.0 계획서와 동일)**

### Phase 4 검증: 서머타임 스케줄러
- [ ] `is_daylight_saving()` 정확히 동작
- [ ] 동절기/서머타임 스케줄 자동 전환
- [ ] DST 변경일 자동 감지 및 재설정
- [ ] 모든 시간이 KST 기준으로 정확

### Phase 5 검증: 브리핑 (프리마켓 + 체크포인트)
- [ ] 23:00 (동절기) / 22:00 (서머타임) 프리마켓 브리핑 생성
- [ ] 장중 체크포인트 ±1% 이상 변동 시에만 생성
- [ ] 포트폴리오 섹션 포함 확인

### Phase 6 검증: 국내장 브리핑
**(v2.0 계획서와 동일)**

### Phase 7 검증: KIS API 연동
- [ ] 보유종목 조회 정상
- [ ] 주간 성과 계산 정확
- [ ] 급등락 알림 (±5%) 동작
- [ ] 브리핑에 포트폴리오 섹션 포함

### Phase 8 검증: 텔레그램
- [ ] 봇 토큰/채팅ID 설정
- [ ] 5종 정기 브리핑 전송 확인
- [ ] 속보 알림 실시간 전송
- [ ] 명령어 응답 (/status, /portfolio 등)
- [ ] 긴 메시지 분할 전송

### Phase 9 검증: 주간 리포트
- [ ] 토요일 14:00 주간 리뷰 생성
- [ ] 일요일 22:00 주간 전망 생성
- [ ] AI 시스템 분석 섹션 포함
- [ ] 개선 사항 추출 및 로깅

### Phase 10 검증: 통합 테스트
- [ ] 24시간 연속 운영 테스트
- [ ] 서머타임 전환 시뮬레이션
- [ ] 전체 브리핑 사이클 테스트
- [ ] 에러 복구 테스트

---

## 12. 완료 기준

| 항목 | 상태 | 설명 |
|------|------|------|
| **DB** | ✅ | 필요한 모든 테이블/컬럼 생성 |
| **Ollama** | ✅ | 24시간 5분 간격 전처리 |
| **서머타임** | ✅ | 자동 감지 및 스케줄 조정 |
| **프리마켓 브리핑** | ✅ | 23:00/22:00 생성 |
| **장중 체크포인트** | ✅ | 01:00/03:00 (변동 시) |
| **미국 마감 브리핑** | ✅ | 07:10/06:10 생성 |
| **국내 오픈 브리핑** | ✅ | 08:00 생성 |
| **주간 리뷰** | ✅ | 토요일 14:00 |
| **주간 전망** | ✅ | 일요일 22:00 + 시스템 분석 |
| **텔레그램** | ✅ | 모든 브리핑 + 속보 알림 |
| **KIS API** | ✅ | 포트폴리오 연동 완료 |
| **캐싱** | ✅ | 비용 70% 절감 달성 |

---

## 📚 참고 문서

- **원본 Plan 파일**: `C:\Users\a\.claude\plans\dapper-cuddling-bear.md`
- **v2.0 계획서**: `daily_briefing_system_v2_implementation_plan.md`
- **구조 맵**: `docs/architecture/structure-map.md`

---

## 📝 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2026-01-22 | v2.0 | 초기 통합 계획서 |
| 2026-01-22 | v2.1 | 프리마켓/체크포인트, 서머타임, 텔레그램, KIS API, 주간 리포트 추가 |

---

**End of Implementation Plan v2.1 Final**
