import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

print("Checking imports...")

try:
    from backend.api.feeds_router import router as feeds_router
    print("✅ Feeds router imported successfully")
except ImportError as e:
    print(f"❌ Feeds router import failed: {e}")
except Exception as e:
    print(f"❌ Feeds router error: {e}")

try:
    from backend.api.ai_review_router import router as ai_review_router
    print("✅ AI Review router imported successfully")
except ImportError as e:
    print(f"❌ AI Review router import failed: {e}")
except Exception as e:
    print(f"❌ AI Review router error: {e}")

try:
    from backend.api.ceo_analysis_router import router as ceo_analysis_router
    print("✅ CEO Analysis router imported successfully")
except ImportError as e:
    print(f"❌ CEO Analysis router import failed: {e}")

try:
    from backend.api.incremental_router import router as incremental_router
    print("✅ Incremental router imported successfully")
except ImportError as e:
    print(f"❌ Incremental router import failed: {e}")
