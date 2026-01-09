"""
Unified News Processor

통합 뉴스 처리 파이프라인:
크롤링 → 중복 제거 → 분석 → 저장을 원자적으로 처리

Features:
- URL + Content Hash + Semantic 중복 체크
- 선택적 분석 (중요 뉴스만)
- 원자적 DB 저장
- 배치 처리 지원
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session
from backend.data.news_models import NewsArticle, NewsAnalysis, NewsTickerRelevance
from backend.data.rss_crawler import generate_content_hash
from backend.data.news_analyzer import NewsDeepAnalyzer
from backend.ai.llm.local_embeddings import LocalEmbeddingService
from backend.ai.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class ProcessedNews:
    """처리된 뉴스 결과"""
    article: NewsArticle
    analysis: Optional[NewsAnalysis]
    was_analyzed: bool
    skipped_reason: Optional[str] = None


@dataclass
class ProcessingResult:
    """배치 처리 결과"""
    processed: List[ProcessedNews]
    skipped: List[Dict[str, Any]]
    errors: List[Exception]


class UnifiedNewsProcessor:
    """
    통합 뉴스 처리기
    
    크롤링된 원시 기사를 받아서:
    1. URL 중복 체크
    2. Content Hash 중복 체크
    3. Semantic 중복 체크 (선택)
    4. 임베딩 생성
    5. 분석 (선택)
    6. DB 저장 (원자적)
    """
    
    def __init__(
        self,
        db: Session,
        semantic_dedup: bool = False,
        semantic_threshold: float = 0.95,
        analyze_all: bool = False
    ):
        self.db = db
        self.semantic_dedup = semantic_dedup
        self.semantic_threshold = semantic_threshold
        self.analyze_all = analyze_all
        
        # Services
        self.embedding_service = LocalEmbeddingService()
        self.ollama_client = OllamaClient()
        self.analyzer = NewsDeepAnalyzer(db)
        
        # Stats
        self.stats = {
            "total": 0,
            "skipped_url": 0,
            "skipped_hash": 0,
            "skipped_semantic": 0,
            "saved": 0,
            "analyzed": 0,
            "errors": 0
        }
    
    def _check_url_duplicate(self, url: str) -> bool:
        """URL 중복 체크"""
        existing = self.db.query(NewsArticle).filter(NewsArticle.url == url).first()
        return existing is not None
    
    def _check_hash_duplicate(self, content_hash: str) -> bool:
        """Content Hash 중복 체크"""
        existing = self.db.query(NewsArticle).filter(
            NewsArticle.content_hash == content_hash
        ).first()
        return existing is not None
    
    def _check_semantic_duplicate(
        self,
        title: str,
        content: str,
        embedding: List[float]
    ) -> Optional[NewsArticle]:
        """
        의미적 중복 체크 (임베딩 유사도)
        
        최근 24시간 기사와 비교하여 유사도 > threshold면 중복으로 판단
        """
        if not self.semantic_dedup:
            return None
        
        # 최근 24시간 기사 조회
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_articles = (
            self.db.query(NewsArticle)
            .filter(NewsArticle.published_date >= cutoff)
            .filter(NewsArticle.embedding.isnot(None))
            .limit(100)  # 최대 100개만 비교
            .all()
        )
        
        # 코사인 유사도 계산
        import numpy as np
        new_emb = np.array(embedding)
        
        for article in recent_articles:
            if article.embedding:
                old_emb = np.array(article.embedding)
                
                # 코사인 유사도
                similarity = np.dot(new_emb, old_emb) / (
                    np.linalg.norm(new_emb) * np.linalg.norm(old_emb)
                )
                
                if similarity > self.semantic_threshold:
                    logger.info(
                        f"Semantic duplicate found (similarity: {similarity:.3f})\n"
                        f"  New: {title[:50]}...\n"
                        f"  Old: {article.title[:50]}..."
                    )
                    return article
        
        return None
    
    def _should_analyze(self, article_data: Dict[str, Any]) -> bool:
        """
        분석 여부 결정
        
        analyze_all=True면 모두 분석
        아니면 중요한 것만 분석 (키워드 기반)
        """
        if self.analyze_all:
            return True
        
        # 중요 키워드 체크
        important_keywords = [
            "earnings", "merger", "acquisition", "lawsuit", "bankruptcy",
            "FDA", "approval", "recall", "layoff", "CEO", "dividend",
            "실적", "인수", "합병", "소송", "파산", "승인", "리콜", "해고", "배당"
        ]
        
        title = article_data.get("title", "").lower()
        content = article_data.get("content", "").lower()
        
        for keyword in important_keywords:
            if keyword.lower() in title or keyword.lower() in content:
                return True
        
        return False
    
    async def process_article(
        self,
        raw_article: Dict[str, Any]
    ) -> Optional[ProcessedNews]:
        """
        단일 기사 처리
        
        Args:
            raw_article: 크롤링된 원시 기사 데이터
            
        Returns:
            ProcessedNews: 처리된 결과
            None: 중복으로 스킵됨
        """
        self.stats["total"] += 1
        
        url = raw_article.get("url", "")
        title = raw_article.get("title", "")
        content = raw_article.get("content", "")
        
        if not url or not title:
            logger.warning("Skipped: Missing URL or title")
            return None
        
        try:
            # Stage 1: URL 중복 체크
            if self._check_url_duplicate(url):
                self.stats["skipped_url"] += 1
                logger.debug(f"Skipped (URL): {title[:50]}...")
                return None
            
            # Stage 2: Content Hash 중복 체크
            content_hash = None
            if content and len(content) > 50:
                content_hash = generate_content_hash(title, content)
                
                if self._check_hash_duplicate(content_hash):
                    self.stats["skipped_hash"] += 1
                    logger.info(f"Skipped (Hash): {title[:50]}...")
                    return None
            
            # Stage 3: 임베딩 생성
            embedding_text = f"{title}\n{content[:500]}" if content else title
            embedding = self.embedding_service.get_embedding(embedding_text)
            
            # Stage 4: Semantic 중복 체크 (선택적)
            if self.semantic_dedup:
                semantic_dup = self._check_semantic_duplicate(title, content, embedding)
                if semantic_dup:
                    self.stats["skipped_semantic"] += 1
                    return None
            
            # Stage 5: 기사 저장 (분석 전)
            news_article = NewsArticle(
                url=url,
                title=title,
                source=raw_article.get("source", ""),
                feed_source=raw_article.get("feed_source", "rss"),
                published_date=raw_article.get("published_date"),
                content=content,
                summary=raw_article.get("summary", ""),
                keywords=raw_article.get("keywords", []),
                author=raw_article.get("author", []),
                top_image=raw_article.get("top_image", ""),
                content_hash=content_hash,
                embedding=embedding
            )
            
            self.db.add(news_article)
            self.db.flush()  # ID 생성
            
            # Stage 6: 분석 (선택적)
            analysis = None
            if self._should_analyze(raw_article):
                try:
                    analysis = self.analyzer.analyze_article(news_article)
                    if analysis:
                        self.stats["analyzed"] += 1
                except Exception as e:
                    logger.error(f"Analysis failed for {title[:50]}: {e}")
            
            # Commit
            self.db.commit()
            self.db.refresh(news_article)
            
            self.stats["saved"] += 1
            logger.info(f"✅ Saved: {title[:50]}... (analyzed: {analysis is not None})")
            
            return ProcessedNews(
                article=news_article,
                analysis=analysis,
                was_analyzed=analysis is not None
            )
            
        except Exception as e:
            self.db.rollback()
            self.stats["errors"] += 1
            logger.error(f"Failed to process article {title[:50]}: {e}")
            raise
    
    async def process_batch(
        self,
        raw_articles: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> ProcessingResult:
        """
        배치 처리
        
        Args:
            raw_articles: 크롤링된 원시 기사 목록
            max_concurrent: 최대 동시 처리 수
            
        Returns:
            ProcessingResult: 처리 결과 통계
        """
        logger.info(f"Starting batch processing: {len(raw_articles)} articles")
        
        processed = []
        skipped = []
        errors = []
        
        # 순차 처리 (DB 트랜잭션 때문에)
        for i, article in enumerate(raw_articles, 1):
            try:
                result = await self.process_article(article)
                
                if result:
                    processed.append(result)
                else:
                    skipped.append({
                        "title": article.get("title", ""),
                        "url": article.get("url", "")
                    })
                
                # 진행 상황 로그
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(raw_articles)} articles processed")
                    
            except Exception as e:
                errors.append(e)
                logger.error(f"Error processing article {i}: {e}")
        
        # 최종 통계
        logger.info(f"""
Batch processing complete:
  Total: {self.stats['total']}
  Saved: {self.stats['saved']}
  Skipped (URL): {self.stats['skipped_url']}
  Skipped (Hash): {self.stats['skipped_hash']}
  Skipped (Semantic): {self.stats['skipped_semantic']}
  Analyzed: {self.stats['analyzed']}
  Errors: {self.stats['errors']}
""")
        
        return ProcessingResult(
            processed=processed,
            skipped=skipped,
            errors=errors
        )
    
    def get_stats(self) -> Dict[str, int]:
        """처리 통계 반환"""
        return self.stats.copy()
