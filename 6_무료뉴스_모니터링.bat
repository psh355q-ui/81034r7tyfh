@echo off
chcp 65001 > nul
title Free News Monitor

:menu
cls
echo ================================================
echo    Free News Monitor (무료 뉴스 모니터링)
echo ================================================
echo.
echo 100%% 무료 뉴스 소스만 사용합니다
echo (구독료 없음, 페이월 없음)
echo.
echo 모드 선택:
echo.
echo   1. 백악관 공식 사이트만 (가장 신뢰도 높음)
echo      - whitehouse.gov
echo      - 2분 간격
echo.
echo   2. 속보 중심 (Reuters + AP + CNBC)
echo      - 빠른 뉴스 업데이트
echo      - 3분 간격
echo.
echo   3. 모든 무료 소스 (종합)
echo      - 백악관 + Reuters + AP + CNBC + C-SPAN + Bloomberg
echo      - 2-5분 간격
echo.
echo   4. RSS 피드만 (가장 가볍고 빠름)
echo      - 서버 부담 없음
echo      - 2-3분 간격
echo.
echo   5. 종료
echo.
echo ================================================
set /p choice="선택 (1-5): "

if "%choice%"=="1" goto whitehouse
if "%choice%"=="2" goto breaking
if "%choice%"=="3" goto all
if "%choice%"=="4" goto rss
if "%choice%"=="5" goto end
goto menu

:whitehouse
cls
echo ================================================
echo    백악관 공식 사이트 모니터링
echo ================================================
echo.
call venv\Scripts\activate.bat
if not exist logs mkdir logs
python backend/scripts/monitor_free_news.py whitehouse
pause
goto menu

:breaking
cls
echo ================================================
echo    속보 중심 모니터링
echo ================================================
echo.
call venv\Scripts\activate.bat
if not exist logs mkdir logs
python backend/scripts/monitor_free_news.py breaking
pause
goto menu

:all
cls
echo ================================================
echo    모든 무료 소스 모니터링
echo ================================================
echo.
call venv\Scripts\activate.bat
if not exist logs mkdir logs
python backend/scripts/monitor_free_news.py all
pause
goto menu

:rss
cls
echo ================================================
echo    RSS 피드 모니터링
echo ================================================
echo.
call venv\Scripts\activate.bat
if not exist logs mkdir logs
python backend/scripts/monitor_free_news.py rss
pause
goto menu

:end
echo.
echo 프로그램을 종료합니다.
timeout /t 2 > nul
