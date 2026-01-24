@echo off
chcp 65001 > nul
title White House Monitor

echo ================================================
echo    백악관 공식 사이트 모니터링 (무료)
echo ================================================
echo.
echo 모니터링 URL:
echo   - whitehouse.gov/briefing-room/speeches-remarks/
echo   - whitehouse.gov/briefing-room/statements-releases/
echo.
echo 간격: 2분마다 자동 새로고침
echo 로그: logs\free_news_monitor.log
echo.
echo Press Ctrl+C to stop
echo ================================================
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM logs 디렉토리 생성
if not exist logs mkdir logs

REM 백악관 모니터링 시작
python backend/scripts/monitor_free_news.py whitehouse

pause
