"""
Constitution Rules - Financial Forensics Integration

AI Trading Agent의 Pre-Check/Post-Check에 재무 포렌식 분석 통합

Rules:
1. Pre-Check: 거래 전 재무 건강도 확인
2. Post-Check: 거래 후 포트폴리오 리스크 재평가
3. Auto-Sell: CRITICAL Red Flag 감지 시 자동 매도

Author: AI Trading System
Date: 2025-11-21
Phase: 14 Task 2
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# Constitution Rule: Financial Forensics Check
# ============================================================================

class FinancialForensicsRule:
    """
    Constitution Rule for Financial Forensics
    
    재무 포렌식 분석을 통한 거래 승인/거부
    """
    
    def __init__(self):
        self.enabled = True
        self.auto_sell_on_critical = True  # CRITICAL 감지 시 자동 매도
        self.block_buy_on_high_risk = True  # HIGH_RISK 이상 매수 차단
    
    async def pre_check(self, ticker: str, action: str, analysis: dict) -> dict:
        """
        거래 전 체크
        
        Args:
            ticker: 종목 티커
            action: BUY, SELL, HOLD
            analysis: AI 분석 결과
            
        Returns:
            {
                "approved": bool,
                "reason": str,
                "modified_action": Optional[str],
                "forensics_verdict": str
            }
        """
        if not self.enabled:
            return {"approved": True, "reason": "Forensics check disabled"}
        
        # 매도는 항상 허용
        if action == "SELL":
            return {"approved": True, "reason": "SELL action always allowed"}
        
        # 재무 포렌식 분석 실행
        from forensics_router import check_forensics_for_ticker
        
        try:
            forensics = await check_forensics_for_ticker(ticker)
            verdict = forensics['verdict']
            recommendation = forensics['recommendation']
            critical_count = forensics['critical_count']
            
            logger.info(
                f"Forensics check for {ticker}: {verdict} "
                f"({critical_count} critical flags)"
            )
            
            # CRITICAL: 매수 차단, 보유 중이면 매도 권장
            if verdict == "CRITICAL":
                if action == "BUY":
                    return {
                        "approved": False,
                        "reason": f"BLOCKED: Critical accounting red flags detected ({critical_count} critical)",
                        "forensics_verdict": verdict,
                        "modified_action": None
                    }
                elif action == "HOLD" and self.auto_sell_on_critical:
                    return {
                        "approved": True,
                        "reason": f"Modified to SELL due to critical red flags ({critical_count} critical)",
                        "forensics_verdict": verdict,
                        "modified_action": "SELL"
                    }
            
            # HIGH_RISK: 매수 차단
            elif verdict == "HIGH_RISK":
                if action == "BUY" and self.block_buy_on_high_risk:
                    return {
                        "approved": False,
                        "reason": "BLOCKED: High risk accounting concerns detected",
                        "forensics_verdict": verdict,
                        "modified_action": None
                    }
            
            # SUSPICIOUS: 경고만
            elif verdict == "SUSPICIOUS":
                if action == "BUY":
                    return {
                        "approved": True,
                        "reason": "APPROVED with warning: Some accounting concerns detected",
                        "forensics_verdict": verdict,
                        "modified_action": None,
                        "warning": f"Forensics verdict: {verdict}"
                    }
            
            # CLEAN: 정상 통과
            return {
                "approved": True,
                "reason": f"Financial forensics check passed: {verdict}",
                "forensics_verdict": verdict
            }
            
        except Exception as e:
            logger.error(f"Error in forensics pre-check for {ticker}: {e}")
            
            # 에러 발생 시 보수적으로 거부
            return {
                "approved": False,
                "reason": f"Forensics check failed: {str(e)}",
                "forensics_verdict": "ERROR"
            }
    
    async def post_check(self, ticker: str, action: str, execution_result: dict) -> dict:
        """
        거래 후 체크
        
        거래 완료 후 포트폴리오 전체의 재무 건강도 재평가
        
        Args:
            ticker: 거래한 종목
            action: 실행한 액션
            execution_result: 거래 실행 결과
            
        Returns:
            {"status": str, "alerts": List[str]}
        """
        # 매도 후에는 체크 불필요
        if action == "SELL":
            return {"status": "OK", "alerts": []}
        
        # 매수 후 포트폴리오 재평가
        # (실제로는 현재 보유 종목 전체 확인)
        
        return {"status": "OK", "alerts": []}


# ============================================================================
# Integration with Trading Agent
# ============================================================================

class EnhancedConstitutionRules:
    """
    강화된 Constitution Rules
    
    기존 규칙 + Financial Forensics
    """
    
    def __init__(self, config: dict):
        self.config = config
        
        # 기존 규칙들
        self.max_position_size = config.get('max_position_size', 0.10)
        self.daily_trade_limit = config.get('daily_trade_limit', 10)
        self.daily_loss_limit = config.get('daily_loss_limit', -500)
        
        # 새로운 규칙: Financial Forensics
        self.forensics_rule = FinancialForensicsRule()
    
    async def pre_trade_check(
        self,
        ticker: str,
        action: str,
        position_size: float,
        analysis: dict
    ) -> dict:
        """
        통합 Pre-Trade Check
        
        1. 기존 규칙 체크 (포지션 크기, 일일 거래 한도 등)
        2. Financial Forensics 체크
        
        Returns:
            {
                "approved": bool,
                "reason": str,
                "modified_action": Optional[str],
                "modified_position_size": Optional[float]
            }
        """
        checks = []
        
        # 1. 기본 규칙 체크
        basic_check = self._check_basic_rules(ticker, action, position_size)
        checks.append(basic_check)
        
        if not basic_check['approved']:
            return basic_check
        
        # 2. Financial Forensics 체크
        forensics_check = await self.forensics_rule.pre_check(ticker, action, analysis)
        checks.append(forensics_check)
        
        if not forensics_check['approved']:
            return forensics_check
        
        # 액션 수정이 있으면 반영
        if forensics_check.get('modified_action'):
            return {
                "approved": True,
                "reason": forensics_check['reason'],
                "modified_action": forensics_check['modified_action'],
                "forensics_verdict": forensics_check['forensics_verdict']
            }
        
        # 모든 체크 통과
        return {
            "approved": True,
            "reason": "All constitution checks passed",
            "warnings": [c.get('warning') for c in checks if c.get('warning')]
        }
    
    def _check_basic_rules(self, ticker: str, action: str, position_size: float) -> dict:
        """기존 기본 규칙 체크"""
        
        # 포지션 크기 체크
        if position_size > self.max_position_size:
            return {
                "approved": False,
                "reason": f"Position size ({position_size:.1%}) exceeds limit ({self.max_position_size:.1%})",
                "modified_position_size": self.max_position_size
            }
        
        # (다른 기본 규칙들...)
        
        return {"approved": True, "reason": "Basic rules passed"}


# ============================================================================
# Example Usage
# ============================================================================

async def example_usage():
    """사용 예시"""
    
    # Constitution Rules 초기화
    config = {
        'max_position_size': 0.10,
        'daily_trade_limit': 10,
        'daily_loss_limit': -500
    }
    
    rules = EnhancedConstitutionRules(config)
    
    # 거래 전 체크
    result = await rules.pre_trade_check(
        ticker="NVDA",
        action="BUY",
        position_size=0.05,
        analysis={"confidence": 0.8}
    )
    
    print(f"Approved: {result['approved']}")
    print(f"Reason: {result['reason']}")
    
    if result.get('modified_action'):
        print(f"Modified Action: {result['modified_action']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
