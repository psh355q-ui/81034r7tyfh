"""
Unified News Processor 테스트 스크립트

⚠️ DEPRECATED: This test file uses SQLite and should be updated to use PostgreSQL.
    For testing with PostgreSQL, use `pytest tests/` instead.
"""
import sys
import asyncio
sys.path.insert(0, 'd:/code/ai-trading-system')

from backend.database.repository import get_sync_session
from backend.data.rss_crawler import RSSCrawler
from backend.data.processors.unified_news_processor import UnifiedNewsProcessor

async def test_unified_processor():
    """통합 뉴스 처리 파이프라인 테스트"""
    print("=" * 80)
    print("Unified News Processor 테스트")
    print("=" * 80)
    print()

    # PostgreSQL 세션 사용
    db = get_sync_session()
    
    try:
        # 1. RSS Crawler로 원시 기사 가져오기
        print("[1] RSS 피드 크롤링 (DB 저장 안함)")
        print("-" * 80)
        crawler = RSSCrawler(db)
        raw_articles = crawler.fetch_all_feeds(extract_content=True)
        print(f"✅ 크롤링 완료: {len(raw_articles)}개 기사")
        print()
        
        # 2. UnifiedNewsProcessor로 처리
        print("[2] 통합 처리 (중복 제거 + 분석 + 저장)")
        print("-" * 80)
        
        processor = UnifiedNewsProcessor(
            db=db,
            semantic_dedup=False,  # 처음엔 비활성화
            analyze_all=False  # 중요한 것만 분석
        )
        
        result = await processor.process_batch(raw_articles)
        
        print()
        print("=" * 80)
        print("처리 결과:")
        print("=" * 80)
        print(f"총 기사: {len(raw_articles)}")
        print(f"저장됨: {len(result.processed)}")
        print(f"중복 스킵: {len(result.skipped)}")
        print(f"오류: {len(result.errors)}")
        print()
        
        # 3. 통계
        stats = processor.get_stats()
        print("상세 통계:")
        print(f"  URL 중복: {stats['skipped_url']}")
        print(f"  Hash 중복: {stats['skipped_hash']}")
        print(f"  Semantic 중복: {stats['skipped_semantic']}")
        print(f"  분석됨: {stats['analyzed']}")
        print()
        
        # 4. 저장된 기사 샘플
        if result.processed:
            print("저장된 기사 샘플:")
            for i, processed in enumerate(result.processed[:3], 1):
                print(f"\n[{i}] {processed.article.title[:60]}...")
                print(f"    출처: {processed.article.source}")
                print(f"    분석: {'✅' if processed.was_analyzed else '❌'}")
                if processed.analysis:
                    print(f"    감성: {processed.analysis.sentiment_overall} ({processed.analysis.sentiment_score:.2f})")
        
        print()
        print("=" * 80)
        print("✅ 테스트 완료!")
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_unified_processor())
