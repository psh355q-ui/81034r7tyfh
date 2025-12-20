import re

# Fix NewsAggregation.tsx
with open('pages/NewsAggregation.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'useEffect,\s*', '', content)
content = re.sub(r'BarChart2,\s*', '', content)
content = re.sub(r'NewsStats,\s*', '', content)
content = re.sub(r'getSentimentBgColor,\s*', '', content)
content = re.sub(r'const queryClient[^;]+;', '', content)
with open('pages/NewsAggregation.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed NewsAggregation.tsx")

# Fix RssFeedManagement.tsx
with open('pages/RssFeedManagement.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'const \[showDetails, setShowDetails\][^;]+;', '', content)
with open('pages/RssFeedManagement.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed RssFeedManagement.tsx")

# Fix Signals.tsx
with open('pages/Signals.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'const actionBg[^;]+;', '', content)
with open('pages/Signals.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed Signals.tsx")

print("All remaining files fixed!")
