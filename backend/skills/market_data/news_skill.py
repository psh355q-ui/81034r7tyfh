"""
News Skill

뉴스 수집 및 검색 Skill

Author: AI Trading System
Date: 2025-12-04
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from backend.skills.base_skill import BaseSkill, SkillCategory, CostTier

logger = logging.getLogger(__name__)


class NewsSkill(BaseSkill):
    """
    뉴스 수집 및 검색 Skill

    기능:
    - 뉴스 검색 (키워드 기반)
    - 최신 뉴스 조회
    - 티커별 뉴스 필터링

    Usage:
        skill = NewsSkill()
        tools = skill.get_tools()
        result = await skill.execute("search_news", keyword="AAPL", max_results=20)
    """

    def __init__(self):
        """초기화"""
        super().__init__(
            name="MarketData.News",
            category=SkillCategory.MARKET_DATA,
            description="실시간 뉴스 수집, 검색, 필터링",
            keywords=[
                "뉴스", "news", "기사", "article", "언론", "보도",
                "뉴스검색", "news search", "최신뉴스", "latest news"
            ],
            cost_tier=CostTier.FREE,  # RSS 기반이므로 무료
            requires_api_key=False,
            rate_limit_per_min=None,
        )

        # 뉴스 크롤러 초기화 (지연 로딩)
        self._crawler = None

    def _get_crawler(self):
        """뉴스 크롤러 가져오기 (지연 로딩)"""
        if self._crawler is None:
            try:
                from backend.data.news_crawler import NaverNewsCrawler
                self._crawler = NaverNewsCrawler()
                logger.info("News crawler initialized")
            except ImportError:
                logger.error("Failed to import NaverNewsCrawler")
                raise

        return self._crawler

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        News Skill이 제공하는 도구 목록

        Returns:
            도구 정의 리스트
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_news",
                    "description": "키워드로 뉴스 검색. 특정 기업이나 주제에 대한 최신 뉴스를 찾을 때 사용.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "검색 키워드 (예: 'AAPL', '삼성전자', 'AI technology')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "최대 결과 수 (기본값: 20)",
                                "default": 20
                            },
                            "language": {
                                "type": "string",
                                "description": "언어 필터 (ko, en)",
                                "enum": ["ko", "en", "all"],
                                "default": "all"
                            }
                        },
                        "required": ["keyword"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_latest_news",
                    "description": "최신 뉴스 조회. 특정 카테고리의 최근 뉴스를 가져올 때 사용.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "뉴스 카테고리",
                                "enum": ["all", "economy", "stock", "tech", "politics"],
                                "default": "all"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "가져올 뉴스 개수 (기본값: 10)",
                                "default": 10
                            },
                            "hours": {
                                "type": "integer",
                                "description": "최근 N시간 이내 뉴스만 (기본값: 24시간)",
                                "default": 24
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_news_by_ticker",
                    "description": "특정 티커(종목)의 관련 뉴스 조회",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "종목 티커 (예: 'AAPL', '005930')"
                            },
                            "days": {
                                "type": "integer",
                                "description": "최근 N일간 뉴스 (기본값: 7일)",
                                "default": 7
                            },
                            "min_relevance": {
                                "type": "number",
                                "description": "최소 연관성 점수 (0-1, 기본값: 0.5)",
                                "default": 0.5
                            }
                        },
                        "required": ["ticker"]
                    }
                }
            }
        ]

    async def execute(self, tool_name: str, **kwargs) -> Any:
        """
        도구 실행

        Args:
            tool_name: 실행할 도구 이름
            **kwargs: 도구 파라미터

        Returns:
            실행 결과

        Raises:
            ValueError: 알 수 없는 도구
        """
        try:
            if tool_name == "search_news":
                result = await self._search_news(**kwargs)
            elif tool_name == "get_latest_news":
                result = await self._get_latest_news(**kwargs)
            elif tool_name == "get_news_by_ticker":
                result = await self._get_news_by_ticker(**kwargs)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            # 통계 업데이트
            self._track_call(success=True, cost_usd=0.0)  # RSS는 무료

            return result

        except Exception as e:
            # 오류 추적
            self._track_call(success=False)
            logger.error(f"Error executing {tool_name}: {e}")
            raise

    async def _search_news(
        self,
        keyword: str,
        max_results: int = 20,
        language: str = "all"
    ) -> Dict[str, Any]:
        """
        뉴스 검색

        Args:
            keyword: 검색 키워드
            max_results: 최대 결과 수
            language: 언어 필터

        Returns:
            검색 결과
        """
        crawler = self._get_crawler()

        # 뉴스 검색 (실제 구현은 crawler에 따라 다름)
        articles = await crawler.search_news(keyword, max_results)

        # 언어 필터링
        if language != "all":
            articles = [a for a in articles if self._detect_language(a.get("title", "")) == language]

        return {
            "success": True,
            "keyword": keyword,
            "total_results": len(articles),
            "articles": [
                {
                    "title": a.get("title"),
                    "source": a.get("source"),
                    "published_at": a.get("published_at"),
                    "url": a.get("url"),
                    "summary": a.get("summary", "")[:200],  # 요약 200자
                }
                for a in articles
            ]
        }

    async def _get_latest_news(
        self,
        category: str = "all",
        limit: int = 10,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        최신 뉴스 조회

        Args:
            category: 카테고리
            limit: 결과 개수
            hours: 최근 N시간

        Returns:
            뉴스 목록
        """
        crawler = self._get_crawler()

        # 시간 필터
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # 뉴스 조회
        articles = await crawler.get_latest(category, limit * 2)  # 여유분 조회

        # 시간 필터링
        filtered = [
            a for a in articles
            if a.get("published_at", datetime.min) >= cutoff_time
        ][:limit]

        return {
            "success": True,
            "category": category,
            "total_results": len(filtered),
            "articles": [
                {
                    "title": a.get("title"),
                    "source": a.get("source"),
                    "published_at": a.get("published_at").isoformat() if a.get("published_at") else None,
                    "url": a.get("url"),
                }
                for a in filtered
            ]
        }

    async def _get_news_by_ticker(
        self,
        ticker: str,
        days: int = 7,
        min_relevance: float = 0.5
    ) -> Dict[str, Any]:
        """
        티커별 뉴스 조회

        Args:
            ticker: 종목 티커
            days: 최근 N일
            min_relevance: 최소 연관성

        Returns:
            관련 뉴스 목록
        """
        try:
            from backend.data.news_models import get_db, NewsArticle
            from sqlalchemy import and_

            # DB에서 조회
            db = next(get_db())
            cutoff_date = datetime.now() - timedelta(days=days)

            articles = (
                db.query(NewsArticle)
                .filter(
                    and_(
                        NewsArticle.published_at >= cutoff_date,
                        NewsArticle.ticker_relevances.any(
                            and_(
                                NewsArticle.ticker_relevances.ticker == ticker,
                                NewsArticle.ticker_relevances.relevance_score >= min_relevance
                            )
                        )
                    )
                )
                .order_by(NewsArticle.published_at.desc())
                .limit(50)
                .all()
            )

            return {
                "success": True,
                "ticker": ticker,
                "total_results": len(articles),
                "articles": [
                    {
                        "title": a.title,
                        "source": a.source,
                        "published_at": a.published_at.isoformat() if a.published_at else None,
                        "url": a.url,
                        "relevance_score": next(
                            (rel.relevance_score for rel in a.ticker_relevances if rel.ticker == ticker),
                            0.0
                        ),
                    }
                    for a in articles
                ]
            }

        except ImportError:
            # DB 모델이 없으면 검색으로 대체
            logger.warning("NewsArticle model not found, falling back to search")
            return await self._search_news(keyword=ticker, max_results=20)

    def _detect_language(self, text: str) -> str:
        """
        간단한 언어 감지

        Args:
            text: 텍스트

        Returns:
            'ko' 또는 'en'
        """
        # 한글이 포함되어 있으면 한국어
        if any('\uac00' <= char <= '\ud7a3' for char in text):
            return "ko"
        return "en"
