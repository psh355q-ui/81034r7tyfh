@echo off
echo 🚀 Running Backend Unit Tests (Windows)...

cd backend

:: Set up environment variables for testing
set PYTHONPATH=%CD%
set TEST_MODE=true
set DATABASE_URL=sqlite:///./test.db
set KIS_APP_KEY=mock
set KIS_APP_SECRET=mock
set KIS_ACCOUNT_NUMBER=mock

:: Run pytest
:: Excluding integration tests that require real DB/API
python -m pytest tests/ -k "not integration" -v

if %ERRORLEVEL% EQU 0 (
    echo ✅ Tests Passed!
) else (
    echo ❌ Tests Failed!
)

cd ..
