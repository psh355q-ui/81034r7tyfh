"""
Enhanced Trading Agent V2

기존 TradingAgent를 확장하여 새 모듈들을 통합:
- DynamicScreener: 일일 종목 자동 선정
- MacroDataCollector: 매크로 환경 체크
- SkepticAgent: 최종 결정 전 반대 논거 검토
- FeedbackLoop: 예측 결과 추적 및 보정

사용법:
    agent = EnhancedTradingAgent()
    
    # 1. 오늘의 후보 종목 가져오기
    candidates = await agent.get_daily_candidates()
    
    # 2. 분석 (매크로 체크 + 회의론적 검토 포함)
    decision = await agent.analyze_enhanced("NVDA")
    
    # 3. 일일 브리핑 생성
    briefing = await agent.generate_daily_briefing()
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from backend.ai.trading_agent import TradingAgent
from backend.models.trading_decision import TradingDecision

# New V2 Modules
from backend.services.market_scanner import DynamicScreener, ScreenerCandidate
from backend.services.market_scanner.massive_api_client import get_massive_client
from backend.ai.macro import MacroDataCollector, MacroSnapshot, MarketRegime
from backend.ai.feedback import FeedbackLoop
from backend.ai.reasoning.skeptic_agent import SkepticAgent, SkepticRecommendation
from backend.ai.reasoning.macro_consistency_checker import MacroConsistencyChecker
from backend.intelligence.reporter.daily_briefing import DailyBriefingGenerator

logger = logging.getLogger(__name__)


class EnhancedTradingAgent(TradingAgent):
    """
    Enhanced Trading Agent V2
    
    기존 TradingAgent + 새 모듈 통합:
    - Dynamic Screener (Phase A)
    - Macro Data Collector (Phase C)
    - Self-Feedback Loop (Phase D)
    - Skeptic Agent (Phase G)
    """
    
    def __init__(self, enable_skeptic: bool = True, enable_macro_check: bool = True):
        super().__init__()
        
        # V2 모듈 초기화
        self.massive_client = get_massive_client()
        self.screener = DynamicScreener(
            max_candidates=20,
            massive_api_client=self.massive_client,
        )
        self.macro_collector = MacroDataCollector()
        self.feedback_loop = FeedbackLoop()
        self.skeptic_agent = SkepticAgent()
        self.macro_checker = MacroConsistencyChecker()
        self.briefing_generator = DailyBriefingGenerator()
        
        # 설정
        self.enable_skeptic = enable_skeptic
        self.enable_macro_check = enable_macro_check
        
        # V2 메트릭스
        self.v2_metrics = {
            "screener_scans": 0,
            "macro_checks": 0,
            "skeptic_reviews": 0,
            "predictions_recorded": 0,
            "skeptic_blocked": 0,  # Skeptic이 AVOID 권고한 횟수
        }
        
        logger.info("EnhancedTradingAgent V2 initialized")
        logger.info(f"  - Skeptic Agent: {'enabled' if enable_skeptic else 'disabled'}")
        logger.info(f"  - Macro Check: {'enabled' if enable_macro_check else 'disabled'}")
    
    async def get_daily_candidates(self, force_scan: bool = False) -> List[ScreenerCandidate]:
        """
        오늘의 후보 종목 가져오기
        
        Args:
            force_scan: True이면 캐시 무시하고 새로 스캔
            
        Returns:
            List[ScreenerCandidate]: 후보 종목 리스트
        """
        if force_scan:
            result = await self.screener.scan()
            self.v2_metrics["screener_scans"] += 1
            return result.candidates
        
        # 캐시된 결과 확인
        result = self.screener.get_last_result()
        if result:
            return result.candidates
        
        # 캐시 없으면 새로 스캔
        result = await self.screener.scan()
        self.v2_metrics["screener_scans"] += 1
        return result.candidates
    
    async def analyze_enhanced(
        self,
        ticker: str,
        market_context: Optional[Dict] = None,
        portfolio_context: Optional[Dict] = None,
        skip_skeptic: bool = False,
    ) -> Dict[str, Any]:
        """
        강화된 분석 수행
        
        1. 매크로 환경 체크 (신규)
        2. 기존 TradingAgent.analyze() 호출
        3. Skeptic Agent 검토 (신규)
        4. 예측 기록 (신규)
        
        Args:
            ticker: 종목 티커
            market_context: 시장 컨텍스트
            portfolio_context: 포트폴리오 컨텍스트
            skip_skeptic: Skeptic 검토 건너뛰기
            
        Returns:
            Dict with decision, macro_snapshot, skeptic_analysis
        """
        result = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "decision": None,
            "macro_snapshot": None,
            "macro_warnings": [],
            "skeptic_analysis": None,
            "final_recommendation": None,
        }
        
        # Step 1: 매크로 환경 체크
        if self.enable_macro_check:
            try:
                macro = await self.macro_collector.get_snapshot()
                result["macro_snapshot"] = self.macro_collector.to_dict(macro)
                self.v2_metrics["macro_checks"] += 1
                
                # 매크로 경고 확인
                adjustment = self.macro_collector.get_trading_signal_adjustment(macro)
                result["macro_warnings"] = adjustment.get("warnings", [])
                
                # CRASH 모드면 매수 차단
                if macro.market_regime == MarketRegime.CRASH:
                    logger.warning(f"CRASH 모드 감지 - {ticker} 분석 제한")
                    result["decision"] = TradingDecision(
                        ticker=ticker,
                        action="HOLD",
                        conviction=0.0,
                        reasoning="시장 폭락 국면 (CRASH) - 매수 보류",
                        risk_factors=["market_crash"],
                        features_used={},
                    )
                    result["final_recommendation"] = "HOLD - 시장 상황 불안정"
                    return result
                
                # 매크로 컨텍스트 업데이트
                if market_context is None:
                    market_context = {}
                market_context.update({
                    "vix": macro.vix,
                    "market_regime": macro.market_regime.value,
                    "risk_on_score": macro.risk_on_score,
                })
                
            except Exception as e:
                logger.error(f"매크로 데이터 수집 실패: {e}")
        
        # Step 2: 기존 분석 실행
        decision = await self.analyze(
            ticker=ticker,
            market_context=market_context,
            portfolio_context=portfolio_context,
        )
        result["decision"] = decision
        
        # Step 3: Skeptic Agent 검토
        if self.enable_skeptic and not skip_skeptic and decision.action != "HOLD":
            try:
                consensus = {
                    "action": decision.action,
                    "confidence": decision.conviction,
                    "reasoning": decision.reasoning,
                }
                
                skeptic = await self.skeptic_agent.analyze(
                    ticker=ticker,
                    consensus_analysis=consensus,
                    market_data={
                        "pe_ratio": decision.features_used.get("pe_ratio"),
                        "short_interest": decision.features_used.get("short_interest"),
                    },
                )
                
                result["skeptic_analysis"] = {
                    "skeptic_score": skeptic.skeptic_score,
                    "recommendation": skeptic.recommendation.value,
                    "counter_arguments": skeptic.counter_arguments[:3],
                    "overlooked_risks": skeptic.overlooked_risks[:3],
                    "worst_case_probability": skeptic.worst_case_probability,
                }
                
                self.v2_metrics["skeptic_reviews"] += 1
                
                # Skeptic이 AVOID 권고하면 경고
                if skeptic.recommendation == SkepticRecommendation.AVOID:
                    logger.warning(f"Skeptic AVOID 권고: {ticker}")
                    result["final_recommendation"] = (
                        f"⚠️ 주의: Skeptic Agent가 {decision.action} 회피 권고 "
                        f"(회의론 점수: {skeptic.skeptic_score:.0f})"
                    )
                    self.v2_metrics["skeptic_blocked"] += 1
                else:
                    result["final_recommendation"] = (
                        f"{decision.action} (확신도: {decision.conviction:.0%})"
                    )
                
            except Exception as e:
                logger.error(f"Skeptic 분석 실패: {e}")
        else:
            result["final_recommendation"] = f"{decision.action} (확신도: {decision.conviction:.0%})"
        
        # Step 4: 예측 기록
        try:
            await self.feedback_loop.record_prediction(
                ticker=ticker,
                action=decision.action,
                conviction=decision.conviction,
                model_used="enhanced_trading_agent",
                entry_price=decision.features_used.get("current_price"),
                reasoning=decision.reasoning[:200],
            )
            self.v2_metrics["predictions_recorded"] += 1
        except Exception as e:
            logger.error(f"예측 기록 실패: {e}")
        
        return result
    
    async def check_macro_consistency(self) -> Dict[str, Any]:
        """
        매크로 정합성 체크
        
        경제 지표 간 모순 탐지
        
        Returns:
            Dict with contradictions and report
        """
        try:
            macro = await self.macro_collector.get_snapshot()
            
            # 체커에 전달할 데이터 구성
            macro_data = {
                "vix": macro.vix,
                "credit_spread": macro.credit_spread,
                "sp500_return_1m": macro.sp500_return_1m,
            }
            
            contradictions = await self.macro_checker.detect_contradictions(macro_data)
            
            return {
                "contradictions_found": len(contradictions),
                "contradictions": [
                    {
                        "type": c.anomaly_type.value,
                        "severity": c.severity.value,
                        "description": c.contradiction_description,
                        "implication": c.market_implication,
                    }
                    for c in contradictions
                ],
                "report": self.macro_checker.format_report_korean(contradictions),
            }
            
        except Exception as e:
            logger.error(f"매크로 정합성 체크 실패: {e}")
            return {"error": str(e)}
    
    async def generate_daily_briefing(self) -> str:
        """
        일일 브리핑 생성 (한국어)
        
        Returns:
            str: Markdown 형식 브리핑
        """
        try:
            briefing = await self.briefing_generator.generate_daily_briefing()
            return self.briefing_generator.to_markdown(briefing)
        except Exception as e:
            logger.error(f"일일 브리핑 생성 실패: {e}")
            return f"# 브리핑 생성 실패\n\n오류: {e}"
    
    async def run_daily_workflow(self) -> Dict[str, Any]:
        """
        일일 워크플로우 실행
        
        1. 일일 브리핑 생성
        2. 매크로 체크
        3. 종목 스크리닝
        4. 상위 후보 분석
        
        Returns:
            Dict with all results
        """
        logger.info("=== 일일 워크플로우 시작 ===")
        
        workflow_result = {
            "timestamp": datetime.now().isoformat(),
            "briefing": None,
            "macro_check": None,
            "candidates": [],
            "analyses": [],
        }
        
        # 1. 일일 브리핑
        logger.info("Step 1: 일일 브리핑 생성")
        workflow_result["briefing"] = await self.generate_daily_briefing()
        
        # 2. 매크로 체크
        logger.info("Step 2: 매크로 정합성 체크")
        workflow_result["macro_check"] = await self.check_macro_consistency()
        
        # 3. 종목 스크리닝
        logger.info("Step 3: 종목 스크리닝")
        candidates = await self.get_daily_candidates(force_scan=True)
        workflow_result["candidates"] = [
            self.screener.to_dict(c) for c in candidates[:10]
        ]
        
        # 4. 상위 5개 종목 분석
        logger.info("Step 4: 상위 종목 분석")
        for candidate in candidates[:5]:
            try:
                analysis = await self.analyze_enhanced(candidate.ticker)
                workflow_result["analyses"].append({
                    "ticker": candidate.ticker,
                    "screener_score": candidate.score,
                    "decision": analysis["decision"].action if analysis["decision"] else "ERROR",
                    "conviction": analysis["decision"].conviction if analysis["decision"] else 0,
                    "final_recommendation": analysis["final_recommendation"],
                    "skeptic_score": analysis.get("skeptic_analysis", {}).get("skeptic_score"),
                })
            except Exception as e:
                logger.error(f"{candidate.ticker} 분석 실패: {e}")
        
        logger.info("=== 일일 워크플로우 완료 ===")
        return workflow_result
    
    def get_v2_metrics(self) -> Dict[str, Any]:
        """V2 메트릭스 조회"""
        base_metrics = self.get_metrics()
        base_metrics["v2_metrics"] = self.v2_metrics.copy()
        return base_metrics
