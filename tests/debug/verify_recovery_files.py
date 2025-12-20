import os
from pathlib import Path

# Project Root (Assumed to be where the script is run or hardcoded)
PROJECT_ROOT = Path(r"d:\code\ai-trading-system")

# List of 37 Files from Implementation Plan
FILES_TO_CHECK = [
    # 1. Backend Core
    "backend/constitution/risk_limits.py",
    "backend/constitution/allocation_rules.py",
    "backend/constitution/trading_constraints.py",
    "backend/constitution/constitution.py",
    "backend/constitution/check_integrity.py",
    "backend/ai/debate/constitutional_debate_engine.py",

    # 2. Data & Models
    "backend/data/models/proposal.py",
    "backend/data/models/shadow_trade.py",
    "backend/migrations/versions/251215_shadow_trades.py",
    "backend/migrations/versions/251215_proposals.py",

    # 3. Backtest & Reporting
    "backend/backtesting/shadow_trade_tracker.py",
    "backend/backtesting/portfolio_manager.py",
    "backend/backtesting/backtest_engine.py",
    "backend/backtesting/constitutional_backtest_engine.py",
    "backend/backtesting/performance_metrics.py",
    "backend/reporting/shield_metrics.py",
    "backend/reporting/shield_report_generator.py",

    # 4. Notifications & Live Trading
    "backend/notifications/telegram_commander_bot.py",
    "run_live_trading.py",

    # 5. Frontend
    "frontend/src/components/war-room/WarRoom.tsx",
    "frontend/src/components/war-room/WarRoom.css",
    "frontend/src/pages/WarRoomPage.tsx",
    "frontend/src/App.tsx",
    "frontend/src/components/Layout/Sidebar.tsx",
    
    # + Additional checks from previous analysis
    "backend/backtesting/signal_backtest_engine.py",
    "frontend/src/pages/BacktestDashboard.tsx"
]

def check_files():
    print("=" * 60)
    print("🔍 PROJECT FILE INTEGRITY CHECK (Phase 1)")
    print("=" * 60)
    
    missing = []
    existing = []
    
    for relative_path in FILES_TO_CHECK:
        full_path = PROJECT_ROOT / relative_path
        if full_path.exists():
            existing.append(relative_path)
            # print(f"✅ FOUND: {relative_path}")
        else:
            missing.append(relative_path)
            print(f"❌ MISSING: {relative_path}")
            
    print("-" * 60)
    print(f"Total Files Checked: {len(FILES_TO_CHECK)}")
    print(f"✅ Existing: {len(existing)}")
    print(f"❌ Missing:  {len(missing)}")
    print("=" * 60)
    
    if missing:
        print("\n[Action Required] The following files need to be restored:")
        for f in missing:
            print(f" - {f}")
    else:
        print("\nAll critical files exist! You are ready for Phase 2.")

if __name__ == "__main__":
    check_files()
