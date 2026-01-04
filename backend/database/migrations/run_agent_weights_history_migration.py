"""
Run AgentWeightsHistory Migration (Direct psycopg2)
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Get DB URL and parse
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env")

print("Connecting to PostgreSQL...")

# Connect with psycopg2
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

sql_file = "backend/database/migrations/create_agent_weights_history.sql"

print(f"Reading SQL from: {sql_file}")
with open(sql_file, 'r') as f:
    sql = f.read()

print("Executing migration...")
cursor.execute(sql)
conn.commit()

cursor.close()
conn.close()

print("✅ Migration completed successfully!")
print("   Created table: agent_weights_history")
