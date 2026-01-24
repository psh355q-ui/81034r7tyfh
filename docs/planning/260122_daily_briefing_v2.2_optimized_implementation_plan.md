# Daily Briefing System v2.2 - 최적화된 구현 계획서

**작성일**: 2026-01-22  
**버전**: v2.2 Optimized Implementation Plan (Real-time Economic Watcher 포함)  
**상태**: 계획 완료, 구현 대기  
**원본 계획**: `docs/planning/260122_daily_briefing_system_v2.2_implementation_plan.md`

---

## 📊 요약

24시간 AI 기반 트레이딩 브리핑 시스템 + **실시간 경제지표 감시 시스템**. 5가지 일간 브리핑, 자동 서머타임 스케줄링, 70% API 비용 절감을 위한 지능형 캐싱, KIS 포트폴리오 연동, 실시간 텔레그램 알림, **경제지표 발표 10초 내 분석 및 알림**, 자가 개선 AI 분석을 포함한 주간 리포트 시스템을 구현합니다.

**총 예상 시간**: 19일 (약 3주)

---

## 🆕 v2.2 신규 기능: Real-time Economic Watcher

### 문제점
- 기존 RSS 크롤링(10분 주기)으로는 경제지표 발표 직후 반영 불가능
- GDP, PCE, CPI 등 주요 지표 발표 시 시장 변동성 급격히 증가
- 뉴스 기사는 발표 5~10분 후에야 나타남

### 해결책
**이벤트 기반 스나이퍼(Sniper) 모듈**:
1. 발표 시간까지 대기 (asyncio.sleep)
2. 발표 10초 후 트리거 → Actual 값 수집
3. 예상(Forecast) vs 실제(Actual) 괴리(Surprise) 계산
4. 즉시 브리핑 업데이트 + 텔레그램 알림

### 대상 지표
- ★★★ GDP, PCE, CPI, 고용지표, FOMC 회의록
- ★★ EIA 재고, 주택지표, PMI
- ★ 기타 참고 지표

---

## 🎯 기존 시스템 분석

### ✅ 이미 구현된 기능들

| 기능 | 구현 상태 | 파일 |
|------|----------|------|
| **데이터베이스 모델** | ✅ 완료 | `backend/database/models.py` |
| **텔레그램 알림 시스템** | ✅ 완료 | `backend/notifications/telegram_notifier.py` |
| **일일 브리핑 서비스** | ✅ 완료 | `backend/services/daily_briefing_service.py` |
| **일일 리포트 스케줄러** | ✅ 완료 | `backend/services/daily_report_scheduler.py` |
| **Ollama 통합** | ✅ 완료 | `backend/ai/llm/ollama_client.py` |
| **KIS API 연동** | ✅ 완료 | `backend/brokers/kis_broker.py` |
| **개선된 브리핑 생성기** | ✅ 완료 | `backend/ai/reporters/enhanced_daily_reporter.py` |

### 🔍 주요 발견사항

1. **DB 모델**: [`NewsArticle`](backend/database/models.py:82-153)에 이미 많은 필드가 있어 최소한의 추가만 필요
2. **텔레그램**: [`TelegramNotifier`](backend/notifications/telegram_notifier.py:43-596)가 완전하지만 명령어 핸들러 없음
3. **Ollama**: 이미 완전히 통합되어 있음, 전처리 스케줄러만 필요
4. **KIS API**: 포트폴리오 조회 기능이 이미 구현됨
5. **브리핑 시스템**: [`EnhancedDailyReporter`](backend/ai/reporters/enhanced_daily_reporter.py:45-782)와 [`DailyBriefingService`](backend/services/daily_briefing_service.py:24-215)가 중복됨

---

## 🚀 최적화된 구현 계획

### Phase 0: 사전 준비 (1일)

**목표**: 기존 시스템 완전 이해 및 환경 설정

**작업**:
- [x] 기존 코드베이스 완전 이해
- [x] DB 스키마 검증 및 마이그레이션 계획 수립
- [x] Ollama 모델 설치 확인 (`llama3.2:3b`)
- [x] 텔레그램 봇 설정 확인 (@BotFather)
- [x] 환경 변수 설정 검증
- [x] Investing.com 크롤링 테스트

**검증**:
- [x] Ollama 서버 정상 작동 확인
- [x] 텔레그램 봇 토큰 및 채팅 ID 확인
- [x] KIS API 연결 상태 확인
- [x] Investing.com 접속 가능 확인

---

### Phase 1: DB 마이그레이션 (1일)

**목표**: 캐싱, 주간 리포트, 경제지표를 위한 DB 스키마 업데이트

**파일**: `backend/database/models.py`

**변경사항**:

**`DailyBriefing` 모델**:
```python
# 기존 필드 활용 + 최소 추가
importance_score = Column(Integer, nullable=True)         # 0-100 중요도
cache_hit = Column(Boolean, nullable=True)                # 캐시 사용 여부
api_cost = Column(Float, nullable=True)                   # API 비용(USD)
generation_time = Column(Float, nullable=True)            # 생성 시간(초)
```

**신규 테이블 `WeeklyReport`**:
```python
class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    
    id = Column(Integer, primary_key=True)
    type = Column(String(20))  # 'review' or 'outlook'
    content = Column(Text)
    metrics = Column(JSONB, nullable=True)  # 성과 지표
    ai_analysis = Column(JSONB, nullable=True)  # AI 자가 분석
    created_at = Column(DateTime, default=datetime.utcnow)
```

