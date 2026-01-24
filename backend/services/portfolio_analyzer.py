"""
portfolio_analyzer.py - PHASE7: KIS 포트폴리오 통합

📊 Data Sources:
    - KIS Broker: 계좌 잔고 및 보유 종목 조회
    - News Database: 보유 종목 관련 뉴스 조회
    - Telegram Notifier: 포트폴리오 알림 전송

🔗 External Dependencies:
    - backend.brokers.kis_broker: KIS API 연동
    - backend.database.repository: 뉴스 데이터 조회
    - backend.notifications.telegram_notifier: 텔레그램 알림
    - logging: 로깅

📤 Main Functions:
    - get_holdings_for_briefing(): 브리핑용 보유 종목 조회
    - check_portfolio_alerts(): 포트폴리오 알림 (±5% 변동)
    - generate_briefing_section(): 브리핑 섹션 생성

🔄 Called By:
    - backend/ai/reporters/enhanced_daily_reporter.py: 브리핑 생성 시 포트폴리오 섹션 추가
    - backend/services/daily_briefing_cache_manager.py: 중요도 점수 계산 시 포트폴리오 알림 개수 확인

📝 Notes:
    - ±5% 변동 시 텔레그램 즉시 알림
    - 보유 종목 관련 뉴스 강조
    - 맞춤형 분석 제공

Author: AI Trading System Team
Date: 2026-01-23
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class PortfolioAnalyzer:
    """
    포트폴리오 분석 및 브리핑 섹션 생성
    
    KIS Broker와 연동하여 보유 종목 정보를 조회하고,
    포트폴리오 알림 및 브리핑 섹션을 생성합니다.
    """
    
    def __init__(self, kis_broker=None, telegram_notifier=None):
        """
        PortfolioAnalyzer 초기화
        
        Args:
            kis_broker: KISBroker 인스턴스 (옵션)
            telegram_notifier: TelegramNotifier 인스턴스 (옵션)
        """
        self.kis_broker = kis_broker
        self.telegram_notifier = telegram_notifier
        self._last_alert_check_time = None
        
        logger.info("PortfolioAnalyzer initialized")
    
    async def get_holdings_for_briefing(self) -> List[Dict[str, Any]]:
        """
        브리핑용 보유 종목 조회
        
        Returns:
            보유 종목 리스트
            ```python
            [
                {
                    'ticker': 'AAPL',
                    'name': 'Apple Inc.',
                    'quantity': 100,
                    'avg_price': 150.0,
                    'current_price': 155.0,
                    'market_value': 15500.0,
                    'profit_loss': 500.0,
                    'profit_loss_pct': 3.33,
                    'daily_pnl': 300.0,
                    'daily_return_pct': 1.97,
                    'market': 'US'  # KR or US
                },
                ...
            ]
            ```
        """
        if not self.kis_broker:
            logger.warning("KIS Broker not available, returning empty holdings")
            return []
        
        try:
            # KIS Broker에서 잔고 조회
            balance = self.kis_broker.get_account_balance()
            
            if not balance or 'positions' not in balance:
                logger.warning("No positions found in KIS balance")
                return []
            
            positions = balance['positions']
            
            # 브리핑용 포맷으로 변환
            holdings = []
            for pos in positions:
                # KIS Broker 응답 포맷 변환
                holding = {
                    'ticker': pos.get('symbol', ''),
                    'name': pos.get('name', pos.get('symbol', '')),
                    'quantity': pos.get('quantity', 0),
                    'avg_price': pos.get('avg_price', 0.0),
                    'current_price': pos.get('current_price', 0.0),
                    'market_value': pos.get('market_value', 0.0),
                    'profit_loss': pos.get('profit_loss', 0.0),
                    'profit_loss_pct': 0.0,
                    'daily_pnl': pos.get('daily_pnl', 0.0),
                    'daily_return_pct': pos.get('daily_return_pct', 0.0),
                    'market': 'US'  # KIS는 미국 주식만 지원
                }
                
                # 총 수익률 계산
                if holding['avg_price'] > 0:
                    holding['profit_loss_pct'] = (
                        (holding['current_price'] - holding['avg_price']) / 
                        holding['avg_price'] * 100
                    )
                
                holdings.append(holding)
            
            logger.info(f"Retrieved {len(holdings)} holdings for briefing")
            return holdings
            
        except Exception as e:
            logger.error(f"Failed to get holdings for briefing: {e}", exc_info=True)
            return []
    
    async def check_portfolio_alerts(self) -> List[Dict[str, Any]]:
        """
        포트폴리오 알림 (±5% 변동)
        
        일일 변동 ±5% 이상 감지 시:
        1. API 검색으로 변동 원인 파악
        2. 텔레그램 알림 전송
        
        Returns:
            알림 리스트
            ```python
            [
                {
                    'ticker': 'AAPL',
                    'name': 'Apple Inc.',
                    'daily_return_pct': 6.5,
                    'alert_type': 'GAIN',  # GAIN or LOSS
                    'reason': 'Earnings beat expectations',
                    'timestamp': datetime.now()
                },
                ...
            ]
            ```
        """
        if not self.kis_broker:
            logger.warning("KIS Broker not available, skipping portfolio alerts")
            return []
        
        try:
            # 보유 종목 조회
            holdings = await self.get_holdings_for_briefing()
            
            if not holdings:
                logger.info("No holdings to check for alerts")
                return []
            
            alerts = []
            ALERT_THRESHOLD = 5.0  # ±5%
            
            for holding in holdings:
                daily_return_pct = holding.get('daily_return_pct', 0.0)
                ticker = holding.get('ticker', '')
                
                # ±5% 변동 확인
                if abs(daily_return_pct) >= ALERT_THRESHOLD:
                    alert_type = 'GAIN' if daily_return_pct > 0 else 'LOSS'
                    
                    # 변동 원인 파악 (뉴스 검색)
                    reason = await self._analyze_price_movement(ticker, daily_return_pct)
                    
                    alert = {
                        'ticker': ticker,
                        'name': holding.get('name', ticker),
                        'daily_return_pct': daily_return_pct,
                        'alert_type': alert_type,
                        'reason': reason,
                        'timestamp': datetime.now()
                    }
                    
                    alerts.append(alert)
                    
                    # 텔레그램 알림 전송
                    if self.telegram_notifier:
                        await self._send_portfolio_alert(alert)
            
            if alerts:
                logger.info(f"Generated {len(alerts)} portfolio alerts")
            else:
                logger.info("No portfolio alerts generated")
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to check portfolio alerts: {e}", exc_info=True)
            return []
    
    async def _analyze_price_movement(self, ticker: str, return_pct: float) -> str:
        """
        가격 변동 원인 분석
        
        뉴스 검색으로 변동 원인 파악
        
        Args:
            ticker: 종목 티커
            return_pct: 일일 수익률
            
        Returns:
            변동 원인 설명
        """
        try:
            # 뉴스 검색 (데이터베이스 쿼리)
            from backend.database.repository import get_sync_session
            from backend.database.models import NewsArticle
            
            # 최근 24시간 뉴스 검색
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            with get_sync_session() as db:
                # tickers 컬럼에서 해당 티커가 포함된 뉴스 검색
                news_items = db.query(NewsArticle).filter(
                    NewsArticle.published_date >= start_time,
                    NewsArticle.published_date <= end_time
                ).order_by(NewsArticle.published_date.desc()).limit(5).all()
            
            # 티커 필터링 (tickers 컬럼은 JSONB 형태)
            filtered_news = []
            for news in news_items:
                # tickers 컬럼이 있는지 확인
                if hasattr(news, 'tickers') and news.tickers:
                    # tickers가 리스트인 경우
                    if isinstance(news.tickers, list):
                        if ticker.upper() in [t.upper() for t in news.tickers]:
                            filtered_news.append(news)
                    # tickers가 문자열인 경우
                    elif isinstance(news.tickers, str):
                        if ticker.upper() in news.tickers.upper():
                            filtered_news.append(news)
            
            if filtered_news:
                # 뉴스 요약
                reasons = []
                for news in filtered_news[:3]:
                    title = getattr(news, 'title', '')
                    if title:
                        reasons.append(title)
                
                if reasons:
                    return " | ".join(reasons)
            
            # 뉴스가 없는 경우 기본 메시지
            direction = "상승" if return_pct > 0 else "하락"
            return f"{direction} ({abs(return_pct):.1f}%) - 뉴스 없음"
            
        except Exception as e:
            logger.warning(f"Failed to analyze price movement for {ticker}: {e}")
            direction = "상승" if return_pct > 0 else "하락"
            return f"{direction} ({abs(return_pct):.1f}%) - 분석 실패"
    
    async def _send_portfolio_alert(self, alert: Dict[str, Any]):
        """
        포트폴리오 알림 텔레그램 전송
        
        Args:
            alert: 알림 딕셔너리
        """
        try:
            emoji = "📈" if alert['alert_type'] == 'GAIN' else "📉"
            
            message = f"""
{emoji} 포트폴리오 알림

