# Database Modernization & Stabilization Plan

## 1. Overview
The current system relies on a local PostgreSQL/TimescaleDB installation that has proven unstable (authentication issues, dependency on local environment). The goal is to modernize the database infrastructure to be robust, portable, and cloud-ready.

## 2. Current Issues
1.  **Dependency on Local Environment**: Code crashes if local DB is down or misconfigured (fixed via "Soft Fail", but underlying issue remains).
2.  **Authentication Hell**: Frequent `password authentication failed for user "postgres"` errors due to local vs. docker conflicts.
3.  **TimescaleDB Availability**: The `asyncpg` driver is optional, but without it, advanced features (TickFlow, etc.) degrade.

## 3. Proposed Solution (Future Work)

### Phase A: Containerized Infrastructure (Docker)
Instead of relying on a local Windows Postgres installation, we will move to a strictly containerized setup.

-   **Docker Compose**: define `db` service using official `timescale/timescaledb:latest-pg14` image.
-   **Volume Management**: Persist data in `./data/db` explicitly, independent of OS registry.
-   **Environment Variables**: Enforce `.env` based configuration for ALL database connections (Host, Port, User, Pass).

### Phase B: Cloud Migration Path (Supabase / Neon)
To support "Real Trading" without maintaining local servers:
-   **Cloud Choice**: Migrate to Supabase (Postgres + pgvector) or Neon (Serverless Postgres).
-   **Connection Pooling**: Use built-in connection poolers (PgBouncer) provided by these services.

### Phase C: ORM Standardization
-   **SQLAlchemy Async**: Fully standardize on SQLAlchemy 2.0 (Async) for all interactions, deprecating raw `asyncpg` queries where possible to reduce maintenance burden.
-   **Alembic Migrations**: Enforce schema changes via Alembic, not raw SQL scripts.

## 4. Action Items
1.  [ ] Create `docker-compose.yml` with TimescaleDB + Redis.
2.  [ ] Write migration script to export current local data -> Docker volume.
3.  [ ] update `backend/config.py` to prefer Docker service names when running in container.

## 5. Timeline
-   **Q2 2026**: Phase A (Local Docker)
-   **Q3 2026**: Phase B (Cloud Migration for Live Trading)
