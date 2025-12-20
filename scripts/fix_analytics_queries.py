"""
Fix SQLAlchemy 2.0 async queries in analytics modules
"""
import re

files = [
    'backend/analytics/performance_attribution.py',
    'backend/analytics/risk_analytics.py',
    'backend/analytics/trade_analytics.py',
]

for filepath in files:
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace imports
    content = content.replace('from sqlalchemy.orm import Session', 'from sqlalchemy.ext.asyncio import AsyncSession')
    if 'from sqlalchemy import func' in content and 'select' not in content:
        content = content.replace('from sqlalchemy import func', 'from sqlalchemy import func, select')

    # Replace Session type hint
    content = content.replace('db_session: Session', 'db_session: AsyncSession')

    # Replace .query().filter().all() pattern
    pattern = r'(\s+)(\w+)\s*=\s*self\.db\.query\((\w+)\)\.filter\((.*?)\)\.all\(\)'

    def replace_query(match):
        indent = match.group(1)
        var_name = match.group(2)
        model = match.group(3)
        conditions = match.group(4)

        return f'''{indent}stmt = select({model}).where(
{indent}    {conditions}
{indent})
{indent}result = await self.db.execute(stmt)
{indent}{var_name} = result.scalars().all()'''

    content = re.sub(pattern, replace_query, content, flags=re.DOTALL)

    # Replace .query().filter().first() pattern
    pattern = r'(\s+)(\w+)\s*=\s*self\.db\.query\((\w+)\)\.filter\((.*?)\)\.first\(\)'

    def replace_query_first(match):
        indent = match.group(1)
        var_name = match.group(2)
        model = match.group(3)
        conditions = match.group(4)

        return f'''{indent}stmt = select({model}).where(
{indent}    {conditions}
{indent})
{indent}result = await self.db.execute(stmt)
{indent}{var_name} = result.scalars().first()'''

    content = re.sub(pattern, replace_query_first, content, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  ✓ Fixed {filepath}")

print("\nAll analytics modules have been updated for SQLAlchemy 2.0 async!")
