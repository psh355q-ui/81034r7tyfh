"""
Tests for Smart Options Flow Module (Phase B)

pytest -v tests/test_options.py
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import pandas as pd

from backend.ai.options.smart_options_analyzer import (
    SmartOptionsAnalyzer,
    SmartOptionFlow,
    TradeSide,
    Sentiment,
)
from backend.ai.options.whale_detector import (
    WhaleDetector,
    WhaleOrder,
    WhaleActivity,
    WhaleDirection,
)


class TestSmartOptionsAnalyzer:
    """SmartOptionsAnalyzer 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        return SmartOptionsAnalyzer(whale_threshold=50_000)
    
    def test_determine_trade_side_buy(self, analyzer):
        """Ask 쪽 체결 → BUY 판별"""
        # last가 ask에 가까움
        side = analyzer._determine_trade_side(
            last=9.95,
            bid=9.50,
            ask=10.00
        )
        assert side == TradeSide.BUY
    
    def test_determine_trade_side_sell(self, analyzer):
        """Bid 쪽 체결 → SELL 판별"""
        # last가 bid에 가까움
        side = analyzer._determine_trade_side(
            last=9.55,
            bid=9.50,
            ask=10.00
        )
        assert side == TradeSide.SELL
    
    def test_determine_trade_side_neutral(self, analyzer):
        """중간 체결 → NEUTRAL 판별"""
        side = analyzer._determine_trade_side(
            last=9.75,
            bid=9.50,
            ask=10.00
        )
        assert side == TradeSide.NEUTRAL
    
    def test_determine_trade_side_invalid_spread(self, analyzer):
        """유효하지 않은 스프레드 처리"""
        side = analyzer._determine_trade_side(
            last=10.00,
            bid=10.00,
            ask=10.00
        )
        assert side == TradeSide.NEUTRAL
    
    @pytest.mark.asyncio
    async def test_empty_flow_creation(self, analyzer):
        """빈 결과 생성 테스트"""
        flow = analyzer._create_empty_flow("TEST")
        
        assert flow.ticker == "TEST"
        assert flow.net_delta == 0
        assert flow.sentiment == Sentiment.NEUTRAL


class TestWhaleDetector:
    """WhaleDetector 테스트"""
    
    @pytest.fixture
    def detector(self):
        return WhaleDetector(threshold=50_000, mega_threshold=500_000)
    
    def test_detect_whale_orders(self, detector):
        """고래 주문 감지 테스트"""
        orders = [
            {"premium": 100_000, "volume": 100, "direction": "BULLISH"},
            {"premium": 30_000, "volume": 30, "direction": "BEARISH"},  # 미달
            {"premium": 75_000, "volume": 75, "direction": "BULLISH"},
        ]
        
        activity = detector.detect("TEST", orders)
        
        assert activity.total_orders == 2  # $50K+ 만
        assert activity.bullish_orders == 2
        assert activity.net_direction == WhaleDirection.BULLISH
    
    def test_whale_score_calculation(self, detector):
        """고래 점수 계산 테스트"""
        orders = [
            WhaleOrder(
                ticker="TEST",
                timestamp=datetime.now(),
                contract_type="call",
                strike=100,
                expiration="2024-01-20",
                volume=100,
                premium=600_000,  # 메가 고래
                trade_side="BUY",
                direction="BULLISH",
            )
        ]
        
        score = detector._calculate_whale_score(orders, 600_000)
        
        assert score >= 60  # 메가 고래 + 높은 프리미엄
    
    def test_empty_whale_activity(self, detector):
        """고래 없을 때 처리"""
        activity = detector.detect("TEST", [])
        
        assert activity.total_orders == 0
        assert activity.net_direction == WhaleDirection.MIXED
        assert activity.whale_score == 0


class TestSmartOptionFlow:
    """SmartOptionFlow 데이터 구조 테스트"""
    
    def test_flow_creation(self):
        """Flow 생성 테스트"""
        flow = SmartOptionFlow(
            ticker="NVDA",
            timestamp=datetime.now(),
            net_call_premium=1_000_000,
            net_put_premium=-500_000,
            total_premium=1_500_000,
            net_delta=0.5,
            delta_interpretation="BULLISH",
            call_buy_volume=500,
            call_sell_volume=200,
            put_buy_volume=100,
            put_sell_volume=300,
            whale_orders=[{"premium": 100_000}],
            whale_bullish_pct=0.8,
            sentiment=Sentiment.BULLISH,
            sentiment_score=75,
        )
        
        assert flow.ticker == "NVDA"
        assert flow.net_delta == 0.5
        assert flow.sentiment == Sentiment.BULLISH
        assert len(flow.whale_orders) == 1


# 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
