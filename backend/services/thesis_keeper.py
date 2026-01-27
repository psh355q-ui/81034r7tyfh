"""
Thesis Keeper Service

투자 논리(Thesis) 저장 및 관리 서비스
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.data.thesis_models import PortfolioThesis
from backend.core.database import get_db, Base, engine
import logging

logger = logging.getLogger(__name__)


class ThesisKeeper:
    """
    Investment Thesis Management Service
    
    투자 논리 저장, 조회, 위반 표시
    """
    
    async def save_thesis(self, thesis_data: Dict, session: AsyncSession) -> int:
        """
        새 투자 논리 저장
        
        Args:
            thesis_data: 논리 데이터
                - ticker: 종목 심볼
                - thesis_text: 투자 논리 텍스트
                - moat_type: 해자 유형 (optional)
                - moat_strength: 해자 강도 0.0~1.0 (optional)
            session: Database session
        
        Returns:
            int: 생성된 thesis ID
        """
        thesis = PortfolioThesis(
            ticker=thesis_data['ticker'],
            thesis_text=thesis_data['thesis_text'],
            moat_type=thesis_data.get('moat_type'),
            moat_strength=thesis_data.get('moat_strength'),
            status='active'
        )
        
        session.add(thesis)
        await session.flush()  # Get ID before commit
        
        logger.info(f"Saved thesis for {thesis.ticker}: ID {thesis.id}")
        return thesis.id
    
    async def get_thesis(self, ticker: str, session: AsyncSession) -> Optional[Dict]:
        """
        활성 투자 논리 조회
        
        Args:
            ticker: 종목 심볼
            session: Database session
        
        Returns:
            Dict: 논리 데이터 or None
        """
        stmt = select(PortfolioThesis).where(
            PortfolioThesis.ticker == ticker,
            PortfolioThesis.status == 'active'
        ).order_by(PortfolioThesis.created_at.desc()).limit(1)
        
        result = await session.execute(stmt)
        thesis = result.scalar_one_or_none()
        
        if not thesis:
            return None
        
        return {
            'id': thesis.id,
            'ticker': thesis.ticker,
            'thesis_text': thesis.thesis_text,
            'moat_type': thesis.moat_type,
            'moat_strength': float(thesis.moat_strength) if thesis.moat_strength else None,
            'entry_date': thesis.entry_date,
            'status': thesis.status,
            'violation_reason': thesis.violation_reason,
            'violation_date': thesis.violation_date
        }
    
    async def mark_violated(self, ticker: str, reason: str, session: AsyncSession):
        """
        투자 논리 위반 표시
        
        Args:
            ticker: 종목 심볼
            reason: 위반 사유
            session: Database session
        """
        stmt = (
            update(PortfolioThesis)
            .where(
                PortfolioThesis.ticker == ticker,
                PortfolioThesis.status == 'active'
            )
            .values(
                status='violated',
                violation_reason=reason,
                violation_date=func.current_timestamp(),
                updated_at=func.current_timestamp()
            )
        )
        
        await session.execute(stmt)
        logger.warning(f"Thesis violated for {ticker}: {reason}")
    
    async def get_violated_thesis(self, ticker: str, session: AsyncSession) -> Optional[Dict]:
        """위반된 논리 조회"""
        stmt = select(PortfolioThesis).where(
            PortfolioThesis.ticker == ticker,
            PortfolioThesis.status == 'violated'
        ).order_by(PortfolioThesis.violation_date.desc()).limit(1)
        
        result = await session.execute(stmt)
        thesis = result.scalar_one_or_none()
        
        if not thesis:
            return None
        
        return {
            'id': thesis.id,
            'ticker': thesis.ticker,
            'thesis_text': thesis.thesis_text,
            'moat_type': thesis.moat_type,
            'moat_strength': float(thesis.moat_strength) if thesis.moat_strength else None,
            'entry_date': thesis.entry_date,
            'status': thesis.status,
            'violation_reason': thesis.violation_reason,
            'violation_date': thesis.violation_date
        }
    
    async def get_thesis_history(self, ticker: str, session: AsyncSession) -> List[Dict]:
        """전체 논리 이력 조회"""
        stmt = select(PortfolioThesis).where(
            PortfolioThesis.ticker == ticker
        ).order_by(PortfolioThesis.created_at.asc())
        
        result = await session.execute(stmt)
        theses = result.scalars().all()
        
        return [
            {
                'id': thesis.id,
                'ticker': thesis.ticker,
                'thesis_text': thesis.thesis_text,
                'moat_type': thesis.moat_type,
                'moat_strength': float(thesis.moat_strength) if thesis.moat_strength else None,
                'entry_date': thesis.entry_date,
                'status': thesis.status,
                'violation_reason': thesis.violation_reason,
                'violation_date': thesis.violation_date
            }
            for thesis in theses
        ]
    
    async def update_moat_strength(self, ticker: str, new_strength: float, session: AsyncSession):
        """해자 강도 업데이트"""
        stmt = (
            update(PortfolioThesis)
            .where(
                PortfolioThesis.ticker == ticker,
                PortfolioThesis.status == 'active'
            )
            .values(
                moat_strength=new_strength,
                updated_at=func.current_timestamp()
            )
        )
        
        await session.execute(stmt)
    
    async def find_by_moat_type(self, moat_type: str, session: AsyncSession) -> List[Dict]:
        """해자 유형별 논리 검색"""
        stmt = select(PortfolioThesis).where(
            PortfolioThesis.moat_type == moat_type,
            PortfolioThesis.status == 'active'
        ).order_by(PortfolioThesis.moat_strength.desc())
        
        result = await session.execute(stmt)
        theses = result.scalars().all()
        
        return [
            {
                'id': thesis.id,
                'ticker': thesis.ticker,
                'thesis_text': thesis.thesis_text,
                'moat_type': thesis.moat_type,
                'moat_strength': float(thesis.moat_strength) if thesis.moat_strength else None,
                'entry_date': thesis.entry_date,
                'status': thesis.status
            }
            for thesis in theses
        ]
    
    async def ensure_table_exists(self):
        """테이블 존재 확인 및 생성"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PortfolioThesis table ensured")
    
    async def clear_test_data(self, session: AsyncSession):
        """테스트 데이터 클리어 (테스트용)"""
        await session.execute("DELETE FROM portfolio_thesis")
        logger.info("Test data cleared")
