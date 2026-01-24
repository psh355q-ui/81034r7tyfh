"""
Economic Watcher Service

경제 지표 감시 시스템 (Real-time Economic Watcher)

Features:
- 매일 00:05 오늘의 경제 일정 로드
- 이벤트별 스나이퍼 스케줄링 (발표 시간까지 대기, 발표 +10초 후 트리거)
- Actual 값 수집 (재시도 3회, 5초 간격)
- Surprise 분석 (예상 vs 실제)
- 즉시 알림 + 브리핑 Context 주입

Usage:
    from backend.services.economic_watcher import EconomicWatcherService
    
    watcher = EconomicWatcherService()
    await watcher.start_daily_monitoring()
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from backend.services.economic_calendar_manager import EconomicCalendarManager
from backend.database.models import EconomicEvent
from backend.database.db_service import get_db_service
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EconomicWatcherService:
    """
    경제 지표 감지 서비스 (Real-time Economic Watcher)
    
    Features:
    - 매일 00:05 오늘의 경제 일정 로드
    - 이벤트별 스나이퍼 스케줄링 (발표 시간까지 대기, 발표 +10초 후 트리거)
    - Actual 값 수집 (재시도 3회, 5초 간격)
    - Surprise 분석 (예상 vs 실제)
    - 즉시 알림 + 브리핑 Context 주입
    """
    
    def __init__(self):
        self.calendar_manager = EconomicCalendarManager()
        self.active_tasks = {}  # 활성 스케줄링 태스
        self.task_results = {}  # 태스 결과
        
        # 스케줄링 설정
        self.schedule_time = "00:05"  # 매일 00:05에 스케줄링 실행
        self.retry_count = 3  # Actual 값 수집 재시도 횟수
        self.retry_interval = 5  # 재시도 간격 (초)
    
    async def load_today_events(self) -> List[Dict]:
        """
        오늘의 경제 이벤트 로드
        
        Returns:
            오늘의 이벤트 리스트
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        events = await self.calendar_manager.get_today_events()
        
        # ★★★ 이벤트만 필터링
        high_importance_events = [
            event for event in events
            if event['importance'] >= 3
        ]
        
        logger.info(f"Loaded {len(high_importance_events)} high importance events for today")
        return high_importance_events
    
    async def _analyze_surprise(self, event: Dict, actual_value: str) -> Dict[str, any]:
        """
        Surprise 분석
        
        Args:
            event: 이벤트 딕셔너리
            actual_value: 실제치
            
        Returns:
            Surprise 분석 결과
        """
        try:
            forecast = event.get('forecast')
            previous = event.get('previous')
            
            if not actual_value or actual_value == '.':
                return {
                    'surprise_pct': None,
                    'direction': None,
                    'score': None,
                    'message': 'No actual value'
                }
            
            actual = float(actual_value)
            
            # Surprise 계산 (실제 vs 예상)
            if forecast and forecast != '.':
                forecast_float = float(forecast)
                surprise_pct = ((actual - forecast_float) / forecast_float) * 100
            elif previous and previous != '.':
                previous_float = float(previous)
                surprise_pct = ((actual - previous_float) / previous_float) * 100
            else:
                surprise_pct = None
            
            # 방향 결정
            if surprise_pct is not None:
                if surprise_pct > 0.5:
                    direction = 'Bullish'
                    score = min(int(abs(surprise_pct) * 10), 100)
                elif surprise_pct < -0.5:
                    direction = 'Bearish'
                    score = min(int(abs(surprise_pct) * 10), 100)
                else:
                    direction = 'Neutral'
                    score = 0
            
            return {
                'surprise_pct': surprise_pct,
                'direction': direction,
                'score': score,
                'message': f"{direction} ({surprise_pct:.2f}%)" if surprise_pct else "Neutral"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing surprise: {e}")
            return {
                'surprise_pct': None,
                'direction': None,
                'score': None,
                'message': f"Error: {e}"
            }
    
    async def _schedule_event_task(self, event: Dict):
        """
        이벤트별 스케줄링 태스 생성
        
        Args:
            event: 이벤트 딕셔너리
        """
        try:
            event_time = event['event_time']
            event_name = event['event_name']
            
            # 현재 시간
            now = datetime.now()
            
            # 발표 시간까지 대기 시간 계산
            time_until_event = event_time - now
            wait_seconds = max(0, time_until_event.total_seconds())
            
            if wait_seconds > 0:
                logger.info(f"⏰ Scheduling event: {event_name} at {event_time}, waiting {wait_seconds}s")
                
                # 발표 시간까지 대기
                await asyncio.sleep(wait_seconds)
            
            # 발표 +10초 후 트리거
            logger.info(f"🎯 Triggering event: {event_name}")
            
            # Actual 값 수집 (재시도)
            actual_value = None
            for attempt in range(self.retry_count):
                try:
                    # FRED API에서 최신 데이터 수집
                    db_service = await get_db_service()

                    async with db_service.get_session() as session:
                        result = await session.execute(
                            text(f"SELECT actual FROM economic_events "
                                 f"WHERE event_name = '{event['event_name']}' "
                                 f"ORDER BY event_time DESC LIMIT 1")
                        )

                        row = result.fetchone()
                        if row and row[0]:
                            actual_value = row[0]
                            logger.info(f"✓ Fetched actual value for {event_name}: {actual_value}")
                            break

                    if actual_value:
                        break

                    # 재시도 간격
                    if attempt < self.retry_count - 1:
                        logger.info(f"⏳ Retry {attempt + 1}/{self.retry_count} in {self.retry_interval}s...")
                        await asyncio.sleep(self.retry_interval)
                except Exception as e:
                    logger.error(f"Error fetching actual value: {e}")
                    if attempt < self.retry_count - 1:
                        await asyncio.sleep(self.retry_interval)

            # Surprise 분석
            if actual_value:
                analysis = await self._analyze_surprise(event, actual_value)
                
                # 이벤트 업데이트
                db_service = await get_db_service()
                
                async with db_service.get_session() as session:
                    await session.execute(
                        text(f"UPDATE economic_events "
                             f"SET actual = '{actual_value}', "
                             f"surprise_pct = {analysis['surprise_pct']}, "
                             f"impact_direction = '{analysis['direction']}', "
                             f"impact_score = {analysis['score']}, "
                             f"notes = '{analysis['message']}', "
                             f"updated_at = NOW() "
                             f"WHERE event_name = '{event['event_name']}' "
                             f"AND event_time = '{event['event_time']}'")
                    )
                    await session.commit()
                
                logger.info(f"✓ Updated {event_name}: Actual={actual_value}, Surprise={analysis['message']}")
                
                # 브리핑 Context 생성 (예시 사용)
                context = f"""
                경제 지표 발표:
                - {event_name}
                - 예상치: {event.get('forecast')}
                - 실제치: {actual_value}
                - 이전치: {event.get('previous')}
                - Surprise: {analysis['message']}
                - 영향도: {analysis['score']}
                """
                
                # 즉시 알림 (텔레그램)
                await self._send_telegram_alert(event, analysis)
                
                return {
                    'success': True,
                    'actual_value': actual_value,
                    'analysis': analysis
                }
            else:
                logger.warning(f"⚠️ Could not fetch actual value for {event_name}")
                return {
                    'success': False,
                    'actual_value': None,
                    'analysis': None
                }
                
        except Exception as e:
            logger.error(f"Error scheduling event task: {e}")
            return {
                'success': False,
                'actual_value': None,
                'analysis': None
            }
    
    async def _send_telegram_alert(self, event: Dict, analysis: Dict):
        """
        텔레그램 즉시 알림
        
        Args:
            event: 이벤트 딕셔너리
            analysis: Surprise 분석 결과
        """
        try:
            # 텔레그램 봇 토큰 가져오기
            from backend.services.telegram_bot import TelegramBot
            telegram_bot = TelegramBot()
            
            # 알림 메시지 생성
            importance_stars = '★' * event['importance']
            
            message = f"""
            📊 경제 지표 발표 알림

            {importance_stars} {event['event_name']}

            📅 발표 시간: {event['event_time'].strftime('%H:%M')}
            
            📊 실제치: {analysis.get('actual_value', 'N/A')}
            📊 이전치: {event.get('previous', 'N/A')}
            
            📊 Surprise: {analysis.get('message', 'N/A')}
            📊 영향도: {analysis.get('score', 'N/A')}

            📈 시장에 미치는 영향이 예상됩니다.
            """
            
            # 텔레그램으로 전송
            await telegram_bot.send_message(message)
            
            logger.info(f"✓ Sent Telegram alert for {event['event_name']}")
            
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
    
    async def start_daily_monitoring(self) -> Dict[str, any]:
        """
        일일 감시 시작
        
        Returns:
            감시 결과
        """
        logger.info("=" * 60)
        logger.info("Starting daily economic monitoring")
        logger.info("=" * 60)
        
        try:
            # 오늘의 경제 이벤트 로드
            events = await self.load_today_events()
            
            if not events:
                logger.warning("No high importance events for today")
                return {
                    'success': False,
                    'message': 'No events to monitor'
                }
            
            logger.info(f"Found {len(events)} events to monitor")
            
            # 각 이벤트별 스케줄링 태스 생성
            tasks = []
            for event in events:
                task = asyncio.create_task(self._schedule_event_task(event))
                tasks.append(task)
            
            # 모든 태스 실행
            results = await asyncio.gather(*tasks)
            
            # 결과 집계
            success_count = sum(1 for result in results if result.get('success', False))
            failed_count = len(results) - success_count
            
            logger.info(f"✓ Monitoring completed: {success_count} success, {failed_count} failed")
            
            return {
                'success': True,
                'message': f"Monitoring completed: {success_count} success, {failed_count} failed",
                'events_count': len(events),
                'success_count': success_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            logger.error(f"Error in daily monitoring: {e}")
            return {
                'success': False,
                'message': f"Error: {e}"
            }
    
    async def get_economic_context(self) -> str:
        """
        브리핑용 경제 지표 Context 생성
        
        Returns:
            경제 지표 Context 문자열
        """
        try:
            # 최근 7일간의 경제 이벤트 조회
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = today - timedelta(days=7)
            
            events = await self.calendar_manager.get_cached_events(start_date, today)
            
            if not events:
                return "최근 7일간 경제 이벤트가 없습니다."
            
            # ★★★ 이벤트만 필터링
            high_importance_events = [
                event for event in events
                if event['importance'] >= 3
            ]
            
            if not high_importance_events:
                return "최근 7일간 중요 경제 이벤트가 없습니다."
            
            # Context 생성
            context_lines = [
                "## 📊 최근 7일간 주요 경제 지표",
                ""
            ]
            
            for event in high_importance_events[:10]:  # 최근 10개만 표시
                event_time = event['event_time'].strftime('%Y-%m-%d %H:%M')
                importance_stars = '★' * event['importance']
                
                line = f"- **{event_time}** {importance_stars} **{event['event_name']}**"
                
                if event.get('actual'):
                    line += f"  - 실제: {event['actual']}"
                if event.get('previous'):
                    line += f"  - 이전: {event['previous']}"
                if event.get('surprise_pct') is not None:
                    line += f"  - Surprise: {event['surprise_pct']:.2f}%"
                if event.get('impact_direction'):
                    line += f"  - 영향: {event['impact_direction']}"
                if event.get('impact_score'):
                    line += f"  - 점수: {event['impact_score']}"
                
                context_lines.append(line)
            
            context_lines.append("")
            context_lines.append("## 📈 시장 영향 분석")
            context_lines.append("")
            context_lines.append("최근 경제 지표 발표에 따라 시장이 크게 변동할 것으로 예상됩니다.")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f"Error getting economic context: {e}")
            return f"Error getting economic context: {e}"


async def main():
    """메인 함수 - 테스트용"""
    watcher = EconomicWatcherService()
    
    print("=" * 60)
    print("Economic Watcher Service Test")
    print("=" * 60)
    print()
    
    # 일일 감시 테스트
    print("1. Starting daily monitoring...")
    result = await watcher.start_daily_monitoring()
    print(f"   Result: {result['message']}")
    print()
    
    # 경제 Context 조회 테스트
    print("2. Getting economic context...")
    context = await watcher.get_economic_context()
    print(f"   Context:")
    print(context)
    print()


if __name__ == "__main__":
    asyncio.run(main())
