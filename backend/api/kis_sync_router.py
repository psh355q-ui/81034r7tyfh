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

from backend.database.models import TradingSignal, NewsArticle, AnalysisResult, PositionOwnership
from backend.database.repository import get_sync_session
from backend.brokers.kis_broker import KISBroker
import os
from backend.ai.skills.common.logging_decorator import log_endpoint

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


def sync_kis_portfolio_task(db: Session, default_persona_mode: str = "long_term") -> Dict[str, Any]:
    """
    KIS 계좌 동기화 백그라운드 작업
    
    Args:
        db: Database session
        default_persona_mode: 새 포지션의 기본 전략 (long_term, trading, dividend, aggressive)

    Returns:
        동기화 결과 딕셔너리
    """
    from backend.database.repository_multi_strategy import (
        PositionOwnershipRepository,
        StrategyRepository
    )
    
    try:
        # 1. KIS Broker를 통해 포트폴리오 조회
        broker = KISBroker()
        portfolio_data = broker.get_portfolio()
        
        if not portfolio_data or not portfolio_data.get("positions"):
            logger.warning("No positions found in KIS account")
            return {"success": True, "positions_count": 0, "message": "No positions"}

        positions = portfolio_data["positions"]
        kis_tickers = set(pos.get("symbol", "").upper() for pos in positions if pos.get("symbol"))

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

        # 6. 소유권 자동 동기화 (NEW)
        ownership_repo = PositionOwnershipRepository(session=db)
        strategy_repo = StrategyRepository(session=db)
        
        # 기본 전략 조회 (사용자의 현재 persona mode)
        default_strategy = strategy_repo.get_by_name(default_persona_mode)
        if not default_strategy:
            # Fallback: long_term 전략 생성
            logger.warning(f"Strategy '{default_persona_mode}' not found, creating it")
            default_strategy = strategy_repo.create(
                name=default_persona_mode,
                display_name="장기 투자" if default_persona_mode == "long_term" else default_persona_mode.replace("_", " ").title(),
                persona_type=default_persona_mode,
                priority=100 if default_persona_mode == "long_term" else 80,
                time_horizon="long" if default_persona_mode == "long_term" else "medium"
            )
            db.commit()
        
        ownership_created = 0
        ownership_skipped = 0
        ownership_removed = 0
        
        # 6a. 새 포지션에 대해 소유권 생성
        for pos in positions:
            ticker = pos.get("symbol", "").upper()
            if not ticker:
                continue
                
            # 기존 소유권 확인
            existing = ownership_repo.get_primary_ownership(ticker)
            if existing:
                ownership_skipped += 1
                logger.debug(f"Ownership already exists for {ticker}, skipping")
                continue
            
            # 새 소유권 생성
            try:
                ownership_repo.acquire_ownership(
                    strategy_id=default_strategy.id,
                    ticker=ticker,
                    ownership_type="primary",
                    lock_duration_days=None,  # 잠금 없음
                    reasoning=f"Auto-assigned from KIS sync (persona: {default_persona_mode})"
                )
                ownership_created += 1
                logger.info(f"Created ownership for {ticker} -> {default_persona_mode}")
            except Exception as e:
                logger.warning(f"Failed to create ownership for {ticker}: {e}")
        
        # 6b. 매도된 포지션의 소유권 해제
        all_ownerships = db.query(PositionOwnership).all()
        for ownership in all_ownerships:
            if ownership.ticker not in kis_tickers:
                # KIS에 없는 포지션 = 매도됨
                ownership_repo.release_ownership(ownership.ticker, ownership.strategy_id)
                ownership_removed += 1
                logger.info(f"Released ownership for sold position: {ownership.ticker}")
        
        db.commit()

        logger.info(f"KIS sync completed: {created_count} positions, ownership: +{ownership_created} ={ownership_skipped} -{ownership_removed}")

        return {
            "success": True,
            "positions_count": created_count,
            "removed_count": old_count,
            "cash": portfolio_data.get("cash", 0),
            "synced_at": datetime.now().isoformat(),
            "ownership": {
                "created": ownership_created,
                "skipped": ownership_skipped,
                "removed": ownership_removed
            }
        }

    except Exception as e:
        logger.error(f"KIS sync failed: {e}", exc_info=True)
        db.rollback()
        return {"success": False, "error": str(e)}


@router.post("/sync")
@log_endpoint("kis", "system")
async def manual_sync(
    background_tasks: BackgroundTasks,
    persona_mode: str = "long_term",
    db: Session = Depends(get_db)
):
    """
    수동 KIS 계좌 동기화

    Usage:
        POST /api/kis/sync?persona_mode=long_term

    Args:
        persona_mode: 새 포지션에 할당할 기본 전략 (long_term, trading, dividend, aggressive)

    Returns:
        동기화 작업 시작 메시지
    """
    # 백그라운드에서 동기화 실행 (persona_mode 전달)
    background_tasks.add_task(sync_kis_portfolio_task, db, persona_mode)

    return {
        "status": "started",
        "message": f"KIS portfolio sync started in background (default strategy: {persona_mode})",
        "timestamp": datetime.now().isoformat(),
        "persona_mode": persona_mode
    }


@router.post("/sync/immediate")
@log_endpoint("kis", "system")
async def immediate_sync(
    persona_mode: str = "long_term",
    db: Session = Depends(get_db)
):
    """
    즉시 KIS 계좌 동기화 (동기 방식)

    Usage:
        POST /api/kis/sync/immediate?persona_mode=long_term

    Args:
        persona_mode: 새 포지션에 할당할 기본 전략 (long_term, trading, dividend, aggressive)

    Returns:
        동기화 결과 (ownership 생성/삭제 정보 포함)
    """
    result = sync_kis_portfolio_task(db, persona_mode)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Sync failed"))

    return result


@router.post("/webhook/trade")
@log_endpoint("kis", "system")
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
@log_endpoint("kis", "system")
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
