"""
DEPRECATED: This file has been merged into backend/main.py

As of 2025-12-19, all routers from this file have been consolidated into
backend/main.py to create a single unified entry point.

This file is kept for reference only and should NOT be used.

Use backend/main.py instead:
    python -m uvicorn backend.main:app --port 8001

Or use the start_backend.bat script.

Migration notes:
- All 8 routers from this file are now in backend/main.py
- start_backend.bat has been updated to use backend.main:app
- Total routers in unified backend/main.py: 22
"""

# This file should not be imported or used
raise DeprecationWarning(
    "backend/api/main.py is deprecated. Use backend/main.py instead."
)
