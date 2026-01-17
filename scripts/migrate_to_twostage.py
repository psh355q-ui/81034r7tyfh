"""
Migration Script: Move legacy agents to deprecated/ and replace with Two-Stage

This script:
1. Moves legacy MVP agents to backend/ai/mvp/deprecated/
2. Replaces them with Two-Stage versions
3. Preserves original filenames for backward compatibility
"""

import os
import shutil
from pathlib import Path

# Paths
mvp_dir = Path("backend/ai/mvp")
deprecated_dir = mvp_dir / "deprecated"

# Create deprecated directory if not exists
deprecated_dir.mkdir(exist_ok=True)

print("="*60)
print("Two-Stage Migration: Legacy → Deprecated")
print("="*60)

# Legacy files to move to deprecated/
legacy_files = [
    "trader_agent_mvp.py",
    "risk_agent_mvp.py",
    "analyst_agent_mvp.py",
    "war_room_mvp.py"
]

# Two-Stage files to replace with (will be renamed to legacy names)
twostage_files = {
    "trader_agent_mvp.py": "trader_agent_twostage.py",
    "risk_agent_mvp.py": "risk_agent_twostage.py",
    "analyst_agent_mvp.py": "analyst_agent_twostage.py",
    "war_room_mvp.py": "war_room_mvp_twostage.py"
}

# Step 1: Move legacy files to deprecated/
print("\n[Step 1] Moving legacy files to deprecated/...")

for filename in legacy_files:
    source = mvp_dir / filename
    target = deprecated_dir / filename

    if source.exists():
        if target.exists():
            print(f"  ⚠️  {filename} already in deprecated/, skipping")
        else:
            shutil.move(str(source), str(target))
            print(f"  ✓ Moved {filename} → deprecated/{filename}")
    else:
        print(f"  ⚠️  {filename} not found, skipping")

# Step 2: Copy Two-Stage files to original names
print("\n[Step 2] Replacing with Two-Stage versions...")

for legacy_name, twostage_name in twostage_files.items():
    source = mvp_dir / twostage_name
    target = mvp_dir / legacy_name

    if not source.exists():
        print(f"  ❌ {twostage_name} not found!")
        continue

    if target.exists():
        print(f"  ⚠️  {legacy_name} already exists (unexpected!)")
        # Backup existing file
        backup = mvp_dir / f"{legacy_name}.backup"
        shutil.move(str(target), str(backup))
        print(f"  → Backed up to {legacy_name}.backup")

    # Copy Two-Stage file to original name
    shutil.copy(str(source), str(target))
    print(f"  ✓ Copied {twostage_name} → {legacy_name}")

# Step 3: Remove original twostage files (optional - keep for now)
print("\n[Step 3] Keeping original twostage files for reference...")
print("  (Can remove manually if migration is successful)")

print("\n" + "="*60)
print("Migration Complete!")
print("="*60)

# Show final state
print("\n[Final State]")
print(f"deprecated/ folder has {len(list(deprecated_dir.glob('*.py')))} files")
print(f"mvp/ folder has {len(list(mvp_dir.glob('*.py')))} files")

print("\n[Legacy Files in deprecated/]")
for f in sorted(deprecated_dir.glob('*.py')):
    print(f"  - {f.name}")

print("\n[Active MVP Files]")
for f in sorted(mvp_dir.glob('*.py')):
    if f.name != '__init__.py' and 'twostage' not in f.name and 'deprecated' not in f.name:
        print(f"  - {f.name}")

print("\n✅ Migration complete. You can now:")
print("   1. Test the system with: python backend/tests/test_warroom_twostage.py")
print("   2. If working, delete twostage files: rm backend/ai/mvp/*_twostage.py")
print("   3. If issues, restore from: backend/ai/mvp/deprecated/")
