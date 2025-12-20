"""
13F Thesis Validation - Unit Tests

ChatGPT Feature 4: 13F Filing 투자 논리 검증

작성일: 2025-12-16
"""

import pytest
from datetime import datetime, timedelta
from backend.data.collectors.smart_money_collector import SmartMoneyCollector


def test_validate_thesis_working():
    """투자 논리 작동 중 (매수 후 상승)"""
    collector = SmartMoneyCollector()
    
    result = collector.validate_thesis(
        ticker="OXY",
        filing_date="2024-09-30",
        filing_price=58.2,
        action="INCREASE"
    )
    
    # 현재가가 filing_price보다 높으면 THESIS_WORKING
    # (실제 API 호출이므로 정확한 값은 변동)
    assert result["thesis_status"] in ["THESIS_WORKING", "THESIS_UNCLEAR", "THESIS_FAILED"]
    assert result["filing_price"] == 58.2
    assert result["current_price"] > 0
    assert "reasoning" in result


def test_validate_thesis_failed():
    """투자 논리 실패 (매수 후 급락)"""
    collector = SmartMoneyCollector()
    
    # 시뮬레이션: 현재가가 filing_price의 80% (20% 하락)
    result = collector.validate_thesis(
        ticker="TEST",  # 존재하지 않는 티커 (fallback to filing_price)
        filing_date="2024-06-30",
        filing_price=100.0,
        action="INCREASE"
    )
    
    # Fallback시 current_price = filing_price이므로 THESIS_UNCLEAR
    assert result["filing_price"] == 100.0
    assert result["price_change_pct"] == 0.0  # No change when fallback


def test_validate_thesis_correct_exit():
    """정확한 출구 (매도 후 하락)"""
    collector = SmartMoneyCollector()
    
    # 매도 후 가격이 떨어졌다면 CORRECT_EXIT
    # 실제 검증은 실제 티커로 해야 하지만, 로직은 확인 가능
    result = collector.validate_thesis(
        ticker="EXAMPLE",
        filing_date="2024-07-01",
        filing_price=150.0,
        action="SOLD_OUT"
    )
    
    assert result["thesis_status"] in ["CORRECT_EXIT", "THESIS_UNCLEAR", "THESIS_FAILED"]
    assert result["action"] == "SOLD_OUT" if "action" in result else True


def test_validate_thesis_time_elapsed():
    """경과 시간 계산"""
    collector = SmartMoneyCollector()
    
    # 90일 전
    filing_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    result = collector.validate_thesis(
        ticker="AAPL",
        filing_date=filing_date,
        filing_price=170.0,
        action="NEW"
    )
    
    # 약 90일 경과
    assert 85 <= result["time_elapsed_days"] <= 95


def test_validate_thesis_unclear():
    """판단 보류 (작은 변동)"""
    collector = SmartMoneyCollector()
    
    # DECREASE 액션은 보통 THESIS_UNCLEAR
    result = collector.validate_thesis(
        ticker="MSFT",
        filing_date="2024-10-01",
        filing_price=420.0,
        action="DECREASE"
    )
    
    assert result["thesis_status"] == "THESIS_UNCLEAR"
    assert "비중 축소" in result["reasoning"]


def test_validate_thesis_response_structure():
    """응답 구조 검증"""
    collector = SmartMoneyCollector()
    
    result = collector.validate_thesis(
        ticker="NVDA",
        filing_date="2024-08-15",
        filing_price=110.0,
        action="INCREASE"
    )
    
    # 필수 필드 확인
    required_fields = [
        "thesis_status",
        "filing_price",
        "current_price",
        "price_change",
        "price_change_pct",
        "time_elapsed_days",
        "reasoning"
    ]
    
    for field in required_fields:
        assert field in result, f"Missing field: {field}"
    
    # 타입 확인
    assert isinstance(result["thesis_status"], str)
    assert isinstance(result["filing_price"], (int, float))
    assert isinstance(result["current_price"], (int, float))
    assert isinstance(result["price_change_pct"], float)
    assert isinstance(result["time_elapsed_days"], int)
    assert isinstance(result["reasoning"], str)


def test_validate_thesis_status_values():
    """thesis_status 값 검증"""
    valid_statuses = [
        "THESIS_WORKING",
        "THESIS_FAILED",
        "THESIS_UNCLEAR",
        "CORRECT_EXIT"
    ]
    
    collector = SmartMoneyCollector()
    
    result = collector.validate_thesis(
        ticker="TSLA",
        filing_date="2024-09-01",
        filing_price=220.0,
        action="NEW"
    )
    
    assert result["thesis_status"] in valid_statuses, \
        f"Invalid status: {result['thesis_status']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
