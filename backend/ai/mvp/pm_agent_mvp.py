"""
PM Agent MVP - Final Decision Maker

Phase: MVP Consolidation
Date: 2025-12-31

Purpose:
    포트폴리오 매니저 - 최종 의사결정자
    - Hard Rules 검증 (코드 기반, AI 해석 금지)
    - Silence Policy 실행 (판단 거부 권한)
    - 3개 Agent 의견 통합 및 최종 결정
    - 포트폴리오 수준 리스크 관리

Key Responsibilities:
    1. Hard Rules 검증 (code-enforced, not AI)
    2. Silence Policy (confidence < threshold → reject)
    3. 3개 Agent 의견 가중 평균 및 최종 결정
    4. 포트폴리오 수준 리스크 체크 (집중도, 상관관계)
    5. 최종 거부권 행사 (extreme risk, low confidence)

Hard Rules (Code-Enforced):
    1. Position Size > 30% → REJECT
    2. Total Portfolio Risk > 5% → REJECT
    3. Agent Disagreement > 60% → REJECT or REDUCE
    4. Average Confidence < 50% → REJECT (Silence Policy)
    5. Stop Loss not set → REJECT
    6. Risk Level = "extreme" → REJECT
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import google.generativeai as genai

# Configure logger
logger = logging.getLogger(__name__)


class PMAgentMVP:
    """MVP PM Agent - 최종 의사결정자 + Hard Rules + Silence Policy"""

    def __init__(self):
        """Initialize PM Agent MVP"""
        # Gemini API 설정
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Agent configuration
        self.role = "포트폴리오 매니저"

        # ===================================================================
        # HARD RULES (Code-Enforced, NOT AI-interpreted)
        # Updated: 2025-12-31 - Relaxed max_agent_disagreement for Phase 1
        # ===================================================================
        self.HARD_RULES = {
            'max_position_size': 0.30,  # 30% 포지션 절대 상한
            'max_portfolio_risk': 0.05,  # 5% 포트폴리오 전체 리스크 상한
            'min_avg_confidence': 0.50,  # 50% 평균 confidence 하한 (Silence Policy)
            'max_agent_disagreement': 0.75,  # 75% 의견 불일치 상한 (Phase 1 완화: 60% → 75%)
            'stop_loss_required': True,  # Stop Loss 필수
            'reject_extreme_risk': True,  # Risk Level "extreme" 시 거부
            'max_correlated_positions': 3,  # 높은 상관관계 포지션 최대 3개
            'max_sector_concentration': 0.40  # 40% 섹터 집중도 상한
        }
        # 🔍 DEBUG: PM Agent 인스턴스 생성 시점 확인
        logger.info(f"🔍 INIT DEBUG: PMAgentMVP created, max_agent_disagreement={self.HARD_RULES['max_agent_disagreement']}, instance_id={id(self)}, HARD_RULES_id={id(self.HARD_RULES)}")

        # Silence Policy threshold
        self.SILENCE_THRESHOLD = 0.50  # Confidence < 50% → 판단 거부

        # System prompt
        self.system_prompt = """당신은 포트폴리오 매니저입니다.

역할:
1. 3개 Agent 의견을 종합하여 최종 결정
2. 포트폴리오 수준 리스크 평가
3. 의견 불일치 시 조정 및 중재
4. 최종 거부권 행사 (필요 시)

분석 원칙:
- Hard Rules는 코드가 검증 (당신은 판단만)
- Confidence가 낮으면 거부 권장
- Agent 간 의견 차이가 크면 신중 모드
- 포트폴리오 전체 관점에서 평가

출력 형식:
{
    "final_decision": "approve" | "reject" | "reduce_size" | "silence",
    "confidence": 0.0 ~ 1.0,
    "reasoning": "최종 결정 근거",
    "recommended_action": "buy" | "sell" | "hold",
    "position_size_adjustment": 0.0 ~ 1.0 (1.0 = full size, 0.5 = half),
    "risk_assessment": {
        "portfolio_risk_score": 0.0 ~ 10.0,
        "concentration_risk": 0.0 ~ 10.0,
        "correlation_risk": 0.0 ~ 10.0,
        "overall_portfolio_health": 0.0 ~ 10.0
    },
    "agent_consensus": {
        "agreement_level": 0.0 ~ 1.0,
        "conflicting_opinions": ["agent1 vs agent2 on X"],
        "resolution": "how conflicts were resolved"
    },
    "warnings": ["warning1", "warning2", ...],
    "approval_conditions": ["condition1", "condition2", ...] or []
}

