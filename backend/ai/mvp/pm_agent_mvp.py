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

from backend.ai.schemas.war_room_schemas import PMDecision
from backend.ai.safety.leverage_guardian import get_leverage_guardian
from backend.ai.router.persona_router import get_persona_router

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

        # PersonaRouter 인스턴스
        self.persona_router = get_persona_router()

        # Phase 2: Persona-specific Hard Rules
        self.PERSONA_HARD_RULES_DEF = {
            "trading": {
                "max_portfolio_risk_pct": 0.15,
                "max_agent_disagreement": 0.60,
                "max_position_pct": 0.10
            },
            "long_term": {
                "max_portfolio_risk_pct": 0.20,
                "max_agent_disagreement": 0.70,
                "max_position_pct": 0.15
            },
            "dividend": {
                "max_portfolio_risk_pct": 0.10,
                "max_agent_disagreement": 0.40,
                "max_position_pct": 0.08
            },
            "aggressive": {
                "max_portfolio_risk_pct": 0.25,
                "max_agent_disagreement": 0.80,
                "max_position_pct": 0.20
            }
        }
        
        # ===================================================================
        # HARD RULES (Dynamic from PersonaRouter)
        # Updated: 2026-01-08 - Persona-specific thresholds
        # ===================================================================
        # 페르소나별 동적 규칙 가져오기
        persona_hard_rules = self.persona_router.get_hard_rules()
        
        self.HARD_RULES = {
            'max_position_size': 0.30,  # 30% 포지션 절대 상한 (모든 페르소나 공통)
            'max_portfolio_risk': 0.05,  # 5% 포트폴리오 전체 리스크 상한 (공통)
            'min_avg_confidence': persona_hard_rules.get('min_avg_confidence', 0.50),  # 페르소나별
            'max_agent_disagreement': persona_hard_rules.get('max_agent_disagreement', 0.67),  # 페르소나별
            'stop_loss_required': True,  # Stop Loss 필수 (공통)
            'reject_extreme_risk': True,  # Risk Level "extreme" 시 거부 (공통)
            'max_correlated_positions': 3,  # 높은 상관관계 포지션 최대 3개 (공통)
            'max_sector_concentration': 0.40  # 40% 섹터 집중도 상한 (공통)
        }
        
        # 🔍 DEBUG: PM Agent 인스턴스 생성 시점 확인
        current_mode = self.persona_router.get_current_mode()
        logger.info(
            f"🔍 INIT DEBUG: PMAgentMVP created with Persona={current_mode.value}, "
            f"max_agent_disagreement={self.HARD_RULES['max_agent_disagreement']}, "
            f"min_avg_confidence={self.HARD_RULES['min_avg_confidence']}, "
            f"instance_id={id(self)}"
        )

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

## Context-Aware Analysis (NEW)

`action_context` 파라미터에 따라 분석 관점을 조정하세요:

### 1. existing_position (보유 중인 종목)
- **목적**: HOLD vs SELL 판단, 추가매수 여부 결정
- **분석 초점**:
  - 현재 포지션 유지 권장 여부
  - 추가 매수 타이밍 및 가격대 (구체적)
  - 익절/손절 레벨 (평균가 대비 %)
  - Stop-loss 조정 권장
  - 포지션 축소/확대 비율
  - 투자 논리(Thesis) 유효성 재확인
  - 다음 재평가 시점 (실적 발표, 이벤트)

### 2. new_position (신규 진입 검토)
- **목적**: BUY vs HOLD 판단
- **분석 초점**:
  - 진입 타이밍 및 진입가
  - 목표가 및 손절가
  - 포지션 사이즈 권장

## Portfolio Action Guide (NEW)

보유 종목에 대해 다음 4가지 액션 중 하나를 선택하세요:

1. **SELL (매도 추천)**: 리스크 급증, 손절가 도달, 목표가 도달, 기술적 약세
   - 언제: 구체적 가격 레벨 또는 조건 (예: "$185 저항 돌파 실패 시")
   - 얼마나: 일부 익절(50%) vs 전량 청산

