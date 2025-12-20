@echo off
REM ================================================================================
REM Uninstall RSS Crawler Windows Scheduled Task
REM ================================================================================

echo ================================================================================
echo AI Trading System - Uninstall RSS Crawler Service
echo ================================================================================
echo.

REM Check admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges
    echo Please run as Administrator
    pause
    exit /b 1
)

echo Stopping task (if running)...
schtasks /End /TN "AI Trading RSS Crawler" >nul 2>&1

echo Deleting task...
schtasks /Delete /TN "AI Trading RSS Crawler" /F

if %errorLevel% equ 0 (
    echo [OK] Task removed successfully
) else (
    echo [INFO] Task was not installed or already removed
)

echo.
pause
