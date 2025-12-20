
import sys
import os
from sqlalchemy import create_engine, text, inspect

# Valid connection string for local docker
SQLALCHEMY_DATABASE_URL = "postgresql://ai_trading_user:wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU@localhost:5541/ai_trading"

def migrate_analysis_table():
    print(f"Connecting to DB...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('analysis_results')]
        
        print(f"Existing columns: {columns}")
        
        alter_commands = []
        
        if 'title_kr' not in columns:
            alter_commands.append("ALTER TABLE analysis_results ADD COLUMN title_kr VARCHAR(500)")
        if 'tickers' not in columns:
            alter_commands.append("ALTER TABLE analysis_results ADD COLUMN tickers VARCHAR(200)")
        if 'sector' not in columns:
            alter_commands.append("ALTER TABLE analysis_results ADD COLUMN sector VARCHAR(100)")
        if 'sentiment_score' not in columns:
            alter_commands.append("ALTER TABLE analysis_results ADD COLUMN sentiment_score FLOAT")
        if 'sentiment_label' not in columns:
            alter_commands.append("ALTER TABLE analysis_results ADD COLUMN sentiment_label VARCHAR(50)")
        if 'urgency' not in columns:
            alter_commands.append("ALTER TABLE analysis_results ADD COLUMN urgency VARCHAR(50)")
        if 'impact_magnitude' not in columns:
            alter_commands.append("ALTER TABLE analysis_results ADD COLUMN impact_magnitude FLOAT")
        if 'trading_actionable' not in columns:
            # boolean default false requires some care, usually better to add nullable, then update, then set not null.
            # but simple ADD COLUMN is fine for now, will be null for old rows.
            alter_commands.append("ALTER TABLE analysis_results ADD COLUMN trading_actionable BOOLEAN DEFAULT FALSE")

        for cmd in alter_commands:
            print(f"Executing: {cmd}")
            try:
                conn.execute(text(cmd))
                conn.commit()
                print("Success.")
            except Exception as e:
                print(f"Error executing {cmd}: {e}")
                
    print("Migration check complete.")

if __name__ == "__main__":
    # Add project root to path
    sys.path.append(os.getcwd())
    migrate_analysis_table()
