@echo off
REM ============================================================================
REM AI Trading System - Frontend Dev Server Starter
REM ============================================================================

echo.
echo ================================================================================
echo Starting AI Trading System Frontend (React + Vite)
echo ================================================================================
echo.

REM Change to frontend directory
cd /d "%~dp0frontend"

echo Current Directory: %CD%
echo.

REM Check Node.js version
echo Checking Node.js version...
node --version
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo node_modules not found. Installing dependencies...
    call npm install
    echo.
)

echo.
echo ================================================================================
echo Starting Vite Dev Server...
echo ================================================================================
echo.
echo Frontend URL: http://localhost:3002
echo Dashboard: http://localhost:3002/dashboard
echo.
echo Backend Proxy: http://localhost:8001
echo.

REM Start Vite dev server on port 3002
call npm run dev

pause
