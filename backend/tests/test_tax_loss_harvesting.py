"""
Tax Loss Harvesting 테스트
"""

import pytest
from datetime import datetime, timedelta
from backend.tax import (
    TaxLossHarvester,
    TaxBracket,
    Position
)


@pytest.fixture
def sample_positions():
    """테스트용 샘플 포지션"""
    return [
        # 큰 손실 - NVDA
        Position(
            ticker="NVDA",
            quantity=100,
            purchase_price=500.0,
            purchase_date=datetime.now() - timedelta(days=200),
            current_price=400.0,  # -$10,000 손실
            sector="Technology",
            industry="Semiconductors"
        ),
        # 중간 손실 - TSLA
        Position(
            ticker="TSLA",
            quantity=50,
            purchase_price=300.0,
            purchase_date=datetime.now() - timedelta(days=100),
            current_price=240.0,  # -$3,000 손실
            sector="Technology",
            industry="Automotive"
        ),
        # 작은 손실 - AAPL (임계값 미만)
        Position(
            ticker="AAPL",
            quantity=10,
            purchase_price=180.0,
            purchase_date=datetime.now() - timedelta(days=50),
            current_price=150.0,  # -$300 손실 (너무 작음)
            sector="Technology",
            industry="Consumer Electronics"
        ),
        # 이익 - MSFT (손실 아님)
        Position(
            ticker="MSFT",
            quantity=50,
            purchase_price=300.0,
            purchase_date=datetime.now() - timedelta(days=400),
            current_price=400.0,  # +$5,000 이익
            sector="Technology",
            industry="Software"
        ),
    ]


@pytest.fixture
def harvester():
    """TaxLossHarvester 인스턴스"""
    return TaxLossHarvester(tax_bracket=TaxBracket.BRACKET_24)


def test_identify_loss_positions(harvester, sample_positions):
    """손실 포지션 식별 테스트"""
    loss_positions = harvester.identify_loss_positions(sample_positions, min_loss=3000.0)

    # NVDA와 TSLA만 포함되어야 함 (AAPL은 너무 작고, MSFT는 이익)
    assert len(loss_positions) == 2

    # 손실액이 큰 순서로 정렬되어야 함
    assert loss_positions[0].position.ticker == "NVDA"
    assert loss_positions[1].position.ticker == "TSLA"

    # 손실액 확인
    assert loss_positions[0].unrealized_loss == -10000.0
    assert loss_positions[1].unrealized_loss == -3000.0


def test_find_alternative_stocks(harvester):
    """대체 종목 찾기 테스트"""
    alternatives = harvester.find_alternative_stocks(
        ticker="NVDA",
        sector="Technology",
        industry="Semiconductors"
    )

    # 대체 종목이 있어야 함
    assert len(alternatives) > 0

    # AMD, INTC 등이 포함되어야 함
    alt_tickers = [alt.ticker for alt in alternatives]
    assert "AMD" in alt_tickers or "INTC" in alt_tickers

    # 같은 섹터여야 함
    for alt in alternatives:
        assert alt.sector == "Technology"


def test_calculate_tax_savings_short_term(harvester):
    """단기 손실 세금 절감 계산 테스트"""
    loss_amount = -5000.0
    is_long_term = False

    tax_savings, deduction, carryover = harvester.calculate_tax_savings(
        loss_amount, is_long_term
    )

    # 단기 손실: 24% 세율 적용
    # 최대 $3,000 공제
    assert deduction == 3000.0
    assert carryover == 2000.0  # 초과 손실 이월
    assert tax_savings == 3000.0 * 0.24  # $720


def test_calculate_tax_savings_long_term(harvester):
    """장기 손실 세금 절감 계산 테스트"""
    loss_amount = -4000.0
    is_long_term = True

    tax_savings, deduction, carryover = harvester.calculate_tax_savings(
        loss_amount, is_long_term
    )

    # 장기 손실: 15% 세율 적용
    # 최대 $3,000 공제
    assert deduction == 3000.0
    assert carryover == 1000.0
    assert tax_savings == 3000.0 * 0.15  # $450


def test_generate_recommendations(harvester, sample_positions):
    """추천 생성 테스트"""
    recommendations = harvester.generate_recommendations(
        positions=sample_positions,
        min_loss=3000.0
    )

    # 2개의 추천이 생성되어야 함
    assert len(recommendations) == 2

    # 각 추천에 대체 종목이 있어야 함
    for rec in recommendations:
        assert len(rec.alternatives) > 0
        assert rec.tax_savings > 0
        assert rec.repurchase_date > rec.harvest_date
        assert len(rec.notes) > 0


