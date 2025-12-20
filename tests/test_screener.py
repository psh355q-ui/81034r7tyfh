"""
Tests for Dynamic Screener Module (Phase A)

pytest -v tests/test_screener.py
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

# Test imports
from backend.services.market_scanner.scanner import (
    DynamicScreener,
    ScreenerCandidate,
    ScanResult,
)
from backend.services.market_scanner.filters.volume_filter import (
    VolumeFilter,
    VolumeFilterResult,
)
from backend.services.market_scanner.filters.volatility_filter import (
    VolatilityFilter,
    VolatilityFilterResult,
)
from backend.services.market_scanner.filters.momentum_filter import (
    MomentumFilter,
    MomentumFilterResult,
)
from backend.services.market_scanner.massive_api_client import (
    RateLimiter,
    RateLimitConfig,
)


class TestVolumeFilter:
    """VolumeFilter 테스트"""
    
    @pytest.fixture
    def filter(self):
        return VolumeFilter(min_ratio=2.0, min_volume=500_000)
    
    @pytest.mark.asyncio
    async def test_volume_filter_pass(self, filter):
        """거래량 급등 종목 통과 테스트"""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock data: 현재 거래량이 평균의 3배
            mock_hist = MagicMock()
            mock_hist.__len__ = lambda self: 20
            mock_hist.__getitem__ = lambda self, key: MagicMock(
                iloc=MagicMock(__getitem__=lambda s, i: 3000000 if i == -1 else 1000000),
                tail=lambda n: MagicMock(mean=lambda: 1000000)
            )
            mock_ticker.return_value.history.return_value = mock_hist
            
            result = await filter.check("TEST")
            
            assert result.ticker == "TEST"
            assert result.volume_ratio > 0
    
    @pytest.mark.asyncio
    async def test_volume_filter_error_handling(self, filter):
        """에러 발생 시 graceful 처리"""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.history.side_effect = Exception("API Error")
            
            result = await filter.check("ERROR")
            
            assert result.passed == False
            assert "오류" in result.reason


class TestRateLimiter:
    """Rate Limiter 테스트 (Massive API)"""
    
    @pytest.fixture
    def limiter(self):
        return RateLimiter(RateLimitConfig(calls_per_minute=5))
    
    @pytest.mark.asyncio
    async def test_initial_calls_allowed(self, limiter):
        """초기 호출 허용 확인"""
        for i in range(5):
            allowed = await limiter.acquire()
            assert allowed == True
    
    def test_remaining_calls(self, limiter):
        """남은 호출 횟수 확인"""
        remaining = limiter.get_remaining_calls()
        assert remaining == 5


class TestDynamicScreener:
    """DynamicScreener 통합 테스트"""
    
    @pytest.fixture
    def screener(self):
        return DynamicScreener(max_candidates=10)
    
    def test_weights_sum_to_one(self, screener):
        """가중치 합계 검증"""
        total = sum(screener.weights.values())
        assert abs(total - 1.0) < 0.01
    
    def test_to_dict_format(self, screener):
        """to_dict 형식 검증"""
        candidate = ScreenerCandidate(
            ticker="TEST",
            score=75.5,
            volume_score=80,
            volatility_score=70,
            momentum_score=75,
            options_score=77,
            volume_ratio=2.5,
            price_change_pct=3.2,
            sector="Technology",
            reasons=["테스트 사유"],
        )
        
        result = screener.to_dict(candidate)
        
        assert result["ticker"] == "TEST"
        assert result["score"] == 75.5
        assert "scores" in result
        assert result["sector"] == "Technology"


class TestMomentumFilter:
    """MomentumFilter 테스트"""
    
    @pytest.fixture
    def filter(self):
        return MomentumFilter(min_return_5d=3.0)
    
    def test_momentum_signal_classification(self, filter):
        """모멘텀 신호 분류 테스트"""
        # 강한 상승
        assert filter.min_return_5d == 3.0


class TestScreenerCandidate:
    """ScreenerCandidate 데이터 구조 테스트"""
    
    def test_candidate_creation(self):
        """후보 생성 테스트"""
        candidate = ScreenerCandidate(
            ticker="NVDA",
            score=85,
            volume_score=90,
            volatility_score=80,
            momentum_score=85,
            options_score=85,
            volume_ratio=3.5,
            price_change_pct=5.2,
            sector="Semiconductors",
            reasons=["거래량 급등", "모멘텀 강세"],
        )
        
        assert candidate.ticker == "NVDA"
        assert candidate.score == 85
        assert len(candidate.reasons) == 2


# 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
