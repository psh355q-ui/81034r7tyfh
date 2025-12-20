"""
Options Data Fetcher

Yahoo Finance에서 옵션 체인 데이터를 수집하여
Smart Money의 움직임을 추적합니다.

Features:
- Options Chain 데이터 수집
- Put/Call Ratio 계산
- Unusual Options Activity 감지
- Large Orders (100+ contracts) 추적

Author: AI Trading System
Date: 2025-11-21
Phase: 15 Task 1
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import yfinance as yf
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class OptionContract:
    """옵션 계약 정보"""
    ticker: str
    contract_symbol: str
    strike: float
    expiration: str
    option_type: str  # 'call' or 'put'
    
    # 가격 정보
    last_price: float
    bid: float
    ask: float
    
    # 거래량 정보
    volume: int
    open_interest: int
    
    # Greeks (있으면)
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    
    # 계산된 지표
    moneyness: Optional[str] = None  # ITM, ATM, OTM
    
    def to_dict(self) -> dict:
        return {
            'ticker': self.ticker,
            'contract_symbol': self.contract_symbol,
            'strike': self.strike,
            'expiration': self.expiration,
            'option_type': self.option_type,
            'last_price': self.last_price,
            'bid': self.bid,
            'ask': self.ask,
            'volume': self.volume,
            'open_interest': self.open_interest,
            'implied_volatility': self.implied_volatility,
            'moneyness': self.moneyness
        }


@dataclass
class OptionsFlowData:
    """옵션 흐름 데이터"""
    ticker: str
    current_price: float
    timestamp: datetime
    
    # Put/Call 데이터
    total_call_volume: int
    total_put_volume: int
    total_call_oi: int
    total_put_oi: int
    
    # 비율
    put_call_ratio_volume: float
    put_call_ratio_oi: float
    
    # 주요 계약
    top_call_contracts: List[OptionContract]
    top_put_contracts: List[OptionContract]
    
    # Unusual Activity
    unusual_calls: List[OptionContract]
    unusual_puts: List[OptionContract]
    
    def to_dict(self) -> dict:
        return {
            'ticker': self.ticker,
            'current_price': self.current_price,
            'timestamp': self.timestamp.isoformat(),
            'total_call_volume': self.total_call_volume,
            'total_put_volume': self.total_put_volume,
            'total_call_oi': self.total_call_oi,
            'total_put_oi': self.total_put_oi,
            'put_call_ratio_volume': round(self.put_call_ratio_volume, 2),
            'put_call_ratio_oi': round(self.put_call_ratio_oi, 2),
            'top_call_contracts': [c.to_dict() for c in self.top_call_contracts[:5]],
            'top_put_contracts': [c.to_dict() for c in self.top_put_contracts[:5]],
            'unusual_calls_count': len(self.unusual_calls),
            'unusual_puts_count': len(self.unusual_puts),
        }


# ============================================================================
# Options Data Fetcher
# ============================================================================

class OptionsDataFetcher:
    """옵션 데이터 수집기"""
    
    def __init__(self):
        self.cache = {}  # ticker -> (data, timestamp)
        self.cache_ttl = 300  # 5분 캐시
    
    def get_options_flow(self, ticker: str, use_cache: bool = True) -> Optional[OptionsFlowData]:
        """
        옵션 흐름 데이터 가져오기
        
        Args:
            ticker: 종목 티커
            use_cache: 캐시 사용 여부
            
        Returns:
            OptionsFlowData 또는 None
        """
        ticker_upper = ticker.upper()
        
        # 캐시 확인
        if use_cache and ticker_upper in self.cache:
            cached_data, cached_time = self.cache[ticker_upper]
            age = (datetime.now() - cached_time).total_seconds()
            
            if age < self.cache_ttl:
                logger.info(f"Using cached options data for {ticker_upper} (age: {age:.0f}s)")
                return cached_data
        
        # 새로 가져오기
        logger.info(f"Fetching fresh options data for {ticker_upper}")
        
        try:
            stock = yf.Ticker(ticker_upper)
            
            # 현재 주가
            current_price = stock.history(period='1d')['Close'].iloc[-1]
            
            # 만기일 리스트
            expirations = stock.options
            
            if not expirations:
                logger.warning(f"No options available for {ticker_upper}")
                return None
            
            # 가장 가까운 만기 (보통 가장 거래량 많음)
            nearest_expiration = expirations[0]
            
            # 옵션 체인 가져오기
            opt_chain = stock.option_chain(nearest_expiration)
            calls = opt_chain.calls
            puts = opt_chain.puts
            
            if calls.empty or puts.empty:
                logger.warning(f"Empty options chain for {ticker_upper}")
                return None
            
            # Call 계약 파싱
            call_contracts = self._parse_contracts(
                ticker_upper, calls, 'call', nearest_expiration, current_price
            )
            
            # Put 계약 파싱
            put_contracts = self._parse_contracts(
                ticker_upper, puts, 'put', nearest_expiration, current_price
            )
            
            # 총 거래량 계산
            total_call_volume = calls['volume'].fillna(0).sum()
            total_put_volume = puts['volume'].fillna(0).sum()
            total_call_oi = calls['openInterest'].fillna(0).sum()
            total_put_oi = puts['openInterest'].fillna(0).sum()
            
            # Put/Call Ratio 계산
            pcr_volume = total_put_volume / total_call_volume if total_call_volume > 0 else 0
            pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            # Top 계약 (거래량 기준)
            top_calls = sorted(call_contracts, key=lambda x: x.volume, reverse=True)[:10]
            top_puts = sorted(put_contracts, key=lambda x: x.volume, reverse=True)[:10]
            
            # Unusual Activity 감지
            unusual_calls = self._detect_unusual_activity(call_contracts)
            unusual_puts = self._detect_unusual_activity(put_contracts)
            
            # 데이터 생성
            flow_data = OptionsFlowData(
                ticker=ticker_upper,
                current_price=current_price,
                timestamp=datetime.now(),
                total_call_volume=int(total_call_volume),
                total_put_volume=int(total_put_volume),
                total_call_oi=int(total_call_oi),
                total_put_oi=int(total_put_oi),
                put_call_ratio_volume=pcr_volume,
                put_call_ratio_oi=pcr_oi,
                top_call_contracts=top_calls,
                top_put_contracts=top_puts,
                unusual_calls=unusual_calls,
                unusual_puts=unusual_puts
            )
            
            # 캐시 저장
            self.cache[ticker_upper] = (flow_data, datetime.now())
            
            logger.info(
                f"Options flow for {ticker_upper}: "
                f"PCR(V)={pcr_volume:.2f}, PCR(OI)={pcr_oi:.2f}, "
                f"Unusual={len(unusual_calls)+len(unusual_puts)}"
            )
            
            return flow_data
            
        except Exception as e:
            logger.error(f"Error fetching options data for {ticker_upper}: {e}")
            return None
    
    def _parse_contracts(
        self,
        ticker: str,
        df: pd.DataFrame,
        option_type: str,
        expiration: str,
        current_price: float
    ) -> List[OptionContract]:
        """DataFrame을 OptionContract 리스트로 변환"""
        
        contracts = []
        
        for _, row in df.iterrows():
            try:
                strike = float(row['strike'])
                volume = int(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0
                open_interest = int(row.get('openInterest', 0)) if pd.notna(row.get('openInterest')) else 0
                
                # 거래량 0인 계약은 제외
                if volume == 0:
                    continue
                
                # Moneyness 계산
                moneyness = self._calculate_moneyness(strike, current_price, option_type)
                
                contract = OptionContract(
                    ticker=ticker,
                    contract_symbol=row.get('contractSymbol', ''),
                    strike=strike,
                    expiration=expiration,
                    option_type=option_type,
                    last_price=float(row.get('lastPrice', 0)),
                    bid=float(row.get('bid', 0)),
                    ask=float(row.get('ask', 0)),
                    volume=volume,
                    open_interest=open_interest,
                    implied_volatility=float(row.get('impliedVolatility', 0)) if pd.notna(row.get('impliedVolatility')) else None,
                    moneyness=moneyness
                )
                
                contracts.append(contract)
                
            except Exception as e:
                logger.debug(f"Error parsing contract: {e}")
                continue
        
        return contracts
    
    @staticmethod
    def _calculate_moneyness(strike: float, current_price: float, option_type: str) -> str:
        """
        옵션의 Moneyness 계산
        
        Returns:
            'ITM' (In The Money), 'ATM' (At The Money), 'OTM' (Out of The Money)
        """
        diff_pct = abs(strike - current_price) / current_price
        
        # ATM: 현재가 ±2% 이내
        if diff_pct < 0.02:
            return 'ATM'
        
        # Call
        if option_type == 'call':
            return 'ITM' if strike < current_price else 'OTM'
        
        # Put
        else:
            return 'ITM' if strike > current_price else 'OTM'
    
    def _detect_unusual_activity(
        self,
        contracts: List[OptionContract],
        volume_threshold: int = 100,
        vol_oi_ratio_threshold: float = 2.0
    ) -> List[OptionContract]:
        """
        Unusual Options Activity 감지
        
        기준:
        1. 거래량 > 100 contracts
        2. Volume/Open Interest > 2.0 (거래량이 평소보다 2배 이상)
        
        Args:
            contracts: 옵션 계약 리스트
            volume_threshold: 최소 거래량
            vol_oi_ratio_threshold: Volume/OI 비율 임계값
            
        Returns:
            Unusual 계약 리스트
        """
        unusual = []
        
        for contract in contracts:
            # 거래량 체크
            if contract.volume < volume_threshold:
                continue
            
            # Volume/OI 비율 체크
            if contract.open_interest > 0:
                vol_oi_ratio = contract.volume / contract.open_interest
                
                if vol_oi_ratio >= vol_oi_ratio_threshold:
                    unusual.append(contract)
            else:
                # Open Interest가 0인데 거래량이 많으면 새로운 포지션
                if contract.volume >= volume_threshold:
                    unusual.append(contract)
        
        return unusual


# ============================================================================
# Put/Call Ratio Analyzer
# ============================================================================

class PutCallRatioAnalyzer:
    """Put/Call Ratio 분석기"""
    
    # 해석 기준
    PCR_BEARISH_THRESHOLD = 1.5   # PCR > 1.5 → 매우 약세
    PCR_BULLISH_THRESHOLD = 0.7   # PCR < 0.7 → 매우 강세
    
    @staticmethod
    def interpret_pcr(pcr_volume: float, pcr_oi: float) -> Dict:
        """
        Put/Call Ratio 해석
        
        PCR > 1.0: Put이 많음 → 약세 (하락 예상)
        PCR < 1.0: Call이 많음 → 강세 (상승 예상)
        
        Args:
            pcr_volume: 거래량 기준 PCR
            pcr_oi: 미결제약정 기준 PCR
            
        Returns:
            해석 결과
        """
        # 거래량 기준 해석 (단기)
        if pcr_volume >= PutCallRatioAnalyzer.PCR_BEARISH_THRESHOLD:
            volume_sentiment = "VERY_BEARISH"
            volume_interpretation = "Heavy put buying (smart money expects decline)"
        elif pcr_volume > 1.0:
            volume_sentiment = "BEARISH"
            volume_interpretation = "More puts than calls (cautious sentiment)"
        elif pcr_volume <= PutCallRatioAnalyzer.PCR_BULLISH_THRESHOLD:
            volume_sentiment = "VERY_BULLISH"
            volume_interpretation = "Heavy call buying (smart money expects rally)"
        elif pcr_volume < 1.0:
            volume_sentiment = "BULLISH"
            volume_interpretation = "More calls than puts (optimistic sentiment)"
        else:
            volume_sentiment = "NEUTRAL"
            volume_interpretation = "Balanced options activity"
        
        # OI 기준 해석 (장기)
        if pcr_oi >= PutCallRatioAnalyzer.PCR_BEARISH_THRESHOLD:
            oi_sentiment = "VERY_BEARISH"
        elif pcr_oi > 1.0:
            oi_sentiment = "BEARISH"
        elif pcr_oi <= PutCallRatioAnalyzer.PCR_BULLISH_THRESHOLD:
            oi_sentiment = "VERY_BULLISH"
        elif pcr_oi < 1.0:
            oi_sentiment = "BULLISH"
        else:
            oi_sentiment = "NEUTRAL"
        
        # 종합 판단
        if volume_sentiment in ["VERY_BEARISH", "BEARISH"] and oi_sentiment in ["VERY_BEARISH", "BEARISH"]:
            overall = "BEARISH"
            recommendation = "Consider SHORT or reduce exposure"
        elif volume_sentiment in ["VERY_BULLISH", "BULLISH"] and oi_sentiment in ["VERY_BULLISH", "BULLISH"]:
            overall = "BULLISH"
            recommendation = "Consider LONG or increase exposure"
        else:
            overall = "MIXED"
            recommendation = "Wait for clearer signal"
        
        return {
            'pcr_volume': round(pcr_volume, 2),
            'pcr_oi': round(pcr_oi, 2),
            'volume_sentiment': volume_sentiment,
            'volume_interpretation': volume_interpretation,
            'oi_sentiment': oi_sentiment,
            'overall_sentiment': overall,
            'recommendation': recommendation
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # NVIDIA 옵션 흐름 분석
    fetcher = OptionsDataFetcher()
    analyzer = PutCallRatioAnalyzer()
    
    flow = fetcher.get_options_flow("NVDA")
    
    if flow:
        print("\n" + "="*60)
        print(f"Options Flow Analysis: {flow.ticker}")
        print("="*60)
        print(f"Current Price: ${flow.current_price:.2f}")
        print(f"\nPut/Call Ratios:")
        print(f"  Volume:        {flow.put_call_ratio_volume:.2f}")
        print(f"  Open Interest: {flow.put_call_ratio_oi:.2f}")
        
        # 해석
        interpretation = analyzer.interpret_pcr(
            flow.put_call_ratio_volume,
            flow.put_call_ratio_oi
        )
        
        print(f"\nInterpretation:")
        print(f"  Volume Sentiment: {interpretation['volume_sentiment']}")
        print(f"  {interpretation['volume_interpretation']}")
        print(f"\n  Overall: {interpretation['overall_sentiment']}")
        print(f"  Recommendation: {interpretation['recommendation']}")
        
        print(f"\nUnusual Activity:")
        print(f"  Unusual Calls: {len(flow.unusual_calls)}")
        print(f"  Unusual Puts:  {len(flow.unusual_puts)}")
        
        if flow.unusual_puts:
            print(f"\n  Top Unusual Puts:")
            for put in flow.unusual_puts[:3]:
                print(f"    ${put.strike} {put.expiration}: {put.volume} contracts (OI: {put.open_interest})")
        
        print("="*60)
