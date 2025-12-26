"""
Add chip_war_vote column to ai_debate_sessions table

Phase 24: ChipWarAgent integration
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# DB connection
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    database=os.getenv("POSTGRES_DB", "ai_trading"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD")  # Must be set in .env
)

cursor = conn.cursor()

# Add chip_war_vote column
try:
    cursor.execute("""
        ALTER TABLE ai_debate_sessions
        ADD COLUMN IF NOT EXISTS chip_war_vote VARCHAR(10);
    """)

    cursor.execute("""
        COMMENT ON COLUMN ai_debate_sessions.chip_war_vote
        IS 'Chip War Agent vote (Phase 24: NVDA vs GOOGL TPU competition)';
    """)

    conn.commit()
    print("✅ chip_war_vote column added successfully")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()

finally:
    cursor.close()
    conn.close()
