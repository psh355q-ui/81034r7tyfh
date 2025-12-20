"""
AI Role Manager - AI 역할 계층화 관리 시스템

Phase F1: AI 집단지성 고도화

각 AI 에이전트에 특화된 역할을 부여하여 토론과 의사결정의 품질을 높임

역할 정의:
- Macro Strategist: 거시 환경 분석 (금리, 매크로 이벤트)
- Sector Specialist: 섹터 로테이션 및 밸류체인 분석
- Risk Controller: 리스크 관리 및 경고
- Execution Optimizer: 타이밍 및 체결 최적화
- Devil's Advocate: 반대 논리 전용

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# AI 역할 정의
# ═══════════════════════════════════════════════════════════════

class AIRole(str, Enum):
    """AI 에이전트 역할 타입"""
    MACRO_STRATEGIST = "macro_strategist"      # 거시 환경 담당
    SECTOR_SPECIALIST = "sector_specialist"    # 섹터 로테이션 담당
    RISK_CONTROLLER = "risk_controller"        # 리스크 관리 전용
    EXECUTION_OPTIMIZER = "execution_optimizer"  # 타이밍/체결 최적화
    DEVILS_ADVOCATE = "devils_advocate"        # 반대 논리 전용
    GENERAL_ANALYST = "general_analyst"        # 범용 분석


class AIAgentType(str, Enum):
    """AI 에이전트 타입 (실제 모델)"""
    CLAUDE = "claude"
    CHATGPT = "chatgpt"
    GEMINI = "gemini"


@dataclass
class RoleConfig:
    """역할별 설정"""
    role: AIRole
    description: str
    focus_areas: List[str]
    prompt_prefix: str
    weight_multiplier: float = 1.0
    is_contrarian: bool = False  # 반대 의견 역할인지
    

@dataclass
class AgentAssignment:
    """에이전트-역할 할당"""
    agent_type: AIAgentType
    primary_role: AIRole
    secondary_roles: List[AIRole] = field(default_factory=list)
    current_weight: float = 1.0
    performance_score: float = 0.5
    assigned_at: datetime = field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════
# 역할별 기본 설정
# ═══════════════════════════════════════════════════════════════

DEFAULT_ROLE_CONFIGS: Dict[AIRole, RoleConfig] = {
    AIRole.MACRO_STRATEGIST: RoleConfig(
        role=AIRole.MACRO_STRATEGIST,
        description="거시 경제 환경 분석 전문가",
        focus_areas=[
            "금리 정책 (Fed, BOJ, ECB)",
            "인플레이션/디플레이션 추세",
            "글로벌 유동성 흐름",
            "지정학적 리스크",
            "통화 강세/약세"
        ],
        prompt_prefix="""당신은 거시 경제 전략가입니다. 
글로벌 매크로 환경이 해당 투자에 미치는 영향을 중점적으로 분석하세요.
금리, 인플레이션, 글로벌 자금 흐름, 지정학적 리스크를 특히 고려하세요.""",
        weight_multiplier=1.2
    ),
    
    AIRole.SECTOR_SPECIALIST: RoleConfig(
        role=AIRole.SECTOR_SPECIALIST,
        description="섹터 및 밸류체인 분석 전문가",
        focus_areas=[
            "섹터 로테이션 추세",
            "밸류체인 연관 관계",
            "경쟁사 동향",
            "수급/재고 사이클",
            "기술 트렌드"
        ],
        prompt_prefix="""당신은 섹터 전문가입니다.
해당 종목의 섹터 내 위치, 밸류체인 관계, 경쟁 구도를 중점적으로 분석하세요.
공급망 리스크와 섹터 로테이션 가능성을 특히 고려하세요.""",
        weight_multiplier=1.1
    ),
    
    AIRole.RISK_CONTROLLER: RoleConfig(
        role=AIRole.RISK_CONTROLLER,
        description="리스크 관리 전문가",
        focus_areas=[
            "하방 리스크 시나리오",
            "변동성 분석",
            "유동성 리스크",
            "테일 리스크",
            "포지션 사이징"
        ],
        prompt_prefix="""당신은 리스크 관리자입니다.
