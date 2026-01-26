"""
Persona Integration Service - Persona System Integration with Trading System

Phase 3: Persona-based Trading
Date: 2026-01-25

Purpose:
    Persona 시스템을 기존 투자 시스템과 통합합니다.
    - War Room MVP와 Persona Router 연동
    - Trading Signal 생성 시 Persona 적용
    - Order 실행 시 Persona 기반 리스크 관리
    - Portfolio 리밸런싱 지원
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.database.models import (
    Persona,
    TradingSignal,
    Order,
    MultiAssetPosition,
    PortfolioAllocation,
)
from backend.services.persona_trading_service import PersonaTradingService
from backend.ai.router.persona_router import PersonaMode, get_persona_router


class PersonaIntegrationService:
    """
    Persona Integration Service - Persona 시스템 통합
    
    기존 투자 시스템(War Room MVP, Trading Signal, Order 등)과
    Persona 시스템을 연동하여 Persona 기반 투자를 지원합니다.
    """
    
    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.persona_service = PersonaTradingService(db)
        self.persona_router = get_persona_router()
    
    # ============================================================================
    # War Room MVP Integration
    # ============================================================================
    
    def apply_persona_to_war_room_decision(
        self,
        user_id: str,
        ticker: str,
        action: str,
        confidence: float,
        agent_votes: Dict[str, Dict[str, any]]
    ) -> Tuple[bool, str, Dict[str, any]]:
        """
        War Room MVP 결정에 Persona 적용
        
        Args:
            user_id: 사용자 ID
            ticker: 티커
            action: 액션 (BUY/SELL/HOLD)
            confidence: 확신도
            agent_votes: 에이전트 투표 결과
                {
                    "trader_mvp": {"action": "BUY", "confidence": 0.8, "reasoning": "..."},
                    "risk_mvp": {"action": "HOLD", "confidence": 0.7, "reasoning": "..."},
                    "analyst_mvp": {"action": "BUY", "confidence": 0.9, "reasoning": "..."}
                }
        
        Returns:
            (허용 여부, 메시지, Persona 적용 결과)
        """
        # 사용자의 Persona 조회
        persona = self.persona_service.get_user_persona(user_id)
        if not persona:
            persona = self.persona_service.get_default_persona()
        
        # Persona Router 모드 전환
        persona_mode = self.persona_service._map_persona_to_mode(persona.name)
        self.persona_router.set_mode(persona_mode)
        
        # Persona 가중치 적용
        weights = self.persona_router.get_weights(persona_mode)
        
        # 가중치 적용된 최종 결정 계산
        weighted_decision = self._calculate_weighted_decision(
            agent_votes,
            weights
        )
        
        # Hard Rules 검증
        agent_disagreement = self._calculate_agent_disagreement(agent_votes)
        avg_confidence = sum(v["confidence"] for v in agent_votes.values()) / len(agent_votes)
        
        allowed, message = self.persona_service.validate_signal_with_persona(
            persona,
            confidence,
            agent_disagreement,
            avg_confidence
        )
        
        result = {
            "persona_id": persona.id,
            "persona_name": persona.display_name,
            "persona_mode": persona_mode,
            "weights": weights,
            "weighted_decision": weighted_decision,
            "agent_disagreement": agent_disagreement,
            "avg_confidence": avg_confidence,
            "hard_rules": {
                "max_agent_disagreement": float(persona.max_agent_disagreement),
                "min_avg_confidence": float(persona.min_avg_confidence),
            }
        }
        
        return (allowed, message, result)
    
    def _calculate_weighted_decision(
        self,
        agent_votes: Dict[str, Dict[str, any]],
        weights: Dict[str, float]
    ) -> Dict[str, any]:
        """
        가중치 적용된 최종 결정 계산
        
        Args:
            agent_votes: 에이전트 투표 결과
            weights: 에이전트 가중치
        
        Returns:
            가중치 적용된 결정
        """
        # 액션별 가중치 합계 계산
        action_scores = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        
        for agent_name, vote in agent_votes.items():
            weight = weights.get(agent_name, 0.0)
            action = vote.get("action", "HOLD")
            confidence = vote.get("confidence", 0.5)
            
            action_scores[action] += weight * confidence
        
        # 최대 점수 액션 선택
        final_action = max(action_scores, key=action_scores.get)
        final_confidence = action_scores[final_action]
        
        return {
            "action": final_action,
            "confidence": final_confidence,
            "action_scores": action_scores
        }
    
    def _calculate_agent_disagreement(
        self,
        agent_votes: Dict[str, Dict[str, any]]
    ) -> float:
        """
        에이전트 불일치도 계산
        
        Args:
            agent_votes: 에이전트 투표 결과
        
        Returns:
            불일치도 (0.0 ~ 1.0)
        """
        actions = [v["action"] for v in agent_votes.values()]
        
        # 모든 에이전트가 동일한 액션
        if len(set(actions)) == 1:
            return 0.0
        
        # 2명 동의, 1명 반대
        if len(set(actions)) == 2:
            # 가장 많은 액션의 비율
            most_common = max(set(actions), key=actions.count)
            ratio = actions.count(most_common) / len(actions)
            return 1.0 - ratio
        
        # 3명 모두 다름
        return 1.0
    
    # ============================================================================
    # Trading Signal Integration
    # ============================================================================
    
    def create_persona_aware_signal(
        self,
        user_id: str,
        ticker: str,
        action: str,
        confidence: float,
        reasoning: str,
        agent_votes: Optional[Dict[str, Dict[str, any]]] = None,
        metadata: Optional[Dict[str, any]] = None
    ) -> TradingSignal:
        """
        Persona 인지 Trading Signal 생성
        
        Args:
            user_id: 사용자 ID
            ticker: 티커
            action: 액션 (BUY/SELL/HOLD)
            confidence: 확신도
            reasoning: 추론
            agent_votes: 에이전트 투표 결과
            metadata: 추가 메타데이터
        
        Returns:
            생성된 TradingSignal
        """
        # 사용자의 Persona 조회
        persona = self.persona_service.get_user_persona(user_id)
        if not persona:
            persona = self.persona_service.get_default_persona()
        
        # War Room 결정에 Persona 적용
        if agent_votes:
            allowed, message, persona_result = self.apply_persona_to_war_room_decision(
                user_id, ticker, action, confidence, agent_votes
            )
            
            if not allowed:
                # Hard Rules 위반 시 HOLD로 변경
                action = "HOLD"
                reasoning = f"{reasoning}\n\n[Persona Override: {message}]"
        
        # Trading Signal 생성
        signal = TradingSignal(
            ticker=ticker,
            action=action,
            signal_type="PERSONA",
            confidence=confidence,
            reasoning=reasoning,
            source="persona_integration",
            news_title=metadata.get("news_title") if metadata else None,
            news_source=metadata.get("news_source") if metadata else None,
        )
        
        self.db.add(signal)
        self.db.commit()
        self.db.refresh(signal)
        
        return signal
    
    # ============================================================================
    # Order Integration
    # ============================================================================
    
    def validate_order_with_persona(
        self,
        user_id: str,
        ticker: str,
        order_value: float,
        portfolio_value: float,
        sector: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, any]]:
        """
        Order에 Persona 기반 리스크 관리 적용
        
        Args:
            user_id: 사용자 ID
            ticker: 티커
            order_value: 주문 가치
            portfolio_value: 포트폴리오 총 가치
            sector: 섹터
        
        Returns:
            (허용 여부, 메시지, 검증 결과)
        """
        # 사용자의 Persona 조회
        persona = self.persona_service.get_user_persona(user_id)
        if not persona:
            persona = self.persona_service.get_default_persona()
        
        # 포지션 제한 확인
        allowed, message = self.persona_service.check_position_limit(
            persona,
            ticker,
            order_value,
            portfolio_value,
            sector
        )
        
        result = {
            "persona_id": persona.id,
            "persona_name": persona.display_name,
            "order_value": order_value,
            "portfolio_value": portfolio_value,
            "position_pct": order_value / portfolio_value if portfolio_value > 0 else 0,
            "max_position_pct": float(persona.max_position_size),
            "max_sector_exposure": float(persona.max_sector_exposure),
            "leverage_allowed": persona.leverage_allowed,
            "max_leverage_pct": float(persona.max_leverage_pct),
        }
        
        return (allowed, message, result)
    
    def calculate_order_size_with_persona(
        self,
        user_id: str,
        ticker: str,
        portfolio_value: float,
        confidence: float,
        risk_level: str = "MEDIUM"
    ) -> Tuple[float, Dict[str, any]]:
        """
        Persona 기반 주문 사이즈 계산
        
        Args:
            user_id: 사용자 ID
            ticker: 티커
            portfolio_value: 포트폴리오 총 가치
            confidence: 확신도
            risk_level: 리스크 레벨
        
        Returns:
            (주문 사이즈, 계산 결과)
        """
        # 사용자의 Persona 조회
        persona = self.persona_service.get_user_persona(user_id)
        if not persona:
            persona = self.persona_service.get_default_persona()
        
        # 포지션 사이즈 계산
        position_size = self.persona_service.calculate_position_size(
            persona,
            portfolio_value,
            confidence,
            risk_level
        )
        
        result = {
            "persona_id": persona.id,
            "persona_name": persona.display_name,
            "portfolio_value": portfolio_value,
            "confidence": confidence,
            "risk_level": risk_level,
            "position_size": position_size,
            "position_pct": position_size / portfolio_value if portfolio_value > 0 else 0,
            "max_position_pct": float(persona.max_position_size),
        }
        
        return (position_size, result)
    
    # ============================================================================
    # Portfolio Rebalancing Integration
    # ============================================================================
    
    def get_rebalance_recommendations(
        self,
        user_id: str,
        total_value: float,
        current_positions: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        Persona 기반 포트폴리오 리밸런싱 추천
        
        Args:
            user_id: 사용자 ID
            total_value: 총 포트폴리오 가치
            current_positions: 현재 포지션 목록
        
        Returns:
            리밸런싱 추천 목록
        """
        # 사용자의 Persona 조회
        persona = self.persona_service.get_user_persona(user_id)
        if not persona:
            persona = self.persona_service.get_default_persona()
        
        # 리밸런싱 추천 생성
        recommendations = self.persona_service.get_rebalance_recommendations(
            persona,
            total_value,
            current_positions
        )
        
        # Persona 정보 추가
        for rec in recommendations:
            rec["persona_id"] = persona.id
            rec["persona_name"] = persona.display_name
        
        return recommendations
    
    def update_portfolio_allocation(
        self,
        persona_id: int,
        asset_class: str,
        current_allocation: float
    ) -> PortfolioAllocation:
        """
        포트폴리오 배분 업데이트
        
        Args:
            persona_id: 페르소나 ID
            asset_class: 자산 클래스
            current_allocation: 현재 배분 비율
        
        Returns:
            업데이트된 PortfolioAllocation
        """
        # 기존 배분 조회
        allocation = self.db.query(PortfolioAllocation).filter(
            and_(
                PortfolioAllocation.persona_id == persona_id,
                PortfolioAllocation.asset_class == asset_class
            )
        ).first()
        
        if allocation:
            # 기존 배분 업데이트
            allocation.current_allocation = current_allocation
            allocation.deviation = abs(allocation.target_allocation - current_allocation)
            allocation.updated_at = datetime.now()
        else:
            # 새 배분 생성
            persona = self.db.query(Persona).filter(Persona.id == persona_id).first()
            if not persona:
                raise ValueError(f"Persona not found: {persona_id}")
            
            allocation = PortfolioAllocation(
                persona_id=persona_id,
                asset_class=asset_class,
                target_allocation=0.0,  # 기본값
                current_allocation=current_allocation,
                deviation=0.0,
            )
            self.db.add(allocation)
        
        self.db.commit()
        self.db.refresh(allocation)
        
        return allocation


# ============================================================================
# Helper Functions
# ============================================================================

def get_persona_integration_service(db: Session) -> PersonaIntegrationService:
    """
    Persona Integration Service 인스턴스 생성
    
    Args:
        db: SQLAlchemy database session
    
    Returns:
        PersonaIntegrationService 인스턴스
    """
    return PersonaIntegrationService(db)


# ============================================================================
# Test Code
# ============================================================================

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Test code (실제 사용 시에는 DB 연결 필요)
    print("=== Persona Integration Service Test ===")
    print("Service initialized successfully")
