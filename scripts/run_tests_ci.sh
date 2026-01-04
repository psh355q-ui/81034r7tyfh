#!/bin/bash
# Run tests in a CI-like environment (Unit tests only)

echo "🚀 Running Backend Unit Tests..."
cd backend

# Set up environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)
export TEST_MODE=true
export DATABASE_URL="sqlite:///./test.db"
export KIS_APP_KEY="mock"
export KIS_APP_SECRET="mock"
export KIS_ACCOUNT_NUMBER="mock"

# Run pytest
# Excluding integration tests that require real DB/API
python -m pytest tests/ -k "not integration" -v

EXIT_CODE=$?
cd ..

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Tests Passed!"
else
    echo "❌ Tests Failed!"
fi

exit $EXIT_CODE
