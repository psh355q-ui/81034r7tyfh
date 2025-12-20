"""
환경 변수 확인 스크립트
.env 파일의 설정값들이 제대로 로드되는지 확인

작성일: 2025-12-15
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

print("\n" + "="*70)
print(" "*20 + "🔍 환경 변수 확인")
print("="*70 + "\n")

# 확인할 환경 변수들
env_vars = {
    '필수': [
        'DATABASE_URL',
    ],
    'Data APIs': [
        'FRED_API_KEY',
        'NEWS_API_KEY',
    ],
    'AI Models': [
        'CLAUDE_API_KEY',
        'GEMINI_API_KEY',
        'OPENAI_API_KEY',
    ],
    'Telegram': [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID',
        'TELEGRAM_COMMANDER_CHAT_ID',
    ],
    'Korean Trading': [
        'KIS_APP_KEY',
        'KIS_APP_SECRET',
        'KIS_ACCOUNT_NUMBER',
    ]
}

# 카테고리별로 확인
for category, vars_list in env_vars.items():
    print(f"{'='*70}")
    print(f"{category}")
    print(f"{'='*70}")
    
    for var in vars_list:
        value = os.getenv(var)
        if value:
            # 보안을 위해 일부만 표시
            if len(value) > 20:
                display = value[:10] + "..." + value[-5:]
            else:
                display = value[:5] + "..." if len(value) > 5 else value
            print(f"  ✅ {var:30} = {display}")
        else:
            print(f"  ❌ {var:30} = (설정 안됨)")
    print()

# 요약
print("="*70)
print("📊 요약")
print("="*70 + "\n")

total_vars = sum(len(vars_list) for vars_list in env_vars.values())
set_vars = sum(1 for vars_list in env_vars.values() for var in vars_list if os.getenv(var))

print(f"총 환경 변수: {total_vars}개")
print(f"설정된 변수: {set_vars}개")
print(f"설정률: {set_vars/total_vars*100:.1f}%\n")

# 핵심 기능별 상태
print("핵심 기능 사용 가능 여부:")
print(f"  Constitutional System: ✅ (환경 변수 불필요)")
print(f"  Yahoo Finance: ✅ (환경 변수 불필요)")
print(f"  SEC EDGAR: ✅ (환경 변수 불필요)")
print(f"  FRED API: {'✅' if os.getenv('FRED_API_KEY') else '❌ (FRED_API_KEY 필요)'}")
print(f"  Telegram Bot: {'✅' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ (TELEGRAM_BOT_TOKEN 필요)'}")
print(f"  AI Models: {'✅' if os.getenv('GEMINI_API_KEY') or os.getenv('OPENAI_API_KEY') else '❌ (AI API 키 필요)'}")
print(f"  KIS Trading: {'✅' if os.getenv('KIS_APP_KEY') else '❌ (KIS API 키 필요)'}")
print(f"  Database: {'✅' if os.getenv('DATABASE_URL') else '❌ (DATABASE_URL 필요)'}")

print("\n" + "="*70)
print()
