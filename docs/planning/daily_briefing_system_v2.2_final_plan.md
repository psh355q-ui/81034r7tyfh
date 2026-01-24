# Daily Briefing System v2.2 - 최종 통합 개발 계획서

**작성일**: 2026-01-22  
**버전**: v2.2 Final  
**검토**: Claude Code + ChatGPT + Gemini + Claude Opus 통합 검토  
**시스템**: Antigravity AI Trading System  

---

## 📋 목차

1. [시스템 개요](#1-시스템-개요)
2. [24시간 운영 타임라인](#2-24시간-운영-타임라인)
3. [서머타임 적용 스케줄러](#3-서머타임-적용-스케줄러)
4. [핵심 아키텍처](#4-핵심-아키텍처)
5. [구현 Phase 순서](#5-구현-phase-순서)
6. [Phase별 상세 작업](#6-phase별-상세-작업)
7. [🆕 Real-time Economic Watcher](#7-real-time-economic-watcher)
8. [브리핑 프롬프트 전문](#8-브리핑-프롬프트-전문)
9. [텔레그램 알림 시스템](#9-텔레그램-알림-시스템)
10. [KIS API 포트폴리오 연동](#10-kis-api-포트폴리오-연동)
11. [주간 리포트 시스템](#11-주간-리포트-시스템)
12. [검증 체크리스트](#12-검증-체크리스트)
13. [완료 기준](#13-완료-기준)

---

## 1. 시스템 개요

### 1.1 목표

| 목표 | 설명 |
|------|------|
| **비용 절감** | 캐싱 전략으로 LLM API 호출 70% 절감 |
| **24시간 운영** | RSS 크롤링 + Ollama 전처리 상시 가동 |
| **5단계 브리핑** | 프리마켓 → 장중 체크 → 마감 → 국내 → 주간 |
| **🆕 실시간 경제지표** | 발표 10~30초 내 Actual 수집 및 분석 |
| **실시간 알림** | 텔레그램 봇으로 속보/브리핑/지표 푸시 |
| **포트폴리오 연동** | KIS API 기반 보유종목 맞춤 분석 |
| **자동 개선** | 주간 시스템 분석으로 지속적 개선 |

### 1.2 v2.2 신규 기능: Real-time Economic Watcher

```
┌─────────────────────────────────────────────────────────────────┐
│              🆕 Real-time Economic Watcher                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   [문제점]                                                       │
│   RSS 크롤링 5분 주기로는 경제지표 발표 직후 반영 불가능          │
│                                                                  │
│   [해결책]                                                       │
│   이벤트 기반 스나이퍼(Sniper) 모듈                              │
│   - 발표 시간까지 대기 (Sleep)                                   │
│   - 발표 10초 후 트리거 → Actual 값 수집                         │
│   - 예상 vs 실제 괴리(Surprise) 계산                             │
│   - 즉시 브리핑 업데이트 + 텔레그램 알림                         │
│                                                                  │
│   [대상 지표]                                                    │
│   ★★★ GDP, PCE, CPI, 고용지표, FOMC                            │
│   ★★  EIA 재고, 주택지표, PMI                                   │
│   ★   기타 참고 지표                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 브리핑 체계 (5단계 + 실시간)

```
┌─────────────────────────────────────────────────────────────────┐
│                    📅 일간 브리핑 (평일)                          │
├─────────────────────────────────────────────────────────────────┤
│  23:00  🌙 프리마켓 브리핑      - 미국장 시작 전 뉴스 정리        │
│  ??:??  ⚡ 경제지표 속보        - 발표 10초 후 즉시 알림 (NEW)   │
│  01:00  📍 장중 체크포인트 #1   - 장 시작 30분 후 점검           │
│  03:00  📍 장중 체크포인트 #2   - 장 중간 점검                   │
│  07:10  🇺🇸 미국장 마감 브리핑   - 장 마감 분석                  │
│  08:00  🇰🇷 국내장 오픈 브리핑   - 한국 시장 연결                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    📅 주간 브리핑 (주말)                          │
├─────────────────────────────────────────────────────────────────┤
│  토 07:10  🇺🇸 금요일 마감 브리핑  - 주간 마지막 장 분석          │
│  토 14:00  📊 주간 리뷰          - 한 주 성과 분석               │
│  일 22:00  🔮 주간 전망 리포트    - 다음 주 전망 + 시스템 분석   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 24시간 운영 타임라인

### 2.1 평일 타임라인 (한국 시간 기준)

```
═══════════════════════════════════════════════════════════════
                    📅 평일 24시간 운영
═══════════════════════════════════════════════════════════════

     [상시 가동]
     ┌─────────────────────────────────────────────────────┐
     │  🔄 RSS 크롤링: 10분 간격                            │
     │  🤖 Ollama 전처리: 5분 간격                          │
     │  📡 텔레그램 속보 알림: 실시간                        │
     │  ⚡ 경제지표 스나이퍼: 이벤트 기반 (NEW)              │
     └─────────────────────────────────────────────────────┘

06:00 ═══════════ 🔔 미국장 마감 (동절기) ═══════════
      │
07:10 ├─── 🇺🇸 미국장 마감 브리핑 생성
      │         └─ 📲 텔레그램 전송
      │
08:00 ├─── 🇰🇷 국내장 오픈 브리핑 생성
      │         └─ 📲 텔레그램 전송
      │
09:00 ═══════════ 🔔 국내장 시작 ═══════════
      │
15:30 ═══════════ 🔔 국내장 마감 ═══════════
      │
22:00 ├─── 🔄 Ollama 전처리 강화 (장전 뉴스 집중)
      │
22:30 ├─── ⚡ 경제지표 발표 (GDP, PCE 등) - 스나이퍼 대기
      │         └─ 22:30:10 Actual 수집 → 즉시 분석
      │         └─ 📲 텔레그램 즉시 알림
      │
23:00 ├─── 🌙 프리마켓 브리핑 생성 (경제지표 결과 포함)
      │         └─ 📲 텔레그램 전송
      │
00:00 ├─── ⚡ 경제지표 발표 (PCE 등) - 스나이퍼 대기
      │
00:30 ═══════════ 🔔 미국장 시작 (동절기) ═══════════
      │    ├─── ⚡ EIA 재고 발표 - 스나이퍼 대기
      │
01:00 ├─── 📍 장중 체크포인트 #1
      │
02:00 ├─── ⚡ EIA 원유 재고 발표 - 스나이퍼 대기
      │
03:00 ├─── 📍 장중 체크포인트 #2
      │
06:00 ═══════════ 🔔 미국장 마감 ═══════════ (반복)
```

---

## 3. 서머타임 적용 스케줄러

**(v2.1과 동일 - 생략)**

---

## 4. 핵심 아키텍처

### 4.1 시스템 구성도 (v2.2 - Economic Watcher 추가)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI Trading System v2.2                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐           │
│   │ RSS Crawler  │────▶│   Ollama     │────▶│  PostgreSQL  │           │
│   │ (10분 간격)   │     │ 전처리(5분)  │     │     DB       │           │
│   └──────────────┘     └──────────────┘     └──────┬───────┘           │
│                                                      │                   │
│   ┌──────────────────────────────────────────────────┼──────────────┐   │
│   │               🆕 Economic Watcher                │              │   │
│   │  ┌─────────────────────────────────────────────────────────┐   │   │
│   │  │  [Event Sniper Scheduler]                               │   │   │
│   │  │    │                                                     │   │   │
│   │  │    ├─ 매일 00:00: 오늘의 ★★★ 일정 로드                  │   │   │
│   │  │    ├─ 발표 시간까지 Sleep                                │   │   │
│   │  │    ├─ 발표 +10초: Actual 값 Fetch                        │   │   │
│   │  │    ├─ Surprise 계산 (예상 vs 실제)                       │   │   │
│   │  │    └─ 즉시 알림 + 브리핑 Context 주입                    │   │   │
│   │  └─────────────────────────────────────────────────────────┘   │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                      │                   │
│   ┌──────────────────────────────────────────────────┼──────────────┐   │
│   │                    Briefing Engine               │              │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌────────────▼───────────┐  │   │
│   │  │ 프리마켓    │  │ 장중 체크   │  │   Gemini/Claude API    │  │   │
│   │  │ 브리핑      │  │ 포인트      │  │   (웹 검색 + 심층검토)   │  │   │
│   │  └─────────────┘  └─────────────┘  └────────────────────────┘  │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────┐  │   │
│   │  │ 미국 마감   │  │ 국내 오픈   │  │     주간 리포트        │  │   │
│   │  │ 브리핑      │  │ 브리핑      │  │  (리뷰 + 전망 + 분석)   │  │   │
│   │  └─────────────┘  └─────────────┘  └────────────────────────┘  │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│   ┌────────────────────────────────┼────────────────────────────────┐   │
│   │              Integration Layer │                                │   │
│   │  ┌─────────────┐  ┌───────────▼─┐  ┌─────────────────────────┐ │   │
│   │  │  KIS API    │  │  Telegram   │  │   Cache Manager         │ │   │
│   │  │ 포트폴리오  │  │    Bot      │  │   (중요도 기반 캐싱)     │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 영향도 점수 계산 (경제지표 포함)

| 소스 | 가중치 | 설명 |
|------|--------|------|
| 뉴스 영향도 | 30% | RSS 뉴스 market_relevance 합산 |
| **🆕 경제지표 영향도** | **40%** | Surprise 크기에 따른 점수 |
| 기술/섹터 시그널 | 20% | 섹터 로테이션, 기술적 지표 |
| AI 추천주 변경 | 10% | AI 모델 추천 종목 변화 |

```python
total_score = news_score * 0.3 + econ_score * 0.4 + tech_score * 0.2 + ai_score * 0.1
```

---

## 5. 구현 Phase 순서

```
═══════════════════════════════════════════════════════════════
                    구현 Phase 순서 (총 11단계)
═══════════════════════════════════════════════════════════════

Phase 1: DB 마이그레이션 (선행 필수)
  └─> models.py 수정 (NewsArticle + EconomicEvent 테이블)
  └─> 마이그레이션 → DB 적용

Phase 2: Ollama 전처리 시스템
  └─> ollama_rss_preprocessor.py 생성

Phase 3: 캐싱 시스템
  └─> daily_briefing_cache_manager.py 생성

Phase 3.5: 🆕 Real-time Economic Watcher (NEW)
  └─> economic_event 테이블 생성
  └─> economic_calendar_fetcher.py (일정 수집)
  └─> economic_watcher.py (스나이퍼 로직)
  └─> economic_analyzer.py (Surprise 분석)

Phase 4: 서머타임 스케줄러
  └─> timezone_manager.py 생성
  └─> dynamic_scheduler.py 생성

Phase 5: 미국장 브리핑 (마감 + 프리마켓 + 체크포인트)
  └─> enhanced_daily_reporter.py 수정
  └─> 경제지표 Context 통합

Phase 6: 국내장 브리핑
  └─> korean_market_briefing_reporter.py 생성

Phase 7: KIS API 포트폴리오 연동
  └─> portfolio_analyzer.py 생성

Phase 8: 텔레그램 알림 시스템
  └─> telegram_bot.py 생성
  └─> 경제지표 속보 알림 추가

Phase 9: 주간 리포트 시스템
  └─> weekly_reporter.py 생성

Phase 10: API & 통합 테스트
  └─> reports_router.py 수정
  └─> 전체 시스템 통합 테스트
```

---

## 6. Phase별 상세 작업

### Phase 1: DB 마이그레이션

#### Task 1.1: models.py 수정 (EconomicEvent 추가)

**파일**: `backend/database/models.py`

```python
# ═══════════════════════════════════════════════════════════════
# Economic Events Table (Daily Briefing System v2.2)
# ═══════════════════════════════════════════════════════════════

class EconomicEvent(Base):
    """경제 캘린더 이벤트 테이블"""
    
    __tablename__ = "economic_events"

    id = Column(Integer, primary_key=True, index=True)
    
    # 기본 정보
    event_name = Column(String(200), nullable=False, index=True,
        comment='이벤트명 (예: 미국 3분기 실질 GDP)')
    event_name_en = Column(String(200), nullable=True,
        comment='영문 이벤트명')
    country = Column(String(10), default="US", index=True,
        comment='국가 코드 (US, KR, EU, CN, JP)')
    category = Column(String(50), nullable=True,
        comment='카테고리 (GDP, Inflation, Employment, Housing, Energy, Fed)')
    
    # 시간 정보
    event_time = Column(DateTime(timezone=True), nullable=False, index=True,
        comment='발표 예정 시간 (KST)')
    event_time_utc = Column(DateTime(timezone=True), nullable=True,
        comment='발표 예정 시간 (UTC)')
    
    # 중요도
    importance = Column(Integer, default=1,
        comment='중요도 (1=★, 2=★★, 3=★★★)')
    
    # 수치 데이터
    forecast = Column(String(50), nullable=True,
        comment='예상치 (예: 4.3%)')
    actual = Column(String(50), nullable=True,
        comment='실제치 (발표 후 업데이트)')
    previous = Column(String(50), nullable=True,
        comment='이전치 (예: 4.3%)')
    
    # 분석 결과
    surprise_pct = Column(Float, nullable=True,
        comment='서프라이즈 비율 ((실제-예상)/예상 * 100)')
    impact_direction = Column(String(20), nullable=True,
        comment='영향 방향 (Bullish, Bearish, Neutral)')
    impact_score = Column(Integer, nullable=True,
        comment='영향도 점수 (0-100)')
    
    # 상태
    is_processed = Column(Boolean, default=False, index=True,
        comment='처리 완료 여부')
    processed_at = Column(DateTime(timezone=True), nullable=True,
        comment='처리 시간')
    fetch_attempts = Column(Integer, default=0,
        comment='Actual 수집 시도 횟수')
    
    # 메타
    source = Column(String(50), nullable=True,
        comment='데이터 소스 (Investing.com, FMP, AlphaVantage)')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_econ_event_time', 'event_time'),
        Index('idx_econ_country_importance', 'country', 'importance'),
        Index('idx_econ_unprocessed', 'is_processed', 'event_time',
              postgresql_where=text('is_processed = false')),
    )


class EconomicEventHistory(Base):
    """경제 지표 히스토리 (분석용)"""
    
    __tablename__ = "economic_event_history"
    
    id = Column(Integer, primary_key=True)
    event_name = Column(String(200), nullable=False, index=True)
    event_time = Column(DateTime(timezone=True), nullable=False)
    forecast = Column(String(50))
    actual = Column(String(50))
    previous = Column(String(50))
    surprise_pct = Column(Float)
    market_reaction = Column(JSONB, nullable=True,
        comment='시장 반응 (S&P 5분/15분/1시간 변동률)')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### Task 1.2: 마이그레이션 파일

**파일**: `backend/database/migrations/add_economic_events_table.py`

```python
"""
Add Economic Events table for Real-time Economic Watcher

Migration for Daily Briefing System v2.2
Created: 2026-01-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


def upgrade():
    """Create economic_events table"""
    print("🔄 Creating economic_events table...")
    
    op.create_table(
        'economic_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_name', sa.String(200), nullable=False, index=True),
        sa.Column('event_name_en', sa.String(200), nullable=True),
        sa.Column('country', sa.String(10), default='US', index=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('event_time_utc', sa.DateTime(timezone=True), nullable=True),
        sa.Column('importance', sa.Integer(), default=1),
        sa.Column('forecast', sa.String(50), nullable=True),
        sa.Column('actual', sa.String(50), nullable=True),
        sa.Column('previous', sa.String(50), nullable=True),
        sa.Column('surprise_pct', sa.Float(), nullable=True),
        sa.Column('impact_direction', sa.String(20), nullable=True),
        sa.Column('impact_score', sa.Integer(), nullable=True),
        sa.Column('is_processed', sa.Boolean(), default=False, index=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetch_attempts', sa.Integer(), default=0),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # History table
    op.create_table(
        'economic_event_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_name', sa.String(200), nullable=False, index=True),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('forecast', sa.String(50)),
        sa.Column('actual', sa.String(50)),
        sa.Column('previous', sa.String(50)),
        sa.Column('surprise_pct', sa.Float()),
        sa.Column('market_reaction', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    print("✅ Economic events tables created")


def downgrade():
    """Drop economic_events tables"""
    op.drop_table('economic_event_history')
    op.drop_table('economic_events')
```

---

## 7. 🆕 Real-time Economic Watcher

### 7.1 시스템 흐름도

```
┌─────────────────────────────────────────────────────────────────┐
│                   Economic Watcher Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Step 1] 매일 00:00 - 오늘의 일정 로드                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Economic Calendar Fetcher                               │    │
│  │  - Investing.com 캘린더 크롤링                           │    │
│  │  - ★★★ 이벤트만 필터링                                  │    │
│  │  - DB에 저장 (is_processed = False)                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                          ▼                                       │
│  [Step 2] 이벤트별 스나이퍼 스케줄링                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Event Sniper Scheduler                                  │    │
│  │  - 22:30 GDP 발표 → 22:30:10 트리거 예약                 │    │
│  │  - 00:00 PCE 발표 → 00:00:10 트리거 예약                 │    │
│  │  - asyncio.create_task(sniper_execution)                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                          ▼                                       │
│  [Step 3] 발표 시간 + 10초 → 스나이퍼 발동                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Sniper Execution                                        │    │
│  │  - Actual 값 수집 (재시도 3회, 5초 간격)                  │    │
│  │  - 수집 실패 시 15초 후 재시도                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                          ▼                                       │
│  [Step 4] Surprise 분석                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Surprise Analyzer                                       │    │
│  │  - 예상 4.3% vs 실제 3.5% → -18.6% 괴리                  │    │
│  │  - Impact Score 계산                                     │    │
│  │  - Bullish/Bearish/Neutral 판정                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                       │
│                          ▼                                       │
│  [Step 5] 즉시 알림 + 브리핑 Context 주입                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Alert & Context Injection                               │    │
│  │  - 📲 텔레그램 즉시 알림                                  │    │
│  │  - 브리핑 생성 시 '긴급 컨텍스트'로 최우선 반영            │    │
│  │  - DB 업데이트 (is_processed = True)                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 데이터 소스 선택

| 소스 | 장점 | 단점 | 추천도 |
|------|------|------|--------|
| **Investing.com** | 무료, 한글 지원, 포괄적 | 크롤링 필요, 구조 변경 위험 | ⭐⭐⭐ |
| **FMP API** | 안정적, JSON 형식 | 유료 (무료 제한적) | ⭐⭐⭐ |
| **Alpha Vantage** | 무료 티어 있음 | 실시간성 부족 | ⭐⭐ |
| **FRED API** | 공식, 신뢰성 | GDP/PCE만, 딜레이 있음 | ⭐⭐ |
| **ForexFactory** | 무료, 상세 | 영문만 | ⭐⭐ |

**추천 전략**:
1. **1차**: Investing.com 크롤러 (무료, 한글)
2. **백업**: FMP API (안정성)
3. **검증**: FRED API (공식 데이터 크로스체크)

### 7.3 Economic Calendar Fetcher

**파일**: `backend/services/economic_calendar_fetcher.py`

```python
"""
Economic Calendar Fetcher

Investing.com 경제 캘린더에서 오늘의 주요 일정 수집
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import EconomicEvent
from backend.database.connection import DatabaseSession

logger = logging.getLogger(__name__)


class EconomicCalendarFetcher:
    """경제 캘린더 수집기"""
    
    # Investing.com 경제 캘린더 URL
    INVESTING_URL = "https://kr.investing.com/economic-calendar/"
    
    # 주요 지표 카테고리 매핑
    CATEGORY_MAP = {
        'gdp': 'GDP',
        '국내총생산': 'GDP',
        'pce': 'Inflation',
        '개인소비지출': 'Inflation',
        'cpi': 'Inflation',
        '소비자물가': 'Inflation',
        '실업': 'Employment',
        '고용': 'Employment',
        'nonfarm': 'Employment',
        '비농업': 'Employment',
        'fomc': 'Fed',
        '금리': 'Fed',
        'eia': 'Energy',
        '원유': 'Energy',
        '천연가스': 'Energy',
        '재고': 'Energy',
        '주택': 'Housing',
        'pmi': 'PMI',
        '구매관리자': 'PMI',
    }
    
    # 중요도 필터 (★★★만)
    MIN_IMPORTANCE = 3
    
    def __init__(self):
        self.tz_kst = ZoneInfo("Asia/Seoul")
        self.tz_utc = ZoneInfo("UTC")
    
    async def fetch_todays_events(self) -> List[Dict]:
        """
        오늘의 경제 일정 수집
        
        Returns:
            List of event dictionaries
        """
        logger.info("📅 Fetching today's economic calendar...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.INVESTING_URL,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"❌ Failed to fetch calendar: {response.status_code}")
                    return []
                
                return self._parse_calendar_html(response.text)
                
        except Exception as e:
            logger.error(f"❌ Error fetching calendar: {e}")
            return []
    
    def _parse_calendar_html(self, html: str) -> List[Dict]:
        """HTML 파싱하여 이벤트 추출"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Investing.com 캘린더 테이블 파싱
        # (실제 구현 시 사이트 구조에 맞게 조정 필요)
        rows = soup.select('tr.js-event-item')
        
        for row in rows:
            try:
                # 중요도 (별 개수)
                importance = len(row.select('.grayFullBullishIcon'))
                if importance < self.MIN_IMPORTANCE:
                    continue
                
                # 시간
                time_cell = row.select_one('.time')
                time_str = time_cell.text.strip() if time_cell else None
                
                # 국가
                country_cell = row.select_one('.flagCur')
                country = country_cell.get('title', 'US')[:2].upper() if country_cell else 'US'
                
                # 이벤트명
                event_cell = row.select_one('.event')
                event_name = event_cell.text.strip() if event_cell else None
                
                # 예상/실제/이전
                forecast = row.select_one('.forecast')
                actual = row.select_one('.actual')
                previous = row.select_one('.previous')
                
                if event_name and time_str:
                    event = {
                        'event_name': event_name,
                        'country': country,
                        'importance': importance,
                        'time_str': time_str,
                        'forecast': forecast.text.strip() if forecast else None,
                        'actual': actual.text.strip() if actual else None,
                        'previous': previous.text.strip() if previous else None,
                        'category': self._detect_category(event_name),
                    }
                    events.append(event)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error parsing row: {e}")
                continue
        
        logger.info(f"✅ Found {len(events)} high-importance events")
        return events
    
    def _detect_category(self, event_name: str) -> str:
        """이벤트명에서 카테고리 추출"""
        name_lower = event_name.lower()
        for keyword, category in self.CATEGORY_MAP.items():
            if keyword in name_lower:
                return category
        return 'Other'
    
    async def save_events_to_db(self, events: List[Dict]) -> int:
        """이벤트를 DB에 저장"""
        saved_count = 0
        
        async with DatabaseSession() as session:
            for event_data in events:
                try:
                    # 중복 체크
                    existing = await session.execute(
                        select(EconomicEvent).where(
                            and_(
                                EconomicEvent.event_name == event_data['event_name'],
                                EconomicEvent.event_time == event_data['event_time']
                            )
                        )
                    )
                    
                    if existing.scalar_one_or_none():
                        continue
                    
                    # 새 이벤트 저장
                    event = EconomicEvent(
                        event_name=event_data['event_name'],
                        country=event_data['country'],
                        category=event_data['category'],
                        importance=event_data['importance'],
                        event_time=event_data['event_time'],
                        forecast=event_data['forecast'],
                        previous=event_data['previous'],
                        source='Investing.com'
                    )
                    session.add(event)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error saving event: {e}")
                    continue
            
            await session.commit()
        
        logger.info(f"✅ Saved {saved_count} events to DB")
        return saved_count


# Alternative: FMP API Fetcher
class FMPCalendarFetcher:
    """Financial Modeling Prep API 기반 캘린더 수집기 (백업)"""
    
    FMP_API_URL = "https://financialmodelingprep.com/api/v3/economic_calendar"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def fetch_events(self, from_date: str, to_date: str) -> List[Dict]:
        """FMP API로 경제 일정 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.FMP_API_URL,
                params={
                    'from': from_date,
                    'to': to_date,
                    'apikey': self.api_key
                }
            )
            
            if response.status_code == 200:
                return response.json()
            return []
```

### 7.4 Economic Watcher (스나이퍼)

**파일**: `backend/services/economic_watcher.py`

```python
"""
Economic Watcher (Event Sniper)

경제 지표 발표 직후 10~30초 내 Actual 값 수집 및 분석
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import EconomicEvent, EconomicEventHistory
from backend.database.connection import DatabaseSession
from backend.services.economic_calendar_fetcher import EconomicCalendarFetcher, FMPCalendarFetcher
from backend.notifications.telegram_bot import get_telegram_bot

logger = logging.getLogger(__name__)


class EconomicWatcher:
    """
    경제 지표 실시간 감시자 (Event Sniper)
    
    작동 방식:
    1. 매일 00:00에 오늘의 ★★★ 일정 로드
    2. 각 이벤트 발표 시간에 맞춰 스나이퍼 태스크 생성
    3. 발표 +10초에 Actual 값 수집 시도
    4. Surprise 분석 후 즉시 알림
    """
    
    # 설정
    SNIPER_DELAY_SECONDS = 10  # 발표 후 대기 시간
    MAX_FETCH_ATTEMPTS = 3     # 최대 재시도 횟수
    RETRY_INTERVAL = 5         # 재시도 간격 (초)
    
    def __init__(self):
        self.calendar_fetcher = EconomicCalendarFetcher()
        self.telegram_bot = get_telegram_bot()
        self.tz_kst = ZoneInfo("Asia/Seoul")
        self._active_tasks: Dict[int, asyncio.Task] = {}
    
    async def initialize(self):
        """초기화 및 텔레그램 봇 연결"""
        await self.telegram_bot.initialize()
        logger.info("✅ Economic Watcher initialized")
    
    async def schedule_todays_events(self):
        """
        매일 실행: 오늘의 ★★★ 일정을 로드하고 스나이퍼 예약
        
        스케줄러에서 매일 00:00에 호출
        """
        logger.info("📅 Scheduling today's economic events...")
        
        # 1. 캘린더에서 오늘 일정 수집
        events = await self.calendar_fetcher.fetch_todays_events()
        
        # 2. DB에 저장
        await self.calendar_fetcher.save_events_to_db(events)
        
        # 3. 미처리 이벤트 조회
        async with DatabaseSession() as session:
            unprocessed = await session.execute(
                select(EconomicEvent).where(
                    and_(
                        EconomicEvent.is_processed == False,
                        EconomicEvent.event_time >= datetime.now(self.tz_kst),
                        EconomicEvent.importance >= 3  # ★★★만
                    )
                ).order_by(EconomicEvent.event_time)
            )
            events_to_schedule = unprocessed.scalars().all()
        
        # 4. 각 이벤트에 대해 스나이퍼 태스크 생성
        for event in events_to_schedule:
            wait_seconds = (event.event_time - datetime.now(self.tz_kst)).total_seconds()
            
            if wait_seconds > 0:
                logger.info(
                    f"⏰ Sniper scheduled: {event.event_name} "
                    f"({wait_seconds:.0f}초 후, {event.event_time.strftime('%H:%M:%S')})"
                )
                
                # 비동기 태스크 생성
                task = asyncio.create_task(
                    self._sniper_execution(event.id, wait_seconds)
                )
                self._active_tasks[event.id] = task
        
        logger.info(f"✅ Scheduled {len(events_to_schedule)} sniper tasks")
    
    async def _sniper_execution(self, event_id: int, wait_seconds: float):
        """
        스나이퍼 실행: 발표 시간까지 대기 후 Actual 수집
        
        Args:
            event_id: 이벤트 ID
            wait_seconds: 발표까지 남은 시간 (초)
        """
        try:
            # 1. 발표 시간 + 10초까지 대기
            total_wait = wait_seconds + self.SNIPER_DELAY_SECONDS
            logger.info(f"💤 Sniper sleeping for {total_wait:.0f} seconds (event_id={event_id})")
            await asyncio.sleep(total_wait)
            
            # 2. 이벤트 정보 조회
            async with DatabaseSession() as session:
                event = await session.get(EconomicEvent, event_id)
                if not event:
                    logger.error(f"❌ Event not found: {event_id}")
                    return
                
                logger.info(f"🔫 Sniper triggered: {event.event_name}")
                
                # 3. Actual 값 수집 (재시도 로직)
                actual_data = None
                for attempt in range(self.MAX_FETCH_ATTEMPTS):
                    actual_data = await self._fetch_actual_value(event)
                    
                    if actual_data and actual_data.get('actual'):
                        logger.info(f"✅ Actual fetched: {actual_data['actual']}")
                        break
                    
                    logger.warning(f"⚠️ Attempt {attempt + 1} failed, retrying in {self.RETRY_INTERVAL}s...")
                    await asyncio.sleep(self.RETRY_INTERVAL)
                
                if not actual_data or not actual_data.get('actual'):
                    logger.error(f"❌ Failed to fetch actual after {self.MAX_FETCH_ATTEMPTS} attempts")
                    event.fetch_attempts = self.MAX_FETCH_ATTEMPTS
                    await session.commit()
                    return
                
                # 4. Surprise 분석
                analysis = self._analyze_surprise(event, actual_data)
                
                # 5. DB 업데이트
                event.actual = actual_data['actual']
                event.surprise_pct = analysis['surprise_pct']
                event.impact_direction = analysis['direction']
                event.impact_score = analysis['score']
                event.is_processed = True
                event.processed_at = datetime.now(self.tz_kst)
                
                await session.commit()
                
                # 6. 히스토리 저장
                history = EconomicEventHistory(
                    event_name=event.event_name,
                    event_time=event.event_time,
                    forecast=event.forecast,
                    actual=event.actual,
                    previous=event.previous,
                    surprise_pct=analysis['surprise_pct']
                )
                session.add(history)
                await session.commit()
                
                # 7. 텔레그램 알림
                await self._send_alert(event, analysis)
                
                logger.info(
                    f"✅ Event processed: {event.event_name} | "
                    f"Actual: {event.actual} | "
                    f"Surprise: {analysis['surprise_pct']:.1f}% | "
                    f"Impact: {analysis['direction']}"
                )
                
        except asyncio.CancelledError:
            logger.info(f"🛑 Sniper cancelled: event_id={event_id}")
        except Exception as e:
            logger.error(f"❌ Sniper error: {e}")
        finally:
            # 태스크 정리
            if event_id in self._active_tasks:
                del self._active_tasks[event_id]
    
    async def _fetch_actual_value(self, event: EconomicEvent) -> Optional[Dict]:
        """
        Actual 값 수집
        
        여러 소스에서 시도:
        1. Investing.com 실시간 크롤링
        2. FMP API (백업)
        """
        # 1차: Investing.com
        actual = await self._fetch_from_investing(event)
        if actual:
            return actual
        
        # 2차: FMP API (설정된 경우)
        # actual = await self._fetch_from_fmp(event)
        # if actual:
        #     return actual
        
        return None
    
    async def _fetch_from_investing(self, event: EconomicEvent) -> Optional[Dict]:
        """Investing.com에서 Actual 수집"""
        # 실제 구현 필요 - 페이지 재크롤링하여 actual 값 추출
        # TODO: Investing.com 페이지의 actual 셀 파싱
        pass
    
    def _analyze_surprise(self, event: EconomicEvent, actual_data: Dict) -> Dict:
        """
        Surprise 분석
        
        Returns:
            {
                'surprise_pct': float,  # 괴리율
                'direction': str,       # Bullish/Bearish/Neutral
                'score': int            # 영향도 점수 (0-100)
            }
        """
        try:
            # 수치 파싱 (%, K, M 등 단위 처리)
            forecast = self._parse_value(event.forecast)
            actual = self._parse_value(actual_data['actual'])
            
            if forecast is None or actual is None:
                return {'surprise_pct': 0, 'direction': 'Neutral', 'score': 20}
            
            # Surprise 계산
            if forecast != 0:
                surprise_pct = ((actual - forecast) / abs(forecast)) * 100
            else:
                surprise_pct = 0
            
            # 방향 판정 (지표별 해석 다름)
            direction = self._determine_direction(event.category, surprise_pct)
            
            # 영향도 점수 (0-100)
            score = self._calculate_impact_score(abs(surprise_pct), event.importance)
            
            return {
                'surprise_pct': surprise_pct,
                'direction': direction,
                'score': score
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing surprise: {e}")
            return {'surprise_pct': 0, 'direction': 'Neutral', 'score': 20}
    
    def _parse_value(self, value_str: str) -> Optional[float]:
        """문자열에서 숫자 추출"""
        if not value_str:
            return None
        
        try:
            # 단위 제거 및 변환
            clean = value_str.strip()
            clean = clean.replace('%', '').replace(',', '')
            clean = clean.replace('K', '000').replace('M', '000000')
            clean = clean.replace('B', '000000000')
            return float(clean)
        except:
            return None
    
    def _determine_direction(self, category: str, surprise_pct: float) -> str:
        """
        카테고리별 영향 방향 판정
        
        - GDP 상회 → Bullish
        - 실업수당 하회 → Bullish (경기 좋음)
        - CPI/PCE 상회 → Bearish (인플레이션 우려)
        """
        # 절대값이 작으면 Neutral
        if abs(surprise_pct) < 2:
            return 'Neutral'
        
        # 카테고리별 해석
        if category in ['GDP', 'Employment', 'PMI']:
            # 높으면 좋음
            return 'Bullish' if surprise_pct > 0 else 'Bearish'
        
        elif category in ['Inflation']:
            # 높으면 나쁨 (인플레이션 우려)
            return 'Bearish' if surprise_pct > 0 else 'Bullish'
        
        elif category == 'Employment' and '실업' in str(category):
            # 실업수당 청구건수: 낮으면 좋음
            return 'Bullish' if surprise_pct < 0 else 'Bearish'
        
        else:
            # 기본: 절대값 기준
            return 'High Volatility'
    
    def _calculate_impact_score(self, abs_surprise: float, importance: int) -> int:
        """
        영향도 점수 계산 (0-100)
        
        | Surprise | Score |
        |----------|-------|
        | > 20%    | 90    |
        | 10-20%   | 70    |
        | 5-10%    | 50    |
        | 2-5%     | 30    |
        | < 2%     | 10    |
        
        + 중요도 가중치 (★★★ = 1.0, ★★ = 0.7, ★ = 0.4)
        """
        if abs_surprise > 20:
            base_score = 90
        elif abs_surprise > 10:
            base_score = 70
        elif abs_surprise > 5:
            base_score = 50
        elif abs_surprise > 2:
            base_score = 30
        else:
            base_score = 10
        
        # 중요도 가중치
        importance_weight = {3: 1.0, 2: 0.7, 1: 0.4}.get(importance, 0.5)
        
        return int(base_score * importance_weight)
    
    async def _send_alert(self, event: EconomicEvent, analysis: Dict):
        """텔레그램 알림 전송"""
        # 영향도 이모지
        if analysis['direction'] == 'Bullish':
            emoji = "📈"
            impact_emoji = "🟢"
        elif analysis['direction'] == 'Bearish':
            emoji = "📉"
            impact_emoji = "🔴"
        else:
            emoji = "📊"
            impact_emoji = "🟡"
        
        # 메시지 생성
        message = f"""
⚡ *Economic Data Alert* {emoji}

*{event.event_name}*
🕐 {event.event_time.strftime('%H:%M')} KST

📊 *결과*
• 예상: {event.forecast or 'N/A'}
• 실제: {event.actual}
• 이전: {event.previous or 'N/A'}

{impact_emoji} *분석*
• Surprise: {analysis['surprise_pct']:+.1f}%
• 영향: {analysis['direction']}
• 점수: {analysis['score']}/100

💡 *해석*
{self._generate_interpretation(event, analysis)}
"""
        
        await self.telegram_bot.bot.send_message(
            chat_id=self.telegram_bot.chat_id,
            text=message,
            parse_mode='Markdown'
        )
    
    def _generate_interpretation(self, event: EconomicEvent, analysis: Dict) -> str:
        """간단한 해석 생성"""
        if analysis['direction'] == 'Bullish':
            return "시장에 긍정적 신호. 위험자산 선호 강화 가능."
        elif analysis['direction'] == 'Bearish':
            return "시장에 부정적 신호. 변동성 확대 주의."
        else:
            return "예상 범위 내. 시장 영향 제한적."
    
    def cancel_all_tasks(self):
        """모든 스나이퍼 태스크 취소"""
        for task in self._active_tasks.values():
            task.cancel()
        self._active_tasks.clear()
        logger.info("🛑 All sniper tasks cancelled")


# 싱글톤
_economic_watcher = None

def get_economic_watcher() -> EconomicWatcher:
    global _economic_watcher
    if _economic_watcher is None:
        _economic_watcher = EconomicWatcher()
    return _economic_watcher
```

### 7.5 브리핑 통합 - 긴급 컨텍스트 주입

**프롬프트 추가 섹션**:

```python
ECONOMIC_CONTEXT_SECTION = """
═══════════════════════════════════════════════════════════════
[⚡ 긴급 경제 지표 업데이트]

다음은 최근 발표된 주요 경제 지표입니다.
예상치(Consensus)와 크게 다른 경우, 시장 분석의 최우선 근거로 사용하세요.

{economic_events}

※ Surprise가 ±5% 이상인 지표는 시장 방향에 즉각적 영향을 미칩니다.
═══════════════════════════════════════════════════════════════
"""

# 예시 출력
"""
[⚡ 긴급 경제 지표 업데이트]

1) 미국 3분기 실질 GDP ★★★
   - 예상: 4.3%
   - 실제: 3.5% (▼ -18.6% 하회)
   - 영향: 📉 Bearish (경기 둔화 우려)

2) 신규실업수당청구건수 ★★★
   - 예상: 209K
   - 실제: 198K (▼ -5.3% 하회)
   - 영향: 📈 Bullish (고용 시장 견고)

3) 11월 PCE 가격지수 ★★★
   - 예상: 2.8%
   - 실제: 2.9% (▲ +3.6% 상회)
   - 영향: 📉 Bearish (인플레이션 우려)

=> 종합: GDP 둔화 + PCE 상승 → 스태그플레이션 우려 부각
"""
```

### 7.6 스케줄러 통합

**파일**: `backend/automation/dynamic_scheduler.py` (수정)

```python
# 기존 스케줄러에 Economic Watcher 추가

class DynamicBriefingScheduler:
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
        self.tz_manager = get_timezone_manager()
        self.economic_watcher = get_economic_watcher()  # 추가
        self._jobs = {}
    
    def setup_schedules(self):
        """모든 스케줄 설정"""
        # ... 기존 브리핑 스케줄 ...
        
        # 🆕 Economic Watcher 스케줄 추가
        # 매일 00:00에 오늘의 경제 일정 로드 및 스나이퍼 예약
        self._add_job(
            "economic_calendar_load",
            self._load_economic_calendar,
            "00:05",  # 00:05 (여유 있게)
            "mon-sun"
        )
        
        logger.info("✅ Economic Watcher scheduled")
    
    async def _load_economic_calendar(self):
        """매일 경제 캘린더 로드 및 스나이퍼 스케줄링"""
        await self.economic_watcher.schedule_todays_events()
```

### 7.7 환경 변수 추가

**.env 추가**:
```env
# Economic Calendar Settings
ECONOMIC_CALENDAR_ENABLED=true
ECONOMIC_SNIPER_DELAY_SECONDS=10
ECONOMIC_MAX_FETCH_ATTEMPTS=3
ECONOMIC_RETRY_INTERVAL=5

# Data Sources
INVESTING_CALENDAR_URL=https://kr.investing.com/economic-calendar/
FMP_API_KEY=your_fmp_api_key  # 선택적 (백업용)

# Alert Settings
ECONOMIC_ALERT_MIN_IMPORTANCE=3  # ★★★만 알림
ECONOMIC_ALERT_MIN_SURPRISE=5    # 5% 이상 괴리 시에만 알림
```

---

## 8. 브리핑 프롬프트 전문

### 8.1 프리마켓 브리핑 (경제지표 포함)

```python
PREMARKET_BRIEFING_PROMPT = """
당신은 월가 트레이더를 위한 프리마켓 애널리스트입니다.
미국장 시작 전, 오늘 밤 주목해야 할 내용을 빠르게 정리하세요.

═══════════════════════════════════════════════════════════════
[입력: Ollama 전처리 RSS (최근 6시간)]
{preprocessed_rss_data}

[입력: 보유 포트폴리오 (KIS API)]
{portfolio_data}

[⚡ 긴급 경제 지표 업데이트]
{economic_events_context}
═══════════════════════════════════════════════════════════════

### 🔍 심층 검토 지침

1. **경제 지표 분석 (최우선)**
   - 방금 발표된 지표가 예상과 크게 다른가?
   - 시장에 미치는 영향은?
   - Bullish/Bearish 시그널 판단

2. **속보 및 핫이슈**
   - 검색: "breaking news stocks", "market moving news"

3. **프리마켓 동향**
   - 검색: "premarket movers", "futures now"

4. **오늘 밤 추가 일정**
   - 아직 발표 안 된 경제 지표
   - 실적 발표 예정

═══════════════════════════════════════════════════════════════

### 📋 출력 형식

## 🌙 Pre-Market Briefing ({current_date})
> [오늘 밤 시장 핵심 한 문장 - 경제지표 결과 반영]

## ⚡ Economic Data Flash
| 지표 | 예상 | 실제 | Surprise | 영향 |
|------|------|------|----------|------|
| GDP | | | | 📈/📉 |
| PCE | | | | 📈/📉 |
| ... | | | | |

**시장 해석**: [경제지표 종합 분석 2-3문장]

## 🔴 Tonight's Hot Issues (Top 3)
(기존 형식 유지)

## 📊 Pre-Market Snapshot
(기존 형식 유지)

## 🎯 Trading Setup
> 경제지표 결과를 반영한 오늘 밤 시나리오
"""
```

---

## 9~11. 텔레그램/KIS API/주간 리포트

**(v2.1과 동일 - 생략)**

---

## 12. 검증 체크리스트

### Phase 3.5 검증: Economic Watcher (NEW)

- [ ] **DB 테이블**
  - [ ] `economic_events` 테이블 생성 확인
  - [ ] `economic_event_history` 테이블 생성 확인
  - [ ] 인덱스 정상 생성

- [ ] **캘린더 수집**
  - [ ] Investing.com 크롤링 정상 동작
  - [ ] ★★★ 이벤트만 필터링
  - [ ] DB 저장 확인

- [ ] **스나이퍼 스케줄링**
  - [ ] 매일 00:05 캘린더 로드
  - [ ] 이벤트별 asyncio.Task 생성
  - [ ] 발표 시간 +10초에 트리거

- [ ] **Actual 수집**
  - [ ] 재시도 로직 (3회, 5초 간격)
  - [ ] 수집 성공률 > 90%

- [ ] **Surprise 분석**
  - [ ] 괴리율 계산 정확
  - [ ] 방향 판정 (Bullish/Bearish/Neutral)
  - [ ] 영향도 점수 (0-100)

- [ ] **알림 및 통합**
  - [ ] 텔레그램 즉시 알림
  - [ ] 브리핑 Context 주입
  - [ ] 히스토리 저장

---

## 13. 완료 기준

| 항목 | 상태 | 설명 |
|------|------|------|
| **DB** | ✅ | NewsArticle + EconomicEvent 테이블 |
| **Ollama** | ✅ | 24시간 5분 간격 전처리 |
| **🆕 Economic Watcher** | ✅ | 발표 10초 후 Actual 수집 |
| **서머타임** | ✅ | 자동 감지 및 스케줄 조정 |
| **프리마켓 브리핑** | ✅ | 경제지표 결과 포함 |
| **장중 체크포인트** | ✅ | 01:00/03:00 (변동 시) |
| **미국 마감 브리핑** | ✅ | 경제지표 영향 분석 포함 |
| **국내 오픈 브리핑** | ✅ | US→KR 연결 |
| **주간 리포트** | ✅ | 토/일 생성 + 시스템 분석 |
| **텔레그램** | ✅ | 브리핑 + 속보 + 경제지표 알림 |
| **KIS API** | ✅ | 포트폴리오 연동 |

---

## 📝 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2026-01-22 | v2.0 | 초기 통합 계획서 |
| 2026-01-22 | v2.1 | 프리마켓, 서머타임, 텔레그램, KIS API, 주간 리포트 |
| 2026-01-22 | v2.2 | **Real-time Economic Watcher 추가** |

---

**End of Implementation Plan v2.2 Final**
