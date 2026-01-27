"""
Thesis Keeper Tests

TDD Phase: 투자 논리 저장 및 관리 테스트
"""

import pytest
import asyncio
from datetime import datetime
from backend.services.thesis_keeper import ThesisKeeper
from backend.core.database import AsyncSessionLocal, Base, engine


@pytest.fixture(scope="function")
async def db_session():
    """Setup test database session"""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with AsyncSessionLocal() as session:
        # Clear test data
        await session.execute("DELETE FROM portfolio_thesis")
        await session.commit()
        
        yield session
        
        # Cleanup
        await session.rollback()


@pytest.fixture
def keeper():
    """Setup ThesisKeeper"""
    return ThesisKeeper()


class TestThesisKeeper:
    """Test Thesis Keeper Service"""
    
    @pytest.mark.asyncio
    async def test_save_thesis(self, keeper, db_session):
        """Test: Save new investment thesis"""
        thesis_data = {
            'ticker': 'NVDA',
            'thesis_text': 'AI 반도체 수요 급증, CUDA 생태계 독점',
            'moat_type': 'network_effect',
            'moat_strength': 0.95
        }
        
        thesis_id = await keeper.save_thesis(thesis_data, db_session)
        await db_session.commit()
        
        assert thesis_id > 0
        assert isinstance(thesis_id, int)
    
    @pytest.mark.asyncio
    async def test_get_active_thesis(self, keeper, db_session):
        """Test: Retrieve active thesis for ticker"""
        # Arrange
        await keeper.save_thesis({
            'ticker': 'NVDA',
            'thesis_text': 'AI dominance',
            'moat_type': 'network_effect',
            'moat_strength': 0.95
        }, db_session)
        await db_session.commit()
        
        # Act
        thesis = await keeper.get_thesis('NVDA', db_session)
        
        # Assert
        assert thesis is not None
        assert thesis['ticker'] == 'NVDA'
        assert thesis['status'] == 'active'
        assert thesis['moat_type'] == 'network_effect'
        assert thesis['thesis_text'] == 'AI dominance'
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_thesis(self, keeper, db_session):
        """Test: Get thesis for ticker with no thesis"""
        thesis = await keeper.get_thesis('INVALID', db_session)
        
        assert thesis is None
    
    @pytest.mark.asyncio
    async def test_mark_thesis_violated(self, keeper, db_session):
        """Test: Mark thesis as violated"""
        # Arrange
        await keeper.save_thesis({
            'ticker': 'INTC',
            'thesis_text': 'x86 독점',
            'moat_type': 'switching_cost'
        }, db_session)
        await db_session.commit()
        
        # Act
        await keeper.mark_violated('INTC', 'ARM 전환으로 x86 독점 무너짐', db_session)
        await db_session.commit()
        
        # Assert
        thesis = await keeper.get_thesis('INTC', db_session)
        assert thesis is None  # No active thesis
        
        violated = await keeper.get_violated_thesis('INTC', db_session)
        assert violated is not None
        assert violated['status'] == 'violated'
        assert 'ARM 전환' in violated['violation_reason']
    
    @pytest.mark.asyncio
    async def test_thesis_history(self, keeper, db_session):
        """Test: Get thesis history for ticker"""
        # Arrange: Create multiple theses
        await keeper.save_thesis({'ticker': 'AAPL', 'thesis_text': 'iPhone 성장'}, db_session)
        await db_session.commit()
        
        await keeper.mark_violated('AAPL', 'iPhone 성장 둔화', db_session)
        await db_session.commit()
        
        await keeper.save_thesis({'ticker': 'AAPL', 'thesis_text': 'Services 전환'}, db_session)
        await db_session.commit()
        
        # Act
        history = await keeper.get_thesis_history('AAPL', db_session)
        
        # Assert
        assert len(history) == 2
        assert history[0]['status'] == 'violated'  # Oldest first
        assert history[1]['status'] == 'active'
    
    @pytest.mark.asyncio
    async def test_update_thesis_strength(self, keeper, db_session):
        """Test: Update moat strength"""
        await keeper.save_thesis({
            'ticker': 'GOOGL',
            'thesis_text': 'Search monopoly',
            'moat_type': 'network_effect',
            'moat_strength': 0.90
        }, db_session)
        await db_session.commit()
        
        await keeper.update_moat_strength('GOOGL', 0.85, db_session)
        await db_session.commit()
        
        thesis = await keeper.get_thesis('GOOGL', db_session)
        assert abs(thesis['moat_strength'] - 0.85) < 0.01
    
    @pytest.mark.asyncio
    async def test_search_by_moat_type(self, keeper, db_session):
        """Test: Find all theses by moat type"""
        await keeper.save_thesis({'ticker': 'NVDA', 'moat_type': 'network_effect', 'thesis_text': 'AI'}, db_session)
        await keeper.save_thesis({'ticker': 'GOOGL', 'moat_type': 'network_effect', 'thesis_text': 'Search'}, db_session)
        await keeper.save_thesis({'ticker': 'WMT', 'moat_type': 'cost_advantage', 'thesis_text': 'Scale'}, db_session)
        await db_session.commit()
        
        network_theses = await keeper.find_by_moat_type('network_effect', db_session)
        
        assert len(network_theses) == 2
        assert all(t['moat_type'] == 'network_effect' for t in network_theses)


if __name__ == '__main__':
    """직접 실행 시 테스트 수행"""
    pytest.main([__file__, '-v', '--tb=short'])
