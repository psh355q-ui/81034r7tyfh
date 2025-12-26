"""
Logs Router - 로그 조회 API

실행 이력 및 시스템 로그를 조회하는 REST API
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
import traceback

from backend.log_manager import log_manager, LogLevel, LogCategory

# Agent Logging
from backend.ai.skills.common.agent_logger import AgentLogger
from backend.ai.skills.common.log_schema import (
    ExecutionLog,
    ErrorLog,
    ExecutionStatus,
    ErrorImpact
)

router = APIRouter(prefix="/logs", tags=["Logs"])
agent_logger = AgentLogger("log-manager", "system")

@router.get("")
async def get_logs(
    limit: int = Query(100, ge=1, le=1000, description="최대 로그 수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
    level: Optional[str] = Query(None, description="로그 레벨 필터 (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    category: Optional[str] = Query(None, description="카테고리 필터 (SYSTEM, API, TRADING, etc.)"),
    days: int = Query(7, ge=1, le=30, description="최근 N일"),
    search: Optional[str] = Query(None, description="검색어"),
):
    """
    로그 목록 조회

    **Parameters:**
    - limit: 최대 결과 수 (1-1000)
    - offset: 페이지네이션 시작 위치
    - level: 로그 레벨 필터
    - category: 카테고리 필터
    - days: 최근 N일 조회 (1-30)
    - search: 메시지 검색어

    **Returns:**
    - total_count: 전체 로그 수
    - logs: 로그 목록
    - limit: 요청한 limit
    - offset: 요청한 offset
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    return log_manager.get_logs(
        limit=limit,
        offset=offset,
        level=level,
        category=category,
        start_date=start_date,
        end_date=end_date,
        search=search
    )

@router.get("/statistics")
async def get_log_statistics(
    days: int = Query(7, ge=1, le=30, description="최근 N일")
):
    """
    로그 통계 조회

    **Parameters:**
    - days: 최근 N일 통계 (1-30)

    **Returns:**
    - total_logs: 전체 로그 수
    - by_level: 레벨별 로그 수
    - by_category: 카테고리별 로그 수
    - errors_count: 에러 로그 수
    - warnings_count: 경고 로그 수
    """
    start_time = datetime.now()
    task_id = f"log-stats-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    try:
        result = log_manager.get_statistics(days=days)
        
        # Log successful execution
        agent_logger.log_execution(ExecutionLog(
            timestamp=datetime.now(),
            agent="system/log-manager",
            task_id=task_id,
            status=ExecutionStatus.SUCCESS,
            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            input={"days": days},
            output={
                "total_logs": result.get("total_logs", 0),
                "errors_count": result.get("errors_count", 0)
            }
        ))
        
        return result
    
    except Exception as e:
        # Log error
        agent_logger.log_error(ErrorLog(
            timestamp=datetime.now(),
            agent="system/log-manager",
            task_id=task_id,
            error={
                "type": type(e).__name__,
                "message": str(e),
                "stack": traceback.format_exc(),
                "context": {"days": days}
            },
            impact=ErrorImpact.LOW,
            recovery_attempted=False
        ))
        raise

@router.get("/levels")
async def get_log_levels():
    """
    사용 가능한 로그 레벨 목록

    **Returns:**
    - levels: 로그 레벨 리스트
    """
    return {
        "levels": [level.value for level in LogLevel]
    }

@router.get("/categories")
async def get_log_categories():
    """
    사용 가능한 로그 카테고리 목록

    **Returns:**
    - categories: 카테고리 리스트
    """
    return {
        "categories": [category.value for category in LogCategory]
    }

@router.post("/cleanup")
async def cleanup_old_logs(
    days: int = Query(30, ge=7, le=365, description="보관 기간 (일)")
):
    """
    오래된 로그 파일 삭제

    **Parameters:**
    - days: 보관 기간 (7-365일)

    **Returns:**
    - deleted_count: 삭제된 파일 수
    - message: 결과 메시지
    """
    deleted_count = log_manager.cleanup_old_logs(days=days)

    return {
        "deleted_count": deleted_count,
        "message": f"Successfully deleted {deleted_count} old log files"
    }
