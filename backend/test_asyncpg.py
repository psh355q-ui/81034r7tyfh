"""Test asyncpg connection to Docker PostgreSQL"""
import asyncio
import asyncpg
import os

async def test_connection():
    try:
        pool = await asyncpg.create_pool(
            host='127.0.0.1',
            port=5434,
            database='ai_trading',
            user='postgres',
            password=os.getenv('DB_PASSWORD', '')
        )
        async with pool.acquire() as conn:
            version = await conn.fetchval('SELECT version()')
            print('SUCCESS! asyncpg connected!')
            print('PostgreSQL:', version[:80])
        await pool.close()
        return True
    except Exception as e:
        print(f'FAILED: {e}')
        return False

if __name__ == '__main__':
    asyncio.run(test_connection())
