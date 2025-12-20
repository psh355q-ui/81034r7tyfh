"""
Whale Detector
고래 주문 ($50,000+) 감지 및 추적
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WhaleDirection(Enum):
    """고래 방향성"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    MIXED = "MIXED"


@dataclass
class WhaleOrder:
    """고래 주문 정보"""
    ticker: str
    timestamp: datetime
    contract_type: str  # call, put
    strike: float
    expiration: str
    volume: int
    premium: float  # 총 프리미엄 (USD)
    trade_side: str  # BUY, SELL, NEUTRAL
    direction: str  # BULLISH, BEARISH
    underlying_price: Optional[float] = None
    implied_volatility: Optional[float] = None


@dataclass
class WhaleActivity:
    """고래 활동 요약"""
    ticker: str
    timestamp: datetime
    total_orders: int
    total_premium: float
    bullish_orders: int
    bearish_orders: int
    net_direction: WhaleDirection
    top_orders: List[WhaleOrder] = field(default_factory=list)
    whale_score: float = 0.0  # 0-100


class WhaleDetector:
    """
    Whale Detector
    
    대형 옵션 주문을 감지하고 분석
    $50,000 이상의 단일 거래를 "고래 주문"으로 분류
    """
    
    def __init__(
        self,
        threshold: float = 50_000,  # 고래 기준 $50K
        mega_threshold: float = 500_000,  # 메가 고래 $500K
        track_history: bool = True,
    ):
        self.threshold = threshold
        self.mega_threshold = mega_threshold
        self.track_history = track_history
        
        # 히스토리 저장
        self._history: Dict[str, List[WhaleOrder]] = {}
    
    def detect(
        self,
        ticker: str,
        orders: List[Dict],
    ) -> WhaleActivity:
        """
        고래 주문 감지
        
        Args:
            ticker: 종목 티커
            orders: 옵션 주문 리스트
            
        Returns:
            WhaleActivity: 고래 활동 요약
        """
        whale_orders = []
        
        for order in orders:
            premium = order.get('premium', 0)
            
            if premium >= self.threshold:
                whale_order = WhaleOrder(
                    ticker=ticker,
                    timestamp=datetime.now(),
                    contract_type=order.get('contract_type', 'unknown'),
                    strike=order.get('strike', 0),
                    expiration=order.get('expiration', ''),
                    volume=order.get('volume', 0),
                    premium=premium,
                    trade_side=order.get('trade_side', 'NEUTRAL'),
                    direction=order.get('direction', 'NEUTRAL'),
                    underlying_price=order.get('underlying_price'),
                    implied_volatility=order.get('implied_volatility'),
                )
                whale_orders.append(whale_order)
        
        # 히스토리 저장
        if self.track_history and whale_orders:
            if ticker not in self._history:
                self._history[ticker] = []
            self._history[ticker].extend(whale_orders)
            
            # 최근 7일만 유지
            cutoff = datetime.now() - timedelta(days=7)
            self._history[ticker] = [
                o for o in self._history[ticker]
                if o.timestamp >= cutoff
            ]
        
        # 방향성 분석
        bullish = sum(1 for o in whale_orders if o.direction == 'BULLISH')
        bearish = sum(1 for o in whale_orders if o.direction == 'BEARISH')
        
        if bullish > bearish * 1.5:
            net_direction = WhaleDirection.BULLISH
        elif bearish > bullish * 1.5:
            net_direction = WhaleDirection.BEARISH
        else:
            net_direction = WhaleDirection.MIXED
        
        # 고래 점수 (0-100)
        total_premium = sum(o.premium for o in whale_orders)
        whale_score = self._calculate_whale_score(whale_orders, total_premium)
        
        # 상위 5개 주문
        top_orders = sorted(whale_orders, key=lambda x: x.premium, reverse=True)[:5]
        
        return WhaleActivity(
            ticker=ticker,
            timestamp=datetime.now(),
            total_orders=len(whale_orders),
            total_premium=total_premium,
            bullish_orders=bullish,
            bearish_orders=bearish,
            net_direction=net_direction,
            top_orders=top_orders,
            whale_score=whale_score,
        )
    
    def _calculate_whale_score(
        self,
        orders: List[WhaleOrder],
        total_premium: float,
    ) -> float:
        """
        고래 점수 계산
        
        기준:
        - 주문 수: 5개 이상 → +30점
        - 총 프리미엄: $1M 이상 → +40점
        - 메가 고래: $500K 이상 단일 주문 → +30점
        """
        score = 0
        
        # 주문 수 점수
        if len(orders) >= 10:
            score += 30
        elif len(orders) >= 5:
            score += 20
        elif len(orders) >= 2:
            score += 10
        
        # 총 프리미엄 점수
        if total_premium >= 1_000_000:
            score += 40
        elif total_premium >= 500_000:
            score += 30
        elif total_premium >= 100_000:
            score += 20
        elif total_premium >= 50_000:
            score += 10
        
        # 메가 고래 점수
        mega_orders = [o for o in orders if o.premium >= self.mega_threshold]
        if mega_orders:
            score += 30
        
        return min(100, score)
    
    def get_recent_whales(
        self,
        ticker: str,
        days: int = 7,
    ) -> List[WhaleOrder]:
        """최근 고래 주문 조회"""
        if ticker not in self._history:
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        return [
            o for o in self._history[ticker]
            if o.timestamp >= cutoff
        ]
    
    def get_whale_trend(
        self,
        ticker: str,
        days: int = 7,
    ) -> Dict:
        """고래 트렌드 분석"""
        orders = self.get_recent_whales(ticker, days)
        
        if not orders:
            return {
                "ticker": ticker,
                "trend": "NO_DATA",
                "bullish_ratio": 0.5,
                "total_premium": 0,
            }
        
        bullish = sum(1 for o in orders if o.direction == 'BULLISH')
        total = len(orders)
        
        bullish_ratio = bullish / total if total > 0 else 0.5
        total_premium = sum(o.premium for o in orders)
        
        if bullish_ratio >= 0.7:
            trend = "STRONGLY_BULLISH"
        elif bullish_ratio >= 0.55:
            trend = "BULLISH"
        elif bullish_ratio <= 0.3:
            trend = "STRONGLY_BEARISH"
        elif bullish_ratio <= 0.45:
            trend = "BEARISH"
        else:
            trend = "NEUTRAL"
        
        return {
            "ticker": ticker,
            "trend": trend,
            "bullish_ratio": round(bullish_ratio, 2),
            "total_premium": total_premium,
            "order_count": total,
        }
