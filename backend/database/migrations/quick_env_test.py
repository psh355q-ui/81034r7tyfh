"""
Quick test to verify .env is being read correctly
"""
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path, override=True)

print("=" * 60)
print("ENV FILE TEST")
print("=" * 60)
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_PASSWORD: {os.getenv('DB_PASSWORD')}")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
print("=" * 60)

# Test connection with psycopg2
try:
    import psycopg2
    
    # Try with environment variables
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    print("✅ psycopg2 connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ psycopg2 connection failed: {e}")