투자의 잠재적 위험 요소와 손실 시나리오를 중점적으로 분석하세요.
최악의 경우를 가정하고, 리스크/리워드 비율을 냉정하게 평가하세요.
손절 기준과 포지션 사이징을 반드시 제안하세요.""",
        weight_multiplier=1.3  # 리스크 관리자는 더 높은 가중치
    ),
    
    AIRole.EXECUTION_OPTIMIZER: RoleConfig(
        role=AIRole.EXECUTION_OPTIMIZER,
        description="체결 최적화 전문가",
        focus_areas=[
            "진입/청산 타이밍",
            "호가창 분석",
            "슬리피지 최소화",
            "분할 매수/매도",
            "시장 미시구조"
        ],
        prompt_prefix="""당신은 체결 최적화 전문가입니다.
최적의 진입/청산 타이밍과 방법을 중점적으로 분석하세요.
시장 유동성, 호가 스프레드, 분할 체결 전략을 고려하세요.""",
        weight_multiplier=0.8
    ),
    
    AIRole.DEVILS_ADVOCATE: RoleConfig(
        role=AIRole.DEVILS_ADVOCATE,
        description="반대 논리 전문가 (Devil's Advocate)",
        focus_areas=[
            "다수 의견의 허점",
            "간과된 리스크",
            "역발상 시나리오",
            "편향 검증",
            "대안적 해석"
        ],
        prompt_prefix="""당신은 Devil's Advocate입니다.
다른 분석가들의 의견에 대한 반론을 제시하는 것이 당신의 역할입니다.
강제로 반대 논거를 찾고, 간과된 리스크와 허점을 지적하세요.
다수가 낙관적이면 비관적 시나리오를, 비관적이면 낙관적 시나리오를 제시하세요.""",
        weight_multiplier=0.7,
        is_contrarian=True
    ),
    
    AIRole.GENERAL_ANALYST: RoleConfig(
        role=AIRole.GENERAL_ANALYST,
        description="범용 분석가",
        focus_areas=[
            "종합 분석",
            "밸류에이션",
            "실적 전망",
            "뉴스 해석",
            "트렌드 분석"
        ],
        prompt_prefix="""당신은 투자 분석가입니다.
