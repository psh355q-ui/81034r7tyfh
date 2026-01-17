"""
News Poller Service

Features:
- Periodic RSS Crawling (5 min interval)
- Keyword Pre-filtering (save AI tokens)
- Triggering Deep Reasoning Agent for critical events
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from backend.data.rss_crawler import RSSCrawler
from backend.data.news_analyzer import NewsDeepAnalyzer
from backend.ai.reasoning.deep_reasoning_agent import DeepReasoningAgent
# Use PostgreSQL instead of SQLite
from backend.database.models import NewsArticle, NewsAnalysis, TradingSignal
from backend.database.repository import get_sync_session
from backend.data.processors.unified_news_processor import UnifiedNewsProcessor

logger = logging.getLogger(__name__)

# Trigger Keywords (Pre-filter)
# 이 키워드가 포함된 뉴스만 AI 분석을 수행하여 비용 절감
CRITICAL_KEYWORDS = [
    "war", "invasion", "military", "conflict", "attack",
    "sanction", "embargo", "ban",
    "crisis", "shortage", "collapse", "bankrupt",
    "rate hike", "inflation", "cpi", "fomc",
    "oil", "semiconductor", "chip", "taiwan", "china"
]

class NewsPoller:
    def __init__(self):
        self.is_running = False
        self.interval_seconds = 300  # 5 minutes
        self.deep_agent = DeepReasoningAgent()
        self._last_triggered = {}  # Cache for debouncing events
        
    async def start(self):
        """Start the polling loop"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("📰 NewsPoller started (Interval: 5m)")
        
        while self.is_running:
            try:
                await self.poll_and_process()
            except Exception as e:
                logger.error(f"❌ NewsPoller Loop Error: {e}", exc_info=True)
            
            await asyncio.sleep(self.interval_seconds)

    def stop(self):
        self.is_running = False
        logger.info("📰 NewsPoller stopped")

    async def poll_and_process(self):
        """Single polling cycle (with UnifiedNewsProcessor)"""
        db = get_sync_session()  # PostgreSQL session
        try:
            crawler = RSSCrawler(db)
            
            # 1. Fetch all enabled feeds (DB 저장 안함!)
            logger.info("🕷️ Fetching RSS feeds...")
            raw_articles = await asyncio.to_thread(crawler.fetch_all_feeds)
            
            if not raw_articles:
                logger.info("No new articles found.")
                return

            logger.info(f"📥 Fetched {len(raw_articles)} raw articles.")

            # 2. UnifiedNewsProcessor로 통합 처리
            logger.info("⚙️ Processing through UnifiedNewsProcessor...")
            processor = UnifiedNewsProcessor(
                db=db,
                semantic_dedup=False,  # 비활성화 (향후 활성화 가능)
                analyze_all=False  # 중요한 것만 분석
            )
            
            result = await processor.process_batch(raw_articles)
            
            # 3. 통계 로깅
            stats = processor.get_stats()
            logger.info(f"""📊 Processing Complete:
  Total: {stats['total']}
  Saved: {stats['saved']}
  Analyzed: {stats['analyzed']}
  Skipped (URL): {stats['skipped_url']}
  Skipped (Hash): {stats['skipped_hash']}
  Errors: {stats['errors']}
""")

            # 4. 중요 뉴스에 대한 Deep Reasoning 트리거
            for processed in result.processed:
                if processed.analysis and processed.analysis.urgency in ["high", "critical"]:
                    logger.warning(f"🧠 High Urgency Event: {processed.article.title[:60]}...")
                    
                    # 키워드 추출
                    matched_keywords = self._check_keywords(processed.article)
                    
                    if matched_keywords:
                        await self._trigger_deep_reasoning(
                            db,
                            processed.article,
                            matched_keywords,
                            processed.analysis
                        )
                    
        finally:
            db.close()

    def _check_keywords(self, article: NewsArticle) -> List[str]:
        """Check if article matches critical keywords"""
        text_to_check = (f"{article.title} {article.summary or ''}").lower()
        matches = [k for k in CRITICAL_KEYWORDS if k in text_to_check]
        return matches

    async def _trigger_deep_reasoning(self, db: Session, article: NewsArticle, keywords: List[str], analysis: NewsAnalysis):
        """Deep Reasoning Agent 호출 및 시그널 생성 (with Debouncing)"""
        try:
            # 결정: Event Type (단순 키워드 기반 매핑 for MVP)
            event_type = "GEOPOLITICS"
            if any(k in keywords for k in ["semiconductor", "chip", "taiwan"]):
                event_type = "CHIP_WAR"

            # Debouncing Check: 1시간 내 동일 유형 이벤트 무시
            last_time = self._last_triggered.get(event_type)
            if last_time and (datetime.utcnow() - last_time).total_seconds() < 3600:
                logger.info(f"⏳ Debouncing: Skipping Deep Reasoning for {event_type} (Last run: {last_time})")
                return

            # 기본 정보 구성
            base_info = {
                "title": article.title,
                "summary": article.summary,
                "published_at": str(article.published_date),
                "source": article.source,
                "initial_analysis": {
                    "urgency": analysis.urgency,
                    "sentiment": analysis.sentiment_overall,
                    "impact": analysis.market_impact_short
                }
            }

            # Deep Reasoning 실행
            result = await self.deep_agent.analyze_event(event_type, keywords, base_info)
            
            # Update debounce timestamp check
            self._last_triggered[event_type] = datetime.utcnow()
            
            if result.get("status") == "SUCCESS":
                action_plan = result.get("action_plan", {})
                action = action_plan.get("action", "HOLD")
                
                if action != "HOLD":
                    # Signal 생성 & 저장
                    signal = TradingSignal(
                        ticker="MARKET" if event_type=="GEOPOLITICS" else "NVDA", # MVP Simplification
                        action=action,
                        signal_type="DEEP_REASONING",
                        confidence=action_plan.get("confidence", 0.0),
                        reasoning=f"Event: {article.title[:50]}... | {action_plan.get('reasoning')}", # Fixed field name
                        source="news_poller", # Fixed source
                        generated_at=datetime.utcnow(),
                        # meta_data=result # Postgres model might not have meta_data column yet or use JSON
                    )
                    
                    # Safe DB Add with error handling
                    try:
                       db.add(signal)
                       db.commit()
                       logger.info(f"🚨 DeepReasoning Signal Created: {action} (Conf: {signal.confidence})")
                    except Exception as db_e:
                       logger.error(f"Failed to save signal: {db_e}")
                       db.rollback()
            
        except Exception as e:
            logger.error(f"❌ DeepReasoning Trigger Failed: {e}", exc_info=True)
