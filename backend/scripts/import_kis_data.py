"""
KIS 계좌 데이터 가져오기
실제 한국투자증권 계좌의 포지션 데이터를 데이터베이스에 동기화

Usage:
    python backend/scripts/import_kis_data.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.models import TradingSignal, NewsArticle, AnalysisResult
from backend.database.repository import get_sync_session
from backend.trading.kis_client import auth, inquire_oversea_balance
import os


def import_kis_positions():
    """KIS 계좌 잔고를 데이터베이스에 저장"""

    print("=" * 80)
    print("KIS Account Data Import")
    print("=" * 80)
    print()

    # 0. KIS API 인증
    print("🔐 Authenticating with KIS API...")
    kis_env = os.getenv("KIS_ENV", "production")
    svr = "prod" if kis_env == "production" else "vps"

    if not auth(svr=svr, product="01"):
        print("❌ KIS authentication failed!")
        print("   Please check your .env file:")
        print("   - KIS_APP_KEY")
        print("   - KIS_APP_SECRET")
        print("   - KIS_ACCOUNT_NUMBER")
        print("   - KIS_ENV (production or development)")
        return

    print(f"✅ Authenticated with KIS API ({'실전' if svr == 'prod' else '모의'} mode)")
    print()

    db = get_sync_session()

    try:
        # 1. KIS API로 잔고 조회
        print("📡 Fetching account balance from KIS API...")
        balance_data = inquire_oversea_balance()

        if not balance_data or not balance_data.get("positions"):
            print("❌ No positions found in KIS account")
            print(f"   Response: {balance_data}")
            return

        positions = balance_data["positions"]
        cash = balance_data.get("cash", 0)

        print(f"✅ Found {len(positions)} positions")
        print(f"💰 Available cash: ${cash:,.2f}")
        print()

        # 2. 더미 뉴스/분석 레코드 생성 (외래키 요구사항)
        dummy_article = NewsArticle(
            title="KIS Account Sync",
            content="Positions synchronized from Korea Investment & Securities account",
            url=f"https://kis-sync/{datetime.now().timestamp()}",
            source="KIS_API",
            published_date=datetime.now(),
            crawled_at=datetime.now(),
            content_hash=f"kis_sync_{datetime.now().timestamp()}"
        )
        db.add(dummy_article)
        db.commit()
        db.refresh(dummy_article)

        dummy_analysis = AnalysisResult(
            article_id=dummy_article.id,
            analyzed_at=datetime.now(),
            model_name="kis_import",
            theme="KIS Account Synchronization",
            bull_case="Real trading positions from brokerage account",
            bear_case="Real trading positions from brokerage account"
        )
        db.add(dummy_analysis)
        db.commit()
        db.refresh(dummy_analysis)

        # 3. 기존 KIS 시그널만 삭제 (외래키 제약 회피)
        print("🗑️  Removing old KIS synced signals...")
        old_signals = db.query(TradingSignal).filter(TradingSignal.signal_type == "KIS_SYNC").count()
        if old_signals > 0:
            db.query(TradingSignal).filter(TradingSignal.signal_type == "KIS_SYNC").delete()
            db.commit()
            print(f"   Removed {old_signals} old KIS signals")

        # 4. 포지션 저장
        print("\n💾 Saving positions to database...")
        created_count = 0

        for pos in positions:
            # Remove non-ASCII characters from name
            name = str(pos.get('name', pos.get('symbol', 'Unknown')))
            name_ascii = name.encode('ascii', 'ignore').decode('ascii')

            signal = TradingSignal(
                analysis_id=dummy_analysis.id,
                ticker=pos.get("symbol", pos.get("ticker", "UNKNOWN")),
                signal_type="KIS_SYNC",
                action="BUY",
                confidence=1.0,
                reasoning=f"KIS Position: {pos.get('symbol', 'N/A')}",
                generated_at=datetime.now(),
                entry_price=pos.get("avg_price", pos.get("entry_price", 0)),
                quantity=pos.get("quantity", 0),
                exit_price=None,
                exit_date=None,
                news_summary=f"KIS: {pos.get('exchange', 'NASD')} {name_ascii}"
            )
            db.add(signal)
            created_count += 1

            print(f"  ✓ {pos.get('symbol', 'N/A'):6s} | {pos.get('quantity', 0):4d} shares @ ${pos.get('avg_price', 0):8.2f} | Current: ${pos.get('current_price', 0):8.2f} | P/L: {pos.get('yield', 0):6.2f}%")

        db.commit()

        print()
        print("=" * 80)
        print(f"✅ Successfully imported {created_count} positions from KIS")
        print("=" * 80)
        print()

        # 5. 요약 정보
        summary = balance_data.get("summary", {})
        print("📊 Account Summary:")
        print(f"  Available Cash: ${cash:,.2f}")
        print(f"  Total Positions: {created_count}")
        if summary:
            print(f"  Total Profit/Loss: ${summary.get('total_profit_loss', 0):,.2f}")
            print(f"  Total Eval Profit: ${summary.get('total_eval_profit', 0):,.2f}")
        print()

        print("Next steps:")
        print("  1. Refresh your Dashboard: http://localhost:3002/dashboard")
        print("  2. Check API: http://localhost:8001/api/portfolio")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    import_kis_positions()
