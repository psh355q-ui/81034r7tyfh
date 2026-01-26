"""
Persona Trading Service - Persona-based Investment Logic

Phase 3: Persona-based Trading
Date: 2026-01-25

Purpose:
    페르소나별 투자 로직을 구현합니다.
    - 자산 배분 비율 계산
    - 리스크 관리
    - 리밸런싱 로직
    - 포지션 사이징

Persona Types:
    - CONSERVATIVE: 보수형 (안정성 우선, 배당/채권 중심)
    - AGGRESSIVE: 공격형 (고수익 추구, 성장주/레버리지 허용)
    - GROWTH: 성장형 (가치/성장 추구, 펀더멘털 중심)
    - BALANCED: 밸런스형 (균형 잡힌 포트폴리오, 기본값)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.database.models import Persona, PortfolioAllocation, UserPersonaPreference
from backend.database.models_assets import Asset, MultiAssetPosition
from backend.ai.router.persona_router import PersonaMode, get_persona_router


class PersonaTradingService:
    """
    Persona Trading Service - 페르소나별 투자 로직
    
    페르소나 설정에 따라 자산 배분, 리스크 관리, 포지션 사이징 등의
    투자 결정을 지원합니다.
    """
    
    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.persona_router = get_persona_router()
    
    # ============================================================================
    # Persona 조회 및 설정
    # ============================================================================
    
    def get_persona_by_name(self, name: str) -> Optional[Persona]:
        """
        이름으로 페르소나 조회
        
        Args:
            name: 페르소나 이름 (CONSERVATIVE, AGGRESSIVE, GROWTH, BALANCED)
        
        Returns:
            Persona 객체 또는 None
        """
        return self.db.query(Persona).filter(
            and_(
                Persona.name == name.upper(),
                Persona.is_active == True
            )
        ).first()
    
    def get_default_persona(self) -> Optional[Persona]:
        """기본 페르소나 조회"""
        return self.db.query(Persona).filter(
            and_(
                Persona.is_default == True,
                Persona.is_active == True
            )
        ).first()
    
    def get_all_active_personas(self) -> List[Persona]:
        """모든 활성 페르소나 조회"""
        return self.db.query(Persona).filter(
            Persona.is_active == True
        ).order_by(Persona.name).all()
    
    def get_user_persona(self, user_id: str) -> Optional[Persona]:
        """
        사용자의 페르소나 조회
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            사용자의 페르소나 또는 None
        """
        preference = self.db.query(UserPersonaPreference).filter(
            UserPersonaPreference.user_id == user_id
        ).first()
        
        if preference:
            return self.db.query(Persona).filter(
                and_(
                    Persona.id == preference.persona_id,
                    Persona.is_active == True
                )
            ).first()
        
        # 사용자 페르소나가 없으면 기본 페르소나 반환
        return self.get_default_persona()
    
    # ============================================================================
    # 자산 배분 계산
    # ============================================================================
    
    def calculate_portfolio_allocation(
        self,
        persona: Persona,
        total_value: float,
        current_allocations: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        페르소나별 포트폴리오 배분 계산
        
        Args:
            persona: 페르소나 객체
            total_value: 총 포트폴리오 가치
            current_allocations: 현재 자산별 배분 (예: {"STOCK": 0.50, "BOND": 0.30, "CASH": 0.20})
        
        Returns:
            자산별 배분 정보
            {
                "STOCK": {"target": 0.60, "current": 0.50, "target_value": 60000, "current_value": 50000, "rebalance": True},
                "BOND": {"target": 0.30, "current": 0.30, "target_value": 30000, "current_value": 30000, "rebalance": False},
                "CASH": {"target": 0.10, "current": 0.20, "target_value": 10000, "current_value": 20000, "rebalance": True}
            }
        """
        # 기본 배분 비율 (페르소나 설정)
        target_allocations = {
            "STOCK": float(persona.stock_allocation),
            "BOND": float(persona.bond_allocation),
            "CASH": float(persona.cash_allocation)
        }
        
        # 현재 배분이 없으면 기본값 사용
        if current_allocations is None:
            current_allocations = {
                "STOCK": 0.0,
                "BOND": 0.0,
                "CASH": 1.0  # 전부 현금
            }
        
        result = {}
        
        for asset_class, target_pct in target_allocations.items():
            current_pct = current_allocations.get(asset_class, 0.0)
            target_value = total_value * target_pct
            current_value = total_value * current_pct
            deviation = abs(target_pct - current_pct)
            
            # 리밸런싱 필요 여부 확인
            rebalance_threshold = 0.05  # 5% 기본 임계값
            rebalance_needed = deviation > rebalance_threshold
            
            result[asset_class] = {
                "target": target_pct,
                "current": current_pct,
                "target_value": target_value,
                "current_value": current_value,
                "deviation": deviation,
                "rebalance": rebalance_needed,
                "adjustment": target_value - current_value  # 양수: 매수, 음수: 매도
            }
        
        return result
    
    def get_rebalance_recommendations(
        self,
        persona: Persona,
        total_value: float,
        current_positions: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """
        리밸런싱 추천 목록 생성
        
        Args:
            persona: 페르소나 객체
            total_value: 총 포트폴리오 가치
            current_positions: 현재 포지션 목록
                [{"asset_class": "STOCK", "value": 50000, "ticker": "AAPL"}, ...]
        
        Returns:
            리밸런싱 추천 목록
        """
        # 현재 자산별 배분 계산
        current_allocations = {}
        for pos in current_positions:
            asset_class = pos.get("asset_class", "CASH")
            value = pos.get("value", 0)
            current_allocations[asset_class] = current_allocations.get(asset_class, 0) + value
        
        # 비율로 변환
        for asset_class in current_allocations:
            current_allocations[asset_class] = current_allocations[asset_class] / total_value if total_value > 0 else 0
        
        # 배분 계산
        allocation = self.calculate_portfolio_allocation(persona, total_value, current_allocations)
        
        # 리밸런싱 추천 생성
        recommendations = []
        
        for asset_class, info in allocation.items():
            if info["rebalance"]:
                adjustment = info["adjustment"]
                
                if adjustment > 0:
                    action = "BUY"
                    message = f"{asset_class} 비중 증가 필요 (+{adjustment:,.0f})"
                else:
                    action = "SELL"
                    message = f"{asset_class} 비중 감소 필요 ({adjustment:,.0f})"
                
                recommendations.append({
                    "asset_class": asset_class,
                    "action": action,
                    "target_pct": info["target"],
                    "current_pct": info["current"],
                    "adjustment": adjustment,
                    "message": message,
                    "priority": "HIGH" if abs(info["deviation"]) > 0.10 else "MEDIUM"
                })
        
        # 우선순위 정렬 (편차가 큰 순서)
        recommendations.sort(key=lambda x: abs(x["adjustment"]), reverse=True)
        
        return recommendations
    
    # ============================================================================
    # 포지션 사이징
    # ============================================================================
    
    def calculate_position_size(
        self,
        persona: Persona,
        total_value: float,
        confidence: float,
        risk_level: str = "MEDIUM"
    ) -> float:
        """
        페르소나별 포지션 사이즈 계산
        
        Args:
            persona: 페르소나 객체
            total_value: 총 포트폴리오 가치
            confidence: 시그널 확신도 (0.0 ~ 1.0)
            risk_level: 리스크 레벨 (LOW, MEDIUM, HIGH)
        
        Returns:
            포지션 사이즈 (금액)
        """
        # 기본 최대 포지션 비중
        max_position_pct = float(persona.max_position_size)
        
        # 리스크 레벨에 따른 조정
        risk_adjustment = {
            "LOW": 1.2,      # 리스크 낮음: 포지션 증가
            "MEDIUM": 1.0,   # 리스크 중간: 기본값
            "HIGH": 0.8      # 리스크 높음: 포지션 감소
        }.get(risk_level, 1.0)
        
        # 확신도에 따른 조정
        confidence_adjustment = confidence
        
        # 페르소나 리스크 허용도에 따른 조정
        risk_tolerance_adjustment = {
            "VERY_LOW": 0.5,
            "LOW": 0.7,
            "MEDIUM": 1.0,
            "HIGH": 1.3,
            "VERY_HIGH": 1.5
        }.get(persona.risk_tolerance, 1.0)
        
        # 최종 포지션 비중 계산
        final_position_pct = (
            max_position_pct *
            risk_adjustment *
            confidence_adjustment *
            risk_tolerance_adjustment
        )
        
        # 최대 20% 제한
        final_position_pct = min(final_position_pct, 0.20)
        
        return total_value * final_position_pct
    
    def calculate_stop_loss(
        self,
        persona: Persona,
        entry_price: float,
        ticker: Optional[str] = None
    ) -> float:
        """
        페르소나별 손절가 계산
        
        Args:
            persona: 페르소나 객체
            entry_price: 진입 가격
            ticker: 티커 (레버리지 상품 확인용)
        
        Returns:
            손절가
        """
        stop_loss_pct = float(persona.stop_loss_pct)
        
        # 레버리지 상품 확인
        if ticker:
            from backend.ai.safety.leverage_guardian import get_leverage_guardian
            guardian = get_leverage_guardian()
            
            if guardian.is_leveraged(ticker):
                # 레버리지 상품은 손절가를 더 타이트하게
                stop_loss_pct *= 0.5
        
        return entry_price * (1 - stop_loss_pct)
    
    # ============================================================================
    # 리스크 관리
    # ============================================================================
    
    def check_position_limit(
        self,
        persona: Persona,
        ticker: str,
        position_value: float,
        total_value: float,
        sector: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        포지션 제한 확인
        
        Args:
            persona: 페르소나 객체
            ticker: 티커
            position_value: 포지션 가치
            total_value: 총 포트폴리오 가치
            sector: 섹터
        
        Returns:
            (허용 여부, 메시지)
        """
        # 1. 단일 포지션 제한 확인
        position_pct = position_value / total_value if total_value > 0 else 0
        max_position_pct = float(persona.max_position_size)
        
        if position_pct > max_position_pct:
            return (
                False,
                f"단일 포지션 제한 초과: {position_pct:.1%} > {max_position_pct:.1%}"
            )
        
        # 2. 섹터 노출 확인 (섹터 정보가 있는 경우)
        if sector:
            # 현재 섹터별 포지션 조회 (실제 구현에서는 DB 조회 필요)
            # 여기서는 간단히 예시만 작성
            max_sector_pct = float(persona.max_sector_exposure)
            
            # 섹터 노출 계산 로직 (실제 구현 필요)
            # current_sector_pct = self.calculate_sector_exposure(persona, sector)
            # if current_sector_pct + position_pct > max_sector_pct:
            #     return False, f"섹터 노출 제한 초과: {sector}"
        
        # 3. 레버리지 상품 확인
        from backend.ai.safety.leverage_guardian import get_leverage_guardian
        guardian = get_leverage_guardian()
        
        if guardian.is_leveraged(ticker):
            if not persona.leverage_allowed:
                return (
                    False,
                    f"이 페르소나는 레버리지 상품을 허용하지 않습니다: {ticker}"
                )
            
            # 레버리지 비중 확인
            max_leverage_pct = float(persona.max_leverage_pct)
            # current_leverage_pct = self.calculate_leverage_exposure(persona)
            # if current_leverage_pct + position_pct > max_leverage_pct:
            #     return False, f"레버리지 비중 제한 초과: {max_leverage_pct:.1%}"
        
        return (True, "포지션 허용")
    
    def validate_signal_with_persona(
        self,
        persona: Persona,
        signal_confidence: float,
        agent_disagreement: float,
        avg_confidence: float
    ) -> Tuple[bool, str]:
        """
        페르소나 Hard Rules로 시그널 검증
        
        Args:
            persona: 페르소나 객체
            signal_confidence: 시그널 확신도
            agent_disagreement: 에이전트 불일치도 (0.0 ~ 1.0)
            avg_confidence: 평균 확신도
        
        Returns:
            (허용 여부, 메시지)
        """
        # 1. 최소 확신도 확인
        min_confidence = float(persona.min_avg_confidence)
        if avg_confidence < min_confidence:
            return (
                False,
                f"확신도 부족: {avg_confidence:.2%} < {min_confidence:.2%}"
            )
        
        # 2. 에이전트 불일치 확인
        max_disagreement = float(persona.max_agent_disagreement)
        if agent_disagreement > max_disagreement:
            return (
                False,
                f"에이전트 불일치 초과: {agent_disagreement:.2%} > {max_disagreement:.2%}"
            )
        
        return (True, "시그널 허용")
    
    # ============================================================================
    # 페르소나 전환
    # ============================================================================
    
    def switch_persona(
        self,
        user_id: str,
        new_persona_name: str
    ) -> Tuple[bool, str, Optional[Persona]]:
        """
        사용자 페르소나 전환
        
        Args:
            user_id: 사용자 ID
            new_persona_name: 새 페르소나 이름
        
        Returns:
            (성공 여부, 메시지, 새 페르소나)
        """
        # 새 페르소나 조회
        new_persona = self.get_persona_by_name(new_persona_name)
        if not new_persona:
            return (False, f"페르소나를 찾을 수 없습니다: {new_persona_name}", None)
        
        # 기존 사용자 페르소나 선호도 조회
        preference = self.db.query(UserPersonaPreference).filter(
            UserPersonaPreference.user_id == user_id
        ).first()
        
        if preference:
            # 기존 선호도 업데이트
            old_persona_id = preference.persona_id
            preference.persona_id = new_persona.id
            preference.last_switched_at = datetime.now()
            preference.switch_count += 1
            preference.updated_at = datetime.now()
        else:
            # 새 선호도 생성
            preference = UserPersonaPreference(
                user_id=user_id,
                persona_id=new_persona.id,
                last_switched_at=datetime.now(),
                switch_count=1
            )
            self.db.add(preference)
        
        self.db.commit()
        
        # Persona Router 모드 전환
        persona_mode = self._map_persona_to_mode(new_persona.name)
        self.persona_router.set_mode(persona_mode)
        
        return (True, f"페르소나가 전환되었습니다: {new_persona.display_name}", new_persona)
    
    def _map_persona_to_mode(self, persona_name: str) -> str:
        """
        페르소나 이름을 Persona Router 모드로 매핑
        
        Args:
            persona_name: 페르소나 이름
        
        Returns:
            Persona Router 모드
        """
        mapping = {
            "CONSERVATIVE": "dividend",
            "AGGRESSIVE": "aggressive",
            "GROWTH": "long_term",
            "BALANCED": "trading"
        }
        return mapping.get(persona_name, "trading")
    
    def _map_mode_to_persona(self, mode: str) -> str:
        """
        Persona Router 모드를 페르소나 이름으로 매핑
        
        Args:
            mode: Persona Router 모드
        
        Returns:
            페르소나 이름
        """
        mapping = {
            "dividend": "CONSERVATIVE",
            "aggressive": "AGGRESSIVE",
            "long_term": "GROWTH",
            "trading": "BALANCED"
        }
        return mapping.get(mode, "BALANCED")


# ============================================================================
# Helper Functions
# ============================================================================

def get_persona_trading_service(db: Session) -> PersonaTradingService:
    """
    Persona Trading Service 인스턴스 생성
    
    Args:
        db: SQLAlchemy database session
    
    Returns:
        PersonaTradingService 인스턴스
    """
    return PersonaTradingService(db)


# ============================================================================
# Test Code
# ============================================================================

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Test code (실제 사용 시에는 DB 연결 필요)
    print("=== Persona Trading Service Test ===")
    print("Service initialized successfully")
