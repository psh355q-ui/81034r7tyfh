"""
Database Service for Historical Data Seeding

Handles database connections and insertion operations with:
- SQLAlchemy ORM for transactional operations
- asyncpg for high-performance bulk inserts
- Connection pooling and error handling
- Automatic schema migration support

Author: AI Trading System Team
Date: 2025-12-21
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

try:
    from backend.config import get_settings
    from backend.database.models import Base, NewsArticle
except ImportError:
    # Standalone execution fallback
    import os

    class MockSettings:
        timescale_host = os.getenv("DB_HOST", "localhost")
        timescale_port = int(os.getenv("DB_PORT", "5433"))
        timescale_user = os.getenv("DB_USER", "postgres")
        timescale_password = os.getenv("DB_PASSWORD", "")  # Must be set in .env
        timescale_database = os.getenv("DB_NAME", "ai_trading")

    def get_settings():
        return MockSettings()

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Database service for Historical Data Seeding operations.

    Features:
    - Async connection pooling (asyncpg)
    - Bulk INSERT optimization
    - Transaction management
    - Error handling and retry logic
    """

    def __init__(self):
        """Initialize database service."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)

        # Async connection pool
        self.pool: Optional[asyncpg.Pool] = None

        # SQLAlchemy async engine
        self.async_engine = None
        self.async_session_maker = None

        # Build connection strings
        self.asyncpg_url = self._build_asyncpg_url()
        self.sqlalchemy_url = self._build_sqlalchemy_url()

    def _build_asyncpg_url(self) -> str:
        """Build asyncpg connection URL."""
        return (
            f"postgresql://{self.settings.timescale_user}:"
            f"{self.settings.timescale_password}@"
            f"{self.settings.timescale_host}:{self.settings.timescale_port}/"
            f"{self.settings.timescale_database}"
        )

    def _build_sqlalchemy_url(self) -> str:
        """Build SQLAlchemy async connection URL."""
        return (
            f"postgresql+asyncpg://{self.settings.timescale_user}:"
            f"{self.settings.timescale_password}@"
            f"{self.settings.timescale_host}:{self.settings.timescale_port}/"
            f"{self.settings.timescale_database}"
        )

    async def connect(self):
        """Initialize database connections."""
        try:
            # Create asyncpg connection pool
            self.pool = await asyncpg.create_pool(
                self.asyncpg_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            self.logger.info("asyncpg connection pool created")

            # Create SQLAlchemy async engine
            self.async_engine = create_async_engine(
                self.sqlalchemy_url,
                echo=False,
                pool_size=10,
                max_overflow=20
            )
            self.async_session_maker = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            self.logger.info("SQLAlchemy async engine created")

        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Close database connections."""
        try:
            if self.pool:
                await self.pool.close()
                self.logger.info("asyncpg connection pool closed")

            if self.async_engine:
                await self.async_engine.dispose()
                self.logger.info("SQLAlchemy async engine disposed")

        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")

    @asynccontextmanager
    async def get_session(self):
        """Get async SQLAlchemy session (context manager)."""
        if not self.async_session_maker:
            await self.connect()

        session = self.async_session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def bulk_insert_news_articles(
        self,
        articles: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> int:
        """
        Bulk insert news articles using asyncpg COPY.

        This is MUCH faster than individual INSERTs:
        - asyncpg COPY: ~50,000 rows/sec
        - Individual INSERT: ~1,000 rows/sec

        Args:
            articles: List of article dicts with keys:
                - title, content, url, source, published_date, content_hash
                - Optional: embedding, tags, tickers, sentiment_score,
                  sentiment_label, source_category, metadata,
                  processed_at, embedding_model
            batch_size: Number of rows per batch

        Returns:
            Number of articles inserted
        """
        if not articles:
            return 0

        if not self.pool:
            await self.connect()

        inserted_count = 0

        # Process in batches
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]

            try:
                async with self.pool.acquire() as conn:
                    # Prepare data for COPY
                    records = []
                    for article in batch:
                        # Required fields
                        record = (
                            article.get('title'),
                            article.get('content'),
                            article.get('url'),
                            article.get('source'),
                            article.get('published_date'),
                            article.get('content_hash'),
                            article.get('crawled_at', datetime.now()),
                            # Extended fields
                            article.get('embedding'),  # VECTOR type
                            article.get('tags'),  # TEXT[]
                            article.get('tickers'),  # TEXT[]
                            article.get('sentiment_score'),  # FLOAT
                            article.get('sentiment_label'),  # VARCHAR
                            article.get('source_category'),  # VARCHAR
                            article.get('metadata'),  # JSONB
                            article.get('processed_at'),  # TIMESTAMPTZ
                            article.get('embedding_model'),  # VARCHAR
                        )
                        records.append(record)

                    # Bulk INSERT with ON CONFLICT DO NOTHING (skip duplicates)
                    await conn.copy_records_to_table(
                        'news_articles',
                        records=records,
                        columns=[
                            'title', 'content', 'url', 'source',
                            'published_date', 'content_hash', 'crawled_at',
                            'embedding', 'tags', 'tickers', 'sentiment_score',
                            'sentiment_label', 'source_category', 'metadata',
                            'processed_at', 'embedding_model'
                        ],
                        # Note: asyncpg copy_records_to_table doesn't support
                        # ON CONFLICT, so we need to use executemany instead
                        # for duplicate handling
                    )

                    inserted_count += len(batch)
                    self.logger.info(
                        f"Inserted batch {i // batch_size + 1}: "
                        f"{len(batch)} articles (total: {inserted_count})"
                    )

            except asyncpg.exceptions.UniqueViolationError as e:
                self.logger.warning(f"Duplicate articles in batch {i // batch_size + 1}: {e}")
                # Fall back to individual inserts with ON CONFLICT
                inserted = await self._insert_articles_individually(conn, batch)
                inserted_count += inserted

            except Exception as e:
                self.logger.error(f"Failed to insert batch {i // batch_size + 1}: {e}")
                # Try individual inserts as fallback
                try:
                    async with self.pool.acquire() as conn:
                        inserted = await self._insert_articles_individually(conn, batch)
                        inserted_count += inserted
                except Exception as e2:
                    self.logger.error(f"Fallback insert also failed: {e2}")

        return inserted_count

    async def _insert_articles_individually(
        self,
        conn: asyncpg.Connection,
        articles: List[Dict[str, Any]]
    ) -> int:
        """
        Insert articles one by one with ON CONFLICT DO NOTHING.

        Slower but handles duplicates gracefully.
        """
        query = """
            INSERT INTO news_articles (
                title, content, url, source, published_date, content_hash, crawled_at,
                embedding, tags, tickers, sentiment_score, sentiment_label,
                source_category, metadata, processed_at, embedding_model
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            ON CONFLICT (url) DO NOTHING
            RETURNING id
        """

        inserted_count = 0
        for article in articles:
            try:
                result = await conn.fetchval(
                    query,
                    article.get('title'),
                    article.get('content'),
                    article.get('url'),
                    article.get('source'),
                    article.get('published_date'),
                    article.get('content_hash'),
                    article.get('crawled_at', datetime.now()),
                    article.get('embedding'),
                    article.get('tags'),
                    article.get('tickers'),
                    article.get('sentiment_score'),
                    article.get('sentiment_label'),
                    article.get('source_category'),
                    article.get('metadata'),
                    article.get('processed_at'),
                    article.get('embedding_model'),
                )
                if result:  # If id was returned, insert succeeded
                    inserted_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to insert article {article.get('url')}: {e}")

        return inserted_count

    async def bulk_insert_stock_prices(
        self,
        prices: List[Dict[str, Any]],
        batch_size: int = 5000
    ) -> int:
        """
        Bulk insert stock price data using asyncpg COPY.

        Args:
            prices: List of price dicts with keys:
                - ticker, date, open, high, low, close, volume, adj_close
                - Optional: metadata
            batch_size: Number of rows per batch

        Returns:
            Number of price records inserted
        """
        if not prices:
            return 0

        if not self.pool:
            await self.connect()

        inserted_count = 0

        # Process in batches
        for i in range(0, len(prices), batch_size):
            batch = prices[i:i + batch_size]

            try:
                async with self.pool.acquire() as conn:
                    # Prepare data for COPY
                    records = []
                    for price in batch:
                        record = (
                            price.get('time') or price.get('date'),  # Support both 'time' and 'date'
                            price.get('ticker'),
                            price.get('open'),
                            price.get('high'),
                            price.get('low'),
                            price.get('close'),
                            price.get('volume'),
                            price.get('adjusted_close') or price.get('adj_close'),  # Support both names
                        )
                        records.append(record)

                    # Bulk INSERT (match actual database schema)
                    await conn.copy_records_to_table(
                        'stock_prices',
                        records=records,
                        columns=[
                            'time', 'ticker', 'open', 'high', 'low',
                            'close', 'volume', 'adjusted_close'
                        ]
                    )

                    inserted_count += len(batch)
                    self.logger.info(
                        f"Inserted batch {i // batch_size + 1}: "
                        f"{len(batch)} price records (total: {inserted_count})"
                    )

            except asyncpg.exceptions.UniqueViolationError as e:
                self.logger.warning(f"Duplicate prices in batch {i // batch_size + 1}: {e}")
                # Fall back to individual inserts
                inserted = await self._insert_prices_individually(conn, batch)
                inserted_count += inserted

            except Exception as e:
                self.logger.error(f"Failed to insert batch {i // batch_size + 1}: {e}")
                # Try individual inserts as fallback
                try:
                    async with self.pool.acquire() as conn:
                        inserted = await self._insert_prices_individually(conn, batch)
                        inserted_count += inserted
                except Exception as e2:
                    self.logger.error(f"Fallback insert also failed: {e2}")

        return inserted_count

    async def _insert_prices_individually(
        self,
        conn: asyncpg.Connection,
        prices: List[Dict[str, Any]]
    ) -> int:
        """
        Insert prices one by one with ON CONFLICT DO NOTHING.
        """
        query = """
            INSERT INTO stock_prices (
                time, ticker, open, high, low, close, volume, adjusted_close
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (time, ticker) DO NOTHING
            RETURNING time
        """

        inserted_count = 0
        for price in prices:
            try:
                result = await conn.fetchval(
                    query,
                    price.get('time') or price.get('date'),
                    price.get('ticker'),
                    price.get('open'),
                    price.get('high'),
                    price.get('low'),
                    price.get('close'),
                    price.get('volume'),
                    price.get('adjusted_close') or price.get('adj_close'),
                )
                if result:
                    inserted_count += 1
            except Exception as e:
                self.logger.warning(
                    f"Failed to insert price {price.get('ticker')} "
                    f"{price.get('date')}: {e}"
                )

        return inserted_count

    async def update_collection_progress(
        self,
        source: str,
        collection_type: str,
        start_date: datetime,
        end_date: datetime,
        status: str,
        total_items: int = 0,
        processed_items: int = 0,
        failed_items: int = 0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Update data collection progress tracking.

        Args:
            source: Data source name
            collection_type: Type of data ('news', 'prices', 'embeddings')
            start_date: Collection start date
            end_date: Collection end date
            status: Job status ('pending', 'running', 'completed', 'failed')
            total_items: Total items to process
            processed_items: Items successfully processed
            failed_items: Items that failed
            error_message: Error message if failed
            metadata: Additional metadata

        Returns:
            Progress record ID
        """
        if not self.pool:
            await self.connect()

        query = """
            INSERT INTO data_collection_progress (
                source, collection_type, start_date, end_date,
                total_items, processed_items, failed_items,
                status, error_message, metadata,
                started_at, completed_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())
            ON CONFLICT (source, collection_type, start_date, end_date)
            DO UPDATE SET
                total_items = EXCLUDED.total_items,
                processed_items = EXCLUDED.processed_items,
                failed_items = EXCLUDED.failed_items,
                status = EXCLUDED.status,
                error_message = EXCLUDED.error_message,
                metadata = EXCLUDED.metadata,
                completed_at = EXCLUDED.completed_at,
                updated_at = NOW()
            RETURNING id
        """

        started_at = datetime.now() if status == 'running' else None
        completed_at = datetime.now() if status in ('completed', 'failed') else None

        async with self.pool.acquire() as conn:
            record_id = await conn.fetchval(
                query,
                source, collection_type, start_date, end_date,
                total_items, processed_items, failed_items,
                status, error_message, metadata,
                started_at, completed_at
            )

        return record_id


# Global database service instance
_db_service: Optional[DatabaseService] = None


async def get_db_service() -> DatabaseService:
    """Get global database service instance (singleton)."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
        await _db_service.connect()
    return _db_service


async def cleanup_db_service():
    """Cleanup global database service."""
    global _db_service
    if _db_service:
        await _db_service.disconnect()
        _db_service = None


# Standalone test
if __name__ == "__main__":
    import asyncio

    print("=" * 80)
    print("Database Service Test")
    print("=" * 80)
    print()

    async def test_connection():
        """Test database connection."""
        db = DatabaseService()

        try:
            print("Testing database connection...")
            await db.connect()
            print("✅ Connection successful!")

            # Test simple query
            async with db.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                print(f"\nPostgreSQL version:")
                print(f"  {version[:100]}...")

                # Check if tables exist
                tables = await conn.fetch("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)

                print(f"\nExisting tables ({len(tables)}):")
                for table in tables:
                    print(f"  - {table['table_name']}")

        except Exception as e:
            print(f"❌ Connection failed: {e}")

        finally:
            await db.disconnect()
            print("\n✅ Disconnected")

    asyncio.run(test_connection())

    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)