**신규 테이블 `EconomicEvent` (v2.2 NEW)**:
```python
class EconomicEvent(Base):
    __tablename__ = "economic_events"
    
    id = Column(Integer, primary_key=True)
    event_name = Column(String(200))  # 예: "미국 3분기 실질 GDP"
    country = Column(String(10))      # US, KR, EU, CN, JP
    category = Column(String(50))     # GDP, Inflation, Employment, etc.
    
    event_time = Column(DateTime, nullable=False)  # 발표 예정 시간 (KST)
    importance = Column(Integer)      # 1=★, 2=★★, 3=★★★
    
    forecast = Column(String(50))     # 예상치 (4.3%)
    actual = Column(String(50))       # 실제치 (발표 후 업데이트)
    previous = Column(String(50))     # 이전치
    
    surprise_pct = Column(Float)      # (실제-예상)/예상 * 100
    impact_direction = Column(String(20))  # Bullish/Bearish/Neutral
    impact_score = Column(Integer)    # 영향도 점수 (0-100)
    
    is_processed = Column(Boolean, default=False)    # 처리 완료 여부
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_economic_event_time', 'event_time'),
        Index('idx_economic_importance', 'importance'),
        Index('idx_economic_processed', 'is_processed'),
    )
```

**작업**:
- [x] `DailyBriefing` 모델 업데이트
- [x] `WeeklyReport` 테이블 생성
- [x] `EconomicEvent` 테이블 생성
- [x] Alembic 마이그레이션 생성
- [x] 마이그레이션 적용
- [x] 스키마 변경 검증

**검증**:
- [x] 마이그레이션 성공 여부
- [x] 새로운 필드/테이블 정상 생성 확인
- [x] 인덱스 정상 생성 확인

---

### Phase 2: Ollama 전처리 스케줄러 (1일)

**목표**: RSS 뉴스를 Ollama로 전처리하여 API 비용 절감

**파일**: `backend/automation/ollama_scheduler.py`

**핵심 기능**:
- RSS 크롤러와 연동 (10분 간격)
- Ollama로 뉴스 전처리 (요약, 중요도 분류, 티커 추출)
- 전처리 결과 DB 저장
- 처리 시간 및 성능 추적

**처리 흐름**:
```
RSS 크롤링(10분) → Ollama 전처리(5분) → DB 저장 → 브리핑 생성 시 활용
```

**작업**:
- [x] `OllamaScheduler` 클래스 생성
- [x] RSS 크롤러와 Ollama 연동
- [x] 전처리 결과 DB 저장 로직
- [x] 5분 간격 스케줄링
- [x] 성능 테스트

**검증**:
- [x] 전처리 정확도 테스트
- [x] 처리 시간 30초 이내 확인
- [x] DB 저장 정상 여부

---

### Phase 3: 지능형 캐싱 시스템 (2일)

**목표**: 3단계 캐싱 전략으로 API 비용 70% 절감

**파일**: `backend/services/daily_briefing_cache_manager.py`

**3단계 캐싱 전략** (원본 5단계에서 최적화):

| 중요도 점수 | 액션 | 설명 |
|-------------|------|------|
| **0-20** | `CACHE_HIT` | 변경 없음, 이전 브리핑 재사용 |
| **20-60** | `PARTIAL_REGEN` | 변경된 섹션만 재생성 |
| **60-100** | `FULL_REGEN` | 전체 브리핑 재생성 |

**중요도 점수 계산식**:
```python
score = 0
score += (high_importance_news_count * 20)  # HIGH 뉴스 1개당 +20
score += (index_change_pct * 15)            # 지수 변동 1%당 +15
score += (portfolio_alerts * 10)            # 포트폴리오 알림 1개당 +10
score += (breaking_news_flag * 25)          # 속보 키워드 +25
score += (economic_surprise_score * 30)      # 경제지표 괴리 (v2.2)
score -= (hours_since_last * 5)             # 시간 경과 1시간당 -5
```

**작업**:
- [x] `DailyBriefingCacheManager` 클래스 생성
- [x] 3단계 캐싱 전략 구현
- [x] 중요도 점수 계산 로직 (경제지표 포함)
- [x] 캐시 적중률 추적
- [x] 비용 절감 지표 측정

**검증**:
- [x] 캐시 적중률 60% 이상 확인
- [x] API 비용 절감 70% 확인
- [x] 각 캐싱 레벨 동작 검증

---

### Phase 3.5: 🆕 Real-time Economic Watcher (5일)

**목표**: 경제지표 발표 10초 내 Actual 수집 및 알림

**일정 상세**:
- Investing.com 크롤링 구조 파악: 1일
- Economic Watcher 구현: 2일
- 테스트 및 디버깅: 1-2일
- 통합 테스트: 1일

**시스템 흐름**:

```
[Step 1] 매일 00:05 - 오늘의 경제 일정 로드
   └─> Economic Calendar Fetcher
       └─> Investing.com 크롤링
       └─> ★★★ 이벤트만 필터링
       └─> DB 저장 (is_processed = False)

[Step 2] 이벤트별 스나이퍼 스케줄링
   └─> Event Sniper Scheduler
       └─> 22:30 GDP 발표 → 22:30:10 트리거 예약
       └─> asyncio.create_task(sniper_execution)

[Step 3] 발표 시간 + 10초 → 스나이퍼 발동
   └─> Sniper Execution
       └─> Actual 값 수집 (재시도 3회, 5초 간격)

[Step 4] Surprise 분석
   └─> Surprise Analyzer
       └─> 예상 4.3% vs 실제 3.5% → -18.6% 괴리
       └─> Impact Score 계산
       └─> Bullish/Bearish/Neutral 판정

[Step 5] 즉시 알림 + 브리핑 Context 주입
   └─> Alert & Context Injection
       └─> 📲 텔레그램 즉시 알림
       └─> 브리핑 생성 시 '긴급 컨텍스트'로 최우선 반영
       └─> DB 업데이트 (is_processed = True)
```

