"""
Log Manager - 구조화된 로깅 및 이력 관리

실행 이력을 JSON 형식으로 저장하고 조회하는 기능 제공
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, asdict
from enum import Enum
import os

# 로그 레벨
class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# 로그 카테고리
class LogCategory(str, Enum):
    SYSTEM = "SYSTEM"
    API = "API"
    TRADING = "TRADING"
    ANALYSIS = "ANALYSIS"
    EXECUTION = "EXECUTION"
    RISK = "RISK"
    DATA = "DATA"
    ALERT = "ALERT"

@dataclass
class LogEntry:
    """로그 항목"""
    timestamp: str
    level: str
    category: str
    message: str
    details: Optional[Dict] = None
    user: Optional[str] = None
    request_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

class LogManager:
    """로그 관리자"""

    def __init__(self, log_dir: str = "/app/data/logs"):
        self.log_dir = Path(log_dir)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            # 폴백: /tmp 디렉토리 사용
            self.log_dir = Path("/tmp/logs")
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # 로그 파일 경로
        self.current_log_file = self.log_dir / f"app_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"

        # Python logging 설정
        self._setup_python_logging()
        self.logger = logging.getLogger(__name__)

    def _setup_python_logging(self):
        """Python 표준 로깅 설정"""
        # 파일 핸들러 (일별 로그)
        log_file = self.log_dir / f"system_{datetime.utcnow().strftime('%Y%m%d')}.log"

        # 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 파일 핸들러
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # 기존 핸들러 제거 (중복 방지)
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        details: Optional[Dict] = None,
        user: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """구조화된 로그 기록"""
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=level.value,
            category=category.value,
            message=message,
            details=details,
            user=user,
            request_id=request_id
        )

        # JSONL 파일에 기록
        with open(self.current_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + '\n')

        # Python logging에도 기록
        log_method = getattr(self.logger, level.value.lower())
        log_method(f"[{category.value}] {message}")

    def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        level: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> Dict:
        """로그 조회"""
        logs = []
        total_count = 0

        # 날짜 범위 설정
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        # 해당 날짜 범위의 로그 파일 찾기
        log_files = self._get_log_files_in_range(start_date, end_date)

        # 각 파일에서 로그 읽기
        for log_file in sorted(log_files, reverse=True):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())

                            # 필터링
                            if level and entry.get('level') != level:
                                continue
                            if category and entry.get('category') != category:
                                continue
                            if search and search.lower() not in entry.get('message', '').lower():
                                continue

                            total_count += 1

                            # 페이지네이션
                            if total_count <= offset:
                                continue
                            if len(logs) >= limit:
                                continue

                            logs.append(entry)

                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                self.logger.error(f"Error reading log file {log_file}: {e}")
                continue

        return {
            "total_count": total_count,
            "logs": logs,
            "limit": limit,
            "offset": offset
        }

    def _get_log_files_in_range(self, start_date: datetime, end_date: datetime) -> List[Path]:
        """날짜 범위 내의 로그 파일 목록"""
        log_files = []

        current_date = start_date.date()
        end = end_date.date()

        while current_date <= end:
            log_file = self.log_dir / f"app_{current_date.strftime('%Y%m%d')}.jsonl"
            if log_file.exists():
                log_files.append(log_file)
            current_date += timedelta(days=1)

        return log_files

    def get_statistics(self, days: int = 7) -> Dict:
        """로그 통계"""
        start_date = datetime.utcnow() - timedelta(days=days)

        stats = {
            "total_logs": 0,
            "by_level": {},
            "by_category": {},
            "errors_count": 0,
            "warnings_count": 0
        }

        log_files = self._get_log_files_in_range(start_date, datetime.utcnow())

        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())

                            stats["total_logs"] += 1

                            # 레벨별 집계
                            level = entry.get('level', 'UNKNOWN')
                            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

                            # 카테고리별 집계
                            category = entry.get('category', 'UNKNOWN')
                            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

                            # 에러/경고 카운트
                            if level == 'ERROR':
                                stats["errors_count"] += 1
                            elif level == 'WARNING':
                                stats["warnings_count"] += 1

                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                self.logger.error(f"Error reading log file {log_file}: {e}")
                continue

        return stats

    def cleanup_old_logs(self, days: int = 30):
        """오래된 로그 파일 삭제"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted_count = 0
        for log_file in self.log_dir.glob("*.jsonl"):
            try:
                # 파일명에서 날짜 추출
                date_str = log_file.stem.split('_')[-1]
                file_date = datetime.strptime(date_str, '%Y%m%d')

                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    self.logger.info(f"Deleted old log file: {log_file}")

            except Exception as e:
                self.logger.error(f"Error deleting log file {log_file}: {e}")
                continue

        return deleted_count

# 글로벌 인스턴스
log_manager = LogManager()
