import re

# Fix CostDashboard.tsx
with open('components/CostDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'setRefreshInterval\b', '_setRefreshInterval', content)
with open('components/CostDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed CostDashboard.tsx")

# Fix GeminiFreePopup.tsx
with open('components/GeminiFree/GeminiFreePopup.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'MessageSquare,\s*', '', content)
content = re.sub(r'BarChart2,\s*', '', content)
content = re.sub(r'const getUsageColor[^;]+;', '', content)
with open('components/GeminiFree/GeminiFreePopup.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed GeminiFreePopup.tsx")

# Fix NewsRiskFilter.tsx
with open('components/NewsRiskFilter.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'TrendingDown,\s*', '', content)
content = re.sub(r'Check,\s*', '', content)
with open('components/NewsRiskFilter.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed NewsRiskFilter.tsx")

# Fix InteractivePortfolio.tsx
with open('components/Portfolio/InteractivePortfolio.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'useRef,\s*', '', content)
with open('components/Portfolio/InteractivePortfolio.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed InteractivePortfolio.tsx")

# Fix SECSemanticSearch.tsx
with open('components/SECSemanticSearch.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'ExternalLink,\s*', '', content)
with open('components/SECSemanticSearch.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed SECSemanticSearch.tsx")

# Fix BacktestDashboard.tsx
with open('pages/BacktestDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'useEffect,\s*', '', content)
with open('pages/BacktestDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed BacktestDashboard.tsx")

# Fix Logs.tsx
with open('pages/Logs.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
content = re.sub(r'Trash2,\s*', '', content)
content = re.sub(r'LogEntry,\s*', '', content)
content = re.sub(r'variant="ghost"', 'variant="secondary"', content)
with open('pages/Logs.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed Logs.tsx")

print("All files fixed!")
