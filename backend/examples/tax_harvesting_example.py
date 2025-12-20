"""
Tax Loss Harvesting 사용 예시
"""

from datetime import datetime, timedelta
from backend.tax import (
    TaxLossHarvester,
    TaxBracket,
    Position,
    format_recommendation_report
)


def example_1_basic_usage():
    """기본 사용 예시"""
    print("=" * 80)
    print("Example 1: Basic Tax Loss Harvesting")
    print("=" * 80)

    # 1. TaxLossHarvester 초기화 (24% 세율)
    harvester = TaxLossHarvester(tax_bracket=TaxBracket.BRACKET_24)

    # 2. 포지션 정의
    positions = [
        Position(
            ticker="NVDA",
            quantity=100,
            purchase_price=500.0,
            purchase_date=datetime.now() - timedelta(days=200),
            current_price=400.0,  # -$10,000 손실
            sector="Technology",
            industry="Semiconductors"
        ),
        Position(
            ticker="TSLA",
            quantity=50,
            purchase_price=300.0,
            purchase_date=datetime.now() - timedelta(days=100),
            current_price=240.0,  # -$3,000 손실
            sector="Technology",
            industry="Automotive"
        ),
    ]

    # 3. 추천 생성
    recommendations = harvester.generate_recommendations(positions)

    # 4. 결과 출력
    report = format_recommendation_report(recommendations)
    print(report)


def example_2_wash_sale_check():
    """Wash Sale Rule 확인 예시"""
    print("\n" + "=" * 80)
    print("Example 2: Wash Sale Rule Check")
    print("=" * 80)

    harvester = TaxLossHarvester()

    # AAPL을 12월 1일에 매각
    ticker = "AAPL"
    sell_date = datetime(2024, 12, 1)

    # 매수 내역
    purchase_history = [
        (datetime(2024, 11, 15), 50),   # 16일 전 매수 (위반!)
        (datetime(2024, 10, 1), 30),    # 61일 전 매수 (OK)
    ]

    is_violation, reason = harvester.check_wash_sale_violation(
        ticker, sell_date, purchase_history
    )

    print(f"\nTicker: {ticker}")
    print(f"Sell Date: {sell_date.strftime('%Y-%m-%d')}")
    print(f"\nPurchase History:")
    for date, qty in purchase_history:
        days_diff = abs((date - sell_date).days)
        print(f"  - {date.strftime('%Y-%m-%d')}: {qty} shares ({days_diff} days before sell)")

    print(f"\nWash Sale Violation: {'YES' if is_violation else 'NO'}")
    if reason:
        print(f"Reason: {reason}")


def example_3_simulation():
    """전략 시뮬레이션 예시"""
    print("\n" + "=" * 80)
    print("Example 3: Strategy Simulation")
    print("=" * 80)

    harvester = TaxLossHarvester(tax_bracket=TaxBracket.BRACKET_24)

    # 여러 손실 포지션
    positions = [
        Position(
            ticker="NVDA",
            quantity=100,
            purchase_price=500.0,
            purchase_date=datetime.now() - timedelta(days=200),
            current_price=400.0,  # -$10,000
            sector="Technology",
            industry="Semiconductors"
        ),
        Position(
            ticker="TSLA",
            quantity=50,
            purchase_price=300.0,
            purchase_date=datetime.now() - timedelta(days=100),
            current_price=240.0,  # -$3,000
            sector="Technology",
            industry="Automotive"
        ),
        Position(
            ticker="META",
            quantity=40,
            purchase_price=350.0,
            purchase_date=datetime.now() - timedelta(days=150),
            current_price=280.0,  # -$2,800
            sector="Technology",
            industry="Social Media"
        ),
    ]

    # 목표 손실액: $10,000
    result = harvester.simulate_harvest_strategy(positions, target_loss=10000.0)

    print(f"\nTarget Loss: $10,000")
    print(f"Actual Loss: ${result['total_loss']:,.2f}")
    print(f"Tax Savings: ${result['total_tax_savings']:,.2f}")
    print(f"Positions to Harvest: {', '.join(result['positions_to_harvest'])}")
    print(f"Number of Positions: {result['num_positions']}")
    print(f"Average Savings per Position: ${result['average_savings_per_position']:,.2f}")


def example_4_alternative_stocks():
    """대체 종목 찾기 예시"""
    print("\n" + "=" * 80)
    print("Example 4: Finding Alternative Stocks")
    print("=" * 80)

    harvester = TaxLossHarvester()

    # NVDA의 대체 종목 찾기
    alternatives = harvester.find_alternative_stocks(
        ticker="NVDA",
        sector="Technology",
        industry="Semiconductors"
    )

    print("\nOriginal Stock: NVDA (NVIDIA)")
    print(f"Sector: Technology")
    print(f"\nAlternative Stocks (to avoid Wash Sale):")
    for i, alt in enumerate(alternatives, 1):
        print(f"\n{i}. {alt.ticker} - {alt.name}")
        print(f"   Sector: {alt.sector}")
        print(f"   Correlation: {alt.correlation:.2f}")
        print(f"   Reason: {alt.reason}")


def example_5_tax_bracket_comparison():
    """세금 구간별 비교 예시"""
    print("\n" + "=" * 80)
    print("Example 5: Tax Bracket Comparison")
    print("=" * 80)

    # 동일한 손실 포지션
    position = Position(
        ticker="AAPL",
        quantity=100,
        purchase_price=200.0,
        purchase_date=datetime.now() - timedelta(days=100),
        current_price=170.0,  # -$3,000
        sector="Technology",
        industry="Consumer Electronics"
    )

    # 여러 세금 구간에서 계산
    tax_brackets = [
        TaxBracket.BRACKET_10,
        TaxBracket.BRACKET_22,
        TaxBracket.BRACKET_24,
        TaxBracket.BRACKET_37,
    ]

    print("\nLoss Position: AAPL -$3,000")
    print(f"Holding Period: 100 days (short-term)")
    print("\nTax Savings by Bracket:")

    for bracket in tax_brackets:
        harvester = TaxLossHarvester(tax_bracket=bracket)
        tax_savings, deduction, carryover = harvester.calculate_tax_savings(
            loss_amount=-3000.0,
            is_long_term=False
        )

        print(f"  {bracket.name}: ${tax_savings:,.2f} ({bracket.value * 100:.0f}% rate)")