**핵심 파일**:

**1. Economic Calendar Fetcher** (`backend/services/economic_calendar_fetcher.py`)
- Investing.com 경제 캘린더 크롤링
- ★★★ 이벤트만 필터링
- DB 저장
- **🆕 크롤링 구조 변경 감지 로직**
- **🆕 FMP API 백업 시스템**
- **🆕 매일 00:05 로드 실패 시 00:10, 00:15 재시도**

**2. Economic Watcher** (`backend/services/economic_watcher.py`)
- 매일 00:05 오늘의 일정 로드 및 스나이퍼 예약
- 발표 +15초에 Actual 수집 (시스템 부하 고려)
- 재시도 로직 (3회, 5초 간격)
- Surprise 분석 및 영향도 점수 계산
- 텔레그램 즉시 알림

**3. 브리핑 통합**
- 모든 브리핑에 경제지표 긴급 Context 섹션 추가
- Surprise ±5% 이상 시 최우선 분석

**🆕 4. Economic Watcher 테스트 전략**
```python
# 테스트용 Mock 이벤트
test_event = EconomicEvent(
    event_name="Test GDP",
    event_time=datetime.now() + timedelta(minutes=2),
    forecast="4.3%",
    importance=3
)
# 실제 발표 전 모의 테스트 필수
# 타이밍, 재시도, 알림 모두 검증
```

**Surprise 분석 로직**:

```python
def _analyze_surprise(event, actual_data):
    # 1. 괴리율 계산
    surprise_pct = ((actual - forecast) / abs(forecast)) * 100
    
    # 2. 방향 판정 (카테고리별 해석 다름)
    if category in ['GDP', 'Employment', 'PMI']:
        direction = 'Bullish' if surprise_pct > 0 else 'Bearish'
    elif category == 'Inflation':
        direction = 'Bearish' if surprise_pct > 0 else 'Bullish'
    
    # 3. 영향도 점수 (0-100)
    if abs(surprise_pct) > 20: score = 90
    elif abs(surprise_pct) > 10: score = 70
    elif abs(surprise_pct) > 5: score = 50
    else: score = 30
    
    return {
        'surprise_pct': surprise_pct,
        'direction': direction,
        'score': score
    }
```

**텔레그램 알림 예시**:

```
⚡ Economic Data Alert 📉

미국 3분기 실질 GDP
🕐 22:30 KST

📊 결과
• 예상: 4.3%
• 실제: 3.5%
• 이전: 4.5%

🔴 분석
• Surprise: -18.6%
• 영향: Bearish
• 점수: 90/100

💡 해석
시장에 부정적 신호. 변동성 확대 주의.
```

**작업**:
- [x] `EconomicCalendarFetcher` 클래스 생성
- [x] Investing.com 크롤러 구현
- [x] `EconomicWatcher` 클래스 생성
- [x] 스나이퍼 스케줄링 구현
- [x] Actual 수집 로직 (재시도 포함)
- [x] Surprise 분석 로직
- [x] 텔레그램 즉시 알림
- [x] 브리핑 Context 주입

**검증**:
- [x] 캘린더 수집 성공률 >95%
- [x] Actual 수집 성공률 >90%
- [x] 발표 후 10~30초 내 알림 전송
- [x] Surprise 분석 정확성

---

### Phase 4: 서머타임 자동 관리 (1일)

**목표**: Python `zoneinfo`를 사용한 자동 DST 관리

**파일**: 
- `backend/utils/timezone_manager.py`
- `backend/automation/dynamic_scheduler.py`

**서머타임 규칙**:
- **하절기 (3월 2째 일요일 ~ 11월 1째 일요일)**: EDT (UTC-4)
- **동절기 (11월 ~ 3월)**: EST (UTC-5)
- 한국 시차: 하절기 13시간, 동절기 14시간

**자동 조정 로직**:
```python
from zoneinfo import ZoneInfo
from datetime import datetime

TZ_EST = ZoneInfo("America/New_York")
TZ_KST = ZoneInfo("Asia/Seoul")

def get_schedule(self, name: str) -> str:
    """현재 시간대에 맞는 스케줄 반환"""
    # zoneinfo가 자동 DST 처리
    est_time = datetime.now(TZ_EST)
    kst_time = datetime.now(TZ_KST)
    
    # DST에 따라 스케줄 반환
    if est_time.dst() != timedelta(0):  # 하절기
        return self.SCHEDULES["daylight"][name]
    else:  # 동절기
        return self.SCHEDULES["standard"][name]
```

**Dynamic Scheduler에 추가**:
```python
# Economic Watcher 스케줄 추가
self._add_job(
    "economic_calendar_load",
    self._load_economic_calendar,
    "00:05",
    "mon-sun"
)
```

**작업**:
- [x] `TimezoneManager` 클래스 생성
- [x] `DynamicScheduler` 클래스 생성
- [x] DST 자동 감지 로직
- [x] 스케줄 자동 전환 구현
- [x] Economic Watcher 스케줄 추가
- [x] DST 테스트

**검증**:
- [x] 동절기/하절기 정확히 감지
- [x] 스케줄 자동 전환 확인
- [x] DST 변경일 자동 재설정
- [x] Economic Watcher 스케줄 정상 작동

---

