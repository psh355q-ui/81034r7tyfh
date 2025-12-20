# LLM Model Configuration Migration

## Summary

All hardcoded Gemini model names have been centralized to use the `GEMINI_MODEL` environment variable from `.env`.

## Changes Made

### 1. Updated Files

#### `backend/data/news_analyzer.py`
- Line 112-120: Load `GEMINI_MODEL` from environment (default: `gemini-2.5-flash`)
- Line 115-117: Auto-add `models/` prefix if not present
- Line 338: Use `os.getenv("GEMINI_MODEL")` for `model_used` field

#### `backend/ai/gemini_client.py`
- Line 73-75: Load `GEMINI_MODEL` from environment
- Line 87: Dynamic log message with actual model name

### 2. Created `.env.example`
- Comprehensive template with all environment variables
- Organized by category (API Keys, Models, Trading, etc.)
- Includes helpful comments and default values

## Environment Variable

```env
# In .env file
GEMINI_MODEL=gemini-2.5-flash
```

### Available Models
- `gemini-2.5-flash` - Fastest, cheapest (recommended)
- `gemini-2.5-pro` - More capable, slower
- `gemini-2.0-flash-exp` - Experimental version

**Note**: API automatically adds `models/` prefix if not present.

## Benefits

1. **Easy Model Switching**: Change model in one place (`.env`)
2. **Environment-Specific**: Use different models for dev/staging/prod
3. **Version Control Safe**: `.env` excluded, `.env.example` tracked
4. **Fallback Support**: Defaults to `gemini-2.5-flash` if not set

## Testing

After backend restart:
```bash
# Should log: "NewsDeepAnalyzer initialized with model: models/gemini-2.5-flash"
# Should log: "GeminiClient initialized with model: gemini-2.5-flash"
```

## Remaining Hardcoded References

These files still have hardcoded models (lower priority):
- `backend/api/gemini_free_router.py` (gemini-1.5-flash)
- `backend/api/ai_chat_router.py` (gemini-1.5-flash, gemini-1.5-pro)
- `backend/ai/news_intelligence_analyzer.py` (gemini-1.5-flash)
- `backend/ai/reasoning/engine.py` (gemini-2.5-flash, fallback: gemini-1.5-flash)
- `backend/config_phase14.py` (gemini-2.5-pro, gemini-2.5-flash)

These can be updated in a future iteration if needed.
