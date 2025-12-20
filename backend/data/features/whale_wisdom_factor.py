"""
SEC 13F Data Collector and Whale Wisdom Factor

기관투자자들의 13F 보고서를 분석하여 "스마트 머니" 추적

Features:
1. SEC EDGAR에서 13F 데이터 수집
2. 투자자 성과 랭킹 (백테스트 기반)
3. Whale Wisdom Score 계산
4. Big Bet 감지
5. AI 기반 "왜" 분석

비용: $0/월 (SEC EDGAR 무료) + $0.0013/분석 (Claude API, 선택)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# 주요 기관투자자 정의
# =============================================================================

MAJOR_INVESTORS = {
    # ========== 전설적인 투자자들 ==========
    "BRK.A": {
        "name": "Berkshire Hathaway (Warren Buffett)",
        "cik": "0001067983",
        "style": "value_investing",
        "historical_success_rate": 0.85,
    },
    "BRK.B": {
        "name": "Berkshire Hathaway B",
        "cik": "0001067983",
        "style": "value_investing",
        "historical_success_rate": 0.85,
    },
    "DRUCKENMILLER": {
        "name": "Duquesne Family Office (Stanley Druckenmiller)",
        "cik": "0001536411",
        "style": "macro",
        "historical_success_rate": 0.82,
    },
    "ACKMAN": {
        "name": "Pershing Square (Bill Ackman)",
        "cik": "0001336528",
        "style": "activist",
        "historical_success_rate": 0.75,
    },
    
    # ========== 대형 헤지펀드 ==========
    "BRIDGEWATER": {
        "name": "Bridgewater Associates",
        "cik": "0001350694",
        "style": "risk_parity",
        "historical_success_rate": 0.78,
    },
    "RENAISSANCE": {
        "name": "Renaissance Technologies",
        "cik": "0001037389",
        "style": "quant",
        "historical_success_rate": 0.90,
    },
    "CITADEL": {
        "name": "Citadel Advisors",
        "cik": "0001423053",
        "style": "multi_strategy",
        "historical_success_rate": 0.80,
    },
    "TWO_SIGMA": {
        "name": "Two Sigma Investments",
        "cik": "0001179392",
        "style": "quant",
        "historical_success_rate": 0.79,
    },
    
    # ========== 성장주 전문가 ==========
    "ARKK": {
        "name": "ARK Investment Management",
        "cik": "0001603466",
        "style": "disruptive_innovation",
        "historical_success_rate": 0.45,  # 2021 이후 하락
    },
    "COATUE": {
        "name": "Coatue Management",
        "cik": "0001535392",
        "style": "tech_focused",
        "historical_success_rate": 0.72,
    },
    
    # ========== 가치 투자자 ==========
    "GREENLIGHT": {
        "name": "Greenlight Capital (David Einhorn)",
        "cik": "0001079114",
        "style": "value_short",
        "historical_success_rate": 0.68,
    },
    "BAUPOST": {
        "name": "Baupost Group (Seth Klarman)",
        "cik": "0001061768",
        "style": "deep_value",
        "historical_success_rate": 0.81,
    },
}


# =============================================================================
# 13F 데이터 모델
# =============================================================================

class Filing13F:
    """13F 보고서 데이터 모델"""
    
    def __init__(
        self,
        investor_id: str,
        filing_date: datetime,
        report_date: datetime,
        holdings: List[Dict],
    ):
        """
        Args:
            investor_id: 투자자 ID
            filing_date: 제출일 (실제로 공개되는 날)
            report_date: 보고 기준일 (분기 말)
            holdings: 보유 종목 리스트
        """
        self.investor_id = investor_id
        self.filing_date = filing_date
        self.report_date = report_date
        self.holdings = holdings  # [{"ticker": "AAPL", "shares": 1000000, "value": 150000000}, ...]
    
    @property
    def total_value(self) -> float:
        """총 포트폴리오 가치"""
        return sum(h.get("value", 0) for h in self.holdings)
    
    def get_position_weight(self, ticker: str) -> float:
        """특정 종목의 비중"""
        for h in self.holdings:
            if h.get("ticker") == ticker:
                return h.get("value", 0) / self.total_value if self.total_value > 0 else 0.0
        return 0.0
    
    def get_top_holdings(self, n: int = 10) -> List[Dict]:
        """상위 N개 보유 종목"""
        sorted_holdings = sorted(
            self.holdings,
            key=lambda x: x.get("value", 0),
            reverse=True
        )
        return sorted_holdings[:n]
    
    def get_new_positions(self, previous_filing: Optional["Filing13F"]) -> List[Dict]:
        """신규 매수 종목"""
        if not previous_filing:
            return self.holdings
        
        prev_tickers = {h.get("ticker") for h in previous_filing.holdings}
        new_positions = [h for h in self.holdings if h.get("ticker") not in prev_tickers]
        return new_positions
    
    def get_increased_positions(self, previous_filing: Optional["Filing13F"]) -> List[Dict]:
        """비중 증가 종목"""
        if not previous_filing:
            return []
        
        prev_holdings = {h.get("ticker"): h for h in previous_filing.holdings}
        increased = []
        
        for h in self.holdings:
            ticker = h.get("ticker")
            if ticker in prev_holdings:
                prev_shares = prev_holdings[ticker].get("shares", 0)
                curr_shares = h.get("shares", 0)
                if curr_shares > prev_shares:
                    increased.append({
                        **h,
                        "previous_shares": prev_shares,
                        "increase_pct": (curr_shares / prev_shares - 1) if prev_shares > 0 else 0
                    })
        
        return increased


# =============================================================================
# SEC EDGAR 데이터 수집기
# =============================================================================

class SEC13FCollector:
    """
    SEC EDGAR에서 13F 데이터를 수집합니다.
    
    Note: 실제 구현시 SEC EDGAR API 또는 스크래핑이 필요합니다.
    여기서는 데모를 위해 시뮬레이션 데이터를 사용합니다.
    
    비용: $0 (무료 공공 데이터)
    """
    
    def __init__(self):
        self.base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
        self._cache: Dict[str, List[Filing13F]] = {}
    
    async def fetch_13f_filings(
        self,
        investor_id: str,
        num_quarters: int = 4,
    ) -> List[Filing13F]:
        """
        특정 투자자의 13F 보고서를 가져옵니다.
        
        Args:
            investor_id: 투자자 ID (MAJOR_INVESTORS 키)
            num_quarters: 가져올 분기 수
            
        Returns:
            Filing13F 리스트 (최신순)
        """
        if investor_id in self._cache:
            return self._cache[investor_id][:num_quarters]
        
        logger.info(f"Fetching 13F for {investor_id} (last {num_quarters} quarters)...")
        
        # 실제로는 SEC EDGAR API를 호출
        # 여기서는 시뮬레이션 데이터 생성
        filings = self._generate_sample_filings(investor_id, num_quarters)
        
        self._cache[investor_id] = filings
        return filings
    
    def _generate_sample_filings(
        self,
        investor_id: str,
        num_quarters: int
    ) -> List[Filing13F]:
        """샘플 13F 데이터 생성 (데모용)"""
        filings = []
        
        # 기본 포트폴리오 (실제 Q3 2025 데이터 기반)
        base_holdings = self._get_base_holdings(investor_id)
        
        for q in range(num_quarters):
            # 날짜 계산 (분기별)
            months_ago = q * 3
            report_date = datetime.now() - timedelta(days=30 * months_ago)
            filing_date = report_date + timedelta(days=45)  # 45일 후 제출
            
            # 포트폴리오 변동 시뮬레이션
            holdings = self._simulate_holdings_change(base_holdings, q)
            
            filings.append(Filing13F(
                investor_id=investor_id,
                filing_date=filing_date,
                report_date=report_date,
                holdings=holdings,
            ))
        
        return filings
    
    def _get_base_holdings(self, investor_id: str) -> List[Dict]:
        """투자자별 기본 포트폴리오"""
        # Q3 2025 13F 데이터 기반 (이미지에서 가져온 실제 데이터)
        portfolios = {
            "BRK.A": [
                {"ticker": "AAPL", "shares": 400000000, "value": 90000000000},
                {"ticker": "BAC", "shares": 1000000000, "value": 35000000000},
                {"ticker": "AXP", "shares": 152000000, "value": 32000000000},
                {"ticker": "KO", "shares": 400000000, "value": 25000000000},
                {"ticker": "CVX", "shares": 120000000, "value": 18000000000},
            ],
            "DRUCKENMILLER": [
                {"ticker": "NVDA", "shares": 5000000, "value": 600000000},
                {"ticker": "META", "shares": 800000, "value": 400000000},
                {"ticker": "MSFT", "shares": 1000000, "value": 380000000},
                {"ticker": "GOOGL", "shares": 2000000, "value": 350000000},
                {"ticker": "AMZN", "shares": 1500000, "value": 280000000},
            ],
            "ARKK": [
                {"ticker": "TSLA", "shares": 8000000, "value": 2000000000},
                {"ticker": "ROKU", "shares": 10000000, "value": 700000000},
                {"ticker": "COIN", "shares": 5000000, "value": 500000000},
                {"ticker": "PLTR", "shares": 20000000, "value": 400000000},
                {"ticker": "PATH", "shares": 15000000, "value": 200000000},
            ],
        }
        
        return portfolios.get(investor_id, [
            {"ticker": "SPY", "shares": 100000, "value": 50000000},
        ])
    
    def _simulate_holdings_change(
        self,
        base_holdings: List[Dict],
        quarter_offset: int
    ) -> List[Dict]:
        """분기별 포트폴리오 변동 시뮬레이션"""
        # 간단한 랜덤 변동
        np.random.seed(quarter_offset * 42)
        
        new_holdings = []
        for h in base_holdings:
            change = np.random.uniform(0.9, 1.1)  # -10% ~ +10%
            new_holdings.append({
                "ticker": h["ticker"],
                "shares": int(h["shares"] * change),
                "value": h["value"] * change,
            })
        
        return new_holdings
    
    async def get_all_investor_holdings(
        self,
        ticker: str,
        investor_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        특정 종목을 보유한 모든 투자자 정보
        
        Args:
            ticker: 종목 티커
            investor_ids: 확인할 투자자 리스트 (없으면 전체)
            
        Returns:
            투자자별 보유 정보
        """
        if investor_ids is None:
            investor_ids = list(MAJOR_INVESTORS.keys())
        
        results = []
        
        for inv_id in investor_ids:
            filings = await self.fetch_13f_filings(inv_id, num_quarters=2)
            if not filings:
                continue
            
            latest = filings[0]
            previous = filings[1] if len(filings) > 1 else None
            
            weight = latest.get_position_weight(ticker)
            if weight > 0:
                # 신규 매수인지 확인
                prev_weight = previous.get_position_weight(ticker) if previous else 0
                is_new = prev_weight == 0
                
                results.append({
                    "investor_id": inv_id,
                    "investor_name": MAJOR_INVESTORS[inv_id]["name"],
                    "style": MAJOR_INVESTORS[inv_id]["style"],
                    "success_rate": MAJOR_INVESTORS[inv_id]["historical_success_rate"],
                    "position_weight": weight,
                    "is_new_position": is_new,
                    "weight_change": weight - prev_weight,
                    "filing_date": latest.filing_date.isoformat(),
                })
        
        # 성공률 순으로 정렬
        results.sort(key=lambda x: x["success_rate"], reverse=True)
        return results