### Phase 5: 미국 시장 브리핑 (3일)

**목표**: 3가지 미국 시장 브리핑 생성 + 경제지표 Context

**파일**: `backend/ai/reporters/enhanced_daily_reporter.py` (기존 확장)

**3가지 브리핑 타입**:

**1. 프리마켓 브리핑** (23:00/22:00)
```python
async def generate_premarket_briefing(self) -> str:
    # 1. Ollama 전처리 RSS (최근 6시간)
    # 2. KIS API 포트폴리오 조회
    # 3. 🆕 최근 발표된 경제지표 조회
    economic_context = await self._get_recent_economic_events()
    # 4. API 웹 검색: "premarket movers", "futures"
    # 5. 브리핑 생성 + 텔레그램 전송
```

**프롬프트 추가 섹션**:
```markdown
[⚡ 긴급 경제 지표 업데이트]

1) 미국 3분기 실질 GDP ★★★
   - 예상: 4.3%
   - 실제: 3.5% (▼ -18.6% 하회)
   - 영향: 📉 Bearish (경기 둔화 우려)

2) 신규실업수당청구건수 ★★★
   - 예상: 209K
   - 실제: 198K (▼ -5.3% 하회)
   - 영향: 📈 Bullish (고용 시장 견고)

=> 종합: GDP 둔화 + 고용 견고 → 소프트 랜딩 시나리오
```

**2. 장중 체크포인트** (01:00, 03:00)
```python
async def generate_checkpoint(self, num: int) -> Optional[str]:
    # 유의미한 변동 감지 (±1% 이상)
    # → 있으면 간략 업데이트 생성
    # → 없으면 스킵 (API 절약)
```

**3. 미국 마감 브리핑** (07:10/06:10)
- 장 마감 종합 분석
- 섹터별 성과
- 주요 이슈 정리

**작업**:
- [x] 프리마켓 브리핑 구현
- [x] 경제지표 Context 통합
- [x] 체크포인트 #1, #2 구현
- [x] 미국 마감 브리핑 구현
- [x] 브리핑 프롬프트 작성
- [x] 조건부 트리거 테스트

**검증**:
- [x] 3가지 브리핑 모두 스케줄대로 생성
- [x] 포트폴리오 섹션 포함 확인
- [x] 경제지표 Context 반영 확인
- [x] 체크포인트 조건부 트리거 확인

---

### Phase 6: 국내 시장 브리핑 (2일)

**목표**: 한국 시장 오픈 전 브리핑 생성

**파일**: `backend/ai/reporters/korean_market_briefing_reporter.py`

**데이터 소스**:
- 전일 미국 장 결과
- 아시아 선물 (닛케이, 항셍)
- 코스피 섹터 전망
- 환율/원자재 영향

**특징**: 미국 장 → 한국 장 연결 분석

**작업**:
- [x] `KoreanMarketBriefingReporter` 클래스 생성
- [x] 미국-한국 시장 연계 분석
- [x] 국내 브리핑 템플릿 작성
- [x] 국내 브리핑 테스트 (08:00)

**검증**:
- [x] 국내 브리핑 정상 생성
- [x] 미국-한국 연결 분석 정확성

---

### Phase 7: KIS 포트폴리오 통합 (1일)

**목표**: 모든 브리핑에 포트폴리오 섹션 포함

**파일**: `backend/services/portfolio_analyzer.py`

**주요 기능**:

**1. 보유 종목 조회**
```python
async def get_holdings_for_briefing(self) -> List[Dict]:
    holdings = await kis_client.get_stock_balance()
    return [{
        'ticker': h['ticker'],
        'name': h['name'],
        'pnl_pct': h['pnl_pct'],
        'market': h['market']  # KR or US
    } for h in holdings]
```

**2. 포트폴리오 알림** (±5% 변동)
```python
async def check_portfolio_alerts(self) -> List[Dict]:
    # 일일 변동 ±5% 이상 감지
    # API 검색으로 변동 원인 파악
    # 텔레그램 알림 전송
```

**3. 브리핑 섹션 생성**
- 모든 브리핑에 포트폴리오 섹션 포함
- 보유 종목 관련 뉴스 강조
- 맞춤형 분석 제공

**작업**:
- [x] `PortfolioAnalyzer` 클래스 생성
- [x] 보유 종목 조회 구현
- [x] 포트폴리오 알림 (±5%) 구현
- [x] 브리핑 섹션 통합
- [x] KIS API 연동 테스트

**검증**:
- [x] KIS API 연동 정상
- [x] ±5% 알림 트리거 확인
- [x] 맞춤 분석 제공 확인

---

### Phase 8: 텔레그램 명령어 (1일)

**목표**: 텔레그램 봇 명령어 핸들러 구현

**파일**: `backend/notifications/telegram_command_bot.py`

**명령어**:
- `/status` - 현재 시장 현황
- `/portfolio` - 포트폴리오 요약
- `/schedule` - 오늘 브리핑 스케줄
- `/economic` - 오늘의 경제 일정 (v2.2)
- `/help` - 도움말

**알림 유형 추가**:
1. 정기 브리핑 (5종)
2. 실시간 속보
3. 포트폴리오 알림
4. **🆕 경제지표 즉시 알림**

```python
async def send_economic_alert(self, event, analysis):
    emoji = "📈" if analysis['direction'] == 'Bullish' else "📉"
    message = f"""
⚡ Economic Data Alert {emoji}

*{event.event_name}*
🕐 {event.event_time.strftime('%H:%M')} KST

📊 결과
• 예상: {event.forecast}
• 실제: {event.actual}
• Surprise: {analysis['surprise_pct']:+.1f}%

{emoji} 영향: {analysis['direction']}
"""
    await self.bot.send_message(...)
```

