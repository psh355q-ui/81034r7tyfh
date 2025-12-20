"""
Macro Data Collector

거시경제 데이터를 체계적으로 수집하여 AI 분석에 반영
VIX, 금리, 선물, CDS, Dollar Index 등 통합
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import yfinance as yf
import asyncio

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """시장 국면"""
    BULL = "상승장"
    BEAR = "하락장"
    SIDEWAYS = "횡보장"
    CRASH = "폭락장"
    RECOVERY = "회복장"


class RiskAppetite(Enum):
    """위험 선호도"""
    RISK_ON = "위험자산 선호"
    RISK_OFF = "안전자산 선호"
    NEUTRAL = "중립"


@dataclass
class MacroSnapshot:
    """거시경제 스냅샷"""
    timestamp: datetime
    
    # 변동성
    vix: float = 0.0
    vix_3m: float = 0.0  # 3개월 VIX
    vix_term_structure: str = "NORMAL"  # CONTANGO / BACKWARDATION
    
    # 금리
    treasury_10y: float = 0.0
    treasury_2y: float = 0.0
    yield_curve: float = 0.0  # 10Y - 2Y (역전 여부)
    fed_funds_rate: float = 5.25
    credit_spread: float = 0.0  # High Yield Spread
    
    # 통화/상품
    dxy: float = 0.0  # Dollar Index
    gold: float = 0.0
    oil_wti: float = 0.0
    
    # 주식 지수
    sp500: float = 0.0
    nasdaq: float = 0.0
    sp500_return_1m: float = 0.0
    
    # 종합 지표
    risk_on_score: float = 50.0  # 0 (Risk-Off) ~ 100 (Risk-On)
    market_regime: MarketRegime = MarketRegime.SIDEWAYS
    risk_appetite: RiskAppetite = RiskAppetite.NEUTRAL
    
    # 메타데이터
    data_sources: List[str] = field(default_factory=list)
    missing_data: List[str] = field(default_factory=list)


# Yahoo Finance 심볼 매핑
MACRO_SYMBOLS = {
    # 변동성
    "vix": "^VIX",
    "vix_3m": "^VIX3M",
    
    # 금리
    "treasury_10y": "^TNX",
    "treasury_2y": "^IRX",  # 13-week T-Bill (2Y 대용)
    
    # 통화/상품
    "dxy": "DX-Y.NYB",
    "gold": "GC=F",
    "oil_wti": "CL=F",
    
    # 주식 지수
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "sp500_etf": "SPY",
    
    # Credit Spread (HYG - LQD 스프레드로 추정)
    "hyg": "HYG",  # High Yield
    "lqd": "LQD",  # Investment Grade
}


class MacroDataCollector:
    """
    Macro Data Collector
    
    거시경제 데이터를 실시간으로 수집하고
    시장 국면 및 Risk-On/Off 상태를 판단합니다.
    """
    
    def __init__(self, fred_api_key: str = None):
        self.fred_api_key = fred_api_key
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 300  # 5분
    
    async def get_snapshot(self, force_refresh: bool = False) -> MacroSnapshot:
        """
        현재 매크로 스냅샷 조회
        
        Args:
            force_refresh: 캐시 무시하고 새로 조회
            
        Returns:
            MacroSnapshot: 현재 매크로 데이터
        """
        # 캐시 체크
        if not force_refresh and self._is_cache_valid():
            return self._cache.get("snapshot")
        
        logger.info("매크로 데이터 수집 시작")
        
        snapshot = MacroSnapshot(timestamp=datetime.now())
        missing = []
        
        # 병렬로 데이터 수집
        tasks = {
            "vix": self._fetch_price("vix"),
            "vix_3m": self._fetch_price("vix_3m"),
            "treasury_10y": self._fetch_price("treasury_10y"),
            "treasury_2y": self._fetch_price("treasury_2y"),
            "dxy": self._fetch_price("dxy"),
            "gold": self._fetch_price("gold"),
            "oil_wti": self._fetch_price("oil_wti"),
            "sp500": self._fetch_price("sp500"),
            "nasdaq": self._fetch_price("nasdaq"),
            "hyg": self._fetch_price("hyg"),
            "lqd": self._fetch_price("lqd"),
            "sp500_return": self._fetch_return("sp500_etf", days=20),
        }
        
        results = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except Exception as e:
                logger.error(f"{key} 데이터 수집 실패: {e}")
                results[key] = None
                missing.append(key)
        
        # 스냅샷 채우기
        snapshot.vix = results.get("vix") or 0
        snapshot.vix_3m = results.get("vix_3m") or 0
        snapshot.treasury_10y = results.get("treasury_10y") or 0
        snapshot.treasury_2y = results.get("treasury_2y") or 0
        snapshot.dxy = results.get("dxy") or 0
        snapshot.gold = results.get("gold") or 0
        snapshot.oil_wti = results.get("oil_wti") or 0
        snapshot.sp500 = results.get("sp500") or 0
        snapshot.nasdaq = results.get("nasdaq") or 0
        snapshot.sp500_return_1m = results.get("sp500_return") or 0
        
        # VIX Term Structure
        if snapshot.vix > 0 and snapshot.vix_3m > 0:
            if snapshot.vix > snapshot.vix_3m:
                snapshot.vix_term_structure = "BACKWARDATION"  # 단기 VIX > 장기 = 불안
            else:
                snapshot.vix_term_structure = "CONTANGO"  # 정상
        
        # Yield Curve
        snapshot.yield_curve = snapshot.treasury_10y - snapshot.treasury_2y
        
        # Credit Spread (HYG - LQD yield 차이 추정)
        hyg = results.get("hyg") or 0
        lqd = results.get("lqd") or 0
        if hyg > 0 and lqd > 0:
            # 가격 기반 스프레드 추정 (실제로는 yield 필요)
            snapshot.credit_spread = abs(hyg - lqd) / lqd * 10 if lqd > 0 else 0
        
        # 시장 국면 및 Risk-On/Off 계산
        snapshot.market_regime = self._determine_regime(snapshot)
        snapshot.risk_appetite = self._determine_risk_appetite(snapshot)
        snapshot.risk_on_score = self._calculate_risk_on_score(snapshot)
        
        snapshot.missing_data = missing
        snapshot.data_sources = ["Yahoo Finance"]
        
        # 캐시 저장
        self._cache["snapshot"] = snapshot
        self._cache_timestamp = datetime.now()
        
        logger.info(f"매크로 스냅샷 완료: {snapshot.market_regime.value}, Risk-On: {snapshot.risk_on_score:.0f}")
        
        return snapshot
    
    async def _fetch_price(self, key: str) -> Optional[float]:
        """Yahoo Finance에서 현재가 조회"""
        symbol = MACRO_SYMBOLS.get(key)
        if not symbol:
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        except Exception as e:
            logger.error(f"{symbol} 가격 조회 실패: {e}")
        
        return None
    
    async def _fetch_return(self, key: str, days: int = 20) -> Optional[float]:
        """수익률 계산"""
        symbol = MACRO_SYMBOLS.get(key)
        if not symbol:
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            if len(hist) >= days:
                current = float(hist['Close'].iloc[-1])
                past = float(hist['Close'].iloc[-days])
                return (current - past) / past * 100
        except Exception as e:
            logger.error(f"{symbol} 수익률 계산 실패: {e}")
        
        return None
    
    def _determine_regime(self, snapshot: MacroSnapshot) -> MarketRegime:
        """
        시장 국면 판단
        
        VIX > 30 → CRASH
        VIX > 20 & Yield Curve < 0 → BEAR
        VIX < 15 & Return > 0 → BULL
        else → SIDEWAYS
        """
        if snapshot.vix > 30:
            return MarketRegime.CRASH
        
        if snapshot.vix > 25 and snapshot.sp500_return_1m < -5:
            return MarketRegime.CRASH
        
        if snapshot.vix > 20 and snapshot.yield_curve < 0:
            return MarketRegime.BEAR
        
        if snapshot.vix < 15 and snapshot.sp500_return_1m > 3:
            return MarketRegime.BULL
        
        if snapshot.sp500_return_1m > 5:
            return MarketRegime.BULL
        elif snapshot.sp500_return_1m < -5:
            return MarketRegime.BEAR
        
        return MarketRegime.SIDEWAYS
    
    def _determine_risk_appetite(self, snapshot: MacroSnapshot) -> RiskAppetite:
        """
        위험 선호도 판단
        
        VIX < 15 & Credit Spread < 1 → RISK_ON
        VIX > 25 or Credit Spread > 2 → RISK_OFF
        else → NEUTRAL
        """
        if snapshot.vix < 15 and snapshot.credit_spread < 1.0:
            return RiskAppetite.RISK_ON
        
        if snapshot.vix > 25 or snapshot.credit_spread > 2.0:
            return RiskAppetite.RISK_OFF
        
        if snapshot.vix < 18 and snapshot.sp500_return_1m > 0:
            return RiskAppetite.RISK_ON
        
        return RiskAppetite.NEUTRAL
    
    def _calculate_risk_on_score(self, snapshot: MacroSnapshot) -> float:
        """
        Risk-On 점수 계산 (0-100)
        
        높을수록 위험자산 선호 환경
        """
        score = 50  # 기본
        
        # VIX 기반 (40점)
        if snapshot.vix < 12:
            score += 20
        elif snapshot.vix < 15:
            score += 15
        elif snapshot.vix < 18:
            score += 10
        elif snapshot.vix > 25:
            score -= 15
        elif snapshot.vix > 30:
            score -= 25
        
        # 수익률 기반 (30점)
        if snapshot.sp500_return_1m > 5:
            score += 15
        elif snapshot.sp500_return_1m > 2:
            score += 10
        elif snapshot.sp500_return_1m < -5:
            score -= 15
        elif snapshot.sp500_return_1m < -2:
            score -= 10
        
        # VIX Term Structure (15점)
        if snapshot.vix_term_structure == "CONTANGO":
            score += 10
        elif snapshot.vix_term_structure == "BACKWARDATION":
            score -= 10
        
        # 달러 강세/약세 (15점)
        # DXY 100 이하 = 약달러 = Risk-On
        if snapshot.dxy < 100:
            score += 10
        elif snapshot.dxy > 105:
            score -= 10
        
        return max(0, min(100, score))
    
    def _is_cache_valid(self) -> bool:
        """캐시 유효성 체크"""
        if not self._cache_timestamp:
            return False
        
        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl
    
    def get_trading_signal_adjustment(
        self,
        snapshot: MacroSnapshot,
    ) -> Dict[str, Any]:
        """
        트레이딩 시그널 조정값 반환
        
        Trading Agent Pre-Check에 사용
        """
        adjustments = {
            "regime": snapshot.market_regime.value,
            "risk_appetite": snapshot.risk_appetite.value,
            "risk_on_score": snapshot.risk_on_score,
            "position_size_multiplier": 1.0,
            "buy_allowed": True,
            "sell_allowed": True,
            "warnings": [],
        }
        
        # CRASH 모드
        if snapshot.market_regime == MarketRegime.CRASH:
            adjustments["buy_allowed"] = False
            adjustments["position_size_multiplier"] = 0.5
            adjustments["warnings"].append("🔴 시장 폭락 국면 - 매수 중단")
        
        # Risk-Off
        elif snapshot.risk_appetite == RiskAppetite.RISK_OFF:
            adjustments["position_size_multiplier"] = 0.7
            adjustments["warnings"].append("⚠️ Risk-Off 환경 - 포지션 축소 권장")
        
        # VIX 백워데이션 (단기 불안)
        if snapshot.vix_term_structure == "BACKWARDATION":
            adjustments["warnings"].append("⚠️ VIX 백워데이션 - 단기 변동성 주의")
        
        # Yield Curve 역전
        if snapshot.yield_curve < 0:
            adjustments["warnings"].append("⚠️ 수익률 곡선 역전 - 경기 침체 신호")
        
        return adjustments
    
    def to_dict(self, snapshot: MacroSnapshot) -> Dict[str, Any]:
        """MacroSnapshot을 딕셔너리로 변환"""
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "volatility": {
                "vix": round(snapshot.vix, 2),
                "vix_3m": round(snapshot.vix_3m, 2),
                "term_structure": snapshot.vix_term_structure,
            },
            "rates": {
                "treasury_10y": round(snapshot.treasury_10y, 2),
                "treasury_2y": round(snapshot.treasury_2y, 2),
                "yield_curve": round(snapshot.yield_curve, 2),
                "credit_spread": round(snapshot.credit_spread, 2),
            },
            "currencies": {
                "dxy": round(snapshot.dxy, 2),
                "gold": round(snapshot.gold, 2),
                "oil_wti": round(snapshot.oil_wti, 2),
            },
            "indices": {
                "sp500": round(snapshot.sp500, 2),
                "nasdaq": round(snapshot.nasdaq, 2),
                "sp500_return_1m": round(snapshot.sp500_return_1m, 2),
            },
            "analysis": {
                "market_regime": snapshot.market_regime.value,
                "risk_appetite": snapshot.risk_appetite.value,
                "risk_on_score": round(snapshot.risk_on_score, 1),
            },
        }
