"""
Database Analysis Script - Identify Test vs Real Data

분석 항목:
1. 모든 TradingSignal 조회
2. signal_model별 분류
3. KIS 동기화 vs 테스트 데이터 구분
4. 삭제 대상 확인
"""

import asyncio
from sqlalchemy import select
from backend.database.models import TradingSignal, NewsArticle
from backend.database.repository import get_async_session

async def analyze_database():
    """데이터베이스 분석 및 리포트 생성"""
    
    async with get_async_session() as db:
        # 1. 모든 시그널 조회
        result = await db.execute(select(TradingSignal))
        signals = result.scalars().all()
        
        print("=" * 80)
        print("DATABASE ANALYSIS - Trading Signals")
        print("=" * 80)
        print(f"\nTotal Signals: {len(signals)}\n")
        
        # 2. signal_model별 분류
        model_counts = {}
        for signal in signals:
            model = signal.signal_model or "UNKNOWN"
            if model not in model_counts:
                model_counts[model] = []
            model_counts[model].append(signal)
        
        print("\n📊 Signals by Model:")
        print("-" * 80)
        for model, sigs in model_counts.items():
            print(f"\n{model}: {len(sigs)} signals")
            for sig in sigs[:5]:  # 최대 5개만 표시
                status = "ACTIVE" if sig.status == "active" else "CLOSED"
                print(f"  - {sig.ticker:6} | {sig.action:4} | ${sig.entry_price:8.2f} | {status:7} | {sig.generated_at.strftime('%Y-%m-%d')}")
            if len(sigs) > 5:
                print(f"  ... and {len(sigs) - 5} more")
        
        # 3. KIS 동기화 데이터 식별
        print("\n" + "=" * 80)
        print("KIS SYNCHRONIZED DATA")
        print("=" * 80)
        
        kis_signals = [s for s in signals if s.signal_model in ["KIS_SYNC", "KIS_API"]]
        print(f"\nKIS Signals: {len(kis_signals)}")
        for sig in kis_signals:
            print(f"  {sig.ticker:6} | ${sig.entry_price:8.2f} | Qty: {sig.quantity:4} | {sig.generated_at.strftime('%Y-%m-%d %H:%M')}")
        
        # 4. 테스트 데이터 식별
        print("\n" + "=" * 80)
        print("TEST DATA (삭제 대상)")
        print("=" * 80)
        
        test_signals = [s for s in signals if s.signal_model == "test_model"]
        print(f"\nTest Signals: {len(test_signals)}")
        for sig in test_signals:
            print(f"  {sig.ticker:6} | ${sig.entry_price:8.2f} | Qty: {sig.quantity:4} | {sig.generated_at.strftime('%Y-%m-%d %H:%M')}")
        
        # 5. 뉴스 기사 확인
        print("\n" + "=" * 80)
        print("NEWS ARTICLES")
        print("=" * 80)
        
        result = await db.execute(select(NewsArticle))
        articles = result.scalars().all()
        print(f"\nTotal Articles: {len(articles)}")
        
        test_articles = [a for a in articles if "TEST_SEED" in (a.source or "")]
        print(f"Test Articles: {len(test_articles)}")
        real_articles = len(articles) - len(test_articles)
        print(f"Real Articles: {real_articles}")
        
        # 6. 요약 및 권장사항
        print("\n" + "=" * 80)
        print("SUMMARY & RECOMMENDATIONS")
        print("=" * 80)
        
        print(f"\n✅ Real Data:")
        print(f"   - KIS Signals: {len(kis_signals)}")
        print(f"   - Real News: {real_articles}")
        
        print(f"\n⚠️  Test Data (삭제 필요):")
        print(f"   - Test Signals: {len(test_signals)}")
        print(f"   - Test News: {len(test_articles)}")
        
        if len(test_signals) > 0:
            print(f"\n🗑️  삭제 명령:")
            print(f"   DELETE FROM trading_signals WHERE signal_model = 'test_model';")
            print(f"   Expected to delete: {len(test_signals)} records")
        
        if len(test_articles) > 0:
            print(f"\n   DELETE FROM news_articles WHERE source LIKE '%TEST_SEED%';")
            print(f"   Expected to delete: {len(test_articles)} records")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(analyze_database())