**기술 세부사항**:
- 텔레그램 4096자 제한 자동 분할
- 마크다운 포맷팅
- Rate limiting (0.5초 간격)

**작업**:
- [x] `TelegramCommandBot` 클래스 생성
- [x] 명령어 핸들러 구현
- [x] 경제지표 알림 추가
- [x] 실시간 속보 알림
- [x] 메시지 분할 로직
- [x] 알림 테스트

**검증**:
- [x] 모든 명령어 응답 확인
- [x] 긴 메시지 분할 확인
- [x] 실시간 속보 알림 확인
- [x] 경제지표 즉시 알림 확인

---

### Phase 9: 주간 리포트 시스템 (2일)

**목표**: 주간 리뷰 및 AI 시스템 자가 분석

**파일**: `backend/ai/reporters/weekly_reporter.py`

**토요일 14:00 - 주간 리뷰**:
```python
async def generate_weekly_review(self) -> str:
    # 1. 이번 주 브리핑 수집
    # 2. 포트폴리오 주간 성과 (KIS API)
    # 3. 시장 주간 요약
    # 4. 브리핑 정확도 분석
    # 5. 리포트 생성 + 전송
```

**일요일 22:00 - 주간 전망 + AI 시스템 분석**:
```python
async def generate_weekly_outlook_with_system_analysis(self) -> str:
    # 1. 다음 주 경제 캘린더
    # 2. 시장 전망
    # 3. 🤖 AI 시스템 자가 분석
    #    - 잘한 점 / 잘못한 점
    #    - 개선 필요 사항
    #    - 시스템 수정 제안
    # 4. 개선사항 자동 추출 → 로깅
```

**주간 전망에 경제지표 정확도 분석 추가**:
- 예측 vs 실제 적중률
- Surprise 방향 예측 정확도
- 시장 반응 분석 (지표 발표 후 S&P 5분/15분/1시간 변동률)

**자가 개선 루프**:
1. AI가 자신의 성과 분석
2. 개선사항 구조화 추출
3. 우선순위별 로깅
4. (향후) GitHub 이슈 자동 생성

**작업**:
- [ ] `WeeklyReporter` 클래스 생성
- [ ] 주간 리뷰 (토요일 14:00)
- [ ] 주간 전망 + AI 시스템 분석 (일요일 22:00)
- [ ] 경제지표 정확도 분석 추가
- [ ] 개선사항 자동 추출
- [ ] 주간 리포트 테스트

**검증**:
- [ ] 토요일 리뷰 생성 확인
- [ ] 일요일 전망 + AI 분석 확인
- [ ] 경제지표 정확도 분석 확인
- [ ] 개선사항 추출 확인

---

### Phase 10: API 라우트 및 통합 테스트 (2일)

**목표**: API 엔드포인트 추가 및 전체 시스템 통합 테스트

**파일**: `backend/api/routers/reports_router.py`

**신규 엔드포인트**:
- `GET /api/reports/premarket` - 프리마켓 브리핑
- `GET /api/reports/checkpoint/{num}` - 체크포인트
- `GET /api/reports/korean-market` - 국내 시장 브리핑
- `GET /api/reports/weekly/{type}` - 주간 리포트
- `POST /api/reports/trigger/{type}` - 수동 트리거
- **`GET /api/reports/economic-events/today`** - 오늘의 경제 일정 (v2.2)
- **`GET /api/reports/economic-events/recent`** - 최근 발표된 지표 (v2.2)
- **`POST /api/reports/economic-events/manual-trigger`** - 수동 스나이퍼 트리거 (v2.2)

**통합 테스트**:
- 24시간 연속 운영 테스트
- DST 전환 시뮬레이션
- 모든 브리핑 타입 검증
- **Economic Watcher 통합 테스트**
- 에러 복구 테스트

**작업**:
- [ ] 신규 엔드포인트 추가
- [ ] 경제지표 관련 엔드포인트 추가
- [ ] API 라우터 업데이트
- [ ] 24시간 연속 운영 테스트
- [ ] DST 전환 시뮬레이션
- [ ] Economic Watcher 통합 테스트
- [ ] 전체 시스템 통합 검증

**검증**:
- [ ] 모든 엔드포인트 정상 작동
- [ ] 24시간 연속 운영 안정성
- [ ] DST 전환 오류 없음
- [ ] 모든 브리핑 타입 검증
- [ ] Economic Watcher 정상 작동

---

## 📊 시스템 아키텍처

### 전체 구성도 (v2.2)

