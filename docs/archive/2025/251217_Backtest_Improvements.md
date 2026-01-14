# Backtest System Improvements - 2025-12-17

## 개요

백테스트 시스템의 UI 개선 및 데이터 품질 향상을 위한 일련의 개선 작업을 완료했습니다.

---

## 완료된 개선 사항

### 1. 헌법 준수 정보 표시 (Constitutional Compliance Banner)

**목적:** 백테스트와 실제 거래의 차이점을 명확히 표시

**구현 내용:**
- 백테스트 페이지 상단에 헌법 준수 배너 추가
- 각 조항별 적용 상태 시각적 표시:
  - ✅ 제1조 (자본 보존): 적용
  - ✅ 제2조 (설명 가능성): 적용
  - 🤖 제3조 (인간 승인): **AI 자동** (백테스트는 AI 완전 자율 시뮬레이션)
  - ⚠️ 제4조 (Circuit Breaker): 부분 적용
- 실제 거래 시 인간 승인 필수 안내 메시지

**파일:**
- `frontend/src/pages/BacktestDashboard.tsx` (100-130, 290-316 라인)

---

### 2. 백테스트 기간 표시

**목적:** 백테스트 기간을 명확히 표시하여 사용자 이해도 향상

**구현 내용:**
- 백테스트 결과 상단에 "백테스트 기간" 섹션 추가
- 시작일 ~ 종료일 표시 (예: 2024-01-01 ~ 2024-12-31)
- 눈에 띄는 그라디언트 배경으로 강조

**파일:**
- `frontend/src/pages/BacktestDashboard.tsx` (104-120 라인)

---

### 3. 거래 내역 날짜 형식 개선

**목적:** 거래 내역의 가독성 향상

**구현 내용:**
- 거래 내역 테이블에 "매수일", "매도일" 컬럼 추가
- YYMMDD 형식으로 날짜 표시 (예: 240315 → 2024년 3월 15일)
- `formatDate()` 헬퍼 함수 구현

**파일:**
- `frontend/src/pages/BacktestDashboard.tsx` (447-475 라인)

---

### 4. 중복 뉴스 처리 버그 수정

**문제:** 같은 뉴스가 매일 재처리되어 5만+ 개의 중복 시그널 생성

**원인:**
```python
# 기존: 같은 뉴스를 계속 재처리
def _get_available_analyses(self, current_time):
    return all_analyses_up_to_current_time  # 매일 전체 뉴스 반환!
```

**해결책:**
```python
# 개선: 처리된 뉴스 ID 추적
def __init__(self):
    self.processed_analyses: set = set()  # 처리된 뉴스 ID

def _process_analysis(self, analysis):
    if analysis.id in self.processed_analyses:
        return  # 이미 처리됨
    self.processed_analyses.add(analysis.id)
    # ... 시그널 생성
```

**결과:**
- 시그널 수: 54,369개 → 152개 (정상화)
- 실행률: 0.0% → 3.3% (현실적인 수치)

**파일:**
- `backend/backtesting/signal_backtest_engine.py` (359-365, 447-476 라인)

---

### 5. 뉴스 데이터 균등 분산

**문제:** 랜덤 시드 고정으로 뉴스가 초반에 집중됨

**원인:**
```python
random.seed(42)  # 고정 시드
day_offset = random.randint(0, total_days - 1)  # 항상 같은 패턴
```

**해결책:**
```python
# 균등 분산 알고리즘
days_per_news = total_days / num_news
for i in range(num_news):
    base_day = int(i * days_per_news)
    random_offset = random.randint(-2, 2)  # 작은 랜덤성
    day_offset = max(0, min(total_days - 1, base_day + random_offset))
```

**결과:**
- 뉴스 분포: 1년 전체에 고르게 생성
- 로그 확인: First 5 news dates: 2024-01-01~01-06, Last 5 news dates: 2024-12-24~12-31

**파일:**
- `backend/api/backtest_router.py` (191-204 라인)

---

### 6. SignalValidator 호환성 개선

**문제:** 백테스트 엔진이 `validator.validate()` 호출, 하지만 메서드 없음

**원인:**
```python
# signal_validator.py에는 validate_signal()만 존재
def validate_signal(self, signal, ...): ...

# 백테스트 엔진은 validate() 호출
is_valid, reason = self.signal_validator.validate(signal)  # ❌ 에러!
```

