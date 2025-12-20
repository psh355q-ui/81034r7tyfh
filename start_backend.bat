@echo off
REM ============================================================================
REM AI Trading System - Backend Server Starter
REM ============================================================================

echo.
echo ================================================================================
echo Starting AI Trading System Backend Server
echo ================================================================================
echo.

REM Change to PROJECT ROOT (not backend directory)
cd /d "%~dp0"

echo Current Directory: %CD%
echo.

REM Check Python version
python --version
echo.

REM Install dependencies to CURRENT Python (important!)
echo Installing dependencies to current Python environment...
python -m pip install --user fastapi "uvicorn[standard]" --upgrade --quiet

echo.
echo ================================================================================
echo Starting Server...
echo ================================================================================
echo.
echo API Documentation: http://localhost:8001/docs
echo News API (Realtime): http://localhost:8001/news/realtime/health
echo.

REM Start uvicorn from PROJECT ROOT with backend.main:app
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

pause
