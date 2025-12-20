"""
Tests for Self-Feedback Loop Module (Phase D)

pytest -v tests/test_feedback.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from backend.ai.feedback.feedback_loop import (
    FeedbackLoop,
    PredictionRecord,
    ModelPerformance,
    CalibrationAdjustment,
)


class TestFeedbackLoop:
    """FeedbackLoop 테스트"""
    
    @pytest.fixture
    def loop(self):
        return FeedbackLoop()
    
    @pytest.mark.asyncio
    async def test_record_prediction(self, loop):
        """예측 기록 테스트"""
        pred_id = await loop.record_prediction(
            ticker="AAPL",
            action="BUY",
            conviction=0.8,
            model_used="claude",
            entry_price=175.0,
        )
        
        assert pred_id == 1
        assert len(loop._predictions) == 1
        assert loop._predictions[0].ticker == "AAPL"
    
    @pytest.mark.asyncio
    async def test_multiple_predictions(self, loop):
        """다중 예측 기록"""
        await loop.record_prediction("AAPL", "BUY", 0.8, "claude")
        await loop.record_prediction("NVDA", "SELL", 0.7, "gemini")
        await loop.record_prediction("MSFT", "HOLD", 0.5, "claude")
        
        assert len(loop._predictions) == 3
    
    @pytest.mark.asyncio
    async def test_get_model_performance_empty(self, loop):
        """빈 성과 조회"""
        results = await loop.get_model_performance()
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_get_model_performance_with_data(self, loop):
        """데이터 있을 때 성과 조회"""
        # 예측 기록
        for i in range(10):
            await loop.record_prediction(
                ticker=f"TEST{i}",
                action="BUY",
                conviction=0.8,
                model_used="test_model",
            )
        
        # 수동으로 예측 결과 설정
        for i, pred in enumerate(loop._predictions):
            pred.prediction_correct = (i % 2 == 0)  # 50% 정확도
        
        results = await loop.get_model_performance()
        
        assert len(results) == 1
        assert results[0].model_name == "test_model"
        assert results[0].total_predictions == 10
        assert results[0].accuracy == 0.5
    
    @pytest.mark.asyncio
    async def test_calibration_adjustment(self, loop):
        """보정값 계산 테스트"""
        # 충분한 데이터 생성
        for i in range(10):
            await loop.record_prediction(
                ticker=f"TEST{i}",
                action="BUY",
                conviction=0.8,
                model_used="test_model",
            )
            loop._predictions[-1].prediction_correct = (i < 6)  # 60% 정확도
        
        adjustments = await loop.get_calibration_adjustment("test_model", "BUY")
        
        assert "BUY" in adjustments
        cal = adjustments["BUY"]
        assert cal.original_confidence == 0.8
        assert cal.adjustment_ratio < 1.0  # 80% 확신에 60% 정확도 → 하향 조정
    
    def test_apply_calibration_no_cache(self, loop):
        """캐시 없을 때 원래 값 반환"""
        result = loop.apply_calibration("unknown", "BUY", 0.8)
        
        assert result == 0.8


class TestPredictionRecord:
    """PredictionRecord 데이터 구조 테스트"""
    
    def test_record_creation(self):
        """레코드 생성"""
        record = PredictionRecord(
            id=1,
            ticker="AAPL",
            action="BUY",
            conviction=0.85,
            model_used="claude",
            entry_price=175.0,
        )
        
        assert record.ticker == "AAPL"
        assert record.conviction == 0.85
        assert record.prediction_correct is None  # 아직 평가 안됨
    
    def test_record_with_results(self):
        """결과 포함 레코드"""
        record = PredictionRecord(
            ticker="NVDA",
            action="BUY",
            conviction=0.9,
            actual_return_5d=7.5,
            prediction_correct=True,
        )
        
        assert record.actual_return_5d == 7.5
        assert record.prediction_correct == True


class TestModelPerformance:
    """ModelPerformance 데이터 구조 테스트"""
    
    def test_performance_creation(self):
        """성과 객체 생성"""
        perf = ModelPerformance(
            model_name="claude",
            total_predictions=100,
            correct_predictions=75,
            accuracy=0.75,
            buy_accuracy=0.80,
            sell_accuracy=0.65,
        )
        
        assert perf.model_name == "claude"
        assert perf.accuracy == 0.75
        assert perf.confidence_calibration == 1.0  # 기본값


# 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
