"""
간단한 Telegram 테스트
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# 직접 telegram_notifier 코드 사용
async def test_send_message():
    import aiohttp
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("❌ Telegram credentials not configured")
        return False
    
    print("=" * 80)
    print("Telegram Simple Test")
    print("=" * 80)
    print(f"\n✅ Bot Token: {bot_token[:10]}...")
    print(f"✅ Chat ID: {chat_id}")
    
    # Send test message
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    message = """
<b>🧪 Telegram Test Message</b>

This is a test message from AI Trading System.

Kill Switch Telegram integration is working!

<code>⏰ 2026-01-03 15:40:00</code>
""".strip()
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    print("\n📡 Sending test message...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    print("✅ Message sent successfully!")
                    print("\n📱 Check your Telegram app!")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Failed to send: {response.status}")
                    print(f"Response: {text}")
                    return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_send_message())
    
    print("\n" + "=" * 80)
    if success:
        print("✅ Telegram integration working!")
    else:
        print("❌ Telegram integration failed")
    print("=" * 80)