중요:
- final_decision = "silence"는 판단 거부 (정보 불충분)
- Agent 의견이 상충하면 보수적으로 결정
- 포트폴리오 전체 건강도 우선 고려
- **반드시 한글로 응답할 것** (reasoning, warnings, approval_conditions 등 모든 텍스트 필드는 한국어로 작성)
"""

    def make_final_decision(
        self,
        symbol: str,
        trader_opinion: Dict[str, Any],
        risk_opinion: Dict[str, Any],
        analyst_opinion: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        correlation_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        최종 의사결정 수행

        Args:
            symbol: 종목 심볼
            trader_opinion: Trader Agent MVP 의견
                {
                    'action': str,
                    'confidence': float,
                    'opportunity_score': float,
                    'weight': 0.35
                }
            risk_opinion: Risk Agent MVP 의견
                {
                    'risk_level': str,
                    'confidence': float,
                    'recommendation': str,
                    'position_size_usd': float,
                    'stop_loss_pct': float,
                    'weight': 0.35
                }
            analyst_opinion: Analyst Agent MVP 의견
                {
                    'action': str,
                    'confidence': float,
                    'overall_information_score': float,
                    'red_flags': list,
                    'weight': 0.30
                }
            portfolio_state: 포트폴리오 현재 상태
                {
                    'total_value': float,
                    'current_positions': [{'symbol': str, 'value': float, 'sector': str}],
                    'available_cash': float,
                    'total_risk': float
                }
            correlation_data: 상관관계 데이터 (optional)
                {
                    'correlated_positions': [{'symbol': str, 'correlation': float}]
                }

        Returns:
            Dict containing:
                - final_decision: approve/reject/reduce_size/silence
                - confidence: 최종 confidence
                - reasoning: 결정 근거
                - recommended_action: buy/sell/hold
                - position_size_adjustment: 포지션 조정 배율
                - risk_assessment: 리스크 평가
                - agent_consensus: Agent 합의 분석
                - warnings: 경고 사항
                - hard_rules_passed: Hard Rules 통과 여부
                - hard_rules_violations: Hard Rules 위반 내역
        """
        # ================================================================
        # STEP 1: HARD RULES VALIDATION (Code-Enforced)
        # ================================================================
        hard_rules_result = self._validate_hard_rules(
            symbol=symbol,
            trader_opinion=trader_opinion,
            risk_opinion=risk_opinion,
            analyst_opinion=analyst_opinion,
            portfolio_state=portfolio_state,
            correlation_data=correlation_data
        )

        # Hard Rules 위반 시 즉시 거부
        if not hard_rules_result['passed']:
            return {
                'agent': 'pm_mvp',
                'final_decision': 'reject',
                'confidence': 0.0,
                'reasoning': f"Hard Rules 위반: {', '.join(hard_rules_result['violations'])}",
                'recommended_action': 'hold',
                'position_size_adjustment': 0.0,
                'risk_assessment': {
                    'portfolio_risk_score': 10.0,
                    'concentration_risk': 10.0,
                    'correlation_risk': 10.0,
                    'overall_portfolio_health': 0.0
                },
                'agent_consensus': {
                    'agreement_level': 0.0,
                    'conflicting_opinions': [],
                    'resolution': 'Rejected by Hard Rules'
                },
                'warnings': hard_rules_result['violations'],
                'hard_rules_passed': False,
                'hard_rules_violations': hard_rules_result['violations'],
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol
            }

        # ================================================================
        # STEP 2: SILENCE POLICY CHECK
        # ================================================================
        avg_confidence = (
            trader_opinion['confidence'] * trader_opinion['weight'] +
            risk_opinion['confidence'] * risk_opinion['weight'] +
            analyst_opinion['confidence'] * analyst_opinion['weight']
        )

        # Silence Policy: 평균 confidence < threshold → 판단 거부
        if avg_confidence < self.SILENCE_THRESHOLD:
            return {
                'agent': 'pm_mvp',
                'final_decision': 'silence',
                'confidence': avg_confidence,
                'reasoning': f"Silence Policy: Average confidence ({avg_confidence:.2f}) below threshold ({self.SILENCE_THRESHOLD})",
                'recommended_action': 'hold',
                'position_size_adjustment': 0.0,
                'risk_assessment': {
                    'portfolio_risk_score': 5.0,
                    'concentration_risk': 5.0,
                    'correlation_risk': 5.0,
                    'overall_portfolio_health': 5.0
                },
                'agent_consensus': {
                    'agreement_level': 0.0,
                    'conflicting_opinions': [],
                    'resolution': 'Silence - insufficient confidence'
                },
                'warnings': ['Insufficient confidence for decision'],
                'hard_rules_passed': True,
                'hard_rules_violations': [],
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol
            }

        # ================================================================
        # STEP 3: AI-BASED FINAL DECISION
        # ================================================================
        # Construct prompt for PM Agent
        prompt = self._build_prompt(
            symbol=symbol,
            trader_opinion=trader_opinion,
            risk_opinion=risk_opinion,
            analyst_opinion=analyst_opinion,
            portfolio_state=portfolio_state,
            correlation_data=correlation_data,
            avg_confidence=avg_confidence
        )

        # Call Gemini API
        try:
            response = self.model.generate_content([
                self.system_prompt,
                prompt
            ])

            # Parse response
            result = self._parse_response(response.text)

            # Add metadata and hard rules info
            result['agent'] = 'pm_mvp'
            result['hard_rules_passed'] = True
            result['hard_rules_violations'] = []
            result['timestamp'] = datetime.utcnow().isoformat()
            result['symbol'] = symbol
            result['avg_agent_confidence'] = avg_confidence

            return result

        except Exception as e:
            # Error handling - return safe default (reject)
            return {
                'agent': 'pm_mvp',
                'final_decision': 'reject',
                'confidence': 0.0,
                'reasoning': f'PM analysis failed: {str(e)}',
                'recommended_action': 'hold',
                'position_size_adjustment': 0.0,
                'risk_assessment': {
                    'portfolio_risk_score': 10.0,
                    'concentration_risk': 10.0,
                    'correlation_risk': 10.0,
                    'overall_portfolio_health': 0.0
                },
                'agent_consensus': {
                    'agreement_level': 0.0,
                    'conflicting_opinions': [],
                    'resolution': 'Error - rejected for safety'
                },
                'warnings': [f'PM Agent error: {str(e)}'],
                'hard_rules_passed': True,
                'hard_rules_violations': [],
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'error': str(e)
            }

    def _validate_hard_rules(
        self,
        symbol: str,
        trader_opinion: Dict[str, Any],
        risk_opinion: Dict[str, Any],
        analyst_opinion: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        correlation_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Hard Rules 검증 (Code-Enforced)

        Returns:
            {
                'passed': bool,
                'violations': List[str]
            }
        """
        violations = []

        # Rule 1: Position Size > 30%
        position_size_pct = risk_opinion.get('position_size_pct', 0.0)
        if position_size_pct > self.HARD_RULES['max_position_size']:
            violations.append(
                f"포지션 크기 {position_size_pct*100:.1f}%가 최대 허용치 {self.HARD_RULES['max_position_size']*100}%를 초과합니다"
            )

        # Rule 2: Total Portfolio Risk > 5%
        total_risk = portfolio_state.get('total_risk', 0.0)
        if total_risk > self.HARD_RULES['max_portfolio_risk']:
            violations.append(
                f"포트폴리오 리스크 {total_risk*100:.1f}%가 최대 허용치 {self.HARD_RULES['max_portfolio_risk']*100:.1f}%를 초과합니다"
            )

        # Rule 3: Agent Disagreement > 75% (Phase 1 완화)
        actions = [
            trader_opinion.get('action', 'pass'),
            risk_opinion.get('recommendation', 'reject'),
            analyst_opinion.get('action', 'pass')
        ]
        # Count unique actions (excluding 'pass')
        non_pass_actions = [a for a in actions if a != 'pass']
        if len(non_pass_actions) > 0:
            disagreement = 1.0 - (non_pass_actions.count(non_pass_actions[0]) / len(non_pass_actions))
            # 🔍 DEBUG: 실제 validation 시점의 HARD_RULES 값 확인
            logger.warning(f"🔍 VALIDATION DEBUG: disagreement={disagreement:.2f}, max_allowed={self.HARD_RULES['max_agent_disagreement']}, HARD_RULES_id={id(self.HARD_RULES)}, actions={actions}, non_pass={non_pass_actions}")
            if disagreement > self.HARD_RULES['max_agent_disagreement']:
                violations.append(
                    f"Agent 의견 불일치 {disagreement*100:.0f}%가 최대 허용치 {self.HARD_RULES['max_agent_disagreement']*100:.0f}%를 초과합니다"
                )

        # Rule 4: Average Confidence < 50% (handled by Silence Policy, but double-check)
        confidences = [
            trader_opinion.get('confidence', 0.0),
            risk_opinion.get('confidence', 0.0),
            analyst_opinion.get('confidence', 0.0)
        ]
        avg_conf = sum(confidences) / len(confidences)
        if avg_conf < self.HARD_RULES['min_avg_confidence']:
            violations.append(
                f"평균 신뢰도 {avg_conf*100:.0f}%가 최소 요구치 {self.HARD_RULES['min_avg_confidence']*100:.0f}% 미만입니다"
            )

        # Rule 5: Stop Loss Required
        if self.HARD_RULES['stop_loss_required']:
            stop_loss = risk_opinion.get('stop_loss_pct', 0.0)
            if stop_loss <= 0.0 or stop_loss > 0.10:  # Must be 0.1% ~ 10%
                violations.append(
                    f"손절매 {stop_loss*100:.2f}%가 유효하지 않습니다 (0.1% ~ 10% 범위여야 함)"
                )

        # Rule 6: Risk Level "extreme" → Reject
        if self.HARD_RULES['reject_extreme_risk']:
            risk_level = risk_opinion.get('risk_level', 'medium')
            if risk_level == 'extreme':
                violations.append(
                    "리스크 수준이 'extreme'으로 자동 거부됩니다"
                )

        # Rule 7: Correlated Positions > 3
        if correlation_data:
            correlated_positions = correlation_data.get('correlated_positions', [])
            high_corr_count = len([p for p in correlated_positions if p.get('correlation', 0) > 0.7])
            if high_corr_count >= self.HARD_RULES['max_correlated_positions']:
                violations.append(
                    f"상관관계가 높은 포지션이 너무 많습니다 ({high_corr_count}개) - 최대 {self.HARD_RULES['max_correlated_positions']}개"
                )

        # Rule 8: Sector Concentration > 40%
        current_positions = portfolio_state.get('current_positions', [])
        total_value = portfolio_state.get('total_value', 1)
        if current_positions:
            # Calculate sector concentration
            sector_values = {}
            for pos in current_positions:
                sector = pos.get('sector', 'Unknown')
                value = pos.get('value', 0)
                sector_values[sector] = sector_values.get(sector, 0) + value

            max_sector_pct = max(sector_values.values()) / total_value if total_value > 0 else 0
            if max_sector_pct > self.HARD_RULES['max_sector_concentration']:
                violations.append(
                    f"섹터 집중도 {max_sector_pct*100:.1f}%가 최대 허용치 {self.HARD_RULES['max_sector_concentration']*100:.1f}%를 초과합니다"
                )

        return {
            'passed': len(violations) == 0,
            'violations': violations
        }

    def _build_prompt(
        self,
        symbol: str,
        trader_opinion: Dict[str, Any],
        risk_opinion: Dict[str, Any],
        analyst_opinion: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        correlation_data: Optional[Dict[str, Any]],
        avg_confidence: float
    ) -> str:
        """Build PM decision prompt"""
        prompt_parts = [
            f"종목: {symbol}",
            f"평균 Confidence: {avg_confidence:.2f}",
            "",
            "=== Trader Agent (35% weight) ===",
            f"Action: {trader_opinion.get('action', 'N/A')}",
            f"Confidence: {trader_opinion.get('confidence', 0):.2f}",
            f"Opportunity Score: {trader_opinion.get('opportunity_score', 0):.1f}",
            f"Reasoning: {trader_opinion.get('reasoning', 'N/A')}",
            "",
            "=== Risk Agent (35% weight) ===",
            f"Risk Level: {risk_opinion.get('risk_level', 'N/A')}",
            f"Confidence: {risk_opinion.get('confidence', 0):.2f}",
            f"Recommendation: {risk_opinion.get('recommendation', 'N/A')}",
            f"Position Size: ${risk_opinion.get('position_size_usd', 0):,.0f} ({(risk_opinion.get('position_size_pct', 0) * 100):.1f}%)",
            f"Stop Loss: {(risk_opinion.get('stop_loss_pct', 0) * 100):.1f}%",
            f"Reasoning: {risk_opinion.get('reasoning', 'N/A')}",
            "",
            "=== Analyst Agent (30% weight) ===",
            f"Action: {analyst_opinion.get('action', 'N/A')}",
            f"Confidence: {analyst_opinion.get('confidence', 0):.2f}",
            f"Info Score: {analyst_opinion.get('overall_information_score', 0):.1f}",
            f"Red Flags: {', '.join(analyst_opinion.get('red_flags', [])) or 'None'}",
            f"Reasoning: {analyst_opinion.get('reasoning', 'N/A')}",
            "",
            "=== Portfolio State ===",
            f"Total Value: ${portfolio_state.get('total_value', 0):,.0f}",
            f"Available Cash: ${portfolio_state.get('available_cash', 0):,.0f}",
            f"Current Positions: {len(portfolio_state.get('current_positions', []))}",
            f"Total Risk: {(portfolio_state.get('total_risk', 0) * 100):.1f}%",
        ]

        if correlation_data:
            prompt_parts.append("\n=== Correlation Data ===")
            corr_positions = correlation_data.get('correlated_positions', [])
            if corr_positions:
                prompt_parts.append("Highly Correlated Positions:")
                for pos in corr_positions[:3]:
                    prompt_parts.append(f"  - {pos.get('symbol', 'N/A')}: {pos.get('correlation', 0):.2f}")

        prompt_parts.append("\n위 정보를 종합하여 최종 결정을 내리고 JSON 형식으로 답변하세요.")

        return "\n".join(prompt_parts)

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response"""
        import json
        import re

        # Extract JSON
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
                    raise ValueError("No valid JSON found")

        # Provide defaults
        result.setdefault('final_decision', 'reject')
        result.setdefault('confidence', 0.5)
        result.setdefault('reasoning', 'No reasoning provided')
        result.setdefault('recommended_action', 'hold')
        result.setdefault('position_size_adjustment', 1.0)
        result.setdefault('warnings', [])
        result.setdefault('approval_conditions', [])

        if 'risk_assessment' not in result:
            result['risk_assessment'] = {}
        risk_assess = result['risk_assessment']
        risk_assess.setdefault('portfolio_risk_score', 5.0)
        risk_assess.setdefault('concentration_risk', 5.0)
        risk_assess.setdefault('correlation_risk', 5.0)
        risk_assess.setdefault('overall_portfolio_health', 5.0)

        if 'agent_consensus' not in result:
            result['agent_consensus'] = {}
        consensus = result['agent_consensus']
        consensus.setdefault('agreement_level', 0.5)
        consensus.setdefault('conflicting_opinions', [])
        consensus.setdefault('resolution', 'N/A')

        # Validate values
        valid_decisions = ['approve', 'reject', 'reduce_size', 'silence']
        if result['final_decision'] not in valid_decisions:
            result['final_decision'] = 'reject'

        valid_actions = ['buy', 'sell', 'hold']
        if result['recommended_action'] not in valid_actions:
            result['recommended_action'] = 'hold'

        result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
        result['position_size_adjustment'] = max(0.0, min(1.0, float(result['position_size_adjustment'])))

        return result

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'name': 'PMAgentMVP',
            'role': self.role,
            'focus': '최종 의사결정 + Hard Rules + Silence Policy',
            'responsibilities': [
                'Hard Rules 검증 (code-enforced)',
                'Silence Policy 실행',
                '3개 Agent 의견 통합',
                '포트폴리오 수준 리스크 관리',
                '최종 거부권 행사'
            ],
            'hard_rules': self.HARD_RULES,
            'silence_threshold': self.SILENCE_THRESHOLD
        }