<b>{alert['name']} ({alert['ticker']})</b>
일일 변동: {alert['daily_return_pct']:+.2f}%

<b>변동 원인:</b>
{alert['reason']}
"""
            
            # 텔레그램 알림 전송
            if self.telegram_notifier:
                await self.telegram_notifier.send_message(
                    message=message,
                    parse_mode='HTML'
                )
            
            logger.info(f"Portfolio alert sent for {alert['ticker']}")
            
        except Exception as e:
            logger.error(f"Failed to send portfolio alert: {e}", exc_info=True)
    
    async def generate_briefing_section(self, holdings: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        브리핑 섹션 생성
        
        모든 브리핑에 포트폴리오 섹션 포함
        
        Args:
            holdings: 보유 종목 리스트 (옵션, 없으면 조회)
            
        Returns:
            브리핑 섹션
            ```python
            {
                'total_value': 100000.0,
                'total_pnl': 5000.0,
                'total_return_pct': 5.0,
                'daily_pnl': 1000.0,
                'daily_return_pct': 1.0,
                'positions': [
                    {
                        'ticker': 'AAPL',
                        'name': 'Apple Inc.',
                        'quantity': 100,
                        'avg_price': 150.0,
                        'current_price': 155.0,
                        'market_value': 15500.0,
                        'profit_loss': 500.0,
                        'profit_loss_pct': 3.33,
                        'daily_pnl': 300.0,
                        'daily_return_pct': 1.97,
                        'market': 'US'
                    },
                    ...
                ],
                'top_performers': [...],
                'bottom_performers': [...],
                'alert_count': 2
            }
            ```
        """
        try:
            # 보유 종목 조회
            if holdings is None:
                holdings = await self.get_holdings_for_briefing()
            
            if not holdings:
                return {
                    'total_value': 0.0,
                    'total_pnl': 0.0,
                    'total_return_pct': 0.0,
                    'daily_pnl': 0.0,
                    'daily_return_pct': 0.0,
                    'positions': [],
                    'top_performers': [],
                    'bottom_performers': [],
                    'alert_count': 0
                }
            
            # 총 계산
            total_value = sum(h.get('market_value', 0) for h in holdings)
            total_pnl = sum(h.get('profit_loss', 0) for h in holdings)
            daily_pnl = sum(h.get('daily_pnl', 0) for h in holdings)
            
            # 총 수익률 계산
            total_invested = sum(h.get('avg_price', 0) * h.get('quantity', 0) for h in holdings)
            total_return_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0
            daily_return_pct = (daily_pnl / (total_value - daily_pnl) * 100) if (total_value - daily_pnl) > 0 else 0.0
            
            # 상위/하위 종목 정렬
            sorted_by_daily = sorted(holdings, key=lambda x: x.get('daily_return_pct', 0), reverse=True)
            top_performers = sorted_by_daily[:3]
            bottom_performers = sorted_by_daily[-3:] if len(sorted_by_daily) > 3 else []
            
            # 알림 개수 계산
            alert_count = sum(1 for h in holdings if abs(h.get('daily_return_pct', 0)) >= 5.0)
            
            section = {
                'total_value': total_value,
                'total_pnl': total_pnl,
                'total_return_pct': total_return_pct,
                'daily_pnl': daily_pnl,
                'daily_return_pct': daily_return_pct,
                'positions': holdings,
                'top_performers': top_performers,
                'bottom_performers': bottom_performers,
                'alert_count': alert_count
            }
            
            logger.info(f"Generated briefing section: ${total_value:,.2f}, "
                       f"P&L: ${total_pnl:+,.2f} ({total_return_pct:+.2f}%), "
                       f"Daily: ${daily_pnl:+,.2f} ({daily_return_pct:+.2f}%), "
                       f"Alerts: {alert_count}")
            
            return section
            
        except Exception as e:
            logger.error(f"Failed to generate briefing section: {e}", exc_info=True)
            return {
                'total_value': 0.0,
                'total_pnl': 0.0,
                'total_return_pct': 0.0,
                'daily_pnl': 0.0,
                'daily_return_pct': 0.0,
                'positions': [],
                'top_performers': [],
                'bottom_performers': [],
                'alert_count': 0
            }
    
    async def get_alert_count(self) -> int:
        """
        포트폴리오 알림 개수 조회
        
        Returns:
            알림 개수
        """
        try:
            holdings = await self.get_holdings_for_briefing()
            alert_count = sum(1 for h in holdings if abs(h.get('daily_return_pct', 0)) >= 5.0)
            return alert_count
        except Exception as e:
            logger.error(f"Failed to get alert count: {e}", exc_info=True)
            return 0


