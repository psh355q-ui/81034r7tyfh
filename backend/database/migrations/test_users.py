"""
여러 사용자 이름으로 연결 테스트
"""
import asyncio
import asyncpg

async def test_users():
    users_to_test = [
        "postgres",
        "ai_trading_user",
        "admin",
        "root",
        "poddb",
    ]
    
    password = "wLzgEDIoOztauSbE12iAh7PDWwdhQ84D6_kT1XJQjZU"
    
    print("🔍 사용자 이름 테스트\n")
    
    for user in users_to_test:
        try:
            print(f"테스트: {user}... ", end="")
            conn = await asyncpg.connect(
                host="127.0.0.1",
                port=5432,
                user=user,
                password=password,
                database="ai_trading",
                timeout=3
            )
            print(f"✅ 성공!")
            
            # 현재 사용자 확인
            current_user = await conn.fetchval("SELECT current_user")
            version = await conn.fetchval("SELECT version()")
            print(f"   현재 사용자: {current_user}")
            print(f"   DB 버전: {version[:60]}...")
            
            await conn.close()
            return user
            
        except asyncpg.exceptions.InvalidPasswordError:
            print(f"❌ 비밀번호 오류")
        except asyncpg.exceptions.InvalidAuthorizationSpecificationError:
            print(f"❌ 사용자 없음")
        except Exception as e:
            print(f"❌ {type(e).__name__}: {str(e)[:50]}")
    
    return None

if __name__ == "__main__":
    result = asyncio.run(test_users())
    if result:
        print(f"\n✅ 올바른 사용자 이름: {result}")
    else:
        print("\n❌ 모든 사용자 이름 실패")
