"""
Overseas Stock Functions for KIS API
Replaces functionality of overseas_stock_functions.py using backend.trading.kis_client.
"""

import logging
from typing import Dict, Optional, List, Union
from backend.trading import kis_client as kc

logger = logging.getLogger(__name__)

def get_price(excd: str, symb: str) -> List[Dict]:
    """
    해외주식 현재가 상세 조회
    
    Args:
        excd: 거래소코드 (NASD, NYSE, AMEX, SEHK, SHAA, SZAA, TKSE, HASE, VNSE)
        symb: 종목코드
        
    Returns:
        List[Dict]: 시세 정보 리스트 (보통 1개 요소)
    """
    url = "/uapi/overseas-price/v1/quotations/price"
    tr_id = "HHDFS00000300"
    
    params = {
        "AUTH": "",
        "EXCD": excd,
        "SYMB": symb,
    }
    
    resp = kc.invoke_api(url, tr_id, params, "GET")
    
    if resp.isOK():
        output = resp.getBody().output
        if isinstance(output, dict):
            return [output]
        return output
    else:
        resp.printError()
        return []

def get_balance(cano: str, acnt_prdt_cd: str, ovrs_excg_cd: str, tr_crcy_cd: str = "USD") -> Dict:
    """
    해외주식 잔고 조회
    """
    url = "/uapi/overseas-stock/v1/trading/inquire-balance"
    
    # 실전/모의 구분
    if "vts" in kc._env.my_url:
        tr_id = "VTTS3012R"
    else:
        tr_id = "TTTS3012R"
        
    params = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "OVRS_EXCG_CD": ovrs_excg_cd,
        "TR_CRCY_CD": tr_crcy_cd,
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": "",
    }
    
    resp = kc.invoke_api(url, tr_id, params, "GET")
    
    if resp.isOK():
        body = resp.getBody()
        return {
            "output1": body.output1, # 잔고상세
            "output2": body.output2  # 결제잔고상세
        }
    else:
        resp.printError()
        return {}

def buy_order(cano: str, acnt_prdt_cd: str, excg: str, symb: str, qty: int, price: float = 0, ord_dvsn: str = "00"):
    """
    해외주식 매수 주문
    """
    return _do_order(cano, acnt_prdt_cd, excg, symb, qty, price, "buy", ord_dvsn)

def sell_order(cano: str, acnt_prdt_cd: str, excg: str, symb: str, qty: int, price: float = 0, ord_dvsn: str = "00"):
    """
    해외주식 매도 주문
    """
    return _do_order(cano, acnt_prdt_cd, excg, symb, qty, price, "sell", ord_dvsn)

def _do_order(cano: str, acnt_prdt_cd: str, excg: str, symb: str, qty: int, price: float, side: str, ord_dvsn: str):
    """
    주문 실행 공통 (미국주간 or 야간/일반 구분 필요하나 여기선 기본 주문 API 사용)
    """
    url = "/uapi/overseas-stock/v1/trading/order"
    
    if "vts" in kc._env.my_url:
        tr_id = "VTTT1002U" if side == "buy" else "VTTT1001U"
    else:
        tr_id = "TTTT1002U" if side == "buy" else "TTTT1001U" # NASD/NYSE/AMEX
        # 거래소별 TR ID 다를 수 있음. 여기선 미국 기준 (TTTT1002U)
        # 만약 주간거래라면 TTTS6036U 등 다를 수 있음.
    
    # KIS API 문서에 따르면 해외주식 주문은 거래소별/국가별로 TR ID가 상이함.
    # 미국(NASD, NYSE, AMEX): JTTT1002U (매수), JTTT1001U (매도)
    # 아래 코드는 일반적인 케이스를 가정함.
    
    # 정확한 TR ID 매핑이 필요함.
    # 예시: 미국 매수 JTTT1002U (실전), VTTT1002U (모의)
    if side == "buy":
        tr_id = "VTTT1002U" if "vts" in kc._env.my_url else "JTTT1002U"
    else:
        tr_id = "VTTT1001U" if "vts" in kc._env.my_url else "JTTT1001U"

    params = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "OVRS_EXCG_CD": excg,
        "PDNO": symb,
        "ORD_QTY": str(qty),
        "OVRS_ORD_UNPR": str(price),
        "ORD_SVR_DVSN_CD": "0",
        "ORD_DVSN": ord_dvsn # 00: 지정가, 01: 시장가 (미국제외 등 확인 필요)
    }
    
    resp = kc.invoke_api(url, tr_id, params, "POST")
    return resp.getBody()

def get_daily_price(excd: str, symb: str, period: str = "D") -> List[Dict]:
    """
    해외주식 기간별 시세 (일/주/월봉)
    
    API: /uapi/overseas-price/v1/quotations/inquire-daily-chartprice
    TR_ID: HHDFS76240000
    """
    url = "/uapi/overseas-price/v1/quotations/inquire-daily-chartprice"
    tr_id = "HHDFS76240000"
    
    # 날짜 계산 (오늘 기준)
    import datetime
    today = datetime.datetime.now().strftime("%Y%m%d")
    
    # 기간 구분: 0:일, 1:주, 2:월
    gubn = "0"
    if period == "W": gubn = "1"
    elif period == "M": gubn = "2"
    
    params = {
        "AUTH": "",
        "EXCD": excd,
        "SYMB": symb,
        "GUBN": gubn,
        "BYMD": today, # 기준일자
        "MODP": "1"    # 수정주가반영여부 (1:반영)
    }
    
    resp = kc.invoke_api(url, tr_id, params, "GET")
    
    if resp.isOK():
        return resp.getBody().output2 # output2가 일별 데이터 리스트
    else:
        resp.printError()
        return []

def get_present_balance(cano: str, acnt_prdt_cd: str) -> Dict:
    """
    해외주식 체결기준현재잔고 (예수금 조회용)
    
    API: /uapi/overseas-stock/v1/trading/inquire-present-balance
    TR_ID:
        - 실전: CTRP6504R
        - 모의: VTRP6504R
    """
    url = "/uapi/overseas-stock/v1/trading/inquire-present-balance"
    
    if "vts" in kc._env.my_url:
        tr_id = "VTRP6504R"
    else:
        tr_id = "CTRP6504R"
    
    params = {
        "CANO": cano,
        "ACNT_PRDT_CD": acnt_prdt_cd,
        "WCRC_FRCR_DVSN_CD": "02", # 01:원화, 02:외화
        "NATN_CD": "840",          # 미국(840)
        "TR_MKET_CD": "00",        # 전체
        "INQR_DVSN_CD": "00"       # 전체
    }
    
    resp = kc.invoke_api(url, tr_id, params, "GET")
    
    if resp.isOK():
        return resp.getBody()
    else:
        resp.printError()
        return {}

def get_price_detail(excd: str, symb: str) -> Dict:
    """
    해외주식 현재가 상세 조회 (일일 등락폭 등 포함)
    API: /uapi/overseas-price/v1/quotations/price-detail
    TR_ID: HHDFS76200200
    Args:
        excd: NAS, NYS, AMS, HKS, TSE, SHS, SZS, HNX, HSX
    """
    url = "/uapi/overseas-price/v1/quotations/price-detail"
    tr_id = "HHDFS76200200"
    
    params = {
        "AUTH": "",
        "EXCD": excd,
        "SYMB": symb,
    }
    
    resp = kc.invoke_api(url, tr_id, params, "GET")
    
    if resp.isOK():
        return resp.getBody().output
    else:
        resp.printError()
        return {}