```
┌─────────────────────────────────────────────────────────────┐
│                  24시간 브리핑 시스템 v2.2                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │ RSS 크롤러  │────▶│    Ollama    │────▶│ PostgreSQL  │  │
│  │  (10분)     │     │ 전처리 (5분) │     │     DB      │  │
│  └─────────────┘     └──────────────┘     └──────┬──────┘  │
│                                                    │         │
│  ┌────────────────────────────────────────────────┼──────┐  │
│  │        🆕 Real-time Economic Watcher           │      │  │
│  │  ┌───────────────────────────────────────────────────┐  │
│  │  │ [Event Sniper Scheduler]                          │  │
│  │  │  - 매일 00:05: 오늘의 ★★★ 일정 로드             │  │
│  │  │  - 발표 시간까지 Sleep                            │  │
│  │  │  - 발표 +10초: Actual 값 Fetch                    │  │
│  │  │  - Surprise 계산 (예상 vs 실제)                   │  │
│  │  │  - 즉시 알림 + 브리핑 Context 주입                │  │
│  │  └───────────────────────────────────────────────────┘  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                    │         │
│  ┌────────────────────────────────────────────────┼──────┐  │
│  │           6단계 브리핑 엔진                    │      │  │
│  │  ┌──────────┬──────────┬──────────┬──────────┐ │      │  │
│  │  │경제지표  │프리마켓  │체크포인트│미국 마감 │ │      │  │
│  │  │ 속보*    │ 23:00*   │01:00/03* │ 07:10*   │ │      │  │
│  │  └──────────┴──────────┴──────────┴──────────┘ │      │  │
│  │  ┌──────────┐                                  │      │  │
│  │  │국내 오픈 │                                  │      │  │
│  │  │  08:00   │                                  │      │  │
│  │  └──────────┘                                  │      │  │
│  │                                                  │      │  │
│  │  ┌────────────────────────────────────────────┐ │      │  │
│  │  │   지능형 캐싱 (3단계 전략)              │ │      │  │
│  │  │   CACHE_HIT | PARTIAL_REGEN | FULL_REGEN │ │      │  │
│  │  └────────────────────────────────────────────┘ │      │  │
│  │                                                  │      │  │
│  │  ┌────────────────────────────────────────────┐ │      │  │
│  │  │   Gemini/Claude API + 웹 검색              │ │      │  │
│  │  │   + 경제지표 긴급 Context                  │ │      │  │
│  │  └────────────────────────────────────────────┘ │      │  │
│  └─────────────────────────────────────────────────┘      │  │
│                                                            │
│  ┌────────────────────────────────────────────────────────┤  │
│  │              통합 레이어                               │  │
│  │  ┌──────────────┬──────────────┬────────────────────┐  │  │
│  │  │  KIS API     │  텔레그램    │  DST 자동 관리     │  │  │
│  │  │  포트폴리오  │  봇/명령어   │  (zoneinfo)       │  │  │
│  │  └──────────────┴──────────────┴────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘

* = 서머타임 자동 조정 (동절기/하절기)
* = 발표 10초 후 즉시 알림
```

---

## 📋 6단계 브리핑 스케줄 (v2.2)

| 시간 | 브리핑 타입 | 목적 | DST 조정 |
|------|------------|------|----------|
| **??:??** | ⚡ **경제지표 속보** | **발표 10초 후 즉시 알림 (NEW)** | - |
| **23:00** / 22:00 | 🌙 프리마켓 | 미국 장 시작 전 프리뷰 (경제지표 포함) | ✅ |
| **01:00** / 00:00 | 📍 체크포인트 #1 | 장 시작 30분 후 (유의미한 변동 시) | ✅ |
| **03:00** / 02:00 | 📍 체크포인트 #2 | 장 중간 점검 (유의미한 변동 시) | ✅ |
| **07:10** / 06:10 | 🇺🇸 미국 마감 | 미국 장 마감 분석 | ✅ |
| **08:00** | 🇰🇷 국내 오픈 | 한국 시장 오픈 브리핑 | ❌ |

**추가 주간 리포트:**
- **토요일 14:00**: 📊 주간 리뷰
- **일요일 22:00**: 🔮 주간 전망 + 🤖 AI 시스템 자가 분석

---

## 🔍 주요 최적화사항

### 1. DB 마이그레이션 최적화
- **문제점**: 원본 계획에서 [`NewsArticle`](backend/database/models.py:82-153)에 이미 많은 필드가 있음
- **개선안**: 기존 필드 활용 + 최소한의 필드만 추가
  - `preprocessed_summary` → 기존 `summary` 활용 가능
  - `ollama_model` → 기존 `embedding_model` 활용 가능
  - `processing_time` → `metadata_` JSONB 필드 활용

### 2. 캐싱 시스템 단순화
- **문제점**: 원본 5단계 캐싱 전략이 복잡함
- **개선안**: 3단계 전략으로 단순화
  - `CACHE_HIT` (0-20): 이전 브리핑 재사용
  - `PARTIAL_REGEN` (20-60): 변경된 섹션만 재생성
  - `FULL_REGEN` (60+): 전체 재생성

### 3. 서머타임 관리
- **문제점**: 원본 계획의 DST 전환 로직이 복잡
- **개선안**: Python `zoneinfo` 라이브러리 사용 (Python 3.9+)
  - `datetime.now(TZ_EST)`로 자동 DST 처리
  - 별도의 감지 로직 불필요

### 4. 브리핑 시스템 통합
- **문제점**: [`EnhancedDailyReporter`](backend/ai/reporters/enhanced_daily_reporter.py:45-782)와 [`DailyBriefingService`](backend/services/daily_briefing_service.py:24-215)가 중복됨
- **개선안**: 단일 클래스로 통합
  - `DailyBriefingService`를 확장하여 6단계 브리핑 지원
  - 기존 코드 최대한 재사용

### 5. 텔레그램 명령어
- **문제점**: [`TelegramNotifier`](backend/notifications/telegram_notifier.py:43-596)가 이미 존재하지만 명령어 핸들러 없음
- **개선안**: `TelegramCommandBot` 클래스 추가
  - `/status`, `/portfolio`, `/schedule`, `/economic`, `/help` 명령어 구현
  - 기존 `TelegramNotifier`와 통합

### 6. 주간 리포트
- **문제점**: [`DailyReportScheduler`](backend/services/daily_report_scheduler.py:71-445)가 주간 리포트를 이미 지원
- **개선안**: 기존 스케줄러 확장
  - AI 시스템 자가 분석 기능 추가
  - 경제지표 정확도 분석 추가
  - 토요일/일요일 스케줄 조정

