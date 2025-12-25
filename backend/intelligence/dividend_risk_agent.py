"""
Dividend Risk Agent - 배당주 리스크 평가 에이전트

Phase 21: Dividend Intelligence Module - Step 1.4
Date: 2025-12-25

Features:
- 리스크 점수 계산 (0-100, 높을수록 위험)
- Payout Ratio, FCF, Debt/Equity 분석
- 섹터별 금리/경기 민감도
- War Room 9번째 에이전트로 통합
"""

import yfinance as yf
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DividendRiskAgent:
    """배당주 리스크 평가 에이전트"""
    
    # 리스크 점수 기준
    RISK_THRESHOLDS = {
        "payout_ratio": {
            "normal": 80,     # 일반 기업: 80% 초과 시 위험
            "reit": 100       # REIT: 100% 초과 시 위험 (REIT는 90% 이상 배당 의무)
        },
        "fcf": 0,             # FCF < 0 위험
        "debt_to_equity": 2.0  # D/E > 2.0 위험
    }
    
    # 리스크 점수 가중치
    RISK_WEIGHTS = {
        "payout_ratio": 40,   # 배당 성향 (최대 40점)
        "fcf": 30,            # 잉여현금흐름 (최대 30점)
        "debt_to_equity": 15, # 부채비율 (최대 15점)
        "dividend_growth": 15 # 배당 성장성 (최대 15점)
    }
    
    def calculate_risk_score(self, ticker: str) -> Dict:
        """
        리스크 점수 계산 (0-100, 높을수록 위험)
        
        평가 기준:
        - Payout Ratio > 80% (리츠는 100%): +40점
        - FCF (Free Cash Flow) < 0: +30점
        - Debt/Equity > 2.0: +15점
        - 5년 배당 성장 정체 (< 3%): +15점
        
        Args:
            ticker: 종목 코드
        
        Returns:
            {
                "ticker": "JNJ",
                "risk_score": 25,
                "risk_level": "Safe",  # Safe | Warning | Danger
                "warnings": [
                    "High Payout Ratio 85.3%"
                ],
                "metrics": {
                    "payout_ratio": 85.3,
                    "fcf": 15000000000,
                    "debt_to_equity": 1.2,
                    "dividend_growth_5y": 6.5
                },
                "sector": "Healthcare",
                "is_reit": false
            }
        """
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            risk_score = 0
            warnings = []
            metrics = {}
            
            # 섹터 정보
            sector = info.get('sector', 'Unknown')
            is_reit = (sector == 'Real Estate')
            
            # 1. Payout Ratio 체크
            payout_ratio = info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0
            metrics['payout_ratio'] = round(payout_ratio, 2)
            
            threshold = self.RISK_THRESHOLDS['payout_ratio']['reit'] if is_reit else self.RISK_THRESHOLDS['payout_ratio']['normal']
            
            if payout_ratio > threshold:
                points = self.RISK_WEIGHTS['payout_ratio']
                risk_score += points
                
                if is_reit:
                    warnings.append(f"Payout Ratio {payout_ratio:.1f}% exceeds 100% (REIT)")
                else:
                    warnings.append(f"High Payout Ratio {payout_ratio:.1f}%")
                
                logger.warning(f"{ticker}: High payout ratio {payout_ratio:.1f}% (+{points} risk)")
            
            # 2. FCF (Free Cash Flow) 체크
            fcf = info.get('freeCashflow', 0)
            metrics['fcf'] = fcf
            
            if fcf < 0:
                points = self.RISK_WEIGHTS['fcf']
                risk_score += points
                warnings.append("Negative Free Cash Flow")
                logger.warning(f"{ticker}: Negative FCF (+{points} risk)")
            
            # 3. Debt/Equity 체크
            debt_to_equity_raw = info.get('debtToEquity', 0)
            debt_to_equity = debt_to_equity_raw / 100 if debt_to_equity_raw else 0
            metrics['debt_to_equity'] = round(debt_to_equity, 2)
            
            if debt_to_equity > self.RISK_THRESHOLDS['debt_to_equity']:
                points = self.RISK_WEIGHTS['debt_to_equity']
                risk_score += points
                warnings.append(f"High Debt/Equity {debt_to_equity:.2f}")
                logger.warning(f"{ticker}: High D/E {debt_to_equity:.2f} (+{points} risk)")
            
            # 4. 배당 성장 정체 체크
            dividend_growth_5y = info.get('dividendGrowth', 0) * 100 if info.get('dividendGrowth') else None
            
            if dividend_growth_5y is not None:
                metrics['dividend_growth_5y'] = round(dividend_growth_5y, 2)
                
                if dividend_growth_5y < 3:  # 5년 평균 성장률 < 3%
                    points = self.RISK_WEIGHTS['dividend_growth']
                    risk_score += points
                    warnings.append(f"Low Dividend Growth {dividend_growth_5y:.1f}%")
                    logger.warning(f"{ticker}: Low dividend growth (+{points} risk)")
            else:
                # 배당 성장 데이터 없음
                metrics['dividend_growth_5y'] = None
            
            # 리스크 레벨 결정
            risk_level = self._get_risk_level(risk_score)
            
            return {
                "ticker": ticker,
                "risk_score": min(risk_score, 100),  # 최대 100점
                "risk_level": risk_level,
                "warnings": warnings,
                "metrics": metrics,
                "sector": sector,
                "is_reit": is_reit
            }
        
        except Exception as e:
            logger.error(f"Failed to calculate risk score for {ticker}: {e}")
            return {
                "ticker": ticker,
                "risk_score": 0,
                "risk_level": "Unknown",
                "warnings": [f"Error: {str(e)}"],
                "metrics": {},
                "sector": "Unknown",
                "is_reit": False,
                "error": str(e)
            }
    
    def _get_risk_level(self, score: int) -> str:
        """리스크 레벨 반환"""
        if score < 30:
            return "Safe"
        elif score < 60:
            return "Warning"
        else:
            return "Danger"
    
    def get_sector_sensitivity(self, sector: str) -> Dict:
        """
        섹터별 금리/경기 민감도
        
        Args:
            sector: 섹터명 (예: "Utilities", "Real Estate")
        
        Returns:
            {
                "sector": "Utilities",
                "interest_rate": "High",  # Low | Medium | High
                "economy": "Low",         # Low | Medium | High
                "description": "금리 상승 시 배당주 가격 하락 위험"
            }
        """
        
        sensitivities = {
            "Utilities": {
                "interest_rate": "High",
                "economy": "Low",
                "description": "금리 상승 시 배당주 가격 하락 위험. 경기 방어적"
            },
            "Real Estate": {
                "interest_rate": "High",
                "economy": "Medium",
                "description": "금리 민감도 매우 높음. 부동산 경기 영향"
            },
            "Consumer Staples": {
                "interest_rate": "Low",
                "economy": "Low",
                "description": "금리/경기 둔감. 가장 안정적인 배당주"
            },
            "Financials": {
                "interest_rate": "Medium",
                "economy": "High",
                "description": "금리 상승 시 이익 증가 가능. 경기 민감"
            },
            "Energy": {
                "interest_rate": "Medium",
                "economy": "High",
                "description": "유가 및 경기 변동 영향 큼"
            },
            "Healthcare": {
                "interest_rate": "Low",
                "economy": "Low",
                "description": "경기 방어적. 안정적 배당"
            },
            "Industrials": {
                "interest_rate": "Medium",
                "economy": "High",
                "description": "경기 순환적. 경기 좋을 때 배당 증가"
            },
            "Technology": {
                "interest_rate": "Medium",
                "economy": "Medium",
                "description": "성장주 성향 강함. 배당률 낮음"
            },
            "Communication Services": {
                "interest_rate": "Medium",
                "economy": "Medium",
                "description": "경쟁 및 규제 리스크"
            },
            "Consumer Discretionary": {
                "interest_rate": "Medium",
                "economy": "High",
                "description": "경기 순환적. 소비 심리 영향"
            },
            "Materials": {
                "interest_rate": "Medium",
                "economy": "High",
                "description": "원자재 가격 및 경기 영향"
            }
        }
        
        default = {
            "interest_rate": "Medium",
            "economy": "Medium",
            "description": "일반적인 섹터 특성"
        }
        
        result = sensitivities.get(sector, default)
        result['sector'] = sector
        
        return result
    
    async def vote_for_war_room(self, ticker: str, context: Dict) -> Dict:
        """
        War Room 투표 (9번째 에이전트)
        
        배당주 리스크 관점에서 투표
        
        Args:
            ticker: 종목 코드
            context: War Room 컨텍스트 (가격, 뉴스 등)
        
        Returns:
            {
                "agent": "dividend_risk",
                "ticker": "JNJ",
                "action": "BUY",  # BUY | SELL | HOLD | REDUCE
                "confidence": 0.75,
                "reasoning": "Low risk score (25). Safe dividend stock with...",
                "risk_assessment": {
                    "risk_score": 25,
                    "risk_level": "Safe",
                    ...
                }
            }
        """
        
        # 리스크 평가
        risk_assessment = self.calculate_risk_score(ticker)
        
        risk_score = risk_assessment['risk_score']
        risk_level = risk_assessment['risk_level']
        
        # 투표 결정 로직
        if risk_score < 30:
            # Low Risk: BUY 추천
            action = "BUY"
            confidence = 0.70 + (30 - risk_score) / 100  # 0.70 ~ 1.00
            reasoning = f"Low risk score ({risk_score}). Safe dividend stock with strong fundamentals. "
            
        elif risk_score < 60:
            # Medium Risk: HOLD 또는 REDUCE
            action = "HOLD"
            confidence = 0.50 + (60 - risk_score) / 100  # 0.50 ~ 0.80
            reasoning = f"Medium risk score ({risk_score}). Some concerns exist. "
            
            if risk_assessment['warnings']:
                reasoning += f"Warnings: {'; '.join(risk_assessment['warnings'][:2])}. "
            
        else:
            # High Risk: SELL 추천
            action = "SELL"
            confidence = 0.60 + (risk_score - 60) / 100  # 0.60 ~ 1.00
            reasoning = f"High risk score ({risk_score}). Significant dividend sustainability concerns. "
            reasoning += f"Warnings: {'; '.join(risk_assessment['warnings'])}. "
        
        # 섹터 민감도 추가
        sector_sensitivity = self.get_sector_sensitivity(risk_assessment['sector'])
        reasoning += f"Sector: {risk_assessment['sector']} (Interest Rate Sensitivity: {sector_sensitivity['interest_rate']}). "
        
        return {
            "agent": "dividend_risk",
            "ticker": ticker,
            "action": action,
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "risk_assessment": risk_assessment,
            "sector_sensitivity": sector_sensitivity
        }