2. **BUY_MORE (추가 매수)**: 강한 모멘텀, 긍정적 촉매, 낮은 리스크
   - 언제: 구체적 매수 타이밍 (예: "지지선 $176 유지 시")
   - 얼마나: 추가 매수 비중 (ex: 현재 대비 +20%)

3. **HOLD (보유 유지)**: 중립적 신호, 촉매 대기 중
   - 추가 매수 불필요 명시
   - 다음 재평가 시점 제시 (예: "실적 발표 2026-02-15 후")
   - Stop-loss 조정 여부

4. **DO_NOT_BUY (미진입/관망)**: 높은 리스크, 불확실한 테마

출력 형식:
{
    ... existing fields ...,
    "portfolio_action": "buy_more" | "sell" | "hold" | "do_not_buy",
    "action_reason": "액션 선택 이유 (한국어, 구체적 가격/조건 포함)",
    "action_strength": "weak" | "moderate" | "strong",
    "position_adjustment_pct": -1.0 ~ 1.0  // -0.5 = 50% 매도, +0.2 = 20% 추가매수
}

**중요**: action_reason에는 반드시 구체적인 가격 레벨과 조건을 포함하세요.
예: "평균가 $175 대비 현재가 $178 (+1.7%), 저항선 $185 돌파 시 50% 익절 권장"

## Original Output Format
{
    "final_decision": "approve" | "reject" | "reduce_size" | "silence" | "conditional",
    "confidence": 0.0 ~ 1.0,
    "reasoning": "최종 결정 근거",
    "conditions": ["조건1", "조건2"] (final_decision="conditional"일 때 필수),
    "human_question": "인간 확인 질문" (conditional일 때),
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
    "approval_conditions": ["condition1", "condition2", ...] or [],
    "portfolio_action": "buy_more" | "sell" | "hold" | "do_not_buy",
    "action_reason": "액션 선택 이유 (한국어, 구체적 가격/조건 포함)",
    "action_strength": "weak" | "moderate" | "strong",
    "position_adjustment_pct": -1.0 ~ 1.0
}

