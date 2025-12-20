"""
A/B Backtest Engine (Phase 14)
==============================

두 가지 분석 방법을 비교하는 백테스트 엔진:
1. Keyword-only: 단순 키워드 기반 신호 (Baseline)
2. CoT+RAG: 심층 추론 + Knowledge Graph 기반 신호

사용법:
    engine = ABBacktestEngine()
    results = await engine.run_comparison(events)
    engine.print_comparison_report(results)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
import json

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    HAS_YFINANCE = True
except ImportError:
    # Minimal pandas for mock data
    import pandas as pd
    import numpy as np
    HAS_YFINANCE = False
    print("Warning: yfinance not installed. Using mock data.")


@dataclass
class EventSignal:
    """이벤트 신호"""
    ticker: str
    action: str  # BUY, SELL, TRIM, HOLD
    confidence: float
    reason: str
    method: str  # "keyword" or "cot_rag"


@dataclass 
class BacktestEvent:
    """백테스트 이벤트"""
    name: str
    date: str  # YYYY-MM-DD
    news_text: str
    keywords: List[str]
    candidates: List[str]  # 후보 티커들
    
    # 분석 결과 (실행 후 채워짐)
    keyword_signals: List[EventSignal] = field(default_factory=list)
    cot_rag_signals: List[EventSignal] = field(default_factory=list)


@dataclass
class BacktestResult:
    """백테스트 결과"""
    event_name: str
    ticker: str
    method: str
    action: str
    confidence: float
    
    # 가격 데이터
    entry_price: float
    exit_price: float
    return_pct: float
    
    # 벤치마크 비교
    benchmark_return: float  # SPY
    abnormal_return: float   # 초과 수익
    
    # 기간별 CAR
    car_30: float = 0.0   # 30일 누적 초과 수익
    car_60: float = 0.0   # 60일
    car_120: float = 0.0  # 120일


@dataclass
class ComparisonReport:
    """비교 리포트"""
    keyword_results: List[BacktestResult]
    cot_rag_results: List[BacktestResult]
    
    # 통계
    keyword_avg_car: float = 0.0
    cot_rag_avg_car: float = 0.0
    keyword_hit_rate: float = 0.0  # 양수 CAR 비율
    cot_rag_hit_rate: float = 0.0
    keyword_sharpe: float = 0.0
    cot_rag_sharpe: float = 0.0


class ABBacktestEngine:
    """A/B 백테스트 엔진"""
    
    # 역사적 이벤트 (테스트용)
    HISTORICAL_EVENTS = [
        BacktestEvent(
            name="Apple M1",
            date="2020-11-10",
            news_text="Apple announces M1 chip, first Apple Silicon for Mac",
            keywords=["M1", "Apple Silicon", "ARM"],
            candidates=["AAPL", "INTC", "AMD", "QCOM"]
        ),
        BacktestEvent(
            name="AWS Trainium",
            date="2020-12-01", 
            news_text="AWS launches Trainium, its new custom ML training chip",
            keywords=["Trainium", "AWS", "ML chip"],
            candidates=["AMZN", "NVDA", "INTC"]
        ),
        BacktestEvent(
            name="Google TPU v4",
            date="2021-05-18",
            news_text="Google announces TPU v4 with 2x performance improvement",
            keywords=["TPU", "v4", "Google Cloud"],
            candidates=["GOOGL", "AVGO", "NVDA"]
        ),
        BacktestEvent(
            name="NVIDIA A100",
            date="2020-05-14",
            news_text="NVIDIA announces A100 GPU based on Ampere architecture",
            keywords=["A100", "Ampere", "datacenter GPU"],
            candidates=["NVDA", "AMD", "INTC"]
        ),
        BacktestEvent(
            name="OpenAI Stargate",
            date="2024-01-16",
            news_text="OpenAI plans $500B Stargate datacenter project with Microsoft",
            keywords=["Stargate", "datacenter", "AI infrastructure"],
            candidates=["MSFT", "NVDA", "AVGO", "VST"]
        )
    ]
    
    # 키워드 → 티커 매핑 (Keyword-only 방법)
    KEYWORD_RULES = {
        "TPU": {"GOOGL": "BUY", "NVDA": "NEUTRAL"},
        "M1": {"AAPL": "BUY", "INTC": "SELL"},
        "Trainium": {"AMZN": "BUY", "NVDA": "NEUTRAL"},
        "A100": {"NVDA": "BUY", "AMD": "NEUTRAL"},
        "Stargate": {"MSFT": "BUY", "NVDA": "BUY"},
        "datacenter": {"NVDA": "BUY", "AVGO": "BUY"},
        "GPU": {"NVDA": "BUY", "AMD": "BUY"},
        "ARM": {"QCOM": "BUY", "INTC": "SELL"},
        "HBM": {"SK Hynix": "BUY", "MU": "BUY"}
    }
    
    def __init__(
        self,
        deep_reasoning_strategy=None,
        trading_days: int = 120,
        benchmark: str = "SPY"
    ):
        self.deep_reasoning = deep_reasoning_strategy
        self.trading_days = trading_days
        self.benchmark = benchmark
        
        # 캐시
        self._price_cache: Dict[str, pd.DataFrame] = {}
    
    # ============================================
    # Price Data
    # ============================================
    
    def _get_prices(
        self,
        ticker: str,
        start: datetime,
        end: datetime
    ):
        """가격 데이터 조회"""
        if not HAS_YFINANCE:
            return self._mock_prices(ticker, start, end)
        
        cache_key = f"{ticker}_{start.date()}_{end.date()}"
        if cache_key in self._price_cache:
            return self._price_cache[cache_key]
        
        try:
            df = yf.download(
                ticker,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False
            )
            if not df.empty:
                self._price_cache[cache_key] = df
                return df
        except Exception as e:
            print(f"  [Error] Failed to fetch {ticker}: {e}")
        
        return None
    
    def _mock_prices(
        self,
        ticker: str,
        start: datetime,
        end: datetime
    ):
        """Mock 가격 데이터 (테스트용)"""
        import random
        
        dates = pd.date_range(start=start, end=end, freq='B')
        
        # 티커별 다른 수익률 시뮬레이션
        base_return = {
            "GOOGL": 0.0008, "AVGO": 0.001, "NVDA": 0.0007,
            "AAPL": 0.0006, "MSFT": 0.0005, "AMZN": 0.0005,
            "INTC": -0.0003, "AMD": 0.0004, "SPY": 0.0003
        }.get(ticker, 0.0004)
        
        prices = [100]
        for _ in range(len(dates) - 1):
            daily_return = base_return + random.gauss(0, 0.02)
            prices.append(prices[-1] * (1 + daily_return))
        
        return pd.DataFrame({
            'Adj Close': prices,
            'Close': prices,
            'Volume': [1000000] * len(dates)
        }, index=dates)
    
    # ============================================
    # Keyword-only Analysis
    # ============================================
    
    def _keyword_analysis(self, event: BacktestEvent) -> List[EventSignal]:
        """키워드 기반 단순 분석"""
        signals = []
        news_lower = event.news_text.lower()
        
        for keyword, actions in self.KEYWORD_RULES.items():
            if keyword.lower() in news_lower:
                for ticker, action in actions.items():
                    if ticker in event.candidates or action != "NEUTRAL":
                        signals.append(EventSignal(
                            ticker=ticker,
                            action=action,
                            confidence=0.6,  # 고정 신뢰도
                            reason=f"Keyword match: {keyword}",
                            method="keyword"
                        ))
        
        # 중복 제거 (같은 티커)
        seen = set()
        unique_signals = []
        for s in signals:
            if s.ticker not in seen:
                seen.add(s.ticker)
                unique_signals.append(s)
        
        return unique_signals
    
    # ============================================
    # CoT+RAG Analysis
    # ============================================
    
    async def _cot_rag_analysis(self, event: BacktestEvent) -> List[EventSignal]:
        """심층 추론 기반 분석"""
        if not self.deep_reasoning:
            # Mock 결과
            return self._mock_cot_analysis(event)
        
        result = await self.deep_reasoning.analyze_news(event.news_text)
        
        signals = []
        
        # Primary beneficiary
        if result.primary_beneficiary:
            pb = result.primary_beneficiary
            signals.append(EventSignal(
                ticker=pb.get("ticker", ""),
                action=pb.get("action", "HOLD"),
                confidence=pb.get("confidence", 0.7),
                reason=pb.get("reason", "Primary beneficiary"),
                method="cot_rag"
            ))
        
        # Hidden beneficiary
        if result.hidden_beneficiary:
            hb = result.hidden_beneficiary
            signals.append(EventSignal(
                ticker=hb.get("ticker", ""),
                action=hb.get("action", "BUY"),
                confidence=hb.get("confidence", 0.7),
                reason=hb.get("reason", "Hidden beneficiary"),
                method="cot_rag"
            ))
        
        # Loser
        if result.loser:
            l = result.loser
            signals.append(EventSignal(
                ticker=l.get("ticker", ""),
                action=l.get("action", "SELL"),
                confidence=l.get("confidence", 0.5),
                reason=l.get("reason", "Loser"),
                method="cot_rag"
            ))
        
        return signals
    
    def _mock_cot_analysis(self, event: BacktestEvent) -> List[EventSignal]:
        """Mock CoT 분석 (테스트용)"""
        # 이벤트별 예상 결과
        mock_results = {
            "Apple M1": [
                EventSignal("AAPL", "BUY", 0.85, "Vertical integration advantage", "cot_rag"),
                EventSignal("INTC", "SELL", 0.75, "Lost Mac business", "cot_rag"),
                EventSignal("QCOM", "BUY", 0.65, "ARM ecosystem growth", "cot_rag")
            ],
            "Google TPU v4": [
                EventSignal("GOOGL", "BUY", 0.85, "AI infrastructure leadership", "cot_rag"),
                EventSignal("AVGO", "BUY", 0.90, "Hidden: TPU design partner", "cot_rag"),
                EventSignal("NVDA", "TRIM", 0.60, "Long-term threat", "cot_rag")
            ],
            "AWS Trainium": [
                EventSignal("AMZN", "BUY", 0.80, "Custom AI chip cost savings", "cot_rag"),
                EventSignal("NVDA", "NEUTRAL", 0.50, "Mixed impact", "cot_rag")
            ],
            "NVIDIA A100": [
                EventSignal("NVDA", "BUY", 0.90, "Datacenter GPU dominance", "cot_rag"),
                EventSignal("AMD", "BUY", 0.65, "Rising tide lifts all boats", "cot_rag")
            ],
            "OpenAI Stargate": [
                EventSignal("MSFT", "BUY", 0.80, "OpenAI partnership", "cot_rag"),
                EventSignal("AVGO", "BUY", 0.85, "Hidden: Custom chip designer", "cot_rag"),
                EventSignal("VST", "BUY", 0.75, "Hidden: Power infrastructure", "cot_rag"),
                EventSignal("NVDA", "NEUTRAL", 0.55, "Short-term boost, long-term ASIC risk", "cot_rag")
            ]
        }
        
        return mock_results.get(event.name, [])
    
    # ============================================
    # Backtest Execution
    # ============================================
    
    def _calculate_returns(
        self,
        ticker: str,
        event_date: datetime,
        action: str
    ) -> Tuple[float, float, float, float]:
        """
        수익률 계산
        
        Returns:
            (entry_price, exit_price, return_pct, benchmark_return)
        """
        start = event_date - timedelta(days=10)
        end = event_date + timedelta(days=self.trading_days + 10)
        
        # 자산 가격
        prices = self._get_prices(ticker, start, end)
        if prices is None or prices.empty:
            return 0, 0, 0, 0
        
        # 벤치마크 가격
        benchmark_prices = self._get_prices(self.benchmark, start, end)
        if benchmark_prices is None or benchmark_prices.empty:
            benchmark_prices = prices.copy()
        
        # 진입일 (이벤트 다음 날)
        entry_date = event_date + timedelta(days=1)
        
        # 가장 가까운 거래일 찾기
        try:
            entry_idx = prices.index.get_indexer([entry_date], method='bfill')[0]
            exit_idx = min(entry_idx + self.trading_days, len(prices) - 1)
            
            # Handle potential tuple/array from Adj Close column
            adj_close = prices['Adj Close']
            if hasattr(adj_close.iloc[entry_idx], '__iter__') and not isinstance(adj_close.iloc[entry_idx], str):
                entry_price = float(adj_close.iloc[entry_idx].iloc[0] if hasattr(adj_close.iloc[entry_idx], 'iloc') else adj_close.iloc[entry_idx][0])
                exit_price = float(adj_close.iloc[exit_idx].iloc[0] if hasattr(adj_close.iloc[exit_idx], 'iloc') else adj_close.iloc[exit_idx][0])
            else:
                entry_price = float(adj_close.iloc[entry_idx])
                exit_price = float(adj_close.iloc[exit_idx])
            
            # 수익률
            if action in ["BUY", "STRONG_BUY"]:
                return_pct = (exit_price - entry_price) / entry_price
            elif action in ["SELL", "TRIM"]:
                return_pct = (entry_price - exit_price) / entry_price  # 숏 포지션
            else:
                return_pct = 0
            
            # 벤치마크 수익률
            bm_adj = benchmark_prices['Adj Close']
            if hasattr(bm_adj.iloc[entry_idx], '__iter__') and not isinstance(bm_adj.iloc[entry_idx], str):
                bm_entry = float(bm_adj.iloc[entry_idx].iloc[0] if hasattr(bm_adj.iloc[entry_idx], 'iloc') else bm_adj.iloc[entry_idx][0])
                bm_exit = float(bm_adj.iloc[exit_idx].iloc[0] if hasattr(bm_adj.iloc[exit_idx], 'iloc') else bm_adj.iloc[exit_idx][0])
            else:
                bm_entry = float(bm_adj.iloc[entry_idx])
                bm_exit = float(bm_adj.iloc[exit_idx])
            benchmark_return = (bm_exit - bm_entry) / bm_entry
            
            return entry_price, exit_price, return_pct, benchmark_return
            
        except Exception as e:
            print(f"  [Error] Calculate returns for {ticker}: {e}")
            return 0, 0, 0, 0
    
    def _backtest_signal(
        self,
        signal: EventSignal,
        event: BacktestEvent
    ) -> BacktestResult:
        """단일 신호 백테스트"""
        event_date = datetime.strptime(event.date, "%Y-%m-%d")
        
        entry, exit_p, ret, bm_ret = self._calculate_returns(
            signal.ticker,
            event_date,
            signal.action
        )
        
        abnormal_return = ret - bm_ret
        
        return BacktestResult(
            event_name=event.name,
            ticker=signal.ticker,
            method=signal.method,
            action=signal.action,
            confidence=signal.confidence,
            entry_price=entry,
            exit_price=exit_p,
            return_pct=ret,
            benchmark_return=bm_ret,
            abnormal_return=abnormal_return,
            car_30=abnormal_return * 0.25,  # 간략화
            car_60=abnormal_return * 0.5,
            car_120=abnormal_return
        )
    
    # ============================================
    # Main Comparison
    # ============================================
    
    async def run_comparison(
        self,
        events: Optional[List[BacktestEvent]] = None
    ) -> ComparisonReport:
        """A/B 비교 실행"""
        events = events or self.HISTORICAL_EVENTS
        
        keyword_results = []
        cot_rag_results = []
        
        for event in events:
            print(f"\n{'='*60}")
            print(f"Event: {event.name} ({event.date})")
            print(f"{'='*60}")
            
            # Keyword-only 분석
            print("\n[Method A: Keyword-only]")
            keyword_signals = self._keyword_analysis(event)
            for sig in keyword_signals:
                print(f"  {sig.ticker}: {sig.action} ({sig.reason})")
                result = self._backtest_signal(sig, event)
                keyword_results.append(result)
            
            # CoT+RAG 분석
            print("\n[Method B: CoT+RAG]")
            cot_signals = await self._cot_rag_analysis(event)
            for sig in cot_signals:
                print(f"  {sig.ticker}: {sig.action} ({sig.reason})")
                result = self._backtest_signal(sig, event)
                cot_rag_results.append(result)
        
        # 통계 계산
        report = self._calculate_statistics(keyword_results, cot_rag_results)
        
        return report
    
    def _calculate_statistics(
        self,
        keyword_results: List[BacktestResult],
        cot_rag_results: List[BacktestResult]
    ) -> ComparisonReport:
        """통계 계산"""
        def calc_stats(results: List[BacktestResult]) -> Tuple[float, float, float]:
            if not results:
                return 0.0, 0.0, 0.0
            
            cars = [r.abnormal_return for r in results]
            avg_car = sum(cars) / len(cars) if cars else 0
            hit_rate = sum(1 for c in cars if c > 0) / len(cars) if cars else 0
            
            # Sharpe (간략화)
            if len(cars) > 1:
                import statistics
                std = statistics.stdev(cars) if len(cars) > 1 else 1
                sharpe = avg_car / std if std > 0 else 0
            else:
                sharpe = 0
            
            return avg_car, hit_rate, sharpe
        
        kw_avg, kw_hit, kw_sharpe = calc_stats(keyword_results)
        cot_avg, cot_hit, cot_sharpe = calc_stats(cot_rag_results)
        
        return ComparisonReport(
            keyword_results=keyword_results,
            cot_rag_results=cot_rag_results,
            keyword_avg_car=kw_avg,
            cot_rag_avg_car=cot_avg,
            keyword_hit_rate=kw_hit,
            cot_rag_hit_rate=cot_hit,
            keyword_sharpe=kw_sharpe,
            cot_rag_sharpe=cot_sharpe
        )
    
    # ============================================
    # Reporting
    # ============================================
    
    def print_comparison_report(self, report: ComparisonReport):
        """비교 리포트 출력"""
        print("\n")
        print("=" * 70)
        print("                    A/B BACKTEST COMPARISON REPORT")
        print("=" * 70)
        
        print("\n┌─────────────────────────────────────────────────────────────────┐")
        print("│                        SUMMARY STATISTICS                        │")
        print("├─────────────────────┬──────────────────┬────────────────────────┤")
        print("│ Metric              │ Keyword-only     │ CoT+RAG                │")
        print("├─────────────────────┼──────────────────┼────────────────────────┤")
        print(f"│ Avg Abnormal Return │ {report.keyword_avg_car:>14.2%}  │ {report.cot_rag_avg_car:>20.2%}  │")
        print(f"│ Hit Rate            │ {report.keyword_hit_rate:>14.2%}  │ {report.cot_rag_hit_rate:>20.2%}  │")
        print(f"│ Sharpe Ratio        │ {report.keyword_sharpe:>14.2f}  │ {report.cot_rag_sharpe:>20.2f}  │")
        print(f"│ Total Signals       │ {len(report.keyword_results):>14}  │ {len(report.cot_rag_results):>20}  │")
        print("└─────────────────────┴──────────────────┴────────────────────────┘")
        
        # 승자 판정
        if report.cot_rag_avg_car > report.keyword_avg_car:
            improvement = (report.cot_rag_avg_car - report.keyword_avg_car) / abs(report.keyword_avg_car) * 100 if report.keyword_avg_car != 0 else 100
            print(f"\n🏆 WINNER: CoT+RAG (+{improvement:.1f}% improvement)")
        else:
            print(f"\n🏆 WINNER: Keyword-only (Simpler is better?)")
        
        # Hidden Beneficiary 발견 성과
        print("\n┌─────────────────────────────────────────────────────────────────┐")
        print("│                    HIDDEN BENEFICIARY ANALYSIS                  │")
        print("└─────────────────────────────────────────────────────────────────┘")
        
        hidden_signals = [r for r in report.cot_rag_results if "Hidden" in r.ticker or r.abnormal_return > 0.1]
        if hidden_signals:
            for hs in hidden_signals[:5]:
                print(f"  ✓ {hs.ticker} ({hs.event_name}): {hs.abnormal_return:+.2%} abnormal return")
        else:
            print("  No hidden beneficiaries identified")
        
        # 개별 결과
        print("\n┌─────────────────────────────────────────────────────────────────┐")
        print("│                      DETAILED RESULTS                           │")
        print("└─────────────────────────────────────────────────────────────────┘")
        
        print("\n[Keyword-only Results]")
        for r in report.keyword_results[:10]:
            status = "✓" if r.abnormal_return > 0 else "✗"
            print(f"  {status} {r.event_name} / {r.ticker}: {r.return_pct:+.2%} "
                  f"(AR: {r.abnormal_return:+.2%})")
        
        print("\n[CoT+RAG Results]")
        for r in report.cot_rag_results[:10]:
            status = "✓" if r.abnormal_return > 0 else "✗"
            print(f"  {status} {r.event_name} / {r.ticker}: {r.return_pct:+.2%} "
                  f"(AR: {r.abnormal_return:+.2%})")


# ============================================
# Demo
# ============================================

async def demo():
    """데모 실행"""
    print("=== A/B Backtest Engine Demo ===\n")
    
    engine = ABBacktestEngine()
    
    # 일부 이벤트만 테스트
    test_events = engine.HISTORICAL_EVENTS[:3]
    
    report = await engine.run_comparison(test_events)
    engine.print_comparison_report(report)


if __name__ == "__main__":
    asyncio.run(demo())
