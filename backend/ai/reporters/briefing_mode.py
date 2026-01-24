"""
Briefing Mode Definitions - v2.3

시점에 따른 브리핑 모드 정의 (ChatGPT/Gemini 합의 기반)

핵심 원칙:
- CLOSING: Because/Result (직설법) - 이미 발생한 결과 분석
- MORNING: If/Then (가정법) - 시나리오 기반 대응 전략

작성일: 2026-01-24
"""

from enum import Enum
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Any


class BriefingMode(Enum):
    """브리핑 모드"""
    CLOSING = "CLOSING"    # 미국장 마감 후 (06:10/07:10 KST)
    MORNING = "MORNING"    # 미국장 개장 전 (22:30/23:00 KST)
    INTRADAY = "INTRADAY"  # 장중 체크포인트 (01:00, 03:00 KST)
    KOREAN = "KOREAN"      # 한국장 오픈 전 (08:00 KST)


def get_current_briefing_mode() -> BriefingMode:
    """
    현재 시간에 맞는 브리핑 모드 반환 (KST 기준)

    시간대별 모드:
    - 06:00 ~ 09:00 KST: CLOSING (미국장 마감 브리핑)
    - 09:00 ~ 16:00 KST: KOREAN (한국장 시간)
    - 22:00 ~ 00:00 KST: MORNING (프리마켓 브리핑)
    - 00:00 ~ 06:00 KST: INTRADAY (장중 체크포인트)
    """
    kst = ZoneInfo("Asia/Seoul")
    now = datetime.now(kst)
    hour = now.hour

    if 6 <= hour < 9:
        return BriefingMode.CLOSING
    elif 9 <= hour < 16:
        return BriefingMode.KOREAN
    elif 22 <= hour <= 23:
        return BriefingMode.MORNING
    else:  # 0-6시 또는 16-22시
        return BriefingMode.INTRADAY


# 모드별 프롬프트 제약 조건
MODE_CONSTRAINTS: Dict[BriefingMode, Dict[str, Any]] = {
    BriefingMode.CLOSING: {
        "name": "마감 브리핑",
        "grammar": "Because / Result (직설법)",
        "indicators": "Actual / Surprise (실제 발표값)",
        "focus": "왜 이렇게 끝났는가? 결과 분석",
        "banned_phrases": [
            "예상 상회 시", "예상 하회 시", "~할 경우", "~한다면",
            "시나리오 A", "시나리오 B", "If", "만약"
        ],
        "required_phrases": [
            "결과", "실제", "마감", "반응", "상승/하락 마감"
        ],
        "output_style": "결과 중심 - 무슨 일이 있었고, 왜 그렇게 됐는지",
        "economic_indicator_format": """
**경제지표 결과 분석** (CLOSING 전용):
- 지표명: [실제값] (예상: [예상값], 서프라이즈: [차이])
- 시장 반응: [실제로 어떻게 움직였는지]
- 해석: [왜 그렇게 반응했는지]
""",
    },

    BriefingMode.MORNING: {
        "name": "프리마켓 브리핑",
        "grammar": "If / Then (가정법)",
        "indicators": "Expected / Forecast (예상치)",
        "focus": "어떻게 대응할 것인가? 시나리오 분석",
        "banned_phrases": [
            "마감했다", "반응했다", "결과적으로", "상승 마감", "하락 마감"
        ],
        "required_phrases": [
            "예상", "시나리오", "대응 전략", "IF", "THEN", "Case"
        ],
        "output_style": "시나리오 중심 - 무슨 일이 예정되어 있고, 어떻게 대응할지",
        "economic_indicator_format": """
**경제지표 시나리오 분석** (MORNING 전용):
- 지표명: 예상 [예상값], 이전 [이전값]
- Case A (예상 상회 시): [시장 예상 반응] → [대응 전략]
- Case B (예상 하회 시): [시장 예상 반응] → [대응 전략]
- Case C (예상 부합 시): [시장 예상 반응] → [대응 전략]
""",
    },

    BriefingMode.INTRADAY: {
        "name": "장중 체크포인트",
        "grammar": "Observation / Alert (관찰)",
        "indicators": "Delta / Change (변동폭)",
        "focus": "유의미한 변동이 있는가?",
        "banned_phrases": [],
        "required_phrases": [
            "변동", "주목", "모니터링", "급등", "급락"
        ],
        "output_style": "변동 중심 - ±1% 이상 변동 시에만 분석",
        "threshold": 1.0,  # 1% 이상 변동 시에만 리포트 생성
    },

    BriefingMode.KOREAN: {
        "name": "한국장 오픈 브리핑",
        "grammar": "Linkage / Impact (연계 분석)",
        "indicators": "US Close → KR Open (미국장 결과 → 한국장 영향)",
        "focus": "미국장 결과가 한국장에 미치는 영향",
        "banned_phrases": [],
        "required_phrases": [
            "연계", "영향", "코스피", "코스닥", "외국인", "환율"
        ],
        "output_style": "연계 중심 - 미국장 결과 → 한국장 전망",
    },
}


