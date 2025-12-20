"""
Smart Money Collector - 스마트 머니 추적

기관 투자자 및 내부자의 움직임을 추적하여
스마트 머니 흐름을 감지

핵심 기능:
1. 13F Filings - 기관 투자자 보유 변화
2. Insider Trading - 내부자 거래 추적
3. Block Trades - 대량 거래 감지
4. Smart Money 신호 생성

작성일: 2025-12-15
Phase: E Week 3-4
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class HolderType(Enum):
    """보유자 유형"""
    HEDGE_FUND = "hedge_fund"
    MUTUAL_FUND = "mutual_fund"
    PENSION_FUND = "pension_fund"
    INSURANCE = "insurance"
    INDIVIDUAL = "individual"


class TransactionType(Enum):
    """거래 유형"""
    BUY = "buy"
    SELL = "sell"
    OPTION_EXERCISE = "option_exercise"


class SignalStrength(Enum):
    """신호 강도"""
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


@dataclass
class InstitutionalHolder:
    """기관 투자자"""
    name: str
    holder_type: HolderType
    shares: int
    value: float  # 달러
    percentage: float  # 보유 비율
    change_shares: int = 0  # 변화량
    change_percentage: float = 0.0
    quarter: str = ""  # 2024Q3


@dataclass
class InsiderTrade:
    """내부자 거래"""
    ticker: str
    insider_name: str
    position: str  # CEO, CFO, Director
    transaction_type: TransactionType
    shares: int
    price: float
    value: float
    date: datetime
    is_10b5_1: bool = False  # 사전 계획된 거래 여부


@dataclass
class BlockTrade:
    """대량 거래"""
    ticker: str
    date: datetime
    volume: int
    average_volume: int
    volume_ratio: float  # 평균 대비 배수
    price_impact: float  # 가격 영향


@dataclass
class SmartMoneySignal:
    """스마트 머니 신호"""
    ticker: str
    signal_strength: SignalStrength
    institution_buying_pressure: float  # 0.0 ~ 1.0
    insider_activity_score: float  # -1.0 ~ 1.0
    block_trade_score: float
    key_institutions: List[str]
    key_insiders: List[str]
    confidence: float
    recommendation: str
    analysis: str
    timestamp: datetime = field(default_factory=datetime.now)


class SmartMoneyCollector:
    """
    스마트 머니 추적기
    
    기관 투자자와 내부자의 움직임을 추적하여
    스마트 머니 흐름을 파악합니다.
    
    Usage:
        collector = SmartMoneyCollector()
        
        # 스마트 머니 분석
        signal = await collector.analyze_smart_money("AAPL")
        
        print(f"Signal: {signal.signal_strength.value}")
        print(f"Institution Pressure: {signal.institution_buying_pressure:.0%}")
        print(f"Recommendation: {signal.recommendation}")
    """
    
    # 주요 기관 투자자 (신뢰도 높음)
    MAJOR_INSTITUTIONS = [
        "Berkshire Hathaway",
        "Vanguard Group",
        "BlackRock",
        "State Street",
        "Fidelity",
        "T. Rowe Price",
        "Capital Group",
        "JPMorgan Chase"
    ]
    
    def __init__(self):
        logger.info("SmartMoneyCollector initialized")
    
    async def get_institutional_holders(
        self,
        ticker: str,
        limit: int = 10
    ) -> List[InstitutionalHolder]:
        """
        기관 투자자 보유 현황
        
        Args:
            ticker: 종목 코드
            limit: 조회 개수
            
        Returns:
            InstitutionalHolder 리스트
        """
        logger.info(f"Fetching institutional holders for {ticker}")
        
        # 실제로는 SEC EDGAR API, Yahoo Finance 사용
        # 여기서는 샘플 데이터
        
        holders = []
        
        # 샘플 데이터
        sample_holders = [
            {
                "name": "Vanguard Group",
                "type": HolderType.MUTUAL_FUND,
                "shares": 1_500_000_000,
                "value": 250_000_000_000,
                "percentage": 7.2,
                "change_shares": 50_000_000,
                "change_pct": 3.5
            },
            {
                "name": "BlackRock",
                "type": HolderType.MUTUAL_FUND,
                "shares": 1_200_000_000,
                "value": 200_000_000_000,
                "percentage": 6.0,
                "change_shares": 30_000_000,
                "change_pct": 2.6
            },
            {
                "name": "Berkshire Hathaway",
                "type": HolderType.HEDGE_FUND,
                "shares": 500_000_000,
                "value": 85_000_000_000,
                "percentage": 2.5,
                "change_shares": 100_000_000,  # 대량 매수!
                "change_pct": 25.0
            }
        ]
        
        for sample in sample_holders[:limit]:
            holder = InstitutionalHolder(
                name=sample["name"],
                holder_type=sample["type"],
                shares=sample["shares"],
                value=sample["value"],
                percentage=sample["percentage"],
                change_shares=sample["change_shares"],
                change_percentage=sample["change_pct"],
                quarter="2024Q4"
            )
            holders.append(holder)
        
        logger.info(f"Found {len(holders)} institutional holders")
        return holders
    
    async def get_insider_trades(
        self,
        ticker: str,
        days: int = 30
    ) -> List[InsiderTrade]:
        """
        내부자 거래 내역
        
        Args:
            ticker: 종목 코드
            days: 조회 기간 (일)
            
        Returns:
            InsiderTrade 리스트
        """
        logger.info(f"Fetching insider trades for {ticker} ({days} days)")
        
        # 실제로는 OpenInsider.com, SEC Form 4 사용
        
        trades = []
        
        # 샘플 데이터
        sample_trades = [
            {
                "insider": "Tim Cook",
                "position": "CEO",
                "type": TransactionType.BUY,
                "shares": 100_000,
                "price": 175.0,
                "days_ago": 5
            },
            {
                "insider": "Luca Maestri",
                "position": "CFO",
                "type": TransactionType.BUY,
                "shares": 50_000,
                "price": 174.5,
                "days_ago": 7
            },
            {
                "insider": "Board Member",
                "position": "Director",
                "type": TransactionType.SELL,
                "shares": 20_000,
                "price": 176.0,
                "days_ago": 10
            }
        ]
        
        for sample in sample_trades:
            trade_date = datetime.now() - timedelta(days=sample["days_ago"])
            
            trade = InsiderTrade(
                ticker=ticker,
                insider_name=sample["insider"],
                position=sample["position"],
                transaction_type=sample["type"],
                shares=sample["shares"],
                price=sample["price"],
                value=sample["shares"] * sample["price"],
                date=trade_date
            )
            trades.append(trade)
        
        logger.info(f"Found {len(trades)} insider trades")
        return trades
    
    def calculate_institution_pressure(
        self,
        holders: List[InstitutionalHolder]
    ) -> float:
        """
        기관 매수 압력 계산
        
        Args:
            holders: 기관 투자자 리스트
            
        Returns:
            매수 압력 (0.0 ~ 1.0)
        """
        if not holders:
            return 0.5
        
        total_weight = 0.0
        weighted_change = 0.0
        
        for holder in holders:
            # 주요 기관일수록 가중치 높음
            weight = 2.0 if holder.name in self.MAJOR_INSTITUTIONS else 1.0
            
            # 보유 비율도 고려
            weight *= (holder.percentage / 10.0)
            
            # 변화율 정규화 (-1.0 ~ 1.0)
            normalized_change = max(-1.0, min(1.0, holder.change_percentage / 50.0))
            
            weighted_change += normalized_change * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        # 0.0 (강한 매도) ~ 1.0 (강한 매수)
        pressure = (weighted_change / total_weight + 1.0) / 2.0
        
        return max(0.0, min(1.0, pressure))
    
    def calculate_insider_score(
        self,
        trades: List[InsiderTrade]
    ) -> float:
        """
        내부자 활동 점수
        
        Args:
            trades: 내부자 거래 리스트
            
        Returns:
            점수 (-1.0 ~ 1.0)
        """
        if not trades:
            return 0.0
        
        buy_value = 0.0
        sell_value = 0.0
        
        for trade in trades:
            # CEO, CFO의 거래는 가중치 2배
            weight = 2.0 if trade.position in ["CEO", "CFO"] else 1.0
            
            # 사전 계획된 거래는 신호가 약함
            if trade.is_10b5_1:
                weight *= 0.5
            
            if trade.transaction_type == TransactionType.BUY:
                buy_value += trade.value * weight
            elif trade.transaction_type == TransactionType.SELL:
                sell_value += trade.value * weight
        
        total = buy_value + sell_value
        if total == 0:
            return 0.0
        
        # -1.0 (강한 매도) ~ 1.0 (강한 매수)
        score = (buy_value - sell_value) / total
        
        return score
    
    async def analyze_smart_money(
        self,
        ticker: str
    ) -> SmartMoneySignal:
        """
        스마트 머니 종합 분석
        
        Args:
            ticker: 종목 코드
            
        Returns:
            SmartMoneySignal
        """
        logger.info(f"Analyzing smart money for {ticker}")
        
        # 1. 기관 투자자 분석
        holders = await self.get_institutional_holders(ticker)
        institution_pressure = self.calculate_institution_pressure(holders)
        
        # 2. 내부자 거래 분석
        insider_trades = await self.get_insider_trades(ticker)
        insider_score = self.calculate_insider_score(insider_trades)
        
        # 3. 종합 신호 강도
        # 기관 압력 60%, 내부자 40% 가중
        combined_score = (institution_pressure - 0.5) * 1.2 + insider_score * 0.8
        
        if combined_score > 0.6:
            signal_strength = SignalStrength.VERY_BULLISH
        elif combined_score > 0.2:
            signal_strength = SignalStrength.BULLISH
        elif combined_score < -0.6:
            signal_strength = SignalStrength.VERY_BEARISH
        elif combined_score < -0.2:
            signal_strength = SignalStrength.BEARISH
        else:
            signal_strength = SignalStrength.NEUTRAL
        
        # 4. 주요 기관/내부자
        key_institutions = [
            h.name for h in holders[:3]
            if h.change_percentage > 5.0
        ]
        
        key_insiders = [
            t.insider_name for t in insider_trades
            if t.transaction_type == TransactionType.BUY
            and t.position in ["CEO", "CFO"]
        ]
        
        # 5. 신뢰도
        # 데이터가 많고 명확할수록 높음
        confidence = min(
            (len(holders) / 10.0) * 0.5 + 
            (len(insider_trades) / 5.0) * 0.5,
            1.0
        )
        
        # 6. 추천
        if signal_strength == SignalStrength.VERY_BULLISH:
            recommendation = "STRONG_BUY - 주요 기관 대량 매수 포착"
        elif signal_strength == SignalStrength.BULLISH:
            recommendation = "BUY - 기관 매수 압력 증가"
        elif signal_strength == SignalStrength.VERY_BEARISH:
            recommendation = "STRONG_SELL - 기관 이탈 감지"
        elif signal_strength == SignalStrength.BEARISH:
            recommendation = "SELL - 내부자 매도 증가"
        else:
            recommendation = "HOLD - 스마트 머니 중립"
        
        # 7. 분석
        analysis = f"""
        기관 매수 압력: {institution_pressure:.0%}
        내부자 활동: {"긍정" if insider_score > 0 else "부정" if insider_score < 0 else "중립"}
        주요 움직임: {len(key_institutions)}개 기관, {len(key_insiders)}명 내부자
        """
        
        signal = SmartMoneySignal(
            ticker=ticker,
            signal_strength=signal_strength,
            institution_buying_pressure=institution_pressure,
            insider_activity_score=insider_score,
            block_trade_score=0.0,  # TODO: 추후 구현
            key_institutions=key_institutions,
            key_insiders=key_insiders,
            confidence=confidence,
            recommendation=recommendation,
            analysis=analysis
        )
        
        logger.info(
            f"Smart money analysis complete: "
            f"{signal_strength.value} (pressure={institution_pressure:.0%})"
        )
        
        return signal
    
    def validate_thesis(
        self,
        ticker: str,
        filing_date: str,
        filing_price: float,
        action: str
    ) -> Dict[str, Any]:
        """
        ChatGPT Feature 4: 13F 투자 논리 검증
        
        과거 13F filing 시점 가격과 현재 가격 비교하여
        기관 투자자의 투자 논리가 유효한지 판단
        
        Returns:
            {
                "thesis_status": "THESIS_WORKING" | "THESIS_FAILED" | "CORRECT_EXIT" | "THESIS_UNCLEAR",
                "filing_price": float,
                "current_price": float,
                "price_change_pct": float,
                "time_elapsed_days": int,
                "reasoning": str
            }
        """
        from datetime import datetime
        
        # 1. 현재 가격 조회
        try:
            from backend.data.collectors.api_clients.yahoo_client import get_yahoo_client
            yahoo = get_yahoo_client()
            current_price = yahoo.get_current_price(ticker)
        except Exception as e:
            logger.warning(f"Failed to get current price for {ticker}: {e}")
            current_price = filing_price
        
        # 2. 가격 변화 계산
        price_change = current_price - filing_price
        price_change_pct = (price_change / filing_price) if filing_price > 0 else 0
        
        # 3. 경과 시간
        try:
            filing_dt = datetime.strptime(filing_date, "%Y-%m-%d")
            time_elapsed = (datetime.now() - filing_dt).days
        except:
            time_elapsed = 0
        
        # 4. 논리 검증
        thesis_status = "THESIS_UNCLEAR"
        reasoning = ""
        
        if action in ["NEW", "INCREASE"]:
            if price_change_pct > 0.10:
                thesis_status = "THESIS_WORKING"
                reasoning = f"기관 매수 후 {price_change_pct:.1%} 상승. 투자 논리 작동 중."
            elif price_change_pct < -0.15:
                thesis_status = "THESIS_FAILED"
                reasoning = f"기관 매수 후 {price_change_pct:.1%} 하락. 투자 논리 실패."
            else:
                thesis_status = "THESIS_UNCLEAR"
                reasoning = f"기관 매수 후 {price_change_pct:.1%} 변동. 판단 보류."
        
        elif action == "SOLD_OUT":
            if price_change_pct < -0.10:
                thesis_status = "CORRECT_EXIT"
                reasoning = f"기관 매도 후 {price_change_pct:.1%} 하락. 정확한 타이밍."
            elif price_change_pct > 0.15:
                thesis_status = "THESIS_FAILED"
                reasoning = f"기관 매도 후 {price_change_pct:.1%} 상승. 조기 매도."
            else:
                thesis_status = "THESIS_UNCLEAR"
                reasoning = f"기관 매도 후 {price_change_pct:.1%} 변동. 판단 보류."
        
        logger.info(f"13F Validation: {ticker} {action} @ ${filing_price:.2f} → ${current_price:.2f} = {thesis_status}")
        
        return {
            "thesis_status": thesis_status,
            "filing_price": filing_price,
            "current_price": current_price,
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "time_elapsed_days": time_elapsed,
            "reasoning": reasoning
        }


# 전역 인스턴스
_smart_money_collector = None


def get_smart_money_collector() -> SmartMoneyCollector:
    """전역 SmartMoneyCollector 인스턴스 반환"""
    global _smart_money_collector
    if _smart_money_collector is None:
        _smart_money_collector = SmartMoneyCollector()
    return _smart_money_collector


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=== Smart Money Collector Test ===\n")
        
        collector = SmartMoneyCollector()
        
        # 1. 기관 투자자
        print("🏦 Institutional Holders:\n")
        holders = await collector.get_institutional_holders("AAPL")
        
        for holder in holders:
            change_sign = "+" if holder.change_shares > 0 else ""
            print(f"{holder.name} ({holder.holder_type.value})")
            print(f"  보유: {holder.shares:,} shares ({holder.percentage}%)")
            print(f"  변화: {change_sign}{holder.change_shares:,} ({change_sign}{holder.change_percentage}%)")
            print()
        
        # 2. 내부자 거래
        print("👔 Insider Trades (30 days):\n")
        trades = await collector.get_insider_trades("AAPL")
        
        for trade in trades:
            action = "🟢 BUY" if trade.transaction_type == TransactionType.BUY else "🔴 SELL"
            print(f"{action} - {trade.insider_name} ({trade.position})")
            print(f"  {trade.shares:,} shares @ ${trade.price:.2f}")
            print(f"  Value: ${trade.value:,.0f}")
            print(f"  Date: {trade.date.strftime('%Y-%m-%d')}")
            print()
        
        # 3. 스마트 머니 분석
        print("🎯 Smart Money Analysis:\n")
        signal = await collector.analyze_smart_money("AAPL")
        
        print(f"Signal: {signal.signal_strength.value.upper()}")
        print(f"Institution Pressure: {signal.institution_buying_pressure:.0%}")
        print(f"Insider Activity: {signal.insider_activity_score:+.2f}")
        print(f"Confidence: {signal.confidence:.0%}")
        print()
        
        if signal.key_institutions:
            print(f"Key Institutions:")
            for inst in signal.key_institutions:
                print(f"  - {inst}")
            print()
        
        if signal.key_insiders:
            print(f"Key Insiders:")
            for insider in signal.key_insiders:
                print(f"  - {insider}")
            print()
        
        print(f"💡 Recommendation: {signal.recommendation}")
        
        print("\n✅ Smart Money Collector test completed!")
    
    asyncio.run(test())
