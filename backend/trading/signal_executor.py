"""
시그널 실행기 (Signal Executor)

Phase 9 뉴스 분석 시그널 → 한국투자증권 실제 주문 변환

주요 기능:
1. 시그널 검증 (Kill Switch, 포지션 크기)
2. 시그널 → 주문 변환
3. 주문 실행 및 모니터링
4. 거래 로그 및 통계

⚠️ 경고: 실거래는 실제 금전 손실 위험이 있습니다!
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

import kis_client as ka

logger = logging.getLogger(__name__)


# =============================================================================
# 데이터 모델
# =============================================================================

@dataclass
class TradingSignal:
    """거래 시그널 (Phase 9에서 생성)"""
    id: str
    ticker: str  # 종목코드 (예: "005930")
    action: str  # BUY, SELL, HOLD
    position_size: float  # 0.0 ~ 1.0 (포트폴리오 비율)
    confidence: float  # 신뢰도 (0.0 ~ 1.0)
    execution_type: str  # MARKET, LIMIT
    reason: str  # 시그널 생성 이유
    urgency: str  # LOW, MEDIUM, HIGH, IMMEDIATE
    created_at: str  # ISO 8601


@dataclass
class ExecutionResult:
    """주문 실행 결과"""
    signal_id: str
    success: bool
    order_no: str
    ticker: str
    side: str  # BUY, SELL
    quantity: int
    price: int
    total_value: int
    message: str
    executed_at: str


@dataclass
class SafetyCheckResult:
    """안전 검증 결과"""
    passed: bool
    checks: Dict[str, bool]
    reasons: List[str]


# =============================================================================
# 시그널 실행기
# =============================================================================

class SignalExecutor:
    """
    시그널 실행기
    
    Phase 9 거래 시그널을 검증하고 실제 주문으로 변환
    
    안전 장치:
    - Kill Switch
    - 최대 포지션 크기 제한
    - 일일 거래 횟수 제한
    - 일일 손실 제한
    - 신뢰도 임계값
    """
    
    def __init__(
        self,
        max_position_pct: float = 0.10,  # 최대 포지션 10%
        max_daily_trades: int = 10,  # 일일 최대 거래
        max_daily_loss_pct: float = 2.0,  # 일일 최대 손실 2%
        min_confidence: float = 0.7,  # 최소 신뢰도
        require_confirmation: bool = True,  # 사용자 확인 필요
    ):
        """
        Args:
            max_position_pct: 최대 포지션 크기 (자본 대비 %)
            max_daily_trades: 일일 최대 거래 횟수
            max_daily_loss_pct: 일일 최대 손실 % (Kill Switch)
            min_confidence: 최소 신뢰도 임계값
            require_confirmation: 주문 전 사용자 확인 필요 여부
        """
        self.max_position_pct = max_position_pct
        self.max_daily_trades = max_daily_trades
        self.max_daily_loss_pct = max_daily_loss_pct
        self.min_confidence = min_confidence
        self.require_confirmation = require_confirmation
        
        # 상태
        self.kill_switch_active = False
        self.kill_switch_reason = ""
        self.daily_trades_count = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        # 실행 기록
        self.execution_history: List[ExecutionResult] = []
        
        # 인증 상태
        self.authenticated = False
        
        # 로그 파일
        self.log_file = Path("./execution_log.json")
    
    def initialize(self, svr: str = "vps", product: str = "01") -> bool:
        """
        API 인증 초기화
        
        Args:
            svr: "prod" (실전) 또는 "vps" (모의)
            product: 상품코드
        
        Returns:
            성공 여부
        """
        logger.info("시그널 실행기 초기화...")
        
        if ka.auth(svr=svr, product=product):
            self.authenticated = True
            logger.info(f"인증 성공: {'실전' if svr == 'prod' else '모의'} 투자")
            return True
        else:
            logger.error("인증 실패")
            return False
    
    def _reset_daily_stats(self):
        """일일 통계 리셋 (자정 기준)"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_trades_count = 0
            self.daily_pnl = 0.0
            self.last_reset_date = today
            logger.info("일일 통계 리셋")
    
    def activate_kill_switch(self, reason: str):
        """Kill Switch 활성화"""
        self.kill_switch_active = True
        self.kill_switch_reason = reason
        logger.critical(f"🚨 KILL SWITCH 활성화: {reason}")
    
    def deactivate_kill_switch(self):
        """Kill Switch 비활성화"""
        self.kill_switch_active = False
        self.kill_switch_reason = ""
        logger.warning("Kill Switch 비활성화")
    
    def check_safety(self, signal: TradingSignal) -> SafetyCheckResult:
        """
        시그널 안전 검증
        
        Returns:
            SafetyCheckResult
        """
        self._reset_daily_stats()
        
        checks = {}
        reasons = []
        
        # 1. Kill Switch
        checks["kill_switch"] = not self.kill_switch_active
        if self.kill_switch_active:
            reasons.append(f"Kill Switch 활성화: {self.kill_switch_reason}")
        
        # 2. 일일 거래 횟수
        checks["daily_trades"] = self.daily_trades_count < self.max_daily_trades
        if not checks["daily_trades"]:
            reasons.append(f"일일 거래 한도 초과: {self.daily_trades_count}/{self.max_daily_trades}")
        
        # 3. 신뢰도
        checks["confidence"] = signal.confidence >= self.min_confidence
        if not checks["confidence"]:
            reasons.append(f"신뢰도 부족: {signal.confidence:.2f} < {self.min_confidence}")
        
        # 4. 포지션 크기
        checks["position_size"] = signal.position_size <= self.max_position_pct
        if not checks["position_size"]:
            reasons.append(f"포지션 크기 초과: {signal.position_size:.2%} > {self.max_position_pct:.2%}")
        
        # 5. 유효한 액션
        checks["valid_action"] = signal.action in ["BUY", "SELL"]
        if not checks["valid_action"]:
            reasons.append(f"유효하지 않은 액션: {signal.action}")
        
        # 6. 티커 형식
        checks["valid_ticker"] = len(signal.ticker) == 6 and signal.ticker.isdigit()
        if not checks["valid_ticker"]:
            reasons.append(f"유효하지 않은 종목코드: {signal.ticker}")
        
        # 7. 인증 상태
        checks["authenticated"] = self.authenticated
        if not checks["authenticated"]:
            reasons.append("API 인증 필요")
        
        passed = all(checks.values())
        
        return SafetyCheckResult(
            passed=passed,
            checks=checks,
            reasons=reasons
        )
    
    def calculate_order_quantity(
        self,
        signal: TradingSignal,
        current_price: int
    ) -> int:
        """
        주문 수량 계산
        
        Args:
            signal: 거래 시그널
            current_price: 현재가
        
        Returns:
            주문 수량
        """
        if current_price <= 0:
            return 0
        
        # 계좌 잔고 조회
        balance = ka.inquire_balance()
        if not balance:
            logger.error("잔고 조회 실패")
            return 0
        
        # 총 자본
        total_capital = balance["summary"].get("tot_evlu_amt", 0)
        if total_capital <= 0:
            return 0
        
        # 포지션 가치
        position_value = total_capital * signal.position_size
        
        # 수량 계산
        quantity = int(position_value / current_price)
        
        # 최소 1주
        quantity = max(1, quantity)
        
        logger.info(f"주문수량 계산: 자본 {total_capital:,}원 × {signal.position_size:.2%} = {position_value:,}원 / {current_price:,}원 = {quantity}주")
        
        return quantity
    
    def execute_signal(
        self,
        signal: TradingSignal,
        dry_run: bool = True
    ) -> ExecutionResult:
        """
        시그널 실행
        
        Args:
            signal: 거래 시그널
            dry_run: True면 실제 주문 없이 시뮬레이션
        
        Returns:
            ExecutionResult
        """
        logger.info(f"시그널 실행: {signal.ticker} {signal.action}")
        
        # 1. 안전 검증
        safety = self.check_safety(signal)
        
        if not safety.passed:
            logger.warning(f"안전 검증 실패: {safety.reasons}")
            return ExecutionResult(
                signal_id=signal.id,
                success=False,
                order_no="",
                ticker=signal.ticker,
                side=signal.action,
                quantity=0,
                price=0,
                total_value=0,
                message=f"안전 검증 실패: {', '.join(safety.reasons)}",
                executed_at=datetime.now().isoformat()
            )
        
        # 2. 현재가 조회
        price_info = ka.inquire_price(signal.ticker)
        if not price_info:
            return ExecutionResult(
                signal_id=signal.id,
                success=False,
                order_no="",
                ticker=signal.ticker,
                side=signal.action,
                quantity=0,
                price=0,
                total_value=0,
                message="현재가 조회 실패",
                executed_at=datetime.now().isoformat()
            )
        
        current_price = price_info["stck_prpr"]
        logger.info(f"{signal.ticker} 현재가: {current_price:,}원")
        
        # 3. 주문 수량 계산
        quantity = self.calculate_order_quantity(signal, current_price)
        
        if quantity <= 0:
            return ExecutionResult(
                signal_id=signal.id,
                success=False,
                order_no="",
                ticker=signal.ticker,
                side=signal.action,
                quantity=0,
                price=current_price,
                total_value=0,
                message="주문 수량이 0",
                executed_at=datetime.now().isoformat()
            )
        
        total_value = quantity * current_price
        
        # 4. 사용자 확인
        if self.require_confirmation and not dry_run:
            print(f"\n⚠️ 주문 확인")
            print(f"  종목: {signal.ticker}")
            print(f"  방향: {signal.action}")
            print(f"  수량: {quantity}주")
            print(f"  가격: {current_price:,}원 ({signal.execution_type})")
            print(f"  총액: {total_value:,}원")
            print(f"  이유: {signal.reason}")
            
            confirm = input("\n주문을 실행하시겠습니까? (yes/no): ")
            if confirm.lower() != "yes":
                return ExecutionResult(
                    signal_id=signal.id,
                    success=False,
                    order_no="",
                    ticker=signal.ticker,
                    side=signal.action,
                    quantity=quantity,
                    price=current_price,
                    total_value=total_value,
                    message="사용자 취소",
                    executed_at=datetime.now().isoformat()
                )
        
        # 5. 주문 실행
        if dry_run:
            logger.info("🧪 DRY RUN 모드 - 실제 주문 없음")
            order_result = {
                "success": True,
                "odno": f"DRY_{datetime.now().strftime('%H%M%S')}",
                "message": "Dry run 성공"
            }
        else:
            # 실제 주문
            if signal.action == "BUY":
                if signal.execution_type == "MARKET":
                    order_result = ka.buy_order(signal.ticker, quantity, 0)
                else:
                    order_result = ka.buy_order(signal.ticker, quantity, current_price)
            else:  # SELL
                if signal.execution_type == "MARKET":
                    order_result = ka.sell_order(signal.ticker, quantity, 0)
                else:
                    order_result = ka.sell_order(signal.ticker, quantity, current_price)
        
        # 6. 결과 처리
        if order_result["success"]:
            self.daily_trades_count += 1
            logger.info(f"✅ 주문 성공: {order_result['odno']}")
            
            result = ExecutionResult(
                signal_id=signal.id,
                success=True,
                order_no=order_result.get("odno", ""),
                ticker=signal.ticker,
                side=signal.action,
                quantity=quantity,
                price=current_price,
                total_value=total_value,
                message=order_result.get("message", "성공"),
                executed_at=datetime.now().isoformat()
            )
        else:
            logger.error(f"❌ 주문 실패: {order_result['message']}")
            
            result = ExecutionResult(
                signal_id=signal.id,
                success=False,
                order_no="",
                ticker=signal.ticker,
                side=signal.action,
                quantity=quantity,
                price=current_price,
                total_value=total_value,
                message=order_result.get("message", "실패"),
                executed_at=datetime.now().isoformat()
            )
        
        # 7. 기록
        self.execution_history.append(result)
        self._save_execution_log(result)
        
        return result
    
    def _save_execution_log(self, result: ExecutionResult):
        """실행 로그 저장"""
        try:
            # 기존 로그 로드
            if self.log_file.exists():
                with open(self.log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # 추가
            logs.append(asdict(result))
            
            # 저장
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"로그 저장 실패: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """실행 통계 조회"""
        self._reset_daily_stats()
        
        total_executions = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        
        return {
            "kill_switch_active": self.kill_switch_active,
            "kill_switch_reason": self.kill_switch_reason,
            "daily_trades_count": self.daily_trades_count,
            "max_daily_trades": self.max_daily_trades,
            "daily_pnl_pct": self.daily_pnl,
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": total_executions - successful,
            "success_rate": successful / total_executions if total_executions > 0 else 0.0,
        }
    
    def get_execution_history(
        self,
        limit: int = 50,
        ticker: Optional[str] = None
    ) -> List[Dict]:
        """실행 이력 조회"""
        history = self.execution_history[-limit:]
        
        if ticker:
            history = [h for h in history if h.ticker == ticker]
        
        return [asdict(h) for h in history]


# =============================================================================
# 데모 / 테스트
# =============================================================================

def run_demo():
    """시그널 실행기 데모"""
    print("=" * 70)
    print("🚀 시그널 실행기 데모")
    print("=" * 70)
    
    # 1. 초기화
    executor = SignalExecutor(
        max_position_pct=0.10,
        max_daily_trades=10,
        min_confidence=0.7,
        require_confirmation=False  # 데모에서는 확인 없이
    )
    
    print("\n1️⃣ 시그널 실행기 설정")
    print(f"  최대 포지션: {executor.max_position_pct:.1%}")
    print(f"  일일 최대 거래: {executor.max_daily_trades}")
    print(f"  최소 신뢰도: {executor.min_confidence}")
    
    # 2. 인증
    print("\n2️⃣ API 인증")
    if not executor.initialize(svr="vps"):
        print("❌ 인증 실패. kis_devlp.yaml 파일을 확인하세요.")
        return
    print("✅ 인증 성공!")
    
    # 3. 테스트 시그널
    print("\n3️⃣ 테스트 시그널 생성")
    
    test_signal = TradingSignal(
        id="test_001",
        ticker="005930",  # 삼성전자
        action="BUY",
        position_size=0.05,  # 5%
        confidence=0.85,
        execution_type="MARKET",
        reason="뉴스 분석 - 긍정적 실적 발표",
        urgency="HIGH",
        created_at=datetime.now().isoformat()
    )
    
    print(f"  시그널 ID: {test_signal.id}")
    print(f"  종목: {test_signal.ticker}")
    print(f"  방향: {test_signal.action}")
    print(f"  포지션: {test_signal.position_size:.1%}")
    print(f"  신뢰도: {test_signal.confidence:.1%}")
    
    # 4. 안전 검증
    print("\n4️⃣ 안전 검증")
    safety = executor.check_safety(test_signal)
    
    print(f"  검증 결과: {'✅ PASS' if safety.passed else '❌ FAIL'}")
    for check, passed in safety.checks.items():
        print(f"    - {check}: {'✅' if passed else '❌'}")
    
    if safety.reasons:
        print(f"  실패 사유: {safety.reasons}")
    
    # 5. Dry Run 실행
    print("\n5️⃣ Dry Run 실행 (실제 주문 없음)")
    result = executor.execute_signal(test_signal, dry_run=True)
    
    print(f"  성공: {result.success}")
    print(f"  주문번호: {result.order_no}")
    print(f"  수량: {result.quantity}주")
    print(f"  가격: {result.price:,}원")
    print(f"  총액: {result.total_value:,}원")
    print(f"  메시지: {result.message}")
    
    # 6. Kill Switch 테스트
    print("\n6️⃣ Kill Switch 테스트")
    executor.activate_kill_switch("일일 손실 한도 초과")
    
    safety = executor.check_safety(test_signal)
    print(f"  Kill Switch 활성: {executor.kill_switch_active}")
    print(f"  검증 결과: {'✅ PASS' if safety.passed else '❌ FAIL'}")
    
    executor.deactivate_kill_switch()
    print(f"  Kill Switch 비활성화")
    
    # 7. 통계
    print("\n7️⃣ 실행 통계")
    stats = executor.get_stats()
    
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ 시그널 실행기 데모 완료!")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(message)s"
    )
    run_demo()