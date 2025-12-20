"""
Port 5541 PostgreSQL 연결 테스트 (.env 설정 그대로)
"""
import asyncio
import asyncpg

async def test_5541():
    password = "wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU"
    users = ["postgres", "ai_trading_user", "admin"]
    
    print("🔍 Port 5541 PostgreSQL 테스트\n")
    
    for user in users:
        try:
            print(f"테스트: {user}@localhost:5541... ", end="")
            conn = await asyncpg.connect(
                host="localhost",
                port=5541,
                user=user,
                password=password,
                database="ai_trading",
                timeout=3
            )
            print(f"✅ 성공!")
            
            current_user = await conn.fetchval("SELECT current_user")
            version = await conn.fetchval("SELECT version()")
            print(f"   현재 사용자: {current_user}")
            print(f"   DB 버전: {version[:60]}...")
            
            await conn.close()
            return user
            
        except Exception as e:
            print(f"❌ {type(e).__name__}")
    
    return None

if __name__ == "__main__":
    result = asyncio.run(test_5541())
    if result:
        print(f"\n✅ Port 5541에서 연결 성공! 사용자: {result}")
        print("👉 .env 파일이 port 5541을 사용하도록 설정되어 있습니다.")
    else:
        print("\n❌ Port 5541 연결 실패")
