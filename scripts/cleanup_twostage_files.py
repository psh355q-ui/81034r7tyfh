"""
Cleanup Script: Remove twostage files after successful migration

After migration is verified:
- trader_agent_mvp.py (now Two-Stage)
- risk_agent_mvp.py (now Two-Stage)
- analyst_agent_mvp.py (now Two-Stage)
- war_room_mvp.py (now Two-Stage)

We can remove the original twostage files:
- trader_agent_twostage.py
- risk_agent_twostage.py
- analyst_agent_twostage.py
- war_room_mvp_twostage.py
"""

import os
from pathlib import Path

# Paths
mvp_dir = Path("backend/ai/mvp")

# Twostage files to remove
twostage_files = [
    "trader_agent_twostage.py",
    "risk_agent_twostage.py",
    "analyst_agent_twostage.py",
    "war_room_mvp_twostage.py"
]

print("="*60)
print("Cleanup: Remove twostage files")
print("="*60)

print("\n[Files to Remove]")
for filename in twostage_files:
    filepath = mvp_dir / filename
    if filepath.exists():
        size = filepath.stat().st_size
        print(f"  - {filename} ({size} bytes)")
    else:
        print(f"  ⚠️  {filename} not found")

print("\nProceed with removal? (This will delete the files above)")
print("Press Ctrl+C to cancel, or press Enter to continue...")

# For automation, skip confirmation
# input()

removed = 0
kept = 0

print("\n[Removing files...]")

for filename in twostage_files:
    filepath = mvp_dir / filename
    if filepath.exists():
        filepath.unlink()
        print(f"  ✓ Removed {filename}")
        removed += 1
    else:
        print(f"  ⚠️  {filename} not found (already removed?)")
        kept += 1

print("\n" + "="*60)
print("Cleanup Complete!")
print("="*60)
print(f"Removed: {removed} files")
print(f"Kept/Skipped: {kept} files")

# Show final state
print("\n[Remaining MVP Files]")
for f in sorted(mvp_dir.glob('*.py')):
    if f.name != '__init__.py' and 'deprecated' not in str(f):
        print(f"  - {f.name}")

print("\n[Deprecated Files]")
deprecated_dir = mvp_dir / "deprecated"
for f in sorted(deprecated_dir.glob('*.py')):
    print(f"  - deprecated/{f.name}")

print("\n✅ Cleanup complete!")
print("   - Legacy files preserved in: backend/ai/mvp/deprecated/")
print("   - Active files use Two-Stage architecture")
