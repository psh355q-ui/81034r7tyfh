"""
Google News RSS 수집기
무료, API 키 불필요, bot 차단 없음
"""
import aiohttp
from xml.etree import ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class GoogleNewsRSSCollector:
    """
    Google News RSS 수집기
    
    장점:
    - 무료, 무제한
    - API 키 불필요
    - bot 차단 없음
    - 전 세계 뉴스 커버리지
    
    단점:
    - 5-15분 지연
    - Forex Factory보다 느림
    """
    
    BASE_URL = "https://news.google.com/rss/search"
    
    async def search_news(
        self, 
        query: str,
        hours_back: int = 2
    ) -> List[Dict[str, Any]]:
        """
        뉴스 검색
        
        Args:
            query: 검색어 (e.g., "Williams Federal Reserve")
            hours_back: 몇 시간 전 뉴스까지 (기본 2시간)
        
        Returns:
            뉴스 기사 리스트
        """
        try:
            # URL 인코딩
            encoded_query = quote_plus(query)
            
            # Google News RSS URL
            url = f"{self.BASE_URL}?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.error(f"Google News returned {resp.status}")
                        return []
                    
                    xml_content = await resp.text()
            
            # XML 파싱
            root = ET.fromstring(xml_content)
            
            articles = []
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                pub_date_elem = item.find('pubDate')
                description_elem = item.find('description')
                source_elem = item.find('source')
                
                if not title_elem or not link_elem:
                    continue
                
                title = title_elem.text
                link = link_elem.text
                pub_date_str = pub_date_elem.text if pub_date_elem is not None else ''
                description = description_elem.text if description_elem is not None else ''
                source = source_elem.text if source_elem is not None else 'Unknown'
                
                # 발행 시간 파싱
                try:
                    pub_date = self._parse_rss_date(pub_date_str)
                except:
                    pub_date = datetime.now()
                
                # 시간 필터링
                time_diff_hours = (datetime.now() - pub_date).total_seconds() / 3600
                if time_diff_hours > hours_back:
                    continue
                
                articles.append({
                    'title': title,
                    'link': link,
                    'published_at': pub_date,
                    'source': source,
                    'description': description,
                    'query': query
                })
            
            return articles
        
        except Exception as e:
            logger.error(f"Google News search error: {e}", exc_info=True)
            return []
    
    async def search_fed_speech(
        self, 
        official_name: str,
        speech_topic: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        특정 연준 의원의 발언 뉴스 검색
        
        Args:
            official_name: 의원 이름 (e.g., "Williams", "Powell")
            speech_topic: 발언 주제 (옵션)
        
        Returns:
            가장 최근 뉴스 또는 None
        """
        # 검색 쿼리 구성
        if speech_topic:
            query = f"{official_name} Federal Reserve {speech_topic}"
        else:
            query = f"{official_name} Federal Reserve speech"
        
        articles = await self.search_news(query, hours_back=1)
        
        if not articles:
            # 더 넓은 검색
            query = f"{official_name} Fed"
            articles = await self.search_news(query, hours_back=2)
        
        if articles:
            # 가장 최근 기사 반환
            return articles[0]
        
        return None
    
    async def search_economic_event(
        self, 
        event_name: str
    ) -> List[Dict[str, Any]]:
        """
        경제 이벤트 뉴스 검색
        
        Args:
            event_name: 이벤트 이름 (e.g., "CPI", "NFP", "GDP")
        
        Returns:
            관련 뉴스 리스트
        """
        # 여러 검색어 시도
        queries = [
            f"{event_name} report",
            f"{event_name} data",
            f"US {event_name}",
        ]
        
        all_articles = []
        
        for query in queries:
            articles = await self.search_news(query, hours_back=1)
            all_articles.extend(articles)
        
        # 중복 제거 (같은 링크)
        seen_links = set()
        unique_articles = []
        
        for article in all_articles:
            if article['link'] not in seen_links:
                seen_links.add(article['link'])
                unique_articles.append(article)
        
        # 발행 시간 순 정렬
        unique_articles.sort(key=lambda x: x['published_at'], reverse=True)
        
        return unique_articles
    
    def _parse_rss_date(self, date_str: str) -> datetime:
        """
        RSS 날짜 형식 파싱
        
        예: "Wed, 17 Dec 2025 14:30:00 GMT"
        """
        from email.utils import parsedate_to_datetime
        
        try:
            return parsedate_to_datetime(date_str)
        except:
            # Fallback
            return datetime.now()