해당 투자 기회를 종합적으로 분석하고 권고안을 제시하세요.""",
        weight_multiplier=1.0
    )
}


# ═══════════════════════════════════════════════════════════════
# AI Role Manager 클래스
# ═══════════════════════════════════════════════════════════════

class AIRoleManager:
    """
    AI 역할 관리자
    
    각 AI 에이전트에 역할을 할당하고, 역할에 따른 프롬프트 및 가중치 관리
    
    Usage:
        manager = AIRoleManager()
        
        # 역할 할당
        manager.assign_role(AIAgentType.CLAUDE, AIRole.RISK_CONTROLLER)
        manager.assign_role(AIAgentType.CHATGPT, AIRole.SECTOR_SPECIALIST)
        manager.assign_role(AIAgentType.GEMINI, AIRole.MACRO_STRATEGIST)
        
        # 역할별 프롬프트 가져오기
        prompt = manager.get_role_prompt(AIAgentType.CLAUDE)
        
        # 현재 할당 상태 조회
        assignments = manager.get_all_assignments()
    """
    
    def __init__(self):
        self.role_configs: Dict[AIRole, RoleConfig] = DEFAULT_ROLE_CONFIGS.copy()
        self.assignments: Dict[AIAgentType, AgentAssignment] = {}
        self._history: List[Dict[str, Any]] = []
        
        # 기본 할당 설정
        self._setup_default_assignments()
        
        logger.info("AIRoleManager initialized with default assignments")
    
    def _setup_default_assignments(self):
        """기본 역할 할당"""
        # Claude: 리스크 관리자 (보수적 성향 활용)
        self.assignments[AIAgentType.CLAUDE] = AgentAssignment(
            agent_type=AIAgentType.CLAUDE,
            primary_role=AIRole.RISK_CONTROLLER,
            secondary_roles=[AIRole.GENERAL_ANALYST]
        )
        
        # ChatGPT: 섹터 전문가 (분석적 성향 활용)
        self.assignments[AIAgentType.CHATGPT] = AgentAssignment(
            agent_type=AIAgentType.CHATGPT,
            primary_role=AIRole.SECTOR_SPECIALIST,
            secondary_roles=[AIRole.MACRO_STRATEGIST]
        )
        
        # Gemini: 매크로 전략가 (빠른 검색/분석 활용)
        self.assignments[AIAgentType.GEMINI] = AgentAssignment(
            agent_type=AIAgentType.GEMINI,
            primary_role=AIRole.MACRO_STRATEGIST,
            secondary_roles=[AIRole.DEVILS_ADVOCATE]
        )
    
    def assign_role(
        self, 
        agent_type: AIAgentType, 
        primary_role: AIRole,
        secondary_roles: Optional[List[AIRole]] = None
    ) -> AgentAssignment:
        """
        에이전트에 역할 할당
        
        Args:
            agent_type: AI 에이전트 타입
            primary_role: 주 역할
            secondary_roles: 보조 역할 목록
            
        Returns:
            AgentAssignment: 할당 결과
        """
        assignment = AgentAssignment(
            agent_type=agent_type,
            primary_role=primary_role,
            secondary_roles=secondary_roles or []
        )
        
        old_assignment = self.assignments.get(agent_type)
        self.assignments[agent_type] = assignment
        
        # 히스토리 기록
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "assign_role",
            "agent": agent_type.value,
            "old_role": old_assignment.primary_role.value if old_assignment else None,
            "new_role": primary_role.value
        })
        
        logger.info(f"Assigned role {primary_role.value} to {agent_type.value}")
        return assignment
    
    def get_assignment(self, agent_type: AIAgentType) -> Optional[AgentAssignment]:
        """에이전트의 현재 역할 할당 조회"""
        return self.assignments.get(agent_type)
    
    def get_all_assignments(self) -> Dict[AIAgentType, AgentAssignment]:
        """모든 역할 할당 조회"""
        return self.assignments.copy()
    
    def get_role_config(self, role: AIRole) -> RoleConfig:
        """역할 설정 조회"""
        return self.role_configs[role]
    
    def get_role_prompt(self, agent_type: AIAgentType) -> str:
        """
        에이전트의 역할에 맞는 프롬프트 프리픽스 반환
        
        Args:
            agent_type: AI 에이전트 타입
            
        Returns:
            str: 역할 기반 프롬프트 프리픽스
        """
        assignment = self.assignments.get(agent_type)
        if not assignment:
            return ""
        
        config = self.role_configs.get(assignment.primary_role)
        if not config:
            return ""
        
        return config.prompt_prefix
    
    def get_agent_weight(self, agent_type: AIAgentType) -> float:
        """
        에이전트의 투표 가중치 계산
        
        역할 기반 가중치 * 성과 기반 가중치
        """
        assignment = self.assignments.get(agent_type)
        if not assignment:
            return 1.0
        
        role_config = self.role_configs.get(assignment.primary_role)
        role_multiplier = role_config.weight_multiplier if role_config else 1.0
        
        # 성과 기반 조정 (0.5 ~ 1.5)
        performance_multiplier = 0.5 + assignment.performance_score
        
        return assignment.current_weight * role_multiplier * performance_multiplier
    
    def update_performance(
        self, 
        agent_type: AIAgentType, 
        correct_prediction: bool,
        pnl_result: Optional[float] = None
    ):
        """
        에이전트 성과 업데이트
        
        Args:
            agent_type: AI 에이전트 타입
            correct_prediction: 예측 정확성
            pnl_result: 실현 손익 (선택)
        """
        assignment = self.assignments.get(agent_type)
        if not assignment:
            return
        
        # EMA 방식으로 성과 점수 업데이트
        alpha = 0.1  # 학습률
        prediction_score = 1.0 if correct_prediction else 0.0
        
        if pnl_result is not None:
            # PnL 기반 추가 점수 (0~1 사이로 정규화)
            pnl_score = max(0, min(1, (pnl_result + 10) / 20))
            score = (prediction_score + pnl_score) / 2
        else:
            score = prediction_score
        
        assignment.performance_score = (
            (1 - alpha) * assignment.performance_score + alpha * score
        )
        
        logger.debug(
            f"Updated {agent_type.value} performance: {assignment.performance_score:.3f}"
        )
    
    def get_agents_by_role(self, role: AIRole) -> List[AIAgentType]:
        """특정 역할을 가진 에이전트 목록 반환"""
        agents = []
        for agent_type, assignment in self.assignments.items():
            if assignment.primary_role == role or role in assignment.secondary_roles:
                agents.append(agent_type)
        return agents
    
    def get_contrarian_agents(self) -> List[AIAgentType]:
        """반대 의견 역할을 가진 에이전트 목록"""
        contrarian_agents = []
        for agent_type, assignment in self.assignments.items():
            role_config = self.role_configs.get(assignment.primary_role)
            if role_config and role_config.is_contrarian:
                contrarian_agents.append(agent_type)
        return contrarian_agents
    
    def rotate_roles(self):
        """
        역할 로테이션 (성과 기반)
        
        성과가 낮은 에이전트에게 새로운 역할 부여하여 학습 기회 제공
        """
        # 성과 기준 정렬
        sorted_agents = sorted(
            self.assignments.items(),
            key=lambda x: x[1].performance_score
        )
        
        if len(sorted_agents) < 2:
            return
        
        # 최저 성과와 최고 성과 에이전트의 역할 교환
        lowest = sorted_agents[0]
        highest = sorted_agents[-1]
        
        # 역할 교환
        lowest_role = lowest[1].primary_role
        highest_role = highest[1].primary_role
        
        self.assign_role(lowest[0], highest_role)
        self.assign_role(highest[0], lowest_role)
        
        logger.info(
            f"Rotated roles: {lowest[0].value} -> {highest_role.value}, "
            f"{highest[0].value} -> {lowest_role.value}"
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """현재 상태 요약"""
        return {
            "assignments": {
                agent.value: {
                    "primary_role": assignment.primary_role.value,
                    "secondary_roles": [r.value for r in assignment.secondary_roles],
                    "weight": self.get_agent_weight(agent),
                    "performance_score": assignment.performance_score
                }
                for agent, assignment in self.assignments.items()
            },
            "total_agents": len(self.assignments),
            "history_count": len(self._history)
        }


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_role_manager: Optional[AIRoleManager] = None


def get_role_manager() -> AIRoleManager:
    """AIRoleManager 싱글톤 인스턴스"""
    global _role_manager
    if _role_manager is None:
        _role_manager = AIRoleManager()
    return _role_manager


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 테스트
    manager = get_role_manager()
    
    print("=== AI Role Manager Test ===\n")
    
    # 현재 할당 상태
    print("Current Assignments:")
    summary = manager.get_summary()
    for agent, info in summary["assignments"].items():
        print(f"  {agent}: {info['primary_role']} (weight: {info['weight']:.2f})")
    
    print("\n" + "="*50)
    
    # 역할별 프롬프트
    print("\nRole Prompts:")
    for agent_type in AIAgentType:
        prompt = manager.get_role_prompt(agent_type)
        print(f"\n[{agent_type.value}]")
        print(prompt[:100] + "..." if len(prompt) > 100 else prompt)
    
    print("\n" + "="*50)
    
    # 성과 업데이트 테스트
    print("\nPerformance Update Test:")
    manager.update_performance(AIAgentType.CLAUDE, True, pnl_result=5.0)
    manager.update_performance(AIAgentType.CHATGPT, False, pnl_result=-3.0)
    manager.update_performance(AIAgentType.GEMINI, True, pnl_result=2.0)
    
    summary = manager.get_summary()
    for agent, info in summary["assignments"].items():
        print(f"  {agent}: score={info['performance_score']:.3f}, weight={info['weight']:.2f}")
