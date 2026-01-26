"""Alembic migration environment configuration."""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool, create_engine
from sqlalchemy.engine import Connection

from alembic import context

# Try async engine, fallback to sync
try:
    from sqlalchemy.ext.asyncio import async_engine_from_config
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override database URL from environment variable for security
# This prevents hardcoding credentials in alembic.ini
database_url = os.getenv('DATABASE_URL')
if database_url:
    config.set_main_option('sqlalchemy.url', database_url)

# add your model's MetaData object here
# for 'autogenerate' support
# Import your models here for autogenerate to work
try:
    from backend.database.models import Base
    target_metadata = Base.metadata
except ImportError:
    # Fallback if import fails
    target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online_sync() -> None:
    """Run migrations in 'online' mode using sync engine (psycopg)."""
    
    # Get URL and convert async URL to sync if needed
    url = config.get_main_option("sqlalchemy.url")
    if url and "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # Check if async driver is available
    url = config.get_main_option("sqlalchemy.url")
    use_async = ASYNC_AVAILABLE and url and "+asyncpg" in url
    
    if use_async:
        try:
            asyncio.run(run_async_migrations())
        except Exception as e:
            print(f"Async migration failed: {e}, falling back to sync mode")
            run_migrations_online_sync()
    else:
        # Use sync mode with psycopg (v3)
        run_migrations_online_sync()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

