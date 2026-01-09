"""
뉴스 분석을 위한 Ollama 클라이언트 래퍼.
Gemini API를 대체합니다.
"""
import httpx
from typing import Dict, Any, List
import json
import logging
import os

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama LLM 클라이언트 (Gemini 대체)"""
    
    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        timeout: float = 60.0
    ):
        """
        Ollama 클라이언트 초기화
        
        Args:
            base_url: Ollama 서버 URL (기본: http://localhost:11434)
            model: 사용할 모델 (기본: llama3.2:3b)
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = model or os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
        self.timeout = timeout
        
        logger.info(f"Ollama client initialized: {self.base_url}, model: {self.model}")
    
    def check_health(self) -> bool:
        """
        Ollama 서버 상태 확인
        
        Returns:
            서버가 정상이면 True
        """
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    def analyze_news_sentiment(self, title: str, content: str) -> Dict[str, Any]:
        """
        뉴스 감성 및 거래 영향 분석
        
        Args:
            title: 뉴스 제목
            content: 뉴스 본문
            
        Returns:
            {
                'sentiment_overall': 'positive' | 'negative' | 'neutral',
                'sentiment_score': float,  # -1.0 ~ 1.0
                'confidence': float,  # 0.0 ~ 1.0
                'trading_actionable': bool,
                'key_points': List[str],
                'affected_tickers': List[str]
            }
        """
        prompt = f"""당신은 금융 뉴스 분석 전문가입니다. 다음 뉴스를 분석하세요:

제목: {title}
내용: {content[:1500]}

다음 JSON 형식으로 분석 결과를 제공하세요:
{{
    "sentiment_overall": "positive/negative/neutral",
    "sentiment_score": 0.0,
    "confidence": 0.85,
    "trading_actionable": true,
    "key_points": ["핵심 포인트1", "핵심 포인트2"],
    "affected_tickers": ["AAPL", "MSFT"]
}}

규칙:
- sentiment_score: -1.0 (매우 부정) ~ 1.0 (매우 긍정)
- confidence: 0.0 ~ 1.0 (분석 확신도)
- trading_actionable: 거래에 영향을 줄 만한 뉴스인지
- key_points: 최대 3개
- affected_tickers: 관련 주식 티커 (없으면 빈 리스트)

유효한 JSON만 응답하세요."""

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.3,  # 일관성을 위해 낮은 온도
                        "num_predict": 300   # 토큰 제한
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._fallback_analysis()
            
            result = response.json()
            
            # JSON 파싱
            try:
                analysis = json.loads(result["response"])
                
                # 유효성 검증
                required_keys = ['sentiment_overall', 'sentiment_score', 'confidence']
                if not all(key in analysis for key in required_keys):
                    logger.warning("Missing required keys in Ollama response")
                    return self._fallback_analysis()
                
                logger.info(f"✅ News analyzed: {analysis['sentiment_overall']} ({analysis['sentiment_score']:.2f})")
                return analysis
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Ollama JSON response: {e}")
                logger.debug(f"Raw response: {result.get('response', '')}")
                return self._fallback_analysis()
            
        except httpx.TimeoutException:
            logger.error(f"Ollama request timeout ({self.timeout}s)")
            return self._fallback_analysis()
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return self._fallback_analysis()
    
    def _fallback_analysis(self) -> Dict[str, Any]:
        """
        Ollama 실패 시 폴백 분석
        
        Returns:
            기본 중립 분석 결과
        """
        return {
            'sentiment_overall': 'neutral',
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'trading_actionable': False,
            'key_points': [],
            'affected_tickers': []
        }


# 글로벌 인스턴스 (싱글톤)
_ollama_client = None


def get_ollama_client() -> OllamaClient:
    """
    Ollama 클라이언트 싱글톤 인스턴스 가져오기
    
    Returns:
        OllamaClient 인스턴스
    """
    global _ollama_client
    
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    
    return _ollama_client
