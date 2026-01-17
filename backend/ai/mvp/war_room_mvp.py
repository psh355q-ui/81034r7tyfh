"""
War Room MVP - Two-Stage Edition

Phase: MVP Consolidation - Two-Stage Architecture
Date: 2026-01-17

Purpose:
    Two-Stage 아키텍처가 적용된 War Room
    - Trader Agent MVP (35% weight) - Two-Stage
    - Risk Agent MVP (30% weight) - Two-Stage
    - Analyst Agent MVP (35% weight) - Two-Stage
    - PM Agent MVP - Final Decision (Hard Rules + Silence Policy)

Two-Stage Architecture:
    Stage 1: Reasoning Agent (GLM-4.7) → 자연어 추론
    Stage 2: Structuring Agent (GLM-4-Flash) → JSON 변환

Benefits:
    - GLM-4.7 추론 능력 최대화
    - JSON 안정성 확보
    - 각 스테이지 독립적 최적화 가능
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Two-Stage MVP Agents
from .trader_agent_mvp import TraderAgentMVP
from .risk_agent_mvp import RiskAgentMVP
from .analyst_agent_mvp import AnalystAgentMVP
from .pm_agent_mvp import PMAgentMVP

# Execution layer
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.execution.execution_router import ExecutionRouter
from backend.execution.order_validator import OrderValidator
from backend.monitoring.performance_monitor import perf_monitor

# Persona Router for dynamic weights
from backend.ai.router.persona_router import PersonaRouter, PersonaMode, get_persona_router


class WarRoomMVP:
    """MVP War Room - Two-Stage Agent System"""

    def __init__(self):
        """Initialize War Room MVP with Two-Stage Agents"""
        # Initialize Two-Stage agents
        self.trader_agent = TraderAgentMVP()
        self.risk_agent = RiskAgentMVP()
        self.analyst_agent = AnalystAgentMVP()

        # Initialize PM agent (final decision maker)
        self.pm_agent = PMAgentMVP()
        print(f"🔍 DEBUG: PM Agent HARD_RULES loaded: max_agent_disagreement = {self.pm_agent.HARD_RULES['max_agent_disagreement']}")

        # Initialize execution layer
        self.execution_router = ExecutionRouter()
        self.order_validator = OrderValidator()

        # War Room metadata
        self.session_id = datetime.utcnow().isoformat()
        self.decision_history: List[Dict[str, Any]] = []

        # Persona Router for dynamic weights
        self.persona_router = get_persona_router()

        print(f"✅ WarRoomMVP initialized with Two-Stage agents")
        print(f"   - Trader: {self.trader_agent.get_agent_info()['name']}")
        print(f"   - Risk: {self.risk_agent.get_agent_info()['name']}")
        print(f"   - Analyst: {self.analyst_agent.get_agent_info()['name']}")

    async def deliberate(
        self,
        symbol: str,
        action_context: str,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None,
        persona_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        전쟁실 심의 - Two-Stage Agent 협업 의사결정

        Args:
            symbol: 종목 심볼 (예: AAPL, NVDA)
            action_context: 액션 맥락 (예: "new_position", "stop_loss_check", "rebalancing")
            market_data: 시장 데이터
            portfolio_state: 포트폴리오 상태
            additional_data: 추가 데이터 (optional)
            persona_mode: 페르소나 모드 (optional)

        Returns:
            Dict containing final decision and all agent opinions
        """
        print(f"\n{'='*80}")
        print(f"WAR ROOM MVP (Two-Stage) - Deliberation Started")
        print(f"Symbol: {symbol} | Context: {action_context}")
        print(f"Session: {self.session_id}")
        print(f"{'='*80}\n")

        # ================================================================
        # STEP 1: EXECUTION ROUTING (Fast Track vs Deep Dive)
        # ================================================================
        print("[STEP 1] Execution Routing...")
        routing_result = self.execution_router.route(
            action=action_context,
            symbol=symbol,
            current_state=market_data.get('price_data', {}),
            market_conditions=market_data.get('market_conditions'),
            portfolio_context=portfolio_state
        )

        execution_mode = routing_result['execution_mode']
        print(f"  → Mode: {execution_mode}")
        print(f"  → Reasoning: {routing_result['reasoning']}\n")

        # Fast Track: Skip AI, use rule-based execution
        if routing_result['bypass_ai']:
            print("[FAST TRACK] Bypassing AI - Rule-based execution\n")
            return {
                'final_decision': 'fast_track_executed',
                'execution_mode': execution_mode,
                'routing_result': routing_result,
                'timestamp': datetime.utcnow().isoformat()
            }

        # ================================================================
        # STEP 2: TWO-STAGE AGENT DELIBERATION (Parallelized)
        # ================================================================
        print("[STEP 2] Two-Stage Agent Deliberation...\n")

        # Extract data for agents
        price_data = market_data.get('price_data', {})
        technical_data = market_data.get('technical_data')
        market_conditions = market_data.get('market_conditions')
        multi_timeframe = market_data.get('multi_timeframe')
        option_data = market_data.get('option_data')

        # Run all three agents in parallel (Stage 1 + Stage 2 handled internally)
        print("  [Parallel] Starting Two-Stage Agents...")
        trader_task = self.trader_agent.analyze(
            symbol=symbol,
            price_data=price_data,
            technical_data=technical_data,
            chipwar_events=additional_data.get('chipwar_events') if additional_data else None,
            market_context=market_conditions,
            multi_timeframe_data=multi_timeframe,
            option_data=option_data
        )

        risk_task = self.risk_agent.analyze(
            symbol=symbol,
            price_data=price_data,
            technical_data=technical_data,
            position_size_pct=portfolio_state.get('position_size_pct'),
            market_context=market_conditions
        )

        analyst_task = self.analyst_agent.analyze(
            symbol=symbol,
            price_data=price_data,
            technical_data=technical_data,
            news_data=additional_data.get('news_articles') if additional_data else None,
            macro_data=additional_data.get('macro_indicators') if additional_data else None,
            institutional_flow=additional_data.get('institutional_data') if additional_data else None,
            geopolitical_risks=additional_data.get('geopolitical_risks') if additional_data else None,
            sector_context=additional_data.get('sector_context') if additional_data else None
        )

        # Wait for all agents
        trader_opinion, risk_opinion, analyst_opinion = await asyncio.gather(
            trader_task, risk_task, analyst_task, return_exceptions=True
        )

        # Handle exceptions
        if isinstance(trader_opinion, Exception):
            print(f"  ❌ [Trader Agent] Failed: {trader_opinion}")
            trader_opinion = self._get_safe_default('trader', symbol)
        else:
            latency = trader_opinion.get('latency_seconds', 'N/A')
            print(f"  ✅ [Trader Agent] Action: {trader_opinion.get('action', 'N/A')} (Confidence: {trader_opinion.get('confidence', 0):.2f}, Latency: {latency}s)")

        if isinstance(risk_opinion, Exception):
            print(f"  ❌ [Risk Agent] Failed: {risk_opinion}")
            risk_opinion = self._get_safe_default('risk', symbol)
        else:
            latency = risk_opinion.get('latency_seconds', 'N/A')
            print(f"  ✅ [Risk Agent] Recommendation: {risk_opinion.get('recommendation', 'N/A')} (Level: {risk_opinion.get('risk_level', 'N/A')}, Latency: {latency}s)")

        if isinstance(analyst_opinion, Exception):
            print(f"  ❌ [Analyst Agent] Failed: {analyst_opinion}")
            analyst_opinion = self._get_safe_default('analyst', symbol)
        else:
            latency = analyst_opinion.get('latency_seconds', 'N/A')
            print(f"  ✅ [Analyst Agent] Action: {analyst_opinion['action']} (Score: {analyst_opinion.get('overall_information_score', 0):.1f}, Latency: {latency}s)")

        # ================================================================
        # STEP 2.5: INJECT DYNAMIC WEIGHTS FROM PERSONA ROUTER
        # ================================================================
        weights = self.persona_router.get_weights(persona_mode)
        persona_config = self.persona_router.get_config(persona_mode)

        # Inject weights into each agent's opinion
        trader_opinion['weight'] = weights.get('trader_mvp', 0.35)
        risk_opinion['weight'] = weights.get('risk_mvp', 0.30)
        analyst_opinion['weight'] = weights.get('analyst_mvp', 0.35)

        print(f"\n  [Persona Mode] {persona_config.mode.value.upper()}")
        print(f"  [Dynamic Weights] Trader={weights['trader_mvp']:.0%}, Risk={weights['risk_mvp']:.0%}, Analyst={weights['analyst_mvp']:.0%}")

        # ================================================================
        # STEP 3: PM FINAL DECISION (Hard Rules + Silence Policy)
        # ================================================================
        print("\n[STEP 3] PM Final Decision (Hard Rules + Silence Policy)...\n")

        pm_decision = self.pm_agent.make_final_decision(
            symbol=symbol,
            trader_opinion=trader_opinion,
            risk_opinion=risk_opinion,
            analyst_opinion=analyst_opinion,
            portfolio_state=portfolio_state,
            correlation_data=additional_data.get('correlation_data') if additional_data else None
        )

        print(f"  → Final Decision: {pm_decision['final_decision']}")
        print(f"  → Confidence: {pm_decision['confidence']:.2f}")
        print(f"  → Hard Rules Passed: {pm_decision['hard_rules_passed']}")
        if pm_decision.get('hard_rules_violations'):
            print(f"  → Violations: {pm_decision['hard_rules_violations']}")

        # ================================================================
        # STEP 4: ORDER VALIDATION (if approved)
        # ================================================================
        validation_result = None
        if pm_decision['final_decision'] == 'approve':
            print("\n[STEP 4] Order Validation (Hard Rules)...\n")

            # Construct order from decisions
            order = {
                'symbol': symbol,
                'action': pm_decision['recommended_action'],
                'quantity': int(risk_opinion.get('max_position_pct', 0.05) * portfolio_state.get('total_value', 0) / price_data.get('current_price', 1)),
                'price': price_data.get('current_price', 0),
                'order_value': risk_opinion.get('max_position_pct', 0.05) * portfolio_state.get('total_value', 0),
                'position_size_pct': risk_opinion.get('max_position_pct', 0.05),
                'stop_loss_pct': risk_opinion.get('stop_loss_pct', 0.02),
                'timestamp': datetime.utcnow().isoformat()
            }

            validation_result = self.order_validator.validate(
                order=order,
                portfolio_state=portfolio_state,
                market_state=market_conditions
            )

            print(f"  → Validation Result: {validation_result['result']}")
            print(f"  → Can Execute: {validation_result['can_execute']}")

        # ================================================================
        # STEP 5: CONVERSATION SUMMARY
        # ================================================================
        conversation_summary = self._generate_summary(
            trader_opinion=trader_opinion,
            risk_opinion=risk_opinion,
            analyst_opinion=analyst_opinion,
            pm_decision=pm_decision,
            validation_result=validation_result
        )

        # ================================================================
        # FINAL RESULT
        # ================================================================
        final_result = {
            'session_id': self.session_id,
            'symbol': symbol,
            'action_context': action_context,
            'execution_mode': execution_mode,
            'routing_result': routing_result,
            'agent_opinions': {
                'trader': trader_opinion,
                'risk': risk_opinion,
                'analyst': analyst_opinion
            },
            'pm_decision': pm_decision,
            'validation_result': validation_result,
            'final_decision': pm_decision['final_decision'],
            'recommended_action': pm_decision.get('recommended_action', 'hold'),
            'confidence': pm_decision['confidence'],
            'position_size_pct': risk_opinion.get('max_position_pct', 0.05),
            'stop_loss_pct': risk_opinion.get('stop_loss_pct', 0.02),
            'conversation_summary': conversation_summary,
            'can_execute': validation_result['can_execute'] if validation_result else False,
            'timestamp': datetime.utcnow().isoformat(),
            'weights': weights,
            'persona_mode': persona_config.mode.value,
            'persona_description': persona_config.description,
            'architecture': 'two-stage'
        }

        # Record in history
        self.decision_history.append(final_result)

        print(f"\n{'='*80}")
        print(f"WAR ROOM MVP (Two-Stage) - Deliberation Completed")
        print(f"Final Decision: {final_result['final_decision']}")
        print(f"Can Execute: {final_result['can_execute']}")
        print(f"{'='*80}\n")

        return final_result

    def _get_safe_default(self, agent_type: str, symbol: str) -> Dict[str, Any]:
        """Get safe default when agent fails"""
        if agent_type == 'trader':
            return {
                'agent': 'trader_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': 'Agent failed - using safe default',
                'opportunity_score': 0.0,
                'momentum_strength': 'weak',
                'weight': 0.35,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'failed'
            }
        elif agent_type == 'risk':
            return {
                'agent': 'risk_mvp',
                'risk_level': 'high',
                'confidence': 0.0,
                'reasoning': 'Agent failed - using safe default',
                'stop_loss_pct': 0.05,
                'take_profit_pct': 0.10,
                'max_position_pct': 0.05,
                'recommendation': 'reject',
                'weight': 0.30,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'failed'
            }
        else:  # analyst
            return {
                'agent': 'analyst_mvp',
                'action': 'pass',
                'confidence': 0.0,
                'reasoning': 'Agent failed - using safe default',
                'news_headline': 'Analysis failed',
                'news_sentiment': 'neutral',
                'overall_information_score': 0.0,
                'weight': 0.35,
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'stage': 'failed'
            }

    def _generate_summary(
        self,
        trader_opinion: Dict[str, Any],
        risk_opinion: Dict[str, Any],
        analyst_opinion: Dict[str, Any],
        pm_decision: Dict[str, Any],
        validation_result: Optional[Dict[str, Any]]
    ) -> str:
        """Generate conversation summary"""
        summary_lines = [
            "=== WAR ROOM MVP (Two-Stage) - DELIBERATION SUMMARY ===",
            "",
            f"[Trader Agent - 35%] {trader_opinion.get('action', 'pass').upper()}",
            f"  Confidence: {trader_opinion.get('confidence', 0):.2f}",
            f"  Opportunity: {trader_opinion.get('opportunity_score', 0):.1f}/100",
            f"  Reasoning: {trader_opinion.get('reasoning', 'N/A')[:150]}...",
            f"  Stage: {trader_opinion.get('stage', 'unknown')}",
            "",
            f"[Risk Agent - 30%] {risk_opinion.get('recommendation', 'reject').upper()}",
            f"  Risk Level: {risk_opinion.get('risk_level', 'high')}",
            f"  Max Position: {(risk_opinion.get('max_position_pct', 0.05) * 100):.1f}%",
            f"  Stop Loss: {(risk_opinion.get('stop_loss_pct', 0.05) * 100):.1f}%",
            f"  Reasoning: {risk_opinion.get('reasoning', 'N/A')[:150]}...",
            f"  Stage: {risk_opinion.get('stage', 'unknown')}",
            "",
            f"[Analyst Agent - 35%] {analyst_opinion.get('action', 'pass').upper()}",
            f"  Confidence: {analyst_opinion.get('confidence', 0):.2f}",
            f"  Info Score: {analyst_opinion.get('overall_information_score', 0):.1f}/10",
            f"  Reasoning: {analyst_opinion.get('reasoning', 'N/A')[:150]}...",
            f"  Stage: {analyst_opinion.get('stage', 'unknown')}",
            "",
            f"[PM Agent] FINAL DECISION: {pm_decision['final_decision'].upper()}",
            f"  Confidence: {pm_decision['confidence']:.2f}",
            f"  Hard Rules: {'PASSED' if pm_decision['hard_rules_passed'] else 'FAILED'}",
        ]

        if validation_result:
            summary_lines.extend([
                "",
                f"[Validation] {validation_result['result'].upper()}",
                f"  Can Execute: {validation_result['can_execute']}",
            ])

        return "\n".join(summary_lines)

    def get_war_room_info(self) -> Dict[str, Any]:
        """Get War Room information"""
        current_mode = self.persona_router.get_current_mode()
        weights = self.persona_router.get_weights(current_mode.value)

        return {
            'name': 'WarRoomMVP',
            'version': '2.1.0 (Hybrid LLM)',
            'current_mode': current_mode.value,
            'architecture': 'two-stage-hybrid',
            'agent_structure': '3+1 Voting System (Hybrid LLM)',
            'llm_strategy': 'Hybrid - Risk: GLM, Trader/Analyst: Gemini',
            'agents': [
                {
                    'name': 'Trader Agent MVP',
                    'implementation': 'Two-Stage Gemini',
                    'llm_provider': 'Gemini 2.0 Flash',
                    'weight': weights.get('trader_mvp', 0.35),
                    'focus': 'Attack - Opportunities',
                    'benefits': ['High concurrency', 'Fast response', 'Cost-effective']
                },
                {
                    'name': 'Risk Agent MVP',
                    'implementation': 'Two-Stage GLM',
                    'llm_provider': 'GLM-4.7 + GLM-4.6V',
                    'weight': weights.get('risk_mvp', 0.30),
                    'focus': 'Defense - Risk Management + Position Sizing',
                    'benefits': ['Best accuracy', 'Reliable for critical decisions']
                },
                {
                    'name': 'Analyst Agent MVP',
                    'implementation': 'Two-Stage Gemini',
                    'llm_provider': 'Gemini 2.0 Flash',
                    'weight': weights.get('analyst_mvp', 0.35),
                    'focus': 'Information - News + Macro + Institutional',
                    'benefits': ['High concurrency', 'Fast response', 'Cost-effective']
                },
                {
                    'name': 'PM Agent MVP',
                    'weight': 'Final Decision',
                    'focus': 'Hard Rules + Silence Policy + Portfolio Management'
                }
            ],
            'execution_layer': {
                'router': 'Fast Track vs Deep Dive',
                'validator': 'Hard Rules Enforcement'
            },
            'decision_count': len(self.decision_history),
            'session_id': self.session_id,
            'hybrid_llm_benefits': {
                'glm_requests': 2,  # Risk Agent only
                'gemini_requests': 4,  # Trader + Analyst Agents
                'total_requests': 6,
                'concurrency_compliance': 'GLM: 2/3 (✅), Gemini: 4/60+ (✅)',
                'benefit': 'Solves GLM Concurrency Limit 3 while maintaining accuracy'
            }
        }

    async def close(self):
        """Close all agent sessions."""
        await self.trader_agent.close()
        await self.risk_agent.close()
        await self.analyst_agent.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Example usage
