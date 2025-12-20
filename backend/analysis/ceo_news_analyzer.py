"""
CEO News Analyzer - Phase 15 Tier 3

뉴스 기반 CEO 발언 분석 시스템:
- 실시간 뉴스에서 CEO 발언 추출
- Claude로 발언 의도 분석
- RAG로 과거 유사 발언 검색
- SEC 공시와 교차 검증
"""

import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from backend.services.fast_polling_service import FastNewsItem
from backend.data.vector_store.store import VectorStore
from anthropic import AsyncAnthropic


logger = logging.getLogger(__name__)


# ============================================
# Data Models
# ============================================

@dataclass
class CEOQuote:
    """뉴스에서 추출한 CEO 발언"""
    text: str
    source: str  # "news" | "sec_filing"
    ticker: str
    published_at: datetime
    news_url: Optional[str] = None
    sentiment: Optional[float] = None
    analyzed: bool = False
    confidence: float = 0.0


@dataclass
class CrossValidation:
    """SEC 교차 검증 결과"""
    consistent: Optional[bool]
    discrepancy: Optional[str]
    alert_level: str  # "NONE" | "LOW" | "HIGH"
    sec_sentiment: Optional[float] = None
    news_sentiment: Optional[float] = None


# ============================================
# CEO News Analyzer
# ============================================

