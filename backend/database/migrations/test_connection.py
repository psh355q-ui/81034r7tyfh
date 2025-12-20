"""
PostgreSQL 연결 테스트 스크립트
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    configs = [
        {
            "name": "Docker (5432)",
            "host": "localhost",
            "port": 5432,
            "user": os.getenv("TIMESCALE_USER", "postgres"),
            "password": os.getenv("TIMESCALE_PASSWORD", ""),
            "database": os.getenv("TIMESCALE_DATABASE", "ai_trading"),
        },
        {
            "name": "Local (5541)",
            "host": "localhost",
            "port": 5541,
            "user": os.getenv("TIMESCALE_USER", "postgres"),
            "password": os.getenv("TIMESCALE_PASSWORD", ""),
            "database": os.getenv("TIMESCALE_DATABASE", "ai_trading"),
        },
        {
            "name": "127.0.0.1 (5432)",
            "host": "127.0.0.1",
            "port": 5432,
            "user": os.getenv("TIMESCALE_USER", "postgres"),
            "password": os.getenv("TIMESCALE_PASSWORD", ""),
            "database": os.getenv("TIMESCALE_DATABASE", "ai_trading"),
        },
    ]
    
    print("🔍 PostgreSQL 연결 테스트\n")
    
    for config in configs:
        try:
            print(f"테스트 중: {config['name']}")
            print(f"  Host: {config['host']}")
            print(f"  Port: {config['port']}")
            print(f"  User: {config['user']}")
            print(f"  Database: {config['database']}")
            
            conn = await asyncpg.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                timeout=5
            )
            
            version = await conn.fetchval("SELECT version()")
            print(f"  ✅ 연결 성공!")
            print(f"  {version[:80]}...\n")
            
            await conn.close()
            
        except Exception as e:
            print(f"  ❌ 연결 실패: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_connection())