# Example usage
if __name__ == "__main__":
    pm = PMAgentMVP()

    # Test data
    trader_op = {
        'action': 'buy',
        'confidence': 0.75,
        'opportunity_score': 7.5,
        'reasoning': 'Strong momentum',
        'weight': 0.35
    }

    risk_op = {
        'risk_level': 'medium',
        'confidence': 0.65,
        'recommendation': 'approve',
        'position_size_usd': 5000,
        'position_size_pct': 0.05,
        'stop_loss_pct': 0.02,
        'reasoning': 'Acceptable risk',
        'weight': 0.35
    }

    analyst_op = {
        'action': 'buy',
        'confidence': 0.70,
        'overall_information_score': 6.0,
        'red_flags': [],
        'reasoning': 'Positive catalysts',
        'weight': 0.30
    }

    portfolio = {
        'total_value': 100000,
        'available_cash': 50000,
        'current_positions': [],
        'total_risk': 0.02
    }

    result = pm.make_final_decision(
        symbol='AAPL',
        trader_opinion=trader_op,
        risk_opinion=risk_op,
        analyst_opinion=analyst_op,
        portfolio_state=portfolio
    )

    print(f"Final Decision: {result['final_decision']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Recommended Action: {result['recommended_action']}")
    print(f"Hard Rules Passed: {result['hard_rules_passed']}")
    print(f"Warnings: {result['warnings']}")
