import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.getcwd())

print("🚀 Simulating main.py startup to catch router errors...")

# 1. AI Review Router
print("\n--- Checking AI Review Router ---")
try:
    from backend.api.ai_review_router import router as ai_review_router
    print("✅ AI Review Router loaded successfully")
except Exception as e:
    print(f"❌ AI Review Router FAILED: {e}")
    import traceback
    traceback.print_exc()

# 2. Feeds Router
print("\n--- Checking Feeds Router ---")
try:
    from backend.api.feeds_router import router as feeds_router
    print("✅ Feeds Router loaded successfully")
except Exception as e:
    print(f"❌ Feeds Router FAILED: {e}")
    import traceback
    traceback.print_exc()

# 3. Incremental Router (known to fail due to asyncpg)
print("\n--- Checking Incremental Router ---")
try:
    from backend.api.incremental_router import router as incremental_router
    print("✅ Incremental Router loaded successfully")
except Exception as e:
    print(f"❌ Incremental Router FAILED: {e}")
