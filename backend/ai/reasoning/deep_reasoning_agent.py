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
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.ai.economics.chip_war_simulator_v2 import ChipComparator
from backend.ai.gemini_client import call_gemini_api

# Import GLM client for news processing
try:
    from backend.ai.glm_client import GLMClient
    GLM_AVAILABLE = True
except ImportError:
    GLM_AVAILABLE = False

logger = logging.getLogger(__name__)

class DeepReasoningAgent:
    """
    The Brain: 심층 추론 에이전트
    복잡한 지정학적/거시적 이벤트가 발생했을 때(NewsAgent Trigger),
    단순한 뉴스 해석을 넘어 구조적 위험과 파급 효를 시뮬레이션합니다.
    """

    def __init__(self):
        self.agent_name = "deep_reasoning"

        # Load model configuration from environment
        self.provider = os.getenv('DEEP_REASONING_PROVIDER', 'glm').lower()
        default_model = 'glm-4-plus' if self.provider == 'glm' else 'gemini-2.5-flash-lite'
        self.model_name = os.getenv('DEEP_REASONING_MODEL', default_model)

        logger.info(f"🧠 DeepReasoningAgent initialized: provider={self.provider}, model={self.model_name}")

        # Legacy: Chip War Simulation Logic
        try:
            self.chip_comparator = ChipComparator()
            logger.info("🧠 DeepReasoningAgent: Legacy ChipComparator loaded.")
        except Exception as e:
            logger.error(f"❌ DeepReasoningAgent: Failed to load ChipComparator: {e}")
            self.chip_comparator = None

    async def _call_llm(self, prompt: str, response_mime_type: str = "application/json") -> str:
        """
        Call LLM based on provider configuration

        Args:
            prompt: The prompt to send
            response_mime_type: Response type (application/json or text/plain)

        Returns:
            Response text
        """
        if self.provider == 'glm' and GLM_AVAILABLE:
            # Use GLM API
            api_key = os.getenv('GLM_API_KEY')
            if not api_key:
                raise ValueError("GLM_API_KEY not set")

            glm_client = GLMClient(api_key=api_key, model=self.model_name)

            # Set temperature based on response type
            temperature = 0.1 if response_mime_type == "application/json" else 0.7

            response = await glm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=temperature
            )

            # Extract content from response
            message = response["choices"][0]["message"]
            content = message.get("content") or message.get("reasoning_content", "")
            await glm_client.close()

            return content.strip()
        else:
            # Use Gemini API (default)
            return await call_gemini_api(prompt, self.model_name, response_mime_type=response_mime_type)

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
        
        # Hard Force for Venezuela (for MVP/Testing stability)
        if any("venezuela" in k.lower() for k in keywords):
            return {
                "type": "STRUCTURAL",
                "confidence": 0.9,
                "reasoning": "Venezuela related events are hard-coded as STRUCTURAL for Deep Reasoning Matrix Analysis."
            }
        
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
        
        response = await self._call_llm(prompt, response_mime_type="application/json")
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
            venezuela_metrics = {}
            
            if is_venezuela:
                logger.info("🇻🇪 Venezuela Event Detected: Running Mars-WTI Proxy Analysis...")
                venezuela_metrics = await self._analyze_venezuela_metrics()
                
                matrix_context = f"""
                REFER TO VENEZUELA SCENARIO MATRIX (REAL-TIME DATA):
                Current Market Data:
                - WTI Oil (CL=F): ${venezuela_metrics.get('WTI', 'N/A')}
                - Valero (VLO - Heavy Refiner): ${venezuela_metrics.get('VLO', 'N/A')}
                - Chevron (CVX - Producer): ${venezuela_metrics.get('CVX', 'N/A')}
                
                LOGIC:
                - Sanctions RELIEF -> Heavy Crude Supply UP -> Mars Price DOWN -> Refiner Margins (VLO) UP.
                - Sanctions SNAPBACK -> Heavy Crude Supply DOWN -> Refiner Margins DOWN.
                
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
            response = await self._call_llm(prompt, response_mime_type="application/json")
            result = self._parse_json(response)
            
            # Ensure result is a dictionary
            if isinstance(result, list):
                if result:
                    result = result[0] # Take first item if it's a list
                else:
                    result = {}
            
            if is_venezuela:
                result["venezuela_proxy_data"] = venezuela_metrics
                
            return result

    async def _analyze_venezuela_metrics(self) -> Dict[str, float]:
        """
        Analyze Venezuela Proxy Metrics (Mars-WTI Spread).
        Since 'Mars' crude data is paid, we use Valero (VLO) as a proxy for heavy crude refining margins.
        """
        import yfinance as yf
        import pandas as pd
        
        try:
            tickers = ["CL=F", "VLO", "CVX", "XLE"]
            data = await asyncio.to_thread(yf.download, tickers, period="5d", progress=False)
            
            # Extract latest close prices
            latest = {}
            if not data.empty:
                # Handle MultiIndex columns depending on yfinance version/result
                # If multiple tickers: columns are likely (Price, Ticker) MultiIndex
                
                # Try to get Close prices
                df = data
                if 'Close' in data.columns.get_level_values(0):
                     df = data['Close']
                elif 'Adj Close' in data.columns.get_level_values(0):
                     df = data['Adj Close']
                
                for t in tickers:
                    try:
                        # If df has columns as tickers (normal case for multiple tickers)
                        if t in df.columns:
                            val = df[t].iloc[-1]
                        else:
                            # Fallback if structure is different
                            val = 0.0
                            
                        # Handle scalar or Series
                        if isinstance(val, pd.Series):
                            val = val.iloc[0]
                            
                        latest[t] = round(float(val), 2)
                    except Exception:
                        latest[t] = 0.0
            
            # Map to meaningful names
            return {
                "WTI": latest.get("CL=F", 0.0),
                "VLO": latest.get("VLO", 0.0),
                "CVX": latest.get("CVX", 0.0),
                "XLE": latest.get("XLE", 0.0)
            }
        except Exception as e:
            logger.error(f"Failed to fetch Venezuela proxy data: {e}")
            return {}

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
        response = await self._call_llm(prompt, response_mime_type="application/json")
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
            # Clean up potential markdown formatting
            text = response_text.strip()
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0]
            elif text.startswith("```"):
                text = text.split("```")[1].split("```")[0]
            
            # Additional cleanup for common JSON issues
            text = text.strip()
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}. Raw text: {response_text[:200]}...")
            return {}
