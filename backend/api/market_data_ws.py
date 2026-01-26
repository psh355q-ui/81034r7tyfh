"""
Market Data WebSocket Manager

실시간 시장 데이터 스트리밍을 위한 WebSocket 관리자

기능:
1. 실시간 주가 스트리밍 (yfinance 사용)
2. 심볼별 구독 관리
3. 다중 클라이언트 지원
4. 연결 상태 모니터링

참고: Phase 4 - Real-time Execution 완성
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Set, List, Dict
import asyncio
import yfinance as yf
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketDataWebSocketManager:
    """실시간 시장 데이터 스트리밍을 위한 WebSocket 관리자"""

    def __init__(self):
        self.active_connections: Dict[WebSocket, Set[str]] = {}
        self.quote_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = True

    async def connect(self, websocket: WebSocket):
        """WebSocket 연결 수락"""
        await websocket.accept()
        self.active_connections[websocket] = set()
        logger.info(f"[MarketDataWS] 새 연결. 총 연결 수: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 제거"""
        if websocket in self.active_connections:
            symbols = self.active_connections[websocket]
            del self.active_connections[websocket]

            # 구독자가 없으면 스트리밍 중지
            for symbol in symbols:
                if not self._has_subscribers(symbol):
                    self._stop_quote_task(symbol)

        logger.info(f"[MarketDataWS] 연결 종료. 총 연결 수: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, symbols: List[str]):
        """심볼 구독"""
        if websocket not in self.active_connections:
            return

        for symbol in symbols:
            self.active_connections[websocket].add(symbol)

            # 스트리밍 태스크가 없으면 시작
            if symbol not in self.quote_tasks:
                self.quote_tasks[symbol] = asyncio.create_task(
                    self._stream_quotes(symbol)
                )
                logger.info(f"[MarketDataWS] {symbol} 스트리밍 시작")

    async def unsubscribe(self, websocket: WebSocket, symbols: List[str]):
        """심볼 구독 해제"""
        if websocket not in self.active_connections:
            return

        for symbol in symbols:
            self.active_connections[websocket].discard(symbol)

            # 구독자가 없으면 스트리밍 중지
            if not self._has_subscribers(symbol):
                self._stop_quote_task(symbol)
                logger.info(f"[MarketDataWS] {symbol} 스트리밍 중지")

    async def _stream_quotes(self, symbol: str):
        """심볼별 실시간 시세 스트리밍"""
        try:
            retry_count = 0
            max_retries = 3

            while self.is_running:
                try:
                    # 최신 시세 가져오기
                    ticker = yf.Ticker(symbol)
                    info = ticker.info

                    quote = {
                        'symbol': symbol,
                        'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                        'change': info.get('regularMarketChangePercent'),
                        'volume': info.get('volume'),
                        'timestamp': datetime.now().isoformat()
                    }

                    # 구독자에게 브로드캐스트
                    await self._broadcast_to_subscribers(symbol, {
                        'type': 'quote',
                        'data': quote
                    })

                    retry_count = 0  # 성공 시 재시도 카운트 초기화

                    # 5초 대기 (API 제한 고려)
                    await asyncio.sleep(5)

                except Exception as e:
                    retry_count += 1
                    logger.error(f"[MarketDataWS] {symbol} 시세 가져오기 오류 (재시도 {retry_count}/{max_retries}): {e}")

                    if retry_count >= max_retries:
                        logger.error(f"[MarketDataWS] {symbol} 최대 재시도 횟수 초과. 스트리밍 중지.")
                        break

                    # 실패 시 10초 대기 후 재시도
                    await asyncio.sleep(10)

        except asyncio.CancelledError:
            logger.info(f"[MarketDataWS] {symbol} 시세 스트리밍 중지")
        except Exception as e:
            logger.error(f"[MarketDataWS] {symbol} 스트리밍 오류: {e}")

    async def _broadcast_to_subscribers(self, symbol: str, message: Dict):
        """심볼 구독자에게 메시지 브로드캐스트"""
        disconnected = []

        for websocket, symbols in self.active_connections.items():
            if symbol in symbols:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"[MarketDataWS] 브로드캐스트 오류: {e}")
                    disconnected.append(websocket)

        # 연결 끊긴 클라이언트 제거
        for ws in disconnected:
            self.disconnect(ws)

    def _has_subscribers(self, symbol: str) -> bool:
        """심볼 구독자가 있는지 확인"""
        for symbols in self.active_connections.values():
            if symbol in symbols:
                return True
        return False

    def _stop_quote_task(self, symbol: str):
        """시세 스트리밍 태스크 중지"""
        if symbol in self.quote_tasks:
            self.quote_tasks[symbol].cancel()
            del self.quote_tasks[symbol]

    async def broadcast_all(self, message: Dict):
        """모든 연결된 클라이언트에 메시지 브로드캐스트"""
        disconnected = []

        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"[MarketDataWS] 브로드캐스트 오류: {e}")
                disconnected.append(websocket)

        # 연결 끊긴 클라이언트 제거
        for ws in disconnected:
            self.disconnect(ws)

    def get_connection_count(self) -> int:
        """현재 연결 수 반환"""
        return len(self.active_connections)

    def get_subscribed_symbols(self, websocket: WebSocket) -> Set[str]:
        """WebSocket 연결의 구독 심볼 목록 반환"""
        return self.active_connections.get(websocket, set())

    def get_all_subscribed_symbols(self) -> Set[str]:
        """모든 구독 심볼 목록 반환"""
        symbols = set()
        for subscribed in self.active_connections.values():
            symbols.update(subscribed)
        return symbols

    async def shutdown(self):
        """모든 연결 및 태스크 종료"""
        self.is_running = False

        # 모든 스트리밍 태스크 중지
        for symbol in list(self.quote_tasks.keys()):
            self._stop_quote_task(symbol)

        # 모든 연결 종료
        for websocket in list(self.active_connections.keys()):
            try:
                await websocket.close()
            except:
                pass

        self.active_connections.clear()
        logger.info("[MarketDataWS] 모든 연결 및 태스크 종료 완료")


# 전역 인스턴스
market_data_ws_manager = MarketDataWebSocketManager()
