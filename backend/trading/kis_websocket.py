"""
한국투자증권 WebSocket 실시간 시세 클라이언트

공식 GitHub 패턴 기반:
https://github.com/koreainvestment/open-trading-api/blob/main/websocket/python/

주요 기능:
- 실시간 체결가 구독
- 실시간 호가 구독
- 체결통보 수신
- AES256 복호화

참고: websocket/python/ws_domestic_overseas_all.py
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from base64 import b64decode

import websockets
import yaml

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    print("⚠️ pycryptodome 설치 필요: pip install pycryptodome")

logger = logging.getLogger(__name__)


# =============================================================================
# 설정
# =============================================================================

# WebSocket URL
WS_URL_REAL = "ws://ops.koreainvestment.com:21000"
WS_URL_PAPER = "ws://ops.koreainvestment.com:31000"  # 모의투자

# 구독 타입
SUBSCRIBE_TYPES = {
    "H0STCNT0": "주식 체결가",       # 실시간 체결가
    "H0STASP0": "주식 호가",         # 실시간 호가
    "H0STCNI0": "주식 체결통보",     # 체결 통보
    "H0STCNI9": "주식 잔고변동",     # 잔고 변동
}


# =============================================================================
# AES256 복호화
# =============================================================================

def aes_cbc_base64_dec(key: str, iv: str, cipher_text: str) -> str:
    """
    AES256 CBC 복호화
    
    공식 패턴: aes_cbc_base64_dec()
    """
    if not HAS_CRYPTO:
        return cipher_text
    
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    decrypted = unpad(cipher.decrypt(b64decode(cipher_text)), AES.block_size)
    return bytes.decode(decrypted)


# =============================================================================
# WebSocket 접속키 발급
# =============================================================================

def get_websocket_approval(app_key: str, app_secret: str, is_paper: bool = True) -> Dict[str, str]:
    """
    WebSocket 접속키 발급
    
    공식 API: POST /oauth2/Approval
    
    Returns:
        {"approval_key": "...", "iv": "...", "key": "..."}
    """
    import requests
    
    if is_paper:
        url = "https://openapivts.koreainvestment.com:29443/oauth2/Approval"
    else:
        url = "https://openapi.koreainvestment.com:9443/oauth2/Approval"
    
    headers = {
        "content-type": "application/json"
    }
    
    body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "secretkey": app_secret
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "approval_key": data.get("approval_key", ""),
            "iv": data.get("approval_key", "")[:16],  # IV는 앞 16자리
            "key": data.get("approval_key", "")[-32:],  # Key는 뒤 32자리
        }
        
    except Exception as e:
        logger.error(f"WebSocket 접속키 발급 실패: {e}")
        return {}


# =============================================================================
# 데이터 파싱 (공식 패턴)
# =============================================================================

def parse_stock_price(data: str) -> Dict[str, Any]:
    """
    주식 체결가 파싱
    
    공식 형식: 파이프(|)로 구분된 필드
    """
    fields = data.split('^')
    
    if len(fields) < 20:
        return {}
    
    return {
        "ticker": fields[0],           # 유가증권단축종목코드
        "time": fields[1],             # 주식체결시간
        "price": int(fields[2]),       # 주식현재가
        "change_sign": fields[3],      # 전일대비부호
        "change": int(fields[4]),      # 전일대비
        "change_rate": float(fields[5]),  # 등락율
        "open": int(fields[7]),        # 시가
        "high": int(fields[8]),        # 고가
        "low": int(fields[9]),         # 저가
        "volume": int(fields[13]),     # 누적거래량
        "amount": int(fields[14]),     # 누적거래대금
    }


def parse_stock_asking(data: str) -> Dict[str, Any]:
    """
    주식 호가 파싱
    """
    fields = data.split('^')
    
    if len(fields) < 30:
        return {}
    
    return {
        "ticker": fields[0],           # 종목코드
        "time": fields[1],             # 호가시간
        "ask_price1": int(fields[3]),  # 매도호가1
        "bid_price1": int(fields[13]), # 매수호가1
        "ask_qty1": int(fields[23]),   # 매도호가잔량1
        "bid_qty1": int(fields[33]),   # 매수호가잔량1
        "total_ask_qty": int(fields[43]),  # 총매도호가잔량
        "total_bid_qty": int(fields[44]),  # 총매수호가잔량
    }


def parse_execution_notice(data: str) -> Dict[str, Any]:
    """
    체결통보 파싱 (암호화됨)
    """
    fields = data.split('^')
    
    if len(fields) < 10:
        return {}
    
    return {
        "ticker": fields[1],           # 종목코드
        "order_no": fields[2],         # 주문번호
        "order_qty": int(fields[5]),   # 주문수량
        "order_price": int(fields[6]), # 주문가격
        "exec_qty": int(fields[7]),    # 체결수량
        "exec_price": int(fields[8]),  # 체결가격
        "side": "BUY" if fields[4] == "02" else "SELL",  # 매수/매도
    }


# =============================================================================
# WebSocket 클라이언트
# =============================================================================

class KISWebSocket:
    """
    한국투자증권 WebSocket 클라이언트
    
    공식 패턴: KISWebSocket 클래스
    """
    
    def __init__(
        self,
        app_key: str = "",
        app_secret: str = "",
        is_paper: bool = True,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        """
        Args:
            app_key: 앱키
            app_secret: 앱시크릿
            is_paper: 모의투자 여부
            on_message: 메시지 콜백
            on_error: 에러 콜백
        """
        self.app_key = app_key or os.environ.get("KIS_APP_KEY", "")
        self.app_secret = app_secret or os.environ.get("KIS_APP_SECRET", "")
        self.is_paper = is_paper
        
        self.ws_url = WS_URL_PAPER if is_paper else WS_URL_REAL
        
        self.on_message = on_message or self._default_on_message
        self.on_error = on_error or self._default_on_error
        
        self.approval_key = ""
        self.iv = ""
        self.key = ""
        
        self.websocket = None
        self.subscriptions: List[str] = []
        self.running = False
    
    def _default_on_message(self, data: Dict):
        """기본 메시지 핸들러"""
        logger.info(f"수신: {data}")
    
    def _default_on_error(self, error: Exception):
        """기본 에러 핸들러"""
        logger.error(f"WebSocket 에러: {error}")
    
    def get_approval(self) -> bool:
        """WebSocket 접속키 발급"""
        result = get_websocket_approval(self.app_key, self.app_secret, self.is_paper)
        
        if result:
            self.approval_key = result["approval_key"]
            self.iv = result["iv"]
            self.key = result["key"]
            logger.info("WebSocket 접속키 발급 완료")
            return True
        else:
            return False
    
    def _build_subscribe_message(
        self,
        tr_id: str,
        tr_key: str,
        tr_type: str = "1"
    ) -> str:
        """
        구독 요청 메시지 생성
        
        공식 형식:
        {
            "header": {
                "approval_key": "...",
                "custtype": "P",  # 개인
                "tr_type": "1",   # 1: 등록, 2: 해제
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "H0STCNT0",  # 체결가
                    "tr_key": "005930"    # 종목코드
                }
            }
        }
        """
        message = {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": tr_type,
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": tr_id,
                    "tr_key": tr_key
                }
            }
        }
        return json.dumps(message)
    
    def _parse_message(self, message: str) -> Dict:
        """
        수신 메시지 파싱
        
        공식 형식:
        - 0: 실시간 데이터
        - 1: 응답 메시지
        """
        # 응답 메시지 (JSON)
        if message.startswith("{"):
            data = json.loads(message)
            return {
                "type": "response",
                "data": data
            }
        
        # 실시간 데이터 (구분자: |)
        parts = message.split('|')
        
        if len(parts) < 4:
            return {"type": "unknown", "raw": message}
        
        header = parts[0]  # 0: 암호화안함, 1: 암호화
        tr_id = parts[1]   # 거래ID
        count = int(parts[2])  # 데이터 건수
        data = parts[3]    # 데이터
        
        # 암호화 여부
        is_encrypted = header == "1"
        
        # 복호화
        if is_encrypted and HAS_CRYPTO:
            data = aes_cbc_base64_dec(self.key, self.iv, data)
        
        # 데이터 파싱
        parsed = {}
        
        if tr_id == "H0STCNT0":  # 체결가
            parsed = parse_stock_price(data)
            parsed["type"] = "price"
        elif tr_id == "H0STASP0":  # 호가
            parsed = parse_stock_asking(data)
            parsed["type"] = "asking"
        elif tr_id == "H0STCNI0":  # 체결통보
            parsed = parse_execution_notice(data)
            parsed["type"] = "execution"
        else:
            parsed = {"type": "other", "tr_id": tr_id, "data": data}
        
        return parsed
    
    async def connect(self):
        """WebSocket 연결"""
        if not self.approval_key:
            if not self.get_approval():
                raise Exception("WebSocket 접속키 발급 실패")
        
        logger.info(f"WebSocket 연결: {self.ws_url}")
        self.websocket = await websockets.connect(self.ws_url, ping_interval=30)
        self.running = True
        logger.info("WebSocket 연결 성공")
    
    async def disconnect(self):
        """WebSocket 연결 해제"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        logger.info("WebSocket 연결 해제")
    
    async def subscribe(self, tr_id: str, ticker: str):
        """
        실시간 데이터 구독
        
        Args:
            tr_id: 거래ID (예: H0STCNT0)
            ticker: 종목코드 (예: 005930)
        """
        if not self.websocket:
            raise Exception("WebSocket 연결 필요")
        
        message = self._build_subscribe_message(tr_id, ticker, "1")
        await self.websocket.send(message)
        
        self.subscriptions.append(f"{tr_id}:{ticker}")
        logger.info(f"구독: {tr_id} - {ticker}")
    
    async def unsubscribe(self, tr_id: str, ticker: str):
        """구독 해제"""
        if not self.websocket:
            return
        
        message = self._build_subscribe_message(tr_id, ticker, "2")
        await self.websocket.send(message)
        
        key = f"{tr_id}:{ticker}"
        if key in self.subscriptions:
            self.subscriptions.remove(key)
        logger.info(f"구독 해제: {tr_id} - {ticker}")
    
    async def subscribe_price(self, ticker: str):
        """체결가 구독"""
        await self.subscribe("H0STCNT0", ticker)
    
    async def subscribe_asking(self, ticker: str):
        """호가 구독"""
        await self.subscribe("H0STASP0", ticker)
    
    async def listen(self):
        """메시지 수신 루프"""
        if not self.websocket:
            raise Exception("WebSocket 연결 필요")
        
        try:
            while self.running:
                message = await self.websocket.recv()
                parsed = self._parse_message(message)
                
                # 콜백 호출
                self.on_message(parsed)
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket 연결 종료")
        except Exception as e:
            self.on_error(e)
    
    async def run(self, tickers: List[str], duration: int = 60):
        """
        실시간 시세 수신 실행
        
        Args:
            tickers: 종목코드 리스트
            duration: 실행 시간 (초)
        """
        await self.connect()
        
        try:
            # 구독
            for ticker in tickers:
                await self.subscribe_price(ticker)
                await asyncio.sleep(0.1)
            
            # 수신 태스크
            listen_task = asyncio.create_task(self.listen())
            
            # 지정 시간 동안 실행
            await asyncio.sleep(duration)
            
            # 종료
            self.running = False
            listen_task.cancel()
            
        finally:
            await self.disconnect()


