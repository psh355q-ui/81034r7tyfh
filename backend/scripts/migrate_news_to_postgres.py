"""
SQLite to PostgreSQL News Migration Script

Migrates news data from SQLite files to PostgreSQL.
Files to migrate:
- news.db
- news_crawler.db  
- enhanced_news_cache.db

Usage:
    cd ai-trading-system
    python -m backend.scripts.migrate_news_to_postgres
    
    # Or from backend directory:
    cd backend
    python scripts/migrate_news_to_postgres.py
"""

import asyncio
import sqlite3
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from backend.core.database import AsyncSessionLocal
from backend.core.models.news_models import NewsArticle, NewsSource, NewsSyncStatus

logger = logging.getLogger(__name__)

# SQLite file paths (relative to project root)
SQLITE_FILES = [
    "news.db",
    "data/news.db",
    "news_crawler.db",
    "enhanced_news_cache.db",
]


async def migrate_news_articles(
    db: AsyncSession,
    sqlite_conn: sqlite3.Connection,
    table_name: str = "articles"
) -> int:
    """
    Migrate news articles from SQLite to PostgreSQL.
    
    Returns:
        Number of migrated articles
    """
    cursor = sqlite_conn.cursor()
    
    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    if not cursor.fetchone():
        logger.warning(f"Table {table_name} not found in SQLite")
        return 0
    
    # Get columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    logger.info(f"SQLite columns: {columns}")
    
    # Fetch all rows
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    migrated = 0
    for row in rows:
        row_dict = dict(zip(columns, row))
        
        try:
            # Map SQLite columns to PostgreSQL model
            article_data = {
                "title": row_dict.get("title", ""),
                "content": row_dict.get("content") or row_dict.get("body") or row_dict.get("text", ""),
                "summary": row_dict.get("summary"),
                "url": row_dict.get("url") or row_dict.get("link", ""),
                "source": row_dict.get("source") or row_dict.get("feed_name", ""),
                "published_at": _parse_datetime(row_dict.get("published_at") or row_dict.get("pub_date")),
                "crawled_at": _parse_datetime(row_dict.get("crawled_at") or row_dict.get("created_at")),
                "sentiment": row_dict.get("sentiment"),
                "sentiment_score": row_dict.get("sentiment_score"),
                "language": "en",
            }
            
            # Skip if no URL (required field)
            if not article_data["url"]:
                continue
            
            # Upsert into PostgreSQL
            stmt = insert(NewsArticle).values(**article_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["url"],
                set_={
                    "title": stmt.excluded.title,
                    "content": stmt.excluded.content,
                    "summary": stmt.excluded.summary,
                }
            )
            await db.execute(stmt)
            migrated += 1
            
        except Exception as e:
            logger.error(f"Error migrating article: {e}")
            continue
    
    await db.commit()
    return migrated


async def migrate_news_sources(
    db: AsyncSession,
    sqlite_conn: sqlite3.Connection,
    table_name: str = "feeds"
) -> int:
    """
    Migrate RSS feed sources from SQLite to PostgreSQL.
    """
    cursor = sqlite_conn.cursor()
    
    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    if not cursor.fetchone():
        logger.warning(f"Table {table_name} not found in SQLite")
        return 0
    
    # Get columns and data
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    migrated = 0
    for row in rows:
        row_dict = dict(zip(columns, row))
        
        try:
            source_data = {
                "name": row_dict.get("name") or row_dict.get("title", "Unknown"),
                "url": row_dict.get("url") or row_dict.get("feed_url", ""),
                "source_type": "rss",
                "is_active": row_dict.get("is_active", True),
                "category": row_dict.get("category"),
            }
            
            if not source_data["url"]:
                continue
            
            stmt = insert(NewsSource).values(**source_data)
            stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
            await db.execute(stmt)
            migrated += 1
            
        except Exception as e:
            logger.error(f"Error migrating source: {e}")
            continue
    
    await db.commit()
    return migrated


def _parse_datetime(value: Any) -> datetime:
    """Parse various datetime formats."""
    if value is None:
        return datetime.now()
    
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except:
            return datetime.now()
    
    if isinstance(value, str):
        for fmt in [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S GMT",
        ]:
            try:
                return datetime.strptime(value.strip(), fmt)
            except:
                continue
    
    return datetime.now()


