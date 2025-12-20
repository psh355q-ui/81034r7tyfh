# Start backend with PYTHONPATH set for module resolution

$env:PYTHONPATH = "d:\code\ai-trading-system"
Set-Location "d:\code\ai-trading-system\backend"

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
