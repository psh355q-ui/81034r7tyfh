# 실전 사용 가이드

**Constitutional AI Trading System 실전 활용법**

---

## 🚀 빠른 시작

### 방법 1: 대화형 모드 (추천)

```bash
python run_live.py
```

**화면 예시**:
```
🏛️ Constitutional AI Trading System
     실전 투자 도우미

📝 투자 아이디어를 입력하세요:

  종목 코드 (예: AAPL, MSFT, NVDA): AAPL
  
  AAPL을(를) 고려하는 이유:
  (예: AI 칩 기술 돌파구, 실적 호조 등): AI chip breakthrough
  
  예상 액션:
    1. BUY (매수)
    2. SELL (매도)
    3. HOLD (보유)
  선택 (1-3, 기본: 1): 1

📊 AAPL 실시간 데이터 조회 중...
✅ 데이터 수집 완료:
  현재가: $278.28
  변동: +0.09%
  거래량: 39,532,887

🏛️ 헌법 검증
제안 내용:
  종목: AAPL
  액션: BUY
  가격: $278.28
  주문 금액: $10,000 (10%)
  이유: AI chip breakthrough

검증 결과:
  ✅ 헌법 준수 - 거래 가능

💡 Constitutional AI 추천
✅ 승인 가능 제안:
  AAPL BUY @ $278.28

권장 사항:
  1. 헌법 기준을 충족합니다
  2. 포지션 크기를 준수합니다
  3. 리스크가 관리 가능합니다

⚠️ 주의:
  • 최종 결정은 본인이 하세요 (제3조)
  • 시장 상황을 계속 모니터링하세요
  • Stop Loss를 설정하세요
```

---

## 📖 사용 시나리오

### 시나리오 1: 아침 시장 체크

```bash
# 매일 아침 실행
python run_live.py

# 관심 종목 입력
종목: AAPL
이유: 관심 종목
액션: BUY

# → 실시간 가격 확인
# → 헌법 검증
# → 추천 확인
```

**용도**: 매일 포트폴리오 점검

---

### 시나리오 2: 뉴스 발생 시

```bash
python run_live.py

# 뉴스 입력
종목: NVDA
이유: AI GPU 수요 급증 뉴스
액션: BUY

# → Constitutional AI가 검증
# → 안전한지 확인
```

**용도**: 급변 시 빠른 판단

---

### 시나리오 3: 여러 종목 비교

```bash
python run_live.py

# 1차
종목: AAPL
이유: AI chip
액션: BUY
→ 결과 확인

# 다른 종목? y

# 2차
종목: MSFT
이유: Cloud growth
액션: BUY
→ 결과 확인

# 다른 종목? y

# 3차
종목: GOOGL
이유: Ad revenue
액션: BUY
→ 결과 확인
```

**용도**: 포트폴리오 구성

---

## 🎯 실전 사용 팁

### 1. 매일 루틴

**장 시작 전 (9:00 AM)**:
```bash
# 관심 종목 체크
python run_live.py
→ 3-5개 종목 검증
→ 헌법 통과 종목만 매수 고려
```

**장 마감 후 (4:30 PM)**:
```bash
# 오늘 거래 복기
python run_live.py
→ 오늘 매수/매도한 종목 재검증
→ Shadow Trade 업데이트 (수동)
```

---

### 2. 헌법 통과 전략

**✅ 통과하려면**:
- 포지션 크기: 자본의 10% 이하
- 인간 승인: 본인이 직접 결정
- 일일 거래: 5회 이하
- 리스크 관리: Stop Loss 준비

**❌ 거부되면**:
- 포지션 크기 줄이기
- 시장 상황 대기
- 다른 종목 고려

---

### 3. Shadow Trade 활용

**거부된 제안 추적**:
```python
# 수동으로 기록
거부일: 2025-12-15
종목: AAPL
가격: $278.28
이유: 포지션 과다

# 7일 후 (2025-12-22)
종목: AAPL
가격: $270.00 (하락)
→ DEFENSIVE_WIN! ✅
→ "안 사서 $800 손실 회피"
```

---

## 💡 고급 활용

### Option 1: 자동화 (Cron)

```bash
# crontab -e
# 매일 장 시작 30분 전
30 08 * * 1-5 python /path/to/run_live.py --ticker AAPL --auto

# 장 마감 후
30 16 * * 1-5 python /path/to/run_live.py --ticker AAPL --report
```

---

### Option 2: Telegram 통합

```python
# 추후 기능
# Telegram Bot과 연결
# → 알림 자동 수신
# → 승인/거부 버튼 클릭
```

---

### Option 3: Portfolio Mode

```python
# 전체 포트폴리오 분석
tickers = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'TSLA']

for ticker in tickers:
    # Constitutional 검증
    # → 전체 포트폴리오 최적화
```

---

## 📊 출력 이해하기

### 실시간 데이터
```
현재가: $278.28    ← Yahoo Finance 실시간
변동: +0.09%        ← 전일 대비
거래량: 39,532,887  ← 유동성 확인
```

### 헌법 검증
```
✅ 헌법 준수        ← 모든 규칙 통과
❌ 헌법 위반        ← 규칙 위반 감지

위반 사항:
  • 포지션 과다     ← 구체적 이유
  • 인간 승인 필요  ← 필요 조치
```

### AI 추천
```
✅ 승인 가능        ← 거래 가능
❌ 거부 권장        ← 거래 하지 마세요

권장 사항:
  1. 헌법 기준 충족 ← 안전 확인
  2. 포지션 준수     ← 리스크 관리
  3. 관리 가능       ← 통제 가능
```

---

## ⚠️ 주의사항

### 1. 최종 결정은 본인
```
AI는 "제안"만 합니다.
최종 결정은 제3조에 따라 "인간"이 합니다.
```

### 2. 시장 리스크
```
Constitutional AI는 안전을 우선하지만,
시장 리스크를 완전히 제거하지는 못합니다.
```

### 3. 데이터 지연
```
실시간 데이터는 15분 지연될 수 있습니다.
중요한 결정은 실제 브로커 데이터 확인 필수.
```

### 4. Paper Trading 우선
```
처음 사용 시:
1. Paper Trading (모의 투자)
2. 소액으로 테스트
3. 검증 후 본격 사용
```

---

## 🎓 학습 곡선

### Week 1: 탐색
- 하루 1-2번 실행
- 여러 종목 테스트
- 헌법 규칙 이해

### Week 2: 습관화
- 매일 루틴 확립
- 통과/거부 패턴 파악
- Shadow Trade 기록 시작

### Week 3: 최적화
- 나만의 전략 개발
- 포트폴리오 구성
- 성과 측정 시작

### Week 4+: 마스터
- 자동화 고려
- Telegram 통합
- 고급 기능 활용

---

## 📞 도움말

**문제 발생 시**:
1. `docs/QUICK_START.md` 참조
2. `docs/DATABASE_SETUP.md` 확인
3. `docs/TROUBLESHOOTING.md` (예정)

**추가 기능**:
- `test_live_trading.py` - 전체 시스템 테스트
- `demo_constitutional_workflow.py` - 데모 실행

---

**작성일**: 2025-12-15  
**버전**: 2.0.0  
**상태**: ✅ 실전 사용 가능
