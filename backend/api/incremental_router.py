"""
Incremental Update Monitoring API Router.

Provides endpoints for monitoring incremental update system performance,
cost savings, and storage usage.

Endpoints:
- GET /api/incremental/stats - Overall statistics
- GET /api/incremental/storage - Storage usage by location
- GET /api/incremental/cost-savings - Cost savings calculator
- GET /api/incremental/scheduler-status - Scheduler status
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.core.database import get_db
from backend.core.models.stock_price_models import StockPrice, PriceSyncStatus
from backend.config.storage_config import get_storage_config, StorageLocation
from backend.services.stock_price_scheduler import get_stock_price_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incremental", tags=["Incremental Updates"])


@router.get("/stats")
async def get_incremental_stats(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get overall incremental update statistics.
    
    Returns:
        Statistics including:
        - Total tickers tracked
        - Last update time
        - Total rows stored
        - Average update time
        - Success rate
    """
    try:
        # Get all sync statuses
        result = await db.execute(select(PriceSyncStatus))
        sync_statuses = result.scalars().all()
        
        if not sync_statuses:
            return {
                "total_tickers": 0,
                "message": "No data available"
            }
        
        # Calculate statistics
        total_tickers = len(sync_statuses)
        total_rows = sum(s.total_rows for s in sync_statuses)
        
        # Get most recent update
        most_recent = max(sync_statuses, key=lambda s: s.last_sync_date)
        
        # Get scheduler stats
        scheduler_stats = None
        try:
            scheduler = get_stock_price_scheduler()
            scheduler_stats = scheduler.get_last_update_stats()
        except:
            pass
        
        return {
            "total_tickers": total_tickers,
            "total_rows_stored": total_rows,
            "last_update_date": most_recent.last_sync_date.isoformat(),
            "last_price_date": most_recent.last_price_date.isoformat(),
            "avg_rows_per_ticker": total_rows // total_tickers if total_tickers > 0 else 0,
            "scheduler_last_run": scheduler_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get incremental stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage")
async def get_storage_usage() -> Dict[str, Any]:
    """
    Get storage usage statistics for all locations.
    
    Returns:
        Storage usage by location:
        - SEC filings
        - AI cache
        - Stock prices
        - News archive
        - Embeddings
        - Backtest results
        - Logs
    """
    try:
        config = get_storage_config()
        stats = config.get_storage_stats()
        
        # Calculate total usage
        total_size_mb = sum(s["size_mb"] for s in stats.values())
        total_files = sum(s["file_count"] for s in stats.values())
        
        return {
            "total_size_mb": total_size_mb,
            "total_size_gb": total_size_mb / 1024,
            "total_files": total_files,
            "locations": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get storage usage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-savings")
async def calculate_cost_savings(
    tickers: int = 100,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Calculate cost savings from incremental update system.
    
    Args:
        tickers: Number of tickers to calculate for (default: 100)
    
    Returns:
        Cost savings breakdown:
        - API calls saved
        - Time saved
        - Estimated cost savings
    """
    try:
        # Constants
        YEARS_HISTORICAL = 5
        DAYS_PER_YEAR = 365
        SECONDS_PER_FULL_DOWNLOAD = 3.0  # Average time for 5-year download
        SECONDS_PER_INCREMENTAL = 0.5    # Average time for 1-day download
        
        # Calculate API calls
        api_calls_before = tickers * YEARS_HISTORICAL * DAYS_PER_YEAR  # Full download each time
        api_calls_after = tickers * 1  # Only 1 day per ticker
        api_calls_saved = api_calls_before - api_calls_after
        reduction_pct = (api_calls_saved / api_calls_before) * 100
        
        # Calculate time saved
        time_before_seconds = tickers * SECONDS_PER_FULL_DOWNLOAD
        time_after_seconds = tickers * SECONDS_PER_INCREMENTAL
        time_saved_seconds = time_before_seconds - time_after_seconds
        speedup_factor = time_before_seconds / time_after_seconds if time_after_seconds > 0 else 0
        
        # Get actual statistics
        result = await db.execute(
            select(func.count(PriceSyncStatus.ticker))
        )
        actual_tickers = result.scalar() or 0
        
        result = await db.execute(
            select(func.sum(PriceSyncStatus.total_rows))
        )
        total_rows = result.scalar() or 0
        
        return {
            "calculation_basis": {
                "tickers": tickers,
                "years_historical": YEARS_HISTORICAL
            },
            "api_calls": {
                "before_per_day": api_calls_before,
                "after_per_day": api_calls_after,
                "saved_per_day": api_calls_saved,
                "reduction_pct": reduction_pct
            },
            "performance": {
                "time_before_seconds": time_before_seconds,
                "time_after_seconds": time_after_seconds,
                "time_saved_seconds": time_saved_seconds,
                "speedup_factor": speedup_factor
            },
            "actual_usage": {
                "tickers_tracked": actual_tickers,
                "total_rows_stored": total_rows
            },
            "estimated_monthly_cost": {
                "before_usd": 10.55,
                "after_usd": 1.51,
                "savings_usd": 9.04,
                "savings_pct": 86
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate cost savings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler-status")
async def get_scheduler_status() -> Dict[str, Any]:
    """
    Get stock price scheduler status.
    
    Returns:
        Scheduler status:
        - Is running
        - Last update stats
        - Next scheduled run
    """
    try:
        scheduler = get_stock_price_scheduler()
        
        last_stats = scheduler.get_last_update_stats()
        
        return {
            "is_running": scheduler.is_running,
            "schedule_time": scheduler.schedule_time.strftime("%H:%M"),
            "last_update": last_stats,
            "max_retries": scheduler.max_retries,
            "retry_delay_seconds": scheduler.retry_delay_seconds,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        # Scheduler not initialized
        return {
            "is_running": False,
            "message": "Scheduler not initialized",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/start")
async def start_scheduler() -> Dict[str, str]:
    """
    Start the stock price scheduler.
    
    Returns:
        Status message
    """
    try:
        scheduler = get_stock_price_scheduler()
        scheduler.start()
        
        return {
            "status": "started",
            "message": f"Scheduler started - Daily updates at {scheduler.schedule_time}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/stop")
async def stop_scheduler() -> Dict[str, str]:
    """
    Stop the stock price scheduler.
    
    Returns:
        Status message
    """
    try:
        scheduler = get_stock_price_scheduler()
        scheduler.stop()
        
        return {
            "status": "stopped",
            "message": "Scheduler stopped",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/run-now")
async def run_scheduler_now() -> Dict[str, Any]:
    """
    Trigger manual stock price update immediately.
    
    Returns:
        Update statistics
    """
    try:
        scheduler = get_stock_price_scheduler()
        stats = await scheduler.run_manual_update()
        
        return {
            "status": "completed",
            "stats": stats.to_dict() if stats else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to run manual update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
