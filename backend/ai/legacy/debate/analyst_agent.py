"""
Analyst Agent for War Room Debate System

Role: Fundamental analysis specialist
Focuses on: Earnings, valuation (P/E), growth rate, financial health

Author: ai-trading-system
Date: 2025-12-21
Updated: 2025-12-27 - Added PEG Ratio analysis
"""

import logging
from typing import Dict, Any, Optional
import random

logger = logging.getLogger(__name__)


class AnalystAgent:
    """
    Analyst Agent - 펀더멘털 분석 전문가
    
    Core Capabilities:
    - Earnings analysis
    - Valuation metrics (P/E, P/B, P/S)
    - Growth rate assessment
    - Financial health check
    """
    
    def __init__(self):
        self.agent_name = "analyst"
        self.vote_weight = 0.15  # 15% voting weight
    
    async def analyze(self, ticker: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze ticker using fundamental metrics.
        
        Args:
            ticker: Stock ticker symbol
            context: Optional context (financial data, earnings, etc.)
        
        Returns:
            {
                "agent": "analyst",
                "action": "BUY|SELL|HOLD",
                "confidence": 0.0-1.0,
                "reasoning": str,
                "fundamental_factors": {...}
            }
        """
        try:
            logger.info(f"[Analyst Agent] Analyzing {ticker}")
            
            if context and "fundamental_data" in context:
                return await self._analyze_with_real_data(ticker, context["fundamental_data"])
            else:
                return await self._analyze_mock(ticker)
        
        except Exception as e:
            logger.error(f"[Analyst Agent] Error analyzing {ticker}: {e}")
            return self._fallback_response(ticker)
    
    async def _analyze_with_real_data(self, ticker: str, fundamental_data: Dict) -> Dict:
        """
        Analyze using real fundamental metrics.
        
        Expected fundamental_data format:
        {
            "pe_ratio": 25.5,
            "earnings_growth": 0.18,  # 18% YoY (decimal, e.g., 0.18 = 18%)
            "revenue_growth": 0.12,
            "profit_margin": 0.22,
            "debt_to_equity": 0.45
        }
        """
        pe_ratio = fundamental_data.get("pe_ratio", 20)
        earnings_growth = fundamental_data.get("earnings_growth", 0.10)
        revenue_growth = fundamental_data.get("revenue_growth", 0.08)
        profit_margin = fundamental_data.get("profit_margin", 0.15)
        debt_to_equity = fundamental_data.get("debt_to_equity", 0.50)

        action = "HOLD"
        confidence = 0.5
        confidence_boost = 0.0

        # PEG Ratio Analysis (if earnings growth available)
        peg_analysis = None
        if earnings_growth > 0.01:  # At least 1% growth to calculate PEG
            peg_analysis = self._calculate_peg_ratio(pe_ratio, earnings_growth)

        # PEG Ratio-based signals (HIGHEST PRIORITY for growth stocks)
        if peg_analysis:
            peg_ratio = peg_analysis["peg_ratio"]
            peg_valuation = peg_analysis["valuation"]

            if peg_ratio < 0.5:
                # Extremely undervalued growth stock
                action = "BUY"
                confidence = 0.90
                reasoning = f"초저평가 성장주 (PEG {peg_ratio:.2f}, P/E {pe_ratio:.1f}, 성장률 {earnings_growth*100:.1f}%)"

            elif peg_ratio < 1.0:
                # Undervalued growth stock
                confidence_boost += 0.20

            elif peg_ratio > 2.0:
                # Overvalued growth stock
                if action != "SELL":
                    confidence_boost -= 0.15
        
        # Only proceed with traditional fundamental analysis if PEG didn't trigger strong BUY
        if not (peg_analysis and peg_analysis["peg_ratio"] < 0.5):
            # BUY Signals - Strong fundamentals
            if earnings_growth > 0.15 and pe_ratio < 25 and profit_margin > 0.20:
                action = "BUY"
                confidence = 0.88
                reasoning = f"강한 펀더멘털 (실적 성장 {earnings_growth*100:.1f}%, P/E {pe_ratio:.1f}, 이익률 {profit_margin*100:.1f}%)"

            elif earnings_growth > 0.10 and debt_to_equity < 0.40:
                action = "BUY"
                confidence = 0.80
                reasoning = f"안정적 성장 (실적 +{earnings_growth*100:.1f}%, 낮은 부채비율 {debt_to_equity:.2f})"

            # SELL Signals - Weak fundamentals
            elif earnings_growth < -0.05 or profit_margin < 0.05:
                action = "SELL"
                confidence = 0.78
                reasoning = f"펀더멘털 악화 (실적 성장 {earnings_growth*100:+.1f}%, 이익률 {profit_margin*100:.1f}%)"

            elif pe_ratio > 40 and earnings_growth < 0.10:
                action = "SELL"
                confidence = 0.72
                reasoning = f"고평가 우려 (P/E {pe_ratio:.1f}, 성장률 {earnings_growth*100:.1f}% 불균형)"

            # HOLD - Mixed signals
            else:
                reasoning = f"중립 (P/E {pe_ratio:.1f}, 실적 성장 {earnings_growth*100:+.1f}%, 추가 분석 필요)"
                confidence = 0.65

            # Apply PEG Ratio confidence boost
            if peg_analysis and peg_analysis["peg_ratio"] < 1.0 and action == "BUY":
                confidence = min(0.95, confidence + confidence_boost)
                reasoning += f" | PEG {peg_analysis['peg_ratio']:.2f} (성장 대비 저평가)"
            elif peg_analysis and peg_analysis["peg_ratio"] > 2.0:
                confidence = max(0.50, confidence + confidence_boost)
                reasoning += f" | PEG {peg_analysis['peg_ratio']:.2f} (성장 대비 고평가)"
        
        fundamental_factors = {
            "pe_ratio": pe_ratio,
            "earnings_growth": f"{earnings_growth*100:+.1f}%",
            "revenue_growth": f"{revenue_growth*100:+.1f}%",
            "profit_margin": f"{profit_margin*100:.1f}%",
            "debt_to_equity": debt_to_equity,
            "valuation": "UNDERVALUED" if pe_ratio < 20 else "OVERVALUED" if pe_ratio > 30 else "FAIR"
        }

        # Add PEG Ratio to fundamental_factors
        if peg_analysis:
            fundamental_factors["peg_ratio"] = round(peg_analysis["peg_ratio"], 2)

        # Peer Comparison Analysis
        peer_comparison = self._compare_with_peers(ticker, fundamental_data)
        fundamental_factors["peer_comparison"] = {
            "sector": peer_comparison["sector"],
            "competitive_position": peer_comparison["competitive_position"],
            "competitive_score": peer_comparison["competitive_score"]
        }

        # Peer Comparison에 따른 신뢰도 조정
        if peer_comparison["competitive_position"] == "LEADER":
            # 섹터 리더 → BUY 신호 강화
            if action == "BUY":
                confidence_boost += 0.15
                reasoning += f" | {peer_comparison['sector']} 섹터 리더"
            elif action == "HOLD":
                action = "BUY"
                confidence = 0.75
                reasoning = f"{peer_comparison['reasoning']}\n→ 섹터 경쟁 우위 확보 - 매수 추천"
        elif peer_comparison["competitive_position"] == "LAGGING":
            # 섹터 열위 → SELL 신호 강화 또는 BUY 신호 약화
            if action == "SELL":
                confidence_boost += 0.10
                reasoning += f" | {peer_comparison['sector']} 섹터 내 경쟁 열위"
            elif action == "BUY":
                confidence_boost -= 0.15
                reasoning += f" | {peer_comparison['sector']} 섹터 내 경쟁 열위 (주의)"
            fundamental_factors["peg_valuation"] = peg_analysis["valuation"]
        
        return {
            "agent": "analyst",
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "fundamental_factors": fundamental_factors
        }
    
    async def _analyze_mock(self, ticker: str) -> Dict:
        """Mock fundamental analysis"""
        scenarios = [
            {
                "action": "BUY",
                "confidence": 0.88,
                "reasoning": "실적 폭발적 성장 (+22% YoY), P/E 18로 저평가, 이익률 25%",
                "fundamental_factors": {
                    "pe_ratio": 18.5,
                    "earnings_growth": "+22%",
                    "valuation": "UNDERVALUED"
                }
            },
            {
                "action": "SELL",
                "confidence": 0.80,
                "reasoning": "실적 부진 (-8% YoY), P/E 45로 고평가, 부채비율 0.85",
                "fundamental_factors": {
                    "pe_ratio": 45.0,
                    "earnings_growth": "-8%",
                    "debt_to_equity": 0.85,
                    "valuation": "OVERVALUED"
                }
            },
            {
                "action": "HOLD",
                "confidence": 0.70,
                "reasoning": "혼조 (실적 +5%, P/E 28, 이익률 안정적)",
                "fundamental_factors": {
                    "pe_ratio": 28.0,
                    "earnings_growth": "+5%",
                    "valuation": "FAIR"
                }
            }
        ]
        
        return {
            "agent": "analyst",
            **random.choice(scenarios)
        }
    
    def _fallback_response(self, ticker: str) -> Dict:
        """Fallback on error"""
        return {
            "agent": "analyst",
            "action": "HOLD",
            "confidence": 0.55,
            "reasoning": f"펀더멘털 데이터 부족 - {ticker} 추가 조사 필요",
            "fundamental_factors": {
                "error": True
            }
        }

    def _calculate_peg_ratio(self, pe_ratio: float, earnings_growth_rate: float) -> Dict:
        """
        PEG Ratio (Price/Earnings to Growth) 계산

        공식: PEG = P/E Ratio / (Earnings Growth Rate × 100)

        해석:
        - PEG < 0.5: 초저평가 (강한 매수 기회)
        - PEG < 1.0: 저평가 (매수 신호)
        - PEG 1.0 ~ 1.5: 적정 가격
        - PEG 1.5 ~ 2.0: 약간 고평가
        - PEG > 2.0: 고평가 (성장 대비 비쌈)

        예시:
        - NVDA: P/E 60, 성장률 40% → PEG = 60/40 = 1.5 (적정)
        - AAPL: P/E 30, 성장률 10% → PEG = 30/10 = 3.0 (고평가)
        - META: P/E 25, 성장률 30% → PEG = 25/30 = 0.83 (저평가)

        Args:
            pe_ratio: P/E Ratio (예: 25.5)
            earnings_growth_rate: 연간 실적 성장률 (decimal, 예: 0.18 = 18%)

        Returns:
            {
                "peg_ratio": float,
                "valuation": "EXTREMELY_UNDERVALUED|UNDERVALUED|FAIR|OVERVALUED|EXTREMELY_OVERVALUED",
                "interpretation": str
            }
        """
        # Convert growth rate to percentage (0.18 → 18)
        earnings_growth_pct = earnings_growth_rate * 100

        # Calculate PEG Ratio
        if earnings_growth_pct < 1.0:
            # Growth too low to calculate meaningful PEG
            peg_ratio = 999.0  # Set to very high value
            valuation = "N/A"
            interpretation = "실적 성장률이 너무 낮아 PEG 계산 불가"
        else:
            peg_ratio = pe_ratio / earnings_growth_pct

            # Valuation classification
            if peg_ratio < 0.5:
                valuation = "EXTREMELY_UNDERVALUED"
                interpretation = "초저평가 (성장 대비 매우 저렴)"
            elif peg_ratio < 1.0:
                valuation = "UNDERVALUED"
                interpretation = "저평가 (성장 대비 저렴)"
            elif peg_ratio < 1.5:
                valuation = "FAIR"
                interpretation = "적정 가격 (성장과 균형)"
            elif peg_ratio < 2.0:
                valuation = "SLIGHTLY_OVERVALUED"
                interpretation = "약간 고평가"
            else:
                valuation = "OVERVALUED"
                interpretation = "고평가 (성장 대비 비쌈)"

        return {
            "peg_ratio": peg_ratio,
            "valuation": valuation,
            "interpretation": interpretation
        }

    def _compare_with_peers(self, ticker: str, fundamental_data: Dict, peer_data: Optional[Dict] = None) -> Dict:
        """
        동종업계 경쟁사 비교 분석

        비교 항목:
        - P/E Ratio vs 섹터 평균
        - Revenue Growth vs 경쟁사
        - Profit Margin vs 경쟁사
        - Market Share (if available)

        Args:
            ticker: 분석 대상 티커
            fundamental_data: 분석 대상 펀더멘털 데이터
            peer_data: 경쟁사 데이터 (선택)

        Returns:
            {
                "sector": str,
                "peer_comparison": {
                    "pe_vs_sector": str,  # BELOW/ABOVE/INLINE
                    "growth_vs_peers": str,
                    "margin_vs_peers": str
                },
                "competitive_position": str,  # LEADER/COMPETITIVE/LAGGING
                "reasoning": str
            }
        """
        # Sector mapping (간단한 예시)
        SECTOR_MAP = {
            "AAPL": {"sector": "Technology", "peers": ["MSFT", "GOOGL"]},
            "MSFT": {"sector": "Technology", "peers": ["AAPL", "GOOGL"]},
            "GOOGL": {"sector": "Technology", "peers": ["AAPL", "MSFT", "META"]},
            "TSLA": {"sector": "Automotive", "peers": ["F", "GM"]},
            "JPM": {"sector": "Financials", "peers": ["BAC", "WFC", "C"]},
            "JNJ": {"sector": "Healthcare", "peers": ["PFE", "UNH", "ABBV"]},
        }

        # Sector average benchmarks (실제로는 API나 DB에서 가져와야 함)
        SECTOR_BENCHMARKS = {
            "Technology": {
                "avg_pe": 28.5,
                "avg_growth": 0.15,  # 15%
                "avg_margin": 0.25   # 25%
            },
            "Financials": {
                "avg_pe": 12.0,
                "avg_growth": 0.08,
                "avg_margin": 0.20
            },
            "Healthcare": {
                "avg_pe": 18.0,
                "avg_growth": 0.12,
                "avg_margin": 0.18
            },
            "Automotive": {
                "avg_pe": 15.0,
                "avg_growth": 0.10,
                "avg_margin": 0.08
            },
            "DEFAULT": {
                "avg_pe": 20.0,
                "avg_growth": 0.10,
                "avg_margin": 0.15
            }
        }

        # 1. 섹터 확인
        sector_info = SECTOR_MAP.get(ticker, {"sector": "Unknown", "peers": []})
        sector = sector_info["sector"]
        peers = sector_info["peers"]

        # 2. 섹터 벤치마크 가져오기
        benchmark = SECTOR_BENCHMARKS.get(sector, SECTOR_BENCHMARKS["DEFAULT"])

        # 3. 분석 대상 지표
        pe_ratio = fundamental_data.get("pe_ratio", 20)
        revenue_growth = fundamental_data.get("revenue_growth", 0.10)
        profit_margin = fundamental_data.get("profit_margin", 0.15)

        # 4. 섹터 평균 대비 비교
        # P/E Ratio
        if pe_ratio < benchmark["avg_pe"] * 0.85:
            pe_vs_sector = "BELOW"  # 저평가
            pe_interpretation = f"섹터 평균({benchmark['avg_pe']:.1f}) 대비 저평가 (P/E {pe_ratio:.1f})"
        elif pe_ratio > benchmark["avg_pe"] * 1.15:
            pe_vs_sector = "ABOVE"  # 고평가
            pe_interpretation = f"섹터 평균({benchmark['avg_pe']:.1f}) 대비 고평가 (P/E {pe_ratio:.1f})"
        else:
            pe_vs_sector = "INLINE"
            pe_interpretation = f"섹터 평균 수준 (P/E {pe_ratio:.1f})"

        # Revenue Growth
        if revenue_growth > benchmark["avg_growth"] * 1.3:
            growth_vs_peers = "OUTPERFORMING"
            growth_interpretation = f"섹터 평균({benchmark['avg_growth']*100:.1f}%) 대비 우수 ({revenue_growth*100:.1f}%)"
        elif revenue_growth < benchmark["avg_growth"] * 0.7:
            growth_vs_peers = "UNDERPERFORMING"
            growth_interpretation = f"섹터 평균({benchmark['avg_growth']*100:.1f}%) 대비 부진 ({revenue_growth*100:.1f}%)"
        else:
            growth_vs_peers = "INLINE"
            growth_interpretation = f"섹터 평균 수준 ({revenue_growth*100:.1f}%)"

        # Profit Margin
        if profit_margin > benchmark["avg_margin"] * 1.2:
            margin_vs_peers = "SUPERIOR"
            margin_interpretation = f"섹터 평균({benchmark['avg_margin']*100:.1f}%) 대비 우수 ({profit_margin*100:.1f}%)"
        elif profit_margin < benchmark["avg_margin"] * 0.8:
            margin_vs_peers = "INFERIOR"
            margin_interpretation = f"섹터 평균({benchmark['avg_margin']*100:.1f}%) 대비 부진 ({profit_margin*100:.1f}%)"
        else:
            margin_vs_peers = "AVERAGE"
            margin_interpretation = f"섹터 평균 수준 ({profit_margin*100:.1f}%)"

        # 5. 종합 경쟁 우위 판정
        score = 0

        # P/E가 낮으면 +1 (저평가 = 좋음)
        if pe_vs_sector == "BELOW":
            score += 1
        elif pe_vs_sector == "ABOVE":
            score -= 1

        # Growth 높으면 +1
        if growth_vs_peers == "OUTPERFORMING":
            score += 1
        elif growth_vs_peers == "UNDERPERFORMING":
            score -= 1

        # Margin 높으면 +1
        if margin_vs_peers == "SUPERIOR":
            score += 1
        elif margin_vs_peers == "INFERIOR":
            score -= 1

        # 경쟁 위치 판정
        if score >= 2:
            competitive_position = "LEADER"
            position_reasoning = "섹터 내 경쟁 우위 확보"
        elif score >= 0:
            competitive_position = "COMPETITIVE"
            position_reasoning = "섹터 평균 수준 유지"
        else:
            competitive_position = "LAGGING"
            position_reasoning = "섹터 내 경쟁 열위"

        # 6. 종합 reasoning
        reasoning = f"""
{sector} 섹터 분석 (경쟁사: {', '.join(peers[:3]) if peers else 'N/A'}):
- {pe_interpretation}
- {growth_interpretation}
- {margin_interpretation}
→ {position_reasoning}
""".strip()

        return {
            "sector": sector,
            "peers": peers,
            "peer_comparison": {
                "pe_vs_sector": pe_vs_sector,
                "growth_vs_peers": growth_vs_peers,
                "margin_vs_peers": margin_vs_peers
            },
            "competitive_position": competitive_position,
            "competitive_score": score,
            "reasoning": reasoning
        }
