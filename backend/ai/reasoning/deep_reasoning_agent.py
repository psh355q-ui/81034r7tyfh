"""
Deep Reasoning Agent ("The Brain")

A high-level reasoning engine that analyzes complex geopolitical and macro events.
It implements a 4-step tiered reasoning process:
1. Event Classification (Structural vs Noise)
2. Transmission Channel Analysis (Simulation)
3. Scenario Branching (Probabilistic Forecasting)
4. Actionable Signal Generation

It integrates legacy ChipWar logic for technology war scenarios.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.ai.economics.chip_war_simulator_v2 import ChipComparator
from backend.ai.gemini_client import call_gemini_api

logger = logging.getLogger(__name__)

class DeepReasoningAgent:
    """
    The Brain: 심층 추론 에이전트
    복잡한 지정학적/거시적 이벤트가 발생했을 때(NewsAgent Trigger),
    단순한 뉴스 해석을 넘어 구조적 위험과 파급 효를 시뮬레이션합니다.
    """

    def __init__(self):
        self.agent_name = "deep_reasoning"
        self.model_name = "gemini-2.0-flash-exp"
        
        # Legacy: Chip War Simulation Logic
        try:
            self.chip_comparator = ChipComparator()
            logger.info("🧠 DeepReasoningAgent: Legacy ChipComparator loaded.")
        except Exception as e:
            logger.error(f"❌ DeepReasoningAgent: Failed to load ChipComparator: {e}")
            self.chip_comparator = None

    async def analyze_event(self, event_type: str, keywords: List[str], base_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        심층 분석 메인 진입점
        
        Args:
            event_type: "GEOPOLITICS" or "CHIP_WAR"
            keywords: 감지된 키워드 (예: ['invasion', 'war'])
            base_info: 관련 티커, 기본 뉴스 정보 등
            
        Returns:
            Dict: 분석 결과 (시나리오, 행동 지침 등)
        """
        logger.info(f"🧠 DeepReasoning: Starting analysis for {event_type} (keywords: {keywords})")
        
        try:
            # 1. 이벤트 분류 (Structural vs Noise)
            classification = await self._classify_event_structure(event_type, keywords, base_info)
            
            # 노이즈로 판명되면 조기 종료
            if classification['type'] == 'NOISE':
                return self._create_noise_response(classification)

            # 2. 전파 경로 및 시뮬레이션 (Transmission Channels)
            simulation_result = await self._simulate_transmission_channels(event_type, keywords, classification)
            
            # 3. 시나리오 분기 (Scenario Branching)
            scenarios = await self._generate_scenarios(event_type, simulation_result)
            
            # 4. 행동 지침 생성 (Actionable Signals)
            action_plan = self._derive_action_plan(scenarios, base_info.get('ticker'))
            
            return {
                "agent": self.agent_name,
                "status": "SUCCESS",
                "event_type": event_type,
                "classification": classification,
                "simulation": simulation_result,
                "scenarios": scenarios,
                "action_plan": action_plan,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ DeepReasoning Analysis Failed: {e}", exc_info=True)
            return {
                "agent": self.agent_name,
                "status": "ERROR",
                "error": str(e)
            }

    async def _classify_event_structure(self, event_type: str, keywords: List[str], base_info: Dict) -> Dict[str, Any]:
        """1단계: 이벤트가 구조적 위험인지 일시적 노이즈인지 분류"""
        
        # In a real implementation, this would query market data (Yields, Oil, VIX)
        # For MVP, we use Gemini to reason based on the nature of keywords
        
        prompt = f"""
        Analyze whether the following event represents a STRUCTURAL SHIFT or MARKET NOISE.
        Also, quantify the event impact using a 0-10 scale (Event Vector).
        
        Event Type: {event_type}
        Keywords: {keywords}
        Context: {base_info}
        
        Rules:
        - STRUCTURAL: Changes fundamentals (e.g., War, Permanent Sanctions, Paradigm Shift).
        - NOISE: Temporary volatility, rumors, minor fines.
        - "Invasion" or "War" is almost always STRUCTURAL.
        
        Vector Dimensions (0-10):
        1. Intensity: Violence, suddenness, media coverage.
        2. Scope: Local (1) -> Regional (5) -> Global (10).
        3. Duration: Days (1) -> Months (5) -> Years (10).
        4. Economic: Direct GDP hit, supply chain breakage.
        
        JSON Response (Must be in Korean Language for 'reasoning'):
        {{
            "type": "STRUCTURAL" | "NOISE",
            "vectors": {{
                "intensity": 0-10,
                "scope": 0-10,
                "duration": 0-10,
                "economic": 0-10
            }},
            "confidence": 0.0-1.0,
            "reasoning": "짧은 설명 (한국어)"
        }}
        """
        
        response = await call_gemini_api(prompt, self.model_name)
        result = self._parse_json(response)
        
        # Calculate GRS (Geopolitical Risk Score)
        if "vectors" in result:
            v = result["vectors"]
            # Weighted Average: Intensity(30%) + Scope(30%) + Duration(20%) + Economic(20%)
            grs = (v.get("intensity", 0) * 0.3) + \
                  (v.get("scope", 0) * 0.3) + \
                  (v.get("duration", 0) * 0.2) + \
                  (v.get("economic", 0) * 0.2)
            result["grs_score"] = round(grs, 2)  # 0.0 ~ 10.0 scale
            result["grs_label"] = self._get_grs_label(result["grs_score"])
            
        return result

    def _get_grs_label(self, score: float) -> str:
        if score >= 8.0: return "EXTREME"
        if score >= 6.0: return "HIGH"
        if score >= 4.0: return "MODERATE"
        return "LOW"

    async def _simulate_transmission_channels(self, event_type: str, keywords: List[str], classification: Dict) -> Dict[str, Any]:
        """2단계: 파급 경로 시뮬레이션 (Chip War Logic Integration)"""
        
        # A. Chip War Case: Use Legacy Comparator
        if event_type == "CHIP_WAR" and self.chip_comparator:
            logger.info("🧠 Running Legacy ChipComparator logic...")
            
            # Example: Simulate Nvidia vs Google based on keywords
            # If keywords imply "Google TPU breakthrough", assume "google_dominance" scenario
            scenario_key = "google_dominance" if "tpu" in keywords or "custom silicon" in keywords else "base"
            
            # Run blocking legacy code in thread
            comparison = await asyncio.to_thread(
                self.chip_comparator.compare_comprehensive,
                nvidia_key="NV_Rubin",
                google_key="Google_Ironwood_v7",
                scenario=scenario_key
            )
            
            return {
                "channel": "TECHNOLOGY_COMPETITION",
                "details": {
                    "nvidia_tco": comparison["nvidia"]["tco_3yr"],
                    "google_tco": comparison["google"]["tco_3yr"],
                    "disruption_score": comparison["analysis"]["disruption_score"],
                    "verdict": comparison["analysis"]["verdict"]
                }
            }
            
        # B. Geopolitics Case: Macro Simulation
        else:
            # Detect Venezuela specifically for Matrix Logic
            is_venezuela = any("venezuela" in k.lower() for k in keywords)
            
            matrix_context = ""
            if is_venezuela:
                matrix_context = """
                REFER TO VENEZUELA SCENARIO MATRIX:
                1. Full Collapse: Oil supply shock (Bullish Oil), Region destabilized.
                2. Transition: Sanctions relief (Bearish Oil long-term, Bullish CVX/XOM).
                3. Stasis: Continued decay (Neutral).
                
                Focus on sectors: Energy (XLE), Emerging Market Bonds.
                """
            
            prompt = f"""
            Simulate the transmission channels for this geopolitical event: {keywords}
            {matrix_context}
            
            Trace the impact chain:
            Event -> Channel 1 (e.g., Oil Price) -> Channel 2 (e.g., Inflation) -> Channel 3 (e.g., Fed Rates) -> Asset Impact
            
            JSON Response (Values in Korean):
            {{
                "primary_channel": "Oil" | "Supply Chain" | "Sentiment" (Korean),
                "impact_chain": ["Step 1 (Korean)", "Step 2 (Korean)", "Step 3 (Korean)"],
                "est_severity": "HIGH" | "MEDIUM" | "LOW",
                "sector_impacts": {{
                    "Energy": "Bullish/Bearish (Korean)",
                    "Defense": "Bullish/Bearish (Korean)"
                }}
            }}
            """
            response = await call_gemini_api(prompt, self.model_name)
            return self._parse_json(response)

    async def _generate_scenarios(self, event_type: str, simulation: Dict) -> List[Dict[str, Any]]:
        """3단계: 확률적 시나리오 생성"""
        
        prompt = f"""
        Generate 3 distinct future scenarios based on this simulation result.
        
        Event Type: {event_type}
        Simulation: {simulation}
        
        JSON Response (List of objects, ALL TEXT IN KOREAN):
        [
            {{
                "name": "시나리오 A: 최상의 경우",
                "probability": 0.3,
                "description": "설명...",
                "market_implication": "시장 영향..."
            }},
            ...
        ]
        """
        response = await call_gemini_api(prompt, self.model_name)
        result = self._parse_json(response)
        if isinstance(result, list):
            return result
        return []

    def _derive_action_plan(self, scenarios: List[Dict], ticker: Optional[str]) -> Dict[str, Any]:
        """4단계: 행동 지침 생성"""
        
        # Find highest probability scenario
        dominant_scenario = max(scenarios, key=lambda x: x.get('probability', 0)) if scenarios else None
        
        if not dominant_scenario:
            return {"action": "HOLD", "reason": "No clear scenario"}
            
        # Simplistic logic for MVP
        implication = dominant_scenario.get('market_implication', '').lower()
        
        action = "HOLD"
        confidence = dominant_scenario.get('probability', 0.5)
        
        # English & Korean Sentiment Keywords
        bearish_keywords = ["bearish", "negative", "sell", "부정", "하락", "매도", "위험", "약세"]
        bullish_keywords = ["bullish", "positive", "buy", "긍정", "상승", "매수", "기회", "강세"]
        
        if any(k in implication for k in bearish_keywords):
            action = "SELL"
        elif any(k in implication for k in bullish_keywords):
            action = "BUY"
            
        return {
            "action": action,
            "confidence": confidence,
            "key_scenario": dominant_scenario['name'],
            "reasoning": f"Based on {dominant_scenario['name']}: {dominant_scenario['description']}"
        }

    def _create_noise_response(self, classification: Dict) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "status": "IGNORED",
            "reason": "Classified as NOISE",
            "details": classification
        }

    def _parse_json(self, response_text: str) -> Any:
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(response_text)
        except Exception:
            return {}
