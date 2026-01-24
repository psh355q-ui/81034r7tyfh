# Daily Briefing System v2.2 - 구현 계획서

**작성일**: 2026-01-22  
**버전**: v2.2 Implementation Plan (Real-time Economic Watcher 포함)  
**상태**: 계획 완료, 구현 대기  

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

## 요약

24시간 AI 기반 트레이딩 브리핑 시스템 + **실시간 경제지표 감시 시스템**. 5가지 일간 브리핑, 자동 서머타임 스케줄링, 70% API 비용 절감을 위한 지능형 캐싱, KIS 포트폴리오 연동, 실시간 텔레그램 알림, 경제지표 발표 10초 내 분석 및 알림, 자가 개선 AI 분석을 포함한 주간 리포트 시스템.

---

## 시스템 아키텍처

### 전체 구성도 (v2.2)

```
┌─────────────────────────────────────────────────────────────┐
│                  24시간 브리핑 시스템 v2.2                    │
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
│  │           5단계 브리핑 엔진                    │      │  │
│  │  ┌──────────┬──────────┬──────────┬──────────┐ │      │  │
│  │  │프리마켓  │체크포인트│미국 마감 │국내 오픈 │ │      │  │
│  │  │ 23:00*   │01:00/03* │ 07:10*   │ 08:00    │ │      │  │
│  │  └──────────┴──────────┴──────────┴──────────┘ │      │  │
│  │                                                  │      │  │
│  │  ┌────────────────────────────────────────────┐ │      │  │
│  │  │   Gemini/Claude API + 웹 검색              │ │      │  │
│  │  │   (지능형 캐싱: 70% 비용 절감)             │ │      │  │
│  │  │   + 경제지표 긴급 Context                  │ │      │  │
│  │  └────────────────────────────────────────────┘ │      │  │
│  └─────────────────────────────────────────────────┘      │  │
│                                                            │  │
│  ┌────────────────────────────────────────────────────────┤  │
│  │              통합 레이어                               │  │
│  │  ┌──────────────┬──────────────┬────────────────────┐  │  │
│  │  │  KIS API     │  텔레그램    │  캐시 매니저       │  │  │
│  │  │  포트폴리오  │  봇          │  (5단계 전략)      │  │  │
│  │  └──────────────┴──────────────┴────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘

* = 서머타임 자동 조정 (동절기/하절기)
```

---

## 1. 브리핑 시스템 개요

### 1.1 6단계 브리핑 스케줄 (v2.2)

| 시간 | 브리핑 타입 | 목적 | DST 조정 |
|------|------------|------|----------|
| **??:??** | ⚡ **경제지표 속보** | **발표 10초 후 즉시 알림 (NEW)** | - |
| **23:00** / 22:00 | 🌙 프리마켓 | 미국 장 시작 전 프리뷰 (경제지표 포함) | ✅ |
| **01:00** / 00:00 | 📍 체크포인트 #1 | 장 시작 30분 후 (유의미한 변동 시) | ✅ |
| **03:00** / 02:00 | 📍 체크포인트 #2 | 장 중간 점검 (유의미한 변동 시) | ✅ |
| **07:10** / 06:10 | 🇺🇸 미국 마감 | 미국 장 마감 분석 | ✅ |
| **08:00** | 🇰🇷 국내 오픈 | 한국 시장 오픈 브리핑 | ❌ |

**주간 리포트:**
- **토요일 14:00**: 📊 주간 리뷰
- **일요일 22:00**: 🔮 주간 전망 + 🤖 AI 시스템 자가 분석

---

## 2. 구현 Phase (총 11단계)

### Phase 1: 데이터베이스 마이그레이션

**신규 테이블: `economic_events`**

