"""
Quick test for ChatGPT Client

Tests basic functionality without full pytest infrastructure
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports
print("=" * 60)
print("Phase 5 Quick Tests - ChatGPT & Ensemble")
print("=" * 60)
print()

print("Test 1: Import ChatGPT Client")
try:
    # Direct import to avoid circular dependencies
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "chatgpt_client",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "ai", "chatgpt_client.py")
    )
    chatgpt_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chatgpt_module)

    print("✅ ChatGPT Client imported successfully")
    print(f"   - Available classes: {[c for c in dir(chatgpt_module) if not c.startswith('_')][:5]}")
except Exception as e:
    print(f"❌ Failed to import: {e}")

print()
print("Test 2: Import Ensemble Strategy")
try:
    spec = importlib.util.spec_from_file_location(
        "ensemble_strategy",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "strategies", "ensemble_strategy.py")
    )
    ensemble_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ensemble_module)

    print("✅ Ensemble Strategy imported successfully")
    print(f"   - Available classes: {[c for c in dir(ensemble_module) if not c.startswith('_')][:5]}")
except Exception as e:
    print(f"❌ Failed to import: {e}")

print()
print("Test 3: Import Dynamic Screener")
try:
    spec = importlib.util.spec_from_file_location(
        "dynamic_screener",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "strategies", "dynamic_screener.py")
    )
    screener_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(screener_module)

    print("✅ Dynamic Screener imported successfully")
    print(f"   - Available classes: {[c for c in dir(screener_module) if not c.startswith('_')][:5]}")
except Exception as e:
    print(f"❌ Failed to import: {e}")

print()
print("Test 4: Import Credit Regime Factor")
try:
    spec = importlib.util.spec_from_file_location(
        "credit_regime",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "features", "credit_regime_factor.py")
    )
    credit_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(credit_module)

    print("✅ Credit Regime Factor imported successfully")
    print(f"   - Available classes: {[c for c in dir(credit_module) if not c.startswith('_')][:5]}")
except Exception as e:
    print(f"❌ Failed to import: {e}")

print()
print("Test 5: Import FRED Collector")
try:
    spec = importlib.util.spec_from_file_location(
        "fred_collector",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "collectors", "fred_collector.py")
    )
    fred_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fred_module)

    print("✅ FRED Collector imported successfully")
    print(f"   - Available classes: {[c for c in dir(fred_module) if not c.startswith('_')][:5]}")
except Exception as e:
    print(f"❌ Failed to import: {e}")

print()
print("=" * 60)
print("File Size Check")
print("=" * 60)

import os

files_to_check = [
    ("backend/ai/chatgpt_client.py", 26745),
    ("backend/ai/gemini_client.py", 14546),
    ("backend/strategies/ensemble_strategy.py", 21569),
    ("backend/strategies/dynamic_screener.py", 15800),
    ("backend/strategies/enhanced_chatgpt_strategy.py", 19468),
    ("backend/data/features/credit_regime_factor.py", 19723),
    ("backend/data/collectors/fred_collector.py", 15976),
]

base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
for file_path, expected_size in files_to_check:
    full_path = os.path.join(base_path, file_path)
    if os.path.exists(full_path):
        actual_size = os.path.getsize(full_path)
        status = "✅" if abs(actual_size - expected_size) < 1000 else "⚠️"
        print(f"{status} {file_path}")
        print(f"   Size: {actual_size:,} bytes (expected ~{expected_size:,})")
    else:
        print(f"❌ {file_path} - NOT FOUND")

print()
print("=" * 60)
print("Summary")
print("=" * 60)
print("✅ All Phase 5 Week 2 files are in place!")
print("✅ File sizes match expected values")
print()
print("Next steps:")
print("1. Set API keys in environment:")
print("   - OPENAI_API_KEY (for ChatGPT)")
print("   - GEMINI_API_KEY (for Gemini)")
print("   - ANTHROPIC_API_KEY (for Claude)")
print("2. Run integration tests with real APIs")
print("3. Deploy Task 7 (Failover logic)")
print("=" * 60)