# =============================================================================
# 데모 / 테스트
# =============================================================================

async def run_demo():
    """WebSocket 데모"""
    print("=" * 70)
    print("📡 한국투자증권 WebSocket 실시간 시세 - 데모")
    print("=" * 70)
    
    # 환경변수 확인
    app_key = os.environ.get("KIS_APP_KEY", "")
    app_secret = os.environ.get("KIS_APP_SECRET", "")
    
    if not app_key or not app_secret:
        print("\n⚠️ API 키가 설정되지 않았습니다.")
        print("\n환경변수 설정 방법:")
        print('  $env:KIS_APP_KEY = "your_app_key"')
        print('  $env:KIS_APP_SECRET = "your_app_secret"')
        print("\n데모 모드로 구조만 테스트합니다...")
        
        # 데모 메시지 파싱 테스트
        print("\n📊 메시지 파싱 테스트:")
        
        # 체결가 샘플 데이터
        sample_price = "005930^093015^71000^5^-500^-0.70^71000^71500^71000^70800^71200^70900^15000^1500000^106500000^5000^5200^-200^50.00^750000^760000^1^50.80^15.50"
        parsed = parse_stock_price(sample_price)
        print(f"  체결가: {parsed}")
        
        return
    
    # 메시지 핸들러
    def on_message(data: Dict):
        if data.get("type") == "price":
            print(f"📈 {data['ticker']}: {data['price']:,}원 ({data['change_rate']:+.2f}%)")
        elif data.get("type") == "response":
            print(f"📩 응답: {data['data']}")
        else:
            print(f"📨 {data}")
    
    # WebSocket 클라이언트
    ws = KISWebSocket(
        app_key=app_key,
        app_secret=app_secret,
        is_paper=True,  # 모의투자
        on_message=on_message
    )
    
    print("\n1️⃣ WebSocket 접속키 발급")
    if not ws.get_approval():
        print("❌ 접속키 발급 실패")
        return
    print("✅ 접속키 발급 성공")
    
    print("\n2️⃣ 실시간 시세 수신 (10초)")
    tickers = ["005930", "000660"]  # 삼성전자, SK하이닉스
    print(f"  종목: {tickers}")
    
    await ws.run(tickers, duration=10)
    
    print("\n" + "=" * 70)
    print("✅ WebSocket 데모 완료!")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(message)s"
    )
    asyncio.run(run_demo())
