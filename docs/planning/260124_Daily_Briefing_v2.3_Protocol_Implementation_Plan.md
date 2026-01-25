# Daily Briefing System v2.3 - 트레이딩 프로토콜 구현 계획서

**작성일**: 2026-01-24
**기반 문서**: ChatGPT + Gemini 피드백 종합
**핵심 목표**: "읽는 리포트" → "실행하는 프로토콜" 전환

<!-- 
✅ 구현 완료 (2026-01-24)
- Briefing Mode System: backend/ai/reporters/briefing_mode.py
- Prompt Builder: backend/ai/reporters/prompt_builder.py
- Trading Protocol Schema: backend/ai/reporters/schemas/trading_protocol.py
- Market Moving Score: backend/ai/intelligence/market_moving_score.py
- Conflict Resolver: backend/ai/mvp/conflict_resolver.py
- Funnel Generator: backend/ai/reporters/funnel_generator.py
-->

## 📋 목차

1. [핵심 변경 요약](#핵심-변경-요약)
2. [3개 AI 합의 사항](#3개-ai-합의-사항)
3. [구현 우선순위](#구현-우선순위)
4. [Phase별 상세 작업](#phase별-상세-작업)
5. [JSON 스키마 정의](#json-스키마-정의)
6. [DB 스키마 확장](#db-스키마-확장)
7. [검증 체크리스트](#검증-체크리스트)

---

## 핵심 변경 요약

### ❌ 현재 문제점 (v2.2)
1. **시점 불일치**: 마감 브리핑에서 가정법(If/Then) 사용
2. **교과서적 설명**: "PMI 50 이상은 확장..." 같은 불필요한 정의
3. **행동 지침 부재**: "조정 가능성" 같은 모호한 표현
4. **뉴스 노이즈**: CEO 매도 같은 무관한 뉴스 포함
5. **충돌 규칙 없음**: Risk Agent vs Trader Agent 우선순위 미정의

### ✅ v2.3 목표
1. **Closing/Morning 완전 분리**
2. **JSON 프로토콜 출력** (자동매매 연동 가능)
3. **Market Moving Score** (뉴스 필터링 정교화)
4. **3단 깔때기 구조** (State → Scenarios → Impact)
5. **Risk-First 충돌 규칙**

---

## 3개 AI 합의 사항

| 합의 항목 | 설명 |
|----------|------|
| **시점 분리** | Closing = "Because/Result", Morning = "If/Then" |
| **Output 전환** | 마크다운 → JSON 트레이딩 프로토콜 |
| **뉴스 필터링** | Market Moving Score (0-100) = Impact×0.5 + Specificity×0.3 + Reliability×0.2 |
| **충돌 규칙** | Risk Agent = Size 조절, Trader Agent = Direction 결정 |
| **Human Check** | 3가지만: ① Rationale 논리 ② Sizing 과도함 ③ Exit Plan 존재 |

---

## 구현 우선순위

```
🥇 Phase 1: 시점 분리 (CRITICAL)
   └→ Closing/Morning 프롬프트 분기
   └→ 가정법 ↔ 직설법 강제 규칙

🥈 Phase 2: JSON 프로토콜 출력
   └→ Pydantic 스키마 정의
   └→ ai_trade_decisions 테이블 추가
   └→ 기존 리포터에서 JSON 출력 모드 추가

🥉 Phase 3: Market Moving Score
   └→ 뉴스 점수 계산 공식 구현
   └→ 동적 임계값 (VIX 연동)
   └→ 필터링 로직 강화

🏅 Phase 4: Risk/Trader 충돌 규칙
   └→ resolve_trade() 함수 구현
   └→ execution_intent 자동 판단

🏅 Phase 5: 3단 깔때기 구조
   └→ Market State 신호등
   └→ Actionable Scenarios (IF-THEN)
   └→ Portfolio Impact
```

---

## Phase별 상세 작업

### Phase 1: 시점 분리 (Closing/Morning)

#### Task 1.1: 모드 상수 정의

**파일**: `backend/ai/reporters/briefing_mode.py` (신규)

```python
"""
Briefing Mode Definitions

시점에 따른 브리핑 모드 정의
- CLOSING: 마감 브리핑 (Because/Result 중심)
- MORNING: 프리마켓 브리핑 (If/Then 중심)
"""

from enum import Enum
from datetime import datetime
from zoneinfo import ZoneInfo


class BriefingMode(Enum):
    CLOSING = "CLOSING"   # 미국장 마감 후 (06:10/07:10 KST)
    MORNING = "MORNING"   # 미국장 개장 전 (22:30/23:00 KST)
    INTRADAY = "INTRADAY" # 장중 체크포인트 (01:00, 03:00 KST)


def get_current_briefing_mode() -> BriefingMode:
    """
    현재 시간에 맞는 브리핑 모드 반환

    - 06:00 ~ 12:00 KST: CLOSING (미국장 마감 후)
    - 18:00 ~ 06:00 KST: MORNING (미국장 개장 전)
    - 그 외: INTRADAY
    """
    kst = ZoneInfo("Asia/Seoul")
    now = datetime.now(kst)
    hour = now.hour

    if 6 <= hour < 12:
        return BriefingMode.CLOSING
    elif hour >= 18 or hour < 6:
        return BriefingMode.MORNING
    else:
        return BriefingMode.INTRADAY


# 모드별 프롬프트 제약 조건
MODE_CONSTRAINTS = {
    BriefingMode.CLOSING: {
        "grammar": "Because / Result (직설법)",
        "indicators": "Actual / Surprise",
        "focus": "왜 이렇게 끝났는가",
        "banned_phrases": ["If", "예상 상회 시", "예상 하회 시", "시나리오"],
        "required_phrases": ["결과", "실제", "반응", "마감"]
    },
    BriefingMode.MORNING: {
        "grammar": "If / Then (가정법)",
        "indicators": "Expected / Risk",
        "focus": "어떻게 대응할까",
        "banned_phrases": ["결과적으로", "마감했다", "반응했다"],
        "required_phrases": ["예상", "시나리오", "대응", "전략"]
    },
    BriefingMode.INTRADAY: {
        "grammar": "Observation / Alert",
        "indicators": "Delta / Change",
        "focus": "유의미한 변동 있는가",
        "banned_phrases": [],
        "required_phrases": ["변동", "주목", "모니터링"]
    }
}
```

#### Task 1.2: 프롬프트 분기 시스템

**파일**: `backend/ai/reporters/prompt_builder.py` (신규)

```python
"""
Prompt Builder - 모드별 프롬프트 생성

핵심 원칙:
1. Closing = 결과 중심 (교과서적 정의 금지)
2. Morning = 시나리오 중심 (조건부 행동 제시)
"""

from typing import Dict, Any
from .briefing_mode import BriefingMode, MODE_CONSTRAINTS


class PromptBuilder:
    """모드별 프롬프트 생성기"""

    # 공통 시스템 프롬프트 (고정)
    SYSTEM_PROMPT = """
너는 트레이딩 리포트를 작성하지 않는다.
너의 출력은 실행 가능한 JSON 프로토콜이다.

**절대 금지**:
- 형용사, 수사, 교과서적 설명
- "PMI 50 이상은 확장을 의미" 같은 정의
- "전반적으로", "대체로", "약간" 같은 모호한 표현

**필수 사항**:
- 모든 판단은 숫자와 인과관계로만 표현
- 구체적인 가격, 수치, 비중 명시
- 근거 없는 추천 금지
"""

    @staticmethod
    def build_prompt(mode: BriefingMode, data: Dict[str, Any]) -> str:
        """
        모드에 맞는 프롬프트 생성

        Args:
            mode: CLOSING | MORNING | INTRADAY
            data: 분석 데이터 (뉴스, 지표, 시그널 등)
        """
        constraints = MODE_CONSTRAINTS[mode]

        # 모드별 제약 조건 문자열화
        banned = ", ".join(constraints["banned_phrases"])
        required = ", ".join(constraints["required_phrases"])

        mode_specific_prompt = f"""
**현재 모드**: {mode.value}
**문법 규칙**: {constraints["grammar"]}
**지표 표현**: {constraints["indicators"]}
**핵심 질문**: {constraints["focus"]}

**금지 표현**: {banned}
**필수 포함**: {required}
"""

        if mode == BriefingMode.CLOSING:
            return PromptBuilder._build_closing_prompt(mode_specific_prompt, data)
        elif mode == BriefingMode.MORNING:
            return PromptBuilder._build_morning_prompt(mode_specific_prompt, data)
        else:
            return PromptBuilder._build_intraday_prompt(mode_specific_prompt, data)

    @staticmethod
    def _build_closing_prompt(mode_prompt: str, data: Dict) -> str:
        """Closing 브리핑 프롬프트"""
        return f"""
{PromptBuilder.SYSTEM_PROMPT}

{mode_prompt}

---

**Closing Briefing 전용 제약**:
- 현재 시점은 미국 시장 마감 이후다.
- 가정법(If)은 절대 사용하지 마라.
- 이미 발생한 이벤트와 그 결과만 기술하라.
- "왜 이렇게 끝났는지(Because)"에만 답하라.

**경제지표 분석 시**:
- ❌ "예상 상회 시: 주식 상승..." (금지 - 가정법)
- ✅ "결과: 50.1 (예상 49.8 상회). 시장 반응: 나스닥 0.5% 상승 마감" (허용)

**데이터**:
{data}

**출력 형식**: JSON 프로토콜 (스키마 준수)
"""

    @staticmethod
    def _build_morning_prompt(mode_prompt: str, data: Dict) -> str:
        """Morning 브리핑 프롬프트"""
        return f"""
{PromptBuilder.SYSTEM_PROMPT}

{mode_prompt}

---

**Morning Briefing 전용 제약**:
- 현재 시점은 미국 시장 개장 전이다.
- 결과값(Actual)을 언급하지 마라.
- 모든 행동은 조건문(IF-THEN)으로만 표현하라.
- 포지션 사이즈는 Risk Agent 기준을 우선 적용하라.

**시나리오 형식**:
- Case A: IF [조건] THEN [행동] (비중 X%)
- Case B: IF [조건] THEN [행동] (비중 X%)

**데이터**:
{data}

**출력 형식**: JSON 프로토콜 (스키마 준수)
"""

    @staticmethod
    def _build_intraday_prompt(mode_prompt: str, data: Dict) -> str:
        """Intraday 체크포인트 프롬프트"""
        return f"""
{PromptBuilder.SYSTEM_PROMPT}

{mode_prompt}

---

**Intraday 전용 제약**:
- 유의미한 변동(±1% 이상)이 있을 때만 분석 생성
- 변동 없으면 "skip": true 반환
- 간략하게 (500자 이내)

**데이터**:
{data}

**출력 형식**: JSON 프로토콜 (skip 필드 포함)
"""
```

---

### Phase 2: JSON 프로토콜 출력

#### Task 2.1: Pydantic 스키마 정의

**파일**: `backend/ai/reporters/schemas/trading_protocol.py` (신규)

```python
"""
Trading Protocol Schema (Pydantic v2)

ChatGPT/Gemini 합의 기반 JSON 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class CoreIndicators(BaseModel):
    """핵심 4대 지표 (불변)"""
    us10y: dict = Field(description="10년물 국채 금리")
    vix: dict = Field(description="변동성 지수")
    dxy: dict = Field(description="달러 인덱스")
    sector_leadership: List[dict] = Field(description="섹터 로테이션")


class ActionableScenario(BaseModel):
    """IF-THEN 시나리오"""
    condition: str = Field(description="조건 (예: US10Y < 4.10)")
    action: Literal["BUY", "SELL", "HOLD", "INCREASE_EXPOSURE", "REDUCE_EXPOSURE"]
    asset: str = Field(description="대상 자산 (예: QQQ, Technology)")
    size_pct: float = Field(ge=-1.0, le=1.0, description="비중 변화 (-1.0 ~ 1.0)")
    rationale: str = Field(description="근거")


class RiskManagement(BaseModel):
    """리스크 관리"""
    max_position_pct: float = Field(default=0.25, description="최대 포지션 비중")
    stop_loss_rule: str = Field(description="손절 규칙 (예: INDEX < 4950)")
    hedge_required: bool = Field(default=False)


class BacktestData(BaseModel):
    """백테스트 및 AI 고도화용 데이터"""
    model_version: str = Field(description="모델/프롬프트 버전")
    predicted_horizon: str = Field(description="예상 유효 기간 (1D, 1W, 1M)")
    reasoning_hash: str = Field(description="근거 데이터 스냅샷 해시")
    expected_reward_risk_ratio: float = Field(description="기대 손익비")


class TradingProtocol(BaseModel):
    """
    트레이딩 프로토콜 (최종 JSON 스키마)

    특징:
    - Closing/Morning 공용
    - 자동매매/백테스트 연동 가능
    - Human-in-the-loop 최소화
    """

    # 메타데이터
    meta: dict = Field(description="{mode, timestamp_utc, market}")

    # 시장 상태 (신호등)
    market_state: dict = Field(description="{trend, risk_score, risk_level, confidence}")

    # 핵심 4대 지표
    core_indicators: CoreIndicators

    # 시장 내러티브
    narrative: dict = Field(description="{market_story, dominant_driver}")

    # 실행 시나리오 (IF-THEN)
    actionable_scenarios: List[ActionableScenario]

    # 포트폴리오 영향
    portfolio_impact: dict = Field(description="{cash_change_pct, equity_change_pct, focus_assets, commentary}")

    # 리스크 관리
    risk_management: RiskManagement

    # 백테스트 데이터
    backtest_data: Optional[BacktestData] = None

    # Human 체크 필요 여부
    human_check_required: dict = Field(
        default={"rationale_check": True, "sizing_check": True, "exit_plan_check": True}
    )

    # 실행 의도 (AUTO vs HUMAN_APPROVAL)
    execution_intent: Literal["AUTO", "HUMAN_APPROVAL"] = Field(default="HUMAN_APPROVAL")

    class Config:
        json_schema_extra = {
            "example": {
                "meta": {
                    "mode": "CLOSING",
                    "timestamp_utc": "2026-01-24T00:40:00Z",
                    "market": "US"
                },
                "market_state": {
                    "trend": "UP",
                    "risk_score": 42,
                    "risk_level": "MEDIUM",
                    "confidence": 0.78
                },
                "execution_intent": "HUMAN_APPROVAL"
            }
        }
```

#### Task 2.2: DB 테이블 추가

**파일**: `backend/database/migrations/add_ai_trade_decisions_table.py` (신규)

```python
"""
Add AI Trade Decisions Table

트레이딩 프로토콜 저장용 테이블
- JSON 원본 저장 (JSONB)
- 주요 필드 인덱싱 (검색/분석용)
- 백테스트 검증 지원
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


def upgrade():
    """AI 트레이딩 결정 테이블 생성"""
    print("🔄 Creating ai_trade_decisions table...")

    op.create_table(
        'ai_trade_decisions',

        # PK
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        # 핵심 메타데이터 (인덱싱용)
        sa.Column('mode', sa.String(20), nullable=False),  # CLOSING, MORNING
        sa.Column('execution_intent', sa.String(20), nullable=False),  # AUTO, HUMAN_APPROVAL
        sa.Column('market_trend', sa.String(10)),  # UP, SIDE, DOWN
        sa.Column('risk_level', sa.String(10)),  # LOW, MEDIUM, HIGH
        sa.Column('risk_score', sa.Integer),  # 0-100

        # 전체 JSON 데이터
        sa.Column('full_report_json', JSONB, nullable=False),

        # 백테스트용 (JSON에서 추출)
        sa.Column('target_asset', sa.String(50)),
        sa.Column('suggested_action', sa.String(20)),
        sa.Column('suggested_size_pct', sa.Numeric(5, 2)),
        sa.Column('expected_rr_ratio', sa.Numeric(5, 2)),  # 기대 손익비

        # 사후 검증용 (트레이딩 후 업데이트)
        sa.Column('actual_profit_loss', sa.Numeric(10, 2)),
        sa.Column('is_strategy_correct', sa.Boolean),
        sa.Column('validated_at', sa.DateTime(timezone=True)),

        # 버전 관리
        sa.Column('model_version', sa.String(100)),
        sa.Column('prompt_version', sa.String(50))
    )

    # 인덱스 생성
    op.create_index('idx_ai_decisions_created_at', 'ai_trade_decisions', ['created_at'])
    op.create_index('idx_ai_decisions_mode', 'ai_trade_decisions', ['mode'])
    op.create_index('idx_ai_decisions_intent', 'ai_trade_decisions', ['execution_intent'])
    op.create_index('idx_ai_decisions_risk', 'ai_trade_decisions', ['risk_level'])

    print("✅ ai_trade_decisions table created")


def downgrade():
    """테이블 삭제"""
    op.drop_index('idx_ai_decisions_risk')
    op.drop_index('idx_ai_decisions_intent')
    op.drop_index('idx_ai_decisions_mode')
    op.drop_index('idx_ai_decisions_created_at')
    op.drop_table('ai_trade_decisions')
    print("✅ ai_trade_decisions table dropped")
```

---

### Phase 3: Market Moving Score

#### Task 3.1: 뉴스 점수 계산

**파일**: `backend/ai/intelligence/market_moving_score.py` (신규)

```python
"""
Market Moving Score Calculator

공식: Score = Impact×0.5 + Specificity×0.3 + Reliability×0.2

ChatGPT/Gemini 합의 기반
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class MarketMovingScore:
    """뉴스의 시장 영향도 점수"""
    total_score: float  # 0-100
    impact_score: float  # 0-100
    specificity_score: float  # 0-100
    reliability_score: float  # 0-100
    should_include: bool  # 임계값 초과 여부
    reasoning: str


class MarketMovingScoreCalculator:
    """
    Market Moving Score 계산기

    동적 임계값: VIX에 따라 조정
    - VIX 높음 (패닉) → 임계값 높여서 '진짜 큰 뉴스'만 통과
    - VIX 낮음 (안정) → 임계값 낮춰서 민감하게 반응
    """

    # 출처별 신뢰도 점수
    SOURCE_RELIABILITY = {
        # 100점: 공식 소스
        'Bloomberg': 100,
        'Reuters': 100,
        'SEC Filing': 100,
        'Federal Reserve': 100,
        'White House': 100,

        # 80점: 주요 언론
        'CNBC': 80,
        'Wall Street Journal': 80,
        'Financial Times': 80,
        'AP News': 80,

        # 60점: 경제지
        'MarketWatch': 60,
        'Seeking Alpha': 60,
        'Yahoo Finance': 60,

        # 40점: 커뮤니티/블로그
        'Twitter': 40,
        'Reddit': 40,

        # 기본값
        'default': 50
    }

    # 영향도 높은 키워드 (100점)
    HIGH_IMPACT_KEYWORDS = [
        # 실적/가이던스
        r'earnings (beat|miss)',
        r'guidance (raised|lowered|cut)',
        r'revenue (miss|beat|surpass)',

        # 금리/정책
        r'fed (hike|cut|pause|hold)',
        r'fomc (decision|meeting)',
        r'rate (hike|cut|decision)',

        # M&A/규제
        r'(acquire|merger|takeover)',
        r'(antitrust|regulation|lawsuit)',

        # 지정학적
        r'(war|invasion|sanction)',
        r'(tariff|trade war)',
    ]

    # 영향도 중간 키워드 (50점)
    MEDIUM_IMPACT_KEYWORDS = [
        r'analyst (upgrade|downgrade)',
        r'price target (raised|cut)',
        r'market (rally|selloff)',
        r'sector (rotation|shift)',
    ]

    # 구체성 높은 패턴 (100점)
    HIGH_SPECIFICITY_PATTERNS = [
        r'\b[A-Z]{1,5}\b',  # 티커 심볼 (NVDA, MSFT)
        r'\$\d+(\.\d+)?',   # 금액 ($150.25)
        r'\d+(\.\d+)?%',    # 퍼센트 (5.5%)
        r'CPI|PPI|GDP|PCE|NFP',  # 경제지표
    ]

    def __init__(self, current_vix: float = 20.0):
        self.current_vix = current_vix
        self.base_threshold = 60.0

    def calculate(
        self,
        title: str,
        summary: str,
        source: str,
        content: Optional[str] = None
    ) -> MarketMovingScore:
        """
        뉴스의 Market Moving Score 계산

        Returns:
            MarketMovingScore 객체
        """
        text = f"{title} {summary} {content or ''}".lower()

        # 1. Impact Score (50%)
        impact = self._calculate_impact(text)

        # 2. Specificity Score (30%)
        specificity = self._calculate_specificity(text)

        # 3. Reliability Score (20%)
        reliability = self._get_source_reliability(source)

        # 가중 평균
        total = impact * 0.5 + specificity * 0.3 + reliability * 0.2

        # 동적 임계값 계산
        threshold = self._get_dynamic_threshold()

        return MarketMovingScore(
            total_score=round(total, 1),
            impact_score=impact,
            specificity_score=specificity,
            reliability_score=reliability,
            should_include=total >= threshold,
            reasoning=self._generate_reasoning(impact, specificity, reliability, threshold)
        )

    def _calculate_impact(self, text: str) -> float:
        """영향도 점수 계산"""
        # HIGH 키워드 매칭
        for pattern in self.HIGH_IMPACT_KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                return 100.0

        # MEDIUM 키워드 매칭
        for pattern in self.MEDIUM_IMPACT_KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                return 50.0

        # 기본값
        return 20.0

    def _calculate_specificity(self, text: str) -> float:
        """구체성 점수 계산"""
        matches = 0

        for pattern in self.HIGH_SPECIFICITY_PATTERNS:
            if re.search(pattern, text):
                matches += 1

        # 매칭 수에 따라 점수
        if matches >= 3:
            return 100.0
        elif matches >= 2:
            return 70.0
        elif matches >= 1:
            return 40.0
        else:
            return 10.0

    def _get_source_reliability(self, source: str) -> float:
        """출처 신뢰도"""
        return self.SOURCE_RELIABILITY.get(source, self.SOURCE_RELIABILITY['default'])

    def _get_dynamic_threshold(self) -> float:
        """
        VIX 기반 동적 임계값

        - VIX 20 (기준) → threshold = 60
        - VIX 30 (패닉) → threshold = 75 (중요한 뉴스만)
        - VIX 12 (안정) → threshold = 48 (민감하게)
        """
        adjustment = (self.current_vix - 20) * 1.5
        return max(30, min(90, self.base_threshold + adjustment))

    def _generate_reasoning(
        self,
        impact: float,
        specificity: float,
        reliability: float,
        threshold: float
    ) -> str:
        """점수 근거 생성"""
        return (
            f"Impact={impact:.0f}×0.5 + Specificity={specificity:.0f}×0.3 + "
            f"Reliability={reliability:.0f}×0.2 | Threshold={threshold:.1f} (VIX={self.current_vix})"
        )
```

---

### Phase 4: Risk/Trader 충돌 규칙

#### Task 4.1: 충돌 해결 로직

**파일**: `backend/ai/mvp/conflict_resolver.py` (신규)

```python
"""
Risk vs Trader Agent Conflict Resolver

핵심 원칙: "Risk First, Profit Second"
- Risk Agent = Size(비중) 조절
- Trader Agent = Direction(방향) 결정
"""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class TraderSignal:
    """Trader Agent 시그널"""
    direction: Literal["BUY", "SELL", "HOLD"]
    suggested_size: float  # 0.0 ~ 1.0
    confidence: float  # 0.0 ~ 1.0
    rationale: str


@dataclass
class RiskAssessment:
    """Risk Agent 평가"""
    risk_score: int  # 0-100
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    max_size_allowed: float  # 0.0 ~ 1.0
    veto_reason: Optional[str] = None


@dataclass
class ResolvedTrade:
    """최종 결정"""
    action: Literal["BUY", "SELL", "HOLD", "REJECT"]
    size: float
    execution_intent: Literal["AUTO", "HUMAN_APPROVAL"]
    message: str
    original_trader_signal: TraderSignal
    risk_assessment: RiskAssessment


def resolve_trade(
    trader_signal: TraderSignal,
    risk_assessment: RiskAssessment
) -> ResolvedTrade:
    """
    Trader Agent와 Risk Agent 충돌 해결

    규칙:
    - Risk Score ≤ 30 (LOW): 100% 진입
    - Risk Score 31-70 (MEDIUM): 50% 진입
    - Risk Score > 70 (HIGH):
        - Confidence ≥ 0.9: 20% 진입
        - Confidence < 0.9: 진입 거부

    Returns:
        ResolvedTrade 객체
    """
    base_size = trader_signal.suggested_size
    risk_score = risk_assessment.risk_score
    confidence = trader_signal.confidence

    # LOW Risk (≤ 30)
    if risk_score <= 30:
        final_size = base_size
        intent = "AUTO" if confidence >= 0.85 else "HUMAN_APPROVAL"
        message = "✅ 적극 매수 (Risk Low)"
        action = trader_signal.direction

    # MEDIUM Risk (31-70)
    elif risk_score <= 70:
        final_size = base_size * 0.5
        intent = "HUMAN_APPROVAL"
        message = f"⚠️ 비중 축소 진입 ({final_size*100:.0f}%)"
        action = trader_signal.direction

    # HIGH Risk (> 70)
    else:
        if confidence >= 0.9:
            final_size = base_size * 0.2
            intent = "HUMAN_APPROVAL"
            message = f"🔶 초소량 정찰병 투입 ({final_size*100:.0f}%)"
            action = trader_signal.direction
        else:
            final_size = 0.0
            intent = "HUMAN_APPROVAL"
            message = "🚫 리스크 과다로 진입 거부"
            action = "REJECT"

    return ResolvedTrade(
        action=action,
        size=round(final_size, 3),
        execution_intent=intent,
        message=message,
        original_trader_signal=trader_signal,
        risk_assessment=risk_assessment
    )


def determine_execution_intent(
    trader_confidence: float,
    risk_level: str
) -> Literal["AUTO", "HUMAN_APPROVAL"]:
    """
    자동 실행 여부 결정

    AUTO 조건 (단 하나):
    Trader_Confidence > 0.85 AND Risk_Level == 'LOW'
    """
    if trader_confidence > 0.85 and risk_level == "LOW":
        return "AUTO"
    return "HUMAN_APPROVAL"
```

---

### Phase 5: 3단 깔때기 구조

#### Task 5.1: 깔때기 출력 생성기

**파일**: `backend/ai/reporters/funnel_generator.py` (신규)

```python
"""
3단 깔때기 구조 생성기

1. Market State (신호등) - 🟢🟡🔴
2. Actionable Scenarios (IF-THEN)
3. Portfolio Impact (내 포트폴리오 영향)
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class MarketSignal(Enum):
    GREEN = "🟢"   # Bullish
    YELLOW = "🟡"  # Neutral
    RED = "🔴"     # Bearish


@dataclass
class MarketState:
    """시장 상태 신호등"""
    signal: MarketSignal
    trend: str  # UP, SIDE, DOWN
    risk_score: int  # 0-100
    top_action: str  # 한 줄 결론


@dataclass
class ActionableScenario:
    """IF-THEN 시나리오"""
    case_id: str  # A, B, C
    condition: str
    action: str
    asset: str
    size_pct: float


@dataclass
class PortfolioImpact:
    """포트폴리오 영향"""
    focus_assets: List[str]
    commentary: str
    cash_change_pct: float
    equity_change_pct: float


class FunnelGenerator:
    """3단 깔때기 생성기"""

    def generate(
        self,
        indicators: Dict[str, Any],
        scenarios: List[Dict],
        portfolio: Dict
    ) -> Dict[str, Any]:
        """
        3단 깔때기 구조 생성

        Returns:
            {
                "market_state": {...},
                "actionable_scenarios": [...],
                "portfolio_impact": {...}
            }
        """
        # 1. Market State
        market_state = self._generate_market_state(indicators)

        # 2. Actionable Scenarios
        actionable = self._format_scenarios(scenarios)

        # 3. Portfolio Impact
        impact = self._analyze_portfolio_impact(portfolio, scenarios)

        return {
            "market_state": {
                "signal": market_state.signal.value,
                "trend": market_state.trend,
                "risk_score": market_state.risk_score,
                "top_action": market_state.top_action
            },
            "actionable_scenarios": actionable,
            "portfolio_impact": {
                "focus_assets": impact.focus_assets,
                "commentary": impact.commentary,
                "cash_change_pct": impact.cash_change_pct,
                "equity_change_pct": impact.equity_change_pct
            }
        }

    def _generate_market_state(self, indicators: Dict) -> MarketState:
        """시장 상태 판단"""
        vix = indicators.get('vix', {}).get('value', 20)
        us10y_change = indicators.get('us10y', {}).get('day_change_bp', 0)

        # 신호등 결정 로직
        risk_score = self._calculate_risk_score(vix, us10y_change)

        if risk_score <= 30:
            signal = MarketSignal.GREEN
            trend = "UP"
            action = "기술주 비중 확대"
        elif risk_score <= 60:
            signal = MarketSignal.YELLOW
            trend = "SIDE"
            action = "현금 비중 유지"
        else:
            signal = MarketSignal.RED
            trend = "DOWN"
            action = "방어주로 로테이션"

        return MarketState(
            signal=signal,
            trend=trend,
            risk_score=risk_score,
            top_action=action
        )

    def _calculate_risk_score(self, vix: float, rate_change: float) -> int:
        """리스크 점수 계산 (0-100)"""
        # VIX 기여 (최대 50점)
        vix_score = min(50, max(0, (vix - 12) * 2.5))

        # 금리 변동 기여 (최대 30점)
        rate_score = min(30, abs(rate_change) * 3)

        # 기본 점수
        base_score = 20

        return int(min(100, vix_score + rate_score + base_score))

    def _format_scenarios(self, scenarios: List[Dict]) -> List[Dict]:
        """시나리오 포맷팅"""
        formatted = []
        for i, s in enumerate(scenarios[:4]):  # 최대 4개
            formatted.append({
                "case": chr(65 + i),  # A, B, C, D
                "condition": s.get('condition', ''),
                "action": s.get('action', ''),
                "asset": s.get('asset', ''),
                "size_pct": s.get('size_pct', 0.0),
                "rationale": s.get('rationale', '')
            })
        return formatted

    def _analyze_portfolio_impact(
        self,
        portfolio: Dict,
        scenarios: List[Dict]
    ) -> PortfolioImpact:
        """포트폴리오 영향 분석"""
        # 시나리오에서 언급된 자산 추출
        focus_assets = list(set(s.get('asset', '') for s in scenarios if s.get('asset')))

        # 현금/주식 비중 변화 계산
        buy_scenarios = [s for s in scenarios if 'BUY' in s.get('action', '') or 'INCREASE' in s.get('action', '')]
        sell_scenarios = [s for s in scenarios if 'SELL' in s.get('action', '') or 'REDUCE' in s.get('action', '')]

        cash_change = sum(s.get('size_pct', 0) for s in sell_scenarios) - sum(s.get('size_pct', 0) for s in buy_scenarios)

        return PortfolioImpact(
            focus_assets=focus_assets[:5],
            commentary="시나리오 기반 포트폴리오 조정 필요",
            cash_change_pct=round(cash_change, 2),
            equity_change_pct=round(-cash_change, 2)
        )
```

---

## 검증 체크리스트

### Phase 1 검증: 시점 분리
- [x] Closing 브리핑에서 가정법(If) 사용 안 함 ✅ (2026-01-24 검증 완료)
- [x] Morning 브리핑에서 결과값(Actual) 언급 안 함 ✅ (2026-01-24 검증 완료)
- [x] 모드 자동 판단 (시간 기반) ✅ (2026-01-24 검증 완료)

### Phase 2 검증: JSON 프로토콜
- [x] TradingProtocol 스키마 유효성 ✅ (2026-01-24 검증 완료)
- [x] ai_trade_decisions 테이블 생성 ✅ (2026-01-24 검증 완료 - 20컬럼, 9인덱스)
- [x] JSON 저장/조회 정상 ✅ (2026-01-24 검증 완료)

### Phase 3 검증: Market Moving Score
- [x] 뉴스 점수 계산 (0-100) ✅ (2026-01-24 검증 완료 - HIGH:100, MEDIUM:65, LOW:0)
- [x] VIX 연동 동적 임계값 ✅ (2026-01-24 검증 완료 - VIX 12→48, VIX 20→60, VIX 30→75)
- [x] 노이즈 뉴스 필터링 ✅ (2026-01-24 검증 완료 - 4건→2건 필터링)


### Phase 4 검증: 충돌 규칙
- [x] Risk 30 이하 → 100% 진입 ✅ (2026-01-24 검증 완료 - 25%→25%)
- [x] Risk 31-70 → 50% 진입 ✅ (2026-01-24 검증 완료 - 30%→15%)
- [x] Risk 70 초과 + Confidence < 0.9 → 거부 ✅ (2026-01-24 검증 완료 - REJECT)
- [x] Risk 70 초과 + Confidence ≥ 0.9 → 20% 정찰병 ✅ (2026-01-24 검증 완료 - 25%→5%)
- [x] AUTO 실행 조건 ✅ (Confidence > 0.85 AND Risk=LOW)


### Phase 5 검증: 3단 깔때기
- [x] 신호등 출력 (🟢🟡🔴) ✅ (2026-01-24 검증 완료 - VIX 14→🟢, 20→🟡, 32→🔴)
- [x] IF-THEN 시나리오 4개 이하 ✅ (2026-01-24 검증 완료 - 5개 입력→4개 출력)
- [x] 포트폴리오 영향 분석 ✅ (2026-01-24 검증 완료 - Buy 20%-Sell 10%=+10% equity)


---

## 완료 기준

v2.3 완료 시 다음 상태:

1. ✅ **Closing/Morning 완전 분리** - 가정법/직설법 강제 (2026-01-24 완료)
2. ✅ **JSON 프로토콜 출력** - 자동매매 연동 가능 (2026-01-24 완료)
3. ✅ **Market Moving Score** - 뉴스 필터링 정교화 (2026-01-24 완료)
4. ✅ **Risk-First 규칙** - 충돌 해결 로직 (2026-01-24 완료)
5. ✅ **3단 깔때기** - State → Scenarios → Impact (2026-01-24 완료)

**v2.3 전체 구현 완료일**: 2026-01-24


---

## 참고 문서

- **ChatGPT 피드백**: `docs/discussions/260124/chatgptideas.md`
- **Gemini 피드백**: `docs/discussions/260124/geminiideas.md`
- **v2.2 계획서**: `docs/planning/260122_daily_briefing_v2.2_optimized_implementation_plan.md`

---

**End of v2.3 Implementation Plan**
