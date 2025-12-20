
import sys
import os


# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text

# Hardcoded for verification script to avoid import complexity
SQLALCHEMY_DATABASE_URL = "postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading"

def view_latest_analysis():
    print(f"Connecting to DB...")
    # SQLALCHEMY_DATABASE_URL handles the connection details
    engine = create_engine(SQLALCHEMY_DATABASE_URL.replace("+asyncpg", ""), connect_args={'client_encoding': 'utf8'})
    
    with engine.connect() as conn:
        # Query latest 3 analysis results
        query = text("""
        SELECT id, theme, title_kr, tickers, sector, sentiment_score, impact_magnitude 
        FROM analysis_results 
        ORDER BY id DESC 
        LIMIT 3
        """)
        
        result = conn.execute(query)
        rows = result.fetchall()
        
        print("\n" + "="*60)
        print(" LATEST ANALYSIS RESULTS (DB)")
        print("="*60)
        
        if not rows:
            print("No analysis results found.")
        
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"TitleKR: {row[2]}")
            print(f"Tickers: {row[3]}")
            print(f"Sector: {row[4]}")
            print(f"Sentiment: {row[5]}")
            print(f"Magnitude: {row[6]}")
            print("-" * 30)

if __name__ == "__main__":
    try:
        view_latest_analysis()
    except Exception as e:
        print(f"Error viewing data: {e}")
