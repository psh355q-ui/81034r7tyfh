"""
Analyst Agent MVP - Information (30% weight)

Phase: MVP Consolidation
Date: 2025-12-31

Purpose:
    전문 애널리스트의 정보 분석 관점
    - 뉴스 분석 및 해석 (News Agent 흡수)
    - 글로벌 매크로 경제 분석 (Macro Agent 흡수)
    - 기관 투자자 동향 분석 (Institutional Agent 흡수)
    - 반도체 패권 경쟁 지정학적 분석 (ChipWar Agent 일부 흡수)

Key Responsibilities:
    1. 뉴스 이벤트 분석 및 영향 평가
    2. 매크로 경제 지표 해석
    3. 기관 투자자 포지션 변화 추적
    4. 반도체 패권 경쟁 지정학적 리스크 평가
    5. 종합 정보 분석 리포트 생성

Absorbed Legacy Agents:
    - News Agent (100%)
    - Macro Agent (100%)
    - Institutional Agent (100%)
    - ChipWar Agent (지정학 부분)
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import google.generativeai as genai

from backend.ai.schemas.war_room_schemas import AnalystOpinion
from backend.ai.debate.news_agent import NewsAgent
from backend.ai.reasoning.deep_reasoning_agent import DeepReasoningAgent


class AnalystAgentMVP:
    """MVP Analyst Agent - 종합 정보 분석 (News + Macro + Institutional + ChipWar Geopolitics)"""

    def __init__(self):
        """Initialize Analyst Agent MVP"""
        # Gemini API 설정
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Initialize Agents
        self.news_agent = NewsAgent()
        self.deep_reasoning_agent = DeepReasoningAgent()

        # Agent configuration
        self.weight = 0.30  # 30% voting weight
        self.role = "종합 정보 애널리스트"

        # System prompt
        self.system_prompt = """당신은 전문 정보 애널리스트입니다.

역할:
1. 뉴스 이벤트 분석 및 영향 평가
2. 매크로 경제 지표 해석 (금리, 인플레이션, GDP 등)
3. 기관 투자자 포지션 변화 추적 (13F filings, insider trading)
4. 반도체 패권 경쟁 지정학적 리스크 평가 (미중 갈등, 수출 규제 등)
5. 종합 정보 분석 리포트 생성

분석 원칙:
- 팩트 기반 분석 (추측 금지)
- 단기/중기/장기 영향 구분
- 여러 정보 소스 교차 검증
- 지정학적 리스크는 확률 기반 평가

출력 형식:
{
    "action": "buy" | "sell" | "hold" | "pass",
    "confidence": 0.0 ~ 1.0,
    "reasoning": "구체적 분석 근거",
    "news_impact": {
        "sentiment": "positive" | "negative" | "neutral",
        "impact_score": 0.0 ~ 10.0,
        "time_horizon": "short" | "medium" | "long"
    },
    "macro_impact": {
        "interest_rate_risk": 0.0 ~ 10.0,
        "inflation_risk": 0.0 ~ 10.0,
        "recession_risk": 0.0 ~ 10.0,
        "overall_macro_score": -10.0 ~ 10.0
    },
    "institutional_flow": {
        "direction": "inflow" | "outflow" | "neutral",
        "magnitude": 0.0 ~ 10.0,
        "confidence": 0.0 ~ 1.0
    },
    "chipwar_risk": {
        "geopolitical_tension": 0.0 ~ 10.0,
        "export_control_risk": 0.0 ~ 10.0,
        "supply_chain_risk": 0.0 ~ 10.0,
        "overall_chipwar_score": 0.0 ~ 10.0
    },
    "overall_information_score": -10.0 ~ 10.0,
    "key_catalysts": ["catalyst1", "catalyst2", ...],
    "red_flags": ["red_flag1", "red_flag2", ...]
}