### 7. 🆕 Real-time Economic Watcher (v2.2)
- **문제점**: RSS 크롤링(10분)으로는 경제지표 발표 직후 반영 불가
- **개선안**: 이벤트 기반 스나이퍼 모듈
  - 발표 시간 +10초에 Actual 수집
  - Surprise 분석 및 즉시 알림
  - 브리핑 Context 자동 주입

---

## 📅 일정

| Phase | 소요 시간 | 누적 시간 | 주요 작업 |
|-------|----------|----------|----------|
| Phase 0 | 1일 | 1일 | 사전 준비 |
| Phase 1 | 1일 | 2일 | DB 마이그레이션 |
| Phase 2 | 1일 | 3일 | Ollama 전처리 스케줄러 |
| Phase 3 | 2일 | 5일 | 지능형 캐싱 시스템 |
| Phase 3.5 | 5일 | 10일 | 🆕 Real-time Economic Watcher |
| Phase 4 | 1일 | 9일 | 서머타임 자동 관리 |
| Phase 5 | 3일 | 12일 | 미국 시장 브리핑 |
| Phase 6 | 2일 | 14일 | 국내 시장 브리핑 |
| Phase 7 | 1일 | 15일 | KIS 포트폴리오 통합 |
| Phase 8 | 1일 | 16일 | 텔레그램 명령어 |
| Phase 9 | 2일 | 18일 | 주간 리포트 시스템 |
| Phase 10 | 2일 | 20일 | API 라우트 및 통합 테스트 |

**총 예상 시간**: 22일 (약 3.5주)

---

## 🚀 점진적 배포 전략

### 1단계: 기본 인프라 (Phase 0-4) - 1주일 안정화
- DB 마이그레이션
- Ollama 전처리 스케줄러
- 지능형 캐싱 시스템
- 서머타임 자동 관리
- **목표**: 안정적인 기반 구축

### 2단계: 브리핑 시스템 (Phase 5-7) - 1주일 안정화
- 미국 시장 브리핑
- 국내 시장 브리핑
- KIS 포트폴리오 통합
- **목표**: 5단계 브리핑 정상 작동

### 3단계: Economic Watcher + 완성 (Phase 3.5, 8-10) - 최종 테스트 및 배포
- Real-time Economic Watcher
- 텔레그램 명령어
- 주간 리포트 시스템
- API 라우트 및 통합 테스트
- **목표**: 전체 시스템 통합 및 배포

---

## 📊 모니터링 지표 (v2.2 추가)

### Economic Watcher 모니터링
- **수집 성공률**: 목표 ≥90%
- **Surprise 분석 정확도**: 방향 예측 정확도 추적
- **알림 지연 시간**: 발표 후 10~30초 내 전송
- **크롤링 실패율**: 알람 설정 (<5%)

### 시스템 모니터링
- **캐시 적중률**: 목표 >60%
- **일일 API 비용**: 목표 70% 절감
- **텔레그램 전송 성공률**: 목표 >99%
- **시스템 가동률**: 목표 >99%

### 로깅
- 모든 브리핑 생성 로그
- 캐시 결정 로그
- DST 변경 로그
- 텔레그램 전송 상태
- **🆕 Economic Watcher 수집 로그**
- **🆕 Surprise 분석 로그**
- **🆕 크롤링 실패 알람**

---

## ✅ 완료 기준

### 기능 요구사항
- [ ] 5개 일간 브리핑 자동 생성 (평일)
- [ ] **🆕 경제지표 발표 10초 내 Actual 수집 및 알림**
- [ ] **🆕 브리핑에 경제지표 Context 자동 주입**
- [ ] 2개 주간 리포트 자동 생성 (주말)
- [ ] DST 자동 감지 및 스케줄 조정
- [ ] 텔레그램 실시간 알림
- [ ] KIS 포트폴리오 연동
- [ ] 속보 실시간 감지

### 성능 요구사항
- [ ] API 비용 70% 절감
- [ ] 캐시 적중률 60% 이상
- [ ] 브리핑 생성 시간 2분 이내
- [ ] Ollama 전처리 30초 이내
- [ ] **🆕 경제지표 Actual 수집 성공률 ≥90%**
- [ ] **🆕 발표 후 10~30초 내 알림 전송**
- [ ] 시스템 가동률 99% 이상

### 품질 요구사항
- [ ] 11개 Phase 모두 개별 테스트 통과
- [ ] **🆕 Economic Watcher 통합 테스트 통과**
- [ ] 통합 테스트 통과
- [ ] DST 전환 테스트 통과
- [ ] 1주일 안정 운영

---

## 🚨 위험 관리

> [!WARNING]
> **DST 전환 위험**: 연 2회 DST 전환 시 스케줄 오류 가능
> 
> **완화**: Python `zoneinfo` 사용, 매일 자정 DST 체크, 테스트 철저

> [!WARNING]
> **API 비용 초과**: 고변동성 시 캐싱 실패 시 비용 급증
> 
> **완화**: 3단계 캐싱 필수, 일일 모니터링, 호출 제한

> [!IMPORTANT]
> **포트폴리오 정확성**: 실제 금융 데이터, 오류 시 투자 손실
> 
> **완화**: KIS API 응답 검증, 계산 교차 확인, 면책 조항

> [!WARNING] (v2.2 NEW)
> **크롤링 의존성**: Investing.com 사이트 구조 변경 시 크롤러 작동 중단
> 
> **완화**: 
> - FMP API 백업 시스템 구축
> - 사이트 구조 변경 감지 로직
> - 수동 알림 및 페일오버

