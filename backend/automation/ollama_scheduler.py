"""
Ollama 전처리 스케줄러 - PHASE2

RSS 뉴스를 Ollama로 전처리하여 API 비용 절감

Features:
- RSS 크롤러와 연동 (10분 간격)
- Ollama로 뉴스 전처리 (요약, 중요도 분류, 티커 추출)
- 전처리 결과 DB 저장
- 처리 시간 및 성능 추적
- 5분 간격 스케줄링

Usage:
    scheduler = OllamaScheduler()
    await scheduler.start()
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

from backend.news.rss_crawler import RSSNewsCrawler, NewsArticle
from backend.ai.llm.ollama_client import OllamaClient, get_ollama_client
from backend.database.models import NewsArticle as DBNewsArticle
from backend.database.repository import NewsRepository, get_sync_session

logger = logging.getLogger(__name__)


class OllamaScheduler:
    """
    Ollama 전처리 스케줄러
    
    주요 기능:
    - RSS 크롤러와 Ollama 연동
    - 뉴스 전처리 (요약, 중요도 분류, 티커 추출)
    - 전처리 결과 DB 저장
    - 5분 간격 스케줄링
    - 성능 추적
    """
    
    def __init__(
        self,
        interval_seconds: int = 300,
        ollama_client: Optional[OllamaClient] = None
    ):
        """
        Args:
            interval_seconds: 스케줄링 간격 (초), 기본 5분
            ollama_client: Ollama 클라이언트 (None이면 자동 생성)
        """
        self.interval_seconds = interval_seconds
        self.ollama_client = ollama_client or get_ollama_client()
        self.rss_crawler = RSSNewsCrawler()
        
        # 성능 추적
        self.total_processed = 0
        self.total_time = 0.0
        self.success_count = 0
        self.failure_count = 0
        
        logger.info(f"OllamaScheduler initialized: interval={interval_seconds}s")
    
    async def preprocess_article(self, article: NewsArticle) -> Dict:
        """
        뉴스 기사 전처리
        
        Args:
            article: 뉴스 기사
            
        Returns:
            전처리 결과
        """
        start_time = datetime.now()
        
        try:
            # 뉴스 텍스트 준비
            news_text = f"{article.title}. {article.content}"
            
            # Ollama로 전처리
            logger.info(f"[Ollama] Preprocessing: {article.title[:50]}...")
            
            # 종목/섹터 추출
            ticker_result = await self.ollama_client.analyze_news(news_text)
            
            # 감성 분석
            sentiment_result = self.ollama_client.analyze_news_sentiment(
                article.title,
                article.content
            )
            
            # 전처리 결과 조합
            processed_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'article': article,
                'tickers': ticker_result.get('tickers', []),
                'sectors': ticker_result.get('sectors', []),
                'ticker_confidence': ticker_result.get('confidence', 0.0),
                'ticker_reasoning': ticker_result.get('reasoning', ''),
                'sentiment_overall': sentiment_result.get('sentiment_overall', 'neutral'),
                'sentiment_score': sentiment_result.get('sentiment_score', 0.0),
                'sentiment_confidence': sentiment_result.get('confidence', 0.0),
                'trading_actionable': sentiment_result.get('trading_actionable', False),
                'key_points': sentiment_result.get('key_points', []),
                'processed_time': processed_time,
                'timestamp': datetime.now()
            }
            
            logger.info(f"[Ollama] ✅ Preprocessed: {article.title[:50]}... "
                       f"(tickers={len(result['tickers'])}, "
                       f"sentiment={result['sentiment_overall']}, "
                       f"time={processed_time:.2f}s)")
            
            return result
            
        except Exception as e:
            processed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"[Ollama] ❌ Preprocessing failed: {article.title[:50]}... "
                        f"Error: {e} (time={processed_time:.2f}s)")
            
            # 실패 시 기본 결과 반환
            return {
                'article': article,
                'tickers': [],
                'sectors': [],
                'ticker_confidence': 0.0,
                'ticker_reasoning': 'Preprocessing failed',
                'sentiment_overall': 'neutral',
                'sentiment_score': 0.0,
                'sentiment_confidence': 0.0,
                'trading_actionable': False,
                'key_points': [],
                'processed_time': processed_time,
                'timestamp': datetime.now(),
                'error': str(e)
            }
    
    async def save_to_db(self, result: Dict) -> bool:
        """
        전처리 결과 DB 저장
        
        Args:
            result: 전처리 결과
            
        Returns:
            저장 성공 여부
        """
        try:
            # DB 세션 생성
            session = get_sync_session()
            repo = NewsRepository(session=session)
            
            # URL로 기사 찾기
            db_article = repo.get_by_url(result['article'].url)
            
            if db_article:
                # 전처리 결과 업데이트
                db_article.tickers = result['tickers']
                db_article.sectors = result['sectors']
                db_article.sentiment_score = result['sentiment_score']
                db_article.sentiment_label = result['sentiment_overall']
                
                # GLM 분석 결과 저장 (호환성)
                glm_analysis = {
                    'tickers': result['tickers'],
                    'sectors': result['sectors'],
                    'confidence': result['ticker_confidence'],
                    'reasoning': result['ticker_reasoning'],
                    'sentiment_overall': result['sentiment_overall'],
                    'sentiment_score': result['sentiment_score'],
                    'trading_actionable': result['trading_actionable'],
                    'key_points': result['key_points'],
                    'processed_time': result['processed_time']
                }
                db_article.glm_analysis = glm_analysis
                db_article.processed_at = datetime.now()
                
                session.commit()
                
                logger.info(f"[DB] ✅ Saved: news_id={db_article.id}, "
                           f"tickers={result['tickers']}, "
                           f"sentiment={result['sentiment_overall']}")
                return True
            else:
                logger.warning(f"[DB] ⚠️ Article not found: {result['article'].url}")
                return False
                
        except Exception as e:
            logger.error(f"[DB] ❌ Save failed: {e}")
            return False
    
    async def run_single_cycle(self) -> Dict:
        """
        단일 전처리 사이클 실행
        
        Returns:
            사이클 결과 통계
        """
        cycle_start = datetime.now()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"[{cycle_start.strftime('%Y-%m-%d %H:%M:%S')}] Starting Ollama preprocessing cycle")
        logger.info(f"{'='*80}")
        
        # 1. RSS 피드 크롤링
        logger.info("\n[STEP 1] Fetching RSS feeds...")
        articles = await self.rss_crawler.fetch_all_feeds()
        logger.info(f"  Found {len(articles)} articles")
        
        if not articles:
            logger.info("  No new articles found")
            return {
                'cycle_time': 0.0,
                'processed': 0,
                'success': 0,
                'failure': 0,
                'avg_time': 0.0
            }
        
        # 2. 뉴스 전처리
        logger.info(f"\n[STEP 2] Preprocessing articles with Ollama...")
        processed_results = []
        
        for i, article in enumerate(articles[:10], 1):  # 최대 10개만 처리
            logger.info(f"\n  [{i}/{min(len(articles), 10)}] Preprocessing: {article.title[:60]}...")
            
            # 전처리
            result = await self.preprocess_article(article)
            
            # DB 저장
            saved = await self.save_to_db(result)
            
            if saved:
                processed_results.append(result)
                self.success_count += 1
            else:
                self.failure_count += 1
            
            self.total_processed += 1
            self.total_time += result['processed_time']
        
        # 사이클 통계
        cycle_time = (datetime.now() - cycle_start).total_seconds()
        avg_time = self.total_time / self.total_processed if self.total_processed > 0 else 0.0
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Cycle complete:")
        logger.info(f"  Processed: {len(processed_results)} articles")
        logger.info(f"  Success: {self.success_count}, Failure: {self.failure_count}")
        logger.info(f"  Cycle time: {cycle_time:.2f}s")
        logger.info(f"  Avg preprocessing time: {avg_time:.2f}s")
        logger.info(f"  Total processed: {self.total_processed}")
        logger.info(f"{'='*80}")
        
        return {
            'cycle_time': cycle_time,
            'processed': len(processed_results),
            'success': self.success_count,
            'failure': self.failure_count,
            'avg_time': avg_time
        }
    
    async def start(self):
        """
        스케줄러 시작
        """
        logger.info(f"\n{'='*80}")
        logger.info("PHASE2: Ollama Preprocessing Scheduler Started")
        logger.info(f"{'='*80}")
        logger.info(f"  Interval: {self.interval_seconds} seconds ({self.interval_seconds/60:.1f} minutes)")
        logger.info(f"  Ollama model: {self.ollama_client.model}")
        logger.info(f"  Ollama URL: {self.ollama_client.base_url}")
        logger.info(f"{'='*80}\n")
        
        # Ollama 서버 상태 확인
        if not self.ollama_client.check_health():
            logger.error("❌ Ollama server is not running!")
            logger.error("Please start Ollama: ollama serve")
            return
        
        logger.info("✅ Ollama server is running\n")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                logger.info(f"\n[CYCLE #{cycle_count}]")
                
                # 전처리 사이클 실행
                stats = await self.run_single_cycle()
                
                # 다음 사이클까지 대기
                logger.info(f"\n[WAITING] Next cycle in {self.interval_seconds} seconds...")
                await asyncio.sleep(self.interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("\n\n[STOPPED] Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"\n[ERROR] Cycle failed: {e}")
                logger.error(f"Retrying in {self.interval_seconds} seconds...")
                await asyncio.sleep(self.interval_seconds)
    
    async def test_performance(self, num_articles: int = 5) -> Dict:
        """
        성능 테스트
        
        Args:
            num_articles: 테스트할 기사 수
            
        Returns:
            성능 테스트 결과
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"PHASE2: Performance Test ({num_articles} articles)")
        logger.info(f"{'='*80}\n")
        
        # RSS 피드 크롤링
        articles = await self.rss_crawler.fetch_all_feeds()
        
        if not articles:
            logger.error("No articles found for testing")
            return {}
        
        # 테스트용 기사 선택
        test_articles = articles[:num_articles]
        
        results = []
        total_time = 0.0
        
        for i, article in enumerate(test_articles, 1):
            logger.info(f"\n[{i}/{num_articles}] Testing: {article.title[:60]}...")
            
            # 전처리
            result = await self.preprocess_article(article)
            results.append(result)
            
            total_time += result['processed_time']
        
        # 성능 통계
        avg_time = total_time / num_articles
        max_time = max(r['processed_time'] for r in results)
        min_time = min(r['processed_time'] for r in results)
        
        logger.info(f"\n{'='*80}")
        logger.info("Performance Test Results:")
        logger.info(f"  Total articles: {num_articles}")
        logger.info(f"  Total time: {total_time:.2f}s")
        logger.info(f"  Average time: {avg_time:.2f}s")
        logger.info(f"  Max time: {max_time:.2f}s")
        logger.info(f"  Min time: {min_time:.2f}s")
        logger.info(f"  Target: 30s per article")
        logger.info(f"  Status: {'✅ PASS' if avg_time <= 30 else '❌ FAIL'}")
        logger.info(f"{'='*80}")
        
        return {
            'total_articles': num_articles,
            'total_time': total_time,
            'avg_time': avg_time,
            'max_time': max_time,
            'min_time': min_time,
            'pass': avg_time <= 30
        }


# ============================================
# Demo & Testing
# ============================================

async def demo():
    """Ollama 스케줄러 데모"""
    print("=" * 80)
    print("PHASE2: Ollama Preprocessing Scheduler Demo")
    print("=" * 80)
    
    scheduler = OllamaScheduler()
    
    # 성능 테스트
    results = await scheduler.test_performance(num_articles=3)
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    # 데모 실행
    asyncio.run(demo())
    
    # 실제 스케줄러 실행 (주석 해제하여 사용)
    # scheduler = OllamaScheduler(interval_seconds=300)  # 5분마다
    # asyncio.run(scheduler.start())
