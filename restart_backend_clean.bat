@echo off
title AI Trading System - Clean Backend Restart
echo ================================================================================
echo Clean Backend Restart - Cache Clear + Restart
echo ================================================================================
echo.

echo [1/3] Stopping any running Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc >nul 2>&1
echo     - Cache cleared

echo [3/3] Starting Backend...
echo.
call start_backend.bat
