"""
Data Backfill API Router with Progress Tracking.

Endpoints:
- POST /api/backfill/news - Start news backfill job
- POST /api/backfill/prices - Start price data backfill
- GET /api/backfill/status/{job_id} - Check job status
- GET /api/backfill/jobs - List all jobs
- DELETE /api/backfill/jobs/{job_id} - Cancel job

Author: AI Trading System Team
Date: 2025-12-21
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from backend.ai.skills.common.logging_decorator import log_endpoint

try:
    from backend.data.crawlers.multi_source_crawler import MultiSourceNewsCrawler
    from backend.data.processors.news_processor import NewsProcessor
    from backend.data.collectors.stock_price_collector import StockPriceCollector
    from backend.database.repository import (
        get_db_session,
        NewsRepository,
        StockRepository,
        DataCollectionRepository
    )
except ImportError:
    # Mock for standalone testing
    class MultiSourceNewsCrawler:
        pass
    class NewsProcessor:
        pass
    class StockPriceCollector:
        pass

    def get_db_session():
        pass
    class NewsRepository:
        pass
    class StockRepository:
        pass
    class DataCollectionRepository:
        pass


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/backfill", tags=["data-backfill"])


# In-memory job tracking (use Redis/DB in production)
active_jobs: Dict[str, Dict] = {}


class NewsBackfillRequest(BaseModel):
    """Request to backfill news data."""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    keywords: Optional[List[str]] = Field(None, description="Filter keywords")
    tickers: Optional[List[str]] = Field(None, description="Filter tickers")
    sources: Optional[List[str]] = Field(
        None,
        description="News sources (newsapi, google_news, reuters, yahoo)"
    )


class PriceBackfillRequest(BaseModel):
    """Request to backfill price data."""
    tickers: List[str] = Field(..., description="Stock tickers")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    interval: Literal["1d", "1h", "1m"] = Field("1d", description="Data interval (1d, 1h, 1m)")


class BackfillJobResponse(BaseModel):
    """Backfill job creation response."""
    job_id: str
    job_type: str
    status: str
    created_at: datetime
    message: str


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    job_type: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress: Dict
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


@router.post("/news", response_model=BackfillJobResponse)
@log_endpoint("backfill", "system")
async def start_news_backfill(
    request: NewsBackfillRequest,
    background_tasks: BackgroundTasks
):
    """
    Start news data backfill job.

    This will:
    1. Crawl news from multiple sources
    2. Process articles (sentiment, embedding)
    3. Store in database

    Returns job_id for tracking progress.
    """
    try:
        # Parse dates
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)

        # Validate dates
        if start_date > end_date:
            raise HTTPException(400, "start_date must be before end_date")

        if end_date > datetime.now():
            end_date = datetime.now()

        # Create job
        job_id = str(uuid4())
        job = {
            "job_id": job_id,
            "job_type": "news_backfill",
            "status": "pending",
            "progress": {
                "total_articles": 0,
                "crawled_articles": 0,
                "processed_articles": 0,
                "saved_articles": 0,
                "failed_articles": 0
            },
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "params": {
                "start_date": request.start_date,
                "end_date": request.end_date,
                "keywords": request.keywords,
                "tickers": request.tickers,
                "sources": request.sources
            }
        }

        active_jobs[job_id] = job

        # Start background task
        background_tasks.add_task(
            run_news_backfill,
            job_id,
            start_date,
            end_date,
            request.keywords,
            request.tickers
        )

        return BackfillJobResponse(
            job_id=job_id,
            job_type="news_backfill",
            status="pending",
            created_at=job["created_at"],
            message=f"News backfill job started for {start_date.date()} to {end_date.date()}"
        )

    except ValueError as e:
        raise HTTPException(400, f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Failed to start news backfill: {e}")
        raise HTTPException(500, f"Failed to start job: {e}")


@router.post("/prices", response_model=BackfillJobResponse)
@log_endpoint("backfill", "system")
async def start_price_backfill(
    request: PriceBackfillRequest,
    background_tasks: BackgroundTasks
):
    """
    Start price data backfill job.

    This will:
    1. Collect historical OHLCV data
    2. Validate data
    3. Store in database

    Returns job_id for tracking progress.

    Yahoo Finance Limitations:
    - 1m interval: last 7 days only
    - 1h interval: last 730 days (2 years)
    - 1d interval: unlimited historical data
    """
    try:
        # Parse dates
        start_date = datetime.fromisoformat(request.start_date).replace(tzinfo=None)
        end_date = datetime.fromisoformat(request.end_date).replace(tzinfo=None)

        # Validate
        if start_date > end_date:
            raise HTTPException(400, "start_date must be before end_date")

        if not request.tickers:
            raise HTTPException(400, "At least one ticker required")

        if request.interval == "1m":
            cutoff = (datetime.now() - timedelta(days=7)).replace(tzinfo=None)
            if start_date < cutoff:
                raise HTTPException(
                    400,
                    "1-minute interval data is only available for the last 7 days. "
                    "Please adjust start_date."
                )

        if request.interval == "1h":
            cutoff = (datetime.now() - timedelta(days=730)).replace(tzinfo=None)
            if start_date < cutoff:
                raise HTTPException(
                    400,
                    "1-hour interval data is only available for the last 730 days (2 years). "
                    "Please adjust start_date."
                )

        # Create job
        job_id = str(uuid4())
        job = {
            "job_id": job_id,
            "job_type": "price_backfill",
            "status": "pending",
            "progress": {
                "total_tickers": len(request.tickers),
                "processed_tickers": 0,
                "total_data_points": 0,
                "failed_tickers": 0
            },
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "params": {
                "tickers": request.tickers,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "interval": request.interval
            }
        }

        active_jobs[job_id] = job

        # Start background task
        background_tasks.add_task(
            run_price_backfill,
            job_id,
            request.tickers,
            start_date,
            end_date,
            request.interval
        )

        return BackfillJobResponse(
            job_id=job_id,
            job_type="price_backfill",
            status="pending",
            created_at=job["created_at"],
            message=f"Price backfill job started for {len(request.tickers)} tickers"
        )

    except ValueError as e:
        raise HTTPException(400, f"Invalid parameters: {e}")
    except Exception as e:
        logger.error(f"Failed to start price backfill: {e}")
        raise HTTPException(500, f"Failed to start job: {e}")


@router.get("/status/{job_id}", response_model=JobStatusResponse)
@log_endpoint("backfill", "system")
async def get_job_status(job_id: str):
    """Get status of a backfill job."""
    if job_id not in active_jobs:
        raise HTTPException(404, f"Job {job_id} not found")

    job = active_jobs[job_id]

    return JobStatusResponse(
        job_id=job["job_id"],
        job_type=job["job_type"],
        status=job["status"],
        progress=job["progress"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        error_message=job.get("error_message")
    )


@router.get("/jobs")
@log_endpoint("backfill", "system")
async def list_jobs(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 20
):
    """List all backfill jobs with optional filtering."""
    jobs = list(active_jobs.values())

    # Filter by status
    if status:
        jobs = [j for j in jobs if j["status"] == status]

    # Filter by type
    if job_type:
        jobs = [j for j in jobs if j["job_type"] == job_type]

    # Sort by created_at (newest first)
    jobs.sort(key=lambda x: x["created_at"], reverse=True)

    # Limit
    jobs = jobs[:limit]

    return {
        "total": len(jobs),
        "jobs": jobs
    }



# Background tasks



async def run_news_backfill(
    job_id: str,
    start_date: datetime,
    end_date: datetime,
    keywords: Optional[List[str]],
    tickers: Optional[List[str]]
):
    """Run news backfill in background."""
    job = active_jobs[job_id]
    db_job_id = None

    try:
        job["status"] = "running"
        job["started_at"] = datetime.now()

        logger.info(f"Job {job_id}: Starting news backfill")

        # 0. Initialize DB Job
        try:
            async with get_db_session() as session:
                collection_repo = DataCollectionRepository(session)
                db_job = collection_repo.create_job(
                    source="multi_source",
                    collection_type="news",
                    start_date=start_date,
                    end_date=end_date,
                    metadata=job["params"]
                )
                db_job_id = db_job.id
                logger.info(f"Job {job_id}: Created DB job {db_job_id}")
        except Exception as e:
            logger.error(f"Job {job_id}: Failed to create DB job entry: {e}")
            raise e

        # 1. Crawl news
        async with MultiSourceNewsCrawler() as crawler:
            articles = await crawler.crawl_all(
                start_date=start_date,
                end_date=end_date,
                keywords=keywords,
                tickers=tickers
            )

        job["progress"]["total_articles"] = len(articles)
        job["progress"]["crawled_articles"] = len(articles)

        # Update DB progress (Crawl complete)
        if db_job_id:
            try:
                async with get_db_session() as session:
                    collection_repo = DataCollectionRepository(session)
                    collection_repo.update_progress(
                        job_id=db_job_id,
                        processed=0,
                        total=len(articles),
                        status='running'
                    )
            except Exception as e:
                logger.warning(f"Job {job_id}: Failed to update progress (crawl complete): {e}")

        logger.info(f"Job {job_id}: Crawled {len(articles)} articles")

        # 2. Process articles
        processor = NewsProcessor()
        # Process in smaller batches to avoid losing too much work on error, 
        # but here we just process all then save. 
        # Improved: Process and save in chunks to be more robust? 
        # For now, keep existing logic but handle errors better.
        processed = await processor.process_batch(articles, batch_size=10)

        job["progress"]["processed_articles"] = len(processed)

        # 3. Save to database
        saved_count = 0
        async with get_db_session() as session:
            news_repo = NewsRepository(session)
            
            for proc_news in processed:
                try:
                    # Create article dictionary
                    article_dict = {
                        'title': proc_news.article.title,
                        'content': proc_news.article.content,
                        'url': proc_news.article.url,
                        'source': proc_news.article.source,
                        'published_at': proc_news.article.published_at,
                        'content_hash': proc_news.article.generate_hash() if hasattr(proc_news.article, 'generate_hash') else None,
                        'processed_at': proc_news.processed_at,
                        'embedding': proc_news.embedding,
                        'sentiment_score': proc_news.sentiment_score,
                        'sentiment_label': proc_news.sentiment_label,
                        'tags': proc_news.article.tags,
                        'tickers': proc_news.article.tickers,
                        'source_category': proc_news.article.source_category,
                        'metadata': {
                             'author': proc_news.article.author,
                             'processing_errors': proc_news.processing_errors
                        },
                        'embedding_model': proc_news.embedding_model
                    }
                    news_repo.save_processed_article(article_dict)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Failed to save article {proc_news.article.url}: {e}")
                    # Continue to next article even if one fails
            
            # Commit handled by repo or session manager usually, ensure we don't hold transaction if error
        
        # Update completion status in DB
        if db_job_id:
            async with get_db_session() as session:
                collection_repo = DataCollectionRepository(session)
                collection_repo.update_progress(
                        job_id=db_job_id,
                        processed=saved_count,
                        failed=len(articles)-saved_count,
                        status='completed'
                )

        job["progress"]["saved_articles"] = saved_count
        job["status"] = "completed"
        job["completed_at"] = datetime.now()

        logger.info(f"Job {job_id}: Completed successfully. Saved {saved_count} articles.")

    except Exception as e:
        logger.error(f"Job {job_id}: Failed - {e}")
        job["status"] = "failed"
        job["error_message"] = str(e)
        job["completed_at"] = datetime.now()
        
        # Critical: Update DB status to failed using a FRESH session
        if db_job_id:
            try:
                async with get_db_session() as session:
                    collection_repo = DataCollectionRepository(session)
                    collection_repo.update_progress(
                        job_id=db_job_id,
                        processed=job["progress"].get("saved_articles", 0),
                        total=job["progress"].get("total_articles", 0),
                        status='failed',
                        error=str(e)[:255] # Truncate error message if needed
                    )
            except Exception as db_e:
                logger.error(f"Job {job_id}: Failed to update DB status to failed: {db_e}")


async def run_price_backfill(
    job_id: str,
    tickers: List[str],
    start_date: datetime,
    end_date: datetime,
    interval: str
):
    """Run price backfill in background."""
    job = active_jobs[job_id]
    db_job_id = None

    try:
        job["status"] = "running"
        job["started_at"] = datetime.now()

        logger.info(f"Job {job_id}: Starting price backfill for {len(tickers)} tickers")

         # 0. Initialize DB Job
        try:
            async with get_db_session() as session:
                collection_repo = DataCollectionRepository(session)
                db_job = collection_repo.create_job(
                    source="yfinance",
                    collection_type="prices",
                    start_date=start_date,
                    end_date=end_date,
                    metadata=job["params"]
                )
                db_job_id = db_job.id
        except Exception as e:
             logger.error(f"Job {job_id}: Failed to create DB job: {e}")
             raise e

        # Collect price data
        collector = StockPriceCollector()
        results = collector.collect_historical_data(
            tickers, start_date, end_date, interval
        )

        # Update progress
        total_points = sum(len(data) for data in results.values())
        job["progress"]["processed_tickers"] = len(results)
        job["progress"]["total_data_points"] = total_points

        logger.info(f"Job {job_id}: Collected {total_points} data points")

        # Save to database
        async with get_db_session() as session:
             stock_repo = StockRepository(session)
             
             # Convert to dicts for bulk save
             price_dicts = []
             for ticker, data_points in results.items():
                 for p in data_points:
                     price_dicts.append(p.to_dict())
             
             # Bulk save (StockRepository handles batches conceptually, or add batching here)
             # Basic batching for memory management
             batch_size = 5000
             for i in range(0, len(price_dicts), batch_size):
                 batch = price_dicts[i:i+batch_size]
                 stock_repo.save_prices(batch)
             
             job["progress"]["saved_data_points"] = len(price_dicts)
             
             # Update completion
             collection_repo = DataCollectionRepository(session)
             collection_repo.update_progress(
                 job_id=db_job_id,
                 processed=len(price_dicts),
                 total=len(price_dicts),
                 status='completed'
             )

        job["status"] = "completed"
        job["completed_at"] = datetime.now()

        logger.info(f"Job {job_id}: Completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id}: Failed - {e}")
        job["status"] = "failed"
        job["error_message"] = str(e)
        job["completed_at"] = datetime.now()
        
        # Update DB status to failed using FRESH session
        if db_job_id:
            try:
                async with get_db_session() as session:
                    collection_repo = DataCollectionRepository(session)
                    collection_repo.update_progress(
                        job_id=db_job_id,
                        processed=job["progress"].get("saved_data_points", 0),
                        total=job["progress"].get("total_data_points", 0),
                        status='failed',
                        error=str(e)[:255]
                    )
            except Exception as db_e:
                logger.error(f"Job {job_id}: Failed to update DB status to failed: {db_e}")


@router.delete("/jobs/{job_id}", response_model=Dict)
@log_endpoint("backfill", "system")
async def cancel_job(job_id: str):
    """Cancel a running job."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]
    
    if job["status"] in ["completed", "failed", "cancelled"]:
        return {"message": "Job already finished"}

    # Mark as cancelled
    job["status"] = "cancelled"
    job["completed_at"] = datetime.now()
    
    # Update DB if db_job_id exists
    db_job_id = job.get("db_job_id")
    if db_job_id:
        async with get_db_session() as session:
            repo = DataCollectionRepository(session)
            repo.update_progress(
                job_id=db_job_id,
                processed=job["progress"].get("processed_articles", 0),
                status="failed", # Mark as failed/cancelled in DB
                error="Cancelled by user"
            )
            
    logger.info(f"Job {job_id} cancelled by user")
    return {"message": "Job cancelled"}


