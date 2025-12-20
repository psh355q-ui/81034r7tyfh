"""
Fix Database Error Handling in main.py
DB 연결이 없을 때 빈 데이터를 반환하도록 수정
"""

import re

# Read the file
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.content()

# Backup
with open('main.py.backup', 'w', encoding='utf-8') as f:
    f.write(content)

# Add try-except to get_signals function (line ~392)
pattern1 = r'(@app\.get\("/api/signals".*?\n)(async def get_recent_signals\(.*?\n\):\n    """.*?""")'
replacement1 = r'\1\2\n    try:'

# Add except block before the return statement
# This is more complex, so we'll do it manually

print("Please manually add try-except blocks to the following functions:")
print("1. get_recent_signals (line ~392)")
print("2. get_signal_detail (line ~454)")
print("3. get_signal_stats (line ~553)")
print("4. get_performance_stats (line ~601)")
print("\nExample pattern:")
print("""
try:
    # existing code
    return response
except Exception as e:
    logging.error(f"Error: {e}")
    return empty_response
""")
