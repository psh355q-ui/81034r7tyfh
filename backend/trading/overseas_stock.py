"""
Overseas Stock Functions for KIS API
Replaces functionality of overseas_stock_functions.py using backend.trading.kis_client.
"""

import logging
from typing import Dict, Optional, List, Union
from datetime import datetime, timedelta
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
    
    logger.info(f"Calling get_balance: CANO={cano}, ACNT_PRDT_CD={acnt_prdt_cd}, OVRS_EXCG_CD={ovrs_excg_cd}, TR_ID={tr_id}")
    
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
        logger.info(f"get_balance API success")
        logger.info(f"  body type: {type(body)}")
        logger.info(f"  body.output1 type: {type(body.output1) if hasattr(body, 'output1') else 'N/A'}")
        
        output1 = body.output1 if hasattr(body, 'output1') else None
        output2 = body.output2 if hasattr(body, 'output2') else None
        
        if output1:
            logger.info(f"  output1 length: {len(output1) if isinstance(output1, list) else 'not a list'}")
            if isinstance(output1, list) and len(output1) > 0:
                logger.info(f"  output1[0] keys: {output1[0].keys() if isinstance(output1[0], dict) else 'not a dict'}")
        else:
            logger.warning(f"  output1 is empty or falsy: {output1}")
        
        return {
            "output1": output1, # 잔고상세
            "output2": output2  # 결제잔고상세
        }
    else:
        logger.error(f"get_balance API failed - status code: {resp.response.status_code}")
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


# ============================================================================
# 배당 관련 API 함수 (신규 추가)
# ============================================================================

def get_dividend_by_ticker(
    symb: str,
    ncod: str = "US",
    period_days: int = 365
) -> Dict:
    """
    종목별 배당 정보 조회 (ICE 제공)
    
    API: /uapi/overseas-price/v1/quotations/rights-by-ice
    TR_ID: HHDFS78330900
    HTS: [7833] 해외주식 권리(ICE제공)
    
    Args:
        symb: 종목코드 (e.g., "AAPL", "INTL")
        ncod: 국가코드 (CN:중국, HK:홍콩, US:미국, JP:일본, VN:베트남)
        period_days: 조회 기간(일) - 기본 365일 (과거 6개월 + 미래 6개월)
        
    Returns:
        Dict: {
            "annual_dividend": float,     # 연간 배당금 (TTM)
            "dividend_yield": float,      # 배당 수익률
            "frequency": str,             # 배당 주기 (Q:분기, M:월, S:반기, A:연)
            "next_ex_date": str,          # 다음 배당락일 (YYYYMMDD)
            "payment_count": int,         # 연간 지급 횟수
            "history": List[Dict]         # 배당 이력
        }
    """
    try:
        url = "/uapi/overseas-price/v1/quotations/rights-by-ice"
        tr_id = "HHDFS78330900"
        
        # 조회 기간 설정 - KIS API는 빈 문자열일 때 자동으로 ±3개월 조회
        # (공식 샘플 코드에 따르면 st_ymd="", ed_ymd="" 사용)
        today = datetime.now()
        # KIS API 권장: 빈 문자열 사용 시 자동으로 3개월 전 ~ 3개월 후 조회
        start_date = ""  # 빈 문자열
        end_date = ""    # 빈 문자열
        
        params = {
            "NCOD": ncod,      # 국가코드
            "SYMB": symb,      # 종목코드
            "ST_YMD": start_date,  # 일자시작일 (빈 문자열: 자동 3개월 전)
            "ED_YMD": end_date     # 일자종료일 (빈 문자열: 자동 3개월 후)
        }
        
        resp = kc.invoke_api(url, tr_id, params, "GET")
        
        if not resp.isOK():
            logger.warning(f"배당 정보 조회 실패: {symb}")
            return _get_default_dividend_info()
        
        body = resp.getBody()
        output1 = body.output1 if hasattr(body, 'output1') else []
        
        # DEBUG: Log the actual API response
        logger.info(f"🔍 Dividend API Response for {symb}:")
        logger.info(f"  - Response type: {type(output1)}")
        logger.info(f"  - Record count: {len(output1) if isinstance(output1, list) else 'N/A'}")
        
        if isinstance(output1, list) and len(output1) > 0:
            logger.info(f"  - Sample record keys: {output1[0].keys() if isinstance(output1[0], dict) else 'N/A'}")
            logger.info(f"  - First 3 records:")
            for idx, record in enumerate(output1[:3]):
                ca_type = record.get('ca_type', 'N/A')
                ex_dt = record.get('ex_dt', record.get('base_dt', 'N/A'))
                amount = record.get('ca_amt', record.get('div_amt', 'N/A'))
                logger.info(f"    [{idx}] ca_type={ca_type}, ex_dt={ex_dt}, amount={amount}")
        
        # 배당 데이터 필터링 (배당 관련만)
        dividend_records = []
        if isinstance(output1, list):
            for record in output1:
                # 배당 관련 레코드만 필터링
                # KIS API response 필드명 확인 필요 (예: 'ca_type', 'event_type' 등)
                event_type = record.get('ca_type', '').upper()
                if 'DIV' in event_type or '배당' in event_type:
                    dividend_records.append(record)
        
        logger.info(f"  - Filtered dividend records: {len(dividend_records)}")
        
        if not dividend_records:
            logger.info(f"배당 정보 없음: {symb}, 기본값 반환")
            return _get_default_dividend_info()
        
        # TTM 배당금 계산 (과거 12개월)
        one_year_ago = (today - timedelta(days=365)).strftime("%Y%m%d")
        recent_dividends = []
        next_ex_date = None
        
        for div in dividend_records:
            ex_date = div.get('ex_dt', div.get('base_dt', ''))
            amount = float(div.get('ca_amt', div.get('div_amt', 0)))
            
            # 과거 12개월 배당금
            if ex_date >= one_year_ago and ex_date <= today.strftime("%Y%m%d"):
                recent_dividends.append({
                    'date': ex_date,
                    'amount': amount
                })
            
            # 다음 배당락일 (미래 날짜 중 가장 빠른 날짜)
            if ex_date > today.strftime("%Y%m%d"):
                if not next_ex_date or ex_date < next_ex_date:
                    next_ex_date = ex_date
        
        # 연간 배당금 계산
        annual_dividend = sum(d['amount'] for d in recent_dividends)
        payment_count = len(recent_dividends)
        
        # 배당 주기 추정
        if payment_count >= 12:
            frequency = "M"  # 월배당
        elif payment_count >= 4:
            frequency = "Q"  # 분기배당
        elif payment_count >= 2:
            frequency = "S"  # 반기배당
        else:
            frequency = "A"  # 연배당
        
        # 배당 수익률은 현재가 정보가 필요하므로 여기서는 0으로 설정
        # (호출하는 곳에서 current_price로 계산)
        
        return {
            "annual_dividend": round(annual_dividend, 4),
            "dividend_yield": 0.0,  # 현재가로 나중에 계산
            "frequency": frequency,
            "next_ex_date": next_ex_date or "",
            "payment_count": payment_count,
            "history": recent_dividends
        }
        
    except Exception as e:
        logger.error(f"배당 정보 조회 오류 ({symb}): {e}")
        return _get_default_dividend_info()


