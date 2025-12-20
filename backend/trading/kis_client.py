"""
한국투자증권 Open API 클라이언트

공식 GitHub 저장소 패턴 기반:
https://github.com/koreainvestment/open-trading-api

주요 기능:
- kis_devlp.yaml 기반 설정
- OAuth 토큰 자동 발급/갱신
- 국내주식 시세 조회
- 국내주식 매수/매도 주문
- 계좌 잔고 조회
- 주문 취소/정정

참고: examples_user/kis_auth.py & domestic_stock_functions.py
"""

import os
import json
import time
import yaml
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


# =============================================================================
# 설정 파일 경로
# =============================================================================

# 토큰 저장 경로 (공식 샘플과 동일)
config_root = os.path.join(os.path.expanduser("~"), "KIS", "config")
Path(config_root).mkdir(parents=True, exist_ok=True)

# API 설정 파일 (kis_devlp.yaml)
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "kis_devlp.yaml"


# =============================================================================
# 전역 설정 클래스 (공식 패턴)
# =============================================================================

class KISEnv:
    """API 환경 설정 (공식 패턴: getTREnv())"""
    
    def __init__(self):
        self.my_app = ""      # 앱키
        self.my_sec = ""      # 앱시크릿
        self.my_acct = ""     # 계좌번호 (앞 8자리)
        self.my_prod = "01"   # 상품코드 (01: 종합계좌)
        self.my_token = ""    # 접근토큰
        self.my_url = ""      # API URL
        self.htsid = ""       # HTS ID


# 전역 환경 변수
_env = KISEnv()
_base_headers = {}


def getTREnv() -> KISEnv:
    """전역 환경 설정 반환"""
    return _env


def setTREnv(env: KISEnv):
    """전역 환경 설정 설정"""
    global _env
    _env = env


# =============================================================================
# 설정 파일 로드 (kis_devlp.yaml)
# =============================================================================

def load_config() -> Dict[str, str]:
    """
    kis_devlp.yaml 파일 로드
    
    공식 형식:
    my_app: "실전 앱키"
    my_sec: "실전 시크릿"
    paper_app: "모의 앱키"
    paper_sec: "모의 시크릿"
    my_htsid: "HTS ID"
    my_acct_stock: "증권계좌"
    my_paper_stock: "모의계좌"
    my_prod: "01"
    """
    if not CONFIG_FILE.exists():
        # 환경변수에서 읽기 (대안)
        return {
            "my_app": os.environ.get("KIS_APP_KEY", ""),
            "my_sec": os.environ.get("KIS_APP_SECRET", ""),
            "paper_app": os.environ.get("KIS_PAPER_APP_KEY", ""),
            "paper_sec": os.environ.get("KIS_PAPER_APP_SECRET", ""),
            "my_htsid": os.environ.get("KIS_HTS_ID", ""),
            "my_acct_stock": (
                os.environ.get("KIS_ACCOUNT_NO", "") or 
                os.environ.get("KIS_ACCOUNT_NUMBER", "")
            ).split("-")[0],
            "my_paper_stock": os.environ.get("KIS_PAPER_ACCOUNT", ""),
            "my_prod": os.environ.get("KIS_PROD_CODE", "01"),
        }
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config