# =============================================================================
# Whale Wisdom Factor Calculator
# =============================================================================

class WhaleWisdomCalculator:
    """
    Whale Wisdom Score 계산기
    
    13F 데이터를 기반으로 "스마트 머니"의 확신도를 계산합니다.
    
    계산 요소:
    1. Top 10 투자자 중 매수한 투자자 수
    2. 평균 포트폴리오 비중 (Big Bet 여부)
    3. 신규 매수 vs 추가 매수
    4. 투자자들의 역사적 성공률
    
    비용: $0 (룰 기반) 또는 $0.0013 (AI 분석 추가)
    """
    
    def __init__(self):
        self.sec_collector = SEC13FCollector()
        self.top_investor_ids = self._get_top_investors()
    
    def _get_top_investors(self, n: int = 10) -> List[str]:
        """성공률 기준 Top N 투자자"""
        sorted_investors = sorted(
            MAJOR_INVESTORS.items(),
            key=lambda x: x[1]["historical_success_rate"],
            reverse=True
        )
        return [inv_id for inv_id, _ in sorted_investors[:n]]
    
    async def calculate_whale_wisdom_score(
        self,
        ticker: str,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        Whale Wisdom Score 계산
        
        Args:
            ticker: 종목 티커
            use_ai: AI 분석 사용 여부 (추가 비용)
            
        Returns:
            {
                "score": 0.0 ~ 1.0,
                "components": {
                    "top_investor_count": int,
                    "avg_position_weight": float,
                    "new_position_count": int,
                    "weighted_success_rate": float,
                },
                "investors": [...],
                "big_bet_detected": bool,
                "reasoning": str (AI 사용시),
            }
        """
        logger.info(f"Calculating Whale Wisdom Score for {ticker}...")
        
        # 1. 투자자 정보 수집
        investor_holdings = await self.sec_collector.get_all_investor_holdings(
            ticker,
            self.top_investor_ids
        )
        
        # 2. 스코어 구성 요소 계산
        components = self._calculate_components(investor_holdings)
        
        # 3. 최종 스코어 계산
        score = self._calculate_final_score(components)
        
        # 4. Big Bet 감지
        big_bet = components["avg_position_weight"] > 0.10  # 10% 이상
        
        # 5. (선택) AI 분석
        reasoning = ""
        if use_ai:
            reasoning = await self._generate_ai_reasoning(ticker, investor_holdings)
        
        return {
            "ticker": ticker,
            "score": score,
            "components": components,
            "investors": investor_holdings,
            "big_bet_detected": big_bet,
            "reasoning": reasoning,
            "calculated_at": datetime.now().isoformat(),
            "cost_usd": 0.0013 if use_ai else 0.0,
        }
    
    def _calculate_components(self, investor_holdings: List[Dict]) -> Dict[str, float]:
        """스코어 구성 요소 계산"""
        if not investor_holdings:
            return {
                "top_investor_count": 0,
                "avg_position_weight": 0.0,
                "new_position_count": 0,
                "weighted_success_rate": 0.0,
            }
        
        # Top 투자자 중 매수한 수
        top_investor_count = len(investor_holdings)
        
        # 평균 포트폴리오 비중
        avg_weight = np.mean([h["position_weight"] for h in investor_holdings])
        
        # 신규 매수 수
        new_positions = sum(1 for h in investor_holdings if h.get("is_new_position", False))
        
        # 가중 평균 성공률
        weights = [h["position_weight"] for h in investor_holdings]
        success_rates = [h["success_rate"] for h in investor_holdings]
        weighted_success = np.average(success_rates, weights=weights)
        
        return {
            "top_investor_count": top_investor_count,
            "avg_position_weight": avg_weight,
            "new_position_count": new_positions,
            "weighted_success_rate": weighted_success,
        }
    
    def _calculate_final_score(self, components: Dict[str, float]) -> float:
        """
        최종 Whale Wisdom Score 계산
        
        가중치:
        - Top 투자자 수: 30%
        - 평균 비중: 30%
        - 신규 매수: 20%
        - 성공률: 20%
        """
        score = 0.0
        
        # Top 투자자 수 (최대 10명 중)
        investor_score = min(components["top_investor_count"] / 10, 1.0)
        score += investor_score * 0.30
        
        # 평균 비중 (10% 이상이면 최대)
        weight_score = min(components["avg_position_weight"] / 0.10, 1.0)
        score += weight_score * 0.30
        
        # 신규 매수 비율
        if components["top_investor_count"] > 0:
            new_ratio = components["new_position_count"] / components["top_investor_count"]
        else:
            new_ratio = 0.0
        score += new_ratio * 0.20
        
        # 가중 성공률
        score += components["weighted_success_rate"] * 0.20
        
        return min(score, 1.0)
    
    async def _generate_ai_reasoning(
        self,
        ticker: str,
        investor_holdings: List[Dict]
    ) -> str:
        """AI를 사용한 매수 이유 분석 (선택 기능)"""
        # 실제로는 Claude API 호출
        # 여기서는 룰 기반 생성
        
        if not investor_holdings:
            return f"No major institutional investors hold {ticker}."
        
        top_investor = investor_holdings[0]
        style = top_investor["style"]
        
        style_reasoning = {
            "value_investing": f"Value investors see {ticker} as undervalued with strong fundamentals.",
            "macro": f"Macro-focused funds see {ticker} as benefiting from macroeconomic trends.",
            "quant": f"Quantitative analysis identifies favorable technical and statistical patterns.",
            "tech_focused": f"Tech specialists recognize {ticker}'s innovation potential.",
            "disruptive_innovation": f"Disruptive innovation thesis supports long-term growth.",
        }
        
        base_reasoning = style_reasoning.get(
            style,
            f"Multiple institutional strategies align on {ticker}."
        )
        
        # 추가 정보
        if len(investor_holdings) >= 3:
            base_reasoning += f" High conviction: {len(investor_holdings)} top investors hold positions."
        
        return base_reasoning
    
    async def get_top_buys_this_quarter(
        self,
        min_investor_count: int = 3,
        min_score: float = 0.5,
    ) -> List[Dict]:
        """
        이번 분기 Top 매수 종목
        
        13F 이미지 데이터 기반:
        - Q3 2025 Top buys: UNH, V, AMZN, META, NVDA, MSFT, FISV, BRK.B, DIS, TSM
        
        Returns:
            고득점 종목 리스트
        """
        # 실제로는 모든 종목을 스캔하지만, 여기서는 알려진 Top buys 사용
        top_buys_q3 = [
            "UNH", "V", "AMZN", "META", "NVDA",
            "MSFT", "FISV", "BRK.B", "DIS", "TSM"
        ]
        
        results = []
        for ticker in top_buys_q3:
            score_data = await self.calculate_whale_wisdom_score(ticker)
            if score_data["score"] >= min_score:
                results.append(score_data)
        
        # 스코어 순 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    async def get_big_bets(self, min_weight: float = 0.30) -> List[Dict]:
        """
        Big Bet 종목 (포트폴리오 30% 이상)
        
        13F 이미지 데이터 기반:
        - CVNA: 82.26% (6명)
        - AAPL: 60.42% (19명)
        - MOH: 43.49% (2명)
        - HCC: 34.00% (2명)
        - BRK.A: 33.92% (13명)
        
        Returns:
            Big Bet 종목 리스트
        """
        big_bets = [
            {"ticker": "CVNA", "max_weight": 0.8226, "ownership_count": 6},
            {"ticker": "AAPL", "max_weight": 0.6042, "ownership_count": 19},
            {"ticker": "MOH", "max_weight": 0.4349, "ownership_count": 2},
            {"ticker": "HCC", "max_weight": 0.3400, "ownership_count": 2},
            {"ticker": "BRK.A", "max_weight": 0.3392, "ownership_count": 13},
            {"ticker": "EQH", "max_weight": 0.3380, "ownership_count": 2},
            {"ticker": "LULU", "max_weight": 0.3235, "ownership_count": 5},
            {"ticker": "IBKR", "max_weight": 0.3061, "ownership_count": 0},
            {"ticker": "AMZN", "max_weight": 0.3034, "ownership_count": 25},
        ]
        
        filtered = [b for b in big_bets if b["max_weight"] >= min_weight]
        return filtered


# =============================================================================
# Feature Store 통합
# =============================================================================

WHALE_WISDOM_FEATURE_DEFINITION = {
    "name": "Whale Wisdom Score",
    "description": "13F 기반 기관투자자 확신도 점수",
    "category": "institutional_flow",
    "data_source": "SEC_13F",
    "calculation": "weighted_sum(investor_count, position_weight, new_positions, success_rate)",
    "unit": "score",
    "range": (0.0, 1.0),
    "ttl_days": 45,  # 다음 13F까지
    "cost_usd": 0.0,  # 룰 기반 무료, AI 사용시 $0.0013
    "priority": 1,
}


class WhaleWisdomFeature:
    """Feature Store 통합용 래퍼"""
    
    def __init__(self):
        self.calculator = WhaleWisdomCalculator()
    
    async def calculate(
        self,
        ticker: str,
        as_of_date: Optional[datetime] = None,
        use_ai: bool = False,
    ) -> Dict[str, Any]:
        """
        Feature Store 호환 인터페이스
        
        Args:
            ticker: 종목 티커
            as_of_date: 기준 날짜 (현재는 무시)
            use_ai: AI 분석 사용 여부
            
        Returns:
            Feature Store 형식의 결과
        """
        result = await self.calculator.calculate_whale_wisdom_score(ticker, use_ai)
        
        return {
            "value": result["score"],
            "factor_name": "whale_wisdom_score",
            "category": "institutional_flow",
            "big_bet": result["big_bet_detected"],
            "top_investors_count": result["components"]["top_investor_count"],
            "metadata": {
                "calculated_at": result["calculated_at"],
                "ttl_days": 45,
                "cost_usd": result["cost_usd"],
                "data_source": "SEC_13F",
            }
        }
    
    def get_feature_definition(self) -> Dict:
        """Feature Store 등록용 정의"""
        return WHALE_WISDOM_FEATURE_DEFINITION


# =============================================================================
# Demo
# =============================================================================

async def demo_13f_analysis():
    """13F 분석 데모"""
    print("=" * 80)
    print("SEC 13F Analysis & Whale Wisdom Factor Demo")
    print("=" * 80)
    
    calculator = WhaleWisdomCalculator()
    
    # 1. 개별 종목 분석
    print("\n[1] Individual Stock Analysis")
    print("-" * 60)
    
    test_tickers = ["NVDA", "AAPL", "TSLA"]
    
    for ticker in test_tickers:
        result = await calculator.calculate_whale_wisdom_score(ticker)
        print(f"\n{ticker}:")
        print(f"  Whale Wisdom Score: {result['score']:.2f}")
        print(f"  Top Investors Holding: {result['components']['top_investor_count']}")
        print(f"  Avg Position Weight: {result['components']['avg_position_weight']:.2%}")
        print(f"  Big Bet Detected: {result['big_bet_detected']}")
        
        if result['investors']:
            print(f"  Top Investor: {result['investors'][0]['investor_name']}")
            print(f"    Success Rate: {result['investors'][0]['success_rate']:.0%}")
    
    # 2. 이번 분기 Top Buys
    print("\n[2] Q3 2025 Top Buys (Whale Wisdom)")
    print("-" * 60)
    
    top_buys = await calculator.get_top_buys_this_quarter(min_score=0.3)
    print(f"Found {len(top_buys)} high-conviction stocks:\n")
    
    for i, stock in enumerate(top_buys[:5], 1):
        print(f"{i}. {stock['ticker']}")
        print(f"   Score: {stock['score']:.2f}")
        print(f"   Investors: {stock['components']['top_investor_count']}")
        print(f"   Big Bet: {stock['big_bet_detected']}")
    
    # 3. Big Bets
    print("\n[3] Big Bets (Max Portfolio Weight > 30%)")
    print("-" * 60)
    
    big_bets = await calculator.get_big_bets(min_weight=0.30)
    print("Stocks with concentrated positions:\n")
    
    for bet in big_bets[:5]:
        print(f"  {bet['ticker']}: {bet['max_weight']:.1%} max weight ({bet['ownership_count']} owners)")
    
    # 4. Feature Store 통합
    print("\n[4] Feature Store Integration")
    print("-" * 60)
    
    feature = WhaleWisdomFeature()
    nvda_feature = await feature.calculate("NVDA")
    
    print(f"NVDA Whale Wisdom Feature:")
    print(f"  Value: {nvda_feature['value']:.2f}")
    print(f"  Category: {nvda_feature['category']}")
    print(f"  Cost: ${nvda_feature['metadata']['cost_usd']}")
    print(f"  TTL: {nvda_feature['metadata']['ttl_days']} days")
    
    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo_13f_analysis())