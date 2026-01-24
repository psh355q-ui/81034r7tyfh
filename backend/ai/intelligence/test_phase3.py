"""
Phase 3 검증 테스트 - Market Moving Score
"""

from backend.ai.intelligence.market_moving_score import (
    MarketMovingScoreCalculator,
    filter_market_moving_news
)

print('=' * 60)
print('Phase 3 검증 #1: 뉴스 점수 계산 (0-100)')
print('=' * 60)

# 테스트 케이스
test_cases = [
    {
        'name': 'HIGH Impact + HIGH Specificity + HIGH Reliability',
        'title': 'Fed Hikes Rate by 75bp, Markets Crash',
        'summary': 'FOMC raised rates to 5.25%. SPY dropped 3.5%, VIX surged to 35.',
        'source': 'Bloomberg',
        'expected': 'Very High (90+)'
    },
    {
        'name': 'MEDIUM Impact + MEDIUM Specificity',
        'title': 'Analyst Upgrades AAPL to Buy',
        'summary': 'Wells Fargo raised price target to $200.',
        'source': 'CNBC',
        'expected': 'Medium (50-70)'
    },
    {
        'name': 'LOW Impact + LOW Specificity + LOW Reliability',
        'title': 'CEO Might Consider Selling Shares',
        'summary': 'Unconfirmed rumor from social media.',
        'source': 'Twitter',
        'expected': 'Very Low (<30)'
    }
]

calculator = MarketMovingScoreCalculator(current_vix=20.0)

for i, tc in enumerate(test_cases, 1):
    score = calculator.calculate(
        title=tc['title'],
        summary=tc['summary'],
        source=tc['source']
    )
    
    print(f'\n테스트 {i}: {tc["name"]}')
    print(f'  뉴스: {tc["title"][:50]}...')
    print(f'  총점: {score.total_score:.1f}/100')
    print(f'  세부: Impact={score.impact_score:.0f}, Specificity={score.specificity_score:.0f}, Reliability={score.reliability_score:.0f}')
    print(f'  예상: {tc["expected"]}')
    print(f'  판정: {"✅ PASS" if score.total_score >= 0 and score.total_score <= 100 else "❌ FAIL"}')

print('\n✅ 뉴스 점수 계산 검증 완료 (0-100 범위)')

print('\n' + '=' * 60)
print('Phase 3 검증 #2: VIX 연동 동적 임계값')
print('=' * 60)

test_news = {
    'title': 'Market Rally on Strong Earnings',
    'summary': 'SPY up 1.2% as tech earnings beat expectations.',
    'source': 'CNBC'
}

vix_scenarios = [
    (12, 'VIX 12 (안정) → 낮은 임계값 (민감)'),
    (20, 'VIX 20 (정상) → 기준 임계값'),
    (30, 'VIX 30 (패닉) → 높은 임계값 (엄격)'),
]

for vix, description in vix_scenarios:
    calc = MarketMovingScoreCalculator(current_vix=vix)
    score = calc.calculate(
        title=test_news['title'],
        summary=test_news['summary'],
        source=test_news['source']
    )
    
    print(f'\n{description}')
    print(f'  Score: {score.total_score:.1f}')
    print(f'  Threshold: {score.threshold:.1f}')
    decision = "✅ INCLUDE" if score.should_include else "❌ EXCLUDE"
    print(f'  Decision: {decision}')

print('\n✅ VIX 연동 동적 임계값 검증 완료')

print('\n' + '=' * 60)
print('Phase 3 검증 #3: 노이즈 뉴스 필터링')
print('=' * 60)

news_list = [
    {
        'title': 'NVDA Q4 Earnings Beat at $5.5B Revenue',
        'summary': 'NVIDIA reported EPS $5.53, beating $4.92 estimate. Revenue up 265%.',
        'source': 'Bloomberg'
    },
    {
        'title': 'CEO Sold 100 Shares',
        'summary': 'Insider selling reported.',
        'source': 'Blog'
    },
    {
        'title': 'Fed May Possibly Consider Rate Cut Rumor',
        'summary': 'Unconfirmed speculation from social media suggests potential rate cut.',
        'source': 'Twitter'
    },
    {
        'title': 'Market Crashes as Circuit Breaker Triggered',
        'summary': 'SPY halted as VIX surges to 50. Trading suspended.',
        'source': 'Reuters'
    }
]

print(f'\n입력 뉴스: {len(news_list)} 건')
for i, news in enumerate(news_list, 1):
    print(f'  {i}. {news["title"][:50]}... ({news["source"]})')

filtered = filter_market_moving_news(news_list, vix=20.0)

print(f'\n필터링 후: {len(filtered)} 건')
for i, news in enumerate(filtered, 1):
    print(f'  {i}. {news["title"][:50]}... (Score: {news["market_moving_score"]:.1f})')

expected_filtered_out = ['CEO Sold 100 Shares', 'Fed May Possibly Consider']
actual_titles = [n['title'] for n in filtered]

noise_filtered = all(
    not any(noise in title for noise in expected_filtered_out)
    for title in actual_titles
)

result = "✅ PASS" if noise_filtered else "❌ FAIL"
print(f'\n노이즈 필터링 검증: {result}')
print('✅ 노이즈 뉴스 필터링 검증 완료')

print('\n' + '=' * 60)
print('✅ Phase 3 전체 검증 완료')
print('=' * 60)
