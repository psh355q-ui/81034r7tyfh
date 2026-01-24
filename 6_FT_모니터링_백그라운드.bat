@echo off
chcp 65001 > nul

echo ================================================
echo    FT Monitor - Background Mode
echo ================================================
echo.
echo 백그라운드에서 FT 모니터링 시작...
echo 로그: logs\ft_monitor.log
echo.

REM 가상환경 활성화
call venv\Scripts\activate.bat

REM logs 디렉토리 생성
if not exist logs mkdir logs

REM 백그라운드에서 실행
start /B python backend/scripts/monitor_ft.py > logs/ft_monitor.log 2>&1

echo ✅ FT Monitor started in background
echo.
echo 로그 확인:
echo   type logs\ft_monitor.log
echo.
echo 중지 방법:
echo   작업 관리자에서 python.exe 프로세스 종료
echo   또는 taskkill /F /IM python.exe
echo.
pause