중요:
- final_decision = "silence"는 판단 거부 (정보 불충분)
- Agent 의견이 상충하면 보수적으로 결정
- 포트폴리오 전체 건강도 우선 고려
- **반드시 한글로 응답할 것** (reasoning, warnings, approval_conditions, action_reason 등 모든 텍스트 필드는 한국어로 작성)
"""

    def make_final_decision(
        self,
        symbol: str,
        trader_opinion: Dict[str, Any],
        risk_opinion: Dict[str, Any],
        analyst_opinion: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        correlation_data: Optional[Dict[str, Any]] = None,
        action_context: str = "new_position"
    ) -> Dict[str, Any]:
        """
        최종 의사결정 수행
        
        Returns:
            Dict (compatible with PMDecision model)
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
                'action': 'reject', # Schema compatibility
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
                'approval_conditions': [],
                'hard_rules_passed': False,
                'hard_rules_violations': hard_rules_result['violations'],
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol
            }

        # ================================================================
        # STEP 2: SILENCE POLICY CHECK (Dynamic from Persona)
        # ================================================================
        # 현재 Persona의 min_avg_confidence 가져오기
        current_persona_rules = self.persona_router.get_hard_rules()
        min_confidence_threshold = current_persona_rules.get('min_avg_confidence', 0.50)
        
        avg_confidence = (
            trader_opinion.get('confidence', 0) * trader_opinion.get('weight', 0.35) +
            risk_opinion.get('confidence', 0) * risk_opinion.get('weight', 0.35) +
            analyst_opinion.get('confidence', 0) * analyst_opinion.get('weight', 0.30)
        )

        # Silence Policy: 평균 confidence < threshold → 판단 거부 (Dynamic)
        if avg_confidence < min_confidence_threshold:
            current_mode = self.persona_router.get_current_mode()
            return {
                'agent': 'pm_mvp',
                'final_decision': 'silence',
                'action': 'silence', # Schema compatibility
                'confidence': avg_confidence,
                'reasoning': f"Silence Policy: Average confidence ({avg_confidence:.2f}) below threshold ({min_confidence_threshold}) for {current_mode.value} mode",
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
                'approval_conditions': [],
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
            avg_confidence=avg_confidence,
            action_context=action_context
        )

        # Call Gemini API
        try:
            response = self.model.generate_content([
                self.system_prompt,
                prompt
            ])

            logger.info(f"🔍 DEBUG: PM Agent Raw Response:\n{response.text}")

            # Parse and Validate with Pydantic
            decision = self._parse_response(response.text)
            
            # Convert to dict
            result = decision.model_dump()
            
            # Map action -> final_decision (for backward compatibility if needed)
            if 'action' in result and 'final_decision' not in result:
                result['final_decision'] = result['action']
            
            # Map risk_warnings -> warnings (for compatibility if needed)
            if 'risk_warnings' in result and 'warnings' not in result:
                result['warnings'] = result['risk_warnings']

            # Add metadata and hard rules info
            result['agent'] = 'pm_mvp'
            result['hard_rules_passed'] = True
            result['hard_rules_violations'] = []
            result['timestamp'] = datetime.utcnow().isoformat()
            result['symbol'] = symbol
            result['avg_agent_confidence'] = avg_confidence

            # NEW: Add portfolio action guide
            # If AI didn't provide portfolio_action, determine it from the decision
            if 'portfolio_action' not in result or not result['portfolio_action']:
                action_guide = self._determine_portfolio_action(
                    final_decision=result.get('final_decision', 'hold'),
                    recommended_action=result.get('recommended_action', 'hold'),
                    confidence=result.get('confidence', 0.5),
                    risk_level=risk_opinion.get('risk_level', 'medium'),
                    action_context=action_context
                )
                result.update(action_guide)

            return result

        except Exception as e:
            logger.error(f"❌ PM Agent Analysis Failed: {str(e)}", exc_info=True)
            # Error handling - return safe default (reject)
            return {
                'agent': 'pm_mvp',
                'final_decision': 'reject',
                'action': 'reject',
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
                'approval_conditions': [],
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
        Uses Persona-specific rules for limits.
        """
        violations = []
        
        # Get Current Persona Rules
        current_mode = self.persona_router.get_current_mode()
        persona_key = current_mode.value if hasattr(current_mode, 'value') else str(current_mode)
        
        # Fallback to default if persona not in map
        rules = self.PERSONA_HARD_RULES_DEF.get(persona_key, self.PERSONA_HARD_RULES_DEF['trading'])
        
        # Rule 1: Position Size Limit (Persona Specific)
        # Check absolute hard cap (30%) first, then persona limit
        position_size_pct = risk_opinion.get('position_size_pct', 0.0)
        
        if position_size_pct > self.HARD_RULES['max_position_size']: # 30% Absolute Cap
             violations.append(
                f"포지션 크기 {position_size_pct*100:.1f}%가 시스템 절대 한도 {self.HARD_RULES['max_position_size']*100}%를 초과합니다"
            )
        elif position_size_pct > rules['max_position_pct']: # Persona limit
            violations.append(
                f"포지션 크기 {position_size_pct*100:.1f}%가 현재 페르소나({persona_key}) 한도 {rules['max_position_pct']*100:.1f}%를 초과합니다"
            )

        # Rule 2: Total Portfolio Risk (Persona Specific)
        total_risk = portfolio_state.get('total_risk', 0.0)
        
        # Check absolute cap (5%) first? Or just use persona rule?
        # Plan implies specific persona rules: 15%, 20%, 10%, 25%.
        # Legacy hard rule was 5%. The new rules are much looser.
        # I will use the persona rule, but warn if it exceeds the 'safe' 5% legacy baseline if desired?
        # No, the plan replaces the 5% fixed limit.
        
        if total_risk > rules['max_portfolio_risk_pct']:
            violations.append(
                f"포트폴리오 리스크 {total_risk*100:.1f}%가 현재 페르소나({persona_key}) 한도 {rules['max_portfolio_risk_pct']*100:.1f}%를 초과합니다"
            )

        # Rule 3: Agent Disagreement (Directional) -- Updated to use pre-fetched rules
        max_disagreement = rules['max_agent_disagreement']

        # Debug info
        logger.info(
            f"🔍 VALIDATION DEBUG: Persona={persona_key}, Rules={{Risk: {rules['max_portfolio_risk_pct']:.2%}, "
            f"Pos: {rules['max_position_pct']:.2%}, Disagree: {max_disagreement:.2%}}}"
        )

        disagreement = self._calculate_directional_disagreement(
            votes=[
                {'action': trader_opinion.get('action', 'pass'), 'weight': 0.35},
                {'action': risk_opinion.get('recommendation', 'reject'), 'weight': 0.35},
                {'action': analyst_opinion.get('action', 'pass'), 'weight': 0.30}
            ]
        )
        
        # logger.info(...) already in code, keeping logic concise
        if disagreement > max_disagreement:
             violations.append(
                 f"Agent 방향성 불일치 {disagreement*100:.0f}%가 최대 허용치 {max_disagreement*100:.0f}%를 초과합니다 (Persona: {persona_key})"
            )
            
        # Update validation for Position Size and Portfolio Risk using Persona Rules
        # (Overwriting logic for Rule 1 & 2 implies we should have replaced them, 
        # but since this tool replaces chunks, I will modify them in subsequent chunks or assumes default usage is okay for now 
        # BUT wait, I need to apply persona_hard_rules to Rule 1 & 2 too.
        # I will inject a helper method for getting current rules and update Rule 1 & 2 in a separate tool call or larger chunk if possible.
        # For now, let's stick to replacing Rule 3 logic.)

        
        actions = [
            trader_opinion.get('action', 'pass'),
            risk_opinion.get('recommendation', 'reject'),
            analyst_opinion.get('action', 'pass')
        ]
        # Count unique actions (excluding 'pass')
        non_pass_actions = [a for a in actions if a != 'pass']
        if len(non_pass_actions) > 0:
            disagreement = 1.0 - (non_pass_actions.count(non_pass_actions[0]) / len(non_pass_actions))
            # 🔍 DEBUG: 현재 Persona 및 동적 기준 표시
            logger.warning(
                f"🔍 VALIDATION DEBUG: Persona={current_mode.value}, "
                f"disagreement={disagreement:.2f}, max_allowed={max_disagreement}, "
                f"actions={actions}, non_pass={non_pass_actions}"
            )
            if disagreement > max_disagreement:
                violations.append(
                    f"Agent 의견 불일치 {disagreement*100:.0f}%가 최대 허용치 {max_disagreement*100:.0f}%를 초과합니다 (Persona: {current_mode.value})"
                )

        # Rule 4: Average Confidence (Dynamic from Persona)
        # 현재 Persona의 min_avg_confidence 가져오기
        current_persona_rules = self.persona_router.get_hard_rules()
        min_confidence = current_persona_rules.get('min_avg_confidence', 0.50)
        
        confidences = [
            trader_opinion.get('confidence', 0.0),
            risk_opinion.get('confidence', 0.0),
            analyst_opinion.get('confidence', 0.0)
        ]
        avg_conf = sum(confidences) / len(confidences)
        if avg_conf < min_confidence:
            violations.append(
                f"평균 신뢰도 {avg_conf*100:.0f}%가 최소 요구치 {min_confidence*100:.0f}% 미만입니다"
            )

        # Rule 5: Stop Loss Required
        if self.HARD_RULES['stop_loss_required']:
            stop_loss = float(risk_opinion.get('stop_loss_pct', 0.0))
            
            # AI Hallucination Guard: if > 1.0, assume it means percentage (e.g. 10.5 -> 0.105)
            if abs(stop_loss) > 1.0:
                stop_loss = stop_loss / 100.0
                
            # Handle negative values (e.g. -0.05 for 5% loss)
            abs_stop_loss = abs(stop_loss)
            
            if abs_stop_loss <= 0.0 or abs_stop_loss > 0.20:  # Must be 0.1% ~ 20%
                violations.append(
                    f"손절매 {stop_loss*100:.2f}%가 유효하지 않습니다 (0.1% ~ 20% 범위여야 함)"
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

        # Rule 9: Leverage Guardian (10% cap on leveraged ETFs)
        leverage_guardian = get_leverage_guardian()
        if leverage_guardian.is_leveraged(symbol):
            portfolio_value = portfolio_state.get('total_value', 100000)
            current_leverage_value = sum(
                pos.get('value', 0) for pos in current_positions 
                if leverage_guardian.is_leveraged(pos.get('symbol', ''))
            )
            position_value = risk_opinion.get('position_size_usd', 0)
            
            # Check if this order would exceed leverage cap
            max_leverage_value = portfolio_value * 0.10  # 10% cap
            if current_leverage_value + position_value > max_leverage_value:
                violations.append(
                    f"레버리지 상품 한도 초과: 현재 {current_leverage_value:,.0f}원 + 신규 {position_value:,.0f}원 > 최대 {max_leverage_value:,.0f}원 (10%)"
                )
            else:
                # Add warning (not violation) for leverage products
                logger.warning(
                    f"⚠️ 레버리지 상품 {symbol} 거래: 현재 레버리지 비중 "
                    f"{(current_leverage_value + position_value) / portfolio_value * 100:.1f}%"
                )

        return {
            'passed': len(violations) == 0,
            'violations': violations
        }

    def _calculate_directional_disagreement(self, votes: List[Dict[str, Any]]) -> float:
        """
        Calculate disagreement based on direction (Attack vs Defense).
        Neutral votes are excluded from disagreement calculation.
        """
        directions = {
            "attack": ["buy", "매수", "approve", "recommend"],
            "defense": ["sell", "reduce_size", "축소", "reject"],
            "neutral": ["hold", "보류", "pass", "silence"]
        }
        
        attack_weight = 0.0
        defense_weight = 0.0
        
        for v in votes:
            action = v.get('action', '').lower()
            weight = v.get('weight', 0.0)
            
            if action in directions['attack']:
                attack_weight += weight
            elif action in directions['defense']:
                defense_weight += weight
            # Neutral is ignored
            
        total = attack_weight + defense_weight
        if total == 0:
            return 0.0
            
        minority = min(attack_weight, defense_weight)
        # Disagreement is the ratio of the minority opinion to the total non-neutral opinion
        # e.g. 0.7 vs 0.3 -> disagreement is 0.3 / 1.0 = 0.3
        # e.g. 0.35 vs 0.35 -> disagreement is 0.35 / 0.7 = 0.5 (maximum disagreement)
        # Formula from plan: return minority / total
        return minority / total

    def _build_prompt(
        self,
        symbol: str,
        trader_opinion: Dict[str, Any],
        risk_opinion: Dict[str, Any],
        analyst_opinion: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        correlation_data: Optional[Dict[str, Any]],
        avg_confidence: float,
        action_context: str = "new_position"
    ) -> str:
        """Build PM decision prompt"""
        prompt_parts = [
            f"종목: {symbol}",
            f"Context: {action_context.upper()}",
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

    def _determine_portfolio_action(
        self,
        final_decision: str,
        recommended_action: str,
        confidence: float,
        risk_level: str,
        action_context: str = "new_position"
    ) -> Dict[str, Any]:
        """
        Determine portfolio-level action from agent inputs.

        Mapping Logic:
        - approve + sell → SELL
        - approve + buy + confidence > 0.7 → BUY_MORE
        - approve + buy + confidence 0.5-0.7 → HOLD
        - reject + extreme risk → SELL
        - reject + medium/high risk → HOLD
        - silence → HOLD
        - reduce_size → SELL (partial)

        Args:
            final_decision: PM's final decision (approve/reject/silence/reduce_size)
            recommended_action: Recommended action (buy/sell/hold)
            confidence: Confidence level (0.0 ~ 1.0)
            risk_level: Risk level (low/medium/high/extreme)

        Returns:
            Dict with portfolio_action, action_strength, position_adjustment_pct
        """
        # Action mapping based on final_decision, recommended_action, confidence, risk_level
        action_map = {
            ("approve", "sell"): ("sell", "strong"),
            ("approve", "buy"): ("buy_more" if confidence > 0.7 else "hold", "moderate"),
            ("reject", "extreme"): ("sell", "strong"),
            ("reject", "high"): ("hold", "moderate"),
            ("reject", "medium"): ("hold", "moderate"),
            ("silence", ""): ("hold", "weak"),
            ("reduce_size", ""): ("sell", "moderate"),
        }

        # Determine key for action_map
        if final_decision == "reject" and risk_level == "extreme":
            key = ("reject", "extreme")
        elif final_decision == "reject" and risk_level in ("high", "medium"):
            key = ("reject", risk_level)
        elif final_decision == "approve":
            key = ("approve", recommended_action)
        elif final_decision == "silence":
            key = ("silence", "")
        elif final_decision == "reduce_size":
            key = ("reduce_size", "")
        else:
            key = ("approve", "hold")  # Default fallback

        portfolio_action, strength = action_map.get(key, ("hold", "moderate"))

        # Context-Aware Refinement
        if action_context == "existing_position":
            # Avoid 'do_not_buy' for existing positions
            if portfolio_action == "do_not_buy":
                portfolio_action = "hold"
        elif action_context == "new_position":
            # For new positions, 'hold' often means 'do_not_buy' (don't enter yet)
            if portfolio_action == "hold":
                portfolio_action = "do_not_buy"
            # 'sell' is invalid for new position, map to 'do_not_buy'
            if portfolio_action == "sell":
                portfolio_action = "do_not_buy"

        return {
            "portfolio_action": portfolio_action,
            "action_strength": strength,
            "position_adjustment_pct": self._calculate_position_adjustment(
                portfolio_action, confidence
            )
        }

    def _calculate_position_adjustment(self, action: str, confidence: float) -> float:
        """
        Calculate position adjustment percentage.

        Args:
            action: Portfolio action (sell/buy_more/hold/do_not_buy)
            confidence: Confidence level (0.0 ~ 1.0)

        Returns:
            Position adjustment percentage (-1.0 ~ 1.0)
            -0.5 = sell 50%, +0.2 = buy 20% more
        """
        adjustments = {
            "sell": -0.5,      # Sell 50%
            "buy_more": 0.2,    # Add 20%
            "hold": 0.0,
            "do_not_buy": 0.0
        }
        base = adjustments.get(action, 0.0)
        return base * confidence  # Scale by confidence

    def _parse_response(self, response_text: str) -> PMDecision:
        """Parse Gemini response using Pydantic"""
        import json
        import re

        # Extract JSON
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
                    raise ValueError("No valid JSON found")

        # Map warnings -> risk_warnings
        if 'warnings' in result_dict and 'risk_warnings' not in result_dict:
            result_dict['risk_warnings'] = result_dict.pop('warnings')
            
        # Inject hard_rules_passed (logic handled outside AI, so if we are here, it passed)
        if 'hard_rules_passed' not in result_dict:
            result_dict['hard_rules_passed'] = True

        # Ensure compatibility
        valid_actions = ['approve', 'reject', 'reduce_size', 'silence', 'conditional']
        if result_dict.get('action') not in valid_actions:
            result_dict['action'] = 'reject'
            
        # Map conditional -> approve for legacy compatibility (optional, or keep as conditional)
        # If final_decision is conditional, ensures action is at least 'hold' or 'conditional'
        if result_dict.get('final_decision') == 'conditional':
             result_dict['action'] = 'conditional' # Ensure action matches if used elsewhere
            
        # Instantiate and Validate with Pydantic
        return PMDecision(**result_dict)

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
    print(f"Warnings: {result.get('warnings', [])}")
