"""
Trading Tendency Analyzer - Unit Tests

ChatGPT Feature 6 Tests

작성일: 2025-12-16
"""

import pytest
from datetime import datetime, timedelta
from backend.metrics.trading_tendency_analyzer import (
    TradingTendencyAnalyzer,
    TradeAction,
    TendencyLevel
)


def test_conservative_tendency():
    """보수적 성향 테스트"""
    analyzer = TradingTendencyAnalyzer()
    
    # 작은 포지션, 많은 분산
    trades = [
        TradeAction(
            ticker="AAPL",
            action="BUY",
            quantity=10,
            price=180,
            timestamp=datetime.now(),
            portfolio_percentage=3.0  # 3%
        ),
        TradeAction(
            ticker="MSFT",
            action="BUY",
            quantity=5,
            price=420,
            timestamp=datetime.now(),
            portfolio_percentage=4.0  # 4%
        )
    ]
    
    portfolio = {
        'positions': [
            {'ticker': 'AAPL'},
            {'ticker': 'MSFT'},
            {'ticker': 'GOOGL'},
            {'ticker': 'AMZN'},
            {'ticker': 'META'},
            {'ticker': 'NVDA'},
            {'ticker': 'TSLA'},
            {'ticker': 'AMD'},
            {'ticker': 'INTC'},
            {'ticker': 'NFLX'}  # 10종목
        ]
    }
    
    result = analyzer.analyze_tendency(trades, portfolio)
    
    assert result.tendency_score < 50  # 보수적
    assert result.tendency_level in [
        TendencyLevel.VERY_CONSERVATIVE,
        TendencyLevel.CONSERVATIVE,
        TendencyLevel.MODERATE
    ]


def test_aggressive_tendency():
    """공격적 성향 테스트"""
    analyzer = TradingTendencyAnalyzer()
    
    # 큰 포지션, 집중 투자
    trades = [
        TradeAction(
            ticker="NVDA",
            action="BUY",
            quantity=100,
            price=560,
            timestamp=datetime.now(),
            portfolio_percentage=25.0  # 25%
        ),
        TradeAction(
            ticker="TSLA",
            action="BUY",
            quantity=50,
            price=250,
            timestamp=datetime.now(),
            portfolio_percentage=20.0  # 20%
        )
    ]
    
    portfolio = {
        'positions': [
            {'ticker': 'NVDA'},
            {'ticker': 'TSLA'}  # 2종목만
        ]
    }
    
    result = analyzer.analyze_tendency(trades, portfolio)
    
    assert result.tendency_score > 50  # 공격적
    assert result.tendency_level in [
        TendencyLevel.MODERATE,
        TendencyLevel.AGGRESSIVE,
        TendencyLevel.VERY_AGGRESSIVE
    ]


def test_position_size_analysis():
    """포지션 크기 분석 테스트"""
    analyzer = TradingTendencyAnalyzer()
    
    # Small positions
    small_trades = [
        TradeAction("A", "BUY", 10, 100, datetime.now(), 2.0),
        TradeAction("B", "BUY", 10, 100, datetime.now(), 3.0)
    ]
    
    score_small = analyzer._analyze_position_size(small_trades)
    assert score_small < 40  # 보수적
    
    # Large positions
    large_trades = [
        TradeAction("A", "BUY", 100, 100, datetime.now(), 20.0),
        TradeAction("B", "BUY", 100, 100, datetime.now(), 25.0)
    ]
    
    score_large = analyzer._analyze_position_size(large_trades)
    assert score_large > 60  # 공격적


def test_diversification_analysis():
    """분산 투자 분석 테스트"""
    analyzer = TradingTendencyAnalyzer()
    
    # 많은 종목 (보수적)
    portfolio_many = {
        'positions': [{'ticker': f'STOCK{i}'} for i in range(20)]
    }
    
    score_many = analyzer._analyze_diversification(portfolio_many)
    assert score_many < 40
    
    # 적은 종목 (공격적)
    portfolio_few = {
        'positions': [{'ticker': 'NVDA'}, {'ticker': 'TSLA'}]
    }
    
    score_few = analyzer._analyze_diversification(portfolio_few)
    assert score_few > 60


def test_tendency_level_determination():
    """성향 레벨 결정 테스트"""
    analyzer = TradingTendencyAnalyzer()
    
    assert analyzer._determine_level(10) == TendencyLevel.VERY_CONSERVATIVE
    assert analyzer._determine_level(30) == TendencyLevel.CONSERVATIVE
    assert analyzer._determine_level(50) == TendencyLevel.MODERATE
    assert analyzer._determine_level(70) == TendencyLevel.AGGRESSIVE
    assert analyzer._determine_level(90) == TendencyLevel.VERY_AGGRESSIVE


def test_insights_generation():
    """인사이트 생성 테스트"""
    analyzer = TradingTendencyAnalyzer()
    
    from backend.metrics.trading_tendency_analyzer import TendencyMetrics
    
    metrics = TendencyMetrics(
        position_size_score=80,  # 공격적
        holding_period_score=50,
        risk_level_score=50,
        diversification_score=75,  # 집중
        reaction_speed_score=50
    )
    
    insights = analyzer._generate_insights(metrics, 65)
    
    assert len(insights) > 0
    assert any("공격적" in i or "집중" in i for i in insights)


def test_recommendations_generation():
    """추천사항 생성 테스트"""
    analyzer = TradingTendencyAnalyzer()
    
    from backend.metrics.trading_tendency_analyzer import TendencyMetrics
    
    # 매우 공격적
    metrics_aggressive = TendencyMetrics(
        position_size_score=90,
        holding_period_score=80,
        risk_level_score=70,
        diversification_score=85,
        reaction_speed_score=75
    )
    
    recommendations = analyzer._generate_recommendations(80, metrics_aggressive)
    
    assert len(recommendations) > 0


def test_empty_portfolio():
    """빈 포트폴리오 테스트"""
    analyzer = TradingTendencyAnalyzer()
    
    result = analyzer.analyze_tendency([], {'positions': []})
    
    assert result.tendency_score == 50.0  # 중립
    assert result.tendency_level == TendencyLevel.MODERATE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
