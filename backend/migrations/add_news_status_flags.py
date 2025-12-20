"""
Database Migration: Add Status Flags to news_articles

Adds three boolean columns to track processing status:
- has_tags: Whether article has been auto-tagged
- has_embedding: Whether article has vector embedding
- rag_indexed: Whether article is indexed in RAG system

Author: AI Trading System
Date: 2025-12-20
"""

import sqlite3
import os
from pathlib import Path

# Database path (same logic as news_models.py)
DB_PATH = Path("/app/data/news.db")
try:
    # Try to create directory if it doesn't exist
    if not DB_PATH.exists():
        # Docker path doesn't exist, use local dev path
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        DATA_DIR = PROJECT_ROOT / "data" / "news"
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DB_PATH = DATA_DIR / "news.db"
except (PermissionError, OSError):
    # Fallback to temp directory
    DB_PATH = Path("/tmp/news.db")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)



def run_migration():
    """Add status flag columns to news_articles table"""
    
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    print(f"📁 Database: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(news_articles)")
        columns = {row[1] for row in cursor.fetchall()}
        
        migrations_needed = []
        if 'has_tags' not in columns:
            migrations_needed.append('has_tags')
        if 'has_embedding' not in columns:
            migrations_needed.append('has_embedding')
        if 'rag_indexed' not in columns:
            migrations_needed.append('rag_indexed')
        
        if not migrations_needed:
            print("✅ All columns already exist. No migration needed.")
            return True
        
        print(f"🔄 Adding columns: {', '.join(migrations_needed)}")
        
        # Add columns
        if 'has_tags' in migrations_needed:
            cursor.execute("""
                ALTER TABLE news_articles 
                ADD COLUMN has_tags BOOLEAN DEFAULT 0 NOT NULL
            """)
            print("  ✓ Added has_tags")
        
        if 'has_embedding' in migrations_needed:
            cursor.execute("""
                ALTER TABLE news_articles 
                ADD COLUMN has_embedding BOOLEAN DEFAULT 0 NOT NULL
            """)
            print("  ✓ Added has_embedding")
        
        if 'rag_indexed' in migrations_needed:
            cursor.execute("""
                ALTER TABLE news_articles 
                ADD COLUMN rag_indexed BOOLEAN DEFAULT 0 NOT NULL
            """)
            print("  ✓ Added rag_indexed")
        
        conn.commit()
        
        # Verify
        cursor.execute("PRAGMA table_info(news_articles)")
        new_columns = {row[1] for row in cursor.fetchall()}
        
        print("\n📊 Verification:")
        print(f"  has_tags: {'✅' if 'has_tags' in new_columns else '❌'}")
        print(f"  has_embedding: {'✅' if 'has_embedding' in new_columns else '❌'}")
        print(f"  rag_indexed: {'✅' if 'rag_indexed' in new_columns else '❌'}")
        
        # Show sample data
        cursor.execute("""
            SELECT id, title, has_tags, has_embedding, rag_indexed 
            FROM news_articles 
            LIMIT 5
        """)
        rows = cursor.fetchall()
        
        if rows:
            print("\n📰 Sample Articles (showing new columns):")
            for row in rows:
                print(f"  ID {row[0]}: tags={row[2]}, emb={row[3]}, rag={row[4]}")
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 70)
    print("DB Migration: Add Status Flags to news_articles")
    print("=" * 70)
    print()
    
    success = run_migration()
    
    print()
    if success:
        print("🎉 Migration complete! You can now track article processing status.")
    else:
        print("⚠️  Migration failed. Please check the errors above.")
