"""
Amendment Mode - 헌법 개정 모드

입법(Legislation)과 위변조(Tampering) 구분

작성일: 2025-12-15
버전: 2.1.0
"""

from enum import Enum
from datetime import datetime
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class ConstitutionMode(Enum):
    """
    헌법 모드
    
    NORMAL: 정상 운용 (엄격한 무결성 검증)
    AMENDMENT: 개정 모드 (변경 허용, 로깅 필수)
    """
    
    NORMAL = "normal"
    """정상 운용 모드 - 헌법 변경 시 System Freeze"""
    
    AMENDMENT = "amendment"
    """개정 모드 - 헌법 변경 허용 (개정 절차 진행 중)"""


class AmendmentLog:
    """
    헌법 개정 기록
    
    모든 헌법 개정은 반드시 기록되어야 함
    """
    
    def __init__(
        self,
        version: str,
        files_changed: list[str],
        reason: str,
        author: str,
        timestamp: datetime
    ):
        """
        Args:
            version: 새 헌법 버전 (예: "2.0.2")
            files_changed: 수정된 파일 목록
            reason: 개정 이유
            author: 개정 승인자
            timestamp: 개정 시각
        """
        self.version = version
        self.files_changed = files_changed
        self.reason = reason
        self.author = author
        self.timestamp = timestamp
    
    def to_dict(self) -> dict:
        """딕셔너리 변환"""
        return {
            'version': self.version,
            'files_changed': self.files_changed,
            'reason': self.reason,
            'author': self.author,
            'timestamp': self.timestamp.isoformat()
        }


def get_constitution_mode() -> ConstitutionMode:
    """
    현재 헌법 모드 반환
    
    환경변수 CONSTITUTION_MODE로 제어:
    - NORMAL (기본값): 엄격한 무결성 검증
    - AMENDMENT: 개정 모드, 변경 허용
    
    Returns:
        ConstitutionMode enum
        
    Example:
        >>> import os
        >>> os.environ['CONSTITUTION_MODE'] = 'AMENDMENT'
        >>> mode = get_constitution_mode()
        >>> print(mode)
        ConstitutionMode.AMENDMENT
    """
    mode_str = os.getenv("CONSTITUTION_MODE", "NORMAL").upper()
    
    try:
        mode = ConstitutionMode[mode_str]
        
        if mode == ConstitutionMode.AMENDMENT:
            logger.warning("⚠️ AMENDMENT MODE: 헌법 변경이 허용됩니다")
            logger.warning("   프로덕션 환경에서는 사용하지 마십시오!")
        
        return mode
    
    except KeyError:
        logger.error(f"❌ 잘못된 CONSTITUTION_MODE: {mode_str}")
        logger.error("   NORMAL 또는 AMENDMENT만 허용됩니다")
        logger.error("   기본값 NORMAL로 설정합니다")
        return ConstitutionMode.NORMAL


def allow_amendment() -> bool:
    """
    헌법 개정 허용 여부
    
    Returns:
        True: 개정 모드 (변경 허용)
        False: 정상 모드 (변경 시 System Freeze)
        
    Example:
        >>> if allow_amendment():
        ...     print("헌법 개정 가능")
        ... else:
        ...     print("헌법 변경 금지")
    """
    return get_constitution_mode() == ConstitutionMode.AMENDMENT


def require_normal_mode():
    """
    정상 모드 강제
    
    프로덕션 환경에서 호출하여 Amendment Mode 방지
    
    Raises:
        RuntimeError: Amendment Mode인 경우
        
    Example:
        >>> # 프로덕션 시작 시
        >>> require_normal_mode()
    """
    if allow_amendment():
        raise RuntimeError(
            "❌ 프로덕션 환경에서 AMENDMENT MODE는 허용되지 않습니다!\n"
            "CONSTITUTION_MODE 환경변수를 제거하거나 NORMAL로 설정하십시오."
        )


# 개정 권한 (현재: 단일 키 모델)
AMENDMENT_AUTHORITY = {
    "owners": ["system", "developer"],
    "requires_approval": 1  # 1명만 필요
}


def is_authorized(author: str) -> bool:
    """
    개정 권한 확인
    
    Args:
        author: 개정 시도자
        
    Returns:
        True: 권한 있음
        False: 권한 없음
    """
    return author in AMENDMENT_AUTHORITY["owners"]


if __name__ == "__main__":
    # 테스트
    print("=== Amendment Mode Test ===\n")
    
    print("기본 모드:")
    mode = get_constitution_mode()
    print(f"  현재 모드: {mode.value}")
    print(f"  개정 허용: {allow_amendment()}")
    
    print("\n환경변수 설정 테스트:")
    os.environ['CONSTITUTION_MODE'] = 'AMENDMENT'
    mode = get_constitution_mode()
    print(f"  AMENDMENT 모드: {mode.value}")
    print(f"  개정 허용: {allow_amendment()}")
    
    print("\n권한 테스트:")
    print(f"  'system' 권한: {is_authorized('system')}")
    print(f"  'hacker' 권한: {is_authorized('hacker')}")
    
    print("\n개정 기록 테스트:")
    log = AmendmentLog(
        version="2.0.2",
        files_changed=["trading_constraints.py"],
        reason="MAX_VOLUME_PARTICIPATION 1% → 5%",
        author="developer",
        timestamp=datetime.now()
    )
    print(f"  버전: {log.version}")
    print(f"  이유: {log.reason}")
    
    # 환경변수 정리
    del os.environ['CONSTITUTION_MODE']
    
    print("\n✅ Amendment Mode 정의 완료!")
