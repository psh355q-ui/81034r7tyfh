@echo off
REM ============================================================================
REM AI Trading System - Database Only Starter (PostgreSQL + Redis)
REM ============================================================================

echo.
echo ================================================================================
echo Starting AI Trading System Database Services
echo ================================================================================
echo.
echo PostgreSQL (TimescaleDB): localhost:5432
echo Redis: localhost:6379
echo.
echo ================================================================================
echo.

REM Change to project root
cd /d "%~dp0"

echo Starting PostgreSQL and Redis with Docker Compose...
echo.

docker-compose up -d timescaledb redis

echo.
echo ================================================================================
echo Database Services Started
echo ================================================================================
echo.
echo PostgreSQL: localhost:5432
echo   Database: ai_trading
echo   User: ai_trading_user
echo.
echo Redis: localhost:6379
echo.
echo To stop: docker-compose down
echo To view logs: docker-compose logs -f timescaledb redis
echo.

pause
