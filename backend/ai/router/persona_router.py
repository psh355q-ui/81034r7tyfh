"""
Persona Router - Dynamic Mode Switching for AI Trading System

Phase: Phase 4.1 - Grand Unified Strategy
Date: 2026-01-05

Purpose:
    사용자의 투자 페르소나(모드)에 따라 War Room MVP Agent 가중치를 동적으로 조절합니다.
    마치 하나의 엔진으로 4개의 다른 AI처럼 동작하게 합니다.

Modes:
    - DIVIDEND: 배당/안정 추구 (Analyst++, Risk++, Trader--)
    - LONG_TERM: 가치/성장 추구 (Analyst+++, Risk+, Trader--)
    - TRADING: 단기/모멘텀 (기존 기본값)
    - AGGRESSIVE: 레버리지/헤지 (Trader++, Risk-, Analyst--)

Usage:
    router = PersonaRouter()
    weights = router.get_weights("DIVIDEND")
    # Returns: {"trader_mvp": 0.10, "risk_mvp": 0.40, "analyst_mvp": 0.50}
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class PersonaMode(str, Enum):
    """사용자 투자 페르소나 모드"""
    DIVIDEND = "dividend"       # 배당/안정 추구
    LONG_TERM = "long_term"     # 가치/성장 추구
    TRADING = "trading"         # 단기/모멘텀 (기본)
    AGGRESSIVE = "aggressive"   # 레버리지/헤지 (위험)


@dataclass
class PersonaConfig:
    """페르소나별 설정"""
    mode: PersonaMode
    weights: Dict[str, float]
    features: Dict[str, bool]
    description: str


# 페르소나별 Agent 가중치 정의
PERSONA_WEIGHTS: Dict[PersonaMode, Dict[str, float]] = {
    PersonaMode.DIVIDEND: {
        "trader_mvp": 0.10,   # 기술적 분석 최소화
        "risk_mvp": 0.40,     # 안정성 강화
        "analyst_mvp": 0.50,  # 펀더멘털 중심 (배당 분석 포함)
    },
    PersonaMode.LONG_TERM: {
        "trader_mvp": 0.15,   # 모멘텀 참고만
        "risk_mvp": 0.25,     # 리스크 적당히
        "analyst_mvp": 0.60,  # 가치/성장 분석 최대화
    },
    PersonaMode.TRADING: {
        "trader_mvp": 0.35,   # 기존 기본값
        "risk_mvp": 0.35,
        "analyst_mvp": 0.30,
    },
    PersonaMode.AGGRESSIVE: {
        "trader_mvp": 0.50,   # 공격적 포착
        "risk_mvp": 0.30,     # 리스크 축소 (단, Leverage Guardian 활성화)
        "analyst_mvp": 0.20,
    },
}

# 페르소나별 활성화 기능
PERSONA_FEATURES: Dict[PersonaMode, Dict[str, bool]] = {
    PersonaMode.DIVIDEND: {
        "yield_trap_detector": True,
        "dividend_calendar": True,
        "noise_filter": True,
        "leverage_guardian": False,  # 배당 모드에서는 레버리지 금지
        "thesis_violation": False,
    },
    PersonaMode.LONG_TERM: {
        "yield_trap_detector": False,
        "dividend_calendar": False,
        "noise_filter": True,         # 노이즈 필터링 활성화
        "leverage_guardian": False,   # 장기 모드에서도 레버리지 금지
        "thesis_violation": True,     # 투자 아이디어 훼손 감지
    },
    PersonaMode.TRADING: {
        "yield_trap_detector": False,
        "dividend_calendar": False,
        "noise_filter": False,
        "leverage_guardian": False,
        "thesis_violation": False,
    },
    PersonaMode.AGGRESSIVE: {
        "yield_trap_detector": False,
        "dividend_calendar": False,
        "noise_filter": False,
        "leverage_guardian": True,    # 레버리지 10% 제한 활성화
        "thesis_violation": False,
    },
}

# 페르소나별 설명
PERSONA_DESCRIPTIONS: Dict[PersonaMode, str] = {
    PersonaMode.DIVIDEND: "배당/안정 추구: 현금흐름 최적화, Yield Trap 방지",
    PersonaMode.LONG_TERM: "가치/성장 투자: 펀더멘털 중심, 노이즈 필터링",
    PersonaMode.TRADING: "단기 트레이딩: 모멘텀/뉴스 기반 빠른 의사결정",
    PersonaMode.AGGRESSIVE: "공격적 투자: 레버리지 허용 (10% 제한), FOMO 제어",
}


class PersonaRouter:
    """
    Persona Router - 사용자 모드에 따른 동적 가중치 및 기능 전환
    
    War Room MVP 엔진과 연동하여, 동일한 입력에 대해
    페르소나에 따라 다른 분석 가중치를 적용합니다.
    """
    
    def __init__(self, default_mode: PersonaMode = PersonaMode.TRADING):
        """
        Args:
            default_mode: 기본 페르소나 모드 (기본값: TRADING)
        """
        self.default_mode = default_mode
        self._current_mode: PersonaMode = default_mode
    
    def get_weights(self, mode: Optional[str] = None) -> Dict[str, float]:
        """
        지정된 모드(또는 현재 모드)에 대한 Agent 가중치 반환
        
        Args:
            mode: 페르소나 모드 문자열 (예: "dividend", "long_term")
                  None이면 현재 모드 사용
        
        Returns:
            Dict[str, float]: Agent별 가중치
            예: {"trader_mvp": 0.35, "risk_mvp": 0.35, "analyst_mvp": 0.30}
        """
        persona = self._resolve_mode(mode)
        return PERSONA_WEIGHTS.get(persona, PERSONA_WEIGHTS[PersonaMode.TRADING])
    
    def get_features(self, mode: Optional[str] = None) -> Dict[str, bool]:
        """
        지정된 모드에 대한 활성화 기능 목록 반환
        
        Args:
            mode: 페르소나 모드 문자열
        
        Returns:
            Dict[str, bool]: 기능별 활성화 여부
        """
        persona = self._resolve_mode(mode)
        return PERSONA_FEATURES.get(persona, PERSONA_FEATURES[PersonaMode.TRADING])
    
    def get_config(self, mode: Optional[str] = None) -> PersonaConfig:
        """
        지정된 모드에 대한 전체 설정 반환
        
        Args:
            mode: 페르소나 모드 문자열
        
        Returns:
            PersonaConfig: 모드, 가중치, 기능, 설명 포함
        """
        persona = self._resolve_mode(mode)
        return PersonaConfig(
            mode=persona,
            weights=PERSONA_WEIGHTS.get(persona, PERSONA_WEIGHTS[PersonaMode.TRADING]),
            features=PERSONA_FEATURES.get(persona, PERSONA_FEATURES[PersonaMode.TRADING]),
            description=PERSONA_DESCRIPTIONS.get(persona, "")
        )
    
    def set_mode(self, mode: str) -> PersonaMode:
        """
        현재 모드를 변경
        
        Args:
            mode: 새로운 페르소나 모드 문자열
        
        Returns:
            PersonaMode: 변경된 모드
        """
        self._current_mode = self._resolve_mode(mode)
        return self._current_mode
    
    def get_current_mode(self) -> PersonaMode:
        """현재 모드 반환"""
        return self._current_mode
    
    def _resolve_mode(self, mode: Optional[str]) -> PersonaMode:
        """
        문자열 모드를 PersonaMode enum으로 변환
        
        Args:
            mode: 모드 문자열 또는 None
        
        Returns:
            PersonaMode: 해당 enum 값 (없으면 현재 모드)
        """
        if mode is None:
            return self._current_mode
        
        # 문자열을 enum으로 변환
        mode_lower = mode.lower().strip()
        for persona in PersonaMode:
            if persona.value == mode_lower:
                return persona
        
        # 매칭 실패 시 기본 모드 반환
        return self._current_mode
    
    def is_leverage_allowed(self, mode: Optional[str] = None) -> bool:
        """
        해당 모드에서 레버리지 사용 가능 여부
        
        Note: AGGRESSIVE 모드에서만 레버리지 사용 가능 (10% 제한)
        """
        features = self.get_features(mode)
        # leverage_guardian이 True면 레버리지 허용 (단, 제한 적용)
        # False면 레버리지 금지
        return features.get("leverage_guardian", False)
    
    def get_leverage_cap(self, mode: Optional[str] = None) -> float:
        """
        레버리지 상품 최대 허용 비율 (전체 자산 대비)
        
        Returns:
            float: 레버리지 허용 비율 (예: 0.1 = 10%)
                   레버리지 금지 모드는 0.0 반환
        """
        if self.is_leverage_allowed(mode):
            return 0.10  # 10% cap for aggressive mode
        return 0.0


# 싱글톤 인스턴스 (전역 사용 가능)
_default_router: Optional[PersonaRouter] = None


def get_persona_router() -> PersonaRouter:
    """전역 PersonaRouter 인스턴스 반환"""
    global _default_router
    if _default_router is None:
        _default_router = PersonaRouter()
    return _default_router


# 테스트용
if __name__ == "__main__":
    router = PersonaRouter()
    
    print("=== Persona Router Test ===\n")
    
    for mode in PersonaMode:
        config = router.get_config(mode.value)
        print(f"📊 {mode.value.upper()}")
        print(f"   설명: {config.description}")
        print(f"   가중치: {config.weights}")
        print(f"   기능: {config.features}")
        print(f"   레버리지: {'허용 (10% 제한)' if router.is_leverage_allowed(mode.value) else '금지'}")
        print()
