@echo off
title AI Trading System - Main Backend
echo ================================================================================
echo Starting AI Trading System
echo ================================================================================

:: 1. Start News Poller in a separate window
echo Starting News Poller in separate window...
start "AI Trading - News Poller" cmd /k "python -m backend.run_news_crawler"

:: 2. Start Main Backend Server in this window
echo.
echo Starting Main Backend Server...
echo (News Poller is running in the other window)
echo.
python -m uvicorn backend.main:app --reload --port 8001

pause
