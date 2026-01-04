
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.secrets_manager import SecretsManager

def migrate():
    """Migrate .env to encrypted secrets"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return

    print(f"📂 Loading {env_file}...")
    load_dotenv(env_file)

    # Important keys to migrate
    target_keys = [
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "KIS_APP_KEY",
        "KIS_APP_SECRET",
        "KIS_ACCOUNT_NUMBER",
        "DATABASE_URL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SLACK_WEBHOOK_URL",
        "SERPAPI_API_KEY",
        "NEWS_API_KEY"
    ]

    secrets = {}
    print("\n🔍 Scanning for secrets...")
    
    for key in target_keys:
        val = os.getenv(key)
        if val:
            secrets[key] = val
            print(f"   ✅ Found: {key}")
        else:
            print(f"   ⚠️  Missing: {key}")

    if not secrets:
        print("\n❌ No secrets found to migrate.")
        return

    print(f"\n🔐 Encrypting {len(secrets)} secrets...")
    manager = SecretsManager()
    manager.encrypt_secrets(secrets)

    print("\n✅ Migration Complete!")
    print(f"   Secrets file: {manager.secrets_file}")
    print(f"   Key file:     {manager.key_file}")
    print("\n⚠️  IMPORTANT:")
    print("   1. Add '.secrets.key' and '.secrets.enc' to .gitignore")
    print("   2. Keep '.secrets.key' SAFE (Back it up!)")
    print("   3. You can now use 'backend.config.secrets_manager.get_secret' to access these values.")

if __name__ == "__main__":
    migrate()
