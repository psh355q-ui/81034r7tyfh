"""
Telegram Chat ID 확인 스크립트

실행: python get_chat_id.py
목적: 현재 봇이 접근 가능한 모든 Chat ID 확인
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

print("\n" + "="*70)
print(" "*20 + "📱 Telegram Chat ID 확인")
print("="*70 + "\n")

token = os.getenv('TELEGRAM_BOT_TOKEN')

if not token:
    print("❌ TELEGRAM_BOT_TOKEN이 .env에 없습니다!")
    print("\n.env 파일에 추가하세요:")
    print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
    exit(1)

print(f"✅ Bot Token: {token[:20]}...\n")
print("봇의 모든 대화 조회 중...\n")

try:
    response = requests.get(f'https://api.telegram.org/bot{token}/getUpdates')
    data = response.json()
    
    if not data.get('ok'):
        print(f"❌ API 오류: {data.get('description')}")
        exit(1)
    
    updates = data.get('result', [])
    
    if not updates:
        print("⚠️ 대화 기록이 없습니다!")
        print("\n해결 방법:")
        print("  1. Telegram에서 봇에게 아무 메시지나 보내세요")
        print("  2. 그룹에 봇을 추가하고 메시지 보내세요")
        print("  3. 이 스크립트를 다시 실행하세요")
        exit(0)
    
    print(f"발견된 대화: {len(updates)}개\n")
    print("="*70)
    print(f"{'유형':<12} | {'Chat ID':<20} | {'이름/제목':<30}")
    print("="*70)
    
    seen_chats = set()
    
    for update in updates:
        if 'message' in update:
            chat = update['message']['chat']
            chat_id = chat['id']
            
            if chat_id in seen_chats:
                continue
            seen_chats.add(chat_id)
            
            chat_type = chat['type']
            name = chat.get('title') or chat.get('first_name') or 'Unknown'
            
            print(f"{chat_type:<12} | {chat_id:<20} | {name:<30}")
    
    print("="*70)
    print("\n💡 사용 방법:")
    print("\n.env 파일에 추가:")
    print("```")
    print("# 개인 대화 (private)")
    print("TELEGRAM_CHAT_ID=위의_Chat_ID")
    print("")
    print("# Commander 전용 (그룹 추천)")
    print("TELEGRAM_COMMANDER_CHAT_ID=그룹_Chat_ID")
    print("```")
    print("\n📝 추천:")
    print("  • 일반 알림: 개인 Chat (private)")
    print("  • Commander: 그룹 Chat (group/supergroup)")
    print("  • 같은 ID 사용해도 OK!")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70 + "\n")
