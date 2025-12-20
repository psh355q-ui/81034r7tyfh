# Quick Fix Guide - Google API Key Issue

## Problem
- GOOGLE_API_KEY is in .env file
- But backend returns: "No API_KEY or ADC found"
- Result: Analysis fails silently

## Solution

### Step 1: Verify .env file
```bash
# Check if key is set
cat .env | grep GOOGLE_API_KEY
# Should show: GOOGLE_API_KEY=AIza...
```

### Step 2: Restart Backend
```bash
# Stop current backend (Ctrl+C)
# Restart
./start_backend.bat
```

### Step 3: Test Analysis
```bash
# In browser: http://localhost:3002/news
# Click "AI 분석 (10개)"
# Check backend logs for successful analysis
```

### Step 4: Verify DB
```bash
python check_db.py
# Should now show: "Analyzed articles: 10"
```

### Step 5: Run Processing Test
```bash
python test_news_processing.py
# Should process articles and generate tags/embeddings
```

## Alternative: Set Environment Variable Directly

If .env still not working:

```powershell
# PowerShell (before starting backend)
$env:GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE"
python -m uvicorn backend.main:app --reload --port 8001
```

## Verify Backend Loaded Key

After restart, check logs for:
```
GeminiClient initialized with model: gemini-1.5-flash
```

If you see "No API key" warning, environment loading failed.
