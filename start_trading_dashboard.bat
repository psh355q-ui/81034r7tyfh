@echo off
echo ================================================================================
echo AI Trading System - Trading Dashboard Startup
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/2] Starting Backend API Server...
start "AI Trading API" cmd /k "python scripts\run_api_server.py"
timeout /t 5 /nobreak >nul

echo [2/2] Starting Frontend Dev Server...
start "AI Trading Frontend" cmd /k "cd frontend && npm run dev -- --port 5173 --host 0.0.0.0"

echo.
echo ================================================================================
echo Services Started!
echo ================================================================================
echo.
echo Backend API:  http://localhost:8001/docs
echo Frontend:     http://localhost:5173/
echo.
echo Press any key to open browser...
pause >nul

REM Open browser
start http://localhost:5173/trading

echo.
echo To stop services, close the terminal windows or press Ctrl+C
