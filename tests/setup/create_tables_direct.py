"""
직접 SQL로 테이블 생성

Alembic 의존성 문제 우회
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

print("\n" + "="*70)
print(" "*15 + "🗄️ PostgreSQL 테이블 생성")
print("="*70 + "\n")

# DATABASE_URL 파싱
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL')
result = urlparse(db_url)

# 연결
conn = psycopg2.connect(
    host=result.hostname,
    port=result.port,
    database=result.path[1:],
    user=result.username,
    password=result.password
)

cursor = conn.cursor()

# 1. shadow_trades 테이블
print("1️⃣ shadow_trades 테이블 생성...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS shadow_trades (
        id SERIAL PRIMARY KEY,
        proposal_id INTEGER,
        ticker VARCHAR(20) NOT NULL,
        action VARCHAR(10) NOT NULL,
        entry_price FLOAT NOT NULL,
        entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        exit_price FLOAT,
        exit_date TIMESTAMP,
        virtual_pnl FLOAT DEFAULT 0.0,
        rejection_reason TEXT,
        status VARCHAR(20) DEFAULT 'TRACKING',
        result_type VARCHAR(30),
        tracking_days INTEGER DEFAULT 7,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
print("   ✅ shadow_trades 생성 완료")

# 2. proposals 테이블
print("\n2️⃣ proposals 테이블 생성...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposals (
        id SERIAL PRIMARY KEY,
        ticker VARCHAR(20) NOT NULL,
        action VARCHAR(10) NOT NULL,
        target_price FLOAT NOT NULL,
        amount FLOAT,
        confidence FLOAT,
        consensus_level FLOAT,
        ai_reasoning TEXT,
        is_constitutional BOOLEAN DEFAULT FALSE,
        constitutional_violations TEXT,
        violated_articles TEXT,
        status VARCHAR(20) DEFAULT 'PENDING',
        commander_decision VARCHAR(20),
        telegram_message_id BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        decided_at TIMESTAMP
    );
""")
print("   ✅ proposals 생성 완료")

# 3. 인덱스 생성
print("\n3️⃣ 인덱스 생성...")

cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_shadow_trades_ticker 
    ON shadow_trades(ticker);
""")

cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_shadow_trades_status 
    ON shadow_trades(status);
""")

cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_proposals_ticker 
    ON proposals(ticker);
""")

cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_proposals_status 
    ON proposals(status);
""")

cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_proposals_telegram_message_id 
    ON proposals(telegram_message_id);
""")

print("   ✅ 인덱스 생성 완료")

# 커밋
conn.commit()

# 확인
print("\n4️⃣ 테이블 확인...")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")

tables = cursor.fetchall()
for table in tables:
    print(f"   • {table[0]}")

cursor.close()
conn.close()

print("\n" + "="*70)
print("✅ 테이블 생성 완료!")
print("="*70)
print("\n🚀 이제 사용 가능:")
print("  • Commander Mode (Telegram 승인/거부)")
print("  • Shadow Trade 추적 (DB 저장)")
print("  • 히스토리 관리 (모든 제안 기록)\n")
