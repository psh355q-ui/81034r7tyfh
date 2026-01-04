import sys
import os
from datetime import datetime

# Add root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from backend.database.repository import MacroContextRepository, get_sync_session

def check_macro_context():
    """Check if macro context exists for today"""
    with get_sync_session() as session:
        repo = MacroContextRepository(session)
        
        # Check for today
        today = datetime.now().date()
        print(f"Checking macro context for date: {today}")
        
        # Repository is synchronous
        context = repo.get_latest()
        
        if context:
            context_date = context.snapshot_date
            print(f"Latest context date: {context_date}")
            
            if context_date == today:
                print("✅ Macro context exists for today.")
                return True
            else:
                print(f"❌ No macro context for today. Latest is from {context_date}")
                return False
        else:
            print("❌ No macro context found in database.")
            return False

if __name__ == "__main__":
    if check_macro_context():
        sys.exit(0)
    else:
        sys.exit(1)
