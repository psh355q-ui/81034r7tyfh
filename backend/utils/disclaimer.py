"""
AI Trading System - 면책 조항 (Disclaimer) 모듈
================================================

모든 브리핑 및 투자 관련 문서에 법적 면책 조항을 자동 삽입합니다.

참고: docs/discussions/260105_Claudecodeideas2.md
"""

from datetime import datetime
from typing import Optional


# ===============================================
# 면책 조항 템플릿
# ===============================================

DISCLAIMERS = {
    # 일반 면책 조항 (모든 브리핑에 기본 적용)
    "general": (
        "⚠️ **투자 유의사항**\n"
        "본 브리핑은 투자 참고 정보를 제공하며, 투자 결정에 대한 책임은 "
        "전적으로 사용자에게 있습니다. 본 서비스는 투자자문업 등록 서비스가 아닙니다."
    ),

    # AI 분석 한계 (AI 생성 콘텐츠에 적용)
    "ai_limitation": (
        "🤖 **AI 분석 한계**\n"
        "본 분석은 AI가 과거 데이터와 공개된 뉴스를 기반으로 생성한 것으로, "
        "미래 수익을 보장하지 않습니다. AI 모델의 오류 가능성이 항상 존재합니다."
    ),

    # 레버리지/인버스 상품 경고
    "leverage": (
        "⚡ **레버리지/인버스 상품 경고**\n"
        "레버리지/인버스 ETF는 원금 전액 손실 가능성이 있습니다. "
        "장기 보유 시 복리 효과로 인해 기초지수와 괴리가 발생합니다."
    ),

    # 배당 관련
    "dividend": (
        "💰 **배당 관련 유의사항**\n"
        "배당금은 기업 실적에 따라 삭감되거나 중단될 수 있으며, "
        "과거 배당 이력이 미래 배당을 보장하지 않습니다."
    ),

    # 경제지표 분석
    "economic": (
        "📊 **경제지표 분석 유의사항**\n"
        "경제지표 해석은 AI의 분석이며, 실제 시장 반응은 "
        "예상과 다를 수 있습니다. 정확한 데이터는 공식 발표를 참고하세요."
    ),

    # 시장 예측
    "market_forecast": (
        "🔮 **시장 전망 유의사항**\n"
        "시장 예측은 불확실성이 높으며, 예상치 못한 이벤트로 인해 "
        "급격한 변동이 발생할 수 있습니다."
    ),

    # 포트폴리오 분석
    "portfolio": (
        "📋 **포트폴리오 분석 유의사항**\n"
        "제시된 리밸런싱 제안은 참고용이며, 개인의 투자 목표, "
        "위험 허용도, 세금 상황에 따라 적합하지 않을 수 있습니다."
    ),
}


# ===============================================
# 브리핑 타입별 면책 조항 매핑
# ===============================================

BRIEFING_DISCLAIMERS = {
    "premarket": ["general", "ai_limitation"],
    "checkpoint": ["general", "ai_limitation"],
    "us_close": ["general", "ai_limitation", "market_forecast"],
    "korean_market": ["general", "ai_limitation", "market_forecast"],
    "weekly_review": ["general", "ai_limitation", "portfolio"],
    "weekly_outlook": ["general", "ai_limitation", "market_forecast"],
    "daily": ["general", "ai_limitation"],
    "economic": ["general", "ai_limitation", "economic"],
    "portfolio": ["general", "ai_limitation", "portfolio"],
}


def get_disclaimer_header(briefing_type: str = "daily") -> str:
    """
    브리핑 타입에 맞는 면책 조항 헤더 생성

    Args:
        briefing_type: 브리핑 타입 (premarket, checkpoint, daily 등)

    Returns:
        마크다운 형식의 면책 조항 헤더
    """
    disclaimer_keys = BRIEFING_DISCLAIMERS.get(briefing_type, ["general", "ai_limitation"])

    lines = [
        "---",
        "",
        "> **📜 법적 고지 (Legal Disclaimer)**",
        ">",
    ]

    for key in disclaimer_keys:
        disclaimer_text = DISCLAIMERS.get(key, "")
        if disclaimer_text:
            # 멀티라인을 > 형식으로 변환
            for line in disclaimer_text.split("\n"):
                lines.append(f"> {line}")
            lines.append(">")

    lines.extend([
        "",
        "---",
        "",
    ])

    return "\n".join(lines)


def get_disclaimer_footer() -> str:
    """
    브리핑 하단 AI 생성 고지

    Returns:
        마크다운 형식의 푸터
    """
    return (
        "\n---\n"
        f"📢 이 브리핑은 AI가 자동 생성했습니다. ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n"
        "\n"
        "*본 자료는 투자 권유가 아니며, 투자의 최종 책임은 투자자 본인에게 있습니다.*\n"
    )


def wrap_briefing_with_disclaimer(
    content: str,
    briefing_type: str = "daily",
    include_header: bool = True,
    include_footer: bool = True
) -> str:
    """
    브리핑 콘텐츠에 면책 조항을 래핑

    Args:
        content: 원본 브리핑 콘텐츠
        briefing_type: 브리핑 타입
        include_header: 헤더 면책 조항 포함 여부
        include_footer: 푸터 AI 생성 고지 포함 여부

    Returns:
        면책 조항이 포함된 브리핑 콘텐츠
    """
    parts = []

    if include_header:
        parts.append(get_disclaimer_header(briefing_type))

    parts.append(content)

    if include_footer:
        parts.append(get_disclaimer_footer())

    return "\n".join(parts)


def get_telegram_disclaimer(briefing_type: str = "daily") -> str:
    """
    텔레그램용 간략 면책 조항 (4096자 제한 고려)

    Args:
        briefing_type: 브리핑 타입

    Returns:
        간략한 면책 문구
    """
    return (
        "⚠️ *투자 참고용 AI 분석입니다. "
        "투자 결정 책임은 본인에게 있습니다.*"
    )


# ===============================================
# 테스트
# ===============================================

if __name__ == "__main__":
    print("=" * 60)
    print("면책 조항 테스트")
    print("=" * 60)

    # 프리마켓 브리핑 면책 조항
    print("\n[프리마켓 브리핑 면책 조항]")
    print(get_disclaimer_header("premarket"))

    # 주간 전망 면책 조항
    print("\n[주간 전망 브리핑 면책 조항]")
    print(get_disclaimer_header("weekly_outlook"))

    # 콘텐츠 래핑 테스트
    print("\n[콘텐츠 래핑 테스트]")
    sample_content = "# 테스트 브리핑\n\n오늘의 시장 분석입니다."
    wrapped = wrap_briefing_with_disclaimer(sample_content, "daily")
    print(wrapped)
