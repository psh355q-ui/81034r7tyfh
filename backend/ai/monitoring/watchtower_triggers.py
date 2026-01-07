
"""
The Watchtower Triggers
========================
Defines keywords and patterns that trigger expensive deep reasoning analysis.
Used by NewsAgent and other monitoring components to filter noise.

Categories:
1. GEOPOLITICAL_CRITICAL (Physical Conflict)
2. CHIP_WAR_CRITICAL (Tech War)
3. MACRO_SHOCK (Economic Crisis)
4. REGULATORY_RISK (Legal/Compliance)
"""

from typing import Dict, List

# 1. 물리적 분쟁 및 전쟁 (가장 높은 우선순위)
GEOPOLITICAL_TRIGGERS = [
    # English
    "invasion", "military operation", "declaration of war", "airstrike",
    "blockade", "nuclear threat", "missile launch", "troops deployed",
    "mobilization", "annexation", "sanctions package", "embargo",
    
    # Korean
    "침공", "전쟁 선포", "군사 작전", "공습", "미사일 발사",
    "봉쇄", "핵 위협", "병력 배치", "동원령", "합병", "대규모 제재"
]

# 2. 기술 패권 및 무역 전쟁 (칩 워)
CHIP_WAR_TRIGGERS = [
    # English
    "export control", "chip ban", "semiconductor restriction", 
    "entity list", "technology transfer", "custom silicon", "tpu",
    "advanced node", "lithography equipment", "asml", "smic", "huawei",
    
    # Korean
    "수출 통제", "반도체 제재", "칩 규제", "엔티티 리스트", 
    "기술 이전", "자체 칩", "미세 공정", "노광 장비"
]

# 3. 매크로 경제 충격 (금리, 인플레, 파산) - 2026 Context
MACRO_SHOCK_TRIGGERS = [
    # English
    "rate hike", "emergency cut", "hyperinflation", "default",
    "bankruptcy", "liquidity crisis", "yield curve control",
    "flash crash", "market halt", "peg broken",
    
    # Korean
    "금리 인상", "긴급 인하", "초인플레이션", "디폴트", 
    "파산", "유동성 위기", "일드 커브 컨트롤", "플래시 크래시", "거래 정지"
]

# 4. 규제 및 소송 (기업 리스크)
REGULATORY_TRIGGERS = [
    # English
    "antitrust", "monopoly", "doj lawsuit", "sec investigation",
    "fraud", "accounting irregularity", "delisting", "short seller report",
    
    # Korean
    "반독점", "독점", "법무부 소송", "검찰 조사", "SEC 조사",
    "분식 회계", "상장 폐지", "공매도 리포트"
]

def get_all_triggers() -> Dict[str, List[str]]:
    """모든 트리거 키워드 반환"""
    return {
        "GEOPOLITICS": GEOPOLITICAL_TRIGGERS,
        "CHIP_WAR": CHIP_WAR_TRIGGERS,
        "MACRO": MACRO_SHOCK_TRIGGERS,
        "REGULATORY": REGULATORY_TRIGGERS
    }
