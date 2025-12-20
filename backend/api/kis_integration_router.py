"""
KIS Integration Router - Phase A/B/C/D + 한국투자증권 통합

전체 파이프라인 실행 후 KIS 실제 주문 실행:
Security → Phase A → Phase C → Phase B → KIS Order

작성일: 2025-12-03
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import os

# Phase Integration Router
from backend.api.phase_integration_router import (
    NewsAnalysisRequest,
    FullPipelineResponse,
    full_pipeline_analysis
)

# Load .env explicitly
from dotenv import load_dotenv
load_dotenv()

# KIS Broker
try:
    from backend.brokers.kis_broker import KISBroker, KIS_AVAILABLE
    KIS_BROKER_AVAILABLE = KIS_AVAILABLE
except ImportError:
    KISBroker = None
    KIS_BROKER_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kis", tags=["KIS Integration"])


# ============================================================================
# Request/Response Models
# ============================================================================

class KISAutoTradeRequest(BaseModel):
    """KIS 자동매매 요청"""
    headline: str
    body: str = ""
    url: Optional[str] = None

    # KIS 설정
    account_no: Optional[str] = None  # None이면 환경변수에서 읽기
    is_virtual: Optional[bool] = None  # None이면 환경변수 설정 따름
    dry_run: bool = False  # True이면 분석만 하고 실제 주문 안 함


class KISOrderResult(BaseModel):
    """KIS 주문 결과"""
    success: bool
    symbol: str
    side: str  # BUY/SELL
    quantity: int
    order_type: str  # MARKET/LIMIT
    status: str
    message: Optional[str] = None
    kis_response: Optional[Dict] = None


class KISAutoTradeResponse(BaseModel):
    """KIS 자동매매 응답"""
    # Phase 파이프라인 분석 결과
    analysis: FullPipelineResponse

    # KIS 주문 실행 결과
    kis_enabled: bool
    kis_order_executed: bool
    kis_order_result: Optional[KISOrderResult] = None

    # 메타데이터
    timestamp: str
    mode: str  # "VIRTUAL" or "REAL"


class KISBalanceResponse(BaseModel):
    """KIS 계좌 잔고 응답"""
    total_value: float
    cash: float
    positions: List[Dict[str, Any]]
    broker: str
    mode: str
    account: str


# ============================================================================
# KIS Broker 초기화
# ============================================================================


# 환경변수에서 기본 모드 로드
KIS_ENV = os.environ.get("KIS_ENV", "sandbox").lower()
DEFAULT_IS_VIRTUAL = KIS_ENV != "production"

def get_kis_broker(account_no: Optional[str] = None, is_virtual: Optional[bool] = None) -> KISBroker:
    """
    KIS Broker 인스턴스 생성

    Args:
        account_no: 계좌번호 (None이면 환경변수에서 읽기)
        is_virtual: 모의투자 여부 (None이면 환경변수 기본값 사용)

    Returns:
        KISBroker 인스턴스
    """
    if not KIS_BROKER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="KIS API가 사용 불가능합니다. KIS API 경로를 확인하세요."
        )

    # 기본값 설정
    if is_virtual is None:
        is_virtual = DEFAULT_IS_VIRTUAL

    # 계좌번호 설정
    if account_no is None:
        account_no = os.getenv("KIS_ACCOUNT_NUMBER", "")
        if not account_no:
            raise HTTPException(
                status_code=400,
                detail="계좌번호가 설정되지 않았습니다. KIS_ACCOUNT_NUMBER 환경변수를 확인하세요."
            )

    # Broker 초기화
    try:
        broker = KISBroker(
            account_no=account_no,
            product_code="01",  # 종합계좌
            is_virtual=is_virtual
        )
        return broker

    except Exception as e:
        logger.error(f"KIS Broker 초기화 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"KIS Broker 초기화 실패: {str(e)}"
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/auto-trade", response_model=KISAutoTradeResponse)
async def kis_auto_trade(request: KISAutoTradeRequest):
    """
    전체 파이프라인 + KIS 자동매매

    Pipeline:
    1. Security: URL/Text 검증
    2. Phase A: 뉴스 세그먼트 분류
    3. Phase C: AI 3-way 토론 + 편향 탐지
    4. Phase B: PERI/Buffett Index + Signal to Order
    5. KIS: 실제 주문 실행
    """
    logger.info(f"KIS Auto Trade 시작 (is_virtual={request.is_virtual}, dry_run={request.dry_run})")

    try:
        # ========================================
        # Step 1: Phase 파이프라인 실행
        # ========================================
        news_request = NewsAnalysisRequest(
            headline=request.headline,
            body=request.body,
            url=request.url
        )

        analysis = await full_pipeline_analysis(news_request)

        logger.info(f"Phase 분석 완료: {analysis.final_ticker} {analysis.final_action}")

        # ========================================
        # Step 2: KIS 주문 실행 여부 판단
        # ========================================
        should_execute_order = (
            KIS_BROKER_AVAILABLE and
            analysis.order_created and
            not request.dry_run
        )

        kis_order_result = None

        if should_execute_order:
            # KIS Broker 초기화
            broker = get_kis_broker(
                account_no=request.account_no,
                is_virtual=request.is_virtual
            )

            logger.info(f"KIS 주문 실행: {analysis.order_side} {analysis.final_ticker} x{analysis.order_quantity}")

            # 주문 실행
            if analysis.order_side == "buy":
                kis_response = broker.buy_market_order(
                    symbol=analysis.final_ticker,
                    quantity=analysis.order_quantity,
                    exchange="NASDAQ"  # TODO: 거래소 자동 감지
                )
            elif analysis.order_side == "sell":
                kis_response = broker.sell_market_order(
                    symbol=analysis.final_ticker,
                    quantity=analysis.order_quantity,
                    exchange="NASDAQ"
                )
            else:
                kis_response = None

            # 주문 결과 파싱
            if kis_response:
                kis_order_result = KISOrderResult(
                    success=True,
                    symbol=kis_response["symbol"],
                    side=kis_response["side"],
                    quantity=kis_response["quantity"],
                    order_type=kis_response["order_type"],
                    status=kis_response["status"],
                    kis_response=kis_response.get("result")
                )
                logger.info(f"KIS 주문 성공: {kis_order_result.symbol} {kis_order_result.side}")
            else:
                logger.error(f"KIS 주문 실패")

        # ========================================
        # Step 3: 응답 생성
        # ========================================
        return KISAutoTradeResponse(
            analysis=analysis,
            kis_enabled=KIS_BROKER_AVAILABLE,
            kis_order_executed=kis_order_result is not None,
            kis_order_result=kis_order_result,
            timestamp=datetime.now().isoformat(),
            mode="VIRTUAL" if request.is_virtual else "REAL"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"KIS Auto Trade 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance", response_model=KISBalanceResponse)
async def get_kis_balance(
    account_no: Optional[str] = None,
    is_virtual: Optional[bool] = None
):
    """
    KIS 계좌 잔고 조회
    """
    try:
        broker = get_kis_broker(account_no=account_no, is_virtual=is_virtual)

        balance = broker.get_account_balance()
        if not balance:
            raise HTTPException(status_code=500, detail="잔고 조회 실패")

        broker_info = broker.get_info()

        return KISBalanceResponse(
            total_value=balance.get("total_value", 0),
            cash=balance.get("cash", 0),
            positions=balance.get("positions", []),
            broker=broker_info["broker"],
            mode=broker_info["mode"],
            account=broker_info["account"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"잔고 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/price/{symbol}")
async def get_kis_price(
    symbol: str,
    exchange: str = "NASDAQ",
    account_no: Optional[str] = None,
    is_virtual: Optional[bool] = None
):
    """
    KIS 실시간 시세 조회
    """
    try:
        broker = get_kis_broker(account_no=account_no, is_virtual=is_virtual)

        price_info = broker.get_price(symbol=symbol, exchange=exchange)
        if not price_info:
            raise HTTPException(status_code=404, detail=f"{symbol} 시세 조회 실패")

        return price_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시세 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def kis_health_check():
    """KIS 연동 상태 확인"""
    return {
        "kis_available": KIS_BROKER_AVAILABLE,
        "status": "OK" if KIS_BROKER_AVAILABLE else "KIS API NOT AVAILABLE",
        "message": "KIS Open Trading API 연동 정상" if KIS_BROKER_AVAILABLE else "KIS_API_PATH 확인 필요",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/manual-order")
async def manual_order(
    symbol: str,
    side: str,  # "BUY" or "SELL"
    quantity: int,
    exchange: str = "NASDAQ",
    account_no: Optional[str] = None,
    is_virtual: Optional[bool] = None
):
    """
    수동 주문 (Phase 파이프라인 없이 직접 주문)

    테스트 용도로 사용
    """
    if not KIS_BROKER_AVAILABLE:
        raise HTTPException(status_code=503, detail="KIS API 사용 불가")

    try:
        broker = get_kis_broker(account_no=account_no, is_virtual=is_virtual)

        if side.upper() == "BUY":
            result = broker.buy_market_order(symbol, quantity, exchange)
        elif side.upper() == "SELL":
            result = broker.sell_market_order(symbol, quantity, exchange)
        else:
            raise HTTPException(status_code=400, detail="side는 BUY 또는 SELL이어야 합니다")

        if not result:
            raise HTTPException(status_code=500, detail="주문 실패")

        return {
            "success": True,
            "order": result,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"수동 주문 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 통계 및 모니터링
# ============================================================================

@router.get("/stats")
async def kis_stats():
    """KIS 통합 통계"""
    return {
        "integration": {
            "kis_available": KIS_BROKER_AVAILABLE,
            "phase_a_modules": 5,
            "phase_b_modules": 4,
            "phase_c_modules": 3,
            "security_modules": 4,
            "total_modules": 16
        },
        "features": {
            "security_validation": True,
            "news_classification": True,
            "ai_debate": True,
            "bias_detection": True,
            "macro_risk_analysis": True,
            "kis_order_execution": KIS_BROKER_AVAILABLE
        },
        "status": "READY" if KIS_BROKER_AVAILABLE else "KIS_NOT_CONFIGURED",
        "timestamp": datetime.now().isoformat()
    }