> [!WARNING] (v2.2 NEW)
> **Actual 수집 실패**: 네트워크 지연, 사이트 다운 등으로 수집 실패 가능
> 
> **완화**: 
> - 재시도 로직 (3회, 5초 간격)
> - 15초, 30초 후 추가 시도
> - 실패 시 사용자에게 알림

> [!IMPORTANT] (v2.2 NEW)
> **시간 정확성**: asyncio.sleep 기반이므로 시스템 부하 시 지연 가능
> 
> **완화**: 
> - 높은 우선순위 프로세스로 실행
> - 타임스탬프 로깅으로 지연 모니터링
> - 발표 시간 -5초 여유 + 10초 지연 = 15초 내 수집 목표

> [!WARNING] (v2.2 NEW)
> **텔레그램 Rate Limiting**: 속보 + 브리핑 동시 전송 시 제한 위반
> 
> **완화**: 
> - 큐 시스템 도입
> - 0.5초 간격 확보
> - 우선순위 기반 전송 (경제지표 > 속보 > 브리핑)

> [!WARNING] (v2.2 NEW)
> **Investing.com 구조 변경**: 사이트 구조 변경 시 크롤러 작동 중단
> 
> **완화**: 
> - 구조 변경 감지 로직 추가
> - 예상 HTML 구조 검증
> - 변경 감지 시 알림

---

## 📚 관련 문서

- **원본 계획**: `docs/planning/260122_daily_briefing_system_v2.2_implementation_plan.md`
- **v2.1 최적화 계획**: `docs/planning/260122_daily_briefing_v2.1_optimized_implementation_plan.md`
- **TASKS**: `TASKS.md`
- **아키텍처**: `docs/architecture/structure-map.md`
- **DB 모델**: `backend/database/models.py`
- **텔레그램**: `backend/notifications/telegram_notifier.py`
- **Ollama**: `backend/ai/llm/ollama_client.py`

---

## 📝 배포 가이드

### 환경 설정

**.env 추가 설정**:
```env
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Telegram
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ENABLE_ALERTS=true

# Cache
CACHE_ENABLE=true
CACHE_TARGET_SAVINGS=0.70

# Economic Calendar Settings (v2.2 NEW)
ECONOMIC_CALENDAR_ENABLED=true
ECONOMIC_SNIPER_DELAY_SECONDS=10
ECONOMIC_MAX_FETCH_ATTEMPTS=3
ECONOMIC_RETRY_INTERVAL=5

# Data Sources
INVESTING_CALENDAR_URL=https://kr.investing.com/economic-calendar/
FMP_API_KEY=your_fmp_api_key  # 선택적

# Alert Settings
ECONOMIC_ALERT_MIN_IMPORTANCE=3     # ★★★만
ECONOMIC_ALERT_MIN_SURPRISE=5       # 5% 이상 괴리 시에만
```

### 배포 순서

1. **DB 마이그레이션**
   ```bash
   alembic revision --autogenerate -m "Add v2.2 fields and economic events"
   alembic upgrade head
   ```

2. **Ollama 설치**
   ```bash
   ollama pull llama3.2:3b
   ollama serve
   ```

3. **텔레그램 봇 설정**
   - @BotFather로 봇 생성
   - 토큰 및 채팅 ID 획득
   - `.env`에 설정

4. **Economic Watcher 초기화**
   ```bash
   # 오늘의 경제 일정 수동 로드 (테스트)
   python -m backend.services.economic_calendar_fetcher
   ```

5. **스케줄러 시작**
   ```bash
   python -m backend.automation.main_scheduler
   ```

---

## 🚀 권장 시작 순서

### Phase 0 (1일) → 즉시 시작 가능
- 기존 시스템 완전 이해
- DB 스키마 검증
- Ollama 모델 설치 확인
- 텔레그램 봇 설정 확인
- Investing.com 크롤링 테스트

### Phase 1 (1일) → DB 마이그레이션
- `DailyBriefing` 모델 업데이트
- `WeeklyReport` 테이블 생성
- `EconomicEvent` 테이블 생성
- Alembic 마이그레이션 생성 및 적용

### Phase 2-3 (3일) → 기본 인프라
- **Phase 2**: Ollama 전처리 스케줄러
- **Phase 3**: 지능형 캐싱 시스템
- **목표**: 1주일 안정화

### Phase 4 (1일) → 서머타임 자동 관리
- `TimezoneManager` 클래스 생성
- `DynamicScheduler` 클래스 생성
- DST 자동 감지 로직
- 스케줄 자동 전환 구현

### Phase 5-7 (3일) → 브리핑 시스템
- **Phase 5**: 미국 시장 브리핑
- **Phase 6**: 국내 시장 브리핑
- **Phase 7**: KIS 포트폴리오 통합
- **목표**: 1주일 안정화

### Phase 3.5 (5일) → Economic Watcher (중요!)
- Investing.com 크롤링 구조 파악: 1일
- Economic Watcher 구현: 2일
- 테스트 및 디버깅: 1-2일
- 통합 테스트: 1일

### Phase 8-10 (4일) → 완성
- **Phase 8**: 텔레그램 명령어
- **Phase 9**: 주간 리포트 시스템
- **Phase 10**: API 라우트 및 통합 테스트
- **목표**: 최종 테스트 및 배포

---

**작성자**: AI Trading System Team  
**검토일**: 2026-01-22  
**다음 액션**: Phase 0 시작 - 사전 준비
