"""
Telegram Bot 직접 연결 테스트
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

async def test_telegram():
    from backend.notifications.telegram_notifier import create_telegram_notifier
    
    print("=" * 80)
    print("Telegram Bot Direct Connection Test")
    print("=" * 80)
    
    # 1. Create notifier
    print("\n1. Creating Telegram Notifier...")
    telegram = create_telegram_notifier()
    
    if not telegram:
        print("   ❌ Failed to create Telegram notifier")
        print("   Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return
    
    print("   ✅ Notifier created successfully")
    print(f"   Enabled: {telegram.enabled}")
    print(f"   Chat ID: {telegram.chat_id[:10]}...")
    
    # 2. Test connection
    print("\n2. Testing connection...")
    try:
        success = await telegram.test_connection()
        if success:
            print("   ✅ Connection test successful!")
            print("   📱 Check your Telegram for test message")
        else:
            print("   ❌ Connection test failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Send Kill Switch alert
    print("\n3. Sending Kill Switch Alert...")
    try:
        success = await telegram.send_kill_switch_alert(
            reason="manual",
            daily_loss_pct=-3.5,
            threshold_pct=5.0
        )
        
        if success:
            print("   ✅ Kill Switch alert sent!")
            print("   📱 Check your Telegram for the alert message")
        else:
            print("   ❌ Failed to send alert")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Get stats
    print("\n4. Notification Stats:")
    stats = telegram.get_stats()
    print(f"   Total sent: {stats['total_sent']}")
    print(f"   Total failed: {stats['total_failed']}")
    print(f"   Messages in last hour: {stats['messages_last_hour']}")
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_telegram())
