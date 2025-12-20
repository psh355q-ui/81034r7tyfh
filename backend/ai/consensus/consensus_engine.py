"""
Consensus Engine - 3-AI 방어적 투표 시스템

Phase E1: Defensive Consensus Engine
Phase F1: AI 집단지성 고도화 통합

3개 AI(Claude, ChatGPT, Gemini)가 동일한 MarketContext를 받아
비대칭 의사결정 로직에 따라 투표하여 최종 결정

새로운 F1 기능:
- AI 역할 기반 프롬프트 (AIRoleManager)
- 응답 품질 검증 (DecisionProtocol)
- 토론 기록 저장 (DebateLogger)
- 성과 기반 가중치 (AgentWeightTrainer)

작성일: 2025-12-06
수정일: 2025-12-08 (Phase F1 통합)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

from backend.schemas.base_schema import MarketContext, SignalAction
from backend.ai.consensus.consensus_models import (
    ConsensusResult,
    AIVote,
    VoteDecision,
    ConsensusStrength,
    VoteRequest,
    ConsensusStats
)
from backend.ai.consensus.voting_rules import VotingRules, VoteRequirement

# Phase F1: AI 집단지성 모듈 통합
try:
    from backend.ai.collective import get_role_manager, AIAgentType
    from backend.ai.core import get_decision_protocol, validate_decision
    from backend.ai.meta import (
        get_debate_logger, get_weight_trainer,
        VoteType, AgentVote as DebateAgentVote, MarketContextSnapshot
    )
    F1_MODULES_AVAILABLE = True
except ImportError as e:
    F1_MODULES_AVAILABLE = False
    logging.warning(f"F1 modules not available: {e}")

logger = logging.getLogger(__name__)


class ConsensusEngine:
    """
    3-AI Defensive Consensus Engine

    비대칭 의사결정 로직:
    - STOP_LOSS: 1명 경고 → 즉시 실행
    - BUY: 2명 찬성 → 허용
    - DCA: 3명 전원 동의 → 허용

    Usage:
        engine = ConsensusEngine(claude_client, chatgpt_client, gemini_client)
        result = await engine.vote_on_signal(context, "BUY")
        if result.approved:
            # 시그널 실행
    """

    def __init__(
        self,
        claude_client=None,
        chatgpt_client=None,
        gemini_client=None,
        enable_f1_features: bool = True  # Phase F1 기능 활성화
    ):
        """
        Initialize Consensus Engine

        Args:
            claude_client: ClaudeClient 인스턴스
            chatgpt_client: ChatGPTClient 인스턴스
            gemini_client: GeminiClient 인스턴스
            enable_f1_features: Phase F1 기능 활성화 여부
        """
        self.clients = {}

        if claude_client:
            self.clients["claude"] = claude_client
        if chatgpt_client:
            self.clients["chatgpt"] = chatgpt_client
        if gemini_client:
            self.clients["gemini"] = gemini_client

        if len(self.clients) == 0:
            logger.warning("No AI clients provided, Consensus Engine will use mock votes")

        # 통계
        self.stats = ConsensusStats()
        self._vote_history: List[ConsensusResult] = []

        # Phase F1: AI 집단지성 모듈 초기화
        self.f1_enabled = enable_f1_features and F1_MODULES_AVAILABLE
        if self.f1_enabled:
            self._role_manager = get_role_manager()
            self._decision_protocol = get_decision_protocol()
            self._debate_logger = get_debate_logger()
            self._weight_trainer = get_weight_trainer()
            logger.info("Phase F1 modules integrated: RoleManager, DecisionProtocol, DebateLogger, WeightTrainer")
        else:
            self._role_manager = None
            self._decision_protocol = None
            self._debate_logger = None
            self._weight_trainer = None

        logger.info(f"ConsensusEngine initialized with {len(self.clients)} AI clients, F1={self.f1_enabled}")

    async def vote_on_signal(
        self,
        context: MarketContext,
        action: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> ConsensusResult:
        """
        특정 액션에 대해 3개 AI의 투표 수집 및 합의 도출

        Args:
            context: 시장 컨텍스트 (MarketContext)
            action: 투표 대상 액션 (BUY/SELL/DCA/STOP_LOSS 등)
            additional_info: 추가 정보 (가격, DCA 횟수 등)

        Returns:
            ConsensusResult: 투표 결과 및 최종 승인 여부
        """
        start_time = datetime.now()

        logger.info(f"Starting consensus vote for {action} on {context.ticker}")

        # 1. 각 AI에게 투표 요청
        votes = await self._collect_votes(context, action, additional_info or {})

        # 2. 투표 집계
        approve_count = sum(
            1 for vote in votes.values()
            if vote.decision == VoteDecision.APPROVE
        )
        reject_count = sum(
            1 for vote in votes.values()
            if vote.decision == VoteDecision.REJECT
        )

        # 3. 비대칭 규칙 적용
        requirement = VotingRules.get_requirement(action)
        approved = VotingRules.is_approved(action, approve_count)

        # 4. Consensus 강도 계산
        consensus_strength = self._calculate_consensus_strength(approve_count)

        # 5. 평균 메트릭 계산
        confidence_avg = sum(v.confidence for v in votes.values()) / len(votes)
        risk_scores = [v.risk_score for v in votes.values() if v.risk_score is not None]
        risk_score_avg = sum(risk_scores) / len(risk_scores) if risk_scores else None

        # 6. 결과 생성
        result = ConsensusResult(
            approved=approved,
            action=action,
            votes=votes,
            approve_count=approve_count,
            reject_count=reject_count,
            consensus_strength=consensus_strength,
            confidence_avg=confidence_avg,
            risk_score_avg=risk_score_avg,
            ticker=context.ticker,
            vote_requirement=requirement.value,
            timestamp=datetime.now(),
            metadata={
                "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                **(additional_info or {})
            }
        )

        # 7. 통계 업데이트
        self._update_stats(result)
        
        # 8. Phase F1: 토론 기록 저장
        if self.f1_enabled and self._debate_logger:
            self._log_debate_to_f1(context, action, votes, result)

        logger.info(
            f"Consensus result: {action} {'APPROVED' if approved else 'REJECTED'} "
            f"({approve_count}/3 votes, requirement: {requirement.value})"
        )

        return result

    async def _collect_votes(
        self,
        context: MarketContext,
        action: str,
        additional_info: Dict[str, Any]
    ) -> Dict[str, AIVote]:
        """
        3개 AI로부터 병렬로 투표 수집

        Args:
            context: 시장 컨텍스트
            action: 투표 대상 액션
            additional_info: 추가 정보

        Returns:
            AI별 투표 결과 딕셔너리
        """
        if len(self.clients) == 0:
            # Mock votes for testing
            return self._generate_mock_votes(context, action)

        # 병렬 투표 수집
        vote_tasks = []
        ai_names = []

        for ai_name, client in self.clients.items():
            task = self._request_vote_from_ai(ai_name, client, context, action, additional_info)
            vote_tasks.append(task)
            ai_names.append(ai_name)

        # 모든 투표를 동시에 수집 (최대 지연시간 = 가장 느린 AI)
        vote_results = await asyncio.gather(*vote_tasks, return_exceptions=True)

        # 결과 조합
        votes = {}
        for ai_name, vote_result in zip(ai_names, vote_results):
            if isinstance(vote_result, Exception):
                logger.error(f"Vote collection failed for {ai_name}: {vote_result}")
                # 에러 발생 시 기권 처리
                votes[ai_name] = AIVote(
                    ai_model=ai_name,
                    decision=VoteDecision.ABSTAIN,
                    confidence=0.0,
                    reasoning=f"Vote collection failed: {str(vote_result)}"
                )
            else:
                votes[ai_name] = vote_result

        return votes

    async def _request_vote_from_ai(
        self,
        ai_name: str,
        client: Any,
        context: MarketContext,
        action: str,
        additional_info: Dict[str, Any]
    ) -> AIVote:
        """
        개별 AI에게 투표 요청 (Phase F1: 역할 기반 프롬프트 적용)

        Args:
            ai_name: AI 모델명
            client: AI 클라이언트 인스턴스
            context: 시장 컨텍스트
            action: 투표 대상 액션
            additional_info: 추가 정보

        Returns:
            AIVote: 투표 결과
        """
        try:
            # Phase F1: 역할 기반 프롬프트 구성 (ai_name 전달)
            prompt = self._build_voting_prompt(context, action, additional_info, ai_name=ai_name)

            # AI 호출 (기존 analyze_stock 메서드 활용)
            response = await client.analyze_stock(
                ticker=context.ticker or "UNKNOWN",
                features=self._context_to_features(context),
                market_context={"action_to_vote": action},
                portfolio_context=additional_info
            )

            # Phase F1: 응답 품질 검증
            if self.f1_enabled and self._decision_protocol:
                validation = self._decision_protocol.validate(response)
                if not validation.is_valid:
                    logger.warning(
                        f"[{ai_name}] Response validation failed: "
                        f"{validation.error_count} errors, {validation.warning_count} warnings"
                    )
                    # 검증 실패 시 기권 처리
                    return AIVote(
                        ai_model=ai_name,
                        decision=VoteDecision.ABSTAIN,
                        confidence=0.0,
                        reasoning=f"Response validation failed: {[i.message for i in validation.issues[:3]]}"
                    )

            # 응답 파싱하여 AIVote로 변환
            return self._parse_ai_response_to_vote(ai_name, response, action)

        except Exception as e:
            logger.error(f"Vote request failed for {ai_name}: {e}")
            return AIVote(
                ai_model=ai_name,
                decision=VoteDecision.ABSTAIN,
                confidence=0.0,
                reasoning=f"Error during vote: {str(e)}"
            )

    def _build_voting_prompt(
        self,
        context: MarketContext,
        action: str,
        additional_info: Dict[str, Any],
        ai_name: str = None  # Phase F1: AI 이름 추가
    ) -> str:
        """투표용 프롬프트 구성 (Phase F1: 역할 기반 프롬프트 추가)"""
        
        # Phase F1: 역할 기반 프롬프트 프리픽스 추가
        role_prefix = ""
        if self.f1_enabled and self._role_manager and ai_name:
            try:
                agent_type = AIAgentType(ai_name)
                role_prefix = self._role_manager.get_role_prompt(agent_type)
                if role_prefix:
                    role_prefix = f"{role_prefix}\n\n---\n\n"
            except (ValueError, KeyError):
                pass
        
        prompt_parts = [
            role_prefix,  # Phase F1: 역할 프롬프트
            f"You are voting on a {action} signal for {context.ticker}.",
            "",
            "Based on the market context provided, decide whether to APPROVE or REJECT this action.",
            "",
            "Consider:",
            "- Fundamentals and company health",
            "- Market sentiment and news",
            "- Risk factors and supply chain",
            "- Current market regime",
            "",
        ]

        if action == "STOP_LOSS":
            prompt_parts.extend([
                "This is a STOP_LOSS action (defensive).",
                "APPROVE if you see ANY significant risk that warrants cutting losses.",
                "Even minor concerns should lead to APPROVAL for protection.",
                ""
            ])
        elif action == "DCA":
            prompt_parts.extend([
                "This is a DCA (Dollar Cost Averaging) action.",
                "APPROVE ONLY if:",
                "  1. Fundamentals remain strong",
                "  2. Price drop is temporary/technical",
                "  3. No deterioration in business outlook",
                "Be VERY conservative - reject if any doubt exists.",
                ""
            ])
        elif action == "BUY":
            prompt_parts.extend([
                "This is a BUY action.",
                "APPROVE if you have reasonable confidence in the opportunity.",
                "REJECT if significant risks or uncertainties exist.",
                ""
            ])

        if additional_info:
            prompt_parts.append(f"Additional context: {additional_info}")

        return "\n".join(prompt_parts)

    def _context_to_features(self, context: MarketContext) -> Dict[str, Any]:
        """MarketContext를 AI features 딕셔너리로 변환"""
        features = {}

        if context.news:
            features["news_sentiment"] = context.news.sentiment
            features["news_segment"] = context.news.segment.value if context.news.segment else None

        if context.unit_economics:
            features["token_cost"] = context.unit_economics.token_cost

        if context.risk_factors:
            features["risk_factors"] = context.risk_factors

        if context.market_regime:
            features["market_regime"] = context.market_regime.value

        return features

    def _parse_ai_response_to_vote(
        self,
        ai_name: str,
        response: Dict[str, Any],
        action: str
    ) -> AIVote:
        """
        AI 응답을 AIVote로 파싱

        Args:
            ai_name: AI 모델명
            response: AI analyze_stock() 응답
            action: 투표 대상 액션

        Returns:
            AIVote
        """
        # AI의 action 추천과 투표 대상 action 비교
        ai_action = response.get("action", "HOLD")
        conviction = response.get("conviction", 0.5)
        reasoning = response.get("reasoning", "No reasoning provided")
        risk_factors = response.get("risk_factors", [])

        # 투표 결정 로직
        if action == "STOP_LOSS":
            # STOP_LOSS는 AI가 SELL을 추천하거나 리스크가 높으면 APPROVE
            if ai_action == "SELL" or len(risk_factors) >= 2:
                decision = VoteDecision.APPROVE
            else:
                decision = VoteDecision.REJECT
        elif action == "DCA":
            # DCA는 AI가 BUY를 강력히 추천하고 리스크가 낮아야 APPROVE
            if ai_action == "BUY" and conviction >= 0.7 and len(risk_factors) <= 1:
                decision = VoteDecision.APPROVE
            else:
                decision = VoteDecision.REJECT
        elif action in ["BUY", "INCREASE"]:
            # BUY는 AI가 BUY/HOLD 추천하면 APPROVE
            if ai_action in ["BUY", "HOLD"]:
                decision = VoteDecision.APPROVE
            else:
                decision = VoteDecision.REJECT
        elif action in ["SELL", "REDUCE"]:
            # SELL은 AI가 SELL 추천하면 APPROVE
            if ai_action == "SELL":
                decision = VoteDecision.APPROVE
            else:
                decision = VoteDecision.REJECT
        else:
            # 기본: conviction 기반
            decision = VoteDecision.APPROVE if conviction >= 0.6 else VoteDecision.REJECT

        return AIVote(
            ai_model=ai_name,
            decision=decision,
            confidence=conviction,
            reasoning=reasoning,
            risk_score=len(risk_factors) / 5.0 if risk_factors else None,
            timestamp=datetime.now()
        )

    def _generate_mock_votes(
        self,
        context: MarketContext,
        action: str
    ) -> Dict[str, AIVote]:
        """테스트용 Mock 투표 생성"""
        import random

        mock_votes = {}
        ai_models = ["claude", "chatgpt", "gemini"]

        for ai_name in ai_models:
            # 랜덤 투표 (테스트용)
            if action == "STOP_LOSS":
                # STOP_LOSS는 보수적으로 - 50% 확률로 APPROVE
                decision = VoteDecision.APPROVE if random.random() > 0.5 else VoteDecision.REJECT
            elif action == "DCA":
                # DCA는 매우 보수적으로 - 30% 확률로 APPROVE
                decision = VoteDecision.APPROVE if random.random() > 0.7 else VoteDecision.REJECT
            else:
                # 일반 액션 - 60% 확률로 APPROVE
                decision = VoteDecision.APPROVE if random.random() > 0.4 else VoteDecision.REJECT

            mock_votes[ai_name] = AIVote(
                ai_model=ai_name,
                decision=decision,
                confidence=random.uniform(0.6, 0.9),
                reasoning=f"Mock vote from {ai_name} for {action}",
                risk_score=random.uniform(0.2, 0.6)
            )

        return mock_votes

    def _calculate_consensus_strength(self, approve_count: int) -> ConsensusStrength:
        """Consensus 강도 계산"""
        if approve_count == 3:
            return ConsensusStrength.UNANIMOUS
        elif approve_count == 2:
            return ConsensusStrength.STRONG
        elif approve_count == 1:
            return ConsensusStrength.WEAK
        else:
            return ConsensusStrength.NO_CONSENSUS

    def _update_stats(self, result: ConsensusResult):
        """통계 업데이트"""
        self.stats.total_votes += 1

        if result.approved:
            self.stats.approved_votes += 1
        else:
            self.stats.rejected_votes += 1

        # 승인율 계산
        if self.stats.total_votes > 0:
            self.stats.approval_rate = self.stats.approved_votes / self.stats.total_votes

        # 액션별 투표 수
        if result.action not in self.stats.votes_by_action:
            self.stats.votes_by_action[result.action] = 0
        self.stats.votes_by_action[result.action] += 1

        # AI 일치율 계산 (다수 의견과 일치하는 비율)
        majority_decision = VoteDecision.APPROVE if result.approve_count >= 2 else VoteDecision.REJECT
        for ai_name, vote in result.votes.items():
            if ai_name not in self.stats.ai_agreement_rate:
                self.stats.ai_agreement_rate[ai_name] = 0.0

            # 간단한 이동 평균 업데이트
            is_agree = (vote.decision == majority_decision)
            current_rate = self.stats.ai_agreement_rate[ai_name]
            alpha = 0.1  # 학습률
            self.stats.ai_agreement_rate[ai_name] = current_rate * (1 - alpha) + is_agree * alpha

        # 평균 처리 시간
        processing_time = result.metadata.get("processing_time_ms", 0)
        if self.stats.avg_consensus_time_ms == 0:
            self.stats.avg_consensus_time_ms = processing_time
        else:
            alpha = 0.1
            self.stats.avg_consensus_time_ms = (
                self.stats.avg_consensus_time_ms * (1 - alpha) + processing_time * alpha
            )

        # 히스토리 저장 (최근 100개만)
        self._vote_history.append(result)
        if len(self._vote_history) > 100:
            self._vote_history.pop(0)
    
    def _log_debate_to_f1(
        self,
        context: MarketContext,
        action: str,
        votes: Dict[str, AIVote],
        result: ConsensusResult
    ):
        """
        Phase F1: 토론 결과를 DebateLogger에 저장
        """
        if not self.f1_enabled or not self._debate_logger:
            return
        
        try:
            # 투표 데이터 변환
            debate_votes = []
            for ai_name, vote in votes.items():
                # VoteDecision -> VoteType 변환
                if vote.decision == VoteDecision.APPROVE:
                    if action.upper() in ["BUY", "INCREASE", "DCA"]:
                        vote_type = VoteType.BUY
                    elif action.upper() in ["SELL", "REDUCE", "STOP_LOSS"]:
                        vote_type = VoteType.SELL
                    else:
                        vote_type = VoteType.HOLD
                elif vote.decision == VoteDecision.REJECT:
                    vote_type = VoteType.HOLD
                else:
                    vote_type = VoteType.ABSTAIN
                
                # 역할 정보 가져오기
                role = None
                if self._role_manager:
                    try:
                        agent_type = AIAgentType(ai_name)
                        assignment = self._role_manager.get_assignment(agent_type)
                        if assignment:
                            role = assignment.primary_role.value
                    except:
                        pass
                
                debate_votes.append(DebateAgentVote(
                    agent_name=ai_name,
                    vote=vote_type,
                    confidence=vote.confidence,
                    reasoning=vote.reasoning or "",
                    role=role
                ))
            
            # 시장 컨텍스트 스냅샷
            market_snapshot = MarketContextSnapshot(
                price=0.0,  # TODO: 실제 가격 연동
                volatility=context.risk_factors.get("volatility") if context.risk_factors else None,
                market_sentiment=context.market_regime.value if context.market_regime else None
            )
            
            # 최종 결정 변환
            if result.approved:
                if action.upper() in ["BUY", "INCREASE"]:
                    final_decision = VoteType.BUY
                elif action.upper() == "DCA":
                    final_decision = VoteType.DCA
                elif action.upper() in ["SELL", "REDUCE"]:
                    final_decision = VoteType.SELL
                elif action.upper() == "STOP_LOSS":
                    final_decision = VoteType.STOP_LOSS
                else:
                    final_decision = VoteType.HOLD
            else:
                final_decision = VoteType.HOLD
            
            # 반대 에이전트 목록
            dissenting = [
                ai_name for ai_name, vote in votes.items()
                if vote.decision != VoteDecision.APPROVE
            ]
            
            # 토론 기록
            self._debate_logger.log_debate(
                ticker=context.ticker or "UNKNOWN",
                topic=f"{action} 결정",
                votes=debate_votes,
                context=market_snapshot,
                final_decision=final_decision,
                consensus_strength=result.approve_count / 3.0,
                dissenting_agents=dissenting
            )
            
            logger.debug(f"Debate logged for {context.ticker}: {action}")
            
        except Exception as e:
            logger.error(f"Failed to log debate: {e}")
    
    def get_agent_weights(self) -> Dict[str, float]:
        """
        Phase F1: 에이전트별 가중치 조회
        """
        if self.f1_enabled and self._weight_trainer:
            return self._weight_trainer.get_all_weights()
        return {"claude": 1.0, "chatgpt": 1.0, "gemini": 1.0}
    
    def get_role_assignments(self) -> Dict[str, str]:
        """
        Phase F1: 에이전트별 역할 할당 조회
        """
        if self.f1_enabled and self._role_manager:
            assignments = self._role_manager.get_all_assignments()
            return {
                agent.value: assignment.primary_role.value
                for agent, assignment in assignments.items()
            }
        return {}

    def get_stats(self) -> ConsensusStats:
        """통계 조회"""
        return self.stats

    def get_recent_votes(self, limit: int = 10) -> List[ConsensusResult]:
        """최근 투표 결과 조회"""
        return self._vote_history[-limit:]

    async def evaluate_dca(
        self,
        ticker: str,
        current_price: float,
        avg_entry_price: float,
        dca_count: int,
        total_invested: float,
        context: MarketContext
    ) -> Dict[str, Any]:
        """
        DCA 실행에 대한 종합 평가

        1. DCA 전략으로 기본 조건 확인
        2. 조건 충족 시 3-AI Consensus 투표
        3. 3명 전원 동의 필요 (3/3)

        Args:
            ticker: 종목 티커
            current_price: 현재 가격
            avg_entry_price: 평균 매수가
            dca_count: 현재 DCA 횟수
            total_invested: 총 투자액
            context: 시장 컨텍스트

        Returns:
            Dict with:
                - dca_recommended: bool (DCA 추천 여부)
                - consensus_approved: bool (Consensus 승인 여부)
                - dca_decision: DCADecision
                - consensus_result: Optional[ConsensusResult]
                - final_decision: str ("APPROVED" | "REJECTED")
        """
        from backend.ai.strategies.dca_strategy import get_dca_strategy

        logger.info(f"Evaluating DCA for {ticker}: ${current_price} vs ${avg_entry_price}")

        # 1. DCA 전략 기본 평가
        dca_strategy = get_dca_strategy()
        dca_decision = await dca_strategy.should_dca(
            ticker=ticker,
            current_price=current_price,
            avg_entry_price=avg_entry_price,
            dca_count=dca_count,
            total_invested=total_invested,
            context=context
        )

        # 2. DCA 전략이 거부하면 즉시 반환
        if not dca_decision.should_dca:
            return {
                "dca_recommended": False,
                "consensus_approved": False,
                "dca_decision": dca_decision,
                "consensus_result": None,
                "final_decision": "REJECTED",
                "rejection_reason": dca_decision.reasoning
            }

        # 3. DCA 전략이 승인하면 Consensus 투표 진행
        additional_info = {
            "current_price": current_price,
            "avg_entry_price": avg_entry_price,
            "dca_count": dca_count,
            "price_drop_pct": ((current_price - avg_entry_price) / avg_entry_price) * 100,
            "position_size": dca_decision.position_size,
            "dca_reasoning": dca_decision.reasoning
        }

        consensus_result = await self.vote_on_signal(
            context=context,
            action="DCA",
            additional_info=additional_info
        )

        # 4. 최종 결정: DCA는 3명 전원 동의 필요
        final_approved = consensus_result.approved

        return {
            "dca_recommended": True,
            "consensus_approved": final_approved,
            "dca_decision": dca_decision,
            "consensus_result": consensus_result,
            "final_decision": "APPROVED" if final_approved else "REJECTED",
            "approval_details": {
                "votes": f"{consensus_result.approve_count}/3",
                "requirement": consensus_result.vote_requirement,
                "consensus_strength": consensus_result.consensus_strength.value
            }
        }


# ============================================================================
# Global Singleton
# ============================================================================

_consensus_engine: Optional[ConsensusEngine] = None


def get_consensus_engine() -> ConsensusEngine:
    """Consensus Engine 싱글톤 인스턴스"""
    global _consensus_engine
    if _consensus_engine is None:
        # AI 클라이언트 초기화 (지연 초기화)
        try:
            from backend.ai.ai_client_factory import get_ai_client

            claude_client = get_ai_client("claude")
            chatgpt_client = get_ai_client("chatgpt")
            gemini_client = get_ai_client("gemini")

            _consensus_engine = ConsensusEngine(
                claude_client=claude_client,
                chatgpt_client=chatgpt_client,
                gemini_client=gemini_client
            )
        except Exception as e:
            logger.warning(f"Failed to initialize AI clients: {e}, using mock consensus engine")
            _consensus_engine = ConsensusEngine()  # Mock mode

    return _consensus_engine


# ============================================================================
# 테스트 및 데모
# ============================================================================

if __name__ == "__main__":
    import asyncio
    from backend.schemas.base_schema import MarketContext, NewsFeatures, MarketSegment

    async def test_consensus():
        print("=" * 70)
        print("Consensus Engine Test")
        print("=" * 70)

        # Mock Consensus Engine (AI 클라이언트 없이 테스트)
        engine = ConsensusEngine()

        # 테스트 MarketContext
        context = MarketContext(
            ticker="NVDA",
            company_name="NVIDIA",
            news=NewsFeatures(
                headline="NVIDIA announces new Blackwell GPU",
                segment=MarketSegment.TRAINING,
                sentiment=0.85
            )
        )

        # 다양한 액션에 대해 투표 테스트
        test_actions = ["BUY", "SELL", "DCA", "STOP_LOSS"]

        for action in test_actions:
            print(f"\n{'-' * 70}")
            print(f"Testing: {action}")
            print(f"{'-' * 70}")

            result = await engine.vote_on_signal(context, action)

            status = "APPROVED" if result.approved else "REJECTED"
            print(f"Result: {status}")
            print(f"Votes: {result.approve_count}/3 (requirement: {result.vote_requirement})")
            print(f"Consensus Strength: {result.consensus_strength.value}")
            print(f"Confidence Avg: {result.confidence_avg:.2f}")

            print(f"\nIndividual Votes:")
            for ai_name, vote in result.votes.items():
                print(f"  {ai_name}: {vote.decision.value} (confidence: {vote.confidence:.2f})")

        # 통계 출력
        print(f"\n{'=' * 70}")
        print("Consensus Engine Statistics")
        print(f"{'=' * 70}")
        stats = engine.get_stats()
        print(f"Total Votes: {stats.total_votes}")
        print(f"Approved: {stats.approved_votes}")
        print(f"Rejected: {stats.rejected_votes}")
        print(f"Approval Rate: {stats.approval_rate:.1%}")

    asyncio.run(test_consensus())
