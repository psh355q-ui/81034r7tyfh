import sqlite3
import os

DB_PATH = 'data/news.db'

def migrate_v2():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print('Checking definition...')
        cursor.execute("PRAGMA table_info(news_articles)")
        existing_cols = [c[1] for c in cursor.fetchall()]
        print('Existing columns:', existing_cols)

        # Columns to add to match backend/database/models.py
        # Note: SQLite doesn't strictly enforce types, using TEXT/REAL/BLOB as appropriate
        columns_to_add = [
            ("content_hash", "TEXT"),
            ("embedding", "TEXT"), # ARRAY in Postgres, mapped to TEXT/JSON in SQLite
            ("tags", "TEXT"),      # ARRAY in Postgres
            ("tickers", "TEXT"),   # ARRAY in Postgres
            ("sentiment_score", "REAL"),
            ("sentiment_label", "TEXT"),
            ("source_category", "TEXT"),
            ("metadata", "TEXT"),  # JSONB in Postgres
            ("processed_at", "TIMESTAMP"),
            ("embedding_model", "TEXT")
        ]

        for col_name, col_type in columns_to_add:
            if col_name not in existing_cols:
                print(f"Adding column {col_name} ({col_type})...")
                try:
                    cursor.execute(f"ALTER TABLE news_articles ADD COLUMN {col_name} {col_type}")
                except Exception as e:
                    print(f"Failed to add {col_name}: {e}")
            else:
                print(f"Column {col_name} already exists.")

        # Special handling for 'content_hash' which is non-nullable in Postgres but we must add as nullable or with default
        # Since we are adding to existing table, it must be nullable or have default. 
        # We'll populate it if it's empty? No, just leave it null for now.
        # But wait, Postgres model says nullable=False. If SQLAlchemy tries to read it and it's None, is it okay?
        # Python None is fine. Operations might assume it's there.
        # Let's optionally index content_hash if needed.
        
        conn.commit()
        
        # Verify
        cursor.execute('PRAGMA table_info(news_articles)')
        final_cols = [c[1] for c in cursor.fetchall()]
        print('Final Schema:', final_cols)
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_v2()
