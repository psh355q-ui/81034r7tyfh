"""
Enhanced FRED Data Collector (Credit + FX + Debt Regime Factors)

Gemini 및 ChatGPT 제안에 따라, AI 없이 ($0 비용)
미국 연방준비제도(FRED)에서 매크로 지표를 수집합니다.

수집 데이터:
1. 신용 스프레드 (Credit Spread) - ChatGPT 제안
2. 환율 (Dollar Index) - 사용자 제안  
3. 국가 부채 (US Debt) - YouTube 시나리오 기반

이 데이터는 'ChatGPTStrategy'의 시장 국면 판단에 사용됩니다.

비용: $0/월 (무료 FRED API)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

# 로거 설정
logger = logging.getLogger(__name__)


# =============================================================================
# FRED 데이터 티커 정의
# =============================================================================

FRED_TICKERS = {
    # ========== 1. 신용 스프레드 (ChatGPT 제안) ==========
    # 미국 하이일드(HY) 스프레드 - 위험 자산 공포 민감도 (가장 중요)
    "HY_SPREAD": "BAMLH0A0HYM2",
    
    # 미국 투자등급(IG) 스프레드 - 글로벌 자금시장 긴장도
    "IG_SPREAD": "BAMLC0A0CM",
    
    # TED 스프레드 - 금융 시스템 스트레스
    "TED_SPREAD": "TEDRATE",
    
    # ========== 2. 환율 (사용자 제안) ==========
    # 달러 인덱스 (광역 무역 가중치) - Risk-Off 지표
    "DXY": "DTWEXBGS",
    
    # ========== 3. 국가 부채 (YouTube 시나리오) ==========
    # 미국 총 공공 부채 (분기별)
    "US_DEBT": "GFDEBTN",
    
    # ========== 4. 추가 경제 지표 ==========
    # 연방 기금 금리 (기준 금리)
    "FED_FUNDS_RATE": "FEDFUNDS",
    
    # 10년 국채 수익률
    "TREASURY_10Y": "DGS10",
    
    # 2년 국채 수익률 (수익률 곡선 역전 감지용)
    "TREASURY_2Y": "DGS2",
    
    # 실업률
    "UNEMPLOYMENT": "UNRATE",
}


class EnhancedFREDCollector:
    """
    강화된 FRED 데이터 수집기
    
    Features:
    - 신용 스프레드, 환율, 국가 부채 수집
    - 자동 팩터 계산 (스트레스 지표, YoY 변화율 등)
    - 데이터 품질 검증
    - 캐싱 지원
    """
    
    def __init__(self, cache_days: int = 1):
        """
        Args:
            cache_days: 캐시 유효 기간 (일)
        """
        self.cache_days = cache_days
        self._cache: Dict[str, Tuple[datetime, pd.DataFrame]] = {}
        self._last_fetch: Optional[datetime] = None
        
    async def fetch_all_data(
        self, 
        days_lookback: int = 365 * 2,
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        모든 FRED 데이터를 한 번에 가져옵니다.
        
        Args:
            days_lookback: 과거 데이터 조회 기간 (기본 2년)
            force_refresh: 캐시 무시하고 새로 가져오기
            
        Returns:
            모든 FRED 지표가 포함된 DataFrame
        """
        # 캐시 확인
        if not force_refresh and self._is_cache_valid():
            logger.info("Using cached FRED data")
            return self._cache.get("all_data", (None, None))[1]
        
        logger.info(f"Fetching FRED data (last {days_lookback} days)...")
        
        start_date = datetime.now() - timedelta(days=days_lookback)
        end_date = datetime.now()
        
        try:
            # pandas-datareader를 동적으로 import (설치 여부 확인)
            try:
                import pandas_datareader.data as web
            except ImportError:
                logger.error("pandas-datareader not installed. Run: pip install pandas-datareader")
                return None
            
            # FRED 데이터 호출
            df = web.DataReader(
                list(FRED_TICKERS.values()),
                'fred',
                start_date,
                end_date
            )
            
            # 컬럼명 리네임
            df = df.rename(columns={v: k for k, v in FRED_TICKERS.items()})
            
            # FRED 데이터는 주말/휴일에 NaN
            df = df.ffill()  # Forward fill
            df = df.fillna(0.0)
            
            # 캐시 저장
            self._cache["all_data"] = (datetime.now(), df)
            self._last_fetch = datetime.now()
            
            logger.info(f"FRED fetch successful. Latest data: {df.index[-1].date()}")
            self._log_latest_values(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch FRED data: {e}", exc_info=True)
            return None
    
    def _is_cache_valid(self) -> bool:
        """캐시 유효성 확인"""
        if "all_data" not in self._cache:
            return False
        
        cache_time, _ = self._cache["all_data"]
        age = datetime.now() - cache_time
        return age < timedelta(days=self.cache_days)
    
    def _log_latest_values(self, df: pd.DataFrame):
        """최신 값 로깅"""
        latest = df.iloc[-1]
        logger.info("Latest FRED values:")
        logger.info(f"  - HY_SPREAD: {latest.get('HY_SPREAD', 'N/A'):.2f}")
        logger.info(f"  - IG_SPREAD: {latest.get('IG_SPREAD', 'N/A'):.2f}")
        logger.info(f"  - DXY: {latest.get('DXY', 'N/A'):.2f}")
        logger.info(f"  - TREASURY_10Y: {latest.get('TREASURY_10Y', 'N/A'):.2f}%")
    
    async def calculate_macro_factors(
        self,
        df: Optional[pd.DataFrame] = None
    ) -> Dict[str, float]:
        """
        매크로 팩터를 계산합니다.
        
        ChatGPT 제안 기반:
        1. credit_stress_factor: HY 스프레드 기준 스트레스 지표
        2. dollar_strength_factor: 달러 강세 지표
        3. debt_pressure_factor: 국가 부채 압박 지표
        4. yield_curve_inversion: 수익률 곡선 역전 여부
        
        Returns:
            {
                "credit_stress_factor": float,
                "dollar_strength_factor": float,
                "debt_pressure_factor": float,
                "yield_curve_inversion": bool,
                "is_2sigma_breach": bool,
                ...
            }
        """
        if df is None:
            df = await self.fetch_all_data()
            if df is None:
                return self._get_default_factors()
        
        factors = {}
        
        try:
            # ========== 1. 신용 스트레스 팩터 (ChatGPT 제안) ==========
            if "HY_SPREAD" in df.columns:
                latest_hy = df["HY_SPREAD"].iloc[-1]
                avg_1y_hy = df["HY_SPREAD"].tail(252).mean()  # 1년 = 252 거래일
                std_1y_hy = df["HY_SPREAD"].tail(252).std()
                
                # 1년 평균 대비 비율
                factors["credit_stress_factor"] = (latest_hy / avg_1y_hy) - 1.0
                
                # 2-Sigma 임계값 (ChatGPT 제안)
                threshold_2sigma = avg_1y_hy + (2 * std_1y_hy)
                factors["is_2sigma_breach"] = latest_hy > threshold_2sigma
                
                factors["hy_spread_current"] = latest_hy
                factors["hy_spread_avg_1y"] = avg_1y_hy
                factors["hy_spread_2sigma_threshold"] = threshold_2sigma
            
            # ========== 2. 달러 강세 팩터 (사용자 제안) ==========
            if "DXY" in df.columns:
                latest_dxy = df["DXY"].iloc[-1]
                avg_1y_dxy = df["DXY"].tail(252).mean()
                
                # 1년 평균 대비 강세율
                factors["dollar_strength_factor"] = (latest_dxy / avg_1y_dxy) - 1.0
                factors["dxy_current"] = latest_dxy
                factors["dxy_avg_1y"] = avg_1y_dxy
            
            # ========== 3. 국가 부채 압박 팩터 (YouTube 시나리오) ==========
            if "US_DEBT" in df.columns:
                # 국가 부채는 분기별 데이터이므로 YoY 계산
                latest_debt = df["US_DEBT"].iloc[-1]
                
                # 1년 전 데이터 찾기 (약 4 데이터 포인트 전)
                debt_1y_ago_idx = max(0, len(df) - 365)
                debt_1y_ago = df["US_DEBT"].iloc[debt_1y_ago_idx]
                
                if debt_1y_ago > 0:
                    factors["debt_pressure_factor"] = (latest_debt / debt_1y_ago) - 1.0
                else:
                    factors["debt_pressure_factor"] = 0.0
                
                factors["us_debt_current"] = latest_debt
                factors["us_debt_yoy_change"] = factors["debt_pressure_factor"]
            
            # ========== 4. 수익률 곡선 역전 ==========
            if "TREASURY_10Y" in df.columns and "TREASURY_2Y" in df.columns:
                latest_10y = df["TREASURY_10Y"].iloc[-1]
                latest_2y = df["TREASURY_2Y"].iloc[-1]
                
                # 10Y - 2Y 스프레드 (음수 = 역전)
                spread = latest_10y - latest_2y
                factors["yield_curve_spread"] = spread
                factors["yield_curve_inversion"] = spread < 0
            
            # ========== 5. 종합 위험 점수 ==========
            factors["macro_risk_score"] = self._calculate_composite_risk(factors)
            
        except Exception as e:
            logger.error(f"Error calculating macro factors: {e}", exc_info=True)
            return self._get_default_factors()
        
        return factors
    
    def _calculate_composite_risk(self, factors: Dict[str, float]) -> float:
        """
        종합 매크로 리스크 점수 계산 (0.0 ~ 1.0)
        
        가중치:
        - 신용 스트레스: 40%
        - 달러 강세: 30%
        - 부채 압박: 20%
        - 수익률 역전: 10%
        """
        score = 0.0
        
        # 신용 스트레스 (40%)
        credit_stress = factors.get("credit_stress_factor", 0.0)
        # 0.3 이상이면 위험, 0.5 이상이면 매우 위험
        score += min(credit_stress / 0.5, 1.0) * 0.4
        
        # 달러 강세 (30%)
        dollar_strength = factors.get("dollar_strength_factor", 0.0)
        # 0.05 이상이면 강세, 0.10 이상이면 매우 강세
        score += min(dollar_strength / 0.10, 1.0) * 0.3
        
        # 부채 압박 (20%)
        debt_pressure = factors.get("debt_pressure_factor", 0.0)
        # 0.10 (10% YoY 증가) 이상이면 위험
        score += min(debt_pressure / 0.15, 1.0) * 0.2
        
        # 수익률 곡선 역전 (10%)
        if factors.get("yield_curve_inversion", False):
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_default_factors(self) -> Dict[str, float]:
        """기본 팩터 값 (데이터 없을 때)"""
        return {
            "credit_stress_factor": 0.0,
            "dollar_strength_factor": 0.0,
            "debt_pressure_factor": 0.0,
            "yield_curve_inversion": False,
            "is_2sigma_breach": False,
            "macro_risk_score": 0.0,
        }
    
    async def get_regime_signals(self) -> Dict[str, str]:
        """
        시장 국면 신호를 반환합니다.
        
        Returns:
            {
                "credit_signal": "NORMAL" | "WARNING" | "CRITICAL",
                "fx_signal": "WEAK" | "NEUTRAL" | "STRONG",
                "debt_signal": "STABLE" | "GROWING" | "ACCELERATING",
                "overall_signal": "BULL" | "SIDEWAYS" | "RISK_OFF" | "CRASH"
            }
        """
        factors = await self.calculate_macro_factors()
        
        signals = {}
        
        # 신용 신호
        credit_stress = factors.get("credit_stress_factor", 0.0)
        if factors.get("is_2sigma_breach", False):
            signals["credit_signal"] = "CRITICAL"
        elif credit_stress > 0.3:
            signals["credit_signal"] = "WARNING"
        else:
            signals["credit_signal"] = "NORMAL"
        
        # 환율 신호
        dollar_strength = factors.get("dollar_strength_factor", 0.0)
        if dollar_strength > 0.05:
            signals["fx_signal"] = "STRONG"
        elif dollar_strength < -0.05:
            signals["fx_signal"] = "WEAK"
        else:
            signals["fx_signal"] = "NEUTRAL"
        
        # 부채 신호
        debt_pressure = factors.get("debt_pressure_factor", 0.0)
        if debt_pressure > 0.10:
            signals["debt_signal"] = "ACCELERATING"
        elif debt_pressure > 0.05:
            signals["debt_signal"] = "GROWING"
        else:
            signals["debt_signal"] = "STABLE"
        
        # 종합 신호 (ChatGPT 제안 로직)
        macro_risk = factors.get("macro_risk_score", 0.0)
        if macro_risk > 0.7:
            signals["overall_signal"] = "CRASH"
        elif macro_risk > 0.5:
            signals["overall_signal"] = "RISK_OFF"
        elif macro_risk > 0.3:
            signals["overall_signal"] = "SIDEWAYS"
        else:
            signals["overall_signal"] = "BULL"
        
        signals["macro_risk_score"] = macro_risk
        
        return signals
    
    def get_metrics(self) -> Dict:
        """수집기 메트릭 반환"""
        return {
            "last_fetch": self._last_fetch.isoformat() if self._last_fetch else None,
            "cache_valid": self._is_cache_valid(),
            "tickers_count": len(FRED_TICKERS),
            "cost_usd": 0.0,  # 무료 API
        }


# =============================================================================
# 유동성 고갈 이벤트 감지기 (Gemini 제안)
# =============================================================================

class LiquidityCrunchDetector:
    """
    M7 유동성 고갈 시나리오 감지기
    
    YouTube 영상 분석:
    - M7 기업의 대규모 채권 발행 감지
    - AI 군비경쟁으로 인한 현금 소진
    - 기관의 선제적 현금 확보 패턴
    """
    
    def __init__(self):
        self.m7_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]
        self.recent_events: list = []
    
    async def check_liquidity_warning(
        self,
        news_headlines: list[str],
        earnings_data: Optional[Dict] = None
    ) -> Dict:
        """
        유동성 고갈 경고 신호 확인
        
        트리거 조건 (Gemini 제안):
        - M7 기업의 실적이 '기대 이상'으로 발표됨
        - 해당 기업이 24시간 이내에 '대규모 채권 발행'을 발표함
        
        Args:
            news_headlines: 최근 뉴스 헤드라인
            earnings_data: 실적 데이터 (옵션)
            
        Returns:
            {
                "LIQUIDITY_CRUNCH_WARNING": bool,
                "triggered_by": list,
                "confidence": float,
                "details": str
            }
        """
        warning_signals = []
        
        # 키워드 기반 감지
        bond_keywords = [
            "bond offering", "debt issuance", "bond sale",
            "채권 발행", "회사채", "자금 조달",
            "billion dollar bond", "corporate bond",
            "financing round", "capital raise"
        ]
        
        ai_investment_keywords = [
            "data center", "AI infrastructure", "capex",
            "capital expenditure", "AI investment",
            "데이터 센터", "AI 투자", "설비 투자"
        ]
        
        for headline in news_headlines:
            headline_lower = headline.lower()
            
            # M7 기업 + 채권 발행
            for ticker in self.m7_tickers:
                if ticker.lower() in headline_lower or \
                   self._get_company_name(ticker).lower() in headline_lower:
                    
                    # 채권 발행 키워드
                    if any(kw in headline_lower for kw in bond_keywords):
                        warning_signals.append({
                            "ticker": ticker,
                            "event": "BOND_ISSUANCE",
                            "headline": headline
                        })
                    
                    # AI 투자 키워드
                    if any(kw in headline_lower for kw in ai_investment_keywords):
                        warning_signals.append({
                            "ticker": ticker,
                            "event": "AI_CAPEX",
                            "headline": headline
                        })
        
        # 경고 판단
        is_warning = len(warning_signals) >= 2  # 2개 이상 신호
        confidence = min(len(warning_signals) / 5, 1.0)
        
        return {
            "LIQUIDITY_CRUNCH_WARNING": is_warning,
            "triggered_by": warning_signals,
            "confidence": confidence,
            "details": f"Detected {len(warning_signals)} liquidity warning signals"
        }
    
    def _get_company_name(self, ticker: str) -> str:
        """티커를 회사명으로 변환"""
        mapping = {
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Google",
            "AMZN": "Amazon",
            "META": "Meta",
            "NVDA": "NVIDIA",
            "TSLA": "Tesla"
        }
        return mapping.get(ticker, ticker)


