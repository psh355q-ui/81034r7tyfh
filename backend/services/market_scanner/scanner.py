"""
Dynamic Market Screener

매일 아침 Pre-Market (08:00 EST)에 실행하여
AI가 분석할 종목 후보군을 자동 선정합니다.

선정 기준:
1. 거래량 급등: 어제 거래량 > 20일 평균의 200%
2. 변동성 돌파: ATR 기반 돌파 감지
3. 모멘텀: 5일 수익률 + RSI
4. 옵션 이상: Unusual Options Activity 감지
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio
import logging

from .filters import VolumeFilter, VolatilityFilter, MomentumFilter, OptionsFilter
from .universe import get_universe, get_sector, UniverseType

logger = logging.getLogger(__name__)


@dataclass
class ScreenerCandidate:
    """스크리너 후보 종목"""
    ticker: str
    score: float  # 종합 점수 (0-100)
    volume_score: float  # 거래량 점수
    volatility_score: float  # 변동성 점수
    momentum_score: float  # 모멘텀 점수
    options_score: float  # 옵션 이상 점수
    volume_ratio: float  # 거래량 비율 (vs 20일 평균)
    price_change_pct: float  # 가격 변동률
    sector: str  # 섹터
    reasons: List[str] = field(default_factory=list)  # 선정 사유
    filter_details: Dict[str, Any] = field(default_factory=dict)  # 필터별 상세 결과


@dataclass
class ScanResult:
    """스캔 결과"""
    timestamp: datetime
    total_scanned: int
    candidates: List[ScreenerCandidate]
    scan_duration_seconds: float
    errors: List[str] = field(default_factory=list)


class DynamicScreener:
    """
    Dynamic Market Screener
    
    AI가 매일 분석할 종목 후보군을 자동 선정
    """
    
    def __init__(
        self,
        max_candidates: int = 20,
        min_market_cap: float = 1e9,  # 최소 시가총액 $1B
        min_volume: int = 500_000,  # 최소 일평균 거래량
        massive_api_client=None,  # Massive API 클라이언트
    ):
        self.max_candidates = max_candidates
        self.min_market_cap = min_market_cap
        self.min_volume = min_volume
        
        # 필터 가중치
        self.weights = {
            "volume": 0.25,
            "volatility": 0.20,
            "momentum": 0.25,
            "options": 0.30,
        }
        
        # 필터 초기화
        self.volume_filter = VolumeFilter(min_volume=min_volume)
        self.volatility_filter = VolatilityFilter()
        self.momentum_filter = MomentumFilter()
        self.options_filter = OptionsFilter(massive_api_client=massive_api_client)
        
        # 통계
        self.last_scan_result: Optional[ScanResult] = None
    
    async def scan(
        self,
        universe: List[str] = None,
        universe_type: UniverseType = UniverseType.COMBINED,
    ) -> ScanResult:
        """
        시장 전체를 스캔하여 후보 종목 선정
        
        Args:
            universe: 스캔할 종목 리스트 (None이면 기본 유니버스 사용)
            universe_type: 유니버스 타입
            
        Returns:
            ScanResult: 스캔 결과
        """
        start_time = datetime.now()
        
        # 종목 리스트 가져오기
        if universe is None:
            universe = get_universe(universe_type)
        
        logger.info(f"스캔 시작: {len(universe)}개 종목")
        
        candidates: List[ScreenerCandidate] = []
        errors: List[str] = []
        
        # 병렬로 종목 분석 (배치로 처리하여 API 과부하 방지)
        batch_size = 10
        for i in range(0, len(universe), batch_size):
            batch = universe[i:i + batch_size]
            
            tasks = [self._analyze_ticker(ticker) for ticker in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for ticker, result in zip(batch, results):
                if isinstance(result, Exception):
                    errors.append(f"{ticker}: {str(result)}")
                elif result is not None:
                    candidates.append(result)
            
            # API 레이트 리밋 방지
            await asyncio.sleep(0.5)
        
        # 점수 순으로 정렬하고 상위 N개 선택
        candidates.sort(key=lambda x: x.score, reverse=True)
        top_candidates = candidates[:self.max_candidates]
        
        scan_duration = (datetime.now() - start_time).total_seconds()
        
        result = ScanResult(
            timestamp=datetime.now(),
            total_scanned=len(universe),
            candidates=top_candidates,
            scan_duration_seconds=scan_duration,
            errors=errors[:10],  # 최대 10개 에러만 저장
        )
        
        self.last_scan_result = result
        
        logger.info(f"스캔 완료: {len(top_candidates)}개 후보 선정 ({scan_duration:.1f}초)")
        
        return result
    
    async def _analyze_ticker(self, ticker: str) -> Optional[ScreenerCandidate]:
        """
        개별 종목 분석
        
        Args:
            ticker: 종목 티커
            
        Returns:
            ScreenerCandidate or None: 필터 통과 시 후보 반환
        """
        try:
            # 모든 필터 병렬 실행
            volume_result, volatility_result, momentum_result, options_result = await asyncio.gather(
                self.volume_filter.check(ticker),
                self.volatility_filter.check(ticker),
                self.momentum_filter.check(ticker),
                self.options_filter.check(ticker),
            )
            
            # 최소 하나의 필터라도 통과해야 함
            passed_any = any([
                volume_result.passed,
                volatility_result.passed,
                momentum_result.passed,
                options_result.passed,
            ])
            
            if not passed_any:
                return None
            
            # 종합 점수 계산 (가중 평균)
            total_score = (
                volume_result.score * self.weights["volume"] +
                volatility_result.score * self.weights["volatility"] +
                momentum_result.score * self.weights["momentum"] +
                options_result.score * self.weights["options"]
            )
            
            # 최소 점수 임계값
            if total_score < 20:
                return None
            
            # 선정 사유 수집
            reasons = []
            if volume_result.passed:
                reasons.append(volume_result.reason)
            if volatility_result.passed:
                reasons.append(volatility_result.reason)
            if momentum_result.passed:
                reasons.append(momentum_result.reason)
            if options_result.passed:
                reasons.append(options_result.reason)
            
            return ScreenerCandidate(
                ticker=ticker,
                score=total_score,
                volume_score=volume_result.score,
                volatility_score=volatility_result.score,
                momentum_score=momentum_result.score,
                options_score=options_result.score,
                volume_ratio=volume_result.volume_ratio,
                price_change_pct=volatility_result.price_change_pct,
                sector=get_sector(ticker),
                reasons=reasons,
                filter_details={
                    "volume": {
                        "current": volume_result.current_volume,
                        "avg_20d": volume_result.avg_volume_20d,
                        "ratio": volume_result.volume_ratio,
                    },
                    "volatility": {
                        "atr_14": volatility_result.atr_14,
                        "breakout": volatility_result.breakout_detected,
                    },
                    "momentum": {
                        "return_5d": momentum_result.return_5d,
                        "return_20d": momentum_result.return_20d,
                        "rsi_14": momentum_result.rsi_14,
                        "signal": momentum_result.momentum_signal,
                    },
                    "options": {
                        "put_call_ratio": options_result.put_call_ratio,
                        "unusual_volume": options_result.unusual_volume,
                        "sentiment": options_result.options_sentiment,
                        "whale_activity": options_result.whale_activity,
                    },
                },
            )
            
        except Exception as e:
            logger.error(f"{ticker} 분석 실패: {e}")
            return None
    
    async def quick_scan(self, tickers: List[str]) -> List[ScreenerCandidate]:
        """
        지정된 종목만 빠르게 스캔
        
        Args:
            tickers: 스캔할 종목 리스트
            
        Returns:
            List[ScreenerCandidate]: 후보 목록
        """
        result = await self.scan(universe=tickers)
        return result.candidates
    
    def get_last_result(self) -> Optional[ScanResult]:
        """마지막 스캔 결과 반환"""
        return self.last_scan_result
    
    def to_dict(self, candidate: ScreenerCandidate) -> Dict[str, Any]:
        """ScreenerCandidate를 딕셔너리로 변환"""
        return {
            "ticker": candidate.ticker,
            "score": round(candidate.score, 1),
            "scores": {
                "volume": round(candidate.volume_score, 1),
                "volatility": round(candidate.volatility_score, 1),
                "momentum": round(candidate.momentum_score, 1),
                "options": round(candidate.options_score, 1),
            },
            "volume_ratio": round(candidate.volume_ratio, 2),
            "price_change_pct": round(candidate.price_change_pct, 2),
            "sector": candidate.sector,
            "reasons": candidate.reasons,
            "details": candidate.filter_details,
        }
