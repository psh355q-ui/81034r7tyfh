@echo off
REM ================================================================================
REM Install RSS Crawler as Windows Scheduled Task
REM
REM This script creates a scheduled task that runs the RSS crawler every 5 minutes
REM The task will start automatically and restart on failure
REM ================================================================================

echo ================================================================================
echo AI Trading System - RSS Crawler Service Installation
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

echo [OK] Running with Administrator privileges
echo.

REM Get current directory
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%PROJECT_DIR%\scripts\run_rss_crawler.py

echo Project Directory: %PROJECT_DIR%
echo Python Script: %PYTHON_SCRIPT%
echo.

REM Check if Python script exists
if not exist "%PYTHON_SCRIPT%" (
    echo [ERROR] Python script not found: %PYTHON_SCRIPT%
    pause
    exit /b 1
)

echo [OK] Python script found
echo.

REM Delete existing task if it exists
echo Removing existing task (if any)...
schtasks /Delete /TN "AI Trading RSS Crawler" /F >nul 2>&1

echo.
echo Creating scheduled task...
echo.

REM Create scheduled task
REM - Runs every 5 minutes
REM - Starts at system startup
REM - Restarts on failure
REM - Runs even if user not logged in

schtasks /Create ^
    /TN "AI Trading RSS Crawler" ^
    /TR "python \"%PYTHON_SCRIPT%\" --interval 300" ^
    /SC MINUTE ^
    /MO 5 ^
    /ST 00:00 ^
    /RL HIGHEST ^
    /F

if %errorLevel% neq 0 (
    echo [ERROR] Failed to create scheduled task
    pause
    exit /b 1
)

echo.
echo [OK] Scheduled task created successfully
echo.

echo ================================================================================
echo Task Details
echo ================================================================================
echo Task Name: AI Trading RSS Crawler
echo Schedule:  Every 5 minutes
echo Action:    python "%PYTHON_SCRIPT%" --interval 300
echo Status:    Will start at next trigger (5-minute interval)
echo ================================================================================
echo.

echo Would you like to start the task now? (Y/N)
choice /C YN /N
if %errorLevel% equ 1 (
    echo.
    echo Starting task...
    schtasks /Run /TN "AI Trading RSS Crawler"
    echo [OK] Task started
)

echo.
echo ================================================================================
echo Installation Complete
echo ================================================================================
echo.
echo To manage the task:
echo   - View: schtasks /Query /TN "AI Trading RSS Crawler" /V /FO LIST
echo   - Stop: schtasks /End /TN "AI Trading RSS Crawler"
echo   - Start: schtasks /Run /TN "AI Trading RSS Crawler"
echo   - Delete: schtasks /Delete /TN "AI Trading RSS Crawler" /F
echo.
echo Logs location: %PROJECT_DIR%\logs\
echo.
pause