def _get_default_dividend_info() -> Dict:
    """배당 정보 조회 실패 시 기본값 반환"""
    return {
        "annual_dividend": 0.0,
        "dividend_yield": 0.0,
        "frequency": "Q",
        "next_ex_date": "",
        "payment_count": 0,
        "history": []
    }


def get_period_dividend_rights(
    start_date: str,
    end_date: str,
    ticker: str = "",
    right_type: str = "03"  # 03: 배당
) -> List[Dict]:
    """
    기간별 배당 권리 조회
    
    API: /uapi/overseas-price/v1/quotations/period-rights
    TR_ID: CTRGT011R
    HTS: [7520] 기간별해외증권권리조회
    
    Args:
        start_date: 조회시작일 (YYYYMMDD)
        end_date: 조회종료일 (YYYYMMDD)
        ticker: 종목코드 (선택, 빈 문자열이면 전체)
        right_type: 권리유형코드 (03:배당, 74:배당옵션, 75:특별배당)
        
    Returns:
        List[Dict]: 배당 일정 목록
    """
    try:
        url = "/uapi/overseas-price/v1/quotations/period-rights"
        tr_id = "CTRGT011R"
        
        params = {
            "RGHT_TYPE_CD": right_type,    # 03: 배당
            "INQR_DVSN_CD": "02",          # 02: 현지기준일
            "INQR_STRT_DT": start_date,
            "INQR_END_DT": end_date,
            "PDNO": ticker,                # 상품번호 (종목코드)
            "PRDT_TYPE_CD": "",
            "CTX_AREA_NK50": "",
            "CTX_AREA_FK50": ""
        }
        
        resp = kc.invoke_api(url, tr_id, params, "GET")
        
        if resp.isOK():
            body = resp.getBody()
            output = body.output if hasattr(body, 'output') else []
            return output if isinstance(output, list) else []
        else:
            logger.warning(f"기간별 배당권리 조회 실패: {start_date} ~ {end_date}")
            return []
            
    except Exception as e:
        logger.error(f"기간별 배당권리 조회 오류: {e}")
        return []
