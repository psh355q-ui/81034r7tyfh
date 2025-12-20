"""
Options Filter
옵션 이상 징후 감지 필터 (Massive API 연동)
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
import asyncio
from datetime import datetime


@dataclass
class OptionsFilterResult:
    """옵션 필터 결과"""
    ticker: str
    score: float  # 0-100
    put_call_ratio: float
    unusual_volume: bool
    implied_volatility: Optional[float]
    options_sentiment: str  # BULLISH, BEARISH, NEUTRAL
    whale_activity: bool
    passed: bool
    reason: str


class OptionsFilter:
    """
    옵션 이상 징후 필터
    
    Massive API를 사용하여 옵션 데이터 분석
    분당 5회 호출 제한 적용
    
    분석 기준:
    - Put/Call 비율
    - 이상 거래량
    - 내재 변동성 급등
    - 대형 주문 감지
    """
    
    def __init__(
        self,
        massive_api_client=None,  # MassiveAPIClient 인스턴스
        put_call_bullish_threshold: float = 0.7,  # 0.7 미만이면 강세
        put_call_bearish_threshold: float = 1.3,  # 1.3 초과면 약세
        unusual_volume_ratio: float = 2.0,  # 평균 대비 2배
    ):
        self.massive_api_client = massive_api_client
        self.put_call_bullish_threshold = put_call_bullish_threshold
        self.put_call_bearish_threshold = put_call_bearish_threshold
        self.unusual_volume_ratio = unusual_volume_ratio
    
    async def check(self, ticker: str) -> OptionsFilterResult:
        """
        옵션 필터 체크
        
        Args:
            ticker: 종목 티커
            
        Returns:
            OptionsFilterResult: 필터 결과
        """
        try:
            # 항상 yfinance를 기본으로 사용 (API 호출 절약)
            result = await self._check_with_yfinance(ticker)
            
            # 유망 종목이고 Massive API가 있으면 고래 활동만 추가 체크
            # (점수가 높은 종목만 Massive API 호출하여 API 사용량 최소화)
            if result.passed and result.score >= 40 and self.massive_api_client:
                try:
                    whale_result = await self._check_whale_activity(ticker)
                    if whale_result:
                        result.whale_activity = True
                        result.score = min(100, result.score + 20)
                        result.reason += ", 고래 활동 감지"
                except Exception:
                    pass  # Massive API 실패해도 yfinance 결과 유지
            
            return result
            
        except Exception as e:
            return OptionsFilterResult(
                ticker=ticker,
                score=0,
                put_call_ratio=1.0,
                unusual_volume=False,
                implied_volatility=None,
                options_sentiment="NEUTRAL",
                whale_activity=False,
                passed=False,
                reason=f"오류: {str(e)}"
            )
    
    async def _check_with_yfinance(self, ticker: str) -> OptionsFilterResult:
        """yfinance를 사용한 기본 옵션 분석"""
        import yfinance as yf
        
        try:
            stock = yf.Ticker(ticker)
            
            # 옵션 체인 가져오기
            if not stock.options:
                return OptionsFilterResult(
                    ticker=ticker,
                    score=0,
                    put_call_ratio=1.0,
                    unusual_volume=False,
                    implied_volatility=None,
                    options_sentiment="NEUTRAL",
                    whale_activity=False,
                    passed=False,
                    reason="옵션 데이터 없음"
                )
            
            # 가장 가까운 만기 옵션 체인
            nearest_expiry = stock.options[0]
            opt_chain = stock.option_chain(nearest_expiry)
            
            calls = opt_chain.calls
            puts = opt_chain.puts
            
            # Put/Call 비율 계산
            total_call_volume = calls['volume'].sum() if 'volume' in calls.columns else 0
            total_put_volume = puts['volume'].sum() if 'volume' in puts.columns else 0
            
            put_call_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else 1.0
            
            # 평균 IV 계산
            avg_iv = None
            if 'impliedVolatility' in calls.columns:
                avg_iv = float(calls['impliedVolatility'].mean())
            
            # 이상 거래량 감지 (간단 버전)
            total_volume = total_call_volume + total_put_volume
            unusual_volume = total_volume > 10000  # 임계값
            
            # 센티먼트 결정
            if put_call_ratio < self.put_call_bullish_threshold:
                options_sentiment = "BULLISH"
            elif put_call_ratio > self.put_call_bearish_threshold:
                options_sentiment = "BEARISH"
            else:
                options_sentiment = "NEUTRAL"
            
            # 점수 계산 (강세 신호일수록 높은 점수)
            if options_sentiment == "BULLISH":
                score = min(100, (self.put_call_bullish_threshold - put_call_ratio) / self.put_call_bullish_threshold * 100)
                passed = True
                reason = f"옵션 강세 신호 (P/C: {put_call_ratio:.2f})"
            elif options_sentiment == "BEARISH":
                score = 0
                passed = False
                reason = f"옵션 약세 신호 (P/C: {put_call_ratio:.2f})"
            else:
                score = 30
                passed = False
                reason = f"옵션 중립 (P/C: {put_call_ratio:.2f})"
            
            # 이상 거래량이면 보너스
            if unusual_volume and passed:
                score = min(100, score + 20)
                reason += ", 이상 거래량 감지"
            
            return OptionsFilterResult(
                ticker=ticker,
                score=score,
                put_call_ratio=put_call_ratio,
                unusual_volume=unusual_volume,
                implied_volatility=avg_iv,
                options_sentiment=options_sentiment,
                whale_activity=False,  # yfinance로는 감지 불가
                passed=passed,
                reason=reason
            )
            
        except Exception as e:
            return OptionsFilterResult(
                ticker=ticker,
                score=0,
                put_call_ratio=1.0,
                unusual_volume=False,
                implied_volatility=None,
                options_sentiment="NEUTRAL",
                whale_activity=False,
                passed=False,
                reason=f"yfinance 오류: {str(e)}"
            )
    
    async def _check_with_massive_api(self, ticker: str) -> OptionsFilterResult:
        """Massive API를 사용한 고급 옵션 분석"""
        try:
            # Massive API에서 옵션 데이터 가져오기
            options_data = await self.massive_api_client.get_options_chain(ticker)
            
            if not options_data:
                return await self._check_with_yfinance(ticker)
            
            # 상세 분석 수행
            put_call_ratio = options_data.get('put_call_ratio', 1.0)
            unusual_volume = options_data.get('unusual_volume', False)
            implied_volatility = options_data.get('avg_iv')
            whale_activity = options_data.get('whale_orders', False)
            
            # 센티먼트 결정
            if put_call_ratio < self.put_call_bullish_threshold:
                options_sentiment = "BULLISH"
            elif put_call_ratio > self.put_call_bearish_threshold:
                options_sentiment = "BEARISH"
            else:
                options_sentiment = "NEUTRAL"
            
            # 점수 계산
            score = 0
            reasons = []
            
            if options_sentiment == "BULLISH":
                score += 40
                reasons.append(f"강세 P/C: {put_call_ratio:.2f}")
            
            if unusual_volume:
                score += 30
                reasons.append("이상 거래량")
            
            if whale_activity:
                score += 30
                reasons.append("고래 활동")
            
            passed = score >= 40
            reason = ", ".join(reasons) if reasons else "특이사항 없음"
            
            return OptionsFilterResult(
                ticker=ticker,
                score=min(100, score),
                put_call_ratio=put_call_ratio,
                unusual_volume=unusual_volume,
                implied_volatility=implied_volatility,
                options_sentiment=options_sentiment,
                whale_activity=whale_activity,
                passed=passed,
                reason=reason
            )
            
        except Exception as e:
            # Massive API 실패 시 yfinance로 폴백
            return await self._check_with_yfinance(ticker)
    
    async def _check_whale_activity(self, ticker: str) -> bool:
        """
        Massive API로 고래 활동만 체크 (API 호출 1회)
        
        Args:
            ticker: 종목 티커
            
        Returns:
            bool: 고래 활동 감지 여부
        """
        if not self.massive_api_client:
            return False
        
        try:
            options_data = await self.massive_api_client.get_options_chain(ticker)
            
            if not options_data:
                return False
            
            # 대량 콜 옵션 구매 감지 (고래 활동 지표)
            whale_activity = options_data.get('whale_orders', False)
            
            # 추가 지표: 이상 거래량이 있고 Put/Call이 강세면 고래 활동으로 간주
            if not whale_activity:
                put_call_ratio = options_data.get('put_call_ratio', 1.0)
                unusual_volume = options_data.get('unusual_volume', False)
                whale_activity = unusual_volume and put_call_ratio < 0.5
            
            return whale_activity
            
        except Exception:
            return False

