"""Test Database Connection"""
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

print("=" * 80)
print("Database Configuration Test")
print("=" * 80)
print()

# Check environment variables
print("Environment Variables:")
print(f"  TIMESCALE_HOST: {os.getenv('TIMESCALE_HOST')}")
print(f"  TIMESCALE_PORT: {os.getenv('TIMESCALE_PORT')}")
print(f"  TIMESCALE_USER: {os.getenv('TIMESCALE_USER')}")
print(f"  TIMESCALE_PASSWORD: {os.getenv('TIMESCALE_PASSWORD')[:10]}..." if os.getenv('TIMESCALE_PASSWORD') else "None")
print(f"  TIMESCALE_DATABASE: {os.getenv('TIMESCALE_DATABASE')}")
print(f"  DATABASE_URL: {os.getenv('DATABASE_URL')}")
print()

# Import and check repository configuration
from backend.database.repository import DATABASE_URL
print(f"Constructed DATABASE_URL: {DATABASE_URL}")
print()

# Try to connect
print("Attempting database connection...")
try:
    from backend.database.repository import get_sync_session
    db = get_sync_session()
    print("✅ Connection successful!")

    # Try a simple query
    from backend.database.models import TradingSignal
    count = db.query(TradingSignal).count()
    print(f"✅ Query successful! Found {count} trading signals")

    db.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
