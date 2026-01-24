"""
Test Models for v2.2 Implementation

Tests for:
- DailyBriefing caching fields
- WeeklyReport table
- EconomicEvent table

Usage:
    pytest tests/test_models.py
"""

import pytest
import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.database.models import DailyBriefing, WeeklyReport, EconomicEvent


def test_daily_briefing_cache_fields():
    """Test DailyBriefing caching fields"""
    # cache_key 필드 확인
    assert hasattr(DailyBriefing, 'cache_key'), "DailyBriefing should have cache_key field"
    
    # cache_hit 필드 확인
    assert hasattr(DailyBriefing, 'cache_hit'), "DailyBriefing should have cache_hit field"
    
    # cache_ttl 필드 확인
    assert hasattr(DailyBriefing, 'cache_ttl'), "DailyBriefing should have cache_ttl field"
    
    # importance_score 필드 확인
    assert hasattr(DailyBriefing, 'importance_score'), "DailyBriefing should have importance_score field"
    
    # economic_events_count 필드 확인
    assert hasattr(DailyBriefing, 'economic_events_count'), "DailyBriefing should have economic_events_count field"
    
    # sector_rotation_score 필드 확인
    assert hasattr(DailyBriefing, 'sector_rotation_score'), "DailyBriefing should have sector_rotation_score field"
    
    print("✓ DailyBriefing caching fields test passed")


def test_weekly_report_table_exists():
    """Test WeeklyReport table"""
    # __tablename__ 확인
    assert hasattr(WeeklyReport, '__tablename__'), "WeeklyReport should have __tablename__"
    assert WeeklyReport.__tablename__ == 'weekly_reports', "WeeklyReport table name should be 'weekly_reports'"
    
    # 필드 확인
    required_fields = [
        'id', 'week_start', 'week_end', 'content', 'metrics',
        'cache_key', 'cache_hit', 'cache_ttl', 'created_at', 'updated_at'
    ]
    
    for field in required_fields:
        assert hasattr(WeeklyReport, field), f"WeeklyReport should have {field} field"
    
    print("✓ WeeklyReport table test passed")


def test_economic_event_table_exists():
    """Test EconomicEvent table"""
    # __tablename__ 확인
    assert hasattr(EconomicEvent, '__tablename__'), "EconomicEvent should have __tablename__"
    assert EconomicEvent.__tablename__ == 'economic_events', "EconomicEvent table name should be 'economic_events'"
    
    # 필드 확인
    required_fields = [
        'id', 'event_name', 'country', 'category', 'event_time', 'importance',
        'forecast', 'actual', 'previous', 'surprise_pct', 'impact_direction',
        'impact_score', 'is_processed', 'processed_at', 'created_at', 'notes', 'updated_at'
    ]
    
    for field in required_fields:
        assert hasattr(EconomicEvent, field), f"EconomicEvent should have {field} field"
    
    print("✓ EconomicEvent table test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Test Models for v2.2 Implementation")
    print("=" * 60)
    print()
    
    # 모든 테스트 실행
    try:
        test_daily_briefing_cache_fields()
        test_weekly_report_table_exists()
        test_economic_event_table_exists()
        
        print()
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"✗ Test failed: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Unexpected error: {e}")
        print("=" * 60)
        sys.exit(1)