def get_mode_constraints(mode: BriefingMode) -> Dict[str, Any]:
    """모드별 제약 조건 반환"""
    return MODE_CONSTRAINTS.get(mode, MODE_CONSTRAINTS[BriefingMode.CLOSING])


def validate_output_for_mode(output: str, mode: BriefingMode) -> Dict[str, Any]:
    """
    출력이 모드 제약 조건을 준수하는지 검증

    Returns:
        {
            "valid": bool,
            "violations": List[str],  # 위반된 금지 표현
            "missing": List[str],     # 누락된 필수 표현
            "score": float            # 0-100 준수 점수
        }
    """
    constraints = get_mode_constraints(mode)
    output_lower = output.lower()

    violations = []
    missing = []

    # 금지 표현 검사
    for phrase in constraints.get("banned_phrases", []):
        if phrase.lower() in output_lower:
            violations.append(phrase)

    # 필수 표현 검사
    for phrase in constraints.get("required_phrases", []):
        if phrase.lower() not in output_lower:
            missing.append(phrase)

    # 점수 계산
    total_checks = len(constraints.get("banned_phrases", [])) + len(constraints.get("required_phrases", []))
    failed_checks = len(violations) + len(missing)

    score = 100.0 if total_checks == 0 else ((total_checks - failed_checks) / total_checks) * 100

    return {
        "valid": len(violations) == 0 and len(missing) == 0,
        "violations": violations,
        "missing": missing,
        "score": round(score, 1)
    }


def get_mode_system_prompt(mode: BriefingMode) -> str:
    """
    모드별 시스템 프롬프트 반환

    이 프롬프트는 LLM에게 모드별 제약 조건을 강제합니다.
    """
    constraints = get_mode_constraints(mode)
    banned = ", ".join(f'"{p}"' for p in constraints.get("banned_phrases", []))
    required = ", ".join(f'"{p}"' for p in constraints.get("required_phrases", []))

    return f"""
## 브리핑 모드: {constraints['name']} ({mode.value})

**문법 규칙**: {constraints['grammar']}
**지표 표현**: {constraints['indicators']}
**핵심 질문**: {constraints['focus']}
**출력 스타일**: {constraints['output_style']}

### 절대 금지 표현 (사용 시 규칙 위반):
{banned if banned else "없음"}

### 필수 포함 표현 (반드시 사용):
{required if required else "없음"}

{constraints.get('economic_indicator_format', '')}
"""


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Briefing Mode Test")
    print("=" * 60)

    # 현재 모드 확인
    current = get_current_briefing_mode()
    print(f"\n현재 모드: {current.value}")

    # 각 모드별 제약 조건 출력
    for mode in BriefingMode:
        print(f"\n{'='*40}")
        print(f"Mode: {mode.value}")
        print(get_mode_system_prompt(mode))

    # 검증 테스트
    print("\n" + "=" * 60)
    print("Validation Test")
    print("=" * 60)

    # CLOSING 모드에서 가정법 사용 (위반)
    closing_bad = "예상 상회 시 주식이 상승할 것입니다."
    result = validate_output_for_mode(closing_bad, BriefingMode.CLOSING)
    print(f"\nCLOSING 위반 테스트: {result}")

    # CLOSING 모드에서 직설법 사용 (정상)
    closing_good = "PMI 결과 50.1로 예상 상회. 시장은 0.5% 상승 마감. 금리 상승 압력으로 반응했다."
    result = validate_output_for_mode(closing_good, BriefingMode.CLOSING)
    print(f"CLOSING 정상 테스트: {result}")
