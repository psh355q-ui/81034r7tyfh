"""
Analyst Agent MVP - Information (30% weight)

Phase: MVP Consolidation
Date: 2025-12-31

Purpose:
    전문 애널리스트의 정보 분석 관점
    - 뉴스 분석 및 해석 (News Agent 흡수)
    - 글로벌 매크로 경제 분석 (Macro Agent 흡수)
    - 기관 투자자 동향 분석 (Institutional Agent 흡수)
    - 칩워 지정학적 분석 (ChipWar Agent 일부 흡수)

Key Responsibilities:
    1. 뉴스 이벤트 분석 및 영향 평가
    2. 매크로 경제 지표 해석
    3. 기관 투자자 포지션 변화 추적
    4. 칩워 지정학적 리스크 평가
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

        # Agent configuration
        self.weight = 0.30  # 30% voting weight
        self.role = "종합 정보 애널리스트"

        # System prompt
        self.system_prompt = """당신은 전문 정보 애널리스트입니다.

역할:
1. 뉴스 이벤트 분석 및 영향 평가
2. 매크로 경제 지표 해석 (금리, 인플레이션, GDP 등)
3. 기관 투자자 포지션 변화 추적 (13F filings, insider trading)
4. 칩워 지정학적 리스크 평가 (미중 갈등, 수출 규제 등)
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
- 정보가 불충분하면 confidence를 낮추고 "pass" 권장
- Red flags가 있으면 반드시 명시
- 매크로/칩워 리스크는 확률적으로 평가
"""

    def analyze(
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

        Args:
            symbol: 종목 심볼 (예: NVDA, TSM)
            news_articles: 뉴스 기사 리스트 (optional)
                [
                    {
                        'title': str,
                        'published': str,
                        'source': str,
                        'summary': str
                    }
                ]
            macro_indicators: 매크로 경제 지표 (optional)
                {
                    'interest_rate': float,
                    'inflation_rate': float,
                    'gdp_growth': float,
                    'unemployment_rate': float,
                    'fed_policy': str (hawkish/dovish/neutral)
                }
            institutional_data: 기관 투자자 데이터 (optional)
                {
                    'latest_13f_changes': [{'institution': str, 'change_pct': float}],
                    'insider_trading': [{'type': 'buy'|'sell', 'amount': float}],
                    'institutional_ownership_pct': float
                }
            chipwar_events: 칩워 관련 이벤트 (optional)
                [
                    {
                        'event': str,
                        'impact': str,
                        'date': str,
                        'source': str
                    }
                ]
            price_context: 가격 맥락 (optional)
                {
                    'current_price': float,
                    'trend': str
                }

        Returns:
            Dict containing:
                - action: buy/sell/hold/pass
                - confidence: 0.0 ~ 1.0
                - reasoning: 종합 분석 근거
                - news_impact: 뉴스 영향 분석
                - macro_impact: 매크로 영향 분석
                - institutional_flow: 기관 자금 흐름
                - chipwar_risk: 칩워 리스크
                - overall_information_score: 종합 정보 점수
                - key_catalysts: 주요 촉매제
                - red_flags: 경고 신호
        """
        # Construct analysis prompt
        prompt = self._build_prompt(
            symbol=symbol,
            news_articles=news_articles,
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

            # Parse response
            result = self._parse_response(response.text)

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
                'overall_information_score': 0.0,
                'key_catalysts': [],
                'red_flags': [f'Analysis error: {str(e)}'],
                'weight': self.weight,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'error': str(e)
            }

    def _build_prompt(
        self,
        symbol: str,
        news_articles: Optional[List[Dict[str, Any]]],
        macro_indicators: Optional[Dict[str, Any]],
        institutional_data: Optional[Dict[str, Any]],
        chipwar_events: Optional[List[Dict[str, Any]]],
        price_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive analysis prompt"""
        prompt_parts = [
            f"종목: {symbol}",
        ]

        # Price context
        if price_context:
            prompt_parts.append(f"현재가: ${price_context.get('current_price', 'N/A')}")
            prompt_parts.append(f"트렌드: {price_context.get('trend', 'N/A')}")

        # News articles
        if news_articles and len(news_articles) > 0:
            prompt_parts.append("\n=== 뉴스 분석 ===")
            for i, article in enumerate(news_articles[:5]):  # Top 5
                prompt_parts.append(f"\n[뉴스 {i+1}]")
                prompt_parts.append(f"제목: {article.get('title', 'N/A')}")
                prompt_parts.append(f"출처: {article.get('source', 'N/A')}")
                prompt_parts.append(f"발행: {article.get('published', 'N/A')}")
                if 'summary' in article:
                    prompt_parts.append(f"요약: {article['summary']}")

        # Macro indicators
        if macro_indicators:
            prompt_parts.append("\n=== 매크로 경제 지표 ===")
            if 'interest_rate' in macro_indicators:
                prompt_parts.append(f"기준금리: {macro_indicators['interest_rate']:.2f}%")
            if 'inflation_rate' in macro_indicators:
                prompt_parts.append(f"인플레이션: {macro_indicators['inflation_rate']:.2f}%")
            if 'gdp_growth' in macro_indicators:
                prompt_parts.append(f"GDP 성장률: {macro_indicators['gdp_growth']:.2f}%")
            if 'unemployment_rate' in macro_indicators:
                prompt_parts.append(f"실업률: {macro_indicators['unemployment_rate']:.2f}%")
            if 'fed_policy' in macro_indicators:
                prompt_parts.append(f"연준 정책 스탠스: {macro_indicators['fed_policy']}")

        # Institutional data
        if institutional_data:
            prompt_parts.append("\n=== 기관 투자자 동향 ===")
            if 'institutional_ownership_pct' in institutional_data:
                prompt_parts.append(f"기관 보유 비율: {institutional_data['institutional_ownership_pct']:.1f}%")

            if 'latest_13f_changes' in institutional_data:
                changes = institutional_data['latest_13f_changes']
                if changes:
                    prompt_parts.append("최근 13F 변동:")
                    for change in changes[:3]:  # Top 3
                        inst = change.get('institution', 'Unknown')
                        pct = change.get('change_pct', 0)
                        prompt_parts.append(f"  - {inst}: {pct:+.1f}%")

            if 'insider_trading' in institutional_data:
                trades = institutional_data['insider_trading']
                if trades:
                    prompt_parts.append("내부자 거래:")
                    for trade in trades[:3]:  # Top 3
                        trade_type = trade.get('type', 'N/A')
                        amount = trade.get('amount', 0)
                        prompt_parts.append(f"  - {trade_type.upper()}: ${amount:,.0f}")

        # ChipWar events
        if chipwar_events and len(chipwar_events) > 0:
            prompt_parts.append("\n=== 칩워 지정학 이벤트 ===")
            for i, event in enumerate(chipwar_events[:5]):  # Top 5
                prompt_parts.append(f"\n[이벤트 {i+1}]")
                prompt_parts.append(f"내용: {event.get('event', 'N/A')}")
                prompt_parts.append(f"영향: {event.get('impact', 'N/A')}")
                prompt_parts.append(f"날짜: {event.get('date', 'N/A')}")
                if 'source' in event:
                    prompt_parts.append(f"출처: {event['source']}")

        prompt_parts.append("\n위 정보를 종합적으로 분석하고 JSON 형식으로 답변하세요.")

        return "\n".join(prompt_parts)

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response"""
        import json
        import re

        # Extract JSON from response
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    raise ValueError("No valid JSON found in response")

        # Validate and provide defaults for required fields
        if 'action' not in result:
            result['action'] = 'pass'
        if 'confidence' not in result:
            result['confidence'] = 0.5
        if 'reasoning' not in result:
            result['reasoning'] = 'No reasoning provided'

        # Validate news_impact
        if 'news_impact' not in result:
            result['news_impact'] = {}
        news = result['news_impact']
        if 'sentiment' not in news:
            news['sentiment'] = 'neutral'
        if 'impact_score' not in news:
            news['impact_score'] = 0.0
        if 'time_horizon' not in news:
            news['time_horizon'] = 'short'

        # Validate macro_impact
        if 'macro_impact' not in result:
            result['macro_impact'] = {}
        macro = result['macro_impact']
        macro.setdefault('interest_rate_risk', 5.0)
        macro.setdefault('inflation_risk', 5.0)
        macro.setdefault('recession_risk', 5.0)
        macro.setdefault('overall_macro_score', 0.0)

        # Validate institutional_flow
        if 'institutional_flow' not in result:
            result['institutional_flow'] = {}
        inst = result['institutional_flow']
        inst.setdefault('direction', 'neutral')
        inst.setdefault('magnitude', 0.0)
        inst.setdefault('confidence', 0.0)

        # Validate chipwar_risk
        if 'chipwar_risk' not in result:
            result['chipwar_risk'] = {}
        chipwar = result['chipwar_risk']
        chipwar.setdefault('geopolitical_tension', 5.0)
        chipwar.setdefault('export_control_risk', 5.0)
        chipwar.setdefault('supply_chain_risk', 5.0)
        chipwar.setdefault('overall_chipwar_score', 5.0)

        # Validate overall_information_score
        if 'overall_information_score' not in result:
            result['overall_information_score'] = 0.0

        # Validate key_catalysts and red_flags
        if 'key_catalysts' not in result:
            result['key_catalysts'] = []
        if 'red_flags' not in result:
            result['red_flags'] = []

        # Value range validation
        valid_actions = ['buy', 'sell', 'hold', 'pass']
        if result['action'] not in valid_actions:
            result['action'] = 'pass'

        result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
        news['impact_score'] = max(0.0, min(10.0, float(news['impact_score'])))

        valid_sentiments = ['positive', 'negative', 'neutral']
        if news['sentiment'] not in valid_sentiments:
            news['sentiment'] = 'neutral'

        valid_horizons = ['short', 'medium', 'long']
        if news['time_horizon'] not in valid_horizons:
            news['time_horizon'] = 'short'

        # Clamp macro scores
        for key in ['interest_rate_risk', 'inflation_risk', 'recession_risk']:
            macro[key] = max(0.0, min(10.0, float(macro[key])))
        macro['overall_macro_score'] = max(-10.0, min(10.0, float(macro['overall_macro_score'])))

        # Validate institutional direction
        valid_directions = ['inflow', 'outflow', 'neutral']
        if inst['direction'] not in valid_directions:
            inst['direction'] = 'neutral'
        inst['magnitude'] = max(0.0, min(10.0, float(inst['magnitude'])))
        inst['confidence'] = max(0.0, min(1.0, float(inst['confidence'])))

        # Clamp chipwar scores
        for key in ['geopolitical_tension', 'export_control_risk', 'supply_chain_risk', 'overall_chipwar_score']:
            chipwar[key] = max(0.0, min(10.0, float(chipwar[key])))

        result['overall_information_score'] = max(-10.0, min(10.0, float(result['overall_information_score'])))

        return result

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': 'AnalystAgentMVP',
            'role': self.role,
            'weight': self.weight,
            'focus': '종합 정보 분석 (News + Macro + Institutional + ChipWar)',
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
                '칩워 지정학적 리스크 평가',
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
