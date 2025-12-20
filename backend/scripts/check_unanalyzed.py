
import sys
import os
from sqlalchemy import create_engine, text

# Import hardcoded URL to avoid import issues
SQLALCHEMY_DATABASE_URL = "postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading"

def check_unanalyzed_news():
    print(f"Connecting to DB...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'client_encoding': 'utf8'})
    
    with engine.connect() as conn:
        # Check total news count
        count_sql = text("SELECT COUNT(*) FROM news_articles")
        total_count = conn.execute(count_sql).scalar()
        print(f"Total News Articles: {total_count}")

        # Check unanalyzed count (excluding KIS_API)
        unanalyzed_sql = text("""
            SELECT COUNT(*) 
            FROM news_articles n
            LEFT JOIN analysis_results a ON n.id = a.article_id
            WHERE a.id IS NULL 
            AND n.source != 'KIS_API'
        """)
        unanalyzed_count = conn.execute(unanalyzed_sql).scalar()
        print(f"Unanalyzed Real News (excluding KIS_API): {unanalyzed_count}")
        
        # Show sample of what is available to analyze
        if unanalyzed_count > 0:
            sample_sql = text("""
                SELECT n.id, n.title, n.source
                FROM news_articles n
                LEFT JOIN analysis_results a ON n.id = a.article_id
                WHERE a.id IS NULL 
                AND n.source != 'KIS_API'
                LIMIT 5
            """)
            rows = conn.execute(sample_sql).fetchall()
            print("\nSample Unanalyzed Articles:")
            for row in rows:
                print(f"[{row[0]}] {row[1]} ({row[2]})")

if __name__ == "__main__":
    check_unanalyzed_news()
