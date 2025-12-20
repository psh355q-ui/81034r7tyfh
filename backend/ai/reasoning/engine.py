import logging
import os
import json
from typing import Dict, Any, Optional
import google.generativeai as genai

from backend.ai.reasoning.models import MarketThesis, ReasoningStep
from backend.ai.reasoning.prompts import DEEP_REASONING_SYSTEM_PROMPT, ANALYSIS_PROMPT_TEMPLATE
from backend.ai.reasoning.heuristics import calculate_heuristic_confidence

logger = logging.getLogger(__name__)

class DeepReasoningEngine:
    def __init__(self, model_name: str = None):
        """
        Initialize Deep Reasoning Engine with Gemini model.
        
        Args:
            model_name: Override model name. If None, reads from GEMINI_MODEL env var.
        """
        # Get model name from env or use provided override
        if model_name is None:
            model_name = os.getenv("GEMINI_MODEL")
        
        # Fallback chain if no model specified
        if not model_name:
            # Try modern models first, fallback to older stable versions
            model_name = "gemini-2.5-flash"
            logger.info(f"Using default Gemini model: {model_name}")
        else:
            logger.info(f"Using configured Gemini model: {model_name}")
        
        self.model_name = model_name
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # Allow init without key for Mock mode
        if self.api_key:
            genai.configure(api_key=self.api_key)
            try:
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"✅ DeepReasoningEngine initialized with model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                # Try fallback to stable version
                fallback_model = "gemini-1.5-flash"
                logger.warning(f"Falling back to {fallback_model}")
                self.model = genai.GenerativeModel(fallback_model)
                self.model_name = fallback_model
        else:
            self.model = None
            logger.warning("DeepReasoningEngine initialized in MOCK MODE (No API Key)")
        
    async def analyze_ticker(
        self, 
        ticker: str, 
        news_context: str, 
        technical_data: Dict[str, Any],
        news_sentiment: str = "Neutral",
        use_mock: bool = False
    ) -> Optional[MarketThesis]:
        """
        Synthesizes News and Technicals to form a Thesis.
        """
        # Mock Mode Hook
        if use_mock or not self.model:
            return self._generate_mock_thesis(ticker)

        try:
            # Construct Prompt
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                ticker=ticker,
                rag_context=news_context,
                rsi=technical_data.get('rsi', 'N/A'),
                macd=technical_data.get('macd', 'N/A'),
                ma_status=technical_data.get('ma_status', 'N/A'),
                price_action=technical_data.get('price_action', 'N/A'),
                news_sentiment=news_sentiment
            )
            
            full_prompt = f"{DEEP_REASONING_SYSTEM_PROMPT}\n\n{prompt}"
            
            response = await self.model.generate_content_async(full_prompt)
            raw_text = response.text.strip()
            
            # Clean Markdown
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()
            
            # Parse JSON
            data = json.loads(raw_text)
            
            # Validate with Pydantic
            thesis = MarketThesis(**data)
            
            # Apply Heuristics
            adjusted_score = calculate_heuristic_confidence(thesis, technical_data)
            thesis.final_confidence_score = adjusted_score
            
            return thesis
            
        except Exception as e:
            logger.error(f"Deep Reasoning Analysis failed for {ticker}: {e}")
            return None

    def _generate_mock_thesis(self, ticker: str) -> MarketThesis:
        """Generates a fake thesis for testing UI/Data flow."""
        
        # Detect Korean stocks
        is_korean = ticker.endswith('.KS') or ticker.endswith('.KQ')
        
        if is_korean:
            # Korean stock mock data
            company_name = ticker.split('.')[0]
            
            # Map common Korean companies
            korean_companies = {
                '005930': '삼성전자',
                '000660': 'SK하이닉스',
                '005380': '현대차',
                '000270': '기아',
                '035420': 'NAVER',
                '035720': '카카오',
                '373220': 'LG에너지솔루션',
                '207940': '삼성바이오로직스'
            }
            
            display_name = korean_companies.get(company_name, ticker)
            
            return MarketThesis(
                ticker=ticker,
                direction="BULLISH",
                time_horizon="SWING",
                summary=f"{display_name} Mock 분석: K칩법 수혜주로 긍정적 전망. 글로벌 수요 증가와 국내 반도체 정책 지원이 호재.",
                bull_case=f"{display_name}는 글로벌 시장 점유율 확대 중. 신규 투자와 기술 혁신으로 경쟁력 강화.",
                bear_case="환율 변동성, 중국 경제 둔화, 원자재 가격 상승 리스크 존재.",
                reasoning_trace=[
                    ReasoningStep(
                        step_number=1,
                        premise=f"{display_name} 실적 개선 뉴스 확인",
                        inference="매출 증가와 수익성 개선 예상",
                        conclusion="주가 상승 가능성 높음",
                        confidence=0.75
                    ),
                    ReasoningStep(
                        step_number=2,
                        premise="KOSPI 지수 안정적 흐름",
                        inference="시장 sentiment 긍정적",
                        conclusion="매수 타이밍 적절",
                        confidence=0.70
                    )
                ],
                key_risks=["환율 리스크", "중국 수요 감소", "반도체 재고 증가"],
                catalysts=["실적 발표 예정", "정부 지원 정책", "신제품 출시"],
                final_confidence_score=0.78
            )
        else:
            # US stock mock data (original logic)
            return MarketThesis(
                ticker=ticker,
                direction="BULLISH",
                time_horizon="SWING",
                summary=f"Mock analysis for {ticker}: Strong AI demand signals offset partially by macro fears.",
                bull_case="AI adoption accelerating, new product launch imminent.",
                bear_case="High valuation multiples, potential regulatory headwinds.",
                reasoning_trace=[
                    ReasoningStep(
                        step_number=1,
                        premise="News mentions 'Record Sales'",
                        inference="Revenue beat likely",
                        conclusion="Stock should gap up",
                        confidence=0.8
                    ),
                    ReasoningStep(
                        step_number=2,
                        premise="RSI is 65 (Neutral/High)",
                        inference="Room to run before overbought",
                        conclusion="Technical setup supports entry",
                        confidence=0.7
                    )
                ],
                key_risks=["Fed rate hike", "Competitor product launch"],
                catalysts=["Earnings call next week"],
                final_confidence_score=0.85
            )

# Singleton instance for easy import
try:
    reasoning_engine = DeepReasoningEngine()
except Exception:
    reasoning_engine = None
