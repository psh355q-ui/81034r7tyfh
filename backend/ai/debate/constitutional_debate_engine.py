"""
Constitutional AIDebateEngine Integration

AIDebateEngine과 Constitution을 통합하는 래퍼

모든 AI 제안이 헌법 검증을 거치도록 보장합니다.

작성일: 2025-12-15
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from backend.ai.debate.ai_debate_engine import AIDebateEngine, DebateResult
from backend.constitution import Constitution, SystemFreeze
from backend.backtest.shadow_trade_tracker import ShadowTradeTracker
from backend.schemas.base_schema import InvestmentSignal, MarketContext

logger = logging.getLogger(__name__)


class ConstitutionalDebateEngine:
    """
    Constitutional AI Debate Engine
    
    AIDebateEngine을 Constitution으로 감싼 래퍼
    
    모든 AI 제안이 헌법 검증을 거치며,
    위반 시 자동으로 거부하고 Shadow Trade를 생성합니다.
    
    Usage:
        engine = ConstitutionalDebateEngine(db_session)
        result = engine.debate_and_validate(
            news_item, market_context, portfolio_state
        )
    """
    
    def __init__(
        self,
        db_session=None,
        ai_debate_engine: Optional[AIDebateEngine] = None,
        constitution: Optional[Constitution] = None,
        shadow_tracker: Optional[ShadowTradeTracker] = None,
        strict_mode: bool = True
    ):
        """
        초기화
        
        Args:
            db_session: DB 세션 (Shadow Tracker용)
            ai_debate_engine: AI Debate Engine (None이면 생성)
            constitution: Constitution (None이면 생성)
            shadow_tracker: Shadow Trade Tracker (None이면 생성)
            strict_mode: 엄격 모드 (헌법 위반 시 예외 발생)
        """
        self.db_session = db_session
        self.strict_mode = strict_mode
        
        # AIDebateEngine
        self.debate_engine = ai_debate_engine or AIDebateEngine(
            enable_logging=True,
            enable_weight_training=True,
            enable_skeptic=True,
            enable_institutional=True
        )
        
        # Constitution
        self.constitution = constitution or Constitution()
        
        # Shadow Trade Tracker
        self.shadow_tracker = shadow_tracker
        if db_session and not shadow_tracker:
            from backend.data.collectors.api_clients.yahoo_client import YahooFinanceClient
            self.shadow_tracker = ShadowTradeTracker(
                db_session=db_session,
                yahoo_client=YahooFinanceClient()
            )
        
        logger.info("🏛️ Constitutional Debate Engine 초기화 완료")
        logger.info(f"   헌법 버전: {self.constitution.VERSION}")
        logger.info(f"   Strict Mode: {self.strict_mode}")
    
    def debate_and_validate(
        self,
        news_item: Dict[str, Any],
        market_context: MarketContext,
        portfolio_state: Optional[Dict[str, Any]] = None
    ) -> Tuple[DebateResult, bool, List[str]]:
        """
        AI 토론 + 헌법 검증
        
        Args:
            news_item: 뉴스 데이터
            market_context: 시장 컨텍스트
            portfolio_state: 포트폴리오 상태 (선택)
                {
                    'total_capital': float,
                    'current_allocation': dict,
                    'daily_trades': int,
                    ...
                }
        
        Returns:
            (debate_result, is_constitutional, violations)
        """
        # 1. AI 토론 실행
        logger.info(f"🎭 AI Debate 시작: {news_item.get('title', 'Unknown')[:50]}...")
        
        debate_result = self.debate_engine.debate_investment_decision(
            news_item=news_item,
            market_context=market_context
        )
        
        # 2. 헌법 검증
        logger.info("🏛️ 헌법 검증 시작...")
        
        is_constitutional, violations, violated_articles = self._validate_proposal(
            debate_result.final_signal,
            market_context,
            portfolio_state
        )
        
        # 3. 위반 처리
        if not is_constitutional:
            self._handle_violation(
                debate_result,
                violations,
                violated_articles,
                market_context
            )
        
        return debate_result, is_constitutional, violations
    
    def _validate_proposal(
        self,
        signal: InvestmentSignal,
        market_context: MarketContext,
        portfolio_state: Optional[Dict] = None
    ) -> Tuple[bool, List[str], List[str]]:
        """
        제안 헌법 검증
        
        Args:
            signal: AI 생성 시그널
            market_context: 시장 컨텍스트
            portfolio_state: 포트폴리오 상태
        
        Returns:
            (is_valid, violations, violated_articles)
        """
        # InvestmentSignal을 Proposal 형식으로 변환
        proposal = {
            'ticker': signal.ticker,
            'action': signal.action.value,
            'position_value': getattr(signal, 'position_value', 0),
            'order_value_usd': getattr(signal, 'order_value', 0),
            'is_approved': False  # 아직 승인 안 됨
        }
        
        # 컨텍스트 구성
        context = {
            'total_capital': portfolio_state.get('total_capital', 10000000) if portfolio_state else 10000000,
            'current_allocation': portfolio_state.get('current_allocation', {'stock': 0.5, 'cash': 0.5}) if portfolio_state else {'stock': 0.5, 'cash': 0.5},
            'market_regime': getattr(market_context, 'market_regime', 'neutral'),
            'daily_trades': portfolio_state.get('daily_trades', 0) if portfolio_state else 0,
            'weekly_trades': portfolio_state.get('weekly_trades', 0) if portfolio_state else 0,
            'daily_volume_usd': 10000000  # 기본값
        }
        
        # Circuit Breaker 체크
        if portfolio_state:
            daily_loss = portfolio_state.get('daily_loss', 0)
            total_dd = portfolio_state.get('total_drawdown', 0)
            vix = getattr(market_context, 'vix', 15)
            
            should_trigger, reason = self.constitution.validate_circuit_breaker_trigger(
                daily_loss, total_dd, vix
            )
            
            if should_trigger:
                logger.warning(f"🚨 Circuit Breaker 발동: {reason}")
                return False, [f"Circuit Breaker: {reason}"], ["제4조: 강제 개입"]
        
        # 헌법 검증
        is_valid, violations, violated_articles = self.constitution.validate_proposal(
            proposal, context
        )
        
        return is_valid, violations, violated_articles
    
    def _handle_violation(
        self,
        debate_result: DebateResult,
        violations: List[str],
        violated_articles: List[str],
        market_context: MarketContext
    ):
        """
        헌법 위반 처리
        
        Args:
            debate_result: 토론 결과
            violations: 위반 사항
            violated_articles: 위반된 조항
            market_context: 시장 컨텍스트
        """
        signal = debate_result.final_signal
        
        logger.warning(f"⚠️ 헌법 위반 감지: {signal.ticker} {signal.action.value}")
        
        for v in violations:
            logger.warning(f"   - {v}")
        
        for article in violated_articles:
            logger.warning(f"   📜 {article}")
        
        # Shadow Trade 생성 (DB 있을 때만)
        if self.shadow_tracker and self.db_session:
            try:
                proposal = {
                    'ticker': signal.ticker,
                    'action': signal.action.value,
                    'entry_price': signal.target_price,
                    'shares': 0  # 계산 필요
                }
                
                # 거부 사유
                rejection_reason = violations[0] if violations else "헌법 위반"
                
                shadow = self.shadow_tracker.create_shadow_trade(
                    proposal=proposal,
                    rejection_reason=rejection_reason,
                    violated_articles=violated_articles,
                    tracking_days=7
                )
                
                logger.info(f"🛡️ Shadow Trade 생성: {shadow.id}")
            
            except Exception as e:
                logger.error(f"Shadow Trade 생성 실패: {e}")
        
        # Strict Mode
        if self.strict_mode:
            summary = self.constitution.get_violated_articles_summary(violated_articles)
            raise SystemFreeze(
                f"헌법 위반으로 제안 거부:\n{summary}\n\n위반 사항:\n" +
                "\n".join(f"  - {v}" for v in violations)
            )
    
    def get_constitution_summary(self) -> str:
        """헌법 요약 조회"""
        return self.constitution.get_constitution_summary()
    
    def validate_system_health(
        self,
        portfolio_state: Dict[str, Any],
        market_context: MarketContext
    ) -> Tuple[bool, List[str]]:
        """
        시스템 건강성 검증
        
        Circuit Breaker 발동 여부 등 체크
        
        Args:
            portfolio_state: 포트폴리오 상태
            market_context: 시장 컨텍스트
        
        Returns:
            (is_healthy, warnings)
        """
        warnings = []
        
        # Circuit Breaker
        daily_loss = portfolio_state.get('daily_loss', 0)
        total_dd = portfolio_state.get('total_drawdown', 0)
        vix = getattr(market_context, 'vix', 15)
        
        should_trigger, reason = self.constitution.validate_circuit_breaker_trigger(
            daily_loss, total_dd, vix
        )
        
        if should_trigger:
            warnings.append(f"🚨 Circuit Breaker: {reason}")
        
        # 자본 보존율
        initial = portfolio_state.get('initial_capital', 10000000)
        current = portfolio_state.get('total_capital', initial)
        preservation_rate = (current / initial * 100) if initial > 0 else 100
        
        if preservation_rate < 95:
            warnings.append(f"⚠️ 자본 보존율 주의: {preservation_rate:.1f}%")
        
        # VIX 경고
        if vix >= self.constitution.risk.VIX_CAUTION_THRESHOLD:
            warnings.append(f"⚠️ VIX 주의: {vix}")
        
        is_healthy = len(warnings) == 0
        
        return is_healthy, warnings


if __name__ == "__main__":
    # 테스트
    print("=== Constitutional Debate Engine Test ===\n")
    
    print("이 모듈은 AIDebateEngine + Constitution 통합입니다.\n")
    
    print("주요 기능:")
    print("  1. AI 토론 실행")
    print("  2. 헌법 자동 검증")
    print("  3. 위반 시 Shadow Trade 생성")
    print("  4. Strict Mode에서는 즉시 차단")
    
    print("\n사용 예시:\n")
    print("""
    engine = ConstitutionalDebateEngine(
        db_session=db,
        strict_mode=True
    )
    
    result, is_constitutional, violations = engine.debate_and_validate(
        news_item=news,
        market_context=context,
        portfolio_state=portfolio
    )
    
    if is_constitutional:
        print("✅ 헌법 준수, 제안 승인 가능")
    else:
        print(f"❌ 헌법 위반: {violations}")
        # Shadow Trade 자동 생성됨
    """)
    
    print("\n✅ Constitutional Debate Engine 구현 완료!")
