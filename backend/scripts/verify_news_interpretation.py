"""
News Agent Enhancement 검증 스크립트

news_interpretations 테이블 확인
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.repository import get_sync_session

def check_news_interpretations():
    """News interpretations 테이블 확인"""
    db = get_sync_session()
    
    try:
        # SQL 쿼리
        result = db.execute("""
            SELECT COUNT(*) as total
            FROM news_interpretations 
        """).fetchone()
        
        total = result[0] if result else 0
        print(f"\n✅ Total news interpretations: {total}\n")
        
        if total > 0:
            # 최근 5개 조회
            results = db.execute("""
                SELECT 
                    id,
                    ticker,
                    headline_bias,
                    expected_impact,
                    time_horizon,
                    confidence,
                    DATE(interpreted_at) as date
                FROM news_interpretations
                ORDER BY interpreted_at DESC
                LIMIT 5
            """).fetchall()
            
            print("Recent interpretations:")
            print("-" * 80)
            for row in results:
                print(f"ID: {row[0]}")
                print(f"  Ticker: {row[1]}")
                print(f"  Bias: {row[2]} | Impact: {row[3]} | Horizon: {row[4]}")
                print(f"  Confidence: {row[5]} | Date: {row[6]}")
                print("-" * 80)
        else:
            print("⚠️  No interpretations found yet.")
            print("   Run War Room to generate interpretations.")
        
        # Macro context도 확인
        macro_result = db.execute("""
            SELECT COUNT(*) as total
            FROM macro_context_snapshots
        """).fetchone()
        
        macro_total = macro_result[0] if macro_result else 0
        print(f"\n✅ Total macro context snapshots: {macro_total}")
        
        if macro_total > 0:
            latest = db.execute("""
                SELECT 
                    snapshot_date,
                    regime,
                    fed_stance,
                    market_sentiment
                FROM macro_context_snapshots
                ORDER BY snapshot_date DESC
                LIMIT 1
            """).fetchone()
            
            if latest:
                print(f"   Latest: {latest[0]} - {latest[1]}, {latest[2]}, {latest[3]}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_news_interpretations()