def example_6_long_term_vs_short_term():
    """장기/단기 보유 비교 예시"""
    print("\n" + "=" * 80)
    print("Example 6: Long-term vs Short-term Holding")
    print("=" * 80)

    harvester = TaxLossHarvester(tax_bracket=TaxBracket.BRACKET_24)

    # 단기 보유 (200일)
    short_term = Position(
        ticker="AAPL",
        quantity=100,
        purchase_price=200.0,
        purchase_date=datetime.now() - timedelta(days=200),
        current_price=170.0,  # -$3,000
        sector="Technology",
        industry="Consumer Electronics"
    )

    # 장기 보유 (400일)
    long_term = Position(
        ticker="MSFT",
        quantity=100,
        purchase_price=200.0,
        purchase_date=datetime.now() - timedelta(days=400),
        current_price=170.0,  # -$3,000
        sector="Technology",
        industry="Software"
    )

    # 단기 계산
    short_tax_savings, _, _ = harvester.calculate_tax_savings(-3000.0, is_long_term=False)

    # 장기 계산
    long_tax_savings, _, _ = harvester.calculate_tax_savings(-3000.0, is_long_term=True)

    print("\nSame Loss Amount: -$3,000")
    print("\nShort-term (<1 year, 200 days):")
    print(f"  Tax Rate: 24% (ordinary income)")
    print(f"  Tax Savings: ${short_tax_savings:,.2f}")

    print("\nLong-term (>=1 year, 400 days):")
    print(f"  Tax Rate: 15% (long-term capital gains)")
    print(f"  Tax Savings: ${long_tax_savings:,.2f}")

    print(f"\nDifference: ${short_tax_savings - long_tax_savings:,.2f}")
    print("💡 Short-term losses provide higher tax savings!")


def example_7_real_world_scenario():
    """실제 시나리오 예시"""
    print("\n" + "=" * 80)
    print("Example 7: Real-world Scenario")
    print("=" * 80)

    print("\nScenario: End of year tax optimization")
    print("Current Date: December 10, 2024")
    print("Tax Bracket: 24%")
    print("\nPortfolio:")

    harvester = TaxLossHarvester(tax_bracket=TaxBracket.BRACKET_24)

    positions = [
        Position(
            ticker="NVDA",
            quantity=50,
            purchase_price=600.0,
            purchase_date=datetime(2024, 3, 15),
            current_price=480.0,  # -$6,000 (20% loss)
            sector="Technology",
            industry="Semiconductors"
        ),
        Position(
            ticker="TSLA",
            quantity=30,
            purchase_price=280.0,
            purchase_date=datetime(2024, 6, 1),
            current_price=240.0,  # -$1,200 (14% loss)
            sector="Technology",
            industry="Automotive"
        ),
        Position(
            ticker="AAPL",
            quantity=100,
            purchase_price=180.0,
            purchase_date=datetime(2023, 1, 10),
            current_price=195.0,  # +$1,500 (8% gain)
            sector="Technology",
            industry="Consumer Electronics"
        ),
    ]

    print("\n1. NVDA: 50 shares @ $600 → $480 (-$6,000, -20%)")
    print("   Purchase: 2024-03-15 (270 days ago)")

    print("\n2. TSLA: 30 shares @ $280 → $240 (-$1,200, -14%)")
    print("   Purchase: 2024-06-01 (192 days ago)")

    print("\n3. AAPL: 100 shares @ $180 → $195 (+$1,500, +8%)")
    print("   Purchase: 2023-01-10 (699 days ago)")

    print("\n" + "-" * 80)

    # 추천 생성
    recommendations = harvester.generate_recommendations(positions, min_loss=1000.0)

    print(f"\nRecommendations: {len(recommendations)} positions for tax loss harvesting")

    total_loss = 0
    total_savings = 0

    for i, rec in enumerate(recommendations, 1):
        pos = rec.loss_position.position
        print(f"\n{i}. {pos.ticker}:")
        print(f"   Loss: ${abs(rec.loss_position.unrealized_loss):,.2f}")
        print(f"   Tax Savings: ${rec.tax_savings:,.2f}")
        print(f"   Holding: {rec.loss_position.days_held} days ({'long-term' if rec.loss_position.is_long_term else 'short-term'})")
        print(f"   Alternatives: {', '.join([a.ticker for a in rec.alternatives[:3]])}")
        print(f"   Repurchase Date: {rec.repurchase_date.strftime('%Y-%m-%d')}")

        total_loss += abs(rec.loss_position.unrealized_loss)
        total_savings += rec.tax_savings

    print("\n" + "=" * 80)
    print(f"Total Unrealized Loss: ${total_loss:,.2f}")
    print(f"Total Tax Savings: ${total_savings:,.2f}")
    print("=" * 80)


if __name__ == "__main__":
    example_1_basic_usage()
    example_2_wash_sale_check()
    example_3_simulation()
    example_4_alternative_stocks()
    example_5_tax_bracket_comparison()
    example_6_long_term_vs_short_term()
    example_7_real_world_scenario()

    print("\n\n💡 Note: This is for educational purposes only.")
    print("Please consult with a tax professional for your specific situation.")
