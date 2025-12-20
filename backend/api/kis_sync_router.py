"""
KIS Portfolio Sync Router
실시간 포트폴리오 동기화 및 자동 업데이트

Features:
- Manual sync endpoint (즉시 KIS 계좌 동기화)
- Webhook for trade notifications (매매 발생 시 자동 동기화)
- Scheduled auto-sync (주기적 동기화)
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any
import logging

from backend.database.models import TradingSignal, NewsArticle, AnalysisResult
from backend.database.repository import get_sync_session
from backend.trading.kis_client import auth, inquire_oversea_balance
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kis", tags=["KIS Sync"])


# Database dependency
def get_db():
    """Database session dependency"""
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


def sync_kis_portfolio_task(db: Session) -> Dict[str, Any]:
    """
    KIS 계좌 동기화 백그라운드 작업

    Returns:
        동기화 결과 딕셔너리
    """
    try:
        # 1. KIS API 인증
        kis_env = os.getenv("KIS_ENV", "production")
        svr = "prod" if kis_env == "production" else "vps"

        if not auth(svr=svr, product="01"):
            logger.error("KIS authentication failed")
            return {"success": False, "error": "Authentication failed"}

        # 2. 잔고 조회
        balance_data = inquire_oversea_balance()

        if not balance_data or not balance_data.get("positions"):
            logger.warning("No positions found in KIS account")
            return {"success": True, "positions_count": 0, "message": "No positions"}

        positions = balance_data["positions"]

        # 3. 더미 뉴스/분석 레코드 생성
        dummy_article = NewsArticle(
            title="KIS Account Sync",
            content="Auto-sync from Korea Investment & Securities",
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
            model_name="kis_sync",
            theme="KIS Account Auto-Sync",
            bull_case="Real positions from brokerage",
            bear_case="Real positions from brokerage"
        )
        db.add(dummy_analysis)
        db.commit()
        db.refresh(dummy_analysis)

        # 4. 기존 KIS 시그널 삭제
        old_count = db.query(TradingSignal).filter(
            TradingSignal.signal_type == "KIS_SYNC"
        ).delete()
        db.commit()

        # 5. 새 포지션 저장
        created_count = 0
        for pos in positions:
            name = str(pos.get('name', pos.get('symbol', 'Unknown')))
            name_ascii = name.encode('ascii', 'ignore').decode('ascii')

            signal = TradingSignal(
                analysis_id=dummy_analysis.id,
                ticker=pos.get("symbol", "UNKNOWN"),
                signal_type="KIS_SYNC",
                action="BUY",
                confidence=1.0,
                reasoning=f"KIS Position: {pos.get('symbol', 'N/A')}",
                generated_at=datetime.now(),
                entry_price=pos.get("avg_price", 0),
                quantity=pos.get("quantity", 0),
                exit_price=None,
                exit_date=None,
                news_summary=f"KIS: {pos.get('exchange', 'NASD')} {name_ascii}"
            )
            db.add(signal)
            created_count += 1

        db.commit()

        logger.info(f"KIS sync completed: {created_count} positions imported")

        return {
            "success": True,
            "positions_count": created_count,
            "removed_count": old_count,
            "cash": balance_data.get("cash", 0),
            "synced_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"KIS sync failed: {e}", exc_info=True)
        db.rollback()
        return {"success": False, "error": str(e)}


@router.post("/sync")
async def manual_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    수동 KIS 계좌 동기화

    Usage:
        POST /api/kis/sync

    Returns:
        동기화 작업 시작 메시지
    """
    # 백그라운드에서 동기화 실행
    background_tasks.add_task(sync_kis_portfolio_task, db)

    return {
        "status": "started",
        "message": "KIS portfolio sync started in background",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/sync/immediate")
async def immediate_sync(db: Session = Depends(get_db)):
    """
    즉시 KIS 계좌 동기화 (동기 방식)

    Usage:
        POST /api/kis/sync/immediate

    Returns:
        동기화 결과
    """
    result = sync_kis_portfolio_task(db)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Sync failed"))

    return result


@router.post("/webhook/trade")
async def trade_webhook(
    trade_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    KIS 거래 발생 시 웹훅 엔드포인트

    매수/매도 체결 시 자동으로 호출되어 포트폴리오 동기화

    Usage:
        POST /api/kis/webhook/trade
        Body: {
            "ticker": "AAPL",
            "action": "BUY" or "SELL",
            "quantity": 10,
            "price": 150.00,
            "timestamp": "2025-12-10T10:00:00"
        }
    """
    logger.info(f"Trade webhook received: {trade_data}")

    # 백그라운드에서 동기화 실행
    background_tasks.add_task(sync_kis_portfolio_task, db)

    return {
        "status": "received",
        "message": "Trade notification received, syncing portfolio",
        "trade": trade_data
    }


@router.get("/sync/status")
async def sync_status(db: Session = Depends(get_db)):
    """
    현재 동기화 상태 조회

    Returns:
        마지막 동기화 시간, KIS_SYNC 포지션 수 등
    """
    kis_positions = db.query(TradingSignal).filter(
        TradingSignal.signal_type == "KIS_SYNC",
        TradingSignal.exit_price.is_(None)
    ).all()

    latest_sync = None
    if kis_positions:
        latest_sync = max(p.generated_at for p in kis_positions)

    return {
        "kis_positions_count": len(kis_positions),
        "last_synced_at": latest_sync.isoformat() if latest_sync else None,
        "tickers": [p.ticker for p in kis_positions]
    }
