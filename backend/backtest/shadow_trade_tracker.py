"""
Shadow Trade Tracker - 그림자 거래 추적기

거부된 제안을 가상으로 추적하여 방어 성과 측정

작성일: 2025-12-15
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from backend.data.models.shadow_trade import ShadowTrade
from backend.data.collectors.api_clients.yahoo_client import YahooFinanceClient

logger = logging.getLogger(__name__)


class ShadowTradeTracker:
    """
    Shadow Trade Tracker
    
    거부되거나 HOLD된 제안을 가상으로 추적하여
    "안 샀기 때문에 손실을 피했다"를 증명합니다.
    
    Usage:
        tracker = ShadowTradeTracker(db_session)
        tracker.create_shadow_trade(proposal, reason)
        tracker.update_all_shadow_trades()
        report = tracker.generate_shield_report()
    """
    
    def __init__(self, db_session: Session, yahoo_client: Optional[YahooFinanceClient] = None):
        """
        초기화
        
        Args:
            db_session: DB 세션
            yahoo_client: Yahoo Finance 클라이언트 (None이면 생성)
        """
        self.db = db_session
        self.yahoo_client = yahoo_client or YahooFinanceClient()
    
    def create_shadow_trade(
        self,
        proposal: Dict[str, Any],
        rejection_reason: str,
        violated_articles: Optional[List[str]] = None,
        tracking_days: int = 7
    ) -> ShadowTrade:
        """
        새로운 그림자 거래 생성
        
        Args:
            proposal: 거부된 제안
                {
                    'ticker': str,
                    'action': 'BUY'/'SELL',
                    'entry_price': float,
                    'shares': int
                }
            rejection_reason: 거부 사유
            violated_articles: 위반된 헌법 조항
            tracking_days: 추적 기간 (기본 7일)
            
        Returns:
            생성된 ShadowTrade
        """
        ticker = proposal.get('ticker')
        action = proposal.get('action', 'BUY')
        entry_price = proposal.get('entry_price', 0.0)
        shares = proposal.get('shares', 0)
        
        # 현재 가격 조회 (entry_price가 없으면)
        if entry_price == 0.0:
            current_price = self.yahoo_client.get_current_price(ticker)
            entry_price = current_price
        
        # Shadow Trade 생성
        shadow = ShadowTrade(
            proposal_id=proposal.get('id'),
            ticker=ticker,
            action=action,
            entry_price=entry_price,
            shares=shares,
            rejection_reason=rejection_reason,
            violated_articles=', '.join(violated_articles) if violated_articles else None,
            tracking_days=tracking_days,
            status='TRACKING'
        )
        
        self.db.add(shadow)
        self.db.commit()
        
        logger.info(
            f"🛡️ Shadow Trade 생성: {ticker} {action} @ ${entry_price} "
            f"(사유: {rejection_reason})"
        )
        
        return shadow
    
    def update_shadow_trade(self, shadow: ShadowTrade) -> ShadowTrade:
        """
        그림자 거래 업데이트
        
        현재 시장 가격으로 손익 재계산
        
        Args:
            shadow: Shadow Trade
            
        Returns:
            업데이트된 Shadow Trade
        """
        # 현재 가격 조회
        try:
            current_price = self.yahoo_client.get_current_price(shadow.ticker)
            
            if current_price:
                shadow.update_pnl(current_price)
                self.db.commit()
                
                logger.debug(
                    f"Shadow Trade 업데이트: {shadow.ticker} "
                    f"${shadow.entry_price} → ${current_price} "
                    f"({shadow.virtual_pnl_pct:+.2%})"
                )
        
        except Exception as e:
            logger.error(f"Shadow Trade 업데이트 실패: {shadow.ticker} - {e}")
        
        return shadow
    
    def update_all_shadow_trades(self):
        """
        모든 활성 그림자 거래 업데이트
        """
        # TRACKING 상태인 거래만 조회
        active_shadows = self.db.query(ShadowTrade).filter(
            ShadowTrade.status == 'TRACKING'
        ).all()
        
        logger.info(f"🔄 활성 Shadow Trades 업데이트 중... ({len(active_shadows)}개)")
        
        for shadow in active_shadows:
            # 추적 기간 만료 체크
            if shadow.created_at:
                elapsed = datetime.utcnow() - shadow.created_at
                
                if elapsed.days >= shadow.tracking_days:
                    # 추적 종료
                    current_price = self.yahoo_client.get_current_price(shadow.ticker)
                    if current_price:
                        shadow.close_tracking(current_price)
                        logger.info(f"✅ Shadow Trade 종료: {shadow.ticker}")
                    continue
            
            # 업데이트
            self.update_shadow_trade(shadow)
        
        self.db.commit()
    
    def close_expired_shadows(self, max_age_days: int = 30):
        """
        오래된 그림자 거래 정리
        
        Args:
            max_age_days: 최대 보관 기간
        """
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        old_shadows = self.db.query(ShadowTrade).filter(
            ShadowTrade.status == 'TRACKING',
            ShadowTrade.created_at < cutoff_date
        ).all()
        
        for shadow in old_shadows:
            current_price = self.yahoo_client.get_current_price(shadow.ticker)
            if current_price:
                shadow.close_tracking(current_price)
        
        self.db.commit()
        logger.info(f"🗑️ 만료된 Shadow Trades {len(old_shadows)}개 종료")
    
    def get_defensive_wins(self, days: int = 7) -> List[ShadowTrade]:
        """
        방어 성공 사례 조회
        
        Args:
            days: 조회 기간 (일)
            
        Returns:
            방어 성공한 Shadow Trades
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        all_shadows = self.db.query(ShadowTrade).filter(
            ShadowTrade.created_at >= cutoff
        ).all()
        
        # 방어 성공만 필터
        defensive_wins = [s for s in all_shadows if s.is_defensive_win()]
        
        return defensive_wins
    
    def calculate_total_avoided_loss(self, days: int = 7) -> float:
        """
        총 방어 손실 계산
        
        Args:
            days: 조회 기간
            
        Returns:
            총 방어 손실 금액 ($)
        """
        wins = self.get_defensive_wins(days)
        total = sum(s.get_avoided_loss() for s in wins)
        
        return total
    
    def generate_shield_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Shield Report (방패 보고서) 생성
        
        Args:
            days: 조회 기간
            
        Returns:
            방어 성과 리포트
        """
        wins = self.get_defensive_wins(days)
        total_avoided = self.calculate_total_avoided_loss(days)
        
        # 전체 Shadow Trades
        cutoff = datetime.utcnow() - timedelta(days=days)
        all_shadows = self.db.query(ShadowTrade).filter(
            ShadowTrade.created_at >= cutoff
        ).all()
        
        report = {
            'period_days': days,
            'total_rejected_proposals': len(all_shadows),
            'defensive_wins': len(wins),
            'defensive_win_rate': len(wins) / len(all_shadows) if all_shadows else 0,
            'total_avoided_loss': total_avoided,
            'highlights': []
        }
        
        # 주요 사례 (손실 방어 금액 상위 3개)
        sorted_wins = sorted(wins, key=lambda x: x.get_avoided_loss(), reverse=True)
        
        for shadow in sorted_wins[:3]:
            report['highlights'].append({
                'ticker': shadow.ticker,
                'action': shadow.action,
                'rejection_reason': shadow.rejection_reason,
                'entry_price': shadow.entry_price,
                'exit_price': shadow.exit_price,
                'avoided_loss': shadow.get_avoided_loss(),
                'pnl_pct': shadow.virtual_pnl_pct,
                'date': shadow.created_at.strftime('%Y-%m-%d')
            })
        
        return report
    
    def get_shadow_by_ticker(self, ticker: str) -> List[ShadowTrade]:
        """
        특정 종목의 Shadow Trades 조회
        
        Args:
            ticker: 종목 코드
            
        Returns:
            Shadow Trades 리스트
        """
        return self.db.query(ShadowTrade).filter(
            ShadowTrade.ticker == ticker
        ).order_by(ShadowTrade.created_at.desc()).all()


if __name__ == "__main__":
    # 테스트
    print("=== Shadow Trade Tracker Test ===\n")
    
    print("이 모듈은 DB 세션이 필요합니다.")
    print("실제 사용 예시:\n")
    
    print("""
    # 1. Shadow Trade 생성
    proposal = {
        'ticker': 'TSLA',
        'action': 'BUY',
        'entry_price': 250.0,
        'shares': 40
    }
    
    tracker = ShadowTradeTracker(db_session)
    shadow = tracker.create_shadow_trade(
        proposal,
        rejection_reason="VIX 25 초과, 방어 모드",
        violated_articles=["제4조: 강제 개입"]
    )
    
    # 2. 업데이트
    tracker.update_all_shadow_trades()
    
    # 3. 리포트 생성
    report = tracker.generate_shield_report(days=7)
    print(f"방어 성공: {report['defensive_wins']}건")
    print(f"방어 금액: ${report['total_avoided_loss']:,.0f}")
    """)
    
    print("\n✅ Shadow Trade Tracker 구현 완료!")