def create_sample_config():
    """샘플 설정 파일 생성"""
    sample = """# 한국투자증권 API 설정 파일
# https://apiportal.koreainvestment.com/ 에서 발급

# 실전투자
my_app: "여기에 실전투자 앱키 입력"
my_sec: "여기에 실전투자 앱시크릿 입력"

# 모의투자
paper_app: "여기에 모의투자 앱키 입력"
paper_sec: "여기에 모의투자 앱시크릿 입력"

# HTS ID (체결통보 등에 사용)
my_htsid: "사용자 HTS ID"

# 계좌번호 앞 8자리
my_acct_stock: "증권계좌 8자리"
my_paper_stock: "모의투자 증권계좌 8자리"

# 계좌번호 뒤 2자리
my_prod: "01"  # 종합계좌

# User-Agent
my_agent: "Mozilla/5.0"
"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(sample)
    
    logger.info(f"샘플 설정 파일 생성: {CONFIG_FILE}")


# =============================================================================
# 인증 함수 (kis_auth.py 패턴)
# =============================================================================

def auth(svr: str = "vps", product: str = "01") -> bool:
    """
    API 인증 초기화
    
    Args:
        svr: "prod" (실전투자) 또는 "vps" (모의투자)
        product: 상품코드 ("01": 종합계좌)
    
    Returns:
        인증 성공 여부
    
    공식 패턴:
        ka.auth(svr="prod", product="01")  # 실전
        ka.auth(svr="vps", product="01")   # 모의
    """
    global _env, _base_headers
    
    config = load_config()
    
    if not config.get("my_app") and not config.get("paper_app"):
        logger.error("API 키가 설정되지 않았습니다. kis_devlp.yaml 파일을 확인하세요.")
        create_sample_config()
        return False
    
    # 환경 설정
    if svr == "prod":
        # 실전투자
        _env.my_app = config.get("my_app", "")
        _env.my_sec = config.get("my_sec", "")
        _env.my_acct = config.get("my_acct_stock", "")
        _env.my_url = "https://openapi.koreainvestment.com:9443"
    else:
        # 모의투자 (기본값)
        _env.my_app = config.get("paper_app", config.get("my_app", ""))
        _env.my_sec = config.get("paper_sec", config.get("my_sec", ""))
        _env.my_acct = config.get("my_paper_stock", config.get("my_acct_stock", ""))
        _env.my_url = "https://openapivts.koreainvestment.com:29443"
    
    _env.my_prod = product
    _env.htsid = config.get("my_htsid", "")
    
    # 토큰 발급
    token = _get_access_token()
    if not token:
        logger.error("토큰 발급 실패")
        return False
    
    _env.my_token = token
    
    # 기본 헤더 설정
    _base_headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": _env.my_app,
        "appsecret": _env.my_sec,
    }
    
    logger.info(f"인증 완료: {'실전' if svr == 'prod' else '모의'} 투자 모드")
    logger.info(f"계좌: {_env.my_acct}-{_env.my_prod}")
    
    return True


def _get_access_token() -> str:
    """
    OAuth 접근토큰 발급
    
    공식 API: POST /oauth2/tokenP
    
    토큰 캐싱:
    - 토큰 만료시간 확인
    - 캐시 파일에서 로드/저장
    """
    # 토큰 캐시 파일
    cache_file = Path(config_root) / f"kis_token_{'prod' if 'openapi.' in _env.my_url else 'vps'}.json"
    
    # 캐시된 토큰 확인
    if cache_file.exists():
        with open(cache_file, "r") as f:
            cached = json.load(f)
        
        # 만료시간 확인
        expires_at = cached.get("expires_at", 0)
        if time.time() < expires_at - 3600:  # 1시간 여유
            logger.info("캐시된 토큰 사용")
            return cached.get("access_token", "")
    
    # 새 토큰 발급
    url = f"{_env.my_url}/oauth2/tokenP"
    
    headers = {
        "content-type": "application/json"
    }
    
    body = {
        "grant_type": "client_credentials",
        "appkey": _env.my_app,
        "appsecret": _env.my_sec
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        
        data = response.json()
        
        access_token = data.get("access_token", "")
        expires_in = data.get("expires_in", 86400)  # 기본 24시간
        
        if not access_token:
            logger.error(f"토큰 발급 실패: {data}")
            return ""
        
        # 캐시 저장
        cache_data = {
            "access_token": access_token,
            "expires_at": time.time() + expires_in,
            "token_type": data.get("token_type", "Bearer"),
        }
        
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)
        
        logger.info(f"새 토큰 발급 완료 (만료: {expires_in}초)")
        return access_token
        
    except Exception as e:
        logger.error(f"토큰 발급 오류: {e}")
        return ""


def _get_hashkey(body: Dict) -> str:
    """
    해시키 발급 (주문 시 필요)
    
    공식 API: POST /uapi/hashkey
    """
    url = f"{_env.my_url}/uapi/hashkey"
    
    headers = {
        "content-type": "application/json",
        "appkey": _env.my_app,
        "appsecret": _env.my_sec,
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        
        data = response.json()
        return data.get("HASH", "")
        
    except Exception as e:
        logger.error(f"해시키 발급 오류: {e}")
        return ""


# =============================================================================
# API 응답 클래스 (공식 패턴)
# =============================================================================

class APIResponse:
    """API 응답 래퍼 (공식 패턴: APIResp)"""
    
    def __init__(self, response: requests.Response):
        self.response = response
        self._data = None
        
        try:
            self._data = response.json()
        except:
            self._data = {}
    
    def isOK(self) -> bool:
        """성공 여부 확인"""
        if self.response.status_code != 200:
            return False
        
        # rt_cd: 0이면 성공
        rt_cd = self._data.get("rt_cd", "1")
        return rt_cd == "0"
    
    def getBody(self):
        """응답 본문 반환"""
        return _DictWrapper(self._data)
    
    def getMessage(self) -> str:
        """응답 메시지"""
        return self._data.get("msg1", "")
    
    def getReturnCode(self) -> str:
        """리턴 코드"""
        return self._data.get("rt_cd", "")
    
    def printError(self):
        """에러 출력"""
        logger.error(f"API 오류: {self.getMessage()}")
        logger.error(f"리턴코드: {self.getReturnCode()}")
        logger.error(f"상세: {self._data}")
    
    def getHeader(self, key: str) -> str:
        """응답 헤더 조회"""
        return self.response.headers.get(key, "")


class _DictWrapper:
    """딕셔너리 래퍼 (점 표기법 지원)"""
    
    def __init__(self, data: Dict):
        self._data = data
    
    def __getattr__(self, key):
        value = self._data.get(key)
        if isinstance(value, dict):
            return _DictWrapper(value)
        return value
    
    def __getitem__(self, key):
        return self._data.get(key)
    
    def get(self, key, default=None):
        return self._data.get(key, default)


# =============================================================================
# API 호출 함수
# =============================================================================

def _url_fetch(url_path: str, tr_id: str, params: Dict, method: str = "GET") -> APIResponse:
    """
    API 호출 공통 함수
    
    Args:
        url_path: API 경로 (예: /uapi/domestic-stock/v1/quotations/inquire-price)
        tr_id: 거래ID (예: FHKST01010100)
        params: 요청 파라미터
        method: HTTP 메서드 (GET/POST)
    
    Returns:
        APIResponse 객체
    """
    url = f"{_env.my_url}{url_path}"
    
    headers = _base_headers.copy()
    headers["tr_id"] = tr_id
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        else:
            # POST 요청은 해시키 필요
            if "CANO" in params:  # 주문 관련 API
                hashkey = _get_hashkey(params)
                if hashkey:
                    headers["hashkey"] = hashkey
            response = requests.post(url, headers=headers, json=params)
        
        return APIResponse(response)
        
    except Exception as e:
        logger.error(f"API 호출 오류: {e}")
        logger.error(f"URL: {url}")
        logger.error(f"Headers: {headers}")
        logger.error(f"Params: {params}")
        
        # 빈 응답 반환
        class EmptyResponse:
            status_code = 500
            text = str(e)
            def json(self):
                return {"rt_cd": "1", "msg1": str(e)}
        
        return APIResponse(EmptyResponse())


def invoke_api(url_path: str, tr_id: str, params: Dict, method: str = "GET") -> APIResponse:
    """
    API 호출 (외부 모듈용 래퍼)
    
    Args:
        url_path: API 경로
        tr_id: 거래ID
        params: 요청 파라미터
        method: HTTP 메서드 (GET/POST)
    
    Returns:
        APIResponse 객체
    """
    return _url_fetch(url_path, tr_id, params, method)



# =============================================================================
# 국내주식 시세 조회 (domestic_stock_functions.py 패턴)
# =============================================================================

def inquire_price(fid_input_iscd: str) -> Dict:
    """
    주식 현재가 시세 조회
    
    공식 API: GET /uapi/domestic-stock/v1/quotations/inquire-price
    TR ID: FHKST01010100
    
    Args:
        fid_input_iscd: 종목코드 (예: "005930" 삼성전자)
    
    Returns:
        시세 정보 딕셔너리
    """
    url = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = "FHKST01010100"
    
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",  # J: 주식, ETF, ETN
        "FID_INPUT_ISCD": fid_input_iscd
    }
    
    resp = _url_fetch(url, tr_id, params, "GET")
    
    if resp.isOK():
        output = resp.getBody().output
        return {
            "stck_prpr": int(output.get("stck_prpr", 0)),  # 현재가
            "prdy_vrss": int(output.get("prdy_vrss", 0)),  # 전일대비
            "prdy_vrss_sign": output.get("prdy_vrss_sign", ""),  # 전일대비부호
            "prdy_ctrt": float(output.get("prdy_ctrt", 0)),  # 전일대비율
            "acml_vol": int(output.get("acml_vol", 0)),  # 누적거래량
            "acml_tr_pbmn": int(output.get("acml_tr_pbmn", 0)),  # 누적거래대금
            "stck_oprc": int(output.get("stck_oprc", 0)),  # 시가
            "stck_hgpr": int(output.get("stck_hgpr", 0)),  # 고가
            "stck_lwpr": int(output.get("stck_lwpr", 0)),  # 저가
            "per": float(output.get("per", 0)),  # PER
            "pbr": float(output.get("pbr", 0)),  # PBR
            "eps": float(output.get("eps", 0)),  # EPS
            "bps": float(output.get("bps", 0)),  # BPS
        }
    else:
        resp.printError()
        return {}


def inquire_daily_price(fid_input_iscd: str, period: str = "D", adj_price: str = "1") -> list:
    """
    주식 일봉 조회
    
    공식 API: GET /uapi/domestic-stock/v1/quotations/inquire-daily-price
    TR ID: FHKST01010400
    
    Args:
        fid_input_iscd: 종목코드
        period: D(일), W(주), M(월), Y(년)
        adj_price: 0(수정안함), 1(수정주가 반영)
    
    Returns:
        일봉 데이터 리스트
    """
    url = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    tr_id = "FHKST01010400"
    
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": fid_input_iscd,
        "FID_PERIOD_DIV_CODE": period,
        "FID_ORG_ADJ_PRC": adj_price,
    }
    
    resp = _url_fetch(url, tr_id, params, "GET")
    
    if resp.isOK():
        output = resp.getBody().output
        if isinstance(output, list):
            return output
        return [output] if output else []
    else:
        resp.printError()
        return []


# =============================================================================
# 계좌 조회
# =============================================================================

def inquire_balance() -> Dict:
    """
    계좌 잔고 조회
    
    공식 API: GET /uapi/domestic-stock/v1/trading/inquire-balance
    TR ID: 
        - 실전: TTTC8434R
        - 모의: VTTC8434R
    
    Returns:
        잔고 정보 딕셔너리
    """
    url = "/uapi/domestic-stock/v1/trading/inquire-balance"
    
    # 모의투자/실전투자 구분
    if "vts" in _env.my_url:
        tr_id = "VTTC8434R"
    else:
        tr_id = "TTTC8434R"
    
    params = {
        "CANO": _env.my_acct,
        "ACNT_PRDT_CD": _env.my_prod,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }
    
    resp = _url_fetch(url, tr_id, params, "GET")
    
    if resp.isOK():
        body = resp.getBody()
        output1 = body.output1  # 보유종목
        output2 = body.output2  # 계좌요약
        
        # 보유종목 파싱
        positions = []
        if output1:
            for item in output1:
                if isinstance(item, dict) and int(item.get("hldg_qty", 0)) > 0:
                    positions.append({
                        "pdno": item.get("pdno", ""),  # 종목코드
                        "prdt_name": item.get("prdt_name", ""),  # 종목명
                        "hldg_qty": int(item.get("hldg_qty", 0)),  # 보유수량
                        "pchs_avg_pric": float(item.get("pchs_avg_pric", 0)),  # 평균단가
                        "pchs_amt": int(item.get("pchs_amt", 0)),  # 매입금액
                        "prpr": int(item.get("prpr", 0)),  # 현재가
                        "evlu_amt": int(item.get("evlu_amt", 0)),  # 평가금액
                        "evlu_pfls_amt": int(item.get("evlu_pfls_amt", 0)),  # 평가손익
                        "evlu_pfls_rt": float(item.get("evlu_pfls_rt", 0)),  # 수익률
                    })
        
        # 계좌요약
        summary = {}
        if output2 and len(output2) > 0:
            out2 = output2[0] if isinstance(output2, list) else output2
            summary = {
                "dnca_tot_amt": int(out2.get("dnca_tot_amt", 0)),  # 예수금총액
                "nxdy_excc_amt": int(out2.get("nxdy_excc_amt", 0)),  # 익일정산금액
                "prvs_rcdl_excc_amt": int(out2.get("prvs_rcdl_excc_amt", 0)),  # 가수도정산금액
                "cma_evlu_amt": int(out2.get("cma_evlu_amt", 0)),  # CMA평가금액
                "bfdy_buy_amt": int(out2.get("bfdy_buy_amt", 0)),  # 전일매수금액
                "thdt_buy_amt": int(out2.get("thdt_buy_amt", 0)),  # 금일매수금액
                "tot_evlu_amt": int(out2.get("tot_evlu_amt", 0)),  # 총평가금액
                "nass_amt": int(out2.get("nass_amt", 0)),  # 순자산금액
                "pchs_amt_smtl": int(out2.get("pchs_amt_smtl_amt", 0)),  # 매입금액합계
                "evlu_amt_smtl": int(out2.get("evlu_amt_smtl_amt", 0)),  # 평가금액합계
                "evlu_pfls_smtl": int(out2.get("evlu_pfls_smtl_amt", 0)),  # 평가손익합계
            }
        
        return {
            "positions": positions,
            "summary": summary,
        }
    else:
        resp.printError()
        return {"positions": [], "summary": {}}


def inquire_psbl_order(pdno: str, ord_unpr: int = 0) -> int:
    """
    매수가능조회
    
    공식 API: GET /uapi/domestic-stock/v1/trading/inquire-psbl-order
    TR ID: 
        - 실전: TTTC8908R
        - 모의: VTTC8908R
    
    Args:
        pdno: 종목코드
        ord_unpr: 주문단가 (0이면 시장가)
    
    Returns:
        매수가능수량
    """
    url = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"
    
    if "vts" in _env.my_url:
        tr_id = "VTTC8908R"
    else:
        tr_id = "TTTC8908R"
    
    params = {
        "CANO": _env.my_acct,
        "ACNT_PRDT_CD": _env.my_prod,
        "PDNO": pdno,
        "ORD_UNPR": str(ord_unpr),
        "ORD_DVSN": "00" if ord_unpr > 0 else "01",  # 00: 지정가, 01: 시장가
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "N",
    }
    
    resp = _url_fetch(url, tr_id, params, "GET")
    
    if resp.isOK():
        output = resp.getBody().output
        return int(output.get("ord_psbl_qty", 0))
    else:
        resp.printError()
        return 0


# =============================================================================
# 주문 실행
# =============================================================================

def do_order(
    pdno: str,
    ord_qty: int,
    ord_unpr: int = 0,
    buy_flag: bool = True,
    ord_dvsn: str = "00"
) -> Dict:
    """
    주식 매수/매도 주문
    
    공식 API: POST /uapi/domestic-stock/v1/trading/order-cash
    TR ID:
        - 실전: TTTC0802U (매수), TTTC0801U (매도)
        - 모의: VTTC0802U (매수), VTTC0801U (매도)
    
    Args:
        pdno: 종목코드
        ord_qty: 주문수량
        ord_unpr: 주문단가 (0이면 시장가)
        buy_flag: True면 매수, False면 매도
        ord_dvsn: 주문구분
            "00": 지정가
            "01": 시장가
            "02": 조건부지정가
            "03": 최유리지정가
            "04": 최우선지정가
            "05": 장전시간외
            "06": 장후시간외
    
    Returns:
        주문 결과 딕셔너리
    """
    url = "/uapi/domestic-stock/v1/trading/order-cash"
    
    # TR ID 설정
    if "vts" in _env.my_url:
        tr_id = "VTTC0802U" if buy_flag else "VTTC0801U"
    else:
        tr_id = "TTTC0802U" if buy_flag else "TTTC0801U"
    
    # 시장가일 경우
    if ord_unpr == 0:
        ord_dvsn = "01"  # 시장가
    
    params = {
        "CANO": _env.my_acct,
        "ACNT_PRDT_CD": _env.my_prod,
        "PDNO": pdno,
        "ORD_DVSN": ord_dvsn,
        "ORD_QTY": str(ord_qty),
        "ORD_UNPR": str(ord_unpr),
        "CTAC_TLNO": "",
        "SLL_TYPE": "01",
        "ALGO_NO": "",
    }
    
    resp = _url_fetch(url, tr_id, params, "POST")
    
    if resp.isOK():
        output = resp.getBody().output
        return {
            "success": True,
            "odno": output.get("ODNO", ""),  # 주문번호
            "ord_tmd": output.get("ORD_TMD", ""),  # 주문시각
            "message": resp.getMessage(),
        }
    else:
        resp.printError()
        return {
            "success": False,
            "odno": "",
            "ord_tmd": "",
            "message": resp.getMessage(),
        }


def buy_order(pdno: str, ord_qty: int, ord_unpr: int = 0) -> Dict:
    """
    매수 주문
    
    Args:
        pdno: 종목코드
        ord_qty: 주문수량
        ord_unpr: 주문단가 (0이면 시장가)
    """
    return do_order(pdno, ord_qty, ord_unpr, buy_flag=True)


def sell_order(pdno: str, ord_qty: int, ord_unpr: int = 0) -> Dict:
    """
    매도 주문
    
    Args:
        pdno: 종목코드
        ord_qty: 주문수량
        ord_unpr: 주문단가 (0이면 시장가)
    """
    return do_order(pdno, ord_qty, ord_unpr, buy_flag=False)


def cancel_order(
    orgn_odno: str,
    pdno: str,
    ord_qty: int,
    ord_unpr: int = 0,
    qty_all_yn: str = "Y"
) -> Dict:
    """
    주문 취소
    
    공식 API: POST /uapi/domestic-stock/v1/trading/order-rvsecncl
    TR ID:
        - 실전: TTTC0803U
        - 모의: VTTC0803U
    
    Args:
        orgn_odno: 원주문번호
        pdno: 종목코드
        ord_qty: 취소수량
        ord_unpr: 주문단가
        qty_all_yn: 전량여부 (Y/N)
    
    Returns:
        취소 결과
    """
    url = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
    
    if "vts" in _env.my_url:
        tr_id = "VTTC0803U"
    else:
        tr_id = "TTTC0803U"
    
    params = {
        "CANO": _env.my_acct,
        "ACNT_PRDT_CD": _env.my_prod,
        "KRX_FWDG_ORD_ORGNO": "",  # (Null 값 설정) 주문시 한국투자증권 시스템에서 지정된 영업점코드
        "ORGN_ODNO": orgn_odno,
        "ORD_DVSN": "00",  # 지정가
        "RVSE_CNCL_DVSN_CD": "02",  # 02: 취소
        "ORD_QTY": str(ord_qty),
        "ORD_UNPR": str(ord_unpr),
        "QTY_ALL_ORD_YN": qty_all_yn,
    }
    
    resp = _url_fetch(url, tr_id, params, "POST")
    
    if resp.isOK():
        output = resp.getBody().output
        return {
            "success": True,
            "odno": output.get("ODNO", ""),
            "message": resp.getMessage(),
        }
    else:
        resp.printError()
        return {
            "success": False,
            "odno": "",
            "message": resp.getMessage(),
        }


def inquire_daily_ccld(start_date: str = "", end_date: str = "") -> list:
    """
    일별 체결 내역 조회
    
    공식 API: GET /uapi/domestic-stock/v1/trading/inquire-daily-ccld
    TR ID:
        - 실전: TTTC8001R
        - 모의: VTTC8001R
    
    Args:
        start_date: 시작일자 (YYYYMMDD)
        end_date: 종료일자 (YYYYMMDD)
    
    Returns:
        체결 내역 리스트
    """
    url = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
    
    if "vts" in _env.my_url:
        tr_id = "VTTC8001R"
    else:
        tr_id = "TTTC8001R"
    
    # 기본값: 오늘
    if not start_date:
        start_date = datetime.now().strftime("%Y%m%d")
    if not end_date:
        end_date = start_date
    
    params = {
        "CANO": _env.my_acct,
        "ACNT_PRDT_CD": _env.my_prod,
        "INQR_STRT_DT": start_date,
        "INQR_END_DT": end_date,
        "SLL_BUY_DVSN_CD": "00",  # 00: 전체, 01: 매도, 02: 매수
        "INQR_DVSN": "00",  # 00: 역순, 01: 정순
        "PDNO": "",
        "CCLD_DVSN": "00",  # 00: 전체, 01: 체결, 02: 미체결
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "INQR_DVSN_3": "00",  # 00: 전체, 01: 현금, 02: 융자, 03: 대출, 04: 대주
        "INQR_DVSN_1": "",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }
    
    resp = _url_fetch(url, tr_id, params, "GET")
    
    if resp.isOK():
        output = resp.getBody().output1
        if not output:
            return []
        
        results = []
        for item in output:
            if isinstance(item, dict):
                results.append({
                    "ord_dt": item.get("ord_dt", ""),  # 주문일자
                    "ord_tmd": item.get("ord_tmd", ""),  # 주문시각
                    "odno": item.get("odno", ""),  # 주문번호
                    "pdno": item.get("pdno", ""),  # 종목코드
                    "prdt_name": item.get("prdt_name", ""),  # 종목명
                    "sll_buy_dvsn_cd": item.get("sll_buy_dvsn_cd", ""),  # 매도매수구분
                    "ord_qty": int(item.get("ord_qty", 0)),  # 주문수량
                    "ord_unpr": int(item.get("ord_unpr", 0)),  # 주문단가
                    "tot_ccld_qty": int(item.get("tot_ccld_qty", 0)),  # 총체결수량
                    "avg_prvs": int(item.get("avg_prvs", 0)),  # 평균가
                    "cncl_yn": item.get("cncl_yn", ""),  # 취소여부
                })
        
        return results
    else:
        resp.printError()
        return []


# =============================================================================
# 데모 / 테스트
# =============================================================================

def run_demo():
    """API 데모 실행"""
    print("=" * 70)
    print("🏦 한국투자증권 Open API 클라이언트 - 공식 패턴")
    print("=" * 70)
    
    # 1. 인증
    print("\n1️⃣ 인증 초기화")
    if not auth(svr="vps", product="01"):  # 모의투자
        print("❌ 인증 실패. kis_devlp.yaml 파일을 확인하세요.")
        create_sample_config()
        return
    
    print("✅ 인증 성공!")
    print(f"  - 환경: {'모의투자' if 'vts' in _env.my_url else '실전투자'}")
    print(f"  - 계좌: {_env.my_acct}-{_env.my_prod}")
    
    # 2. 시세 조회
    print("\n2️⃣ 삼성전자 시세 조회")
    price_info = inquire_price("005930")
    
    if price_info:
        print(f"  현재가: {price_info['stck_prpr']:,}원")
        print(f"  전일대비: {price_info['prdy_vrss']:,}원 ({price_info['prdy_ctrt']}%)")
        print(f"  거래량: {price_info['acml_vol']:,}주")
        print(f"  PER: {price_info['per']}")
        print(f"  PBR: {price_info['pbr']}")
    else:
        print("  시세 조회 실패")
    
    # 3. 계좌 잔고
    print("\n3️⃣ 계좌 잔고 조회")
    balance = inquire_balance()
    
    if balance:
        summary = balance.get("summary", {})
        positions = balance.get("positions", [])
        
        print(f"  예수금: {summary.get('dnca_tot_amt', 0):,}원")
        print(f"  총평가금액: {summary.get('tot_evlu_amt', 0):,}원")
        print(f"  평가손익: {summary.get('evlu_pfls_smtl', 0):,}원")
        
        if positions:
            print(f"\n  보유종목:")
            for pos in positions[:5]:
                print(f"    - {pos['prdt_name']} ({pos['pdno']})")
                print(f"      수량: {pos['hldg_qty']}주, 수익률: {pos['evlu_pfls_rt']}%")
    else:
        print("  잔고 조회 실패")
    
    # 4. 매수가능조회
    print("\n4️⃣ 삼성전자 매수가능수량 조회")
    qty = inquire_psbl_order("005930", 70000)
    print(f"  70,000원 기준 매수가능: {qty}주")
    
    # 5. 체결내역
    print("\n5️⃣ 당일 체결내역 조회")
    orders = inquire_daily_ccld()
    
    if orders:
        print(f"  총 {len(orders)}건의 주문")
        for order in orders[:3]:
            side = "매수" if order["sll_buy_dvsn_cd"] == "02" else "매도"
            print(f"    - {order['prdt_name']} {side} {order['ord_qty']}주 @ {order['ord_unpr']:,}원")
    else:
        print("  주문 내역 없음")
    
    print("\n" + "=" * 70)
    print("✅ 데모 완료!")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(message)s"
    )
    run_demo()
