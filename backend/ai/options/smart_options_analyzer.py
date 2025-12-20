"""
Smart Options Analyzer

단순 Put/Call 비율이 아닌, 실제 돈이 어디로 흐르는지 추적
Bid-Ask 기반으로 매수/매도 성향을 판별

핵심 개념:
  Put Volume 증가 시:
  - Case A: 체결가가 Ask(매도호가) 근처 → 매수자가 급함 (Aggressive Buy) → Put 매수 = 하락 베팅 🐻
  - Case B: 체결가가 Bid(매수호가) 근처 → 매도자가 급함 (Aggressive Sell) → Put 매도 = 상승/횡보 베팅 🐂
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from enum import Enum
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TradeSide(Enum):
    """거래 방향"""
    BUY = "BUY"      # Ask 쪽 체결 (급한 매수)
    SELL = "SELL"    # Bid 쪽 체결 (급한 매도)
    NEUTRAL = "NEUTRAL"  # 중간 체결


class Sentiment(Enum):
    """옵션 센티먼트"""
    BULLISH = "BULLISH"      # 강세
    BEARISH = "BEARISH"      # 약세
    NEUTRAL = "NEUTRAL"      # 중립
    VERY_BULLISH = "VERY_BULLISH"  # 매우 강세
    VERY_BEARISH = "VERY_BEARISH"  # 매우 약세


@dataclass
class SmartOptionFlow:
    """Smart Options Flow 분석 결과"""
    ticker: str
    timestamp: datetime
    
    # Premium 흐름
    net_call_premium: float       # Call 순매수 금액
    net_put_premium: float        # Put 순매수 금액
    total_premium: float          # 총 거래 금액
    
    # Delta 흐름 (방향성)
    net_delta: float              # -1 (약세) ~ +1 (강세)
    delta_interpretation: str     # BULLISH / BEARISH / NEUTRAL
    
    # 거래 분석
    call_buy_volume: int          # Call 매수 거래량
    call_sell_volume: int         # Call 매도 거래량
    put_buy_volume: int           # Put 매수 거래량
    put_sell_volume: int          # Put 매도 거래량
    
    # 고래 주문
    whale_orders: List[Dict] = field(default_factory=list)  # $50,000+ 대형 주문
    whale_bullish_pct: float = 0.0  # 고래 중 강세 비율
    
    # 센티먼트
    sentiment: Sentiment = Sentiment.NEUTRAL
    sentiment_score: float = 50.0  # 0 (극도 약세) ~ 100 (극도 강세)
    
    # 상세
    put_call_ratio: float = 1.0
    unusual_activity: bool = False
    key_insights: List[str] = field(default_factory=list)


class SmartOptionsAnalyzer:
    """
    Smart Options Analyzer
    
    Bid-Ask Spread 기반으로 매수/매도 성향을 판별하고
    실제 자금 흐름(Net Premium, Net Delta)을 추적합니다.
    """
    
    def __init__(
        self,
        whale_threshold: float = 50_000,      # 고래 주문 기준 $50K
        bid_ask_buy_pct: float = 0.40,        # Ask 쪽 40% 이내면 BUY
        bid_ask_sell_pct: float = 0.40,       # Bid 쪽 40% 이내면 SELL
        massive_api_client=None,
    ):
        self.whale_threshold = whale_threshold
        self.bid_ask_buy_pct = bid_ask_buy_pct
        self.bid_ask_sell_pct = bid_ask_sell_pct
        self.massive_api_client = massive_api_client
    
    def _determine_trade_side(
        self,
        last: float,
        bid: float,
        ask: float,
    ) -> TradeSide:
        """
        체결가 위치로 매수/매도 판별
        
        Ask 쪽 40% 내 → BUY (급한 매수)
        Bid 쪽 40% 내 → SELL (급한 매도)
        중간 → NEUTRAL
        
        Args:
            last: 체결가
            bid: 매수호가
            ask: 매도호가
            
        Returns:
            TradeSide: 거래 방향
        """
        if bid >= ask or ask <= 0:
            return TradeSide.NEUTRAL
        
        spread = ask - bid
        
        # Ask 쪽 40% 이내 → 급한 매수
        if last >= (ask - spread * self.bid_ask_buy_pct):
            return TradeSide.BUY
        
        # Bid 쪽 40% 이내 → 급한 매도
        elif last <= (bid + spread * self.bid_ask_sell_pct):
            return TradeSide.SELL
        
        return TradeSide.NEUTRAL
    
    async def analyze_flow(
        self,
        ticker: str,
        chain_data: pd.DataFrame = None,
        current_price: float = None,
    ) -> SmartOptionFlow:
        """
        옵션 체인 데이터 분석
        
        Args:
            ticker: 종목 티커
            chain_data: 옵션 체인 데이터 (없으면 API에서 가져옴)
            current_price: 현재 주가 (없으면 API에서 가져옴)
            
        Returns:
            SmartOptionFlow: 분석 결과
        """
        try:
            # 데이터 가져오기
            if chain_data is None:
                chain_data = await self._fetch_options_data(ticker)
            
            if current_price is None:
                current_price = await self._fetch_current_price(ticker)
            
            if chain_data is None or chain_data.empty:
                return self._create_empty_flow(ticker)
            
            # 각 옵션 계약 분석
            call_analysis = await self._analyze_contracts(
                chain_data[chain_data['contract_type'] == 'call'],
                "call",
            )
            put_analysis = await self._analyze_contracts(
                chain_data[chain_data['contract_type'] == 'put'],
                "put",
            )
            
            # Net Delta 계산
            net_delta = self._calculate_net_delta(call_analysis, put_analysis)
            
            # 센티먼트 결정
            sentiment, sentiment_score = self._determine_sentiment(
                call_analysis, put_analysis, net_delta
            )
            
            # 고래 주문 분석
            whale_orders = self._identify_whale_orders(chain_data)
            whale_bullish_pct = self._calculate_whale_bullish_pct(whale_orders)
            
            # 인사이트 생성
            key_insights = self._generate_insights(
                call_analysis, put_analysis, whale_orders, sentiment
            )
            
            # Put/Call 비율
            put_call_ratio = (
                put_analysis['total_volume'] / call_analysis['total_volume']
                if call_analysis['total_volume'] > 0 else 1.0
            )
            
            return SmartOptionFlow(
                ticker=ticker,
                timestamp=datetime.now(),
                net_call_premium=call_analysis['net_premium'],
                net_put_premium=put_analysis['net_premium'],
                total_premium=call_analysis['total_premium'] + put_analysis['total_premium'],
                net_delta=net_delta,
                delta_interpretation=sentiment.value,
                call_buy_volume=call_analysis['buy_volume'],
                call_sell_volume=call_analysis['sell_volume'],
                put_buy_volume=put_analysis['buy_volume'],
                put_sell_volume=put_analysis['sell_volume'],
                whale_orders=whale_orders,
                whale_bullish_pct=whale_bullish_pct,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                put_call_ratio=put_call_ratio,
                unusual_activity=len(whale_orders) >= 3,
                key_insights=key_insights,
            )
            
        except Exception as e:
            logger.error(f"{ticker} 옵션 분석 실패: {e}")
            return self._create_empty_flow(ticker)
    
    async def _analyze_contracts(
        self,
        contracts: pd.DataFrame,
        contract_type: str,
    ) -> Dict:
        """
        옵션 계약 그룹 분석
        
        Args:
            contracts: 옵션 계약 데이터
            contract_type: call 또는 put
            
        Returns:
            분석 결과 딕셔너리
        """
        if contracts.empty:
            return {
                'total_volume': 0,
                'buy_volume': 0,
                'sell_volume': 0,
                'neutral_volume': 0,
                'total_premium': 0,
                'net_premium': 0,
            }
        
        buy_volume = 0
        sell_volume = 0
        neutral_volume = 0
        buy_premium = 0
        sell_premium = 0
        
        for _, row in contracts.iterrows():
            volume = row.get('volume', 0) or 0
            last_price = row.get('lastPrice', row.get('last', 0)) or 0
            bid = row.get('bid', 0) or 0
            ask = row.get('ask', 0) or 0
            
            # 거래 방향 판별
            side = self._determine_trade_side(last_price, bid, ask)
            premium = volume * last_price * 100  # 계약당 100주
            
            if side == TradeSide.BUY:
                buy_volume += volume
                buy_premium += premium
            elif side == TradeSide.SELL:
                sell_volume += volume
                sell_premium += premium
            else:
                neutral_volume += volume
        
        return {
            'total_volume': buy_volume + sell_volume + neutral_volume,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'neutral_volume': neutral_volume,
            'total_premium': buy_premium + sell_premium,
            'net_premium': buy_premium - sell_premium,  # 순매수 금액
        }
    
    def _calculate_net_delta(
        self,
        call_analysis: Dict,
        put_analysis: Dict,
    ) -> float:
        """
        Net Delta 계산
        
        - Call 매수 → +Delta (강세)
        - Call 매도 → -Delta (약세)
        - Put 매수 → -Delta (약세)
        - Put 매도 → +Delta (강세)
        
        Returns:
            -1 ~ +1 사이의 값
        """
        # 가중치 적용
        bullish_signal = (
            call_analysis['buy_volume'] +   # Call 매수 (강세)
            put_analysis['sell_volume']     # Put 매도 (강세)
        )
        bearish_signal = (
            call_analysis['sell_volume'] +  # Call 매도 (약세)
            put_analysis['buy_volume']      # Put 매수 (약세)
        )
        
        total = bullish_signal + bearish_signal
        if total == 0:
            return 0.0
        
        # -1 (순 약세) ~ +1 (순 강세)
        net_delta = (bullish_signal - bearish_signal) / total
        return round(net_delta, 3)
    
    def _determine_sentiment(
        self,
        call_analysis: Dict,
        put_analysis: Dict,
        net_delta: float,
    ) -> tuple:
        """
        센티먼트 결정
        
        Returns:
            (Sentiment, score 0-100)
        """
        # 점수 계산 (0-100)
        score = (net_delta + 1) / 2 * 100  # -1~+1 → 0~100
        score = round(score, 1)
        
        # 센티먼트 결정
        if net_delta >= 0.5:
            sentiment = Sentiment.VERY_BULLISH
        elif net_delta >= 0.2:
            sentiment = Sentiment.BULLISH
        elif net_delta <= -0.5:
            sentiment = Sentiment.VERY_BEARISH
        elif net_delta <= -0.2:
            sentiment = Sentiment.BEARISH
        else:
            sentiment = Sentiment.NEUTRAL
        
        return sentiment, score
    
    def _identify_whale_orders(
        self,
        chain_data: pd.DataFrame,
    ) -> List[Dict]:
        """
        고래 주문 식별 ($50K+)
        """
        whale_orders = []
        
        for _, row in chain_data.iterrows():
            volume = row.get('volume', 0) or 0
            last_price = row.get('lastPrice', row.get('last', 0)) or 0
            premium = volume * last_price * 100
            
            if premium >= self.whale_threshold:
                bid = row.get('bid', 0) or 0
                ask = row.get('ask', 0) or 0
                side = self._determine_trade_side(last_price, bid, ask)
                contract_type = row.get('contract_type', 'unknown')
                
                # 방향성 해석
                if contract_type == 'call':
                    direction = "BULLISH" if side == TradeSide.BUY else "BEARISH"
                else:  # put
                    direction = "BEARISH" if side == TradeSide.BUY else "BULLISH"
                
                whale_orders.append({
                    'strike': row.get('strike'),
                    'expiration': str(row.get('expiration', '')),
                    'contract_type': contract_type,
                    'volume': volume,
                    'premium': round(premium, 2),
                    'trade_side': side.value,
                    'direction': direction,
                })
        
        return whale_orders
    
    def _calculate_whale_bullish_pct(self, whale_orders: List[Dict]) -> float:
        """고래 중 강세 비율"""
        if not whale_orders:
            return 0.5
        
        bullish = sum(1 for w in whale_orders if w['direction'] == 'BULLISH')
        return round(bullish / len(whale_orders), 2)
    
    def _generate_insights(
        self,
        call_analysis: Dict,
        put_analysis: Dict,
        whale_orders: List[Dict],
        sentiment: Sentiment,
    ) -> List[str]:
        """핵심 인사이트 생성"""
        insights = []
        
        # 센티먼트 인사이트
        if sentiment == Sentiment.VERY_BULLISH:
            insights.append("🐂 옵션 시장에서 매우 강한 강세 신호 감지")
        elif sentiment == Sentiment.VERY_BEARISH:
            insights.append("🐻 옵션 시장에서 매우 강한 약세 신호 감지")
        
        # 콜 분석
        if call_analysis['buy_volume'] > call_analysis['sell_volume'] * 2:
            insights.append(f"📈 콜 옵션 순매수 우세 ({call_analysis['buy_volume']:,} vs {call_analysis['sell_volume']:,})")
        
        # 풋 분석
        if put_analysis['buy_volume'] > put_analysis['sell_volume'] * 2:
            insights.append(f"📉 풋 옵션 순매수 우세 (하락 헤지 또는 베팅)")
        
        # 고래 인사이트
        if len(whale_orders) > 0:
            total_whale_premium = sum(w['premium'] for w in whale_orders)
            insights.append(f"🐋 고래 주문 {len(whale_orders)}건 (${total_whale_premium:,.0f})")
        
        return insights
    
    async def _fetch_options_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """옵션 데이터 가져오기"""
        if self.massive_api_client:
            data = await self.massive_api_client.get_options_chain(ticker)
            if data and 'contracts' in data:
                return pd.DataFrame(data['contracts'])
        
        # Fallback: yfinance
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            if not stock.options:
                return None
            
            exp = stock.options[0]
            chain = stock.option_chain(exp)
            
            calls = chain.calls.copy()
            calls['contract_type'] = 'call'
            
            puts = chain.puts.copy()
            puts['contract_type'] = 'put'
            
            return pd.concat([calls, puts], ignore_index=True)
            
        except Exception as e:
            logger.error(f"옵션 데이터 가져오기 실패: {e}")
            return None
    
    async def _fetch_current_price(self, ticker: str) -> Optional[float]:
        """현재가 가져오기"""
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        except Exception:
            pass
        return None
    
    def _create_empty_flow(self, ticker: str) -> SmartOptionFlow:
        """빈 결과 생성"""
        return SmartOptionFlow(
            ticker=ticker,
            timestamp=datetime.now(),
            net_call_premium=0,
            net_put_premium=0,
            total_premium=0,
            net_delta=0,
            delta_interpretation="NEUTRAL",
            call_buy_volume=0,
            call_sell_volume=0,
            put_buy_volume=0,
            put_sell_volume=0,
        )
