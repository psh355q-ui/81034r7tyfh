"""
News Deep Analysis Service

Gemini 무료 API를 활용한 뉴스 심층 분석
- 본문 전체 분석 (제목만이 아님)
- 감정/톤/긴급도/신뢰성 다각도 분석
- 시장 영향도 예측
- 우회 표현 해석
- 비용: $0 (무료 티어)
"""

import json
import re
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from sqlalchemy import text

# Google Generative AI SDK
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

from backend.database.models import NewsArticle, NewsAnalysis, NewsTickerRelevance
from backend.database.repository import get_sync_session

# Initialize logger
logger = logging.getLogger(__name__)

# ============================================================================
# Rate Limit Tracking (무료 티어 1,500회/일)
# ============================================================================

from pathlib import Path

# Docker 컨테이너 호환 경로
USAGE_FILE = Path("/app/data/gemini_daily_usage.json")
try:
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    USAGE_FILE = Path("/tmp/gemini_daily_usage.json")


def get_daily_usage() -> dict:
    """오늘의 사용량 조회"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    if USAGE_FILE.exists():
        with open(USAGE_FILE, "r") as f:
            data = json.load(f)
        if data.get("date") == today:
            return data
    
    return {
        "date": today,
        "request_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
    }


def update_daily_usage(input_tokens: int, output_tokens: int) -> dict:
    """일일 사용량 업데이트"""
    usage = get_daily_usage()
    usage["request_count"] += 1
    usage["total_input_tokens"] += input_tokens
    usage["total_output_tokens"] += output_tokens
    usage["last_request_time"] = datetime.utcnow().isoformat()
    
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_FILE, "w") as f:
        json.dump(usage, f, indent=2)
    
    return usage


def check_rate_limit() -> bool:
    """무료 티어 제한 확인"""
    usage = get_daily_usage()
    return usage["request_count"] < 1500


# ============================================================================
# Deep Analysis Service
# ============================================================================

class NewsDeepAnalyzer:
    """
    뉴스 심층 분석 서비스
    
    Gemini 1.5 Flash 무료 티어 사용
    - 1,500회/일 무료
    - 본문 전체 분석
    - 비용: $0
    """
    
    def __init__(self, db: Session = None):
        self.db = db if db else get_sync_session()
        self._owned_session = db is None
        
        if not GENAI_AVAILABLE:
            raise ImportError("google-generativeai 패키지를 설치하세요: pip install google-generativeai")
        
        # Load API key and model from environment
        import os
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        # Add 'models/' prefix if not present
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"NewsDeepAnalyzer initialized with model: {model_name}")
        
    def __del__(self):
        if hasattr(self, '_owned_session') and self._owned_session:
            self.db.close()
    
    def extract_tickers_from_title(self, title: str) -> List[str]:
        """
        Extract stock tickers from article title
        """
        tickers = []
        
        # Pattern 1: (EXCHANGE:TICKER)
        exchange_pattern = r'\((?:NASDAQ|NYSE|AMEX|NYSEAMERICAN|OTC):([A-Z]{1,5})\)'
        matches = re.findall(exchange_pattern, title, re.IGNORECASE)
        tickers.extend(matches)
        
        # Pattern 2: $TICKER
        dollar_pattern = r'\$([A-Z]{1,5})(?:\s|$|\.|,)'
        matches = re.findall(dollar_pattern, title)
        tickers.extend(matches)
        
        # Pattern 3: TICKER stock/shares/Inc.
        stock_pattern = r'\b([A-Z]{2,5})\s+(?:stock|shares|Inc\.|Corp\.|Limited)'
        matches = re.findall(stock_pattern, title)
        tickers.extend([t for t in matches if len(t) >= 2 and len(t) <= 5])
        
        # Deduplicate and return
        return list(set(tickers))
    
    def create_analysis_prompt(self, article: NewsArticle) -> str:
        """분석 프롬프트 생성"""
        # 본문 우선, 없으면 요약 사용
        content = article.content_text or article.content_summary or ""
        if len(content) > 8000:  # ~2000 토큰
            content = content[:8000] + "... [truncated]"
        
        keywords = ", ".join(article.keywords or [])
        
        prompt = f"""
다음 뉴스 기사를 심층 분석해주세요:

====== 뉴스 정보 ======
제목: {article.title}
출처: {article.source}
발행일: {article.published_at}
키워드: {keywords}

====== 본문 내용 ======
{content}

====== 분석 요청 ======
아래 JSON 형식으로 분석 결과를 반환해주세요:

{{
  "sentiment": "positive|negative|neutral|mixed",
  "sentiment_score": -1.0에서 1.0,
  "urgency": "low|medium|high|critical",
  "market_impact_short": "bullish|bearish|neutral|uncertain",
  "market_impact_long": "bullish|bearish|neutral|uncertain",
  "impact_magnitude": 0.0에서 1.0,
  "actionable": true|false,
  "risk_category": "legal|regulatory|operational|financial|strategic|none"
}}

CRITICAL: 
- Output ONLY valid JSON
- No markdown, no code blocks, no extra text
- All values must be properly quoted strings or numbers
- Ensure all quotes are properly closed
"""
        return prompt
    
    def parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """JSON 응답 파싱 (개선된 버전)"""
        # 마크다운 코드 블록 제거
        text = response_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        text = text.strip()
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        text = text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                if len(parsed) > 0 and isinstance(parsed[0], dict):
                    return parsed[0]
                else:
                    return {"error": "Invalid list response"}
            return parsed
        except json.JSONDecodeError:
            try:
                # 역슬래시 이스케이프 문제 수정
                text = text.replace('\\\\', '\\')
                return json.loads(text)
            except:
                pass
            
            # Simple fix for trailing commas
            try:
                text = re.sub(r',(\s*[}\]])', r'\1', text)
                return json.loads(text)
            except:
                pass

            return {
                "error": "JSON parse failed",
                "raw_preview": response_text[:200]
            }
    
    def analyze_article(self, article: NewsArticle) -> Optional[NewsAnalysis]:
        """단일 기사 분석"""
        if not check_rate_limit():
            raise Exception("일일 무료 한도 초과 (1,500회/일). 내일 다시 시도하세요.")
        
        # 이미 분석됨?
        if article.analysis:
            return article.analysis
        
        # 본문 확인
        if not article.content_text or len(article.content_text) < 50:
            if not article.content_summary or len(article.content_summary) < 50:
                return None
        
        # 프롬프트 생성
        prompt = self.create_analysis_prompt(article)
        
        # Gemini API 호출
        import time
        start_time = time.time()
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # Very low for consistent structured output
                    max_output_tokens=2000,
                    response_mime_type="application/json",  # Force JSON response
                )
            )
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
        
        # 토큰 추정 및 사용량
        input_tokens = len(prompt) // 4
        output_tokens = len(response.text) // 4
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
        
        update_daily_usage(input_tokens, output_tokens)
        
        # 응답 파싱
        analysis_data = self.parse_analysis_response(response.text)
        
        if "error" in analysis_data:
            print(f"⚠️ Parse error for {article.title[:50]}: {analysis_data['error']}")
            return None
        
        def _safe_bool(value: Any) -> bool:
            if isinstance(value, bool): return value
            if isinstance(value, str): return value.lower() in ('true', '1', 'yes')
            return bool(value)
        
        # DB에 저장
        news_analysis = NewsAnalysis(
            article_id=article.id,
            sentiment_overall=analysis_data.get("sentiment", "neutral"),
            sentiment_score=float(analysis_data.get("sentiment_score", 0.0)),
            sentiment_confidence=0.8,
            tone_objective_score=0.5,
            urgency=analysis_data.get("urgency", "medium"),
            sensationalism=0.0,
            market_impact_short=analysis_data.get("market_impact_short", "neutral"),
            market_impact_long=analysis_data.get("market_impact_long", "neutral"),
            impact_magnitude=float(analysis_data.get("impact_magnitude", 0.0)),
            affected_sectors=[],
            key_facts=[],
            key_opinions=[],
            key_implications=[],
            key_warnings=[],
            indirect_expressions=[],
            red_flags=[],
            trading_actionable=_safe_bool(analysis_data.get("actionable", False)),
            risk_category=analysis_data.get("risk_category", "none"),
            recommendation="",
            source_reliability=0.7,
            data_backed=_safe_bool(analysis_data.get("data_backed", False)),
            multiple_sources_cited=_safe_bool(analysis_data.get("multiple_sources", False)),
            potential_bias="",
            model_used=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            tokens_used=input_tokens + output_tokens,
            analysis_cost=0.0
        )
        
        self.db.add(news_analysis)
        
        # Extract tickers
        extracted_tickers = self.extract_tickers_from_title(article.title)
        
        # Save ticker relevances
        for ticker in extracted_tickers:
            ticker_rel = NewsTickerRelevance(
                article_id=article.id,
                ticker=ticker.upper(),
                relevance_score=0.8,
                sentiment_for_ticker=float(analysis_data.get("sentiment_score", 0.0)),
            )
            self.db.add(ticker_rel)
        
        self.db.commit()
        self.db.refresh(news_analysis)
        
        return news_analysis
    
    def analyze_batch(self, articles: List[NewsArticle], max_count: int = 50) -> Dict[str, Any]:
        """배치 분석 (무료 한도 내에서)"""
        results = {
            "analyzed": 0,
            "skipped": 0,
            "errors": 0,
            "details": []
        }
        
        for i, article in enumerate(articles[:max_count]):
            if not check_rate_limit():
                results["errors"] += 1
                break
            
            try:
                analysis = self.analyze_article(article)
                if analysis:
                    results["analyzed"] += 1
                    results["details"].append({
                        "title": article.title[:60],
                        "sentiment": analysis.sentiment_overall
                    })
                else:
                    results["skipped"] += 1
            except Exception as e:
                results["errors"] += 1
                results["details"].append({"error": str(e)})
            
            if (i + 1) % 10 == 0:
                import time
                time.sleep(1)
        
        return results


# ============================================================================
# Helper Functions
# ============================================================================

def get_analyzed_articles(
    db: Session,
    limit: int = 50,
    sentiment: Optional[str] = None,
    actionable_only: bool = False
) -> List[NewsArticle]:
    """분석된 기사 조회"""
    query = db.query(NewsArticle).join(NewsAnalysis)
    
    if sentiment:
        query = query.filter(NewsAnalysis.sentiment_overall == sentiment)
    
    if actionable_only:
        query = query.filter(NewsAnalysis.trading_actionable == True)

    return query.order_by(NewsArticle.published_date.desc()).limit(limit).all()


def get_ticker_news(db: Session, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
    """특정 티커 관련 뉴스"""
    relevances = (
        db.query(NewsTickerRelevance)
        .filter(NewsTickerRelevance.ticker == ticker)
        .order_by(NewsTickerRelevance.relevance_score.desc())
        .limit(limit)
        .all()
    )

    results = []
    for rel in relevances:
        article = rel.article
        results.append({
            "article_id": article.id,
            "title": article.title,
            "source": article.source,
            "published_at": article.published_date.isoformat() if article.published_date else None,
            "relevance": rel.relevance_score,
            "sentiment": rel.sentiment_for_ticker
        })

    return results


def get_high_impact_news(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """고영향도 뉴스 조회"""
    from backend.data.news_models import NewsArticle, NewsAnalysis

    articles = (
        db.query(NewsArticle)
        .join(NewsAnalysis)
        .filter(NewsAnalysis.impact_magnitude >= 0.7)
        .order_by(NewsArticle.published_date.desc())
        .limit(limit)
        .all()
    )

    results = []
    for article in articles:
        analysis = article.analysis
        results.append({
            "id": article.id,
            "title": article.title,
            "source": article.source,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "impact_magnitude": analysis.impact_magnitude if analysis else 0,
            "urgency": analysis.urgency if analysis else "unknown"
        })

    return results


def get_warning_news(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """경고성 뉴스 조회"""
    from backend.data.news_models import NewsArticle, NewsAnalysis

    articles = (
        db.query(NewsArticle)
        .join(NewsAnalysis)
        .filter(NewsAnalysis.red_flags.isnot(None))
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for article in articles:
        analysis = article.analysis
        results.append({
            "id": article.id,
            "title": article.title,
            "source": article.source,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "red_flags": analysis.red_flags if analysis else [],
            "risk_category": analysis.risk_category if analysis else "unknown"
        })

    return results


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    print("🧠 News Deep Analysis Test (PostgreSQL)")
    
    db = get_sync_session()
    
    try:
        # Get unanalyzed articles
        # This function was in rss_crawler, let's redefine simplified or import from there if available
        # Actually it's better to raw query here to be self-contained for test
        unanalyzed = (
            db.query(NewsArticle)
            .outerjoin(NewsArticle.analysis)
            .filter(NewsArticle.analysis == None)
            .order_by(NewsArticle.published_at.desc())
            .limit(5)
            .all()
        )
        
        print(f"\n📰 Found {len(unanalyzed)} unanalyzed articles")
        
        if unanalyzed:
            analyzer = NewsDeepAnalyzer(db)
            
            print("\n🔬 Analyzing articles...")
            results = analyzer.analyze_batch(unanalyzed, max_count=2)
            
            print(f"\n✅ Analysis Complete: {results['analyzed']} analyzed")
            
    finally:
        db.close()