class CEONewsAnalyzer:
    """
    뉴스 기반 CEO 발언 분석기
    
    Features:
    - 실시간 뉴스에서 CEO 발언 추출
    - Claude로 발언 의도 분석
    - RAG로 과거 유사 발언 검색
    - SEC 공시와 교차 검증
    
    Usage:
        analyzer = CEONewsAnalyzer(vector_store, claude_client)
        quotes = await analyzer.analyze_news_for_ceo_quotes(news_items)
    """
    
    # 회사명 → 티커 매핑 (주요 종목)
    COMPANY_TO_TICKER = {
        "nvidia": "NVDA",
        "apple": "AAPL",
        "microsoft": "MSFT",
        "tesla": "TSLA",
        "amazon": "AMZN",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "meta": "META",
        "facebook": "META",
        "netflix": "NFLX",
        "amd": "AMD",
        "intel": "INTC",
        "qualcomm": "QCOM",
        "broadcom": "AVGO",
        "salesforce": "CRM",
        "oracle": "ORCL",
        "adobe": "ADBE",
        "cisco": "CSCO",
        "ibm": "IBM",
        "paypal": "PYPL",
    }
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        claude_client: Optional[AsyncAnthropic] = None
    ):
        """
        Initialize CEO News Analyzer
        
        Args:
            vector_store: VectorStore instance for RAG
            claude_client: Claude API client for sentiment analysis
        """
        self.vector_store = vector_store
        self.claude_client = claude_client
        self.ceo_quotes_cache: List[CEOQuote] = []
    
    async def analyze_news_for_ceo_quotes(
        self,
        news_items: List[FastNewsItem]
    ) -> List[CEOQuote]:
        """
        뉴스에서 CEO 발언 추출 및 분석
        
        Args:
            news_items: Fast Polling Service에서 수집한 뉴스
            
        Returns:
            CEO 발언 목록
        """
        ceo_quotes = []
        
        for news_item in news_items:
            # CEO 발언 추출
            quote = self._extract_ceo_quote(news_item)
            if not quote:
                continue
            
            # Claude로 발언 의도 분석 (선택적)
            if self.claude_client:
                try:
                    analysis = await self._analyze_quote_intent(quote)
                    quote.sentiment = analysis.get("sentiment", 0.0)
                    quote.confidence = analysis.get("confidence_score", 0.0)
                    quote.analyzed = True
                except Exception as e:
                    logger.error(f"Failed to analyze quote intent: {e}")
            
            # RAG로 과거 유사 발언 검색 (선택적)
            if self.vector_store:
                try:
                    similar = await self.vector_store.find_similar_ceo_statements(
                        current_statement=quote.text,
                        ticker=quote.ticker,
                        top_k=3
                    )
                    
                    # 유사 발언이 있고 결과가 부정적이면 경고
                    if similar and any(
                        m.get("outcome") and "NEGATIVE" in str(m.get("outcome"))
                        for m in similar
                    ):
                        logger.warning(
                            f"[CEO QUOTE WARNING] {quote.ticker}: Similar past statement "
                            f"had negative outcome. Quote: {quote.text[:100]}..."
                        )
                except Exception as e:
                    logger.error(f"Failed to search similar statements: {e}")
            
            ceo_quotes.append(quote)
            
            # Vector Store에 저장 (선택적)
            if self.vector_store:
                try:
                    await self._store_quote(quote)
                except Exception as e:
                    logger.error(f"Failed to store quote: {e}")
        
        logger.info(f"Extracted {len(ceo_quotes)} CEO quotes from {len(news_items)} news items")
        return ceo_quotes
    
    def _extract_ceo_quote(self, news_item: FastNewsItem) -> Optional[CEOQuote]:
        """
        뉴스에서 CEO 발언 추출
        
        Args:
            news_item: 뉴스 아이템
            
        Returns:
            CEOQuote 또는 None
        """
        title = news_item.title
        
        # CEO 발언 패턴
        patterns = [
            # "CEO says..."
            r'ceo\s+(?:says?|said|stated?|announced?|warned?|expects?)[:\s]+["\']?([^"\']{20,200})',
            # "CEO John Smith: '...'"
            r'(?:ceo|chief executive)\s+(\w+\s+\w+)[:\s]+["\']([^"\']{20,200})',
            # "According to CEO..."
            r'according to (?:the\s+)?ceo[,\s]+["\']?([^"\']{20,200})',
            # "'...' said CEO"
            r'"([^"]{20,200})"\s+(?:said|says|stated)\s+(?:the\s+)?ceo',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                # 마지막 그룹이 발언 내용
                quote_text = match.group(match.lastindex)
                
                # 티커 추출
                ticker = self._extract_ticker(title)
                if not ticker:
                    continue
                
                return CEOQuote(
                    text=quote_text.strip(),
                    source="news",
                    ticker=ticker,
                    published_at=news_item.published_at,
                    news_url=news_item.url,
                    sentiment=news_item.sentiment
                )
        
        return None
    
    def _extract_ticker(self, text: str) -> Optional[str]:
        """
        텍스트에서 티커 추출
        
        Args:
            text: 뉴스 제목 또는 본문
            
        Returns:
            티커 심볼 또는 None
        """
        text_lower = text.lower()
        
        # 회사명 → 티커 매핑
        for company, ticker in self.COMPANY_TO_TICKER.items():
            if company in text_lower:
                return ticker
        
        # 티커 직접 매칭 (대문자 1-5자)
        ticker_match = re.search(r'\b([A-Z]{1,5})\b', text)
        if ticker_match:
            potential_ticker = ticker_match.group(1)
            # 일반적인 단어 제외
            if potential_ticker not in ["CEO", "CFO", "AI", "US", "UK", "EU", "IPO"]:
                return potential_ticker
        
        return None
    
    async def _analyze_quote_intent(self, quote: CEOQuote) -> Dict:
        """
        Claude로 CEO 발언 의도 분석
        
        Args:
            quote: CEO Quote
            
        Returns:
            분석 결과 딕셔너리
        """
        if not self.claude_client:
            return {}
        
        prompt = f"""Analyze this CEO statement:

Ticker: {quote.ticker}
Quote: "{quote.text}"
Source: {quote.source}

Assess:
1. Sentiment (-1.0 to +1.0)
2. Confidence level (HIGH/MEDIUM/LOW)
3. Forward-looking or retrospective?
4. Any hedging language?
5. Key message

Output JSON only:
{{
  "sentiment": 0.0,
  "confidence_level": "MEDIUM",
  "is_forward_looking": true,
  "has_hedging": false,
  "key_message": "Brief summary",
  "confidence_score": 0.8
}}
"""
        
        try:
            response = await self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            import json
            result_text = response.content[0].text
            result = json.loads(result_text)
            
            return result
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {}
    
    async def _store_quote(self, quote: CEOQuote):
        """
        Vector Store에 CEO 발언 저장
        
        Args:
            quote: CEO Quote
        """
        if not self.vector_store:
            return
        
        await self.vector_store.add_document(
            ticker=quote.ticker,
            doc_type="ceo_quote",
            content=quote.text,
            metadata={
                "source": quote.source,
                "published_at": quote.published_at.isoformat(),
                "sentiment": quote.sentiment,
                "news_url": quote.news_url,
                "confidence": quote.confidence
            },
            document_date=quote.published_at,
            auto_tag=True
        )
    
    async def cross_validate_with_sec(
        self,
        ticker: str,
        news_quote: CEOQuote
    ) -> CrossValidation:
        """
        뉴스 발언과 SEC 공시 교차 검증
        
        Args:
            ticker: 주식 티커
            news_quote: 뉴스에서 추출한 CEO 발언
            
        Returns:
            CrossValidation 결과
        """
        # 최근 SEC 분석 조회 (placeholder)
        # 실제 구현 시 데이터베이스에서 조회
        sec_analysis = await self._get_latest_sec_analysis(ticker)
        
        if not sec_analysis:
            return CrossValidation(
                consistent=None,
                discrepancy=None,
                alert_level="NONE"
            )
        
        # 감정 비교
        sec_sentiment = sec_analysis.get("sentiment_score", 0.0)
        news_sentiment = news_quote.sentiment or 0.0
        
        sentiment_diff = abs(sec_sentiment - news_sentiment)
        
        if sentiment_diff > 0.5:
            # 큰 불일치
            return CrossValidation(
                consistent=False,
                discrepancy=f"SEC sentiment: {sec_sentiment:.2f}, News: {news_sentiment:.2f}",
                alert_level="HIGH",
                sec_sentiment=sec_sentiment,
                news_sentiment=news_sentiment
            )
        elif sentiment_diff > 0.3:
            return CrossValidation(
                consistent=False,
                discrepancy=f"Moderate difference: {sentiment_diff:.2f}",
                alert_level="LOW",
                sec_sentiment=sec_sentiment,
                news_sentiment=news_sentiment
            )
        else:
            return CrossValidation(
                consistent=True,
                discrepancy=None,
                alert_level="NONE",
                sec_sentiment=sec_sentiment,
                news_sentiment=news_sentiment
            )
    
    async def _get_latest_sec_analysis(self, ticker: str) -> Optional[Dict]:
        """
        최근 SEC 분석 결과 조회 (placeholder)
        
        Args:
            ticker: 주식 티커
            
        Returns:
            SEC 분석 결과 또는 None
        """
        # TODO: 실제 데이터베이스에서 조회
        # 현재는 placeholder
        return None


# ============================================
# Utility Functions
# ============================================

def extract_ceo_quotes_from_news_batch(
    news_items: List[FastNewsItem]
) -> List[CEOQuote]:
    """
    뉴스 배치에서 CEO 발언 추출 (동기 버전)
    
    Args:
        news_items: 뉴스 아이템 목록
        
    Returns:
        CEO Quote 목록
    """
    analyzer = CEONewsAnalyzer()
    quotes = []
    
    for news_item in news_items:
        quote = analyzer._extract_ceo_quote(news_item)
        if quote:
            quotes.append(quote)
    
    return quotes
