"""
Ticker Name Mappings
영문 티커 → 영문명 + 한글명 매핑
"""

from typing import Dict, List

# 티커명 매핑 딕셔너리
# 각 티커에 대해 검색 키워드 리스트 제공 (영문명, 한글명, 약어 등)
TICKER_MAPPINGS: Dict[str, List[str]] = {
    # 기술주 (Tech Giants)
    "AAPL": ["Apple", "애플", "아이폰"],
    "MSFT": ["Microsoft", "마이크로소프트", "MS"],
    "GOOGL": ["Google", "Alphabet", "구글", "알파벳"],
    "GOOG": ["Google", "Alphabet", "구글", "알파벳"],
    "AMZN": ["Amazon", "아마존"],
    "META": ["Meta", "Facebook", "메타", "페이스북"],
    "TSLA": ["Tesla", "테슬라"],
    "NFLX": ["Netflix", "넷플릭스"],
    
    # 반도체 (Semiconductors)
    "NVDA": ["NVIDIA", "Nvidia", "엔비디아"],
    "AMD": ["AMD", "Advanced Micro Devices", "어드밴스드 마이크로 디바이스"],
    "INTC": ["Intel", "인텔"],
    "TSM": ["TSMC", "Taiwan Semiconductor", "대만 반도체", "TSMC"],
    "ASML": ["ASML"],
    "QCOM": ["Qualcomm", "퀄컴"],
    "AVGO": ["Broadcom", "브로드컴"],
    "MU": ["Micron", "마이크론"],
    "AMAT": ["Applied Materials", "어플라이드 머티어리얼즈"],
    "LRCX": ["Lam Research", "램 리서치"],
    
    # 자동차 (Automotive)
    "GM": ["General Motors", "GM", "제너럴모터스"],
    "F": ["Ford", "포드"],
    "NIO": ["NIO", "니오"],
    "RIVN": ["Rivian", "리비안"],
    "LCID": ["Lucid", "루시드"],
    
    # 금융 (Finance)
    "JPM": ["JPMorgan", "JP Morgan", "제이피모건"],
    "BAC": ["Bank of America", "뱅크오브아메리카", "BOA"],
    "WFC": ["Wells Fargo", "웰스파고"],
    "GS": ["Goldman Sachs", "골드만삭스"],
    "MS": ["Morgan Stanley", "모건스탠리"],
    "C": ["Citigroup", "씨티그룹", "시티"],
    "V": ["Visa", "비자"],
    "MA": ["Mastercard", "마스터카드"],
    "PYPL": ["PayPal", "페이팔"],
    
    # 소비재 (Consumer)
    "NKE": ["Nike", "나이키"],
    "SBUX": ["Starbucks", "스타벅스"],
    "MCD": ["McDonald's", "McDonalds", "맥도날드"],
    "DIS": ["Disney", "디즈니"],
    "COST": ["Costco", "코스트코"],
    "WMT": ["Walmart", "월마트"],
    "TGT": ["Target", "타겟"],
    
    # 헬스케어 (Healthcare)
    "JNJ": ["Johnson & Johnson", "존슨앤존슨"],
    "UNH": ["UnitedHealth", "유나이티드헬스"],
    "PFE": ["Pfizer", "화이자"],
    "ABBV": ["AbbVie", "애브비"],
    "TMO": ["Thermo Fisher", "써모 피셔"],
    "LLY": ["Eli Lilly", "일라이 릴리"],
    
    # 에너지 (Energy)
    "XOM": ["ExxonMobil", "엑슨모빌"],
    "CVX": ["Chevron", "쉐브론"],
    "COP": ["ConocoPhillips", "코노코필립스"],
    
    # 항공우주/방산 (Aerospace & Defense)
    "BA": ["Boeing", "보잉"],
    "LMT": ["Lockheed Martin", "록히드마틴"],
    "RTX": ["Raytheon", "레이시온"],
    
    # 통신 (Telecom)
    "T": ["AT&T", "AT&T", "에이티앤티"],
    "VZ": ["Verizon", "버라이즌"],
    "TMUS": ["T-Mobile", "티모바일"],
    
    # 산업 (Industrial)
    "CAT": ["Caterpillar", "캐터필러"],
    "DE": ["Deere", "John Deere", "디어"],
    "GE": ["General Electric", "GE", "제너럴일렉트릭"],
    
    # AI/클라우드 (AI & Cloud)
    "CRM": ["Salesforce", "세일즈포스"],
    "ORCL": ["Oracle", "오라클"],
    "ADBE": ["Adobe", "어도비"],
    "NOW": ["ServiceNow", "서비스나우"],
    "SNOW": ["Snowflake", "스노우플레이크"],
    "PLTR": ["Palantir", "팔란티어"],
}


def get_ticker_keywords(ticker: str) -> List[str]:
    """
    티커에 대한 검색 키워드 리스트 반환
    
    Args:
        ticker: 티커 심볼 (예: TSLA, AAPL)
        
    Returns:
        검색 키워드 리스트 (티커 포함)
    """
    ticker_upper = ticker.upper()
    keywords = [ticker_upper]  # 티커 자체도 포함
    
    # 매핑된 키워드 추가
    if ticker_upper in TICKER_MAPPINGS:
        keywords.extend(TICKER_MAPPINGS[ticker_upper])
    
    return keywords


def get_company_name(ticker: str, lang: str = "en") -> str:
    """
    티커의 회사명 반환
    
    Args:
        ticker: 티커 심볼
        lang: 언어 ("en" or "ko")
        
    Returns:
        회사명 (없으면 티커 반환)
    """
    ticker_upper = ticker.upper()
    
    if ticker_upper not in TICKER_MAPPINGS:
        return ticker_upper
    
    keywords = TICKER_MAPPINGS[ticker_upper]
    
    if lang == "ko":
        # 한글이 포함된 첫 번째 키워드 반환
        for keyword in keywords:
            if any('\u3131' <= c <= '\u318F' or '\uAC00' <= c <= '\uD7A3' for c in keyword):
                return keyword
        # 한글이 없으면 첫 번째 영문명
        return keywords[0] if keywords else ticker_upper
    else:
        # 영문명 (첫 번째)
        return keywords[0] if keywords else ticker_upper