@router.get("/data/news")
@log_endpoint("backfill", "system")
async def get_backfilled_news(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ticker: Optional[str] = None,
    limit: int = 100
):
    """
    Get backfilled news data from PostgreSQL.
    
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD
    - ticker: Filter by ticker (e.g. AAPL)
    """
    try:
        dt_start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        dt_end = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S") if end_date else None
        
        async with get_db_session() as session:
            repo = DataCollectionRepository(session)
            articles = repo.get_collected_news(
                start_date=dt_start,
                end_date=dt_end,
                ticker=ticker,
                limit=limit
            )
            
            return {
                "count": len(articles),
                "articles": [
                    {
                        "id": a.id,
                        "title": a.title,
                        "source": a.source,
                        "published_date": a.published_date.isoformat() if a.published_date else None,
                        "sentiment_label": a.sentiment_label,
                        "sentiment_score": a.sentiment_score,
                        "tickers": a.tickers,
                        "tags": a.tags
                    }
                    for a in articles
                ]
            }
    except Exception as e:
        logger.error(f"Failed to fetch backfilled news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# For testing
if __name__ == "__main__":
    print("Data Backfill API Router loaded successfully")
    print(f"Endpoints: {len(router.routes)}")
    for route in router.routes:
        print(f"  {route.methods} {route.path}")
