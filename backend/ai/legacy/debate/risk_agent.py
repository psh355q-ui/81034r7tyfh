"""
Risk Agent for War Room Debate System

Role: Risk management and portfolio protection specialist
Focuses on: Drawdown limits, position sizing, volatility, correlation

Author: ai-trading-system
Date: 2025-12-21
Updated: 2025-12-27 - Added Sharpe Ratio, Kelly Criterion, CDS Premium analysis
"""

import logging
from typing import Dict, Any, Optional, List
import random

logger = logging.getLogger(__name__)


class RiskAgent:
    """
    Risk Agent - 리스크 관리 및 포트폴리오 보호 전문가
    
    Core Capabilities:
    - Drawdown monitoring
    - Position sizing calculation
    - Volatility assessment
    - Portfolio correlation analysis
    """
    
    def __init__(self):
        self.agent_name = "risk"
        self.vote_weight = 0.20  # 20% voting weight (highest authority)
    
    async def analyze(self, ticker: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze risk factors for ticker.
        
        Args:
            ticker: Stock ticker symbol
            context: Optional context (volatility, portfolio state, etc.)
        
        Returns:
            {
                "agent": "risk",
                "action": "BUY|SELL|HOLD",
                "confidence": 0.0-1.0,
                "reasoning": str,
                "risk_factors": {...}
            }
        """
        try:
            logger.info(f"[Risk Agent] Analyzing {ticker}")
            
            if context and "risk_data" in context:
                return await self._analyze_with_real_data(ticker, context["risk_data"])
            else:
                return await self._analyze_mock(ticker)
        
        except Exception as e:
            logger.error(f"[Risk Agent] Error analyzing {ticker}: {e}")
            return self._fallback_response(ticker)
    
    async def _analyze_with_real_data(self, ticker: str, risk_data: Dict) -> Dict:
        """
        Analyze using real risk metrics.

        Expected risk_data format:
        {
            "volatility": 0.25,  # 25% annualized
            "beta": 1.2,
            "max_drawdown": -0.08,  # -8%
            "correlation_spy": 0.85,
            "position_size": 0.05,  # 5% of portfolio
            "returns": [0.01, -0.02, ...],  # Optional: Daily returns for Sharpe calculation
            "cds_spread": 150  # Optional: CDS spread in bps
        }
        """
        volatility = risk_data.get("volatility", 0.20)
        beta = risk_data.get("beta", 1.0)
        max_drawdown = risk_data.get("max_drawdown", 0)
        correlation_spy = risk_data.get("correlation_spy", 0.80)
        position_size = risk_data.get("position_size", 0.05)
        returns = risk_data.get("returns", [])
        cds_spread = risk_data.get("cds_spread", None)

        action = "HOLD"
        confidence = 0.5
        confidence_boost = 0.0
        risk_factors = {}

        # CDS Premium Analysis (if available)
        cds_analysis = None
        if cds_spread is not None:
            cds_analysis = self._analyze_cds_premium(cds_spread, ticker)
            risk_factors["cds_premium"] = {
                "spread_bps": cds_analysis["cds_spread_bps"],
                "credit_risk": cds_analysis["credit_risk_level"],
                "risk_score": f"{cds_analysis['risk_score']:.1f}/10"
            }

            # CDS Premium에 따른 판단
            if cds_analysis["credit_risk_level"] == "CRITICAL":
                # 부도 위험 매우 높음 - 강한 SELL
                action = "SELL"
                confidence = 0.90
                reasoning = f"{cds_analysis['reasoning']} - 즉시 청산 권장"
            elif cds_analysis["credit_risk_level"] == "HIGH":
                # 신용 리스크 높음 - SELL 또는 HOLD
                if action != "SELL":
                    action = "SELL"
                    confidence = 0.80
                    reasoning = cds_analysis['reasoning']
            else:
                # LOW 또는 MODERATE - confidence modifier 적용
                confidence_boost += cds_analysis["confidence_modifier"]

        # Sharpe Ratio Analysis (if returns data available)
        sharpe_ratio = None
        if returns and len(returns) >= 20:
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            risk_factors["sharpe_ratio"] = f"{sharpe_ratio:.2f}"

            # Sharpe Ratio에 따른 판단 (CDS CRITICAL이 아닌 경우만)
            if cds_analysis is None or cds_analysis["credit_risk_level"] not in ["CRITICAL", "HIGH"]:
                if sharpe_ratio < 0.5:
                    # 샤프 비율 낮음 - 리스크 대비 수익 부족
                    if action != "SELL":
                        action = "SELL"
                        confidence = 0.85
                        reasoning = f"낮은 샤프 비율 ({sharpe_ratio:.2f} < 0.5) - 리스크 대비 수익 부족"
                elif sharpe_ratio > 1.5:
                    # 샤프 비율 우수 - 안정적 수익
                    confidence_boost += 0.15

        # VaR Analysis (if returns data available)
        var_analysis = None
        if returns and len(returns) >= 30:
            var_analysis = self._calculate_var(returns)
            risk_factors["var_1day"] = f"{var_analysis['var_1day']*100:.2f}%"
            risk_factors["cvar"] = f"{var_analysis['cvar']*100:.2f}%"

            # VaR에 따른 위험도 판단 (CDS CRITICAL이 아닌 경우만)
            if cds_analysis is None or cds_analysis["credit_risk_level"] not in ["CRITICAL", "HIGH"]:
                var_1day = var_analysis['var_1day']
                cvar = var_analysis['cvar']

                # VaR가 -5% 이하 (헌법 제4조 위반 가능성)
                if var_1day < -0.05:
                    if action != "SELL":
                        action = "SELL"
                        confidence = 0.88
                        reasoning = f"높은 VaR ({var_1day*100:.2f}%) - 헌법 제4조 위반 가능성, CVaR {cvar*100:.2f}%"
                # CVaR가 -10% 이하 (극단적 손실 위험)
                elif cvar < -0.10:
                    confidence_boost -= 0.1
                # VaR가 -2% 이상 (낮은 리스크)
                elif var_1day > -0.02:
                    confidence_boost += 0.05

        # Risk-based decision logic (CDS가 CRITICAL/HIGH가 아닌 경우만)
        if cds_analysis is None or cds_analysis["credit_risk_level"] not in ["CRITICAL", "HIGH"]:
            # HIGH RISK - Recommend SELL or HOLD
            if volatility > 0.40 or max_drawdown < -0.10:
                action = "SELL"
                confidence = 0.85
                reasoning = f"고위험 상태 (변동성 {volatility*100:.0f}%, 최대낙폭 {max_drawdown*100:.1f}%) - 헌법 제4조 위반 가능성"

            elif volatility > 0.30 and beta > 1.5:
                action = "HOLD"
                confidence = 0.75
                reasoning = f"높은 변동성 ({volatility*100:.0f}%) + 고베타 ({beta:.2f}) - 관망 추천"

            # LOW RISK - Approve BUY
            elif volatility < 0.20 and max_drawdown > -0.05:
                action = "BUY"
                base_confidence = 0.87

                # Sharpe Ratio가 우수하면 신뢰도 증가
                if sharpe_ratio and sharpe_ratio > 1.5:
                    confidence = min(0.95, base_confidence + 0.1)
                    reasoning = f"낮은 리스크 (변동성 {volatility*100:.0f}%, 낙폭 {max_drawdown*100:.1f}%) + 우수한 샤프 비율 ({sharpe_ratio:.2f}) - 안전한 진입 가능"
                else:
                    confidence = base_confidence
                    reasoning = f"낮은 리스크 (변동성 {volatility*100:.0f}%, 낙폭 {max_drawdown*100:.1f}%) - 안전한 진입 가능"

                # CDS Premium이 LOW면 추가 신뢰도 증가
                if cds_analysis and cds_analysis["credit_risk_level"] == "LOW":
                    reasoning += f" + 낮은 신용 리스크 (CDS {cds_analysis['cds_spread_bps']}bps)"

            # MEDIUM RISK
            else:
                risk_level = "중간" if volatility < 0.30 else "높음"
                reasoning = f"{risk_level} 리스크 (변동성 {volatility*100:.0f}%, 베타 {beta:.2f}) - 포지션 크기 조절 필요"
                confidence = 0.65

                # Sharpe Ratio 추가 정보
                if sharpe_ratio and sharpe_ratio > 1.0:
                    reasoning += f" | 샤프 비율 양호 ({sharpe_ratio:.2f})"
                    confidence_boost += 0.1

                # CDS Premium 추가 정보
                if cds_analysis and cds_analysis["credit_risk_level"] == "MODERATE":
                    reasoning += f" | 보통 신용도 (CDS {cds_analysis['cds_spread_bps']}bps)"

        # Final confidence adjustment
        confidence = min(0.95, confidence + confidence_boost)

        risk_factors.update({
            "volatility": f"{volatility*100:.1f}%",
            "beta": beta,
            "max_drawdown": f"{max_drawdown*100:.1f}%",
            "correlation_spy": correlation_spy,
            "position_size": f"{position_size*100:.1f}%",
            "risk_level": "HIGH" if volatility > 0.30 else "MEDIUM" if volatility > 0.20 else "LOW"
        })

        return {
            "agent": "risk",
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_factors": risk_factors
        }
    
    async def _analyze_mock(self, ticker: str) -> Dict:
        """Mock risk analysis"""
        scenarios = [
            {
                "action": "BUY",
                "confidence": 0.87,
                "reasoning": "낮은 변동성 (18%), 최대낙폭 -3.2%, 안전한 진입 가능",
                "risk_factors": {
                    "volatility": "18%",
                    "max_drawdown": "-3.2%",
                    "risk_level": "LOW"
                }
            },
            {
                "action": "SELL",
                "confidence": 0.85,
                "reasoning": "고변동성 경고 (45%), 헌법 제4조 (-5% 한도) 임박, 손절 필요",
                "risk_factors": {
                    "volatility": "45%",
                    "max_drawdown": "-8.5%",
                    "risk_level": "CRITICAL"
                }
            },
            {
                "action": "HOLD",
                "confidence": 0.75,
                "reasoning": "중간 변동성 (28%), 베타 1.5 - 포지션 크기 50% 축소 권장",
                "risk_factors": {
                    "volatility": "28%",
                    "beta": 1.5,
                    "risk_level": "MEDIUM"
                }
            }
        ]
        
        return {
            "agent": "risk",
            **random.choice(scenarios)
        }
    
    def _fallback_response(self, ticker: str) -> Dict:
        """Conservative fallback on error"""
        return {
            "agent": "risk",
            "action": "HOLD",
            "confidence": 0.60,
            "reasoning": f"리스크 데이터 부족 - {ticker} 안전을 위해 관망 추천",
            "risk_factors": {
                "error": True,
                "risk_level": "UNKNOWN"
            }
        }

    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.04) -> float:
        """
        샤프 비율 계산

        공식: (평균 수익률 - 무위험 수익률) / 수익률 표준편차

        Args:
            returns: 일별 수익률 리스트 (예: [0.01, -0.02, 0.015, ...])
            risk_free_rate: 연간 무위험 수익률 (기본값: 4% = 0.04)

        Returns:
            Sharpe Ratio
            - < 0: 무위험 수익률보다 낮음 (나쁨)
            - 0-1: 양호
            - 1-2: 우수
            - > 2: 매우 우수

        해석:
        - 1.0 이상이면 리스크 대비 수익이 양호
        - 2.0 이상이면 우수한 투자
        """
        try:
            import numpy as np

            if len(returns) < 20:
                logger.warning(f"Sharpe Ratio 계산 실패: 데이터 부족 ({len(returns)}개)")
                return 0.0

            returns_array = np.array(returns)

            # 연간화 (252 거래일 가정)
            annual_return = np.mean(returns_array) * 252
            annual_volatility = np.std(returns_array) * np.sqrt(252)

            if annual_volatility == 0:
                return 0.0

            sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility

            return sharpe_ratio

        except Exception as e:
            logger.error(f"Sharpe Ratio 계산 오류: {e}")
            return 0.0

    def _calculate_kelly_position(self, win_rate: float, avg_win: float, avg_loss: float) -> Dict:
        """
        켈리 기준 (Kelly Criterion) 포지션 크기 계산

        공식: f* = (p * b - q) / b
        where:
        - f*: 최적 포지션 비율
        - p: 승률
        - q: 패율 (1-p)
        - b: 이익/손실 비율

        Args:
            win_rate: 승률 (0~1, 예: 0.60 = 60%)
            avg_win: 평균 이익률 (예: 0.08 = 8%)
            avg_loss: 평균 손실률 (예: 0.04 = 4%)

        Returns:
            {
                "kelly_fraction": float,  # 켈리 비율
                "half_kelly": float,  # 안전 마진 (켈리의 50%)
                "recommended_pct": float,  # 권장 포지션 비율
                "reasoning": str
            }

        해석:
        - Half-Kelly 사용 (켈리의 50%)으로 안전성 확보
        - 최대 25% 포지션 제한
        """
        try:
            if win_rate <= 0 or win_rate >= 1:
                return {
                    "kelly_fraction": 0.0,
                    "half_kelly": 0.0,
                    "recommended_pct": 0.0,
                    "reasoning": "승률 데이터 부적절"
                }

            if avg_loss == 0:
                return {
                    "kelly_fraction": 0.0,
                    "half_kelly": 0.0,
                    "recommended_pct": 0.0,
                    "reasoning": "손실 데이터 없음"
                }

            p = win_rate  # 승률
            q = 1 - win_rate  # 패율
            b = avg_win / abs(avg_loss)  # 이익/손실 비율

            # 켈리 공식
            kelly_fraction = (p * b - q) / b

            # 안전 마진: Half-Kelly (켈리의 50%)
            # 최대 25% 포지션 제한
            half_kelly = max(0, min(kelly_fraction * 0.5, 0.25))

            if kelly_fraction < 0:
                reasoning = "기대수익 음수 - 거래 부적합"
                recommended_pct = 0.0
            elif half_kelly == 0.25:
                reasoning = f"최대 포지션 제한 (25%) 적용 (Full Kelly: {kelly_fraction:.1%})"
                recommended_pct = 0.25
            else:
                reasoning = f"켈리 기준 권장: {half_kelly:.1%} (승률 {win_rate:.1%}, 이익/손실비 {b:.2f})"
                recommended_pct = half_kelly

            return {
                "kelly_fraction": kelly_fraction,
                "half_kelly": half_kelly,
                "recommended_pct": recommended_pct,
                "reasoning": reasoning
            }

        except Exception as e:
            logger.error(f"Kelly Criterion 계산 오류: {e}")
            return {
                "kelly_fraction": 0.0,
                "half_kelly": 0.0,
                "recommended_pct": 0.0,
                "reasoning": f"계산 오류: {str(e)}"
            }

    def _calculate_var(self, returns: List[float], confidence_level: float = 0.95, time_horizon: int = 1) -> Dict:
        """
        VaR (Value at Risk) 계산 (Historical Method)

        VaR는 특정 신뢰수준에서 주어진 기간 동안 발생할 수 있는 최대 손실을 예측

        Args:
            returns: 일별 수익률 리스트 (예: [0.01, -0.02, 0.015, ...])
            confidence_level: 신뢰수준 (기본값: 0.95 = 95%)
            time_horizon: 예측 기간 (일 수, 기본값: 1일)

        Returns:
            {
                "var_1day": float,  # 1일 VaR (%)
                "var_10day": float,  # 10일 VaR (%)
                "cvar": float,  # Conditional VaR (Expected Shortfall)
                "confidence_level": float,  # 신뢰수준
                "interpretation": str  # 해석
            }

        해석:
        - VaR 95%: "95% 확률로 손실이 VaR보다 작을 것"
        - CVaR: VaR 초과 시 평균 손실 (꼬리 위험)

        예시:
        - VaR 95% 1일 = -3% → "95% 확률로 내일 손실이 -3% 이하일 것"
        - CVaR = -5% → "최악의 5% 시나리오에서 평균 손실은 -5%"
        """
        try:
            import numpy as np

            if len(returns) < 30:
                logger.warning(f"VaR 계산 실패: 데이터 부족 ({len(returns)}개, 최소 30개 필요)")
                return {
                    "var_1day": 0.0,
                    "var_10day": 0.0,
                    "cvar": 0.0,
                    "confidence_level": confidence_level,
                    "interpretation": "데이터 부족 - VaR 계산 불가"
                }

            returns_array = np.array(returns)

            # Historical VaR: 하위 percentile 사용
            var_percentile = (1 - confidence_level) * 100
            var_1day = np.percentile(returns_array, var_percentile)

            # 10일 VaR (Square Root of Time Rule)
            var_10day = var_1day * np.sqrt(10)

            # CVaR (Conditional VaR / Expected Shortfall)
            # VaR 초과 손실의 평균
            tail_losses = returns_array[returns_array <= var_1day]
            cvar = np.mean(tail_losses) if len(tail_losses) > 0 else var_1day

            # 해석 생성
            interpretation = (
                f"95% 신뢰수준 1일 VaR: {var_1day*100:.2f}% "
                f"(95% 확률로 손실이 {abs(var_1day)*100:.2f}% 이하) | "
                f"최악 5% 시나리오 평균 손실(CVaR): {cvar*100:.2f}%"
            )

            logger.info(f"[Risk Agent] VaR 계산 완료: 1일 VaR={var_1day*100:.2f}%, CVaR={cvar*100:.2f}%")

            return {
                "var_1day": var_1day,
                "var_10day": var_10day,
                "cvar": cvar,
                "confidence_level": confidence_level,
                "interpretation": interpretation
            }

        except Exception as e:
            logger.error(f"VaR 계산 오류: {e}")
            return {
                "var_1day": 0.0,
                "var_10day": 0.0,
                "cvar": 0.0,
                "confidence_level": confidence_level,
                "interpretation": f"VaR 계산 실패: {str(e)}"
            }

    def _analyze_cds_premium(self, cds_spread: float, ticker: str = "") -> Dict:
        """
        CDS Premium (Credit Default Swap Spread) 분석

        CDS Premium은 기업의 신용 리스크를 나타내는 지표
        - 높을수록 부도 위험이 높음
        - 시장이 인식하는 기업의 신용도 반영

        Args:
            cds_spread: CDS 스프레드 (bps, 예: 150 = 1.5%)
            ticker: 종목 코드 (로깅용)

        Returns:
            {
                "credit_risk_level": str,  # LOW/MODERATE/HIGH/CRITICAL
                "risk_score": float,  # 0-10 (10이 최악)
                "reasoning": str,
                "action_impact": str  # POSITIVE/NEUTRAL/NEGATIVE
            }

        CDS Spread 기준:
        - < 100 bps (1%): 낮은 신용 리스크 (투자 등급)
        - 100-200 bps: 보통 신용 리스크
        - 200-500 bps: 높은 신용 리스크 (투기 등급)
        - > 500 bps (5%): 매우 높은 신용 리스크 (부도 임박 가능성)
        """
        try:
            # CDS Spread에 따른 신용 리스크 등급 결정
            if cds_spread < 100:
                credit_risk_level = "LOW"
                risk_score = min(10, cds_spread / 100 * 3)  # 0-3점
                reasoning = f"낮은 신용 리스크 (CDS {cds_spread:.0f}bps) - 투자 등급 기업"
                action_impact = "POSITIVE"
                confidence_modifier = 0.1  # BUY 신뢰도 증가

            elif cds_spread < 200:
                credit_risk_level = "MODERATE"
                risk_score = 3 + (cds_spread - 100) / 100 * 3  # 3-6점
                reasoning = f"보통 신용 리스크 (CDS {cds_spread:.0f}bps) - 안정적이나 주의 필요"
                action_impact = "NEUTRAL"
                confidence_modifier = 0.0

            elif cds_spread < 500:
                credit_risk_level = "HIGH"
                risk_score = 6 + (cds_spread - 200) / 300 * 3  # 6-9점
                reasoning = f"높은 신용 리스크 (CDS {cds_spread:.0f}bps) - 투기 등급, 부도 위험 상승"
                action_impact = "NEGATIVE"
                confidence_modifier = -0.15  # SELL 신호 강화

            else:  # >= 500 bps
                credit_risk_level = "CRITICAL"
                risk_score = min(10, 9 + (cds_spread - 500) / 500)  # 9-10점
                reasoning = f"매우 높은 신용 리스크 (CDS {cds_spread:.0f}bps) - 부도 임박 가능성"
                action_impact = "NEGATIVE"
                confidence_modifier = -0.25  # 강한 SELL 신호

            logger.info(f"[Risk Agent] CDS Premium 분석 ({ticker}): {cds_spread}bps → {credit_risk_level}")

            return {
                "credit_risk_level": credit_risk_level,
                "risk_score": risk_score,
                "cds_spread_bps": cds_spread,
                "reasoning": reasoning,
                "action_impact": action_impact,
                "confidence_modifier": confidence_modifier
            }

        except Exception as e:
            logger.error(f"CDS Premium 분석 오류 ({ticker}): {e}")
            return {
                "credit_risk_level": "UNKNOWN",
                "risk_score": 5.0,
                "cds_spread_bps": 0,
                "reasoning": f"CDS 데이터 분석 실패: {str(e)}",
                "action_impact": "NEUTRAL",
                "confidence_modifier": 0.0
            }
