"""Fix all .query() calls in analytics files"""
import re

files = [
    'backend/analytics/trade_analytics.py',
    'backend/analytics/risk_analytics.py',
]

for filepath in files:
    print(f"Fixing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Count how many .query( we have
    count_before = content.count('.query(')

    # Replace all variations of .query()
    # Pattern 1: self.db.query(Model).filter(...).all()
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*self\.db\.query\(([^)]+)\)\.filter\((.*?)\)\.all\(\)',
        r'\1stmt = select(\3).where(\n\1    \4\n\1)\n\1result = await self.db.execute(stmt)\n\1\2 = result.scalars().all()',
        content,
        flags=re.DOTALL
    )

    # Pattern 2: self.db.query(Model).filter(...).first()
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*self\.db\.query\(([^)]+)\)\.filter\((.*?)\)\.first\(\)',
        r'\1stmt = select(\3).where(\n\1    \4\n\1)\n\1result = await self.db.execute(stmt)\n\1\2 = result.scalars().first()',
        content,
        flags=re.DOTALL
    )

    # Pattern 3: self.db.query(Model).all()
    content = re.sub(
        r'(\s+)(\w+)\s*=\s*self\.db\.query\(([^)]+)\)\.all\(\)',
        r'\1stmt = select(\3)\n\1result = await self.db.execute(stmt)\n\1\2 = result.scalars().all()',
        content
    )

    count_after = content.count('.query(')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  Fixed {count_before - count_after} .query() calls (remaining: {count_after})")

print("\nDone!")
