"""
Unified News Processor

통합 뉴스 처리 파이프라인:
크롤링 → 중복 제거 → GLM 분석 → 저장을 원자적으로 처리

Features:
- URL + Content Hash + Semantic 중복 체크
- GLM-4.7 종목/섹터 추출 (모든 뉴스)
- 선택적 Deep Analysis (중요 뉴스만)
- 원자적 DB 저장
- 배치 처리 지원
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session
# Use PostgreSQL models (backend.database.models) instead of SQLite (backend.data.news_models)
from backend.database.models import NewsArticle, NewsAnalysis, NewsTickerRelevance
from backend.data.rss_crawler import generate_content_hash
from backend.data.news_analyzer import NewsDeepAnalyzer
from backend.ai.llm.local_embeddings import LocalEmbeddingService
from backend.ai.llm.ollama_client import OllamaClient

# GLM-4.7 Client (Phase 1 Integration)
try:
    from backend.ai.glm_client import GLMClient, MockGLMClient
    GLM_AVAILABLE = True
except ImportError:
    GLM_AVAILABLE = False
    logger.warning("GLM client not available, using fallback")

logger = logging.getLogger(__name__)


@dataclass
class ProcessedNews:
    """처리된 뉴스 결과"""
    article: NewsArticle
    analysis: Optional[NewsAnalysis]
    was_analyzed: bool
    glm_analysis: Optional[Dict] = None  # GLM 분석 결과 추가
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
    4. GLM 분석 (종목/섹터 추출)
    5. 임베딩 생성
    6. Deep Analysis (선택적)
    7. DB 저장 (원자적)
    """

    def __init__(
        self,
        db: Session,
        semantic_dedup: bool = False,
        semantic_threshold: float = 0.95,
        analyze_all: bool = False,
        glm_rate_limit: float = None
    ):
        self.db = db
        self.semantic_dedup = semantic_dedup
        self.semantic_threshold = semantic_threshold
        self.analyze_all = analyze_all

        # Rate Limiting for GLM API (prevent Concurrency Limit exceeded)
        # GLM-4-Plus has Concurrency Limit 20
        # Default: 3.0 seconds between calls (very conservative for stability)
        self.glm_rate_limit = glm_rate_limit or float(os.environ.get("NEWS_GLM_RATE_LIMIT", "3.0"))

        # Concurrency Control: Semaphore to limit simultaneous GLM API calls
        # Prevents bursting requests that exceed GLM's Concurrency Limit
        # Recommended: 3-5 for stability (GLM-4-Plus has limit of 20)
        glm_concurrency_limit = int(os.environ.get("NEWS_GLM_CONCURRENCY", "3"))
        self.glm_semaphore = asyncio.Semaphore(glm_concurrency_limit)
        logger.info(f"✅ GLM Concurrency Limit: {glm_concurrency_limit} simultaneous requests")

        # Services
        self.embedding_service = LocalEmbeddingService()
        self.ollama_client = OllamaClient()
        self.analyzer = NewsDeepAnalyzer(db)

        # LLM Client Selection
        # 1. GLM API (유료, 정확도 높음)
        # 2. Ollama Local LLM (무료, 로컬 실행)
        self.use_ollama = os.environ.get("NEWS_USE_OLLAMA", "true").lower() == "true"
        self.glm_enabled = os.environ.get("NEWS_GLM_ENABLED", "true").lower() == "true" and not self.use_ollama

        # Ollama Local LLM (무료, 종목/섹터 추출)
        if self.use_ollama:
            self.llm_client = self.ollama_client
            logger.info("✅ Using Ollama Local LLM for ticker/sector extraction (COST: $0)")
        # GLM API (유료)
        elif GLM_AVAILABLE and self.glm_enabled:
            glm_api_key = os.environ.get("GLM_API_KEY")
            glm_model = os.environ.get("NEWS_GLM_MODEL", "glm-4-plus")
            if glm_api_key and glm_api_key != "your-glm-api-key-here":
                try:
                    self.llm_client = GLMClient(api_key=glm_api_key, model=glm_model)
                    logger.info(f"✅ GLM Client initialized (Real API) with model: {glm_model}")
                except Exception as e:
                    logger.warning(f"GLM init failed, using Ollama: {e}")
                    self.llm_client = self.ollama_client
            else:
                self.llm_client = self.ollama_client
                logger.warning("⚠️ GLM_API_KEY not set, using Ollama (COST: $0)")
        else:
            # Fallback to Ollama
            self.llm_client = self.ollama_client
            logger.info("ℹ️ Using Ollama Local LLM (COST: $0)")

        # Stats
        self.stats = {
            "total": 0,
            "skipped_url": 0,
            "skipped_hash": 0,
            "skipped_semantic": 0,
            "saved": 0,
            "analyzed": 0,
            "glm_analyzed": 0,  # GLM 분석 통계 추가
            "errors": 0
        }

    def _check_url_duplicate(self, url: str) -> Optional[NewsArticle]:
        """
        URL 중복 체크 (상세 로깅 포함)

        Returns:
            NewsArticle: 중복 기사가 존재하면 해당 기사 객체 반환
            None: 중복이 없으면 None 반환
        """
        existing = self.db.query(NewsArticle).filter(NewsArticle.url == url).first()
        if existing:
            logger.info(f"🔄 Duplicate URL found: {url}")
            logger.info(f"   Existing: {existing.title[:80]}...")
            logger.info(f"   Article ID: {existing.id} | Published: {existing.published_date}")

            # GLM 분석 데이터 확인
            if existing.glm_analysis:
                tickers = existing.glm_analysis.get('tickers', [])
                sectors = existing.glm_analysis.get('sectors', [])
                confidence = existing.glm_analysis.get('confidence', 0)
                logger.info(f"   Existing data: GLM analysis ✅")
                logger.info(f"      - Tickers: {tickers}")
                logger.info(f"      - Sectors: {sectors}")
                logger.info(f"      - Confidence: {confidence:.2f}")
            else:
                logger.info(f"   Existing data: GLM analysis ❌")

            # Deep Analysis 데이터 확인
            if existing.analysis:
                logger.info(f"   Existing data: Deep analysis ✅")
                logger.info(f"      - Sentiment: {existing.analysis.sentiment_overall}")
                logger.info(f"      - Score: {existing.analysis.sentiment_score:.2f}")
                logger.info(f"      - Urgency: {existing.analysis.urgency}")
            else:
                logger.info(f"   Existing data: Deep analysis ❌")

        return existing
    
    def _check_hash_duplicate(self, content_hash: str) -> Optional[NewsArticle]:
        """
        Content Hash 중복 체크 (상세 로깅 포함)

        Returns:
            NewsArticle: 중복 기사가 존재하면 해당 기사 객체 반환
            None: 중복이 없으면 None 반환
        """
        existing = self.db.query(NewsArticle).filter(
            NewsArticle.content_hash == content_hash
        ).first()
        if existing:
            logger.info(f"🔄 Duplicate content hash found")
            logger.info(f"   Existing: {existing.title[:80]}...")
            logger.info(f"   Article ID: {existing.id} | URL: {existing.url}")

            # GLM 분석 데이터 확인
            if existing.glm_analysis:
                tickers = existing.glm_analysis.get('tickers', [])
                logger.info(f"   Existing data: GLM analysis ✅ (Tickers: {tickers})")
            else:
                logger.info(f"   Existing data: GLM analysis ❌")

            # Deep Analysis 데이터 확인
            if existing.analysis:
                logger.info(f"   Existing data: Deep analysis ✅ (Sentiment: {existing.analysis.sentiment_overall})")
            else:
                logger.info(f"   Existing data: Deep analysis ❌")

        return existing
    
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
                    logger.info(f"🔄 Semantic duplicate found (similarity: {similarity:.3f})")
                    logger.info(f"   New: {title[:80]}...")
                    logger.info(f"   Existing: {article.title[:80]}...")
                    logger.info(f"   Article ID: {article.id} | Similarity: {similarity:.3f}")

                    # GLM 분석 데이터 확인
                    if article.glm_analysis:
                        tickers = article.glm_analysis.get('tickers', [])
                        logger.info(f"   Existing data: GLM analysis ✅ (Tickers: {tickers})")
                    else:
                        logger.info(f"   Existing data: GLM analysis ❌")

                    # Deep Analysis 데이터 확인
                    if article.analysis:
                        logger.info(f"   Existing data: Deep analysis ✅ (Sentiment: {article.analysis.sentiment_overall})")
                    else:
                        logger.info(f"   Existing data: Deep analysis ❌")

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
            if existing_article := self._check_url_duplicate(url):
                self.stats["skipped_url"] += 1
                logger.info(f"⏭️  Skipping duplicate article: {title[:80]}...")
                logger.info(f"   Reason: URL already exists with ID {existing_article.id}")
                logger.info(f"   New URL: {url}")
                logger.info(f"   Existing URL: {existing_article.url}")
                return None

            # Stage 2: Content Hash 중복 체크
            # Always generate content_hash (DB requires NOT NULL)
            # Use title+content if available, otherwise title only
            hash_input = f"{title}\n{content}" if content and len(content) > 50 else title
            content_hash = generate_content_hash(hash_input, "")

            # Only check duplicate if we have substantial content
            if content and len(content) > 50:
                if existing_article := self._check_hash_duplicate(content_hash):
                    self.stats["skipped_hash"] += 1
                    logger.info(f"⏭️  Skipping duplicate article: {title[:80]}...")
                    logger.info(f"   Reason: Content hash already exists with ID {existing_article.id}")
                    logger.info(f"   New: {title[:80]}...")
                    logger.info(f"   Existing: {existing_article.title[:80]}...")
                    return None
            
            # Stage 3: 임베딩 생성
            embedding_text = f"{title}\n{content[:500]}" if content else title
            embedding = self.embedding_service.get_embedding(embedding_text)
            
            # Stage 4: Semantic 중복 체크 (선택적)
            if self.semantic_dedup:
                semantic_dup = self._check_semantic_duplicate(title, content, embedding)
                if semantic_dup:
                    self.stats["skipped_semantic"] += 1
                    logger.info(f"⏭️  Skipping duplicate article: {title[:80]}...")
                    logger.info(f"   Reason: Semantic duplicate with ID {semantic_dup.id}")
                    return None
            
            # Stage 5: 기사 저장 (분석 전)
            # Map raw_article fields to PostgreSQL NewsArticle model
            author_val = raw_article.get("author", [])
            if isinstance(author_val, list):
                author_val = ", ".join(author_val) if author_val else None

            news_article = NewsArticle(
                url=url,
                title=title,
                source=raw_article.get("source", ""),
                published_date=raw_article.get("published_date"),
                content=content,
                summary=raw_article.get("summary", ""),
                author=author_val,
                content_hash=content_hash,
                embedding=embedding,
                tags=raw_article.get("keywords", []),  # keywords -> tags
                metadata_={  # Store extra fields in JSONB metadata
                    "feed_source": raw_article.get("feed_source", "rss"),
                    "top_image": raw_article.get("top_image", ""),
                }
            )
            
            self.db.add(news_article)
            self.db.flush()  # ID 생성

            # Stage 5.5: GLM 분석 (종목/섹터 추출) - 모든 뉴스 수행
            # Concurrency Control: Semaphore + Rate Limiting
            # - Semaphore: 최대 동시 요청 수 제한 (기본 3개)
            # - Rate Limit: 요청 간 지연 (기본 3초)
            glm_analysis = None
            if self.llm_client:
                try:
                    # Semaphore로 동시 요청 수 제한 (GLM Concurrency Limit 초과 방지)
                    async with self.glm_semaphore:
                        news_text = f"{title}\n{content[:1000] if content else ''}"
                        glm_analysis = await self.llm_client.analyze_news(news_text)

                        # Rate Limiting: 다음 요청 전 지연
                        await asyncio.sleep(self.glm_rate_limit)

                    if glm_analysis:
                        self.stats["glm_analyzed"] += 1

                        # DB의 glm_analysis 컬럼에 저장
                        # Note: NewsArticle 모델에 glm_analysis 컬럼이 있어야 함
                        try:
                            from backend.database.models import NewsArticle as DBNewsArticle
                            from backend.database.repository import NewsRepository

                            repo = NewsRepository(session=self.db)
                            # 이미 flush된 news_article의 ID 사용
                            repo.save_glm_analysis(news_article.id, glm_analysis)
                        except Exception as db_err:
                            logger.warning(f"GLM DB save failed: {db_err}")

                        logger.info(
                            f"[GLM] {title[:40]}... | "
                            f"Tickers: {glm_analysis.get('tickers', [])} | "
                            f"Confidence: {glm_analysis.get('confidence', 0):.2f}"
                        )
                except Exception as e:
                    logger.error(f"GLM analysis failed for {title[:50]}: {e}")

            # Stage 6: Deep Analysis (선택적)
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
            logger.info(f"✅ Saved: {title[:50]}... (GLM: {glm_analysis is not None}, Deep: {analysis is not None})")

            return ProcessedNews(
                article=news_article,
                analysis=analysis,
                was_analyzed=analysis is not None,
                glm_analysis=glm_analysis
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
  GLM Analyzed: {self.stats['glm_analyzed']}
  Deep Analyzed: {self.stats['analyzed']}
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
