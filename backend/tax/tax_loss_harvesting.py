"""
Tax Loss Harvesting Module
세금 최적화를 위한 손실 포지션 매각 및 대체 종목 추천

주요 기능:
1. 손실 포지션 식별 ($3,000 이상 손실)
2. Wash Sale Rule 회피 (30일 규칙)
3. 유사 종목 추천 (같은 섹터, 다른 티커)
4. 세금 절감 시뮬레이션
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaxBracket(Enum):
    """미국 연방 소득세 구간"""
    BRACKET_10 = 0.10
    BRACKET_12 = 0.12
    BRACKET_22 = 0.22
    BRACKET_24 = 0.24
    BRACKET_32 = 0.32
    BRACKET_35 = 0.35
    BRACKET_37 = 0.37


@dataclass
class Position:
    """포지션 정보"""
    ticker: str
    quantity: int
    purchase_price: float
    purchase_date: datetime
    current_price: float
    sector: str
    industry: str


@dataclass
class LossPosition:
    """손실 포지션"""
    position: Position
    unrealized_loss: float
    loss_percentage: float
    days_held: int
    is_long_term: bool  # 1년 이상 보유


@dataclass
class AlternativeStock:
    """대체 종목"""
    ticker: str
    name: str
    sector: str
    industry: str
    correlation: float  # 원본 종목과의 상관계수
    reason: str


@dataclass
class TaxHarvestingRecommendation:
    """Tax Loss Harvesting 추천"""
    loss_position: LossPosition
    alternatives: List[AlternativeStock]
    tax_savings: float
    harvest_date: datetime
    repurchase_date: datetime  # Wash Sale 회피 날짜
    notes: List[str]


class TaxLossHarvester:
    """Tax Loss Harvesting 엔진"""

    # Wash Sale Rule: 매각 전후 30일 이내 동일 종목 매수 금지
    WASH_SALE_DAYS = 30

    # 최소 손실 금액 ($3,000 이상 권장)
    MIN_LOSS_THRESHOLD = 3000.0

    # 장기/단기 보유 기준 (365일)
    LONG_TERM_HOLDING_DAYS = 365

    # 섹터별 대체 종목 매핑
    ALTERNATIVE_STOCKS = {
        "Technology": {
            "AAPL": ["MSFT", "GOOGL", "META", "NVDA"],
            "MSFT": ["AAPL", "GOOGL", "AMZN", "ORCL"],
            "NVDA": ["AMD", "INTC", "QCOM", "AVGO"],
            "TSLA": ["RIVN", "LCID", "NIO", "F"],
            "META": ["GOOGL", "SNAP", "PINS", "TWTR"],
        },
        "Healthcare": {
            "JNJ": ["PFE", "ABBV", "MRK", "LLY"],
            "UNH": ["CVS", "CI", "HUM", "ANTM"],
        },
        "Finance": {
            "JPM": ["BAC", "WFC", "C", "GS"],
            "V": ["MA", "AXP", "PYPL", "SQ"],
        },
        "Consumer": {
            "AMZN": ["WMT", "TGT", "COST", "HD"],
            "COST": ["WMT", "TGT", "DLTR", "DG"],
        },
        "Energy": {
            "XOM": ["CVX", "COP", "SLB", "EOG"],
            "CVX": ["XOM", "BP", "SHEL", "TTE"],
        }
    }

    def __init__(self, tax_bracket: TaxBracket = TaxBracket.BRACKET_24):
        self.tax_bracket = tax_bracket
        self.logger = logging.getLogger(__name__)

    def identify_loss_positions(
        self,
        positions: List[Position],
        min_loss: float = MIN_LOSS_THRESHOLD
    ) -> List[LossPosition]:
        """
        손실 포지션 식별

        Args:
            positions: 전체 포지션 리스트
            min_loss: 최소 손실 금액 ($3,000 권장)

        Returns:
            손실 포지션 리스트
        """
        loss_positions = []

        for position in positions:
            unrealized_loss = self._calculate_unrealized_loss(position)

            # 손실이 최소 임계값 이상인 경우만
            if unrealized_loss <= -min_loss:
                loss_percentage = (unrealized_loss / (position.purchase_price * position.quantity)) * 100
                days_held = (datetime.now() - position.purchase_date).days
                is_long_term = days_held >= self.LONG_TERM_HOLDING_DAYS

                loss_pos = LossPosition(
                    position=position,
                    unrealized_loss=unrealized_loss,
                    loss_percentage=loss_percentage,
                    days_held=days_held,
                    is_long_term=is_long_term
                )

                loss_positions.append(loss_pos)

                self.logger.info(
                    f"Loss position identified: {position.ticker} "
                    f"- ${unrealized_loss:.2f} ({loss_percentage:.2f}%)"
                )

        # 손실액이 큰 순서로 정렬
        loss_positions.sort(key=lambda x: x.unrealized_loss)

        return loss_positions

    def _calculate_unrealized_loss(self, position: Position) -> float:
        """미실현 손익 계산"""
        cost_basis = position.purchase_price * position.quantity
        current_value = position.current_price * position.quantity
        return current_value - cost_basis

    def find_alternative_stocks(
        self,
        ticker: str,
        sector: str,
        industry: str
    ) -> List[AlternativeStock]:
        """
        Wash Sale Rule을 회피하기 위한 대체 종목 찾기

        Args:
            ticker: 원본 티커
            sector: 섹터
            industry: 산업

        Returns:
            대체 종목 리스트
        """
        alternatives = []

        # 1. 미리 정의된 대체 종목 사용
        if sector in self.ALTERNATIVE_STOCKS:
            if ticker in self.ALTERNATIVE_STOCKS[sector]:
                predefined = self.ALTERNATIVE_STOCKS[sector][ticker]
                for alt_ticker in predefined:
                    alternatives.append(AlternativeStock(
                        ticker=alt_ticker,
                        name=self._get_stock_name(alt_ticker),
                        sector=sector,
                        industry=industry,
                        correlation=0.85,  # 예상 상관계수
                        reason=f"Same sector ({sector}), high correlation"
                    ))

        # 2. 섹터 ETF 추천 (최후의 수단)
        if not alternatives:
            etf_map = {
                "Technology": "XLK",
                "Healthcare": "XLV",
                "Finance": "XLF",
                "Consumer": "XLY",
                "Energy": "XLE",
            }

            if sector in etf_map:
                alternatives.append(AlternativeStock(
                    ticker=etf_map[sector],
                    name=f"{sector} Select Sector SPDR Fund",
                    sector=sector,
                    industry="ETF",
                    correlation=0.90,
                    reason=f"Sector ETF - maintains {sector} exposure"
                ))

        return alternatives[:5]  # 최대 5개 추천

    def _get_stock_name(self, ticker: str) -> str:
        """티커 심볼로 회사 이름 가져오기 (간단한 매핑)"""
        name_map = {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc.",
            "NVDA": "NVIDIA Corporation",
            "TSLA": "Tesla Inc.",
            "META": "Meta Platforms Inc.",
            "AMZN": "Amazon.com Inc.",
            "JPM": "JPMorgan Chase & Co.",
            "V": "Visa Inc.",
            "MA": "Mastercard Inc.",
            "AMD": "Advanced Micro Devices",
            "INTC": "Intel Corporation",
        }
        return name_map.get(ticker, ticker)

    def calculate_tax_savings(
        self,
        loss_amount: float,
        is_long_term: bool,
        ordinary_income: float = 0
    ) -> Tuple[float, float, float]:
        """
        세금 절감액 계산

        미국 세법 기준:
        - 단기 손실 (< 1년): Ordinary income과 상쇄 가능
        - 장기 손실 (>= 1년): Long-term capital gains과 상쇄
        - 최대 $3,000까지 ordinary income 공제 가능
        - 초과 손실은 이월 가능

        Args:
            loss_amount: 손실액 (음수)
            is_long_term: 장기 보유 여부
            ordinary_income: 일반 소득 (선택)

        Returns:
            (세금 절감액, 이번 연도 공제액, 이월 손실액)
        """
        loss_amount = abs(loss_amount)  # 양수로 변환

        # 이번 연도 최대 공제액: $3,000
        max_deduction = 3000.0
        current_year_deduction = min(loss_amount, max_deduction)
        carryover_loss = max(0, loss_amount - max_deduction)

        # 세금 절감액 계산
        if is_long_term:
            # 장기 자본 손실: 15% ~ 20% 절감 (보수적으로 15% 사용)
            tax_rate = 0.15
        else:
            # 단기 자본 손실: 일반 소득세율 적용
            tax_rate = self.tax_bracket.value

        tax_savings = current_year_deduction * tax_rate

        self.logger.info(
            f"Tax savings calculated: ${tax_savings:.2f} "
            f"(Deduction: ${current_year_deduction:.2f}, "
            f"Carryover: ${carryover_loss:.2f})"
        )

        return tax_savings, current_year_deduction, carryover_loss

    def generate_recommendations(
        self,
        positions: List[Position],
        min_loss: float = MIN_LOSS_THRESHOLD
    ) -> List[TaxHarvestingRecommendation]:
        """
        Tax Loss Harvesting 추천 생성

        Args:
            positions: 전체 포지션 리스트
            min_loss: 최소 손실 금액

        Returns:
            추천 리스트
        """
        recommendations = []

        # 1. 손실 포지션 식별
        loss_positions = self.identify_loss_positions(positions, min_loss)

        if not loss_positions:
            self.logger.info("No loss positions found for tax harvesting")
            return recommendations

        # 2. 각 손실 포지션에 대한 추천 생성
        for loss_pos in loss_positions:
            position = loss_pos.position

            # 대체 종목 찾기
            alternatives = self.find_alternative_stocks(
                position.ticker,
                position.sector,
                position.industry
            )

            # 세금 절감액 계산
            tax_savings, deduction, carryover = self.calculate_tax_savings(
                loss_pos.unrealized_loss,
                loss_pos.is_long_term
            )

            # Wash Sale 회피 날짜 계산
            harvest_date = datetime.now()
            repurchase_date = harvest_date + timedelta(days=self.WASH_SALE_DAYS + 1)

            # 추천 노트
            notes = []
            notes.append(f"Unrealized loss: ${abs(loss_pos.unrealized_loss):,.2f}")
            notes.append(f"Tax savings: ${tax_savings:,.2f}")
            notes.append(f"Holding period: {loss_pos.days_held} days ({'long-term' if loss_pos.is_long_term else 'short-term'})")
            notes.append(f"Repurchase allowed after: {repurchase_date.strftime('%Y-%m-%d')}")

            if carryover > 0:
                notes.append(f"Carryover loss: ${carryover:,.2f}")

            if len(alternatives) > 0:
                notes.append(f"Recommended alternatives: {', '.join([a.ticker for a in alternatives[:3]])}")
            else:
                notes.append("⚠️ No suitable alternatives found - consider sector ETF")

            recommendation = TaxHarvestingRecommendation(
                loss_position=loss_pos,
                alternatives=alternatives,
                tax_savings=tax_savings,
                harvest_date=harvest_date,
                repurchase_date=repurchase_date,
                notes=notes
            )

            recommendations.append(recommendation)

        return recommendations

    def check_wash_sale_violation(
        self,
        ticker: str,
        sell_date: datetime,
        purchase_history: List[Tuple[datetime, int]]  # (date, quantity)
    ) -> Tuple[bool, Optional[str]]:
        """
        Wash Sale Rule 위반 여부 확인

        Args:
            ticker: 티커 심볼
            sell_date: 매각 날짜
            purchase_history: 매수 내역 [(날짜, 수량), ...]

        Returns:
            (위반 여부, 위반 사유)
        """
        wash_sale_start = sell_date - timedelta(days=self.WASH_SALE_DAYS)
        wash_sale_end = sell_date + timedelta(days=self.WASH_SALE_DAYS)

        for purchase_date, quantity in purchase_history:
            if wash_sale_start <= purchase_date <= wash_sale_end and purchase_date != sell_date:
                days_diff = abs((purchase_date - sell_date).days)
                reason = (
                    f"Wash Sale violation detected: {ticker} purchased "
                    f"{days_diff} days {'before' if purchase_date < sell_date else 'after'} sell date. "
                    f"Loss deduction will be disallowed."
                )
                return True, reason

        return False, None

    def simulate_harvest_strategy(
        self,
        positions: List[Position],
        target_loss: float = 10000.0
    ) -> Dict:
        """
        Tax Loss Harvesting 전략 시뮬레이션

        Args:
            positions: 전체 포지션
            target_loss: 목표 손실액 ($10,000 목표)

        Returns:
            시뮬레이션 결과
        """
        recommendations = self.generate_recommendations(positions)

        total_loss = 0
        total_tax_savings = 0
        selected_positions = []

        for rec in recommendations:
            if total_loss >= target_loss:
                break

            total_loss += abs(rec.loss_position.unrealized_loss)
            total_tax_savings += rec.tax_savings
            selected_positions.append(rec.loss_position.position.ticker)

        result = {
            "total_loss": total_loss,
            "total_tax_savings": total_tax_savings,
            "positions_to_harvest": selected_positions,
            "num_positions": len(selected_positions),
            "average_savings_per_position": total_tax_savings / len(selected_positions) if selected_positions else 0
        }

        return result


def format_recommendation_report(recommendations: List[TaxHarvestingRecommendation]) -> str:
    """추천 내용을 보기 좋게 포맷팅"""
    if not recommendations:
        return "No tax loss harvesting opportunities found."

    report = []
    report.append("=" * 80)
    report.append("TAX LOSS HARVESTING RECOMMENDATIONS")
    report.append("=" * 80)
    report.append("")

    total_savings = sum(rec.tax_savings for rec in recommendations)
    total_loss = sum(abs(rec.loss_position.unrealized_loss) for rec in recommendations)

    report.append(f"Total Potential Tax Savings: ${total_savings:,.2f}")
    report.append(f"Total Unrealized Losses: ${total_loss:,.2f}")
    report.append(f"Number of Positions: {len(recommendations)}")
    report.append("")
    report.append("-" * 80)

    for i, rec in enumerate(recommendations, 1):
        pos = rec.loss_position.position
        report.append(f"\n{i}. {pos.ticker} - {pos.sector}")
        report.append(f"   Purchase: {pos.purchase_date.strftime('%Y-%m-%d')} @ ${pos.purchase_price:.2f}")
        report.append(f"   Current:  ${pos.current_price:.2f} ({rec.loss_position.loss_percentage:.2f}%)")
        report.append(f"   Loss:     ${abs(rec.loss_position.unrealized_loss):,.2f}")
        report.append(f"   Tax Savings: ${rec.tax_savings:,.2f}")
        report.append("")
        report.append("   Alternative Stocks:")
        for alt in rec.alternatives[:3]:
            report.append(f"   • {alt.ticker} - {alt.name}")
            report.append(f"     Reason: {alt.reason}")
        report.append("")
        report.append("   Notes:")
        for note in rec.notes:
            report.append(f"   • {note}")
        report.append("-" * 80)

    return "\n".join(report)
