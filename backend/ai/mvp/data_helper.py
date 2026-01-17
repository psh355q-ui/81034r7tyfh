"""
War Room MVP - Data Helper
데이터 수집 및 준비
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# PostgreSQL 모델 사용 (backend.database.models)
from backend.database.models import NewsArticle
from backend.database.repository import NewsRepository
from backend.data.rss_crawler import get_recent_articles
# news_analyzer는 의존성 문제로 조건부 import
try:
    from backend.data.news_analyzer import get_ticker_news
    GET_TICKER_NEWS_AVAILABLE = True
except ImportError:
    GET_TICKER_NEWS_AVAILABLE = False
    get_ticker_news = None
from backend.ai.mvp.ticker_mappings import get_ticker_keywords


def get_news_for_symbol(
    symbol: str,
    db: Session,
    hours: int = 24,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    특정 심볼에 대한 뉴스 기사 가져오기
    
    영문명 + 한글명 + 티커로 검색하여 한글 뉴스도 정확히 매칭
    
    Args:
        symbol: 티커 심볼 (예: TSLA, AAPL)
        db: DB 세션
        hours: 최근 N시간 (기본 24시간)
        limit: 최대 개수 (기본 10개)
        
    Returns:
        뉴스 기사 리스트
    """
    try:
        # 1. 티커별 뉴스 먼저 시도 (NewsTickerRelevance 테이블)
        if GET_TICKER_NEWS_AVAILABLE and get_ticker_news:
            ticker_news = get_ticker_news(db, symbol.upper(), limit)

            if ticker_news:
                print(f"   → Found {len(ticker_news)} articles from ticker mapping")
                return [
                    {
                        'title': article.get('title', ''),
                        'source': article.get('source', 'Unknown'),
                        'published': article.get('published_at', datetime.utcnow().isoformat()),
                        'summary': article.get('summary', ''),
                        'sentiment': article.get('sentiment'),
                        'url': article.get('url', '')
                    }
                    for article in ticker_news[:limit]
                ]

        # 2. 키워드 검색 (영문명 + 한글명 + 티커)
        keywords = get_ticker_keywords(symbol)
        print(f"   → Searching with keywords: {keywords}")
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = db.query(NewsArticle).filter(
            NewsArticle.crawled_at >= cutoff_time
        )
        
        # 모든 키워드에 대해 OR 조건으로 검색
        from sqlalchemy import or_
        
        conditions = []
        for keyword in keywords:
            conditions.extend([
                NewsArticle.title.ilike(f'%{keyword}%'),
                NewsArticle.summary.ilike(f'%{keyword}%'),
                NewsArticle.content.ilike(f'%{keyword}%')
            ])
        
        query = query.filter(or_(*conditions))
        
        articles = query.order_by(
            NewsArticle.published_date.desc()
        ).limit(limit).all()
        
        print(f"   → Found {len(articles)} articles from keyword search")
        
        return [
            {
                'title': a.title,
                'source': a.source or 'RSS',
                'published': a.published_date.isoformat() if a.published_date else datetime.utcnow().isoformat(),
                'summary': a.summary or (a.content[:200] if a.content else ''),
                'sentiment': a.sentiment_label or 'neutral',
                'url': a.url
            }
            for a in articles
        ]
        
    except Exception as e:
        print(f"⚠️ Failed to fetch news for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return []


def prepare_additional_data(
    symbol: str,
    db: Session
) -> Dict[str, Any]:
    """
    War Room MVP를 위한 추가 데이터 준비
    
    Args:
        symbol: 티커 심볼
        db: DB 세션
        
    Returns:
        additional_data 딕셔너리
    """
    # News Articles (최근 24시간, 최대 10개)
    news_articles = get_news_for_symbol(symbol, db, hours=24, limit=10)
    
    # Macro Indicators (TODO: 외부 API 연동)
    macro_indicators = {
        'interest_rate': 5.25,  # Fed Funds Rate (mock)
        'inflation_rate': 3.2,  # CPI (mock)
        'vix': 18.5,  # Volatility Index (mock)
        'yield_curve': {
            '2y': 4.5,
            '10y': 4.2
        }
    }
    
    # Institutional Data (TODO: 13F filings, insider trading)
    institutional_data = {
        'recent_activity': 'accumulation',  # mock
        'confidence': 0.6  # mock
    }
    
    # ChipWar Events (반도체 관련 종목에만 적용)
    chipwar_events = []
    if any(keyword in symbol.upper() for keyword in ['NVDA', 'AMD', 'INTC', 'TSM', 'ASML']):
        chipwar_events = [
            {
                'event_type': 'export_control',
                'severity': 'medium',
                'date': datetime.utcnow().isoformat()
            }
        ]
    
    return {
        'news_articles': news_articles,
        'macro_indicators': macro_indicators,
        'institutional_data': institutional_data,
        'chipwar_events': chipwar_events,
        'correlation_data': None  # TODO: 상관관계 데이터
    }
