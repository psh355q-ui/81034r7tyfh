"""
News Analysis API Router - SSE Streaming

Separate router for real-time analysis progress tracking
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import asyncio

from backend.data.news_models import get_db
from backend.data.rss_crawler import get_unanalyzed_articles
from backend.data.news_analyzer import NewsDeepAnalyzer


router = APIRouter(prefix="/news", tags=["News Analysis"])


@router.get("/analyze-stream")
async def analyze_articles_stream(
    max_count: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    SSE 스트리밍으로 실시간 분석 진행률 표시
    
    백그라운드 처리:
    - 클라이언트 연결 해제 후에도 서버에서 계속 분석
    - 실시간 진행률 업데이트
    - 완료/스킵/에러 통계
    
    Args:
        max_count: 최대 분석 개수 (1-100)
        
    Returns:
        SSE stream with progress updates
    """
    
    async def event_generator():
        try:
            # Get unanalyzed articles
            unanalyzed = get_unanalyzed_articles(db, limit=max_count)
            total_articles = len(unanalyzed)
            
            # No articles case
            if total_articles == 0:
                completion = {
                    'status': 'completed',
                    'message': 'No articles to analyze',
                    'progress_percent': 100,
                    'current_index': 0,
                    'total_articles': 0,
                    'completed': 0,
                    'skipped': 0,
                    'errors': 0
                }
                yield f"data: {json.dumps(completion)}\n\n"
                return
            
            # Initialize analyzer and counters
            analyzer = NewsDeepAnalyzer(db)
            completed = 0
            skipped = 0
            errors = 0
            
            # Process each article
            for index, article in enumerate(unanalyzed, 1):
                # Send progress update
                progress = {
                    'status': 'running',
                    'current_index': index,
                    'total_articles': total_articles,
                    'progress_percent': (index / total_articles) * 100,
                    'current_article': article.title[:80] if article.title else 'Untitled',
                    'completed': completed,
                    'skipped': skipped,
                    'errors': errors
                }
                yield f"data: {json.dumps(progress)}\n\n"
                await asyncio.sleep(0.1)  # Allow client to receive
                
                # Analyze article
                try:
                    result = analyzer.analyze_article(article)
                    if result:
                        completed += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errors += 1
                    print(f"❌ Analysis error for article {article.id}: {e}")
            
            # Send completion message
            completion = {
                'status': 'completed',
                'current_index': total_articles,
                'total_articles': total_articles,
                'progress_percent': 100,
                'completed': completed,
                'skipped': skipped,
                'errors': errors,
                'message': f'Analysis complete! {completed} analyzed, {skipped} skipped, {errors} errors.'
            }
            yield f"data: {json.dumps(completion)}\n\n"
            await asyncio.sleep(1.0)  # Final message delivery
            
        except Exception as e:
            # Error case
            error_response = {
                'status': 'error',
                'message': f'Stream error: {str(e)}',
                'progress_percent': 0
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
