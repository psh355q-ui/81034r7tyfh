"""
Quick script to check stock_prices table schema
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_schema():
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD'),  # Must be set in .env
        database=os.getenv('POSTGRES_DB', 'ai_trading')
    )

    try:
        # Check if stock_prices table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'stock_prices'
            )
        """)

        print(f"stock_prices table exists: {table_exists}")
        print()

        if table_exists:
            # Get column information
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'stock_prices'
                ORDER BY ordinal_position
            """)

            print(f"Columns in stock_prices table ({len(columns)} total):")
            print("-" * 80)
            for col in columns:
                print(f"  {col['column_name']:20} {col['data_type']:20} "
                      f"NULL: {col['is_nullable']:3} Default: {col['column_default']}")
        else:
            print("Table does not exist! Need to run migration 008.")

        print()
        print("-" * 80)

        # List all tables
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        print(f"\nAll tables in database ({len(tables)} total):")
        for table in tables:
            print(f"  - {table['table_name']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_schema())
