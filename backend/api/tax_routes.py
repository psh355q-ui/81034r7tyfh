"""
Tax Loss Harvesting API Routes
세금 최적화 관련 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from backend.tax import (
    TaxLossHarvester,
    TaxBracket,
    Position,
    format_recommendation_report
)

router = APIRouter(prefix="/api/v1/tax", tags=["tax"])


# Pydantic Models for API
class PositionInput(BaseModel):
    """포지션 입력 모델"""
    ticker: str = Field(..., example="AAPL")
    quantity: int = Field(..., gt=0, example=100)
    purchase_price: float = Field(..., gt=0, example=150.25)
    purchase_date: str = Field(..., example="2024-01-15")
    current_price: float = Field(..., gt=0, example=120.50)
    sector: str = Field(..., example="Technology")
    industry: str = Field(default="Technology", example="Consumer Electronics")


class TaxHarvestingRequest(BaseModel):
    """Tax Loss Harvesting 요청"""
    positions: List[PositionInput]
    tax_bracket: str = Field(default="BRACKET_24", example="BRACKET_24")
    min_loss: float = Field(default=3000.0, ge=0, example=3000.0)


class AlternativeStockResponse(BaseModel):
    """대체 종목 응답"""
    ticker: str
    name: str
    sector: str
    industry: str
    correlation: float
    reason: str


class LossPositionResponse(BaseModel):
    """손실 포지션 응답"""
    ticker: str
    quantity: int
    purchase_price: float
    purchase_date: str
    current_price: float
    unrealized_loss: float
    loss_percentage: float
    days_held: int
    is_long_term: bool


class TaxHarvestingRecommendationResponse(BaseModel):
    """Tax Loss Harvesting 추천 응답"""
    loss_position: LossPositionResponse
    alternatives: List[AlternativeStockResponse]
    tax_savings: float
    harvest_date: str
    repurchase_date: str
    notes: List[str]


class TaxHarvestingResponse(BaseModel):
    """Tax Loss Harvesting 전체 응답"""
    total_positions: int
    loss_positions_count: int
    total_unrealized_loss: float
    total_tax_savings: float
    recommendations: List[TaxHarvestingRecommendationResponse]
    report: str


class SimulationRequest(BaseModel):
    """시뮬레이션 요청"""
    positions: List[PositionInput]
    tax_bracket: str = Field(default="BRACKET_24")
    target_loss: float = Field(default=10000.0, ge=0)


class SimulationResponse(BaseModel):
    """시뮬레이션 응답"""
    total_loss: float
    total_tax_savings: float
    positions_to_harvest: List[str]
    num_positions: int
    average_savings_per_position: float


class WashSaleCheckRequest(BaseModel):
    """Wash Sale 확인 요청"""
    ticker: str
    sell_date: str
    purchase_history: List[dict]  # [{"date": "2024-01-01", "quantity": 10}, ...]


class WashSaleCheckResponse(BaseModel):
    """Wash Sale 확인 응답"""
    is_violation: bool
    reason: Optional[str] = None


def get_tax_bracket(bracket_str: str) -> TaxBracket:
    """문자열을 TaxBracket enum으로 변환"""
    bracket_map = {
        "BRACKET_10": TaxBracket.BRACKET_10,
        "BRACKET_12": TaxBracket.BRACKET_12,
        "BRACKET_22": TaxBracket.BRACKET_22,
        "BRACKET_24": TaxBracket.BRACKET_24,
        "BRACKET_32": TaxBracket.BRACKET_32,
        "BRACKET_35": TaxBracket.BRACKET_35,
        "BRACKET_37": TaxBracket.BRACKET_37,
    }
    return bracket_map.get(bracket_str, TaxBracket.BRACKET_24)


def convert_position_input(pos_input: PositionInput) -> Position:
    """PositionInput을 Position 객체로 변환"""
    return Position(
        ticker=pos_input.ticker,
        quantity=pos_input.quantity,
        purchase_price=pos_input.purchase_price,
        purchase_date=datetime.fromisoformat(pos_input.purchase_date),
        current_price=pos_input.current_price,
        sector=pos_input.sector,
        industry=pos_input.industry
    )


@router.post("/harvest", response_model=TaxHarvestingResponse)
async def get_tax_harvesting_recommendations(request: TaxHarvestingRequest):
    """
    Tax Loss Harvesting 추천 받기

    사용자의 포지션을 분석하여 세금 최적화를 위한 손실 매각 추천을 생성합니다.

    - **positions**: 보유 포지션 리스트
    - **tax_bracket**: 세금 구간 (BRACKET_10 ~ BRACKET_37)
    - **min_loss**: 최소 손실 금액 ($3,000 권장)

    Returns:
        - 손실 포지션 목록
        - 대체 종목 추천
        - 예상 세금 절감액
        - Wash Sale 회피 날짜
    """
    try:
        # Tax bracket 설정
        tax_bracket = get_tax_bracket(request.tax_bracket)

        # TaxLossHarvester 초기화
        harvester = TaxLossHarvester(tax_bracket=tax_bracket)

        # 포지션 변환
        positions = [convert_position_input(pos) for pos in request.positions]

        # 추천 생성
        recommendations = harvester.generate_recommendations(
            positions=positions,
            min_loss=request.min_loss
        )

        # 응답 생성
        response_recommendations = []
        total_tax_savings = 0
        total_unrealized_loss = 0

        for rec in recommendations:
            loss_pos = rec.loss_position

            loss_pos_response = LossPositionResponse(
                ticker=loss_pos.position.ticker,
                quantity=loss_pos.position.quantity,
                purchase_price=loss_pos.position.purchase_price,
                purchase_date=loss_pos.position.purchase_date.strftime("%Y-%m-%d"),
                current_price=loss_pos.position.current_price,
                unrealized_loss=loss_pos.unrealized_loss,
                loss_percentage=loss_pos.loss_percentage,
                days_held=loss_pos.days_held,
                is_long_term=loss_pos.is_long_term
            )

            alternatives_response = [
                AlternativeStockResponse(
                    ticker=alt.ticker,
                    name=alt.name,
                    sector=alt.sector,
                    industry=alt.industry,
                    correlation=alt.correlation,
                    reason=alt.reason
                )
                for alt in rec.alternatives
            ]

            rec_response = TaxHarvestingRecommendationResponse(
                loss_position=loss_pos_response,
                alternatives=alternatives_response,
                tax_savings=rec.tax_savings,
                harvest_date=rec.harvest_date.strftime("%Y-%m-%d"),
                repurchase_date=rec.repurchase_date.strftime("%Y-%m-%d"),
                notes=rec.notes
            )

            response_recommendations.append(rec_response)
            total_tax_savings += rec.tax_savings
            total_unrealized_loss += abs(loss_pos.unrealized_loss)

        # 보고서 생성
        report = format_recommendation_report(recommendations)

        return TaxHarvestingResponse(
            total_positions=len(positions),
            loss_positions_count=len(recommendations),
            total_unrealized_loss=total_unrealized_loss,
            total_tax_savings=total_tax_savings,
            recommendations=response_recommendations,
            report=report
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_harvest_strategy(request: SimulationRequest):
    """
    Tax Loss Harvesting 전략 시뮬레이션

    목표 손실액에 도달하기 위한 최적의 포지션 조합을 시뮬레이션합니다.

    - **positions**: 보유 포지션 리스트
    - **tax_bracket**: 세금 구간
    - **target_loss**: 목표 손실액 ($10,000 권장)

    Returns:
        - 총 손실액
        - 총 세금 절감액
        - 매각할 포지션 목록
    """
    try:
        tax_bracket = get_tax_bracket(request.tax_bracket)
        harvester = TaxLossHarvester(tax_bracket=tax_bracket)

        positions = [convert_position_input(pos) for pos in request.positions]

        result = harvester.simulate_harvest_strategy(
            positions=positions,
            target_loss=request.target_loss
        )

        return SimulationResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wash-sale-check", response_model=WashSaleCheckResponse)
async def check_wash_sale(request: WashSaleCheckRequest):
    """
    Wash Sale Rule 위반 여부 확인

    특정 티커의 매각이 Wash Sale Rule을 위반하는지 확인합니다.

    - **ticker**: 티커 심볼
    - **sell_date**: 매각 날짜
    - **purchase_history**: 매수 내역 [{"date": "2024-01-01", "quantity": 10}, ...]

    Returns:
        - is_violation: 위반 여부
        - reason: 위반 사유 (위반 시)
    """
    try:
        harvester = TaxLossHarvester()

        sell_date = datetime.fromisoformat(request.sell_date)
        purchase_history = [
            (datetime.fromisoformat(p["date"]), p["quantity"])
            for p in request.purchase_history
        ]

        is_violation, reason = harvester.check_wash_sale_violation(
            ticker=request.ticker,
            sell_date=sell_date,
            purchase_history=purchase_history
        )

        return WashSaleCheckResponse(
            is_violation=is_violation,
            reason=reason
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tax-brackets")
async def get_tax_brackets():
    """
    미국 연방 소득세 구간 정보 조회

    Returns:
        세금 구간 목록 및 세율
    """
    return {
        "tax_brackets": [
            {"bracket": "BRACKET_10", "rate": 0.10, "description": "10% bracket"},
            {"bracket": "BRACKET_12", "rate": 0.12, "description": "12% bracket"},
            {"bracket": "BRACKET_22", "rate": 0.22, "description": "22% bracket"},
            {"bracket": "BRACKET_24", "rate": 0.24, "description": "24% bracket (default)"},
            {"bracket": "BRACKET_32", "rate": 0.32, "description": "32% bracket"},
            {"bracket": "BRACKET_35", "rate": 0.35, "description": "35% bracket"},
            {"bracket": "BRACKET_37", "rate": 0.37, "description": "37% bracket"},
        ],
        "notes": [
            "Short-term losses (< 1 year) offset ordinary income at your tax bracket rate",
            "Long-term losses (>= 1 year) offset long-term capital gains at 15-20% rate",
            "Maximum $3,000 per year can be deducted against ordinary income",
            "Excess losses can be carried forward to future years"
        ]
    }


@router.get("/education")
async def get_tax_education():
    """
    Tax Loss Harvesting 교육 자료

    세금 최적화에 대한 기본 정보를 제공합니다.
    """
    return {
        "title": "Tax Loss Harvesting Guide",
        "sections": [
            {
                "title": "What is Tax Loss Harvesting?",
                "content": (
                    "Tax loss harvesting is the practice of selling investments at a loss "
                    "to offset capital gains and reduce your tax liability. You can deduct up to "
                    "$3,000 per year against ordinary income, with excess losses carried forward."
                )
            },
            {
                "title": "Wash Sale Rule",
                "content": (
                    "The IRS Wash Sale Rule prohibits claiming a loss if you buy the same or "
                    "'substantially identical' security within 30 days before or after the sale. "
                    "To avoid this, consider purchasing similar but not identical alternatives."
                )
            },
            {
                "title": "Best Practices",
                "content": (
                    "1. Review your portfolio regularly for harvesting opportunities\n"
                    "2. Focus on losses of $3,000 or more for maximum benefit\n"
                    "3. Use alternative investments to maintain market exposure\n"
                    "4. Consider long-term vs short-term holding periods\n"
                    "5. Keep detailed records of all transactions"
                )
            },
            {
                "title": "Tax Rates",
                "content": (
                    "Short-term capital gains (< 1 year): Taxed at ordinary income rates (10-37%)\n"
                    "Long-term capital gains (>= 1 year): Taxed at preferential rates (0%, 15%, 20%)"
                )
            }
        ],
        "disclaimer": (
            "This information is for educational purposes only and should not be considered "
            "tax advice. Please consult with a qualified tax professional for your specific situation."
        )
    }