# =============================================================================
# 데모 및 테스트
# =============================================================================

async def demo_enhanced_fred():
    """강화된 FRED 수집기 데모"""
    print("=" * 80)
    print("Enhanced FRED Collector Demo")
    print("=" * 80)
    
    collector = EnhancedFREDCollector()
    
    # 1. 데이터 수집
    print("\n[1] Fetching FRED data...")
    df = await collector.fetch_all_data(days_lookback=365)
    
    if df is not None:
        print(f"✅ Data fetched successfully")
        print(f"   - Date range: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"   - Columns: {list(df.columns)}")
        
        # 2. 매크로 팩터 계산
        print("\n[2] Calculating macro factors...")
        factors = await collector.calculate_macro_factors(df)
        
        print("\n📊 Macro Factors:")
        print(f"   Credit Stress Factor: {factors.get('credit_stress_factor', 0):+.2%}")
        print(f"   Dollar Strength Factor: {factors.get('dollar_strength_factor', 0):+.2%}")
        print(f"   Debt Pressure Factor: {factors.get('debt_pressure_factor', 0):+.2%}")
        print(f"   Yield Curve Inversion: {factors.get('yield_curve_inversion', False)}")
        print(f"   2-Sigma Breach: {factors.get('is_2sigma_breach', False)}")
        print(f"   Composite Risk Score: {factors.get('macro_risk_score', 0):.2f}")
        
        # 3. 시장 국면 신호
        print("\n[3] Getting regime signals...")
        signals = await collector.get_regime_signals()
        
        print("\n🚦 Market Signals:")
        print(f"   Credit Signal: {signals.get('credit_signal', 'N/A')}")
        print(f"   FX Signal: {signals.get('fx_signal', 'N/A')}")
        print(f"   Debt Signal: {signals.get('debt_signal', 'N/A')}")
        print(f"   Overall Signal: {signals.get('overall_signal', 'N/A')}")
        
        # 4. 메트릭
        print("\n[4] Collector metrics:")
        metrics = collector.get_metrics()
        print(f"   Last fetch: {metrics['last_fetch']}")
        print(f"   Cost: ${metrics['cost_usd']}/month")
    else:
        print("❌ Failed to fetch data. Please install pandas-datareader:")
        print("   pip install pandas-datareader")
    
    # 5. 유동성 고갈 감지기 테스트
    print("\n[5] Testing Liquidity Crunch Detector...")
    detector = LiquidityCrunchDetector()
    
    # 테스트 뉴스 (가상)
    test_headlines = [
        "Meta announces $30 billion bond offering to fund AI infrastructure",
        "Google plans massive data center expansion with $25B investment",
        "Microsoft raises $10 billion through corporate bonds",
        "Apple reports record Q4 earnings, beats estimates",
    ]
    
    result = await detector.check_liquidity_warning(test_headlines)
    print(f"\n🚨 Liquidity Crunch Warning: {result['LIQUIDITY_CRUNCH_WARNING']}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"   Signals detected: {len(result['triggered_by'])}")
    
    if result['triggered_by']:
        print("   Triggered by:")
        for signal in result['triggered_by'][:3]:
            print(f"     - {signal['ticker']}: {signal['event']}")
    
    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo_enhanced_fred())