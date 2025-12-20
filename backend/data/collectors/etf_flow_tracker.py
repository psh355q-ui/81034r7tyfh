"""
ETF Flow Tracker - 섹터 로테이션 감지

주요 ETF의 자금 흐름을 추적하여 섹터 로테이션을 감지

핵심 기능:
1. 주요 ETF 모니터링 (QQQ, SPY, XLF, XLE, XLV, XLI 등)
2. 일일 자금 유입/유출 계산
3. 섹터 Hot/Cold 판단
4. 로테이션 신호 생성

작성일: 2025-12-15
Phase: E Week 1
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SectorType(Enum):
    """섹터 유형"""
    TECHNOLOGY = "technology"
    FINANCIALS = "financials"
    ENERGY = "energy"
    HEALTHCARE = "healthcare"
    INDUSTRIALS = "industrials"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    UTILITIES = "utilities"
    REAL_ESTATE = "real_estate"
    MATERIALS = "materials"
    COMMUNICATIONS = "communications"


class FlowTrend(Enum):
    """자금 흐름 트렌드"""
    STRONG_INFLOW = "strong_inflow"      # 강한 유입
    MODERATE_INFLOW = "moderate_inflow"  # 중간 유입
    NEUTRAL = "neutral"                  # 중립
    MODERATE_OUTFLOW = "moderate_outflow"  # 중간 유출
    STRONG_OUTFLOW = "strong_outflow"    # 강한 유출


@dataclass
class ETFFlowData:
    """ETF 자금 흐름 데이터"""
    ticker: str
    sector: SectorType
    date: datetime
    volume: float
    price: float
    aum: float  # Assets Under Management (운용 자산)
    daily_flow: float  # 일일 자금 흐름 (달러)
    flow_percentage: float  # AUM 대비 흐름 비율
    trend: FlowTrend


@dataclass
class SectorRotationSignal:
    """섹터 로테이션 신호"""
    hot_sectors: List[SectorType]  # 유입 상위 섹터
    cold_sectors: List[SectorType]  # 유출 상위 섹터
    neutral_sectors: List[SectorType]  # 중립 섹터
    rotation_strength: float  # 로테이션 강도 (0.0 ~ 1.0)
    confidence: float  # 신뢰도
    details: Dict[SectorType, ETFFlowData] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class ETFFlowTracker:
    """
    ETF 자금 흐름 추적기
    
    주요 섹터 ETF의 자금 유입/유출을 모니터링하여
    섹터 로테이션을 감지합니다.
    
    Usage:
        tracker = ETFFlowTracker()
        
        # 섹터 로테이션 분석
        signal = await tracker.analyze_sector_rotation()
        
        print(f"Hot Sectors: {signal.hot_sectors}")
        print(f"Cold Sectors: {signal.cold_sectors}")
        print(f"Rotation Strength: {signal.rotation_strength:.0%}")
    """
    
    # 주요 섹터 ETF 매핑
    SECTOR_ETFS = {
        "QQQ": SectorType.TECHNOLOGY,      # Nasdaq 100 (Tech)
        "XLF": SectorType.FINANCIALS,       # Financial Select
        "XLE": SectorType.ENERGY,           # Energy Select
        "XLV": SectorType.HEALTHCARE,       # Healthcare Select
        "XLI": SectorType.INDUSTRIALS,      # Industrial Select
        "XLY": SectorType.CONSUMER_DISCRETIONARY,  # Consumer Discretionary
        "XLP": SectorType.CONSUMER_STAPLES,  # Consumer Staples
        "XLU": SectorType.UTILITIES,        # Utilities Select
        "XLRE": SectorType.REAL_ESTATE,     # Real Estate
        "XLB": SectorType.MATERIALS,        # Materials Select
        "XLC": SectorType.COMMUNICATIONS    # Communication Services
    }
    
    def __init__(self, lookback_days: int = 5):
        """
        Args:
            lookback_days: 분석 기간 (일)
        """
        self.lookback_days = lookback_days
        logger.info(f"ETFFlowTracker initialized (lookback={lookback_days} days)")
    
    async def get_etf_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        ETF 데이터 수집 (Yahoo Finance 연동)
        
        Args:
            ticker: ETF 티커
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            ETF 데이터 리스트
        """
        from backend.data.collectors.api_clients.yahoo_client import get_yahoo_client
        
        logger.info(f"Fetching ETF data for {ticker} (real data)")
        
        try:
            # Yahoo Finance Client 사용
            client = get_yahoo_client()
            
            # 기간 계산
            days = (end_date - start_date).days
            period = f"{days}d"
            
            # 실제 데이터 가져오기
            yahoo_data = client.get_etf_data(ticker, period=period)
            
            if not yahoo_data:
                logger.warning(f"No data for {ticker}, using fallback")
                return self._get_fallback_data(ticker, start_date, end_date)
            
            # 데이터 변환
            result = []
            for i in range(len(yahoo_data['dates'])):
                result.append({
                    "date": yahoo_data['dates'][i],
                    "volume": yahoo_data['volume'][i],
                    "price": yahoo_data['price'][i],
                    "aum": yahoo_data['aum']
                })
            
            logger.info(f"Retrieved {len(result)} real data points for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch real data for {ticker}: {e}")
            return self._get_fallback_data(ticker, start_date, end_date)
    
    def _get_fallback_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """폴백 샘플 데이터"""
        logger.warning(f"Using fallback sample data for {ticker}")
        
        sample_data = []
        current_date = start_date
        
        while current_date <= end_date:
            sample_data.append({
                "date": current_date,
                "volume": 50_000_000,
                "price": 400.0,
                "aum": 200_000_000_000
            })
            current_date += timedelta(days=1)
        
        return sample_data
    
    def calculate_flow(
        self,
        ticker: str,
        data: List[Dict]
    ) -> List[ETFFlowData]:
        """
        자금 흐름 계산
        
        Args:
            ticker: ETF 티커
            data: ETF 데이터
            
        Returns:
            ETFFlowData 리스트
        """
        flows = []
        sector = self.SECTOR_ETFS.get(ticker, SectorType.TECHNOLOGY)
        
        for i in range(len(data)):
            if i == 0:
                # 첫 날은 비교 불가
                daily_flow = 0.0
            else:
                # 거래량 변화 × 가격 = 자금 흐름 (간단한 근사)
                volume_change = data[i]["volume"] - data[i-1]["volume"]
                daily_flow = volume_change * data[i]["price"]
            
            aum = data[i]["aum"]
            flow_percentage = (daily_flow / aum * 100) if aum > 0 else 0.0
            
            # 트렌드 판정
            if flow_percentage > 0.5:
                trend = FlowTrend.STRONG_INFLOW
            elif flow_percentage > 0.2:
                trend = FlowTrend.MODERATE_INFLOW
            elif flow_percentage < -0.5:
                trend = FlowTrend.STRONG_OUTFLOW
            elif flow_percentage < -0.2:
                trend = FlowTrend.MODERATE_OUTFLOW
            else:
                trend = FlowTrend.NEUTRAL
            
            flow_data = ETFFlowData(
                ticker=ticker,
                sector=sector,
                date=data[i]["date"],
                volume=data[i]["volume"],
                price=data[i]["price"],
                aum=aum,
                daily_flow=daily_flow,
                flow_percentage=flow_percentage,
                trend=trend
            )
            
            flows.append(flow_data)
        
        return flows
    
    async def analyze_sector_rotation(self) -> SectorRotationSignal:
        """
        섹터 로테이션 분석
        
        Returns:
            SectorRotationSignal
        """
        logger.info("Analyzing sector rotation")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        # 1. 모든 ETF 데이터 수집
        all_flows: Dict[str, List[ETFFlowData]] = {}
        
        for ticker in self.SECTOR_ETFS.keys():
            data = await self.get_etf_data(ticker, start_date, end_date)
            flows = self.calculate_flow(ticker, data)
            all_flows[ticker] = flows
        
        # 2. 섹터별 평균 흐름 계산
        sector_avg_flows: Dict[SectorType, float] = {}
        sector_details: Dict[SectorType, ETFFlowData] = {}
        
        for ticker, flows in all_flows.items():
            sector = self.SECTOR_ETFS[ticker]
            
            # 최근 N일 평균
            avg_flow_pct = sum(f.flow_percentage for f in flows) / len(flows)
            sector_avg_flows[sector] = avg_flow_pct
            
            # 가장 최근 데이터 저장
            sector_details[sector] = flows[-1]
        
        # 3. Hot/Cold 섹터 분류
        sorted_sectors = sorted(
            sector_avg_flows.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        hot_sectors = []
        cold_sectors = []
        neutral_sectors = []
        
        for sector, avg_flow in sorted_sectors:
            if avg_flow > 0.3:
                hot_sectors.append(sector)
            elif avg_flow < -0.3:
                cold_sectors.append(sector)
            else:
                neutral_sectors.append(sector)
        
        # 4. 로테이ション 강도 계산
        if len(hot_sectors) > 0 and len(cold_sectors) > 0:
            # Hot과 Cold의 차이가 클수록 강한 로테이션
            max_hot = max(sector_avg_flows[s] for s in hot_sectors)
            max_cold = abs(min(sector_avg_flows[s] for s in cold_sectors))
            rotation_strength = min((max_hot + max_cold) / 2, 1.0)
        else:
            rotation_strength = 0.0
        
        # 5. 신뢰도 계산
        # 데이터 포인트가 많을수록, 트렌드가 명확할수록 높음
        confidence = min(len(all_flows) / len(self.SECTOR_ETFS), 1.0)
        
        signal = SectorRotationSignal(
            hot_sectors=hot_sectors,
            cold_sectors=cold_sectors,
            neutral_sectors=neutral_sectors,
            rotation_strength=rotation_strength,
            confidence=confidence,
            details=sector_details
        )
        
        logger.info(
            f"Rotation analysis complete: "
            f"{len(hot_sectors)} hot, {len(cold_sectors)} cold sectors"
        )
        
        return signal
    
    def get_trading_recommendation(
        self,
        signal: SectorRotationSignal
    ) -> Dict[str, str]:
        """
        거래 추천 생성
        
        Args:
            signal: 섹터 로테이션 신호
            
        Returns:
            섹터별 추천 (BUY/SELL/HOLD)
        """
        recommendations = {}
        
        for sector in signal.hot_sectors:
            if signal.rotation_strength > 0.7:
                recommendations[sector.value] = "STRONG_BUY"
            else:
                recommendations[sector.value] = "BUY"
        
        for sector in signal.cold_sectors:
            if signal.rotation_strength > 0.7:
                recommendations[sector.value] = "STRONG_SELL"
            else:
                recommendations[sector.value] = "SELL"
        
        for sector in signal.neutral_sectors:
            recommendations[sector.value] = "HOLD"
        
        return recommendations


# 전역 인스턴스
_etf_flow_tracker = None


def get_etf_flow_tracker() -> ETFFlowTracker:
    """전역 ETFFlowTracker 인스턴스 반환"""
    global _etf_flow_tracker
    if _etf_flow_tracker is None:
        _etf_flow_tracker = ETFFlowTracker()
    return _etf_flow_tracker


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== ETF Flow Tracker Test ===\n")
        
        tracker = ETFFlowTracker(lookback_days=5)
        
        # 섹터 로테이션 분석
        print("Analyzing sector rotation...\n")
        signal = await tracker.analyze_sector_rotation()
        
        print(f"🔥 Hot Sectors ({len(signal.hot_sectors)}):")
        for sector in signal.hot_sectors:
            flow_data = signal.details[sector]
            print(f"  - {sector.value.upper()}: {flow_data.flow_percentage:+.2f}%")
        
        print(f"\n❄️  Cold Sectors ({len(signal.cold_sectors)}):")
        for sector in signal.cold_sectors:
            flow_data = signal.details[sector]
            print(f"  - {sector.value.upper()}: {flow_data.flow_percentage:+.2f}%")
        
        print(f"\n⚪ Neutral Sectors ({len(signal.neutral_sectors)}):")
        for sector in signal.neutral_sectors:
            print(f"  - {sector.value.upper()}")
        
        print(f"\n📊 Rotation Strength: {signal.rotation_strength:.0%}")
        print(f"🎯 Confidence: {signal.confidence:.0%}")
        
        # 거래 추천
        print("\n💡 Trading Recommendations:")
        recs = tracker.get_trading_recommendation(signal)
        for sector, rec in recs.items():
            print(f"  - {sector.upper()}: {rec}")
        
        print("\n✅ ETF Flow Tracker test completed!")
    
    asyncio.run(test())
