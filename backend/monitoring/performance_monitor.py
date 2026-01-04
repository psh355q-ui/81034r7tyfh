"""
Performance Monitor - 실시간 성능 추적 및 알림 시스템

Date: 2026-01-03
Phase: Performance & Analytics (P5)
"""
import time
import psutil
from functools import wraps
from typing import Callable, Dict, Any, Optional
import asyncio
import logging
from backend.notifications.telegram_notifier import create_telegram_notifier

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    서버 성능 및 함수 실행 시간을 모니터링하고
    임계값 초과 시 경고를 발송하는 시스템
    """

    def __init__(self, threshold_seconds: float = 1.0):
        self.threshold = threshold_seconds
        self.metrics: list[Dict[str, Any]] = []
        self._telegram = None

    @property
    def telegram(self):
        if self._telegram is None:
            self._telegram = create_telegram_notifier()
        return self._telegram

    def monitor(self, func: Callable):
        """함수 실행 시간 및 메모리 사용량 모니터링 데코레이터"""
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                end_memory = process.memory_info().rss / 1024 / 1024
                memory_delta = end_memory - start_memory

                self._record_metric(func.__name__, elapsed, memory_delta)
                
                if elapsed > self.threshold:
                    await self._send_alert(func.__name__, elapsed, memory_delta)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                end_memory = process.memory_info().rss / 1024 / 1024
                memory_delta = end_memory - start_memory

                self._record_metric(func.__name__, elapsed, memory_delta)

                if elapsed > self.threshold:
                    # Sync 함수에서는 비동기 알림을 보낼 수 없으므로 로그만 남기거나
                    # 별도 스레드로 알림을 보낼 수 있음 (여기서는 로그만)
                    logger.warning(
                        f"⚠️ Performance Alert: {func.__name__} took {elapsed:.2f}s "
                        f"(Mem: {memory_delta:+.1f}MB)"
                    )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    def _record_metric(self, func_name: str, elapsed: float, memory_delta: float):
        """메트릭 기록"""
        metric = {
            'function': func_name,
            'elapsed': elapsed,
            'memory_delta': memory_delta,
            'timestamp': time.time()
        }
        self.metrics.append(metric)
        # 1000개까지만 유지
        if len(self.metrics) > 1000:
            self.metrics.pop(0)

    async def _send_alert(self, func_name: str, elapsed: float, memory_delta: float):
        """Telegram 알림 전송"""
        if not self.telegram:
            return

        message = (
            f"⚠️ <b>Performance Alert</b>\n\n"
            f"Functions: <code>{func_name}</code>\n"
            f"Time: <b>{elapsed:.2f}s</b> (Threshold: {self.threshold}s)\n"
            f"Memory: {memory_delta:+.1f}MB"
        )
        try:
            # create_telegram_notifier might return None if disabled
            if self.telegram:
                await self.telegram.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send performance alert: {e}")

    def get_system_stats(self) -> Dict[str, float]:
        """현재 시스템 전체 상태 반환"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }

# 글로벌 인스턴스 (기본 임계값 5초)
perf_monitor = PerformanceMonitor(threshold_seconds=5.0)
