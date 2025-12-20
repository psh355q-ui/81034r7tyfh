"""
Subscription Manager - 구독 모델 관리

Phase F6: 비용 최적화

Claude Pro, Gemini Pro 구독을 활용하여 API 비용을 0에 가깝게

핵심 전략:
- Claude Code CLI 활용 (배치 작업)
- Gemini Pro 무료 쿼터 (분당 15회)
- 모델 차익거래 (Model Arbitrage)
- Prompt Caching

작성일: 2025-12-08
참조: 10_Ideas_Integration_Plan_v3.md
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 스키마 정의
# ═══════════════════════════════════════════════════════════════

class SubscriptionType(str, Enum):
    """구독 유형"""
    CLAUDE_PRO = "claude_pro"       # $20/월
    GEMINI_PRO = "gemini_pro"       # $20/월
    OPENAI_PLUS = "openai_plus"     # $20/월
    FREE = "free"


class ModelProvider(str, Enum):
    """모델 제공자"""
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    LOCAL = "local"


class TaskType(str, Enum):
    """작업 유형"""
    FAST_ANALYSIS = "fast_analysis"      # 일반/고속 분석
    DEEP_REASONING = "deep_reasoning"    # 심층 추론
    CODING = "coding"                    # 코딩/문맥
    SECURE_FINANCE = "secure_finance"    # 보안/금융
    BATCH_PROCESSING = "batch_processing"  # 배치 처리
    FACT_CHECK = "fact_check"            # 팩트 체크


@dataclass
class SubscriptionStatus:
    """구독 상태"""
    subscription_type: SubscriptionType
    is_active: bool
    monthly_quota: Optional[int]  # 월간 쿼터 (메시지 수)
    used_today: int
    remaining_today: int
    rate_limit_per_minute: int
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.subscription_type.value,
            "is_active": self.is_active,
            "monthly_quota": self.monthly_quota,
            "used_today": self.used_today,
            "remaining_today": self.remaining_today,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class ModelOption:
    """모델 옵션"""
    model_id: str
    provider: ModelProvider
    cost_per_1m_input: float  # $/1M tokens
    cost_per_1m_output: float
    speed: float  # tokens/sec
    intelligence_score: float  # 0-100
    best_for: List[TaskType]
    requires_subscription: Optional[SubscriptionType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "provider": self.provider.value,
            "cost_per_1m": {
                "input": self.cost_per_1m_input,
                "output": self.cost_per_1m_output
            },
            "speed": self.speed,
            "intelligence_score": self.intelligence_score,
            "best_for": [t.value for t in self.best_for]
        }


@dataclass
class UsageRecord:
    """사용 기록"""
    model: str
    task_type: TaskType
    input_tokens: int
    output_tokens: int
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)
    via_subscription: bool = False


# ═══════════════════════════════════════════════════════════════
# Model Router - 최적 모델 선택
# ═══════════════════════════════════════════════════════════════

class ModelRouter:
    """
    모델 차익거래 라우터
    
    작업 유형에 따라 최적의 모델을 선택하여 비용 최적화
    """
    
    # 모델 카탈로그
    MODELS = {
        # Free/Low Cost Models
        "gemini-2.0-flash": ModelOption(
            model_id="gemini-2.0-flash",
            provider=ModelProvider.GOOGLE,
            cost_per_1m_input=0.075,
            cost_per_1m_output=0.30,
            speed=200,
            intelligence_score=85,
            best_for=[TaskType.FAST_ANALYSIS, TaskType.FACT_CHECK]
        ),
        "deepseek-r1": ModelOption(
            model_id="deepseek-r1",
            provider=ModelProvider.DEEPSEEK,
            cost_per_1m_input=0.55,
            cost_per_1m_output=2.19,
            speed=80,
            intelligence_score=92,
            best_for=[TaskType.DEEP_REASONING]
        ),
        "claude-3.5-sonnet": ModelOption(
            model_id="claude-3.5-sonnet",
            provider=ModelProvider.ANTHROPIC,
            cost_per_1m_input=3.0,
            cost_per_1m_output=15.0,
            speed=80,
            intelligence_score=95,
            best_for=[TaskType.CODING, TaskType.DEEP_REASONING],
            requires_subscription=SubscriptionType.CLAUDE_PRO
        ),
        "claude-pro-cli": ModelOption(
            model_id="claude-pro-cli",
            provider=ModelProvider.ANTHROPIC,
            cost_per_1m_input=0.0,  # 구독 포함
            cost_per_1m_output=0.0,
            speed=50,
            intelligence_score=95,
            best_for=[TaskType.BATCH_PROCESSING, TaskType.CODING],
            requires_subscription=SubscriptionType.CLAUDE_PRO
        ),
        "gemini-pro": ModelOption(
            model_id="gemini-pro",
            provider=ModelProvider.GOOGLE,
            cost_per_1m_input=0.0,  # Pro 구독 포함
            cost_per_1m_output=0.0,
            speed=100,
            intelligence_score=88,
            best_for=[TaskType.FAST_ANALYSIS, TaskType.FACT_CHECK],
            requires_subscription=SubscriptionType.GEMINI_PRO
        ),
        "gpt-4o": ModelOption(
            model_id="gpt-4o",
            provider=ModelProvider.OPENAI,
            cost_per_1m_input=2.5,
            cost_per_1m_output=10.0,
            speed=100,
            intelligence_score=93,
            best_for=[TaskType.SECURE_FINANCE]
        ),
        "gpt-4o-mini": ModelOption(
            model_id="gpt-4o-mini",
            provider=ModelProvider.OPENAI,
            cost_per_1m_input=0.15,
            cost_per_1m_output=0.60,
            speed=150,
            intelligence_score=82,
            best_for=[TaskType.FAST_ANALYSIS]
        ),
    }
    
    # 작업별 우선순위
    TASK_PRIORITY = {
        TaskType.FAST_ANALYSIS: ["gemini-2.0-flash", "gemini-pro", "gpt-4o-mini"],
        TaskType.DEEP_REASONING: ["deepseek-r1", "claude-pro-cli", "claude-3.5-sonnet"],
        TaskType.CODING: ["claude-pro-cli", "claude-3.5-sonnet", "deepseek-r1"],
        TaskType.SECURE_FINANCE: ["gpt-4o", "claude-3.5-sonnet"],
        TaskType.BATCH_PROCESSING: ["claude-pro-cli", "gemini-pro", "deepseek-r1"],
        TaskType.FACT_CHECK: ["gemini-pro", "gemini-2.0-flash"],
    }
    
    def __init__(self, subscription_manager: 'SubscriptionManager'):
        self.subscription_manager = subscription_manager
    
    def select_model(
        self,
        task_type: TaskType,
        prefer_free: bool = True,
        min_intelligence: float = 0
    ) -> ModelOption:
        """
        작업에 최적인 모델 선택
        
        Args:
            task_type: 작업 유형
            prefer_free: 무료/구독 모델 우선
            min_intelligence: 최소 지능 점수
            
        Returns:
            선택된 모델
        """
        priority_list = self.TASK_PRIORITY.get(task_type, list(self.MODELS.keys()))
        
        for model_id in priority_list:
            model = self.MODELS.get(model_id)
            if not model:
                continue
            
            # 지능 점수 확인
            if model.intelligence_score < min_intelligence:
                continue
            
            # 구독 필요한 모델인 경우 구독 상태 확인
            if model.requires_subscription:
                status = self.subscription_manager.get_status(model.requires_subscription)
                if not status or not status.is_active:
                    continue
                if status.remaining_today <= 0:
                    continue
            
            # 무료 우선 모드에서 유료 모델 스킵
            if prefer_free and model.cost_per_1m_input > 0:
                if not model.requires_subscription:
                    continue
            
            return model
        
        # Fallback: 가장 저렴한 모델
        return self.MODELS["gpt-4o-mini"]
    
    def estimate_cost(
        self,
        model: ModelOption,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """비용 추정"""
        if model.requires_subscription:
            status = self.subscription_manager.get_status(model.requires_subscription)
            if status and status.is_active:
                return 0.0
        
        input_cost = (input_tokens / 1_000_000) * model.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * model.cost_per_1m_output
        return input_cost + output_cost


# ═══════════════════════════════════════════════════════════════
# Subscription Manager
# ═══════════════════════════════════════════════════════════════

class SubscriptionManager:
    """
    구독 관리자
    
    Usage:
        manager = SubscriptionManager()
        
        # 구독 활성화
        manager.activate(SubscriptionType.CLAUDE_PRO)
        manager.activate(SubscriptionType.GEMINI_PRO)
        
        # 최적 모델 선택
        router = manager.get_router()
        model = router.select_model(TaskType.DEEP_REASONING)
        
        # 사용 기록
        manager.record_usage(model, TaskType.DEEP_REASONING, 1000, 500)
    """
    
    # 구독별 기본 쿼터
    DEFAULT_QUOTAS = {
        SubscriptionType.CLAUDE_PRO: {
            "daily_messages": 100,  # Claude Pro 추정 (변동 가능)
            "rate_per_minute": 15
        },
        SubscriptionType.GEMINI_PRO: {
            "daily_messages": 1500,  # Gemini Pro
            "rate_per_minute": 15
        },
        SubscriptionType.OPENAI_PLUS: {
            "daily_messages": 80,
            "rate_per_minute": 50
        }
    }
    
    def __init__(self, data_dir: Optional[Path] = None):
        """초기화"""
        self.data_dir = data_dir or Path("data/subscriptions")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._subscriptions: Dict[SubscriptionType, SubscriptionStatus] = {}
        self._usage_history: List[UsageRecord] = []
        self._daily_usage: Dict[SubscriptionType, int] = {}
        
        # 기본 구독 로드
        self._load_subscriptions()
        
        logger.info("SubscriptionManager initialized")
    
    def _load_subscriptions(self):
        """구독 정보 로드"""
        # 기본 설정: Claude Pro, Gemini Pro 활성화
        self._subscriptions[SubscriptionType.CLAUDE_PRO] = SubscriptionStatus(
            subscription_type=SubscriptionType.CLAUDE_PRO,
            is_active=True,
            monthly_quota=None,  # 무제한 (일일 제한 있음)
            used_today=0,
            remaining_today=self.DEFAULT_QUOTAS[SubscriptionType.CLAUDE_PRO]["daily_messages"],
            rate_limit_per_minute=15
        )
        
        self._subscriptions[SubscriptionType.GEMINI_PRO] = SubscriptionStatus(
            subscription_type=SubscriptionType.GEMINI_PRO,
            is_active=True,
            monthly_quota=None,
            used_today=0,
            remaining_today=self.DEFAULT_QUOTAS[SubscriptionType.GEMINI_PRO]["daily_messages"],
            rate_limit_per_minute=15
        )
    
    def activate(
        self,
        subscription_type: SubscriptionType,
        expires_at: Optional[datetime] = None
    ):
        """구독 활성화"""
        quota_info = self.DEFAULT_QUOTAS.get(subscription_type, {})
        
        self._subscriptions[subscription_type] = SubscriptionStatus(
            subscription_type=subscription_type,
            is_active=True,
            monthly_quota=None,
            used_today=0,
            remaining_today=quota_info.get("daily_messages", 100),
            rate_limit_per_minute=quota_info.get("rate_per_minute", 10),
            expires_at=expires_at
        )
        
        logger.info(f"Activated subscription: {subscription_type.value}")
    
    def deactivate(self, subscription_type: SubscriptionType):
        """구독 비활성화"""
        if subscription_type in self._subscriptions:
            self._subscriptions[subscription_type].is_active = False
            logger.info(f"Deactivated subscription: {subscription_type.value}")
    
    def get_status(self, subscription_type: SubscriptionType) -> Optional[SubscriptionStatus]:
        """구독 상태 조회"""
        return self._subscriptions.get(subscription_type)
    
    def get_all_statuses(self) -> Dict[str, SubscriptionStatus]:
        """모든 구독 상태"""
        return {s.value: status for s, status in self._subscriptions.items()}
    
    def record_usage(
        self,
        model: ModelOption,
        task_type: TaskType,
        input_tokens: int,
        output_tokens: int
    ):
        """사용 기록"""
        # 구독 쿼터 차감
        via_subscription = False
        if model.requires_subscription:
            sub = model.requires_subscription
            if sub in self._subscriptions:
                self._subscriptions[sub].used_today += 1
                self._subscriptions[sub].remaining_today -= 1
                via_subscription = True
        
        # 비용 계산
        cost = 0.0
        if not via_subscription:
            cost = (input_tokens / 1_000_000) * model.cost_per_1m_input
            cost += (output_tokens / 1_000_000) * model.cost_per_1m_output
        
        # 기록 저장
        record = UsageRecord(
            model=model.model_id,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            via_subscription=via_subscription
        )
        self._usage_history.append(record)
        
        logger.debug(f"Recorded usage: {model.model_id}, cost=${cost:.4f}")
    
    def get_daily_cost(self) -> float:
        """일일 비용 조회"""
        today = date.today()
        return sum(
            r.cost for r in self._usage_history
            if r.timestamp.date() == today
        )
    
    def get_monthly_cost(self) -> float:
        """월간 비용 조회"""
        this_month = date.today().replace(day=1)
        return sum(
            r.cost for r in self._usage_history
            if r.timestamp.date() >= this_month
        )
    
    def get_saved_cost(self) -> float:
        """절감된 비용 (구독으로 처리된 건)"""
        return sum(
            self._estimate_if_paid(r)
            for r in self._usage_history
            if r.via_subscription
        )
    
    def _estimate_if_paid(self, record: UsageRecord) -> float:
        """API로 했다면의 예상 비용"""
        # Claude 3.5 Sonnet 가격 기준
        return (record.input_tokens / 1_000_000) * 3.0 + (record.output_tokens / 1_000_000) * 15.0
    
    def get_router(self) -> ModelRouter:
        """ModelRouter 인스턴스"""
        return ModelRouter(self)
    
    def reset_daily_usage(self):
        """일일 사용량 리셋 (매일 자정 호출)"""
        for sub_type, status in self._subscriptions.items():
            quota_info = self.DEFAULT_QUOTAS.get(sub_type, {})
            status.used_today = 0
            status.remaining_today = quota_info.get("daily_messages", 100)
        
        logger.info("Daily usage reset")
    
    def get_summary(self) -> Dict[str, Any]:
        """요약"""
        return {
            "active_subscriptions": [
                s.value for s, status in self._subscriptions.items()
                if status.is_active
            ],
            "daily_cost": self.get_daily_cost(),
            "monthly_cost": self.get_monthly_cost(),
            "saved_cost": self.get_saved_cost(),
            "today_usage": {
                s.value: status.used_today
                for s, status in self._subscriptions.items()
            }
        }


# ═══════════════════════════════════════════════════════════════
# Global Singleton
# ═══════════════════════════════════════════════════════════════

_subscription_manager: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    """SubscriptionManager 싱글톤 인스턴스"""
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = SubscriptionManager()
    return _subscription_manager


# ═══════════════════════════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    manager = SubscriptionManager()
    router = manager.get_router()
    
    print("=== Subscription Manager Test ===\n")
    
    # 구독 상태 확인
    print("Active Subscriptions:")
    for sub_type, status in manager.get_all_statuses().items():
        if status.is_active:
            print(f"  ✅ {sub_type}: {status.remaining_today} remaining today")
    
    # 작업별 최적 모델 선택
    print("\n모델 선택 테스트:")
    test_tasks = [
        TaskType.FAST_ANALYSIS,
        TaskType.DEEP_REASONING,
        TaskType.CODING,
        TaskType.BATCH_PROCESSING
    ]
    
    for task in test_tasks:
        model = router.select_model(task, prefer_free=True)
        cost = router.estimate_cost(model, 1000, 500)
        sub_tag = "(구독)" if model.requires_subscription else ""
        print(f"  {task.value}: {model.model_id} {sub_tag}")
        print(f"    비용: ${cost:.4f}/1.5K tokens, 지능: {model.intelligence_score}")
    
    # 사용 기록 시뮬레이션
    print("\n사용 시뮬레이션:")
    for task in test_tasks:
        model = router.select_model(task)
        manager.record_usage(model, task, 1000, 500)
    
    summary = manager.get_summary()
    print(f"  일일 비용: ${summary['daily_cost']:.4f}")
    print(f"  절감 비용: ${summary['saved_cost']:.4f}")
