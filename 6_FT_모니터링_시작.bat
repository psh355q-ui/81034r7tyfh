@echo off
chcp 65001 > nul
title FT Stealth Monitor

echo ================================================
echo    Financial Times Stealth Monitor
echo ================================================
echo.
echo 백악관 연설 등 중요 뉴스를 3분마다 자동 크롤링
echo (실제 브라우저처럼 행동 - User-Agent 로테이션)
echo.
echo Press Ctrl+C to stop
echo ================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM logs 디렉토리 생성
if not exist logs mkdir logs

REM 모니터 실행
python backend/scripts/monitor_ft.py

pause