```python
class EconomicEvent(Base):
    __tablename__ = "economic_events"
    
    id = Column(Integer, primary_key=True)
    event_name = Column(String(200))  # 예: "미국 3분기 실질 GDP"
    country = Column(String(10))      # US, KR, EU, CN, JP
    category = Column(String(50))     # GDP, Inflation, Employment, etc.
    
    event_time = Column(DateTime(timezone=True))  # 발표 예정 시간 (KST)
    importance = Column(Integer)      # 1=★, 2=★★, 3=★★★
    
    forecast = Column(String(50))     # 예상치 (4.3%)
    actual = Column(String(50))       # 실제치 (발표 후 업데이트)
    previous = Column(String(50))     # 이전치
    
    surprise_pct = Column(Float)      # (실제-예상)/예상 * 100
    impact_direction = Column(String(20))  # Bullish/Bearish/Neutral
    impact_score = Column(Integer)    # 영향도 점수 (0-100)
    
    is_processed = Column(Boolean)    # 처리 완료 여부
    processed_at = Column(DateTime(timezone=True))
```

---

### Phase 2: Ollama 전처리 시스템

*(v2.1과 동일)*

---

### Phase 3: 지능형 캐싱 시스템

*(v2.1과 동일)*

---

### **Phase 3.5: 🆕 Real-time Economic Watcher (NEW)**

#### 시스템 흐름

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

#### 핵심 파일

**1. Economic Calendar Fetcher** (`backend/services/economic_calendar_fetcher.py`)
- Investing.com 경제 캘린더 크롤링
- ★★★ 이벤트만 필터링
- DB 저장

**2. Economic Watcher** (`backend/services/economic_watcher.py`)
- 매일 00:05 오늘의 일정 로드 및 스나이퍼 예약
- 발표 +10초에 Actual 수집
- 재시도 로직 (3회, 5초 간격)
- Surprise 분석 및 영향도 점수 계산
- 텔레그램 즉시 알림

**3. 브리핑 통합**
- 모든 브리핑에 경제지표 긴급 Context 섹션 추가
- Surprise ±5% 이상 시 최우선 분석

#### Surprise 분석 로직

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

#### 텔레그램 알림 예시

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

---

### Phase 4: 서머타임 자동 관리

*(v2.1과 동일)*

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

---

### Phase 5: 미국 시장 브리핑

**프리마켓 브리핑에 경제지표 Context 추가**:

