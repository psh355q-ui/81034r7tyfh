"""
Phase E 전체 통합 테스트

Consensus Engine + DCA Strategy + Position Tracking 연동 테스트

작성일: 2025-12-06
"""

import asyncio
import sys


async def full_integration_test():
    """전체 통합 테스트 실행"""
    from backend.data.position_tracker import get_position_tracker
    from backend.ai.consensus import get_consensus_engine
    from backend.schemas.base_schema import MarketContext, NewsFeatures, MarketSegment, MarketRegime

    print('=' * 80)
    print('Phase E Full Integration Test: Consensus + DCA + Position Tracking')
    print('=' * 80)

    # 1. 초기 포지션 생성
    print('\n[Step 1] Creating initial position: NVDA @ $150')
    print('-' * 80)

    tracker = get_position_tracker(data_dir='backend/data/integration_test')

    try:
        pos = tracker.create_position(
            ticker='NVDA',
            company_name='NVIDIA',
            initial_price=150.0,
            initial_amount=10000.0,
            reasoning='Initial entry - AI market leader'
        )
        print(f'[OK] Position created: {pos.total_shares:.2f} shares @ ${pos.avg_entry_price:.2f}')
        print(f'     Total invested: ${pos.total_invested:.2f}')
    except ValueError:
        print('[OK] Position already exists, using existing')
        pos = tracker.get_position('NVDA')

    # 2. 가격 하락 후 DCA 평가 (1차: -10%)
    print('\n[Step 2] 1st DCA Evaluation: Price drops to $135 (-10%)')
    print('-' * 80)

    context = MarketContext(
        ticker='NVDA',
        company_name='NVIDIA',
        news=NewsFeatures(
            headline='NVIDIA Q3 results meet expectations despite market volatility',
            segment=MarketSegment.TRAINING,
            sentiment=0.4
        ),
        market_regime=MarketRegime.SIDEWAYS
    )

    engine = get_consensus_engine()

    result1 = await engine.evaluate_dca(
        ticker='NVDA',
        current_price=135.0,
        avg_entry_price=pos.avg_entry_price,
        dca_count=pos.dca_count,
        total_invested=pos.total_invested,
        context=context
    )

    print(f'DCA Strategy: {"RECOMMENDED" if result1["dca_recommended"] else "NOT RECOMMENDED"}')
    print(f'Consensus: {"APPROVED" if result1["consensus_approved"] else "REJECTED"}')
    print(f'Final Decision: {result1["final_decision"]}')

    if result1.get('approval_details'):
        details = result1['approval_details']
        print(f'Votes: {details["votes"]} (requirement: {details["requirement"]})')
        print(f'Consensus Strength: {details["consensus_strength"]}')

    # 3. Consensus 승인 시 Position에 DCA 추가
    if result1['final_decision'] == 'APPROVED':
        print('\n[Step 3] DCA Approved -> Updating Position')
        print('-' * 80)

        tracker.add_dca_entry(
            ticker='NVDA',
            price=135.0,
            amount=5000.0,
            reasoning=result1['dca_decision'].reasoning
        )

        pos = tracker.get_position('NVDA')
        print(f'[OK] Position updated:')
        print(f'     Shares: {pos.total_shares:.2f}')
        print(f'     Avg Price: ${pos.avg_entry_price:.2f}')
        print(f'     Total Invested: ${pos.total_invested:.2f}')
        print(f'     DCA Count: {pos.dca_count}')
    else:
        print('\n[Step 3] DCA Rejected -> Position Unchanged')
        print('-' * 80)
        if result1.get('dca_decision'):
            print(f'Rejection reason: {result1["dca_decision"].reasoning}')

    # 4. 추가 하락 후 2차 DCA 평가 (-20%)
    print('\n[Step 4] 2nd DCA Evaluation: Price drops to $120 (-20%)')
    print('-' * 80)

    pos = tracker.get_position('NVDA')

    context2 = MarketContext(
        ticker='NVDA',
        company_name='NVIDIA',
        news=NewsFeatures(
            headline='NVIDIA maintains strong data center demand',
            segment=MarketSegment.TRAINING,
            sentiment=0.5
        ),
        market_regime=MarketRegime.SIDEWAYS
    )

    result2 = await engine.evaluate_dca(
        ticker='NVDA',
        current_price=120.0,
        avg_entry_price=pos.avg_entry_price,
        dca_count=pos.dca_count,
        total_invested=pos.total_invested,
        context=context2
    )

    print(f'DCA Strategy: {"RECOMMENDED" if result2["dca_recommended"] else "NOT RECOMMENDED"}')
    print(f'Consensus: {"APPROVED" if result2["consensus_approved"] else "REJECTED"}')
    print(f'Final Decision: {result2["final_decision"]}')

    if result2['final_decision'] == 'APPROVED':
        tracker.add_dca_entry(
            ticker='NVDA',
            price=120.0,
            amount=3300.0,
            reasoning=result2['dca_decision'].reasoning
        )
        print('[OK] 2nd DCA executed')

    # 5. 최종 포트폴리오 상태
    print('\n[Step 5] Final Portfolio Status')
    print('-' * 80)

    pos = tracker.get_position('NVDA')
    current_price = 125.0
    pnl = pos.get_unrealized_pnl(current_price)

    print(f'Position Summary:')
    print(f'  Total Shares: {pos.total_shares:.2f}')
    print(f'  Avg Entry Price: ${pos.avg_entry_price:.2f}')
    print(f'  Total Invested: ${pos.total_invested:.2f}')
    print(f'  DCA Count: {pos.dca_count}/3')
    print(f'')
    print(f'Current P&L (@ ${current_price}):')
    print(f'  Current Value: ${pnl["current_value"]:.2f}')
    print(f'  Unrealized P&L: ${pnl["pnl"]:.2f} ({pnl["pnl_pct"]:.2f}%)')

    print(f'\nDCA History:')
    for i, entry in enumerate(pos.dca_entries):
        print(f'  {i+1}. ${entry.price:.2f} x {entry.shares:.2f} shares = ${entry.amount:.2f}')
        if entry.reasoning:
            reason = entry.reasoning[:70] + '...' if len(entry.reasoning) > 70 else entry.reasoning
            print(f'     -> {reason}')

    print('\n' + '=' * 80)
    print('[SUCCESS] Full integration test completed!')
    print('=' * 80)


if __name__ == '__main__':
    asyncio.run(full_integration_test())
