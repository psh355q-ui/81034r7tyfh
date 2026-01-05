"""
War Room MVP - 3+1 Voting System

Phase: MVP Consolidation
Date: 2025-12-31

Purpose:
    MVP 전쟁실 - 3개 Agent + 1 PM의 협업 시스템
    - Trader Agent MVP (35% weight) - Attack
    - Risk Agent MVP (35% weight) - Defense
    - Analyst Agent MVP (30% weight) - Information
    - PM Agent MVP - Final Decision (Hard Rules + Silence Policy)

Voting System:
    1. 각 Agent는 가중치에 따라 투표
    2. Weighted average로 종합 의견 도출
    3. PM Agent가 최종 검증 및 결정
    4. Hard Rules 위반 시 즉시 거부

Legacy vs MVP:
    - Legacy: 8-9 agents (비용 높음, 속도 느림)
    - MVP: 3+1 agents (비용 절감, 속도 향상)
    - Agent 수 67% 감소 → 비용/시간 67% 감소 예상
"""

import os
from typing import Dict, Any, Optional, List
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# MVP Agents
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
    """MVP War Room - 3+1 Agent Voting System"""

    def __init__(self):
        """Initialize War Room MVP"""
        # Initialize 3 voting agents
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

    async def deliberate(
        self,
        symbol: str,
        action_context: str,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None,
        persona_mode: Optional[str] = None  # NEW: Dynamic persona mode
    ) -> Dict[str, Any]:
        """
        전쟁실 심의 - 3+1 Agent 협업 의사결정

        Args:
            symbol: 종목 심볼 (예: AAPL, NVDA)
            action_context: 액션 맥락 (예: "new_position", "stop_loss_check", "rebalancing")
            market_data: 시장 데이터
                {
                    'price_data': {...},
                    'technical_data': {...},
                    'market_conditions': {...}
                }
            portfolio_state: 포트폴리오 상태
                {
                    'total_value': float,
                    'available_cash': float,
                    'current_positions': [...],
                    'total_risk': float
                }
            additional_data: 추가 데이터 (optional)
                {
                    'news_articles': [...],
                    'macro_indicators': {...},
                    'chipwar_events': [...],
                    'correlation_data': {...}
                }

        Returns:
            Dict containing:
                - final_decision: approve/reject/reduce_size/silence
                - recommended_action: buy/sell/hold
                - confidence: 최종 confidence
                - position_size: 추천 포지션 크기
                - execution_mode: fast_track/deep_dive
                - agent_opinions: 각 Agent 의견
                - pm_decision: PM Agent 최종 결정
                - validation_result: Hard Rules 검증 결과
                - conversation_summary: 심의 요약
        """
        print(f"\n{'='*80}")
        print(f"WAR ROOM MVP - Deliberation Started")
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
        print(f"  → Reasoning: {routing_result['reasoning']}")
        print(f"  → Estimated Time: {routing_result['estimated_processing_time']}s\n")

        # Fast Track: Skip AI, use rule-based execution
        if routing_result['bypass_ai']:
            print("[FAST TRACK] Bypassing AI - Rule-based execution\n")
            # Fast Track logic (향후 구현)
            return {
                'final_decision': 'fast_track_executed',
                'execution_mode': execution_mode,
                'routing_result': routing_result,
                'timestamp': datetime.utcnow().isoformat()
            }

        # ================================================================
        # STEP 2: AGENT DELIBERATION (3 Agents - Parallelized)
        # ================================================================
        print("[STEP 2] Agent Deliberation (3 Agents - Parallelized)...\n")
        
        loop = asyncio.get_running_loop()
        
        # 1. Start Trader and Analyst in parallel
        print("  [Parallel] Starting Trader & Analyst Agents...")
        trader_task = loop.run_in_executor(
            None, 
            self.trader_agent.analyze,
            symbol,
            market_data.get('price_data', {}),
            market_data.get('technical_data'),
            additional_data.get('chipwar_events') if additional_data else None,
            market_data.get('market_conditions')
        )
        
        # Analyst Agent is now async (uses News Agent)
        analyst_task = asyncio.create_task(
            self.analyst_agent.analyze(
                symbol,
                additional_data.get('news_articles') if additional_data else None,
                additional_data.get('macro_indicators') if additional_data else None,
                additional_data.get('institutional_data') if additional_data else None,
                additional_data.get('chipwar_events') if additional_data else None,
                market_data.get('price_data')
            )
        )
        
        # 2. Wait for Trader Agent (Dependencies: Risk Agent needs Trader Opinion)
        trader_opinion = await trader_task
        print(f"  [Trader Agent] Action: {trader_opinion['action']} (Confidence: {trader_opinion['confidence']:.2f})")
        
        # 3. Start Risk Agent (Depends on Trader)
        print("  [Risk Agent] Starting Risk Agent (using Trader opinion)...")
        risk_task = loop.run_in_executor(
            None,
            self.risk_agent.analyze,
            symbol,
            market_data.get('price_data', {}),
            trader_opinion,
            market_data.get('market_conditions'),
            additional_data.get('dividend_info') if additional_data else None,
            portfolio_state
        )
        
        # 4. Wait for remaining tasks
        risk_opinion = await risk_task
        analyst_opinion = await analyst_task
        
        print(f"  [Risk Agent] Recommendation: {risk_opinion['recommendation']} (Level: {risk_opinion['risk_level']})")
        print(f"  [Analyst Agent] Action: {analyst_opinion['action']} (Info Score: {analyst_opinion['overall_score']:.1f})")

        # ================================================================
        # STEP 2.5: INJECT DYNAMIC WEIGHTS FROM PERSONA ROUTER
        # ================================================================
        weights = self.persona_router.get_weights(persona_mode)
        persona_config = self.persona_router.get_config(persona_mode)
        
        # Inject weights into each agent's opinion
        trader_opinion['weight'] = weights.get('trader_mvp', 0.35)
        risk_opinion['weight'] = weights.get('risk_mvp', 0.35)
        analyst_opinion['weight'] = weights.get('analyst_mvp', 0.30)
        
        print(f"\n  [Persona Mode] {persona_config.mode.value.upper()}")
        print(f"  [Dynamic Weights] Trader={weights['trader_mvp']:.0%}, Risk={weights['risk_mvp']:.0%}, Analyst={weights['analyst_mvp']:.0%}")

        # ================================================================
        # STEP 3: PM FINAL DECISION (Hard Rules + Silence Policy)
        # ================================================================
        print("[STEP 3] PM Final Decision (Hard Rules + Silence Policy)...\n")

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
        print(f"  → Reasoning: {pm_decision['reasoning']}\n")

        # ================================================================
        # STEP 4: ORDER VALIDATION (if approved)
        # ================================================================
        validation_result = None
        if pm_decision['final_decision'] == 'approve':
            print("[STEP 4] Order Validation (Hard Rules)...\n")

            # Construct order from decisions
            order = {
                'symbol': symbol,
                'action': pm_decision['recommended_action'],
                'quantity': int(risk_opinion.get('position_size_usd', 0) / market_data['price_data'].get('current_price', 1)),
                'price': market_data['price_data'].get('current_price', 0),
                'order_value': risk_opinion.get('position_size_usd', 0),
                'position_size_pct': risk_opinion.get('position_size_pct', 0),
                'stop_loss_pct': risk_opinion.get('stop_loss_pct', 0.02),
                'timestamp': datetime.utcnow().isoformat()
            }

            validation_result = self.order_validator.validate(
                order=order,
                portfolio_state=portfolio_state,
                market_state=market_data.get('market_conditions')
            )

            print(f"  → Validation Result: {validation_result['result']}")
            print(f"  → Can Execute: {validation_result['can_execute']}")
            if validation_result.get('violations'):
                print(f"  → Violations: {validation_result['violations']}")
            if validation_result.get('warnings'):
                print(f"  → Warnings: {validation_result['warnings']}\n")

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
            'position_size_usd': risk_opinion.get('position_size_usd', 0),
            'position_size_shares': risk_opinion.get('position_size_shares', 0),
            'stop_loss_pct': risk_opinion.get('stop_loss_pct', 0),
            'conversation_summary': conversation_summary,
            'can_execute': validation_result['can_execute'] if validation_result else False,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Record in history
        self.decision_history.append(final_result)

        print(f"\n{'='*80}")
        print(f"WAR ROOM MVP - Deliberation Completed")
        print(f"Final Decision: {final_result['final_decision']}")
        print(f"Can Execute: {final_result['can_execute']}")
        print(f"{'='*80}\n")

        return final_result

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
            "=== WAR ROOM MVP - DELIBERATION SUMMARY ===",
            "",
            f"[Trader Agent - 35%] {trader_opinion['action'].upper()}",
            f"  Confidence: {trader_opinion['confidence']:.2f}",
            f"  Opportunity: {trader_opinion.get('opportunity_score', 0):.1f}/10",
            f"  Reasoning: {trader_opinion['reasoning'][:150]}...",
            "",
            f"[Risk Agent - 35%] {risk_opinion['recommendation'].upper()}",
            f"  Risk Level: {risk_opinion['risk_level']}",
            f"  Position Size: ${risk_opinion.get('position_size_usd', 0):,.0f} ({(risk_opinion.get('position_size_pct', 0) * 100):.1f}%)",
            f"  Stop Loss: {(risk_opinion['stop_loss_pct'] * 100):.1f}%",
            f"  Reasoning: {risk_opinion['reasoning'][:150]}...",
            "",
            f"[Analyst Agent - 30%] {analyst_opinion['action'].upper()}",
            f"  Confidence: {analyst_opinion['confidence']:.2f}",
            f"  Info Score: {analyst_opinion['overall_score']:.1f}/10",
            f"  Red Flags: {', '.join(analyst_opinion['red_flags']) if analyst_opinion['red_flags'] else 'None'}",
            "",
            f"[PM Agent] FINAL DECISION: {pm_decision['final_decision'].upper()}",
            f"  Confidence: {pm_decision['confidence']:.2f}",
            f"  Hard Rules: {'PASSED' if pm_decision['hard_rules_passed'] else 'FAILED'}",
            f"  Reasoning: {pm_decision['reasoning'][:150]}...",
        ]

        if validation_result:
            summary_lines.extend([
                "",
                f"[Validation] {validation_result['result'].upper()}",
                f"  Can Execute: {validation_result['can_execute']}",
            ])
            if validation_result.get('violations'):
                summary_lines.append(f"  Violations: {', '.join(validation_result['violations'])}")

        return "\n".join(summary_lines)

    def get_war_room_info(self) -> Dict[str, Any]:
        """Get War Room information"""
        return {
            'name': 'WarRoomMVP',
            'version': '1.0.0',
            'agent_structure': '3+1 Voting System',
            'agents': [
                {
                    'name': 'Trader Agent MVP',
                    'weight': 0.35,
                    'focus': 'Attack - Opportunities'
                },
                {
                    'name': 'Risk Agent MVP',
                    'weight': 0.35,
                    'focus': 'Defense - Risk Management + Position Sizing'
                },
                {
                    'name': 'Analyst Agent MVP',
                    'weight': 0.30,
                    'focus': 'Information - News + Macro + Institutional + ChipWar'
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
            'improvement_vs_legacy': {
                'agent_count_reduction': '67% (9 → 3+1)',
                'expected_cost_reduction': '~67%',
                'expected_speed_improvement': '~67%'
            }
        }


# Example usage
if __name__ == "__main__":
    # Initialize War Room
    war_room = WarRoomMVP()

    # Test data
    market_data = {
        'price_data': {
            'current_price': 150.25,
            'open': 148.50,
            'high': 151.00,
            'low': 147.80,
            'volume': 45000000,
            'high_52w': 180.00,
            'low_52w': 120.00,
            'volatility': 0.25
        },
        'technical_data': {
            'rsi': 62.5,
            'macd': {'value': 1.2, 'signal': 0.8},
            'moving_averages': {'ma50': 145.00, 'ma200': 140.00}
        },
        'market_conditions': {
            'vix': 18.5,
            'market_sentiment': 0.6,
            'is_market_open': True
        }
    }

    portfolio_state = {
        'total_value': 100000,
        'available_cash': 50000,
        'current_positions': [],
        'total_risk': 0.02,
        'position_count': 3
    }

    additional_data = {
        'news_articles': [
            {
                'title': 'Apple announces new product line',
                'source': 'Reuters',
                'published': '2025-12-30',
                'summary': 'New iPhone features AI capabilities'
            }
        ],
        'macro_indicators': {
            'interest_rate': 5.25,
            'inflation_rate': 3.1,
            'gdp_growth': 2.5,
            'fed_policy': 'hawkish'
        }
    }

    # Run deliberation
    result = war_room.deliberate(
        symbol='AAPL',
        action_context='new_position',
        market_data=market_data,
        portfolio_state=portfolio_state,
        additional_data=additional_data
    )

    print("\n=== FINAL RESULT ===")
    print(f"Decision: {result['final_decision']}")
    print(f"Action: {result['recommended_action']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Position Size: ${result['position_size_usd']:,.0f} ({result.get('position_size_shares', 0)} shares)")
    print(f"Can Execute: {result['can_execute']}")

    print("\n=== WAR ROOM INFO ===")
    info = war_room.get_war_room_info()
    print(f"Version: {info['version']}")
    print(f"Structure: {info['agent_structure']}")
    print(f"Cost Reduction: {info['improvement_vs_legacy']['expected_cost_reduction']}")