```python
async def generate_premarket_briefing(self) -> str:
    # 1. Ollama 전처리 RSS
    # 2. KIS API 포트폴리오
    # 3. 🆕 최근 발표된 경제지표 조회
    economic_context = await self._get_recent_economic_events()
    
    # 4. 프롬프트에 경제지표 섹션 추가
    prompt = PREMARKET_BRIEFING_PROMPT.format(
        preprocessed_rss=...,
        portfolio_data=...,
        economic_events_context=economic_context  # 추가
    )
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

---

### Phase 6: 국내 시장 브리핑

*(v2.1과 동일)*

---

### Phase 7: KIS API 포트폴리오 연동

*(v2.1과 동일)*

---

### Phase 8: 텔레그램 알림 시스템

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

---

### Phase 9: 주간 리포트 시스템

*(v2.1과 동일)*

**주간 전망에 경제지표 정확도 분석 추가**:
- 예측 vs 실제 적중률
- Surprise 방향 예측 정확도
- 시장 반응 분석 (지표 발표 후 S&P 5분/15분/1시간 변동률)

---

### Phase 10: API 라우트 및 통합 테스트

**신규 엔드포인트**:
- `GET /api/reports/economic-events/today` - 오늘의 경제 일정
- `GET /api/reports/economic-events/recent` - 최근 발표된 지표 (processed=True)
- `POST /api/reports/economic-events/manual-trigger` - 수동 스나이퍼 트리거

---

## 3. 검증 계획

### Phase 3.5 검증: Economic Watcher (NEW)

**DB 테이블**:
- [ ] `economic_events` 테이블 생성 확인
- [ ] `economic_event_history` 테이블 생성 확인
- [ ] 인덱스 정상 생성

**캘린더 수집**:
- [ ] Investing.com 크롤링 정상 동작
- [ ] ★★★ 이벤트만 필터링
- [ ] DB 저장 확인

**스나이퍼 스케줄링**:
- [ ] 매일 00:05 캘린더 로드
- [ ] 이벤트별 asyncio.Task 생성
- [ ] 발표 시간 +10초에 트리거

**Actual 수집**:
- [ ] 재시도 로직 (3회, 5초 간격)
- [ ] 수집 성공률 >90%

**Surprise 분석**:
- [ ] 괴리율 계산 정확
- [ ] 방향 판정 (Bullish/Bearish/Neutral)
- [ ] 영향도 점수 (0-100)

**알림 및 통합**:
- [ ] 텔레그램 즉시 알림
- [ ] 브리핑 Context 주입
- [ ] 히스토리 저장

---

## 4. 배포 가이드

### 환경 설정

**.env 추가 설정**:
```env
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
   alembic revision --autogenerate -m "Add economic events table v2.2"
   alembic upgrade head
   ```

2. **Economic Watcher 초기화**
   ```bash
   # 오늘의 경제 일정 수동 로드 (테스트)
   python -m backend.services.economic_calendar_fetcher
   ```

3. **스케줄러 시작**
   ```bash
   python -m backend.automation.main_scheduler
   ```

---

## 5. 위험 관리

> [!WARNING]
> **크롤링 의존성**: Investing.com 사이트 구조 변경 시 크롤러 작동 중단
> 
> **완화**: 
> - FMP API 백업 시스템 구축
> - 사이트 구조 변경 감지 로직
> - 수동 알림 및 페일오버

> [!WARNING]
> **Actual 수집 실패**: 네트워크 지연, 사이트 다운 등으로 수집 실패 가능
> 
> **완화**: 
> - 재시도 로직 (3회, 5초 간격)
> - 15초, 30초 후 추가 시도
> - 실패 시 사용자에게 알림

> [!IMPORTANT]
> **시간 정확성**: asyncio.sleep 기반이므로 시스템 부하 시 지연 가능
> 
> **완화**: 
> - 높은 우선순위 프로세스로 실행
> - 타임스탬프 로깅으로 지연 모니터링
> - 10초 + 버퍼 5초 = 15초 내 수집 목표

---

## 6. 완료 기준

✅ **기능**:
- [ ] 5개 일간 브리핑 자동 생성
- [ ] **🆕 경제지표 발표 10초 내 Actual 수집 및 알림**
- [ ] **🆕 브리핑에 경제지표 Context 자동 주입**
- [ ] 2개 주간 리포트 자동 생성
- [ ] DST 자동 감지 및 조정
- [ ] 텔레그램 알림 정상 작동
- [ ] 포트폴리오 연동 완료

✅ **성능**:
- [ ] API 비용 ≥70% 절감
- [ ] 캐시 적중률 ≥60%
- [ ] **🆕 경제지표 Actual 수집 성공률 ≥90%**
- [ ] **🆕 발표 후 10~30초 내 알림 전송**
- [ ] 시스템 가동률 ≥99%

✅ **품질**:
- [ ] 11개 Phase 모두 테스트
- [ ] **🆕 Economic Watcher 통합 테스트 통과**
- [ ] 통합 테스트 통과
- [ ] 1주일 안정 운영

---

## 7. 일정

**예상 소요 기간**: 2.5-3.5주 (19-23일)

| Phase | 소요 | 누적 |
|-------|------|------|
| Phase 1 (DB) | 1일 | 1일 |
| Phase 2-3 (Ollama+Cache) | 3-4일 | 4-5일 |
| **Phase 3.5 (Economic Watcher)** | **3-4일** | **7-9일** |
| Phase 4-6 (Schedule+Briefing) | 4-5일 | 11-14일 |
| Phase 7-8 (Portfolio+Telegram) | 3-4일 | 14-18일 |
| Phase 9 (Weekly) | 2-3일 | 16-21일 |
| Phase 10 (Integration) | 3-4일 | 19-25일 |

---

## 8. 참고 문서

- **v2.2 원본 계획**: `docs/planning/daily_briefing_system_v2.2_final_plan.md`
- **v2.1 계획**: `docs/planning/daily_briefing_system_v2.1_final_plan.md`
- **아키텍처**: `docs/architecture/structure-map.md`
- **Task 목록**: `TASKS.md`

---

**작성**: 2026-01-22  
**v2.2 주요 추가사항**: Real-time Economic Watcher  
**승인 대기중**
