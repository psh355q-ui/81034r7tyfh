import sys
sys.path.insert(0, 'd:/code/ai-trading-system')

from backend.database.repository import get_sync_session
from backend.database.models import NewsArticle, NewsAnalysis

db = get_sync_session()

try:
    total = db.query(NewsArticle).count()
    analyzed = db.query(NewsAnalysis).count()
    ollama = db.query(NewsAnalysis).filter(NewsAnalysis.model_used.like('%llama%')).count()
    
    print(f"총 기사: {total}")
    print(f"분석 완료: {analyzed}")
    print(f"Ollama 분석: {ollama}")
    
    # 최신 분석 1개 확인
    latest = db.query(NewsAnalysis).order_by(NewsAnalysis.id.desc()).first()
    if latest:
        print(f"\n최신 분석 모델: {latest.model_used}")
        
finally:
    db.close()