# ========== Demo Function ==========

async def demo():
    """
    PortfolioAnalyzer 데모 함수
    """
    print("=" * 80)
    print("PHASE7: KIS 포트폴리오 통합 데모")
    print("=" * 80)
    
    # KIS Broker 초기화 (환경 변수 필요)
    kis_broker = None
    try:
        from backend.brokers.kis_broker import KISBroker
        
        account_no = os.getenv('KIS_ACCOUNT_NUMBER')
        if account_no:
            is_virtual = os.getenv('KIS_IS_VIRTUAL', 'true').lower() == 'true'
            kis_broker = KISBroker(account_no=account_no, is_virtual=is_virtual)
            print("\n✅ KIS Broker initialized")
        else:
            print("\n⚠️  KIS_ACCOUNT_NUMBER not set, using mock data")
    except Exception as e:
        print(f"\n⚠️  KIS Broker initialization failed: {e}")
    
    # PortfolioAnalyzer 초기화
    analyzer = PortfolioAnalyzer(kis_broker=kis_broker)
    
    # 1. 보유 종목 조회
    print("\n[1] 보유 종목 조회")
    print("-" * 80)
    holdings = await analyzer.get_holdings_for_briefing()
    
    if holdings:
        print(f"✅ {len(holdings)} 개 종목 조회 완료")
        for h in holdings[:3]:  # 최대 3개만 표시
            print(f"  - {h['ticker']}: {h['quantity']} shares @ ${h['avg_price']:.2f} "
                  f"→ ${h['current_price']:.2f} ({h['daily_return_pct']:+.2f}%)")
    else:
        print("⚠️  보유 종목 없음 (KIS Broker 연결 필요)")
        # Mock 데이터 사용
        holdings = [
            {
                'ticker': 'AAPL',
                'name': 'Apple Inc.',
                'quantity': 100,
                'avg_price': 150.0,
                'current_price': 155.0,
                'market_value': 15500.0,
                'profit_loss': 500.0,
                'daily_pnl': 300.0,
                'daily_return_pct': 1.97,
                'market': 'US'
            },
            {
                'ticker': 'NVDA',
                'name': 'NVIDIA Corp.',
                'quantity': 50,
                'avg_price': 400.0,
                'current_price': 450.0,
                'market_value': 22500.0,
                'profit_loss': 2500.0,
                'daily_pnl': 1000.0,
                'daily_return_pct': 2.27,
                'market': 'US'
            }
        ]
        print(f"  Mock 데이터: {len(holdings)} 개 종목")
    
    # 2. 포트폴리오 알림 확인
    print("\n[2] 포트폴리오 알림 확인 (±5% 변동)")
    print("-" * 80)
    alerts = await analyzer.check_portfolio_alerts()
    
    if alerts:
        print(f"✅ {len(alerts)} 개 알림 발생")
        for alert in alerts:
            emoji = "📈" if alert['alert_type'] == 'GAIN' else "📉"
            print(f"  {emoji} {alert['ticker']} ({alert['name']}): "
                  f"{alert['daily_return_pct']:+.2f}% - {alert['reason']}")
    else:
        print("✅ 알림 없음 (±5% 이내 변동)")
    
    # 3. 브리핑 섹션 생성
    print("\n[3] 브리핑 섹션 생성")
    print("-" * 80)
    section = await analyzer.generate_briefing_section(holdings)
    
    print(f"✅ 브리핑 섹션 생성 완료")
    print(f"  총 자산: ${section['total_value']:,.2f}")
    print(f"  총 수익: ${section['total_pnl']:+,.2f} ({section['total_return_pct']:+.2f}%)")
    print(f"  일일 수익: ${section['daily_pnl']:+,.2f} ({section['daily_return_pct']:+.2f}%)")
    print(f"  알림 개수: {section['alert_count']}")
    
    if section['top_performers']:
        print(f"\n  📈 상위 종목:")
        for p in section['top_performers']:
            print(f"    - {p['ticker']}: {p['daily_return_pct']:+.2f}%")
    
    if section['bottom_performers']:
        print(f"\n  📉 하위 종목:")
        for p in section['bottom_performers']:
            print(f"    - {p['ticker']}: {p['daily_return_pct']:+.2f}%")
    
    # 4. 알림 개수 조회
    print("\n[4] 알림 개수 조회")
    print("-" * 80)
    alert_count = await analyzer.get_alert_count()
    print(f"✅ 현재 알림 개수: {alert_count}")
    
    print("\n" + "=" * 80)
    print("PHASE7 데모 완료")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