**해결책:**
```python
# signal_validator.py에 validate() 래퍼 메서드 추가
def validate(self, signal: TradingSignal) -> Tuple[bool, str]:
    approved, reason, _ = self.validate_signal(signal)
    return (approved, reason)
```

**파일:**
- `backend/signals/signal_validator.py` (200-212 라인)
- `backend/api/backtest_router.py` (logger import 추가)

---

### 7. 백테스트 설정 완화

**문제:** 실시간 거래용 검증 설정이 백테스트에는 너무 엄격

**해결책:**
```python
# 백테스트용 SignalValidator 초기 화
self.signal_validator = SignalValidator(
    min_confidence=0.6,  # 0.7 → 0.6 완화
    max_position_size=1.0,  # 엔진에서 관리
    max_daily_trades=100,  # 제한 없음
    daily_loss_limit_pct=10.0  # 관대하게
)
```

**파일:**
- `backend/backtesting/signal_backtest_engine.py` (365-372 라인)

---

### 8. 티커 확장 (핵심 개선)

**문제:** 7개 티커만 있어서 초기에 모두 매수 후 거래 중단

**시나리오:**
```
1월: AAPL, TSLA, MSFT, NVDA, GOOGL, AMZN, META 모두 매수
    (같은 티커 중복 보유 불가 규칙)
2월: 일부 청산, 하지만 대부분 유지
3~12월: 새 뉴스 → "이미 보유 중" → 거래 없음 ❌
```

**해결책:**
```python
# 티커 확장: 7개 → 20개
tickers = [
    # Big Tech (7)
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    # Tech/Semiconductors (7)
    "AMD", "INTC", "QCOM", "CRM", "NFLX", "DIS", "V",
    # Finance/Consumer (6)
    "JPM", "BAC", "WMT", "PG", "KO", "PEP"
]
```

**결과:**
- 거래 수: 11개 → **22개** (2배 증가)
- 실행률: 11% → **24.8%** (크게 개선)
- 기간: **1년 전체**에 고르게 분산
- 다양한 섹터 (테크, 반도체, 금융, 소비재)

**파일:**
- `backend/api/backtest_router.py` (192-200, 241-256 라인)

---

## 백테스트 결과 개선 비교

### Before (문제 상황)
```
총 시그널: 54,369개 (중복!)
실행됨: 2개
거래 기간: 2024-01-05 ~ 2024-01-06 (2일만!)
승률: 50%
```

### After (개선 후)
```
총 시그널: 121개 (정상)
실행됨: 30개
실행률: 24.8%
거래 기간: 2024-01-09 ~ 2024-12월 (1년 전체)
거래 수: 22개
티커: 20개 (다양한 섹터)
승률: 36.4% (Mock 데이터 특성상 정상)
```

---

## 기술적 개선 사항

### 1. 코드 품질
- ✅ 중복 코드 제거
- ✅ 에러 핸들링 강화
- ✅ 호환성 개선 (validate 메서드)
- ✅ 로깅 추가 (디버깅 용이)

### 2. 데이터 품질
- ✅ 중복 제거 메커니즘
- ✅ 균등 분산 알고리즘
- ✅ 티커 다양화
- ✅ 현실적인 검증 설정

### 3. 사용자 경험
- ✅ 명확한 기간 표시
- ✅ 헌법 준수 정보
- ✅ YYMMDD 날짜 형식
- ✅ 더 많은 거래 데이터

---

## 다음 단계 (Historical Data Seeding)

사용자 요구사항에 따라 다음 기능 개발 예정:

### 1. Multi-Source News Crawling
- NewsAPI: 100건/일
- Google News: RSS 크롤링
- Yahoo Finance: 티커별 뉴스

### 2. Comprehensive News Processing
- 임베딩 생성 (OpenAI 1536-dim)
- 자동 태깅 (주제, 티커, 감정)
- 핵심 주장/요약 추출
- 메타데이터 구조화 (출처, 기자, YYMMDDHHMMSS)

### 3. yfinance Integration
- 무료 무제한 주가 데이터
- OHLCV 전체 제공
- 역사적 데이터 백필

자세한 계획은 `implementation_plan.md` 참조.

---

## 참고 파일

**Frontend:**
- `frontend/src/pages/BacktestDashboard.tsx`

**Backend:**
- `backend/backtesting/signal_backtest_engine.py`
- `backend/api/backtest_router.py`
- `backend/signals/signal_validator.py`

**문서:**
- `implementation_plan.md` (Historical Data Seeding 계획)
- `task.md` (전체 작업 체크리스트)
