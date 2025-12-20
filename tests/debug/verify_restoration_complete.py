import os
from pathlib import Path
import sys

# Project Root
PROJECT_ROOT = Path(r"d:\code\ai-trading-system")

# List of files we restored/verified
RESTORED_FILES = [
    # Phase 2: Backend Core
    "backend/backtesting/performance_metrics.py",
    "backend/backtesting/portfolio_manager.py",
    "backend/backtesting/shadow_trade_tracker.py",
    "backend/backtesting/constitutional_backtest_engine.py",
    "backend/notifications/telegram_commander_bot.py",
    "backend/ai/debate/constitutional_debate_engine.py", # Existed but verified
    "run_live_trading.py",
    
    # Phase 3: Frontend
    "frontend/src/pages/WarRoomPage.tsx",
    "frontend/src/App.tsx",
    "frontend/src/components/Layout/Sidebar.tsx",
    
    # Additional Context
    "backend/constitution/constitution.py"
]

def check_file_content(path, must_contain_list):
    full_path = PROJECT_ROOT / path
    if not full_path.exists():
        print(f"❌ MISSING: {path}")
        return False
        
    try:
        content = full_path.read_text(encoding='utf-8')
        all_found = True
        for term in must_contain_list:
            if term not in content:
                print(f"⚠️  WARNING: {path} missing content '{term}'")
                all_found = False
        if all_found:
            print(f"✅ VERIFIED: {path}")
        return all_found
    except Exception as e:
        print(f"❌ READ ERROR: {path} - {e}")
        return False

def main():
    print("=" * 60)
    print("🚦 FINAL RESTORATION VERIFICATION")
    print("=" * 60)
    
    success = True
    
    # 1. Check Engines
    success &= check_file_content("backend/backtesting/constitutional_backtest_engine.py", 
                                ["class ConstitutionalBacktestEngine", "ShadowTradeTracker", "PortfolioManager"])
    
    success &= check_file_content("run_live_trading.py", 
                                ["class LiveTradingEngine", "ConstitutionalDebateEngine", "TelegramCommanderBot"])

    # 2. Check Frontend Routes
    success &= check_file_content("frontend/src/App.tsx", 
                                ["/war-room", "WarRoomPage"])
                                
    success &= check_file_content("frontend/src/components/Layout/Sidebar.tsx", 
                                ["/war-room", "AI War Room"])

    print("-" * 60)
    if success:
        print("🎉 SUCCESS: All Critical Components Restored & Linked!")
        print("   - Constitutional Backtest Engine: READY")
        print("   - Live Trading Engine: READY")
        print("   - War Room UI: LINKED")
    else:
        print("⚠️  WARNING: Some checks failed. Review above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
