@echo off
REM ============================================================================
REM AI Trading System - Full Stack Starter (Backend + Frontend)
REM ============================================================================

echo.
echo ================================================================================
echo Starting AI Trading System (Full Stack)
echo ================================================================================
echo.
echo Backend: http://localhost:8001
echo Frontend: http://localhost:3002
echo Dashboard: http://localhost:3002/dashboard
echo API Docs: http://localhost:8001/docs
echo.
echo ================================================================================
echo.

REM Change to project root
cd /d "%~dp0"

REM Start backend in a new window
echo Starting Backend Server...
start "AI Trading Backend" cmd /k "start_backend.bat"

REM Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
echo Starting Frontend Server...
start "AI Trading Frontend" cmd /k "start_frontend.bat"

echo.
echo ================================================================================
echo Both servers are starting in separate windows...
echo ================================================================================
echo.
echo Backend: http://localhost:8001/docs
echo Frontend: http://localhost:3002/dashboard
echo.
echo Close this window to keep servers running.
echo To stop servers, close the Backend and Frontend windows.
echo.

pause
