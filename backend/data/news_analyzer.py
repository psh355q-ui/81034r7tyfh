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

# Google Generative AI SDK
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

from backend.data.news_models import NewsArticle, NewsAnalysis, NewsTickerRelevance, SessionLocal

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
    
    def __init__(self, db: Session):
        self.db = db
        
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
    
    def extract_tickers_from_title(self, title: str) -> List[str]:
        """
        Extract stock tickers from article title
        
        Patterns:
        - (NASDAQ:AAPL)
        - (NYSE:NVDA)
        - $AAPL
        - AAPL stock
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
        
        # 제어 문자 제거
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # 이스케이프되지 않은 개행 문자 처리
        text = text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        
        # JSON 파싱 시도
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # 더 적극적인 정리
            try:
                # 역슬래시 이스케이프 문제 수정
                text = text.replace('\\\\', '\\')
                return json.loads(text)
            except:
                pass
            
            # JSON5 스타일 정리 (trailing commas 등)
            try:
                # 마지막 콤마 제거
                text = re.sub(r',(\s*[}\]])', r'\1', text)
                return json.loads(text)
            except:
                pass
            
            # 최후의 수단: 빈 구조 반환
            print(f"⚠️ JSON parse failed after all attempts: {str(e)[:100]}")
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
        
        # 본문 확인 - content_text 또는 content_summary 사용
        if not article.content_text or len(article.content_text) < 50:
            # content_text가 없으면 content_summary 사용
            if not article.content_summary or len(article.content_summary) < 50:
                return None
        
        # 프롬프트 생성
        prompt = self.create_analysis_prompt(article)
        
        # Gemini API 호출
        import time
        start_time = time.time()
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,  # Very low for consistent structured output
                max_output_tokens=2000,
                response_mime_type="application/json",  # Force JSON response
            )
        )
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # 토큰 추정
        input_tokens = len(prompt) // 4
        output_tokens = len(response.text) // 4
        
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
        
        # 사용량 업데이트
        update_daily_usage(input_tokens, output_tokens)
        
        # 응답 파싱
        analysis_data = self.parse_analysis_response(response.text)
        
        if "error" in analysis_data:
            print(f"⚠️ Parse error for {article.title[:50]}: {analysis_data['error']}")
            return None
        
        # DB에 저장 (simplified schema)
        news_analysis = NewsAnalysis(
            article_id=article.id,
            
            # Sentiment
            sentiment_overall=analysis_data.get("sentiment", "neutral"),
            sentiment_score=float(analysis_data.get("sentiment_score", 0.0)),
            sentiment_confidence=0.8,  # Default confidence
            
            # Tone
            tone_objective_score=0.5,  # Default
            urgency=analysis_data.get("urgency", "medium"),
            sensationalism=0.0,
            
            # Market Impact
            market_impact_short=analysis_data.get("market_impact_short", "neutral"),
            market_impact_long=analysis_data.get("market_impact_long", "neutral"),
            impact_magnitude=float(analysis_data.get("impact_magnitude", 0.0)),
            affected_sectors=[],
            
            # Key Findings (minimal)
            key_facts=[],
            key_opinions=[],
            key_implications=[],
            key_warnings=[],
            
            # Indirect Expressions (minimal)
            indirect_expressions=[],
            red_flags=[],
            
            # Trading Relevance
            trading_actionable=analysis_data.get("actionable", False),
            risk_category=analysis_data.get("risk_category", "none"),
            recommendation="",
            
            # Credibility (defaults)
            source_reliability=0.7,
            data_backed=False,
            multiple_sources_cited=False,
            potential_bias="",
            
            # Model Info
            model_used=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            tokens_used=input_tokens + output_tokens,
            analysis_cost=0.0,  # 무료!
        )
        
        self.db.add(news_analysis)
        
        # Extract tickers from title
        extracted_tickers = self.extract_tickers_from_title(article.title)
        
        # Save ticker relevances
        for ticker in extracted_tickers:
            ticker_rel = NewsTickerRelevance(
                article_id=article.id,
                ticker=ticker.upper(),
                relevance_score=0.8,  # High relevance since it's in the title
                sentiment_for_ticker=float(analysis_data.get("sentiment_score", 0.0)),
            )
            self.db.add(ticker_rel)
            logger.info(f"Added ticker {ticker} for article {article.id}")
        
        # Also process AI-detected companies (if provided)
        companies = analysis_data.get("related_entities", {}).get("companies", [])
        for company in companies:
            if company.get("ticker") and company["ticker"] not in extracted_tickers:
                ticker_rel = NewsTickerRelevance(
                    article_id=article.id,
                    ticker=company["ticker"],
                    relevance_score=company.get("relevance", 0.5),
                    sentiment_for_ticker=company.get("sentiment", 0.0),
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
                results["details"].append({
                    "title": article.title,
                    "error": "Rate limit reached"
                })
                break
            
            try:
                analysis = self.analyze_article(article)
                if analysis:
                    results["analyzed"] += 1
                    results["details"].append({
                        "title": article.title[:60],
                        "sentiment": analysis.sentiment_overall,
                        "score": analysis.sentiment_score,
                        "actionable": analysis.trading_actionable
                    })
                else:
                    results["skipped"] += 1
            except Exception as e:
                results["errors"] += 1
                results["details"].append({
                    "title": article.title,
                    "error": str(e)
                })
            
            # Rate limiting (15 RPM)
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(articles[:max_count])} articles...")
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
    
    return query.order_by(NewsArticle.published_at.desc()).limit(limit).all()


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
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "relevance": rel.relevance_score,
            "sentiment": rel.sentiment_for_ticker,
            "analysis": {
                "overall_sentiment": article.analysis.sentiment_overall if article.analysis else None,
                "impact": article.analysis.market_impact_short if article.analysis else None,
                "actionable": article.analysis.trading_actionable if article.analysis else False,
            } if article.analysis else None
        })
    
    return results


def get_high_impact_news(db: Session, min_magnitude: float = 0.6) -> List[NewsArticle]:
    """높은 영향도 뉴스"""
    return (
        db.query(NewsArticle)
        .join(NewsAnalysis)
        .filter(NewsAnalysis.impact_magnitude >= min_magnitude)
        .order_by(NewsAnalysis.impact_magnitude.desc())
        .limit(20)
        .all()
    )


def get_warning_news(db: Session) -> List[NewsArticle]:
    """경고 신호가 있는 뉴스"""
    return (
        db.query(NewsArticle)
        .join(NewsAnalysis)
        .filter(NewsAnalysis.key_warnings != None)
        .filter(NewsAnalysis.key_warnings != "[]")
        .order_by(NewsArticle.published_at.desc())
        .limit(20)
        .all()
    )


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == "__main__":
    print("🧠 News Deep Analysis Test")
    
    from news_models import init_db
    init_db()
    
    db = SessionLocal()
    
    try:
        # Get unanalyzed articles
        from rss_crawler import get_unanalyzed_articles
        unanalyzed = get_unanalyzed_articles(db, limit=5)
        
        print(f"\n📰 Found {len(unanalyzed)} unanalyzed articles")
        
        if unanalyzed:
            analyzer = NewsDeepAnalyzer(db)
            
            print("\n🔬 Analyzing articles...")
            results = analyzer.analyze_batch(unanalyzed, max_count=5)
            
            print(f"\n✅ Analysis Complete!")
            print(f"  Analyzed: {results['analyzed']}")
            print(f"  Skipped: {results['skipped']}")
            print(f"  Errors: {results['errors']}")
            
            print("\n📊 Results:")
            for detail in results['details']:
                if "error" not in detail:
                    print(f"  - {detail['title']}")
                    print(f"    Sentiment: {detail['sentiment']} ({detail['score']:.2f})")
                    print(f"    Actionable: {detail['actionable']}")
                else:
                    print(f"  - {detail['title']}: ERROR - {detail['error']}")
        
        # Check usage
        usage = get_daily_usage()
        print(f"\n📈 Daily Usage: {usage['request_count']}/1500 requests")
        
    finally:
        db.close()
