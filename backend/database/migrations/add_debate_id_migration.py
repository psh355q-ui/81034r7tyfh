"""
Database Migration: Add debate_id to ai_debate_sessions

문제: War Room 기능이 100% 실패
원인: DB 테이블에 debate_id 칼럼 없음
해결: 칼럼 추가 및 제약조건 설정
"""

from sqlalchemy import create_engine, text
import os
from datetime import datetime

def get_db_url():
    """DB 연결 문자열 가져오기"""
    return os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/ai_trading')

def check_column_exists(engine):
    """debate_id 칼럼이 이미 있는지 확인"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ai_debate_sessions' 
            AND column_name = 'debate_id'
        """))
        return result.fetchone() is not None

def upgrade():
    """Migration: debate_id 칼럼 추가"""
    
    print("="*70)
    print("DB Migration: Add debate_id to ai_debate_sessions")
    print("="*70)
    
    engine = create_engine(get_db_url())
    
    # 1. 칼럼이 이미 있는지 확인
    if check_column_exists(engine):
        print("✅ debate_id 칼럼이 이미 존재합니다. Migration 불필요.")
        return
    
    print("\n🔧 Migration 시작...")
    
    with engine.begin() as conn:
        # 2. 칼럼 추가
        print("Step 1: Adding debate_id column...")
        conn.execute(text("""
            ALTER TABLE ai_debate_sessions 
            ADD COLUMN debate_id VARCHAR(100)
        """))
        print("  ✅ Column added")
        
        # 3. 기존 데이터에 debate_id 생성 (있다면)
        print("\nStep 2: Backfilling existing data...")
        conn.execute(text("""
            UPDATE ai_debate_sessions 
            SET debate_id = 'debate-' || ticker || '-' || 
                to_char(created_at, 'YYYYMMDD-HH24MISS')
            WHERE debate_id IS NULL
        """))
        print("  ✅ Existing data updated")
        
        # 4. NOT NULL 제약조건 추가
        print("\nStep 3: Adding NOT NULL constraint...")
        conn.execute(text("""
            ALTER TABLE ai_debate_sessions 
            ALTER COLUMN debate_id SET NOT NULL
        """))
        print("  ✅ NOT NULL constraint added")
        
        # 5. UNIQUE 제약조건 추가
        print("\nStep 4: Adding UNIQUE constraint...")
        conn.execute(text("""
            ALTER TABLE ai_debate_sessions 
            ADD CONSTRAINT uq_debate_id UNIQUE (debate_id)
        """))
        print("  ✅ UNIQUE constraint added")
        
        # 6. 인덱스 추가
        print("\nStep 5: Creating index...")
        conn.execute(text("""
            CREATE INDEX idx_debate_debate_id 
            ON ai_debate_sessions(debate_id)
        """))
        print("  ✅ Index created")
    
    print("\n" + "="*70)
    print("✅ Migration 완료!")
    print("="*70)

def downgrade():
    """Rollback: debate_id 칼럼 제거"""
    
    print("="*70)
    print("DB Migration Rollback: Remove debate_id")
    print("="*70)
    
    engine = create_engine(get_db_url())
    
    with engine.begin() as conn:
        print("\nRemoving debate_id column...")
        conn.execute(text("""
            ALTER TABLE ai_debate_sessions 
            DROP COLUMN IF EXISTS debate_id CASCADE
        """))
        print("  ✅ Column removed")
    
    print("\n" + "="*70)
    print("✅ Rollback 완료!")
    print("="*70)

def verify():
    """Migration 결과 확인"""
    
    print("\n" + "="*70)
    print("Verification")
    print("="*70)
    
    engine = create_engine(get_db_url())
    
    with engine.connect() as conn:
        # 칼럼 정보 조회
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'ai_debate_sessions' 
            ORDER BY ordinal_position
        """))
        
        print("\n📋 ai_debate_sessions 테이블 구조:")
        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            max_len = f"({row[3]})" if row[3] else ""
            print(f"  - {row[0]}: {row[1]}{max_len} {nullable}")
        
        # 제약조건 조회
        result = conn.execute(text("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'ai_debate_sessions'
        """))
        
        print("\n🔒 제약조건:")
        for row in result:
            print(f"  - {row[0]}: {row[1]}")
        
        # 인덱스 조회
        result = conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'ai_debate_sessions'
        """))
        
        print("\n📊 인덱스:")
        for row in result:
            print(f"  - {row[0]}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "downgrade":
            downgrade()
        elif command == "verify":
            verify()
        else:
            print("Usage: python add_debate_id_migration.py [upgrade|downgrade|verify]")
    else:
        # Default: upgrade
        upgrade()
        verify()