def find_sqlite_files(base_path: str = ".") -> List[Path]:
    """Find all SQLite news files."""
    found = []
    base = Path(base_path)
    
    for pattern in SQLITE_FILES:
        matches = list(base.glob(f"**/{pattern}"))
        found.extend(matches)
    
    # Also search for any .db files in common locations
    for db_file in base.glob("*.db"):
        if db_file not in found:
            found.append(db_file)
    
    return found


async def run_migration(base_path: str = ".") -> Dict[str, Any]:
    """
    Run full migration from SQLite to PostgreSQL.
    
    Returns:
        Migration statistics
    """
    stats = {
        "files_found": 0,
        "files_processed": 0,
        "articles_migrated": 0,
        "sources_migrated": 0,
        "errors": [],
    }
    
    # Find SQLite files
    sqlite_files = find_sqlite_files(base_path)
    stats["files_found"] = len(sqlite_files)
    
    if not sqlite_files:
        logger.warning("No SQLite files found for migration")
        return stats
    
    logger.info(f"Found {len(sqlite_files)} SQLite files to migrate")
    
    # Deduplicate files (avoid processing same file twice)
    unique_files = list(set(str(f) for f in sqlite_files))
    sqlite_files = [Path(f) for f in unique_files]
    logger.info(f"Unique files: {len(sqlite_files)}")
    
    async with AsyncSessionLocal() as db:
        # Create tables if not exist
        from sqlalchemy import text
        try:
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS news_articles (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT,
                    summary TEXT,
                    url VARCHAR(2048) UNIQUE NOT NULL,
                    source VARCHAR(255),
                    published_at TIMESTAMPTZ,
                    crawled_at TIMESTAMPTZ DEFAULT NOW(),
                    tickers TEXT[],
                    sectors TEXT[],
                    sentiment VARCHAR(20),
                    sentiment_score FLOAT,
                    event_type VARCHAR(50),
                    importance INTEGER DEFAULT 1,
                    is_embedded BOOLEAN DEFAULT FALSE,
                    embedding_id INTEGER,
                    language VARCHAR(10) DEFAULT 'en',
                    word_count INTEGER,
                    extra_data JSONB
                )
            """))
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS news_sources (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    url VARCHAR(2048) NOT NULL,
                    source_type VARCHAR(50) DEFAULT 'rss',
                    is_active BOOLEAN DEFAULT TRUE,
                    crawl_interval_minutes INTEGER DEFAULT 30,
                    last_crawl_at TIMESTAMPTZ,
                    total_articles INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    category VARCHAR(100),
                    priority INTEGER DEFAULT 5,
                    config JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            await db.commit()
            logger.info("Tables created successfully")
        except Exception as e:
            logger.error(f"Table creation error: {e}")
            await db.rollback()
        
        for sqlite_path in sqlite_files:
            try:
                logger.info(f"Processing: {sqlite_path}")
                
                conn = sqlite3.connect(str(sqlite_path))
                
                # List all tables
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [t[0] for t in cursor.fetchall()]
                logger.info(f"  Tables: {tables}")
                
                # Migrate articles
                for table in ["articles", "news", "news_articles", "cached_articles"]:
                    if table in tables:
                        count = await migrate_news_articles(db, conn, table)
                        stats["articles_migrated"] += count
                        logger.info(f"  Migrated {count} articles from {table}")
                
                # Migrate sources
                for table in ["feeds", "rss_feeds", "sources", "news_sources"]:
                    if table in tables:
                        count = await migrate_news_sources(db, conn, table)
                        stats["sources_migrated"] += count
                        logger.info(f"  Migrated {count} sources from {table}")
                
                conn.close()
                stats["files_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing {sqlite_path}: {e}")
                stats["errors"].append(str(e))
    
    return stats


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    base_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print(f"Starting SQLite → PostgreSQL migration from {base_path}")
    stats = asyncio.run(run_migration(base_path))
    
    print("\n=== Migration Complete ===")
    print(f"Files found: {stats['files_found']}")
    print(f"Files processed: {stats['files_processed']}")
    print(f"Articles migrated: {stats['articles_migrated']}")
    print(f"Sources migrated: {stats['sources_migrated']}")
    if stats["errors"]:
        print(f"Errors: {len(stats['errors'])}")
        for err in stats["errors"][:5]:
            print(f"  - {err}")