# CLI 실행
async def main():
    """테스트 실행"""
    
    agent = DividendRiskAgent()
    
    print("=" * 70)
    print("Dividend Risk Agent Test")
    print("=" * 70)
    print()
    
    # 테스트 종목
    test_tickers = [
        "JNJ",    # 안전한 배당주
        "T",      # 높은 배당률 (위험 가능)
        "F",      # 제조업 (경기 순환)
        "O"       # REIT
    ]
    
    for ticker in test_tickers:
        print(f"\n📊 Testing: {ticker}")
        print("-" * 70)
        
        # 리스크 평가
        risk = agent.calculate_risk_score(ticker)
        
        print(f"Risk Score: {risk['risk_score']} ({risk['risk_level']})")
        print(f"Sector: {risk['sector']} (REIT: {risk['is_reit']})")
        print(f"Metrics:")
        print(f"  - Payout Ratio: {risk['metrics'].get('payout_ratio', 'N/A')}%")
        print(f"  - FCF: ${risk['metrics'].get('fcf', 0):,.0f}")
        print(f"  - Debt/Equity: {risk['metrics'].get('debt_to_equity', 'N/A')}")
        print(f"  - Dividend Growth (5y): {risk['metrics'].get('dividend_growth_5y', 'N/A')}%")
        
        if risk['warnings']:
            print(f"⚠️ Warnings:")
            for warning in risk['warnings']:
                print(f"  - {warning}")
        
        # 섹터 민감도
        sensitivity = agent.get_sector_sensitivity(risk['sector'])
        print(f"Sensitivity:")
        print(f"  - Interest Rate: {sensitivity['interest_rate']}")
        print(f"  - Economy: {sensitivity['economy']}")
        print(f"  - Description: {sensitivity['description']}")
        
        # War Room 투표
        vote = await agent.vote_for_war_room(ticker, {})
        print(f"\n🗳️ War Room Vote:")
        print(f"  - Action: {vote['action']}")
        print(f"  - Confidence: {vote['confidence']:.0%}")
        print(f"  - Reasoning: {vote['reasoning'][:100]}...")
    
    print("\n" + "=" * 70)
    print("✅ Test completed")
    print("=" * 70)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