중요:
- **반드시 한글로 응답할 것** (reasoning, key_catalysts, red_flags 등 모든 텍스트 필드는 한국어로 작성)
- 정보가 불충분하면 confidence를 낮추고 "pass" 권장
- Red flags가 있으면 반드시 명시
- 반도체 패권 경쟁 리스크는 확률적으로 평가
"""

    async def analyze(
        self,
        symbol: str,
        news_articles: Optional[List[Dict[str, Any]]] = None,
        macro_indicators: Optional[Dict[str, Any]] = None,
        institutional_data: Optional[Dict[str, Any]] = None,
        chipwar_events: Optional[List[Dict[str, Any]]] = None,
        price_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        종합 정보 분석
        
        Returns:
            Dict (compatible with AnalystOpinion model)
        """
        # Get News Interpretations from News Agent
        news_interpretations = []
        deep_reasoning_result = None
        
        if news_articles:
            try:
                # 1. Use NewsAgent to interpret articles with Macro Context
                news_interpretations = await self.news_agent.interpret_articles(symbol, news_articles)
                
                # 2. [NEW] Check for Critical Geopolitical/ChipWar Events
                critical_event = self.news_agent.detect_critical_events(news_articles)
                
                if critical_event['detected']:
                    print(f"🚨 AnalystAgent: Detected {critical_event['event_type']} ({critical_event['keywords']})")
                    keywords = critical_event['keywords']
                    base_info = {'ticker': symbol, 'news_count': len(news_articles)}
                    
                    # 3. [NEW] Trigger Deep Reasonig Agent
                    deep_reasoning_result = await self.deep_reasoning_agent.analyze_event(
                        event_type=critical_event['event_type'],
                        keywords=keywords,
                        base_info=base_info
                    )
            except Exception as e:
                print(f"⚠️ AnalystAgent: News interpretation/reasoning failed: {e}")

        # Construct analysis prompt
        prompt = self._build_prompt(
            symbol=symbol,
            news_articles=news_articles,
            news_interpretations=news_interpretations,
            deep_reasoning_result=deep_reasoning_result, # [NEW] Pass result
            macro_indicators=macro_indicators,
            institutional_data=institutional_data,
            chipwar_events=chipwar_events,
            price_context=price_context
        )

        # Call Gemini API
        try:
            response = self.model.generate_content([
                self.system_prompt,
                prompt
            ])

            # Parse and Validate with Pydantic
            # _parse_response now returns AnalystOpinion object
            opinion = self._parse_response(response.text)

            # Convert to dict for compatibility
            result = opinion.model_dump()

            # Add metadata
            result['agent'] = 'analyst_mvp'
            result['weight'] = self.weight
            result['timestamp'] = datetime.utcnow().isoformat()
            result['symbol'] = symbol

            return result

        except Exception as e:
            # Error handling - return safe default
            return {
                'agent': 'analyst_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': f'분석 실패: {str(e)}',
                'news_impact': {
                    'sentiment': 'neutral',
                    'impact_score': 0.0,
                    'time_horizon': 'short'
                },
                'macro_impact': {
                    'interest_rate_risk': 5.0,
                    'inflation_risk': 5.0,
                    'recession_risk': 5.0,
                    'overall_macro_score': 0.0
                },
                'institutional_flow': {
                    'direction': 'neutral',
                    'magnitude': 0.0,
                    'confidence': 0.0
                },
                'chipwar_risk': {
                    'geopolitical_tension': 5.0,
                    'export_control_risk': 5.0,
                    'supply_chain_risk': 5.0,
                    'overall_chipwar_score': 5.0
                },
                'overall_score': 0.0,
                'key_catalysts': [],
                'red_flags': [f'Analysis error: {str(e)}'],
                'weight': self.weight,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'error': str(e)
            }

    # ... _build_prompt kept ...

    def _build_prompt(
        self,
        symbol: str,
        news_articles: Optional[List[Dict[str, Any]]] = None,
        news_interpretations: Optional[List[Dict[str, Any]]] = None,
        deep_reasoning_result: Optional[Dict[str, Any]] = None, # [NEW]
        macro_indicators: Optional[Dict[str, Any]] = None,
        institutional_data: Optional[Dict[str, Any]] = None,
        chipwar_events: Optional[List[Dict[str, Any]]] = None,
        price_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Construct analysis prompt"""
        prompt = f"Analyze information for {symbol} based on the following data:\n\n"
        
        # 1. News Analysis (with Interpretations)
        prompt += "1. News & Events:\n"
        
        # [NEW] Add Deep Reasoning Analysis (Top Priority)
        if deep_reasoning_result and deep_reasoning_result.get('status') == 'SUCCESS':
            prompt += "🚨 [CRITICAL: DEEP REASONING ANALYSIS]\n"
            prompt += f"Event Type: {deep_reasoning_result.get('event_type')}\n"
            
            # Add classification
            classification = deep_reasoning_result.get('classification', {})
            prompt += f"Classification: {classification.get('type')} (Confidence: {classification.get('confidence')})\n"
            
            # Add simulation
            simulation = deep_reasoning_result.get('simulation', {})
            prompt += f"Simulation Channel: {simulation.get('channel')}\n"
            prompt += f"Impact Chain: {simulation.get('impact_chain')}\n"
            
            # Add action plan (Most important)
            action_plan = deep_reasoning_result.get('action_plan', {})
            prompt += f"⚠️ RECOMMENDED STRATEGY: {action_plan.get('action')} (Scenario: {action_plan.get('key_scenario')})\n"
            prompt += f"   Reasoning: {action_plan.get('reasoning')}\n\n"

        # Add Expert Interpretations (High Value)
        if news_interpretations:
            prompt += "[News Agent Expert Analysis]\n"
            for i, interp in enumerate(news_interpretations):
                headline = interp.get('headline') or interp.get('title') or 'News'
                impact = interp.get('expected_impact', 'Unknown')
                score = interp.get('impact_score', 0)
                reasoning = interp.get('reasoning', 'No reasoning provided')
                
                prompt += f"- Analysis {i+1}: {headline}\n"
                prompt += f"  Impact: {impact} (Score: {score}/10)\n"
                prompt += f"  Timeframe: {interp.get('time_horizon', 'Short')}\n"
                prompt += f"  Insight: {reasoning}\n\n"
        
        # Add Raw Articles
        if news_articles:
            prompt += "[Raw News Articles]\n"
            for i, article in enumerate(news_articles[:5]):  # Limit to 5
                prompt += f"- {article.get('title')}\n"
                source = article.get('source', 'Unknown')
                summary = article.get('summary', 'N/A')
                prompt += f"  Source: {source} | Summary: {summary}\n"
        else:
            prompt += "No recent news reported.\n"

        prompt += "\n"

        # 2. Macro Indicators
        prompt += "2. Macro Economic Context:\n"
        if macro_indicators:
            for k, v in macro_indicators.items():
                prompt += f"- {k}: {v}\n"
        else:
            prompt += "No macro data provided.\n"
        prompt += "\n"

        # 3. Institutional Data
        prompt += "3. Institutional Flow:\n"
        if institutional_data:
            # Assuming simplified dict for prompt
            prompt += f"{str(institutional_data)}\n"
        else:
             prompt += "No institutional data.\n"
        prompt += "\n"
        
        # 4. Chip War / Geopolitics
        prompt += "4. Chip War & Geopolitics:\n"
        if chipwar_events:
            for event in chipwar_events:
                date_str = event.get('date', 'Unknown Date')
                evt = event.get('event', 'Unknown Event')
                impact = event.get('impact', 'Unknown Impact')
                prompt += f"- {date_str}: {evt} (Impact: {impact})\n"
        else:
             prompt += "No significant geopolitical events.\n"
        prompt += "\n"
        
        # 5. Price Context
        if price_context:
             prompt += f"5. Price Context: {price_context}\n"
        
        return prompt

    def _parse_response(self, response_text: str) -> AnalystOpinion:
        """Parse Gemini response using Pydantic"""
        import json
        import re

        # Extract JSON from response
        try:
            result_dict = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                result_dict = json.loads(json_match.group(1))
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result_dict = json.loads(json_match.group(0))
                else:
                    raise ValueError("No valid JSON found in response")

        # Basic field normalization
        if 'overall_information_score' in result_dict:
            result_dict['overall_score'] = result_dict.pop('overall_information_score')
        
        # Ensure default fields if missing (Pydantic defaults handle most, but ensure dict structure)
        
        # Instantiate and Validate with Pydantic
        return AnalystOpinion(**result_dict)

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': 'AnalystAgentMVP',
            'role': self.role,
            'weight': self.weight,
            'focus': '종합 정보 분석 (News + Macro + Institutional + 반도체 패권 경쟁)',
            'absorbed_agents': [
                'News Agent',
                'Macro Agent',
                'Institutional Agent',
                'ChipWar Agent (geopolitics)'
            ],
            'responsibilities': [
                '뉴스 이벤트 분석 및 영향 평가',
                '매크로 경제 지표 해석',
                '기관 투자자 동향 분석',
                '반도체 패권 경쟁 지정학적 리스크 평가',
                '종합 정보 분석 리포트 생성'
            ]
        }


# Example usage
if __name__ == "__main__":
    agent = AnalystAgentMVP()

    # Test data
    news_articles = [
        {
            'title': 'NVIDIA announces new AI chip',
            'source': 'Reuters',
            'published': '2025-12-30',
            'summary': 'New GPU targets enterprise AI market'
        }
    ]

    macro_indicators = {
        'interest_rate': 5.25,
        'inflation_rate': 3.1,
        'gdp_growth': 2.5,
        'fed_policy': 'hawkish'
    }

    chipwar_events = [
        {
            'event': 'US tightens chip export controls to China',
            'impact': 'Negative for NVIDIA China revenue',
            'date': '2025-12-28'
        }
    ]

    result = agent.analyze(
        symbol='NVDA',
        news_articles=news_articles,
        macro_indicators=macro_indicators,
        chipwar_events=chipwar_events,
        price_context={'current_price': 500.0, 'trend': 'uptrend'}
    )

    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Overall Info Score: {result['overall_information_score']:.1f}")
    print(f"Key Catalysts: {result['key_catalysts']}")
    print(f"Red Flags: {result['red_flags']}")