if __name__ == "__main__":
    async def test():
        # Initialize War Room
        war_room = WarRoomMVP()

        # Test data
        market_data = {
            'price_data': {
                'current_price': 150.25,
                'open': 148.50,
                'high': 151.00,
                'low': 147.80,
                'volume': 45000000
            },
            'technical_data': {
                'rsi': 62.5,
                'macd': {'value': 1.2, 'signal': 0.8},
                'moving_averages': {'ma50': 145.00, 'ma200': 140.00}
            },
            'market_conditions': {
                'vix': 18.5,
                'market_sentiment': 0.6
            }
        }

        portfolio_state = {
            'total_value': 100000,
            'available_cash': 50000,
            'current_positions': []
        }

        additional_data = {
            'news_articles': [
                {'title': 'Apple announces new product line', 'source': 'Reuters'}
            ],
            'macro_indicators': {
                'interest_rate': 5.25,
                'inflation_rate': 3.1
            }
        }

        # Run deliberation
        result = await war_room.deliberate(
            symbol='AAPL',
            action_context='new_position',
            market_data=market_data,
            portfolio_state=portfolio_state,
            additional_data=additional_data
        )

        print("\n=== FINAL RESULT ===")
        print(f"Decision: {result['final_decision']}")
        print(f"Architecture: {result['architecture']}")

    asyncio.run(test())