def test_wash_sale_violation_before_sell(harvester):
    """Wash Sale 위반 테스트 (매각 전 매수)"""
    ticker = "AAPL"
    sell_date = datetime(2024, 12, 1)

    # 매각 20일 전에 매수 (위반)
    purchase_history = [
        (datetime(2024, 11, 11), 10),  # 20일 전
    ]

    is_violation, reason = harvester.check_wash_sale_violation(
        ticker, sell_date, purchase_history
    )

    assert is_violation is True
    assert "Wash Sale violation" in reason


def test_wash_sale_violation_after_sell(harvester):
    """Wash Sale 위반 테스트 (매각 후 매수)"""
    ticker = "AAPL"
    sell_date = datetime(2024, 12, 1)

    # 매각 15일 후에 매수 (위반)
    purchase_history = [
        (datetime(2024, 12, 16), 10),  # 15일 후
    ]

    is_violation, reason = harvester.check_wash_sale_violation(
        ticker, sell_date, purchase_history
    )

    assert is_violation is True
    assert "after" in reason


def test_wash_sale_no_violation(harvester):
    """Wash Sale 위반 없음 테스트"""
    ticker = "AAPL"
    sell_date = datetime(2024, 12, 1)

    # 매각 40일 전에 매수 (위반 아님)
    purchase_history = [
        (datetime(2024, 10, 22), 10),  # 40일 전
        (datetime(2025, 1, 10), 5),    # 40일 후
    ]

    is_violation, reason = harvester.check_wash_sale_violation(
        ticker, sell_date, purchase_history
    )

    assert is_violation is False
    assert reason is None


def test_simulate_harvest_strategy(harvester, sample_positions):
    """전략 시뮬레이션 테스트"""
    result = harvester.simulate_harvest_strategy(
        positions=sample_positions,
        target_loss=10000.0
    )

    # 결과 확인
    assert result["total_loss"] >= 10000.0
    assert result["total_tax_savings"] > 0
    assert len(result["positions_to_harvest"]) > 0
    assert result["num_positions"] > 0


def test_long_term_vs_short_term(sample_positions):
    """장기/단기 보유 세금 차이 테스트"""
    # 장기 보유 (365일 이상)
    long_term_harvester = TaxLossHarvester(tax_bracket=TaxBracket.BRACKET_24)
    long_term_position = Position(
        ticker="AAPL",
        quantity=100,
        purchase_price=200.0,
        purchase_date=datetime.now() - timedelta(days=400),  # 400일 전
        current_price=170.0,  # -$3,000
        sector="Technology",
        industry="Consumer Electronics"
    )

    # 단기 보유 (365일 미만)
    short_term_position = Position(
        ticker="MSFT",
        quantity=100,
        purchase_price=200.0,
        purchase_date=datetime.now() - timedelta(days=200),  # 200일 전
        current_price=170.0,  # -$3,000
        sector="Technology",
        industry="Software"
    )

    long_recs = long_term_harvester.generate_recommendations([long_term_position])
    short_recs = long_term_harvester.generate_recommendations([short_term_position])

    # 단기 손실이 세금 절감이 더 커야 함 (24% vs 15%)
    assert short_recs[0].tax_savings > long_recs[0].tax_savings


def test_tax_bracket_impact():
    """세금 구간에 따른 절감액 차이 테스트"""
    position = Position(
        ticker="AAPL",
        quantity=100,
        purchase_price=200.0,
        purchase_date=datetime.now() - timedelta(days=100),
        current_price=170.0,  # -$3,000
        sector="Technology",
        industry="Consumer Electronics"
    )

    # 10% 세율
    harvester_10 = TaxLossHarvester(tax_bracket=TaxBracket.BRACKET_10)
    recs_10 = harvester_10.generate_recommendations([position])

    # 37% 세율
    harvester_37 = TaxLossHarvester(tax_bracket=TaxBracket.BRACKET_37)
    recs_37 = harvester_37.generate_recommendations([position])

    # 37% 세율이 더 큰 절감액을 가져야 함
    assert recs_37[0].tax_savings > recs_10[0].tax_savings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
