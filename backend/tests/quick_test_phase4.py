"""
Quick Test Runner for PHASE 4 Features
Bypasses conftest.py to avoid async SQLite issues
"""

import sys
import asyncio
from datetime import datetime


def test_fcm_router_import():
    """Test that FCM router can be imported"""
    try:
        from backend.api.fcm_router import router
        print("✅ FCM Router import successful")
        print(f"   - Router prefix: {router.prefix}")
        print(f"   - Number of routes: {len(router.routes)}")
        return True
    except Exception as e:
        print(f"❌ FCM Router import failed: {e}")
        return False


def test_fcm_model_import():
    """Test that UserFCMToken model can be imported"""
    try:
        from backend.database.models import UserFCMToken
        print("✅ UserFCMToken model import successful")
        print(f"   - Table name: {UserFCMToken.__tablename__}")
        return True
    except Exception as e:
        print(f"❌ UserFCMToken model import failed: {e}")
        return False


def test_market_data_ws_import():
    """Test that Market Data WebSocket Manager can be imported"""
    try:
        from backend.api.market_data_ws import MarketDataWebSocketManager
        print("✅ MarketDataWebSocketManager import successful")
        manager = MarketDataWebSocketManager()
        print(f"   - Initial connection count: {manager.get_connection_count()}")
        return True
    except Exception as e:
        print(f"❌ MarketDataWebSocketManager import failed: {e}")
        return False


def test_push_notification_service():
    """Test that Push Notification Service can be imported"""
    try:
        from backend.services.push_notification_service import PushNotificationService
        print("✅ PushNotificationService import successful")
        service = PushNotificationService()
        enabled = service.is_enabled()
        print(f"   - Service enabled: {enabled}")
        if not enabled:
            print("   - Note: Firebase credentials not configured (expected)")
        return True
    except Exception as e:
        print(f"❌ PushNotificationService import failed: {e}")
        return False


def test_event_subscribers():
    """Test that event subscribers can be imported"""
    try:
        from backend.events.subscribers import (
            ConflictEventSubscriber,
            PortfolioEventSubscriber,
            TradingSignalEventSubscriber
        )
        print("✅ Event Subscribers import successful")
        print(f"   - ConflictEventSubscriber: OK")
        print(f"   - PortfolioEventSubscriber: OK")
        print(f"   - TradingSignalEventSubscriber: OK")
        return True
    except Exception as e:
        print(f"❌ Event Subscribers import failed: {e}")
        return False


def test_database_connection():
    """Test database connection"""
    try:
        from sqlalchemy import create_engine, text
        import os
        
        # Use sync connection for testing
        db_url = "postgresql://postgres:Qkqhdi1!@localhost:5433/ai_trading"
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM user_fcm_tokens"))
            count = result.scalar()
            print("✅ Database connection successful")
            print(f"   - user_fcm_tokens table exists")
            print(f"   - Current row count: {count}")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("PHASE 4: Real-time Execution - Quick Test Runner")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}\n")
    
    tests = [
        ("FCM Router Import", test_fcm_router_import),
        ("UserFCMToken Model Import", test_fcm_model_import),
        ("Market Data WebSocket Import", test_market_data_ws_import),
        ("Push Notification Service", test_push_notification_service),
        ("Event Subscribers", test_event_subscribers),
        ("Database Connection", test_database_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        print("-" * 60)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
